# AGENTS.md

> Universal operating contract for any AI agent working with this repository.
> This file follows the [agents.md](https://agents.md/) convention and is the primary entry point for Codex, Aider, OpenCode, Windsurf, Cursor, Gemini CLI, Claude Code, or any other AI coding runtime.

---

## What this repository provides

A **tool-agnostic engineering workflow plugin** that can be installed into any AI coding runtime. It delivers:

- A **methodology** for understanding and delivering system changes (`docs/`)
- An **execution layer** that translates the methodology into a runnable workflow with **four execution modes** (Zero-ceremony / Three-line delivery / Lean / Full), trigger conditions, phase minimums, and artifact templates (`skills/`)
- A **Change Manifest schema** so AI output can be structurally declared, human-reviewable, and CI-verifiable (`schemas/`, with worked examples under `skills/engineering-workflow/templates/manifests/`)

It is **not** a stack-specific style guide. It does not assume a language, framework, cloud, or model. Capabilities are named as categories (file read, code search, shell execution, sub-agent delegation) and mapped at runtime to whatever the host agent provides.

---

## Core operating contract

These rules apply to any AI agent using this plugin, regardless of host runtime.

### 1. Honest reporting over optimistic summaries

- Never claim completion without verification and evidence.
- Do not mix "analysis / suggestion / plan" with "implementation". Either output analysis only, or write the files and state which files changed.
- When uncertain, say so. Escalate rather than fabricate.

### 2. Scope discipline

- Touch only what the task requires. Do not bundle opportunistic cleanup.
- If a task implies modifying shared contracts, shared components, or cross-repo interfaces, surface the impact and get confirmation first.
- Prefer the smallest workflow that preserves quality. Do not impose Full mode ceremony on Lean-appropriate work.

### 3. Source of truth before consumers

- Before patching a symptom, identify which source-of-truth pattern applies (see `docs/source-of-truth-patterns.md`).
- Fix at the SoT; do not patch consumers to mask SoT drift.
- If SoT is unclear, that is the first thing to resolve — not code changes.

### 4. Surface-first analysis

Every change passes through one or more of these four surfaces. Mark them before choosing verification:

| Surface | Examples |
|---|---|
| User surface | UI, routes, components, copy, state, i18n, a11y |
| System interface surface | APIs, events, jobs, webhooks, SDK boundaries, public contracts |
| Information surface | schema, fields, enums, validation, config, feature flags |
| Operational surface | logs, audit, telemetry, docs, migration, rollout, rollback |

Domain-specific surface extensions are allowed; map them back to one of the four first. Full definition: `docs/surfaces.md`.

### 5. Evidence before completion

Verification is chosen by the affected surfaces, not by habit. Examples:

- Build / compile / test for implementation surfaces
- Browser / screenshot / interaction proof for user surfaces
- API / payload / contract verification for system interface surfaces
- Query / migration / cache verification for information surfaces
- Logs / generated docs / changelog evidence for operational surfaces

No evidence → not done.

### 6. Phase-gate discipline

Every phase of a multi-phase Full-mode initiative ends with an **explicit, named check** that either passes or fails. Five rules apply:

1. **Every phase ends with an explicit gate** — the check is a repeatable action (a command, a manifest field inspection, a named human approval), it produces an artifact, and it is tied to the phase's declared exit criteria. Silent scope-shrink to force a pass is prohibited.
2. **The ROADMAP is a first-class artifact** — any initiative that spans more than one phase opens an entry in the repo's `ROADMAP.md`. Rows record entry/exit criteria, verification command, pass/fail status, commit SHA, and notes. The ROADMAP is append-mostly and cross-session; fresh sessions resume from it, not from code diffs.
3. **Commit at every gate when version control is available** — one commit per passed gate; commit SHA is recorded back into the ROADMAP row; failing gates do not produce a commit. Pre-commit hooks and signing are never bypassed.
4. **Spec documents are read in full before planning** — skim-and-start produces plans that silently drift from the spec. Read in full, enumerate constraints into the manifest or ROADMAP, re-read the spec at Phase 2 / 3 / 5 / 7, treat discovered spec conflicts as `escalation.trigger: spec_conflict` rather than silent deviation.
5. **Records are written at phase boundaries, not at initiative end** — lost phase records on interrupt are lost work. Surprises and scope changes go into the phase-log subsection immediately.

**Ceremony scaling.** These five rules apply in full to **Full mode** only. **Lean mode** compresses them to a single gate event at Lean-5 delivery (Lean steps Lean-0 … Lean-4 are not individually gated). **Three-line delivery** and **Zero-ceremony** changes are waived from phase-gate discipline entirely — their artifact is the commit or PR description. The per-rule × per-mode application table is in `docs/phase-gate-discipline.md §Ceremony scaling — how the six rules apply per execution mode`. Mode definitions: `docs/glossary.md §Execution mode`.

Full spec: `docs/phase-gate-discipline.md`. Evidence-before-completion applies in every mode, regardless of ceremony scaling.

### 7. Multi-agent role separation (when the runtime supports sub-agents)

When a change is non-trivial (Full mode), and the host runtime provides a sub-agent / agent-spawn mechanism, separate the work across three role-bound identities:

| Role | May do | May not do | Permission-category enforcement |
|---|---|---|---|
| **Planner** | Read, search, network fetch; produce manifest front-half + Task Prompt; spawn Implementer; optionally spawn non-canonical research / code-explorer / surface-investigator sub-agents per role-composition Patterns 1 / 2 / 5 | Write or edit code; spawn another Planner or Reviewer | No write / shell-mutation tools |
| **Implementer** | Everything needed to execute the plan + collect evidence; optionally spawn non-canonical test-writer sub-agent per role-composition Pattern 3 | Re-classify surfaces / change `breaking_change.level`; spawn another Implementer, Planner, or Reviewer; self-review | Sub-agent spawning limited to non-canonical test-writer use |
| **Reviewer** | Read, search, verification-only shell (tests / builds / lint / git-log); produce `review_notes` + `approvals`; optionally spawn non-canonical reference-sampler / specialized-audit sub-agents per role-composition Patterns 4 / 6 | Edit code; spawn another Reviewer or any canonical role; self-approve a change it implemented | **No write / edit tools — this is the single most important row** |

**Two delegation categories.** The rows above distinguish **canonical-role delegation** (spawning another Planner / Implementer / Reviewer — only Planner → Implementer is allowed, the rest are forbidden to keep the canonical execution tree flat) from **non-canonical sub-agent delegation** (spawning a research / code-explorer / test-writer / reference-sampler / surface-investigator / audit sub-agent — governed by the six patterns in `reference-implementations/roles/role-composition-patterns.md`, with envelope-inheritance and anti-collusion constraints). Patterns 5 and 6 are parallel fan-outs with additional discipline in `skills/engineering-workflow/references/parallelization-patterns.md` (cache-window rule, context pack, canonical-role fan-in synthesis, cross-cutting gap check, `parallel_groups` audit trail).

**Anti-collusion rule:** within one Full-mode change, the same AI identity must not play more than one of `{Planner, Implementer, Reviewer}`. Implementer ≡ Reviewer is the highest-risk combination and is forbidden outright. The rule extends transitively to non-canonical sub-agents: a sub-agent identity that matches any canonical role's identity on the same change collapses the rule.

Runtime bridges translate this matrix into runtime-specific agent configuration:

- **Claude Code** — `agents/{planner,implementer,reviewer}.md`; mechanically enforced via per-agent `tools:` frontmatter.
- **Cursor** — `.cursor/rules/{planner,implementer,reviewer}.mdc`; mechanically enforced when paired with a per-role Custom Mode that excludes edit/apply tools.
- **Gemini CLI / Windsurf / Codex** — `reference-implementations/roles/{planner,implementer,reviewer}.md`; prose-only, since these runtimes do not gate tool exposure per persona. Pair with distinct sessions per role, OS-level read-only working dir for Reviewer, and session-identity recording in `approvals`.

Full matrix (mechanical vs prose-only, per runtime): `docs/multi-agent-handoff.md` §Enforcement across runtimes.

Full contract: `docs/multi-agent-handoff.md` §tool-permission-matrix + §single-agent-anti-collusion-rule. Lean mode (trivial single-surface changes) exempts Planner ≡ Implementer collapse.

### 8. Change Manifest as structured output

For non-trivial changes (2+ surfaces, SoT trade-off, breaking change, or rollback considerations), produce or update a **Change Manifest** (YAML, conforming to `schemas/change-manifest.schema.yaml`).

Three modes of use:

- **Generate**: in Phase 1/2, draft a manifest from the requirement — it aligns faster than prose.
- **Verify**: in Phase 4/5, diff the manifest against actual changes; flag drift.
- **Handoff**: an upstream agent's manifest becomes a downstream agent's context and constraints.

Trivial changes (single-file typo, pure comment) are exempt. When uncertain, produce one.

Spec: `docs/change-manifest-spec.md` · Examples: `skills/engineering-workflow/templates/manifests/change-manifest.example-*.yaml`

### 9. Agent persona discipline

Every AI-agent invocation under this contract reasons from a **real domain-expert persona** (system architect / motion designer / UX designer / deck designer / prototyper / …), not from the generic "I am an AI assistant" default that produces detectably AI-shaped output.

- **Selected by the medium of the output**, not by the format of the input. A request phrased as "write HTML for an animation" is animation work — persona is `motion designer`, not `web designer`. The medium is what the user *experiences* through the rendering substrate.
- **Shifts when the medium shifts**, even mid-session. If the next task is a slide deck and the prior task was a system diagram, drop the architect stance and adopt the deck designer stance. Carrying over the prior persona is a category error.
- **Orthogonal to the canonical workflow role.** The role names the workflow position and tool envelope (Planner / Implementer / Reviewer per §7); the persona names the domain stance the agent reasons from. The two layers stack and never substitute. Specialist sub-agent roles (`reference-implementations/roles/specialist-roles-registry.md`) are a third axis.
- **Persona never overrides tool permissions, anti-collusion, phase-gate discipline, evidence requirements, or non-fabrication rules.** A persona that "wins" against any of these has been used as a smuggling device, not a stance. Persona-as-permission-escalation ("as a senior architect I can approve this myself") is explicitly forbidden.

Full contract: `docs/agent-persona-discipline.md` · Worked example: `docs/examples/agent-persona-example.md`

### 10. Output craft discipline

Every output the agent produces — code, prose, manifests, summaries, UI, deliverables — must clear three rules:

- **Every element earns its place.** For each element added (a section, a paragraph, a control, a comment, an emoji, a graphic), the agent must answer "what would be lost if this were removed?" If the answer is "nothing, but it fills the space", the element is filler and must be removed. Default to omission, not inclusion. Treat empty space as content.
- **Output adapts to its medium; the AI default is rejected.** The default styling an AI produces is a fingerprint, not a feature. A motion graphic does not look like a marketing page. A slide deck does not look like a Notion document. A system diagram does not look like a UI prototype. The persona declared per §9 picks the styling vocabulary; conventions that arrive by default (three-column hero, six-card grid, gradient CTA, emoji-as-icons, ornament SVG, layout-balancing sections, dummy data) are filler everywhere they are not part of the medium. Inventing data to populate a layout is also a §1 / §9-of-`ai-operating-contract.md` non-fabrication violation.
- **Summaries are caveats and next steps, not recap.** The diff and the manifest are the record; the agent's contribution at the summary slot is what those records do not say — caveats (residual risk, gotchas, what was assumed), next steps (what is still pending, what to confirm). Do not restate completed actions; do not open with preamble; do not close with flourish.

The rules are stated as principles, not as exhaustive trope lists, so they remain medium-agnostic as new AI defaults emerge.

Full contract: `docs/output-craft-discipline.md`

---

## Recommended reading order

This file is a **table of contents** ([`docs/repo-as-context-discipline.md`](docs/repo-as-context-discipline.md) Rule 2). For the full discoverability index of every methodology file, read [`docs/README.md`](docs/README.md). The shortest paths in:

- **Fast lookup (30 seconds)** → [`docs/operational-cheat-sheet.md`](docs/operational-cheat-sheet.md)
- **Five-minute orientation** → [`docs/onboarding/orientation.md`](docs/onboarding/orientation.md)
- **First principles (why)** → [`docs/principles.md`](docs/principles.md)
- **Routing aid (manifest needed? / which SoT pattern? / single vs multi-agent? / HITL escalation?)** → [`docs/decision-trees.md`](docs/decision-trees.md)
- **Execution layer (when and how)** → [`skills/engineering-workflow/SKILL.md`](skills/engineering-workflow/SKILL.md)
- **Structured output contract** → [`schemas/change-manifest.schema.yaml`](schemas/change-manifest.schema.yaml) + worked examples under [`skills/engineering-workflow/templates/manifests/`](skills/engineering-workflow/templates/manifests/)
- **Per-runtime entry points** → see §How to use this plugin in different runtimes below
- **Stack bridges (the only place where specific tool / framework / language names appear)** → [`docs/bridges/`](docs/bridges/)
- **Reference implementations (non-normative)** → [`reference-implementations/`](reference-implementations/)

The 4-tier index in [`docs/README.md`](docs/README.md) lists every methodology file by tier (onboarding / core contract / disciplines / references); use it when looking up a rule by topic rather than by entry point.

---

## How to use this plugin in different runtimes

Each runtime has its own entry point, but all of them end up pointing at `skills/engineering-workflow/SKILL.md` and the `docs/` methodology.

| Runtime | Entry point | Notes |
|---|---|---|
| **Claude Code** | `.claude-plugin/plugin.json` + `skills/` auto-load | Install via `/plugin marketplace add <repo-url>` then `/plugin install agent-protocol` |
| **Cursor** | `.cursor/rules/*.mdc` bridge | Rules auto-load when repo is opened |
| **Gemini CLI** | `GEMINI.md` at repo root | Loaded at session start |
| **Windsurf** | `.windsurfrules` at repo root | Loaded at session start |
| **Codex** | `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json` | Install as a local Codex plugin; see `docs/codex-install.md`. `AGENTS.md` remains the fallback entry point |
| **Aider / OpenCode / others** | `AGENTS.md` (this file) | Agents.md convention is automatic for supporting runtimes |
| **Custom agent (API SDK)** | Point your system prompt at `AGENTS.md` | Plus any `docs/` or `skills/` files you want in context |

See `README.md` for installation details per runtime.

---

## File role map (where normative content is allowed to live)

The table above lists **installation entry points** per runtime. The full per-file role classification — which file owns which rule, which files are SoT vs thin-bridge vs reference, where a new rule belongs — lives in [`docs/file-role-map.md`](docs/file-role-map.md). Read that file when adding a new normative claim, or when two files appear to state the same rule in different words.

The invariant the map enforces: a normative claim appears in **exactly one** SoT file. Every consumer cites that section by name. When two files state the same rule in different words, the thin-bridge / runtime role-spec / reference wrapper yields; the SoT file wins.

---

## Stop conditions

Do not proceed if any of these are true:

- The source of truth is unclear and you would be guessing.
- Affected surfaces cannot be enumerated.
- A breaking change has no identified migration path.
- Rollback strategy is unknown for a change that needs one.
- Verification evidence cannot be produced.

Stop, state the blocker, and ask.

---

## Behavior boundaries (hard rules)

- Never fabricate file paths, APIs, or library behavior. If unsure, read the code or ask.
- Never claim a fix is verified without running the verification.
- Never expand scope silently. Scope changes require explicit acknowledgment.
- Never bypass CI checks, signing, or hooks without explicit user authorization.
- Never commit secrets, credentials, or local developer config.

Full detail: `docs/ai-operating-contract.md`.
