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
