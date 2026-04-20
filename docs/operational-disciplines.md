# Operational Disciplines

> **English TL;DR**
> Per-change checklist for the *operational surface* — the most commonly under-invested one. Four questions every delivery must answer: **who can trace it if it fails** (logs, audit, correlation id), **how is it rolled back** (rollback mode 1/2/3 plus exact steps), **what does the next handoff see** (changelog, handoff note, migration note), **where is the evidence** (test output, metric snapshot, screenshot, telemetry link). Covers per-item quality floors: structured logs (not string concat), audit trail for state-changing ops, telemetry with metric names not ad-hoc strings, changelog entries that say *why* not just *what*, migration notes that include reversal path, rollout plan with a *stop condition*. Companion to `implementation-disciplines.md` (which covers the implementation surface) and `user-surface-disciplines.md`.

This document covers the operational surface — the surface every task touches and the one most often under-invested.

## When this document applies

Almost every change will touch at least one of:

- log / audit
- telemetry / monitoring / alerting
- rollout / migration / rollback
- docs / changelog / handoff
- evidence preservation

## Questions that must be answered at delivery

- If it breaks, who can trace it?
- If it must be rolled back, how?
- If it must be handed off, what does the next person look at?
- If it must be verified, where is the evidence kept?

## Primary observation axes

### Traceable

- Critical changes leave behind operational records or diagnostic signals.
- When something goes wrong, event ordering can be reconstructed.

### Rollback-able

- The change has a reversal path or a safe degradation strategy.
- Switch points for migrations / feature flags are explicit.

### Hand-off-able

- The completion report is directly usable by whoever picks up next.
- Key decisions, constraints, and risks are recorded.

### Evidence preserved

- Verification outputs, screenshots, and payloads can be cited.
- Evidence does not vanish when the session ends.

## General review checklist

- [ ] Significant changes leave operational records.
- [ ] Outward-facing behavior changes are documented or changelog'd.
- [ ] rollout / rollback strategy can be stated.
- [ ] The completion report has genuine handoff value.

## See also

- `adoption-anti-metrics.md` — **non-normative** diagnostic aids for
  catching ceremonial adoption of the above checklist (evidence paths
  all pointing at the same artifact, `rollback.overall_mode` always 1,
  LGTM-only review notes). Not CI gates — review conversations.
- [ ] Monitoring / alerts have been adjusted where needed.
