# agent-protocol

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Plugin: Multi-agent](https://img.shields.io/badge/plugin-multi--agent-blue.svg)](./AGENTS.md)
[![Skill: Engineering Workflow](https://img.shields.io/badge/skill-engineering--workflow-purple.svg)](./skills/engineering-workflow/SKILL.md)
[![Version: 1.0.0](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)](./CHANGELOG.md)
[![Language: English-only](https://img.shields.io/badge/language-English--only-blue.svg)](./CHANGELOG.md)

A **tool-agnostic engineering workflow plugin** for AI coding agents.
**Not bound to any language, framework, runtime, AI agent, model, or cloud.**

> **Language policy.** All normative content — methodology docs, skills, schemas, templates, operating contract — is English-only. New contributions MUST be English; any CJK in normative files is treated as a release-gate failure by the full-repo scan encoded in `docs/phase-gate-discipline.md`.

Install once; it works across Claude Code, Cursor, Gemini CLI, Windsurf, Codex, Aider, OpenCode, or any agent that reads `AGENTS.md`.

---

## What you get

1. **Runtime operating contract** — [`AGENTS.md`](./AGENTS.md)
   Honest reporting, scope discipline, source-of-truth rules, surface-first analysis, evidence requirements, Change Manifest contract.

2. **Engineering workflow skill** — [`skills/engineering-workflow/SKILL.md`](./skills/engineering-workflow/SKILL.md)
   Lean / Full modes, phase minimums (Phase 0 – 8), capability-category guidance, spec / plan / test / completion templates.

3. **Methodology documentation** — [`docs/`](./docs/)
   Four canonical surfaces, 10 SoT patterns, breaking-change severity matrix, rollback modes, cross-cutting concerns, AI operating contract, security & supply-chain disciplines, change decomposition, team / org-scale disciplines, AI project memory, automation contract, multi-agent handoff, worked examples.

4. **Structured AI output contract** — [`schemas/`](./schemas/) + [`templates/`](./templates/)
   Change Manifest JSON Schema and worked example manifests (CRUD, mobile offline, game live-ops, multi-agent handoff progression).

5. **Stack bridges (optional, opt-in)** — [`docs/bridges/`](./docs/bridges/)
   The only place where specific framework / tool / language names appear. Bridges map the tool-agnostic methodology onto a given stack (Flutter, Android Kotlin + XML, Android Jetpack Compose, Ktor, Unity 3D). Add more bridges for your own stack by copying [`docs/stack-bridge-template.md`](./docs/stack-bridge-template.md).

6. **Multi-agent bridge (Claude Code)** — [`.claude-plugin/agents/`](./.claude-plugin/agents/)
   Three role-bound sub-agents — `planner`, `implementer`, `reviewer` — with tool-permission matrices that enforce the multi-agent-handoff contract mechanically (Reviewer has no write tools; Planner has no edit tools; Implementer cannot spawn further sub-agents). See [`docs/multi-agent-handoff.md`](./docs/multi-agent-handoff.md) §tool-permission-matrix. Other runtimes apply the same matrix using their own agent mechanism (see `AGENTS.md` §7).

---

## Install

### Claude Code

```bash
# One-off install
/plugin marketplace add https://github.com/<your-org>/agent-protocol
/plugin install agent-protocol@agent-protocol
```

Or local dev (symlink this repo into your plugins directory):

```bash
ln -s /absolute/path/to/agent-protocol ~/.claude/plugins/agent-protocol
```

Claude Code auto-loads `.claude-plugin/plugin.json` and `skills/*/SKILL.md`.

### Cursor

1. Clone or add this repo as a submodule in your project.
2. Cursor auto-loads `.cursor/rules/*.mdc`. Copy or symlink the file:

```bash
cp -r agent-protocol/.cursor/rules/engineering-workflow.mdc <your-project>/.cursor/rules/
```

Or keep the full repo in your project and point Cursor at it.

### Gemini CLI

Drop `GEMINI.md` at your project root (or in a parent directory Gemini CLI discovers):

```bash
cp agent-protocol/GEMINI.md <your-project>/GEMINI.md
# or
ln -s /path/to/agent-protocol/GEMINI.md <your-project>/GEMINI.md
```

Gemini loads it at session start.

### Windsurf

```bash
cp agent-protocol/.windsurfrules <your-project>/.windsurfrules
```

### Codex / Aider / OpenCode / any agents.md-aware agent

Place `AGENTS.md` at your project root. These agents follow the [agents.md](https://agents.md/) convention and will read it automatically.

```bash
cp agent-protocol/AGENTS.md <your-project>/AGENTS.md
```

### Custom agent (Anthropic / OpenAI / Google SDK, self-hosted)

Point your system prompt at `AGENTS.md` and make `skills/` + `docs/` + `schemas/` + `templates/` available via file access. The content is already tool-agnostic.

---

## Repository layout

```text
agent-protocol/
├── AGENTS.md                   # Universal operating contract (read first)
├── CLAUDE.md                   # Claude Code-specific guidance (for repo contributors)
├── GEMINI.md                   # Gemini CLI bridge
├── .windsurfrules              # Windsurf bridge
├── .cursor/rules/              # Cursor bridge
│   └── engineering-workflow.mdc
├── .claude-plugin/             # Claude Code plugin manifest + agents
│   ├── plugin.json
│   ├── marketplace.json
│   └── agents/                 # Role-bound sub-agents (Planner / Implementer / Reviewer)
│       ├── planner.md
│       ├── implementer.md
│       └── reviewer.md
├── skills/                     # Workflow execution layer
│   └── engineering-workflow/
│       ├── SKILL.md
│       ├── phases/             # Phase 0 – 8 detail
│       ├── references/         # Checklists, decision trees, phase minimums
│       └── templates/          # Spec / plan / test / completion templates
├── docs/                       # Methodology (tool-agnostic)
│   ├── product-engineering-operating-system.md
│   ├── principles.md
│   ├── surfaces.md
│   ├── source-of-truth-patterns.md
│   ├── breaking-change-framework.md
│   ├── rollback-asymmetry.md
│   ├── cross-cutting-concerns.md
│   ├── security-supply-chain-disciplines.md
│   ├── change-decomposition.md
│   ├── team-org-disciplines.md
│   ├── ai-operating-contract.md
│   ├── ai-project-memory.md
│   ├── multi-agent-handoff.md
│   ├── automation-contract.md
│   ├── automation-contract-algorithm.md
│   ├── phase-gate-discipline.md  # Per-phase gate + ROADMAP contract
│   ├── adoption-strategy.md
│   ├── glossary.md
│   ├── onboarding/             # Fast-path docs (incl. english-quick-start.md)
│   ├── bridges/                # Stack-specific bridges (ONLY place with tool names)
│   │   ├── flutter-stack-bridge.md
│   │   ├── android-kotlin-stack-bridge.md
│   │   ├── ktor-stack-bridge.md
│   │   └── unity-stack-bridge.md
│   └── examples/               # Worked examples across domains
│       ├── bugfix-example.md
│       ├── refactor-example.md
│       ├── migration-rollout-example.md
│       ├── game-dev-example.md
│       ├── game-liveops-example.md
│       ├── mobile-offline-feature-example.md
│       ├── ml-model-training-example.md
│       ├── data-pipeline-example.md
│       └── embedded-firmware-example.md
├── schemas/                    # Change Manifest JSON Schema
│   └── change-manifest.schema.yaml
├── templates/                  # Change Manifest examples
│   ├── change-manifest.example-crud.yaml
│   ├── change-manifest.example-mobile-offline.yaml
│   ├── change-manifest.example-game-gacha.yaml
│   └── change-manifest.example-multi-agent-handoff.yaml
├── reference-implementations/  # Non-normative example validators
│   └── validator-posix-shell/  # POSIX shell + yq + pluggable schema validator
├── ROADMAP.md                   # Multi-session tracking artifact for in-flight initiatives
├── CHANGELOG.md
├── CONTRIBUTING.md
├── VERSIONING.md
├── LICENSE
└── .github/release_template.md
```

---

## Why this plugin exists

Most coding agents optimize for "write code that looks right." This plugin optimizes for **managing change**:

- **Before code**: identify source of truth, enumerate affected surfaces, classify risk, pick workflow mode.
- **During code**: evidence for every surface you touch; no silent scope expansion; SoT before consumers.
- **After code**: structured completion artifact (Change Manifest) that a human or downstream agent can verify.

The method is expressed as **capability categories** (file read, code search, shell execution, sub-agent delegation), not vendor tool names, so it ports cleanly to any runtime.

---

## Core world view

Don't first ask:
- "Is this a frontend problem?"
- "Is this a backend problem?"

First ask:
- Where is the **source of truth** for this capability?
- Which **surfaces** will feel the change?
- Which **consumers** will be affected?
- What **evidence** proves this change actually works?

The four core surfaces:

| Surface | Content |
|---|---|
| User surface | UI, routes, components, copy, state, i18n, a11y |
| System interface surface | APIs, events, jobs, webhooks, SDK boundaries, public contracts |
| Information surface | schema, fields, enums, validation, config, feature flags |
| Operational surface | logs, audit, telemetry, docs, migration, rollout, rollback |

Full definitions and extensions: [`docs/surfaces.md`](./docs/surfaces.md).

---

## Reading paths

### Quick start (5 min)

1. [`docs/onboarding/english-quick-start.md`](./docs/onboarding/english-quick-start.md)
2. [`docs/phase-gate-discipline.md`](./docs/phase-gate-discipline.md) — per-phase gate + ROADMAP contract
3. [`docs/onboarding/quick-start.md`](./docs/onboarding/quick-start.md)

### Full methodology

See [`AGENTS.md`](./AGENTS.md) "Recommended reading order".

### When your situation matches

- Multiple agents cooperating on one change → [`docs/multi-agent-handoff.md`](./docs/multi-agent-handoff.md) + [`templates/change-manifest.example-multi-agent-handoff.yaml`](./templates/change-manifest.example-multi-agent-handoff.yaml)
- Feature too large to ship as one change → [`docs/change-decomposition.md`](./docs/change-decomposition.md)
- Security / supply-chain / PII path touched → [`docs/security-supply-chain-disciplines.md`](./docs/security-supply-chain-disciplines.md)
- Team / org-scale concerns (consumer registry, deprecation queue) → [`docs/team-org-disciplines.md`](./docs/team-org-disciplines.md)
- Long-lived session or cross-session work → [`docs/ai-project-memory.md`](./docs/ai-project-memory.md)
- Writing a validator / CI gate for this methodology → [`docs/automation-contract.md`](./docs/automation-contract.md) (capability spec) + [`docs/automation-contract-algorithm.md`](./docs/automation-contract-algorithm.md) (normative algorithm) + [`reference-implementations/`](./reference-implementations/) (non-normative example validators)
- Writing agent-runtime hooks (pre-tool-use, pre-commit, on-stop) → [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md) (four hook categories + I/O contract + exit-code semantics) + [`reference-implementations/hooks-claude-code/`](./reference-implementations/hooks-claude-code/) (non-normative Claude Code bridge)

### Execution layer

- [`skills/engineering-workflow/SKILL.md`](./skills/engineering-workflow/SKILL.md) — main skill
- [`skills/engineering-workflow/references/startup-checklist.md`](./skills/engineering-workflow/references/startup-checklist.md)
- [`skills/engineering-workflow/references/mode-decision-tree.md`](./skills/engineering-workflow/references/mode-decision-tree.md)

### Stack bridges (pick one when relevant)

- [`docs/bridges/flutter-stack-bridge.md`](./docs/bridges/flutter-stack-bridge.md)
- [`docs/bridges/android-kotlin-stack-bridge.md`](./docs/bridges/android-kotlin-stack-bridge.md)
- [`docs/bridges/ktor-stack-bridge.md`](./docs/bridges/ktor-stack-bridge.md)
- [`docs/bridges/unity-stack-bridge.md`](./docs/bridges/unity-stack-bridge.md)

Other stacks: copy [`docs/stack-bridge-template.md`](./docs/stack-bridge-template.md) into `docs/bridges/<your-stack>-stack-bridge.md` and fill it in for your team.

---

## Versioning and contribution

- Version strategy: [`VERSIONING.md`](./VERSIONING.md)
- Change history: [`CHANGELOG.md`](./CHANGELOG.md)
- Contribution rules: [`CONTRIBUTING.md`](./CONTRIBUTING.md)

---

## License

MIT. Fork, localize, customize internally — welcome.
