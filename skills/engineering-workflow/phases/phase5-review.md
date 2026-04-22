# Phase 5: Review

## Goal

Inspect the result across five angles: correctness, quality, security, UX, and operations.

## Lean / Full minimums

### Lean minimum
- Self-review.
- Evidence-consistency review.
- Risk-note update.

### Full minimum
- Self-review.
- Quality review.
- Security / UX / operations review.
- Explicit findings resolution.

## Universal checklist

- The change matches the requirement.
- No dependent files were missed.
- No leftover debug / temp code.
- Verification results are consistent with the evidence.
- Documentation and handoff information are sufficient.
- The four surfaces show no obvious drift between each other.

## Optional: specialized audit fan-out (Full mode)

When the audit surface is too large for a single invocation (many cross-cutting dimensions, many cited identifiers, tier-mixed evidence), the Reviewer may fan out specialized audit sub-agents — security, remaining cross-cutting dimensions, evidence-reference sampling, acceptance-criterion coverage — per Pattern B in [`../references/parallelization-patterns.md`](../references/parallelization-patterns.md). Audit sub-agents inherit the Reviewer's read-only envelope (no write, no edit), their identities must differ from the Planner's and Implementer's, and the Reviewer performs fan-in synthesis + cross-cutting gap check itself. Record the fan-out in `parallel_groups`. Full-mode only.

## Optional: P5 → P6 overlap zone (Full mode)

Once `phase: review` is set and a `review_notes` skeleton exists, a **pre-filter structural scan** (per `docs/multi-agent-handoff.md §Optional machine-readable pre-filter`) and **sign-off template pre-fill** (acceptance-criterion headers only, not verdict language) may begin in working space before Gate 5 closes. Pre-filter output is binary and cheap to rerun, so this overlap is low-risk; template pre-fill is discarded and rewritten if review findings change the acceptance structure. Approval language is **not** permitted in overlap — that is canonical-role work-ahead and an anti-rationalization hazard. See [`../references/phase-overlap-zones.md`](../references/phase-overlap-zones.md).
