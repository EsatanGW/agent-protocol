# Unity 3D Stack Bridge

> Maps the tool-agnostic methodology to Unity (GameObject / MonoBehaviour pipeline). Bridges are the only layer allowed to name specific tools.

---

## Scope

**Applies to:** Unity projects using the classic GameObject/Component model with C#, URP or HDRP or built-in RP, Addressables for asset management, and a live-ops capable distribution channel (mobile stores / PC / console). DOTS/ECS, render-pipeline variants, and custom engine forks are covered as overlays below.
**Out of scope for this bridge:** cloud build pipeline vendor specifics (reference, not prescription).

---

## Surface mapping

Unity exercises the **full extension set** of the surface model — the Game Dev example uses asset, experience, and performance-budget surfaces, all of which bind here.

> Machine-consumable surface → file-glob mapping lives in
> [`unity-surface-map.yaml`](./unity-surface-map.yaml) and is consumed by
> validator rule 3.2 (surface ↔ file-pattern drift). The Unity map carries
> the richest stack_extensions set in the repository (asset, performance-
> budget, experience, compliance).

### User surface

| Concept | Concrete implementation |
|---|---|
| screens / menus | `Canvas` + UI Toolkit or uGUI |
| controls | `Input System` action maps |
| copy / i18n | Localization package `.po` / `.csv`, `LocalizedString` references |
| state | ScriptableObject-based state containers, or a state library |
| a11y | UI Toolkit accessibility features (where supported) + manual text scaling / contrast |

### System interface surface

| Concept | Concrete implementation |
|---|---|
| Backend API | `UnityWebRequest` or `HttpClient` + generated / hand-written DTOs |
| Event tracking | Analytics SDK with event registry ScriptableObject |
| Platform SDKs | IAP, ads, social, push, cloud save |
| Save files | local file + optional cloud save adapter |
| Multiplayer | netcode library (Mirror, Netcode for GameObjects, custom) |

**Uncontrolled-interface register:**
- Unity editor version (LTS vs Tech stream)
- Platform store policies (Apple / Google / consoles)
- Graphics API changes per OS version
- Platform SDK versions (IAP, ads, push)
- Target device hardware variants

### Information surface

| Concept | Concrete implementation |
|---|---|
| Game config | ScriptableObject assets, optional JSON/CSV loaded at runtime |
| Feature flags | Remote config service + local override |
| Save schema | Version-stamped save format + migration chain |
| Enums / status | C# `enum`, marked `[Serializable]` where needed for inspector |

### Operational surface

| Concept | Concrete implementation |
|---|---|
| Structured logs | `Debug.Log` with a redacting wrapper, or Serilog/NLog |
| Crash / analytics | Unity Cloud Diagnostics, Crashlytics, Sentry |
| Metrics | Custom telemetry batcher + backend ingest |
| Build pipeline | Editor + CLI build scripts, `BuildPipeline.BuildPlayer` |
| Release channels | Internal, closed testing, phased rollout |

### Asset surface (extension — primary for Unity)

| Concept | Concrete implementation |
|---|---|
| Meshes, textures, materials, shaders | under `Assets/` with `.meta` siblings |
| Audio, animation | `.anim`, `.controller`, `.wav`/`.ogg` |
| Scenes / prefabs | `.unity`, `.prefab` with deterministic YAML + `.meta` GUIDs |
| Addressables | groups, labels, remote catalog |

### Experience surface (extension — primary for Unity)

Physics feel, camera framing, VFX/SFX feedback, input responsiveness, animation blending, haptics — verified by playtest discipline (`docs/playtest-discipline.md`).

### Performance-budget surface (extension — primary for Unity)

| Budget | Typical item |
|---|---|
| frame budget | target ms per frame (e.g., 16.6ms @ 60fps) |
| draw calls | max per scene / per camera |
| memory | GPU + CPU peaks, texture budget |
| loading time | scene load, asset stream time |
| package size | per platform, per ABI |

---

## SoT pattern bindings

| Pattern | Unity instance |
|---|---|
| 1 Schema-Defined | ScriptableObject field layout ↔ serialized YAML in asset |
| 2 Config-Defined | Remote config, ScriptableObject configs, build-time defines |
| 3 Enum/Status | `enum`, exhaustive switch, or typed state `ScriptableObject`s |
| 4 Contract-Defined | DTO shared with server (versioned), analytics event registry |
| **4a Pipeline-Order** | **Script Execution Order** (`ProjectSettings/ScriptExecutionOrder.asset`); also Addressables catalog update order |
| 6 Transition-Defined | Animator state machines; game flow controllers with guarded transitions |
| 7 Temporal-Local | Single-player progress authored locally, synced on reconnect; cloud save conflict resolution |
| **8 Dual-Representation** | Canonical case. Editor view of `.unity` / `.prefab` / ScriptableObject ↔ serialized YAML ↔ baked Library metadata ↔ runtime loaded object. `.meta` GUIDs must be preserved. Asset reimport is the explicit sync step. |
| supply-chain (extension) | Package Manager `manifest.json` + `packages-lock.json`; Editor version in `ProjectSettings/ProjectVersion.txt` |

---

## Rollback mode defaults

Unity live-ops has **three-track rollback asymmetry**:

| Track | Default mode |
|---|---|
| Server config / flag change | Mode 1 — reversible |
| Addressables / remote asset patch | Mode 1 or 2 — can push a corrective catalog within minutes to hours |
| Shipped binary (store) | Mode 2 forward-fix — users already updated stay on new version; store review delays apply |
| Already-run live-ops event (rewards granted) | Mode 3 compensation — rewards cannot be retracted without player backlash |

The `docs/examples/game-liveops-example.md` example walks this asymmetry.

---

## Cross-cutting concerns bindings

- **Security:**
  - Client is untrusted — never let client decide currency / economy rewards
  - Save files may be tampered with; validate on server when possible
  - Native plugins (JNI / Objective-C) auditing
  - IAP receipt validation server-side
  - Analytics PII: do not log device identifiers beyond what platform policy allows
- **Supply chain:** third-party assets (Asset Store packs) audited for license + vulnerabilities; native plugins pinned by version
- **Performance:** budgets per target platform; profiler captures archived as evidence; frame timing tests on target device, not editor
- **Observability:** in-game telemetry categorized (economy, progression, technical), with separate retention policies
- **Testability:** EditMode tests for logic, PlayMode tests for scene-level behavior, Test Runner in CI via Cloud Build or self-hosted
- **Error handling:** graceful degradation — disconnect, asset load fail, corrupt save, each has a user-visible safe state
- **Build-time risk:** IL2CPP vs Mono, stripping level, AOT limitations, shader stripping, platform-specific defines

---

## Automation-contract implementation

### Layer 1

Change Manifest validator can run via a Unity CLI batchmode script or an external validator CI job. Output must follow the contract format.

### Layer 2 — Cross-reference consistency

Unity-specific drift checks to ship in bridge CI:

1. **Meta file integrity:** every asset has a matching `.meta`; every `.meta` has a matching asset. GUID stability must be preserved — no duplicate GUIDs.
   ```bash
   # Custom check script or Odin/Mirror validators
   ```
2. **Addressables catalog freshness:** built catalog matches current Addressables settings + labels.
3. **ScriptableObject serialization drift:** compare serialized `.asset` YAML against ScriptableObject field layout; missing or stale fields are a dual-representation violation.
4. **Script execution order audit:** any change to `ScriptExecutionOrder.asset` requires a `manifest.sot_map` entry citing the reason (pipeline-order SoT).
5. **Build report checks:** uncompressed size, draw call estimate, shader variant count — must not exceed declared budgets in the performance-budget surface evidence.

### Layer 3 — Drift detection

Weekly on `main`:
- Orphan assets (present but referenced nowhere)
- Duplicate GUIDs (severe)
- Unused shaders / materials / prefabs
- Stale Addressables groups
- Phase 8 observation overdue for live-ops events with mode-3 rollback

---

## Multi-agent handoff conventions

- `Manifests/<change_id>.yaml` under repo root or `docs/manifests/`
- Commit trailer: `Change-Id: <change_id>`
- Implementer runs Test Runner (EditMode + PlayMode) and archives results before handoff
- Playtest evidence: recorded gameplay clip or observer report (see `docs/playtest-discipline.md`)
- Reviewer verifies performance-budget evidence captured on the target device

---

## Typical workflow per task type

| Task | Mode | Minimum artifacts |
|---|---|---|
| UI text change | Zero ceremony | localization update |
| New cosmetic effect | Lean | asset + playtest clip + frame budget check |
| Gameplay balance change | Full | manifest + before/after playtest + config SoT |
| New Addressables group | Full | manifest + catalog drift verification + rollback track note |
| Live-ops event | Full | manifest with mode-3 rollback + compensation plan + post-event observation |
| Script Execution Order change | Full | manifest citing pipeline-order SoT + regression test |
| Save format migration | Full | forward migration + old-save compatibility test + hard cutoff policy |
| Unity editor version upgrade | Full | uncontrolled_interfaces update + behavior change audit + full Test Runner |

---

## Reference worked examples

Three Unity examples, each exercising a different angle:

- `docs/examples/game-dev-example.md` — in-game shop purchase (asset / experience / performance-budget surfaces combined).
- `docs/examples/game-liveops-example.md` — limited-time event with binary/asset/config three-track strategy, compensation rollback, playtest discipline.
- `docs/examples/unity-game-example.md` — save-data format migration for a new progression system. Exercises save-schema versioning (SoT pattern 1), editor-asset ↔ runtime-object dual representation (pattern 8), IL2CPP / AOT build-time risk, and the full three-track rollback asymmetry (server-config mode 1, Addressables mode 1/2, shipped binary mode 2, on-disk save irreversible).

---

## Netcode / Multiplayer SoT discipline

Multiplayer introduces the hardest SoT problem in Unity: the authoritative state exists on a server (or host peer) but is mirrored to N clients, each of which locally predicts and reconciles. The "source of truth" is not a single place — it's a protocol with explicit authoritative windows.

### Authoritative-state SoT pattern

| Aspect | Pattern |
|--------|---------|
| Server-authoritative game state | Pattern 1 (Schema-Defined) + Pattern 6 (Transition-Defined) — only the server may validate transitions |
| Client-predicted state | Pattern 7 (Temporal-Local) — client's local truth is valid only until server reconciliation |
| RPC / message contracts | Pattern 4 (Contract) — every RPC signature, serialization, and ordering guarantee is a contract |
| Tick / frame authority | Pattern 4a (Pipeline-Order) — the simulation-tick pipeline order is itself a contract (input collection → prediction → network send → network receive → reconciliation → render) |
| Lobby / matchmaking state | Pattern 9 (Resolved/Variant) — client view resolves from matchmaking service + player prefs + platform identity |

### Required manifest fields when netcode is touched

- `surfaces_touched` must include `system_interface` (RPC / netcode messages) with `role: primary`
- Each RPC or networked message in `sot_map` must declare:
  - `pipeline_order` block if the message order is semantically load-bearing
  - `breaking_change.affected_consumers` separately for "server build at version N" and "client build at version M" (they are different consumers with different upgrade cadences)
- `breaking_change.migration_path` for anything beyond L0 on a networked protocol MUST be `parallel_switch` (protocol version negotiation), not `none` — there is always at least a week of mixed-version traffic during rollout
- `rollback.overall_mode` for netcode changes defaults to **mode 2** (forward-fix) — you cannot un-send a replicated state update; mode 1 is only possible if the change is gated behind a server-config flag

### Netcode-specific drift checks

- [ ] Adding a new RPC on client without matching server handler fails build (and vice versa)
- [ ] Changing a `[SerializeField]`-ed netcode message field without a version bump fails review
- [ ] Modifying the simulation-tick pipeline order (input → predict → send → receive → reconcile → render) requires explicit comment + replay-test evidence
- [ ] `NetworkVariable<T>` / replicated property type changes require migration notes; downgrading type is L2+
- [ ] Latency-sensitive changes (anything in the prediction pipeline) require a `playtest` entry with a latency-inflation scenario in the rubric

### Netcode anti-patterns

- ❌ Changing an RPC parameter type in one branch while another branch is still using the old server build → client crashes or silent wrong-field interpretation in mixed traffic.
- ❌ Client-authoritative state transitions for anything economy-relevant (cheat vector).
- ❌ Treating "latency spike on dev network" as flaky test — it's the primary failure mode you're shipping for.
- ❌ Rolling back a client binary while server has already advanced → protocol-mismatch on login, users think the app is broken.

### Multiplayer observability requirements

- Per-player tick drift metric
- Per-connection RTT histogram, not just mean
- Desync event counter (client reconciled away > N units)
- Rejoin / reconnect success rate
- Cheat-detector event rate by category

---

## Console / platform-store publishing discipline

Console (and premium app-store) publishing introduces a rollback-asymmetry and uncontrolled-interface dimension that is qualitatively different from mobile app-store publishing:

- **Certification gates** add multi-week lead time between code-complete and consumer availability.
- **Platform-specific TRCs / lotchecks** each have their own rule sets that change every major platform generation.
- **Patch submission windows** are finite and expensive; a failed cert can delay a patch by weeks.
- **Store-front features** (achievements, trophies, DLC entitlements, cross-save) are themselves contracts with the platform.

### Console publishing SoT pattern mapping

| Concern | Pattern |
|---------|---------|
| Platform TRC / technical requirements | Uncontrolled interface + compliance surface |
| Achievement / trophy registry | Pattern 3 (Enum-Defined) + external consumer (platform) |
| Save-data format, including cross-save | Pattern 1 (Schema-Defined) + Pattern 10 (Host-Lifecycle) — console save systems have specific lifecycle contracts |
| DLC / entitlement manifest | Pattern 4 (Contract) + external consumer |
| Rating / age classification | Compliance surface |

### Required manifest fields for console builds

- `uncontrolled_interfaces` must include one entry per target platform's certification requirements bundle, with `monitoring_channel` pointing to the platform's developer portal release notes.
- `rollback.overall_mode`:
  - Live-ops config via server = mode 1
  - Patch submission = mode 2 at best (cert adds days-to-weeks)
  - Already-delivered in-game currency / entitlements via external store = mode 3 (compensation only)
- `breaking_change.migration_path` for save-data format changes must handle: old save on new binary (migration), new save on old binary (graceful rejection), cross-save conflict resolution.

### Console-specific drift checks

- [ ] Platform SDK version bumps trigger a certification-requirement re-read.
- [ ] Any new achievement/trophy in code has a matching entry in the platform's configured achievement list (detect with a per-platform `achievements-registry.json` mirror that CI compares against the live registry).
- [ ] Save-data format changes require a replay test with every prior shipped save version.
- [ ] Removing a DLC entitlement is L3 minimum (players who paid already own it); migration path is always `rename_and_coexist`.

### Console anti-patterns

- ❌ Assuming PC/mobile-style "ship hotfix immediately" works — console patches need submission-cycle awareness.
- ❌ Shipping a feature that "technically passes cert" but has platform-style-guide deviations that will block the next cert.
- ❌ Changing save-format at a minor patch — should be gated to a major version with explicit migration path.
- ❌ Treating cert failures as individual bugs — they are methodology-level post-mortems (what Phase of the process let this reach cert submission?).

---

## IL2CPP / AOT boundary discipline

Unity's IL2CPP (ahead-of-time compilation to C++) is required for iOS, consoles, WebGL, and most mobile release builds. Several Unity patterns that "work" in editor silently break post-IL2CPP:

### What IL2CPP breaks (and why it matters for SoT)

| Pattern | Editor behavior | IL2CPP behavior | SoT implication |
|---------|-----------------|-----------------|-----------------|
| Reflection over types not referenced statically | Works (Mono JIT) | Code is stripped; `TypeNotFoundException` | `cross_cutting.build_time_risk.minification_rules_touched` must be true; link.xml is the SoT |
| Generic virtual methods with value-type parameters | Works | `AOT will fail` at build time | Requires pre-registration via attribute or explicit instantiation |
| `System.Reflection.Emit` / runtime code gen | Works | Throws at runtime | Architecturally incompatible with IL2CPP targets |
| `JsonUtility` with generic lists of interfaces | Partial-works | Silently drops fields | Serialization contract must use concrete types |
| Expression trees, `dynamic` | Works | Compilation failure or runtime error | Ban at architecture level |
| Assembly loading at runtime | Works (editor) | Completely unsupported | Architecturally incompatible |

### IL2CPP as a build-time-risk SoT

The `link.xml` file (and related `link.xml` entries from referenced packages) is an authoritative SoT for what survives stripping. It is:
- Pattern 4 (Contract) with the IL2CPP toolchain
- Pattern 3 (Enum-Defined) — each `<preserve>` entry is a declaration
- A consumer of every reflection site in the codebase

### Required manifest fields when touching reflection-adjacent code

- `cross_cutting.build_time_risk.minification_rules_touched: true`
- `cross_cutting.build_time_risk.release_build_verified: true` (debug/Mono editor is NOT sufficient evidence)
- An `evidence_plan` entry of type `build_artifact` that is specifically a IL2CPP build with stripping enabled

### IL2CPP-specific drift checks

- [ ] Adding a `Reflection.GetType(string)` call without adding a `link.xml` `<preserve>` entry → flagged.
- [ ] Adding a new JSON-serialized DTO type without a generic instantiation attribute or concrete-type registration → flagged.
- [ ] Stripping level bumps (Low → Medium → High) trigger a full regression suite.
- [ ] `link.xml` changes in a PR require justification (shrinking = good, adding `<preserve>` = must show the specific runtime path that needs it).

### IL2CPP anti-patterns

- ❌ Testing only in editor / Mono and declaring a feature done — AOT specific bugs are undetected.
- ❌ `<assembly fullname="*" preserve="all"/>` as a workaround — defeats stripping entirely, bloats binary.
- ❌ Using reflection inside `Awake()` / `Start()` and hoping it works in release — silent null refs.

---

## Domain-specific Unity extensions

Unity targets are not homogeneous. The base bridge covers 2D/3D game patterns; these are additional overlays for specific domains:

### XR (VR / AR) overlay

- **Additional surfaces:** `experience` is even more load-bearing; add `physical_safety` as a new surface extension (motion sickness, IPD mismatch, guardian boundaries, hand-tracking dropout).
- **Performance-budget becomes stricter:** VR must hit target framerate (e.g. 72/90/120 Hz) with essentially zero misses; a single dropped frame is a felt failure, not a P95 statistic.
- **Additional uncontrolled interfaces:** each XR runtime (OpenXR provider implementations, platform-store-specific XR plugins) has distinct policies.
- **Rollback mode-3 scenarios:** users may have already played a motion-sensitive experience that caused discomfort — compensation-only.

### Mobile Unity overlay

- **Platform stack duplication:** mobile Unity apps are both a Unity app and a native mobile app; platform-specific plugins introduce the same vendor-OS-fork issues as the Android Kotlin bridge (see `android-kotlin-stack-bridge.md` §Vendor OS fork handling), layered on top of Unity's own asset/binary rollback asymmetry.
- **Battery / thermal budget** belongs in the performance-budget surface; not optional.
- **Store publishing** follows the same console-publishing discipline above, but with mobile-store specifics (longer review during major OS releases, app thinning).

### Live-service / GaaS overlay

- **Server-authoritative economy** is Pattern 1+6 with the server as SoT; every economy-affecting client-only change is L1 minimum because of exploitation risk.
- **Seasonal content rotation** treats the season schedule as Pattern 2 (Config-Defined) with compensation rollback if a season is pulled mid-run.
- **Balance patches** have L1 semantic effect on every active player; always require a compensation plan for "my favorite build just got nerfed" even though methodologically it's just L1.

### Industrial / enterprise simulation overlay

- **Physical-world coupling** adds `real_world` surface as primary if the simulation drives hardware (robotics, training rigs).
- **Compliance** often dominates: training simulators used for certification must match specifications with audit trails.
- **Determinism** becomes a first-class requirement — shared with netcode but for a different reason.

### DOTS / ECS overlay

> ⚠️ **API stability caveat.** The core `Entities` package is GA (1.x since 2023); public types like `IComponentData` / `ISystem` / `[UpdateInGroup]` have been stable across multiple minor versions. However, companion subpackages (Entities Graphics, DOTS Animation, Unity Physics for ECS, Netcode for Entities) each have their own release cadence and some remain in preview / experimental channels. Treat this overlay as *pattern-level* — the pattern bindings (Pattern 1 for `IComponentData`, Pattern 4a for `[UpdateInGroup]`) are stable; specific API names in companion subpackages should be pinned in your project's `packages-lock.json` with a project-local note citing the exact subpackage versions verified.

DOTS (Data-Oriented Tech Stack) / ECS (Entity Component System) inverts several ownership assumptions the base bridge makes. GameObject/MonoBehaviour ownership is replaced by **archetype-based component storage + system execution graph**, which changes how Pattern 1 (Schema-Defined), Pattern 4a (Pipeline-Order), and Pattern 8 (Dual-Representation) bind.

#### Surface remapping for ECS

| Base-bridge concept | ECS remapping |
|---|---|
| ScriptableObject state container | Pure `IComponentData` + optional `IBufferElementData` — data-only; no methods |
| MonoBehaviour lifecycle | `SystemBase` / `ISystem` with `OnCreate` / `OnUpdate` / `OnDestroy` |
| Prefab | Subscene baking → baked Entity + components; authoring prefab is editor-only |
| Script Execution Order | `[UpdateInGroup]` / `[UpdateBefore]` / `[UpdateAfter]` attributes on systems |
| Physics / Animator | Unity Physics (ECS) and DOTS Animation (separate subpackages) — NOT classic Physics or Animator |

#### SoT pattern bindings (ECS-specific)

| Pattern | ECS instance |
|---|---|
| 1 Schema-Defined | `IComponentData` struct field layout ↔ baked entity in subscene ↔ archetype storage — **three-way dual-representation** |
| **4a Pipeline-Order** | **System update order** via `[UpdateInGroup(typeof(X))]` attribute graph — this replaces ScriptExecutionOrder and is *the* canonical ECS SoT risk |
| 6 Transition-Defined | State transitions via tag components (adding / removing component = state change) — exhaustive-query discipline is the check |
| 8 Dual-Representation | Authoring GameObject hierarchy → Baker → Entity world; the Baker is the explicit sync step |

#### Build-time risk amplification

DOTS amplifies IL2CPP / AOT risk because:

- Burst-compiled jobs (`[BurstCompile]`) have their own subset of C# — runtime-only validation that editor won't catch
- Generic system queries require concrete type registration for AOT targets (similar to generic-value-type issue but with ECS types)
- Source generators (for `ISystem` codegen) must be compatible with the specific Entities package version

Add to manifest for any ECS-adjacent change:

- `cross_cutting.build_time_risk.burst_compile_verified: true` — a Burst-specific compile pass, not just a regular IL2CPP build
- `cross_cutting.build_time_risk.ecs_baker_reverified: true` — subscene bake output reproduced identically across two clean builds

#### ECS-specific drift checks

- [ ] System update-order graph (`[UpdateInGroup]` + `[UpdateBefore/After]`) changes require an explicit `pipeline_order` entry in the manifest — swapping system order is behavioral (L1) minimum.
- [ ] Adding a new `IComponentData` field without updating the authoring Baker → baked entities silently omit the field. A baker-roundtrip test must cover every authoring type.
- [ ] Generic job types with new type parameters at AOT targets — add a concrete-instantiation attribute or a dummy reference site.
- [ ] Mixing GameObject and ECS code paths is an anti-pattern to audit; hybrid conversion adds *more* dual-representation, not less.

#### ECS anti-patterns

- ❌ Calling `SystemAPI.Query` without an exhaustive component-archetype discipline — silent entity misses in production.
- ❌ Storing managed references (class, string) in `IComponentData` — breaks Burst; use `FixedString*` or blob assets.
- ❌ Relying on ScriptExecutionOrder for ECS systems — SEO does not control ECS system ordering.
- ❌ Upgrading the Entities package without re-running the full Baker + Burst + IL2CPP matrix.

---

## Render pipeline variant discipline

URP / HDRP / built-in RP differ materially enough that shader / material / lighting assets are **pipeline-specific** in ways that break the base bridge's asset-identity assumptions. A project is effectively **one** render pipeline at a time; pipeline switches are a migration event, not a config toggle.

### Pipeline as an uncontrolled-interface-adjacent concern

| Pipeline | Shader authoring | Lighting model | Asset compatibility |
|---|---|---|---|
| Built-in RP | Legacy `.shader` + Surface Shaders | Forward / Deferred legacy paths | Most store / tutorial assets default here |
| URP | Shader Graph (URP target) or `.shader` with URP pragmas | Forward+ | Built-in-RP shaders render pink; migration or shader rewrite required |
| HDRP | Shader Graph (HDRP target) or `.shader` with HDRP pragmas | Physically-based forward + compute-heavy | URP content needs retargeting; cross-platform support narrower |

### SoT implications

- **Shader asset** is Pattern 1 (Schema-Defined) with pipeline as an implicit *target* field; migrating a project's pipeline is a migration across every shader asset — L3 by default on the asset surface.
- **Lit / Unlit material swaps** when switching pipelines are dual-representation (Pattern 8) drift events — the `.mat` file's referenced shader GUID changes meaning under a new pipeline.
- **Quality / tier settings** (`UniversalRenderPipelineAsset`, `HDRenderPipelineAsset`) are Pattern 2 (Config-Defined) — each asset is a config surface; per-tier fan-out must be declared.

### Per-pipeline manifest requirements

When a change touches shaders, materials, lighting, post-processing, or camera setup:

- `surfaces_touched.asset` must declare the render pipeline as a qualifying context
- `cross_cutting.build_time_risk.shader_variant_count_verified: true` — shader variants explode quickly with URP/HDRP keyword sets; a variant-count regression is a build-size / runtime-compile-stall risk
- Performance-budget surface evidence must be captured **on the target pipeline**, not switched mid-capture (compiled shader variants differ)

### Pipeline-migration as a separate event

Switching a project's render pipeline (built-in → URP, URP → HDRP) is a multi-week migration, not a PR:

- Dedicated `migration-rollout` change (see `docs/change-decomposition.md`)
- Freeze new shader / material authoring during migration (to avoid authoring in the old target)
- Asset conversion tooling (URP `2D Renderer Converter`, HDRP `Wizard`) is an adapter, not a ground truth — manual review of every converted asset
- Rollback: mode 3 compensation on the asset surface (converted-back assets are not byte-identical)

### Render-pipeline drift checks

- [ ] Every `.shader` / Shader Graph asset declares its target pipeline; CI fails on a shader with ambiguous or mismatched target.
- [ ] Shader variant count checked in release-build artifacts — exceeding the declared budget is build-time risk.
- [ ] `.mat` files referencing shaders from a non-project pipeline are flagged (copy-paste from asset store is the common cause).
- [ ] Per-platform pipeline assets (mobile URP vs. desktop HDRP in a dual-target project) must have matching feature sets or the mismatch is declared.

---

## Custom engine fork discipline

Teams maintaining a **modified Unity engine** (either via source-access license or via binary patching) inherit an extra SoT layer that the base bridge's Pattern 8 (Dual-Representation) does not account for.

### The fork SoT layer

A custom fork adds a new authoritative axis: *this project's Unity* is not the same as *vanilla Unity x.y.z*. Every piece of behavior that the base bridge attributes to "Unity" must be disambiguated:

| Concern | Vanilla Unity | Custom fork |
|---|---|---|
| `.meta` GUID ownership | Unity editor owns the format | Fork may add per-fork metadata fields → compatibility break if upstreamed |
| `.unity` / `.prefab` YAML serialization | Unity-version-specific schema | Fork-version-specific schema; two forks of the same base version may have divergent dialects |
| Asset import pipeline | Unity's AssetImportContext | May be hooked / replaced; a base-version upgrade may require re-doing the hook |
| Editor scripting API | Stable-ish across Unity minors | Fork may add or remove APIs; upstream sync breaks call sites |

### Fork-specific SoT patterns

| SoT pattern | Fork-specific instance |
|---|---|
| 1 Schema-Defined | Engine source tree + patch set + build config |
| 2 Config-Defined | Fork-specific build flags (e.g., stripped features, added subsystems) |
| 4 Contract-Defined | Fork patch set as a contract with upstream — rebase onto new Unity version is the sync step |
| supply-chain (extension) | Upstream Unity release tags are an uncontrolled interface from the fork's perspective; patch re-applicability is the drift metric |

### Required manifest fields for fork-impacting changes

- `uncontrolled_interfaces` entry: `unity-upstream`, with `monitoring_channel` pointing to Unity's release notes for the pinned base version
- `sot_map` entry for any custom engine subsystem, with `source.location` naming both the fork branch/tag AND the patch file set
- `cross_cutting.build_time_risk`:
  - `engine_build_reverified: true` — editor build + player build of the fork both reproduced
  - `patch_apply_status` — clean / manual-resolution / conflict-in-vendor-directory

### Fork-maintenance drift

- [ ] Fork has a `UPSTREAM.md` or equivalent naming the exact upstream tag / commit — not just "Unity 2022.3"
- [ ] Patch set is version-controlled as an explicit list, not an accumulated diff — each patch has a reason and an owner
- [ ] Rebase-onto-new-upstream is a tracked change (migration-rollout type); cadence declared (e.g., "rebase every LTS minor")
- [ ] `.meta` / `.unity` / `.prefab` serialized files in the project repo must be tagged with the fork version that produced them — migrating a project across fork versions is its own change

### Fork anti-patterns

- ❌ "We fixed it in our engine" without a patch entry — that fix lives only in whoever pressed the button, and disappears on next upstream rebase.
- ❌ Sharing assets between a fork-project and a vanilla-Unity project without a compatibility test — silent serialization drift.
- ❌ Treating upstream Unity upgrades as routine when the fork has hooked asset pipelines or serialization — upgrade is an overlay migration.
- ❌ Letting fork deviation grow without a "give up and return to vanilla" deprecation plan — every fork needs an exit strategy on record.

---

## Validating this bridge against your project

### Self-test checklist

- [ ] **Meta file integrity test** — delete a `.meta` file locally; confirm Unity/CI regenerates it with a different GUID and confirm your CI or a pre-commit hook catches the loss.
- [ ] **Addressables catalog freshness** — change a prefab that's referenced in a remote Addressable group without rebuilding the catalog; confirm CI flags it.
- [ ] **Script Execution Order audit** — enumerate all scripts with non-default execution-order priority; is the priority-to-reason mapping documented in a single file? If not, that file is your first improvement.
- [ ] **IL2CPP build in CI** — does your CI do at least one IL2CPP/AOT build per release branch? If not, you're trusting editor tests for AOT-only bugs.
- [ ] **Netcode protocol version check** — if you ship a multiplayer change, does the RPC registry have a version comparison test in CI?
- [ ] **Save-data migration test** — take a save from the oldest still-supported version; does it load cleanly on `HEAD`?
- [ ] **Platform-cert compliance tracker** — is there a living document of cert requirements per platform, with a last-reviewed date? Quarterly review minimum.

### Known limitations of this bridge

- **Specific DOTS / ECS API drift** — the DOTS/ECS overlay captures pattern-level bindings; concrete `Entities` / `Burst` / `Jobs` package API names shift between minor versions and are pinned in your project's `packages-lock.json` with a project-local note.
- **Mixed Unity + native frameworks** (Flutter / React Native hosting a Unity view, Unity embedded in a native host app) introduce interop-boundary SoT issues not covered here — those sit at the intersection of this bridge and the hosting platform's bridge.
- **Cloud save / cross-progression across stores** has authorization-layer complexity (identity federation, account merging, regional data-residency) that is platform-specific and left project-local.
- **Shader / asset-store vendor compatibility matrices** — the render-pipeline overlay covers pipeline targeting; per-asset-vendor (e.g., specific Asset Store pack) compatibility matrices are project-local.
- **Fork-specific tooling ecosystems** — the custom-fork overlay covers the SoT and drift discipline. Fork-specific internal tooling (custom editor extensions, asset importers) inherits its own documentation requirement beyond this bridge's scope.

For the project-local overlay pattern (Unity UaaL, visual-scripting graphs, platform-specific cross-progression, asset-vendor compatibility matrices, etc.), see [`../bridges-local-deviations-template.md`](../bridges-local-deviations-template.md) and the end-to-end walk-through in [`../bridges-local-deviations-howto.md`](../bridges-local-deviations-howto.md).

---

## What this bridge does NOT override

- Surfaces, manifest, operating contract remain universal.
- This bridge maps Unity's editor/runtime duality (canonical dual-representation case) and the asset / experience / performance-budget surface extensions — but the methodology's definitions of those extensions live in `docs/surfaces.md`.
