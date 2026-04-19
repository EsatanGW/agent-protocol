# Change Manifest Spec

> **English TL;DR**
> The methodology's **machine-readable output contract**. Every non-trivial change produces one YAML manifest that records: which surfaces are touched, which SoT patterns apply, whether breaking-change levels (L0-L4) apply, rollback mode (1/2/3), evidence artifacts, decomposition links (`depends_on` / `blocks` / `co_required` / `part_of`), phase-specific extensions (`implementation_notes`, `review_notes`, `approvals`, `handoff_narrative`), and `waivers` (time-bounded, human-approver-only). The manifest is validated by the automation contract (see `automation-contract-algorithm.md`) at three layers: structural (schema conformance), cross-reference (SoT/surface coverage, deprecation-timeline presence, human-approval requirement for deliver phase), and drift (declared-SoT-must-be-modified, surface ↔ file pattern match via bridge mapping). Canonical schema: `schemas/change-manifest.schema.yaml` (JSON Schema draft 2020-12). Templates: `templates/change-manifest.example-*.yaml`.

> **Purpose:** the Change Manifest is the methodology's **machine-readable output contract**.
> It records — as YAML that both AI agents and CI can inspect — what surfaces this change touches, which SoTs apply, whether this is a breaking change, how it rolls back, and what the evidence is.
>
> This document is the **field-level semantic specification** for that schema — it says which field corresponds to which discipline in the methodology.
>
> **Schema file:** `schemas/change-manifest.schema.yaml` (JSON Schema draft 2020-12)
> **Examples:** `templates/change-manifest.example-*.yaml`

---

## Why a Change Manifest

The methodology's prose docs (surfaces, SoT patterns, cross-cutting, breaking change, rollback, …) describe "what to think about." Without a **fixed output format**, three things keep degrading:

1. **AI output shape drifts every time** — sometimes a list, sometimes prose; nothing automatable.
2. **CI cannot gate** — a human must eyeball each PR to judge whether the methodology was followed.
3. **Agents can't hand off** — an upstream agent's output is unintelligible downstream.

The manifest compresses "the methodology's thinking result" into a YAML with fixed fields. That turns it into:
- The AI's output contract (which fields must be filled, and under what conditions fields become required).
- The CI gate point (schema failure blocks).
- The hand-off format between agents (upstream manifest is downstream input).

---

## One manifest per change

**Principle: one change, one manifest.** Do not pack unrelated changes into the same file.

- `change_id` is a stable identifier in the form `YYYY-MM-DD-short-slug`.
- `supersedes` lets a new manifest replace / extend an older one (never edit a manifest that has already been delivered).
- `phase` is advanced as the change progresses (clarify, investigate, plan, test_plan, implement, review, signoff, deliver, observe).

---

## Top-level field semantics

### `change_id` / `title` / `phase` / `status`

- `phase` corresponds to the eight phases defined in `docs/product-engineering-operating-system.md`.
- `status` is the human workflow state (draft / in_progress / delivered, …), orthogonal to `phase`.
- `title` is a **description**, not marketing copy. `"Add optional expiry_at to Voucher API"` is good; `"Make vouchers more useful"` is not.

### `authors`

Each author has `role: human | ai`.
AI authors **must** fill in `identifier` (model ID, agent name), so the particular AI version that produced the manifest is traceable.

> Maps to `docs/ai-operating-contract.md` §0: AI outputs must be attributable.

### `supersedes` / `last_updated`

When a change advances, don't silently overwrite earlier decisions in the same manifest — update `last_updated`, and when a decision truly pivots, create a new `change_id` and link back via `supersedes`.

---

## `surfaces_touched` — surface identification

Maps to `docs/surfaces.md`.

Each entry has three fields:

| Field | Description |
|-------|-------------|
| `surface` | Core four surfaces + the nine extension surfaces + `custom` (must be registered in `stack-bridge.md`). |
| `role`    | `primary` (origin of the change / where the SoT lives) / `consumer` (must sync because of `primary`) / `incidental` (touched in passing, not load-bearing). |
| `notes`   | One sentence describing what actually changed on that surface. |

### Rules for judging `role`

- **primary** — if this surface is not changed, the change has no point.
- **consumer** — must sync because a primary changed; not syncing would desync.
- **incidental** — pure documentation / comment / record — no behavior impact.

> A change **must have at least one `primary` entry**; otherwise there is no real source for it. CI warns.

### `custom` surface

If your stack has a domain concern that does not fit into the four core + nine extension surfaces, register it in `stack-bridge.md` and then use `custom` + `custom_name`.
The schema enforces that `custom` requires `custom_name`.

---

## `uncontrolled_interfaces` — uncontrolled external dependencies

Maps to `docs/surfaces.md` §controllable vs uncontrollable.

List the **third-party / platform / upstream APIs** this change depends on.
Even if you are not modifying them, list them — because they will change on you.

- `kind`: `third_party_sdk | platform_os | store_policy | upstream_api | regulation`
- `known_deprecation`: if you know a deprecation is coming, write the timeline.
- `monitoring_channel`: where you subscribe to their release notes / advisories.

> Fill this block during Phase 1 (investigate). An empty array means "I have thought about it and there are no uncontrolled deps"; a missing field means "I forgot to consider this." Those are not the same.

---

## `sot_map` — source-of-truth map

Maps to `docs/source-of-truth-patterns.md` (10 patterns + the 4a pipeline sub-type).

Each entry requires:

| Field | Description |
|-------|-------------|
| `info_name` | What this piece of information is (`voucher.expiry_at`, `rarity enum`, `pull contract`). |
| `pattern`   | `1`–`10` or `"4a"`, corresponding to an SoT pattern. |
| `source`    | Which file / system holds the authoritative definition. |
| `consumers` | Who reads this information (code / pipeline / human / external / cache / search / docs). |
| `desync_risk` | `low / medium / high`. |

### Pattern-specific extension fields (conditionally required)

Some patterns have additional required structures (the schema enforces these via `if/then/allOf`):

| Pattern | Extension field | Purpose |
|---------|-----------------|---------|
| 6 Transition-Defined | `transition_guard` | List permitted state transitions + guard points. |
| 7 Temporal-Local     | `temporal_local`   | Record promotion trigger, conflict policy, offline scope. |
| 8 Dual-Representation| `dual_representation` | Record editor_form / runtime_form / sync_step / ci_sync_check. |
| 9 Resolved/Variant   | `variant_resolution` | List candidates, resolution_rule, override layers. |
| 10 Host-Lifecycle    | `host_lifecycle`   | Record host_type, death triggers, persisted layer, restoration path. |
| 4a Pipeline-Order    | `pipeline_order`   | List stages, declared constraints, declaration file. |

> These extension fields are not decoration — they express the concrete discipline the methodology imposes on the pattern.
> For example, pattern 8 requires `ci_sync_check: true`, which directly maps to "codegen artifacts must be committed and verified in CI."

### Judging `desync_risk`

- `low` — CI check + synchronous sync (schema gen, contract test).
- `medium` — batch / near-real-time sync, or a manual sync step.
- `high` — manual / human_process, or crosses system / organizational boundaries.

---

## `cross_cutting` — the six concerns

Maps to `docs/cross-cutting-concerns.md`.

Six fixed fields: `security / performance / observability / testability / error_handling / build_time_risk`.
Each is a `ccDimension` object (`$defs/ccDimension`):

```yaml
impact: none | low | medium | high
notes: "one-sentence"
checklist_items_touched:
  - "ref to a checklist item in cross-cutting-concerns.md"
```

### Dimension-specific sub-fields

| Dimension | Sub-fields | Discipline it maps to |
|-----------|------------|-----------------------|
| performance   | `budget` | Make p95 / memory / frame budgets explicit. |
| observability | `new_events` / `new_dashboards` | Prevent "changed but forgot to add telemetry." |
| testability   | `test_levels` (includes `playtest`) | Force explicit thought about verification levels. |
| error_handling| `classification_updated` / `cancellation_propagation_reviewed` | Cancellation and context-propagation discipline. |
| build_time_risk | `codegen_touched` / `codegen_artifacts_committed` / `minification_rules_touched` / `asset_pipeline_touched` / `determinism_considerations` / `release_build_verified` | Build-time risk. |

### Top-level conditional rules (schema-enforced)

- If `codegen_touched: true`, then `codegen_artifacts_committed` and `release_build_verified` become required.
- `cancellation_propagation_reviewed` recommendation: set `true` whenever long-running asynchronous work is involved.

---

## `breaking_change` — L0 to L4 assessment

Maps to `docs/breaking-change-framework.md`.

```yaml
breaking_change:
  level: L0 | L1 | L2 | L3 | L4
  self_assessed_vs_worst_case: matches | escalated | unresolved
  affected_consumers: [...]
  migration_path: none | gray_rollout | parallel_switch | deprecation_cycle | rename_and_coexist | custom
  migration_plan: "..."               # required for L2+
  deprecation_timeline: {...}         # required for L3+
```

### `self_assessed_vs_worst_case`

The methodology insists on **worst-case grading**. This field forces the AI / author to answer honestly:

- `matches` — first-pass assessment was already the worst case.
- `escalated` — initially assessed lighter; after analysis, escalated.
- `unresolved` — cannot determine yet; a human must judge.

### Conditional required-ness

- `L2+` → `migration_plan` + `affected_consumers` required.
- `L3+` → `deprecation_timeline` required.
- `L4` → `migration_path` restricted to `rename_and_coexist | deprecation_cycle`.

> `L4 (Semantic Reversal)` cannot use parallel_switch, because the same name cannot simultaneously mean two things.

---

## `rollback` — the asymmetry

Maps to `docs/rollback-asymmetry.md`.

```yaml
rollback:
  overall_mode: 1 | 2 | 3
  per_surface_modes: [...]
  long_lived_client_notes: "..."      # required when long-lived clients are involved
  kill_switch: { available, mechanism, tested }
  compensation_plan: "..."             # required when overall_mode == 3
```

The three modes:

| Mode | Name | Typical scenario |
|------|------|------------------|
| 1 | Reversible         | Blue/green, feature flag, config revert. |
| 2 | Forward-Fix        | Shipped clients, migration already run, cache already written. |
| 3 | Compensation Only  | Notifications already sent, payments already charged, physical goods shipped, rewards granted. |

### Conditional rules

- `overall_mode == 3` → `compensation_plan` required.
- If `surfaces_touched` includes `real_world` with `role == primary` → `overall_mode` must be `3`
  (schema-enforced; real-world side effects cannot be rolled back).
- If long-lived clients are involved (iOS/Android apps, desktop, game binaries) → `long_lived_client_notes` required.

### `per_surface_modes`

Different surfaces may have different rollback difficulty (config is reversible; real_world is not).
Record the mode per surface so the reviewer can see the least-reversible face.

---

## `evidence_plan` — Phase-6 sign-off evidence

Maps to `docs/ai-operating-contract.md` §3.

Each evidence entry:

```yaml
- type: unit_test | contract_test | screenshot_diff | migration_dry_run | playtest_result | ...
  surface: "which surface this is for"
  status: planned | in_progress | collected | rejected
  artifact_location: "file path / URL"         # required when status == collected
  summary: "..."
  validated_by: "CI job / human / another agent"
  collected_at: "ISO 8601"
```

### Rules

- **Every `role: primary` surface must have at least one evidence entry** (human or CI check).
- Evidence `type` should match surface nature:
  - `user` → screenshot_diff / interaction_recording / e2e_test
  - `system_interface` → contract_test / api_proof
  - `information` → migration_dry_run / query_plan
  - `operational` → log_sample / metric_diff / runbook_update
  - `experience` → playtest_result
  - `real_world` → reconciliation_report

### Picking among the 19 evidence types

The schema offers 19 enum values. Selection principles:
- **An actually produced artifact**, not a verbal claim of "I did it."
- **Traceable**: `artifact_location` must be openable / retrievable.

---

## `playtest` — required for the experience surface

Maps to `docs/playtest-discipline.md`.

**Top-level condition: if `surfaces_touched` includes `experience`, `playtest` is required.**

```yaml
playtest:
  level: L0 | L1 | L2 | L3
  sample: { size, composition }
  rubric:
    dimensions:
      - { name, pass_threshold }
  baseline:
    type: golden_build | previous_release | ab_control | designer_intent | none
    reference: "tag / version / doc"
    rubric_diff:
      - { dimension, delta, verdict: improved | noise | acceptable_regression | blocking_regression }
  known_regressions: [...]
```

### Key rules

- `sample.size < 3` → only qualifies as "self-test," not a playtest; cannot be a release gate.
- `baseline.type == none` must be justified in the notes.
- Any dimension with `verdict == blocking_regression` → the manifest cannot enter `phase: signoff`.

---

## `post_delivery` — Phase 8 observation

Maps to `docs/post-delivery-observation.md`.

**Top-level condition: if `phase == deliver | observe`, `post_delivery` is required.**

```yaml
post_delivery:
  review_horizon: "7d | 30d | ..."
  metrics_watched:
    - { name, baseline, alert_threshold }
  feedback_channels: [...]
  production_findings: [...]
```

`production_findings` is continuously appended to while `phase: observe`; each entry is `{ finding, severity, action_taken }`.

> Observation is not "nothing blew up for two days, done." `review_horizon` is hard-coded; observation only completes when that horizon elapses.

---

## Decomposition-relationship fields

Maps to `docs/change-decomposition.md` and `docs/concurrent-changes.md`.

When a change cannot stand alone, or has a strict ordering / synchronization requirement, the relationships between manifests become **first-class citizens** rather than verbal agreements.

### `depends_on` / `blocks` (bidirectional)

```yaml
depends_on:
  - change_id: "2026-03-12-add-voucher-enum"
    reason: "Prerequisite for adding the new status field."
blocks:
  - change_id: "2026-03-22-retire-legacy-voucher-api"
    reason: "Legacy-API retirement must wait until the new enum has fully switched over."
```

- **Direction semantics:** `A.depends_on = [B]` ⇔ `B.blocks = [A]`.
- CI should check that the bidirectional mirror is consistent (see `automation-contract-algorithm.md` §2.5).
- If a `depends_on` change is still in `phase: plan`, downstream cannot enter `phase: implement`.

### `co_required` (must ship together)

```yaml
co_required:
  - change_id: "2026-03-14-mobile-consume-new-enum"
    reason: "The moment the server enables the new enum value, the mobile decoder must already be live."
```

- Used when the changes must merge / rollout in the same release window.
- Not a one-way dependency — "bound to ship together."
- Reviewers must look at both manifests' evidence, not each in isolation.

### `part_of` (sub-items pointing up to the parent)

```yaml
part_of:
  change_id: "2026-Q2-auth-overhaul"
  role: "implementation_slice"
```

- When a large change is split into multiple manifests, each child points back to the parent.
- The parent's `phase: observe` cannot close until every `part_of` child has also reached `observe`.
- Maps to "functional decomposition" in `docs/change-decomposition.md`.

### `supersedes` (replacement)

Already present in older versions; complementary to the four fields above. `supersedes` says "this manifest replaces the prior one"; the other fields say "this manifest coexists with other manifests."

### `strategic_parent` (pointer to external decision artifact)

Maps to `docs/strategic-artifacts.md`.

When a change is a slice of a larger initiative whose motivation lives in an **external authoritative document** (ADR, RFC, OKR, design doc, external ticket), use `strategic_parent` to anchor the manifest to that artifact. Agent-protocol deliberately does not define ADR/RFC formats — it only defines the anchor.

```yaml
strategic_parent:
  kind: adr              # enum: adr | rfc | okr | design_doc | external_ticket | other
  location: docs/adr/0042-auth-compliance-rewrite.md
  summary: >
    Comply with 2026 audit requirements by rewriting session-token storage
    off legacy in-memory cache onto an audited KV store. This manifest
    covers the token-store slice only.
  initiative_id: AUTH-REWRITE-2026Q2
```

- **When to set it:** the change is a slice of a larger initiative, the initiative has its own authoritative document, and motivation is *not* self-contained in the manifest.
- **Required fields:** `kind` + `location`. `summary` (≤ 400 chars on what the parent requires of this change) and `initiative_id` (stable identifier shared across sibling manifests) are optional but recommended.
- **Relationship to `part_of`:** `part_of` identifies an internal epic; `strategic_parent` identifies the external decision document. They are complementary — a manifest may have both. Use `part_of` alone for self-documenting internal epics; use `strategic_parent` alone when the external decision is the only scaffolding.
- **Not a container.** The anchor points out — consumers open the parent doc to read its contents. Automation verifies `location` is resolvable; it does not inspect what the parent says.

See `docs/strategic-artifacts.md` for field semantics, aggregation patterns, and anti-patterns.

---

## Per-phase note fields

The **non-code artifacts** that AI and humans produce in each phase are also part of the manifest.
These fields turn the manifest into a **traceable decision log**, not just a delivery spec.

### `implementation_notes` (Phase 4)

Discoveries during implementation, deviations from the original plan, assumptions that were validated or invalidated.

```yaml
implementation_notes:
  - type: plan_delta          # plan drift
    summary: "Discovered the enum value needs 3 weeks of dual-writing, not 1."
    rationale: "Third-party SDK update cadence is longer than estimated."
  - type: discovery
    summary: "Consumer registry was missing the data warehouse."
    rationale: "Found via grep + a direct conversation with the data team."
  - type: scope_flag
    summary: "Found we could piggyback a legacy-field cleanup, but deliberately did not."
    rationale: "Avoid scope creep; open a new ticket."
  - type: evidence_added
  - type: assumption_validated
  - type: assumption_invalidated
```

The `type` enum forces the author to classify discoveries instead of collapsing them into one prose blob.

### `review_notes` (Phase 5)

Reviewer observations. Each entry has a `finding` enum:

```yaml
review_notes:
  - finding: sot_mismatch
    detail: "Manifest claims the SoT is in schema.yaml, but the diff modifies enum.go."
    resolved_by: "Author corrected sot_map."
  - finding: missing_evidence
  - finding: breaking_change_underscored
  - finding: rollback_mode_too_optimistic
  - finding: uncontrolled_interface_missing
  - finding: consumer_coverage_gap
  - finding: cross_cutting_gap
  - finding: scope_expansion
  - finding: ok_with_caveat
  - finding: approved_no_issue
```

### `approvals` (Phase 5 / 6)

Who signed off, in which phase, and over what scope.

```yaml
approvals:
  - approver_role: human        # enum: human | ai
    approver_id: "alice@team"
    scope: delivery              # enum: plan | implementation | delivery | waiver
    timestamp: "2026-04-18T10:23Z"
    notes: "Confirmed rollback mode 2 is acceptable for the mobile long tail."
```

**Conditional rule:** when `phase == deliver`, at least one approval with `approver_role: human` and `scope: delivery` is required. Schema-enforced.

### `handoff_narrative` (Phase 6 → 7 → 8)

What the next handler needs to know when the change is handed off. A short paragraph, not a checklist.

```yaml
handoff_narrative: |
  The new enum value has been live for 72h; metrics are within baseline.
  Note the data-warehouse backfill won't complete until T+5d — until then,
  the analytics dashboard will temporarily lack the pending_review category.
  Support SOP updated to v3.2.
```

**Conditional rule:** required when `phase == observe`.

### `waivers`

For items that "should be done in theory but we decide not to this time." `waivers` is not an escape hatch — the schema enforces **time-boundedness** and **human approval**.

```yaml
waivers:
  - rule: "L3 breaking change requires 2-week deprecation notice"
    reason: "External compliance authority mandates takedown within 7 days; the full timeline cannot be run."
    approver_role: human         # const: human — the schema forbids AI-issued waivers
    approver_id: "compliance-lead@team"
    granted_at: "2026-04-15"
    expires_at: "2026-05-15"     # required — no permanent waivers
    mitigation: "Strengthen consumer-allowlist notifications + 10-day dual-version coexistence."
```

**Conditional rules:**
- `approver_role` const `human` (schema-enforced; cannot be issued by AI).
- `expires_at` required and must be a future date.
- Expired waivers cannot block new validation (auto-expire).

---

## AI-hygiene fields

These fields exist because AI acts as a co-author; they map to `docs/ai-operating-contract.md`.

### `assumptions`

Every assumption the AI makes must be explicitly logged:

```yaml
- statement: "..."
  confidence: low | medium | high
  validation_plan: "Who / how will this be validated?"
```

> "I assumed this API has no third-party consumers" must become an assumption — never sit silently in the AI's head as a fact.

### `escalations`

Points where the AI stops and hands a decision to a human. `trigger` is an enum:

- `third_party_consumer_affected`
- `irreversible_side_effect`
- `rollback_mode_3`
- `breaking_change_l3_or_l4`
- `ambiguous_sot`
- `security_or_pii_path`
- `user_requested_pause`
- `output_mismatch_with_intent`
- `scope_expansion_discovered`

> When the AI hits these situations, it **must** escalate — it cannot decide to continue on its own.

### `residual_risks`

Known risks that cannot be eliminated + severity + mitigation + the accepter:

```yaml
- description: "..."
  severity: low | medium | high | critical
  mitigation: "..."
  accepted_by: "human-signature / 'unaccepted'"
```

`accepted_by: unaccepted` means "nobody has taken ownership of this risk yet"; CI may refuse to let this enter the `deliver` phase.

---

## Top-level schema-conditional rules

The schema enforces the following via `allOf + if/then`:

| Condition | Enforced requirement |
|-----------|----------------------|
| `surfaces_touched` contains `experience` | `playtest` required |
| `phase` ∈ `deliver | observe` | `post_delivery` required |
| `cross_cutting.build_time_risk.codegen_touched == true` | `codegen_artifacts_committed` + `release_build_verified` required |
| `surfaces_touched` contains `real_world` with `role == primary` | `rollback.overall_mode == 3` |
| `breaking_change.level` is `L2+` | `migration_plan` + `affected_consumers` required |
| `breaking_change.level` is `L3+` | `deprecation_timeline` required |
| `breaking_change.level` is `L4`  | `migration_path` restricted to `rename_and_coexist | deprecation_cycle` |
| `rollback.overall_mode == 3` | `compensation_plan` required |
| Patterns 6/7/8/9/10/4a | The matching extension object is required |
| `phase == deliver` | At least one approval with `approver_role: human` and `scope: delivery` |
| `phase == observe` | `handoff_narrative` required |
| `waivers[*].approver_role` | Const `human` (schema forbids AI approval) |
| `waivers[*].expires_at`   | Required and must be a future date |
| `depends_on[*].change_id` ⇔ `blocks[*].change_id` | Bidirectional mirror (checked in `automation-contract-algorithm.md` §2.5) |

---

## CI integration (recommended)

Add a validation job to CI:

```yaml
# Illustrative: .github/workflows/change-manifest-validate.yaml
- name: Validate manifest
  run: |
    ajv validate \
      -s schemas/change-manifest.schema.yaml \
      -d "$(git diff --name-only origin/main | grep change-manifest)"
```

Additional gates (things the methodology enforces beyond the schema):

- `phase == signoff` → every `primary` surface must have evidence with `status: collected`.
- `breaking_change.level in [L3, L4]` → PR requires a designated reviewer.
- `rollback.overall_mode == 3` → a named approver must appear in `residual_risks.accepted_by`.

---

## Modes of AI use of the manifest

### Mode A: generation (AI produces the manifest)

During Phase 1 / 2 (investigate / plan), AI reads the requirement → produces a **draft manifest**.
That draft is AI's **declared understanding** of the change; humans calibrate against it faster than they would against prose.

### Mode B: validation (AI checks an existing manifest)

During Phase 4 / 5 (implement / review), AI compares the manifest against the real diff:
- For the surfaces the diff actually touched, is each one recorded in the manifest?
- Manifest claims `rollback.overall_mode: 1`, but the diff includes an irreversible migration?
- Manifest has no `playtest`, but the diff touches experience-related UI?

### Mode C: hand-off (between agents)

An upstream agent (e.g. an investigate agent) produces a draft manifest.
A downstream agent (implement agent) uses that manifest as both context and a contract constraint.

---

## Relationship to other methodology documents

| Methodology doc | Manifest field |
|-----------------|----------------|
| `surfaces.md` | `surfaces_touched`, `uncontrolled_interfaces` |
| `source-of-truth-patterns.md` | `sot_map` + pattern-specific extensions |
| `cross-cutting-concerns.md` | `cross_cutting` (six dimensions) |
| `breaking-change-framework.md` | `breaking_change` |
| `rollback-asymmetry.md` | `rollback` |
| `playtest-discipline.md` | `playtest` |
| `ai-operating-contract.md` | `authors`, `assumptions`, `escalations`, `residual_risks` |
| `post-delivery-observation.md` | `post_delivery`, `handoff_narrative` |
| `change-decomposition.md`       | `depends_on`, `blocks`, `co_required`, `part_of` |
| `concurrent-changes.md`         | `depends_on`, `co_required` |
| `strategic-artifacts.md`        | `strategic_parent` |
| `automation-contract-algorithm.md` | Source of truth for every conditional rule above. |

---

## Example tour

- `templates/change-manifest.example-crud.yaml`
  - Simple CRUD (new field).
  - SoT patterns 1 + 3 + 4, breaking L0, rollback mode 1.
  - Demonstrates the **minimum skeleton** manifest.

- `templates/change-manifest.example-mobile-offline.yaml`
  - Mobile offline-edit sync.
  - SoT patterns 7 + 8 + 10, breaking L1, rollback mode 2.
  - Demonstrates temporal-local, codegen, host-lifecycle, uncontrolled_interfaces, escalations.

- `templates/change-manifest.example-game-gacha.yaml`
  - Game live-ops gacha drop-rate adjustment.
  - experience + real_world + compliance surfaces.
  - SoT patterns 2 + 9, breaking L1, rollback mode 3.
  - Demonstrates playtest, post_delivery, rollback_mode_3 escalation, compensation_plan.

---

## Versioning

- Breaking changes to the schema follow the methodology's own breaking-change framework.
- When the schema is upgraded, existing manifests are not forced to rewrite; new manifests use the new schema.
- `$id` does not change (URL remains stable); version differences are advanced via internal schema fields.

---

## Common anti-patterns

- ❌ **Packing multiple unrelated changes into one manifest** — loses single focus.
- ❌ **Every `desync_risk` filled as `low`** — almost certainly unexamined.
- ❌ **Evidence `status: collected` but `artifact_location` blank** — fake completion.
- ❌ **`assumptions` always an empty array** — AI must have assumptions; invisible assumptions are the most dangerous.
- ❌ **`rollback.overall_mode: 1` but a primary surface is `real_world`** — the schema blocks this; the intent is to force honesty.
- ❌ **`breaking_change.self_assessed_vs_worst_case: matches` filled reflexively** — the point is to force genuine worst-case thinking.
