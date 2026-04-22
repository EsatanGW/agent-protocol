# Subagent Dispatch Strategy

When scope is large, or an independent review or parallel investigation is needed, subagents may be used.

## Base rules

- Only independent tasks may run in parallel.
- Dependent tasks must run serially.
- Requirement / spec-compliance review and quality review cannot be skipped.

## Serial composition (Patterns 1–4)

The canonical role delegates a single scoped sub-task to a sub-agent, waits, reads the return, and continues. Valid in Full mode; see `reference-implementations/roles/role-composition-patterns.md` §Patterns 1–4 for shapes (research, code-explorer, test-writer, reference-sampler).

## Parallel composition / fan-out (Patterns 5–6)

The canonical role spawns multiple sub-agents in a single batch, then consolidates their structured returns itself. Two canonical patterns:

- **Pattern A — Phase 1 surface-parallel investigators** (Planner-owned).
- **Pattern B — Phase 5 specialized audit fan-out** (Reviewer-owned).

Full-mode only. Execution discipline (cache-window rule, context pack, fan-in synthesis, cross-cutting gap check, `parallel_groups` audit trail): [`../references/parallelization-patterns.md`](../references/parallelization-patterns.md).

### When to fan out vs. work serially

Fan out when **all** of:

- The phase is Full mode.
- The canonical role's work decomposes into 2–4 mutually independent sub-tasks.
- Runtime can spawn distinct sub-agent identities.
- The canonical role can perform fan-in synthesis itself (never delegated).

Work serially when any of:

- Lean or Zero-ceremony.
- Sub-tasks are not independent — they share state that updates incrementally.
- Synthesis cost ≥ serial execution cost (fan-out would be net-negative).
- Only one sub-agent is needed (use Pattern 1–4, not a 1-wide fan-out).

## Discipline summary

| Concern | Rule | Source |
|---|---|---|
| Canonical role writes manifest fields | Always | `role-composition-patterns.md` §The invariant |
| Sub-agent identity distinct from every canonical role | Always | `docs/multi-agent-handoff.md` §Single-agent anti-collusion rule |
| Fan-out spawned in a single tool-call batch | Parallel only | `parallelization-patterns.md` §Cache-window rule |
| Context pack shared across fan-out sub-agents | Parallel only | `../references/context-pack.md` |
| Fan-in synthesis performed by the canonical role | Parallel only | `parallelization-patterns.md` §Fan-in discipline |
| Cross-cutting gap check at fan-in | Parallel only | `parallelization-patterns.md` §Cross-cutting gap check |
| Fan-out recorded in `parallel_groups` | Parallel only | `schemas/change-manifest.schema.yaml` §parallel_groups |

Silent omission of any row is a contract escape, not a shortcut.

## Within-phase fan-out vs between-phase overlap

Sub-agent fan-out (this document) parallelizes work **within a single phase** — the canonical role spawns sub-agents, waits, fans in, and remains inside the same gate. [`../references/phase-overlap-zones.md`](../references/phase-overlap-zones.md) parallelizes **between phases** — prep for Phase N+1 starts before Phase N's gate passes, in working space, with a hard discard-on-fail rule. The two stack (a Phase 1 fan-out can finish its fan-in just as a Phase 2 change-map skeleton begins being drafted) but they solve different problems with different disciplines. Do not conflate them: fan-out does not cross phase gates, and overlap does not spawn sub-agents.
