# Resumption Protocol

When an agent takes over the same engineering task after an interruption, follow this protocol to rebuild context before doing anything else.

**Why this protocol exists.** A session was interrupted, a new session is starting, or a new role is taking over. The temptation is to re-read every prior artifact "just to be safe." That temptation is the failure mode this protocol pushes back against: a verbose handoff prompt plus a complete re-read of all artifacts commonly exhausts the new session's context before any real work begins. Read only what the chosen resume mode requires. The Change Manifest — not the artifact set — is the state snapshot; if it is insufficient to resume from, fix the Manifest, not the reading ritual.

## Step 0: interpret the incoming prompt

Before applying any of the steps below, identify which of two prompt shapes triggered this resumption. The two shapes demand different interpretation rules, and conflating them is the source of a distinct class of silent-break failures.

### Two shapes

- **AI-authored handoff prompt** — produced by an outgoing session using [`../templates/handoff-prompt-template.md`](../templates/handoff-prompt-template.md). Dense pointer block: identity header, resume-mode declaration, one-line next action, open items, read block. Steps 1–6 below apply mechanically from the prompt's fields.
- **Human-originated directive** — the user types a short instruction like `continue`, `resume`, `go`, `繼續`, or a one-line restatement of the next action. Short on content but unambiguous on intent: act on whatever comes next.

### A short human directive is not a passive update

When the resumption is triggered by a bare `continue` / `resume` / `go` / `繼續` / equivalent, the correct response is to **execute `Manifest.next_action`** under whichever resume mode Steps 1–2 select. It is **not** a "no response requested" signal; it is a request to act.

Inbound `system-reminder` blocks, runtime-state change notices (e.g. MCP server connect / disconnect lists, deferred-tool availability updates), and other platform-injected content that may appear in the same turn as the user's directive are **not** user messages. They do not cancel, dilute, or reinterpret the user's text. The user's directive — however short — is what the session responds to.

**The failure this rule prevents.** An incoming session receives a one-word resume prompt, sees heavy system-reminder noise in the same turn, and mis-reads the combination as "user just updated my context; no action requested." The session silently ends its turn. From the user's perspective this is indistinguishable from a runtime crash. The rule above makes the interpretation mechanical: human directive intent is honored regardless of system-reminder volume.

### If the directive is genuinely ambiguous

If no Manifest is in scope, no prior phase header anchors the session, and no active change is identifiable, do **not** silently end the turn. Declare Lazy mode, read whichever Manifest the session's opening artifact points at, and surface the Manifest's `next_action` for the user to confirm or correct. A one-sentence clarifying question is always safer than silence.

### Recommended human-side format (non-mandatory)

Users can reduce ambiguity by writing `resume: <verb> <object>` instead of bare `continue`. Example: `resume: spawn the planner sub-agent for Stage D.1 round 2`. The explicit verb + object form removes the "short-prompt + system-noise → passive-update misjudgment" failure pattern entirely. This is a recommendation, not a requirement — bare `continue` remains a valid directive, and the rule above is what makes it safe.

See [`../../../docs/ai-operating-contract.md`](../../../docs/ai-operating-contract.md) §11 for the symmetric rule on the *outgoing* side (narration is not action). Step 0 handles the incoming-interpretation side; §11 handles the outgoing-execution side. Together they close both ends of the session boundary.

## Step 1: confirm that this is actually the same task
- Is the task name the same?
- Is the source of truth the same?
- Are the affected surfaces the same?

If not, treat it as a new task — do not reuse the old artifacts directly.

## Step 2: declare the resume mode

The incoming session's **first action** is to name which resume mode applies. The mode determines what must be read before work continues. Reading before mode is declared is a protocol violation.

### Decision table

| Situation | Resume mode | What to read (in addition to this prompt) |
|---|---|---|
| Same phase, same role, interrupted mid-work | **Lazy** | Change Manifest only |
| Advancing to a new phase | **Targeted** | Manifest + the artifacts owned by the entering phase (see below) |
| A new role is taking over (e.g. Planner → Implementer) | **Role-scoped** | Manifest + the upstream role's single output artifact (see below) |
| Change Manifest is missing, obviously stale, or drift is suspected | **Full** | The full list below — and declare *why* explicitly |
| Lean mode resume | **Minimal** | Lean-spec note + the current task-list item |

### Per-phase artifact map (for Targeted mode)

When advancing to a new phase, read only the artifacts that phase consumes as input — not every artifact ever produced.

| Entering phase | Artifacts to read beyond the Manifest |
|---|---|
| Phase 1 Investigate | Spec (if the user supplied one) |
| Phase 2 Plan | Investigation summary (already in Manifest) |
| Phase 3 Test Plan | Plan |
| Phase 4 Implement | Plan + test plan |
| Phase 5 Review | Plan + test report + diff of files actually changed |
| Phase 6 Sign-off | Review notes |
| Phase 7 Deliver | Sign-off record |
| Phase 8 Post-delivery | Completion report |

If a listed artifact is missing from the Manifest's pointer block, that is a Manifest-drift signal — not permission to read more widely. Stop and fix the Manifest (see Step 2a).

### Per-role artifact map (for Role-scoped mode)

| Incoming role | Upstream role's single output artifact |
|---|---|
| Planner (receiving a spec) | Clarification / spec |
| Implementer | Plan + test plan |
| Reviewer | Implementation notes + test report |

### Full-resume fallback

Full mode is for disaster recovery only: the Manifest is absent, obviously stale, or drift is suspected. When Full mode is declared, read:

- The spec.
- The plan.
- The test plan.
- The latest test report.
- The completion report (if one exists).

**Declaring Full mode is a named act.** The first message of the resumed session must state *why*. Examples: "Manifest absent from the repo." "Manifest `last_updated` is 14 days ago; git log shows changes since." "The handed-over manifest fails schema validation." A Full resume with no stated reason is a gate-discipline failure (see `docs/phase-gate-discipline.md` Rule 1).

## Step 2a: manifest-completeness check

Before committing to any mode except Full:

- Does the Manifest carry pointers to every artifact the chosen mode needs?
- Does the relevant phase-specific field (`handoff_narrative` for late phases, `implementation_notes` for Phase 4, etc.) answer "what comes next" without requiring an artifact re-read?

If the Manifest cannot answer these without reading other artifacts, **stop and fix the Manifest first**. The Manifest is the state snapshot; if it is insufficient to resume from, it is incomplete. Re-entering the chosen mode after a Manifest patch is cheaper than resuming on a stale state.

See `docs/change-manifest-spec.md` §State-snapshot discipline for the pointer-completeness checklist.

## Step 2b: context-budget rule

Before reading any artifact beyond the Manifest, estimate the cumulative read size (rough: total word count across everything listed, including the handoff prompt itself). Compare it mentally to the runtime's usable context window.

- If the read list plausibly exceeds ~30% of the session's context: **downgrade one tier** (Full → Role-scoped, Role-scoped → Targeted, Targeted → Lazy) and state the downgrade explicitly in the first message.
- If even Lazy mode plausibly exceeds 30%: the Manifest is oversized — a drift signal. Stop, request Manifest compaction, and resume after.

The percentage is advisory — context sizes differ across runtimes — but naming a threshold forces the check to actually happen rather than drifting into "I'll just read it all."

## Step 3: determine the current mode
- Is this task still Lean?
- Or has the scope grown enough to warrant Full?

## Step 4: determine current progress
At minimum, answer:
- Which tasks are complete?
- What evidence already exists?
- What verification is still missing?
- Has residual risk changed?

## Step 5: decide whether any phase must be re-run
Rewind is required when:
- Scope has expanded.
- New public-behavior impact has appeared.
- The source of truth has changed.
- A new consumer has been discovered.
- Existing evidence has been invalidated.

See `docs/phase-gate-discipline.md` Rule 6 for the re-entry decision table.

## Step 6: restate what comes next
Do not just resume patching. State explicitly:
- Resume mode (from Step 2).
- Current mode (Lean / Full).
- Current phase.
- Next action.
- Missing evidence.

## Relationship: resumption vs re-entry

Resumption and re-entry are not the same. Resumption (this doc) is about **reattaching context across a session break** without re-opening a phase. Re-entry (`docs/phase-gate-discipline.md` Rule 6) is about **re-opening a closed phase** because new information invalidated prior work. A session can resume without re-entry; a re-entry always resumes afterward into the re-opened phase.

## See also

- [`../templates/handoff-prompt-template.md`](../templates/handoff-prompt-template.md) — compact template for the outgoing session to use when producing a handoff prompt.
- [`lazy-resume-checklist.md`](lazy-resume-checklist.md) — per-mode 60-second checklist for the incoming session.
- [`../../../docs/change-manifest-spec.md`](../../../docs/change-manifest-spec.md) §State-snapshot discipline — how the Manifest serves as the single state snapshot a resume should need.
- [`../../../docs/phase-gate-discipline.md`](../../../docs/phase-gate-discipline.md) Rule 6 — re-entry protocol for re-opening closed phases.
