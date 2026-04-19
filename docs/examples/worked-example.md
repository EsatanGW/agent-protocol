# Worked Example: batch-resend invoices from the admin console

This is a worked example that shows how to apply the methodology to a realistic-feeling requirement.
All names, paths, and data structures are fictitious — they illustrate the mode of thinking, not a technology template.

---

## Requirement

An admin-console user discovers that some completed orders have no matching invoice generated.
They request a new feature: "batch resend invoices":
- Pick a time range and an optional channel filter.
- The system re-issues invoices for any matching orders.
- Show success and failure counts.

---

## Phase 0 — Clarify

### Affected surfaces
- User surface: the order-list toolbar in the admin console, the resend dialog, result messaging, new-state display.
- System-interface surface: new endpoint `POST /admin/invoices/resend-batch`.
- Information surface: add `RESENT` to `invoice.status`; new request/response contract.
- Operational surface: audit log, doc updates, observation metrics.

### Change boundaries
- Do not change the original invoice-generation logic.
- Do not go async (the user expects to see the result synchronously).
- Do not offer scheduled runs; only a manual batch trigger.

### Public behavior impact
YES (new endpoint, new state semantics, new admin feature).

### Open questions
- ⛔ Partial-failure strategy? → Answer: skip failures, continue processing the rest.
- ⚠️ Batch size limit? → Answer: estimated ≤ 1,000 rows per call; synchronous is fine.
- ⚠️ Permissions? → Answer: a new permission code; finance-admin role only.
- ℹ️ Do we need a result-CSV download? → Answer: not this ticket; plan as a follow-up.

---

## Phase 1 — Investigate

### Main flow
- Source of truth: `invoice.status`; the order-to-channel mapping rules.
- Capability flow: admin action → conditional query → per-row resend → aggregated result returned → UI refresh.

### Impact list
- Admin-console order-list component.
- Resend dialog (new).
- i18n text in three languages.
- Resend endpoint.
- A new batch method on `InvoiceService`.
- `invoice.status` enum extension.
- Audit-log fields.
- Docs and changelog.

### Risks
- If the new status semantics aren't synced to all consumers, the list page may show an unknown status.
- If the batch contains duplicate orders, the handler must be idempotent.

---

## Phase 2 — Plan

### Change map

| Surface | Main change |
|---------|-------------|
| User | Toolbar entry + resend dialog + result messaging + new-state display + i18n. |
| System-interface | `POST /admin/invoices/resend-batch` contract + response shape. |
| Information | Add `RESENT` to `invoice.status`; define request / response payloads. |
| Operational | New permission code, audit log, docs / changelog. |

### Dependency order
1. Information surface (state semantics, contract).
2. System-interface surface (endpoint implementation).
3. User surface (entry, dialog, state presentation, i18n).
4. Operational surface (permissions, logging, docs).
5. End-to-end flow verification.

### Tasks (excerpt)
- Task 1: extend `invoice.status`, define batch-resend behavior.
- Task 2: add the batch-resend endpoint + payload.
- Task 3: admin-console entry, dialog, result messaging.
- Task 4: permissions, audit log, docs.
- Task 5: end-to-end capability verification.

---

## Phase 3 — Test Plan (excerpt)

| TC# | Surface | Test case | Evidence |
|-----|---------|-----------|----------|
| TC-01 | Information | Legacy data unaffected after status enum is extended | Migration + query result |
| TC-02 | System-interface | Happy-path batch resend produces results | Request / response |
| TC-03 | System-interface | Missing time-range params returns 400 | Response |
| TC-04 | User | Dialog opens, submits, result messaging, refresh | Screenshot |
| TC-05 | User | Copy consistent across the three locales | Screenshot |
| TC-06 | End-to-end | Re-running the same range is idempotent | DB before/after diff |
| TC-07 | Operational | Audit log, changelog | Log / changelog |

---

## Phase 4 — Implement

Execute in plan order; spot-check after each task;
once all tasks are done, run the full test plan and preserve evidence.

---

## Phase 5 — Review

- Can users actually perceive "resend succeeded" vs "resend failed"?
- Do all consumers that read `invoice.status` correctly render `RESENT`?
- Is the source of truth clear (`invoice.status` + batch behavior)?
- Can operators see the audit record?

---

## Phase 6 — Sign-off

- Every acceptance criterion PASSes, evidence attached.
- All four surfaces covered.
- Residual risk: if we later need to support asynchronous batching, it will require a separate refactor ticket.

---

## Phase 7 — Deliver

Completion-report summary:
- Capability: batch-resend invoices.
- Surface coverage: all four surfaces.
- Verification: full TC suite PASSed, evidence preserved.
- Ops: resend comes with log + docs.
- Follow-up: CSV download and async queue can be planned later.

---

## What this example is meant to show

1. Thinking starts from "capability + surface," not "frontend / backend."
2. Every surface is named — no surface is defaulted as someone else's problem.
3. Verification and evidence were designed in the plan phase, not back-filled afterwards.
4. The definition of done is a complete change story, not "code merged."
