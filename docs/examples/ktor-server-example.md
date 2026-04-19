# Worked Example: Add a "paused" state to the order lifecycle in a Ktor server

> This example fleshes out the outline in `docs/bridges/ktor-stack-bridge.md` §Reference worked example outline.
> It exercises the three Ktor patterns the bridge calls out as load-bearing:
>
> - **Enum + transition-defined truth must stay in sync across the code state machine and the DB CHECK constraint** (SoT patterns 3 + 6, dual-representation between migration and domain model).
> - **Plugin install order is a contract** (`CallLogging` before `Authentication`, rate-limit before business handlers — SoT pattern 4a).
> - **Server-side rollback is one of the few places where mode 1 is realistic.** But the DB migration inside the same change is still mode 2 — within a single feature you ship two rollback modes.
>
> All names, paths, and data structures are fictitious.

---

## Requirement

The system currently models an `Order` with states `NEW`, `PAID`, `SHIPPED`, `DELIVERED`, `CANCELLED`.

Product asks:

> "Add a `PAUSED` state for orders the operator has put on hold (e.g. fraud review). A paused order cannot be shipped or cancelled directly — it must be resumed first. Resuming returns to the state it was paused from."

Constraints:

- Existing consumers (admin UI, warehouse webhook, analytics export) must not break when they see `PAUSED`.
- Migration must be forward-only; no destructive down-migration.
- `PAUSED → SHIPPED` and `PAUSED → CANCELLED` are forbidden transitions — server must reject with 409.

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces:
- [x] User — (limited) admin UI shows the new chip; actual UI work is a downstream ticket on the admin frontend team.
- [x] System-interface — `GET /orders/:id` response includes `PAUSED`; new `POST /orders/:id/pause` and `POST /orders/:id/resume` endpoints; `POST /orders/:id/cancel` and `/ship` now reject when state is `PAUSED`.
- [x] Information — enum `OrderStatus` adds `PAUSED`; migration adds `PAUSED` to the DB `CHECK (status IN ...)` constraint; new column `paused_from_status` nullable for round-trip on resume.
- [x] Operational — metrics gain per-state counters; structured log per transition; OpenAPI spec regenerated.

Extension surfaces:
- [x] Uncontrollable external — the warehouse provider's webhook consumer (they own the code; we own the contract). They have explicitly stated they do an exhaustive switch on `status` — adding a new enum value is an L1+ break for them unless we negotiate a grace window.

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| System-interface | Two new endpoints, two modified ones (409 for forbidden transitions), OpenAPI regen. |
| Information | Enum + migration + new column; state-machine guard function. |
| Operational | Three new metric labels; structured log transition events; migration runbook. |
| Uncontrollable external | Warehouse webhook contract; consumer-notification timeline. |

### Change boundaries

- Do **not** repurpose an existing status for "paused" — introduce a new one.
- Do **not** drop the old CHECK constraint; add the new value via `ALTER TYPE` / `ALTER CHECK` forward-only.
- Do **not** auto-resume on any path — resume must be explicit.

### Public behavior impact

YES — new status value in API responses; L1+ for exhaustive-switch consumers.

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|---|---|---|---|---|
| Legal order states | DB CHECK constraint (migration file) | Code enum, API response, webhook payload, analytics export | Manual: migration + enum update together | **High** — they are two representations; only a drift test catches mismatch |
| Legal transitions | Kotlin `sealed class` with guard function in `OrderStateMachine.kt` | All state-mutating endpoints | Single function called by every mutator | Medium — easy to bypass if a handler updates state directly via DAO |
| API contract | `openapi.yaml` | Client codegen, consumer tests, warehouse integration | Regenerated via `./gradlew verifyOpenApi` | Medium — hand-editing the YAML vs. regenerating drifts quickly |
| Plugin install order | `Application.module()` in `src/main/kotlin/Application.kt` | Runtime pipeline | Implicit — whoever edits last wins | **High** — swapping `CallLogging` and `Authentication` changes log-vs-auth semantics silently |

### Risks identified

1. **Dual-representation enum drift.** Adding `PAUSED` to the Kotlin enum without updating the DB CHECK is caught only when the first `INSERT` fails in production.
2. **Exhaustive-`when` failure in downstream consumers.** The warehouse team does `when (status) { ... }` — adding a value without telling them + version-negotiating breaks their runtime.
3. **Pipeline-order violation.** A new rate-limit plugin added for the pause endpoint must go **after** `CallLogging` (so rejected requests are logged) but **before** `Authentication` (so unauthenticated floods are cheap). Misplacing it is silent misbehavior.
4. **Round-trip on resume.** If we don't persist the prior state, "resume" has no destination; the current design adds `paused_from_status` as the simplest answer.

---

## Phase 2 — Plan

### Change plan (in dependency order)

1. **Information (migration):** Flyway script `V21__add_paused_order_status.sql`:
   - `ALTER TYPE order_status ADD VALUE 'PAUSED';` (Postgres path) or the CHECK-constraint equivalent on MySQL.
   - `ALTER TABLE orders ADD COLUMN paused_from_status order_status NULL;`
   - Forward-only. No down script.
2. **Information (enum + state machine):** add `PAUSED` to `OrderStatus`; update `OrderStateMachine.canTransition(from, to)` to encode the new transitions and forbidden pairs; `when` over `OrderStatus` is exhaustive — compiler enforces every consumer in-tree updates.
3. **System-interface:** add `pauseOrder`/`resumeOrder` handlers; modify cancel/ship to consult state machine first and return 409 with `{ error: "illegal_transition", from, to }` on forbidden attempts.
4. **Operational:** add metric labels `order.state.transitioned{from,to}`; every transition goes through the state-machine function which logs structured event `order_state_transition`.
5. **System-interface (contract):** regenerate `openapi.yaml`; run `./gradlew verifyOpenApi` to catch drift.
6. **Uncontrolled external (warehouse coordination):**
   - Notify warehouse team with a two-week lead time before enabling the endpoint in production.
   - Add a temporary response-shaping flag: until warehouse confirms their build is updated, `/webhooks/warehouse` filters out `PAUSED` orders from their payload (they only see a paused order once it returns to `PAID` or `CANCELLED`).
   - Record the flag and its sunset date in the uncontrolled-external register.
7. **Plugin install order audit:** if a new rate-limit plugin is introduced for pause/resume, confirm its install position in `Application.module()` and add a comment block declaring the reason.

### Cross-cutting

- **Rollback modes per layer:**
  - Stateless handler change (behind blue/green) = **mode 1**.
  - `V21__` migration = **mode 2** forward-fix (PostgreSQL `ALTER TYPE ADD VALUE` is irreversible).
  - Webhook-shape change already delivered = **mode 3** (we cannot un-send a payload; compensation is a follow-up cleanup endpoint).
- **Security:** `pauseOrder`/`resumeOrder` are admin operations — require the `order:pause` scope in the JWT claim; not reachable from the public API.
- **Performance:** transition count is small; no index changes needed.
- **Supply chain:** no new dependencies.

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|---|---|---|---|
| TC-01 | Information | `V21__add_paused_order_status.sql` applied on a production-like snapshot produces the expected CHECK constraint and column | `pg_dump --schema-only` diff |
| TC-02 | Information | Legal transitions pass, illegal return 409 `illegal_transition` | Integration test output |
| TC-03 | System-interface | `POST /orders/:id/pause` stores `paused_from_status` correctly | DB before/after |
| TC-04 | System-interface | `POST /orders/:id/resume` restores to `paused_from_status`, clears the column | DB before/after |
| TC-05 | System-interface | OpenAPI spec regen produces no diff in CI after handler change | `./gradlew verifyOpenApi` log |
| TC-06 | Operational | Metric label `order.state.transitioned{from=PAID,to=PAUSED}` increments on each pause | Prometheus scrape output |
| TC-07 | Operational | Structured log has one `order_state_transition` event per transition, including the correlation ID | Log snippet |
| TC-08 | Uncontrolled external | Warehouse webhook filter excludes `PAUSED` orders while the flag is on | Webhook payload capture |
| TC-09 | Regression | Cancel / ship on a non-paused order works exactly as before | Existing integration suite re-run |
| TC-10 | Pipeline-order | Unauthenticated request to `/pause` is rejected at `Authentication` but `CallLogging` has already emitted an access-log line | Log + HTTP response |

---

## Phase 4 — Implement

Execute in plan order. Gates:

- After task 1 (migration): run `./gradlew flywayMigrate && ./gradlew dumpSchema && git diff --exit-code db/schema.sql`. Any difference beyond the expected one is drift.
- After task 2 (enum): compile the project — the `when` over `OrderStatus` is exhaustive, so the compiler lists every in-tree consumer that must be updated.
- After task 5 (OpenAPI): run `./gradlew verifyOpenApi` and commit the regenerated spec together.

---

## Phase 5 — Review

Review checks beyond "tests are green":

- Does **every** mutator endpoint go through `OrderStateMachine.transition(from, to)`, or are any DAO calls bypassing it? A grep for `status = OrderStatus\.` in non-test code should yield **one** call site (the state-machine function itself).
- Is the DB CHECK constraint on `status` now aligned with the Kotlin enum? Run the drift test that casts all enum values against the CHECK constraint in a live test DB.
- Does the plugin install order in `Application.module()` still honor the documented ordering? Diff the pipeline-order comment block.
- Has the warehouse-webhook filter been added to the uncontrolled-external register with an explicit sunset date (not "TBD")?
- Is rollback classified correctly per layer? A single "rollback plan: mode 1" on the whole change is wrong — the migration is mode 2.

---

## Phase 6 — Sign-off

- All TCs pass; TC-08 specifically with the warehouse team's staging endpoint.
- Uncontrolled-external register has the webhook-filter row with sunset date `+14 days`.
- OpenAPI spec regenerated and committed; consumer SDKs will pick up the new value.
- Migration run on staging first, then production blue, then production green; rollback plan per layer documented.
- Pipeline-order comment block updated and reviewed.

---

## Phase 7 — Deliver

Completion-report summary:

- Capability: orders can be paused and resumed; illegal transitions return 409 with a machine-readable error code.
- Surface coverage: system-interface primary; information + operational supporting; uncontrolled-external (warehouse) tracked with an explicit compatibility window.
- Verification: TC-01..10 passed with evidence.
- Rollback plan per layer:
  - Stateless code path → mode 1 (blue/green revert).
  - `V21__` migration → mode 2 (forward-fix only).
  - Already-sent webhook payloads during flag-on window → mode 3 (compensation via a cleanup endpoint if needed).
- Observation window: 7 days — watch illegal-transition 409 rate (should be near-zero after warehouse upgrade) and pause/resume volume.

Follow-ups (recorded):

- Remove the warehouse-webhook filter after the sunset date confirms their build is live.
- Add a Grafana panel for the new metric labels (frontend team's board, not this change's scope).

---

## What this example is meant to show

1. **One feature, three rollback modes.** Code is mode 1, migration is mode 2, already-sent webhook payloads are mode 3. Writing "rollback: mode 1" for the whole change is a category error.
2. **Enum + CHECK is a dual-representation SoT.** The drift is only caught by a test that asserts the DB constraint and the Kotlin enum match.
3. **Exhaustive `when` is a gift — outside your repo, it is a contract.** Downstream consumers with their own exhaustive switch are affected by L1+ changes. Coordinate with a written compatibility window, not hope.
4. **Plugin install order is not a convention; it is a contract.** `CallLogging` before `Authentication` is one example; adding a rate-limit plugin requires an explicit placement decision with a justification comment.
