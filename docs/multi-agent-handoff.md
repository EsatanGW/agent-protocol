# Multi-Agent Handoff

> **English TL;DR**
> Defines how multiple AI agents (or AI + human co-authors) collaborate on the same change through a shared, progressively-filled Change Manifest. Names three canonical roles — Planner, Implementer, Reviewer — purely by responsibility, never by tool or model. Covers manifest progression, read/write ownership per phase, conflict escalation, and the minimum handoff checklist.

This document answers one question: **when a single change is completed by multiple agents (or multiple humans) in sequence, who can write which manifest fields at which phase, and who cannot?**

Without a contract, multi-agent collaboration degrades into:

- Each agent rewrites the whole manifest, the latest overwriting the previous.
- Downstream agents redo judgments upstream already made (e.g. re-locating SoTs).
- Nobody knows "who wrote the current manifest and whether it is true."

This document **does not name any specific agent / model / platform** — it defines role contracts only.

---

## Three canonical roles

These roles are **defined by responsibility, not by identity.**
The same agent can play different roles in different phases; a human can play any of these roles too.

### Planner

**Responsibilities:**

- Read the requirement and identify surfaces.
- Build the SoT map and consumer list.
- Assess breaking-change level and rollback mode.
- Decide Lean vs Full mode.
- Produce the "front half" of the manifest: identity, surfaces, sot_map, consumers, risk.

**Must not do:**

- Write implementation code (even if it looks trivial).
- Decide implementation details beyond specifying evidence categories.

**Required fields when handing off downstream:**

- `change_id`, `title`, `phase: plan`.
- `surfaces_touched` (every entry has `role` specified).
- `sot_map` (every entry has `pattern` specified).
- `breaking_change.level` if ≥ L1.
- `rollback.mode`.
- `evidence_plan` (categories enumerated; paths not yet required).

### Implementer

**Responsibilities:**

- Modify code per the Planner's manifest.
- Collect evidence and populate `evidence_plan.artifacts`.
- When a gap in the plan is discovered, **stop** and run the Discovery Loop (see `references/discovery-loop.md`); do not expand the manifest unilaterally.

**Must not do:**

- Re-classify surfaces / re-judge SoT without escalation.
- Change `breaking_change.level` (that is the Planner's judgment).
- Delete any fields the Planner wrote.

**Additional required fields when handing off downstream:**

- `phase: review`.
- `evidence_plan.artifacts` (every entry has a path).
- `implementation_notes` (if any drift from the plan).
- `scope_deltas` (if the Discovery Loop outcome was adopted).

### Reviewer

**Responsibilities:**

- Verify that the Implementer's evidence actually exists and actually substantiates the claims.
- Check cross-cutting concerns (security, performance, observability, testability, errors, build-time risk).
- Decide sign-off or send back.
- Record residual risk.

**Must not do:**

- Write implementation code (if an issue is found, send back to the Implementer).
- Rewrite the Planner's or Implementer's fields (can only flag disagreement in `review_notes`).

**Additional required fields when handing off downstream:**

- `phase: signoff`, or return to `phase: plan / implement`.
- `review_notes`.
- `residual_risk`.
- `approvals` (sign-off record).

---

## Field read/write ownership matrix

Field "ownership" is the key to preventing agents from overwriting each other.

| Field | Planner | Implementer | Reviewer |
|-------|---------|-------------|----------|
| `change_id`, `title` | write | read | read |
| `phase` | write (advance to plan) | write (advance to review) | write (advance to signoff or send back) |
| `surfaces_touched` | write | read + flag discovery | read |
| `sot_map` | write | read | read |
| `breaking_change` | write | read + propose upgrade | read + propose upgrade |
| `rollback` | write | read | read + annotate execution risk |
| `evidence_plan.categories` | write | read | read |
| `evidence_plan.artifacts` | — | write | read + sample-check |
| `implementation_notes` | — | write | read |
| `review_notes` | — | — | write |
| `residual_risk` | draft | augment | finalize |
| `waivers` | — | propose | approve (approver must be human) |

**Rule:** except for `phase`, a downstream role cannot delete or rewrite fields written upstream.
If there is disagreement: **open a new manifest + `supersedes`**, not overwrite in place.

---

## Manifest progression phases

A manifest moves from birth to delivery through the following stages, each with a **minimum field threshold**:

```
draft → plan → test_plan → implement → review → signoff → deliver → observe
 │       │         │           │          │        │         │         │
Planner             Planner  Implementer Reviewer Reviewer Implementer  any
 picks up            or       picks up    picks up sign-off  delivery   observer
                    Tech lead
```

Minimum threshold when entering each stage:

| Entering stage | Minimum required |
|----------------|------------------|
| plan | surfaces_touched, sot_map, consumer list |
| test_plan | evidence_plan.categories, acceptance_criteria |
| implement | plan approved, test_plan exists |
| review | all evidence_plan.artifacts have paths |
| signoff | review_notes has no blocking issue |
| deliver | handoff_narrative exists |
| observe | applies only under Phase 8 trigger conditions (see `phase8-trigger-guide.md`) |

Threshold not met → the downstream role **must not** take over; send back upstream.

---

## Conflict resolution

When the Implementer finds a problem in the Planner's judgment, or the Reviewer finds the Implementer's evidence insufficient:

### Tier 1: annotate

Do not modify upstream fields; instead **flag disagreement** within your own field:

```yaml
implementation_notes:
  - type: planner_disagreement
    field: sot_map[0]
    original: "schema-defined"
    proposed: "transition-defined"
    rationale: "During implementation, the state transitions turned out
                to be constrained by more than just the schema."
    status: pending_review
```

### Tier 2: escalate

If the disagreement affects scope decisions (breaking level, rollback mode, SoT classification), stop and return to the previous stage:

- Implementer → return `phase: plan` for the Planner to re-evaluate.
- Reviewer → return `phase: implement` or `plan`.

Returning is not failure; it is discipline. The AI agent must **return proactively** and not expand its own role boundary to patch things over.

### Tier 3: supersede

If the entire manifest's premise is wrong (e.g. the requirement itself was misread):
**do not overwrite** — create a new manifest:

```yaml
# new manifest
change_id: 2026-04-20-voucher-expiry-v2
supersedes: [2026-04-17-voucher-expiry]
supersede_reason: "Requirement actually demands tenant-scoped expiry;
                   original manifest assumed global."
```

The original manifest is retained as `status: retired`, not deleted (historical record).

---

## Read-in vs write obligations

### Downstream agent's minimum actions on handoff

**Reading is mandatory (cannot be skipped):**

1. Read the manifest handed over from upstream in full.
2. If the manifest references spec / plan / test report, read those too.
3. Compare the manifest against repo reality (check for drift: manifest says "A was changed" but the repo has not moved).
4. If drift exists, **stop and report** — do not proceed.

**Prohibited:**

- Reading only the summary because the manifest is long.
- Assuming upstream is correct and starting work immediately.
- Treating upstream judgment as unchallengeable.

### Write discipline

- Every time `phase` is advanced, `last_updated` must be updated.
- `authors` array appends (not overwrites); a new agent joining leaves its identifier.
- Any Implementer or Reviewer judgment must be traceable to a specific file path / evidence / commit hash — narrative alone is not enough.

---

## Interface with human co-authors

Humans, within this contract, are also a type of "agent role" subject to the same rules.
The only differences:

- Humans can serve as an `approver` (waivers, breaking-change L3/L4).
- AI cannot.
- A human's `identifier` is a git email or team account; an AI's `identifier` must include model ID / agent name / execution timestamp so we can trace which AI version wrote it.

---

## Anti-patterns

- **Single agent does everything:** one agent writes from Plan through Deliver; the role contract is nullified.
- **Silent takeover:** downstream starts work without reading the upstream manifest.
- **Overwriting fields:** downstream edits upstream fields on disagreement (should go through conflict resolution).
- **AI self-approving:** an AI acting as Reviewer approves itself (approver must be human).
- **Long-stale manifest:** `delivered` but Phase 8 observation is empty a month later.

---

## Relationship to other documents

- `ai-operating-contract.md` — single-agent behavior contract (this document is the inter-agent contract).
- `change-manifest-spec.md` — field semantics.
- `automation-contract.md` — automated verification of each stage threshold.
- `references/resumption-protocol.md` — single-agent takeover after a session break.
- `templates/change-manifest.example-multi-agent-handoff.yaml` — a full-progression example.
