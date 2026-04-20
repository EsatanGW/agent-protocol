# Android Jetpack Compose Stack Bridge

> Maps the tool-agnostic methodology to a Jetpack Compose-based Android app.
> **Companion to `android-kotlin-stack-bridge.md`.** Sections on Room, WorkManager, FCM, runtime permissions, vendor-OS forks, deep links, ProGuard/R8, and Play Store release mechanics carry over unchanged — read the XML bridge first, then apply the Compose-specific deltas below.

---

## Scope

**Applies to:** Native Android apps written in Kotlin, using Jetpack Compose for the UI layer (no XML layouts, or XML only at the Activity root / interop boundary), with `androidx.navigation:navigation-compose` for navigation and a unidirectional-data-flow state pattern (ViewModel + `StateFlow` or `State<T>` holders).

**Not in scope for this bridge:**
- Compose Multiplatform (desktop/web/iOS targets) — needs a separate multiplatform bridge.
- Mixed XML-dominant + Compose-interop apps mid-migration — use the XML bridge and treat Compose screens as a local deviation until migration is the majority.

---

## Surface mapping

> Machine-consumable surface → file-glob mapping lives in
> [`android-compose-surface-map.yaml`](./android-compose-surface-map.yaml)
> and is consumed by validator rule 3.2 (surface ↔ file-pattern drift). The
> Compose map diverges from the XML map primarily in the user surface (code
> under `ui/` / `compose/` / `screen/` dirs instead of `res/layout/`).

---

## Delta summary vs. the XML bridge

| Concern | XML bridge answer | Compose bridge answer |
|---|---|---|
| UI-to-code binding | `ViewBinding` generated class (dual representation) | **No generated binding** — Compose is the UI SoT directly; no XML counterpart to drift against |
| Layout drift | XML vs binding vs runtime | **Recomposition drift** — mis-keyed state reads cause recompositions that look correct but drop frames |
| Pipeline-order SoT | OkHttp interceptor order, WorkManager chain | **Compose effect-API ordering + `CompositionLocal` provider nesting** (new Pattern 4a case) |
| Dual representation | XML ↔ ViewBinding; Room entity ↔ schema JSON | Room / Parcelize still dual-representation; **`@Preview` composable ↔ physical render** treated as a non-binding secondary representation |
| Verification | Espresso, Paparazzi | Compose UI Test (semantics tree), Paparazzi / Roborazzi with Compose support, `createComposeRule()` |
| A11y | `contentDescription` attributes | `Modifier.semantics { }` — different API, same discipline |
| Navigation SoT | `NavGraph` XML + Fragment destinations | `NavHost { composable("route") { } }` — routes are strings; treat the string catalog as a Pattern 3 enum |
| Inherited concerns | — | Everything else in the XML bridge (Room, WorkManager, FCM, vendor forks, deep links, ProGuard/R8, Play mechanics) applies as-is |

---

## Surface mapping

### User surface

| Concept | Concrete implementation |
|---|---|
| screens | `@Composable` functions, one per route; `NavHost { composable("home") { HomeScreen() } }` |
| reusable UI | `@Composable` functions, stateless preferred; state hoisted to the caller |
| interaction | `Modifier.clickable`, `pointerInput`, gesture detectors; animations via `animate*AsState`, `AnimatedVisibility`, `Transition` |
| copy / i18n | `stringResource(R.string.key)` reading from `res/values/strings.xml` (same as XML stack) |
| state | `remember { }`, `rememberSaveable { }`, `ViewModel + StateFlow.collectAsStateWithLifecycle()`, `mutableStateOf` |
| validation | In the state holder (ViewModel) or a dedicated `Validator` class; `TextField` surfaces errors via `isError` + supporting text |
| a11y | `Modifier.semantics { contentDescription = ... }`, `Modifier.clearAndSetSemantics`, focus order via `Modifier.focusRequester` |

**Verification surface:**
- `./gradlew test` for unit tests (state holders, pure logic)
- `./gradlew connectedAndroidTest` with `createComposeRule()` / `createAndroidComposeRule()` for UI tests
- Screenshot tests: Paparazzi or Roborazzi (both now support Compose); `@Preview` is NOT a verification artifact — it's an editor aid.

### System interface surface

Identical to the XML bridge. Retrofit / OkHttp / FCM / deep links behave the same regardless of UI layer.

### Information surface

Identical to the XML bridge for DB, DataStore, feature flags, and enums. Compose-specific additions:

| Concept | Concrete implementation |
|---|---|
| UI-local transient state | `remember { mutableStateOf() }` — scoped to the composable, lost on config change unless hoisted |
| Configuration-surviving state | `rememberSaveable { }` — serialized via `Saver` or auto for primitives |
| Process-death-surviving state | ViewModel + `SavedStateHandle` (unchanged from XML stack) |
| Screen state | `UiState` sealed class / data class in the ViewModel, exposed as `StateFlow<UiState>` |

### Operational surface

Identical to the XML bridge. Logging, crash reporting, analytics, ProGuard/R8, signing, release channels all behave identically. Compose adds one operational concern:

- **Compose compiler metrics.** The Compose compiler can emit stability / recomposition reports per module. These are operational-quality data, similar to APK size reports. Budget: no unexpected "unstable" classes in the hot path.

---

## SoT pattern bindings

| Pattern | Compose instance |
|---|---|
| 1 Schema-Defined | Identical to XML bridge (DB DTO → data class) |
| 2 Config-Defined | Identical |
| 3 Enum/Status | `enum class` / `sealed class` / `sealed interface`; `when` exhaustive — **critical in Compose `UiState` handling**, since `when` over a sealed `UiState` is the idiomatic render pattern |
| 3 Enum/Status (new case) | **Navigation routes** — `"home"`, `"profile/{id}"` — the string catalog is an implicit enum; typos are silent runtime failures |
| 4 Contract-Defined | Identical |
| **4a Pipeline-Order (new case)** | **Effect-API ordering inside a composable:** `LaunchedEffect(key)` vs `SideEffect { }` vs `DisposableEffect(key) { onDispose { } }` each run at different points in the composition lifecycle. Mis-ordering causes leaks or missed updates. |
| **4a Pipeline-Order (new case)** | **`CompositionLocal` provider nesting.** Providers lower in the tree override higher ones; a misplaced `CompositionLocalProvider` in a modal/dialog can silently lose theme or auth context |
| 6 Transition-Defined | `UiState` as `sealed class Loading / Success(data) / Error(e)`; transitions guarded in the ViewModel, never mutated directly from the composable |
| 7 Temporal-Local | Identical (Room + WorkManager story carries over) |
| **8 Dual-Representation** | Compose has **far less** dual representation than the XML stack. Remaining cases: Room entity ↔ schema JSON (unchanged), `@Parcelize` ↔ generated `writeToParcel` (unchanged). `@Preview` output is NOT treated as a binding representation — it's debug-only |
| supply-chain (extension) | Identical |

---

## Compose-specific pipeline-order discipline

### Effect APIs

| API | Runs when | Typical misuse |
|---|---|---|
| `LaunchedEffect(key) { }` | On first composition; restarts when `key` changes | Using `Unit` as key when the effect should react to state changes |
| `SideEffect { }` | After every successful recomposition | Performing expensive work here (it runs many times) |
| `DisposableEffect(key) { onDispose { } }` | On first composition; disposes when `key` changes or composition leaves | Forgetting `onDispose` → leak |
| `rememberCoroutineScope()` | Returns a scope tied to the composition | Launching long work that outlives the composition |
| `produceState(initial, key)` | Launches a coroutine; exposes a `State<T>` | Writing into the state outside the `produceState` block |

**Pipeline-order rule:** within a composable, `DisposableEffect`s run outer-to-inner for creation and inner-to-outer for disposal. If two `DisposableEffect`s register listeners on the same resource, the inner one's `onDispose` runs first — this is a contract, not an accident. Document the dependency if present.

### `CompositionLocal` nesting

`CompositionLocalProvider(LocalFoo provides myFoo) { Child() }` — the provider nesting order is a pipeline-order SoT. If `Child` reads `LocalFoo.current`, the most recent provider in its ancestor chain wins. A new provider in a dialog host that shadows an outer theme provider will silently give the dialog a wrong theme — the kind of bug UI tests catch only if they render the dialog path.

---

## State ownership discipline

Compose's unidirectional data flow is the primary correctness property. Three anti-patterns that violate it:

1. **Mutating hoisted state from a deeply-nested composable.** Pass lambdas down, not state objects. If a leaf composable is mutating a `MutableState` owned by an ancestor, state locality is already broken.
2. **Using `var` with `by mutableStateOf()` at top-level / object scope.** Compose state must be tied to a composition (`remember { }`) or a lifecycle-aware holder (ViewModel). Module-level `mutableStateOf()` bypasses both.
3. **Reading `StateFlow` with `.collectAsState()` instead of `.collectAsStateWithLifecycle()`.** The former collects even when the app is backgrounded; the latter stops. Almost every real-world case wants the latter.

### Verification

- Static check: a custom Lint rule or a grep for `MutableState` being passed as a parameter (instead of `State<T>` + lambda).
- Integration: a `StateRestorationTester` test proves the screen survives config change.

---

## Rollback mode defaults

Identical to the XML bridge — the rollback mechanics are determined by the *package* and *store*, not the UI framework. `Compose` itself is a library inside the APK, so it contributes to build-time risk (see below) but not rollback.

---

## Build-time risk

### Compose compiler as a toolchain contract

The Compose compiler plugin is a toolchain version contract. Specifically:

- `compose-compiler` version and `Kotlin` version are tightly coupled — a Kotlin bump without a matching compiler bump fails the build.
- The compiler version selected gates which Compose features are available; lock it in `libs.versions.toml`.
- Compiler metrics (`composeCompiler { reportsDestination = ... }`) produce per-module stability reports; treat unexpected "unstable" classes in the hot path as a drift signal.

### Manifest fields to mark

- `cross_cutting.build_time_risk.minification_rules_touched: true` if the change adds reflection or `Class.forName()` (rare in Compose but not impossible).
- `cross_cutting.build_time_risk.release_build_verified: true` — Compose release builds enable strong skipping and stability inference; behavior can differ from debug.

---

## Automation-contract implementation

### Layer 1 (structural validity)

Identical to the XML bridge.

### Layer 2 — Cross-reference consistency

Compose-specific drift checks to ship in bridge CI:

1. **Navigation-route string drift.** Collect all `composable("...")` routes and all `navController.navigate("...")` call sites. Any navigate-target not matching a declared composable is a typo. Either use a sealed route object (recommended) or a CI grep rule.
2. **Compose compiler metrics gate.** Run `./gradlew :app:assembleRelease -P composeCompiler.reportsDestination=build/composeReports`; fail if any class in the declared hot-path modules is marked `unstable` without a justification comment in that file.
3. **Preview parameter provider drift.** If `@Preview(showBackground = true)` uses a `PreviewParameterProvider<T>`, ensure the provider's output shape still matches `T` (the compiler catches this, but a CI check protects against accidental `@Suppress`).
4. **Lifecycle-aware state collection.** Grep for `.collectAsState()` without `.collectAsStateWithLifecycle()`. Every hit should either be migrated or carry a `// justified: not lifecycle-scoped because ...` comment.
5. **Semantics coverage.** Screens with no `Modifier.semantics` / `contentDescription` on interactive elements fail TalkBack; include a Roborazzi semantics-tree snapshot as a gate on new screens.

### Layer 3 — Drift detection

Identical to the XML bridge, plus:
- Compose compiler version vs. Kotlin version pairing drift against the official compatibility matrix.
- Unreferenced composables (declared but not called from any NavHost or screen) — stale code.

---

## Multi-agent handoff conventions

Identical to the XML bridge.

---

## Typical workflow per task type

| Task | Mode | Minimum artifacts |
|---|---|---|
| String copy change | Zero ceremony | `strings.xml` update |
| New composable within an existing screen | Lean | screenshot test (Paparazzi/Roborazzi) + state-hoisting review |
| New screen + route | Lean → Full if deep-linked | route entry + NavHost registration + screenshot + semantics test |
| New `CompositionLocal` | Full | justification for a new provider + provider-nesting audit + default-value policy |
| Compose compiler version bump | Full | Kotlin + compiler + library matrix update + release-build verification |
| Migrate an XML screen to Compose | Full | both bridges' self-tests run; screenshot parity test required |
| Room / WorkManager / FCM change | Defer to XML bridge | See XML bridge workflow |

---

## Reference worked example

Until a Compose-specific worked example is authored, use:

- `docs/examples/android-kotlin-example.md` for the **information + operational + system-interface** surface work (Room migration, WorkManager, sync). The UI portion (ViewBinding) translates into Compose as: stateless `ExpenseFormScreen(state, onFieldChange)` composable, state hoisted to `ExpenseFormViewModel`, `StateFlow<ExpenseFormUiState>` collected via `collectAsStateWithLifecycle()`.
- `docs/examples/mobile-offline-feature-example.md` for the offline + sync pattern at an architectural level.

---

## Validating this bridge against your project

### Self-test checklist (in addition to XML bridge items that still apply)

- [ ] **Route catalog check** — enumerate every `composable("route")` and every `navigate("target")` in the codebase. Do they match? If not, typos are silently failing in release.
- [ ] **Lifecycle-aware collection audit** — grep for `collectAsState()` (without `WithLifecycle`). Every hit must be justified.
- [ ] **State hoisting audit** — pick 5 leaf composables. Do any of them take a `MutableState<T>` / `MutableStateFlow<T>` as a parameter? (They should take `T` + `(T) -> Unit`.)
- [ ] **`CompositionLocal` provider audit** — list every custom `CompositionLocal`. For each, confirm the default value is either a safe no-op or throws a meaningful error; a silent default is a footgun.
- [ ] **Compose compiler metrics baseline** — run the metrics report, commit the current "stable / unstable" class list as a baseline. Future PRs diff against it.
- [ ] **Screenshot / semantics test coverage** — does every top-level screen have at least one screenshot test and one semantics-tree assertion? If not, start with the top 5 by traffic.
- [ ] **Preview vs. test divergence** — does a composable that looks correct in `@Preview` also render correctly in a Paparazzi / Roborazzi snapshot? If they diverge, the preview is lying (usually due to a missing CompositionLocal at preview time).

### Known limitations of this bridge

- **Compose Multiplatform** (desktop, iOS, web) — not covered. Those targets introduce separate toolchain contracts; a dedicated multiplatform bridge is the right answer.
- **Compose for Wear OS / TV** — shares core discipline but adds platform-specific input (rotary, D-pad) and surface concerns; deviations live in project-local addenda for now.
- **Mixing XML + Compose mid-migration** — either do Compose work through the XML bridge or define a clear per-screen ownership rule; dual-bridge ambiguity is a drift source.
- **Strong skipping / stability inference evolution** — the Compose compiler's stability rules change across versions; this bridge pins discipline but not specific compiler-version guidance.
- **Custom `Modifier` chains with undocumented pipeline order** — adding a new custom modifier is a pipeline-order contract and must be reviewed as such.

---

## What this bridge does NOT override

- Four core surfaces, extension surfaces, Change Manifest schema, operating contract — unchanged.
- The XML bridge's treatment of Room, WorkManager, FCM, runtime permissions, vendor forks, deep links, ProGuard/R8, release channels — all inherited as-is. Do not duplicate those sections here.
- This bridge only provides: the UI-layer delta (state ownership, recomposition, effect APIs, navigation routes, composition-local nesting) and the Compose-toolchain build-time-risk binding.
