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

See `docs/examples/mobile-offline-feature-example.md` — the offline ledger feature example in the main methodology uses patterns (Temporal-Local + Transition + Dual-Representation) that directly apply to Flutter. Specifically:

- `@JsonSerializable` model ↔ `.g.dart` dual-representation
- Local `drift` DB as temporary truth until sync
- `sealed class` state transitions guarded at Bloc level
- Forward-fix rollback only (shipped binary)

Follow that example's structure for Flutter offline features.

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

- **State management library-specific patterns not covered.** Bloc / Riverpod / Provider / GetX each have their own pipeline-order discipline. This bridge covers the conceptual pattern; add a project-local section for your specific library.
- **Platform-channel two-sided contract** is only lightly covered. If your app has heavy platform-native integration, write a companion `flutter-platform-channel-addendum.md` that treats channel messages as IDL → stub pattern (SoT pattern 4 + 8).
- **Federated plugin lifecycle** (plugins with per-platform implementations) has unique SoT complications; not yet covered here.
- **Code push / dynamic delivery** (if used) has additional rollback implications beyond the binary-rollback mode-1 assumption.
- **Web and desktop targets** — this bridge is mobile-first; Web target has different `dart2js` build-time characteristics (different tree-shaking, different reflection story).

---

## What this bridge does NOT override

- The four core surfaces must still be marked.
- The manifest schema is the universal schema; no Flutter-specific fields.
- All normative rules in `AGENTS.md`, `principles.md`, `ai-operating-contract.md` apply as-is.
- This bridge only provides: SoT→file mapping, drift checks, tool invocation examples.
