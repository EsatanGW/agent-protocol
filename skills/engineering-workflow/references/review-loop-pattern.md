# Review-Loop Pattern — Reference Walk-through

> **Status.** Non-normative reference. The binding role contracts live in [`docs/multi-agent-handoff.md`](../../../docs/multi-agent-handoff.md) (Planner / Implementer / Reviewer); the binding HITL escalation table lives in [`docs/decision-trees.md`](../../../docs/decision-trees.md) §Tree D. This file is a worked example of how the Reviewer iterates with the Implementer in an agent-to-agent loop until convergence — and how the loop terminates without spinning indefinitely.

---

## What problem does this solve

When the Reviewer is a separate agent identity (cross-identity Reviewer per `multi-agent-handoff.md` §single-agent-anti-collusion-rule), review is no longer a single human pass — it is an iteration. The Implementer ships a manifest + diff + evidence; the Reviewer reads, finds issues, returns them; the Implementer addresses each issue and returns updated artefacts; the cycle repeats until the Reviewer surfaces no blocking findings.

Without a structured loop, three failure modes recur:

- **LGTM-after-one-pass.** The Reviewer issues `approvals[0].verdict: pass` after a single read without exercising the change. Detection: `adoption-anti-metrics.md` §LGTM-only review.
- **Indefinite spin.** The Implementer addresses each finding, the Reviewer surfaces a new finding tier each pass, the change never converges. Iteration cap missing; both agents exhaust their context budgets without producing a decision.
- **Self-rationalising loops.** The Implementer treats Reviewer findings as suggestions to argue rather than constraints to address. Each iteration adds `review_notes[*].rebuttal` rather than fixing the underlying issue. The change "converges" by Reviewer fatigue, not by resolution.

The pattern is named after the article framing (a Ralph-Wiggum loop — the implementer keeps trying until the reviewer stops finding issues), but the discipline is the failure-mode list above; the name is a mnemonic.

---

## The reference shape (in pseudocode)

```bash
# Each iteration is a complete review cycle.
# The Implementer's identity is fixed across iterations; the Reviewer's identity is fixed across iterations;
# anti-collusion (multi-agent-handoff.md §single-agent-anti-collusion-rule) is enforced once at iteration 0.

iter=0
max_iter=5    # recommended cap; teams may set lower, never higher without escape-hatch justification
state="pending"

while [ "$state" != "approved" ]; do
  iter=$((iter + 1))
  if [ "$iter" -gt "$max_iter" ]; then
    state="escalated"
    record_escalation "$manifest" "review_loop_no_converge"
    break
  fi

  # Implementer side.
  manifest_revision="$(implementer_produce_revision \
    --previous_findings "$reviewer_findings" \
    --apply_fix_or_rationale)"
  evidence_collected="$(implementer_collect_evidence "$manifest_revision")"

  # Hand-off to Reviewer.
  reviewer_findings="$(reviewer_read \
    --manifest "$manifest_revision" \
    --evidence "$evidence_collected")"

  # Reviewer state machine.
  blocker_count="$(echo "$reviewer_findings" | jq '[.[]|select(.severity=="block")]|length')"
  advisory_count="$(echo "$reviewer_findings" | jq '[.[]|select(.severity=="advisory")]|length')"

  if [ "$blocker_count" -eq 0 ] && all_advisory_acked "$reviewer_findings"; then
    state="approved"
    record_approval "$manifest_revision" "$reviewer_identity" "$iter"
  fi

  # Else loop continues with reviewer_findings as the next iteration's input.
done
```

The shape is not the script — it is the **convergence contract**: each iteration ends with either approval (zero blockers, every advisory acked or rationaled), continuation (blockers or unacked advisories remain), or escalation (cap exceeded). No iteration ends with "looks fine, ship it" without one of those three terminal states.

---

## Convergence conditions

A single iteration concludes (Reviewer returns) with one of three states. The **state machine is closed** — no fourth state exists.

### Approved

- Zero `severity: block` findings remain.
- Every `severity: advisory` finding is paired with one of:
  - `acked: true` — Implementer accepts the finding and either applied a fix in this iteration or recorded a follow-up issue per `throughput-first-merge-philosophy.md` Rule 3.
  - `rationale: "<one-sentence justification>"` — Implementer rejects the finding with a stated reason that the Reviewer accepts. The rationale is written in the manifest's `review_notes[*].rationale`, never spoken-only.
- The Reviewer's `approvals[*]` row is added to the manifest with `approver_role`, `iteration_count`, and `approved_at`.

### Continuation

- One or more `severity: block` findings remain, OR
- One or more `severity: advisory` findings remain unacked / unrationaled.
- The Implementer reads the findings, addresses each, and produces the next iteration. The Reviewer reads the new artefacts; the cycle repeats.

### Escalation

- Iteration cap (`max_iter`) reached.
- The change is not approved; the manifest carries `escalations[*].trigger: review_loop_no_converge`; a human is paged per `decision-trees.md §Tree D`.
- The escalation does not invalidate the work — the Implementer's diffs and the Reviewer's findings are persisted; the human reviews the trail and decides whether to extend the cap, re-scope the change, or close it.

---

## Iteration cap and why it is bounded

The cap (recommended five iterations) is bounded for three reasons:

1. **Diagnostic signal.** If five rounds of iteration have not converged, the underlying disagreement is structural — the Reviewer and Implementer are reading the change differently, and a sixth round will not reveal what five rounds did not. Escalating to a human surfaces the structural disagreement.
2. **Context-budget protection.** Each iteration adds findings, fixes, and evidence to both agents' working contexts. Beyond five, the next-iteration agent is reading more rationale than original artefact; signal-to-noise collapses.
3. **Loop-detection.** A five-cap is the smallest cap at which oscillation can be detected — three iterations could be coincidence, five is a pattern. If iterations 1, 3, 5 surface findings about the same field that iterations 2, 4 reverted, the change is oscillating; escalation is the right move.

Teams may set `max_iter` lower (typical: 3 for low-risk changes) but raising the cap above five requires the team's adoption record to name the justification — typically a domain where multi-iteration convergence is structurally expected (e.g. complex schema migrations).

---

## Local + cloud reviewer composition

The pattern supports multiple Reviewer identities concurrently. The article that named the philosophy describes a "local self-review + cloud agent reviewer" composition — the Implementer runs an in-loop Reviewer on the local working tree before the cross-identity Reviewer reads the manifest.

The composition is governed by `multi-agent-handoff.md §Composable specialist sub-agent roles`:

- **Local self-review** — the Implementer spawns a non-canonical reference-sampler sub-agent (Pattern 4 per `reference-implementations/roles/role-composition-patterns.md`) that re-reads the diff against the manifest's intent. This is **not** a canonical Reviewer pass; it is a self-check that surfaces obvious gaps before the cross-identity Reviewer reads. Findings from this pass are filed as Implementer self-review notes, not as Reviewer findings.
- **Cross-identity Reviewer** — the canonical Reviewer per `AGENTS.md §7` reads the manifest, exercises sampling rights per `ai-operating-contract.md`, and produces `approvals[*]`. This is the binding pass; the loop's convergence is determined here.
- **Specialist sub-agent reviewers** — security-reviewer / performance-reviewer / architect specialists per `reference-implementations/roles/specialist-roles-registry.md` participate when their domain is in scope. Each specialist produces its own findings; the canonical Reviewer aggregates them into `review_notes[*]` and decides convergence.

Composition does not relax the convergence contract — every Reviewer (canonical or specialist) returns findings into the same iteration; the cycle terminates only when **all** Reviewers' findings reach the approved state.

---

## Anti-patterns this reference rejects

- *Self-approval after self-review.* The local self-review sub-agent is the Implementer's; its "no findings" is not an approval — only the cross-identity Reviewer's `approvals[*]` row counts. A team that treats self-review as approval has collapsed Implementer ≡ Reviewer per `multi-agent-handoff.md §single-agent-anti-collusion-rule`.
- *Cap raise to escape escalation.* A team that hits the cap and raises `max_iter` to push through is masking a structural disagreement. The escalation is the signal; the cap raise is the silencing of the signal.
- *Findings-as-conversation.* The Reviewer's role is not to discuss; it is to surface findings into manifest fields. A finding that lives only in chat is not a finding; the loop's audit trail is the manifest's `review_notes[*]`, not the conversation log.
- *Rationale-by-handwave.* Per the contract above, an advisory finding's `rationale` is one sentence with a stated reason. "We discussed and agreed" is not a rationale — it does not survive future audit. The Reviewer should reject vague rationales and re-surface the finding.
- *Cross-iteration finding deletion.* A finding that was real in iteration 2 cannot be silently dropped in iteration 4. If the underlying issue was resolved, iteration 4's `review_notes[*]` records the resolution. If the finding was wrong, iteration 4 records the rationale for retraction.
- *Treating local self-review as a substitute for the cross-identity pass.* Local self-review reduces the work of the cross-identity Reviewer; it does not substitute for it. A change that ships with only local self-review evidence (no cross-identity `approvals[*]`) has not crossed the L3 rung threshold per `autonomy-ladder-discipline.md` §L3.
- *Reviewer-as-author.* Per `AGENTS.md §7`, the Reviewer has no write tools. A Reviewer that "fixes the issue while reading" has crossed into Implementer; the change's role separation is collapsed; the manifest is no longer multi-agent. The Reviewer's contribution is findings, not commits.

---

## Where this fits in the methodology

- **Iteration shape for `docs/multi-agent-handoff.md` §single-agent-anti-collusion-rule** — that rule says identities cannot collapse; this loop is what those distinct identities do once separated.
- **Convergence shape for `docs/decision-trees.md` §Tree D** — the cap-exceeded escalation maps to the "agent autonomy ceiling reached" leaf.
- **L3+ rung dependency in `docs/autonomy-ladder-discipline.md`** — L3 mandates a cross-identity Reviewer; this loop is how that Reviewer operates without spinning.
- **Throughput-first interaction (`docs/throughput-first-merge-philosophy.md`)** — Rule 1's default-advisory posture means most Reviewer findings are advisory; the loop terminates when blockers are zero and advisories are acked or rationaled, not when zero findings remain.
- **Pairs with `references/back-pressure-loop.md`** — back-pressure governs hook output; this loop governs Reviewer output. Both reject decorative "all good" signals; both require terminal states (silent / one-line / approved / continuation / escalation).
- **Pairs with `references/application-driven-loop.md`** — that loop governs the Implementer's verification; this loop governs the Reviewer's audit. They run in parallel within one iteration: Implementer captures application-driven evidence, Reviewer queries it.
