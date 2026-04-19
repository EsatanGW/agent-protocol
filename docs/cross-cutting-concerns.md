# Cross-Cutting Concerns

> **English TL;DR**
> Six concerns that apply to *every surface* a change touches — they are not surfaces themselves. **Security** (threat model, PII handling, auth/authz, secret management per surface). **Performance** (latency / throughput / resource budgets — budgets declared per surface). **Observability** (metrics, logs, traces, alerts with a per-surface view; includes the "is this change even observable?" question). **Testability** (which test levels exist for each surface, can this be tested at all, what's the smallest reproducible case). **Error handling** (classification, propagation, recovery; cancellation propagation treated as a distinct sub-concern — 6 capability categories: structured scope, explicit context/token, abort signal/controller, drop/ownership-based, thread interrupt, manual flag check). **Build-time risk** (codegen drift, code shrinker / name mangler classes of toolchains, AOT-compile runtime families, asset pipeline, determinism variance across platforms / hashes / locales / GPU vendors). Each concern has a per-surface checklist and anti-pattern list. Used during Phase 5 (Review) and the Change Manifest.

This document covers six concerns that cut across every surface a change touches:
**security, performance, observability, testability, error handling, and build-time risk.**

They are not independent surfaces — they are attributes that must be checked on every surface.

---

## Why these are not independent surfaces

Security and performance have no dedicated source of truth or consumer set — they attach themselves to every surface.

For example:

- User-surface security = XSS protection, CSRF tokens, input sanitization.
- System-interface-surface security = auth, rate limiting, payload validation.
- Information-surface security = encryption at rest, access control, audit.
- Operational-surface security = secret management, log redaction.

These concerns therefore appear as **cross-cutting checklists** applied per surface during review.

---

## Security checklist

### User surface

- [ ] User input is sanitized (XSS, injection defenses in place).
- [ ] Sensitive data is not exposed to the client in plaintext.
- [ ] Forms carry CSRF protection.
- [ ] File uploads enforce type and size limits.
- [ ] State is properly cleared on auth-state transitions (login / logout).

### System-interface surface

- [ ] Every endpoint has correct auth and authorization.
- [ ] Rate limiting is in place.
- [ ] Request payloads go through schema validation (unexpected fields rejected).
- [ ] Responses do not leak internal information (stack traces, internal IDs).
- [ ] Cross-origin requests (CORS) are configured correctly.
- [ ] Incoming webhooks have signature verification.

### Information surface

- [ ] Sensitive data (passwords, tokens, PII) is encrypted at rest.
- [ ] DB queries use parameterized query forms (no SQL injection surface).
- [ ] Access control is enforced at the data layer, not merely hidden in the UI.
- [ ] Backups are encrypted.
- [ ] Soft-delete vs hard-delete strategy is explicit.

### Operational surface

- [ ] Logs avoid recording sensitive information (passwords, tokens, credit-card numbers).
- [ ] Secrets (API keys, DB credentials) are provided via environment variables or a dedicated secret-management mechanism — never hard-coded, never logged.
- [ ] Dependencies have a regular or automated known-vulnerability scan.
- [ ] The deploy pipeline does not expose secrets in build / CI logs.
- [ ] Security events have an incident-response process.

---

## Performance checklist

### User surface

- [ ] First load / first interaction times fall within an explicit performance budget.
- [ ] Bulk rendering uses virtualization or batched loading.
- [ ] Images and media are appropriately compressed and lazy-loaded.
- [ ] Animations / interactions hit the configured target frame rate (no jank).
- [ ] Download / install size stays within budget (split bundles / on-demand loading policy).

### System-interface surface

- [ ] Hot-path APIs have response-time SLAs or budgets.
- [ ] Per-item-loop calls (N+1) are eliminated, or explicitly accepted as known-acceptable.
- [ ] A layered cache strategy exists (edge / gateway / application / client).
- [ ] Batching / pagination is used for bulk transfer.
- [ ] Long-running operations run asynchronously (background jobs / queues).

### Information surface

- [ ] Query patterns have matching indexes / partitions / pre-aggregates.
- [ ] Large tables use pagination, partitioning, or historical-data separation.
- [ ] Migrations avoid long table locks or collateral blocking of hot paths.
- [ ] Full-text / fuzzy search uses a dedicated search mechanism (not a full-table scan).
- [ ] Cache-invalidation strategy is explicit (TTL / event-driven / active flush).

### Operational surface

- [ ] Performance monitoring exists (APM / custom metrics).
- [ ] Alerting rules cover latency, error rate, throughput.
- [ ] Major changes are preceded by load tests or capacity estimates.
- [ ] Scale-up / scale-down strategy is defined.
- [ ] Performance regressions have a rollback or degradation plan.

---

## How to use this document

### During Phase 2 (Plan)

Scan the change plan and tag items that touch security or performance:

```markdown
## Cross-Cutting Impact
- Security: the new API endpoint needs auth + rate limit ← system-interface security
- Performance: the query introduces a JOIN; index existence must be confirmed ← information performance
```

### During Phase 5 (Review)

Check the relevant items on each per-surface checklist. Do not re-check the whole list every time — only the surfaces the change actually touches.

### During Phase 6 (Sign-off)

Record verification results for security and performance in evidence:

```markdown
## Cross-Cutting Evidence
- Security: API auth verification passed (screenshot of 401 response attached)
- Performance: EXPLAIN output shows index scan on the new query (plan attached)
```

---

## Do not over-engineer

This checklist is a **review aid**, not a box-checking bureaucracy that every PR must complete.

Usage principles:

- Small change → scan the relevant items quickly.
- Auth / payment / PII surface → work through the security checklist seriously.
- Hot path / bulk data → work through the performance checklist seriously.
- New API / event / state change → work through the observability checklist.
- Architecture change / new module → work through the testability checklist.
- New outward API / third-party integration / user-visible error state → work through the error-handling checklist.
- Changes to codegen / build config / dependency version / shrinker rules / AOT settings / tree-shaking / asset pipeline → work through the build-time-risk checklist.
- Infrastructure change → work through all of them.

---

## Observability checklist

Observability is what ensures that when something breaks, there is enough information to reconstruct the scene.

### User surface

- [ ] Key user operations have analytics events (button clicks, page entry, flow completions).
- [ ] Error states are captured (API failures, render errors, timeouts).
- [ ] User journeys are traceable (session ID, flow ID).
- [ ] Performance metrics are collected (page load time, interaction latency).

### System-interface surface

- [ ] API requests have structured logging (method, path, status, duration).
- [ ] Distributed tracing exists (trace ID stitched across frontend and backend).
- [ ] Error responses carry sufficient context (not just `500`, but why).
- [ ] External-integration calls have timeouts + retries + failure logs.
- [ ] Asynchronous jobs have start / success / failure logs.

### Information surface

- [ ] Data changes have an audit trail (who, when, what changed).
- [ ] Schema migrations leave execution logs.
- [ ] Cache hit/miss ratio is observable.
- [ ] Data-inconsistency events trigger alerts.

### Operational surface

- [ ] All logs use a structured format (machine-parsable, not free text).
- [ ] Log levels are appropriate (no debug noise in production-critical channels).
- [ ] Monitoring dashboards cover the new feature's key metrics.
- [ ] Every alert rule has a matching runbook (what to do after receiving the alert).
- [ ] Log / telemetry retention meets compliance requirements.

---

## Testability checklist

Testability ensures code can be tested efficiently and reliably.

### User surface

- [ ] UI components can be tested in isolation (no reliance on global state for rendering).
- [ ] Interaction logic is separated from rendering (logic testable without spinning up the UI runtime).
- [ ] Test data is easy to construct (factories / builders / fixtures exist).
- [ ] Visual behavior has a regression-detection mechanism (snapshot / golden / screenshot diff).

### System-interface surface

- [ ] Outward interfaces have contract tests (not only local unit tests; payload shape is verified).
- [ ] External dependencies can be mocked or record-and-replayed (tests do not require live third-party services).
- [ ] Async / event-driven flows are verifiable synchronously in tests.
- [ ] Error paths can be triggered in tests (not only the happy path).

### Information surface

- [ ] Data-layer tests use isolated test data (not production data).
- [ ] Migrations can be dry-run in CI and verified both directions.
- [ ] Tests are isolated from each other (no shared state leakage).
- [ ] Large-data scenarios have matching performance / stress tests.

### Operational surface

- [ ] The automated verification pipeline covers key tests (not only static checks).
- [ ] Tests are stable (no flaky tests).
- [ ] Test execution time is reasonable (developers will not skip them for being too slow).
- [ ] Test coverage is high on the critical paths (not chasing 100% globally; chasing coverage on high-risk paths).

---

## Error-handling checklist

Error handling is often reduced to "write a log line inside a `try/catch`," but error is a **signal that propagates across surfaces**, and each step of the propagation can drop important information or distort the user's understanding.

### Why error handling is a distinct cross-cutting dimension

It overlaps none of the other four dimensions:

- Not just observability (recording errors) — also "how errors get translated for the user."
- Not just security (preventing leakage) — also "retaining diagnosability while preserving security."
- Not just performance (retry cost) — also "how failure modes do not avalanche the system."
- Not just testability (testing error paths) — also "error classification itself must be designed."

### Cross-surface propagation chain

```
Data-layer exception (DB constraint, external API timeout)
   ↓ System-interface surface: wrapped as which error code? retry or not?
API response (4xx / 5xx + body)
   ↓ User surface: which message to show? which state to preserve? redirect or not?
UI state (error banner / empty state / dialog)
   ↓ User: understandable? recoverable? worth reporting?
   ↓ Operational surface: log / alert / runbook link
```

**Core principle: error messages get more abstract as they ascend the surfaces, and more concrete as they descend.**

- Closer to the data layer → more specific ("violates UNIQUE constraint on email").
- Closer to the user → more abstract ("This email is already in use").
- The **trace ID** must stitch top to bottom, so that the user-described problem maps back to the original stack trace.

### User surface

- [ ] Every failure state has a clear UI (no "white screen" / "nothing happens" / "loading forever").
- [ ] Error messages are understandable (no raw stack traces, SQL messages, or internal error codes).
- [ ] Recoverable errors provide a recovery action (retry, switch, contact support).
- [ ] Unrecoverable errors say so explicitly (do not encourage pointless retries).
- [ ] Form-validation errors anchor to the specific field (not just a single red banner at the top).
- [ ] Network / offline errors are distinguishable from business-logic errors (do not let "network issue" mask "insufficient balance").
- [ ] The user's already-entered input is not lost in the error state.

### System-interface surface

- [ ] Error classification is structured (not just `Error: something went wrong`).
- [ ] Distinguishes retryable (transient) from non-retryable (permanent).
- [ ] Retries use jittered exponential backoff (no thundering herd).
- [ ] Outward API error codes carry a version commitment (message text cannot be changed arbitrarily).
- [ ] Webhook / event-processing failures have a dead-letter queue.
- [ ] Cross-service errors carry a trace ID end-to-end.
- [ ] Idempotent operations have proper idempotency-key design (retries do not double-charge).

### Information surface

- [ ] DB constraint violations are not leaked as 5xx — the producer translates them into business errors.
- [ ] Partial-write failures have an explicit strategy (transaction / saga / compensation).
- [ ] Deserialization failures have a fallback (a single bad row does not kill the endpoint).
- [ ] The policy for unexpected / missing fields is explicit (reject / ignore / log).

### Operational surface

- [ ] Errors are captured in structured logs (trace ID, user ID, context included).
- [ ] Error grading maps to alert levels: (critical) page immediately, (warn) dashboard, (info) log only.
- [ ] Every alert has a matching runbook (on-call should never receive an alert with no known response).
- [ ] Error metrics (rate, type, user-impact) flow into the dashboard.
- [ ] Error-message / copy changes follow the same flow as i18n (no placeholder strings in production).

### Asymmetric-responsibility principle

A common error-handling anti-pattern is "upstream does nothing; downstream must handle everything" — or the reverse. This methodology uses **asymmetric responsibility** instead:

| Layer | Responsibility |
|-------|----------------|
| **Data / integration layer** | Throw the most specific error (do not swallow the stack trace) |
| **Service / domain layer** | Translate into business language, decide retry-ability, decide escalation |
| **API layer** | Return a stable error code + safe message outward; log full context internally |
| **UI layer** | Translate into user language, offer recovery, preserve input state |
| **User** | Only responsible for "describe what happened / provide a trace ID" |

Each layer does only its own job — no delegation downward, no usurpation upward:

- The data layer must not decide whether to show a dialog.
- The UI layer must not guess why the server internally failed.
- Middle layers must not pass raw SQL errors all the way to the UI.

### Minimum error-classification design

Any system should be able to answer at least:

```
1. Is this a client error or a server error?
2. Can this error be automatically retried?
3. Does this error need human intervention? On-call, support, or the user?
4. Will the same input reproduce it?
5. Does this error affect other users or other data?
```

Any plan / spec must answer these five questions; otherwise error handling is just "wrap it in `try/catch`."

### Cancellation and context propagation

A frequently overlooked sub-area of error handling: when a request / task / user operation is **cancelled** (network drop, user closes the page, upstream times out), **does the cancellation signal propagate to every downstream task?**

This is not "error" in the classic sense — no exception is thrown — but missing it causes:

- Zombie tasks continue producing results nobody needs, wasting resources.
- Cancelled operations produce side effects (write to DB, send notification, charge money).
- The user sees "cancelled" but the server actually finished, leaving state inconsistent.
- Nothing shows up in tests; it accumulates as resource leaks in production.

**Cancellation-propagation mechanisms, by capability category** (specific languages and APIs belong in the stack bridges):

| Capability category | How it works | Caveat |
|---------------------|--------------|--------|
| **Structured scope** | Parent scope cancels all child work automatically; no explicit propagation required | Anything launched in a "global" site outside the scope escapes control |
| **Explicit context / token** | A cancellation context object must be threaded into every blocking downstream call | One missed hop and the downstream never receives cancellation |
| **Abort signal / controller** | A signal object is created; downstream async APIs subscribe to it | Downstream must implement signal handling; not all APIs support it |
| **Drop / ownership-based** | Dropping the future / task (going out of scope) is equivalent to cancellation | Needs language-level ownership; long-lived handles can stall |
| **Thread interrupt** | An interrupt signal is sent; the thread checks for it at cooperative points | If the workload has no check points (pure CPU loop), interrupt never fires |
| **Manual flag check** | Maintain a boolean; poll it at loop / node boundaries | Last-resort fallback when no built-in mechanism exists; responsibility is entirely on the author |

The point is not to memorize any one syntax — it is to remember that **every runtime has a cancellation-propagation mechanism, and every one of them can be used incorrectly.** Which category your stack falls into and what the specific APIs are belongs in the corresponding `docs/bridges/*-stack-bridge.md`.

**Checklist:**

- [ ] Long-running or interruptible operations (HTTP request, DB query, file I/O, loop computation) receive a cancellation signal.
- [ ] Fire-and-forget calls (launch without scope, detached goroutine, `async` without `await`) are **intentional**, not forgotten awaits.
- [ ] Side effects after cancellation (already-emitted log, already-started transaction) have an explicit plan (commit / rollback / compensate).
- [ ] After upstream cancels, downstream does not continue with business-impacting operations (do not charge after cancellation).
- [ ] Cross-service calls translate cancellation into the upstream protocol (HTTP request abort, gRPC cancellation, no MQ ack).
- [ ] Timeouts have explicit ownership (who sets it, what value, who cleans up after expiry).

**Anti-patterns (stated as capability categories; specific languages appear in the stack bridges):**

```text
❌ Structured-scope family: launching a long task at a global site with no scope constraint
   → user navigates away but the task keeps running, writing data it should not.
❌ Explicit-context family: forgetting to pass the context into a downstream blocking call
   → upstream aborted but the outbound request keeps going.
❌ Abort-signal family: an async API call not wired to a signal
   → after navigation, the response is still pending and the callback hits a destroyed component.
❌ Subscription-style resources not disposed when the owner is destroyed
   → a new owner is created while the old one still receives events and mutates global state.
❌ Outside of drop-based languages: assuming a future / callback becomes inert on its own
   → it actually fires and produces side effects that should not exist.
```

**Repair strategies:**

- Treat the cancellation-propagation path as an explicit part of system design, not an afterthought.
- Every async entry point (HTTP handler, UI event handler, job worker) opens a scope / context at start and guarantees all children are cancelled at end.
- Any side-effecting operation checks whether cancellation has occurred **before** execution (`ensureActive()` / `ctx.Err()` / `signal.aborted`).
- Tests exercise the cancellation path: simulate upstream abort and verify that no zombies remain and no side effects leak.

> Bridge to SoT pattern 10: when the host is destroyed (process death), the runtime's cancellation mechanism **may not have time to fire**. Critical side effects cannot rely on cancellation handlers alone — a "post-restart consistency check" (reconciliation) is the backstop.

---

## Build-time-risk checklist

Many bugs are not wrong source code — they are "compile / package / generate / shrink / pack" steps translating correct source into incorrect runtime artifacts. These risks are nearly invisible in local debug builds; they surface only in release, on specific devices, in specific CI pipelines, or on specific AOT targets.

> Cross-reference `source-of-truth-patterns.md` pattern 8 (Dual-Representation Truth) — this entire dimension manages the risk of the bake / compile step between "editor representation" and "runtime representation."

### Why this is its own cross-cutting dimension

It overlaps none of the other five:

- Not just observability — build problems produce noise that looks nothing like runtime errors.
- Not just testability — passing a debug build does not mean passing a release build.
- Not just performance — tree-shaking may delete live code in pursuit of size.
- Not just error handling — these errors often manifest as "app fails to start" or "class not found," with no chance to enter any error-handling path.

### Common risk categories

| Risk | Essence | Typical symptoms |
|------|---------|------------------|
| **Codegen drift** | Editor source changed, generated file did not (see SoT pattern 8) | Runtime does not see new field, method missing, build fails |
| **Minification / obfuscation** (code-shrinker and name-mangler toolchains) | Names shortened or renamed, breaking reflection / string lookup | `ClassNotFound`-style errors, JSON parsing returns null, dynamic loading fails |
| **Shrinking / tree-shaking** | Code deemed unreachable by static analysis is removed | Reflection-only classes vanish; DI registration misses; plugin methods disappear |
| **AOT compile** (runtimes that translate bytecode / source into native code at release time) | No runtime codegen, limited reflection | JIT runs fine locally; release crashes |
| **Asset pipeline** | Images / shaders / audio / fonts / sprite atlases go through compression, format conversion, hash rename | UI cannot find assets, placeholders shown, wrong hash |
| **Build-time injection** | Version, environment variables, feature flags, commit hash burned in at compile time | Wrong-environment build, secrets in release, flags cannot be hot-toggled |
| **Dependency version resolution** | Transitive deps, lock-file drift, native-binary ABI | Same source on different machines produces different bundles |
| **Platform / architecture differences** (CPU architectures, mobile OSes, browser targets) | Same source compiles to different behavior per platform | Specific-device crash, specific-browser missing feature |

### Per-surface checklists

#### User surface

- [ ] Release-build UI matches debug-build UI (embedded fonts, image compression, color profile not altered by the pipeline).
- [ ] Widgets / screens / routes located by reflection or string still resolve after minification (keep rules added).
- [ ] Static assets (images, fonts, lottie, shaders) still load after compression / rename / atlas processing.
- [ ] i18n keys are not treated as dead string constants and removed or rewritten by the minifier.
- [ ] Accessibility labels / IDs are not stripped from the release build.

#### System-interface surface

- [ ] Generated client stubs (gRPC / OpenAPI / GraphQL) and the server spec are verified in-sync by CI.
- [ ] DTOs / requests / responses serialized via reflection have keep or annotation protection so serialization still works after minification.
- [ ] External-SDK shrinker / keep rules are updated alongside SDK version bumps (must check on every SDK upgrade).
- [ ] Build-time feature flags and runtime feature flags do not collide on the same key; the override order is explicit.

#### Information surface

- [ ] Every codegen path (annotation-generated source, IDL-generated stubs, ORM migration, schema generator) has an in-sync check at pre-commit or in CI.
- [ ] Whether generated files are checked in is an explicit team policy (all in / all out / mixed) — consistently applied.
- [ ] Enum / sealed class / discriminated-union `switch` exhaustiveness holds after minification (anti-pattern: the minifier reorders enums).
- [ ] The runtime representation of the DB schema (live DB) and the editor representation (migration files) are in agreed states; out-of-band `ALTER` is prohibited in prod.

#### Operational surface

- [ ] CI runs in release configuration (not only debug); at minimum, key release options (minify / shrink / AOT) are exercised.
- [ ] Builds are reproducible: same commit + same lock file → same artifact hash.
- [ ] Mapping files (name-mangler mapping / source maps) are preserved so release errors can be resolved back to source lines.
- [ ] Build-time constants (version, environment, hash) are observable in startup logs or health endpoints.
- [ ] The build pipeline itself is under version control: Dockerfile / CI config / build scripts go through review, not direct edits on the pipeline.

### Common anti-patterns

**Anti-pattern A — "works on my machine is qualification"**
Debug builds disable minify / shrink / AOT; local testing has zero predictive value.
→ At minimum, run a release-configuration smoke test in CI or staging.

**Anti-pattern B — "`-keep *` as master key"**
To prevent the name mangler from touching anything, keep every class.
→ Loses shrink benefit, artifact size balloons, and the real problem is masked. **Locate** the specific package / annotation instead.

**Anti-pattern C — "run codegen manually"**
Relying on developers to remember to run codegen (IDL → stub, annotation → boilerplate, schema → migration stub).
→ Somebody always forgets; generated files and source drift. Enforce via pre-commit hook + CI gate.

**Anti-pattern D — "try rebuilding when the release build breaks"**
Without a reproducible build or preserved mapping, release-only bugs become guesswork.
→ Preserve mappings, keep log symbols, have error telemetry that resolves back to source.

**Anti-pattern E — "burn a secret into a build-time constant"**
Assuming compiled binaries hide it — a dump reveals it.
→ Build-time only injects **public** information (version, environment name); sensitive values go through a runtime secret store.

### Phase hookup

- **Phase 1 (Investigate):** confirm whether this change touches build / codegen / dependencies / shrinker rules / AOT / asset pipeline.
- **Phase 2 (Plan):** if it does, list affected generated files / keep rules / build-config diff explicitly.
- **Phase 4 (Implement):** run the matching codegen every time source changes; commit the artifact alongside, or verify via CI.
- **Phase 5 (Review):** when reviewing the PR, check generated files (`.g.*` / `*_generated.*` / `_pb.*`), name-mangler keep rules, and the dependency lock-file diff.
- **Phase 6 (Sign-off):** attach smoke results from the release build, not just debug-build passes.

### Cross-build / cross-platform determinism risk

The same logic executed across different builds, platforms, or points in time **can produce different results** — this is not a bug, it is variance in the underlying execution environment. If not handled explicitly, it turns into intermittent bugs that are difficult to reproduce.

**Common sources:**

| Category | Scenario | Symptoms |
|----------|----------|----------|
| **Floating-point precision** | x86 vs ARM, SIMD on/off, FMA instruction, different language math-lib implementations | Physics-simulation drift, ML-inference micro-differences, hash mismatch |
| **Randomness** | No seed fixed, PRNG shared across threads, platforms default to different RNGs | Intermittent test failures, game replays diverge, A/B group drift |
| **Sort stability** | Language / version does not guarantee stable sort (or vice versa); parallel merge order | Same input different order → diff blows up, snapshot tests flake |
| **Time zone / date** | Server UTC, client local time, DST transitions, leap seconds | Cross-day stats wrong; scheduled jobs miss a day |
| **Locale-dependent behavior** | String comparison (Turkish `i` / `İ`), number format (`,` vs `.`), case conversion | Search hit rate differs per locale; sort order differs |
| **Hash randomization** | Some runtimes seed `hash()` differently each launch; some languages do not guarantee map/dict iteration order | Cache keys unstable; iteration-order-dependent tests flake |
| **Compiler optimization** | -O0 vs -O2, different compiler versions, inlining decisions | Timing-sensitive release-only bugs |
| **GPU / shader** | Different drivers, precision hints, GPU-vendor generations | Visual inconsistency, fallback path not triggered |

**Checklist:**

- [ ] Logic that requires reproducibility (replay, audit, ML training) uses a fixed seed, and the seed is recordable and traceable.
- [ ] Timestamps are in an explicit time zone (UTC / ISO-8601 with offset) and not dependent on host locale.
- [ ] When sort keys tie, tie-breakers are declared explicitly (no reliance on language stable-sort guarantees).
- [ ] Binaries deployed cross-platform (mobile, game, desktop) have "same input → same output across platforms" tests on critical paths.
- [ ] Floating-point comparisons use epsilons, not `==`; money or precise-calculation paths use Decimal, not float.
- [ ] Tests do not rely on iteration order (map, set); explicit sort is added where needed.

**Anti-patterns:**

```text
❌ Game replay: client uses local clock and an unseeded RNG; server verification does not match.
❌ ML inference: dev Mac outputs 0.8734, prod Linux AMD outputs 0.8735; cache keys diverge.
❌ Unit test: depends on map iteration order; fails intermittently across 100 runs.
❌ Billing calculation: float sum 0.1 × 10 ≠ 1.0; user is overcharged by a cent.
❌ Time zone: logs stored in local time; cross-time-zone analysis puts day-A events into day-B.
```

**Repair strategies:**

- Determinism requirements must be declared in Phase 1 (do not discover a mismatch in Phase 5).
- For unavoidable non-determinism (GPU, floating point), use tolerance-based verification, not exact equality.
- Seeds, timestamps, and versions for replay / audit flows are part of the evidence.

---

## How the six cross-cutting concerns interact

They are not independent — improving one typically helps others:

| Improving… | Collateral effects |
|------------|--------------------|
| Observability | → Performance problems become visible; error classification sharpens; build-time issues become faster to locate |
| Testability | → Security fixes get easier to verify; error paths become automatable; release builds can be gated by CI |
| Security | → Needs better audit logs (observability); error messages must not leak; build-time-injected secrets move to runtime |
| Performance | → Needs benchmark tests (testability); failure modes no longer avalanche; watch out for shrink / tree-shake removing live code for size |
| Error handling | → Improves observability, security (leakage prevention), testability (error-path coverage) |
| Build-time-risk management | → Improves observability (mapping / version tags), testability (release-build in CI), security (no secret in binary) |
