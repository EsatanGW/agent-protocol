# Application-driven Loop — Reference Walk-through

> **Status.** Non-normative reference. The binding shape lives in [`docs/cross-cutting-concerns.md`](../../../docs/cross-cutting-concerns.md) §Application-driven verification. This file is a worked example showing how an agent that *drives the running application* uses the BEFORE / trigger / AFTER / fix / re-validate pattern to close the loop on a user-surface or operational-surface change.

---

## What problem does this solve

A source-driven check (read the function, run a unit test, read the lint output) answers a different question from an application-driven check (render the page, traverse the flow, capture the runtime event stream, pull the deployed artifact). Source can be correct while the deployed artefact is wrong: minifier rewrites names, release config disables debug paths, the asset pipeline transforms an SVG into a different sprite, the database has history the test fixture does not. A user-surface or operational-surface change that closes only on source-driven evidence is incomplete; the gap surfaces as a Phase 8 finding or — worse — a production incident.

The application-driven loop is the agent-side counterpart of a manual playtest (`docs/playtest-discipline.md`): the agent stands up an isolated instance, captures the system's state before and after a deliberate trigger, diffs the two, and only declares the change closed when the diff matches the intent.

This pattern is the L4 evidence shape in [`docs/autonomy-ladder-discipline.md`](../../../docs/autonomy-ladder-discipline.md) and the per-surface evidence shape declared in [`docs/cross-cutting-concerns.md`](../../../docs/cross-cutting-concerns.md) §Application-driven verification.

---

## The reference shape (in pseudocode)

```bash
# A worked walk-through. Each step names a capability category;
# the runtime bridge picks which concrete tool fulfils it.
# Capability categories — never specific tools — appear here per CLAUDE.md §2.

# 0. Bail-out gate.
# If the change does not touch the user / operational surfaces, application-driven
# evidence is not required. Exit silent (the loop did not apply).
read_event_from_stdin
surfaces=$(jq -r '.context.surfaces_touched[]' )
if ! echo "$surfaces" | grep -qE '^(user|operational)$'; then
  exit 0
fi

# 1. Select target + clear ambient state.
# capability category: shell execution + browser interaction (or app-launch capability)
spin_up_isolated_instance        # per-worktree environment (per observability-legibility-discipline.md)
clear_runtime_event_streams      # log buffer, metric buffer, trace buffer

# 2. Snapshot BEFORE.
# capability category: state capture (DOM tree, screenshot, log slice, metric snapshot, trace baseline)
before_artifact=$(capture_snapshot --tag before)

# 3. Trigger the UI / API / data path the change is supposed to affect.
# capability category: browser interaction OR shell execution OR scripted client
trigger_ui_path                  # the deliberate exercise
runtime_events=$(collect_events_during_trigger)

# 4. Snapshot AFTER.
after_artifact=$(capture_snapshot --tag after)

# 5. Diff BEFORE → AFTER and the runtime event stream.
# Both must match the intent declared in the manifest.
diff_artifact=$(diff_snapshots "$before_artifact" "$after_artifact")
event_findings=$(check_runtime_events "$runtime_events")

# 6. Apply fix + restart, IF the diff or events do not match intent.
# This is the agent-internal corrective loop. Cap iterations at N (recommend N=5);
# beyond N, escalate per ai-operating-contract.md §Stop conditions.
iter=0
while not_clean "$diff_artifact" || has_findings "$event_findings"; do
  iter=$((iter + 1))
  if [ "$iter" -gt 5 ]; then
    echo "ESCALATE: application-driven loop did not converge in 5 iterations" >&2
    exit 1
  fi
  apply_fix
  restart_isolated_instance
  clear_runtime_event_streams
  before_artifact=$(capture_snapshot --tag before-iter-$iter)
  trigger_ui_path
  runtime_events=$(collect_events_during_trigger)
  after_artifact=$(capture_snapshot --tag after-iter-$iter)
  diff_artifact=$(diff_snapshots "$before_artifact" "$after_artifact")
  event_findings=$(check_runtime_events "$runtime_events")
done

# 7. Persist artefacts as evidence.
# Each capture maps to a manifest evidence_plan row. Tag with iteration count
# so the Reviewer can audit how many corrective iterations were needed.
record_evidence_row \
  --type screenshot_diff \
  --location "$diff_artifact" \
  --collected_at "$(now)" \
  --metadata "iterations=$iter"
record_evidence_row \
  --type interaction_recording \
  --location "$runtime_events" \
  --collected_at "$(now)"
exit 0
```

The shape is not the script — it is the **evidence contract**: a BEFORE artefact, a triggered runtime event stream, an AFTER artefact, an iteration-bounded corrective loop, and one evidence row per captured artefact pointing at the artefact location.

---

## Step-by-step evidence mapping

Each step produces a row in `evidence_plan` that resolves to an existing `evidence_plan[*].type` enum value (per `docs/evidence-quality-per-type.md`). The agent does **not** invent new evidence types.

| Loop step | `evidence_plan[*].type` | Per-type acceptance signal (per `evidence-quality-per-type.md`) |
|---|---|---|
| 1 — select target + clear console | `setup_log` (or runtime-bridge equivalent) | The selected target's address / process ID / worktree path is recorded |
| 2 — snapshot BEFORE | `screenshot_diff` (capture mode) OR `dom_snapshot` OR `state_dump` | Artefact file exists, has non-zero size, captured-at timestamp ≥ manifest's earliest `last_updated` |
| 3 — trigger UI path + collect runtime events | `interaction_recording` | Stream covers the trigger window; event count > 0; no truncation marker |
| 4 — snapshot AFTER | same as step 2 | Same per-type acceptance; pairs with step 2 by tag |
| 5 — diff & check events | `screenshot_diff` (diff mode), `log_sample`, `metric_diff` | Diff is non-trivial (something actually changed) and matches the intent stated in the manifest's `purpose` field |
| 6 — apply fix + restart (per iteration) | `corrective_iteration_log` (`runtime_log` enum value with `subtype: corrective`) | One row per iteration; iteration count is the metadata field |
| 7 — persist | All of the above | Each row's `status: collected`; provenance per `automation-contract.md` Rule 2.13 |

---

## What the agent sees on each path

### Path 1 — first iteration is clean

Loop fires. BEFORE captured. Trigger fires. AFTER captured. Diff matches intent. Event stream contains no unexpected error / warning. Loop exits with 1 iteration recorded. `evidence_plan` shows `iterations=0` (the corrective loop did not run; the first attempt was already clean).

### Path 2 — diff matches intent but event stream surfaces a regression

Loop fires. BEFORE captured. Trigger fires. AFTER captured. Diff matches intent. Event stream contains a runtime warning that the manifest did not predict. The loop's step 5 fails on `event_findings`. The agent reads the warning, traces the cause, applies a fix, restarts, re-runs the loop. Iteration 2 is clean. `evidence_plan` records both iterations; the Reviewer sees the two-iteration trail and can audit whether the warning was material.

### Path 3 — loop does not converge in 5 iterations

The iteration cap fires. Step 6's escalation path triggers. The change is *not closed* — instead, the manifest carries an `escalations[*].trigger: application_driven_loop_no_converge` entry, the agent stops, and the human is paged per `decision-trees.md §Tree D`. Five corrective iterations on the same change is a signal the diagnosis is wrong, not the fix; further automated retries waste budget.

---

## What does NOT belong in the loop

- **Source-only evidence.** Reading the function, running unit tests, inspecting the lint output — these complement application-driven evidence; they do not substitute for it. A change that closes with only source-driven evidence on a user / operational surface fails the `cross-cutting-concerns.md §Application-driven verification` discipline.
- **Manual screenshots taken outside the loop.** A screenshot pasted from local desktop, with no provenance, no timestamp, no diff partner, is decorative evidence (`evidence-quality-per-type.md §Decorative evidence`). The loop's screenshot must be machine-captured at a known timestamp and paired with its BEFORE counterpart.
- **Triggering the path without clearing ambient state first.** A BEFORE captured against a polluted log / metric / trace buffer hides the trigger's effect; the diff is not interpretable. Step 1 (clear ambient state) is non-optional.
- **Production triggering.** The loop runs in an isolated per-worktree instance, never against production. Production is observed (Phase 8, `post-delivery-observation.md`); production is not driven by an agent's verification loop.
- **Reusing a single isolated instance across changes.** State leaks between changes — the BEFORE of change B contains the AFTER of change A. Each change spins up its own instance per `docs/observability-legibility-discipline.md` (or, in environments without per-worktree isolation, restarts the instance with a deterministic clean-slate ritual recorded in `evidence_plan`).

---

## Anti-patterns this reference rejects

- *"Restart and retry" without diagnosis.* Step 6 says **apply fix + restart**, not restart alone. A restart-only retry that happens to succeed on iteration 3 hides a flaky test; the next deployment exposes the flake. Each iteration must carry a fix description in its evidence row.
- *No BEFORE artefact.* Without BEFORE, the AFTER cannot be diffed; the agent is reduced to "looks right." The pattern *is* the diff; without BEFORE, the loop did not run.
- *AFTER without runtime event capture.* The AFTER snapshot proves the visible state changed; the runtime events prove *how* it changed and whether anything else changed too. A loop that captures AFTER but not events misses second-order effects (a fixed UI path that introduced a second background timer, a corrected query that doubled write traffic).
- *Iteration cap = ∞.* Five iterations is the recommended cap because beyond that, the diagnosis is wrong. Removing the cap turns the loop into a Ralph-Wiggum infinite retry that exhausts the agent's budget without producing a fix.
- *Persisting only the final iteration's artefacts.* The Reviewer needs the iteration trail to audit whether the corrective loop was substantive or accidental. Discarding intermediate iterations is the loop-side analogue of squashing a debug history.
- *Using the loop as the only evidence shape.* Application-driven evidence is necessary on user / operational surfaces but not sufficient. Information-surface changes still need migration dry-runs; system-interface-surface changes still need contract-level proof. The loop is one column in `evidence_plan`, not the whole row.

---

## Where this fits in the methodology

- **Capability contract counterpart of `docs/cross-cutting-concerns.md` §Application-driven verification** — that section names the discipline; this file demonstrates the loop shape.
- **Cross-checks against `docs/observability-legibility-discipline.md`** — step 1's "spin up isolated instance + clear runtime event streams" presupposes the per-worktree observability stack the discipline mandates. Without that stack, step 3's runtime-event capture cannot run; the loop degrades to BEFORE + AFTER snapshots only, which weakens but does not invalidate the evidence.
- **Cross-checks against `skills/engineering-workflow/references/back-pressure-loop.md`** — the back-pressure pattern governs *hook output* on success/failure; this loop governs *agent execution* against the running application. They are orthogonal: the back-pressure pattern silences a passing audit hook; the application-driven loop captures evidence regardless of pass/fail.
- **Forced rung in `docs/autonomy-ladder-discipline.md`** — L2 mandates application-driven evidence when the user surface is touched and `breaking_change.level >= L2`; L4 mandates it on every change.
- **Cross-checks against `docs/decision-trees.md` §Tree D** — the iteration-cap-exceeded escalation maps to Tree D's "agent autonomy ceiling reached" leaf.
