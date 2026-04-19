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

## Reference worked example outline

*(A full worked example will live at `docs/examples/ktor-server-example.md` in a future update.)*

**Example:** Add a new "paused" state to an order lifecycle.
- System interface surface: orders API response includes new enum value → L1+ (consumers with non-exhaustive switch break)
- Information surface: migration adds allowed state to a CHECK constraint or enum type
- Operational surface: metrics include new state, dashboards updated
- SoT: state machine in code (transition-defined) + DB constraint (schema-defined) — both must be in sync
- Rollback: mode 1 for code, mode 2 for DB (forward-only)

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

- **Multi-tenant / sharding patterns** — not covered. Teams running multi-tenant DBs should add a project-local addendum covering tenant-scoped SoT and cross-tenant drift.
- **gRPC server role** — this bridge assumes HTTP; teams using Ktor + a separate gRPC layer need to extend `system_interface` surface mapping to cover both protobuf IDLs and OpenAPI / GraphQL schemas as parallel SoTs.
- **Observability vendor specifics** — intentionally left abstract (OpenTelemetry-style). If your team uses a specific APM vendor, record the exporter config as project-local.
- **Hexagonal / onion architectures** — the SoT table assumes a conventional layered architecture. Teams using hexagonal patterns may need to re-map "source" fields to domain ports rather than DB classes.
- **Reactive frameworks other than coroutines** (e.g. Reactor-style, Project Loom virtual threads) not covered; cancellation semantics differ materially.

### What to log as a deviation (vs. upstream to this bridge)

- **Project-local deviation** (stays in your repo): unusual in-house frameworks, custom DI glue, compliance overlays specific to your regulated market.
- **Worth upstreaming** (PR to this bridge): generic Ktor patterns we missed, new plugin-order gotchas, widely-used migration tool integrations.

---

## What this bridge does NOT override

- Methodology documents remain tool-agnostic. This bridge is only the concrete mapping for Ktor projects.
- Any Ktor-specific convention adopted here (e.g., outbox pattern) is optional; the methodology only requires the underlying discipline (e.g., Temporal-Local / Pipeline-Order).
