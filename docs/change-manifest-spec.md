# Change Manifest Spec

> **English TL;DR**
> The methodology's **machine-readable output contract**. Every non-trivial change produces one YAML manifest that records: which surfaces are touched, which SoT patterns apply, whether breaking-change levels (L0-L4) apply, rollback mode (1/2/3), evidence artifacts, decomposition links (`depends_on` / `blocks` / `co_required` / `part_of`), phase-specific extensions (`implementation_notes`, `review_notes`, `approvals`, `handoff_narrative`), and `waivers` (time-bounded, human-approver-only). The manifest is validated by the automation contract (see `automation-contract-algorithm.md`) at three layers: structural (schema conformance), cross-reference (SoT/surface coverage, deprecation-timeline presence, human-approval requirement for deliver phase), and drift (declared-SoT-must-be-modified, surface ↔ file pattern match via bridge mapping). Canonical schema: `schemas/change-manifest.schema.yaml` (JSON Schema draft 2020-12). Templates: `skills/engineering-workflow/templates/manifests/change-manifest.example-*.yaml`.

> **Purpose:** the Change Manifest is the methodology's **machine-readable output contract**.
> It records — as YAML that both AI agents and CI can inspect — what surfaces this change touches, which SoTs apply, whether this is a breaking change, how it rolls back, and what the evidence is.
>
> This document is the **field-level semantic specification** for that schema — it says which field corresponds to which discipline in the methodology.
>
> **Schema file:** `schemas/change-manifest.schema.yaml` (JSON Schema draft 2020-12)
> **Examples:** `skills/engineering-workflow/templates/manifests/change-manifest.example-*.yaml`

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

## State-snapshot discipline

The Change Manifest is **the single state snapshot** for a change. If the manifest is insufficient to let a new session resume work without reading any other artifact, the manifest is **incomplete** — fix the manifest, not the reading ritual.

This discipline exists because a common failure mode at session boundaries is: the outgoing session produces a verbose handoff prompt pointing at many artifacts; the incoming session reads them sequentially and exhausts its context window before any real work begins. The remedy is **Manifest completeness**, not a longer read list. The full resumption protocol (incoming session) and handoff template (outgoing session) are normatively defined in `skills/engineering-workflow/references/resumption-protocol.md` and `skills/engineering-workflow/templates/handoff-prompt-template.md`; the discipline below is what the manifest itself must satisfy to make those protocols workable.

### What the manifest must carry as a state snapshot

All of the following must be answerable from the manifest alone, without opening any other file:

- **Current `phase`** — what the change is currently doing.
- **Current `status`** — whether the current phase is `draft`, `in_progress`, `review_ready`, etc.
- **Next action** — either explicit in `handoff_narrative` when one is set, or implicit via `implementation_notes[*].type: plan_delta` entries that describe what comes next.
- **Outstanding escalations** — every `escalations[*]` entry with no resolution record is a blocker the incoming session must address.
- **Invalidated assumptions** — `implementation_notes[*].type: assumption_invalidated` entries change the plan; they belong in the manifest, not in ambient prose.
- **Evidence gaps** — `evidence_plan[*].status: planned` (vs `collected`) tells the incoming session what verification still owes.

### Pointer completeness checklist

Every manifest of a non-trivial change must point to the artifacts the resumption protocol's Targeted / Role-scoped / Full modes will want to read. These use **existing fields** — no schema change — but the manifest author must populate them consistently:

| Pointer | Where it lives in the manifest | When it becomes required |
|---|---|---|
| Spec path | `evidence_plan[*]` with a `type` of `spec_draft` / equivalent, or a `handoff_narrative` pointer | Phase 1+ (once a spec exists) |
| Plan path | `evidence_plan[*]` with a `type` of `plan` / equivalent | Phase 2+ |
| Test plan path | `evidence_plan[*]` with a `type` of `test_plan` / equivalent | Phase 3+ |
| Latest test report path | `evidence_plan[*]` with `status: collected` and matching `artifact_location` | Phase 4+ |
| Completion report path | `evidence_plan[*]` with a `type` of `completion_report`, or referenced from `handoff_narrative` | Phase 7+ |
| ROADMAP row | `part_of.change_id` or a pointer in `handoff_narrative` | Any multi-phase initiative (per `docs/phase-gate-discipline.md` Rule 2) |

If a pointer is missing when the checklist says it is required, that is **not** a reason to re-read the repo at resume time — it is a Manifest-drift signal. The incoming session should stop and fix the manifest before proceeding (see `skills/engineering-workflow/references/resumption-protocol.md` Step 2a).

### Anti-pattern: the fat handoff prompt

A handoff prompt that contains more than a short pointer block (identity header + resume mode + next action + ≤ 3 open items + ≤ 3 read paths) is a signal that the manifest is underfilled and the prompt is compensating. The fix is always to push content into the manifest, not to accept the verbose prompt. See `skills/engineering-workflow/templates/handoff-prompt-template.md` for the compact form.

### Manifest size ceiling

Some AI runtimes refuse to open a file above a single-file read ceiling (typical: ~25,000 tokens or ~2,000 lines) without an explicit offset or line-range argument. A manifest that crosses that ceiling **stops working as a state snapshot**: the incoming session cannot open it in one read, and any fallback to `grep` or offset reads defeats the "one file answers what comes next" guarantee above.

When a manifest approaches the ceiling, the remedies — in order of preference:

1. **Compact in place.** Move verbose narrative into the phase-specific structured note fields (`implementation_notes[]`, `review_notes[]`, `handoff_narrative`, `escalations[]`) and trim redundant prose. Structured fields carry information at lower token cost than free-form prose, and the resumption protocol already knows where to look for them.
2. **Split via `part_of`.** If the change is genuinely large enough to warrant nesting (umbrella initiative with multiple stage children), create child manifests with their own `change_id` and point each one up via `part_of`. Each child must then independently satisfy §State-snapshot discipline — including this sub-clause. The umbrella manifest becomes a thin index of `part_of` children; each child is its own readable snapshot.

**Do not rely on `grep` / offset-read as a workaround.** That workaround:

- Bypasses the `last_updated` / `phase` / `status` header the incoming session is supposed to read in full before acting — drift detection (see `skills/engineering-workflow/references/lazy-resume-checklist.md` Step 3) cannot fire on fields the read window excludes.
- Cannot distinguish "field not populated" from "field not in this read window" — a false-negative on missing pointers.
- Produces selectively-read state that differs between roles in a multi-agent change. That is the opposite of the shared-snapshot guarantee this section exists to provide.

If a handoff prompt instructs the incoming session to "grep for X in the manifest" or "read lines N–M of the manifest," the manifest is the problem and the prompt is compensating. Compact the manifest first; do not accept the instruction.

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
  deprecation_timeline: {...}         # legacy form; dates only
  deprecation: {...}                  # preferred form; see below
```

### `self_assessed_vs_worst_case`

The methodology insists on **worst-case grading**. This field forces the AI / author to answer honestly:

- `matches` — first-pass assessment was already the worst case.
- `escalated` — initially assessed lighter; after analysis, escalated.
- `unresolved` — cannot determine yet; a human must judge.

### Conditional required-ness

- `L2+` → `migration_plan` + `affected_consumers` required.
- `L3+` → **either** `deprecation_timeline` **or** `deprecation` required (automation-contract rule 2.6 accepts both; do not populate both).
- `L4` → `migration_path` restricted to `rename_and_coexist | deprecation_cycle`.

> `L4 (Semantic Reversal)` cannot use parallel_switch, because the same name cannot simultaneously mean two things.

### Deprecating a field (the richer `deprecation` marker)

Introduced in schema 1.7.0. `$ref` → `$defs.deprecation`.

```yaml
breaking_change:
  level: L3
  migration_path: deprecation_cycle
  migration_plan: "Consumers switch from legacy_field to replacement_field by sunset_date."
  deprecation:
    since: "1.7.0"
    remove_in: "2.0.0"
    use_instead: "replacement_field"
    migration_note: |
      Legacy field accepted but emits a warning in the generator. Consumers
      should read replacement_field; writers should populate both during
      the deprecation window.
    announce_date: "2026-04-20"
    sunset_date:   "2026-10-20"
    escalation_contact: "@contract-owners"
```

Use the structured `deprecation` object (not the legacy `deprecation_timeline`) whenever the deprecation has a named replacement or a non-obvious migration path — which is almost always.

**When to attach `deprecation` vs when to bump `breaking_change.level`:**

| Scenario | What to do |
|---|---|
| Field added, nothing removed | L0 or L1; no deprecation marker |
| Field's behavior or default changes | L1/L2; note in `migration_plan`, no deprecation marker |
| Field deprecated but still accepted; new name shipped | L3; populate `deprecation` with `use_instead` |
| Field removed outright (no replacement, no window) | L4 with `migration_path: deprecation_cycle`; populate `deprecation`; schedule removal |
| Field's semantic meaning reversed (same name, inverted sense) | L4 with `migration_path: rename_and_coexist`; populate `deprecation`; do not reuse the old name without renaming |

The `deprecation` marker is the methodology's own instance of the deprecate-then-remove discipline it recommends for every change. Using it keeps the manifest itself honest about what the change is doing.

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

## `implementation_clusters` — Pattern C cluster-parallel record

Optional top-level array. Each entry records one **file-disjoint implementation cluster** delegated to its own canonical Implementer at Phase 4 per `skills/engineering-workflow/references/cluster-parallelism.md` (Pattern C) and `reference-implementations/roles/role-composition-patterns.md` §Pattern 7. Purpose is both planning (Planner writes the field at Phase 2) and audit (each cluster's `status` records execution state; the cluster's `assigned_identity` records which Implementer carried it out).

Backward-compatible: pre-1.13 manifests and Full-mode changes that used a single Implementer (no cluster delegation) both validate without this field. A Full-mode change that did fan out via Pattern C but did not record `implementation_clusters` is an audit-layer contract escape — the substantive record is missing.

```yaml
implementation_clusters:
  - cluster_id: "db-migration"
    label: "Voucher expiry migration + backfill"
    scope_files:
      - "db/migrations/**"
      - "db/seeds/voucher/**"
    scope_surfaces: ["information", "operational"]
    task_refs: ["plan-task-1", "plan-task-2"]
    evidence_refs: ["migration-dry-run-log", "backfill-count-check"]
    independence_rationale: |
      No shared state with API-field or frontend clusters — migration
      runs before either deploys and has its own test suite.
    assigned_identity: "implementer-alice-db"       # must not equal Planner, other clusters, or Reviewer
    status: completed

  - cluster_id: "api-field"
    label: "Voucher expiry field on /vouchers API"
    scope_files:
      - "services/voucher-api/**"
      - "contracts/voucher.proto"
    scope_surfaces: ["system-interface"]
    task_refs: ["plan-task-3", "plan-task-4"]
    evidence_refs: ["api-contract-test", "openapi-diff"]
    independence_rationale: |
      API consumer updates land in a separate downstream change
      (docs/concurrent-changes.md co_required); the API-field cluster
      only ships the server-side addition.
    assigned_identity: "implementer-bob-api"
    status: completed

  - cluster_id: "frontend-copy"
    label: "Expiry display + i18n"
    scope_files:
      - "apps/web/src/vouchers/**"
      - "apps/web/locales/*/voucher.json"
    scope_surfaces: ["user"]
    task_refs: ["plan-task-5"]
    evidence_refs: ["visual-diff", "e2e-voucher-expiry"]
    independence_rationale: |
      Frontend reads the existing API shape; the new expiry field is
      optional on the client until API-field cluster lands.
    assigned_identity: "implementer-carol-web"
    status: completed
```

**Rules:**

- `minItems: 2` (a 1-wide cluster is just serial Phase 4 — do not record it) and `maxItems: 4` (Reviewer cross-cluster cross-cutting gap-check visibility degrades past 3–4, same reason `parallel_groups.sub_agents` caps at 4).
- `scope_files` pair-wise disjointness across clusters is a validator-level cross-item constraint (not expressible in pure JSON Schema). A change with overlapping cluster scopes is invalid even if structurally valid.
- `assigned_identity` must differ from the Planner's identity, from every other cluster's `assigned_identity`, and from the Reviewer's identity-to-be. Anti-collusion applies transitively.
- `independence_rationale` is required narrative justification. A hand-wavy rationale is a signal that the clusters are not actually independent and serial execution is safer.
- `status` lifecycle: `pending → in_progress → completed | blocked_discovery`. A cluster that enters `blocked_discovery` halts all other clusters by default (`cluster-parallelism.md` §Discovery-loop handling).
- When Pattern C is used, a `parallel_groups` entry with `pattern: C_cluster_implementers` should additionally be recorded as an audit breadcrumb pointing at `implementation_clusters`; the substantive cluster data lives in `implementation_clusters` itself, so the `parallel_groups` entry's `synthesis.manifest_fields_written` is typically short (`[implementation_clusters]`) rather than the long synthesis list Patterns A/B produce.

**When the Reviewer audits this field:**

- Verify `assigned_identity` for each cluster appears in `authors[]` with `role: implementer` and is distinct across clusters.
- Verify `scope_files` are pair-wise disjoint (no file appears in two clusters' globs).
- Verify every `evidence_refs` entry resolves to an `evidence_plan.artifacts` row that this cluster's Implementer populated (cross-check `authors` of those evidence rows).
- Perform the cross-cluster cross-cutting gap check: are there issues at cluster intersections that no individual Implementer would catch? (See `cluster-parallelism.md` §6 for the specific questions.)
- Verify no cluster has `status: in_progress` at sign-off time — a Pattern C change that reaches `phase: signoff` with a cluster still running is a compositional escape.

---

## `parallel_groups` — fan-out audit trail

Optional top-level array. Each entry records one **parallel sub-agent fan-out** that occurred during the change, per `skills/engineering-workflow/references/parallelization-patterns.md` and `reference-implementations/roles/role-composition-patterns.md` Patterns 5–6. Entries with `pattern: C_cluster_implementers` additionally serve as audit breadcrumbs for Pattern C (§Pattern C records the substantive data in `implementation_clusters`; the `parallel_groups` entry records that the multi-delegation happened). Purpose is audit, not scheduling — the manifest records fan-out *as it happened* so a Reviewer can confirm canonical-role-performs-synthesis and anti-collusion were honored.

Backward-compatible: pre-1.11 manifests and Full-mode changes that did not fan out both validate without this field. What is **not** valid is a fan-out that happened but was not recorded — that is a contract escape at the audit layer. Lean mode fan-outs do not exist (`role-composition-patterns.md` §When); an entry claiming `owning_role` in Lean mode is itself a composition failure.

```yaml
parallel_groups:
  - group_id: "phase1-surfaces"
    owning_role: planner
    owning_identity: "planner-alice"       # must match an entry in authors[]
    phase: investigate
    pattern: A_surface_investigators       # enum: A_surface_investigators | B_specialized_audit | C_cluster_implementers | other
    context_pack_summary: "4 surfaces in scope; SoT candidates pre-classified; return-slot shape fixed."
    sub_agents:
      - identity: investigator-user-surface
        scope: "User surface sweep — copy, routes, state visibility"
        capability_envelope: read+search
        return_location: ".working/pg-phase1-surfaces/user.yaml"
      - identity: investigator-information-surface
        scope: "Information surface — schema, enums, validation"
        capability_envelope: read+search
        return_location: ".working/pg-phase1-surfaces/info.yaml"
      - identity: investigator-system-interface
        scope: "System interface surface — API + events"
        capability_envelope: read+search
        return_location: ".working/pg-phase1-surfaces/system.yaml"
    synthesis:
      performed_by_identity: "planner-alice"   # MUST equal owning_identity
      timestamp: "2026-04-22T10:05:00Z"
      manifest_fields_written: [sot_map, surfaces_touched, consumers]
      cross_cutting_gap_check:
        performed: true
        gaps_found:
          - "User-surface sweep found the pre-rename copy; information-surface sweep renamed the enum — neither noticed the intersection."
        contradictions_found: []
        suspiciously_empty_returns: []
```

**Rules:**

- `sub_agents` has `minItems: 2` (a 1-wide fan-out is a serial sub-agent call — use Patterns 1–4, not an under-scoped fan-out record) and `maxItems: 4` (past 3 parallel returns, fan-in cross-cutting visibility degrades; larger groups signal over-scoped decomposition).
- `synthesis.performed_by_identity` **must equal** `owning_identity`. Synthesis is never delegated per `role-composition-patterns.md` §The invariant — a mismatch is a composition escape. The schema marks this as a normative constraint; validators enforce it.
- `synthesis.manifest_fields_written` is required and non-empty. A fan-out that wrote no fields produced no value.
- `synthesis.cross_cutting_gap_check.performed` must be `true`. `false` is a composition failure, not a valid outcome — the cross-cutting gap check is the single highest-value step in a fan-out and the one parallelization most commonly silently skips.
- Every sub-agent identity must differ from every canonical role identity on this change (anti-collusion) and from every other sub-agent identity in this group.
- `pattern: other` requires a non-empty `context_pack_summary` so the non-standard fan-out is explicable at audit time.

**When the Reviewer audits this field** (see `docs/multi-agent-handoff.md` §Reviewer and `parallelization-patterns.md` §Fan-in discipline): for any `parallel_groups` entry, verify — (1) `owning_identity` appears in `authors[]`; (2) each sub-agent identity does not; (3) synthesis identity equals owning identity; (4) the manifest fields named in `manifest_fields_written` actually exist and were populated by this change; (5) the cross-cutting gap check lists concrete items or explicitly records "none found." A group passing structural validation but missing substantive gap-check output is the exact failure `docs/multi-agent-handoff.md` §Anti-rationalization rules, Rule 3 catches at the Reviewer level.

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

## CI integration and AI usage modes

Recipes — *how to wire the manifest into CI* and *how AI agents use the manifest in generation / validation / hand-off modes* — live in the companion [`change-manifest-spec-cookbook.md`](change-manifest-spec-cookbook.md). The spec stays normative; the cookbook holds applied material.

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

## Mission-shaped manifests and the example tour

Two extended treatments live in the cookbook to keep this spec focused on field semantics:

- **Mission-shaped manifests** — when a change is exploratory and its acceptance bar is numeric, see [`change-manifest-spec-cookbook.md §Mission-shaped manifests`](change-manifest-spec-cookbook.md#mission-shaped-manifests). The pattern uses existing schema fields (`evidence_plan[*].tier: critical`, `assumptions`, `implementation_notes`, `residual_risks`) and is **not a separate artifact category**.
- **Example tour** — six worked manifests under [`skills/engineering-workflow/templates/manifests/`](../skills/engineering-workflow/templates/manifests/) covering CRUD, mobile-offline, game-gacha live-ops, mission-evaluator, multi-agent handoff progression, and security-sensitive (JWT rotation). One-line summaries of each example live in [`change-manifest-spec-cookbook.md §Example tour`](change-manifest-spec-cookbook.md#example-tour).

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
