# Worked Example: Add an "Offline-Capable Expense Entry" Feature to a Mobile App

> This example shows how to apply the methodology to mobile-specific challenges:
> - Offline-first (Temporal-Local Truth, SoT pattern 7).
> - State transitions (Transition-Defined Truth, SoT pattern 6).
> - Rollback asymmetry (mobile cannot force users onto a lower version).
> - The impact of breaking changes under version fragmentation.
>
> All names, paths, and data structures are fictitious.

---

## Requirement

An expense-tracking app currently requires connectivity for every write.
Product decision: **users should be able to add entries in airplane mode, on the subway, or traveling abroad** — data must auto-sync when they come back online.

Scope:
- Offline creation of entries (amount, category, note, photo).
- Offline edit / delete of entries from the past 30 days.
- Sync-status UI (which entries are "pending sync," "syncing," "conflict").
- Conflict-resolution flow.

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces:
- [x] User — list, form, sync-status icons, conflict-resolution dialog.
- [x] System-interface — sync API, conflict-detection API.
- [x] Information — local SQLite schema, server schema, conflict metadata.
- [x] Operational — sync success rate, conflict rate, support diagnosability.

Extension surfaces:
- [x] Experience — sync animation, "optimistic UI" feedback while offline.
- [x] Uncontrollable external dependencies — iOS / Android background-execution limits, SQLite version compatibility.

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| User | Entry list gains a sync-status icon, conflict dialog, offline prompt banner. |
| System-interface | Add `POST /sync` (batch upload), `GET /sync/since` (download), `POST /resolve-conflict`. |
| Information | SQLite schema gains `local_id`, `server_id`, `sync_status`, `updated_at`, `version`; server-side adds `version`. |
| Operational | `sync_success_rate`, `conflict_rate`, `queue_depth`; support tooling gains sync-log lookup. |
| Experience | Optimistic UI (write reflects immediately), sync-status micro-animation, conflict-resolution UX. |
| Uncontrollable external | iOS Background Tasks (killed under low battery), Android WorkManager (OEM-customized builds may delay execution). |

### Source of truth — multi-pattern combination

This case triggers **three SoT patterns** simultaneously:

| Information | SoT pattern | Notes |
|-------------|-------------|-------|
| Entries already synced | Pattern 1 (Schema-Defined) | Server DB is the truth. |
| **Entries created / edited while offline** | **Pattern 7 (Temporal-Local)** | Client SQLite is temporarily the truth; ownership transfers after sync. |
| Entry sync status (local / syncing / synced / conflict) | **Pattern 6 (Transition-Defined)** | Must follow legal transitions. |
| Entry category definitions | Pattern 2 (Config-Defined) | Server config. |

### Public behavior impact
- Yes: users will see a brand-new sync-status UI; the offline experience goes from "unusable" to "fully usable."
- Acceptance criteria and evidence are not optional.

### Open questions
- ⛔ Conflict-resolution strategy: last-write-wins, version vector, or let the user choose?
- ⛔ How far back can a user edit offline? (Affects how much history the client retains.)
- ⚠️ Multi-device: if device A writes offline but hasn't synced, should device B see it?
- ⚠️ Sync-retry ceiling — and how should we treat entries past that ceiling?

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|-------------|-----|-----------|----------------|-------------|
| Already-synced entries | Server DB | iOS app, Android app, web reports | API pull + push | Low |
| Pending-sync entries (local) | **Device SQLite (temporal-local)** | UI list, sync worker | Sync queue | Medium — needs user intervention on conflict |
| Sync-status enum | `(local) → (syncing) → (synced)` or `→ (conflict) → (synced)` | UI icon, operational dashboard | State machine | High — illegal transitions make UI disagree with reality |
| Entry version | Each entry has `version` (server) + `local_revision` (client) | Conflict detection | Optimistic concurrency | High — this is the basis for conflict resolution |

### Irreversible side-effect inventory (preparing for Phase 2 rollback)

- [x] Client versions already on user devices — cannot be downgraded.
- [x] SQLite schema migrations already written on-device — no reliable down-migration after upgrade.
- [ ] Charged / shipped: N/A in this case.
- [ ] Push notifications already sent: possible (when a conflict needs a notification).
- [x] Offline data already synced to the server DB: once written, we cannot pretend it didn't happen.

### Uncontrollable external-dependency inventory

| Dependency | Risk | Mitigation |
|------------|------|------------|
| iOS Background Tasks | Not executed under low battery or if the user kills the app | Trigger sync on app launch as well. |
| Android WorkManager | Some OEM builds don't fully follow the spec | Add a foreground-service fallback. |
| SQLite migration tooling | Major upgrades can be incompatible | Forward-only migration; do not depend on down-migration. |

---

## Phase 2 — Plan

### Change map

| Surface | Main change |
|---------|-------------|
| User | Sync-status icon, conflict-resolution dialog, offline banner, new list fields. |
| System-interface | Add `POST /sync`, `GET /sync/since`, `POST /resolve-conflict`. |
| Information | SQLite schema migration (add `local_id` / `server_id` / `sync_status` / `version`); server side adds `version`. |
| Operational | Dashboard, support-lookup tooling, alert rules. |
| Experience | Optimistic UI, sync animation, conflict-resolution UX. |

### State machine (Transition-Defined Truth)

Legal transitions, explicitly enumerated:

```
       ┌──────────────┐
       │   (created)  │
       └──────┬───────┘
              ▼
       ┌──────────────┐
       │    local     │  ← offline create
       └──────┬───────┘
              ▼
       ┌──────────────┐         ┌──────────────┐
       │   syncing    │────────▶│   conflict   │
       └──────┬───────┘         └──────┬───────┘
              ▼                        ▼
       ┌──────────────┐         ┌──────────────┐
       │    synced    │◀────────│ user_resolved│
       └──────────────┘         └──────────────┘
```

**Forbidden transitions:**
- `synced → local` (sync complete should not regress to local-only).
- `local → synced` (cannot skip `syncing`).
- `conflict → synced` (must pass through `user_resolved` first).

### Breaking-change assessment (per `breaking-change-framework.md`)

| Change | Level | Path |
|--------|-------|------|
| Server adds `/sync` endpoints | L0 (additive) | Merge directly. |
| Entry adds `version` field | L0 (additive) | Optional field, default 0. |
| Client SQLite schema adds fields | L2 (structural), but scoped to the client | Forward-only migration. |
| User education on conflict resolution | L1 (behavioral), because user expectations change | In-app onboarding paired with the new version. |

### Rollback plan (per `rollback-asymmetry.md`)

**Primary mode: mode 2 (forward-fix rollback).**

Reasons:
- Mobile clients already downloaded cannot be force-downgraded → mode 1 is out.
- On-device SQLite has already migrated; down-migration is unreliable → mode 1 is out.
- But this does not touch money flow / irreversible business actions → mode 3 is not required.

**Forward-fix paths:**
- Server-side kill switch: can block specific client versions from calling `/sync`, degrading the problematic version to "offline read-only."
- Remote config flag: can disable the "offline write" entry, leaving users in offline-browse mode only.
- Hotfix client: expedited app-review release, combined with the minimum-supported-version mechanism to force upgrade.

**Containment:**
- Staged rollout: 1% → 10% → 50% → 100%.
- Monitoring: `sync_success_rate`, `conflict_rate`, crash-free rate.

### Cross-cutting impact

| Dimension | Focus |
|-----------|-------|
| Security | Sync-token validation, preventing cross-account data leakage during sync, on-device PII encryption. |
| Performance | Sync does not block the UI, batch size has a ceiling, photos sync via a separate channel. |
| Observability | Every sync carries a trace ID, conflicts produce structured logs, support can look up a user's recent sync history. |
| Testability | Simulated offline / simulated conflict / simulated partial-success sync (reproducible end-to-end scenarios). |
| **Error handling** | Sync-failure classification (network / auth / conflict / server bug), retry strategy, user-understandable error messages. |

### Tasks (in dependency order)

1. Define the state machine + the irreversible side-effect inventory + the conflict strategy.
2. SQLite schema migration (forward-only).
3. Server schema adds `version`; add the sync API.
4. Client sync worker (with retry + idempotency).
5. UI: sync-status icon, optimistic UI.
6. UI: conflict-resolution flow.
7. Support tooling adds sync-log lookup.
8. Monitoring dashboard, alert rules, kill switch.
9. In-app onboarding (educating users about the new feature and the concept of conflicts).

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|-----|---------|-----------|----------|
| TC-01 | Information | SQLite migration succeeds on all supported versions | CI matrix test |
| TC-02 | System-interface | Offline writes → batch sync succeeds after coming online | Integration test + logs |
| TC-03 | User | An offline-created entry immediately shows a "pending sync" icon in the list | Screenshot |
| TC-04 | User + System-interface | The same entry edited on two devices simultaneously → conflict dialog fires | Screenshot + server log |
| TC-05 | Experience | Optimistic UI: tapping Save returns to the list instantly, no spinner | Recording |
| TC-06 | Operational | Sync-failure error categories land in the dashboard correctly | Dashboard screenshot |
| TC-07 | Cross-cutting (error handling) | User messages are understandable + offer recovery actions in every failure scenario | Screenshot matrix |
| TC-08 | Cross-cutting (rollback) | After the server kill switch engages, the problematic client version degrades to read-only | Operation evidence |
| TC-09 | Regression | Pure-online usage is unaffected | End-to-end suite |
| TC-10 | State machine | Illegal transitions (e.g. `synced → local`) are rejected and logged | Unit test |

---

## Phase 4 — Implement

Build in the Phase 2 task order.
Key rule: state-machine guards are enforced on both client and server — not just via UI.

---

## Phase 5 — Review

**Review checklist:**

- [ ] Legal transitions in the state machine are enforced at the producer layer (not just UI).
- [ ] Conflict-resolution logic has matching unit tests (covering edge cases: both sides delete, A edits while B deletes, A deletes while B edits).
- [ ] SQLite migration is forward-only, with no dependence on down-migration.
- [ ] Sync API is idempotent (uploading the same `local_id` multiple times does not double-write).
- [ ] Optimistic UI correctly rolls back its display on failure.
- [ ] Support tooling has sync-log lookup.
- [ ] Kill switch has been drilled.

---

## Phase 6 — Sign-off

- All test cases passed.
- State machine validated by example traces (trace screenshots attached).
- Rollback plan reviewed by the on-call team.
- Customer support has received onboarding and tooling walkthroughs.

---

## Phase 7 — Deliver

- Staged rollout starting at 1%.
- Server kill switch + remote config flag pre-wired.
- Support SOP updated to include "lookup steps when a user reports a sync issue."

---

## Phase 8 — Post-delivery observation

| Time | Focus |
|------|-------|
| T+24h | `sync_success_rate` ≥ 99%, no spike in conflict rate, no spike in crashes. |
| T+72h | Conflict rate matches expectation (product target < 0.5%); support-ticket categorization. |
| T+7d | Offline-usage share among users; user drop-off rate in the conflict-resolution flow (UX success indicator). |

**Feedback goals:** calibrate the best-practice combination of SoT patterns 6 + 7, and collect real-world data on conflict-resolution UX.

---

## What this example demonstrates

1. **Multi-SoT combination:** in practice you rarely use only one pattern — patterns 6 + 7 + 1 + 2 showing up together is the norm.
2. **Uncontrollable external dependencies are core Phase 1 work:** iOS / Android background-execution limits are somebody else's decisions, not your bug.
3. **Mobile forces forward-fix thinking:** the Phase 2 plan must write this reality in, rather than pretending a rollback is possible.
4. **State transitions are enforced at the producer:** the UI is not enough; the server must reject illegal transitions.
5. **Error handling as cross-cutting concern:** failure modes in offline scenarios are far more complex than online ones — every one needs user-facing language.
