# Worked Example: Migrate User Notification Settings from a Single Column to a Structured Preferences Model

This is a migration / rollout example.
It illustrates:
- Migration is not just a schema change.
- You also have to handle consumer compatibility, rollback, operational observation, and staged rollout.

All names, paths, and data structures are fictitious.

---

## Background

The legacy system has one column:
- `users.notification_enabled: boolean`

The new requirements need to support:
- email
- push
- sms
- marketing opt-in

So it needs to evolve into a structured preferences model:
- `user_notification_preferences`

---

## Why this case matters

Many teams treat migration as:
- Change the schema.
- Run a script.
- Done.

The actual hard part is:
- Legacy consumers still read the old column.
- New consumers want the structured shape.
- Rollout must be staged.
- Rollback must have a real exit.

This is the kind of task where the operational surface and the information surface carry most of the weight.

---

## Phase 0 — Clarify

### Affected surfaces
- User surface: notification-settings page.
- System-interface: `GET /me/preferences`, `PATCH /me/preferences`, notification-dispatch service.
- Information: single boolean column → structured preference object.
- Operational: migration, rollout, rollback, monitoring, handoff.

### Change boundaries
- This ticket includes a dual-write / dual-read compatibility window.
- This ticket does not drop the old column.
- This ticket includes rollout + rollback notes.

### Public behavior impact
YES
- Settings UI changes.
- API payload changes.
- Dispatch logic becomes preference-object-driven.

### Open questions
- ⛔ When the old column and the new preference disagree, which is the source of truth?
- ⛔ How long does the dual-read window last for consumers?
- ⚠️ Does the migration script run once, or in batches?
- ⚠️ How do we write back to the old column during a rollback?

---

## Phase 1 — Investigate

### Main flow
- Old SoT: `users.notification_enabled`.
- New SoT (target): `user_notification_preferences`.
- Consumers: settings page, notification-dispatch service, marketing-preference export, customer-support viewer.

### Findings
- Notification dispatch currently reads only the boolean column.
- The settings page already needs 4 independent options.
- The marketing export still queries the old column directly.
- Monitoring has no preference-migration metrics today.

### Risks
- If both old and new sources exist without a defined precedence, consumers will read different answers.
- Without an explicit dual-read / dual-write strategy during rollout, rollback will fail.

---

## Phase 2 — Plan

### Change map

| Surface | Main change |
|---------|-------------|
| User | Settings page goes from a single toggle to multi-field notification preferences. |
| System-interface | Preferences API reads / writes the structured object; dispatch service reads the canonical preference. |
| Information | Create `user_notification_preferences`, define the canonical model, define the dual-read / dual-write strategy. |
| Operational | Migration script, rollout checklist, rollback plan, monitoring metrics. |

### Dependency order
1. Define the canonical model and the dual-read / dual-write strategy.
2. Create the new data structure and the backfill migration.
3. Adjust producers / consumers.
4. Ship the user-surface changes.
5. Turn on rollout monitoring.
6. Finalize handoff / rollback notes.

### Tasks
- Task 1: define the canonical preference model.
- Task 2: create the new table + the backfill migration.
- Task 3: dual-read / dual-write at the service layer.
- Task 4: settings page + API contract update.
- Task 5: monitoring metrics, rollout checklist, rollback notes.

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|-----|---------|-----------|----------|
| TC-01 | Information | After migration, every legacy row has a corresponding preference row | Query result |
| TC-02 | System-interface | API correctly reads the preference object | Request / response |
| TC-03 | System-interface | Legacy consumers continue to work during the dual-read window | Integration test |
| TC-04 | User | Settings page correctly displays and updates multi-field preferences | Screenshot |
| TC-05 | Operational | Rollout checklist, rollback notes, and monitoring dashboard exist | Document diff / screenshot |
| TC-06 | Regression | Consumers relying only on the old column are unaffected during the compatibility window | Test output |

---

## Phase 4 — Implement

- Start by defining the canonical model.
- Then do the migration + dual-read / dual-write.
- Then update consumers and the UI.
- Finish with rollout / rollback / observability.

---

## Phase 5 — Review

The bar is not "the migration script runs cleanly." It's:
- Is the source of truth clear?
- Is the dual-read / dual-write behavior explainable?
- Is the rollout safe?
- Is the rollback actually executable?
- Which consumers still live in the old world — are they explicitly enumerated?

---

## Phase 6 — Sign-off

- Migration verified.
- Consumer compatibility strategy verified.
- Rollout / rollback information complete.
- Monitoring and handoff in place.

---

## Phase 7 — Deliver

Delivery summary:
- This is not a pure schema migration.
- This is a source-of-truth transition from a single column to a structured preferences model.
- The real outcome is that consumers are aligned, the rollout is safe, rollback is executable, and observability is complete.

---

## What this example is meant to show

1. Migration / rollout tasks are inherently Full mode.
2. The operational surface is not an accessory — it's central to successful delivery.
3. The source-of-truth switch is more critical than the schema itself.
