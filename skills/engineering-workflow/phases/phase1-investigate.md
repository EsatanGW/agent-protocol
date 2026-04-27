# Phase 1: Investigation

## Goal

Trace the real impact surface — no guesswork.

## Lean / Full minimums

### Lean minimum
- Source of truth.
- Main consumers.
- Impact file list.
- Chosen approach.

### Full minimum
- Main flow.
- Source-of-truth / consumer map.
- Impact file list.
- Candidate solutions.
- Recommended approach with trade-offs.

## Optional startup: CCKN consultation

If the change's anticipated `surfaces_touched`, libraries, third-party APIs, or platforms overlap with topics in the repo's CCKN directory (default: `docs/knowledge/`), read the matching CCKNs before tracing the main flow. No overlap → no consultation needed; absent directory → no-op. On a stale match (CCKN or any cited reference > 12 months old), the change inherits the refresh obligation. Canonical rule with match-handling and anti-patterns: [`../../../docs/cross-change-knowledge.md §When to query a CCKN`](../../../docs/cross-change-knowledge.md).

## Investigation dimensions

1. Flow — the path from source of truth to consumer.
2. Contract — fields, enums, payloads, state shape, config keys.
3. Dependency — repo / module / page / service / job / config / doc.
4. Operations — logging, audit, telemetry, migration, rollout.

## Required steps

1. Trace the main flow.
2. Search all related references across relevant file types.
3. Identify the impact list.
4. Find at least 1-2 reference patterns.
5. Summarize options and trade-offs.

## Optional: surface-parallel fan-out (Full mode, 3+ surfaces)

When the investigation spans 3+ surfaces and the serial walk has real clock cost, the Planner may fan out one investigator sub-agent per surface per Pattern A in [`../references/parallelization-patterns.md`](../references/parallelization-patterns.md). Mandatory disciplines: single-batch spawn, shared context pack, canonical-role fan-in synthesis, cross-cutting gap check, `parallel_groups` audit entry. Full-mode only — never fan out in Lean.

## Optional: P1 → P2 overlap zone (Full mode)

Once the surface list and SoT candidates are stable — even while the full impact list is still being finalized — a Phase 2 change-map skeleton (one row per surface, `work: TBD`, `order: TBD`) may begin in session-scoped working space. Constraints: no manifest field writes, ≤20% of Phase 2 work, and full discard if Gate 1 reclassifies any surface or SoT pattern. See [`../references/phase-overlap-zones.md`](../references/phase-overlap-zones.md).

## Gate 1

The phase passes only when:
- The impact file list is sufficiently complete.
- There is a clear recommended approach.
- Risks and trade-offs are explicitly stated.
