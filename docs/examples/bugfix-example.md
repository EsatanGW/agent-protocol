# Worked Example: admin user-list pagination breaks under a specific filter

This is a bug-fix example. It illustrates how to apply the methodology to a situation that "looks like a UI problem but is actually a contract + state alignment problem."
All names, paths, and data structures are fictitious.

---

## Problem description

Customer support reports:
- In the admin console's user list, after applying the "show only disabled accounts" filter,
- page 2 onward is blank,
- but the database confirms the rows actually exist.

---

## Why this case matters

This class of bug is often misdiagnosed as:
- The frontend pagination component is broken.
- The API's pagination is broken.

The real problem is usually one of:
- The request payload's filter isn't carried across page changes.
- The response shape doesn't match the state store's assumptions.
- `count` and `list` derive from different sources of truth.

This is a good illustration of "don't classify by frontend / backend first — look at which surfaces the capability passes through."

---

## Phase 0 — Clarify

### Affected surfaces
- User surface: list, pagination, empty state.
- System-interface surface: pagination contract for `GET /users`.
- Information surface: filter state, page params, total count.
- Operational surface: bug report, verification evidence, regression notes.

### Change boundaries
- Do not rebuild the entire query page.
- Do not change UI layout.
- Only fix the pagination ↔ filter contract-alignment issue.

### Public behavior impact
YES (users see the bug fix).

### Open questions
- ⛔ Does the page-2 request still carry the disabled filter?
- ⚠️ Is the blank state because the list is empty, or because the count is wrong?
- ⚠️ Does every filter have the same problem, or only the `disabled` status?

---

## Phase 1 — Investigate

### Main flow
- Source of truth: URL query / state store — the filter and page params.
- Capability flow: filter state → request payload → API response → state store → table + pagination.

### Impact list
- List page component.
- Filter-form component.
- State store / query hook.
- API-client wrapper.
- `/users` endpoint.
- Pagination total-count composition logic.

### Findings
- Page 1 request correctly carries `status=disabled`.
- Page 2 request loses `status=disabled`.
- UI still shows the disabled filter as applied.
- The API itself has no bug — given a request without the filter, it correctly returns the default dataset.
- On page change, the store only updates `page` — it does not preserve the full filter object.

### Root cause
The true root cause is not the table component. It is that:
- The filter state on the user surface, and
- The request payload on the system-interface surface,
- Lost consistency inside the state store on the information surface.

---

## Phase 2 — Plan

### Change map

| Surface | Main change |
|---------|-------------|
| User | Preserve the existing filter after a page switch. |
| System-interface | The request builder always assembles the payload from the complete query state. |
| Information | The store's page-change handler becomes an immutable merge that does not overwrite the filter. |
| Operational | Add a regression note to the completion report. |

### Tasks
- Task 1: fix the store's page-change behavior.
- Task 2: fix the API request builder so it never emits only the page params.
- Task 3: add a regression test covering page 2 with the filter preserved.
- Task 4: manually verify UI pagination, empty state, and total-count consistency.

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|-----|---------|-----------|----------|
| TC-01 | User | With the disabled filter applied, page 2 still shows data | Screenshot |
| TC-02 | System-interface | Page-2 request retains `status=disabled` | Network capture |
| TC-03 | Information | After a page change, the store retains the original filter object | Test output |
| TC-04 | Regression | Ordinary (no-filter) pagination is unaffected | Screenshot / test output |

---

## Phase 4 — Implement

- Fix the store merge logic.
- Fix the request builder.
- Add the regression test.
- Save screenshot, network payload, and test output as evidence.

---

## Phase 5 — Review

The review checks more than "pagination looks fine now":
- Does the filter the user sees equal the filter actually being queried?
- Is the API request actually correct?
- Do `total count` and `list` derive from the same condition set?

---

## Phase 6 — Sign-off

- Bug fixed and reproducibly verified.
- Regression coverage in place.
- No new empty-state misdiagnosis introduced.

---

## Phase 7 — Deliver

Delivery summary:
- What got fixed is "filter state decoupled from the pagination request."
- This is not just a UI bug.
- Verification evidence includes: UI screenshot, network payload, store/state test.

---

## What this example is meant to show

1. Many bugs have cross-surface desync as the root cause.
2. When the screen goes blank, don't only stare at the UI.
3. Bug-fixes can also be analyzed end-to-end via source of truth / consumers / evidence.
