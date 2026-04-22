# Parallelization Patterns

How a canonical role fans work out to sub-agents, how it fans the results back in, and which disciplines keep the fan-out from silently producing a worse result than serial execution would have.

**Why this document exists.** The three-role contract (`docs/multi-agent-handoff.md`) defines *who* writes what. The role-composition patterns (`reference-implementations/roles/role-composition-patterns.md`) define the general *shape* of a valid sub-agent decomposition. This document is the specific execution layer for **parallel** fan-out: the two canonical parallel patterns, the timing rules that make fan-out economically worthwhile, the fan-in discipline that makes it safe, and the anti-patterns that signal it has gone wrong.

**Scope.** Full mode only. `role-composition-patterns.md` §When role composition is appropriate explicitly excludes Lean and Zero-ceremony — a Lean-mode fan-out is ceremony, not speedup.

---

## When to fan out

Fan-out is appropriate when **all** of the following hold:

- The phase is Full mode and the canonical role's work inside it is large enough that a single invocation produces noticeable output-quality drops (missed surfaces, shallow review, truncated investigation).
- The work decomposes into **mutually independent** sub-tasks — each sub-agent can complete without waiting for another sub-agent's output.
- The runtime can spawn sub-agents with distinct identities per `docs/multi-agent-handoff.md` §Single-agent anti-collusion rule.
- The canonical role can perform the fan-in synthesis itself, in its own context — not delegate it.

Fan-out is **not** appropriate when:

- The sub-tasks share state that must be updated incrementally (they are not independent).
- The canonical role would have to re-read all sub-agent outputs and re-verify them from scratch anyway (the synthesis cost equals the serial cost, minus the fan-out overhead — net negative).
- The phase is Lean or Zero-ceremony.
- More than three sub-agents would be spawned in one group (past three, the synthesis step starts losing cross-cutting visibility; split into two phases or reduce scope).

---

## The two canonical parallel patterns

### Pattern A — Phase 1 surface-parallel investigators

**Owned by:** Planner.

**Trigger:** Full mode, multi-surface change (3+ surfaces touched), Phase 1 Investigate. The serial walk — user surface → system-interface surface → information surface → operational surface — produces a correct answer but consumes significant clock time because each surface scan involves independent `grep`/read passes.

**Shape:**

1. Planner (canonical) produces a **context pack** (`context-pack.md`) naming the change's SoT candidates, the four surfaces in scope, and the glossary terms each investigator will need.
2. Planner spawns **one investigator sub-agent per surface** (at most four), all in a single batch tool-call burst — the cache-window rule (below) requires this.
3. Each investigator's scope is hard-bounded: *"Return the SoT candidate, the consumer list, and the reference patterns for surface X only. Do not cross into surface Y."*
4. Investigators return **structured findings** into a typed slot. The slot shape is fixed per scope — findings are not free-form prose.
5. Planner performs fan-in: reads all returns, applies the cross-cutting gap check (below), and writes `sot_map`, `surfaces_touched`, and `consumers` itself.

**Capability envelope per investigator:** file read, code search. No write. No further sub-agent spawn.

**Why the Planner owns this**: the surface analysis and SoT mapping are the Planner's manifest-field responsibility per `docs/multi-agent-handoff.md`. A sub-agent writing those fields directly is a contract escape (Pattern 1 escape mode in `role-composition-patterns.md` anti-pattern table).

### Pattern B — Phase 5 specialized audit fan-out

**Owned by:** Reviewer.

**Trigger:** Full mode, Phase 5 Review, where the audit surface is large enough that a single Reviewer invocation cannot cover every anti-rationalization rule, every cross-cutting dimension, and every evidence reference without dropping cognitive load somewhere.

**Shape:**

1. Reviewer (canonical) reads the manifest and produces a **context pack** listing the change's surfaces, breaking-change level, evidence tier mix, and cross-cutting dimensions with non-trivial impact.
2. Reviewer spawns specialized audit sub-agents, in a single batch, scoped to a specific audit concern. Common specializations:
    - Security audit (against `docs/cross-cutting-concerns.md` §Security).
    - Cross-cutting audit (the remaining 5 dimensions).
    - Evidence-reference audit (the sampling right from `agents/reviewer.md` — does every cited `file:line` resolve?).
    - Acceptance-criterion coverage audit (does every declared criterion map to a verification step and evidence?).
3. Each audit sub-agent returns **findings with severity** (info / warn / blocking). Findings are not review decisions — they are inputs to the Reviewer's decision.
4. Reviewer performs fan-in: consolidates findings, applies the anti-rationalization rules (`agents/reviewer.md`), runs the cross-cutting gap check, and writes `review_notes` and `approvals` itself.

**Capability envelope per audit sub-agent:** file read, code search, verification-only shell (tests/builds/lint). **No write. No edit.** These sub-agents inherit the Reviewer's envelope per `role-composition-patterns.md` §The invariant.

**Anti-collusion specifically here:** every audit sub-agent's identity must differ from the Planner's and Implementer's identities on this same change. Sharing identity with the Implementer collapses the audit into self-review — Anti-Rationalization Rule 5 is the language-level expression of what this rule prevents structurally.

---

## Mandatory discipline

Both patterns require the following. A fan-out that skips any of these is a composition failure, not a parallelized success.

### Cache-window rule (single-batch spawn)

Fan-out sub-agents are spawned in a **single tool-call batch**, not sequentially. Most AI runtimes cache prompt prefixes with a short TTL (commonly around five minutes). If sub-agents are spawned serially, later sub-agents pay the cache-miss cost, which often erases the parallelization benefit. Spawn in one batch, let the runtime parallelize execution, and collect returns.

Symmetric with `skills/engineering-workflow/SKILL.md` principle 9 (batch independent tool calls), applied at the sub-agent layer.

### Context pack rule (shared, pre-distilled)

Before spawning, the canonical role produces a context pack per `context-pack.md`. The pack is shared across every sub-agent in the group. Without it, each sub-agent re-reads the same `docs/` subset independently, which defeats the parallelization economics.

The context pack is session-scoped (Rule 5a working space) — it is not persisted and not cited as evidence.

### Fan-in discipline (canonical role performs synthesis)

The canonical role reads every sub-agent's return into its own context and writes the manifest field itself. Specifically:

- The canonical role **must** read every return in full. If the returns are too large to read in full, the decomposition was wrong — reduce scope per sub-agent, do not skim.
- A sub-agent's conclusion the canonical role cannot independently justify is **discarded** (or escalated). Reporting a sub-agent's conclusion as one's own without independent justification triggers the "plausibly-complete narrative by proxy" anti-pattern in `role-composition-patterns.md`.
- A fan-out with no recorded fan-in step is not a completed fan-out — it is an orphaned delegation. The `parallel_groups` manifest field makes this visible: a group without a synthesis record is a schema failure.

### Cross-cutting gap check (explicit)

The single highest-value reason to fan out is *also* the single highest-risk — the canonical role sees the union of findings, but each individual sub-agent saw only its slice. A gap that emerges only from the **intersection** of two surfaces will not be flagged by either surface's investigator individually.

At fan-in, the canonical role explicitly asks:

- Are there findings that should exist in the union but that no individual sub-agent produced? (e.g. *User surface sweep finds the copy; Information surface sweep finds the enum. Neither flags that the copy uses the pre-rename enum string.*)
- Does any pair of sub-agent findings contradict each other? Contradictions are always real — one of the two is wrong, or the question was under-specified.
- Is any sub-agent's scope suspiciously empty? Zero findings can mean the sub-task was trivial — or that the sub-agent silently failed.

The cross-cutting gap check is recorded in the synthesis slot of the parallel group, not in a separate artifact. Silent omission of this step is itself the failure mode.

### Audit trail (parallel_groups)

Every fan-out that occurred is recorded in the manifest's optional `parallel_groups` field per `schemas/change-manifest.schema.yaml`. A Reviewer auditing a Planner's fan-out, or a reader reconstructing the change post-hoc, must be able to see: who fanned out, who the sub-agents were (by identity), what scope each had, who synthesized, and which manifest fields were written from that synthesis.

The field is optional — a Full-mode change that chose not to fan out validates against the schema without it. What is *not* valid is a fan-out that happened but was not recorded; that is a contract escape at the audit layer.

---

## Phase applicability summary

| Phase | Applicable pattern | Owning role | Parallelism mechanism |
|---|---|---|---|
| Phase 0 Clarify | — (too early, SoT not yet identified) | — | — |
| Phase 1 Investigate | Pattern A — surface-parallel investigators | Planner | Non-canonical sub-agent fan-out |
| Phase 2 Plan | — (integrative by nature; sub-decomposition into tasks is planning, not fan-out) | — | — |
| Phase 3 Test plan | — (usually integrative; a fan-out here is a smell that the plan is too large) | — | — |
| Phase 4 Implement | **Pattern C — cluster-parallel canonical Implementers** (see [`cluster-parallelism.md`](cluster-parallelism.md)). Pattern 3 from `role-composition-patterns.md` (test-writer sub-agent) remains available as *serial* within-cluster composition. | Planner (spawns Implementers); Implementer per cluster | **Canonical-role multi-delegation** — distinct from sub-agent fan-out |
| Phase 5 Review | Pattern B — specialized audit fan-out | Reviewer | Non-canonical sub-agent fan-out |
| Phase 6 Sign-off | — (human-in-loop checkpoint) | — | — |
| Phase 7 Deliver | — | — | — |

**Two parallelism mechanisms.** Patterns A and B spawn **non-canonical sub-agents** that return findings for the canonical role to synthesize into its own manifest fields. Pattern C spawns **canonical Implementer identities** that each write their own cluster's fields directly. The disciplines in this document (cache-window rule, context pack, fan-in synthesis, cross-cutting gap check, `parallel_groups` audit) apply to Patterns A and B; Pattern C has its own discipline in `cluster-parallelism.md` (file-disjoint clusters, discovery-halt-all-clusters, Reviewer cross-cluster gap check, `implementation_clusters` manifest field). Both mechanisms may appear on the same change — a Phase 1 Pattern A fan-out and a Phase 4 Pattern C delegation and a Phase 5 Pattern B fan-out, each recorded in its own field.

For the canonical-role multi-delegation discipline that Pattern C introduces, see [`cluster-parallelism.md`](cluster-parallelism.md) and `role-composition-patterns.md` §Pattern 7.

---

## Anti-patterns

| Anti-pattern | What breaks |
|---|---|
| Fanning out in Lean or Zero-ceremony mode | Explicit exclusion in `role-composition-patterns.md` §When; ceremony pretending to be optimization |
| Sub-agent writes `sot_map` / `review_notes` directly | Canonical-role-writes-fields invariant escape; unratified fourth role |
| Four-plus sub-agents per group | Fan-in cross-cutting visibility degrades past ~3 parallel returns |
| Serial spawn of fan-out sub-agents | Cache-window rule broken; parallelization cost appears without benefit |
| Fan-in step skipped or delegated to a sub-agent | Composition escape; no canonical owner for the resulting manifest field |
| Canonical role reports union of sub-agent findings without independent verification | "Plausibly-complete narrative by proxy" — `docs/ai-operating-contract.md` §1 failure mode |
| Cross-cutting gap check skipped | The single failure mode parallelization most commonly introduces — gap invisible to any individual sub-agent but present in the union |
| `parallel_groups` not recorded when fan-out happened | Contract escape at the audit layer; Reviewer cannot verify synthesis ownership or anti-collusion |
| Audit sub-agent identity shared with Implementer | Anti-collusion collapse; audit becomes self-review |
| Nested fan-out (sub-agent spawns its own sub-agents) | Execution tree explosion; `role-composition-patterns.md` caps nesting at 3 levels, parallelization should stop at 1 |

---

## Relationship to other documents

- `docs/multi-agent-handoff.md` — canonical three-role contract; parallelization never modifies this
- `reference-implementations/roles/role-composition-patterns.md` — general composition invariants; this doc is the parallel-specific execution layer for Patterns A/B (non-canonical sub-agent fan-out). Pattern 7 in that doc covers Pattern C (canonical-role multi-delegation)
- `skills/engineering-workflow/references/context-pack.md` — the mechanism that makes fan-out context-efficient
- `skills/engineering-workflow/references/cluster-parallelism.md` — Pattern C's dedicated discipline (distinct from this document's Patterns A/B because Pattern C is canonical-role multi-delegation, not sub-agent fan-out)
- `skills/engineering-workflow/phases/subagent-strategy.md` — the phase-file-level pointer that tells an agent when to consult this doc
- `schemas/change-manifest.schema.yaml` §parallel_groups — audit-trail field for Patterns A/B (and an audit breadcrumb entry for C)
- `schemas/change-manifest.schema.yaml` §implementation_clusters — substantive record of Pattern C
- `docs/cross-cutting-concerns.md` — what the cross-cutting gap check is checking against
- `agents/reviewer.md` anti-rationalization rules — still fire on the canonical Reviewer regardless of how many audit sub-agents fed it findings or how many clusters Pattern C split the work across
- `skills/engineering-workflow/SKILL.md` principle 9 — symmetric rule at the tool-call layer; this doc extends the same principle to the sub-agent layer

---

## What this document is not

- **Not a license to fan out by default.** The default in every phase remains: one canonical role, one invocation. Fan out only when the serial cost is genuinely unworkable and the fan-in synthesis cost is less than the saved serial time.
- **Not a replacement for the three-role contract.** The canonical role remains fully accountable for the output, including findings produced by sub-agents the canonical role never independently verified.
- **Not a substitute for investigating carefully.** Fanning out a hasty investigation produces four hasty results, not one careful one.
