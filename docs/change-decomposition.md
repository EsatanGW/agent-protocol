# Change Decomposition

> **English TL;DR**
> Answers: "when should one request become multiple changes, and when should many tickets become one?" Gives six natural fracture lines (SoT boundary, surface cadence differs, consumer cohort separation, asymmetric risk level, different reversibility, delivery-sequencing constraint), four merge signals (tightly-coupled atomicity, shared evidence, split would fabricate a scheduling dependency, changes are too small), a dependency-graph model (supersedes / depends_on / blocks / co_required), and anti-patterns. Entirely tool-agnostic.

"One change = one manifest" is a principle of this methodology,
but it does not answer: **what counts as "one change"?** How many manifests should a requirement become?

This document is the splitting / merging decision discipline.

---

## Why this document exists

Without an explicit splitting standard, two failure modes appear:

**Over-splitting:**

- A single requirement becomes 8 tickets, each running its own manifest.
- The real risk is "the combined side effect of all 8," and nobody is looking at the aggregate.
- Reviewer fatigue; every ticket gets rubber-stamped.

**Over-merging:**

- Three unrelated requirements are crammed into one manifest.
- At rollback time, touching one forces the others to move; nothing can be independently reverted.
- The overall breaking-change level is forced to the highest item; small changes get dragged along.

The real decision is: **where should the seam be?**

---

## Natural fracture lines

These are recommended split points. If the change crosses one of these, it usually becomes two manifests.

### Fracture line 1: SoT boundary

If the requirement changes **two independent sources of truth**, split by default.
Reason: every manifest has one primary SoT; crossing SoTs makes "the origin of change" fuzzy.

**Exception: do not split** when two SoTs are dual representations of the same concept (e.g. schema + codegen output) — that falls under SoT pattern 8 (Dual-Representation) and counts as one.

### Fracture line 2: surface cadence differs

If the requirement touches **multiple surfaces** but they **release on different cadences**, split.
Examples:

- Backend API (ships weekly) + long-lived clients (update every few months) → split.
- System interface (immediate) + support SOP / docs (finalized next week) → split.

Reason: different rollback modes, different verification timing, different responsible party.

### Fracture line 3: consumer cohort separation

If the requirement affects **two different consumer cohorts**, split.
Example: a single change affects internal services and an external-partner SDK → split into:

- Internal change (ships quickly, consumers update in lockstep).
- External change (has a deprecation timeline and an announcement window).

### Fracture line 4: asymmetric risk level

If one part of the requirement is **low risk** and another is **high risk**, split.
Example:

- Add an optional field (L0).
- + Incidentally reinterpret an enum's meaning (L4).

→ Split. L4 requires deprecation + coexistence; L0 should not be forced along for the ride.

### Fracture line 5: different reversibility

If one part of the requirement is **reversible** and another is **irreversible**, split.
Example:

- Frontend copy change (reversible).
- + Background-triggered push notification (irreversible side effect).

→ Split so the irreversible part goes through rollback-mode-3 discipline on its own.

### Fracture line 6: delivery-sequencing constraint

If one part **must ship first** and another **must ship after**, split.
Typical pattern:

- First ship the "both old and new accepted" compatibility window.
- Then ship "switch default to the new version."
- Finally ship "remove the old version."

That is three manifests, in order, with `depends_on` / `blocks` edges.

---

## Merge signals

Conversely, **do not split** when any of these signals is present:

### Merge signal 1: tightly-coupled atomicity

If two changes **cannot be rolled back separately** (one applied without the other would break the system), force them into a single manifest.
Example: schema changed but consumer code did not, or vice versa.

### Merge signal 2: shared evidence

If the verification fully overlaps (same test suite, same screenshot, same metric observation), splitting only duplicates evidence. Merge.

### Merge signal 3: splitting would fabricate a scheduling dependency

If splitting would force "Manifest 2 must wait until Manifest 1 is delivered" despite the two being genuinely parallelizable, the split is creating a serialization penalty. Merge.

### Merge signal 4: changes are too small

Several similar small changes with diff < 30 lines, single surface, single consumer — merging them as one manifest with enumerated items is clearer than splitting into five.

---

## Dependency-graph model

After splitting, the relationships between changes must be describable formally.
The following four relationships are declarable in the manifest (recommended schema-extension fields; see below):

### Relation 1: `supersedes` (replaces)

**Semantics:** A replaces B; B's decisions are no longer in force.
**Context:** the requirement itself has been redefined; the premise of the original manifest is wrong.
**Effect:** B is marked `retired`, not deleted.
(The schema already has this field.)

### Relation 2: `depends_on` (predecessor)

**Semantics:** A can be `implement`ed only after B is `delivered`.
**Context:** A requires B's completed schema / API / data migration as a precondition.
**Effect:** CI can verify B is actually `delivered`, otherwise block A from progressing.

### Relation 3: `blocks` (successor)

**Semantics:** B cannot start until A is `delivered`.
**Context:** A and B modify the same SoT and must be serialized to avoid concurrent conflict.
**Effect:** Semantically the dual of `depends_on` (B depends_on A ⇔ A blocks B); expressed from the initiator's viewpoint.

### Relation 4: `co_required` (jointly required)

**Semantics:** A and B must ship together; shipping only one is not allowed.
**Context:** tightly coupled across surfaces (e.g. API and frontend must be swapped together) but team boundaries prevented merging into one manifest.
**Effect:** the CI release gate checks that both manifests are simultaneously `ready_to_deliver`.

### Graph legality

Under these four relationships, the dependency graph must be:

- Acyclic (except for the `supersedes` chain — its cycle is resolved along the time axis).
- Deadlock-free (A depends_on B simultaneously with B depends_on A is not allowed).
- Topologically sortable (at least one legal ship sequence exists).

The automation layer (`automation-contract.md` tier 2) checks all three.

---

## Decision flow

When receiving a requirement, the splitting decision:

```
Step 1: Identify SoTs
   ├─ One SoT   → default to one manifest; proceed to Step 2.
   └─ Multiple  → default to multiple manifests; proceed to Step 2.
       └─ Exception: dual-representation → merge back to one.

Step 2: Identify surface cadence
   ├─ Same cadence    → keep current split.
   └─ Different       → split further.

Step 3: Identify consumer cohorts
   ├─ Same cohort     → keep current split.
   └─ Different       → split further.

Step 4: Identify risk / reversibility asymmetry
   ├─ Symmetric       → keep.
   └─ Asymmetric      → separate out the asymmetric portion.

Step 5: Check merge signals
   ├─ Any merge signal present → merge the relevant parts back.
   └─ None                     → splitting is final.

Step 6: Draw the dependency graph
   └─ Declare supersedes / depends_on / blocks / co_required edges.
```

---

## Worked scenario: a feature split into five manifests

Requirement: "Add an 'expiry reminder' feature for all paying users."

**Naive approach (one manifest):**

- Modify schema (new field `reminder_settings`).
- New API (read/write reminder settings).
- New frontend settings page.
- New scheduled job (scan for expiries, send notifications).
- Notification templates / support FAQ.

Problems with the single-manifest approach:

- Schema change is a structural change on the information surface (L2).
- Notification dispatch is an irreversible side effect (rollback mode 3).
- Support FAQ is on a different cadence (next week).
- Frontend and backend have different deploy cadences.

**It should be split into:**

```
M1: 2026-04-20-reminder-schema          (L2, rollback 1)
M2: 2026-04-20-reminder-api             (L0 additive, depends_on M1)
M3: 2026-04-20-reminder-frontend        (L0, depends_on M2)
M4: 2026-04-20-reminder-job             (L1 behavioral, rollback 3,
                                         depends_on M1; blocks sending until
                                         M2+M3 are delivered)
M5: 2026-04-27-reminder-support-docs    (operational, low risk)
```

After splitting:

- Each manifest can be rolled back independently (except M4, constrained by irreversible side effect).
- M4 gets the chance to actually send the first notification only after M2/M3 are verified.
- M5 can slip by a week without blocking the others.

---

## Anti-patterns

- **Treating "Epic" as manifest:** a whole quarter's big requirement stuffed into one manifest, losing granularity.
- **Splitting to inflate ticket count:** slicing into 8 tickets purely for the velocity dashboard; every ticket is trivial.
- **Split without a dependency graph:** five manifests each going their own way; merge time reveals ordering collisions.
- **Merged but hidden:** half of the work hidden from `title` and `surfaces_touched` so reviewers never see it.
- **AI merges / splits on its own:** the AI "incidentally" merges another manifest mid-implementation — this violates scope discipline; it must stop and escalate.

---

## Relationship to other documents

- `change-manifest-spec.md` — recommended to extend with `depends_on`, `blocks`, `co_required`, `supersedes` fields.
- `breaking-change-framework.md` — basis for splitting on risk asymmetry.
- `rollback-asymmetry.md` — basis for splitting on reversibility asymmetry.
- `concurrent-changes.md` — coordination when multiple manifests run in parallel (this document decides *how* to split; that one decides *how to coordinate* after splitting).
- `team-org-disciplines.md` — cross-team handoff and dependency-graph management after splitting.
- `automation-contract.md` tier 2 — automated checking of dependency-graph legality.
