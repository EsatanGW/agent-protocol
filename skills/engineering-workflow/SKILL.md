---
name: engineering-workflow
description: Tool-agnostic engineering workflow skill. Use for any real engineering change (feature, bugfix, refactor, migration, rollout). Provides surface-first analysis, source-of-truth discipline, Lean/Full modes, phase minimums, artifact templates, and evidence-driven delivery. Capability categories (file read, code search, shell execution, sub-agent delegation) map to whichever tools the host runtime provides.
---

# Engineering Workflow

Use this skill when the executing agent is handling a real engineering change, not just answering a question.

## Quick operating contract

Before anything else, the universal operating contract for this plugin lives in [`AGENTS.md`](../../AGENTS.md) at repo root. It covers honest reporting, scope discipline, SoT, surface-first analysis, evidence requirements, Change Manifest, stop conditions, and behavior boundaries. The rest of this skill is the **execution layer** for that contract.

If this skill is loaded without `AGENTS.md` being read, read `AGENTS.md` first.

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
- `references/core-principles.md`
- `references/source-of-truth-quick-reference.md`
- `references/cross-cutting-quick-check.md`
- `references/parallelization-patterns.md` — when and how to fan out **within** a phase (Full mode only)
- `references/context-pack.md` — shared-context mechanism for fan-out sub-agents
- `references/phase-overlap-zones.md` — prep work that may begin **between** phases before the prior gate passes (Full mode only; hard discard-on-fail rule; ≤20% budget)

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

### Lean mode
Use for:
- Small bugfixes
- Single contract fixes
- Small-scope refactors
- Low-risk UI adjustments
- Single-surface or low-consumer changes

Goals:
- Fast clarification
- Minimal artifacts
- Verification preserved
- No ceremony for its own sake

### Full mode
Use for:
- New features
- Multi-surface change
- Multi-repo / multi-consumer work
- Migration / rollout / rollback sensitive changes
- Formal sign-off or handoff needs

Goals:
- Full artifact trail
- Explicit change map
- Acceptance coverage
- Residual risk and operations review

See also:
- `references/mode-decision-tree.md`
- `references/misuse-signals.md`
- `references/discovery-loop.md`
- `references/resumption-protocol.md`

## Decision table

| Condition | Suggested mode |
|-----------|----------------|
| Tiny single-file fix, no public behavior impact | No skill or ultra-lean |
| Small bugfix, few consumers, easy verification | Lean |
| Any user-visible / API / schema public behavior change | Lean or Full depending on surface count |
| 2+ surfaces or many consumers | Full |
| Migration / rollout / rollback notes required | Full |
| Needs handoff / completion narrative | Full |
| Unclear risk | Start Lean, upgrade quickly if needed |

## Tool-category guidance by phase

This skill names **capability categories**, not specific tool names.
Map each category to whatever the current agent runtime provides.

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
- Security
- Performance
- Observability
- Testability

These are not separate surfaces; they cut across all surfaces.

Quick reference:
- `references/cross-cutting-quick-check.md`

## Lean workflow

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
Read: `./phases/phase4-implement.md`
Supplement: `./phases/debugging-process.md`

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

Reference:
- `references/phase8-trigger-guide.md`

## Phase minimums

Phase-specific Lean / Full minimums are embedded in the phase docs and also summarized in:
- `references/phase-minimums/phase0-minimums.md`
- `references/phase-minimums/phase1-minimums.md`
- `references/phase-minimums/phase2-minimums.md`
- `references/phase-minimums/phase3-minimums.md`
- `references/phase-minimums/phase4-minimums.md`
- `references/phase-minimums/phase5-minimums.md`
- `references/phase-minimums/phase6-minimums.md`
- `references/phase-minimums/phase7-minimums.md`

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

### Lean mode artifacts
Usually enough:
- minimal spec note
- minimal task list
- verification summary
- delivery summary

### Full mode artifacts
Usually required:
- spec
- plan
- test plan
- test report
- completion report

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
