# AGENTS.md

> Universal operating contract for any AI agent working with this repository.
> This file follows the [agents.md](https://agents.md/) convention and is the primary entry point for Codex, Aider, OpenCode, Windsurf, Cursor, Gemini CLI, Claude Code, or any other AI coding runtime.

---

## What this repository provides

A **tool-agnostic engineering workflow plugin** that can be installed into any AI coding runtime. It delivers:

- A **methodology** for understanding and delivering system changes (`docs/`)
- An **execution layer** that translates the methodology into a runnable workflow with **four execution modes** (Zero-ceremony / Three-line delivery / Lean / Full), trigger conditions, phase minimums, and artifact templates (`skills/`)
- A **Change Manifest schema** so AI output can be structurally declared, human-reviewable, and CI-verifiable (`schemas/`, `templates/`)

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

Spec: `docs/change-manifest-spec.md` · Examples: `templates/change-manifest.example-*.yaml`

---

## Recommended reading order

**Fast lookup (30 seconds, when you don't need reasoning):**

- `docs/operational-cheat-sheet.md` — per-role top 5 actions, 5-second checks, and "when you see X, go to Y" navigation table

**Methodology (why and what):**

1. `docs/onboarding/orientation.md` — 5-minute orientation
2. `docs/phase-gate-discipline.md` — the per-phase verification, ROADMAP, commit-at-gate, and spec-review-before-plan contract
3. `docs/principles.md` — first principles (11 rules with derivations)
4. `docs/surfaces.md` — canonical surface definitions
5. `docs/source-of-truth-patterns.md` — 10 SoT patterns + desync repair
6. `docs/breaking-change-framework.md` — severity matrix + migration paths
7. `docs/rollback-asymmetry.md` — rollback modes + long-lived client handling
8. `docs/cross-cutting-concerns.md` — security, performance, observability, testability, error handling, build-time risk
9. `docs/security-supply-chain-disciplines.md` — surface-first threat modeling, supply chain as uncontrolled interface, secret lifecycle, compliance triggers, incident feedback loop
10. `docs/change-decomposition.md` — when to split or merge a change, dependency graph relations, worked decomposition scenario
11. `docs/team-org-disciplines.md` — consumer registry, contract catalog, deprecation queue, cross-team handoff
12. `docs/ai-operating-contract.md` — detailed AI co-author behavior contract
13. `docs/ai-project-memory.md` — three-layer memory model, write-back protocol, cross-session resumption, conflict resolution
14. `docs/multi-agent-handoff.md` — Planner / Implementer / Reviewer roles, manifest progression, conflict and resumption rules
15. `docs/phase-gate-discipline.md` — per-phase gate, ROADMAP tracking artifact, commit-at-gate, read-spec-before-plan
16. `docs/automation-contract.md` — what a validator must guarantee (structural / cross-reference / drift layers; waiver protocol; offline operability)
17. `docs/automation-contract-algorithm.md` — normative tool-neutral algorithm, layer-by-layer with rule IDs and exit codes; the bridge from capability contract to executable validator
17b. `docs/runtime-hook-contract.md` — capability contract for agent-runtime event-driven hooks (pre-tool-use / post-tool-use / pre-commit / on-stop); four categories (phase-gate / evidence / drift / completion-audit); shares exit-code semantics with the automation contract
18. `docs/adoption-strategy.md` — staged adoption, anti-metrics, decay intervention playbook
19. `docs/adoption-anti-metrics.md` — **non-normative** diagnostic aids for catching ceremonial adoption (same-artifact evidence, rollback-mode monoculture, LGTM-only review); explicitly not CI gates
20. `docs/glossary.md` — canonical term definitions

**Execution layer (when and how):**

- `skills/engineering-workflow/SKILL.md` — the main workflow skill
- `skills/engineering-workflow/references/startup-checklist.md` — 60-second opener
- `skills/engineering-workflow/references/mode-decision-tree.md` — Lean vs Full
- `skills/engineering-workflow/templates/` — spec / plan / test / completion templates

**Structured output (AI contract artifact):**

- `schemas/change-manifest.schema.yaml` — JSON Schema 2020-12 (canonical YAML form, comments + anchors preserved)
- `schemas/change-manifest.schema.json` — generated JSON mirror for Node / browser / GitHub Actions consumers; `.github/scripts/generate-schema-json.py --check` enforces parity in CI
- `schemas/surface-map.schema.yaml` + `.json` — per-bridge surface-map artifact (same dual-format discipline)
- `templates/change-manifest.example-crud.yaml` — simple CRUD example
- `templates/change-manifest.example-mobile-offline.yaml` — offline-first mobile example
- `templates/change-manifest.example-game-gacha.yaml` — live-ops game example
- `templates/change-manifest.example-multi-agent-handoff.yaml` — Planner → Implementer → Reviewer progression of one manifest
- `templates/change-manifest.example-security-sensitive.yaml` — JWT signing-key rotation: SoT pattern 8 (dual-representation), L1 breaking change, mode-3 compensation-only rollback, security / compliance cross-cutting escalations

**Worked examples across domains:**

- `docs/examples/bugfix-example.md` / `refactor-example.md` / `migration-rollout-example.md`
- `docs/examples/game-dev-example.md` / `game-liveops-example.md` / `unity-game-example.md`
- `docs/examples/mobile-offline-feature-example.md`
- `docs/examples/flutter-app-example.md` — multi-platform "Save & Share" with platform-channel two-sided contract
- `docs/examples/android-kotlin-example.md` — offline draft-saving with Room migration + WorkManager + ViewBinding
- `docs/examples/ios-swift-app-example.md` — CloudKit-synced tag feature + Home Screen Widget, private/public CloudKit rollback asymmetry
- `docs/examples/react-nextjs-app-example.md` — App Router migration with Server Action, ISR cache tags, Prisma additive migration, and A/B middleware
- `docs/examples/ktor-server-example.md` — order-lifecycle enum addition with migration + plugin install order + mixed rollback modes
- `docs/examples/ml-model-training-example.md` — ML retrain / rollout with dataset+weights+config SoT
- `docs/examples/data-pipeline-example.md` — schema extension with warehouse / feature store / compliance consumers
- `docs/examples/embedded-firmware-example.md` — OTA across HW versions, long-tail offline devices, three-mode rollback coexistence

**Reference implementations (explicitly non-normative — read only if you are building a validator):**

- `reference-implementations/` — directory index; every sub-implementation ships `README.md` + `DEVIATIONS.md` + source + self-test.
- `reference-implementations/validator-posix-shell/` — POSIX-shell reference validator (needs `yq`, `git`, and an external JSON Schema validator via `$SCHEMA_VALIDATOR`). Implements most of the algorithm; `DEVIATIONS.md` documents the three deliberate gaps.
- `reference-implementations/validator-python/` — Python 3.10+ language-native validator; closes rules 2.4 / 2.5 / 3.2 / 3.4 via PyYAML + jsonschema. Recommended when CI already has a Python interpreter. Pytest suite under `tests/`.
- `reference-implementations/validator-node/` — TypeScript / Node 20+ language-native validator; identical rule coverage and exit-code contract to the Python reference. Recommended for Node-based CI or editor integrations; runtime deps limited to `yaml` + `ajv` + `glob`. Test suite via `node --test`.
- `reference-implementations/roles/` — runtime-neutral Planner / Implementer / Reviewer role prompts. Paste-ready for Cursor Custom Mode, Gemini CLI session, Windsurf mode, Codex profile. Mirrors the §7 permission matrix in prose for runtimes that cannot gate tool exposure per persona.

**Stack bridges (opt-in, the only place where tool / framework / language names appear):**

- `docs/bridges/flutter-stack-bridge.md`
- `docs/bridges/android-kotlin-stack-bridge.md`
- `docs/bridges/android-compose-stack-bridge.md` — companion to the Kotlin + XML bridge; inherits Room / WorkManager / FCM / permission / vendor-fork / deep-link sections, adds Compose-specific state-ownership, effect-API, and recomposition deltas
- `docs/bridges/ios-swift-stack-bridge.md` — iOS/Swift (UIKit + SwiftUI) with Core Data, CloudKit, Widget/Extension multi-process state, and App Store compliance surface
- `docs/bridges/react-nextjs-stack-bridge.md` — React + Next.js App Router with RSC / Server Actions / Middleware / four-layer cache invalidation
- `docs/bridges/ktor-stack-bridge.md`
- `docs/bridges/unity-stack-bridge.md`
- Template for new stacks: `docs/stack-bridge-template.md`

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

The table above lists **installation entry points** per runtime. This map classifies the same files — plus the rest of the repo surface — by their **architectural role**, so a contributor adding a new rule can tell which file owns it. Drift between duplicated rules is the anti-pattern this repo most often warns against; this map is the index that prevents it.

| File / directory | Role | Normative weight |
|---|---|---|
| `AGENTS.md` (this file) | SoT — operating contract (the 8 core rules above) | Canonical; all runtimes inherit from here |
| `docs/multi-agent-handoff.md` | SoT — role contract (Planner / Implementer / Reviewer definitions, field-ownership matrix, tool-permission matrix, anti-collusion, handoff minima) | Canonical for multi-agent discipline; `agents/`, `.cursor/rules/`, `reference-implementations/roles/` all point back here |
| `docs/*.md` (other) | SoT — topic-specific definitions (`surfaces.md`, `source-of-truth-patterns.md`, `breaking-change-framework.md`, `rollback-asymmetry.md`, `phase-gate-discipline.md`, `ai-operating-contract.md`, `glossary.md`, …) | Canonical per topic; referenced from the contracts above |
| `skills/engineering-workflow/SKILL.md` + `skills/**` | SoT — execution layer (modes, phases, templates, references) | Canonical for workflow execution |
| `schemas/**` + `templates/**` | SoT — machine-readable Change Manifest contract + worked examples | Canonical structural output |
| `CLAUDE.md` | Thin-bridge — Claude Code entry; points at `AGENTS.md` + `skills/` | Onboarding only, no new normative content |
| `GEMINI.md` | Thin-bridge — Gemini CLI entry | Same |
| `.windsurfrules` | Thin-bridge — Windsurf entry | Same |
| `.codex-plugin/plugin.json` | Thin-bridge — Codex plugin manifest | Metadata and UI entry only; execution rules remain in `AGENTS.md` + `skills/` |
| `.agents/plugins/marketplace.json` | Thin-bridge — Codex local marketplace entry | Points Codex at the repository root plugin; no new normative content |
| `.cursor/rules/engineering-workflow.mdc` | Thin-bridge with `alwaysApply: true` — Cursor repo-level onboarding | Condensed summary only; every bullet must defer to a `docs/` source |
| `.cursor/rules/{planner,implementer,reviewer}.mdc` | Runtime role-spec — Cursor Custom Mode system prompts | Must remain self-contained because Cursor does not auto-resolve Markdown path references; normative rules are mirrored **from** `docs/multi-agent-handoff.md`, never authored here |
| `agents/{planner,implementer,reviewer}.md` | Runtime role-spec — Claude Code sub-agent definitions with mechanical `tools:` enforcement | Role behaviour must cite `docs/multi-agent-handoff.md` as the source; runtime-specific supplements (Lean-mode collapse, tool-permission rows) are allowed, new normative rules are not |
| `reference-implementations/roles/*.md` | Reference wrappers — runtime-neutral paste-ready prompts for Gemini / Windsurf / Codex / Aider | Never introduce normative content; if the wrapper says something `docs/multi-agent-handoff.md` does not, one of them is wrong |
| `reference-implementations/roles/specialist-roles-registry.md` | Reference wrapper — starter registry for specialist sub-agent roles (`architect`, `security-reviewer`, `performance-reviewer`) per `docs/multi-agent-handoff.md` §Composable specialist sub-agent roles | Non-normative reference; bridges may copy / extend / replace entries. Specialist contract itself lives in `docs/multi-agent-handoff.md`; this file lists which specialists exist |
| `reference-implementations/validator-*/` | Reference wrappers — executable validators for the automation contract | Track the spec in `docs/automation-contract*.md`; `DEVIATIONS.md` is the gap record |

### Where a new rule belongs

- New **operating-contract rule** (applies to every runtime) → extend §Core operating contract in this file; bridges and role-spec files inherit automatically.
- New **multi-agent / role-boundary rule** → `docs/multi-agent-handoff.md` first; update every consumer that cites it in the same change (per `CLAUDE.md` §5).
- New **topic-specific definition** (a surface type, an SoT pattern, a breaking-change level) → its own `docs/*.md` file or section; contracts reference it.
- New **runtime-specific shim** (Cursor quirk, Gemini session idiom, Claude Code frontmatter field) → thin-bridge or runtime role-spec file only; never in `docs/` or this file.
- New **reference implementation** → `reference-implementations/…` with `README.md` + `DEVIATIONS.md`. Always non-normative.

### The invariant this map enforces

A normative claim appears in **exactly one** SoT file. Every consumer cites that section by name. When two files state the same rule in different words, the thin-bridge / runtime role-spec / reference wrapper yields; the SoT file wins.

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
