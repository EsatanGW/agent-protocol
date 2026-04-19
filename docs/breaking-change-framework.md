# Breaking-Change Analysis Framework

> **English TL;DR**
> Structured analysis of "is this breaking? for whom? when? how to migrate?" — not by gut feel, by rubric. Defines a 5-level severity matrix: **L0 Additive** (consumer can ignore), **L1 Behavioral** (same shape, different result; switch-statements silently fall through), **L2 Structural** (schema changes; consumer must change code), **L3 Removal** (capability removed; requires deprecation timeline), **L4 Semantic Reversal** (same name, inverted meaning — most dangerous, silent-fail mode). Classifies consumers into six categories: internal sync, internal async, first-party client, third-party external, data downstream, human process — noting that *data downstream* and *human process* are the most commonly forgotten because they have no type system to complain. Prescribes three standard migration paths (gray rollout / parallel switch / deprecation cycle + rename-and-coexist for L4). Highlights the judgment trap: level is determined by **worst-case consumer**, not most-common consumer. Bridges into `rollback-asymmetry.md` for rollback modes that pair with each level.

> "Is this change breaking? For whom? When? How do we migrate?"
> Do not rely on instinct — rely on structured analysis.

---

## Why this document exists

Many teams understand "breaking change" as "will it break the build or the tests?" That is the **weakest possible definition**. A real breaking change includes:

- The build passes, but runtime behavior changed.
- Our own tests pass, but the consumer's tests fail.
- Synchronous consumers are fine, but offline consumers blow up when they come back online.
- Code consumers are fine, but human workflows (runbooks, support scripts) silently become invalid.

Recognizing breaking change is an extension of source-of-truth thinking: **change the truth, and any consumer's assumption about the truth may collapse.**

---

## Step 1: severity matrix

Every change is first placed into one of the following cells.

| Level | Name | Impact on consumers | Examples |
|-------|------|---------------------|----------|
| L0 | **Additive** | No consumer is affected; capability is simply added | New optional field, new endpoint, new enum value (assuming consumers have a fallback) |
| L1 | **Behavioral** | Same input produces a different output / side effect; schema unchanged | Sort-order change, default-value change, formula tweak, retry-policy change |
| L2 | **Structural** | Schema changed; consumer must change code to compile / parse | Field rename, type change, required→optional (or the reverse), response-shape change |
| L3 | **Removal** | An existing capability is removed; consumers lose something they depended on | Delete a field, delete an endpoint, delete an enum value, drop support for a client version |
| L4 | **Semantic reversal** | Same name, inverted meaning | `is_active` flips from "in use" to "awaiting activation"; `deleted_at` flips from "soft-deleted" to "scheduled-for-deletion" |

> **L4 is the most dangerous level.** The schema did not change, the API call did not change, the build passes, the tests pass — yet every consumer's interpretation of this field is now wrong.
> L4 changes must not be landed in place. They must use rename + coexistence + migration.

### Judgment traps in severity assessment

"I thought it was L0, it turned out to be L1+" is a recurring incident pattern:

| Looks like | Actually is | Why |
|------------|-------------|-----|
| New enum value (L0) | L1+ | A consumer has `switch (status)` without a default branch |
| `nullable` → `non-null` (L0 "stricter, surely better") | L2 | What happens to existing `null` rows? |
| More stable sort order (L0 "improvement") | L1 | A consumer depended on the previous order for dedup / pagination |
| Bug fix (L0 "it was wrong, now it's right") | L1 | A consumer hard-coded a workaround for the bug |
| Default timeout 30s → 10s (L0 "safer") | L1 | Slow consumers start failing systemically |

**Rule: when judging severity, reason about the worst-case consumer, not the common one.**

---

## Step 2: consumer classification

Not all consumers are equally important, and a migration strategy must treat the groups differently.

| Category | Can you force them to upgrade? | Handling strategy |
|----------|-------------------------------|-------------------|
| **Internal synchronous** (same monorepo / same deploy unit) | Yes | Change both sides in the same PR |
| **Internal asynchronous** (different service, different deploy cadence) | Yes but not at the same instant | Dual-write / dual-read transition; version negotiation |
| **First-party client** (in-house mobile app, desktop app) | Partially (forced update has limits) | API versioning, long-tail compatibility, declared minimum supported version |
| **Third-party consumer** (public API, SDK users, partners) | No | Announcement + deprecation timeline + dual-version coexistence |
| **Data downstream** (data warehouse, ETL, analytics) | Usually forgotten | Proactively notify the data team; schema registry; backward-compatible views |
| **Human workflow** (runbooks, support scripts, customer-support SOPs) | Usually unowned | Document updates, training, updated screenshots |

> **The most commonly forgotten categories are the last two.**
> Engineering consumers have a type system that complains. Data-team dashboards and support SOPs do not scream on their own.

---

## Step 3: migration-path decision tree

```
What is the level of this change?
│
├── L0 (Additive)
│   └── Merge directly; no migration path needed.
│       Still update docs, changelog, and SDK type definitions.
│
├── L1 (Behavioral)
│   └── Does any consumer depend on the old behavior?
│       ├── No  → Treat as L0.
│       └── Yes → Path A: gray-rollout + observation (see below).
│
├── L2 (Structural)
│   └── Which consumer category dominates?
│       ├── All internal sync          → Change both sides in the same PR.
│       ├── Has async / third-party    → Path B: coexistence + switch (see below).
│       └── Pure data downstream       → Schema migration + compatibility views.
│
├── L3 (Removal)
│   └── Path C: deprecation lifecycle (see below).
│
└── L4 (Semantic reversal)
    └── In-place modification is prohibited.
        Must go: new name + coexistence + old name kept + marked deprecated.
        Anything else is manufacturing an incident.
```

---

## The three standard migration paths

### Path A — Gray rollout + observation (for L1)

```
T0:  Feature flag wraps the new behavior; 0% rollout.
T1:  Ramp to 1%  → observe 24h (error rate, latency, business metric).
T2:  Ramp to 10% → observe 72h.
T3:  Ramp to 50% → observe 1 week.
T4:  100%.
T5:  Remove the flag (avoid flag permanence).
```

**Decision metric:** do not look only at error rate. Also look at whether *the same user / same entity produces a different decision* under the new behavior.

### Path B — Coexistence + switch (for L2)

```
T0:  New field / new endpoint shipped alongside the old.
T1:  Producer dual-writes both old and new fields.
T2:  Consumers migrate one by one to the new field.
T3:  Confirm all consumers have migrated (via logs / metrics).
T4:  Producer stops writing the old field.
T5:  Remove the old field / old endpoint.
```

**Most common failure point: T3.**

- "Nobody uses it" ≠ "nobody actually uses it."
- You need real telemetry proving zero reads. You cannot rely on `grep` alone.

### Path C — Deprecation lifecycle (for L3 and L4)

```
Stage 1 — Declare deprecated (do not delete yet)
  - Add @deprecated marker; warn icon in docs; changelog entry.
  - Provide "migrate to X" instructions.
  - Add telemetry to track which consumers still use it.

Stage 2 — Warning period
  - Runtime warning logs (non-breaking).
  - For public APIs: email / broadcast the deprecation.
  - Set a removal target date (≥ 2 minor versions is a reasonable baseline).

Stage 3 — Fault injection (optional but recommended)
  - Randomized latency or error injection on the old API.
  - Force remaining consumers to "feel the pain."
  - Must be disable-able (the last straw cannot be the one that takes production down).

Stage 4 — Removal
  - Confirm via telemetry that no consumer remains.
  - Remove at a major-version boundary.
  - Changelog entry marked BREAKING CHANGE.
```

**Core principles:**

- Do not delete quickly just because "nobody seems to use it short-term" — the forgotten consumers are still there.
- Do not defer forever, either — deprecated code accumulates as legacy debt.

---

## Step 4: version-strategy alignment

Different consumer types correspond to different version boundaries:

| Consumer type | Version carrier | When a breaking change can be removed |
|---------------|-----------------|---------------------------------------|
| Internal sync | git commit | Same PR is fine |
| Internal async service | API version header / endpoint path | Dual-version coexistence → observation → switchover |
| Mobile app | App version | Wait N versions (depending on install-base decay) |
| Public SDK | semver major bump | Only at a major version |
| Public REST API | URL path version (`/v2/`) | Only on a new path; the old path honors its declared support window |
| Public GraphQL | `@deprecated` directive + schema registry | Schema-driven; consumers track their own progress |

> **Common failure in hybrid strategies:** internal services change the API without bumping the version header; mobile force-upgrade logic ships without a "client version vs minimum-supported-backend version" negotiation.

---

## Step 5: hookup into the phase workflow

### Phase 0 (Clarify)

- Use the severity matrix to assign an initial level.
- List consumer categories and sizes.

### Phase 1 (Investigate)

- Fully populate the consumer table from step 2.
- Catch the "I thought L0, actually L1+" traps.
- Integrate with the SoT map from `source-of-truth-patterns.md`.

### Phase 2 (Plan)

- Choose the migration path (A / B / C).
- Specify entry and exit criteria for each stage.
- Cross-reference `rollback-asymmetry.md` to confirm rollback feasibility.

### Phase 3 (Test Plan)

- Have tests for both old and new behavior.
- For the coexistence period, have contract tests (both versions must serve simultaneously).

### Phase 5 (Review)

- The reviewer checks the change against this framework: level assignment, consumer coverage, migration path.
- Any L2+ change requires a migration-guide document.

### Phase 8 (Post-delivery)

- Back-fill observation results for each stage of the migration path.
- Recalibrate the estimate-vs-actual timeline for the real deprecation-removal window.

---

## Anti-pattern cheat sheet

| Anti-pattern | Why it's wrong | How to fix |
|--------------|----------------|------------|
| "If it compiles, it's not breaking" | Ignores L1 and L4 | Apply the severity matrix |
| "It's an internal API — no need to version" | Ignores deploy-cadence differences | At minimum, dual-write through a transition window |
| "Merge first, fix later" | L3 / L4 changes cannot be recalled once released | Run the deprecation lifecycle |
| "Nobody's using it — just delete" | Forgets data warehouse / support SOPs / third parties | Prove zero usage via telemetry |
| "We'll clean it all up in the next major" | Major bumps accumulate too many breaking changes at once | Stage deprecations; the major bump is only the cleanup |
| "A feature flag will do" | The flag has no sunset plan → becomes a permanent `if-else` | Path A must include the T5 flag-removal step |
| "Bug fixes don't count as breaking" | Some consumer is relying on that bug | Assess; bug-fix rollouts can still need gray-rollout |

---

## One-page cheat sheet

```
1. Severity:   L0 / L1 / L2 / L3 / L4?
2. Consumer:   internal sync / internal async / first-party /
               third-party / data downstream / human workflow?
3. Path:       A gray rollout / B coexistence switch / C deprecation lifecycle?
4. Version:    git / header / app version / semver major / URL path / schema directive?
5. Phase hook: Phase 0 initial level → Phase 2 path → Phase 3 dual tests →
               Phase 5 review → Phase 8 observation.
```
