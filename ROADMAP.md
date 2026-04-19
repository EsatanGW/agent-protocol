# ROADMAP

> **Purpose.** Multi-session tracking artifact for ongoing, phase-gated work. Each in-flight initiative opens a section here, records every phase's entry / verification / exit status, and stays here until the initiative is closed. ROADMAP sections are **not** deleted when an initiative ships — they are marked `status: closed` so future sessions can audit the history.
>
> **This file is the one the `phase-gate-discipline.md` contract points at.** If an initiative runs without a ROADMAP entry, a verifier MUST flag that before the initiative exits any phase beyond Phase 0.

---

## Schema

Every initiative section follows this shape:

```markdown
## <initiative-slug> — <one-line title>

- **Opened:** YYYY-MM-DD
- **Driver:** <who / which request>
- **Status:** planning | in_progress | paused | closed
- **Target version:** <semver>
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | ... | ... | ... | ✅ passed / ❌ failed / ⏳ in_progress / ⏸ paused | `<sha>` | ... |

### Phase log
<free-form notes, surprises, scope deltas, links to Change Manifests>
```

`Gate verification` must name the **exact command / check / reviewer** that decides pass, not a vague claim. If the gate failed and was re-run, append the rerun row — do not rewrite history.

`Commit` is required when the host repo is under version control (per `phase-gate-discipline.md`). Use the merge commit SHA, not just "merged."

---

## Active initiatives

_(none active)_

---

## Closed initiatives

## multi-agent-layering-bridge — ship 3-agent Planner/Implementer/Reviewer layering as a Claude Code bridge

- **Opened:** 2026-04-19
- **Driver:** User review of the NYCU-Chung/my-claude-devteam plugin (P7/P9/P10 + PUA high-pressure mode + 12-agent team) surfaced the question of whether agent-protocol should adopt hierarchical agent layering. Recommendation landed on a 3-role responsibility-based layering (not job-title) aligned with the existing Planner / Implementer / Reviewer roles in `docs/multi-agent-handoff.md`. User accepted.
- **Status:** closed
- **Target version:** 1.2.0
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Decide layering shape (role-count + enforcement mechanism): whether to copy hierarchical P-levels or to formalize the existing 3-role split with tool-permission enforcement | Conversation decision + scope agreed with user | User accepted 3-role (not P7/P9/P10), responsibility-based (not job-title), tool-permission matrix as enforcement layer, single-agent anti-collusion rule | ✅ passed | _(pre-commit)_ | Hierarchical model rejected — would contradict tool-agnostic / stack-neutral design invariants and over-specify for a generic workflow plugin |
| P1 | Normative layering: add tool-permission matrix and anti-collusion rule to canonical docs | `docs/multi-agent-handoff.md` two new sections (Tool-permission matrix + Single-agent anti-collusion rule); `AGENTS.md` new §7 carrying the same matrix + rule runtime-neutrally | Matrix uses capability categories (file read / code search / file write / shell read-only / shell state-changing / shell verification-only / network fetch / sub-agent delegation), not tool names; rule forbids Implementer ≡ Reviewer outright and permits Planner ≡ Implementer only in Lean mode | ✅ passed | `909fc33` | Reviewer intentionally lacks edit/write — "single most important row" per the matrix |
| P2 | Claude Code bridge: three sub-agent definitions carrying the tool-permission envelopes | `.claude-plugin/agents/planner.md` (tools: Read/Grep/Glob/WebFetch/Task, model: opus); `.claude-plugin/agents/implementer.md` (tools: Read/Grep/Glob/Edit/Write/Bash/WebFetch, model: sonnet); `.claude-plugin/agents/reviewer.md` (tools: Read/Grep/Glob/Bash/WebFetch, model: opus) | Each definition's tools field matches the matrix row for its role; Implementer explicitly has no `Task` (cannot spawn a reviewer of itself); Reviewer explicitly has no Edit/Write | ✅ passed | `909fc33` | Bridge is one of several possible runtime mappings — AGENTS.md carries the runtime-neutral rule |
| P3 | Wire other runtime bridges + surface in index files | `GEMINI.md` / `.windsurfrules` / `.cursor/rules/engineering-workflow.mdc` each gain a "Multi-agent role separation (Full mode)" summary with cross-ref to canonical doc; `README.md` adds bullet 6 and directory-layout entry for `.claude-plugin/agents/` | Every entry point references the same canonical source (`docs/multi-agent-handoff.md`) — no divergent definitions; cross-cutting-term discipline per `CLAUDE.md §5` | ✅ passed | `909fc33` | Bridge files are thin pointers, canonical content stays in AGENTS.md + docs |

### Phase log

- P0 rejected the NYCU-Chung P7/P9/P10 hierarchical model for agent-protocol because (a) hierarchy encodes corporate-ladder vocabulary that is culture-specific and breaks the tool-agnostic invariant (cf. CHANGELOG 1.0.0 "Design invariants") and (b) the existing `docs/multi-agent-handoff.md` already defined Planner / Implementer / Reviewer as canonical responsibility-based roles — we needed enforcement, not a new hierarchy.
- The enforcement mechanism is the tool-permission matrix itself: a Reviewer sub-agent that *cannot* call Edit or Write cannot rewrite the change it is reviewing, which mechanically blocks the self-review anti-pattern that prose rules fail to prevent. Anti-collusion rule closes the remaining gap (same identity playing two roles serially).
- Lean-mode exception — Planner ≡ Implementer — explicitly allowed because Lean mode by definition is a single-agent workflow for trivial changes (typo, small config, doc edit). Implementer ≡ Reviewer has no Lean-mode exception because "review your own code" is the failure mode the contract exists to prevent.
- Implementer model is `sonnet` (cost-efficient on straightforward execution); Planner and Reviewer are `opus` (higher-leverage judgment tasks where step-back cost of the better model is highest).
- No changes to `skills/`, `schemas/`, or methodology semantics. This is an additive bridge on top of existing roles.

---

## runtime-hook-contract — define runtime-layer hook contract + ship Claude Code reference hook bundle

- **Opened:** 2026-04-19
- **Driver:** Agent-protocol had `docs/ci-cd-integration-hooks.md` for CI-layer gating but no specification for *runtime* hooks (agent-lifecycle events: pre-commit, post-tool-use, on-stop). User accepted that formalizing the runtime-layer contract is a methodology gap to close and that a Claude Code reference implementation demonstrates it concretely.
- **Status:** closed
- **Target version:** 1.2.0
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Decide whether a runtime-layer hook contract should be defined separately from `ci-cd-integration-hooks.md` or fold into it; decide the category taxonomy | Conversation decision + scope agreed with user | User accepted separate doc (`docs/runtime-hook-contract.md`); 4 categories (phase-gate / evidence / drift / completion-audit) mapped directly to manifest fields; shared exit-code semantics with `automation-contract.md` (0 pass / 1 block / 2 warn) | ✅ passed | _(pre-commit)_ | Separate doc chosen because runtime and CI layers differ in trigger point, latency budget, and side-effect envelope — folding would blur those distinctions |
| P1 | Write the contract | `docs/runtime-hook-contract.md` (~190 lines) covering: four categories, JSON-over-stdin event schema, exit-code semantics, latency budgets (< 500 ms phase-gate + evidence; < 2 s drift), non-functional requirements (offline / deterministic / no side effects / no model-in-hook), bridge requirements (event mapping, stdin convention, exit-code handling, registration format, ≥ 1 reference hook per A / D) | Contract is tool-agnostic (no Claude Code specifics in the contract itself); cross-refs to `automation-contract.md` and `ci-cd-integration-hooks.md` both bidirectional | ✅ passed | `36b2506` | Tool-agnostic invariant preserved — the contract defines the shape, bridges fill in runtime specifics |
| P2 | Reference implementation: Claude Code hook bundle | `reference-implementations/hooks-claude-code/` with README, DEVIATIONS, `settings.example.json`, and four executable POSIX-sh scripts (`manifest-required.sh`, `evidence-artifact-exists.sh`, `sot-drift-check.sh`, `completion-audit.sh`) | Scripts syntax-clean (`sh -n` pass); empty-repo smoke-test exits 0; absent-`yq` path returns exit 2 with `TOOL_ERROR` per contract; `chmod +x` applied to all scripts | ✅ passed | `36b2506` | Bundle covers all four A/B/C/D categories; portable to other runtimes via their own event-registration mechanism (scripts are POSIX-sh + yq only, no Node/Python dependency) |
| P3 | Wire into index + cross-ref existing docs | `docs/ci-cd-integration-hooks.md` new "Relationship to runtime-layer hooks" section; `docs/automation-contract.md` cross-ref; `AGENTS.md` reading-list entry 17b; `README.md` "When your situation matches" entry; `reference-implementations/README.md` catalog row for `hooks-claude-code/` | Bidirectional cross-refs between CI-hook doc and runtime-hook doc; AGENTS.md reading list in documented order; README bullet added under the right section | ✅ passed | `36b2506` | `validator-posix-shell/` row preserved alongside new hooks row in reference-implementations catalog |

### Phase log

- P0 explicitly framed runtime vs CI as **sibling layers**, not competing layers. Runtime hooks fire during the agent's own tool-call lifecycle (pre-commit, post-tool-use, on-stop). CI hooks fire after the branch/PR reaches shared infrastructure. The same manifest rule can be enforced at both layers — what differs is the blast radius and rollback cost if the rule fires late.
- Category taxonomy (A phase-gate / B evidence / C drift / D completion-audit) mirrors the manifest's own validation layers from `automation-contract-algorithm.md`. This keeps runtime enforcement semantically consistent with CI enforcement — a rule has the same meaning whether it fires in-session or in-pipeline.
- Latency budgets (< 500 ms for A/B, < 2 s for C) are deliberate: runtime hooks block the agent's loop, so slow hooks become productivity taxes. CI hooks have no such budget because they run out-of-band.
- "No model-in-hook" rule is deliberate: hooks must be deterministic so the same manifest + same repo state always produces the same verdict. A hook that calls an LLM is itself a new agent and must be governed by the multi-agent-handoff contract, not by the hook contract.
- Reference bundle uses POSIX-sh + `yq` + `git` only (no Node, no Python, no Claude Code SDK dependency). Portability: the same scripts can be re-registered under a different runtime's event mechanism by only re-writing the settings-file shape — the script bodies stay stack-neutral.
- `sot-drift-check.sh` is postToolUse + matcher `Edit|Write|MultiEdit` — this is the only category that cares about per-tool-call granularity; the other three run at commit / stop boundaries.
- Completion-audit (category D) is the highest-leverage category — it blocks the agent from surfacing "done" when the manifest's `evidence_plan` / `residual_risks.accepted_by` / `escalations.resolved_at` / `phase: observe` narrative are still materially incomplete. This is the single rule set that catches the "dishonest completion" failure mode most directly.

---

## strategic-parent-extension — add external-artifact anchor to Change Manifest schema

- **Opened:** 2026-04-19
- **Driver:** Methodology had `part_of` for internal-epic linkage but no way to anchor a manifest to an external strategic document (ADR / RFC / OKR / design doc / external ticket). User weighed two options — "Phase -1 strategy" ceremony vs. `strategic_parent` schema extension — and chose the schema extension because it stays on the existing manifest's output contract rather than adding a new phase.
- **Status:** closed
- **Target version:** 1.2.0
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Decide: invent Phase -1 "Strategic scope" ceremony OR extend Change Manifest with `strategic_parent` field | Conversation recommendation + user decision | User accepted schema-extension path; Phase -1 rejected because strategic deliberation runs on a different cadence (quarters, committees, human-only review) and does not benefit from phase-gate artifacts | ✅ passed | _(pre-commit)_ | The anchor is a pointer, not a container — agent-protocol deliberately does not define ADR/RFC formats (existing mature standards cover those) |
| P1 | Add optional `strategic_parent` object to the schema | `schemas/change-manifest.schema.yaml` new top-level object after `part_of`; required fields `kind` (enum: adr / rfc / okr / design_doc / external_ticket / other) + `location`; optional `summary` (maxLength 400) + `initiative_id` | Additive change — existing manifests remain valid (field is optional); `additionalProperties: false` on the object; matches SemVer minor-bump policy per `VERSIONING.md` | ✅ passed | _(this change)_ | No retrofitting of the 4 existing example manifests — none of them has a real external strategic parent, and injecting synthetic ones would misrepresent the anchor's intent |
| P2 | Write the explanation doc | `docs/strategic-artifacts.md` (~130 lines): TL;DR, What this is, What this is NOT (no ADR/RFC format definition, no Phase -1 ceremony, no parent-content validation), field semantics table, aggregation patterns, `part_of` vs `strategic_parent` relationship, anti-patterns | Doc is explicit on what agent-protocol does and does not define; cross-refs to `schemas/change-manifest.schema.yaml`, `docs/change-manifest-spec.md`, `docs/change-decomposition.md`, `docs/team-org-disciplines.md`, `docs/phase-gate-discipline.md` | ✅ passed | _(this change)_ | "The anchor is a pointer, not a container" is the doc's thesis sentence |
| P3 | Wire into index + cross-ref existing docs | `docs/change-manifest-spec.md` new `strategic_parent` subsection under Decomposition-relationship fields (after `supersedes`); Relationship-to-other-methodology-documents table gains `strategic-artifacts.md` row | Spec doc cross-refs the dedicated doc; Decomposition section now covers the full field family (`depends_on` / `blocks` / `co_required` / `part_of` / `supersedes` / `strategic_parent`) | ✅ passed | _(this change)_ | `strategic_parent` and `part_of` are explicitly complementary, not alternatives |

### Phase log

- P0 rejected Phase -1 "Strategic scope" for two reasons: (a) the existing Phase 0–8 framework covers implementation-level work, and strategic deliberation runs on a **different timescale** (quarters, committees) that phase-gate artifacts would not help; (b) adding a phase creates a new ceremony with its own template / minimum requirements / gate rule, which is scope creep for a methodology that already has nine phases. The anchor approach achieves the same traceability (manifest points at the decision) without inventing a new ceremony.
- Schema field is **additive** (optional). Existing manifests validate unchanged. Per `VERSIONING.md`, this is a minor-bump-compatible change.
- `kind` enum deliberately covers the five most common artifact types (ADR / RFC / OKR / design_doc / external_ticket) plus `other` as an escape hatch. We do **not** define the format of any of these — ADRs are still ADRs whether your org calls them "Decision Records" or "Tech Notes."
- `initiative_id` (optional) enables aggregation queries across multiple manifests that share the same strategic parent (e.g., "show all manifests under `AUTH-REWRITE-2026Q2`"). Aggregation tooling is out of scope for this methodology layer — any tool that reads the schema can build it.
- Deliberately **did not retrofit** the four existing example manifests (`change-manifest.example-{crud,mobile-offline,game-gacha,multi-agent-handoff}.yaml`). None of them has a genuine external strategic parent; injecting a synthetic ADR / RFC path would model the anchor for readers as "always present," contradicting the doc's position that the field is only for changes where external motivation is not self-contained.
- Cross-ref `part_of` vs `strategic_parent` captured in both the dedicated doc and the manifest spec: internal-epic-ID vs external-decision-document, **complementary, not alternatives**. A manifest may set both (internal epic implementing an external decision).

---

## ktor-graphql-overlay — add GraphQL parallel-IDL overlay to Ktor bridge

- **Opened:** 2026-04-19
- **Driver:** Post `bridge-deduction-closure` re-scoring surfaced GraphQL-as-third-IDL as the single residual with high structural fit (mirrors existing gRPC overlay) and high real-world prevalence. User decision to fill it; other residuals (Flutter Flame, embedder cross-stack, KMM iOS depth, event-sourcing, Unity UaaL, Visual Scripting) confirmed as correctly residual.
- **Status:** closed
- **Target version:** 1.1.0 (bundled with prior initiatives for release)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Re-score residual deductions; confirm only GraphQL worth upstreaming vs. leaving as project-local | Conversation scoring + per-item judgment table | User agreement on single-item scope (GraphQL only); other residuals confirmed correctly project-local | ✅ passed | _(pre-commit)_ | Contrast with `bridge-deduction-closure` P0 — that initiative overrode "project-local" recommendations; this one accepts them for 6/7 residuals |
| P1 | Add GraphQL parallel-IDL overlay to Ktor bridge; update Known Limitations; update CHANGELOG | Insert after gRPC overlay in `docs/bridges/ktor-stack-bridge.md`; remove GraphQL entry from Known Limitations; extend `[Unreleased]` Ktor bullet | Overlay mirrors gRPC overlay structure (SoT discipline + L0–L4 + manifest requirements + drift checks + anti-patterns); adds GraphQL-specifics (N+1 as Pattern 4a, subscription as Pattern 10, federation as cross-subgraph contract, no wire-level versioning escape hatch) | ✅ passed | _(this change)_ | Structural mirror of gRPC overlay keeps bridge internally consistent |

### Phase log

- GraphQL overlay chosen over Flame / embedder / UaaL / KMM-iOS / event-sourcing / Visual Scripting because it was the **only** residual that (a) is a mainstream use case, (b) structurally maps onto the existing parallel-IDL pattern (gRPC overlay already sets up the pattern), and (c) does not require a new cross-stack bridge to be meaningful. The others either need a sibling bridge first (iOS Swift, native host bridge) or are genuinely small-audience project-local choices.
- Overlay adds new concerns GraphQL introduces that gRPC does not: no wire-level versioning (field removal is intrinsically breaking; protobuf can reserve tags), N+1 as a resolver-pipeline risk, subscription lifecycle as Pattern 10, federation composition as an entity-resolution Pattern 4a across subgraphs.
- DataLoader registration order treated as Pattern 4a — parallel to Ktor plugin install order and to gRPC interceptor order. This keeps the "installation-order as contract" theme consistent across all three IDL layers the bridge now covers (HTTP middleware, gRPC interceptors, GraphQL resolver context).
- No changes to other bridges, schemas, or the operating contract. Scope deliberately minimal — this is a single-overlay addendum, not a re-architecture.

---

## bridge-deduction-closure — close self-declared bridge deductions across all four base stacks

- **Opened:** 2026-04-19
- **Driver:** User-initiated follow-up after scoring each bridge against the repo's own specs; user explicit instruction "請幫我完善這四項" (close all four bridges' deduction items, including items previously marked "keep as known limitation").
- **Status:** closed
- **Target version:** 1.1.0 (same minor as per-stack-examples-and-compose-bridge, bundled for release)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Re-score each of the four base bridges (Flutter / Android Kotlin + XML / Ktor / Unity) against repo specs; enumerate deduction items per bridge; user decision on scope (cover all, not selective) | Conversation scoring table + deduction list per bridge | User explicit confirmation to close all deductions on all four bridges, overriding prior "keep as known limitation" recommendation for DOTS/ECS, Flutter web, Ktor multi-tenant / Loom, etc. | ✅ passed | _(pre-commit)_ | Scope diverges from `per-stack-examples-and-compose-bridge` P0 explicit deferrals — this initiative supersedes that deferral per user decision |
| P1 | Flutter + Android deductions | Inline overlay sections added to `docs/bridges/flutter-stack-bridge.md` (Web, Desktop, federated plugin, code push, state-mgmt pipeline) and `docs/bridges/android-kotlin-stack-bridge.md` (KMM, Play Feature Delivery, instrumented-test OS-API); Known Limitations lists narrowed to residual-only | Each new section structurally mirrors existing bridge patterns (Surface mapping / SoT mapping / Rollback / Drift checks / Anti-patterns); no new vendor names leak into methodology docs | ✅ passed | _(this change)_ | Overlays chosen over new bridges to avoid bridge-family proliferation; Flutter Web and Desktop are target-discipline overlays of the Flutter bridge, not sibling bridges |
| P2 | Ktor + Unity deductions | Inline overlay sections added to `docs/bridges/ktor-stack-bridge.md` (observability depth, multi-tenant / sharding, gRPC parallel IDL, hexagonal / onion, virtual threads / Loom, JVM version-drift) and `docs/bridges/unity-stack-bridge.md` (DOTS/ECS with pre-1.0 caveat, render-pipeline variants, custom engine fork); Known Limitations narrowed to residual-only; Unity bridge Scope note updated to reflect DOTS / RP-variants / custom-fork now covered | Observability overlay introduces no new vendor names — contract-only (OpenTelemetry-style is existing pattern); DOTS/ECS overlay explicitly marked pre-1.0 API volatility with project-local `packages-lock.json` pin guidance | ✅ passed | _(this change)_ | DOTS/ECS overlay explicitly caveats API volatility; Unity Scope line rewritten to stop deferring DOTS to "a separate bridge" |
| P3 | Wire changes into release record | Updates to `CHANGELOG.md` `[Unreleased]` (Added + Changed bullets for this wave) and this ROADMAP entry | `[Unreleased]` sections list every new overlay by name; ROADMAP records this initiative as closed with phase log | ✅ passed | _(this change)_ | No new top-level files added in this initiative — all work is in-bridge, preserving the "one bridge per stack, overlays within" structure |

### Phase log

- This initiative explicitly supersedes scope-exclusions from `per-stack-examples-and-compose-bridge` P0. The prior deferrals (DOTS/ECS, Flutter web/desktop as sibling bridges, KMM, Ktor hexagonal / multi-tenant / sharding / gRPC / Loom) stood on the recommendation that they remain project-local. User override replaced that recommendation with "close all deductions in-bridge via overlays."
- Structural choice: inline overlays (matching the existing XR / Mobile Unity / Live-service / Industrial overlays pattern in `unity-stack-bridge.md`) rather than spawning new bridges. Rationale: a new bridge multiplies the README / AGENTS / onboarding / template TL;DR consumer list — `CLAUDE.md §5` (cross-cutting-term discipline) makes that a measurable drift cost. Overlays keep the bridge index stable.
- DOTS/ECS overlay includes an explicit **API stability caveat** at the top of the section. The Entities package is peri-1.0 across its subpackages; the overlay maps *patterns* (Pattern 1 binding of `IComponentData`, Pattern 4a binding of `[UpdateInGroup]`) rather than concrete APIs that will shift. Consumers pin concrete APIs in `packages-lock.json` with a project-local note.
- Flutter Web and Desktop are handled as **target-discipline overlays of the Flutter bridge**, not sibling bridges. Pipeline (`dart2js` / `dart2wasm` / native-AOT), rollback asymmetry (CDN-flag vs. store binary), and signing/notarization differences are captured per-target within the existing bridge rather than cloning its structure.
- Ktor observability depth overlay intentionally frames logs / metrics / traces as **Pattern 4 (Contract-Defined)** rather than operational side-effects. This is the same move the `mobile-offline-feature-example.md` uses for server-side contract stability — logs field names are a contract that every dashboard / alert / SLO rule depends on.
- No changes to `AGENTS.md`, `skills/`, or `schemas/`. All work is documentation — consistent with CLAUDE.md §1 "default to documentation-type edits."
- Bridge Known Limitations lists are now **residual-only** across all four bridges — every prior "known limitation" that was really a scope deferral has been either resolved (via overlay) or narrowed to a genuinely-out-of-scope residual (e.g., "specific APM vendor exporter config stays project-local").

---

## per-stack-examples-and-compose-bridge — fill bridge worked-example gaps + add Compose bridge

- **Opened:** 2026-04-19
- **Driver:** User-initiated review of bridge self-declared limitations; see CHANGELOG `[Unreleased]` entry.
- **Status:** closed
- **Target version:** 1.1.0 (next minor, per `VERSIONING.md`)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Clarify which bridge gaps are worth filling vs. leaving as project-local addenda | Recommendation in conversation + scope agreed with user | User agreement on items 1 (worked examples) and 2 (Compose bridge); DOTS/ECS, Flutter web/desktop-as-new-bridge, KMM, Ktor hexagonal explicitly deferred | ✅ passed | _(pre-commit)_ | Deferred items remain project-local per each bridge's own known-limitations guidance |
| P1 | Draft four worked examples + Compose bridge; flesh out the outlines that the XML and Ktor bridges already had as "future update" placeholders | `docs/examples/{flutter-app,android-kotlin,ktor-server,unity-game}-example.md`, `docs/bridges/android-compose-stack-bridge.md` | Each example's structure and length sit within the `docs/examples/` corpus baseline (137–313 lines); Compose bridge structure mirrors `android-kotlin-stack-bridge.md` and uses cross-references instead of duplication | ✅ passed | _(this change)_ | Compose bridge explicitly inherits XML bridge sections rather than duplicating them |
| P2 | Wire new files into consumers: bridge Reference Worked Example sections, README bridges list, AGENTS.md bridges + examples lists, `english-quick-start.md` bridges list, stack-bridge-template TL;DR, CHANGELOG entry | Edits to README.md, AGENTS.md, docs/onboarding/english-quick-start.md, docs/stack-bridge-template.md, CHANGELOG.md, all four bridge files | Bridge lists consistent across README, AGENTS.md, onboarding, and template TL;DR; no orphan "future update" placeholders remain in bridges | ✅ passed | _(this change)_ | Cross-cutting-term discipline applied per CLAUDE.md §5 |

### Phase log

- Scope deliberately excluded: DOTS/ECS bridge, Flutter web/desktop as a separate bridge, KMM addendum, Ktor hexagonal / multi-tenant / sharding / gRPC / Loom overlays. These remain as self-declared "known limitations" in the respective bridges — each bridge's own guidance is to fill via `docs/bridges-local-deviations.md` in consumer projects, not to carry them upstream unless a gap proves universal.
- Compose bridge intentionally does NOT duplicate Room / WorkManager / FCM / runtime-permission / vendor-fork / deep-link content from the XML bridge. Cross-reference is the canonical pattern; duplication would be a drift source per this repo's source-of-truth discipline.
- No changes to `AGENTS.md` operating contract, `skills/`, or `schemas/`. The addition is documentation-only, consistent with CLAUDE.md §1 "default to documentation-type edits."
