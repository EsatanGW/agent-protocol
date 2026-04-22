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
- **Collect evidence eagerly.** Populate `evidence_plan.artifacts` as each sub-task's verification completes, not batched to the end of Phase 4. Session interrupts during implementation are common; evidence batched to the end is evidence lost on interrupt. Tier-`critical` evidence (`schemas/change-manifest.schema.yaml` §evidence_plan.tier) is highest priority for eager capture — its absence blocks Phase 6 sign-off.

## Pre-handoff self-check

Before the Implementer advances `phase: review`, the five-question self-check in `agents/implementer.md` (and `reference-implementations/roles/implementer.md`) must be cleared. This is a **role-specific** addition on top of the global self-check in `docs/ai-operating-contract.md` §10. A vague or hedged answer to any of the five questions blocks handoff — return to work or trigger the Discovery loop.

## Optional: Pattern C cluster-parallel execution (Full mode)

When the Phase 2 manifest carries a filled `implementation_clusters` field (2–4 file-disjoint clusters per [`../references/cluster-parallelism.md`](../references/cluster-parallelism.md)), Phase 4 runs as parallel cluster-implementation rather than single-Implementer serial execution. The Planner spawns one canonical Implementer per cluster in a single tool-call batch (cache-window rule). Each Implementer:

- Implements only inside its cluster's `scope_files`.
- Runs the cluster's verification and populates its `evidence_refs` entries in `evidence_plan.artifacts`.
- Flips cluster `status` through `pending → in_progress → completed`.
- On Discovery-loop trigger: flips cluster `status: blocked_discovery` and returns — all other clusters halt by default, Planner re-opens Phase 2 per `docs/phase-gate-discipline.md` Rule 6.

Implementers must **not** cross cluster boundaries. Cross-cutting issues at cluster intersections are caught by the Reviewer's cross-cluster cross-cutting gap check in Phase 5, not by any individual Implementer.

## Optional: P4 → P5 overlap zone (Full mode)

Once `surfaces_touched`, `breaking_change.level`, `rollback.mode`, and evidence-plan categories are stable, the Reviewer's **context-pack pre-distillation** (per `../references/context-pack.md`) and reference-sampler seeding for Pattern B (per `../references/parallelization-patterns.md` §Pattern B) may begin in working space. The Reviewer must **not** draft `review_notes` or approval language during overlap — those are canonical-role work-ahead and forbidden. Discard and re-distill if Phase 4 discovers a new surface or upgrades the breaking-change level (triggers Phase 1 re-entry per `docs/phase-gate-discipline.md` Rule 6). See [`../references/phase-overlap-zones.md`](../references/phase-overlap-zones.md).

## See also

- `agents/implementer.md` — role-specific handbook including Pre-handoff self-check
- `docs/ai-operating-contract.md` §10 — global self-check
- `docs/phase-gate-discipline.md` — gate rules including Rule 6 (phase re-entry) for scope changes discovered mid-implementation
- `skills/engineering-workflow/references/discovery-loop.md` — escalation flow when a plan gap is detected
- `skills/engineering-workflow/references/phase-overlap-zones.md` — prep work that Phase 5 may legitimately begin before Gate 4 closes
- `skills/engineering-workflow/references/cluster-parallelism.md` — Pattern C execution discipline when Phase 2 declared `implementation_clusters`
