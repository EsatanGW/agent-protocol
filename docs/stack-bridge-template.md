# Stack Bridge Document Template

> **English TL;DR**
> Template for creating a **stack bridge document** — the *only* place where tool / language / framework names may appear in the plugin. Every team adopting the methodology writes one bridge file mapping the four core surfaces (and any chosen extension surfaces) onto concrete files, tools, and validation commands for their stack. Template sections: (1) declared surfaces (core + extensions with justification), (2) SoT map (pattern → concrete file/table/config), (3) uncontrolled interfaces registry, (4) rollback-mode mapping per surface, (5) build-time risk & codegen artifacts, (6) validation commands, (7) known limitations (what the bridge does *not* yet cover). Canonical examples live under `docs/bridges/` — see `flutter-stack-bridge.md`, `ktor-stack-bridge.md`, `android-kotlin-stack-bridge.md`, `android-compose-stack-bridge.md`, `unity-stack-bridge.md`. Never skip a bridge — running the methodology without one forces every team to re-derive the mapping case-by-case.

> **Purpose:** map the four-surface methodology onto a specific tech stack.
> Each project or stack writes one bridge document explaining what each of the four surfaces corresponds to concretely in that stack.

---

## How to use this template

1. Copy this template into your project (e.g. `docs/stack-bridge.md`).
2. Fill in your stack's information.
3. For each surface, list concrete file paths, tools, and verification methods.
4. If you have domain-specific extension surfaces, declare them in the extensions block.

---

## Template body

```markdown
# [Project Name] Stack Bridge

> Based on: agent-protocol four-surface model
> Stack: [your primary runtime / framework / storage / deployment model]
> Design basis: [if there is a fixed spec (e.g. design-asset dimensions, API contract repo) record it here]

## Surface configuration

Core surfaces (mandatory):
- [x] User surface
- [x] System-interface surface
- [x] Information surface
- [x] Operational surface

Extension surfaces:
- [ ] (Add as dictated by the domain — e.g. asset / experience / performance-budget / data-quality / hardware-interface / model / compliance)

---

## User surface mapping

### Concept mapping
| Concept | Concrete implementation in this project |
|---------|-----------------------------------------|
| route / page | [routing mechanism and file location] |
| component | [component organization and file location] |
| interaction | [interactive component conventions] |
| copy / i18n | [string source and translation mechanism] |
| state management | [state-management approach and location] |
| validation | [the layer where validation happens] |
| a11y | [accessibility / contrast / keyboard-support baseline] |

### Verification methods
- [ ] Static analysis / type checking
- [ ] Unit / component tests
- [ ] Visual comparison (screenshots / recordings / snapshots)
- [ ] Real-device or real-deployment tests

---

## System-interface surface mapping

### Concept mapping
| Concept | Concrete implementation in this project |
|---------|-----------------------------------------|
| API client | [HTTP / RPC client and unified entry/exit points] |
| API contract | [where the contract / schema source of truth lives] |
| event / message | [event / message-queue / real-time mechanism] |
| external integration | [list of third-party integrations and entry points] |

### Verification methods
- [ ] Payload / contract checks
- [ ] Middleware / interceptor behavior checks
- [ ] Mocking / recording of third parties

---

## Information surface mapping

### Concept mapping
| Concept | Concrete implementation in this project |
|---------|-----------------------------------------|
| data model | [how models are defined and where] |
| enum / status | [the source for enum definitions] |
| config | [config source and how it is injected] |
| feature flag | [flag storage and lookup mechanism] |
| code generation | [if codegen is used, command and output location] |

### Verification methods
- [ ] Codegen output is consistent with its source
- [ ] Serialization / deserialization round-trip tests
- [ ] Tolerance of unexpected / null values

---

## Operational surface mapping

### Concept mapping
| Concept | Concrete implementation in this project |
|---------|-----------------------------------------|
| logging | [structured-logging mechanism] |
| crash / error reporting | [crash / exception telemetry mechanism] |
| analytics | [behavior / business analytics mechanism] |
| release / rollout | [phased-release mechanism] |
| rollback | [default rollback mode per surface] |

### Verification methods
- [ ] Health indicators (error rate / crash rate / SLO) are observable
- [ ] Key events can be reconstructed from the record
- [ ] Release information has a written record

---

## Extension surfaces (where applicable)

### [Surface name]

**Scope:**
[List the items this surface covers.]

**Source of Truth:**
[Where the authoritative source for this surface lives.]

**Consumers:**
[Who consumes this surface's data / output.]

**Verification methods:**
- [ ] [Concrete verification steps]

---

## Cross-cutting notes

### Security focus
- [List the security items that matter most in this project.]
- [Example: payment-related pages require additional input validation.]

### Performance focus
- [List the performance budgets or key indicators for this project.]
- [Example: home-page load < 2s; list-scroll maintains 60fps.]

### Error-handling focus
- [Describe the project's error-classification strategy and source of user messages.]
- [Example: all API errors flow through `BaseRes<T>.error_code` + i18n key lookup.]
- [Reference `docs/cross-cutting-concerns.md` error-handling checklist.]

---

## Change lifecycle

### Breaking-change convention
- [The project's definition of a breaking change and the flow that handles it.]
- [Example: API field additions go L0, removals go L3, following the three standard migration paths in `docs/breaking-change-framework.md`.]
- [Example: public SDKs follow semver; L2+ is only permitted on a major-version bump.]

### Rollback capability
- [Default rollback mode for each surface in this project.]
- [Example: web backend = mode 1, mobile client = mode 2, payments = mode 3.]
- [Reference `docs/rollback-asymmetry.md`.]

### Uncontrolled-external-dependency list
- [Third-party SDKs, platforms, policies, and deprecation risks this project depends on.]
- [Example: Stripe SDK vX → vY, Apple ATT policy, Android 14 background-execution limits.]
- [Subscribe to release notes / advisories: name the channel or the responsible person.]

---

## Quick reference

| I want to... | Surfaces involved | Things to check |
|--------------|-------------------|-----------------|
| Add a new page | User + information + operational | route, state, i18n, analytics event |
| Change an API field | System-interface + information + user | contract, model codegen, UI binding |
| Fix a bug | Depends on the bug | Identify source of truth and consumers first |
| Add a new locale | User + operational | translation key, fallback, release notes |
```

---

## Worked examples: how to fill this in

The hints below **do not bind any specific framework** — they describe only what type of mechanism each surface typically lands on within a given domain.
Each domain is annotated with **common gotchas** — the "looks-fine-but-blows-up-later" traps to check off if your stack is in that domain.
Adapt these to your actual stack.

### Rich web / single-page application

| Surface | Typical mechanism |
|---------|-------------------|
| User | Router, component tree, styling system, i18n string management |
| System-interface | HTTP client, real-time communication, external query layer |
| Information | Client-side store, type definitions, runtime config |
| Operational | Error reporting, behavior analytics, release pipeline |

**Common gotchas:**
- [ ] Hydration mismatch (SSR / SSG vs. client render inconsistency) — shows up only in release builds.
- [ ] i18n keys folded into constants by the minifier or missing fallback — users see the raw key.
- [ ] Client-side state doesn't handle cross-tab sync / write races across tabs.
- [ ] Third-party scripts (analytics / chat widget) mutate global state or pollute `prototype`.
- [ ] Service Worker / bfcache keeps users on the old version — issues stop reproducing after release.
- [ ] Bundle-splitting changes route a user to a stale chunk (especially combined with CDN cache).

### Server-side API / backend service

| Surface | Typical mechanism |
|---------|-------------------|
| User | Usually only present in server-rendered or admin UIs |
| System-interface | Routing / middleware / contract spec |
| Information | Data-layer schema, migrations, runtime config, flag system |
| Operational | Structured logs, APM, health checks, deploy scripts |

**Common gotchas:**
- [ ] Migration and deploy ordered backwards (new binaries ship before migration runs) — momentary 500s.
- [ ] Connection pool / transaction leaks under long-running requests.
- [ ] Timezone / timestamp precision mismatch between DB, application layer, and client.
- [ ] Rate-limit granularity unclear (per-user / per-IP / per-token) — a single user can saturate under DDoS.
- [ ] Local dev uses SQLite / in-memory store while prod is Postgres — semantic differences (collation, isolation) slip past.
- [ ] Cron / background-worker timezone differs from host timezone — schedule drifts.

### Long-lifecycle clients (mobile / desktop / embedded)

| Surface | Typical mechanism |
|---------|-------------------|
| User | Screen tree, navigation, i18n, responsive layout |
| System-interface | HTTP client, push notifications, deep links, OS-native bridges |
| Information | Local storage, user preferences, model codegen, offline sync strategy |
| Operational | Crash reporting, analytics, app-store release or OTA updates |

**Common gotchas:**
- [ ] Users linger on old versions, so the server must support multiple client versions concurrently (maps to `rollback-asymmetry.md` mode 3).
- [ ] Release builds go through AOT / minifier / R8 / ProGuard and break reflection / JSON / dynamic class registration (maps to `cross-cutting-concerns.md` build-time risk).
- [ ] Migration: the local-DB schema upgrade strategy doesn't handle users arriving from three versions back.
- [ ] Push token / device ID handling after reinstall, device swap, or iCloud restore.
- [ ] OS upgrades change background / network / permission policies (maps to uncontrolled interfaces).
- [ ] Deep links / universal links don't handle the app-not-installed / not-signed-in / multi-tab cases.

### Real-time interactive runtimes (games / 3D / AR)

| Surface | Typical mechanism |
|---------|-------------------|
| User + experience | Scene, UI canvas, physics / animation / audio feedback (experience verification: see `docs/playtest-discipline.md`) |
| System-interface | Server API, multiplayer protocol, platform SDK |
| Information + asset | Save data, asset bundles, prefab / scene definitions |
| Operational + performance budget | Analytics, crashes, live-ops, draw-call / memory budgets |

**Common gotchas:**
- [ ] "Editor runs" ≠ "target device runs" (IL2CPP / AOT / shader-variant differences — maps to `cross-cutting-concerns.md` build-time risk and SoT pattern 8).
- [ ] Prefab / scene YAML merge conflicts go undetected; references point to deleted objects.
- [ ] Live-ops config hot-reloads cannot be rolled back (players have already claimed rewards — maps to `rollback-asymmetry.md` mode 3).
- [ ] Frame rate untested on low-end devices — experience playtest only runs on high-end.
- [ ] Localized strings overflow / break UI in certain languages.
- [ ] Asset-bundle hash / version out of sync with binary version — assets fail to load post-update.

### Data / analytics platform

| Surface | Typical mechanism |
|---------|-------------------|
| User | Only present if there's a BI / dashboard |
| System-interface | Ingest interface (API / pub-sub), downstream export, schema registry |
| Information + data quality | Table schemas, lineage, freshness, quality monitoring |
| Operational | Job scheduling, failure alerts, lineage docs |

**Common gotchas:**
- [ ] Upstream schema changes without notifying downstream — the pipeline silently produces bad data (NULLs, shifted columns).
- [ ] Reruns / backfills aren't idempotent — duplicates or gaps appear.
- [ ] Late-arriving events don't land in the right partition / aren't recomputed downstream.
- [ ] Timezone / DST makes a daily report miss or duplicate an hour.
- [ ] Dashboards / downstream consumers read raw tables directly — raw-schema changes break dashboards.
- [ ] PII leaks into places it shouldn't (analytics table / backup / BI) — compliance issue discovered after the fact.

### AI / ML systems

| Surface | Typical mechanism |
|---------|-------------------|
| User | Only present if there's an interactive surface (chat / agent / prediction UI) |
| System-interface | Inference API, prompt / tool contracts, upstream model provider |
| Information + model | Model version, weights, datasets, prompts, eval results |
| Operational | Inference cost / latency monitoring, safety-guardrail alerts, rollback strategy |

**Common gotchas:**
- [ ] Prompt or model version isn't version-controlled alongside code / data schema — past outputs cannot be reproduced.
- [ ] Upstream provider silently swaps model versions (maps to uncontrolled interfaces) — behavior drift goes undetected.
- [ ] Eval set and training set have leakage — offline metrics look great, production collapses.
- [ ] Guardrails are only tested on the happy path — adversarial input / multi-language / long-context untested.
- [ ] Cost / latency scales non-linearly at 2× traffic (context window fills up, batch efficiency drops).
- [ ] Fine-tune / RAG index is a dual representation (maps to SoT pattern 8) — index is not rebuilt after data changes.

---

## Reference fill: generic Web CRUD service

> This is an **illustrative** completed example to help teams gauge granularity.
> It binds no specific framework. Adapt to your own stack — don't copy-paste directly.

```markdown
# Example CRUD Service Stack Bridge

> Based on: agent-protocol four-surface model
> Stack: Server-rendered web app + REST API + relational DB
> Service type: Back-office admin system

## Surface configuration
Core surfaces: all enabled
Extension surfaces: none

---

## User surface

| Concept | Implementation | File location |
|---------|---------------|---------------|
| route | HTTP-router definitions | `routes/*` |
| view / template | Server-rendered template | `views/*` |
| component | Shared partials | `views/components/*` |
| i18n | Key-value translation files | `locales/*.json` |
| validation | Form-validation rules | `validators/*` |
| a11y | WCAG 2.1 AA | Semantic HTML + aria-* |

Verification methods:
- Static analysis: lint, type check
- E2E: smoke tests cover login + CRUD happy path
- Screenshot diff: visual regression on key pages
- Manual check: every action reachable via keyboard

---

## System-interface surface

| Concept | Implementation |
|---------|---------------|
| public API | REST under `/api/v1/*` |
| API contract | OpenAPI spec (SoT: `api-spec/openapi.yaml`) |
| webhook | External callbacks under `/webhooks/*` |
| job | Background-queue workers |
| internal RPC | None (monolith) |

Verification methods:
- Contract tests: OpenAPI schema validator
- API response-shape checks
- Webhook-retry idempotency tests

---

## Information surface

| Concept | Implementation | SoT location |
|---------|---------------|--------------|
| DB schema | SQL migrations | `migrations/*.sql` |
| enum / status | DB constraint + program constants | migrations + `constants/status.*` |
| config | Environment variables | `.env.example` (as the doc SoT) |
| feature flag | DB-backed flag table | `flags` table |
| contract | OpenAPI + DB schema | See above |

Verification methods:
- Migrations go through a dry-run on staging
- Enum values checked bidirectionally (DB ↔ code)
- JSON round-trip tests

---

## Operational surface

| Concept | Implementation |
|---------|---------------|
| logs | Structured JSON log via a unified logger |
| audit | Sensitive operations written to `audit_log` table |
| telemetry | Metrics endpoint + APM |
| docs | `docs/` + OpenAPI auto-generation |
| migration / rollout | Phased release + feature flag |
| rollback | Every DB migration ships with a down script |

Verification methods:
- Log-structure schema validation
- Rollback verified runnable before release
- New metrics confirmed to emit data on the dashboard

---

## Cross-cutting

### Security
- All `/api/*` passes through the auth middleware
- User input passes through validator allow-lists
- Secrets never enter logs

### Performance
- Key API p95 < 300ms
- DB queries per request < 10

### Observability
- Every HTTP handler has a request ID
- Error rate > 1% triggers an alert

### Testability
- Every feature flag has both on and off test scenarios

---

## Quick reference

| I want to... | Surfaces | Must check |
|--------------|----------|------------|
| Add an API field | System-interface + information + user | OpenAPI, migration, UI binding, older-client compatibility |
| Change an enum | Information + system-interface + user | DB constraint, API contract, UI menu, i18n |
| Add an admin page | User + information + operational | route, permissions, audit log, analytics |
| Change password rules | Information + user + operational | validator, UI copy, migration plan for existing accounts |
```

---

## Filling-in guidance

1. **Fill the table cells first; come back to the verification methods** — leave unknown implementations blank rather than guess.
2. **Mark only the SoT, not every location** — if an enum is defined in three places, "which one is the SoT" matters more than listing the three.
3. **The quick-reference table is a living document** — add a row each time a new kind of change appears; this is the highest-value output.
4. **Don't treat the template as a checklist** — the template is a map; every team will use only part of it.
