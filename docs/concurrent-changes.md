# Concurrent Change Coordination

> **English TL;DR**
> Coordinates multiple in-flight tickets that touch overlapping surfaces / SoT / feature-flags. Main pipeline assumes "one change at a time" — this doc fills the gap when that assumption breaks. Added to Phase 0 (detect: grep open tickets for shared surface), Phase 2 (agree merge order; define *compatibility window*; manifest gets `co_required` / `depends_on` link to sibling manifest), Phase 5 (review checks both sibling branches simultaneously), Phase 6 (merge order enforced; feature-flag sequencing captured). Four coordination strategies: **sequencing** (hard dep: one merges, the other rebases), **branch isolation + merge-time conflict resolution** (independent branches joined at merge time), **joint design + split implementation** (shared plan, separate execution by different owners), **merge into one ticket** (atomicity beats coordination overhead for tightly-coupled changes). Most common failure: two tickets each pass their own review but together produce a desynced state — manifest `co_required` plus shared integration test is the fix.

When multiple people / multiple tickets touch overlapping surfaces simultaneously,
extra coordination is required to prevent desync.

---

## Why this document exists

The methodology's main pipeline assumes "one change at a time."
In practice, the following occurs regularly:

- Two tickets modifying the same table's schema at the same time.
- One person changing an API contract while another depends on that same contract.
- Feature-flag flip timing spanning the release schedules of multiple tickets.
- A shared component modified by two features in parallel.

Without coordination, each ticket walks through Phase 0→7 on its own and the conflict is discovered only after release.

---

## Which phase handles each piece

### Phase 0: detect conflict risk

Add one check in Phase 0 Clarify:

```markdown
## Concurrent change risk
- Are there other in-flight tickets touching the same surface right now?
- Is the same source of truth being modified by someone else in parallel?
- Will shared components (utils / shared component / base class) be modified simultaneously?
```

### Phase 1: build the conflict map

Mark concurrency risk in the Source of Truth Map:

```markdown
| Information | Source of Truth | Other ticket modifying it concurrently |
|-------------|-----------------|----------------------------------------|
| orders.status enum | DB migration | PROJ-1234 (also changing status) |
| Shared Button component | ComponentLib | PROJ-1235 (also changing Button) |
```

### Phase 2: coordination plan

Based on the conflict map, choose a strategy (see below).

---

## Coordination strategies

### Strategy 1: sequencing

**When:** two tickets modify the same source of truth and cannot be merged.

Steps:

1. Decide which ticket ships first.
2. The later ticket plans in Phase 2 with the earlier ticket's outcome as a precondition.
3. When the first ticket completes Phase 7, notify the second to update its plan.

**Risk:** if the first ticket slips, the second is blocked.

### Strategy 2: branch isolation + merge-time conflict resolution

**When:** two tickets modify different parts of the same file.

Steps:

1. Each develops on an independent branch.
2. The first to merge ships normally.
3. The second rebases before merging and resolves conflicts.
4. The later ticket's Phase 5 (Review) adds an extra check: is post-merge behavior still correct.

### Strategy 3: joint design + split implementation

**When:** two tickets modify different aspects of the same source of truth but are logically coupled.

Steps:

1. Phase 0–2 of the two tickets runs **jointly** (or at minimum, each reviews the other's plan).
2. Within the plan, the scope and interface of each side are explicitly marked.
3. Implementation is independent.
4. Phase 5 (Review) is cross-reviewed.

### Strategy 4: merge into one ticket

**When:** the two tickets overlap heavily; splitting is less efficient than merging.

Steps:

1. Merge into one ticket; run Phase 0→7 once.
2. Mark in the plan that this originated from two independent requirements.
3. If different people need to implement, split in Phase 4.

---

## Shared-component special handling

Shared components (base class, shared widget, utility function) have the broadest blast radius on modification.

### Rules

1. **Before modifying a shared component, list all consumers** — mandatory in Phase 1.
2. **Shared-component changes must not smuggle in feature logic** — split into two commits:
   - First commit: the general shared-component change.
   - Second commit: the feature logic.
3. **If a shared component is being modified by multiple tickets concurrently** — force Strategy 3 (joint design).

---

## Feature-flag concurrent management

Things to watch for when multiple feature flags coexist:

1. **Flags must not have implicit dependencies.**
   - ❌ When Flag A is on, assume Flag B is also on.
   - ✅ Every flag is independently controlled; combinations are tested in Phase 3.

2. **Flag lifecycles must be explicit.**

   ```markdown
   | Flag | Enable date | Full rollout | Removal date |
   |------|-------------|--------------|--------------|
   | NEW_SHOP_UI | 4/15 | 4/22 | 5/1 |
   | DIAMOND_PURCHASE | 4/18 | 4/25 | 5/5 |
   ```

3. **A flag that lingers unremoved is technical debt** — after Phase 8 observation closes, flag removal should become a follow-up ticket.

---

## Minimal version: when this document is not needed

- Team ≤ 2 people; verbal coordination suffices.
- The change's touched surfaces do not overlap with any other in-flight ticket.
- The change lives in an independent module with no shared dependencies.
