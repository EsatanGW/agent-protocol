# Autonomy Ladder Discipline

> **English TL;DR**
> A five-rung progression — **L0 hand-written / L1 draft-assist / L2 in-loop agent / L3 cross-Phase delegation / L4 end-to-end self-driven** — that tells a runtime *how much* of the change cycle the agent is allowed to drive without human intermediation, and *what additional evidence* each rung must collect to earn the privilege. The ladder is **descriptive** of the existing role / phase / risk / evidence machinery — every rung resolves to fields already in the Change Manifest schema and to existing rules in `multi-agent-handoff.md`, `decision-trees.md` Tree D, and `runtime-hook-contract.md`. It is **not** a new permission tier. The §Anti-patterns list rejects rung-claiming (claiming a high rung without the evidence shape that rung requires), rung-skipping (going from L1 directly to L4 without the prior rung's discipline), hidden upgrades, evidence inflation, treating the ladder as a permission tier, and Lean-mode classification gaming.

This document is the **single source of truth** for autonomy progression. Other docs cross-reference it instead of redefining the rungs.

---

## Why this discipline exists

The methodology already says, separately, who may do what (`docs/multi-agent-handoff.md`), when a human must review (`docs/decision-trees.md` §Tree D), what evidence is required (`docs/automation-contract.md`, `docs/evidence-quality-per-type.md`), and which actions a hook must intercept (`docs/runtime-hook-contract.md` §Risky-action interception list). What is **not** said in one place is the progression: starting at hand-written code today, what does an organization climb through to reach an end-to-end self-driven change cycle, and what is the minimum-bar evidence at each step?

Without the ladder, two recurring failures occur:

- **Rung-skipping.** A team that has a working L1 (draft-assist) workflow tries to jump straight to L4 (end-to-end). The agent produces what looks like an L4 deliverable — but the L2 application-driven evidence and L3 cross-Phase manifest discipline never landed. The first incident exposes the gap; trust collapses; the team retreats to L0.
- **Rung-claiming.** A team declares "we are running L4" but produces only L1 evidence. The claim is not falsifiable from the manifest, so it stands until production breaks.

The ladder closes both holes by binding each rung to a *minimum evidence shape* and a *minimum role-separation shape* drawn from rules that already exist.

---

## The five rungs

Each rung lists: scope (what the agent is doing), roles required (per `multi-agent-handoff.md`), minimum evidence (per `evidence-quality-per-type.md`), and HITL trigger (per Tree D). The columns are not new rules — they are the existing rules indexed by autonomy level.

### L0 — Hand-written

**Scope.** Humans write code; the agent is read-only assistance (search, lookup, paste). No agent-authored diff lands.

**Roles.** Human author + (optional) human reviewer. No canonical-role separation required.

**Minimum evidence.** Whatever the team's pre-existing review process produced. The methodology is **not in scope** at L0; the rung exists only as the floor from which L1 begins.

**HITL trigger.** Every change. The agent has no commit privilege.

**Forced upgrade.** None — L0 is a stable state.

### L1 — Draft-assist

**Scope.** Agent drafts a snippet, a manifest section, a test stub; a human reviews, edits, and commits. The diff shape is human-edited; the agent contribution is visible in working space but not in the commit history.

**Roles.** Single agent identity acting in a draft capacity; one human reviewer. Anti-collusion does not apply (the agent is not authoring the merged diff).

**Minimum evidence.** No manifest required for trivial changes (Zero-ceremony / Three-line delivery per `glossary.md §Execution mode`). For larger drafts, the human Reviewer's commit message records that an agent draft was used.

**HITL trigger.** Every commit. The human is the merge point.

**Forced upgrade.** When the agent's drafts are routinely committed verbatim without human edits, the change has effectively crossed into L2 and the L2 discipline kicks in — record the role separation, collect application-driven evidence, etc. Hidden L2 (an agent silently committing without role separation) is the rung-skipping anti-pattern.

### L2 — In-loop agent (single change, single role)

**Scope.** Agent authors a Change Manifest and a diff for one change at a single role (typically Implementer); a separate identity (human or agent in a different role) reviews. Phase 0–8 progression is inside one session.

**Roles.** At minimum two distinct identities — one Implementer + one Reviewer — per `AGENTS.md §7` and `multi-agent-handoff.md §single-agent-anti-collusion-rule`. Implementer ≡ Reviewer is forbidden. Lean-mode collapse (Planner ≡ Implementer for single-surface trivial changes) is allowed; Reviewer remains separate.

**Minimum evidence.** Per-surface rows in `evidence_plan` reach `status: collected` before Phase 5; `breaking_change.level` and `rollback_mode` declared; `phase_log` shows phase-boundary commits per `phase-gate-discipline.md` Rule 5. Application-driven evidence (per `cross-cutting-concerns.md §Application-driven verification`) is required when the change touches the user surface and `breaking_change.level >= L2`.

**HITL trigger.** Tree D leaves: any risky-action match (per `runtime-hook-contract.md §Risky-action interception list`); `breaking_change.level >= L2`; `rollback_mode = 3`; auth/PII/secrets path; canonical methodology content edit at L1+.

**Forced upgrade.** When one change spans multiple manifests (a campaign) or the Reviewer is itself an agent rather than a human, the discipline crosses into L3.

### L3 — Cross-Phase delegation (multi-manifest, agent-to-agent review)

**Scope.** Agent authors plan and diff across multiple Change Manifests connected by `part_of` / `strategic_parent`; review is performed by another agent identity (cross-identity Reviewer) in addition to or in place of human review on advisory-severity findings. Some Phase 5/6 work is delegated to specialist sub-agents per `multi-agent-handoff.md §Composable specialist sub-agent roles`.

**Roles.** Three distinct identities (Planner / Implementer / Reviewer) per `AGENTS.md §7`; specialist sub-agents per `reference-implementations/roles/specialist-roles-registry.md` are spawned for security-reviewer / performance-reviewer / architect work. Anti-collusion is **strict**: no identity plays more than one canonical role within one manifest, and no specialist sub-agent identity matches any canonical role's identity on the same change.

**Minimum evidence.** Everything from L2 plus: `parallel_groups` audit trail when fan-out occurs (per `references/parallelization-patterns.md`); cross-identity `approvals[*].approver_role` populated on review at `breaking_change.level >= L2`; observability-stack evidence (logs, metrics, traces queried from a runtime stack) per the new `observability-legibility-discipline.md` whenever `breaking_change.level >= L2` and the change touches the operational surface.

**HITL trigger.** All L2 triggers, plus: cross-identity Reviewer must be human when `breaking_change.level >= L3`; rollback dry-run must be witnessed by a human at `rollback_mode = 3`; security specialist must be a human when auth/PII/secrets are in scope.

**Forced upgrade.** When the agent begins to drive Phase 8 (post-delivery observation) without a human gate — opening, monitoring, and resolving its own follow-up tickets — the discipline crosses into L4.

### L4 — End-to-end self-driven

**Scope.** Agent runs the full Phase 0–8 loop autonomously: validates state, reproduces the reported failure, captures application-driven evidence (snapshot before/after, event traces), implements the fix, validates by driving the running application, opens the PR, responds to local and cloud agent reviewer feedback, remediates build failures, and merges. A human is in the loop only when a Tree D leaf fires.

**Roles.** Three canonical identities (Planner / Implementer / Reviewer) plus at least one cross-identity Reviewer that is itself an agent; specialist sub-agents per L3; pattern C (multi-Implementer) and dual-Reviewer per `multi-agent-handoff.md §Capability gating by risk level` apply at `breaking_change.level = L4`.

**Minimum evidence.** Everything from L3 plus: a recorded application-driven artefact for *both* the failure reproduction and the post-fix validation (per `references/application-driven-loop.md`); observability-stack evidence at every Phase that touches the operational surface; a back-pressure-shaped completion-audit hook (per `runtime-hook-contract.md §Back-pressure pattern`) that is silent on success and one-line on failure; a Phase 8 observation window with at least one query against the observability stack inside the window.

**HITL trigger.** Only Tree D leaves; everything else is agent-resolved. Human is paged on `breaking_change.level = L4`, on `rollback_mode = 3`, on production-credential-touch, and on canonical methodology content edits at L1+.

**Forced downgrade.** Any rung-claim that fails to produce the minimum evidence shape forces a downgrade — the manifest carries an `escalations[*].trigger: autonomy_evidence_gap` entry and the change is reviewed at the next-lower rung's discipline.

---

## Rung × surface table

A rung is enforced *per surface*. A change may run at L4 on the operational surface (where the agent has full observability) and at L2 on the user surface (where application-driven evidence is collected once and reviewed by a human). The manifest's per-surface `evidence_plan` row carries the rung claim implicitly through the evidence shape it declares.

| Surface | Min rung at which application-driven evidence is mandatory | Min rung at which observability-stack evidence is mandatory |
|---|---|---|
| User surface | L2 (when `breaking_change.level >= L2`) | L4 |
| System interface surface | L3 | L3 |
| Information surface | L3 | L4 |
| Operational surface | L4 | L2 |

The table is descriptive of the rules already present in `evidence-quality-per-type.md`, `cross-cutting-concerns.md §Application-driven verification`, and the new `observability-legibility-discipline.md` — it is the rung-axis projection of those per-type minima.

---

## Upgrade procedure

Climbing from L*n* to L*n+1* is itself a methodology change at canonical-content level L0–L1, and is governed by the same rules as any other methodology change:

1. **Declare the upgrade in the team's adoption record** (per `adoption-strategy.md`). The record names the rung being entered and the date.
2. **Land the prerequisite evidence shape** before claiming the new rung. The first change at the new rung must demonstrate the new minimum, not a pre-existing shape relabelled.
3. **Wait one observation window** (per `post-delivery-observation.md`) before climbing again. Two upgrades in one window is rung-skipping.
4. **Downgrade is unconditional** — any change that fails the rung's minimum evidence forces a per-change downgrade for that change. The team's overall rung is unaffected.

Skipping a rung (L1 → L3, or L2 → L4) is permitted only when the team can demonstrate that the skipped rung's discipline is already met *by some other means* — an independent test harness, an external reviewer pool, a pre-existing observability stack. The skip must be recorded in the adoption record; an unrecorded skip is rung-claiming.

---

## Anti-patterns

- **Rung-claiming.** The team's adoption record says L4; the actual evidence on every change is L2 (no application-driven artefacts, no cross-identity Reviewer, no Phase 8 query). The claim is theatre. Detection: an `anti-entropy-discipline.md` sweep that spot-checks one change per release against the per-rung evidence shape.
- **Rung-skipping.** A change crosses two rungs in one step (L1 to L3) without producing the L2 evidence. Detection: the change's Reviewer entry shows no application-driven evidence row when one is mandatory.
- **Hidden upgrade.** An agent at L1 begins to commit without human edit; effectively L2 but without L2 role separation. Detection: a drift hook that checks whether commits matching `Co-authored-by:` agent footers are paired with a manifest declaring at least an Implementer / Reviewer split.
- **Per-rung evidence inflation.** A rung claim is supported by L1-tier evidence padded with extra rows of the same tier. The padding does not raise the tier — see `evidence-quality-per-type.md §Coverage by counting`.
- **Treating the ladder as a permission tier.** The ladder describes what an autonomous workflow looks like; it does not grant permission to bypass `Tree D`, the risky-action interception list, or the anti-collusion rule. A team running L4 still has every Tree D leaf intact — the rung says "agent drives by default", not "human is removed from the system".
- **Ladder gaming via Lean-mode classification.** A change is declared Lean (single surface, trivial) so that the Reviewer can collapse, then the change is claimed at L3+. Lean is not a rung; rungs apply *within* Full mode where the role separation has teeth. Lean-eligible changes are out-of-scope for the ladder.

---

## Cross-references

- `docs/multi-agent-handoff.md` §Capability gating by risk level — the per-`breaking_change.level` × per-`rollback_mode` matrix that L2/L3/L4 inherit.
- `docs/decision-trees.md` §Tree D — the HITL leaves every rung still routes through.
- `docs/runtime-hook-contract.md` §Risky-action interception list — the ground floor that no rung overrides.
- `docs/cross-cutting-concerns.md` §Application-driven verification — the evidence shape L2+ requires.
- `docs/observability-legibility-discipline.md` — the evidence shape L3+ on the operational surface and L4 on every surface requires.
- `skills/engineering-workflow/references/application-driven-loop.md` — the worked walk-through of the L4 reproduce → fix → validate cycle.
- `skills/engineering-workflow/references/review-loop-pattern.md` — the agent-to-agent review-iteration loop that L3+ depends on.
- `skills/engineering-workflow/references/mode-decision-tree.md` — picks Lean / Full; the ladder applies inside Full mode.
- `docs/evidence-quality-per-type.md` — the per-evidence-type shape every rung's claim must match.
