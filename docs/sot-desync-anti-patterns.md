# SoT Desync Anti-Patterns and Repair Strategies

> **Companion to [`source-of-truth-patterns.md`](source-of-truth-patterns.md).** That file catalogues the **10 SoT identification patterns** (which kind of authority your information has). This file catalogues the **7 desync anti-patterns** (how SoTs go wrong in practice) and the **4 standard repair strategies** for fixing them.
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

### Anti-pattern 6: Fan-out consumer registry drift (one fact, N declarations, N-1 forgotten)

A single fact (typically a version string, a feature-flag name, an enum value, a build identifier) is independently declared in N files because each runtime / package format / index needs its own copy. Updating one is easy; updating all N synchronously requires a registry the human eye does not naturally maintain.

```text
❌ Release commit bumps CHANGELOG.md from 1.20.0 to 1.21.0.
❌ plugin.json .version still 1.20.0
❌ marketplace.json .metadata.version still 1.20.0
❌ README.md badge still 1.20.0
❌ CHANGELOG.json (generated) not regenerated, still 1.20.0
❌ Three of five consumers carry the old version; CI version-consistency check fails.
```

The failure mode pattern: the change author reasons about *one* canonical declaration and treats the others as "trivially derived" — but the derivation is human-mechanical, not automated. Each forgotten declaration is a silent consumer; the failure surfaces only at CI / runtime / first user report, never at edit time.

**Repair:**

- **Centralize via a check script that lists all N declarations** — the script's enumeration *is* the registry. (This repo's [`.github/scripts/check-version-consistency.sh`](../.github/scripts/check-version-consistency.sh) is the worked example: it names plugin.json / marketplace.json / README badge / CHANGELOG.md / CHANGELOG.json as the five declarations of the version string and fails if any disagree.)
- **Run the check pre-push, not pre-merge** — once the change is pushed, fixing fan-out drift requires either a follow-up commit or a force-push of the tag. Pre-push catches it cheaply; pre-merge has already paid the visibility cost.
- **Where possible, demote N-1 of the declarations to generated artifacts** — e.g. CHANGELOG.json is regenerated from CHANGELOG.md by a script. The fewer hand-edited declarations, the smaller the surface.
- **Treat the check script's exit code as the SoT for "does this fact agree across consumers"** — not any single declaration. The CHANGELOG.md author's mental model "I bumped the version" is not the same as the system's "all five agree."

This is structurally Anti-pattern 2 (consumer derives its own truth) at the tooling layer: each consumer file independently *declares* a version that should be derivable from one canonical source. The registry pattern is the hybrid — accept that N files exist, but make their agreement mechanically checkable.

### Anti-pattern 7: Pipeline order treated as an implementation detail (not a contract)

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
| #6 Fan-out consumer registry drift | Strategy 1 (single writer / generated artifact) + Strategy 4 (reconciliation via check-script registry) |
| #7 Pipeline order treated as detail | Strategy 1 (single writer for the order declaration) + relative-constraint declaration |

Strategy 3 (dual-read / dual-write migration) is the meta-strategy used to *transition between* the other strategies — for example, replacing the SoT for a piece of information without a flag-day cutover. Strategy 4 (reconciliation) is the fallback when real-time sync is impossible.

---

## Where this file fits

This is a **diagnostic appendix**, not a normative source. It does not introduce new SoT rules; it catalogues common failure modes of the patterns defined in [`source-of-truth-patterns.md`](source-of-truth-patterns.md) and the standard ways to repair them. If a normative rule is needed (a new pattern, a new sub-pattern), add it to the spec, not to this appendix.
