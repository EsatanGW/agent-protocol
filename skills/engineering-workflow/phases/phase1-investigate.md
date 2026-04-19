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

## Gate 1

The phase passes only when:
- The impact file list is sufficiently complete.
- There is a clear recommended approach.
- Risks and trade-offs are explicitly stated.
