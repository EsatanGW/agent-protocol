# Glossary

> **English TL;DR**
> Canonical definitions for every term used in this methodology: change, surface, source of truth, consumer, contract, evidence, surface coverage, handoff, Lean/Full mode, breaking change levels (L0–L4), rollback modes (1 reversible / 2 forward-fix / 3 compensation), and anti-pattern vocabulary. If another document and this one disagree, fix this one first.

> This file is the authoritative definition of every term used in the repo. Other documents must defer to the definitions here. When a definition is ambiguous, fix it here first rather than redefining it elsewhere.

The methodology deliberately uses a stable vocabulary. Once the vocabulary is stable, the team can discuss changes in a common language instead of realigning on terms in every conversation.

---

## Core terms

### Change

An intentional modification of the system. A change may alter behavior, structure, data, contracts, documentation, or operational state. A code diff is only one of the traces it leaves.

> See: `docs/product-engineering-operating-system.md` §1.

### Surface

The dimension through which a change is perceived. Not a technical layer (frontend / backend / DB) but "who sees the effect of this change, and how."

Four core surfaces: **user surface, system-interface surface, information surface, operational surface.** Domains may declare extension surfaces when needed.

> Canonical definition: `docs/surfaces.md`.

### Source of Truth (SoT)

The **sole authoritative origin** of a given piece of information. When multiple copies exist in the system, this is the copy that wins in a conflict.

Properties of an SoT:

- Every other copy is derived from it.
- Changes must begin there; consumers re-sync afterward.
- In a disagreement, the SoT is right by definition.

> Identification patterns, anti-patterns, and repair strategies: `docs/source-of-truth-patterns.md`.

### Consumer

Any party that depends on a source of truth. A consumer can be:

- Code (another service, a UI binding, an ETL job).
- Data (a downstream warehouse, search index, cache).
- A human workflow (customer-support SOP, on-call runbook, compliance audit).
- An external party (partners, platforms, users of a third-party SDK).

**Consumers are not only code** — the non-code categories are the most commonly forgotten.

### Contract

An agreement between two entities about **shape, semantics, and timing**. It can be a schema, an API spec, an event payload, a shared type, or a documented behavioral commitment.

A contract is itself typically a source of truth.

### Evidence

A reproducible artifact that, **after leaving this conversation / session**, can still be cited to answer: *did this change actually take effect?*

Forms of evidence are not limited to one kind — test logs, screenshots, response payloads, query results, metric snapshots, log excerpts, generated-doc diffs, etc. At minimum, evidence must be:

- **Locatable** — has a path or link.
- **Understandable** — carries enough inline context that it can be read without relying on the original conversation.
- **Traceable** — has a timestamp, version, or run id.

### Surface coverage

Whether every surface affected by this change has been analyzed, planned, implemented, verified, and delivered. Coverage does not mean "every surface had work done on it"; it means "every surface was *checked* to decide whether work was needed."

### Handoff

Transferring the state, decisions, evidence, and residual risk of this change to the next operator, successor, or your future self. **The quality of the handoff is the cost of returning to this situation later.**

A handoff **prompt** (the text the outgoing session sends to the incoming session) is not the same as the Change Manifest. The prompt is a compact pointer block (soft cap: 400 words; hard cap: 800) whose job is to point the incoming session at the Manifest. Handoff content — decisions made, escalations open, evidence collected — belongs in the Manifest; the prompt only references it. See `skills/engineering-workflow/templates/handoff-prompt-template.md` for the format.

---

## Process terms

### Lean / Full mode

Two execution-rigor gears. Lean is the minimum skeleton; Full is the full trace. The selection criterion is not "importance" but surface count, consumer count, reversibility, and handoff needs.

> Decision guidance: `docs/onboarding/when-not-to-use-this.md`, `references/mode-decision-tree.md`.

### Phase 0–8

The nine phases of Full mode: Clarify / Investigate / Plan / Test Plan / Implement / Review / Sign-off / Deliver / Post-delivery Observation. They form a **sequential narrative**, not a checklist that must be executed cell by cell every time.

### Discovery loop

The fallback mechanism for discovering that scope has grown during implementation. Distinct from the fix-retest loop (fix a bug, rerun the tests): a discovery loop goes **back to an earlier phase**, while a fix-retest loop stays inside the same phase.

### Resume mode

One of five declared modes — **Lazy / Targeted / Role-scoped / Full / Minimal** — that the incoming session names as its first action when resuming after a session break. The mode determines what must be read before work continues (Lazy = Manifest only; Targeted = Manifest + the entering phase's input artifacts; Role-scoped = Manifest + upstream role's single output; Full = disaster-recovery fallback requiring explicit justification; Minimal = Lean-spec only).

Declaring a mode is mandatory to prevent the session-handoff context-collapse failure pattern: a verbose handoff prompt + a sequential re-read of every referenced artifact exhausts the new session's context before real work begins. Canonical definition: `skills/engineering-workflow/references/resumption-protocol.md`.

### State snapshot

A single document sufficient to let a new session resume work without reading any other artifact. The Change Manifest plays this role for a change in Full mode; the Lean-spec note plays it for Lean mode. The state-snapshot discipline (see `docs/change-manifest-spec.md` §State-snapshot discipline) holds that if the snapshot is insufficient to resume from, it is **incomplete** — fix the snapshot, do not read more.

### Change map

The core deliverable of Phase 2. For each affected surface: what work is required, in what order, and with what verification.

### Verification plan

The core deliverable of Phase 3. Each acceptance criterion maps to a concrete verification method and an evidence form.

### Completion report

The core deliverable of Phase 7. The narrative version of delivery: what was done, how it was verified, what residual risk remains, what is handed to whom next.

### Cross-Change Knowledge Note (CCKN)

A single-file artifact recording **reusable knowledge that spans multiple changes** — library gotchas, third-party API quirks, platform-specific behavior, domain rules discovered once and referenced repeatedly. Distinct from the Change Manifest (per-change) and from the temporal memory tiers in `ai-project-memory.md` (session / project / organizational, which describe lifespan not topic). Every CCKN carries a `topics` index, a `scope` tag (library / domain-rule / external-api / platform-quirk), a verified-references section with dates, and a changelog tracking which change_ids extended it. Full definition: `docs/cross-change-knowledge.md`. Referenced from the Change Manifest via the optional `knowledge_notes_touched` field.

---

## Classification terms

### Breaking-change level (L0–L4)

The severity of a change with respect to its consumers:

| Level | Name | Essence |
|-------|------|---------|
| L0 | Additive | No consumer is affected; capability is simply added |
| L1 | Behavioral | Same input produces a different result or side effect, but schema is unchanged |
| L2 | Structural | Schema changed; consumers must change code to parse |
| L3 | Removal | An existing capability is removed |
| L4 | Semantic reversal | The same name now means the opposite (the most dangerous) |

> Canonical definition: `docs/breaking-change-framework.md`.

### Rollback mode (1 / 2 / 3)

Three shapes of rollback:

| Mode | Name | Meaning |
|------|------|---------|
| 1 | Reversible rollback | As if it never happened |
| 2 | Forward-fix rollback | Cannot truly return to the prior state; a hotfix must be rolled forward |
| 3 | Compensation rollback | The effect is already irreversible; only compensation is possible |

> Canonical definition: `docs/rollback-asymmetry.md`.

### Public behavior

Any behavior perceivable by a **non-implementer**: end users, callers, downstream data, third-party SDK users, customer support, auditors. When a change affects public behavior, the handoff obligation automatically escalates.

### Controlled vs uncontrolled interface

Two subtypes of the system-interface surface:

- **Controlled** — in-house APIs, in-house events, in-house SDKs. The team controls the pace of change.
- **Uncontrolled** — upstream SDKs, platform policies, OS behavior. The counter-party controls the pace; you can only keep up.

> See `docs/surfaces.md`.

---

## Quality attributes (cross-cutting concerns)

Not independent surfaces — attributes that must be checked per surface:

- **Security**
- **Performance**
- **Observability**
- **Testability**
- **Error handling**

> Per-surface checklist: `docs/cross-cutting-concerns.md`.

---

## Anti-pattern vocabulary

### Desync

The state in which a source of truth and one of its consumers have drifted apart. Common variants: dual-write without coordination, consumers deriving their own truth, cache staleness, documentation drift from implementation, translation keys lagging the canonical copy.

### Local optimization

Deciding a design based only on what one layer or one surface sees, while ignoring the knock-on effects on the others. Preventing this is one of the primary reasons this methodology exists.

### Ceremony

Producing an artifact that nobody reads and that influences no decision. An unmistakable sign of methodology misuse.

> Over-use signals: `docs/onboarding/when-not-to-use-this.md`.

### Silent change

A change in public behavior with no corresponding changelog, docs update, or consumer notification. A classic desync factory.

### False completion

Code has merged but:

- Verification has not run / evidence was not retained.
- Consumers have not yet been synced.
- The operational surface (logs, docs, rollback plan) is absent.

From the user's or operator's perspective, the change is not complete.

---

## Evidence and quality vocabulary

### Reproducible

Any verification step, executed by someone else following the same instructions, produces the same result. A required property of evidence.

### Traceable

The ability to trace from "what the user sees" back to "the earliest change that caused it." Usually stitched together by trace id, commit hash, and ticket id.

### Minimum sufficient evidence

More evidence is not better. Each acceptance criterion needs **one** piece of evidence sufficient to support it. Over-producing evidence is itself a form of ceremony.

---

## Usage rules

1. When any document uses one of these terms, **link to this file** rather than redefining it.
2. Before adding a new term, check whether an equivalent concept already exists here.
3. When a term's definition needs to change, **revise this file** and propagate the change to every affected consumer document.
4. Do not use company-internal or product-specific names in normative content; when an example is needed, use a neutral description.
