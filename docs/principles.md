# First Principles

> **English TL;DR**
> The 11 non-negotiable rules from which the rest of this methodology is derived. Not preferences — consequences. Each rule answers "what fails if we don't hold this?" Key claims: manage change not code; surfaces not layers; SoT before consumers; verification is designed not retrofitted; completion ≠ merge; asymmetries (rollback, upgrade pace, layering) must be faced; the methodology must be able to collapse to zero when not needed; it must be measurable; AI is a co-author, not a tool.

This document answers a single question: **why does this methodology look the way it does?**

Other documents tell you *how* to do things; this one tells you *why* those requirements are not preferences but consequences. If you disagree with any one of these principles, your use of the methodology will degrade into ceremony.

---

## Background assumptions

The methodology assumes your working environment satisfies at least two of the following:

1. The change will be perceived by **at least one non-implementer** (end user, operator, partner team, your future self).
2. The system's **lifetime exceeds a single task cycle** — the traces this change leaves will be inherited by someone later.
3. The work is **recorded digitally** — at least one of commits, tickets, docs, or logs is searchable after the fact.

When none of these hold (e.g. a one-off prototype, a completely personal throwaway script), this methodology will feel heavy. **That is a design choice, not a defect.**

> When the methodology does not apply: `docs/onboarding/when-not-to-use-this.md`.

---

## Principle 1: Change is a first-class entity; code is a trace

**Derivation:** If you manage only code, you lose:

- Why it was done (intent)
- Who it affects (impact)
- How you will prove it is correct (verification)
- How you will investigate it when it breaks (diagnosability)
- What the next person needs to read (handoff)

Therefore: any state described as "done but no context left behind" is, from the system's point of view, unfinished.

> See also: `product-engineering-operating-system.md` §1.

---

## Principle 2: Slice the world by surface, not by technical layer

**Derivation:**

- Slicing by layer (frontend / backend / database) makes each person responsible only for their own layer.
- Cross-layer seams (contracts, enums, validation, docs) end up with no owner, which turns them into desync hotspots by default.
- End users, partners, and operators do not care about your layering — they perceive the system through their own surfaces.

Therefore: every change begins by identifying the affected surfaces, not by identifying which layer owns the code.

> See also: `surfaces.md`, `system-change-perspective.md`.

---

## Principle 3: Find the source of truth before you define consumers

**Derivation:**

- Most bugs are not "the code is wrong" — they are "a consumer's assumption about SoT became invalid."
- A system whose SoT cannot be located cannot define what "correct" means.
- Dual-writes without coordination will desync at some point; it is a question of when, not whether.

Therefore: the core action of Phase 1 is to build a source-of-truth map, not to write code.

> See also: `source-of-truth-patterns.md`.

---

## Principle 4: Consumers are not only code

**Derivation:**

- Engineering consumers have a type system that complains at build time; data consumers, documentation consumers, and human-workflow consumers do not.
- The most commonly forgotten consumers are in those latter categories (data warehouse, support SOP, compliance audit).
- Forgetting to notify one of them is a recurring root cause of incidents.

Therefore: consumer classification must explicitly include non-code consumers.

> See also: `breaking-change-framework.md` §2.

---

## Principle 5: Verification and evidence are designed, not retrofitted

**Derivation:**

- If you only start thinking about "how will I verify this?" at the implementation phase, you will almost always collapse it to "run it and see if it looks right."
- Without verification defined up-front, there is no definition of "done" that can be challenged by anyone else.
- Evidence is the sole artifact that future operations, rollback, audit, and handoff can lean on.

Therefore: Phase 2 / Phase 3 must decide the form of verification and evidence before Phase 4 begins.

> See also: `cross-cutting-concerns.md`, Phase 3 minimums.

---

## Principle 6: "Done" is not merge; it is the convergence of the change narrative

**Derivation:**

- Merge means only that the code landed. It does not mean:
  - Consumers have been synced.
  - Verification has been executed.
  - Operational information is in place.
  - The handoff narrative is legible to the next person.
- Defining "done" as "merged" turns residual work into **unowned debt**.

Therefore: the minimum definition of done is surface coverage ✅ + evidence ✅ + handoff narrative ✅.

> See also: [`situational-disciplines.md §Operational surface`](situational-disciplines.md#operational-surface), Phase 6–7.

---

## Principle 7: Asymmetries must be faced, not flattened

The methodology acknowledges three asymmetries and refuses to pretend they are symmetric:

### 7a. Rollback asymmetry

A web backend rollback takes seconds; a mobile client rollback takes days with a long tail; real-world side effects cannot be rolled back at all. **Treating every change as "reversible" is an incident factory.**

### 7b. Consumer upgrade-pace asymmetry

Internal synchronous consumers can be updated in the same PR; third-party consumers upgrade on a cadence you do not control. **Using one migration strategy for every consumer is an incident factory.**

### 7c. Layering-of-responsibility asymmetry

Error messages become more concrete as they descend surfaces and more abstract as they rise. Middle layers must not leak raw SQL errors into the UI. **Each layer has its own responsibility — it cannot be delegated downward nor usurped upward.**

> See also: `rollback-asymmetry.md`, `breaking-change-framework.md` §2, `cross-cutting-concerns.md` (error handling).

---

## Principle 8: The methodology itself must collapse to zero

**Derivation:**

- A methodology that cannot recognize "this does not apply here" turns into ceremony.
- Any methodology with sufficiently low adoption will eventually be routed around.
- Over-use and under-use are **both** failure modes.

Therefore: there must be four explicit modes — **Zero-ceremony, Three-line delivery, Lean, Full** — and the selection criterion for each must be **objective, recognizable conditions** (surface count, consumer count, reversibility, public-behavior impact), never "it feels like we need it." Canonical mode definitions: `glossary.md §Execution mode`. Decision tree: `skills/engineering-workflow/references/mode-decision-tree.md`.

> See also: `onboarding/when-not-to-use-this.md`.

---

## Principle 9: Tool-agnostic, capability-specific

**Derivation:**

- A methodology tied to specific tools expires when those tools are displaced.
- Teams use radically different tool stacks (different runtimes, different AI agents, different CI platforms).
- Capability categories (file read, code search, shell execution, browser interaction, sub-agent delegation) are stable; specific tool names are not.

Therefore: all normative content refers to **capability categories**, and the mapping to specific tools is deferred to the per-project stack bridge.

> See also: `stack-bridge-template.md`, `skills/engineering-workflow/SKILL.md`.

---

## Principle 10: The methodology must be measurable, otherwise it cannot be improved

**Derivation:**

- Without a baseline, an adoption cannot be judged effective or ineffective.
- Without exit criteria, a methodology becomes an unchallengeable belief.
- Anti-metrics (wrong directions that the methodology would optimize for if left unchecked) matter as much as positive metrics.

Therefore: adoption must come with a baseline, an exit mechanism, and anti-metric monitoring.

> See also: `adoption-strategy.md`.

---

## Principle 11: An AI executor is a co-owner, not a tool

**Derivation:**

- An AI agent in this workflow is not "an automation tool"; it is a co-author.
- A co-author is bound by the same obligations as a human: mark surfaces, leave evidence, report uncertainty honestly, do not pretend an implementation exists.
- A co-author also has weaknesses a human does not share: limited session memory, a tendency to rationalize narratives, and no native perception of real-world side effects.
- The behavior contract for an AI therefore **cannot be identical to the human contract** — additional constraints are required.

Therefore: AI executors need a dedicated operating contract that specifies how uncertainty is reported, what qualifies as acceptable evidence, when to escalate, when to stop, and how to carry context across sessions.

> See also: `ai-operating-contract.md`.

---

## Methodology self-check

When reviewing a plan or report you produced yourself, if any of the following cannot be answered, at least one principle has been bypassed — go back and fill it in:

- Which surfaces are affected?
- Where is the SoT? Who are the consumers?
- How will verification run? Where is evidence stored?
- Is the change reversible? If something goes wrong, how do we investigate?
- What does the next person need to read?

---

## Usage rules

1. This document is the *self-justification* of the methodology, not a checklist.
2. Before adding a new rule to another document, ask: does it derive from one of these principles?
3. Before relaxing any rule, ask: is the principle it derives from genuinely inapplicable to your situation?
4. When principles conflict, record the trade-off. An unrecorded trade-off is an unresolved conflict.
