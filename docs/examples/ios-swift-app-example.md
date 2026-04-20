# Worked Example: Add a CloudKit-synced tag feature with a Widget to an iOS/Swift app

> This example fleshes out the outline in `docs/bridges/ios-swift-stack-bridge.md`.
> It exercises the four iOS patterns the bridge calls out as common footguns:
>
> - **CloudKit schema rollback asymmetry** — the private database can be reset per-user (effectively mode 2: forward-fix); the public database cannot be "rolled back" schema-wise (mode 3: compensation).
> - **Core Data `.xcdatamodeld` versioning** as a dual-representation SoT (model bundle ↔ generated classes ↔ on-device SQLite file).
> - **Widget + App multi-process state** through App Groups + Darwin notifications (Pattern 4a pipeline-order + Pattern 8 dual-representation).
> - **Info.plist / PrivacyInfo.xcprivacy / entitlements drift** as the most common App Store review blocker.
>
> All names, paths, and data structures are fictitious.

---

## Requirement

The app is a personal note-taking tool. Users have long asked for tags, and leadership now wants the tag list to:

1. Sync across a user's devices (iPhone, iPad, Mac Catalyst build).
2. Have a **"Tag of the day"** Home Screen Widget showing the most-used tag from the last 7 days.
3. Optionally sync a **curated public tag library** (editor-picked, read-only for users).

Constraints:

- Minimum supported iOS is 16; target is latest.
- No new third-party dependencies; stay on first-party Apple frameworks.
- App Store review: the sync + Widget combination requires Privacy Nutrition Label and PrivacyInfo.xcprivacy updates.
- Rollout behind a server flag `feature.tags.enabled` so we can disable the UI entry without resubmitting a build.

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces:

- [x] **User** — new Tags tab, Tag picker in the note editor, new Widget UI (small + medium), localized strings in the xcstrings catalog.
- [x] **System-interface** — Widget timeline reload triggers via `WidgetCenter.shared.reloadTimelines(ofKind:)`; Darwin notification when the main app writes tags; Share Extension does not change in scope but must continue to open the app cleanly.
- [x] **Information** — new Core Data entity `Tag` and relationship `Note ↔ Tag`; `.xcdatamodeld` v3 → v4 migration; CloudKit schema updates on both private (user tags) and public (curated library) databases; App Group container for Widget-readable snapshot.
- [x] **Operational** — entitlements change (add `com.apple.developer.icloud-container-identifiers`, App Group), Info.plist gains `NSUserNotificationsUsageDescription` is **not** needed (we do not notify); PrivacyInfo.xcprivacy gains the cloud-sync data type; new fastlane lane for the Widget binary; new signing profile for the Widget target.

Extension surfaces:

- [x] **Compliance** — App Store privacy questionnaire, PrivacyInfo.xcprivacy (tracking domains: none; data types: User Content synced via iCloud), App Group entitlement.
- [x] **Uncontrolled external** — iOS major version (Widget APIs churn across iOS 16/17/18), Apple Silicon vs Intel Macs (Catalyst builds), App Store review, CloudKit service availability.

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| User | New SwiftUI `TagsView`, new Widget bundle `DailyTagWidget`, new xcstrings keys, accessibility labels |
| System-interface | New AppIntent `SelectDailyTagIntent` for Widget configuration; Darwin notification `com.example.app.tags-changed`; Widget timeline provider |
| Information | Core Data v3 → v4 (add `Tag`, add `Note.tags` many-to-many); private CKContainer schema adds `CD_Tag`; public CKContainer adds `CuratedTag` record type; App Group UserDefaults key `dailyTagSnapshot` |
| Operational | Entitlements, PrivacyInfo.xcprivacy, Info.plist (no new keys needed), Widget target in Xcode project, fastlane lane, signing profile |
| Compliance | Privacy Nutrition Label, PrivacyInfo.xcprivacy, App Group entitlement |
| Uncontrolled external | Widget API evolution per iOS release, CloudKit availability, App Store review turnaround |

### Change boundaries

- Do **not** migrate existing notes to new Core Data storage; extend the schema additively.
- Do **not** gate the Widget on the server flag — the Widget must render a "No tags yet" state even when the feature flag is off (Widgets cannot call network).
- Do **not** store the full tag list in `UserDefaults`; the App Group shared container gets only the current-day snapshot.
- Do **not** ship the public database schema change in the same release as the private database schema change — private ships in v3.4, public in v3.5.

### Public behavior impact

YES — visible new tab, new Widget, new iCloud usage. App Store resubmission required.

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|---|---|---|---|---|
| User's tags | Core Data `Tag` entity (private CKContainer via `NSPersistentCloudKitContainer`) | Main app, Widget (via App Group snapshot), Share Extension | Local writes replicated to iCloud on network availability | Medium — Widget reads a snapshot, not the live DB; snapshot must be refreshed on every write |
| Curated public tag library | Public CKContainer record type `CuratedTag` | Main app (read-only) | Pulled via `CKQueryOperation` on app foreground + hourly background task | Low per-user, but schema changes are **not reversible** — public DB is one-way |
| Core Data model version | `.xcdatamodeld` bundle + `NSPersistentStoreCoordinator` version hash | Compile-time class generation, on-device migration detection | Xcode builds the model; app detects version mismatch at store-load time | **High** — lightweight migration handles additive changes; heavyweight requires a mapping model and a release containing both versions |
| Widget snapshot | App Group UserDefaults (suite `group.com.example.app`) under key `dailyTagSnapshot` (JSON-encoded struct) | Widget timeline provider, main app writer | Main app writes after any tag mutation, then `WidgetCenter.reloadTimelines(ofKind: "DailyTagWidget")` | High — schema drift between the struct written by the main app and the struct decoded by the Widget is silent; use a shared Swift package for the struct definition |
| Darwin notification name | Constant `Notifications.tagsChanged` in shared package | Every process that subscribes (main, Widget extension does not subscribe — it relies on `reloadTimelines`; Share Extension subscribes to refresh its tag list) | `CFNotificationCenterPostNotification` from the writing process | Medium — typo creates a silent non-delivery; centralize in a constant |

### Risks identified

1. **CloudKit public DB is forward-only.** Adding a field to `CuratedTag` is fine; renaming or deleting a field is mode 3 compensation (ship code that tolerates both names while the old field is deprecated, then schedule an internal-only removal). The Development → Production schema promotion is one-way per field.
2. **Core Data + CloudKit requires an additive-only schema.** `NSPersistentCloudKitContainer` rejects any non-optional field added to an existing entity without a default, and rejects delete rules that don't translate to CloudKit's (Cascade only on owning side).
3. **Widget struct drift.** If the main app writes a `TagSnapshot` struct with a new `emoji` field but the Widget is still on the old version (because the user did not update the Widget extension, which happens on binary-wide updates only but with a delay), the Widget decodes garbage. Use a shared Swift package and version the struct explicitly.
4. **App Group missing on Mac Catalyst.** App Groups work on Catalyst but the identifier format differs from pure iOS; verify the entitlement file has both variants.
5. **PrivacyInfo.xcprivacy drift.** Adding iCloud sync changes the "Data types collected" set. If the manifest is not updated, the App Store review flags it and the submission is rejected.
6. **Widget configuration AppIntent changes are surface changes.** If we change `SelectDailyTagIntent`'s parameter set, users who had the Widget configured on v3.3 lose their selection on v3.4. This is Pattern 4 (contract-defined).

---

## Phase 2 — Plan

### Change plan (in dependency order)

1. **Shared Swift package.** Create `SharedModel` package with:
   - `TagSnapshot` struct (explicit `schemaVersion: Int` field; current = 1).
   - `Notifications.tagsChanged` constant.
   - `AppGroup.identifier` constant.
   - Unit tests for codable round-trip.
2. **Information surface (Core Data v3 → v4).**
   - Add `Tag` entity with `id: UUID`, `name: String`, `colorHex: String?`, `createdAt: Date`.
   - Add many-to-many relationship `Note.tags ↔ Tag.notes` with `Nullify` delete rule on both sides (required by CloudKit).
   - Mark lightweight migration enabled; add a `ModelV4.xcmappingmodel` only if the migration test fails on real data. Run the migration test suite on:
     - A v3 store with zero notes.
     - A v3 store with 10k notes.
     - A v3 store that was created on iOS 16 and opened on iOS 18 (simulates a long-lived install).
3. **Information surface (CloudKit private schema).**
   - Deploy `CD_Tag` + join record to Development environment via first `NSPersistentCloudKitContainer.initializeCloudKitSchema` run.
   - Verify via CloudKit Dashboard that the record type, fields, and indexes match expectation.
   - Promote Development → Production as a deliberate step, documented in the release plan.
4. **Information surface (CloudKit public schema) — next release, not this one.**
   - Add `CuratedTag` record type with `name`, `colorHex`, `emoji`, `publishedAt` fields.
   - All fields optional; code tolerates missing fields for the bootstrap transition.
5. **User surface — main app.**
   - New `TagsView` (SwiftUI `NavigationStack`).
   - Tag picker sheet in `NoteEditorView`.
   - xcstrings catalog updates for every new string (zh-Hant, en, ja baseline).
6. **User surface — Widget.**
   - New Widget extension target `DailyTagWidget`.
   - Timeline provider reads App Group snapshot; if absent, returns an empty-state placeholder.
   - Configuration via `SelectDailyTagIntent` (AppIntent-based, iOS 17+ style; iOS 16 fallback to static Widget).
7. **System-interface — Darwin notification bridge.**
   - Main app writes snapshot → posts Darwin notification → calls `WidgetCenter.shared.reloadTimelines`.
   - Share Extension subscribes to the Darwin notification and refreshes its in-memory tag list.
8. **Operational — entitlements + signing.**
   - Add App Group `group.com.example.app` to main app, Widget, Share Extension.
   - Add iCloud container `iCloud.com.example.app` with CloudKit capability.
   - Widget target gets its own provisioning profile.
9. **Operational — PrivacyInfo.xcprivacy.**
   - Add `NSPrivacyCollectedDataTypeUserContent` with linked to identity: false, tracking: false, purpose: App Functionality.
   - No `NSPrivacyTracking` changes.
10. **Operational — fastlane + CI.**
    - New `match` entry for Widget signing.
    - Build the Widget binary as part of the app archive (automatic when the target is embedded).
    - Add a CI smoke step: install the archive to a simulator, confirm Widget renders the "No tags yet" state.

### Cross-cutting

- **Security / privacy:** tag names may be personal; ensure they are not logged. OSLog messages use `"\(tagName, privacy: .private)"`.
- **Accessibility:** Widget must have a VoiceOver summary ("Daily tag: Travel. Used 12 times this week."). Main app's color picker exposes the hex value as an accessibility label.
- **Localization:** tag names are user content, not localized. UI chrome is localized via xcstrings.
- **Rollback mode:**
  - UI entry point — mode 1 (server flag `feature.tags.enabled`).
  - Core Data schema — mode 2 (forward-only; once a device migrates to v4 it cannot go back).
  - Private CloudKit schema — mode 2 effectively (a user can reset their iCloud for this container; we are not forced into mode 3).
  - **Public CloudKit schema (next release) — mode 3.** Any rename / removal requires a migration with compensation code, not a rollback.
  - Widget + App Group snapshot format — mode 2 (write snapshot both with and without the new field for one release; then drop the old-field write).

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|---|---|---|---|
| TC-01 | Information | Core Data v3 → v4 lightweight migration on a store with 10k notes | Migration completes < 5s on iPhone 12; no crash; `git diff` of generated class matches expected |
| TC-02 | Information | Fresh install on iOS 16 creates v4 store directly | `NSPersistentStoreMetadataChangedNotification` absent; store version hash matches v4 |
| TC-03 | Information | CloudKit private schema promoted Development → Production without data loss | CloudKit Dashboard screenshot before/after; tester iCloud account shows existing tags post-promotion |
| TC-04 | System-interface | Tag created in main app → Widget updates within 10s | Screen recording |
| TC-05 | System-interface | Darwin notification fires on tag create/update/delete; Share Extension refreshes within one foreground cycle | Console log filtered by subsystem |
| TC-06 | User | Widget renders "No tags yet" empty state on a fresh install with no tags | Widget preview screenshot |
| TC-07 | User | Widget `SelectDailyTagIntent` persists across app updates (v3.3 → v3.4) | Install v3.3 test build, configure Widget, upgrade to v3.4, verify same tag still shown |
| TC-08 | Compliance | PrivacyInfo.xcprivacy contains `NSPrivacyCollectedDataTypeUserContent` with correct linkage fields | File diff; Xcode privacy report build shows the expected entries |
| TC-09 | Compliance | App Store Connect privacy questionnaire matches PrivacyInfo.xcprivacy | Screenshot of both |
| TC-10 | Operational | Entitlements file contains App Group and iCloud container for all three targets | `codesign -d --entitlements :- <app>` output for each |
| TC-11 | Regression | Existing notes editor still saves; existing Share Extension still opens the app | Manual smoke test |
| TC-12 | User (a11y) | VoiceOver reads Widget content correctly in both small and medium sizes | Audio recording |
| TC-13 | Uncontrolled-external | Mac Catalyst build shows the Widget-less UI gracefully (Widget is iOS-only this release) | Catalyst build run |
| TC-14 | Information | App Group snapshot struct round-trips through `JSONEncoder` / `JSONDecoder` with all `schemaVersion: 1` fields | Unit test in `SharedModel` package |

---

## Phase 4 — Implement

Execute in plan order. After each Core Data–touching task run:

```
xcodebuild -scheme NotesApp -destination 'platform=iOS Simulator,name=iPhone 15' test -only-testing:NotesAppTests/CoreDataMigrationTests
```

Additional gates:

- After task 1 (SharedModel), verify the package is consumed by **all three** targets (main, Widget, Share Extension). A missing consumer will manifest as a build error or — worse — a runtime "module not found" when the Widget first loads.
- After task 2 (Core Data v4), commit the `.xcdatamodeld` and the expected-schema snapshot JSON (check into `Tests/Fixtures/CoreData/v4.json`). CI diffs the snapshot against a regenerated one.
- After task 3 (private CloudKit schema), the first sync session in a clean iCloud test account must be observed and screenshotted — not merely trusted to the Xcode log.
- After task 6 (Widget), build and install to a real device (simulator Widget support is flaky across Xcode versions); verify the Widget renders within 30s of install.
- After task 8 (entitlements), run `codesign -d --entitlements :-` on each .app bundle and diff against expected — the most common App Store rejection in this class of change is a missing App Group entitlement on the Widget extension.

---

## Phase 5 — Review

Review checks beyond "tags work":

- Does the Widget use the **shared** `TagSnapshot` struct from `SharedModel`, or does it have a parallel struct definition? (A parallel definition is drift waiting to happen.)
- Does every Core Data relationship use `Nullify` (not `Cascade`, except on the owning side)? `NSPersistentCloudKitContainer` silently rejects `Cascade` on many-to-many.
- Does `NSPersistentCloudKitContainer.initializeCloudKitSchema` run only in a dev-build, gated by `#if DEBUG`? Accidentally shipping the schema-init call in a release build will attempt to redefine schema every launch.
- Does PrivacyInfo.xcprivacy match the actual data behavior? If the app reads `NSUserDefaults` in a way that collects device-wide data, that's a required-reason API; declare it.
- Does the Widget's AppIntent parameter set match exactly what was configured in previous versions? Changing `@Parameter` names in an AppIntent silently invalidates saved configurations.
- Does the Darwin notification name come from the `Notifications.tagsChanged` constant at every call site, or is it a string literal anywhere?
- Did the manifest's `rollback_mode` stay at 2 for private schema + mode 1 for UI flag + explicit note that public schema (next release) is mode 3?

---

## Phase 6 — Sign-off

- All TCs passed with evidence; TC-03 must be observed on a real iCloud account promoted Development → Production, not merely simulated.
- TestFlight internal build distributed; at least three tester iCloud accounts successfully sync tags across two devices each.
- Privacy Nutrition Label updated in App Store Connect and matches PrivacyInfo.xcprivacy (`xcode-build-settings` privacy report compared).
- Widget validated on a physical iPhone running iOS 16 (static-Widget fallback) and iOS 17 (AppIntent configuration).
- Phased release configured at 1% for day 1.

---

## Phase 7 — Deliver

Completion-report summary:

- Capability: tag creation + assignment across notes, CloudKit sync of user tags, "Daily tag" Home Screen Widget.
- Surface coverage: four core + compliance + uncontrolled external.
- Verification: TC-01..14 passed with evidence.
- Rollback plan:
  - UI: mode 1 via server flag `feature.tags.enabled`.
  - Core Data + private CloudKit: mode 2 (forward-only).
  - Public CloudKit (next release): mode 3 (planned in separate Change Manifest).
  - Widget snapshot struct: mode 2 with dual-write-then-drop cadence.
- Observation window: 7 days post-rollout, watch the CloudKit error rate in OSLog, MetricKit hangs, Widget timeline-reload failures, and App Store review PrivacyInfo.xcprivacy flags.

---

## What this example is meant to show

1. **CloudKit public ≠ private for rollback.** Private DB mishaps are contained per-user; public DB schema is global and forward-only. Split them across releases; never ship both in the same resubmission.
2. **Core Data `.xcdatamodeld` is a three-way SoT.** Bundle ↔ generated classes ↔ on-device store. Lightweight migration is not a guarantee; test against a real 10k-row store, not only a fresh simulator.
3. **Widget + App is a two-process system.** Everything crossing the boundary — structs, notifications, entitlements — is a contract. Own that contract in one Swift package.
4. **PrivacyInfo.xcprivacy is a surface, not a compliance checkbox.** Drift between the manifest, the Nutrition Label, and the actual code is the most common App Store review rejection for apps in this class; fold it into the review gate, not the submission gate.
5. **Widget AppIntent parameters are a user-configuration contract.** Treat `@Parameter` names and types with the same care as a public API signature.
