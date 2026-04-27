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
| Sub-agent return is pointers + ≤500-word summary + verdict, not full bodies | All patterns 1–6 | `../references/context-pack.md` §Return discipline — pointers, not transcripts |

Silent omission of any row is a contract escape, not a shortcut.

### Return format — pointers, not transcripts

The last row of the discipline table is the most often violated and the cheapest to detect: a sub-agent that returns a 2 000-word write-up with pasted file bodies has either (a) been given a too-large scope, or (b) been allowed by the parent to use the slot as a free-form journal. Both are pack design failures, not sub-agent failures.

The canonical-role's Task Prompt to the sub-agent must declare the return-slot shape from `references/context-pack.md` §Return discipline (≤500-word summary, `filepath:line` pointers not bodies, structured verdict, ≤5 citations per finding). The fan-in step must reject — not silently digest — returns that violate the shape. A return that violates the shape is the sub-agent answer to a different, larger question; the canonical role must either narrow the question or split the sub-agent invocation, not let the parent context absorb the over-large return.

## Pattern C — canonical-role multi-delegation (not sub-agent fan-out)

This document covers **non-canonical sub-agent composition** — a canonical role spawns helpers that return findings. Pattern C in [`../references/cluster-parallelism.md`](../references/cluster-parallelism.md) is a **different mechanism**: the Planner spawns 2–4 **canonical Implementer identities** in parallel for file-disjoint Phase 4 clusters. Each spawned Implementer has the full canonical envelope and writes its own cluster's code + evidence directly. The disciplines in this file (sub-agents return findings, canonical-role synthesizes, sub-agents inherit read-only envelope) apply to Patterns 1–6 but not to Pattern C. Do not conflate the two: Pattern C spawns canonical roles; this file's patterns spawn non-canonical helpers.

## Within-phase fan-out vs between-phase overlap

Sub-agent fan-out (this document) parallelizes work **within a single phase** — the canonical role spawns sub-agents, waits, fans in, and remains inside the same gate. [`../references/phase-overlap-zones.md`](../references/phase-overlap-zones.md) parallelizes **between phases** — prep for Phase N+1 starts before Phase N's gate passes, in working space, with a hard discard-on-fail rule. The two stack (a Phase 1 fan-out can finish its fan-in just as a Phase 2 change-map skeleton begins being drafted) but they solve different problems with different disciplines. Do not conflate them: fan-out does not cross phase gates, and overlap does not spawn sub-agents.

## Long-running invocations

A sub-agent invocation expected to exceed one prompt-cache window (commonly ~5 minutes) needs additional **time-axis** discipline beyond spawn + synthesize: checkpoint-bounded scope (split long work into reviewable segments), artifact-grounded progress (sub-agent writes to a session-scoped Rule-5a path the canonical role and user can inspect), and the canonical-role non-idle rule (no silent wait — concurrent work or a defined polling plan). Applies across patterns: serial composition (Patterns 1–4), parallel fan-out (Patterns 5–6), and canonical-role multi-delegation (Pattern C / Pattern 7). Orthogonal to the spawn / synthesis disciplines in this document and to the between-phase overlap discipline — a single delegation can be subject to all three layers at once. Full mode only; the patterns this document governs are all Full-only. See [`../references/long-running-delegation.md`](../references/long-running-delegation.md).
