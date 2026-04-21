# Lazy-Resume Checklist

A 60-second checklist for the **incoming session** to run as its first action after receiving a handoff prompt, replacing the old "re-read everything" reflex.

The full normative spec is in [`resumption-protocol.md`](resumption-protocol.md). This file is the field-usable condensate — print this, not the spec, when you are about to resume.

---

## Step 1 — Name the mode (do not read anything yet)

Look at the handoff prompt. Pick one resume mode:

| Signal in the handoff prompt | Mode |
|---|---|
| Same phase, same role, mid-work interruption | Lazy |
| Phase advances (e.g. header says "Phase 4", prior was "Phase 3") | Targeted |
| A different role is now acting (Planner → Implementer etc.) | Role-scoped |
| Manifest missing / stale / not referenced in the prompt | Full |
| Lean-spec header (no Change Manifest) | Minimal |

Announce the chosen mode in your first output before any tool call. If the prompt explicitly declares a mode, use that one unless you see a drift signal (Step 3).

---

## Step 2 — Per-mode read list

### Lazy

- **Read:** Change Manifest only.
- **Do NOT read:** spec, plan, test plan, prior test reports, completion report.

### Targeted

Read the Manifest, then read the input artifacts for the entering phase:

| Entering phase | Read beyond Manifest |
|---|---|
| Phase 1 Investigate | Spec (if user-supplied) |
| Phase 2 Plan | Investigation summary (already in Manifest) |
| Phase 3 Test Plan | Plan |
| Phase 4 Implement | Plan + test plan |
| Phase 5 Review | Plan + test report + diff of changed files |
| Phase 6 Sign-off | Review notes |
| Phase 7 Deliver | Sign-off record |
| Phase 8 Post-delivery | Completion report |

Do NOT read artifacts not in this row. If one is missing, jump to Step 3 (drift).

### Role-scoped

Read the Manifest, then the upstream role's single output:

| Incoming role | Read beyond Manifest |
|---|---|
| Planner | Clarification / spec |
| Implementer | Plan + test plan |
| Reviewer | Implementation notes + test report |

### Full

Only when the Manifest itself is absent, obviously stale, or drift is suspected. Announce *why* before reading.

Read: spec, plan, test plan, latest test report, completion report (if exists).

### Minimal (Lean mode only)

- **Read:** Lean-spec note + the current task-list item.
- **Do NOT read:** any other artifact.

---

## Step 3 — Drift detection

Before reading anything, scan the handoff prompt for these drift signals:

- [ ] Handoff prompt is longer than 800 words (the template's hard cap) — recompact first or reject.
- [ ] Handoff prompt's read block has more than 3 paths — Manifest is incomplete; fix Manifest first.
- [ ] The Manifest path in the prompt does not resolve — stop and report.
- [ ] The Manifest's `phase` field disagrees with the prompt's phase header — stop and report.
- [ ] The Manifest's `last_updated` is older than the most recent change in git log — declare Full mode with reason.
- [ ] A listed read-block path does not exist — stop and report.

If any drift signal triggers: **do not proceed with the chosen mode**. Announce the drift, name the Manifest field that needs fixing, and stop. Widening the read set is not a fix — the state snapshot is broken, and reading more will not repair it.

---

## Step 4 — Context-budget check

Estimate (rough: word count across this prompt + every path you plan to read) and compare to the runtime's usable context.

| Situation | Action |
|---|---|
| Estimated reads ≤ 30% of context | Proceed at the chosen mode |
| Estimated reads > 30% of context | Downgrade one tier (Full → Role-scoped → Targeted → Lazy) and announce the downgrade |
| Even Lazy reads > 30% | Manifest is oversized — drift signal; stop and request Manifest compaction |

This step is advisory but mandatory: naming a threshold makes the check happen.

---

## Step 5 — Start work

Before touching code:

1. Announce: resume mode (from Step 1), current mode (Lean / Full), current phase, next action, missing evidence.
2. Confirm the Manifest's "next action" matches the handoff prompt's "Next action" line.
3. Only now, execute the next action.

---

## What this checklist replaces

The pre-1.9.0 reflex was:
> Re-read the spec, plan, test plan, latest test report, and completion report. Then figure out where you left off.

That reflex caused session-handoff context collapse on Full-mode work. The new reflex is:
> Name the mode. Read the minimum the mode requires. If the Manifest cannot answer "what comes next," fix the Manifest before reading further.

---

## See also

- [`resumption-protocol.md`](resumption-protocol.md) — full normative protocol.
- [`../templates/handoff-prompt-template.md`](../templates/handoff-prompt-template.md) — what the outgoing session sends you.
- [`../../../docs/change-manifest-spec.md`](../../../docs/change-manifest-spec.md) §State-snapshot discipline — why the Manifest, not the artifact set, is the thing you read.
- [`../../../docs/phase-gate-discipline.md`](../../../docs/phase-gate-discipline.md) Rule 6 — re-entry vs resumption.
