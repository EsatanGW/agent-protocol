# iOS / Swift Stack Bridge

> Maps the tool-agnostic methodology to a native iOS app written in Swift.
> Covers UIKit, SwiftUI, and the most common mixed-framework reality (SwiftUI dominant, UIKit where SwiftUI still has gaps — `UIViewController` hosting, some text input, legacy screens). Watch / App Clip / macOS Catalyst deltas are project-local overlays.

---

## Scope

**Applies to:** Native iOS apps written in Swift 5.9+ targeting iOS 15+, distributed via App Store Connect (TestFlight + phased release) or Enterprise / ad-hoc channels, using any mix of UIKit and SwiftUI, with Core Data / SwiftData / a local SQLite library for persistence, and URLSession (possibly wrapped by a thin client) for networking.

**Not in scope for this bridge:**
- **watchOS, tvOS, visionOS, macOS, Catalyst** — share much discipline but differ on input model, lifecycle, and distribution. Cover them as project-local overlays per [`../bridges-local-deviations-template.md`](../bridges-local-deviations-template.md).
- **Cross-platform frameworks running on iOS** (Flutter, React Native, KMM shared code, Xamarin) — use the native-platform bridge (this one) for the iOS surface of those apps *only for iOS-specific deltas*. The cross-platform codebase itself belongs to its own bridge.
- **Objective-C-dominant apps.** Swift interop patterns (bridging header, `NS_SWIFT_NAME`, nullability annotations) are mentioned below but not exhaustively covered — project-local overlay territory.

---

## Surface configuration

Core surfaces (mandatory):
- [x] User surface
- [x] System-interface surface
- [x] Information surface
- [x] Operational surface

Extension surfaces commonly applicable:
- [x] Asset surface (bundled images / `Assets.xcassets` / catalogs / `.mlmodel` / `.usdz`)
- [x] Compliance surface (`Info.plist` usage descriptions, `PrivacyInfo.xcprivacy` manifest, ATT prompts)
- [x] Uncontrolled-external surface (App Store review, iOS major versions, Apple platform-policy changes, third-party SDK behavior drift)

---

## Surface mapping

> Machine-consumable surface → file-glob mapping lives in
> [`ios-swift-surface-map.yaml`](./ios-swift-surface-map.yaml)
> and is consumed by validator rule 3.2 (surface ↔ file-pattern drift).

### User surface

| Concept | Concrete implementation |
|---|---|
| screen (UIKit) | `UIViewController` subclass; `UIViewController`-driving navigation via `UINavigationController` / `UITabBarController` / `UIHostingController` |
| screen (SwiftUI) | `View`-conforming value type; routing via `NavigationStack` / `.navigationDestination(for:)` type-driven destinations (iOS 16+) or `NavigationSplitView` |
| reusable UI (UIKit) | `UIView` subclass with programmatic or `.xib`-backed layout; Auto Layout constraints or the increasingly idiomatic `UIStackView` stacks |
| reusable UI (SwiftUI) | `View`-conforming value; `@ViewBuilder` composition; modifiers ordered outer-to-inner matter (that's a Pattern 4a pipeline-order case — see below) |
| interaction | `UIGestureRecognizer`s, `UIControl`-target-action in UIKit; `.onTapGesture` / `.gesture` / `.dragGesture` + `@FocusState` in SwiftUI |
| copy / i18n | `Localizable.strings` + `.stringsdict` (plurals); `NSLocalizedString(_:comment:)` or `String(localized:comment:)`; `String Catalog` (`.xcstrings`, iOS 17+) as a newer SoT — pick one and migrate fully, never dual-source |
| state (UIKit) | `UIViewController` properties + a view model / `@Observable` reference type; notification patterns via `NotificationCenter` (discouraged in modern code) or Combine `Publisher`s |
| state (SwiftUI) | `@State` (view-local), `@Binding` (passed down), `@StateObject` / `@ObservedObject` (reference semantics, pre-iOS 17), `@Observable` + `@Bindable` (iOS 17+); `@Environment` for injected services |
| validation | In the view model / presenter; `TextField` surfaces errors via conditional UI; use `Formatter` for data-type coercion |
| a11y (UIKit) | `UIAccessibility*` properties on views; `accessibilityIdentifier` for UI testing |
| a11y (SwiftUI) | `.accessibilityLabel` / `.accessibilityValue` / `.accessibilityHint` / `.accessibilityAddTraits` modifiers; `.accessibilityIdentifier` for UI tests |

**Verification surface:**
- `xcodebuild test -scheme <Scheme> -destination <Sim>` — unit + UI tests.
- Snapshot testing (`pointfreeco/swift-snapshot-testing` or Apple's `XCTest` attachment snapshots).
- SwiftUI previews (`#Preview { … }`) are an editor aid, **not** a verification artifact — same discipline as Compose `@Preview`.
- Accessibility Inspector + VoiceOver audit on a physical device before release.

### System-interface surface

| Concept | Concrete implementation |
|---|---|
| HTTP client | `URLSession` directly, or a thin wrapper around `URLSession.shared.data(for:)`/`async`; avoid ad-hoc `URLSession` construction — pool one per app |
| API contract | OpenAPI / GraphQL schema in a shared contract repo; on iOS, generated `Codable` types via `apple/swift-openapi-generator` or a hand-rolled layer — the spec file is the SoT, the generated Swift is a consumer |
| push notifications | APNs payload + `UNUserNotificationCenter` handlers; device-token registration contract with the backend |
| deep links | Universal Links (`apple-app-site-association` on server + `Associated Domains` entitlement), `openURL` custom scheme (legacy), `NSUserActivity` handoff |
| background transfer | `URLSession` with `.background` configuration + `application(_:handleEventsForBackgroundURLSession:)`; separate lifecycle from foreground sessions |
| Sign in with Apple | `ASAuthorizationAppleIDProvider`; token rotation + server-side validation contract with backend |
| SiriKit / App Intents | `App Intents` framework (iOS 16+) — an `AppIntent` is a contract between your app and the system; schema drift = Shortcuts app silently breaks |
| StoreKit | StoreKit 2 async APIs; product IDs declared in App Store Connect ARE the SoT — drift between code and ASC = failed in-app purchases |

**Verification methods:**
- Contract tests for Codable round-trip against canonical JSON fixtures.
- Charles / Proxyman recording replayed through `URLProtocol` stub — NOT dependency on a mocked client if you can avoid it.
- Push: APNs sandbox + production, both verified on a physical device per release.
- Universal Links: Apple's validator endpoint + manual flow (`xcrun simctl openurl` does NOT verify AASA — only a real device does).

### Information surface

| Concept | Concrete implementation |
|---|---|
| data model (legacy) | Core Data `.xcdatamodeld` + generated `NSManagedObject` subclasses (codegen: "Manual/None" recommended — see below) |
| data model (modern) | SwiftData `@Model` (iOS 17+); shares Core Data semantics at the storage layer but exposes type-safe macros |
| local SQL (non-CD) | GRDB or SQLite.swift — schema migrations defined in code; the migration script sequence is the SoT |
| user preferences | `UserDefaults.standard` for single-device; `NSUbiquitousKeyValueStore` for cross-device sync (small values only); `App Groups`-scoped `UserDefaults(suiteName:)` for extensions |
| secure storage | Keychain (`kSecClassGenericPassword` / `kSecClassInternetPassword`); Keychain items survive app deletion unless `kSecAttrAccessible` is set restrictively — worth calling out |
| cloud sync | CloudKit — private database per user, shared database for collaboration, public database for app-wide data; schema lives in CloudKit Dashboard AS WELL as the Core Data model (dual representation — see below) |
| enum / status | Swift `enum` with associated values; Codable-conformant; **raw-value enums must carry an `unknown` fallback case** or `decode(from:)` on an unknown server value crashes decoding |
| config | `Info.plist` values (read via `Bundle.main.infoDictionary`), runtime `JSONDecoder()`-parsed config from a bundled JSON, or a feature-flag service |
| feature flag | `NSUserDefaults`-backed for dev toggles; a runtime flag service (Firebase Remote Config, LaunchDarkly, etc.) for prod |
| code generation | `swift-openapi-generator`, `sourcery`, `mockolo` — the generator config is the SoT, generated output is a consumer |

**Verification methods:**
- Core Data migration lightweight-migration compatibility check: open a v1 store with a v2 model — `NSPersistentStoreCoordinator` either migrates or throws.
- Codable round-trip tests with canonical JSON fixtures; unknown-key tolerance checked explicitly.
- UserDefaults App Group share: write from host app, read from extension in a UI test.

### Operational surface

| Concept | Concrete implementation |
|---|---|
| logging | `OSLog` / `Logger` (`os.Logger`, iOS 14+); privacy levels `.public` / `.private` / `.sensitive` **are load-bearing** — `.public` in release builds goes to Console unredacted |
| crash reporting | Apple's own MetricKit (`MXCrashDiagnostic`) + a third-party (Crashlytics / Sentry / Bugsnag); dSYM upload is a release-pipeline contract |
| performance | MetricKit `MXMetricPayload` — hang / CPU / scroll-performance / energy diagnostics; delivered daily |
| analytics | Event registry lives wherever your analytics SDK sits; the event-name + property-schema is the SoT, not the emission call-sites |
| release / rollout | TestFlight (internal / external groups) → App Store Connect phased release (7-day ramp) → full availability; rollback requires binary rebuild + re-review |
| rollback | **Binary = mode 2 forward-fix for most changes.** CloudKit public schema additions and Game Center leaderboard changes are mode 3 compensation. Server-side-driven features behind a flag can reach mode 1 via flag flip |
| app versioning | `CFBundleShortVersionString` (marketing, semver-shaped) + `CFBundleVersion` (monotonic build number); both must be bumped per TestFlight upload |

**Verification methods:**
- MetricKit payload sampling enabled for at least one staging TestFlight cohort.
- dSYM archive retention for ≥ 1 year (regulatory; also practical — old crashes come in from install base long-tail).
- Release checklist asserts: version + build bumped, changelog entry, privacy manifest updated if SDK API usage changed, `PrivacyInfo.xcprivacy` regenerated.

---

## UIKit ↔ SwiftUI interop (the dual-representation case)

Most non-trivial apps mix the two. The boundary is where most drift happens.

### The four boundary patterns

1. **`UIHostingController`** — embedding SwiftUI in a UIKit flow. State ownership: the SwiftUI view tree owns its state; the hosting controller is a plain `UIViewController` whose children are the SwiftUI tree. Modal presentation, navigation, and dismissal are UIKit concerns.
2. **`UIViewControllerRepresentable` / `UIViewRepresentable`** — embedding UIKit in a SwiftUI flow. State ownership: SwiftUI owns the state, the representable wraps a UIKit object and shuttles state via `makeCoordinator` + `updateUIView(Controller:context:)`. This is a **pipeline-order SoT** — mis-ordered updates in `updateUIView` are a recurring bug.
3. **`NotificationCenter` bridges** — when SwiftUI state changes and a UIKit controller elsewhere needs to react (or vice versa). Tolerable at the seam, anti-pattern if it's load-bearing.
4. **Shared reference-type view model** — both a UIViewController and a SwiftUI View observe the same `@Observable` (or `ObservableObject`) instance. This is the cleanest pattern for incremental migration.

### Anti-patterns to flag in review

- **Mixing `@State` in a SwiftUI view that wraps a UIKit view with mutable internal state.** The UIKit view becomes a silent second SoT; screen rotation or re-instantiation resyncs them in one direction only.
- **A `UIHostingController` whose SwiftUI content mutates its own bound state but the parent UIKit VC reads the initial value.** UIKit side will never see the mutation without an explicit callback binding.
- **SwiftUI view observing a UIKit singleton's `@objc dynamic` KVO property via Combine `publisher(for:)` without cancellation on view disappearance.** Leaks per-scroll.

### Verification

- A UI test that performs the user flow end-to-end across a UIKit → SwiftUI → UIKit hop; it catches the boundary bugs unit tests don't.
- Snapshot tests at both boundaries of a mixed screen.

---

## Multi-process state — App Groups, Widgets, App Intents, Extensions

iOS forces multi-process state once you ship a Widget, Share Extension, Siri/Shortcuts intent, or Action Extension. That state is a **pipeline-order SoT** (Pattern 4a) and a dual-representation risk (Pattern 8).

| Mechanism | Use case | SoT discipline |
|---|---|---|
| `UserDefaults(suiteName: "group.com.example.app")` | Small, frequently-read settings shared with a Widget | Defaults suite is the SoT; host app writes, extension reads. Unidirectional — avoid extension writes |
| Shared Core Data store in App Group container | Large, structured data shared with an extension | Core Data is the SoT; use `NSPersistentContainer(name:)` + a container URL under the App Group. Migrations must run from whichever process opens the store first — harden for either order |
| Shared Keychain access group | Secrets used by main app + extension | Keychain access group is the SoT; access-group string in entitlement is load-bearing — a typo means the extension sees no items |
| `CFNotificationCenterGetDarwinNotifyCenter` | Low-level "something changed, re-fetch" signal | **Not** a data channel — use UserDefaults / Core Data to actually carry the data; Darwin notifications are just a wake-up |
| App Intents + widget timeline refresh | Siri / Shortcuts / Widgets forcing a reload | Contract-Defined (Pattern 4) — the `AppIntent` parameter schema is the IDL. Drift silently breaks Shortcuts users' flows |

### Anti-pattern

- **Widget reads app state directly from `UserDefaults.standard`** (not the App Group suite). Compiles, runs in dev, silently reads nothing in production. Easy to miss in review.

### Verification

- Widget snapshot test that mounts a `WidgetKit` timeline entry and renders.
- UI test chain: open host app → set a value → kill app → trigger widget refresh → assert value visible.

---

## SoT pattern bindings

| Pattern | iOS / Swift instance |
|---|---|
| 1 Schema-Defined | Core Data `.xcdatamodeld` versioning, SwiftData `@Model` schema, OpenAPI spec → generated `Codable` types |
| 2 Config-Defined | `Info.plist`, `PrivacyInfo.xcprivacy`, entitlements files, remote-config JSON |
| 3 Enum/Status | Swift `enum`; **raw-value enums decoding server data MUST have an `unknown` fallback** — the commonest iOS crash of this shape is `Decodable` failure on a new server-side enum value |
| 3 Enum/Status (new case) | **Navigation destinations** under iOS 16 `NavigationStack` — a typed destination set; drift between `.navigationDestination(for:)` registrations and `NavigationPath` appends causes silent no-op navigation |
| 4 Contract-Defined | `AppIntent` parameter schemas, URL scheme / Universal Link route catalog, StoreKit product IDs in ASC ↔ code |
| **4a Pipeline-Order** | `UIViewControllerRepresentable.updateUIViewController(_:context:)` — updates applied in sequence; mis-ordered bindings cause last-writer-wins bugs |
| **4a Pipeline-Order** | SwiftUI modifier order: `.frame(…).padding(…).background(…)` ≠ `.padding(…).frame(…).background(…)`; outer-to-inner composition order IS the contract |
| **4a Pipeline-Order** | `URLSessionConfiguration` chain + `HTTPCookieStorage` + `URLProtocol` registration order |
| **4a Pipeline-Order** | View-controller transition coordinator callbacks (`animate(alongsideTransition:)` vs `completion:`) |
| 5 Event-Defined | Analytics event schema, NSNotification names + userInfo keys (treated as event-schema), APNs payload |
| 6 Transition-Defined | View-state enums rendered via `switch` — loading / loaded(data) / error; `@Observable` view-model state transitions |
| 7 Temporal-Local | Background URLSession completion handlers, `BGTaskScheduler` tasks, `NSPersistentCloudKitContainer` sync windows |
| **8 Dual-Representation** | Core Data model ↔ CloudKit schema; `Assets.xcassets` ↔ runtime `UIImage(named:)` string lookups; `.stringsdict` plural rules ↔ `Localizable.strings` keys; generated `Codable` ↔ OpenAPI spec |
| 9 Computation-Result | `NSCache`, `URLCache`, `NSPersistentStoreCoordinator`'s row cache, memoized `@Observable` computed properties |
| **10 Host-Lifecycle** | App launch → foreground → background → termination → next launch; scene lifecycle (`UIScene`); extension host lifecycle (Widget / Share / Action) |
| supply-chain (extension) | Swift Package Manager resolution (`Package.resolved`); CocoaPods `Podfile.lock`; `PrivacyInfo.xcprivacy` declared API usage for each third-party SDK |

---

## Rollback mode defaults

| Surface | Default mode | Reason |
|---|---|---|
| Backend-driven feature behind a server flag | Mode 1 (reversible) | Flag flip; client is idle |
| Shipped binary bug fix | Mode 2 (forward-fix) | Users install over time; no `UpdateApp` API — even with Phased Release, the only lever is a new build |
| CloudKit private-database schema change | Mode 2 | Private schema is per-user; new version additive; old clients see only their subset |
| CloudKit public-database schema change | **Mode 3 (compensation)** | Old clients of every user see the new schema; drops can't be reversed; additions can be deprecated but remain |
| Core Data lightweight migration | Mode 2 | Automatic; reversal requires migrating forward again to a new model version |
| Core Data heavyweight (manual) migration | Mode 3 if data-lossy; else mode 2 | Bespoke mapping model; test in a release build, not just debug |
| StoreKit product ID catalog | Mode 3 | Receipts from purchased removed products persist indefinitely; legacy product codepaths must remain |
| App Group UserDefaults schema | Mode 2 | Extension may run an old build against a new host (or vice versa) during update; be liberal on read, strict on write |

---

## Build-time risk

### What "release build" breaks that "debug build" doesn't

- **Whole Module Optimization + dead-code elimination** — `@objc dynamic` dispatch preserved, plain dynamic dispatch eliminated. Anything that relies on `NSSelectorFromString` or `NSClassFromString` can disappear.
- **Swift 6 language mode (strict concurrency)** — warning-suppressed actor / isolation violations that passed in Swift 5 mode can become hard errors; release builds may enable different concurrency-checking levels.
- **Bitcode** (deprecated but still present in some pipelines) — release archives may differ from local builds when bitcode is on.
- **App Thinning / Assets slicing** — one device slice missing an asset only surfaces when a specific device downloads the App Store build.
- **`DEBUG` conditional compilation** — any `#if DEBUG` code is removed in release; a debug-only guard that silently suppressed a crash is gone.

### Manifest fields to mark

- `cross_cutting.build_time_risk.release_build_verified: true` — release archive built, signed, and installed on a physical device matching the oldest-supported iOS version.
- `cross_cutting.build_time_risk.codegen_touched: true` if OpenAPI / Sourcery / SwiftData schema regenerated.
- `cross_cutting.build_time_risk.asset_pipeline_touched: true` if `Assets.xcassets` added a new image set, on-demand resource tag, or new variant.
- `cross_cutting.build_time_risk.minification_rules_touched: true` if the change relies on dynamic dispatch that DCE could strip.
- `cross_cutting.build_time_risk.determinism_considerations` — note if the build reads build-time date / hostname / random; reproducibility affects dSYM matching.

---

## Uncontrolled-external dependencies

| Dependency | Monitoring channel |
|---|---|
| iOS major version (N+1 betas) | WWDC announcements + summer beta cycle; test oldest-supported version in CI each release |
| App Store review | ASC review feedback + Apple News Dev blog; deprecations give ≥ 6 months but not always |
| StoreKit / in-app purchase policy | WWDC sessions + StoreKit 2 deprecation notes in SDK |
| Sign in with Apple | Policy changes (rare but happen); server endpoint contract |
| ATT (App Tracking Transparency) | Apple's privacy policy page + ATT-prompt copy requirements |
| APNs | Apple's push notification service advisories; token format changes are announced |
| Third-party SDK behavior drift | Per-SDK release notes; Privacy Manifest requirements cascade from SDK updates |
| Xcode / Swift toolchain | Xcode beta cycle; Swift release notes; Swift 6 migration is a multi-release concern |

Each of these should appear in `uncontrolled_interfaces[]` of your Change Manifest when touched.

---

## Automation-contract implementation

### Layer 1 — Structural validity

Identical to the generic layer 1 — schema-valid YAML, required fields present. No iOS-specific additions.

### Layer 2 — Cross-reference consistency

iOS-specific drift checks to ship in bridge CI:

1. **StoreKit product ID drift.** Collect every product ID string in code (`Product(id:)`, `StoreKit.Product.products(for:)`) and diff against the App Store Connect product catalog (exported via `fastlane deliver` or the App Store Connect API). Any code ID missing from ASC is a silent purchase failure in production.
2. **Info.plist usage description coverage.** For every `NSXxxUsageDescription` key triggered by an API call in code (camera, location, photos, contacts, etc.), assert the key exists in `Info.plist` with non-empty value. Apple's static check fails the build only *sometimes*; explicit check is cheaper than a rejected review.
3. **`PrivacyInfo.xcprivacy` required-reason API coverage.** For each required-reason API used (file timestamp, system boot time, user defaults, disk space), assert the privacy manifest declares a reason. Missing reasons trigger App Store Connect warnings and (since May 2024) rejections.
4. **Core Data / SwiftData model version consistency.** Compare the `.xccurrentversion` pointer to the list of `.xcdatamodel` versions in the `.xcdatamodeld`. A drift here means a version shipped that the app can't open.
5. **Localizable strings key-set parity.** Every key in `Localizable.strings` (or `.xcstrings`) exists in every supported locale. Missing keys fall through to the `base` locale — acceptable but should be explicit.
6. **Universal Links AASA vs entitlements.** The `applinks:` entitlements list must be a subset of the domains served under `.well-known/apple-app-site-association`; mismatched domains silently open in Safari instead of the app.

### Layer 3 — Drift detection

- Swift Package Manager resolved-version drift vs declared version range (`Package.resolved`).
- dSYM archive present for every shipped build (absence means future crash reports are unsymbolicated).
- Derived data vs source drift on `@Observable` / Sourcery / OpenAPI generated Swift — any file under `DerivedSources/` or `Generated/` older than its source.

---

## Multi-agent handoff conventions

- **Planner** owns surface enumeration and rollback-mode selection (the iOS-specific asymmetry around CloudKit public schemas is a load-bearing planner concern).
- **Implementer** owns Xcode / SwiftPM / Codable / UI implementation and the UIKit↔SwiftUI interop glue.
- **Reviewer** owns release-build verification on a physical device matching the oldest supported iOS version, and the privacy manifest / AASA / StoreKit catalog cross-checks listed above.

The anti-collusion rule from `AGENTS.md` §7 applies unchanged: the agent that wrote the feature may not also be the agent that signs off the release build verification.

---

## Typical workflow per task type

| Task | Mode | Minimum artifacts |
|---|---|---|
| String copy change | Zero ceremony | `.strings` / `.xcstrings` update + VoiceOver spot-check if the string is on an a11y path |
| New SwiftUI view inside an existing screen | Lean | Snapshot test + a11y modifiers + state-hoisting review |
| New screen (UIKit or SwiftUI) | Lean → Full if deep-linkable | Route / destination registered + snapshot + a11y audit |
| Core Data lightweight migration | Full | New model version + "Manual/None" codegen regen + migration test from prior version + release-build verification |
| Core Data heavyweight migration | Full | Mapping model + `NSEntityMigrationPolicy` subclass + data-fidelity test + rollback plan (almost always mode 3 if data-lossy) |
| New CloudKit record type in public DB | Full | ASC schema deploy order + mode-3 rollback plan + old-client fallback behavior documented |
| SwiftUI ↔ UIKit interop | Full | Snapshot at both boundaries + memory/retain audit + UI test crossing the seam |
| Add App Intent / Widget / Share Extension | Full | App Group container wiring + privacy manifest update + intent schema review + widget-timeline test |
| Bump iOS deployment target | Full | Release-notes scan for removed APIs + API-availability lints + release-build verified on old device |
| SwiftPM / CocoaPods dependency bump | Lean → Full if it adds capabilities | `Package.resolved` / `Podfile.lock` committed + privacy manifest check + license audit |

---

## Reference worked example

See [`../examples/ios-swift-app-example.md`](../examples/ios-swift-app-example.md) for an end-to-end walk-through of adding a CloudKit-synced tag feature with a Widget, exercising the asymmetric rollback between CloudKit private (forward-fixable) and public (compensation-only) schemas.

For cross-platform / multi-target concerns inherited onto iOS, see [`../examples/mobile-offline-feature-example.md`](../examples/mobile-offline-feature-example.md).

---

## Validating this bridge against your project

### Self-test checklist

- [ ] **Every raw-value enum decoded from server JSON has an `unknown` fallback case.** Grep for `String, Codable` on raw-value enums; every hit without an `@unknown default` in a consuming `switch` is a release-build crash waiting to happen.
- [ ] **Every App Group UserDefaults read/write goes through a named `suiteName`.** Grep for `UserDefaults.standard` inside any target with `Extension` in the name.
- [ ] **Privacy manifest covers every required-reason API usage** in code and in every third-party SDK embedded. Cross-check against Apple's published required-reasons list.
- [ ] **Universal Link domains in the entitlement match the domains actually served from `apple-app-site-association`.** Copy-paste mismatches are the common failure.
- [ ] **StoreKit product IDs in code match the ASC catalog** — exact string match including any `com.example.app.` prefix.
- [ ] **SwiftUI-in-UIKit (`UIHostingController`) and UIKit-in-SwiftUI (`UIViewControllerRepresentable`) state-ownership is documented per screen** — at least a one-liner comment.
- [ ] **Release build tested on a physical device matching the oldest supported iOS version** — simulator is not sufficient for APNs, Universal Links, or StoreKit.
- [ ] **dSYM archives uploaded + retained** for the current + N−1 release.

### Known limitations of this bridge

- **SwiftUI evolution cadence** — modifiers, property wrappers, and navigation APIs change meaningfully per iOS major version. This bridge anchors on iOS 15+ / SwiftUI 3+ / iOS 16 NavigationStack; project-local addenda should capture the specific iOS-version-gated decisions your app makes.
- **Objective-C / Swift bridging nuances** (`NS_SWIFT_NAME`, nullability, generics bridging, `@objc protocol` witness tables) — not exhaustively covered. Needed for any app older than ~2019.
- **macOS Catalyst / iPadOS-specific differences** — `UIApplicationSupportsMultipleScenes`, keyboard focus, pointer cursor. Covered as project-local overlay.
- **watchOS / visionOS** — separate platforms that share Swift + some frameworks but differ on input and lifecycle. Separate overlay bridges.
- **App Clip specifics** — 10 MB uncompressed size budget + Site Association + invocation URL catalog. Treat as project-local overlay.
- **TCA / Redux-style architectures on top of SwiftUI** — out of scope; they replace several of the state-ownership recommendations above with their own discipline.

For the project-local overlay pattern (watch / visionOS / macOS / Catalyst / TCA / App Clip / Objective-C-heavy addenda), see [`../bridges-local-deviations-template.md`](../bridges-local-deviations-template.md) and the end-to-end walk-through in [`../bridges-local-deviations-howto.md`](../bridges-local-deviations-howto.md).

---

## What this bridge does NOT override

- Four core surfaces, extension surfaces, Change Manifest schema, operating contract — unchanged.
- The generic rollback-asymmetry modes (1 / 2 / 3) — the iOS-specific table above is an application, not a replacement.
- The generic breaking-change severity framework (L0–L4) — applies unchanged; the bridge only maps which iOS mechanisms produce which level.
- Anything in `docs/cross-cutting-concerns.md` — build-time risk, performance, security, observability discipline applies to iOS apps as much as any other stack.
