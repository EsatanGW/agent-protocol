# Phase 4: Implementation

## Goal

Execute the approved plan, and run appropriate verification on every affected surface.

## Lean / Full minimums

### Lean minimum
- Implement the tasks.
- Verify the changed behavior.
- Save the minimum evidence.

### Full minimum
- Implement against the approved plan.
- Run the full test plan.
- Collect evidence systematically.
- Write the test report.

## Built-in steps

1. Baseline verification.
2. Implement in task order.
3. Complete verification.
4. Collect evidence.

## Rules

- Do not verify only the surface you're most familiar with.
- Do not skip the cross-surface flow verification.
- No evidence = not tested.
- Every fix re-runs the affected verification.

## Pre-handoff self-check

Before the Implementer advances `phase: review`, the five-question self-check in `agents/implementer.md` (and `reference-implementations/roles/implementer.md`) must be cleared. This is a **role-specific** addition on top of the global self-check in `docs/ai-operating-contract.md` §10. A vague or hedged answer to any of the five questions blocks handoff — return to work or trigger the Discovery loop.

## See also

- `agents/implementer.md` — role-specific handbook including Pre-handoff self-check
- `docs/ai-operating-contract.md` §10 — global self-check
- `docs/phase-gate-discipline.md` — gate rules including Rule 6 (phase re-entry) for scope changes discovered mid-implementation
- `skills/engineering-workflow/references/discovery-loop.md` — escalation flow when a plan gap is detected
