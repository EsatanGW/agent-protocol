# Worked Example: align order-status names so consumers stop each interpreting them differently

This is a refactor / contract-alignment example.
It illustrates a very common situation: nothing new is being added, but naming / contract drift has left the system in a chronically fragile state.

---

## Background

The system has long carried three names for the same state:
- `PENDING_APPROVAL`
- `WAITING_APPROVAL`
- `TO_BE_APPROVED`

Different consumers use different names, which leads to:
- Reports missing rows.
- Inconsistent frontend display.
- Webhook-downstream mappings becoming tangled.

This kind of task is best approached with the **information surface** as the center of gravity.

---

## Phase 0 — Clarify

### Affected surfaces
- User surface: status copy and display mapping.
- System-interface surface: status values in API / event / webhook payloads.
- Information surface: enum, DB values, mapping tables, validation.
- Operational surface: changelog, migration notes, consumer communication, rollout notes.

### Change boundaries
- Do not change business semantics.
- Only unify the name and align consumers.
- If aliasing is needed, keep a compatibility window — don't hard-cut in one step.

### Public behavior impact
YES (consumers will see the status name change).

### Open questions
- ⛔ Which name becomes the canonical value?
- ⛔ Will we allow a compatibility window that accepts the old values?
- ⚠️ Which external consumers are already coupled to the old name?

---

## Phase 1 — Investigate

### Main flow
- Source of truth: order-status enum / DB status value.
- Consumers: frontend display layer, reports, webhook downstream, internal batch jobs.

### Findings
- The DB stores `PENDING_APPROVAL`.
- Some API responses get rewritten to `WAITING_APPROVAL` by an adapter.
- Webhook payloads still send `TO_BE_APPROVED`.
- The frontend i18n keys have their own separate mapping.

### Nature of the problem
This is not a simple rename;
it is multiple consumers having each performed their own local reinterpretation of the same information surface.

---

## Phase 2 — Plan

### Change map

| Surface | Main change |
|---------|-------------|
| Information | Define the canonical status = `PENDING_APPROVAL`. |
| System-interface | API / webhook / adapter layers all emit the canonical value; keep an alias parser where needed. |
| User | Align UI mapping and i18n with the canonical value. |
| Operational | Migration note, deprecation notice, consumer communication. |

### Tasks
- Task 1: build the status canonical-mapping table.
- Task 2: update API / event / webhook producers.
- Task 3: update UI mapping and i18n.
- Task 4: add alias compatibility and a deprecation warning.
- Task 5: add changelog, migration note, consumer notice.

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|-----|---------|-----------|----------|
| TC-01 | Information | Only the canonical source of truth remains in the enum / mapping tables | Test output |
| TC-02 | System-interface | API response uniformly emits the canonical value | Request / response capture |
| TC-03 | System-interface | The old alias is still accepted by the parser (compatibility window) | Test output |
| TC-04 | User | UI display and i18n render correctly | Screenshot |
| TC-05 | Operational | Changelog / migration note / deprecation note are complete | Document diff |

---

## Phase 4 — Implement

- Fix the canonical value first.
- Adjust producers next.
- Adjust consumers after that.
- Finish with operational docs and the deprecation message.

---

## Phase 5 — Review

Review checks:
- Is there truly only one source of truth now?
- Did the other consumers actually switch to the canonical value, or did they just wrap another patch layer on top?
- Is there any downstream mapping that was missed?

---

## Phase 6 — Sign-off

- The canonical value is singular.
- All consumers have been aligned.
- The compatibility strategy is explicit.
- Documentation and the rollout note are complete.

---

## Phase 7 — Deliver

Delivery summary:
- This is not a cosmetic rename.
- This is contract alignment plus consumer cleanup.
- The real outcome is that the system is less likely to fracture into a second dialect.

---

## What this example is meant to show

1. Refactor is not only code cleanup; it can also be repair work on long-standing contract drift.
2. A canonical source of truth is the center of gravity for this kind of task.
3. This kind of task fits Full mode — it is not "just a quick rename."
