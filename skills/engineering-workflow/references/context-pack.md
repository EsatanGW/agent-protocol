# Context Pack

A compact, pre-distilled bundle of change-scoped context that the canonical role produces once and shares across every sub-agent spawned in a fan-out.

**Why this document exists.** Fan-out sub-agents that each re-read the full `docs/` tree defeat their own economics — the time saved by parallelizing is given back (and then some) to redundant per-sub-agent context loading. The context pack is the mechanism that keeps fan-out net-positive: one pre-distillation pass by the canonical role, then every sub-agent consumes the same pack.

**Scope.** Full mode only, immediately before a parallelization fan-out per `parallelization-patterns.md`. A context pack in Lean or Zero-ceremony mode is ceremony, not optimization.

---

## Purpose

A fan-out of *N* sub-agents without a context pack pays *N × context_load* in per-sub-agent reading cost. With a context pack, it pays *1 × context_pack_creation* up front, then *N × small_pack_read*. When the pack is genuinely pre-distilled, this is strongly net-positive for N ≥ 2; when it is lazily copied from the full source, it is net-negative.

The pack exists to save reading cost **and** to increase sub-agent consistency — every sub-agent starts from the same definition of SoT, the same surface list, the same terminology. Two investigators classifying the same enum as different SoT patterns is a fan-in problem that the context pack prevents upstream.

---

## When to produce one

Produce a context pack when **all** of the following hold:

- The current phase is about to fan out per `parallelization-patterns.md` Pattern A or B.
- The fan-out will spawn two or more sub-agents.
- At least one of the sub-agents would otherwise need to read `docs/surfaces.md`, `docs/source-of-truth-patterns.md`, `docs/cross-cutting-concerns.md`, or equivalent methodology artifacts to complete its scope.

Do **not** produce a context pack when:

- The canonical role is working alone (no fan-out).
- Only one sub-agent is being spawned (one Pattern 1/2/3/4 invocation from `role-composition-patterns.md`) — a direct Task Prompt is cheaper than a pack.
- The change is Lean or Zero-ceremony.

---

## Where it lives

**Session-scoped working space**, per `docs/phase-gate-discipline.md` Rule 5a. Not a canonical artifact. Not persisted beyond the change. Not cited in `evidence_plan`. Not referenced from the Change Manifest directly — the manifest only records the `parallel_groups` entry that consumed the pack.

Runtime-specific working-space conventions live in `docs/bridges/*`. The pack is just another session-scoped draft artifact and follows those conventions.

---

## What goes in

The pack is pre-distilled **for this change**, not a general methodology dump. Typical contents:

1. **Change identity (one line).** change_id, title, phase, which fan-out pattern is about to execute.
2. **SoT candidates (from the Planner's prior Phase 0/1 work).** Named symbols + pattern classification (from `docs/source-of-truth-patterns.md` 10 patterns + 4a). Pre-identified so sub-agents do not each re-classify.
3. **Surfaces in scope.** Which of the four (or extension) surfaces are relevant to the fan-out and which sub-agent is responsible for which. No sub-agent should be able to read the pack and be unsure of its own scope.
4. **Terminology snapshot.** Only the glossary terms actually in play for this change, copied into the pack so sub-agents do not re-fetch `docs/glossary.md`. Typically under 10 terms.
5. **Hard boundaries.** What each sub-agent must **not** do — e.g. "*do not cross into surface Y*", "*return findings only, do not write manifest fields*", "*do not spawn further sub-agents*". Explicit boundaries compensate for the sub-agent's limited view.
6. **Return slot shape.** The structured shape the sub-agent's findings must conform to. Typically a small YAML stub (3-8 fields). Pre-declaring the shape is what makes fan-in mechanical.

A pack missing any of items 3, 5, or 6 is under-specified and will produce inconsistent sub-agent returns.

---

## What does NOT go in

- **Full document copies.** The pack is a distillation; if it contains `docs/source-of-truth-patterns.md` verbatim, it is not a pack, it is a re-read.
- **The Change Manifest itself.** Sub-agents do not write manifest fields and should not see the full manifest. Include only the fields a sub-agent needs to do its bounded work.
- **Implementation diffs / evidence artifacts.** Fan-out is for investigation and audit, not for sub-agent-driven edits.
- **Cross-role context.** A Planner's pack for Pattern A investigators should not include Reviewer concerns; a Reviewer's pack for Pattern B audits should not include Planner-phase drafts. Cross-role bleed creates anti-collusion risk.
- **Credentials, secrets, or user-private data.** The pack may be logged by the runtime; treat it as session-scoped but non-confidential.

---

## Size budget

The pack is deliberately small — typically **under 400 words**, almost never over 800. If the pack is larger than 800 words, one of two things is happening:

- The decomposition is wrong — the sub-agents are being asked to do too much individually. Reduce scope per sub-agent.
- The pack is leaking full document copies — re-distill.

The budget is symmetric with the handoff-prompt budget in `skills/engineering-workflow/templates/handoff-prompt-template.md`. Both budgets exist for the same reason: dense pointers beat verbose re-explanation.

---

## Lifecycle

1. **Creation.** Canonical role produces the pack in working space, immediately before the fan-out batch. The pack is never edited after the first sub-agent receives it — changing it mid-fan-out produces inconsistent sub-agent contexts.
2. **Distribution.** Each fan-out sub-agent receives the pack as part of its Task Prompt (or equivalent spawn-time context).
3. **Consumption.** Sub-agents read the pack once, apply the boundaries, produce findings into the declared return slot, return.
4. **Retention.** After fan-in, the pack is retained in working space for the Reviewer's audit trail but is not copied into canonical artifacts. It is discarded at the end of the change.

A pack used by a fan-out must survive long enough for the Reviewer to read it post-hoc if the `parallel_groups` audit requires reproduction. Working space conventions in `docs/bridges/*` cover this retention.

---

## Relationship to other artifacts

- **Change Manifest** — the state snapshot for the change. The pack is **not** part of the manifest and **not** a substitute for it. A sub-agent needing to read manifest fields it was not given in the pack has scope creep; return to the canonical role.
- **Handoff prompt** (`skills/engineering-workflow/templates/handoff-prompt-template.md`) — the compact pointer block sent to a **next session**. The pack is sent to **sub-agents within the same session**. Same budget shape, different recipient.
- **CCKN** (`docs/cross-change-knowledge.md`) — topical knowledge that spans changes. CCKNs may be **referenced** by a pack (e.g. *"this library's rate limit quirk — see CCKN {id}"*), but the CCKN itself is not part of the pack.
- **`parallel_groups` manifest field** — records that a fan-out consumed a pack; does not include the pack's contents.

---

## Template

See `skills/engineering-workflow/templates/context-pack-template.md` for a fillable skeleton. The template enforces the items-3/5/6 completeness rule structurally.

---

## Anti-patterns

| Anti-pattern | What breaks |
|---|---|
| Pack larger than ~800 words | Either over-scoped per sub-agent or leaking full documents; re-distill |
| Pack edited after the first sub-agent received it | Inconsistent sub-agent contexts; fan-in will show undiagnosable contradictions |
| Pack contains the full Change Manifest | Sub-agent overreach enabled; fan-out is now effectively self-assigning manifest-writing work |
| Pack missing return-slot shape | Free-form sub-agent returns; fan-in becomes free-form synthesis; cross-cutting gap check gets skipped |
| Pack re-used across phases (Planner's pack reused by Reviewer) | Cross-role context bleed; anti-collusion risk |
| Pack cited as evidence | Category error — the pack is a working-space optimization, not a verification artifact |
