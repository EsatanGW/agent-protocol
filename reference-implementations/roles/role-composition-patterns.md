# Role Composition Patterns

> **English TL;DR**
> Canonical roles remain Planner / Implementer / Reviewer. When a single role's cognitive load is genuinely too large for one agent invocation, it may internally delegate to *non-canonical* sub-agents — but the canonical role stays the sole writer of manifest fields and the sole party bound by the anti-collusion rule. Sub-agents are tools the canonical role uses; they are not additional roles.

This document is **non-normative**. The canonical operating contract is `docs/multi-agent-handoff.md` — three roles, explicit field ownership, anti-collusion rule. This document addresses a question that arises in practice: *what if one agent invocation cannot comfortably do everything a Planner / Implementer / Reviewer is asked to do?* The answer here is a set of composition patterns that preserve the three-role contract while letting a role decompose its internal work.

---

## When role composition is appropriate

Composition is appropriate when **all** of the following hold:

- The canonical role's work is genuinely too large for a single invocation (not just "the prompt is long" — cognitive load that produces real output-quality drops).
- The work inside that role is itself decomposable into sub-tasks with distinct concerns (e.g. a Planner facing a complex SoT question could benefit from a code-exploration sub-agent).
- The runtime supports multiple sub-agent invocations with distinct identities.
- The operational discipline to run each sub-agent fresh and re-read its output into the canonical role's own context can be maintained.

Composition is **not** appropriate when:

- The role's work would fit in one invocation but the contributor likes to over-decompose — that is ceremony, not composition.
- The runtime cannot grant distinct identities — composition without identity separation collapses back into one agent with extra indirection.
- The task is Lean-mode or Zero-ceremony — composition is never a Lean-mode optimization.

---

## The invariant: three roles remain canonical

Composition does **not** introduce new canonical roles. Planner / Implementer / Reviewer remain the only three identities whose manifest-field ownership is contractually defined. Specifically:

- **Manifest fields.** Only the canonical role writes its own manifest fields. A sub-agent may produce a draft or a finding; the canonical role reads the draft, decides whether to accept it, and writes the field itself. A sub-agent that writes manifest fields directly has escaped composition and become an unratified fourth role.
- **Anti-collusion rule.** The canonical anti-collusion rule (Implementer ≢ Reviewer in the same change) still applies. Composition cannot be used to route around it — e.g. a Reviewer that delegates verification to a sub-agent who shares identity with the Implementer collapses the rule.
- **Tool-permission matrix.** The matrix in `docs/multi-agent-handoff.md` §Tool-permission-matrix applies to the canonical role. A sub-agent must not be granted capabilities the canonical role is denied (e.g. a sub-agent under a Reviewer cannot have write tools).

---

## Four pattern sketches

These are sketches, not prescriptions. Each is valid but optional; a team adopting this plugin may use zero of them and still be fully compliant with the operating contract.

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

**Anti-collusion specifically here.** The reference-sampler's identity must differ from the Implementer whose work is being audited. A reference-sampler that shares identity with the Implementer is auditing itself — Anti-Rationalization Rule 5 (edit-through-the-back-door) is one language-level expression of what this rule prevents structurally.

---

## Shape of a composition

A valid composition has four parts:

1. **Canonical role invocation** — spawned normally per `docs/multi-agent-handoff.md`. Identity assigned at this point.
2. **Sub-agent invocation(s)** — spawned by the canonical role. Each sub-agent has a distinct identity from the canonical role and from each other. Sub-agents are scoped to a single sub-task and return a structured draft or finding.
3. **Consolidation step** — the canonical role reads every sub-agent's return. The canonical role's own context (not sum of sub-agents' contexts) is what writes the manifest fields. If a sub-agent produced a conclusion the canonical role cannot independently justify, that conclusion is discarded or escalated.
4. **Single handoff** — downstream receives handoff from the canonical role, not from any sub-agent. The downstream role never knows (and does not need to know) that composition happened internally.

The canonical role is accountable for the output regardless of how many sub-agents contributed to it. A sub-agent that produced wrong information does not absolve the canonical role — the canonical role failed to verify before using the output.

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

---

## Relationship to other documents

- `docs/multi-agent-handoff.md` — canonical role contract; composition never modifies this
- `docs/multi-agent-handoff.md` §Single-agent anti-collusion rule — still binding for every sub-agent identity
- `docs/multi-agent-handoff.md` §Optional machine-readable pre-filter — a sibling pattern: the pre-filter is also a non-canonical sub-agent invocation, with the same identity-must-differ constraint
- `docs/ai-operating-contract.md` §2a — reference-existence verification; applies to every sub-agent that cites an identifier
- `agents/reviewer.md` anti-rationalization rules — still fire on the canonical Reviewer regardless of how many sub-agents fed it findings

---

## What this document is not

- **Not a replacement for the three-role contract.** The three canonical roles remain the only roles with field ownership.
- **Not a license to proliferate sub-agents.** Two sub-agents in a composition is a decomposition; nine sub-agents per role is a bureaucracy.
- **Not a prescribed pattern.** Teams may use any, all, or none of the four patterns; the document exists to show that composition is possible without losing the contract.

If you find yourself unable to fit the composition into the four parts listed in §Shape of a composition, you do not have a composition — you have a proliferation. Return to the three-role contract and choose a different decomposition.
