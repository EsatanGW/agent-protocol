# Worked Example: Add offline draft-saving to a form in an Android Kotlin + XML app

> This example fleshes out the outline in `docs/bridges/android-kotlin-stack-bridge.md` §Reference worked example outline.
> It exercises the three Android patterns the bridge calls out as common footguns:
>
> - **Room schema as a dual-representation SoT** (entity classes ↔ exported schema JSON ↔ live DB file).
> - **WorkManager unique-work names as an enum** (typo in the unique name silently creates a parallel queue).
> - **Shipped-APK rollback asymmetry** (Play Store "halt rollout" does not downgrade already-updated users).
>
> All names, paths, and data structures are fictitious.

---

## Requirement

The app has a multi-step "Submit Expense Report" form. Users complain that if the process is killed (battery, OS restart, low-memory kill) mid-way, the form is wiped.

Product asks:

> "Every time the user edits a field, save the draft locally. On app restart, offer to resume. When connectivity returns, sync the draft to the server as a `pending` report."

Constraints:

- Autosave must work with no network.
- Draft survives process death and device reboot.
- Sync runs on background power/network availability, not in the foreground.
- Minimum supported API level is 24; target API matches current Play Store requirement.

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces:
- [x] User — new "Resume draft?" banner on form entry, autosave indicator, sync-status chip per draft in a list.
- [x] System-interface — existing `POST /expense-reports` endpoint; new idempotency-key header for retry safety.
- [x] Information — new Room entity `DraftEntity` + migration; WorkManager work-data schema.
- [x] Operational — new analytics events `draft_autosaved`, `draft_resumed`, `draft_synced`; Crashlytics breadcrumb on WorkManager failure.

Extension surfaces:
- [x] Uncontrollable external — Android vendor-OS forks (battery-optimization whitelists vary), Play Store target-SDK-deadline policy, OS background-execution policy changes across API levels.

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| User | Fragment layout `fragment_expense_form.xml` gains an autosave indicator; list screen adds a sync-status chip. |
| System-interface | Request gains `Idempotency-Key` header; response-shape unchanged. |
| Information | New `DraftEntity` + FTS not needed; migration from DB v7 → v8; work-data keys `DRAFT_ID`, `ATTEMPT_COUNT`. |
| Operational | Three new analytics events in the registry; WorkManager retry policy documented. |
| Uncontrollable external | Vendor fork behaviors: some OEMs aggressively kill background workers when app is swiped from recents; behavior differs per family. |

### Change boundaries

- Do **not** change the submission contract shape (only add a header).
- Do **not** rewrite the form layout — only add an indicator.
- Do **not** enable destructive migrations; this must be forward-only.

### Public behavior impact

YES — users see a new resume banner and sync-status UI; shipped APK is mode-2 rollback.

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|---|---|---|---|---|
| Draft content | Local Room DB until synced; server DB after | Form Fragment (read on resume), WorkManager worker (read on sync) | Autosave write on field change | Medium — two consumers read the same row; reconcile via a single repository |
| Draft sync status | Local `DraftEntity.status` enum | List chip, WorkManager worker, support tooling (log redaction) | Worker writes status transitions | Medium — transition must be guarded (pattern 6) |
| Unique work name | Constant `SyncWorkNames.DRAFT_SYNC` | WorkManager enqueue call sites | Hard-coded constant referenced by string | **High** — a typo in any call site silently creates a parallel work queue |
| Schema version | `AppDatabase.version` + exported JSON at `app/schemas/<db>/<version>.json` | Room compiler, migration registry | `@Database(version = 8)` + `MIGRATION_7_8` registered | High — changing version without providing a migration is a compile-time-but-runtime-crash scenario |

### Risks identified

1. **WorkManager unique-work name typo.** Two call sites using slightly different strings silently create two queues and double-sync.
2. **Room migration drift.** Bumping `@Database(version = 8)` without exporting the new schema JSON or registering `MIGRATION_7_8` crashes on real devices that came from v7.
3. **Vendor-fork background kills.** A user on an OEM with aggressive battery management will not see their draft sync until the app is re-foregrounded.
4. **Process death mid-autosave.** The autosave coroutine must be scoped to `viewModelScope` with `SharingStarted.WhileSubscribed`, not `GlobalScope`; otherwise it is killed mid-write and the draft is partial.

---

## Phase 2 — Plan

### Change plan (in dependency order)

1. **Information surface:** define `DraftEntity` with `@PrimaryKey` `local_id`, nullable `server_id`, `content` (JSON-serialized Kotlin class), `status` (enum: DRAFT / PENDING_SYNC / SYNCING / SYNCED / CONFLICT), timestamps. Bump `@Database(version = 8)`, write `MIGRATION_7_8` with forward-only SQL, and run `./gradlew :app:compileDebugKotlin` to export the new schema JSON.
2. **Information surface (work data):** define a `Worker` companion object holding input-data keys (`KEY_DRAFT_ID`, `KEY_ATTEMPT`) as constants — this is the schema for the channel between enqueue site and worker.
3. **System-interface surface:** add the `Idempotency-Key` header in the Retrofit adapter (use draft's `local_id`); document that a retried request with the same key must be idempotent server-side.
4. **User surface:** add autosave indicator and resume banner to `fragment_expense_form.xml`; bind via the generated `FragmentExpenseFormBinding` (ViewBinding). Add the sync-status chip to the list item layout.
5. **Operational surface (WorkManager):** enqueue a `OneTimeWorkRequest` via `enqueueUniqueWork(SyncWorkNames.DRAFT_SYNC, ExistingWorkPolicy.APPEND_OR_REPLACE, request)`; backoff = exponential from 30s; constraints = network connected, battery not low.
6. **Operational surface (analytics):** register the three events in `analytics/events.kt`; redact `content` from logs.
7. **Uncontrolled-external register update:** add a "vendor-OS background-kill behavior" row with a quarterly review date.

### Cross-cutting

- **Security:** draft content may contain expense amounts and vendor names — audit that `Timber` tree redacts these before shipping to Crashlytics.
- **ProGuard / R8:** `DraftEntity` and any `@JsonClass` types used in the Moshi adapter need keep rules if the app uses R8 full mode; the project's current `proguard-rules.pro` already has a catch-all for `@Entity` classes, but the work-data key constants need no keep rules (they are inline).
- **Permissions:** no new permissions.
- **Rollback mode:** shipped APK = mode 2 (forward-fix); feature is behind a remote flag `expense_offline_draft` so we can disable the UI entry (mode 1 for the UI). The underlying Room migration is mode 2 (already-migrated devices cannot downgrade their DB).

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|---|---|---|---|
| TC-01 | Information | Room migration v7 → v8 on a real device populated from a v7 backup | Database inspector dump before/after |
| TC-02 | Information | Exported schema JSON matches `DraftEntity` after `compileDebugKotlin` | `git diff --exit-code app/schemas` output |
| TC-03 | User | Kill app mid-edit, reopen, resume banner appears, fields restored | Screen recording |
| TC-04 | System-interface | Two retries with same `Idempotency-Key` produce one server-side row | Server log |
| TC-05 | Operational | WorkManager enqueued with unique name `DRAFT_SYNC`; second enqueue replaces, does not duplicate | `adb shell dumpsys jobscheduler` snapshot |
| TC-06 | Operational | On airplane mode, worker is retained; on reconnect, runs within 30s | Log capture |
| TC-07 | Operational | On a Chinese-OEM device with aggressive battery management, worker runs within 10 min of foreground return | Vendor-specific device log |
| TC-08 | Regression | Existing "online submit" flow unaffected | Smoke-test report |
| TC-09 | User | Screen reader announces the autosave indicator correctly | TalkBack recording |

---

## Phase 4 — Implement

Execute in plan order; run `./gradlew :app:compileDebugKotlin testDebugUnitTest` after each migration-touching task.

Additional gates:

- After task 1 (Room entity + migration), run `git diff app/schemas` — if nothing changed, the migration was silent; investigate.
- After task 5 (WorkManager), grep the code for every `enqueueUniqueWork` call and confirm the name comes from `SyncWorkNames`, not a string literal.

---

## Phase 5 — Review

Review checks beyond "draft saves":

- Does every `enqueueUniqueWork` call site use the same named constant? (Silent duplicate queues otherwise.)
- Does the migration SQL handle every v7 shape, including the partial schema from the abandoned "quick-save" feature that was feature-flagged off in v5? (Check via database-inspector against a v5-flag-off backup.)
- Does the autosave coroutine live on `viewModelScope`? A `GlobalScope.launch` would lose the autosave on process death.
- Is the `Idempotency-Key` derived from `DraftEntity.local_id`, not from a random UUID regenerated per retry? (Random-per-retry defeats the purpose.)
- Has the uncontrolled-external vendor-fork row been added with a review date?

---

## Phase 6 — Sign-off

- All TCs passed with evidence; TC-07 in particular must be tested on a real vendor-fork device, not an emulator.
- Room schema JSON committed; migration test suite green.
- Play Internal Testing build uploaded; no crashes for 24h on the internal tester cohort.
- Rollback plan documented: UI behind remote flag (mode 1); APK is mode 2.

---

## Phase 7 — Deliver

Completion-report summary:

- Capability: offline draft autosave + background sync for expense reports.
- Surface coverage: four core + uncontrolled external.
- Verification: TC-01..09 passed with evidence.
- Rollback plan: feature flag for UI (mode 1); APK forward-fix (mode 2); Room migration forward-only (mode 2).
- Observation window: 7 days post-rollout, watch `draft_synced` success rate and vendor-fork distribution in WorkManager failure logs.

---

## What this example is meant to show

1. **A Room migration is three things, not one.** The entity class, the migration SQL, and the exported schema JSON must all agree. CI that only compiles without running `./gradlew :app:compileDebugKotlin` on a committed DB snapshot will miss the drift.
2. **A WorkManager unique-work name is an enum, not a string.** Treat it like an enum: declare in one place, import everywhere. A typo is a silent parallel queue.
3. **Shipped APK rollback is mode 2 at best.** Feature flags move the UI to mode 1, but the DB migration and WorkManager scheduled work stay mode 2. Plan for both simultaneously.
4. **Vendor-OS forks are uncontrolled interfaces**, not edge-case emulator bugs. They need a quarterly-review entry.
