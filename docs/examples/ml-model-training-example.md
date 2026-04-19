# Worked Example: ML Model Training & Deployment

> **English TL;DR**
> Walks a realistic AI/ML delivery through the methodology: model surface as a first-class SoT, eval harness as a primary consumer, prompt / weight / training data as dual-representation SoT, and compensation rollback for behavior that cannot be undone. Domain-neutral: does not name any ML framework, trainer, or serving platform.

---

## Scenario

An already-deployed classification model is being upgraded:
- Architecture is unchanged; training data is expanded and the model is re-trained.
- The inference endpoint gains one new input feature column.
- Online traffic will be shifted 5% → 25% → 100%.
- A downstream batch analytics pipeline aggregates this model's output.

---

## Phase 0 — Clarify

### Task type
Feature + migration + rollout-sensitive.

### Affected surfaces

| Surface | Role | Description |
|---------|------|-------------|
| System-interface | primary | Inference API input-field change. |
| Information | primary | Training-dataset schema extension. |
| **Model surface** (extension) | primary | Weights, eval results, inference graph change. |
| Operational | primary | Rollout ratio, monitoring metrics, rollback strategy. |
| User | consumer | Inference outputs indirectly affect UI display. |
| Compliance (extension) | consumer | If the data-collection path touches PII, it must be re-reviewed. |

### Open questions

- Does the training dataset contain PII? If yes, upgrade compliance to primary.
- Can the downstream batch pipeline tolerate a small shift in output distribution?
- How long must the old model be kept as an A/B reference?

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Pattern | Consumers |
|-------------|-----|---------|-----------|
| Training data schema | Dataset version manifest | Schema-Defined (pattern 1) | Training pipeline, eval harness |
| Model weights | Specific version in the registry | Dual-Representation (pattern 8) | Inference serving, eval harness |
| Inference API contract | API spec file | Contract-Defined (pattern 4) | Clients, downstream batch pipeline |
| Eval criteria | Eval-harness configuration | Config-Defined (pattern 2) | Release gate |
| Rollout ratio | Flag service | Config-Defined (pattern 2) | Routing layer |

**Key point: the model surface's SoT is the triple of "weights + training config + dataset snapshot."**
Weights alone cannot reproduce the model; if any of the three is missing, this model cannot be audited.

### Consumer classification

- Internal synchronous: inference serving (can be redeployed).
- Internal asynchronous: batch analytics pipeline (needs historical re-runs).
- Data downstream: reporting dashboards, anomaly-detection dashboards (may false-alert if output distribution shifts).
- Human workflows: customer-support UIs that show model predictions, where SOPs depend on "if this class of prediction is elevated, escalate to a human."

### Key SoT pattern: dual-representation extension

The training-phase SoT (notebook + config + dataset) and the inference-phase SoT (deployed weights + graph)
are two representations separated by the "training run + registry push" step.

Anti-pattern: hot-fixing production weights directly (e.g. manually tweaking bias) —
this bypasses the editor representation, and the fix disappears the next time the runtime is rebuilt from training.

---

## Phase 2 — Plan

### Breaking-change level

| Item | Level | Reason |
|------|-------|--------|
| Inference API adds an input field | L2 | Old clients won't pass it — needs a default or forward-compatibility strategy. |
| Small output-distribution shift | L1 | Same shape, semantic drift of ε — downstream may false-alert. |

### Rollback modes

| Component | Mode | Notes |
|-----------|------|-------|
| Serving traffic routing | Mode 1 | Flip the flag to 0% to revert. |
| Already-emitted predictions | Mode 3 | Predictions already written downstream or used to trigger notifications cannot be recalled — compensate. |
| Model registry | Mode 1 | Old version is retained; it can be re-pointed. |

### Threat modeling (per `security-supply-chain-disciplines.md`)

- **Information leakage:** does the training data include PII? → dataset scan must pass first.
- **Tampering:** model-file integrity (checksum) must be verified both in the registry and in serving.
- **Supply chain:** base images and pre-trained checkpoint versions used during training must be recorded in the SoT map.

### Verification strategy (Phase 3 details below)

- Offline eval (full eval-harness run on the test set).
- Online shadow (shadow traffic comparing new vs old outputs).
- Canary 5% first, then decide whether to continue.
- Re-run the downstream batch pipeline over the last 7 days of history and compare aggregated output deltas.

---

## Phase 3 — Test Plan

| Acceptance criterion | Verification | Evidence |
|----------------------|--------------|----------|
| New-model eval metrics ≥ old model | Full eval harness run | Eval report + side-by-side table |
| No more than 5% inference-latency regression | Load test | P50 / P95 / P99 latency table |
| Shadow output deviation matches expectation | Shadow comparison | Distribution plot + KS statistic |
| Downstream batch-aggregate delta below threshold | Historical re-run | Before / after comparison report |
| No PII-scanner failures | Dataset scan | Scan report |
| No high/critical supply-chain findings | Dependency scan | Scan report |

---

## Phase 4 — Implement

- Training pipeline produces the new version → push to registry.
- Deploy to serving with the flag initially at 0%.
- Shadow compare for one week.
- Ramp 5% → 25% → 100% with at least 24h observation per step.

**AI discipline:**
- Do not unilaterally raise the rollout ratio (this is a rollback-sensitive decision — a human must approve).
- Stop the upgrade on training anomalies (loss NaN, sharp eval regression).
- Do not manually edit deployed weights (dual-representation anti-pattern).

---

## Phases 5–7: Review / Sign-off / Deliver

- Review focus: the evaluation report was actually executed (not estimated), and the shadow comparison has sufficient statistical significance.
- Sign-off: compliance confirms the dataset meets requirements.
- Completion report: attaches three evidence bundles — eval + shadow + latency.

---

## Phase 8 — Post-delivery observation

Timeline:
- T+24h: error rate, model-confidence distribution, whether downstream alert volume increased.
- T+72h: feedback from human-workflow consumers about unusual patterns.
- T+7d: overall business metrics (conversion / accuracy feedback).
- T+30d: long-horizon distribution drift, whether the next training round should start.

**Phase 8 is the core observation loop for ML systems — shipping the model is the start, not the end.**

---

## Common pitfalls

- Treating "eval passed" as "cleared for launch" → eval is a lower bound; shadow and canary prove the real world.
- Only watching accuracy, not distribution → the classic L1 behavioral-change miss.
- Forgetting to re-run the downstream batch → mixing historical reports with new predictions misleads readers.
- Overlooking "customer-support SOPs" as consumers → changes in model-confidence distribution silently break escalation rules.

---

## Linkbacks to `docs/`

- `surfaces.md` — model-surface extension + compliance surface.
- `source-of-truth-patterns.md` — pattern 8 dual-representation, ML variant.
- `breaking-change-framework.md` — L1 vs L2 judgment.
- `rollback-asymmetry.md` — the mode 1 + mode 3 combination.
- `security-supply-chain-disciplines.md` — data + supply-chain discipline.
- `post-delivery-observation.md` — long-horizon observation is mandatory for ML, not optional.
