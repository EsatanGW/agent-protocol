# Flutter Stack Bridge

> This document maps the tool-agnostic methodology in `docs/` to a concrete Flutter (Dart) application stack.
> Only bridges are allowed to name specific tools, packages, and commands. The rest of the methodology stays neutral.

---

## Scope

**Applies to:** Flutter mobile apps (iOS + Android), optional desktop / web targets, using Dart as primary language.
**Typical stack assumed:** Flutter stable channel, Dart null-safety, `build_runner` for codegen, `flutter_test` for tests, `go_router` or similar for routing, a state management library (Bloc / Riverpod / Provider — interchangeable), a lockfile-based dependency manager (`pubspec.lock`).

---

## Surface mapping

### User surface

| Concept | Concrete implementation |
|---|---|
| route / page | `lib/routes/**`, `go_router` config |
| component (widget) | `lib/widgets/**`, stateless / stateful widgets |
| interaction | `GestureDetector`, `InkWell`, animation controllers |
| copy / i18n | `lib/l10n/*.arb`, generated `AppLocalizations` |
| state | Bloc / Cubit / Provider / Riverpod (pick one as convention) |
| validation | Form + FormField validators; cross-field in Bloc |
| a11y | `Semantics`, `ExcludeSemantics`, contrast ratios, `TextScaler` |

**Verification surface:**
- `flutter test` for widget tests
- `flutter test --update-goldens` for golden image tests
- `flutter drive` / `integration_test` for end-to-end on device/simulator
- Manual screenshot evidence for visual changes

### System interface surface

| Concept | Concrete implementation |
|---|---|
| REST API client | `dio` / `http` + typed clients via `retrofit` / hand-written |
| GraphQL | `graphql_flutter` / `ferry` + generated types |
| Platform channels | `MethodChannel`, `EventChannel` (iOS Swift / Android Kotlin) |
| Push / deep links | `firebase_messaging` or platform-neutral equivalent, `uni_links` |
| External SDKs | Declared in `pubspec.yaml`, versions pinned in `pubspec.lock` |

**Uncontrolled-interface register:**
- iOS / Android OS versions
- Store review / privacy policies
- Native SDKs (Firebase, ads, analytics, payment, map)
- Dart SDK / Flutter SDK upgrade timeline

### Information surface

| Concept | Concrete implementation |
|---|---|
| Model classes | `@JsonSerializable` / `@freezed` + generated files |
| Local persistence | `sqflite`, `drift`, `hive`, `shared_preferences` |
| Feature flags | Remote config service + local fallback config |
| Secure storage | `flutter_secure_storage` (OS keychain/keystore backed) |

### Operational surface

| Concept | Concrete implementation |
|---|---|
| Structured logs | `logger` / `logging` package, redacted PII |
| Crash reporting | Firebase Crashlytics or Sentry |
| Telemetry | Analytics SDK with event name registry |
| Release channels | Internal / alpha / beta / production (Play Internal Testing / TestFlight) |
| Version pinning | `pubspec.yaml` (ranges) + `pubspec.lock` (resolved) |

---

## SoT pattern bindings

| Pattern | Flutter instance |
|---|---|
| 1 Schema-Defined | Backend JSON schema → Dart model |
| 2 Config-Defined | Remote config / `.env` via `flutter_dotenv` |
| 3 Enum/Status | `enum` with exhaustive `switch`, consider `sealed class` for variants |
| 4 Contract-Defined | API spec (OpenAPI/Proto) + generated client |
| 4a Pipeline-Order | `dio.Interceptor` registration order, `MultiBlocProvider` order |
| 6 Transition-Defined | State machines in Bloc / `package:state_machine` |
| 7 Temporal-Local | Offline-first with `drift` + sync queue |
| 8 Dual-Representation | **`@JsonSerializable`/`@freezed` class ↔ `*.g.dart` / `*.freezed.dart`** — canonical case, synced by `dart run build_runner build --delete-conflicting-outputs` |
| supply-chain (extension) | `pubspec.lock` + `.dart_tool/package_config.json` |

---

## Rollback mode defaults

| Layer | Default mode |
|---|---|
| Dart code behind a remote feature flag | Mode 1 |
| Shipped app binary (App Store / Play Store) | Mode 2 forward-fix |
| Silent-pushed notification / email sent | Mode 3 compensation |
| Local DB schema migrated | Mode 2 (use forward migrations only, avoid destructive down-migrations) |

**Minimum supported version** should be declared explicitly in `pubspec.yaml` constraints and enforced via a server-side version gate.

---

## Cross-cutting concerns bindings

- **Security checklist integration:** `flutter_secure_storage` for secrets, certificate pinning via `dio` interceptor, ProGuard/R8 rules for Android release builds (via `android/app/proguard-rules.pro`), obfuscation via `--obfuscate --split-debug-info`.
- **Performance budget:** frame budget 16ms (60fps) or 8ms (120fps) depending on target; measure via `flutter run --profile` + DevTools timeline.
- **Observability:** all analytics event names live in one registry file (e.g. `lib/analytics/events.dart`); logs go through a single redacting logger.
- **Testability:** keep widgets dumb, logic in Blocs/Cubits; use `mocktail` for mocks; golden tests for critical visual regressions.
- **Error handling:** follow asymmetric-responsibility principle — raw exceptions at data layer → domain errors at Bloc → user-safe messages at UI.

---

## Automation-contract implementation

Reference implementation layers (mapping to `docs/automation-contract.md`):

### Layer 1 — Structural validity

```bash
# Reference: Node or Dart validator — team may pick either
# Given manifests/*.yaml and schemas/change-manifest.schema.yaml
ajv validate -s schemas/change-manifest.schema.yaml \
  -d "manifests/**/*.yaml" --strict=true
```

Output must follow the `<pass|fail> <path> <rule_id> <severity> <msg>` contract.

### Layer 2 — Cross-reference consistency

Flutter-specific drift checks to ship in the bridge CI:

1. **Codegen drift:** running `dart run build_runner build` must produce no diff. If it does, the repo's `*.g.dart` / `*.freezed.dart` do not match the editor source (dual-representation violation).
   ```bash
   dart run build_runner build --delete-conflicting-outputs
   git diff --exit-code
   ```
2. **Locale drift:** `.arb` files and generated `AppLocalizations` must be in sync.
   ```bash
   flutter gen-l10n
   git diff --exit-code lib/l10n
   ```
3. **Dependency lock drift:** `pubspec.lock` is SoT for installed versions; CI must fail if `pubspec.yaml` changed without `pubspec.lock`.
4. **Evidence path check:** every `evidence_plan.artifacts[].path` listed in the manifest must exist in the repo (or in a linked artifact store).

### Layer 3 — Drift detection

Weekly `main` branch scan:
- Dangling SoT: any `lib/**` file named as SoT in a delivered manifest whose latest commit is newer than the manifest's `last_updated`.
- Supersedes cycle check.
- Phase 8 observation overdue detection for manifests with `observation.required: true`.

---

## Multi-agent handoff conventions

- **Planner output** lands in `manifests/<change_id>.yaml` with `phase: plan`
- **Implementer** commits reference `change_id` in commit message footer: `Change-Id: <change_id>`
- **Reviewer** signs off by creating a GitHub PR review marked `Approves change_id: <change_id>`
- `dart run build_runner build` must be run by the Implementer before opening PR; the Reviewer verifies no drift via Layer 2 check.

---

## Typical Lean workflow per task type

| Task | Mode | Minimum artifacts |
|---|---|---|
| Copy string change | Zero ceremony | `.arb` update + regenerate |
| New widget behind existing screen | Lean | affected surfaces + widget test + golden |
| New endpoint integration | Lean → Full if breaking | manifest with sot_map for contract + codegen + contract test |
| DB schema migration (drift) | Full | manifest + migration + forward-only verify + rollback mode 2 note |
| Major SDK upgrade | Full | manifest + uncontrolled_interfaces update + threat model delta |
| Push notification change | Full | manifest + rollback mode 3 for already-sent |

---

## Reference worked example

**Primary:** `docs/examples/flutter-app-example.md` — "Save & Share" action across iOS / Android / Web / Desktop. Exercises platform-channel two-sided contract (SoT pattern 4 + 8), per-target rollback asymmetry (mobile mode-2, Web mode-1, desktop mode-2), and `@freezed` dual-representation.

**Supplementary:** `docs/examples/mobile-offline-feature-example.md` — the offline ledger feature in the main methodology uses patterns (Temporal-Local + Transition + Dual-Representation) that directly apply to Flutter offline work. Specifically:

- `@JsonSerializable` / `@freezed` model ↔ `.g.dart` / `.freezed.dart` dual-representation
- Local `drift` DB as temporary truth until sync
- `sealed class` state transitions guarded at Bloc level
- Forward-fix rollback only (shipped binary)

Follow the platform-channel example for multi-target features; follow the offline example for sync-heavy features.

---

## Flutter Web target discipline

Flutter Web is not a second-class port of the mobile story — several core assumptions shift:

### What changes on Web vs. mobile

| Concern | Mobile target | Web target |
|---|---|---|
| Build pipeline | AOT via Dart native | `dart2js` (JS) or `dart2wasm` (WASM, opt-in) — different tree-shaking, different reflection story |
| Rollback | Shipped binary = mode 2 | CDN deploy behind a flag = mode 1 (closest to server rollback semantics) |
| Storage | SQLite / secure storage | IndexedDB / `localStorage` / browser cookies — no OS keychain equivalent |
| Platform channels | iOS / Android native handlers | Re-implement as JS-interop via `dart:js_interop` / `dart:js_util`; feature-detect on-demand |
| User surface caching | App binary is the whole surface | Service worker can serve a stale app shell for hours after deploy |
| Reflection | IL2CPP-style stripping rare in debug, active in release | `dart2js` aggressive tree-shaking; `@pragma('vm:entry-point')` not available — annotate with `@JS()`/`@staticInterop` as needed |

### Web-specific SoT additions

| Pattern | Web instance |
|---|---|
| 4a Pipeline-Order | **Service-worker cache strategy** — `workbox`-style precache vs runtime cache ordering; a wrong order ships stale UI for hours. `flutter build web` emits `flutter_service_worker.js` with a hashed asset manifest — treat the manifest as the Pattern 1 schema. |
| 4 Contract-Defined | **Web-specific browser APIs** (`navigator.share`, `navigator.clipboard`, `Notification.requestPermission`) are uncontrolled interfaces; feature-detect, never user-agent-sniff. |
| 7 Temporal-Local | IndexedDB is the Web equivalent of SQLite; schema migrations are forward-only the same way, but the user can wipe site data from browser UI — assume that's always possible. |

### Web-specific drift checks

- [ ] `flutter build web --release` tree-shakes unreferenced reflective targets. Grep for `dart:mirrors` (already forbidden on Web) and any `@JS()` annotation whose target is only referenced via a string literal — these need explicit preservation.
- [ ] Service-worker update strategy: after deploy, confirm the client fetches the new `flutter_service_worker.js` within one session (default behavior is aggressive; custom strategies silently extend staleness).
- [ ] CSP headers cover `wasm-unsafe-eval` if `dart2wasm` is used; otherwise the app fails at runtime with a silent Content-Security-Policy violation.

### Web rollback

| Layer | Default mode |
|---|---|
| Dart/JS behind a CDN + feature flag | Mode 1 (canonical reversible deploy; closest Flutter comes to classic server rollback) |
| Service worker already installed on users' browsers | Mode 2 — you cannot force-evict a service worker; you can only ship a new one with a bumped version string and hope users reload |
| IndexedDB schema migrated in a user's browser | Irreversible per-user (like shipped save files) |

---

## Flutter Desktop target discipline

Flutter Desktop (macOS / Windows / Linux) sits between mobile and Web in every dimension:

### What changes on Desktop vs. mobile

| Concern | Desktop answer |
|---|---|
| Distribution | App Store + DMG (macOS), MSIX + EXE installer (Windows), snap / flatpak / AppImage / deb / rpm (Linux) — each channel has distinct update semantics |
| Signing / notarization | macOS: App Store Connect for App Store, otherwise developer-ID signing + Apple notarization (blocking on first-run otherwise). Windows: EV certificate preferred, SmartScreen reputation builds slowly. Linux: GPG signing per package manager. |
| File system | Direct file system access (unlike mobile sandboxes); path-handling is a first-class Information-surface concern |
| Platform channels | Native C++/Objective-C++/Swift (macOS), C++/C# (Windows via WinRT), C++ (Linux via GTK/Qt) |
| Window / menu | `desktop_window` / native menu integration is a new User-surface concept not present on mobile |
| Rollback | Shipped installer = mode 2 in practice; store-distributed = mode 2 with store-review lag; self-distributed = mode 2 but you control the update cadence |

### Desktop-specific drift checks

- [ ] Release build with macOS notarization: `xcrun altool --notarization-info` output archived as evidence. Debug builds pass where notarized-release would fail (Gatekeeper rejects unsigned file writes to privileged paths).
- [ ] Windows installer: SmartScreen reputation score checked per release; a new signing cert drops reputation to near-zero, re-earned over weeks.
- [ ] Linux: confirm the app works under Wayland and X11 (IME behavior, clipboard scope, display scaling differ).
- [ ] File-path assumptions: every hard-coded path is either `path_provider`-derived or platform-guarded.

### Desktop uncontrolled-interface additions

- macOS: Apple notarization policy, hardened-runtime entitlements, minimum macOS version support window.
- Windows: WinRT API availability per Windows version, SmartScreen reputation building.
- Linux: per-distribution libc versions, desktop environment (GNOME / KDE / others) quirks, package manager gating.

---

## Federated plugin lifecycle

Federated plugins (plugins split into `package`, `package_platform_interface`, `package_<platform>` sub-packages) are the canonical case where one feature is spread across N `pubspec.yaml` files, each with independent version cadence.

### Federated plugin SoT pattern

| Aspect | Pattern |
|---|---|
| Platform-interface abstract class | Pattern 4 (Contract) — the single IDL between app and per-platform implementation |
| Per-platform implementation | Pattern 4 + Pattern 8 (platform interface ↔ platform implementation registered via `pluginClass` in pubspec) |
| Plugin registration | Pattern 4a (Pipeline-Order) — registered plugins run in pubspec-resolved order; shadowing matters when two plugins register the same interface |
| Version resolution | Pattern 1 (Schema) + supply-chain — `pubspec.lock` for the app pins transitively-resolved per-platform packages |

### Required manifest fields when touching a federated plugin

- `sot_map` entry for the platform interface **must name every per-platform implementation it depends on**, since bumping the interface without bumping each implementation is a breaking change per platform independently.
- `uncontrolled_interfaces` must include any platform implementation whose maintainer is external (most community Flutter plugins).
- `breaking_change.affected_consumers` is per-platform; a method added to the interface is additive in Dart but L2+ in Swift/Kotlin until every implementation has a stub.

### Federated plugin drift checks

- [ ] `pubspec.yaml` platform-interface version vs. each per-platform implementation version: if the app pins an interface version that no per-platform implementation supports, resolution picks the newest compatible — silently — and the mismatch only surfaces at method-missing runtime.
- [ ] Every platform interface method has a matching implementation in every registered per-platform package, or an explicit `throw UnimplementedError(...)` with a TODO.

---

## Code push / dynamic delivery

Flutter does not ship a first-party code-push story, but several third-party options exist (Shorebird is the most prominent; Instabug/CodePush-style providers for Dart exist but are less common). Independent of vendor, the methodology implications are:

### Why code push changes the rollback-mode table

| Track | Default mode without code push | With code push |
|---|---|---|
| Shipped binary | Mode 2 (forward-fix only) | **Mode 1** for Dart code (can revert a patch) + Mode 2 for the native shell |
| Native code changes (platform channels, Objective-C/Swift, Kotlin/Java) | Mode 2 | **Still Mode 2** — code push cannot touch native code; this is an Apple App Review constraint, not a vendor limitation |
| Asset changes | Mode 2 | **Mode 1** if the asset is part of the pushed Dart bundle |

### Apple-platform constraint

Apple's App Review Guidelines permit hot-loading compiled JS (historically) and compiled Dart (Shorebird's current position) only when the functionality does not change the app's primary purpose. **This is a policy interface, not a technical one** — track it in `uncontrolled_interfaces`, because an Apple policy change can invalidate the entire strategy overnight.

### Code-push manifest fields

- `rollback.per_surface_modes` must split between "Dart code (mode 1 via code push)" and "native code (mode 2 via store release)" — a single mode-1 claim is a category error.
- `uncontrolled_interfaces` adds the code-push provider's backend + Apple/Google store policy (for the subset of policy that touches dynamic delivery).
- `evidence_plan` must include a rollback drill: actually deploy and revert a Dart-side change end-to-end before shipping the feature behind code push.

---

## State management library pipeline-order

Bloc, Riverpod, Provider, and GetX are not interchangeable pipeline-order wise; the bridge covers the conceptual pattern, but each library binds it differently. Document your choice in a project-local addendum — the summary below is the minimum ruleset per library.

| Library | Pipeline-order contract to preserve |
|---|---|
| **Bloc / Cubit** | `BlocProvider` / `MultiBlocProvider` nesting order = ancestor-first dependency order. A dependent Bloc listed before its dependency silently receives a default-instance or a `ProviderNotFoundException`. |
| **Riverpod** | Provider override order in `ProviderScope(overrides: [...])` resolves last-wins; a forgotten override in a test shell ships a real network client into unit tests. Declarations vs. consumers are decoupled — order matters for overrides, not for declarations. |
| **Provider** | `MultiProvider` children are built top-down; a `ProxyProvider` that reads a sibling must come after it. Silent fallback to `Provider.of<T>(context, listen: false)` with a stale value otherwise. |
| **GetX** | `Get.put` / `Get.lazyPut` call order determines instantiation timing; `permanent: true` bypasses normal lifecycle — treat as a pipeline-order SoT exception that must be justified per call site. |

### State-management drift checks

- [ ] Project-local addendum exists naming the chosen library and its pipeline-order discipline.
- [ ] For Bloc-based projects: a lint rule (or grep) ensures no `BlocProvider` sits above its dependency in the tree.
- [ ] For Riverpod-based projects: test overrides are symmetric (every production provider has a test override, or is explicitly documented as safe to hit real).
- [ ] State-management library upgrade bumps (Bloc major, Riverpod major) are classified as `uncontrolled_interfaces` drift requiring re-audit.

---

## Validating this bridge against your project

Bridges are assumptions until battle-tested. Before trusting this bridge in production CI, run the following self-validation on your repo:

### Self-test checklist

- [ ] **SoT mapping reality check** — take the 5 most recent non-trivial PRs and ask: "was the SoT for that change in the file this bridge's SoT table claims?" If ≥1 is off, the table needs a row added / corrected for your project structure.
- [ ] **Codegen drift reproducibility** — make a deliberate edit to an `@JsonSerializable` class WITHOUT running `build_runner`; confirm CI flags `drift.codegen_touched_but_no_generated_diff`.
- [ ] **Locale drift reproducibility** — add a new ARB key in `intl_en.arb` without regenerating; confirm drift is flagged.
- [ ] **Lock drift reproducibility** — bump a package version in `pubspec.yaml` without updating `pubspec.lock`; confirm drift is flagged.
- [ ] **Rollback-mode mapping exercise** — take a real past incident and re-classify the rollback using this bridge's table; does it match what actually happened? If not, adjust the table.
- [ ] **Platform-channel test** — if your app uses `MethodChannel` / `EventChannel`, confirm `uncontrolled_interfaces` covers iOS and Android sides separately.
- [ ] **Release-build test coverage** — run the app in `flutter run --release --obfuscate` on both platforms; does anything break that worked in debug? (Missing `-keep` rules, tree-shaking failures.)

If any item fails, record the gap in a project-local `docs/bridges-local-deviations.md` and send a PR upstream if the gap is general.

### Known limitations of this bridge

- **State management library-specific internals.** The sections above summarize Bloc / Riverpod / Provider / GetX pipeline-order rules, but library-major-version migrations (e.g., Riverpod 2→3 generator changes) need a project-local addendum with the exact codegen + lint story.
- **Code-push provider specifics.** The section above covers methodology implications; per-vendor specifics (Shorebird config, staged-rollout semantics, enterprise MDM interaction) belong in a project-local addendum keyed to your chosen provider.
- **Mobile-first framing remains in subtle places.** `user surface` tables above assume a touch-first interaction model; keyboard / pointer / large-screen layouts on desktop & Web tablet need extra care in project-local UX guidelines beyond what this bridge prescribes.
- **Linux distribution fragmentation.** The Desktop section names the major package managers but does not enumerate per-distro quirks (libc version spread, desktop-environment IME behavior) — add a project-local deviations entry if you ship broad Linux support.

---

## What this bridge does NOT override

- The four core surfaces must still be marked.
- The manifest schema is the universal schema; no Flutter-specific fields.
- All normative rules in `AGENTS.md`, `principles.md`, `ai-operating-contract.md` apply as-is.
- This bridge only provides: SoT→file mapping, drift checks, tool invocation examples.
