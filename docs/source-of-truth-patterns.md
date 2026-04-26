# Source-of-Truth Patterns

> **English TL;DR**
> "Find the source of truth before patching consumers" is one of the core moves of this methodology. This document catalogues ten SoT patterns that any piece of information in a system falls into: (1) Schema-Defined, (2) Config-Defined, (3) Enum/Status-Defined, (4) Contract-Defined with sub-pattern 4a Pipeline-Order, (5) UI/Design-Defined, (6) Transition-Defined (state machines and valid transitions), (7) Temporal-Local (client or session has local authority only within a time window), (8) Dual-Representation (editor form + runtime form kept in sync by an explicit bake / codegen step), (9) Resolved/Variant Truth (priority chain of candidates), (10) Host-Lifecycle (truth tied to a runtime host's lifetime). For each pattern the doc lists: identification question, common desync symptoms, repair strategy. Six common desync anti-patterns (dual-write, consumer-derived truth, stale cache, doc drift, i18n key drift, pipeline-order as implementation detail) and four repair strategies are enumerated — anti-pattern 6 pairs with sub-pattern 4a. Half-sync gotchas (hot-reload, live-edit, incremental reimport) are treated as a distinct callout within Pattern 8. Used in Phase 1 (Investigate) of the workflow as the core diagnostic move.

"Find the source of truth before you find the consumers" is one of the core moves of this methodology. This document expands that idea into executable identification patterns, common anti-patterns, and repair strategies.

> **Quick decision aid.** If you only need a fast pattern call (10 candidates + sub-pattern 4a) without reading the full catalogue, see [`decision-trees.md §Tree B — Which Source-of-Truth pattern?`](decision-trees.md#tree-b--which-source-of-truth-pattern). The binding rules and edge cases stay here.

---

## What a source of truth is

A source of truth is the **sole authoritative origin** of a given piece of information. When copies of the same information exist in multiple places, the source of truth is the one that wins in a conflict.

**Key properties:**

- Every other copy of the same information is derived from it.
- When making a change, you start there — the consumers re-sync afterward.
- If an inconsistency surfaces, the source of truth is right by definition.

---

## Identification patterns

### Pattern 1: Schema-Defined Truth

The source of truth is a database schema or API spec.

```
DB schema (truth)
  → API response (consumer)
    → Frontend model (consumer)
      → UI render (consumer)
```

**How to identify:** ask "if we add a new field, where do we start the change?" — that answer is the source of truth.

### Pattern 2: Config-Defined Truth

The source of truth is a config file or a feature-flag system.

```
Feature flag service (truth)
  → Backend logic (consumer)
  → Frontend toggle (consumer)
  → Analytics filter (consumer)
```

**How to identify:** ask "who decides whether this feature is on?"

### Pattern 3: Enum / Status-Defined Truth

The source of truth is a set of enum or status values.

```
Order-status enum (truth)
  → DB column (consumer: storage)
  → API response (consumer: transport)
  → UI badge (consumer: display)
  → Analytics event (consumer: logging)
```

**How to identify:** ask "if we need to add a new status value, where do we define it first?"

### Pattern 4: Contract-Defined Truth

The source of truth lives in an agreement between two systems — an API contract, event schema, shared types, or **execution order**.

```
OpenAPI spec (truth)
  → Server implementation (consumer)
  → Client SDK (consumer)
  → API documentation (consumer)
```

**How to identify:** ask "if the request / response format changes, which document is edited?"

#### Sub-pattern 4a: Pipeline-Order Contract (order is also a contract)

A contract is not only about *shape* — it is also about *order*. When N processing stages handle the same request, event, or data stream in sequence, **execution order itself is an implicit contract**. Reordering stages is a breaking change even if no stage's code changed.

**Typical scenarios (stated as concept categories; specific frameworks live in the stack bridges):**

- Server-side HTTP request-handling chain (middleware / filter / plugin install order).
- Client-side HTTP request–response interceptor chain.
- Event-bus subscriber registration order and dispatch order.
- UI / state-management middleware (action → reducer chain, effect middleware).
- Scene / scripting runtime execution scheduling.
- ETL / data-pipeline stage order.
- Build-pipeline stages (lint → test → build → sign → deploy).

**How to identify:** ask "if I swap the order of stage A and stage B, does behavior change?" — if yes, ordering is part of the contract.

**Why it frequently desyncs:**

- Order is usually not captured in a spec or doc; it lives in "the order in which code happens to be written."
- When a new plugin / interceptor is added, its position is chosen ad hoc.
- Different modules register themselves separately, and load order decides the effective order indirectly (less stable).
- Debugging tends to examine a single stage rather than the chain.

**Anti-patterns:**

```text
❌ Auth middleware registered AFTER logging middleware
   → unauthenticated requests get logged with full payload (security leak)

❌ Retry interceptor registered BEFORE error-mapping interceptor
   → retries fire on raw HTTP errors rather than mapped domain errors (wrong semantics)

❌ A new plugin is appended at the end of the chain without considering position
   → it needed to run before compression (to see the original payload) but runs after

❌ Two scene-level scripts both mutate state in an update tick, assuming an order
   the runtime does not actually guarantee
   → intermittent bugs; behavior changes after an unrelated import
```

**Repair:**

- Declare the **expected order** of the pipeline in **one place** (not scattered across module-registration sites).
- Treat any order change as a breaking change; assess blast radius via `docs/breaking-change-framework.md`.
- At registration time, each stage declares relative constraints ("**must run after X / before Y**") so order becomes a verifiable constraint rather than an implicit assumption.
- On PR review, treat pipeline diffs (added / removed / moved stages) as an independent checklist item.

### Pattern 5: UI-Defined Truth (rare but real)

In a few cases the UI is the source of truth — a design system's component spec, for example.

```
Figma design spec (truth)
  → Component implementation (consumer)
  → Storybook documentation (consumer)
  → E2E test snapshot (consumer)
```

### Pattern 6: Transition-Defined Truth

The source of truth is **not the current state value** but the **set of legal state transitions**. Looking at `status = 'shipped'` in isolation tells you nothing — you must also ask "how did it get there from `processing`, and through what mandatory steps?"

```
State-machine definition (truth)
  → DB column (consumer: current value)
  → API response (consumer: current value)
  → UI state (consumer: current value)
  → Audit trail (consumer: transition history)
  → Business workflow (consumer: triggers transitions)
```

**How to identify:** any of the following questions answered "no" puts you in this pattern:

- Can you set `status` directly from A to C? (Must B happen in between?)
- Can every pair of states transition in both directions? (Are any transitions one-way?)
- Does the same status value mean the same thing regardless of predecessor? (Or do different predecessors imply different things?)

**Why this deserves its own pattern:**

Many bugs are not "the data source is wrong" — they are "the state was driven to a legal value through an illegal transition." Seeing `order.status = 'refunded'` is fine, but if it arrived from `pending` skipping `paid`, the books are missing a payment. Schema and enum constraints alone cannot catch this.

**Typical scenarios:**

- Order flows (pending → paid → shipped → delivered → refunded).
- Ticket lifecycles (draft → submitted → approved → published).
- Authentication lifecycles (unverified → email_sent → verified → suspended).
- Deployment flows (building → testing → staging → production).
- Game-level progress (locked → unlocked → in_progress → completed).

**Anti-pattern: "legal value ⇒ system is correct"**

```text
❌ Observed: the system sees order.status == 'shipped' and triggers shipment notification.
❌ Observed: order.status was set directly to 'shipped' without capturing payment first.
(The value is legal; the transition that produced it was illegal.)
```

**Repair:** enforce a transition guard at the source-of-truth layer (language-agnostic pseudocode):

```text
✅ function transitionTo(entity, nextStatus):
✅     if (entity.status, nextStatus) not in ALLOWED_TRANSITIONS:
✅         reject with IllegalTransition(entity.status, nextStatus)
✅     entity.status = nextStatus
✅     auditLog.record(entity.id, previous, next, actor, timestamp)
```

Treat the transition diagram as a reviewable artifact, so consumers (notification services, analytics) can derive which transition events they need to subscribe to from the same definition.

### Pattern 7: Temporal-Local Truth

The source of truth is **temporarily** located in the client / edge node / offline environment. When the network is available or a sync opportunity arrives, authority is transferred to the central system.

```
Client local store (temporary truth, while offline)
  → Sync queue (consumer: waiting to flush)
  → Server DB (eventual truth, after reconciliation)
  → Other client replicas (consumer: receive server update)
```

**How to identify:** ask "when there's no network / the server is unreachable, which copy of this data can be trusted and operated on by the user?"

**This is not anti-pattern 3 (cache staleness); this is design:**

- Cache staleness is "I should have read the newer value but read the old one" — an error.
- Temporal-local truth is "I am authoritative right now; the server will reconcile later" — correct.

Examples:

- A notes app must allow writing in airplane mode.
- Mobile payments must scan QR codes on a subway platform and upload when signal returns.
- A game tracks PvE progress locally and syncs to cloud when online.
- CRDT-based collaboration tools (every client is a truth; merge rules converge).

**Typical scenarios:**

- Offline-first mobile apps.
- Edge / IoT (the central server is not always reachable).
- Game-level progress, single-player PvE.
- Financial / medical apps that must keep working across brief disconnects.

**Design questions this pattern demands:**

1. **Authority handoff timing:** after a local write, when does it get promoted to server truth? Immediate sync? Batched? User-triggered push?
2. **Conflict resolution:** when local and server versions disagree, who wins? Last-write-wins / version vector / CRDT / user manually chooses?
3. **Visibility of local truth:** the same user on two devices — device A wrote locally but has not synced. Should device B see it?
4. **Handling irreversible operations:** can "transfer money," "place order," "delete" happen while offline? Or must they be forced online?

**Anti-pattern: treating temporal-local truth like a cache**

```
❌ Enter airplane mode → "No network, cannot load" white screen.
❌ Write while offline → writes rejected locally; only allowed when online.
❌ Sync conflict → silently overwrite the user's just-made offline edits.
(These treat an offline-first scenario as if it were a connected system with a cache.)
```

**Repair:** explicitly declare which data / operations follow the temporal-local truth pattern, and design dedicated sync queues, conflict resolution, and UI affordances ("this record has not yet synced" icon) for them.

> Side note: patterns 6 (Transition) and 7 (Temporal-Local) frequently combine. If a state transition happened offline, coming back online requires syncing not only the **final state** but the **transition path** as well — otherwise the server-side audit log / notifications / analytics miss a segment.

### Pattern 8: Dual-Representation Truth

The source of truth exists in **two representations simultaneously**:

- **Editor / design-time representation** — human-authored, authoritative for humans (`.proto`, `.unity`, XML layout, `@JsonSerializable` class, design tokens, SQL migration).
- **Runtime / build-time representation** — the derived artifact the system actually runs (generated code, serialized scene binary, `.g.dart`, compiled resources, live DB schema).

Between them sits a **codegen / build / serialization / compile step**. The two are not in a source-consumer relationship — **both are truth**, each authoritative for a different audience:

- The editor representation is authoritative for humans, version control, and PR review.
- The runtime representation is authoritative for the live system.

```
Editor source (authoritative for humans)
  │
  │  codegen / compile / serialize / bake
  ▼
Runtime snapshot (authoritative for the running system)
  │
  ▼
Actual behavior (what users / tests see)
```

**How to identify:** ask "while debugging I see a value different from what the editor shows — why?" If the answer is "because a build / generate / bake / cache step hasn't run yet," you are in this pattern.

**Why this deserves its own pattern:**

Ordinary SoT patterns assume "change the source, consumers follow." The two representations of dual-representation truth do **not** sync automatically — you must **explicitly execute** codegen / rebuild / reimport, or the runtime keeps using the old snapshot. The editor shows the new version and both "look right" during debugging, while system behavior is a third answer.

**Typical scenarios (stated as concept categories; specific tools live in the stack bridges):**

| Category | Editor representation | Runtime representation | Sync action |
|----------|-----------------------|------------------------|-------------|
| Annotation-driven serialization | Class with serialization annotations | Codegen-produced parse / serialize code | Run the corresponding codegen |
| IDL → generated stub | IDL / schema definition file | Generated typed stub or message class | Run the IDL compiler |
| Visual scene / prefab editor | Object tree displayed in the visual editor | Serialized asset + metadata + runtime-loaded object | Asset reimport + runtime restart |
| Declarative layout → compiled resource | Markup layout file | Compiled resource id + runtime view tree | Build produces resources, regenerates resource classes |
| Visual UI editor → packaged archive | Visual UI-editor file | Compiled UI archive | Build re-packs |
| ORM / migration → live schema | Migration file (SQL / DSL / annotation) | Actual DB schema | Run migration tool (especially dangerous when irreversible) |
| Design token | `tokens.json` / Figma variables | Generated CSS / `theme.dart` / Swift theme | Token pipeline build |
| i18n | `en.json` and peers (source files) | Translation bundle compiled into the binary / remote-config snapshot | i18n build, CMS publish |
| ML model | Training notebook + dataset + training config | Deployed model weights + inference graph | Training pipeline + model-registry push |

**Anti-pattern A — changed the editor, forgot the codegen**

```text
❌ Developer adds a field to a @JsonSerializable class.
❌ Does not run build_runner.
❌ Runtime uses the old .g.dart; the new field is null in fromJson.
❌ UI always shows "—"; hours wasted before realizing codegen did not run.
```

**Anti-pattern B — editing the runtime artifact directly (bypassing the editor)**

```text
❌ Manually editing the .g.dart file.
❌ Manually adjusting GUIDs in Unity .meta files.
❌ Running ALTER TABLE on a live DB without going through migration.
Result: next time the runtime artifact is regenerated from the editor representation, manual edits disappear;
or worse — the two never match and nobody knows which one is real.
```

**Anti-pattern C — editor and runtime representations edited concurrently by two people**

```text
❌ A designer moves prefab fields in the Unity GUI.
❌ An engineer pulls on another machine and edits the same prefab (text diff is clean; semantics collide).
❌ After merge the prefab is broken and some references point to deleted objects.
```

**Anti-pattern D — build caches leave runtime frozen on an old snapshot**

```text
❌ Editor edits .proto.
❌ Codegen ran, but IDE cache / Gradle cache / Xcode DerivedData hold the old outputs.
❌ Build succeeds, behavior is old.
```

**Repair strategies:**

1. **Make codegen / build / reimport a non-optional pre-commit / CI gate.**
   - Pre-commit hook diffs generated files against the source.
   - CI runs a clean build and fails if codegen output differs from the checked-in version.
   - Team rule: generated files and their source are committed in the same PR.

2. **The editor representation is the only hand-editable one.**
   - Treat runtime artifacts (`.g.dart`, `_pb.go`, `R` classes, compiled shaders) as read-only.
   - Put `DO NOT EDIT — generated from X` at the top of every generated file.
   - The team chooses whether to version-control generated artifacts or ignore them (a trade-off; either is acceptable when explicit).

3. **Debug flows must distinguish the two representations.**
   - First question when a behavior looks wrong: "has my editor representation been baked / codegen'd into the current runtime?"
   - Provide a single entry-point command for reload / reimport / rebuild so newcomers do not guess which one to run.
   - Have the runtime expose "currently loaded version / build time / source hash" for diagnostics.

4. **Gate irreversible bakes up-front.**
   - A DB migration that cannot be rolled back → migrations require review and a rollback plan.
   - Unity prefab serialization is effectively irreversible → prefab changes go through PR review, not a direct commit to main.
   - Constants baked in at build time (version number, environment) → a wrong one requires a new release; no hotfix.

> Side note: pattern 8 often combines with pattern 4 (Contract) and pattern 5 (UI-Defined). A `.proto` is the editor representation of a contract; the generated stub is the runtime representation. Figma is the editor representation of UI; the component implementation is the runtime representation. The distinction is whether the two are connected by an **automated bake step**.

> **Half-sync gotcha (hot reload / live edit / incremental reimport):**
> Some stacks provide a "partial sync" — code swapped but runtime state not rebuilt. Common forms include:
>
> - UI frameworks' hot reload (code reloaded but widget / view state retained).
> - IDE or compiler incremental builds (only changed classes recompiled; remaining references hold the old classes).
> - Asset / scene-editor incremental reimport (editor stays open but assemblies / bindings are partially rebuilt).
> - Dev-server watch-and-reload (modules reloaded; module-memory state retained).
>
> This is not true sync — the editor representation has been projected to a **subset** of the runtime (the code subset), while a **different subset** (state) remains old. Symptoms: new fields do not appear; DI / provider graphs become inconsistent; resource references turn null.
> **Discipline:** when you suspect a half-sync artifact is producing weirdness, the first step is always a **clean restart + re-reproduce**. A bug that reproduces only before a clean restart is not a real bug.

### Pattern 9: Resolved / Variant Truth

The source of truth is **neither a single file nor a single value** — it is "**the candidate set + the resolution rules**" that together determine the value **in effect right now**. Multiple candidate files / values coexist, and the runtime picks one based on language, screen density, region, device type, feature-flag segment, user identity, time window, etc.

```
Candidates (multiple sources)
     ┌─ default / base
     ├─ variant A (condition X)
     ├─ variant B (condition Y)
     └─ override (condition Z)
         │
         ▼
Resolution algorithm (language / locale / density / flag / segment / media query / variant hierarchy)
         │
         ▼
Effective value at runtime
```

**How to identify:** ask "does this same field / resource / setting get different values under different conditions? If so, **where is the selection rule written**?"

If the answer is "the rule is hidden inside the platform runtime (Android resource resolution), hidden in the design tool (Unity Prefab Variant override), hidden in the framework (i18n fallback chain)," then truth is not any one file — truth is the **rule itself**.

**Typical scenarios:**

| Scenario | Candidate set | Resolution rule |
|----------|---------------|------------------|
| Android resource qualifiers | `values/`, `values-en/`, `values-sw600dp/`, `drawable-xxhdpi/` | Android runtime configuration-match algorithm |
| iOS Asset Catalog variants | 1x / 2x / 3x, dark / light, size class | iOS UIKit automatic selection |
| i18n locale fallback | `en.json`, `en-US.json`, `zh-TW.json`, `zh.json` | Locale fallback chain (missing → parent locale → default) |
| Unity Prefab Variant | Base `.prefab` + one or more variant override layers | Unity override resolution (variant overrides base fields) |
| CSS media query / container query | Multiple rule sets | CSS specificity + media conditions |
| Feature-flag targeting | One flag has different values per segment | Rule engine (country / platform / cohort / % rollout) |
| Layered config | default + env + org + user override | Merge rules (last-wins / deep merge / explicit precedence) |
| Tailwind responsive variants | `text-sm md:text-base lg:text-lg` | Breakpoint match |

**Anti-pattern A — changed the default, forgot the overrides**

```text
❌ Changed the "submit" string in values/strings.xml.
❌ values-zh/strings.xml still holds the old copy; Chinese users see the old text.
❌ "I'm done" — because the Android Studio preview looks right.
```

**Anti-pattern B — added a variant that is never selected**

```text
❌ Added a drawable-xxxhdpi asset, but no project device triggers that bucket.
❌ Added a feature-flag variant whose condition never matches.
❌ In Unity, added a Prefab Variant but the spawner still points at the base prefab.
```

**Anti-pattern C — editor preview's resolution rules disagree with runtime**

```text
❌ Figma shows the "default" variant of a design token.
❌ Android Studio Layout preview defaults to values/, not values-zh/.
❌ Designers and engineers reviewed A; users see B.
```

**Anti-pattern D — lost track of multi-layer overrides**

```text
❌ Prefab Variant 3 overrides a field on Variant 2.
❌ Variant 2 overrides a field on the base.
❌ After changing the base, unclear which variants will follow and which retain their own overrides.
❌ The git diff only shows the base edit; nobody thinks to inspect downstream variants during review.
```

**Anti-pattern E — the resolution rule itself is not version-controlled**

```text
❌ i18n fallback chain hard-coded inside some utility function.
❌ Feature-flag rules edited by a PM in the SaaS console (no PR, no audit).
❌ After a rule change, a past bug report / screenshot can no longer be reproduced (because the rule changed).
```

**Repair strategies:**

1. **Register the rule, not the candidate files, in the SoT map.**
   - ❌ "`values/strings.xml`" → ✅ "Android resource-qualifier resolution; candidates under `values*/strings.xml`."
   - ❌ "feature-flag service" → ✅ "feature-flag targeting rules (DSL / rule file); candidate values in the flag console."

2. **Every variant change must state "under which conditions it takes effect."**
   - Android PR: state which locale / density / OS version the user must be on to see this variant.
   - Unity PR: state which scenes / spawners use this Prefab Variant.
   - Feature flag: state the rollout condition and the expected affected population.

3. **Visualize and make resolution rules inspectable.**
   - Provide a "give me a user / device / environment; tell me what value this field actually resolves to" query capability.
   - Local-side preview mechanisms to switch locale / density / flag, reducing the observation gap between editor and runtime.

4. **Compute blast radius for multi-layer overrides explicitly.**
   - Base-change PR descriptions must list "known variants / overrides that depend on this field."
   - Tooling: preview the variant chain, diff variant deltas.

### Pattern 10: Host-Lifecycle Truth

The authority of the source of truth is **bound to a lifecycle unilaterally controlled by a platform or host**. The host can be killed, suspended, unloaded, or cold-started without warning — the authority evaporates or must be reconstructed.

```
Process / Host alive (truth exists in memory / scope)
     │
     │  [platform decides: kill / suspend / unload / cold start]
     │
     ▼
Process gone (truth lost unless persisted elsewhere)
     │
     ▼
Host restart → either: rebuild from other SoT / restore from snapshot / start fresh
```

**Difference from pattern 7 (Temporal-Local):**

- Pattern 7 is "the network is unavailable, so I am temporarily authoritative" — the user / app controls.
- Pattern 10 is "the host can die at any moment, and my authority will be unilaterally destroyed" — the platform controls.

They can combine: an offline mobile app (pattern 7) whose in-memory state is then destroyed by Android process death (pattern 10).

**Typical scenarios:**

| Platform | Trigger that destroys the host | Mechanisms that typically survive |
|----------|-------------------------------|-----------------------------------|
| Android | System memory pressure → process death; config change → Activity recreate | `onSaveInstanceState` Bundle, `ViewModel` (survives config change but not process death), persisted storage |
| iOS | Background-timeout kill, memory pressure | State-restoration API, NSUserDefaults, Core Data |
| Browser | Tab suspended, bfcache, page-lifecycle freeze / discard | sessionStorage, localStorage, IndexedDB, Service Worker |
| Serverless | Cold start → new instance; instance recycling | External durable layer (DB / cache / queue) |
| Game engine | Scene unload / additive scene switch | DontDestroyOnLoad objects, ScriptableObject, save files |
| Mobile app in background | OS reclaims background apps | Persistent store, cloud sync |
| Container / k8s pod | Pod restart / rescheduling | External state (not container-local disk) |

**How to identify:** ask "if the host is killed right now, would the user / system notice? If yes, what information is lost?"

If the answer is "some in-memory state disappears; users see a blank / reset / error," that state is bound to host-lifecycle truth and needs an explicit decision on whether to promote it to a more durable SoT.

**Anti-pattern A — only tested in dev (which never triggers kills)**

```text
❌ Android app relies on a ViewModel to hold user input.
❌ Never triggered process death in testing.
❌ User returns after ~15 minutes in background → Activity recreated, ViewModel recreated, input gone.
```

**Anti-pattern B — stuffing everything into savedInstanceState / session**

```text
❌ Android: Bundle payload too large → TransactionTooLargeException.
❌ Web: sessionStorage fills with big objects → performance drop, quota exceeded.
❌ No clear decision on "what must persist vs. what can be rebuilt."
```

**Anti-pattern C — serverless function using a global variable as cache**

```text
❌ `const cache = new Map()` at module scope.
❌ Reused instance sees state from a previous request (privacy / data-leak risk).
❌ New cold-start instance has an empty cache; inconsistent behavior.
❌ Developer believes there is a cache; the actual hit rate depends on the platform's instance lifecycle.
```

**Anti-pattern D — assuming the host lives forever**

```text
❌ Mobile app does not save state; assumes users finish in one sitting.
❌ Browser SPA puts all state in memory; F5 / tab restore → blank.
❌ Background job expects to run to completion; the OS kills it before the timeout.
```

**Anti-pattern E — failing to distinguish "real restart" from "restoration restart"**

```text
❌ App cold start runs splash / onboarding.
❌ System-initiated restore also runs the same onboarding → users see onboarding every time they come back.
❌ Conversely: restoration takes the wrong branch and treats an old session as a new session.
```

**Repair strategies:**

1. **Explicitly classify every piece of state as memory-only / host-lifetime / persistent.**
   - Tag each state item by layer: valid only for this interaction (memory), valid while the host is alive (host-lifetime), must outlive the host (persistent).
   - Anything in the host-lifetime layer must have a persistence plan (when to snapshot, when to restore).

2. **Actively trigger host destruction in dev flows.**
   - Android: developer options → "don't keep activities", "background process limit = 0".
   - iOS: background-timeout testing.
   - Serverless: forced cold-start smoke test after each deploy.
   - Web: Chrome DevTools → Application → Storage → Clear; tab-discard simulation.

3. **Distinguish "legitimate rebuild path" from "true cold-start path."**
   - Provide an explicit restoration hook distinct from the cold-start flow.
   - Record a "started from scratch vs. restored from snapshot" flag for debugging.

4. **Discipline around host-bound caches.**
   - Serverless: module-scope caches must be documented as best-effort — no cross-instance guarantee.
   - Mobile: in-memory cache hit rate ≠ the user-visible performance improvement (restarts invalidate it).

5. **Register platform-policy-driven pieces as uncontrolled interfaces.**
   - Bridge to `docs/surfaces.md` (uncontrolled interface): an OS upgrade changes process-death rules and you can only keep up.
   - New OS versions typically tighten background-execution limits; subscribe to release notes.

> Side note: pattern 10 often combines with patterns 7 and 6. An offline mobile app (7) triggers a state transition (6), and the process is killed (10) before the transition syncs — you must solve "offline authority," "transition path," and "host destruction" together. A missed layer drops data or drops audit records.

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

**Repair:** bind documentation updates into the implementation PR checklist (see `docs/ci-cd-integration-hooks.md`).

### Anti-pattern 5: Translation keys drift from the source copy

i18n translation files evolve independently of the original copy.

```
❌ en.json:     "submit_button": "Send Order"
❌ Design file: "Place Order"
❌ fr.json:     "submit_button": "Envoyer la commande" (translated from the old "Send Order")
```

**Repair:** designate the design source as the source of truth for copy; translation files are consumers.

### Anti-pattern 6: Pipeline order treated as an implementation detail (not a contract)

Execution order of N stages / middleware / interceptors **is a contract** (see pattern 4a), but is often treated as "wherever the registration code happens to live."

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
- Treat order changes as breaking changes; run them through `docs/breaking-change-framework.md` for blast radius.
- Have each stage declare its relative constraints (`after: auth`, `before: compression`) so order becomes verifiable.
- Cross-reference `docs/cross-cutting-concerns.md` (build-time risk) for the pipeline-checks item.

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

## How to use this in Phase 1

One of the core activities of Phase 1 (Investigate) is building a source-of-truth map:

```markdown
## Source-of-Truth Map

| Information | Source of truth | Consumers | Sync mechanism | Desync risk |
|-------------|-----------------|-----------|----------------|-------------|
| Order status | `orders.status` (authoritative store) | API response / Admin UI / Analytics | API reads authoritative store directly | Low — single source |
| Product price | `products.price` (authoritative store) | Cache layer / Search index / UI | Cache flushed on write + short TTL | Medium — cache can go stale |
| User permissions | Auth service | Gateway / Frontend / Back office | Signed token (e.g. JWT) | High — token is not updated within its lifetime |
```

This map feeds Phase 2 (Plan), where it is used to decide:

- Which consumers need to be updated together with the change.
- Which sync mechanisms are at risk.
- What verification is needed to confirm consistency.
