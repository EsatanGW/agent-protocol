# Changelog

All notable changes to this project will be documented in this file.

Format inspired by Keep a Changelog; versioning policy in `VERSIONING.md`.

## [Unreleased]

## [1.1.0] - 2026-04-19

### Added

- **Per-stack worked examples** — `docs/examples/flutter-app-example.md` (multi-platform "Save & Share" exercising platform-channel two-sided contract and per-target rollback asymmetry), `docs/examples/android-kotlin-example.md` (offline draft-saving exercising Room migration + WorkManager unique-name discipline + ViewBinding dual-representation), `docs/examples/ktor-server-example.md` (order-lifecycle enum + migration + plugin install order + three-rollback-mode discipline within one feature), `docs/examples/unity-game-example.md` (save-data format migration exercising schema versioning + IL2CPP / AOT build-time risk + three-track rollback asymmetry). Each bridge's Reference Worked Example section now points at its dedicated file; the Ktor and Android-Kotlin bridges' "future update" placeholders are removed.
- **Jetpack Compose stack bridge** — `docs/bridges/android-compose-stack-bridge.md`. Companion to the Kotlin + XML bridge: inherits Room / WorkManager / FCM / runtime-permission / vendor-fork / deep-link / ProGuard-R8 sections and adds Compose-specific deltas for state ownership (`remember` / `rememberSaveable` / ViewModel + `StateFlow`), recomposition hygiene, effect-API pipeline order (`LaunchedEffect` / `SideEffect` / `DisposableEffect`) as a new Pattern 4a case, `CompositionLocal` provider nesting as a Pattern 4a case, navigation-route strings as a Pattern 3 enum, Compose compiler metrics as a drift signal, and Paparazzi / Roborazzi + `createComposeRule()` verification. XML bridge's "known limitations" entry for Compose now cross-references this bridge.
- **Flutter bridge deduction-closure sections** — `docs/bridges/flutter-stack-bridge.md` now covers: Flutter Web target discipline (`dart2js` / `dart2wasm` pipelines, service-worker cache invalidation, CDN-flag rollback vs. store binaries), Flutter Desktop target discipline (window lifecycle, per-OS packaging, signing / notarization asymmetry), federated plugin lifecycle (app-facing / platform-interface / per-platform-impl trio with version-compat tables), code push / dynamic delivery (Shorebird / custom OTA as Pattern 4a + store-policy constraints), and state-management library pipeline-order (Provider / Riverpod / Bloc initialization order as Pattern 4a).
- **Android Kotlin bridge deduction-closure sections** — `docs/bridges/android-kotlin-stack-bridge.md` now covers: KMM shared-code SoT (`expect` / `actual` declarations as Pattern 4, per-target builds, serialization drift), Play Feature Delivery (install-time / conditional / on-demand / instant-app module rollback characteristics + SoT-split fan-out), and instrumented-test OS-API version discipline (silent-skip anti-pattern, min / mid / max API matrix enforcement).
- **Ktor bridge deduction-closure sections** — `docs/bridges/ktor-stack-bridge.md` now covers: observability depth discipline (logs / metrics / traces each as Pattern 4 with cardinality budgets, coroutine-context propagation of `trace_id`, PII hashing), multi-tenant / sharding overlay (row-level / schema-per-tenant / DB-per-tenant rollback asymmetry with both default and per-tenant auth-provider pipeline-order variants, cross-tenant drift as a unique failure mode), gRPC parallel IDL overlay (protobuf-specific L0–L4 + dual-IDL manifest fields), GraphQL parallel IDL overlay (SDL as Pattern 4, DataLoader registration as Pattern 4a, GraphQL-specific L0–L4 with no wire-level versioning, subscription lifecycle as Pattern 10, federation / stitching as cross-subgraph contract, N+1 + query-complexity budget), hexagonal / onion / clean architecture overlay (remapping SoT source fields to domain ports), virtual threads (Loom) / alternative concurrency overlay (pinning hazards + reactive-framework substitution), and a JVM / Kotlin / Ktor / coroutines version-drift discipline for the build-time-risk manifest field.
- **Unity bridge deduction-closure sections** — `docs/bridges/unity-stack-bridge.md` now covers: DOTS / ECS overlay (API stability caveat scoped to companion subpackages since core `Entities` is GA 1.x; system update-order graph as canonical Pattern 4a, three-way authoring ↔ baked ↔ archetype dual-representation, Burst + Baker + IL2CPP triple verification), render pipeline variant discipline (URP / HDRP / built-in RP as pipeline-specific asset targets, shader-variant-count budget, pipeline migration as its own change type), and custom engine fork discipline (fork as an additional SoT layer, patch-set contract with upstream, `UPSTREAM.md` requirement, fork-exit-plan expectation). Scope note updated so these are first-class overlays, not deferrals.

### Changed

- `README.md`, `AGENTS.md`, and `docs/onboarding/english-quick-start.md` bridge indexes updated to include the Compose bridge.
- `AGENTS.md` worked-examples index updated to include the four new per-stack examples.
- `docs/stack-bridge-template.md` TL;DR bridge list updated to include the Compose bridge.
- Each of the four base bridges' "Known limitations" lists rewritten to reflect only residual items after the deduction-closure sections — prior entries that are now covered in-bridge (Flutter web/desktop/federated/code-push/state-mgmt; Android KMM/PFD/instrumented-test API gap; Ktor multi-tenant/sharding/gRPC/hexagonal/Loom; Unity DOTS/ECS/render-pipelines/custom-engine-fork) have been removed or retargeted to narrower residual scopes.

### Fixed

- Android Kotlin bridge Scope note no longer calls the Compose bridge "(future)" — it is now linked as an existing companion with an inherited-sections summary.
- Unity DOTS / ECS overlay caveat clarified — core `Entities` package is GA 1.x (since 2023) with stable `IComponentData` / `ISystem` / `[UpdateInGroup]`; the volatility is scoped to companion subpackages (Entities Graphics, DOTS Animation, Unity Physics for ECS, Netcode for Entities).
- Ktor multi-tenant pipeline-order overlay adds the per-tenant auth-provider variant (Keycloak realm-per-tenant, Auth0 organization, per-tenant OIDC issuer, regulated B2B) where `TenantResolution` correctly precedes `Authentication` — the previous guidance presented the single-auth-provider order as universal.

## [1.0.0] - 2026-04-19

Initial public release. Tool-agnostic engineering workflow plugin for AI coding agents, usable across Claude Code, Cursor, Gemini CLI, Windsurf, Codex, Aider, OpenCode, or any AI runtime that reads `AGENTS.md`.

### Included

- **Operating contract** — `AGENTS.md` defines the universal runtime contract: honest reporting, scope discipline, source-of-truth rules, surface-first analysis, evidence requirements, Change Manifest contract, phase-gate discipline.
- **Engineering workflow skill** — `skills/engineering-workflow/` provides Lean and Full modes, phase minimums for Phase 0 through Phase 8, capability-category guidance, and spec / plan / test / completion templates. Supporting references cover the mode decision tree, discovery loop, resumption protocol, startup checklist, and misuse signals.
- **Methodology documentation** — `docs/` contains the four canonical surfaces plus nine extension surfaces (asset, experience, performance-budget, data-quality, compliance, hardware-interface, real-world, model, uncontrollable-external), ten Source-of-Truth patterns, the L0–L4 breaking-change severity matrix, three rollback modes (Reversible / Forward-fix / Compensation-only), cross-cutting concerns, the AI operating contract, security and supply-chain disciplines, change decomposition, team / org-scale disciplines, AI project memory, multi-agent handoff, automation contract, and phase-gate discipline.
- **Change Manifest contract** — `schemas/change-manifest.schema.yaml` plus four worked example manifests (CRUD, mobile offline, game gacha, multi-agent handoff progression). The schema enforces human-approver waivers, expiry timestamps, bidirectional decomposition links, and phase-appropriate narrative fields.
- **Stack bridges** — `docs/bridges/` maps the tool-agnostic methodology to concrete stacks: Flutter, Android Kotlin + XML, Ktor, Unity 3D. Bridge files are the only place where specific vendor / framework / language names appear. The stack-bridge template (`docs/stack-bridge-template.md`) supports adding your own stack.
- **Automation contract** — capability-level specification (`docs/automation-contract.md`) plus normative algorithm (`docs/automation-contract-algorithm.md`) defining three forced check layers (structural / cross-reference / drift), exit-code stability, and offline operability. A non-normative reference validator (`reference-implementations/validator-posix-shell/`) built on POSIX shell plus `yq` plus a pluggable schema validator illustrates the contract.
- **Worked examples** — `docs/examples/` covers ten domains: worked (batch-resend invoices), bugfix (pagination-filter desync), refactor (order-status canonical alignment), migration-rollout (structured-preferences SoT transition), game-dev (in-game shop), game-liveops (three-track asset/config/binary strategy), mobile-offline-feature, ml-model-training, data-pipeline, embedded-firmware (OTA with hardware-interface + real-world surfaces).
- **Multi-agent entry points** — packaged simultaneously as a Claude Code plugin (`.claude-plugin/`), a Cursor rules bundle (`.cursor/rules/`), a Gemini CLI instruction set (`GEMINI.md`), Windsurf rules (`.windsurfrules`), and an AGENTS.md-compatible contract for Codex / Aider / OpenCode.

### Design invariants

- **English-only.** All normative content — methodology, skills, schemas, templates, operating contract, READMEs — is English. No mixed-language documents; no translation companions.
- **Tool-agnostic.** Specific vendor, model, framework, or product names appear only in `docs/bridges/` and `reference-implementations/`, both of which are explicitly marked non-normative. Methodology docs, the skill layer, the schema, and the Change Manifest templates remain stack-neutral.
- **Capability categories, not tool names.** Every operational instruction names a category (file read, file write, code search, shell execution, sub-agent delegation) rather than a specific tool, so the plugin ports cleanly between AI runtimes.
- **Canonical terminology held fixed.** Severity L0–L4 (Additive / Behavioral / Structural / Removal / Semantic-reversal), rollback modes 1/2/3 (Reversible / Forward-fix / Compensation-only), four canonical surfaces plus extension surfaces, SoT patterns addressed by number, automation tiers L0–L3, three multi-agent roles by responsibility (Planner / Implementer / Reviewer).

### License

MIT. Fork, localize, customize internally.
