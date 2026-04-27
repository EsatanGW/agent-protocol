# Role Composition Patterns

> **English TL;DR**
> Canonical roles remain Planner / Implementer / Reviewer. Three composition mechanisms exist: (a) **non-canonical sub-agent composition** (Patterns 1–6) — a canonical role delegates to sub-agents that return findings; the canonical role writes manifest fields. (b) **canonical-role multi-delegation** (Pattern 7) — the Planner spawns multiple canonical Implementers in parallel (one per cluster); each Implementer writes its own cluster's manifest fields directly. (c) **canonical-role takeover under sandbox fallback** (Pattern 8, 1.28.0) — a documented exception to anti-collusion when an Implementer sub-agent halts on a runtime / sandbox limit; canonical role takes over the Implementer slot, Reviewer slot remains a separate sub-agent identity. Six patterns for mechanism (a): four serial (research, code-explorer, test-writer, reference-sampler) and two parallel fan-out (surface-parallel investigators in Phase 1, specialized audit fan-out in Phase 5 — see `skills/engineering-workflow/references/parallelization-patterns.md`). One pattern for mechanism (b): Pattern 7 (Phase 4 cluster-parallel canonical Implementers — see `skills/engineering-workflow/references/cluster-parallelism.md`). One pattern for mechanism (c): Pattern 8. The anti-collusion rule binds all three; Pattern 8 relaxes it only at the Implementer slot under preconditions, never at the Reviewer slot.

This document is **non-normative**. The canonical operating contract is `docs/multi-agent-handoff.md` — three roles, explicit field ownership, anti-collusion rule. This document addresses a question that arises in practice: *what if one agent invocation cannot comfortably do everything a Planner / Implementer / Reviewer is asked to do?* The answer here is a set of composition patterns that preserve the three-role contract while letting a role decompose its internal work.

---

## When role composition is appropriate

This section covers Patterns 1–6 (non-canonical sub-agent composition). For Pattern 7 (canonical-role multi-delegation), applicability is in `skills/engineering-workflow/references/cluster-parallelism.md` §When to use Pattern C — the criterion is cluster decomposability, not single-role cognitive load.

Composition (Patterns 1–6) is appropriate when **all** of the following hold:

- The canonical role's work is genuinely too large for a single invocation (not just "the prompt is long" — cognitive load that produces real output-quality drops).
- The work inside that role is itself decomposable into sub-tasks with distinct concerns (e.g. a Planner facing a complex SoT question could benefit from a code-exploration sub-agent).
- The runtime supports multiple sub-agent invocations with distinct identities.
- The operational discipline to run each sub-agent fresh and re-read its output into the canonical role's own context can be maintained.

Composition (Patterns 1–6) is **not** appropriate when:

- The role's work would fit in one invocation but the contributor likes to over-decompose — that is ceremony, not composition.
- The runtime cannot grant distinct identities — composition without identity separation collapses back into one agent with extra indirection.
- The task is Lean-mode or Zero-ceremony — composition is never a Lean-mode optimization.

---

## The invariant: three roles remain canonical

Composition does **not** introduce new canonical roles. Planner / Implementer / Reviewer remain the only three identities whose manifest-field ownership is contractually defined. Specifically:

- **Manifest fields.** For Patterns 1–6 only the canonical role writes its own manifest fields; a sub-agent produces a draft or finding the canonical role synthesizes. A sub-agent that writes manifest fields directly has escaped composition. For Pattern 7, each cluster's Implementer is itself a *canonical Implementer* that writes its own cluster's evidence and `implementation_notes` entries directly — this is not an escape because the spawned identity carries the canonical Implementer's contractual ownership; the Planner still writes Planner-owned fields, the Reviewer still writes Reviewer-owned fields.
- **Anti-collusion rule.** The canonical anti-collusion rule (Implementer ≢ Reviewer in the same change) still applies. Composition cannot be used to route around it — e.g. a Reviewer that delegates verification to a sub-agent who shares identity with the Implementer collapses the rule. For Pattern 7 the rule applies transitively: each cluster's assigned_identity must differ from the Planner, from every other cluster's Implementer, and from the Reviewer's identity-to-be.
- **Tool-permission matrix.** The matrix in `docs/multi-agent-handoff.md` §Tool-permission-matrix applies to the canonical role. For Patterns 1–6 a non-canonical sub-agent must not be granted capabilities the canonical role is denied. For Pattern 7 each spawned canonical Implementer has the full canonical Implementer envelope per the matrix — that is the same envelope the matrix already grants; nothing new is unlocked.

---

## Pattern sketches

These are sketches, not prescriptions. Each is valid but optional; a team adopting this plugin may use zero of them and still be fully compliant with the operating contract.

Patterns 1–4 describe **serial** non-canonical-sub-agent composition (the canonical role calls a sub-agent, waits, reads the return, continues). Patterns 5 and 6 describe **parallel** non-canonical-sub-agent composition (fan-out / fan-in) and have their own execution discipline in [`../../skills/engineering-workflow/references/parallelization-patterns.md`](../../skills/engineering-workflow/references/parallelization-patterns.md) — the invariants in this document still apply to them, but the parallelization doc adds cache-window, context-pack, and cross-cutting-gap-check rules on top. Pattern 7 describes **canonical-role multi-delegation** — a different mechanism where the spawned units are canonical Implementers, not non-canonical sub-agents — and has its own execution discipline in [`../../skills/engineering-workflow/references/cluster-parallelism.md`](../../skills/engineering-workflow/references/cluster-parallelism.md).

### Pattern 1 — Planner + research sub-agent

A Planner facing an unfamiliar library / third-party API can delegate a **research sub-agent** to produce a structured summary of the external facts. The sub-agent reads docs, grep-searches local references, and produces a draft of what-we-know-and-do-not-know about the dependency. The Planner reads the draft and decides what to encode into `uncontrolled_interfaces`, `sot_map`, or a Cross-Change Knowledge Note (`docs/cross-change-knowledge.md`).

**Sub-agent capability envelope**: file read, code search, network fetch (read-only).
**Sub-agent must not**: write manifest fields; write CCKN files; spawn further sub-agents.

### Pattern 2 — Planner + code-explorer sub-agent

A Planner facing a large, unfamiliar codebase can delegate a **code-explorer sub-agent** to map existing patterns, identify SoT candidates, and report on consumer classes. The sub-agent traces calls, identifies path candidates for each SoT pattern (1–10, 4a), and produces a structured draft. The Planner reads and consolidates into `sot_map` and `consumers`.

**Sub-agent capability envelope**: file read, code search.
**Sub-agent must not**: write `sot_map`; decide SoT patterns on the Planner's behalf.

### Pattern 3 — Implementer + test-writer sub-agent

An Implementer producing a large verification batch can delegate a **test-writer sub-agent** to produce test files. The Implementer reviews the sub-agent's tests, runs them, and captures the actual test execution output as evidence.

**Sub-agent capability envelope**: file read, code search, file write (scoped to `tests/` or equivalent).
**Sub-agent must not**: run the tests and report results (that is the Implementer's evidence-collection act); write `evidence_plan.artifacts` fields; sign off the step.

### Pattern 4 — Reviewer + reference-sampler sub-agent

A Reviewer facing a manifest with many cited identifiers can delegate a **reference-sampler sub-agent** to pick random citations and reproduce the code-search commands that the Implementer claimed to run (see `docs/ai-operating-contract.md` §2a and `agents/reviewer.md` "Reference-existence sampling right"). The sub-agent reports findings — resolve / does-not-resolve — and the Reviewer decides the finding's weight.

**Sub-agent capability envelope**: file read, code search.
**Sub-agent must not**: write `review_notes`; subjectively rate evidence quality; downgrade the Reviewer's anti-rationalization triggers.

**Anti-collusion specifically here.** The reference-sampler's identity must differ from the Implementer whose work is being audited. A reference-sampler that shares identity with the Implementer is auditing itself — Anti-Rationalization Rule 4 (edit-through-the-back-door) is one language-level expression of what this rule prevents structurally.

### Pattern 5 — Planner + surface-parallel investigators (fan-out)

A Planner facing a multi-surface Full-mode change (typically 3+ surfaces) can spawn one **investigator sub-agent per surface** in a single batch, each scoped to that surface only, and consolidate their structured returns into `sot_map`, `surfaces_touched`, and `consumers`. Unlike Pattern 2 (one code-explorer sub-agent, serial), Pattern 5 is a *parallel* fan-out — typically 2–4 investigators spawned together.

**Sub-agent capability envelope (per investigator):** file read, code search.
**Sub-agent must not:** write manifest fields; cross into another investigator's surface; spawn further sub-agents; perform the fan-in synthesis itself.

**Additional invariants beyond §The invariant above:**

- Sub-agents are spawned in a **single tool-call batch**, not sequentially (cache-window rule in `parallelization-patterns.md`).
- All investigators consume the same **context pack** produced by the Planner before spawn (`skills/engineering-workflow/references/context-pack.md`).
- The Planner performs the **cross-cutting gap check** at fan-in — findings that emerge only from the intersection of two surfaces are the exact failure mode this pattern most often produces, and they are invisible to any individual investigator.
- The fan-out is recorded in the manifest's `parallel_groups` field for audit.

Full execution discipline: `skills/engineering-workflow/references/parallelization-patterns.md` §Pattern A.

### Pattern 6 — Reviewer + specialized audit fan-out

A Reviewer facing a Full-mode change whose audit surface is too large for a single invocation (many cross-cutting dimensions, many cited identifiers, tier-mixed evidence) can spawn specialized **audit sub-agents** in parallel — security audit, remaining cross-cutting dimensions, evidence-reference audit, acceptance-criterion coverage audit — each returning findings with severity. The Reviewer consolidates, applies the anti-rationalization rules, and writes `review_notes` and `approvals`.

**Sub-agent capability envelope (per audit):** file read, code search, verification-only shell. Inherited from the Reviewer per §The invariant — **no write, no edit tools**.
**Sub-agent must not:** write `review_notes`; subjectively rate evidence quality; approve or reject the change; downgrade the Reviewer's anti-rationalization triggers; spawn further sub-agents.

**Additional invariants beyond §The invariant above:**

- Every audit sub-agent's identity differs from the Planner's and the Implementer's on this change (anti-collusion applies transitively — sharing identity with the Implementer collapses audit into self-review, which is exactly Anti-Rationalization Rule 4 at the structural level).
- Audits are spawned in a single batch (cache-window rule).
- All audits consume the same Reviewer-produced context pack.
- The Reviewer performs the cross-cutting gap check and records the fan-out in `parallel_groups`.

Pattern 6 does **not** replace Pattern 4 (reference-sampler) — an evidence-reference audit under Pattern 6 is frequently implemented *using* Pattern 4 semantics as one of the parallel audits.

Full execution discipline: `skills/engineering-workflow/references/parallelization-patterns.md` §Pattern B.

### Pattern 7 — Planner + cluster-parallel canonical Implementers (canonical-role multi-delegation)

Pattern 7 is a **different mechanism** from Patterns 1–6. In Patterns 1–6 a canonical role delegates to **non-canonical sub-agents** that return findings the canonical role synthesizes into its own manifest fields. In Pattern 7 the Planner spawns **multiple canonical Implementer invocations** (one per file-disjoint cluster) at Phase 4 in a single batch; each spawned Implementer is a full canonical Implementer that writes its own cluster's fields directly. A single Reviewer downstream audits the union with a cross-cluster cross-cutting gap check.

The `multi-agent-handoff.md §Tool-permission matrix` already allows Planner-to-Implementer canonical delegation ("Only Planner may delegate canonical roles"). Pattern 7 formalizes the discipline for using that allowance in **parallel**: file-disjoint cluster scopes declared at plan time, single-batch spawn, discovery-in-any-cluster halts all clusters, cross-cluster cross-cutting gap check at Review.

**What is the same as Patterns 5/6:**

- Cache-window rule — single-batch spawn.
- Cluster / sub-agent cap 2–4.
- Anti-collusion — each cluster's assigned Implementer identity differs from the Planner's, every other cluster's, and the Reviewer's.
- Cross-cutting gap check — the specific failure mode parallel *anything* introduces is gaps at the intersection; Pattern 7's gap check happens at Review across clusters.

**What is different from Patterns 5/6:**

- Spawned units are **canonical** Implementers, not non-canonical sub-agents. Each has the full canonical Implementer tool envelope (read, write, shell).
- Sub-agents in Patterns 5/6 **return findings**; Implementers in Pattern 7 **write code and evidence directly** into their cluster's manifest slots.
- Fan-in synthesis in Patterns 5/6 is canonical-role writing manifest fields from sub-agent findings. "Fan-in" in Pattern 7 is assembly + cross-cluster audit — each Implementer already wrote its own fields; the Planner assembles state and the Reviewer audits the union.
- Pattern 7 uses `implementation_clusters` as the substantive record. It may also record an audit breadcrumb in `parallel_groups` (with `pattern: C_cluster_implementers`) so a Reviewer can cross-reference.

**Anti-patterns specific to Pattern 7:**

- Clusters that are not file-disjoint (even "mostly" is insufficient).
- Spawning Implementers serially (cache-window rule broken).
- Letting other clusters continue when one cluster enters Discovery-loop (silent gate bypass).
- Reviewer audits each cluster independently without the cross-cluster gap check.
- Clusters share identity between two spawned Implementers (anti-collusion violated transitively).

Full execution discipline: `skills/engineering-workflow/references/cluster-parallelism.md`.

### Pattern 8 — Canonical-role takeover under sandbox fallback

Pattern 8 is the **third mechanism**, distinct from both non-canonical sub-agent composition (Patterns 1–6) and canonical-role multi-delegation (Pattern 7). It applies when an Implementer sub-agent **halts correctly on a runtime / sandbox limit** — Bash blocked, framework CLI unavailable, network restricted, or other capability the runtime cannot grant — and re-spawning would face the same limit. The canonical role (typically the Planner that originally spawned the Implementer, or the main-control session) **takes over the halted Implementer's Phase 4 work** as "operating Implementer in sandbox fallback mode."

This is a documented **exception to the single-agent anti-collusion rule** (`docs/multi-agent-handoff.md` §Single-agent anti-collusion rule §Rule exceptions). Without Pattern 8 the Phase 4 work stalls indefinitely; with it the canonical role can complete the Implementer's deliverable while preserving the audit-trail properties anti-collusion exists to guarantee.

**Preconditions (all must hold).** Pattern 8 is not a convenience escape — every condition is load-bearing:

1. **Implementer sub-agent halted correctly.** No fabricated evidence (no "all tests passed" without a real test run); transparent stdout reporting that the runtime limit was hit; no silent termination.
2. **Re-spawn would face the same limit.** The limit is runtime-level (sandbox capability gap), not agent-specific. Re-spawning the same Implementer prompt against the same sandbox would loop without progress.
3. **Canonical role's runtime has the missing capability.** If the canonical role's session also lacks the capability, takeover does not unblock — escalate per `docs/ai-operating-contract.md` §5 instead.
4. **Stage scope fits the canonical role's remaining context budget.** Takeover that exhausts the canonical role's context creates a second halt at a worse boundary; if context budget is tight, split via `part_of` or escalate.

**Hard invariants during takeover.**

| Slot | Normal mode | Pattern 8 takeover | Why |
|---|---|---|---|
| Planner | sub-agent | sub-agent (or canonical role; identical to normal) | Read-only + plan output; no shell dependency |
| Implementer | sub-agent | **canonical role** (taking over) | The slot whose runtime gap motivated takeover |
| Reviewer | sub-agent | **sub-agent (mandatory; never relaxed)** | Implementer ≢ Reviewer is the single most consequential anti-collusion boundary; relaxing it under takeover would collapse audit |

**Non-fabrication is not relaxed.** The canonical role taking over is bound by the same `docs/ai-operating-contract.md` §9 non-fabrication list and §3 evidence quality rules as the original Implementer. Every verification command runs for real; every evidence artifact's `artifact_location` points to real stdout / file. If the canonical role's runtime *also* hits a limit during takeover, the takeover halts with the same transparent stdout reporting, escalating to user judgment per §5.

**Required record.** The takeover is recorded in `implementation_notes[*]` with the new sub-field `takeover_attestation` (or, for projects that prefer it, in a project-local extension field; the canonical encoding is via `implementation_notes`). Required content:

- `timestamp` — when takeover began (ISO 8601).
- `reason` — short prose naming the runtime limit that triggered it (e.g. `"Bash tool unavailable in sub-agent runtime"`).
- `commits` — list of commit SHAs the takeover produced.
- `non_fabrication_attestation` — boolean confirming the canonical role ran every verification command for real, plus an enumeration of the commands run.
- `reviewer_audit_status` — set to `pending` at takeover time; flipped to `passed` / `failed` once the Reviewer sub-agent has independently re-run all verification commands and confirmed the takeover output matches.

**Reviewer sub-agent's role under Pattern 8.** The Reviewer is **mandatory** and **must be a different identity from the canonical role that performed takeover** (anti-collusion preserved at the Reviewer boundary). The Reviewer independently re-runs every Implementer verification command — not "trusts the takeover_attestation," not "samples a few commands," but the full verification surface. A Reviewer who finds any fabrication during takeover treats it as **HIGH-severity finding** (Anti-Rationalization Rule 2's unsubstantiated `pass` case at structural level: the canonical role asserted verification without it).

**Anti-patterns specific to Pattern 8.**

- Takeover invoked because re-spawn is *inconvenient* rather than because the runtime limit is real (preconditions 1–2 not met).
- Reviewer slot also taken over by the canonical role (anti-collusion broken at its load-bearing boundary).
- `non_fabrication_attestation` set to true without a real verification-command enumeration (audit becomes ceremony).
- Takeover used as a permanent operating mode rather than an exception (the change should escalate to a runtime that supports the missing capability, not run takeover indefinitely).
- Reviewer sub-agent treats `takeover_attestation` as evidence and skips re-running verification (Anti-Rationalization Rule 3 — read-only review).

**Relation to other rules.**

- `docs/multi-agent-handoff.md §Single-agent anti-collusion rule` — Pattern 8 is the rule's documented exception; the canonical-role-as-Implementer combination is permitted only when Pattern 8 preconditions hold.
- `docs/ai-operating-contract.md §9 Non-fabrication list` — applies unchanged to the canonical role under takeover.
- `docs/ai-operating-contract.md §3 Evidence quality` — the higher-than-human evidence bar applies unchanged.
- `skills/engineering-workflow/references/long-running-delegation.md` — D1 / D2 / D3 govern *running* sub-agents; Pattern 8 governs the *halt-recovery* edge case. Orthogonal: a long-running sub-agent that hits a runtime limit and halts correctly may invoke Pattern 8 as the recovery path.
- `docs/multi-agent-handoff.md §Reviewer §Must not do` — Reviewer's read-only envelope is unchanged; the Reviewer running the post-takeover audit is a normal Reviewer invocation.

**Recurrence signal — when to consider Pattern 8 a project standard vs an exception.** A project that triggers Pattern 8 once or twice has hit two specific runtime limits; Pattern 8 is an exception for that project. A project that triggers it ≥5 times across distinct stages should treat the underlying runtime gap as an *escalation per `docs/ai-operating-contract.md §5`*, not as a recurring takeover routine — the runtime is not a fit for the work being done, and recurring Pattern 8 invocations mask that mismatch.

---

## Shape of a composition

A valid composition has four parts:

1. **Canonical role invocation** — spawned normally per `docs/multi-agent-handoff.md`. Identity assigned at this point.
2. **Sub-agent invocation(s)** — spawned by the canonical role. Each sub-agent has a distinct identity from the canonical role and from each other. Sub-agents are scoped to a single sub-task and return a structured draft or finding.
3. **Consolidation step** — the canonical role reads every sub-agent's return. The canonical role's own context (not sum of sub-agents' contexts) is what writes the manifest fields. If a sub-agent produced a conclusion the canonical role cannot independently justify, that conclusion is discarded or escalated.
4. **Single handoff** — downstream receives handoff from the canonical role, not from any sub-agent. The downstream role never knows (and does not need to know) that composition happened internally.

The canonical role is accountable for the output regardless of how many sub-agents contributed to it. A sub-agent that produced wrong information does not absolve the canonical role — the canonical role failed to verify before using the output.

### Invocation lifecycle

Each sub-agent call is a **one-shot invocation**: the sub-agent runs, produces a structured return, and the invocation terminates. The canonical role must not treat the sub-agent as a long-lived process that continues running between invocations or needs explicit shutdown after return.

Some runtimes expose an **invocation handle** (identifier, address, or similar) that can seed a *new* invocation inheriting the prior one's memory. This is a continuation primitive — state reconstruction, not state continuation. A handle to a returned invocation points at something that has already ended; operations against it cannot reach a "running" instance because none exists. Consequences for the canonical role:

- Do not attempt cleanup, termination, or resource-release on a sub-agent whose invocation has returned — the invocation has already ended.
- Do not assume state persists between sub-agent invocations without an explicit continuation call — context dies with the invocation unless re-seeded via a handle or passed through the canonical role's own state.
- Do not let a dangling invocation-handle linger in working memory as a "pending task" — it points at something that has ended, not a reference to a running process.

Identity is a property of the invocation, not of the handle. A new invocation seeded from a prior handle is a new identity for anti-collusion purposes (per `docs/multi-agent-handoff.md` §Single-agent anti-collusion rule and §The invariant above); handles are not a mechanism to reuse identity across invocations.

---

## Anti-patterns

| Anti-pattern | What breaks |
|---|---|
| Sub-agent writes manifest fields directly | Escapes composition; sub-agent is now a fourth role without a contract |
| Sub-agent shares identity with another canonical role in the same change | Anti-collusion violated by transitive reuse of identity |
| Sub-agent granted capabilities the canonical role lacks | Tool-permission matrix bypass (most dangerous in Reviewer composition) |
| Sub-agent signs off the step / approves the change | Escapes the canonical role's sign-off authority |
| Canonical role reports sub-agent's finding as its own without independent verification | Plausibly-complete narrative by proxy (the failure mode `docs/ai-operating-contract.md` §1 warns against) |
| Composition used in Lean or Zero-ceremony mode | Introduces ceremony at a scale where the mode doesn't support it |
| More than 3 levels of sub-agent nesting | Execution tree explosion; undiagnosable when something goes wrong |
| Parallel fan-out spawned serially (Pattern 5 / 6 / 7) | Cache-window rule broken; parallelization cost paid without the benefit |
| Parallel fan-out with no recorded `parallel_groups` entry (Patterns 5 / 6) or no `implementation_clusters` entry (Pattern 7) | Audit-layer contract escape; Reviewer cannot verify synthesis ownership or anti-collusion |
| Parallel fan-out without the cross-cutting gap check | The specific failure mode parallelization introduces — gaps invisible to any individual sub-agent / cluster but present in the union |
| Pattern 7 clusters that are not file-disjoint | Merge conflicts → implicit serialization + unclear ownership of the conflicted file |
| Pattern 7 Discovery-loop trigger in one cluster while others continue | Default-halt-all invariant broken; other clusters produce work based on an invalidated plan |
| Canonical role attempts cleanup / termination on a sub-agent whose invocation has already returned | Misreads one-shot invocation as a long-lived process; wastes tool calls; on runtimes that return a "not found" error, the error pollutes the canonical role's mental model with a false signal |
| Canonical role treats a stale invocation handle as identity-equivalent to a still-running sub-agent (e.g. reuses the handle for audit work) | Identity is session-bounded per §The invariant and §Invocation lifecycle — a new invocation seeded from a handle is a new identity whose anti-collusion constraints (Rule 5 / Pattern 6) must be re-evaluated, not inherited |

---

## Relationship to other documents

- `docs/multi-agent-handoff.md` — canonical role contract; composition never modifies this
- `docs/multi-agent-handoff.md` §Single-agent anti-collusion rule — still binding for every sub-agent identity
- `docs/ai-operating-contract.md` §2a — reference-existence verification; applies to every sub-agent that cites an identifier
- `docs/multi-agent-handoff.md` §Anti-rationalization rules — still fire on the canonical Reviewer regardless of how many sub-agents fed it findings
- `skills/engineering-workflow/references/parallelization-patterns.md` — execution discipline for Patterns 5 and 6 (cache-window rule, context pack, fan-in synthesis, cross-cutting gap check, `parallel_groups` audit)
- `skills/engineering-workflow/references/context-pack.md` — the shared-context mechanism Patterns 5 and 6 both require
- `skills/engineering-workflow/references/cluster-parallelism.md` — execution discipline for Pattern 7 (file-disjoint clusters, single-batch spawn, discovery-halt-all, Reviewer cross-cluster gap check, `implementation_clusters` audit)
- `schemas/change-manifest.schema.yaml` §parallel_groups — the audit-trail field for Patterns 5 and 6 (and breadcrumb entry for Pattern 7)
- `schemas/change-manifest.schema.yaml` §implementation_clusters — the substantive record for Pattern 7

---

## What this document is not

- **Not a replacement for the three-role contract.** The three canonical roles remain the only roles with field ownership.
- **Not a license to proliferate sub-agents.** Two sub-agents in a composition is a decomposition; nine sub-agents per role is a bureaucracy. The parallel patterns (5, 6, 7) cap at 4 sub-agents / clusters per group for the same reason.
- **Not a prescribed pattern.** Teams may use any, all, or none of the eight patterns; the document exists to show that composition is possible without losing the contract.
- **Not a merger of the three mechanisms.** Patterns 1–6 are non-canonical sub-agent composition; Pattern 7 is canonical-role multi-delegation; Pattern 8 is canonical-role takeover under sandbox fallback (a documented anti-collusion exception). All three preserve the three-role contract, but via different means — do not conflate them.

If you find yourself unable to fit the composition into the four parts listed in §Shape of a composition, you do not have a composition — you have a proliferation. Return to the three-role contract and choose a different decomposition.
