# Evidence Quality per Type

> **English TL;DR**
> The schema enumerates 18 `evidence_plan[*].type` values; this appendix specifies *what good looks like* for each one. For every type: the **artefact shape** that constitutes evidence (not just "something was done"), the **rejection signals** Reviewer should treat as cause to send back, and the typical **tier** (`critical` vs `standard`) the Planner should assign at Phase 2. Non-normative companion to [`docs/change-manifest-spec.md`](change-manifest-spec.md); the schema enum and tier semantics remain canonical there.

---

## How to use this appendix

Each section below covers one type. The structure is:

- **Artefact shape.** What the artefact must contain to count as evidence. Reviewer's audit reads against this list.
- **Rejection signals.** Three observable cues that the artefact does not actually verify what it claims. Any one is a Phase 5 send-back.
- **Default tier.** What the Planner usually assigns at Phase 2. The Reviewer may upgrade `standard` → `critical` (triggers send-back to collect more); never the reverse.

The tier defaults are *suggestions* — the change's actual risk level (per `breaking_change.level`, `rollback_mode`, and surface mix) is what governs. A `standard` default for `screenshot_diff` becomes `critical` on a UI change at L2+; a `critical` default for `migration_dry_run` stays `critical` regardless.

---

## `unit_test`

- **Artefact shape.** Test file path + assertion count + the specific assertions that exercise the change. Build / run output line showing the test passed in the change's commit.
- **Rejection signals.** (1) Test file exists but no assertion exercises the new behaviour. (2) Test passes against the old code (failed to detect that the change happened). (3) Test asserts only that the function does not throw, never on the result.
- **Default tier.** `standard` for additive changes; `critical` for behavioural changes (`breaking_change.level >= L1`).

## `integration_test`

- **Artefact shape.** Test path + the cross-component pair under test (e.g. service ↔ data layer; module A ↔ module B) + the assertion proving the integration boundary holds. Run output for the change's commit.
- **Rejection signals.** (1) The test mocks the boundary it claims to integrate against — that is a unit test in disguise. (2) The test runs only on the happy path with no negative case. (3) The test's run output is from a prior commit (commit SHA does not match `phase: implement` SHA).
- **Default tier.** `critical` when crossing surfaces (e.g. system-interface + information); `standard` when within one surface.

## `contract_test`

- **Artefact shape.** The contract artefact (OpenAPI spec, gRPC `.proto`, GraphQL schema, JSON Schema, IDL) + the test that asserts request / response shapes against it + a run line showing both producer and consumer satisfy the contract.
- **Rejection signals.** (1) Only one side of the contract is tested (producer-only or consumer-only). (2) The contract artefact is in source but the test does not load it; the test re-encodes the shape inline. (3) A field added to the contract has no corresponding assertion.
- **Default tier.** `critical` whenever the system-interface surface is `primary`.

## `e2e_test`

- **Artefact shape.** End-to-end scenario name + the user flow it traverses + the build configuration the test ran under (release, not debug — see [`docs/cross-cutting-concerns.md`](cross-cutting-concerns.md) §Build-time-risk) + the run output.
- **Rejection signals.** (1) The test runs under debug-only configuration. (2) The flow asserts only on intermediate steps, never on the user-visible outcome. (3) The test depends on a fixture / seed that has been mutated since the test was written, so the assertion no longer reflects current intent.
- **Default tier.** `critical` for user-surface changes; `standard` otherwise.

## `screenshot_diff`

- **Artefact shape.** Before image + after image + the change's commit pair (before-commit + after-commit). Coverage: at least the **happy state**, the **error state**, and one **state transition** if the change affects state ([`docs/cross-cutting-concerns.md`](cross-cutting-concerns.md) §Application-driven verification).
- **Rejection signals.** (1) Only the after image is attached; no before image to compare against. (2) The before image is from production (uncontrolled) rather than the immediate pre-change state. (3) The image lacks the change's region — wrong scope, decorative.
- **Default tier.** `critical` for user-surface changes; `standard` for trivial (typo / single-string) changes.

## `interaction_recording`

- **Artefact shape.** Recording file path + the user flow the recording traverses + the assertion list (what the recording proves: "click here, observe X" / "type N, observe Y"). Pause and play points are recoverable from the recording.
- **Rejection signals.** (1) Recording does not include the change's region (the click that triggers the changed behaviour is off-screen or unclicked). (2) Recording is from a different scenario than the change addresses. (3) Recording quality (resolution, framerate) is too low to verify the assertion.
- **Default tier.** `standard` (interaction recordings supplement screenshot diffs; alone they rarely carry critical weight).

## `api_proof`

- **Artefact shape.** Request payload + response payload + status code + the headers that matter (auth, content-type, correlation ID) + the environment (staging / production-equivalent / production). Captured against the change's commit.
- **Rejection signals.** (1) The proof was captured against the *old* code path — the API call was made before the change was deployed. (2) The proof is missing the auth header — anonymous calls do not exercise the change's auth path. (3) The response payload's commit SHA / version field does not match the change's commit.
- **Default tier.** `critical` for system-interface surface as `primary`; `standard` when system-interface is `consumer`.

## `migration_dry_run`

- **Artefact shape.** Dry-run command + dry-run output + the affected tables / collections / indexes + the rollback path tested in the same dry-run + the runtime version of the migration tool. Coverage: 100% of declared affected tables.
- **Rejection signals.** (1) The dry-run runs only the forward path; rollback is untested. (2) The dry-run is on a tiny subset of the affected data — no cardinality stress. (3) The dry-run output is empty (the tool ran but produced no diff — usually means it ran against the wrong target).
- **Default tier.** `critical` always (information-surface migrations are inherently high-impact).

## `query_plan`

- **Artefact shape.** The query (verbatim) + the `EXPLAIN` / `EXPLAIN ANALYZE` output + the index list the query relies on + the row-count estimate (planner) and actual (executor) when available.
- **Rejection signals.** (1) The plan shows a sequential scan on a hot path with no acknowledgement (no waiver). (2) The plan was captured on a tiny test database; the row counts are not representative. (3) The query in the artefact differs in even a comma from the query in the change — the plan is for a different query.
- **Default tier.** `critical` when the change adds or modifies a hot-path query; `standard` for a one-off backfill / report query.

## `log_sample`

- **Artefact shape.** Log query + the time window + the matching log lines (≤ 20, with structured fields visible) + the field-level assertion (which field's presence / value is the proof) — see [`docs/cross-cutting-concerns.md`](cross-cutting-concerns.md) §Application-driven verification.
- **Rejection signals.** (1) The sample is "see the deployment dashboard" — no captured lines. (2) The captured lines lack the change's `correlation_id` or equivalent — they could be from any concurrent change. (3) The log was captured from debug environment but the change targets production / production-equivalent.
- **Default tier.** `standard` for additive logging; `critical` for changes whose verification depends on a new log/event firing.

## `metric_diff`

- **Artefact shape.** Metric name + before window + after window + the difference (with units) + the change-window timestamp that separates them. Confidence: the difference is outside the metric's noise band.
- **Rejection signals.** (1) The before/after windows overlap or are too short to be statistically meaningful. (2) The metric was renamed at deploy; the before-name and after-name are different metrics, not a diff. (3) The diff is within the metric's noise floor and is being reported as a real change.
- **Default tier.** `critical` when the change is performance-driven; `standard` for additive metrics.

## `playtest_result`

- **Artefact shape.** Per [`docs/playtest-discipline.md`](playtest-discipline.md): rubric scores per dimension + sample size + composition + baseline comparison (`baseline.type`) + verdict per dimension (`improved` / `noise` / `acceptable_regression` / `blocking_regression`).
- **Rejection signals.** (1) Sample size below the rubric's `session_minimum_runs`. (2) Baseline is "designer_intent" with no documented intent. (3) Any dimension's verdict is `blocking_regression` and the change has no compensating waiver.
- **Default tier.** Set by the playtest level (`L2` / `L3` are typically `critical`; `L0` / `L1` are `standard`).

## `security_scan`

- **Artefact shape.** Scanner name + scanner version + ruleset version + scan target (commit SHA) + findings list (severity + CVE / CWE / rule ID + locator) + suppressions with rationale.
- **Rejection signals.** (1) Scanner version older than 6 months — ruleset is stale. (2) High-severity finding is suppressed without a rationale entry. (3) The scan target's commit does not match the change's commit (scan was of pre-change code).
- **Default tier.** `critical` for any auth / PII / secret-touching change; `standard` for changes that do not cross those surfaces.

## `load_test`

- **Artefact shape.** Load profile (RPS / concurrency / payload distribution) + duration + result distribution (p50 / p95 / p99) + comparison against budget or baseline + the test environment's spec.
- **Rejection signals.** (1) The load test ran against a single-machine target while production is multi-node — the result does not transfer. (2) Duration too short (< 60 seconds for steady-state metrics). (3) p99 results omitted because "they were too noisy" — the omission itself is the rejection signal.
- **Default tier.** `critical` for changes whose verification depends on capacity claims; `standard` otherwise.

## `build_artifact`

- **Artefact shape.** Build configuration (release vs debug) + the artefact's hash / signature / size + the source commit it was built from + the build environment (CI run ID + base image / SDK version).
- **Rejection signals.** (1) Build is from debug configuration when the change has release-only behaviour (per [`docs/cross-cutting-concerns.md`](cross-cutting-concerns.md) §Build-time-risk). (2) Build hash is missing — reproducibility is lost. (3) Build was produced manually on a developer machine for a release change.
- **Default tier.** `critical` for changes that touch shrinker / minifier / AOT / asset-pipeline; `standard` otherwise.

## `changelog_entry`

- **Artefact shape.** The CHANGELOG entry text + the version number + the section (Added / Changed / Deprecated / Removed / Fixed / Security) + the file path.
- **Rejection signals.** (1) Entry exists but the version is unreleased and no plan to release it (entry is decorative). (2) Entry is in the wrong section (a `Removed` entry placed under `Changed`). (3) Entry is missing for a `breaking_change.level >= L2` change.
- **Default tier.** `standard` for L0–L1; `critical` for L2+ (a missing changelog entry on L2+ is a Reviewer-blocking gap).

## `runbook_update`

- **Artefact shape.** Runbook file path + the section that was edited + the new alert / response / escalation row + the alert rule the runbook now covers.
- **Rejection signals.** (1) Update is generic ("watch for errors") with no actionable steps. (2) Update references an alert that was not created in this change (orphan runbook). (3) Update is in a runbook that no on-call rotation reads.
- **Default tier.** `critical` whenever the change adds an alert / monitor; `standard` for documentation-only updates.

## `reconciliation_report`

- **Artefact shape.** The reconciliation query / job + the discrepancy count (before / after the change) + the per-row reason classification + the report's run timestamp.
- **Rejection signals.** (1) Report shows zero discrepancies but the change touched a known-divergent path — likely a query bug. (2) Discrepancy classification is "unknown" for a non-trivial fraction. (3) Report was generated from a sample, not the full population, without acknowledgement.
- **Default tier.** `critical` for SoT pattern 7 (Temporal-Local) and pattern 8 (Dual-Representation) changes; `standard` otherwise.

---

## Cross-type rules

These apply to **every** evidence row regardless of type:

- **Provenance.** Every row's `artifact_location` must point at a path / URL captured from the change's commit (or a clearly-named successor). An artefact captured from a *different* commit is not evidence of *this* change. The forthcoming evidence-provenance check ([`docs/automation-contract.md`](automation-contract.md) Tier 2) is the mechanical enforcement.
- **Tier monotonicity.** The Reviewer may upgrade `standard` → `critical` (which triggers send-back); the Reviewer may not downgrade `critical` → `standard` (that would let critical evidence be waived).
- **Surface alignment.** The `surface` field must be one of the surfaces actually `touched` in `surfaces_touched[]` with `role` = `primary` or `consumer`. Evidence on an `incidental` surface is decorative.
- **Status truth.** `status: collected` requires `artifact_location` to resolve and `collected_at` to be set. A row marked `collected` with a missing path is a state-snapshot violation; the back-pressure pattern's evidence hook ([`docs/runtime-hook-contract.md`](runtime-hook-contract.md) §Category B) is the runtime-side enforcement.

---

## Anti-patterns

- *Decorative evidence.* The artefact exists but does not exercise the change. Most common in `unit_test` and `screenshot_diff`. Reviewer's sampling right exists for this case.
- *Stale evidence.* The artefact was captured against an earlier commit. The provenance rule is the cure.
- *Coverage-by-counting.* "We have 12 evidence rows" — none of which actually targets the surface that changed. Surface alignment is the cure.
- *Tier inflation.* Marking everything `critical` to look thorough. Reviewer-side cure: trust upgrades, distrust unchanged tiers when the change's risk dropped.
- *Tier compression.* Marking everything `standard` to ease delivery. Reviewer-side cure: never accept a `standard` tier on a `breaking_change.level >= L2` change without an explicit waiver.

---

## Relationship to other documents

- [`docs/change-manifest-spec.md`](change-manifest-spec.md) §`evidence_plan` — the schema-canonical home of the type enum and tier semantics.
- [`docs/automation-contract.md`](automation-contract.md) — the Tier 2 cross-reference layer where evidence-provenance and tier-monotonicity checks live.
- [`docs/runtime-hook-contract.md`](runtime-hook-contract.md) §Category B — the runtime-side enforcement: the artefact path resolves, the file is well-formed.
- [`docs/cross-cutting-concerns.md`](cross-cutting-concerns.md) §Application-driven verification — the surface-mapping that says which evidence types must be application-driven for which surfaces.
- [`docs/playtest-discipline.md`](playtest-discipline.md) — the canonical home for the `playtest_result` rubric semantics.
- [`docs/repo-as-context-discipline.md`](repo-as-context-discipline.md) — the discipline that says external evidence (Slack-link "we tested it") must be transcoded into a repo-resident artefact before it counts.
