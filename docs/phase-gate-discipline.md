# Phase-Gate Discipline

> **Purpose.** The rest of the methodology (`surfaces.md`, `source-of-truth-patterns.md`, `breaking-change-framework.md`, `rollback-asymmetry.md`, the phase files in `skills/engineering-workflow/`) defines *what* each phase produces. This file defines *how* a phase is **closed** — the explicit verification gate, the record, the roadmap entry, the commit, and the doc-review-before-plan rule. It is normative for any agent executing work with this plugin.
>
> Everything here is tool-agnostic and capability-category based. The discipline survives renaming commits, switching version-control systems, or moving from CLI to IDE runtimes, because it is expressed in terms of **what must be true at a gate**, not what tool ran the check.

---

## Why this exists

The plugin has always said "evidence before completion" (see `principles.md` and `skills/engineering-workflow/references/core-principles.md`). That rule fires at *the end* of a change. It does **not** by itself answer four questions that come up inside a multi-phase change:

1. **When is a phase allowed to end?** — Not just "when the work feels done" but when a specific, named check passes.
2. **Where is the history of those gates recorded?** — Not in the committer's head; not in one-off scratch notes; in a durable tracking artifact.
3. **When do we commit?** — Not ad-hoc; at gates, so the version-control history matches the phase history.
4. **What happens when the user hands the agent a spec document?** — Not "skim and start coding"; a review-before-plan discipline so the plan actually reflects the spec.

This file answers those four.

---

## The five rules

### Rule 1 — Every phase ends with an explicit gate

A phase is not closed by declaration. It is closed by a **gate check** that either **passes** or **fails**. A passing gate has three properties:

- The check is a **named, repeatable action**, not a feeling. Examples: "`grep -P '\p{Han}'` over the batch returns zero lines," "the test file referenced in the Change Manifest exists and the runner reports pass," "the reviewer named in the manifest left an `approvals[*]` entry with `approver_role: human`." If the agent cannot name the check, the gate has not been defined yet.
- The check produces an **artifact**: a log line, a test-runner output, a screenshot, an approval entry in the manifest, a metric snapshot. The artifact's location is recorded in the ROADMAP row.
- The check is **tied to the phase's declared exit criteria**, not invented after the fact. If the phase's exit criteria were not stated at phase start, the gate cannot be honestly evaluated.

A failing gate does **not** advance the phase. The agent must either fix the underlying issue and re-run the gate, or downgrade the phase's scope and re-declare the exit criteria explicitly. Silent scope-shrink is a gate bypass and is prohibited (see `ai-operating-contract.md`).

### Rule 2 — The ROADMAP is a first-class artifact

Any initiative that spans more than one phase opens an entry in the repo's `ROADMAP.md`. The ROADMAP is:

- **Durable.** It is checked into the repository. It does not live in the agent's session memory, a ticket tracker, or a chat log.
- **Append-mostly.** Passing gates are marked; failing gates are recorded alongside the re-run, not overwritten. The history is the point.
- **Schema-shaped.** Every row records the phase, scope, artifact(s), the gate's verification step, pass/fail status, the commit SHA (when version-controlled), and a short notes field.
- **Cross-session.** A fresh session resumes by reading the ROADMAP, not by re-deriving state from code diffs.

The `ROADMAP.md` in this repo's root is the canonical example. Other projects adopting this plugin replicate the same shape in their own repo.

The ROADMAP is **not** the Change Manifest. A Change Manifest describes one change's content (surfaces, SoT, evidence). A ROADMAP entry describes one initiative's **execution state** across phases. A non-trivial change will have both: one manifest per change, one ROADMAP row per phase of the initiative the change belongs to.

### Rule 3 — When the host repo is version-controlled, commit at every gate

If the execution environment has version control available:

- Every **passed** phase gate produces a commit. The commit message references the ROADMAP phase (e.g. `docs(i18n): P3 passed — core methodology translated`).
- The commit's SHA is written back into the ROADMAP row before the next phase starts.
- Failed gates do **not** produce a commit. Fix first; commit the fix; then re-run the gate; commit again only on pass.
- Pre-commit hooks and signing are **not** bypassed at gates. If a hook refuses the commit, that is itself a gate failure — fix the underlying issue.
- Do not amend a gate commit to retroactively add "what we forgot." Create a new commit; the history must remain truthful. (See `AGENTS.md` Git Safety Protocol.)

If the environment is **not** version-controlled (scratch directory, notebook, read-only mount), the commit step is replaced with "record the artifact's location in the ROADMAP row." The gate itself still applies. Only the persistence mechanism changes.

### Rule 4 — Spec documents are read in full before planning begins

When the user hands the agent a document or specification — whether it is a PRD, an RFC, a contract spec, an API reference, or a prior ROADMAP — the agent must:

- **Read it in full before producing a plan**, not skim the headers and start writing code. Partial reads produce plans that conflict with the spec's unread sections.
- **Enumerate the spec's constraints** back to the user or into the manifest's `assumptions` / `escalations` fields. "The spec says X; I am planning around X" is a verifiable claim. Silently ignoring X is a gate-discipline violation.
- **Re-read the spec at every subsequent phase**, not only at planning. Specs are referenced at Phase 2 (plan), Phase 3 (test plan), Phase 5 (review), and Phase 7 (completion-report cross-check). A spec that drifts out of the agent's context between phases is a common source of silent drift; re-reading is the countermeasure.
- **Strictly follow the spec during implementation.** If a section of the spec is discovered to be wrong or infeasible, that is an escalation (`escalation.trigger: spec_conflict`), not a license to silently deviate.

"Read in full" is a **capability-category** instruction, not a specific tool instruction. Whichever file-read or context-retrieval capability the runtime provides must be used to get every section into context. If the spec is too large to hold in context, the agent must index it (section map + re-fetch on reference) rather than guess.

### Rule 5 — Records are written at phase boundaries, not at initiative end

Phase outcomes are written to the ROADMAP **immediately** on gate pass or fail — not batched for end-of-initiative cleanup. Reasons:

- A compacted or interrupted session must be resumable from the ROADMAP alone. Lost phase records are lost work.
- The gate record is the evidence that the gate was actually evaluated. Writing it after-the-fact weakens the "evidence before completion" contract.
- Surprises and scope changes discovered during a phase are part of the record. They go in the phase's **Phase log** subsection, not in a separate document that decays.

Batching phase records into a single end-of-initiative write-up is prohibited. If a tool restriction makes phase-boundary writes inconvenient, the ROADMAP still takes precedence — use whatever capability is available, even if awkward.

---

## Gate template

Every phase declares, at phase start, the following. These go into the ROADMAP row before any phase work begins.

| Field | Content | Example |
|---|---|---|
| **Entry criteria** | What must be true to enter this phase | "Phase 0 has passed gate; initiative has a ROADMAP entry" |
| **Scope** | What this phase changes, in files / artifacts / surfaces | "Translate files A, B, C to English; delete Chinese originals" |
| **Exit criteria** | The conditions that define a passing gate | "`grep -P '\p{Han}' A B C` returns zero; A/B/C compile if executable; reader can navigate without Chinese" |
| **Verification command** | The exact check that will be run at gate time | "`grep -P '\p{Han}' A B C \| wc -l`" |
| **Evidence artifact** | Where the check's output is stored | "ROADMAP row `Notes` field; commit message body" |
| **Commit reference** | Where the commit SHA will be recorded on pass | "Same ROADMAP row, `Commit` column" |

If any of these six fields cannot be filled in at phase start, the phase is **not ready to start**. Go back and define them.

---

## Gate outcome types

| Outcome | Meaning | ROADMAP marker | Commit? |
|---|---|---|---|
| **Pass** | Every exit criterion met; artifact captured | `✅ passed` | Yes (when VCS available) |
| **Pass with caveat** | Exit criteria met, but a non-blocking follow-up was identified | `⚠️ passed-with-followup` + ticket link | Yes, with follow-up noted in commit body |
| **Fail** | Exit criterion not met; phase reverts to in-progress | `❌ failed — <short reason>` | No |
| **Defer** | Phase explicitly paused pending external input | `⏸ paused — <reason + expected resume>` | Yes — commit the paused state with an explicit marker |
| **Withdraw** | Phase cancelled; initiative re-planned | `🗑 withdrawn — <link to new plan>` | Yes — commit the withdrawal with a rationale |

A gate outcome is written by whoever ran the check (human or agent). An agent-written outcome must still satisfy `ai-operating-contract.md` §0: attribution, scope, evidence.

---

## How this composes with existing methodology

| Existing concept | How phase-gate discipline adds to it |
|---|---|
| **Phase minimums** (`skills/engineering-workflow/references/phase-minimums/*`) | Phase minimums describe *content* required. The gate rule adds *process*: the content is verified by a named check before the phase closes. |
| **Change Manifest** (`schemas/change-manifest.schema.yaml`) | A Change Manifest is per-change. A ROADMAP row is per-phase-of-an-initiative. Both coexist; they reference each other. |
| **`ai-operating-contract.md` "evidence before completion"** | That rule binds the final delivery. Phase-gate binds every interior phase, so evidence is continuous, not only end-loaded. |
| **`multi-agent-handoff.md` approval chain** | Handoff happens *at* gates. The agent receiving handoff consults the ROADMAP row, not prose. |
| **`post-delivery-observation.md` Phase 8 window** | Phase 8 uses its own gate criteria (the observation horizon). Same framework; longer gate. |

---

## Anti-patterns

| Anti-pattern | Why wrong | Correct form |
|---|---|---|
| "The phase is done because I'm done typing." | No named check; no artifact. | Define the exit criterion up front; run it; record the result. |
| "I'll fill in the ROADMAP at the end." | Lost records on interrupt; weakens evidence. | Write at phase boundaries. |
| Squashing multiple phases into one commit. | History does not match phase record; bisect becomes useless. | One commit per passed gate; history mirrors ROADMAP. |
| Skipping the full spec read "to save time" in planning. | Plans drift from spec silently; discovered late. | Read the spec in full; enumerate constraints; plan against them. |
| Amending a passed-gate commit to add forgotten evidence. | History falsification. | Make a new commit; note the correction. |
| Running the plugin on a repo without a ROADMAP for a multi-phase initiative. | No tracking artifact; the whole discipline collapses. | Open a ROADMAP entry at Phase 0; never advance past Phase 0 without one. |
| Using the Change Manifest as the ROADMAP. | Manifests are per-change; they do not record cross-phase state. | Keep both; each serves its purpose. |
| Defining the gate check after the phase has "looked done." | Opens the door to tautological gates. | Define exit criteria at phase start; do not rewrite them. |

---

## Minimum integration points

To apply this discipline, an agent must do the following at each listed point. These hooks are additions to the existing phase files, not replacements.

### At the start of every phase

1. Open or update the ROADMAP row: fill in entry criteria, scope, exit criteria, verification command, evidence artifact location, commit-reference placeholder.
2. Confirm that any spec document provided by the user has been read in full (Rule 4). If not, do that first.
3. Confirm Phase N-1 closed with a passing gate (Rule 1). If not, resolve that before entering Phase N.

### During a phase

4. Keep the ROADMAP row's `Status` as `⏳ in_progress`. Append to the `Phase log` subsection whenever a surprise, scope delta, or external blocker appears.

### At the end of every phase

5. Run the verification command. Capture its output.
6. Evaluate the outcome (pass / pass-with-caveat / fail / defer / withdraw). Update the row's `Status`.
7. If version-controlled: commit. Write the SHA into the row's `Commit` column.
8. If failed: do not advance. Fix, re-run, re-record.

---

## Relation to the Change Manifest schema

The Change Manifest schema (`schemas/change-manifest.schema.yaml`) already includes `implementation_notes`, `review_notes`, `approvals`, and `handoff_narrative`. These fields are the **change-level** record. The ROADMAP row is the **initiative-level** record above them.

Where the manifest says "the reviewer approved at T," the ROADMAP row says "Phase 5 gate passed at T, approval captured in manifest `<change_id>`." The manifest is the detail; the ROADMAP is the trail.

For single-change initiatives (e.g. a one-manifest bugfix), the ROADMAP row can be minimal — a single P0 + P7 pair is acceptable. For multi-phase initiatives (migrations, cross-team refactors, plugin-level work like this one), the ROADMAP row is the primary tracking artifact.

---

## See also

- `ROADMAP.md` at repo root — canonical live example
- `ai-operating-contract.md` — evidence-before-completion rule that phase-gate discipline extends
- `multi-agent-handoff.md` — how gates interact with cross-agent handoff
- `post-delivery-observation.md` — Phase 8 uses this gate framework with an extended horizon
- `AGENTS.md` — Git Safety Protocol that the commit-at-gate rule defers to
