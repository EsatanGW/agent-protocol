# Ktor Server Stack Bridge

> Maps the tool-agnostic methodology to a Kotlin + Ktor server application. Bridges are the only layer allowed to name specific tools.

---

## Scope

**Applies to:** Kotlin server applications built on Ktor, using coroutines for concurrency, Gradle (Kotlin DSL), a typed DB access layer (Exposed / jOOQ / Ktorm or plain JDBC), and a migration tool (Flyway or Liquibase).
**Runtime neutral:** containerized or JAR, any JVM-based deployment target.

---

## Surface mapping

### User surface (limited — server is backend)

| Concept | Concrete implementation |
|---|---|
| route / endpoint | `routing { get("/...") { } }` |
| error page / response | `StatusPages` plugin configuration |
| **Note** | Server has *no user surface* in the classic sense, but produces responses that are consumed by a UI. Mark these as system interface surface primary, user surface consumer. |

### System interface surface

| Concept | Concrete implementation |
|---|---|
| REST endpoints | `Route` handlers + `ContentNegotiation` (Jackson / Kotlinx) |
| gRPC | via `grpc-kotlin` if used |
| Event publishing | Outbox pattern + broker client (Kafka / NATS / RabbitMQ) |
| Background jobs | Coroutine-based scheduler or external (Quartz, Temporal) |
| External clients | `HttpClient` with engine (CIO / OkHttp / Apache) and interceptor plugins |
| Auth | `Authentication` plugin (JWT / OAuth / session) |

**Uncontrolled-interface register:**
- Kotlin compiler / Ktor / coroutines version transitions
- JDK version (LTS vs non-LTS)
- Upstream SDKs for payment, cloud, identity providers
- Container base image OS vulnerabilities

### Information surface

| Concept | Concrete implementation |
|---|---|
| DB schema | Migration files (Flyway `V__.sql` / Liquibase changelog) |
| Domain model | `data class` + sealed hierarchies |
| DTO (external) | Separate `data class` with serialization annotations — not the domain type |
| Config | `application.conf` (HOCON) or env vars via `ApplicationConfig` |
| Feature flags | Remote config + env override |
| Cache | Redis / in-memory with `Caffeine` |

### Operational surface

| Concept | Concrete implementation |
|---|---|
| Structured logs | SLF4J + Logback JSON encoder, correlation ID via `CallId` plugin |
| Metrics | Micrometer + `MicrometerMetrics` plugin |
| Tracing | OpenTelemetry via Ktor plugin |
| Health checks | `/health` + `/ready` endpoints |
| Deployment | Container image + orchestration (K8s / Nomad / etc.) |
| Migration execution | Run-once on deploy or sidecar |

---

## SoT pattern bindings

| Pattern | Ktor instance |
|---|---|
| 1 Schema-Defined | DB schema in migration files; DTO shape in serializers |
| 2 Config-Defined | `application.conf`, env vars, flag service |
| 3 Enum/Status | `enum class` / `sealed class` — exhaustive `when` required |
| 4 Contract-Defined | OpenAPI spec (hand-written or generated), API version in path |
| **4a Pipeline-Order** | **Ktor plugin install order in `Application.module()`** — this is a canonical case of implicit order contract. Explicit comments recommended. |
| | Example: `install(CallLogging)` MUST come before `install(Authentication)` if you want to log auth failures; the reverse gives you unauthorized requests in clear text in logs (security anti-pattern). |
| 6 Transition-Defined | State machines as `sealed class` + guard functions |
| 7 Temporal-Local | Outbox table + background publisher (not standard but a common pattern) |
| 8 Dual-Representation | Migration files ↔ live DB schema; Kotlinx serializer annotations ↔ JSON on the wire |
| supply-chain (extension) | `gradle/libs.versions.toml` + lock files; container base image tag in Dockerfile |

---

## Rollback mode defaults

| Layer | Default mode |
|---|---|
| Stateless handler change behind blue/green | Mode 1 — canonical reversible rollback case |
| DB migration | Mode 2 forward-fix — write **forward-only** migrations; any "down" migration is a new forward migration |
| Outbox-published event | Mode 3 compensation — already-published cannot be retracted |
| Sent notification / webhook | Mode 3 compensation |
| Running long-lived consumer (e.g., Kafka consumer group) | Mode 2 — may need schema compatibility window |

Server is the one stack where **mode 1 is realistic**. Use it when possible.

---

## Cross-cutting concerns bindings

- **Security:**
  - Authentication plugin mandatory on every non-public route (audit via integration test that checks a baseline set of routes respond 401 without credentials)
  - Rate limiting via plugin or reverse proxy
  - Parameterized queries only (framework enforces but custom SQL must be reviewed)
  - Secrets from env / secret manager; never in `application.conf` committed to repo
  - Input validation at route boundary (reject unknown fields unless explicitly additive)
  - CORS policy explicit, not wildcard in production
  - Webhook signature verification
- **Supply chain:** dependency scan runs on every PR and nightly on base image
- **Performance:** endpoint SLAs tracked, N+1 detection via query profiling, index review on every schema change
- **Observability:** every request has correlation ID; structured logs include endpoint, status, latency, user ID (hashed if PII)
- **Testability:** pure domain functions; `Application.testApplication { }` for integration; testcontainers for DB
- **Error handling:** asymmetric-responsibility — internal exceptions → domain `Result` → `StatusPages` maps to safe HTTP responses
- **Coroutine hygiene:** structured concurrency — every launched coroutine has a defined scope; avoid `GlobalScope`; `CoroutineExceptionHandler` for background work

---

## Automation-contract implementation

### Layer 1

```bash
./gradlew verifyChangeManifests
# or directly with a schema validator:
ajv validate -s schemas/change-manifest.schema.yaml -d "manifests/**/*.yaml" --strict=true
```

### Layer 2 — Cross-reference consistency

Ktor-specific drift checks:

1. **Migration drift:** running migrations on a clean DB must produce a schema identical to a dumped snapshot in `db/schema.sql`.
   ```bash
   ./gradlew flywayMigrate && ./gradlew dumpSchema
   git diff --exit-code db/schema.sql
   ```
2. **OpenAPI drift:** routes defined in code vs spec file — fail if mismatch.
   ```bash
   ./gradlew verifyOpenApi
   ```
3. **Plugin install order audit:** a simple static rule — e.g. `CallLogging` must appear before `Authentication`; enforced via a script that parses `Application.module()`.
4. **Env var reference check:** every `ApplicationConfig.property("x.y")` referenced in code must have a default in `application.conf` or be documented as required.
5. **Dependency lock drift:** gradle lock files and version catalog must be in sync.

### Layer 3 — Drift detection

Weekly on `main`:
- Unused routes (defined but no handler body or commented out)
- Deprecated Ktor / coroutines APIs
- Outbox entries older than threshold (indicates publisher stuck)
- Phase 8 observation overdue for schema migrations

---

## Multi-agent handoff conventions

- `manifests/<change_id>.yaml` with `phase: plan` first
- Commit trailer: `Change-Id: <change_id>`
- Implementer ensures `./gradlew test integrationTest` passes; evidence: test report HTML archived
- Reviewer checks staging env evidence (log snippet + metrics screenshot + migration verification)

---

## Typical workflow per task type

| Task | Mode | Minimum artifacts |
|---|---|---|
| Add optional query parameter | Lean | manifest + contract test |
| Add required field to response | Full (L2) | manifest + consumer migration path + dual-write window |
| New endpoint | Lean → Full if external | manifest + auth review + rate-limit rule |
| Schema migration (additive) | Full | migration + rollback mode 2 note + consumer sync plan |
| Schema migration (drop column) | Full (L3) | deprecation plan + consumer registry check + hard cutoff |
| Ktor version upgrade | Full | uncontrolled_interfaces update + plugin install order re-audit |
| Base image upgrade | Full | supply-chain scan delta + OS vuln diff |

---

## Reference worked example

See `docs/examples/ktor-server-example.md` — "Add a 'paused' state to the order lifecycle." Exercises:

- System interface surface: two new endpoints, two modified ones (409 `illegal_transition`), OpenAPI regen
- Information surface: Flyway migration adds enum value + `paused_from_status` column; forward-only
- Operational surface: per-transition metrics, structured log event, warehouse webhook compatibility window
- Uncontrolled-external: downstream webhook consumer with an exhaustive switch — L1+ unless we ship a shaping flag
- SoT: state machine in code (pattern 6 transition-defined) + DB CHECK constraint (pattern 1 schema-defined) — both must stay in sync (pattern 8 dual-representation)
- Plugin install order: `CallLogging` before `Authentication`; a new rate-limit plugin requires an explicit placement decision (pattern 4a)
- Rollback: handler code = mode 1 (blue/green); migration = mode 2 (forward-fix); already-sent webhook payloads = mode 3 (compensation) — one feature, three rollback modes

---

## Observability depth discipline

The Operational surface table above lists tool *categories*; production-grade Ktor deployments need a concrete contract for what flows through them. Treat observability output as a first-class contract surface (pattern 4) — consumers downstream (dashboards, alert rules, SLO calculators, on-call runbooks) depend on field names and cardinality staying stable.

### Three telemetry tracks, three SoT treatments

| Track | SoT pattern | Breaking-change risk |
|---|---|---|
| Structured logs (JSON) | Pattern 4 (Contract-Defined) — field names form an implicit schema for log-processing pipelines | Renaming `user_id` → `userId` breaks every Grafana / Splunk / Datadog saved query. L2 minimum. |
| Metrics (Micrometer) | Pattern 4 + Pattern 3 (Enum-Defined) — metric names + tag keys are enums consumed by alert rules | Changing a metric name or dropping a tag retires every dashboard panel / alert rule that references it. L3 by default. |
| Traces (OpenTelemetry) | Pattern 4 + Pattern 4a (Pipeline-Order) — span attribute conventions and parent/child order encode the request model | Reparenting spans or dropping attributes breaks trace-based SLO / service-map tooling. L2 minimum. |

### Required log / metric / trace fields

A minimum baseline to make logs and metrics joinable across services:

- `trace_id` + `span_id` — from OTel context; injected into every log event via MDC (`CallId` plugin or a custom coroutine context element that survives `withContext` hops).
- `tenant_id` — if multi-tenant (see overlay below); missing tenant scoping on a metric is a cardinality / isolation bug, not just a logging gap.
- `endpoint` / `route_template` — NOT the raw URI (cardinality explosion) but the `routing { get("/...") }` template string.
- `status_class` as a bucketed tag (`2xx` / `4xx` / `5xx`) alongside exact `status` in logs — metrics tag on the bucket, logs keep the exact code.

### Coroutine context propagation is part of the SoT

`trace_id` lives in the coroutine context, not thread-local storage. Every `launch` / `async` / `withContext` call that crosses a dispatcher must either use `Dispatchers.IO + MDCContext()` or explicitly pre-capture the MDC fields. A launched coroutine that loses the trace ID is observability drift — flag in review.

### PII / hashing discipline

- User identifiers in logs: one-way hashed with a rotating salt unless the specific log event has a *legal* (not just debugging) basis for raw PII.
- Request/response body logging is OFF by default; enabling it on any route requires a `privacy_scope` review checkbox.
- Error messages from upstream SDKs often embed tokens / credit card fragments / emails — sanitize at the `StatusPages` boundary, not downstream in the log pipeline.

### Observability-as-contract drift checks

- [ ] Alert rule file (`*.yaml` for Prometheus / Grafana) version-controlled in the repo; adding a metric without adding an alert or dashboard entry flags a review comment (not a block, but a hygiene reminder).
- [ ] Log-schema snapshot test — a set of golden log events is asserted against a schema (field names + types); renaming a field breaks the test.
- [ ] Cardinality budget per metric — tags × expected distinct values; exceeding budget fails CI (prevents tag-as-ID anti-pattern).

---

## Multi-tenant / sharding overlay

Ktor itself is tenant-agnostic; production multi-tenant services add a tenancy dimension that cuts across every surface. Teams running single-tenant can skip this section.

### Tenant scoping as a cross-cutting SoT

Tenancy is simultaneously:

- **Pattern 4 (Contract-Defined)** — `X-Tenant-ID` header or subdomain in the request contract
- **Pattern 2 (Config-Defined)** — tenant-specific config (feature flags, rate limits, auth providers) resolved from a tenant registry
- **Pattern 1 (Schema-Defined)** — tenant_id column on every tenant-owned table, or schema-per-tenant, or database-per-tenant

| Isolation model | DB layout | Migration impact | Rollback asymmetry |
|---|---|---|---|
| Row-level (`tenant_id` column) | One schema, `tenant_id` on every table + RLS or app-layer filter | One migration hits all tenants simultaneously — L2+ migrations are synchronous across tenants | Mode 2 forward-fix; staged rollout requires feature flag, not tenancy boundary |
| Schema-per-tenant | One DB, N schemas | Migration must iterate N schemas; partial-apply mid-migration = split state | Per-schema rollback is a per-tenant operation — fan-out coordination cost |
| DB-per-tenant | N databases | Migration is N independent operations; can be phased | Per-tenant mode 1 possible — but N times the operational overhead |

### Tenant-aware request pipeline

Tenant resolution placement is Pattern 4a (Pipeline-Order). The correct order depends on the tenancy model:

**Default: single auth provider for all tenants**

```
CallLogging → Authentication → TenantResolution → RateLimit(tenant-scoped) → route handler
```

- TenantResolution before Authentication → unauthenticated requests resolve a tenant (noise in telemetry, potential tenant enumeration attack)
- RateLimit before TenantResolution → one tenant's bursts throttle another

**Variant: per-tenant auth provider (Keycloak realm-per-tenant, Auth0 organization-per-tenant, per-tenant OIDC issuer, regulated-market B2B)**

```
CallLogging → TenantResolution → Authentication(tenant-scoped provider) → RateLimit → route handler
```

- Tenant must resolve first to select which auth realm / issuer / JWKS to validate against
- Unauthenticated-tenant-enumeration risk is mitigated by (a) tenant resolver returning opaque tenant IDs, (b) rate-limiting the pre-auth tenant-resolution endpoint separately

**Rule of thumb:** if any `install(Authentication)` configuration varies per tenant, you are in the Variant case. If one auth config serves all tenants, you are in the Default case. Misordering within your chosen model is L1+ behavioral; switching between models is an architectural change requiring an explicit manifest decision.

### Cross-tenant drift is a unique failure mode

Multi-tenant systems must treat **divergence across tenants** as drift:

- Config values that have drifted per tenant — document which are intentionally tenant-specific vs. accidentally divergent.
- Schema state when using schema-per-tenant — a tenant left behind on migration N-1 is silent drift.
- Feature flags — per-tenant overrides that outlive their reason for existence.

Phase 8 observation MUST check cross-tenant consistency for any multi-tenant change, not just aggregate metrics.

### Sharding addendum

If the tenant dimension maps to DB shards:

- Shard routing key (usually `tenant_id`) is Pattern 4a — ordering / hashing function change is L3 (cannot re-route live data without a backfill).
- Cross-shard queries are an anti-pattern to audit explicitly (every one is a distributed transaction risk).
- Schema migrations on a sharded cluster: the migration tool's notion of "applied" must be shard-aware, not just DB-aware.

---

## gRPC parallel IDL overlay

When a Ktor service exposes both HTTP+OpenAPI and gRPC+protobuf, both IDLs are parallel SoTs — neither is canonical over the other by default.

### Parallel-IDL SoT discipline

- Domain model stays Kotlin `data class` / `sealed class` — **not** the HTTP DTO, **not** the protobuf generated type. Both IDLs serialize **to/from** the domain.
- A feature added to one IDL without the other is a **contract-surface gap**, not a missing feature — write it down as an explicit asymmetry (e.g., "streaming endpoint only on gRPC" is a design choice that must be declared).
- Generated code (from proto compiler and from OpenAPI generator, if any) is **build-time output**, not source of truth — should not be committed unless there's a pinning reason; if committed, a regeneration check runs in CI (Pattern 8 dual-representation).

### Breaking-change severity for gRPC

Protobuf has its own L0–L4 interpretation:

| Change | Severity |
|---|---|
| Adding a new field with a new tag number | L0 (wire-compatible) |
| Reserving or removing a field tag | L3 (clients using the tag break) |
| Changing a field type while keeping the tag | L4 (semantic-reversal — silent wire-level misinterpretation) |
| Renaming a field (same tag, same type) | L1 at the proto level (wire-compatible) but L2 for generated code consumers |
| Changing a service method signature | L3 minimum |

Protobuf wire-compatibility rules do **not** imply safety at the generated-code layer — always check both.

### gRPC-specific manifest requirements

- `system_interface.sot_map` must declare both IDLs with their independent file paths
- `breaking_change.affected_consumers` separates "HTTP clients" from "gRPC clients" — they ship on different cadences (e.g., mobile app vs. internal service)
- `breaking_change.migration_path` for any protobuf-breaking change: `parallel_switch` with a new proto package / service name — never in-place

### Pipeline-order for gRPC interceptors

gRPC interceptor order is the gRPC analog of Ktor plugin install order — explicit ordering comments required; swap test in CI if feasible.

---

## GraphQL parallel IDL overlay

When a Ktor service exposes GraphQL alongside (or instead of) REST + OpenAPI, the GraphQL SDL becomes another parallel SoT. The structural treatment mirrors the gRPC overlay — two IDLs, neither canonical over the other — but GraphQL introduces N+1 query risk, schema federation, and long-lived subscription connections that need their own discipline.

### Parallel-IDL SoT discipline

- GraphQL SDL (`*.graphqls` or code-first via `graphql-kotlin` / `expediagroup-graphql`) is Pattern 4 (Contract-Defined). Domain types serialize to/from it — **not** the other way around.
- Resolvers are adapter-layer code — they map a GraphQL field to a domain operation. A resolver that contains business logic is drift (same rule as "no business logic in route handlers").
- Code-first vs. schema-first is an authoring-mode choice; whichever you pick, the generated side is Pattern 8 (Dual-Representation) — drift between SDL and Kotlin types must have a single sync step (build plugin / annotation processor).

### N+1 as a Pattern 4a (Pipeline-Order) risk

GraphQL's selection model lets clients request nested fields the resolver chain never anticipated. N+1 is the canonical failure:

```
query { users { orders { items { product { ... } } } } }
```

Each nested field resolves per-parent unless the server batches. This means:

- **DataLoader registration order** is Pattern 4a — the DataLoader instance must be installed per-request, *before* the resolver pipeline executes, via the GraphQL execution context
- **Query-depth / query-complexity limits** are Pattern 2 (Config-Defined) — a numeric budget declared per-schema; an unbudgeted schema is a DoS surface
- A schema change that adds a new nested connection (`users.orders.items`) is **L1 minimum** on the performance / observability surface even if it's additive at the IDL level — the new traversal introduces new N+1 paths

### Breaking-change severity for GraphQL

GraphQL has its own L0–L4 interpretation, distinct from protobuf:

| Change | Severity |
|---|---|
| Adding a new type / field / argument (with default) | L0 (schema-additive) |
| Adding a **required** argument to an existing field | L2 (existing queries still valid; mutations may now fail at runtime) |
| Marking a field `@deprecated` | L1 (semantic signal; consumer deadlines unverified until removal) |
| Removing a field / type | L3 (every saved client query / mobile-shipped build targeting the field breaks) |
| Changing a field's return type | L4 (semantic-reversal risk — `Int` → `Float`, `String` → `ID`, or nullability flip) |
| Changing enum value names | L3 (clients with exhaustive switches break) |
| Renaming a field (alias-compatible but breaks persisted queries) | L2 minimum |

GraphQL has **no wire-format versioning** — the schema itself *is* the contract. There is no "deploy v2 alongside v1" escape hatch unless you publish a whole second endpoint. This makes field-removal inherently harder than protobuf tag-removal.

### Subscription lifecycle SoT

GraphQL subscriptions run over persistent transports (WebSocket, SSE). This adds a lifecycle dimension the REST + gRPC request/response model does not have:

- **Connection lifecycle** is Pattern 10 (Host-Lifecycle) — subscription survives across request boundaries; its teardown hook must be explicit (close handler, coroutine cancellation)
- **Schema evolution during an active connection** — a client subscribed to an old schema when the server redeploys: define policy (reject on reconnect, soft-migrate, or force reconnect). Undeclared policy = mode 3 rollback surface
- **Subscription resolver scope** shares the N+1 risk with query resolvers, plus amplification: a 1-per-second event fan-out times an unbounded selection set is an outgoing-bandwidth bug

### Federation / stitching addendum

If the GraphQL layer federates multiple subgraphs (Apollo Federation, schema stitching):

- Each subgraph's SDL is an **independent Pattern 4 contract** with the gateway — the gateway composes; it does not own field semantics
- `@key` / `@external` / `@requires` directives are Pattern 4a — entity-resolution pipeline order across subgraphs
- A subgraph schema change is cross-service by construction — every federation edit needs the consumer list to include the gateway **and** every other subgraph that imports entities from it
- Gateway composition failure is a build-time integration check, not a runtime one — add to `automation-contract` Layer 2 drift checks

### GraphQL-specific manifest requirements

- `system_interface.sot_map` entry for `schema.graphqls` (or equivalent) distinct from any REST OpenAPI entry
- `breaking_change.migration_path` for field removal: **always `parallel_switch` via `@deprecated` → monitored usage drop → removal after declared grace period** — there is no other safe path
- `breaking_change.affected_consumers` must enumerate **persisted query hashes** if the client uses APQ (Automatic Persisted Queries) — a server-side hash registry is itself a Pattern 3 (Enum-Defined) consumer of the schema
- `cross_cutting.performance.query_complexity_budget_verified: true` for any schema change that adds a nested connection or list field

### GraphQL-specific drift checks

- [ ] Schema SDL versioned; diff on every PR surfaces field / type / argument changes with L0–L4 severity annotation
- [ ] DataLoader registration audit — every list-returning resolver has a paired DataLoader, or an explicit "no batching needed" justification
- [ ] Query-complexity / query-depth limit config present; exceeding budget during tests fails build
- [ ] `@deprecated` field usage monitored (metric: requests-per-deprecated-field-per-day); field removal blocked until usage is zero for the declared grace window
- [ ] Persisted query registry in sync with the schema if APQ is enabled
- [ ] Subscription connection-count per-tenant bounded (also relevant for the multi-tenant overlay above)

### GraphQL anti-patterns

- ❌ Treating GraphQL as "just REST with flexible fields" — the selection-set DoS surface is real, not theoretical
- ❌ Removing a field without deprecation + usage monitoring — no grace period = L3 consumer breakage
- ❌ Implementing business logic inside resolvers — same drift as route-handler logic; resolvers are adapters
- ❌ One giant schema co-owned by many teams without federation boundaries — every merge becomes a cross-team negotiation
- ❌ Subscriptions over a bus without backpressure semantics — client floods server on reconnect storms

---

## Hexagonal / onion / clean architecture overlay

The base bridge's SoT table assumes a conventional layered architecture (route → service → repository). Teams using hexagonal / ports-and-adapters / onion variants need to re-map the SoT "source" fields to **domain ports**, not infrastructure adapters.

### Remapping SoT source fields

| SoT pattern | Conventional layer source | Hexagonal source |
|---|---|---|
| 1 Schema-Defined | DB migration file | Domain entity + adapter-side mapping layer; migration is an adapter concern |
| 3 Enum/Status | Any `enum class` | Domain-layer `sealed class` (inner ring); adapter enums are projections |
| 4 Contract-Defined | OpenAPI spec | Inbound port interface; OpenAPI is an adapter artifact generated from the port |
| 6 Transition-Defined | State machine in service class | Domain aggregate's state machine; no infrastructure dependencies allowed |
| 8 Dual-Representation | Migration ↔ DB schema | Domain model ↔ persistence adapter ↔ DB schema (three-way, not two-way) |

### What stays the same

- Pattern 4a (Pipeline-Order) still binds to Ktor plugin install order — infrastructure concern, adapter layer
- Rollback modes unchanged — domain layer is pure; rollback concerns live at adapter boundaries
- Cross-cutting concerns (security, observability) implemented in adapters or application services, never in domain

### What to audit differently

- **Dependency direction rule**: domain must not import adapter types. Audit via a module-boundary check (e.g., ArchUnit rule, Gradle module constraint).
- **Domain-logic leakage into adapters**: business rules in `RouteHandler` / repository method bodies are drift — they should live in domain services / aggregates.
- **Port naming discipline**: inbound ports (`ImportOrderUseCase`) vs. outbound ports (`OrderRepository`) — mixed direction in one interface is a design smell.

### Manifest addendum

- `sot_map.source.location` for hexagonal projects should reference the domain-layer file, not the adapter
- `affected_consumers` should distinguish domain consumers (other domain services) from adapter consumers (HTTP clients, event bus)

The methodology's patterns hold; only the **address** of the SoT moves inward.

---

## Virtual threads (Loom) / alternative concurrency overlay

This bridge assumes structured-concurrency coroutines. Teams running on JDK 21+ with Project Loom virtual threads, or using Reactor / RxJava / Mutiny, inherit different cancellation and context-propagation semantics.

### Virtual threads (JDK 21+)

| Concern | Coroutines default | Virtual threads |
|---|---|---|
| Cancellation | Cooperative via `CancellationException`; structured via `CoroutineScope` | Cooperative via `Thread.interrupt()`; NO structured-concurrency primitive in standard library (JEP 453 `StructuredTaskScope` is preview) |
| Context propagation | `CoroutineContext` — explicit via `withContext` | `ScopedValue` (preview) or `ThreadLocal` — different binding lifetime model |
| Ktor integration | `install(...) { }` inside `Application.module()` | Ktor 2.x/3.x still uses coroutines; mixing virtual threads requires explicit dispatcher (`Dispatchers.IO.asCoroutineDispatcher(virtualThreadExecutor)`) |
| Blocking code cost | A blocking call in `Dispatchers.Default` starves the pool | A blocking call on a virtual thread parks — cheap; but a `synchronized` block pins the carrier thread (anti-pattern) |
| Structured-concurrency scope | `coroutineScope { }` / `supervisorScope { }` — mandatory | `StructuredTaskScope` is preview; without it, you get unstructured fan-out (leaks) |

### Pinning hazards for virtual threads

Virtual threads "pin" (stick to carrier thread, defeating scaling) when inside:

- `synchronized` block (use `ReentrantLock` instead)
- JNI call
- `java.io.File` / `FileInputStream` (pre-JDK 24 behavior; check your JDK version)

This is a build-time / JDK-version concern — add to the uncontrolled-interface register.

### Reactive-framework substitution

If substituting Reactor / RxJava for coroutines:

- Backpressure semantics are new — Pattern 4a (Pipeline-Order) applies to the reactive operator chain, and reorderings are behavioral (L1+).
- Cancellation is operator-chain-based, not scope-based — the "kill a subtree" model doesn't map 1:1.
- Ktor's `suspend` handlers must be adapted — wrapper or use Mutiny-Ktor / Reactor-Ktor integrations.

### Manifest addendum

- If the concurrency model is non-default, declare it in `cross_cutting.build_time_risk` as a `concurrency_model` field
- Any change touching coroutine scope / thread dispatcher / blocking call site → flag as `pipeline_order`-adjacent
- Structured concurrency regression (losing a `coroutineScope` wrap) is L1 even if tests pass — leaked launches are Phase 8 observation items

---

## Build-time risk discipline (JVM / Kotlin version drift)

Ktor's version catalog and lock file describe *what* is pinned; `cross_cutting.build_time_risk` must also describe *which combinations were verified*.

### Version-drift dimensions to declare

| Dimension | Authoritative file | What drift looks like |
|---|---|---|
| Kotlin compiler | `gradle/libs.versions.toml` → `kotlin` | Compiler upgrade may silently change bytecode or break an obsolete compiler plugin |
| Coroutines runtime | `kotlinx-coroutines-core` | Dispatcher / cancellation semantics change between minor versions; `Ktor` requires a compatible pairing |
| Ktor | `ktor-server-core` | Plugin install-order changes in new Ktor majors; install-order assumptions break silently |
| JVM | `org.gradle.java.home` / toolchain spec | JDK-release-specific JIT / GC behavior; LTS vs non-LTS divergence |
| Serialization | `kotlinx-serialization-json` | Serializer contract changes (e.g., nullability handling) → Pattern 8 drift |
| Gradle itself | `gradle/wrapper/gradle-wrapper.properties` | Config-cache / build-cache behavior changes |

### Required manifest fields for version upgrades

- `cross_cutting.build_time_risk.release_build_verified: true` with a link to the release-mode CI run (debug / IDE compile is NOT sufficient for Kotlin / Ktor bumps)
- `cross_cutting.build_time_risk.minification_rules_touched` — if R8 / ProGuard is used in the packaging stage (e.g., for a fat-JAR container), any Kotlin version bump resets the verified configuration
- `uncontrolled_interfaces` entry for the JVM version — even LTS-to-LTS moves (e.g., 17→21) introduce subtle regressions in `String.hashCode` stability across builds, GC behavior, TLS defaults

### Drift checks

- [ ] Gradle version catalog + lock file + `gradle-wrapper.properties` consistency on every PR
- [ ] Ktor + coroutines + Kotlin version triad verified via a pinned pairing matrix (Ktor's compatibility table is a living doc — don't assume latest-of-each works together)
- [ ] Release-mode fat-JAR / container startup check — not just `./gradlew test`
- [ ] Base image digest (not tag) pinned in Dockerfile; tag-only pins are drift waiting to happen

---

## Validating this bridge against your project

### Self-test checklist

- [ ] **Plugin-install order declaration** — find the canonical `Application.module()` file; verify it has explicit ordering comments. If not, that's your first improvement.
- [ ] **Plugin-order drift reproducibility** — swap two unrelated plugins' install order in a branch, run integration tests. Do they catch the behavioral difference? If not, you're missing Pipeline-Order coverage.
- [ ] **Migration schema drift reproducibility** — add a column to a domain class without adding a migration file; confirm CI flags `drift.codegen_touched_but_no_generated_diff` (or equivalent Exposed/jOOQ metadata check).
- [ ] **OpenAPI drift reproducibility** — add a new endpoint without regenerating the OpenAPI spec; confirm CI flags it.
- [ ] **Coroutine scope audit** — grep the codebase for `GlobalScope` / `CoroutineScope(Dispatchers.*)` created outside of lifecycle; each hit should either be removed or documented with a `// justified: ...` comment.
- [ ] **Transaction boundary vs. coroutine scope** — pick one existing endpoint that writes to DB; confirm the transaction begins and ends within a single coroutine context and doesn't leak across `launch` / `async` boundaries.
- [ ] **Kill-switch test** — confirm at least one critical path has a feature-flag-based disable, and that the disable has been exercised in staging in the last quarter.

### Known limitations of this bridge

- **Observability vendor specifics** — the observability depth section gives a tool-agnostic contract (fields / cardinality / PII rules). Specific APM vendor exporter config stays project-local.
- **Tenant registry implementations** — the multi-tenant overlay treats tenant resolution as a middleware concern; the tenant registry itself (DB-backed, config-file, external service) is project-local — each option has its own freshness / drift profile.
- **Specific reactive frameworks** — the virtual-threads / alternative-concurrency overlay flags the *shape* of the substitution (cancellation, context propagation, pinning). Concrete Reactor / RxJava / Mutiny migration playbooks are project-local.
- **Framework-internal coroutine dispatching inside Ktor plugins** — the bridge treats `install(Plugin)` as a black box at the pipeline-order level; plugin internals (how a given plugin launches work) are left to plugin-specific documentation.

### What to log as a deviation (vs. upstream to this bridge)

- **Project-local deviation** (stays in your repo): unusual in-house frameworks, custom DI glue, compliance overlays specific to your regulated market.
- **Worth upstreaming** (PR to this bridge): generic Ktor patterns we missed, new plugin-order gotchas, widely-used migration tool integrations.

---

## What this bridge does NOT override

- Methodology documents remain tool-agnostic. This bridge is only the concrete mapping for Ktor projects.
- Any Ktor-specific convention adopted here (e.g., outbox pattern) is optional; the methodology only requires the underlying discipline (e.g., Temporal-Local / Pipeline-Order).
