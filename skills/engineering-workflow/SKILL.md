---
name: engineering-workflow
description: Tool-agnostic engineering workflow skill. Use for any real engineering change (feature, bugfix, refactor, migration, rollout). Provides surface-first analysis, source-of-truth discipline, four execution modes (Zero-ceremony / Three-line delivery / Lean / Full), phase minimums, artifact templates, and evidence-driven delivery. Capability categories (file read, code search, shell execution, sub-agent delegation) map to whichever tools the host runtime provides.
---

# Engineering Workflow

Use this skill when the executing agent is handling a real engineering change, not just answering a question.

## Quick operating contract

Before anything else, the universal operating contract for this plugin lives in [`AGENTS.md`](../../AGENTS.md) at repo root. It covers honest reporting, scope discipline, SoT, surface-first analysis, evidence requirements, Change Manifest, stop conditions, and behavior boundaries. The rest of this skill is the **execution layer** for that contract.

If this skill is loaded without `AGENTS.md` being read, read `AGENTS.md` first.

## On-demand reading

This skill follows progressive disclosure: only `SKILL.md` (this file) and the universal operating contract in `AGENTS.md` are read on every session. The deeper layers — phase guides, references, templates, examples — are read **on the trigger that needs them**, not eagerly. Eager loading is a context tax: every reference page that is not load-bearing for the current decision crowds out the task itself, and a manifest that crowds out the task is the failure mode that the §Manifest size ceiling discipline already names from the artifact side; the same logic applies to the skill layer.

**Default reading set (always loaded).**

- `AGENTS.md` (root) — universal operating contract.
- `skills/engineering-workflow/SKILL.md` (this file) — execution layer.

**Trigger-based reading (loaded when the trigger fires).**

| Trigger | Read this |
|---|---|
| Entering Phase N | `phases/phaseN-<name>.md` |
| Choosing the workflow mode for a non-trivial change | `references/mode-decision-tree.md` |
| About to fan out non-canonical sub-agents (Pattern A/B) | `references/parallelization-patterns.md` + `references/context-pack.md` |
| Phase 4 has 3+ file-disjoint clusters (Pattern C) | `references/cluster-parallelism.md` |
| Resuming a session with a prior manifest | `references/resumption-protocol.md` + `references/lazy-resume-checklist.md` |
| About to write an artifact | `templates/<artifact>-template.md` |
| Stuck on a manifest field; need one worked example | `examples/change-manifest.example-<scenario>.yaml` |
| Long-running sub-agent invocation | `references/long-running-delegation.md` |
| Phase-overlap prep before prior gate passes | `references/phase-overlap-zones.md` |

The Quick refresher list below is a **trigger index**, not a reading list — it names *where* to find each artifact when the trigger fires, not that all of them should be loaded simultaneously.

**Anti-patterns this discipline rejects.**

- *Eagerly reading all `references/` at session start "for context."* References are organised by trigger; pick the one whose trigger fires.
- *Re-reading a phase guide in every reply within the same phase.* Read once at phase entry; it stays in working memory for the duration of the phase.
- *Loading multiple worked examples for comparison shopping.* Pick one example whose scenario most closely matches; if comparison is genuinely necessary, load two — never the full directory.

## About this skill

This skill is the execution layer built on top of the public method in `docs/`.
The public method explains how to think; this skill explains how to act.

It is tool-agnostic: wherever a capability is named (e.g. "file read", "code search"), map it to whatever the current runtime provides.

## Core operating principles

1. Manage change, not just code
2. Find source of truth before patching consumers
3. Classify affected surfaces before choosing a mode
4. Pick the lightest workflow that still preserves quality
5. Never claim completion without verification and evidence
6. If public behavior changed, handoff obligations increase
7. Close every phase with an explicit gate; track multi-phase work in the repo's `ROADMAP.md`; commit at every passed gate when version control is available (`docs/phase-gate-discipline.md`)
8. When the user hands over a spec document, read it in full before planning and re-reference it at every subsequent phase
9. **Batch independent tool calls in a single message.** Serialize only when a later call needs the output of an earlier one. Unnecessary serialization pays the runtime's per-call round-trip cost for no gain; this is a real, measurable contributor to long-running stages. The same rule extends to the **sub-agent layer** in Full mode: a parallel fan-out (`references/parallelization-patterns.md` Patterns A and B) spawns all sub-agents in one batch — serial spawning breaks the prompt-cache window and erases the parallelization benefit.
10. **Narration is not action.** When you state an intended action at a handoff or role-transition point (e.g. "calling X", "about to run Y"), the next emitted tokens must be the tool call itself — not a new sentence and not end-of-turn. See `docs/ai-operating-contract.md` §11 for the full rule; this is the specific failure mode that produced real-world "session stopped responding" crashes at role-handoff points.

Quick refresher:
- `references/source-of-truth-quick-reference.md`
- `references/parallelization-patterns.md` — when and how to fan out non-canonical sub-agents **within** a phase (Patterns A/B, Full mode only)
- `references/context-pack.md` — shared-context mechanism for fan-out sub-agents
- `references/cluster-parallelism.md` — when the Planner spawns **multiple canonical Implementers** in parallel for file-disjoint Phase 4 clusters (Pattern C, Full mode only; distinct from non-canonical sub-agent fan-out)
- `references/phase-overlap-zones.md` — prep work that may begin **between** phases before the prior gate passes (Full mode only; hard discard-on-fail rule; ≤20% budget)
- `references/long-running-delegation.md` — discipline for long-running sub-agent invocations: checkpoint-bounded scope, artifact-grounded progress, canonical-role non-idle rule (Full mode only; applies to Patterns 1–7 when invocation exceeds one cache window)

## The four core surfaces

Always begin by marking which surfaces are touched:
- User surface — UI, routes, interaction, copy, state visibility, i18n, a11y
- System interface surface — APIs, events, jobs, integrations, public contracts
- Information surface — schema, fields, enum, validation, config, feature flags
- Operational surface — logs, audit, telemetry, docs, migration, rollout, rollback

If the project uses domain-specific extensions, map them back to these four first, then note the extension.

## Trigger conditions

### Always trigger this skill when
- The task touches 2+ files or 2+ surfaces
- The task has public behavior impact
- The task changes contract / schema / state / enum / user-visible behavior
- The task needs reusable evidence or handoff
- The task is a feature, bugfix, refactor, migration, or rollout-sensitive change

### Usually trigger this skill when
- You need investigation before implementation
- You expect to write at least a minimal artifact
- You need cross-repo or cross-module coordination
- You need explicit residual risk notes

### Do NOT trigger this skill when
- Pure Q&A or research with no engineering change
- Non-engineering content creation
- Single-file typo or tiny wording fix with no public behavior risk
- Disposable low-risk script with no consumer or contract impact
- Pure environment inspection like checking versions, ports, or logs

## First 60 seconds command block

Before touching code, answer these in order:
1. What kind of task is this? feature / bugfix / refactor / migration / investigation
2. Which surfaces are affected?
3. Where is the source of truth?
4. Who are the main consumers?
5. Is there public behavior impact?
6. Should this be Lean or Full?
7. What is the minimum artifact set?
8. What evidence must exist before completion?

Use together:
- `references/startup-checklist.md`
- `references/session-opener-snippet.md`

## Mode selection

The methodology has **four canonical modes**, in rising ceremony. Canonical definitions: `docs/glossary.md §Execution mode`. Mode-selection logic (forced-Full / forced-Lean / forced-Three-line / forced-Zero-ceremony scenario tables) is the **source of truth** at `references/mode-decision-tree.md` — consult it rather than this skill file for edge cases.

### Zero-ceremony mode
Use for:
- Pure Q&A / research / reading (no files modified)
- Typo / single-string copy fix (diff < 5 lines, no surface crossing)
- One-off throwaway scripts
- Environment checks

Artifact minimum: none — the commit message is the record.

### Three-line delivery
Use for:
- i18n key **value** change (same semantics)
- New log at an existing call site
- Dependency patch bump with no API change
- README / docstring edit that does not change behavior
- Known-safe config tweak

Artifact minimum: a three-line record (What changed / How verified / Residual risk) in the commit message or PR description. No spec, no ROADMAP row.

### Lean mode
Use for:
- Small bugfixes with a clear root cause
- Single contract fixes
- Small-scope refactors in a well-tested area
- Low-risk UI adjustments
- Single-surface, ≤ 1-consumer changes with ≤ 5-minute verification

Artifact minimum: `templates/lean-spec-template.md` + `templates/lean-verification-template.md` + `templates/lean-delivery-template.md`. Lean has **six steps** (Lean-0 … Lean-5), but they are **not** phases — phase-gate discipline applies once at Lean-5 delivery, not per step (`docs/phase-gate-discipline.md §Ceremony scaling`).

### Full mode
Use for:
- New features
- Multi-surface change
- Multi-repo / multi-consumer work
- Migration / rollout / rollback-sensitive changes
- Formal sign-off or handoff needs
- Any forced-Full trigger (see `references/mode-decision-tree.md §Scenarios that force Full`)

Artifact minimum: spec + plan + test plan + test report + completion report + Change Manifest. Nine phases (Phase 0 … Phase 8); every phase ends with a named gate; ROADMAP row required per phase.

See also:
- `references/mode-decision-tree.md` — **the** canonical decision tree + forced-Full / forced-Lean / forced-Three-line / forced-Zero-ceremony scenario tables
- `references/misuse-signals.md`
- `references/discovery-loop.md`
- `references/resumption-protocol.md`

## Decision table (quick reference)

For mode selection, go to [`references/mode-decision-tree.md`](references/mode-decision-tree.md) — it is the canonical decision tree and the source of truth for the forced-Full / forced-Lean / forced-Three-line / forced-Zero-ceremony scenario tables. Do not maintain a parallel summary here.

## Tool-category guidance by phase

This skill names **capability categories**, not specific tool names.
Map each category to whatever the current agent runtime provides.

Runtime bridges may also expose each phase as a named command (slash command, Custom Mode, persona prompt, prompt prefix). The runtime-neutral alias registry — `clarify`, `investigate`, `plan`, `testplan`, `implement`, `review`, `signoff`, `deliver`, `observe`, plus role-bound variants like `plan-as-architect` and `review-as-security` — lives in [`../../docs/phase-command-vocabulary.md`](../../docs/phase-command-vocabulary.md). Bridges map alias_ids to their own command surface; this skill defines the underlying phase semantics.

### Clarify
Prioritize capabilities:
- File read
- Code / text search
- Conversation / session history lookup (when user references earlier work)
- Ask-the-user (only when information cannot be recovered from the codebase)

### Investigate
Prioritize capabilities:
- Code / text search
- File read
- Web fetch (if the request originates from a web UI or external docs)
- Shell execution (only for runtime / build / log facts)
- Sub-agent delegation, optional: Full mode with 3+ surfaces may fan out one read-only investigator sub-agent per surface per Pattern A (see `references/parallelization-patterns.md` and `phases/subagent-strategy.md`); the Planner performs fan-in synthesis, cross-cutting gap check, and records the fan-out in manifest `parallel_groups`. Lean mode does not fan out.

**Optional CCKN consultation at Phase 1 startup.** If the change's surfaces / libraries / external APIs overlap topics catalogued under `docs/knowledge/`, read the matching CCKNs before tracing the main flow (non-Zero-ceremony tiers only); otherwise no-op. Canonical rule with match-handling, refresh obligation, and anti-patterns: `docs/cross-change-knowledge.md §When to query a CCKN`. Procedural bridge: `phases/phase1-investigate.md §Optional startup: CCKN consultation`.

### Plan
Prioritize capabilities:
- Task list
- File write (for plan artifact)
- File read

### Test Plan
Prioritize capabilities:
- File write
- File read
- Task list

### Implement
Prioritize capabilities:
- Patch / edit
- File write
- Shell execution
- Long-running process management
- Canonical-role delegation, optional: Full mode with 2+ file-disjoint clusters may use Pattern C per `references/cluster-parallelism.md` — the Planner spawns 2–4 canonical Implementers in a single batch, each implementing one cluster; a single Reviewer downstream performs a cross-cluster cross-cutting gap check. Distinct from Patterns A/B (which spawn non-canonical sub-agents); Pattern C spawns full canonical Implementer identities. Lean mode does not use Pattern C.

### Review
Prioritize capabilities:
- Code / text search
- File read
- Sub-agent delegation (for large review scopes or when an independent reviewer stance is useful). Full mode may fan out specialized read-only audit sub-agents per Pattern B (see `references/parallelization-patterns.md`): security audit, remaining cross-cutting dimensions, evidence-reference sampling, acceptance-criterion coverage. The Reviewer performs fan-in synthesis, applies the anti-rationalization rules, runs the cross-cutting gap check, and records the fan-out in `parallel_groups`. Audit sub-agents inherit the Reviewer's read-only envelope; their identities must differ from every canonical role's. Lean mode does not fan out.

### Sign-off / Deliver
Prioritize capabilities:
- File read
- Code / text search
- File write

## Source-of-truth rule

Before implementing any change, identify which source-of-truth pattern applies:
- Schema-defined truth
- Config-defined truth
- Enum / status-defined truth
- Contract-defined truth
- UI-defined truth (rarer, but valid)

Common anti-patterns to watch for:
- Dual write without coordination
- Consumer deriving its own truth
- Cached truth becoming stale
- Documentation drifting from implementation
- Translation keys drifting from canonical copy

Quick reference:
- `references/source-of-truth-quick-reference.md`

## Cross-cutting rule

For every non-trivial engineering change, ask whether the change has implications for:
- Security — new trust boundaries, auth, validation, or secret-handling concerns?
- Performance — hot paths, heavy rendering, large queries, caching, or async work?
- Observability — could someone reconstruct what happened if it fails?
- Testability — can the behavior be reliably verified and repeated?
- Error handling — new failure modes that propagate across surfaces (data → API → UI → user → ops)?

These are not separate surfaces; they cut across all surfaces. If any answer is "yes", mention it in the plan or review output.

## Lean workflow

Lean mode has **six steps**. They are steps, not phases — the word "phase" is reserved for Full mode. Phase-gate discipline (`docs/phase-gate-discipline.md`) applies **once** at Lean-5, not per step. A ROADMAP row is optional for a single-change Lean initiative; see `docs/phase-gate-discipline.md §Ceremony scaling`. If mid-way the scope turns out to need Full, use the Lean → Full step / phase mapping in `docs/glossary.md §Lean → Full step / phase correspondence` to re-enter at the right Full phase.

### Lean-0: Clarify
Minimum output:
- Affected Surfaces
- Main Flow Summary
- Public Behavior Impact
- Open Questions if any

### Lean-1: Investigate
Minimum output:
- Source of truth
- Main consumers
- Impact file list
- Chosen approach

### Lean-2: Minimal Plan
Minimum output:
- Task list
- Verification plan
- Risk note

### Lean-3: Implement
- Implement against the minimal task list
- Spot-check each meaningful change

### Lean-4: Verify
- Cover all changed behavior
- Save minimum evidence

### Lean-5: Deliver Summary
Minimum output:
- Changed behavior
- Verification summary
- Evidence summary
- Residual risk / follow-up

Lean templates:
- `templates/lean-spec-template.md`
- `templates/lean-verification-template.md`
- `templates/lean-delivery-template.md`

## Full workflow

### Phase 0: Clarify
Goal: define boundaries, surfaces, blockers, assumptions.
Read: `./phases/phase0-clarify.md`
Supplement: `./phases/question-template.md`

### Phase 1: Investigate
Goal: trace flow, contracts, source of truth, and consumers.
Read: `./phases/phase1-investigate.md`

### Phase 2: Plan
Goal: write a full change map, task order, and verification strategy.
Read: `./phases/phase2-plan.md`

### Phase 3: Test Plan
Goal: map acceptance criteria to tests and evidence.
Read: `./phases/phase3-testplan.md`

### Phase 4: Implement
Goal: implement against the approved plan and collect evidence.
Read: `./phases/phase4-implement.md` (includes the built-in debugging process used by the fix-retest loop)

### Phase 5: Review
Goal: correctness / quality / security / UX / operations review.
Read: `./phases/phase5-review.md`
Supplement: `./phases/subagent-strategy.md`

### Phase 6: Sign-off
Goal: acceptance, surface coverage, residual risk.
Read: `./phases/phase6-signoff.md`

### Phase 7: Deliver
Goal: completion report, handoff, commit guidance.
Read: `./phases/phase7-deliver.md`

### Phase 8: Post-delivery observation (optional but important)
Not every task needs this, but consider it explicitly when:
- public behavior changed
- migration happened
- financial / auth / high-risk flows changed
- staged rollout or feature flag was involved

If relevant, leave a follow-up note for:
- T+24h
- T+72h
- T+7d

Full criteria, observation timeline, and exit conditions: `docs/post-delivery-observation.md`.

## Phase minimums

Phase-specific minimums for Lean and Full mode. Each row is the minimum content required before the phase gate can close; `docs/phase-gate-discipline.md` governs the gate *process*. Zero-ceremony and Three-line delivery have no phase structure (see the [artifact guidance](#artifact-guidance) section).

| Phase | Lean minimum | Full minimum |
|-------|--------------|--------------|
| **0 — Clarify** | Affected surfaces · Main flow summary · Public behavior impact · Open questions (if any) | Complete draft spec · Acceptance-criteria draft · Blockers / assumptions / boundaries |
| **1 — Investigate** | Source of truth · Main consumers · Impact file list · Chosen approach | Main flow · Source-of-truth / consumer map · Impact file list · Candidate solutions · Recommended approach with trade-offs |
| **2 — Plan** | Minimal task list · Verification plan · Risk note | Overview · Affected surfaces · Change map · Dependency order · Full task list · Verification strategy · Spec coverage matrix |
| **3 — Test Plan** | Minimal verification table · Public behavior coverage · Evidence expectations | Full test plan · Acceptance mapping · Evidence methods · Explicit regression coverage |
| **4 — Implement** | Implement tasks · Verify changed behavior · Save minimum evidence | Implement against approved plan · Run full test plan · Collect evidence systematically · Write test report |
| **5 — Review** | Self-review · Evidence consistency review · Risk-note update | Self-review · Quality review · Security / UX / operations review · Explicit findings resolution |
| **6 — Sign-off** | Confirm changed behavior verified · Write residual risk | Acceptance sign-off · Surface coverage review · Evidence summary · Residual risk summary |
| **7 — Deliver** | Delivery summary · Evidence summary · Follow-up / risk note | Completion report · Handoff narrative · Files to commit · Suggested commit message |

Phase docs (`phases/phase0-clarify.md` … `phases/phase7-deliver.md`) contain the same content with narrative guidance; this matrix is the quick reference.

## Resumption rule

If a session resumes mid-task, do not continue patching blindly. Before any work:

- **Interpret the incoming prompt first.** AI-authored handoff prompts (dense pointer block, mode already declared) and human-originated directives (`continue`, `繼續`, `resume: <verb> <object>`) demand different interpretation. A short human directive is a request to act on `Manifest.next_action`, not a passive context update — runtime-injected content (`system-reminder`, MCP state changes, deferred-tool lists) in the same turn is not part of the directive. See `references/resumption-protocol.md` Step 0.
- **Declare a resume mode** (Lazy / Targeted / Role-scoped / Full / Minimal) and read only what that mode requires. Re-reading every artifact is the failure mode this rule replaces; the session-handoff context-collapse failure pattern is specifically what the mode system exists to prevent.
- **The Change Manifest is the state snapshot.** If the manifest cannot answer "what comes next" without opening another file, fix the manifest — do not compensate by reading more. A manifest that crosses the runtime's single-file read ceiling (~25,000 tokens / ~2,000 lines) is itself failing the snapshot role; compact in place or split via `part_of` before relying on it (see `docs/change-manifest-spec.md` §Manifest size ceiling).
- **Respect the context budget.** If the planned reads exceed roughly 30% of the session's context window, downgrade one tier and say so explicitly.

Reference:
- `references/resumption-protocol.md` — full decision table, per-phase / per-role read lists, Full-mode fallback.
- `references/lazy-resume-checklist.md` — 60-second checklist for the incoming session.
- `templates/handoff-prompt-template.md` — compact handoff format for the outgoing session.

## Misuse protection

Actively avoid these mistakes:
- Turning small work into Full mode ceremony
- Treating high-risk work as Lean patching
- Using the skill for non-engineering tasks
- Continuing after interruption without reloading context
- Producing a verbose handoff prompt that re-explains prior phases and lists many files to read, instead of pointing at the Change Manifest (see `templates/handoff-prompt-template.md`)
- Starting Phase N+1 work during Phase N outside a named overlap zone, or keeping overlap prep when the prior gate fails — both collapse into silent gate bypass (see `references/phase-overlap-zones.md`)

Reference:
- `references/misuse-signals.md`

## Artifact guidance

### Zero-ceremony mode artifacts
- None. The commit message (if any) is the record.

### Three-line delivery artifacts
- A three-line record next to the commit or PR description:
  - What changed
  - How verified
  - Residual risk

### Lean mode artifacts
Usually enough:
- minimal spec note (`templates/lean-spec-template.md`)
- minimal task list
- verification summary (`templates/lean-verification-template.md`)
- delivery summary (`templates/lean-delivery-template.md`)

### Full mode artifacts
Usually required:
- spec
- plan
- test plan
- test report
- completion report
- Change Manifest (per `docs/change-manifest-spec.md`)

## Worked examples to emulate

- `docs/examples/worked-example.md`
- `docs/examples/bugfix-example.md`
- `docs/examples/refactor-example.md`
- `docs/examples/migration-rollout-example.md`
- `docs/examples/game-dev-example.md`

## Final reminder

This skill is not meant to make engineering work bureaucratic.
It is meant to make the executing agent:
- slower when slowness prevents failure
- faster when a heavy workflow would be wasteful
- evidence-driven
- stronger at handoff and continuity
- more reliable across real engineering change
