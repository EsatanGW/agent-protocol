# Team & Org-Scale Disciplines

> **English TL;DR**
> Scales the methodology from single-change discipline to multi-team, multi-quarter operation. Covers consumer registry, SoT inventory / contract catalog, deprecation queue, roadmap-level SoT, cross-team handoff protocols, and ownership boundaries — all without naming any specific tool or platform.

Single-change discipline (surface-first, SoT, evidence, manifest) is handled in other documents.
This document handles problems that only emerge in **multi-team, multi-quarter, long-running operations**:

- Who owns each SoT?
- How many deprecations are still queued?
- When two teams change the same contract, how do they coordinate?
- Where is the roadmap-level SoT?

With single-change discipline alone, the more a team ships, the more organizational debt accrues.

---

## Four organization-level assets

These four are "cross-change, cross-team, cross-quarter" sources of truth.
They are SoTs themselves — managed under SoT discipline.

### Asset 1: Consumer Registry

**What it is:** a list, per "outward contract / SoT / shared resource," of who is currently consuming it.

**Why it's needed:**

- When changing an SoT, you must know **all** consumers to assess breaking-change impact.
- The consumer classification in `breaking-change-framework.md` relies on this data to be applied at all.
- Without the registry, "who is using this?" always falls back to memory and grep.

**Minimum fields:**

- SoT identifier (API endpoint / schema name / event topic / shared library / config key / …).
- Consumer identifier (service name / team / external partner).
- Consumer category (internal sync / internal async / first-party client / third-party / data downstream / human process).
- Contact person or channel.
- Last interaction timestamp.

**When to update:**

- New consumer onboards → register proactively.
- Consumer sunset → deregister proactively.
- At least once per quarter: a "cold-data sweep" (entries with no interaction over a long window flagged for retirement).

**Automation:** the automation layer can statically scan code for some consumers (reference graph), but **data-downstream and human-process consumers must always be registered manually** — these are the classic sources of silent drop-offs.

### Asset 2: Contract Catalog

**What it is:** a centralized index of all internal and external contracts (APIs, events, shared schemas, config keys, shared types…).

**Why it's needed:**

- The manifest's `sot_map` must point into the catalog, not at scattered files.
- New contracts coming online and old ones going offline follow a uniform entry/exit point.
- Cross-team "am I allowed to use this?" has a single authoritative answer.

**Minimum fields:**

- Contract name + unique ID.
- Owner team.
- Stability tier (experimental / stable / deprecated / retired).
- Version history + breaking-change level per version.
- Link to the latest spec file (not a wiki prose description — a machine-readable spec).

**Key discipline:** any new outward contract must be registered in the catalog before it goes live. **A contract not in the catalog is treated as internal-private** and external consumption is refused.

### Asset 3: Deprecation Queue

**What it is:** the current set of items that "must migrate, have not yet finished migrating."

**Why it's needed:**

- Deprecations that nobody watches and have no deadline never finish.
- The **length** and **age** of the queue are key organizational-health signals.
- Without a visible queue, "technical debt" remains a feeling.

**Minimum fields:**

- The item being deprecated (corresponding catalog ID).
- Deprecation announcement date.
- Hard cutoff date (after this, forced retirement).
- Replacement (pointer to the replacement catalog ID).
- Remaining consumer list (pulled from registry).
- Migration owner.

**Key discipline:**

- Any L3/L4 breaking change entering the deprecation phase **simultaneously** enters the queue.
- Queue reviewed weekly; anything past its hard cutoff with remaining consumers escalates to an organization-level event, not a "we'll handle it next week."
- Hard cutoffs cannot be quietly extended (every extension requires a record + new date + escalation approval).

### Asset 4: Roadmap-Level SoT

**What it is:** the organization's single authoritative statement on "what we will and will not do in the next 1–4 quarters."

**Why it's needed:**

- Manifest-level "what does this change do" cannot answer "**should** this change be made at all?"
- Without a roadmap SoT, different teams end up working on overlapping / conflicting things simultaneously.
- When onboarding, "where are we heading" must have a single place to read.

**Minimum fields:**

- Time window (quarter / half / year).
- Strategic themes (described as capability or outcome, not as project name).
- Owner team per theme.
- An explicit "**not** doing" list (equally important).
- Delta from the previous roadmap version (what was added, what was dropped, why).

**Key discipline:**

- The roadmap is versioned; changes have release notes.
- Mid-cycle major changes require explicit escalation — no silent edits.
- The roadmap is the mother of SoTs — an individual manifest's `rationale` should map to a roadmap theme.

---

## Cross-team handoff protocols

When two teams collaborate on a change, discipline beyond a single manifest is required.

### Scenario 1: upstream / downstream teams change the same contract

**Typical:** platform team changes schema; product team consumes schema.

**Protocol:**

1. When the platform team's manifest reaches `phase: plan`, **notify** all consumers listed in the registry.
2. Wait ≥ N business days for an objection window (N depends on breaking level: L1 → 2 days, L2 → 5 days, L3 → ≥ 14 days, L4 → ≥ 30 days).
3. No objection → proceed to `phase: implement`. Objections go to an open discussion; the resolution is written back into the manifest `review_notes`.
4. After the platform team has delivered, each consumer owner in the registry receives a "you need to migrate" list.

### Scenario 2: peer teams modify a shared resource

**Typical:** two feature teams changing a shared component or service at the same time.

**Protocol:**

- The team that plans first locks a "reserved edit window" in the contract catalog.
- The second team waits for the first to deliver, or merges plans (see `concurrent-changes.md`).

### Scenario 3: large change spanning three or more teams

**Typical:** platform-level migration, data migration, account-system overhaul.

**Protocol:**

- Requires a **program-level manifest** (not a change manifest; one level up).
- Every team's change manifest points to the program manifest via a `part_of` field.
- The program manifest records: overall goal, team list, inter-team dependency graph, shared cutoff dates, rollback / forward-fix strategy.

---

## Ownership boundaries

### Principles

- **Every SoT must have an owner team** (not an individual — a team).
- **Owner cannot be empty**; if nobody picks it up, the SoT must be demoted to deprecated rather than left ownerless.
- **Owner transfer requires a handover ritual**: the departing owner finishes registry / catalog / queue updates before exiting.

### Owner's minimum obligations

- Answer consumer contract questions (SLA is self-defined but cannot be unbounded).
- Review consumer registry each quarter; confirm which consumers are still live.
- Lead the breaking-change process for this SoT.
- If abandoning (deprecation), go through the full deprecation-queue flow.

### Handling orphan SoTs

Regular sweep (recommended monthly):

- Any SoT whose owner is a team that has been dissolved?
- Any SoT with no changes and no ticket-filing activity for a year?

Finding an orphan → force-assign a new owner, or enter it into the deprecation queue.
**No "orphan but still alive" state exists.**

---

## Metrics

Organization-level health metrics — complement to the single-change metrics in `adoption-strategy.md`:

| Metric | Meaning | Suggested threshold |
|--------|---------|---------------------|
| Registry coverage | SoTs with consumer-registry data / total SoTs | > 80% green |
| Catalog completeness | Outward contracts catalogued / actual outward contracts | > 95% green |
| Deprecation-queue average age | Average days-in-queue across entries | < 90 days green |
| Hard-cutoff violation rate | Entries past cutoff with consumers / total deprecation entries | < 5% green |
| Orphan-SoT count | Current total of orphan SoTs | 0 green |
| Cross-team objection-window compliance | Changes that honored the window / changes that required it | > 90% green |

These metrics must also pair with counter-metrics — see the counter-metrics section of `adoption-strategy.md`.

---

## Anti-patterns

- **Wiki-as-registry:** consumer lists scattered across manually maintained wiki pages; guaranteed to go stale.
- **Catalog as report:** a catalog exists, but there is no enforcement of "not in catalog = can't be used."
- **Indefinite deprecation:** extend once, twice, forever.
- **Orphan tolerance:** "nobody owns it, but it still runs, so leave it" → the root of the next incident.
- **Roadmap as PR material:** outward narrative differs from internal direction; change decisions have no basis.
- **Cross-team protocol by personal favor:** priority by who-knows-whom, not by protocol — new hires are permanently blocked.

---

## Rollout order

**Do not stand everything up at once.** Mirrors the three-stage approach in `adoption-strategy.md`:

### Stage A: stand up Consumer Registry first (4–8 weeks)

- Start with the SoTs that cause the most incidents.
- Register only "internal sync + data downstream + human process" categories first.

### Stage B: stand up Contract Catalog next (starting three months after Stage A)

- Start with externally public APIs; gradually bring in internal contracts.
- In parallel, enforce "no catalog entry → no new contract goes live."

### Stage C: finally stand up Deprecation Queue + Roadmap SoT

- The queue becomes naturally necessary at the first L3/L4 change.
- The roadmap SoT becomes naturally necessary after the first "two teams did overlapping work" incident.

Once all three are up, organization-level discipline closes the loop.

---

## Relationship to other documents

- `adoption-strategy.md` — team-level rollout strategy (this document is organization-level).
- `breaking-change-framework.md` — consumer classification in this document depends on that framework.
- `concurrent-changes.md` — coordination of parallel changes within a batch (this document handles cross-batch).
- `change-decomposition.md` — when a large change is split into multiple manifests, organization-level discipline tracks them.
- `automation-contract.md` — registry / catalog / queue automation can build on that contract.
