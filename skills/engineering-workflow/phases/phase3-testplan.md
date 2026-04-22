# Phase 3: Test Plan

## Goal

Turn acceptance criteria into executable test cases plus an evidence plan.

## Lean / Full minimums

### Lean minimum
- Minimal verification table.
- Public-behavior coverage.
- Evidence expectations.

### Full minimum
- Full test plan.
- Acceptance mapping.
- Evidence methods.
- Explicit regression coverage.

## Test categories

Select based on the actual affected surfaces:
- Visible behavior.
- Interaction / validation.
- Contract / payload.
- Storage / schema.
- Operations / logging / audit.
- Documentation.
- Regression.

## Optional: P3 → P4 overlap zone (Full mode)

Once test categories are declared, the Phase 4 **baseline verification environment** — test harness scaffold, CI branch, screenshot baseline, metric snapshot — may be prepared in working space before Gate 3 closes. Implementation code is **not** permitted. Discard the harness setup if Phase 3 changes the verification method for any critical-path AC. See [`../references/phase-overlap-zones.md`](../references/phase-overlap-zones.md).

## Gate 3

The phase passes only when:
- Test coverage is sufficient to support implementation.
- Evidence expectations are explicit.
