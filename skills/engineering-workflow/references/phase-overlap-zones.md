# Phase Overlap Zones

Prep work that Phase N+1 may legitimately begin **before** Phase N's gate passes — and the hard rule that keeps overlap from silently weakening gate discipline.

**Why this document exists.** `docs/phase-gate-discipline.md` Rule 1 closes every phase with an explicit gate. That rule says a gate **must** pass before the phase is closed — it does **not** say every piece of Phase N+1 work must wait for Phase N's gate. In practice some Phase N+1 prep work depends only on earlier-phase output that is already stable; making that prep wait pays a wall-clock cost for no safety gain. Without a named discipline, overlap either never happens (cost paid unnecessarily) or happens informally (gate discipline erodes because "we already did it anyway" becomes a gate-bypass excuse). This document names the specific overlap zones and the discipline that keeps overlap genuinely prep, not early execution.

**Scope.** Full mode only. Lean has no ceremony to overlap; Zero-ceremony has no phases to overlap across.

**Relationship to parallelization.** Orthogonal. `parallelization-patterns.md` defines fan-out **within** a phase (one role spawns multiple sub-agents in parallel, single batch, fan-in synthesis). Overlap zones define prep that starts **between** phases. The two stack: a Phase 1 fan-out can finish its fan-in just as a Phase 2 change-map skeleton begins being drafted.

---

## The core rule

An **overlap zone** is prep work that:

1. Does not depend on the prior phase's gate output.
2. Produces an artifact the downstream phase will consume.
3. Is **discarded and redone** if the prior gate fails.

Rule 3 is non-negotiable. Without it, overlap becomes a silent gate bypass — the next phase starts "anyway" and the gate verification was never the real guard. The first two rules identify overlap opportunities; the third keeps the discipline honest.

---

## Named overlap zones

Only these are named overlaps. Anything else is either normal serial work or a gate bypass.

| Overlap | Prep that may begin | Requires (from prior phase) | Must discard if prior gate fails |
|---|---|---|---|
| **P1 → P2** | Change-map skeleton: surface list + SoT-pattern list, one row per affected surface with `work: TBD` / `order: TBD` | Phase 1 investigation stable enough to name surfaces and SoT candidates (Gate 1 draft content exists) | Yes if Phase 1 surface list or SoT classification changes; partial discard if only one surface is revised |
| **P2 → P3** | Test-plan skeleton: one row per acceptance criterion (from Phase 1), `method: TBD`, `evidence: TBD` | Acceptance-criteria draft from Phase 0/1 is stable | No if ACs are stable; yes if Phase 2 adds new ACs that were not in Phase 1's draft |
| **P3 → P4** | Baseline verification environment: test harness scaffold, CI branch, screenshot baseline, metric snapshot. **Not implementation code.** | Phase 3 test categories declared (so env matches the category mix) | Yes if Phase 3 changes test method for a critical path; otherwise env reusable across minor plan changes |
| **P4 → P5** | Reviewer context-pack pre-distillation (per `context-pack.md`), reference-sampler seeding (Pattern B prerequisite) | `surfaces_touched`, `breaking_change.level`, `rollback.mode` stable; evidence-plan categories filled | Yes if Phase 4 discovers a new surface or upgrades breaking-change level (triggers Phase 1 re-entry per Rule 6) |
| **P5 → P6** | Pre-filter structural scan (per `docs/multi-agent-handoff.md §Optional machine-readable pre-filter`); sign-off template pre-fill with acceptance-criterion headers | `phase: review` set; `review_notes` skeleton exists (even if empty) | No — pre-filter output is binary and cheap to rerun; template pre-fill is discarded and rewritten |

### Zones that are **not** overlap zones

- **P0 → P1**: Phase 0 is clarification. Any "Phase 1 prep" during Phase 0 is early surface classification without the clarified requirement — it will be discarded so often that the 20% budget is always breached.
- **P6 → P7**: Sign-off is human-in-loop. Pre-filling a completion report before sign-off is premature narrative and is one of the anti-rationalization patterns (reviewer reaches for a prepared conclusion).
- **P7 → P8**: Phase 8 observation has its own trigger criteria and waits for real post-delivery signal.

---

## Constraints

### 1. No canonical-role work-ahead

Overlap is prep for the **same role's** next-phase work, or work done by an explicit non-canonical sub-agent (per `role-composition-patterns.md`) that returns distillation to the canonical role. An Implementer does not begin Phase 4 implementation code during Phase 3. A Reviewer does not draft `review_notes` approval language during Phase 4.

### 2. No manifest-field writes in overlap

Every overlap artifact begins in session-scoped working space per `phase-gate-discipline.md` Rule 5a. Manifest field writes happen **after** the prior gate passes, using the working-space draft as the source. Writing `test_plan.acceptance_map` fields during Phase 2 is a Rule-5a violation even if the content is correct.

### 3. Discard-on-fail is recorded

If the prior gate fails and overlap work is discarded, the phase's `Phase log` entry names what was discarded and why. Silent re-do without the log entry erases the signal that overlap happened and the gate caught a real problem — the two together are what make overlap safe.

### 4. ≤20% budget

Overlap prep should not exceed roughly 20% of the downstream phase's total work. If it does, overlap is doing real work instead of prep, and one of two things is happening:

- The prior phase's gate was bypassed silently.
- The overlap is no longer discardable (because the downstream phase depends on it as a completed artifact, not a draft).

Either way, treat >20% as a discipline failure and reduce the overlap scope.

### 5. Full mode only

Lean mode collapses phases already; overlap across a collapsed boundary is ceremony. Zero-ceremony has no phase structure to overlap across.

---

## Decision rule at phase boundary

At the start of Phase N, the canonical role asks:

1. Is Phase N-1's gate genuinely on track? (If not, do not overlap into Phase N+1.)
2. Is there a named overlap zone for N → N+1? (If not, do not invent one.)
3. Does the prep artifact fit the constraints above? (Working space, no manifest write, no canonical-role work-ahead, ≤20%.)
4. Will the prep be discarded cleanly if Phase N-1's gate fails? (If not, the work is not prep.)

All four must hold. A "mostly" answer is a "no."

---

## Anti-patterns

| Anti-pattern | What breaks |
|---|---|
| Implementer writes production code during Phase 3 "because the plan looks stable" | Canonical-role work-ahead; Phase 2 gate becomes advisory instead of binding |
| Reviewer drafts approval language during Phase 4 | Anti-rationalization hazard — Reviewer arrives at sign-off with a pre-committed conclusion |
| Overlap artifacts copied into canonical files before the prior gate passes | Rule 5a violation; the canonical artifact now contains unratified content |
| Prior gate fails, overlap work kept anyway "to save time" | Silent gate bypass — the exact failure mode this discipline exists to prevent |
| Overlap work exceeds 20% of downstream phase | Overlap has become execution; the gate is being bypassed by degree |
| Overlap zone invented for P0 → P1 or P6 → P7 | These zones are not overlap zones by design; "overlap" here is premature classification or premature sign-off |
| Nested overlap (Phase N overlaps into N+1 which overlaps into N+2) | Compound discard cost on any prior-gate failure; scope escapes the ≤20% budget quietly |
| Overlap recorded in canonical artifact rather than working space | Makes the discard-on-fail step visible in history — once written to canonical, discarding it requires a rewrite, which the rule forbids |

---

## Relation to other rules

| Rule / doc | Interaction |
|---|---|
| `phase-gate-discipline.md` Rule 1 (explicit gate) | Gate still binding; overlap is prep, not early pass |
| `phase-gate-discipline.md` Rule 5a (working-space discipline) | Overlap artifacts live in working space until the prior gate passes |
| `phase-gate-discipline.md` Rule 6 (phase re-entry) | If overlap prep discovers a re-entry trigger (new surface, SoT mis-classification, breaking-change upgrade), the re-entry procedure applies and all affected overlap work is discarded |
| `parallelization-patterns.md` | Orthogonal — fan-out is within-phase; overlap is between-phase. Both may occur in the same initiative |
| `multi-agent-handoff.md §Optional machine-readable pre-filter` | The P5 → P6 pre-filter scan is the primary named overlap at that boundary |
| `SKILL.md` principle 9 (batch independent tool calls) | Tool-layer analog: same independence principle applied at a different layer |
| `long-running-delegation.md §D3` (canonical-role non-idle rule) | D3's "allowed concurrent work" list cites this document as the boundary — overlap prep is permitted during a long-running delegation only within named zones and the ≤20% budget. Overlap prep into an un-named zone is still a Rule 1 violation regardless of whether a sub-agent is running |

---

## What this document is not

- **Not a license to run phases in parallel.** Gate discipline is preserved; overlap is prep work only.
- **Not a replacement for Lean mode.** If overlap is tempting in most changes, Lean mode is the answer, not between-phase pipelining.
- **Not a license to write manifest fields early.** Manifest writes are always after the relevant gate passes.
- **Not a scheduling optimization to apply by default.** The default at every phase boundary remains: close Phase N's gate, then start Phase N+1. Overlap is opt-in per zone, per change, and only when the prep artifact clearly fits the four constraints.

If overlap is producing >20% of the downstream phase's output, or cannot be cleanly discarded on prior-gate failure, or requires canonical-role work-ahead, the answer is not to bend the rule — it is to accept that this particular change does not have a safe overlap opportunity and to serialize.
