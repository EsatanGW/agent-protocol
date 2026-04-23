# Operational Cheat Sheet

> **Purpose.** A single-page skim surface for "what do I do *right now*." Not a rule spec — rules live in the normative docs linked below. Use this when you need the decision in under 30 seconds; use the linked docs when you need the full reasoning.

---

## Per-role top 5

### Planner

1. **Tag the four core surfaces.** User / system-interface / information / operational — at least one marked `role: primary`. See [`docs/surfaces.md`](surfaces.md).
2. **Map SoT patterns.** Every information piece gets a pattern number (1–10, or 4a); record in `sot_map`. See [`docs/source-of-truth-patterns.md`](source-of-truth-patterns.md).
3. **Judge breaking change by worst-case consumer, not common case.** L0 additive / L1 behavioral / L2 structural / L3 removal / L4 semantic reversal. See [`docs/breaking-change-framework.md`](breaking-change-framework.md).
4. **Pick rollback mode from the most irreversible surface.** Mode 1 reversible / Mode 2 forward-fix / Mode 3 compensation-only. See [`docs/rollback-asymmetry.md`](rollback-asymmetry.md).
5. **Design `evidence_plan` per primary surface, not by habit.** Screenshot for user / contract test for system / migration dry-run for information / log sample for operational. See [`schemas/change-manifest.schema.yaml`](../schemas/change-manifest.schema.yaml).

### Implementer

1. **Read manifest + Task Prompt in full before editing anything.** No skim starts. See [`agents/implementer.md`](../agents/implementer.md).
2. **Verify every cited identifier via code-search before citing.** Function, type, file path, config key, URL — all require a concrete `path:line` or URL resolution. See [`docs/ai-operating-contract.md`](ai-operating-contract.md) §2a.
3. **Fill `evidence_plan.artifacts` with real paths, not prose.** Every `planned` entry on a primary surface becomes `collected` with `artifact_location` before handoff.
4. **On plan gap: stop, don't expand.** Discovery loop + Rule 6 decide re-entry phase. See [`docs/phase-gate-discipline.md`](phase-gate-discipline.md) Rule 6.
5. **Before handoff: clear the 5-question pre-handoff self-check.** Vague answers are failing answers. See [`docs/multi-agent-handoff.md`](multi-agent-handoff.md) §Pre-handoff self-check.

### Reviewer

1. **Open every `artifact_location`. Don't trust prose.** Evidence audit is the core job. See [`agents/reviewer.md`](../agents/reviewer.md).
2. **Run at least one verification-only command yourself.** Reading the Implementer's summary is trust; verification is you with a shell.
3. **Check anti-rationalization triggers.** Six hard send-back conditions: perfect-confidence / hedging / unsubstantiated `pass` / read-only review / edit-through-back-door / thin residual-risk. Any one ⇒ send back.
4. **Exercise the sampling right.** Pick any cited identifier and require the Implementer to reproduce the exact code-search command plus output.
5. **`residual_risk` lists ≥ 3 items or the review is incomplete.** Real changes carry real risk; "none identified" is a red flag, not a pass.

---

## Five-second checks (apply to every non-trivial change)

| Check | Answer in 5 seconds |
|---|---|
| Which of the 4 core surfaces does this touch? | user / system-interface / information / operational (one or more; at least one primary) |
| Which SoT pattern governs the information changed? | pattern 1–10 or 4a (or "no information surface touched") |
| Worst-case consumer's pain level? | L0 / L1 / L2 / L3 / L4 |
| Can rollback return to pre-change state? | Mode 1 (yes, seconds) / Mode 2 (no, fix forward) / Mode 3 (no, compensate) |
| Is there ≥ 1 real `artifact_location` per primary surface? | yes / no (no = handoff blocked) |

---

## When you see X, go to Y

| Situation you're in | Read this |
|---|---|
| "I don't know if I should use this methodology at all" | [`docs/onboarding/when-not-to-use-this.md`](onboarding/when-not-to-use-this.md) |
| User-visible change, needs i18n / screenshot proof | [`docs/surfaces.md`](surfaces.md) User surface + evidence types |
| Schema change, multiple consumers | [`docs/breaking-change-framework.md`](breaking-change-framework.md) + [`docs/source-of-truth-patterns.md`](source-of-truth-patterns.md) |
| Public API, third-party clients, SDK version bump | breaking-change-framework.md Path B / Path C + [`docs/rollback-asymmetry.md`](rollback-asymmetry.md) |
| Already-shipped mobile binary or long-lived client | rollback-asymmetry.md Mode 2 + long-lived-client notes |
| Something will hit payment / push / on-chain / real-world | rollback-asymmetry.md Mode 3 + compensation_plan field |
| Multiple agents hand this change between each other | [`docs/multi-agent-handoff.md`](multi-agent-handoff.md) roles + field ownership |
| Stuck on "can this phase be closed?" | [`docs/phase-gate-discipline.md`](phase-gate-discipline.md) six rules + gate template |
| Plan turned out wrong mid-implementation | phase-gate-discipline.md Rule 6 decision table |
| Want to reuse knowledge from a past change | CCKN pattern — [`docs/cross-change-knowledge.md`](cross-change-knowledge.md) |
| Runtime-specific glue (which tool maps to which capability) | [`docs/bridges/`](bridges/) per-runtime bridges |

---

## When to skip this sheet entirely

If all of the following hold, skip the methodology:

- Diff < 5 lines
- No public behavior change
- No cross-surface impact
- No long-lived consumer

That path is documented in [`docs/onboarding/when-not-to-use-this.md`](onboarding/when-not-to-use-this.md). Don't force Lean mode on work that needs no mode.

---

## What this sheet is *not*

- Not a rule spec — rules live in the linked docs, and those docs win on conflict.
- Not a runtime guide — per-runtime install and tool-mapping lives in [`docs/bridges/`](bridges/).
- Not a ceremony enforcement — if the cheat sheet feels like overhead on a task, the task probably belongs in the "skip" bucket above.

---

## See also

- [`docs/onboarding/orientation.md`](onboarding/orientation.md) — longer onboarding walkthrough with the 11 principles and the navigation map
- [`AGENTS.md`](../AGENTS.md) — the universal operating contract (reach: all runtimes)
- [`docs/principles.md`](principles.md) — the 11 first principles the whole methodology follows
