# Back-pressure Loop — Reference Walk-through

> **Status.** Non-normative reference. The binding shape lives in [`docs/runtime-hook-contract.md`](../../../docs/runtime-hook-contract.md) §Back-pressure pattern. This file is a worked example showing how a completion-audit (Category D) hook is shaped so that its output reinforces — rather than dilutes — the agent's next-turn signal.

---

## What problem does this solve

A naive completion-audit hook that prints `"all checks passed"` at the end of every turn does three things, all bad:

1. **Trains the agent's output channel as low-signal.** Every turn ends with a near-identical block of confirmation text. The agent's next session reads it as background noise; when a real failure fires inside the same template, it is missed.
2. **Inflates context.** Hook output rides in the same window as user input and tool results. A 12-line "all good" trailer per turn, across 30 turns, is 360 lines of context that did not earn its place ([`docs/output-craft-discipline.md`](../../../docs/output-craft-discipline.md)).
3. **Breaks the §Pre-compression protection list discipline.** When compression hits, the hook trailers are equally weighted with the actual decisions; the resumption AI cannot tell which lines are signal.

The back-pressure pattern flips this: the hook is silent unless something is wrong, and the something-is-wrong message is short, specific, and actionable.

---

## The reference shape (in pseudocode)

```bash
# hooks/completion-audit/back-pressure.sh
# Category D hook. Reads JSON event on stdin per the runtime-hook-contract.

read_event_from_stdin

manifest_path=$(jq -r '.manifest.path // empty')

# Bail-out when the hook does not apply (no manifest, or wrong phase).
# Bail-out is exit 0 silent; a hook that does not apply is not a check that passed.
if [[ -z "$manifest_path" || ! -f "$manifest_path" ]]; then
  exit 0   # silent
fi

# Collect findings into a structured array. Do NOT print anything yet.
findings=()

if has_uncollected_evidence "$manifest_path"; then
  findings+=("Phase $(read_phase) has evidence_plan items still 'planned'; collect or waive before claiming completion.")
fi

if has_unresolved_escalation "$manifest_path"; then
  findings+=("Unresolved escalation in manifest: $(first_open_escalation)")
fi

if has_residual_risk_unaccepted "$manifest_path"; then
  findings+=("residual_risks contains an unaccepted entry; review or downgrade.")
fi

# Output discipline:
#   - 0 findings  -> exit 0, silent. The user sees nothing.
#   - >=1 finding -> exit 1, one-line stderr per finding.
if [[ ${#findings[@]} -eq 0 ]]; then
  exit 0
fi

for f in "${findings[@]}"; do
  echo "$f" >&2
done
exit 1
```

The shape is not the script — it is the **output contract**: silent on success, one line per surfaced cause on failure, no preamble, no template, no recap.

---

## What the agent sees on each path

### Path 1 — the change is healthy

Hook fires. Hook computes 0 findings. Hook exits 0 with no output.

Agent's next-turn context contains the user's message and the tool-result transcript. No hook trailer, no template noise. The on-stop check happened — the agent does not need to know it happened to benefit from it.

### Path 2 — one check fails

Hook fires. Hook computes 1 finding (e.g. "evidence_plan items still planned"). Hook prints the one-line cause to stderr and exits 1.

Agent's next-turn context contains the user's message, the tool-result transcript, *and* one short stderr line: `Phase implement has evidence_plan items still 'planned'; collect or waive before claiming completion.` The agent's next reply addresses the cause directly; the channel stayed high-signal.

### Path 3 — multiple checks fail

Hook fires. Hook computes 3 findings. Hook prints 3 stderr lines, one per cause, and exits 1. Each line is short; together they fit on one screen.

The agent's next reply triages the three causes (often by addressing the highest-impact one and surfacing the others as known follow-ups). The user sees three lines, not a 90-line "running 12 checks…" log followed by 3 buried failures.

---

## The discipline in two rules

1. **Silent on exit 0.** No `"all good"`, no `"completed in 200ms"`, no `"ran N checks"`.
2. **One short line per finding on exit non-zero.** No preamble, no recap, no copy-pasted stack trace. If the finding genuinely needs more detail, write the detail to a side-channel artifact (a file under the session working space) and reference it by path in the one stderr line.

---

## Where this fits in the methodology

- **Runtime-side counterpart of [`docs/output-craft-discipline.md`](../../../docs/output-craft-discipline.md)** — both reject decorative output that does not advance the user's next decision.
- **Cross-checks against [`docs/runtime-hook-contract.md`](../../../docs/runtime-hook-contract.md) §Anti-patterns** — specifically "silent-swallow" (the wrong direction: passing without checking) and "kitchen-sink hook" (one hook, many checks, undiagnosable failure). Back-pressure is the right direction: many small hooks, each silent unless it has a cause.
- **Cross-checks against [`docs/ai-operating-contract.md`](../../../docs/ai-operating-contract.md) §Honest reporting** — a hook that prints "all good" is the runtime-side analogue of an agent that claims success without verification. Both are dishonest in the same shape.

---

## Anti-patterns this reference rejects

- *Printing the hook's own banner first ("=== back-pressure check ===")* — the banner is by definition output that earns nothing on success.
- *Returning structured JSON to stdout in addition to stderr.* The contract allows it for aggregation, but if every successful run produces JSON the agent reads, the channel is no longer high-signal. Emit JSON only on non-zero exit, mirroring stderr.
- *Building a "what we checked" file even on success.* The check happened; that fact need not be persisted. Persist only failures (and only as the side-channel artifact referenced by the one-line stderr).
- *Aggregating multiple back-pressure hooks into one wrapper that prints a final summary.* The aggregation re-introduces the template the pattern exists to eliminate. Run the hooks side by side; let each be silent or speak for itself.
