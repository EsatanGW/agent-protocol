# Phase 2: Change Plan

## Goal

Turn the investigation into an executable step-by-step plan.

## Lean / Full minimums

### Lean minimum
- Minimal task list.
- Verification plan.
- Risk note.

### Full minimum
- Overview.
- Affected surfaces.
- Change map.
- Dependency order.
- Full tasks.
- Verification strategy.
- Spec-coverage matrix.

## Built-in steps

1. Change map.
2. Bite-sized tasks.
3. Dependency order.
4. Verification plan per task.
5. Standards self-review.

## Optional: P2 → P3 overlap zone (Full mode)

When acceptance criteria from Phase 0/1 are stable, a Phase 3 test-plan skeleton (one row per AC, `method: TBD`, `evidence: TBD`) may be drafted in working space before Gate 2 closes. Constraints: no manifest writes, ≤20% of Phase 3 work, discard if Phase 2 adds new ACs not in the Phase 1 draft. See [`../references/phase-overlap-zones.md`](../references/phase-overlap-zones.md).

## Optional: declare implementation clusters for Pattern C (Full mode)

If the Phase 2 tasks decompose into 2–4 file-disjoint, independent work bundles (e.g. DB migration + API field + frontend copy + telemetry dashboard), declare them in the manifest's `implementation_clusters` before Gate 2 closes. Each cluster names `scope_files` (pair-wise disjoint across clusters), `independence_rationale`, `task_refs`, and `evidence_refs`. At Phase 4 the Planner will spawn one canonical Implementer per cluster in a single batch. A hand-wavy `independence_rationale` is a signal that the clusters are not actually independent — serialize instead. See [`../references/cluster-parallelism.md`](../references/cluster-parallelism.md).

## Gate 2

The phase passes only when:
- The implementation order is explicit.
- The verification method is explicit.
- Risks and dependencies are clearly written down.
