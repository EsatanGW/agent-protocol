# SoT Desync Anti-Patterns and Repair Strategies

> **Companion to [`source-of-truth-patterns.md`](source-of-truth-patterns.md).** That file catalogues the **10 SoT identification patterns** (which kind of authority your information has). This file catalogues the **6 desync anti-patterns** (how SoTs go wrong in practice) and the **4 standard repair strategies** for fixing them.
>
> The split is by purpose: identification vs diagnosis. Reach for this file once you have identified the SoT pattern and need to assess desync risk or design a repair.

---

## Common desync anti-patterns

### Anti-pattern 1: Dual-write without coordination

Two systems write the same data independently, with no coordination mechanism.

```
❌ Service A writes to DB → order.status = 'shipped'
❌ Service B writes to DB → order.status = 'processing'
(Last-writer-wins race condition.)
```

**Repair:** designate one service as source of truth; the others update via events or API calls.

### Anti-pattern 2: Consumer derives its own truth

The consumer does not read the source of truth — it computes or infers its own version.

```
❌ Backend:  user.isVIP = purchaseCount > 100
❌ Frontend: user.isVIP = totalSpent > 10000
(Two definitions, inconsistent results.)
```

**Repair:** consolidate the VIP definition to one place (usually the backend); the frontend reads the result only.

### Anti-pattern 3: Cached truth goes stale

Cached data is stale, but the system keeps using it as authoritative.

```text
❌ Cache layer:       product.price = 99   (value from 3 hours ago)
❌ Authoritative store: product.price = 129 (just updated)
❌ User sees 99, places an order, charged 129.
```

**Repair:** explicit cache-invalidation strategy. Sensitive data like price needs short TTL, active invalidation on write, or event-driven updates — never rely on natural expiry alone.

### Anti-pattern 4: Documentation drifts from implementation

Docs describe old behavior; the code has moved on.

```
❌ API doc:          POST /orders returns 201
❌ Implementation:   POST /orders returns 200 (changed six months ago)
```

**Repair:** bind documentation updates into the implementation PR checklist (see [`ci-cd-integration-hooks.md`](ci-cd-integration-hooks.md)).

### Anti-pattern 5: Translation keys drift from the source copy

i18n translation files evolve independently of the original copy.

```
❌ en.json:     "submit_button": "Send Order"
❌ Design file: "Place Order"
❌ fr.json:     "submit_button": "Envoyer la commande" (translated from the old "Send Order")
```

**Repair:** designate the design source as the source of truth for copy; translation files are consumers.

### Anti-pattern 6: Pipeline order treated as an implementation detail (not a contract)

Execution order of N stages / middleware / interceptors **is a contract** (see [`source-of-truth-patterns.md` §Sub-pattern 4a: Pipeline-Order Contract](source-of-truth-patterns.md#sub-pattern-4a-pipeline-order-contract-order-is-also-a-contract)), but is often treated as "wherever the registration code happens to live."

```text
❌ Adding a new interceptor to an HTTP client chain after error-mapping.
❌ Result: the interceptor receives raw HTTP errors, not domain errors — semantics broken.
❌ Nobody on the PR notices; the diff is a single registration line.

❌ Server-side plugin / middleware install order drifts across branches.
❌ After merging, staging / prod behavior differs subtly.

❌ Two scene-level scripts mutate state in the update tick without setting Script Execution Order.
❌ Works on dev machines; after an unrelated reimport, ordering flips and visual bugs appear.
```

**Repair:**

- Declare the expected order in **one place** (a pipeline config file, a `registerInterceptors()` function, a Script Execution Order setting).
- Treat order changes as breaking changes; run them through [`breaking-change-framework.md`](breaking-change-framework.md) for blast radius.
- Have each stage declare its relative constraints (`after: auth`, `before: compression`) so order becomes verifiable.
- Cross-reference [`cross-cutting-concerns.md`](cross-cutting-concerns.md) (build-time risk) for the pipeline-checks item.

---

## Standard strategies for repairing desync

### Strategy 1: Single writer

Only one system writes; the others read.

Applicable to: most cases.

### Strategy 2: Event-driven sync

When the source of truth changes, it emits an event; consumers subscribe and update.

Applicable to: many consumers needing near-real-time sync; microservice architectures.

### Strategy 3: Dual-read / dual-write migration

During a migration, old and new systems run in parallel; cutover is gradual.

Applicable to: replacing the source of truth for a given piece of information.

Flow:

```
Phase 1: New system starts writing; reads still go to the old system.
Phase 2: Reads switch to the new system; old system continues writing (as backup).
Phase 3: Old system stops writing.
Phase 4: Old system is removed.
```

### Strategy 4: Reconciliation

Periodically compare the two systems' data, surface discrepancies, and repair them.

Applicable to: environments where real-time sync is not possible (e.g. cross-organization systems).

---

## Mapping anti-patterns to repair strategies

| Anti-pattern | Most often repaired with |
|---|---|
| #1 Dual-write without coordination | Strategy 1 (single writer) — usually the cleanest fix |
| #2 Consumer derives its own truth | Strategy 1 (single writer) — designate the canonical computer |
| #3 Cached truth goes stale | Strategy 2 (event-driven sync) — invalidate on write |
| #4 Doc drifts from implementation | Strategy 1 (single writer) — designate impl as SoT, codegen / templated docs |
| #5 i18n keys drift from source copy | Strategy 1 (single writer) — design source is canonical, translations are consumers |
| #6 Pipeline order treated as detail | Strategy 1 (single writer for the order declaration) + relative-constraint declaration |

Strategy 3 (dual-read / dual-write migration) is the meta-strategy used to *transition between* the other strategies — for example, replacing the SoT for a piece of information without a flag-day cutover. Strategy 4 (reconciliation) is the fallback when real-time sync is impossible.

---

## Where this file fits

This is a **diagnostic appendix**, not a normative source. It does not introduce new SoT rules; it catalogues common failure modes of the patterns defined in [`source-of-truth-patterns.md`](source-of-truth-patterns.md) and the standard ways to repair them. If a normative rule is needed (a new pattern, a new sub-pattern), add it to the spec, not to this appendix.
