# Android Kotlin + XML Stack Bridge

> Maps the tool-agnostic methodology to a traditional Android app stack: Kotlin + XML layouts + Jetpack libraries. Bridges are the only layer allowed to name specific tools.

---

## Scope

**Applies to:** Native Android apps written in Kotlin with XML-based layouts (ViewBinding / DataBinding), targeting API levels set by the team, using Gradle (Kotlin DSL or Groovy) and a standard Jetpack stack.
**Compose-first projects:** see the companion [`android-compose-stack-bridge.md`](./android-compose-stack-bridge.md); this document assumes XML layouts with optional Compose interop. The Compose bridge inherits Room / WorkManager / FCM / runtime-permission / vendor-fork / deep-link / ProGuard-R8 sections from here and overlays Compose-specific deltas.

---

## Surface mapping

> Machine-consumable surface → file-glob mapping lives in
> [`android-kotlin-surface-map.yaml`](./android-kotlin-surface-map.yaml) and
> is consumed by validator rule 3.2 (surface ↔ file-pattern drift).

### User surface

| Concept | Concrete implementation |
|---|---|
| screens | `Activity` / `Fragment`, `NavGraph` destinations |
| layout | `res/layout/*.xml`, `res/layout-<qualifier>/*.xml` |
| components | Custom views, `<include>`, `<merge>`, ViewBinding-generated binding classes |
| interaction | Click / gesture listeners, `MotionLayout`, `Transition` framework |
| copy / i18n | `res/values/strings.xml`, `res/values-<locale>/strings.xml` |
| state | ViewModel + `StateFlow` / `LiveData`, saved state handle |
| validation | Form logic in ViewModel; `TextInputLayout` + error messages |
| a11y | `contentDescription`, `importantForAccessibility`, focus order, TalkBack verification |

**Verification surface:**
- `./gradlew test` for unit tests (Robolectric where needed)
- `./gradlew connectedAndroidTest` for instrumentation
- Espresso / UIAutomator for UI
- Screenshot tests via `Paparazzi` / `Shot` / `Roborazzi`

### System interface surface

| Concept | Concrete implementation |
|---|---|
| REST | Retrofit + OkHttp + interceptor chain |
| GraphQL | Apollo Kotlin with generated types |
| Push | FCM or platform-neutral equivalent |
| Deep links | intent-filter in `AndroidManifest.xml` + `NavDeepLink` |
| IPC | `Intent`, `ContentProvider`, bound `Service`, AIDL |
| Platform APIs | Permissions declared in `AndroidManifest.xml`, runtime permission request |

**Uncontrolled-interface register:**
- Android OS version behaviour changes per API level
- Google Play policy (privacy labels, data safety, target SDK deadlines)
- Store review timelines
- AndroidX / Jetpack library breaking releases
- Native dependencies (NDK, ABI changes)

### Information surface

| Concept | Concrete implementation |
|---|---|
| DB schema | Room entities + auto-generated migrations + `RoomDatabase.Schema` exported JSON |
| Shared prefs / DataStore | Keys registered in a single typed facade |
| Feature flags | Remote config + local override file for dev builds |
| Enums / sealed classes | `enum class` / `sealed class` / `sealed interface` |
| Resources | `res/values/*.xml`, qualifiers (screen size, night mode, locale) |

### Operational surface

| Concept | Concrete implementation |
|---|---|
| Logs | `Timber` + tree with redaction |
| Crash | Crashlytics / Sentry / platform equivalent |
| Analytics | Single event registry Kotlin file |
| ProGuard/R8 | `proguard-rules.pro`, keep rules, mapping file retention |
| Signing | `app/signing-config.properties` (not in repo), key in secret store |
| Release channels | Internal / Closed / Open testing / Production |

---

## SoT pattern bindings

| Pattern | Android instance |
|---|---|
| 1 Schema-Defined | Backend DTO → Moshi/Kotlinx-serialization data class |
| 2 Config-Defined | Remote config, BuildConfig flags, `gradle.properties` |
| 3 Enum/Status | `enum class` / `sealed class`; `when` must be exhaustive |
| 4 Contract-Defined | Retrofit interface + DTO, OpenAPI spec |
| 4a Pipeline-Order | OkHttp `Interceptor` order (`application` vs `network`), `WorkManager` chain |
| 6 Transition-Defined | Finite state machine in ViewModel / `sealed class`; `androidx.lifecycle.Lifecycle` itself is transition SoT |
| 7 Temporal-Local | Room + `WorkManager` sync queue |
| 8 Dual-Representation | **`res/layout/*.xml` ↔ generated `ViewBinding` class**; **Room `@Entity` ↔ generated schema JSON + actual DB schema**; **`@Parcelize` ↔ generated writeToParcel** |
| supply-chain (extension) | `build.gradle.kts` + `libs.versions.toml` + lock files |

---

## Rollback mode defaults

| Layer | Default mode |
|---|---|
| Behind remote feature flag | Mode 1 |
| Released APK / AAB | Mode 2 forward-fix — Play Store rollback is partial (users already updated stay on new version) |
| Room migration applied | Mode 2 (forward-only migrations; destructive migrations flag must be disabled in production) |
| Push / in-app message sent | Mode 3 compensation |
| Granted runtime permission revoked | Mode 2 — require graceful degradation |

**Minimum supported API level** declared in `build.gradle` and enforced by `minSdk`; below that is automatically excluded from Play distribution.

---

## Cross-cutting concerns bindings

- **Security:**
  - Permissions declared in `AndroidManifest.xml`, justify each at review
  - `networkSecurityConfig` pinning for sensitive endpoints
  - `android:allowBackup="false"` for sensitive apps
  - Secrets via Keystore / EncryptedSharedPreferences, never in strings.xml or BuildConfig
  - ProGuard/R8 rules audited for obfuscation and keep rules; mapping file kept for stack trace deobfuscation
  - App signing via Play App Signing; upload key separate
  - `exported` attribute explicit on every component
- **Performance:**
  - Startup time budget tracked (cold / warm / hot)
  - Frame-rate via `FrameMetricsAggregator`, jank monitored in production
  - APK / AAB size budget (per ABI split if relevant)
- **Observability:** ANR / crash rate per release, Play Vitals as operational evidence
- **Testability:** Hilt / Dagger for injection to make ViewModels testable; keep View logic minimal
- **Error handling:** exceptions at data layer → sealed Result at repository → user-safe text at UI (asymmetric responsibility)
- **Build-time risk:** R8 configuration, annotation processors, kapt vs ksp, Gradle plugin version drift

---

## Automation-contract implementation

### Layer 1 — Structural validity

```bash
# Using any JSON Schema validator; the validator must output <pass|fail> <path> <rule_id> <sev> <msg>
./gradlew verifyChangeManifests  # custom task wrapping the validator
```

### Layer 2 — Cross-reference consistency

Android-specific drift checks to ship in bridge CI:

1. **Resource drift:** `ViewBinding` regeneration after layout change — CI can compile and compare.
   ```bash
   ./gradlew assembleDebug
   ```
2. **Room schema drift:** exported schema JSON must match entity classes.
   ```bash
   ./gradlew :app:compileDebugKotlin
   git diff --exit-code app/schemas
   ```
3. **Resource localization drift:** every non-empty `<string>` in default `strings.xml` must have a translation or an explicit `translatable="false"`.
4. **Manifest permissions audit:** any new permission in `AndroidManifest.xml` requires a matching `threat_model` note in the change manifest.
5. **Dependency lock drift:** `libs.versions.toml` change requires updated lock file.

### Layer 3 — Drift detection

Weekly on `main`:
- Unused permissions (declared but never requested at runtime)
- Exported components without intent-filter rationale
- Deprecated API usage against current `compileSdk` target
- Phase 8 observation overdue for crash-sensitive changes

---

## Multi-agent handoff conventions

- `manifests/<change_id>.yaml` at repo root or `docs/manifests/`
- Commit trailer: `Change-Id: <change_id>`
- Implementer ensures `./gradlew assembleDebug testDebugUnitTest` passes before handoff
- Reviewer verifies Play Console evidence (Internal Testing APK upload, vitals snapshot) when relevant

---

## Typical workflow per task type

| Task | Mode | Minimum artifacts |
|---|---|---|
| String copy change | Zero ceremony | strings.xml update |
| Layout tweak (dp / color) | Lean | screenshot / golden test |
| New Room entity or column | Full | migration + exported schema + rollback mode 2 note |
| New runtime permission | Full | manifest permission + UX rationale + threat_model entry |
| FCM integration change | Full | mode 3 note for already-sent + Play policy check |
| Target SDK bump | Full | uncontrolled_interfaces update + behavior change audit |
| Minify/R8 rule change | Full | keep rules + deobfuscation verification |

---

## Reference worked example

See `docs/examples/android-kotlin-example.md` — "Add offline draft-saving to a form." Exercises:

- User surface: form Fragment + ViewBinding + restore-from-process-death banner
- System interface: Retrofit `Idempotency-Key` header for retry safety
- Information surface: Room entity `DraftEntity` + forward-only migration v7→v8 + exported schema JSON
- Operational surface: WorkManager sync chain with enforced unique-work name, analytics events, vendor-fork observability
- SoT: `DraftEntity` as schema-defined (pattern 1); sync state as transition-defined (pattern 6); local-before-synced as temporal-local (pattern 7); WorkManager unique names as enum (pattern 3); entity class ↔ exported schema JSON as dual-representation (pattern 8)
- Rollback: UI behind remote flag (mode 1); APK forward-fix (mode 2); Room migration forward-only (mode 2)

---

## Background execution discipline (WorkManager / Services)

Android's background execution story is fragmented: `WorkManager`, `ForegroundService`, `JobScheduler`, `AlarmManager`, and direct `Coroutine` launches each have different guarantees, constraints, and failure modes. Mapping this to the methodology:

### Background-work SoT pattern mapping

| Component | Primary SoT pattern | Why it matters |
|-----------|---------------------|----------------|
| **WorkManager job definition** | Pattern 4 (Contract) + Pattern 10 (Host-Lifecycle) | Input/output data schema is a contract between the scheduler and the worker; the worker runs in a new process potentially after process death |
| **Worker input data** | Pattern 1 (Schema-Defined) — `workDataOf()` key-value map | Schema drift between enqueue site and worker will silently coerce to null |
| **Unique work name** | Pattern 3 (Enum/Status-Defined) — treat unique names as a closed enum | Typo in unique name silently creates a parallel queue |
| **Foreground service notification** | Pattern 5 (UI-Defined) + compliance surface | OS-enforced contract: no notification = crash on some OS versions |
| **Service lifecycle** | Pattern 10 (Host-Lifecycle) | Process death during execution is expected; worker must be idempotent |

### Required manifest fields when background work is touched

- `surfaces_touched` MUST include `operational` (primary) and `system_interface` (consumer) if work talks to a server.
- `uncontrolled_interfaces` MUST include entries for:
  - `platform_os` — background-execution policy for the minSdk ↔ targetSdk range (doze, app-standby, restricted bucket, background-activity launch)
  - `store_policy` if your app depends on any policy-sensitive capability (exact alarms, foreground-service types, SMS/call background)
- `rollback.per_surface_modes` MUST distinguish between "code rollback" (APK) and "work queue state rollback" (persisted in the worker DB — cannot be rolled back by shipping a new APK).

### Background-work specific drift checks

- [ ] Any new WorkRequest without a matching unique-work name declaration flagged in review
- [ ] Any new Worker class without a registered expected-input-schema comment flagged in review
- [ ] `compileSdk` / `targetSdk` bump → re-audit all background workers against new OS background policies (this is ALWAYS a `uncontrolled_interfaces` update)
- [ ] `foregroundServiceType` additions must be justified in manifest `rationale`; Google Play review will reject mismatches

### Anti-patterns specific to Android background work

- ❌ Launching a `Coroutine` in a ViewModel or Activity for long-running work (dies when process goes to background).
- ❌ Using `WorkManager` for tasks that need to complete within a window shorter than ~10s; the scheduler may defer heavily on restricted devices.
- ❌ Relying on `AlarmManager` exact alarms without declaring the permission and handling the user-revocation path.
- ❌ Hard-coding `setExpedited` assuming quota — quota is device-local, resets daily, is reset on reboot differently across vendors.

---

## Vendor OS fork handling

Android is one API, N OS behaviors. Major vendor forks introduce their own background-execution policies, battery-optimization whitelists, notification-delivery quirks, and default-permission-revocation behaviors.

### Treating vendor OS forks as uncontrolled interfaces

Each vendor OS family you support should appear as a separate entry in `uncontrolled_interfaces`:

| Vendor family | What to track | Typical surprise |
|---------------|---------------|------------------|
| AOSP-compliant (stock Pixel, Android One) | Baseline behavior | The behavior documented in official Android docs |
| East-Asian OEM forks (large market share region-dependent) | Background-execution whitelist UX, app-autostart management, notification-permission defaults | Apps removed from recents = process killed immediately; user-invisible whitelist required |
| Enterprise / MDM forks | Policy-enforced restrictions, app-install channels | Methodology's "rollback mode 1" may be blocked by MDM update-deferral |
| Regional / certified variants (CN market, industrial OEMs) | Services framework absence, alternative push channels | Firebase/Google push SDK does not work; alternative push provider required — a full alternative system-interface |

### Vendor-fork self-test checklist

- [ ] Identify the top 3 vendor OS families in your install base (from Play Console / Firebase Analytics device reports).
- [ ] For each family, document which baseline-Android behaviors are overridden in `docs/bridges/android-vendor-overlays.md` (project-local).
- [ ] Schedule a quarterly "vendor drift check": visit each family's release notes and update the entry.
- [ ] Never assume "works on Pixel = works everywhere" in Phase 6 sign-off.

---

## Deep link consumer registry

Deep links (scheme URIs, App Links / Universal Links, dynamic links) are a consumer surface that is invisible to the type system: the type contract is the URL pattern, not a Kotlin interface.

### Deep links as a Pattern 4 + Pattern 3 SoT

- The **URL-pattern catalog** is the contract (Pattern 4).
- The **set of recognized hosts / path prefixes / deep-link schemes** is an enum (Pattern 3): adding a new one is L0, removing is L3, reusing a path for a new destination is L4 (semantic reversal).
- Each deep link has multiple consumers: internal code routing, the OS's intent resolver, search engines indexing AppLink-verified URLs, Smart Text / link previews, marketing campaigns, email templates, referral flows, third-party partners embedding your links.

### Required deep-link consumer registry fields (per `team-org-disciplines.md`)

For each deep link pattern, maintain:

| Field | Meaning |
|-------|---------|
| `pattern` | The URL pattern (e.g. `/product/{id}`) |
| `destination` | Internal screen / route |
| `since_version` | First app version that recognized this pattern |
| `deprecated_since` | Version where deprecation was announced (if any) |
| `sunset_version` | Version where it stops working |
| `external_consumers` | Who publishes / depends on this link outside the app |
| `domain_verification` | For AppLinks: is the domain autoVerified? |

### Deep-link specific drift checks

- [ ] Every `<intent-filter>` in `AndroidManifest.xml` with a `VIEW` action has a matching entry in the deep-link registry.
- [ ] Adding a new intent-filter in a PR triggers a registry-update requirement (CI check).
- [ ] Removing an intent-filter without a `deprecated_since` + `sunset_version` is blocked (L3 breaking change requires deprecation timeline).
- [ ] `assetlinks.json` hosted on the verified domain matches the app's declared AppLinks (an `uncontrolled_interfaces` drift check).

### Deep-link anti-patterns

- ❌ Renaming a path pattern "for consistency" — external links continue to point at the old name; this is L4 silent semantic reversal.
- ❌ Handling deep links in an Activity's `onCreate` without checking for intent freshness — back-navigation can re-trigger the link.
- ❌ Forgetting to add the new deep link to the domain's `assetlinks.json` — AppLinks silently stop auto-verifying and fall back to the disambiguation dialog.

---

## Kotlin Multiplatform Mobile (KMM) shared-code SoT

KMM projects split code across `commonMain`, `androidMain`, `iosMain` (and optionally `jvmMain`, `jsMain`, etc.). The shared code is a SoT consumed by N platform-specific consumers — the same methodological pattern as a federated plugin in Flutter, but the boundary runs through the Kotlin type system.

### KMM SoT pattern mapping

| Aspect | Pattern |
|---|---|
| `expect class` / `expect fun` in `commonMain` | Pattern 4 (Contract) — the IDL between shared code and each target |
| `actual` implementations per target | Pattern 4 + Pattern 8 (dual representation: `expect` declaration ↔ each `actual`) |
| Shared domain model / DTO | Pattern 1 (Schema-Defined) — `@Serializable` data class lives in `commonMain`, consumed by both platforms |
| Per-target dependency injection | Pattern 4a (Pipeline-Order) — each platform's DI container resolves `actual` implementations in a specific order |
| Binary artifact (Android AAR, iOS XCFramework) | Pattern 8 (build-time dual representation: `commonMain` sources ↔ per-target compiled artifact) |

### Required manifest fields when touching KMM shared code

- `surfaces_touched` must list every consuming target separately (e.g., `android_app`, `ios_app`). A change to `expect fun foo()` without updating every `actual` is a compile-time block on one target and a silent missing-symbol at link on the other.
- `breaking_change.affected_consumers` is **per-target** for any change to `commonMain` public API — adding an `expect` method is L2+ until every `actual` is shipped.
- `evidence_plan` must include at least one build per target, not just `:shared:assembleDebug`.

### KMM-specific drift checks

- [ ] Every `expect` declaration in `commonMain` has a matching `actual` in every target's source set. A CI job runs `./gradlew :shared:compileKotlinAndroid :shared:compileKotlinIosArm64` (etc.) — not only the JVM default.
- [ ] XCFramework / AAR version bump: if the shared module's version constant advances, the iOS Podfile / Swift Package and the Android `implementation project(":shared")` consumers are all updated in the same change.
- [ ] Cross-platform serialization: `@Serializable` classes in `commonMain` produce identical JSON on both targets (test with the same input through both Android and iOS code paths).

### KMM anti-patterns

- ❌ Using `actual typealias` to a platform-specific class that has a different public API on iOS vs Android → the shared consumer accidentally binds to platform-specific API without the type system flagging it.
- ❌ Putting mutable singletons in `commonMain` without thread-safety treatment — iOS Kotlin/Native has different memory model rules than Android JVM (the new memory model is default now but older projects still carry the old-model assumptions).
- ❌ Shipping a shared module where the Android target uses JVM-resolved `java.time.*` and the iOS target uses `kotlinx-datetime`; behavior drifts on DST boundaries.

---

## Play Feature Delivery (on-demand modules)

Play Feature Delivery (dynamic feature modules, install-time modules, on-demand modules) splits an app binary into multiple sub-APKs delivered through the store. Rollback asymmetry is no longer two-track — it becomes multi-track, one per dynamic module.

### Dynamic-module SoT pattern mapping

| Module type | Rollback characteristic |
|---|---|
| **Install-time module** | Same rollback as the base APK — ships together, rolls back together (mode 2) |
| **Conditional module** (device meets criteria) | Mode 2 per-condition cohort; users on devices that no longer match criteria see the module disappear at next install |
| **On-demand module** | Mode 2 for the module itself, but the **request path** (user-triggered download) has mode-3 characteristics: a user who already triggered and cached an old module may run it offline long after a rollback |
| **Instant-app module** | Same as on-demand, plus Google Play-specific cache TTL |

### Required manifest fields when touching dynamic modules

- `surfaces_touched` must list each dynamic module as an independent operational-surface deliverable (they have independent signing, independent release notes, independent rollout staging).
- `rollback.per_surface_modes` must call out the module-cache scenario: a user who downloaded a buggy on-demand module still runs it until they explicitly retry the download (ticket: "cache-invalidation behavior after store rollback is platform-specific and time-bounded").
- `uncontrolled_interfaces` adds the SplitInstallManager download reliability — module fetch can fail for reasons unrelated to your code (disk full, network class restriction, Play Services version on the device).

### Dynamic-module drift checks

- [ ] Every module declared in `build.gradle` `dynamicFeatures` has a matching `com.android.dynamic-feature` module that builds in isolation; CI runs `./gradlew :featureModule:assembleDebug` per module, not only the base.
- [ ] Resource merge: duplicate string / resource IDs across modules silently take the base-module value; a naming convention (module-prefix every resource) is an enforceable lint rule.
- [ ] On-demand module missing at runtime: every entry point goes through `SplitInstallManager.isInstalled()` before invocation, or has a user-facing "this feature is not installed" path.

### Play-Console operational-surface additions

- Staged rollout percentage per module (base and dynamic modules roll out independently).
- Per-module crash rate monitoring (Play Vitals separates by module but the default dashboard may not).
- "Halt rollout" on a dynamic module does not downgrade already-downloaded copies; a kill-switch server flag is the only immediate mitigation.

---

## Instrumented-test OS-API version discipline

Instrumented tests (`androidTest`) run against a specific emulator or device whose API level silently gates which tests execute and which skip. Several anti-patterns slip past code review:

### What the test runner does silently

| Scenario | Runner behavior |
|---|---|
| Test uses an API ≥ `minSdk` but > emulator API level | Test **skips** silently, reported as "not executed" (not a failure) |
| Test uses `@SdkSuppress(minSdkVersion = N)` | Skips on emulators below N, runs above — explicit opt-in |
| Test uses `@RequiresApi(N)` on the method | Compile-time check only; runtime does NOT gate the test |
| Mockable API behavior differs across API levels | Test passes on the CI emulator API level; ships a bug on others |

### Required manifest fields when adding an instrumented test

- `evidence_plan` must name the emulator API levels the test was verified on. `"emulator API 34"` alone is not evidence of `minSdk 24..targetSdk 34` coverage.
- `surfaces_touched` includes a `verification` surface entry if the test suite gains new conditional skips.

### Instrumented-test discipline

- [ ] CI runs instrumented tests on at least **min, mid, max** API levels of the declared support range, not only the latest.
- [ ] `@SdkSuppress` usage is audited: each occurrence names the API-level boundary and justifies why the behavior differs there (OS version note, not just convenience).
- [ ] Tests that touch `PackageManager`, `NotificationManager`, background-execution policy, or any Jetpack library with per-API-level behavior are explicitly marked with the tested API-level range.
- [ ] Silent-skip detection: the CI dashboard flags tests with execution count < (expected matrix size) — an always-skipped test is no test.

### Instrumented-test anti-patterns

- ❌ Adding a `@Test` method and verifying it on the default emulator only; the test silently skips on lower-API CI runs and the author never sees the skip.
- ❌ Using `@RequiresApi(N)` as a substitute for `@SdkSuppress(N)` — the compiler is happy; the runtime skips only at the method body, which can produce flaky pass/fail depending on execution path.
- ❌ Treating "passed on API 34" as evidence of coverage for `minSdk 24` — this is the most common gap that ships in otherwise-disciplined test suites.

---

## Validating this bridge against your project

### Self-test checklist (beyond the stock drift reproductions)

- [ ] **SoT mapping reality check** — pick 5 recent non-trivial PRs; does the bridge's SoT table correctly identify where the authoritative definition lived?
- [ ] **ViewBinding regeneration test** — add a new view id in a layout XML; confirm CI fails if the binding class is stale.
- [ ] **Room schema export verification** — bump schema version without providing a migration; confirm CI blocks.
- [ ] **Localization drift test** — add a new string in default `strings.xml` without a TODO for translations; confirm CI warns.
- [ ] **Permission manifest audit** — add a dangerous permission; confirm CI warns (`manifest.permissions_touched`).
- [ ] **WorkManager unique-name collision test** — submit two separate changes that both introduce the unique name `daily_sync`; confirm the consumer registry flags the collision.
- [ ] **Vendor-fork coverage** — for each of your top 3 vendor OS families, does the bridge have an entry? If not, you're shipping blind on that family.
- [ ] **Deep-link registry sanity** — parse your `AndroidManifest.xml`; is every `VIEW` intent-filter in the registry?

### Known limitations of this bridge

- **Jetpack Compose**-based apps have different state ownership and rendering semantics; this bridge targets XML + ViewBinding. Use the companion `docs/bridges/android-compose-stack-bridge.md` for Compose-first projects; it inherits Room / WorkManager / FCM / permission / vendor-fork / deep-link sections from this bridge and adds Compose-specific deltas.
- **KMM internals beyond the shared-code SoT section** — Kotlin/Native memory model edge cases, iOS framework export granularity, and Swift interop naming rules evolve quickly; the section above establishes the discipline, but per-project specifics belong in a local addendum.
- **Play Feature Delivery internals beyond the rollback table** — `SplitInstallManager` install-time-error code matrix, `PlayCore` library version compatibility, and instant-app-specific entry points are documented by Google and change per Play services version; project-local addendum recommended.
- **Play-Console-level controls** (staged rollout, internal testing track, managed publishing) are operational-surface concerns that this bridge references in sections above but does not fully enumerate — treat each control as a `uncontrolled_interfaces` entry with Google Play release-notes as the monitoring channel.

For the project-local overlay pattern (KMM-iOS depth, Play Feature Delivery internals, vendor-fork tooling, etc.), see [`../bridges-local-deviations-template.md`](../bridges-local-deviations-template.md) and the end-to-end walk-through in [`../bridges-local-deviations-howto.md`](../bridges-local-deviations-howto.md).

---

## What this bridge does NOT override

- Core four surfaces, manifest schema, operating contract — unchanged.
- This bridge only provides: SoT→file mapping, drift checks, toolchain examples, Android-specific cross-cutting binding.
