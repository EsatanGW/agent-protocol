# Glossary

> **English TL;DR**
> Canonical definitions for every term used in this methodology: change, surface, source of truth, consumer, contract, evidence, surface coverage, handoff, the **four execution modes** (Zero-ceremony / Three-line delivery / Lean / Full), breaking change levels (L0–L4), rollback modes (1 reversible / 2 forward-fix / 3 compensation), and anti-pattern vocabulary. If another document and this one disagree, fix this one first.

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

### Execution mode

The methodology has **four execution modes** — Zero-ceremony, Three-line delivery, Lean, Full — arranged by rising ceremony. Each sub-section below is the canonical definition; other documents must defer to this section rather than redefining a mode locally. Selection criteria are **objective, recognizable conditions** (surface count, consumer count, reversibility, public-behavior impact), never "it feels like we need it." Decision tree: `skills/engineering-workflow/references/mode-decision-tree.md`. Upstream principle: `docs/principles.md` §8.

The four modes share one property: **each has a single, named artifact-set minimum**. Over-producing artifacts above a mode's minimum is itself a misuse (see `skills/engineering-workflow/references/misuse-signals.md`).

> **Note on legacy names.** Earlier drafts used `no-process path`, `ultra-lean`, `No skill`, `three-line handoff`, and `stripped-down version` for the first two modes. Those are retired aliases; the canonical names in this glossary are the normative ones. Bridges and examples may still carry the old names transitionally — treat any occurrence as equivalent to the canonical name listed here.

#### Zero-ceremony mode

**No methodology applies; just do the work.** Reserved for tasks where opening any artifact would cost more than the task itself:

- Pure Q&A, research, or reference reading — no files modified.
- Tiny fixes: diff < 5 lines, no public behavior impact, does not cross surfaces.
- One-off low-risk scripts with no long-lived consumer.
- Pure environment checks (read-only).
- Explicitly throwaway experiments that will not land on main.

**Artifact minimum:** none. The change and its commit message are the record.

**Legacy aliases (retired):** `no-process path`, `ultra-lean`, `No skill`.

#### Three-line delivery

**For the gray zone between Zero-ceremony and Lean.** The task has some public impact but reaches only one surface, or is a small refactor in a familiar area protected by tests, or is a well-understood config tweak.

**Artifact minimum:** a three-line record next to the commit or in the PR description:

```
What changed:  <one sentence>
How verified:  <one command or one screenshot>
Residual risk: <one sentence, or "none">
```

No spec, no plan, no ROADMAP row. Phase-gate discipline does not apply (see `docs/phase-gate-discipline.md §Ceremony scaling`).

**Legacy aliases (retired):** `three-line handoff`, `stripped-down version`.

#### Lean mode

**The minimum-ceremony execution with a traceable artifact chain.** Use when a change touches a single surface with ≤ 1 consumer and can be verified in ≤ 5 minutes, and the Zero-ceremony / Three-line-delivery bars do not apply (there is non-trivial behavior change, or evidence will need to be cited later).

Lean mode has **six steps** — Lean-0 Clarify, Lean-1 Investigate, Lean-2 Minimal Plan, Lean-3 Implement, Lean-4 Verify, Lean-5 Deliver Summary. **Lean steps are not phases.** "Phase" is a Full-mode concept; Lean steps collapse into a single phase-boundary for phase-gate purposes — gate discipline applies once, at Lean-5 delivery, not at every step. ROADMAP rows are optional for a Lean single-change initiative (see `docs/phase-gate-discipline.md §Ceremony scaling`).

**Artifact minimum:** `lean-spec-template.md` + `lean-verification-template.md` + `lean-delivery-template.md` (all in `skills/engineering-workflow/templates/`).

#### Full mode

**The complete artifact trail.** Use for new features, multi-surface change, multi-repo / multi-consumer work, migration / rollout / rollback-sensitive changes, or any task that carries a forced-Full trigger (see `skills/engineering-workflow/references/mode-decision-tree.md §Scenarios that force Full`).

Full mode has **nine phases** — Phase 0 Clarify, Phase 1 Investigate, Phase 2 Plan, Phase 3 Test Plan, Phase 4 Implement, Phase 5 Review, Phase 6 Sign-off, Phase 7 Deliver, Phase 8 Post-delivery Observation (optional). Every phase ends with a named gate; `docs/phase-gate-discipline.md` applies in full. A ROADMAP row is required for every phase.

**Artifact minimum:** spec + plan + test plan + test report + completion report + Change Manifest (per `docs/change-manifest-spec.md`).

#### Lean → Full step / phase correspondence

When a Lean-mode task upgrades to Full mid-change (per `mode-decision-tree.md §Mode upgrade / downgrade`), the step / phase mapping is:

| Lean step | Full phase(s) |
|---|---|
| Lean-0 Clarify | Phase 0 Clarify |
| Lean-1 Investigate | Phase 1 Investigate |
| Lean-2 Minimal Plan | Phase 2 Plan **+** Phase 3 Test Plan (Lean merges them) |
| Lean-3 Implement | Phase 4 Implement |
| Lean-4 Verify | (covers portions of Phase 5 Review and Phase 6 Sign-off) |
| Lean-5 Deliver Summary | Phase 7 Deliver |
| (Lean has no counterpart) | Phase 8 Post-delivery Observation |

On upgrade, the agent re-enters at the Lean step's corresponding Full phase and completes the missing Full-mode artifacts from that phase onward.

### Phase 0–8

The nine phases of Full mode: Clarify / Investigate / Plan / Test Plan / Implement / Review / Sign-off / Deliver / Post-delivery Observation. They form a **sequential narrative**, not a checklist that must be executed cell by cell every time. Full-mode phases are distinct from Lean-mode **steps** (Lean-0…Lean-5); see `§Execution mode §Lean mode` above.

### Discovery loop

The fallback mechanism for discovering that scope has grown during implementation. Distinct from the fix-retest loop (fix a bug, rerun the tests): a discovery loop goes **back to an earlier phase**, while a fix-retest loop stays inside the same phase.

### Resume mode

One of five declared modes — **Lazy / Targeted / Role-scoped / Full / Minimal** — that the incoming session names as its first action when resuming after a session break. The mode determines what must be read before work continues (Lazy = Manifest only; Targeted = Manifest + the entering phase's input artifacts; Role-scoped = Manifest + upstream role's single output; Full = disaster-recovery fallback requiring explicit justification; Minimal = Lean-spec only).

Declaring a mode is mandatory to prevent the session-handoff context-collapse failure pattern: a verbose handoff prompt + a sequential re-read of every referenced artifact exhausts the new session's context before real work begins. Canonical definition: `skills/engineering-workflow/references/resumption-protocol.md`.

### Resume prompt

The text that triggers a session resumption, distinct from the Change Manifest it points at. Two shapes:

- **AI-authored handoff prompt** — produced by an outgoing session using `skills/engineering-workflow/templates/handoff-prompt-template.md`. Dense pointer block (soft cap 400 words, hard cap 800); the resumption protocol's Steps 1–6 apply mechanically from its fields.
- **Human-originated directive** — a short instruction from the user like `continue`, `resume`, `go`, `繼續`, or `resume: <verb> <object>`. A short directive is a request to act on `Manifest.next_action`, not a passive context update. Runtime-injected content (`system-reminder`, MCP state changes, deferred-tool availability lists) appearing in the same turn is **not** part of the user's directive and must not reinterpret it into silence.

Canonical definition: `skills/engineering-workflow/references/resumption-protocol.md` Step 0. The symmetric outgoing-side rule ("narration is not action") lives in `docs/ai-operating-contract.md` §11.

### State snapshot

A single document sufficient to let a new session resume work without reading any other artifact. The Change Manifest plays this role for a change in Full mode; the Lean-spec note plays it for Lean mode. The state-snapshot discipline (see `docs/change-manifest-spec.md` §State-snapshot discipline) holds that if the snapshot is insufficient to resume from, it is **incomplete** — fix the snapshot, do not read more.

A snapshot that crosses the runtime's single-file read ceiling (typical: ~25,000 tokens or ~2,000 lines) stops being a usable snapshot — the incoming session cannot open it in one read, and falling back to `grep` or offset-reads defeats the "one file answers what comes next" guarantee. Compact the snapshot in place or split the change via `part_of` before relying on it. See `docs/change-manifest-spec.md` §Manifest size ceiling.

### Change map

The core deliverable of Phase 2. For each affected surface: what work is required, in what order, and with what verification.

### Verification plan

The core deliverable of Phase 3. Each acceptance criterion maps to a concrete verification method and an evidence form.

### Completion report

The core deliverable of Phase 7. The narrative version of delivery: what was done, how it was verified, what residual risk remains, what is handed to whom next.

### Cross-Change Knowledge Note (CCKN)

A single-file artifact recording **reusable knowledge that spans multiple changes** — library gotchas, third-party API quirks, platform-specific behavior, domain rules discovered once and referenced repeatedly. Distinct from the Change Manifest (per-change) and from the temporal memory tiers in `ai-project-memory.md` (session / project / organizational, which describe lifespan not topic). Every CCKN carries a `topics` index, a `scope` tag (library / domain-rule / external-api / platform-quirk), a verified-references section with dates, and a changelog tracking which change_ids extended it. Full definition: `docs/cross-change-knowledge.md`. Referenced from the Change Manifest via the optional `knowledge_notes_touched` field.

CCKNs have asymmetric timing: **query at Phase 1 Investigate startup** (before tracing the main flow, grep the CCKN directory for topics overlap with the change's anticipated surfaces / uncontrolled_interfaces / libraries — §When to query a CCKN); **write during Phase 1** — at initial Investigate per §Ceremony scaling, or at re-entry after a Phase 4 Discovery loop per §Relation to Change Manifest §3. Phase 4 Discovery triggers re-entry; it does not itself write. Querying late is the primary anti-pattern — decisions the CCKN should have informed have already been made.

### Sub-agent invocation

A single spawn-run-return cycle of a non-canonical sub-agent. One-shot: the invocation begins when the canonical role spawns it, ends when the sub-agent produces its structured return, and does not persist as a running process afterward. The canonical role must not treat a returned sub-agent as a long-lived process that needs cleanup or termination.

Some runtimes expose an **invocation handle** (identifier, address, or similar) usable to spawn a *new* invocation inheriting the prior one's memory — a **continuation primitive** (state reconstruction), not a reference to a running process (state continuation). Handles to returned invocations point at something that has already ended; identity is session-bounded, so a new invocation seeded from a handle is a new identity for anti-collusion purposes per `docs/multi-agent-handoff.md` §Single-agent anti-collusion rule.

Canonical reference: `reference-implementations/roles/role-composition-patterns.md` §Shape of a composition → §Invocation lifecycle.

### Fan-out

A composition pattern in which a canonical role (Planner / Implementer / Reviewer) spawns multiple non-canonical sub-agents in parallel to cover sub-tasks whose concerns are mutually independent. Each sub-agent has a distinct identity per `docs/multi-agent-handoff.md` §Single-agent anti-collusion rule, inherits the tool-permission envelope of the canonical role per `reference-implementations/roles/role-composition-patterns.md` §The invariant, and returns findings into a structured slot — never writes manifest fields directly.

Fan-out is a **Full-mode-only** optimization; `role-composition-patterns.md` §When role composition is appropriate explicitly excludes Lean and Zero-ceremony. Canonical fan-out patterns: `skills/engineering-workflow/references/parallelization-patterns.md` (Phase 1 surface investigators, Phase 5 specialized audits).

### Fan-in (synthesis)

The consolidation step that closes a fan-out. The canonical role reads every sub-agent's structured return, performs the **cross-cutting check** (are there gaps the individual sub-agents each missed but the union reveals?), and writes the manifest field itself. Fan-in is never delegated — a sub-agent that performs synthesis has escaped composition.

A fan-out with no recorded fan-in is a composition failure, not a completed fan-out. The `parallel_groups` manifest field enforces this structurally: `synthesis.performed_by_identity` must equal the owning role's identity. See `skills/engineering-workflow/references/parallelization-patterns.md` §Fan-in discipline.

### Context pack

A compact, pre-distilled bundle of change-scoped methodology context (the SoT patterns actually in play, surface definitions that apply, terminology the sub-agent needs) produced by a canonical role at the start of a fan-out and shared across every spawned sub-agent. Lives in session-scoped working space per `docs/phase-gate-discipline.md` Rule 5a — **not** a canonical artifact, not a handoff artifact, not persisted outside the change.

Purpose: reduce per-sub-agent context cost when fan-out sub-agents would otherwise each re-read the full `docs/` tree. Not a substitute for the Change Manifest (which remains the state snapshot) or for `evidence_plan` citations. Canonical definition: `skills/engineering-workflow/references/context-pack.md`; template: `skills/engineering-workflow/templates/context-pack-template.md`.

### Parallel group

An optional manifest record of a single fan-out event. Each entry names: the owning canonical role and identity, the phase in which the fan-out occurred, the set of sub-agents spawned (identity + scope), and the synthesis record (who performed fan-in, which manifest fields were written from it). Purpose is audit, not scheduling — the manifest records fan-out *as it happened*, so a Reviewer can confirm canonical-role-performs-synthesis and anti-collusion were honored.

Optional for backward compatibility — pre-1.11 manifests without `parallel_groups` remain valid. See `schemas/change-manifest.schema.yaml` §parallel_groups and `docs/change-manifest-spec.md` §Parallel groups.

### Phase overlap zone

A named prep-work slot that Phase N+1 may begin **before** Phase N's gate passes, provided three properties hold: (1) the prep does not depend on Phase N's gate output, (2) it produces an artifact the downstream phase will consume, and (3) it is **discarded and redone** if Phase N's gate fails. Overlap zones are between-phase pipeline parallelism and are distinct from fan-out (which is within-phase sub-agent parallelism per `Fan-out` above).

Five named zones: P1 → P2 (change-map skeleton), P2 → P3 (test-plan skeleton from stable ACs), P3 → P4 (baseline verification environment — not implementation code), P4 → P5 (Reviewer context-pack pre-distillation, reference-sampler seeding), P5 → P6 (pre-filter structural scan, sign-off template pre-fill). P0 → P1, P6 → P7, and P7 → P8 are explicitly **not** overlap zones.

Full-mode only. Overlap prep lives in session-scoped working space per `docs/phase-gate-discipline.md` Rule 5a — manifest-field writes only happen after the prior gate passes. Soft cap: ≤20% of the downstream phase's total work; past 20% the prep has become execution and is bypassing the gate by degree. Canonical definition: `skills/engineering-workflow/references/phase-overlap-zones.md`.

### Implementation cluster

A file-disjoint subset of Phase 4 implementation work delegated by the Planner to its own canonical Implementer invocation per **Pattern C** (`skills/engineering-workflow/references/cluster-parallelism.md`). Each cluster declares `scope_files` (the files its Implementer may modify), `independence_rationale` (why independent from other clusters), `assigned_identity` (the Implementer spawned for it), and a `status` lifecycle (`pending → in_progress → completed | blocked_discovery`).

Pattern C is the **only parallel mechanism that spawns canonical-role identities** in multiples. Patterns A and B (`parallelization-patterns.md` — see `Fan-out` above) spawn non-canonical sub-agents that return findings for the canonical role to synthesize. Pattern C spawns canonical Implementers that each write their own cluster's code and evidence directly. The two mechanisms may co-exist on the same change.

Full-mode only. 2–4 clusters per change. File-disjointness across clusters is validator-enforced; a change with overlapping cluster scopes is invalid. Discovery-loop trigger in any cluster halts all clusters by default (conservative — other clusters may be building on an invalidated plan). Canonical definition: `skills/engineering-workflow/references/cluster-parallelism.md`. Schema: `schemas/change-manifest.schema.yaml` §implementation_clusters.

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
