# Long-Running Delegation Discipline

What the canonical role must do when a sub-agent invocation is expected to run longer than one prompt-cache window — and how to keep mid-flight visibility without collapsing the role contract.

**Why this document exists.** Existing execution-layer rules cover *when* to fan out (`parallelization-patterns.md` Patterns A/B) and *when* to delegate canonical Implementers in parallel (`cluster-parallelism.md` Pattern C). They govern the **spawn** discipline (single batch, context pack) and the **synthesis** discipline (fan-in, cross-cutting gap check). They do not govern what happens **in between**: after the canonical role has spawned a sub-agent whose work takes meaningful wall-clock time, what discipline governs the wait? Without a named rule here, three failure modes recur — (1) the canonical role sits idle, its own session eventually exceeds a cache window or a runtime timeout, and the entire change stalls at an invisible boundary; (2) the sub-agent runs long with no intermediate signal, so the canonical role cannot detect drift until the whole invocation returns (too late); (3) the user loses visibility and cannot redirect without killing the session. This document names the discipline.

**Scope.** Full mode only. Sub-agent composition is Lean / Zero-ceremony exempt per `reference-implementations/roles/role-composition-patterns.md §When role composition is appropriate`; a Lean-mode long-running delegation is either a mode-selection failure or a scope under-assessment.

**Relationship to parallelization and overlap.** Orthogonal. `parallelization-patterns.md` governs how a fan-out is spawned (single batch, context pack) and synthesized (fan-in discipline). `phase-overlap-zones.md` governs what prep can begin across phase boundaries. This document governs the **time axis within a single delegation** — independent of whether the delegation is serial (Patterns 1–4), parallel fan-out (Patterns 5–6), or canonical-role multi-delegation (Pattern C / Pattern 7).

---

## When this applies

Apply this discipline when **any** of the following hold:

- A sub-agent invocation is expected to exceed one prompt-cache window (commonly ~5 minutes — the same TTL `parallelization-patterns.md §Cache-window rule` relies on).
- The sub-agent's scope is not broken into reviewable checkpoints and the canonical role has no plan for what to do while it runs.
- The sub-agent returns only at termination, with no intermediate artifact path the canonical role (or the user) can inspect.

**Do not apply** to:

- Short sub-agent invocations that return within one cache window — the overhead of the discipline exceeds its benefit.
- Phase 8 observer spawns — those have their own trigger criteria and time horizon (see `phase8-trigger-guide.md` and `docs/post-delivery-observation.md`); this document's disciplines apply as specific instances, but the Phase 8 trigger guide remains the primary entry.
- Between-phase prep — that is `phase-overlap-zones.md`'s domain.
- Within-batch fan-out spawn timing — that is `parallelization-patterns.md §Cache-window rule`'s domain.

---

## The three disciplines

### D1. Checkpoint-bounded delegation

**Rule.** The scope handed to a single sub-agent invocation must fit within one cache window. If the planned scope would exceed that bound, split it into segments — each segment is a separate invocation whose structured return the canonical role reads before spawning the next.

Sibling rule: `parallelization-patterns.md §Fan-in discipline` already states *"if the returns are too large to read in full, the decomposition was wrong — reduce scope per sub-agent, do not skim."* D1 is the **time-dimension analog** of that space-dimension rule: *if the invocation is too long to run without mid-flight visibility, the decomposition was wrong — split into checkpoints, do not let it run blind.*

**Lower bound.** Segments under ~2 minutes are too small — the overhead of spawn-return-respawn dominates useful work. If the scope is genuinely small, use a single invocation and accept the short wait. D1 is a floor, not a factor to maximize.

**Natural checkpoint boundaries.** Prefer scope boundaries that already correspond to a reviewable return (per-file, per-cluster, per-acceptance-criterion), not arbitrary clock interrupts. A clock-interrupt segment returns at an unnatural point; its "structured return" is not structurable.

Anti-patterns:
- "Let it run as long as it needs; I'll handle whatever comes back." — the no-checkpoint failure.
- Splitting purely by wall-clock duration rather than by natural scope boundaries.

### D2. Artifact-grounded progress

**Rule.** A long-running sub-agent writes intermediate progress to a **session-scoped working-space path** (per `docs/phase-gate-discipline.md §Rule 5a`). The path is:

- **Known to the canonical role at spawn time** — given in the sub-agent's Task Prompt, not discovered on return.
- **Append-only** — progress lines or per-step files added as the sub-agent works; never overwritten, so the canonical role tailing the path sees consistent state.
- **Structured** — each entry carries a step name, status, and a short note. Not free-form logs.
- **Session-scoped, not canonical** — Rule 5a's working-space discipline binds: a progress artifact is *not* a manifest field and *not* an evidence artifact until the canonical role reads it and decides what (if anything) to promote.

Purpose: the canonical role can inspect progress without re-invoking the sub-agent, and the user can read the same path directly. No new storage concept is introduced — this is Rule 5a applied to a new artifact class.

**Failure-signalling.** The last written progress entry is the primary signal when a sub-agent returns an error, times out, or otherwise terminates unexpectedly. A sub-agent that crashes mid-run leaves the last successful checkpoint in the artifact; the canonical role can resume from that checkpoint rather than restarting from scratch.

Anti-patterns:
- Progress emitted only to the sub-agent's stdout / invocation-result channel. That collapses D2 back into "read at termination."
- Progress written to a canonical path (manifest field, ROADMAP row, evidence artifact) mid-flight. Rule 5a forbids pre-gate canonical writes; the canonical role promotes a subset of progress content *after* the segment's return.
- Progress written with no schema — the canonical role then cannot grep for a failure / stall signal.

### D3. Canonical-role non-idle rule

**Rule.** During a long-running sub-agent invocation, the canonical role must have either **defined concurrent work** or **a defined polling plan**. Idle wait is prohibited.

**Allowed concurrent work** (non-exhaustive):

- Tail the D2 progress artifact and react to checkpoints (e.g. adjust the next segment's task prompt before spawning it).
- Pre-distill the context pack for a subsequent fan-out, if one is planned.
- Draft working-space artifacts for the next phase within `phase-overlap-zones.md` bounds (≤20% budget, overlap-zone-named prep only).
- Spawn an independent sub-agent for a genuinely parallel sub-task (still within `parallelization-patterns.md §Cache-window rule` — concurrent spawn in the same batch, not serial).

**Prohibited concurrent work:**

- Canonical-role work-ahead as defined by `phase-overlap-zones.md §Rule 1` — an Implementer does not begin next-phase implementation while a current-phase sub-agent runs.
- Writing manifest fields based on in-flight sub-agent progress — `phase-gate-discipline.md §Rule 5a` still binds.
- Starting an unrelated canonical-role activity in the same session that competes for context budget with the returning sub-agent's synthesis.

D3 is the **within-delegation analog** of `docs/ai-operating-contract.md §11` (narration is not action). §11 closes the *pre-tool-call* silence gap (narrate → end turn without tool call). D3 closes the *post-tool-call* silence gap (fire delegation → end turn / idle while delegation runs). Both are fabrication-by-silence failure modes; neither subsumes the other.

Anti-patterns:
- Canonical role narrates "delegating to sub-agent for the refactor" and ends the turn. (§11 if before tool call; D3 if after tool call.)
- Canonical role fires the delegation and then immediately does nothing until the sub-agent returns — the session eventually hits a runtime timeout at an invisible boundary.
- Canonical role "polls by re-invoking the sub-agent" — re-invocation creates a *new* identity per `role-composition-patterns.md §Invocation lifecycle`; the progress is not in the new invocation. Read the D2 artifact instead.

---

## Failure modes this discipline addresses

| Failure | Root cause | Discipline |
|---|---|---|
| Canonical-role session times out while sub-agent still running | No checkpoint bound on the sub-agent's scope | D1 |
| User cannot see mid-flight progress; has to kill session to redirect | Sub-agent emits no intermediate artifact | D2 |
| Sub-agent drifts halfway through; canonical role finds out only on return | No canonical-role monitoring of in-flight state | D2 + D3 |
| Canonical role narrates delegation, ends turn; looks like silent session break | Post-tool-call silence gap | D3 (symmetric with `ai-operating-contract.md §11`) |
| Invocation-handle reused as "the still-running sub-agent" for checkpoint poll | Misreads one-shot invocation lifecycle | D2 reads the artifact path; see `role-composition-patterns.md §Invocation lifecycle` and that doc's anti-pattern rows |

---

## Relation to named scenarios

The discipline is general; three existing named scenarios are specific applications:

| Scenario | How D1/D2/D3 applies |
|---|---|
| **Phase 8 observer** (`phase8-trigger-guide.md`, `docs/post-delivery-observation.md`) | D1: observer scope bounded to a single trigger; exceeding the horizon requires a new observer spawn, not an unbounded wait. D2: findings append to `post_delivery.production_findings[]` (canonical) after the observer returns; mid-flight working notes stay in Rule-5a working space. D3: canonical role does not idle during the horizon — returns to other work, reads the artifact at trigger time. |
| **Pattern C cluster halt-all** (`cluster-parallelism.md §4 Discovery-loop handling`) | D1: each cluster's scope is bounded by `scope_files`; a cluster whose scope would exceed a cache window is a decomposition problem, not a halt problem. D3: when a cluster enters `blocked_discovery`, the Planner's halt-all behavior is D3 in action — it must have been reading cluster status artifacts (D2) to detect the block, and its concurrent work during in-progress clusters is exactly what D3 requires. |
| **Reviewer Tier-1 send-back** (`docs/multi-agent-handoff.md §Conflict resolution`) | D1: Tier-1 send-back is structurally a checkpoint — the Reviewer returns a scoped finding; the Implementer's re-work is a fresh, bounded invocation (new identity per invocation lifecycle). D3: while the returning Implementer works, the Reviewer's concurrent work is preparing the second audit pass (re-reading the updated diff, pre-distilling the re-review context pack). |

None of these three scenarios needs modification; this document is the general rule they each implement in a specific form.

---

## Capability-category mapping

Tool-agnostic capability requirements:

- **Background spawn** — ability to start a sub-agent invocation asynchronously and continue doing work in the canonical role's session.
- **Working-space artifact read** — standard file read, applied to D2's Rule-5a path. Every runtime that supports the methodology already provides this.
- **Sub-agent progress write** — ability for the sub-agent to write to the D2 artifact path mid-run. Most file-write capabilities satisfy this; stdout-only capabilities do not.
- **Addressable sub-agent (optional)** — ability to send a halt / redirect signal to a specific running sub-agent. Not required for D1/D2/D3; when available, enables richer D3 polling patterns (halt-on-drift, not wait-for-segment-end).

### When a runtime lacks background spawn

The canonical role cannot run concurrent work during the sub-agent invocation — the runtime serializes. D1 and D2 still apply:

- D1 becomes the *only* meaningful discipline — split the sub-agent's scope into small-enough segments that the canonical role's serial wait per segment is tolerable.
- D2 still applies — the sub-agent writes progress to the working-space path, and the canonical role reads the artifact *after* each segment's return. Mid-flight canonical-role inspection is impossible, but the user retains visibility.
- D3 collapses — "concurrent work" is impossible, so "defined polling plan" reduces to "read segment return and decide."

### When a runtime lacks addressable sub-agent

- D1 / D2 fully apply.
- D3 cannot rely on mid-flight interrupts; checkpoints (segment ends) become the only control point. The canonical role plans for redirect **at the next checkpoint**, not immediately.

---

## Anti-patterns

| Anti-pattern | What breaks |
|---|---|
| Canonical role fires delegation, narrates, ends turn without concurrent work or polling plan | D3; symmetric with `ai-operating-contract.md §11` fabrication-by-silence |
| Sub-agent scope sized to maximize parallelism without checkpoint bounds | D1; single-invocation cache-window exceedance |
| Progress emitted only to stdout / invocation-result channel | D2; no mid-flight visibility |
| Canonical role polls by re-invoking the sub-agent | Misreads invocation lifecycle (`role-composition-patterns.md §Invocation lifecycle`); a new invocation is a new identity, not a continuation |
| Checkpoints sized below ~2 minutes each | Segment overhead dominates; discipline cost exceeds benefit — single invocation is better |
| Concurrent work during delegation is canonical-role work-ahead | `phase-overlap-zones.md §Rule 1` violation |
| Mid-flight writes from sub-agent progress into manifest fields | Rule 5a violation; working-space → canonical promotion happens only after canonical role reads the full artifact at segment return |
| Applying D1/D2/D3 in Lean / Zero-ceremony to "be safe" | Sub-agent composition is Full-only; adding the discipline where composition itself does not apply is ceremony, not safety |

---

## Relation to other rules

| Rule / doc | Interaction |
|---|---|
| `parallelization-patterns.md §Cache-window rule` | Sibling: that rule binds fan-out **spawn timing**; D1 binds single-invocation **runtime scope**. Both cite the same cache-window primitive. |
| `parallelization-patterns.md §Fan-in discipline` | D1 is the time-dimension analog of "reduce scope per sub-agent, do not skim." |
| `phase-gate-discipline.md §Rule 5a` | D2 reuses Rule-5a working-space mechanics; no new storage concept. |
| `phase-overlap-zones.md §Rule 1` (no canonical-role work-ahead) | D3's allowed-concurrent-work list respects this rule — overlap prep is permitted only within named zones and the ≤20% budget. |
| `docs/ai-operating-contract.md §11` (narration is not action) | Symmetric: §11 closes pre-tool-call silence; D3 closes post-tool-call silence. Neither subsumes the other. |
| `reference-implementations/roles/role-composition-patterns.md §Invocation lifecycle` | Reuse: invocation is one-shot; handles point at already-terminated invocations. D3 polling uses the D2 artifact path, not handle reuse. |
| `cluster-parallelism.md §4 Discovery-loop handling` / `§5 Planner assembles and spawns Reviewer` | Pattern C halt-all and completion-detection are D3 instances (Planner polls status via the working-space path, reacts to `blocked_discovery` or `completed`). |
| `phase8-trigger-guide.md` + `docs/post-delivery-observation.md` | Phase 8 observer is a D1/D2/D3 instance at the post-delivery horizon. |
| `skills/engineering-workflow/phases/subagent-strategy.md` | Phase-file bridge pointing here from sub-agent-relevant phases. |

---

## What this document is not

- **Not a new role.** All three disciplines are held by the canonical role that spawned the delegation. No new role identity is introduced.
- **Not a new canonical rule.** It is execution-layer, time-bounded discipline. Canonical docs (`AGENTS.md`, `docs/multi-agent-handoff.md`, `docs/ai-operating-contract.md`, `docs/glossary.md`) are deliberately time-agnostic. If a future audit finds this gap warrants canonicalization (e.g. a new `ai-operating-contract.md §12`), that is a separate Full-mode change, not in this document's scope.
- **Not a new storage mechanism.** D2 reuses Rule 5a; no new working-space type, no new schema field.
- **Not applicable in Lean or Zero-ceremony.** Sub-agent composition is Full-only per `role-composition-patterns.md §When`; a Lean-mode long-running delegation is a mode-selection failure — fix the mode, do not add the discipline.
- **Not a license to proliferate checkpoints.** Segments under ~2 minutes are over-decomposition; the discipline is a floor, not a factor to maximize.
