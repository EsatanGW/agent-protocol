# Throughput-first Merge Philosophy

> **English TL;DR**
> When agent throughput far exceeds human attention, the merge gate's job changes. **Three rules.** **(1) Default-advisory.** Lint / drift / completion-audit signals default to advisory; mechanical block is reserved for the risky-action interception list, breaking changes at L2+, rollback-mode-3, and auth/PII/secrets paths. **(2) Short-lived PRs.** A PR that does not close in one work-cycle is a planning failure, not a quality bar — the change is too large or the gate is too strict. **(3) Follow-up over indefinite blocking.** A flaky test, a non-blocking lint regression, a documentation rot finding produce a follow-up issue, not a hold on the in-flight PR. **The escape hatch.** When `breaking_change.level >= L2`, `rollback_mode = 3`, the change touches a risky-action class, or a canonical methodology edit at L1+ fires, throughput-first defers to the strict gate. The philosophy is a posture, not a permission to bypass; the strict gate's leaves remain inviolate.

This document is the **single source of truth** for the merge-gate posture. Other docs (`phase-gate-discipline.md`, `automation-contract.md`, `runtime-hook-contract.md`, `rollback-asymmetry.md`) cross-reference it instead of restating it.

---

## Why this discipline exists

In a low-throughput environment (a small team of humans, a handful of PRs per week), the merge gate's bias toward strict blocking is rational — every block is reviewed by a human, every false positive is caught, the cost of a missed regression is high relative to the cost of a slow merge. In a high-throughput environment (an agent-driven team, dozens of PRs per day), that posture inverts:

- **Block-default produces queue collapse.** Every block costs an agent loop iteration; every iteration costs context budget and wall-clock; the agent's effective throughput drops below the rate at which it can address the blocks. The team's adoption silently degrades to "we wait for the gates to clear."
- **Lint drift accumulates faster than humans can review.** When the gate fires on every taste-level finding, the noise drowns the signal — real findings are buried in routine ones, and the agent's next iteration ignores all of them equally.
- **Long-lived PRs decay.** A PR open for three days against an agent-velocity branch base is rebasing on shifting code; the diff the Reviewer reviewed at hour 0 is not the diff that merges at hour 72. Throughput-first existence is required precisely so that PRs *can* close inside one work-cycle.

The philosophy is not "skip review" — it is "block on the things that warrant blocking, follow up on the things that warrant following up, and stop blocking on everything else." The rule of thumb is recorded by the article that named the pattern: corrections are cheap, waiting is expensive, when throughput far exceeds review capacity.

---

## The three rules

### Rule 1 — Default-advisory

Hook and validator findings default to **advisory severity** unless the rule explicitly opts into block. Advisory findings appear in the manifest's `phase_log` and the PR description; they do not stop the merge. Block is reserved for:

- **Risky-action interception** per `runtime-hook-contract.md §Risky-action interception list` — every row on that list blocks unconditionally.
- **Breaking changes at level L2+** per `breaking-change-framework.md` — the strict gate kicks in; throughput-first defers.
- **Rollback-mode-3** per `rollback-asymmetry.md` — compensation-only changes are not reversible; the strict gate kicks in.
- **Auth / PII / secrets paths** per `security-supply-chain-disciplines.md` — security-reviewer specialist is required; the strict gate kicks in.
- **Canonical methodology content edits at L1+** per `mode-decision-tree.md §Scenarios that force Full` — forced-Full triggers the strict gate; throughput-first defers.

Every other rule defaults to advisory. Runtime bridges may promote individual rules to block locally; the promotion is recorded in the bridge's `DEVIATIONS.md` so the philosophy's posture is auditable per environment.

### Rule 2 — Short-lived PRs

A PR that does not close in one work-cycle (typically a working day for a human team; for an agent-driven team, often hours) is a signal the change is mis-scoped, not a quality bar reached. Three remediations apply, in order of preference:

1. **Decompose the change** per `change-decomposition.md` — split into independent slices that can each close in one cycle.
2. **Move advisory findings to follow-up issues** — the PR closes; the findings ride into the next change.
3. **Escalate the strict gate** — when the strict gate is firing legitimately (Rule 1's escape hatches), the PR length is justified; throughput-first does not apply, and the team accepts the longer cycle as the cost of the strict-gate change.

A PR that has been open for more than two work-cycles without an escape-hatch justification is a `phase_log` finding under the `anti-entropy-discipline.md §Sweeps` and is itself a candidate for sweep-time triage.

### Rule 3 — Follow-up over indefinite blocking

When a finding is real but does not warrant a block:

- **Open a follow-up issue** in the team's tracking system citing the finding's manifest row, severity, and a suggested remediation owner.
- **Record the follow-up in the merging change's `phase_log`** as a `follow_up_issued` entry with the issue's identifier — so the audit trail crosses both the closing change and the follow-up's eventual close.
- **Let the merging PR close.** The follow-up is a new change with its own manifest; treating it as a hold on the in-flight PR collapses two changes into one and defeats Rule 2.

A flaky test that fires once in twenty CI runs is a Rule-3 follow-up, not a block. A flaky test that fires in every other run is a Rule-2 decomposition signal — the change uncovered a flake worth fixing now, in its own slice, before the in-flight change merges.

---

## Mapping to existing rules

The three rules resolve to existing methodology contracts; no new schema field is introduced.

| Rule | Resolves to | Existing rule reference |
|---|---|---|
| Rule 1 (default-advisory) | `automation-contract.md` Rule 2.13 posture | "Default severity: advisory; runtime bridges may opt to block" — already canonical |
| Rule 1 (escape hatches) | `decision-trees.md` Tree D leaves + `runtime-hook-contract.md §Risky-action interception list` | The strict gate fires when any Tree D leaf is hit; throughput-first defers there |
| Rule 2 (short-lived PRs) | `phase-gate-discipline.md` Rule 5 (records at phase boundaries) | A PR that crosses multiple work-cycles fragments the phase-log; recording at boundaries presupposes boundaries close |
| Rule 3 (follow-up over blocking) | `change-decomposition.md` (split rather than bundle) | A finding that becomes its own issue is a decomposition; bundling it into the in-flight change is the anti-pattern |

---

## Per-rung interaction (cross-reference with `autonomy-ladder-discipline.md`)

Throughput-first applies most strongly at the higher rungs. At L0/L1, throughput is bounded by human capacity and the philosophy's leverage is low. At L4, the philosophy is the dominant gate posture — without it, the agent's loop stalls.

| Rung | Throughput-first applicable | Default-advisory weight | Strict-gate posture |
|---|---|---|---|
| L0 / L1 | Optional | Low — humans can handle block-heavy gates | Strict gate is normal |
| L2 | Recommended | Medium — block reserved for L2+ breaking changes and Tree D leaves | Strict gate at Tree D leaves |
| L3 | Strongly recommended | High — block on Tree D leaves only | Strict gate at Tree D leaves only |
| L4 | Required | Maximum — every non-Tree-D rule is advisory by default | Strict gate at Tree D leaves only; agent autonomy depends on Rules 2–3 holding |

A team running L4 with block-default gates has not actually adopted L4 — the agent's loop will stall on the first non-Tree-D advisory the gate elevates. The combination is rung-claiming per `autonomy-ladder-discipline.md` §Anti-patterns.

---

## When throughput-first does NOT apply

The philosophy is a posture, not a permission. The following always override it:

- **The risky-action interception list.** Every row blocks unconditionally; the philosophy never relaxes a row on that list.
- **Breaking changes at L3 / L4.** Long-tail consumer impact and migration-window discipline require strict gates; throughput-first defers.
- **Compensation-only rollback (mode 3).** A change that cannot be rolled back is gated strictly; throughput-first defers.
- **Auth / PII / secrets paths.** Security-reviewer specialist is required; throughput-first defers to the specialist's gate.
- **Canonical methodology content edits at L1+.** The methodology's own content is gated at the strictest level; throughput-first does not apply to changes inside this repository's `docs/`, `skills/`, or `schemas/` (per `CLAUDE.md §4`).
- **Production data-store writes initiated outside a deploy pipeline.** Per `runtime-hook-contract.md §Risky-action interception list` — production writes are blocked; the philosophy never reaches them.

A change that satisfies any of the above runs under the strict gate. The merging team should expect the cycle time to extend; the cost of strict gating is justified by the asymmetry of the failure mode.

---

## Anti-patterns

- **"Throughput-first means skip review."** The philosophy keeps review on every change; it changes only the *blocking* behaviour of advisory findings. A team that uses the philosophy to skip Reviewer entirely is committing the multi-agent-handoff anti-collusion violation, not adopting throughput-first.
- **Promoting the entire ruleset to block "to be safe."** This collapses the philosophy back to block-default; the agent's loop stalls; throughput-first is in name only. The promotion record (in the bridge's `DEVIATIONS.md`) is the audit point.
- **Indefinite follow-up backlog.** Rule 3 produces follow-ups; if the follow-ups are never picked up, the team is using the philosophy to defer work indefinitely. The `anti-entropy-discipline.md` sweeps include follow-up backlog age as a drift signal.
- **Bypassing Rule 1's escape hatches.** A team that lowers the threshold for the strict gate (e.g. treats L2 breaking changes as advisory) has not adopted throughput-first — it has dismantled the strict gate. The escape hatches are non-negotiable.
- **Throughput claim without evidence.** A team that says "we run at 3.5 PRs / engineer / day" but has no measurement of cycle time, follow-up backlog age, or block-vs-advisory ratio is asserting the posture without holding it. Per `principles.md` Principle 10 (the methodology must be measurable), the claim requires the metrics.
- **Treating the philosophy as universal.** Throughput-first is one posture among several; teams in regulated environments, teams shipping safety-critical software, and teams in early adoption (per `adoption-strategy.md`) may reasonably reject the philosophy. The rejection is recorded in the team's adoption record; an unrecorded rejection is silent abdication.

---

## Cross-references

- `docs/automation-contract.md` Rule 2.13 — the default-advisory posture this philosophy generalises.
- `docs/decision-trees.md` §Tree D — the HITL leaves throughput-first defers to.
- `docs/runtime-hook-contract.md` §Risky-action interception list — the unconditional block list that overrides throughput-first.
- `docs/breaking-change-framework.md` — the L0–L4 levels; L2+ overrides throughput-first.
- `docs/rollback-asymmetry.md` — rollback-mode-3 overrides throughput-first.
- `docs/security-supply-chain-disciplines.md` — auth/PII/secrets paths override throughput-first.
- `docs/phase-gate-discipline.md` Rule 5 — short-lived PRs presuppose phase-boundary records that actually close.
- `docs/change-decomposition.md` — the decomposition path Rule 2 prescribes.
- `docs/anti-entropy-discipline.md` — the follow-up backlog drift signal Rule 3 produces.
- `docs/autonomy-ladder-discipline.md` — the per-rung interaction table.
- `skills/engineering-workflow/references/mode-decision-tree.md` §Scenarios that force Full — the canonical-edit gate that defers throughput-first.
