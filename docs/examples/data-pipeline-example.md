# Worked Example: Data Pipeline Schema Migration

> **English TL;DR**
> A batch/streaming data-platform change walked through the methodology: data-quality surface as first-class, freshness/lineage/completeness as evidence categories, downstream consumers (dashboards, ML features, compliance reports) as the hardest-to-notice impact area. Domain-neutral: no vendor or product names.

---

## Scenario

An event-stream schema needs to be extended:
- Add two new fields (one optional; one required with a default value).
- Downstream there are three derived pipelines, five dashboards, and two ML feature stores.
- One of the dashboards powers a regulatory monthly report.

---

## Phase 0 — Clarify

### Task type
Migration + breaking change (for downstream consumers).

### Surfaces

| Surface | Role | Description |
|---------|------|-------------|
| Information | primary | Schema extension. |
| System-interface | primary | Producer-side / consumer-side event contract. |
| **Data-quality surface** (extension) | primary | Completeness, freshness, lineage must be re-verified. |
| Operational | primary | Migration script, rollout plan, monitoring. |
| Compliance surface (extension) | primary | Monthly-report input field changes. |
| User | none | No direct UI impact. |

---

## Phase 1 — Investigate

### SoT Map

| Information | SoT | Pattern | Consumers |
|-------------|-----|---------|-----------|
| Event schema | Version files in the schema registry | Schema-Defined (pattern 1) | Producer, consumer, derived downstream |
| Field semantics (per-field meaning) | Data-contract document | Contract-Defined (pattern 4) | Analysts, ML team, compliance team |
| Data lineage | Lineage system | Contract-Defined (pattern 4) | Impact analysis, incident tracing |
| Derived-table write cadence | Scheduler config | Config-Defined (pattern 2) | Dashboard freshness |

### Consumer classification (data downstream is the easiest to miss)

- Internal synchronous: the producer service (can be redeployed).
- Internal asynchronous: three derived pipelines (some project only the old columns).
- Data downstream: five dashboards (may hard-code field names).
- Human workflows: the regulatory-report analysts (habituated to certain columns).
- ML feature store: training / serving skew risk.

---

## Phase 2 — Plan

### Breaking-change level

| Item | Level | Reason |
|------|-------|--------|
| Add optional field | L0 | Purely additive. |
| Add required field (with default) | L1 | Producer must explicitly populate; otherwise default is used. Consumers that don't handle the default can misread. |

### Rollback modes

- Schema adds a column: **mode 1 is not available** — once written, it is hard to shrink back (platform-dependent).
- In practice, use "mode 2 forward-fix": do not attempt a true rollback; fix forward with a new version.
- Data already written downstream: mode 3 compensation (use a correction script if necessary).

### Migration strategy

1. Register the new contract version in the schema registry (old + new coexist).
2. Upgrade consumers first (so they can read the new field).
3. Upgrade the producer next (start writing the new field).
4. Observe freshness / completeness metrics for one week.
5. Move the old consumer paths into the deprecation queue.

---

## Phase 3 — Test Plan

| Acceptance criterion | Verification | Evidence |
|----------------------|--------------|----------|
| No parse errors during the new + old coexistence window | Contract test | Error-rate log |
| Derived downstream tables correctly include the new field | End-to-end test | Row-count comparison + sampled comparison |
| No freshness regression | Schedule monitoring | Freshness SLA dashboard screenshot |
| Completeness (no nulls, no duplicates, no out-of-order rows) | Data-quality rule | DQ results |
| Lineage updated | Lineage-service scan | Before / after lineage-graph diff |
| Monthly-report fields unaffected (unless a field is added deliberately) | Rerun historical monthly reports | Diff between two report runs |

---

## Phase 4 — Implement

- Register the schema first. Only start writing the new field from the producer after consumers are ready.
- Control the producer upgrade's new-field write ratio via a feature flag (progressive rollout).
- Check DQ alerts every 6 hours.

**AI discipline:**
- Do not let the producer ship before the consumer in order to merge faster.
- When a DQ alert fires, stop progress immediately and investigate.

---

## Phases 5–7

- Review: verify the four evidence bundles are complete — lineage, DQ, freshness, monitoring.
- Sign-off: compliance confirms the monthly report is unaffected.
- Deliver: completion report includes the migration timeline + the old-consumer deprecation plan.

---

## Phase 8 — Post-delivery observation

- T+24h: DQ alerts, freshness, downstream job failure rate.
- T+7d: any analyst reports of "numbers look off" on the dashboards?
- T+30d: progress of old-consumer deprecation (tracked via the deprecation queue).

---

## Common pitfalls

- Thinking "additive" is safe → a consumer using `SELECT *` can break downstream schemas.
- Forgetting the ML feature store → the new field absent in training but present at serving → training/serving skew.
- Not notifying monthly-report analysts → field-meaning change discovered only when the report ships.
- Not registering into lineage → future impact analysis will miss consumers.

---

## Linkbacks to `docs/`

- `surfaces.md` — data-quality surface.
- `source-of-truth-patterns.md` — pattern 1 + pattern 4.
- `breaking-change-framework.md` — the L0 trap ("thought L0, actually L1+").
- `team-org-disciplines.md` — a downstream-data consumer registry is the lifeblood of this kind of change.
- `post-delivery-observation.md` — the T+7d / T+30d analyst-feedback window.
