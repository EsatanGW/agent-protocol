# agent-protocol

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Plugin: Multi-agent](https://img.shields.io/badge/plugin-multi--agent-blue.svg)](./AGENTS.md)
[![Skill: Engineering Workflow](https://img.shields.io/badge/skill-engineering--workflow-purple.svg)](./skills/engineering-workflow/SKILL.md)
[![Version: 1.22.0](https://img.shields.io/badge/version-1.22.0-brightgreen.svg)](./CHANGELOG.md)
[![Language: English-only](https://img.shields.io/badge/language-English--only-blue.svg)](./CHANGELOG.md)

A **tool-agnostic engineering workflow plugin** for AI coding agents.
**Not bound to any language, framework, runtime, AI agent, model, or cloud.**

> **Language policy.** All normative content — methodology docs, skills, schemas, templates, operating contract — is authored in English. New contributions MUST be English.

Install once; it works across Claude Code, Cursor, Gemini CLI, Windsurf, Codex, Aider, OpenCode, or any agent that reads `AGENTS.md`.

---

> **See the whole stack on one page.** [`docs/diagrams.md` §6 — All pieces together](./docs/diagrams.md#6-all-pieces-together--how-the-layers-connect) maps the normative layer (contracts), execution layer (skill + phases), carrier artifacts (manifest + evidence + ROADMAP), and mechanical guardrails (runtime hooks + CI hooks) in a single diagram. Read it before drilling into any specific file.

## What you get

1. **Runtime operating contract** — [`AGENTS.md`](./AGENTS.md)
   Honest reporting, scope discipline, source-of-truth rules, surface-first analysis, evidence requirements, Change Manifest contract.

2. **Engineering workflow skill** — [`skills/engineering-workflow/SKILL.md`](./skills/engineering-workflow/SKILL.md)
   Lean / Full modes, phase minimums (Phase 0 – 8), capability-category guidance, spec / plan / test / completion templates.

3. **Methodology documentation** — [`docs/`](./docs/)
   Four canonical surfaces, 10 SoT patterns, breaking-change severity matrix, rollback modes, cross-cutting concerns, AI operating contract, security & supply-chain disciplines, change decomposition, team / org-scale disciplines, AI project memory, automation contract, multi-agent handoff, worked examples.

4. **Structured AI output contract** — [`schemas/`](./schemas/) + [`skills/engineering-workflow/templates/manifests/`](./skills/engineering-workflow/templates/manifests/)
   Change Manifest JSON Schema (YAML canonical + JSON generated mirror for Node/browser consumers) and worked example manifests (CRUD, mobile offline, game live-ops, multi-agent handoff progression, security-sensitive JWT rotation). Schema carries a reusable `$defs.deprecation` marker so L3/L4 breaking changes can declare deprecate-then-remove timelines directly in-manifest. A generated [`CHANGELOG.json`](./CHANGELOG.json) mirrors the human-readable CHANGELOG for release-automation consumers.

5. **Stack bridges (optional, opt-in)** — [`docs/bridges/`](./docs/bridges/)
   The only place where specific framework / tool / language names appear. Bridges map the tool-agnostic methodology onto a given stack (Flutter, Android Kotlin + XML, Android Jetpack Compose, Ktor, Unity 3D). Add more bridges for your own stack by copying [`docs/stack-bridge-template.md`](./docs/stack-bridge-template.md).

6. **Multi-agent bridge (Claude Code)** — [`agents/`](./agents/)
   Three role-bound sub-agents — `planner`, `implementer`, `reviewer` — with tool-permission matrices that enforce the multi-agent-handoff contract mechanically (Reviewer has no write tools; Planner has no edit tools; Implementer cannot spawn further sub-agents). See [`docs/multi-agent-handoff.md`](./docs/multi-agent-handoff.md) §tool-permission-matrix. Other runtimes apply the same matrix using their own agent mechanism (see `AGENTS.md` §7).

7. **Runnable starter example** — [`examples/starter-repo/`](./examples/starter-repo/)
   A minimal end-to-end demonstration: a schema-valid Change Manifest for a tiny change (`/healthz` endpoint), cited evidence artifacts, a closed ROADMAP initiative, and a 30-line validator. Clone and run `make validate` to see the full contract execute in under a minute. Use as a seed for your own project.

8. **Agent-runtime hook contract + reference bundle** — [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md) + [`reference-implementations/hooks-claude-code/`](./reference-implementations/hooks-claude-code/)
   A tool-agnostic contract for **event-driven guardrails inside the agent's own loop** (pre-commit, post-tool-use, on-stop). Four categories (phase-gate / evidence / drift / completion-audit), JSON-over-stdin event schema, exit-code semantics `0 = pass / 1 = block / 2 = warn`. A Claude Code reference bundle ships five POSIX-sh hooks wiring these categories onto `PreToolUse` / `PostToolUse` / `Stop` events — see the [Agent-runtime hooks](#agent-runtime-hooks) section below for an overview, or [`docs/runtime-hooks-in-practice.md`](./docs/runtime-hooks-in-practice.md) for install steps.

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

Claude Code auto-loads `.claude-plugin/plugin.json`, `skills/*/SKILL.md`, `agents/*.md`, and `hooks/hooks.json` per the Claude Code plugin convention (components live at plugin root, not under `.claude-plugin/`).

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

### Codex

Agent Protocol ships as a Codex plugin at the repository root. The Codex manifest lives at `.codex-plugin/plugin.json`, and the local marketplace entry lives at `.agents/plugins/marketplace.json`.

For a user-wide install, clone the repo and add it to your local Codex marketplace:

```bash
git clone https://github.com/EsatanGW/agent-protocol.git ~/agent-protocol
mkdir -p ~/plugins ~/.agents/plugins
ln -sfn ~/agent-protocol ~/plugins/agent-protocol
```

Then add an `agent-protocol` entry to `~/.agents/plugins/marketplace.json` with `source.path` set to `./plugins/agent-protocol`. Restart Codex so it reloads the local marketplace.

See [`docs/codex-install.md`](./docs/codex-install.md) for user-wide, workspace-scoped, and hook opt-in installation details.

### Aider / OpenCode / any agents.md-aware agent

Place `AGENTS.md` at your project root. These agents follow the [agents.md](https://agents.md/) convention and will read it automatically.

```bash
cp agent-protocol/AGENTS.md <your-project>/AGENTS.md
```

### Custom agent (Anthropic / OpenAI / Google SDK, self-hosted)

Point your system prompt at `AGENTS.md` and make `skills/` + `docs/` + `schemas/` available via file access. The content is already tool-agnostic; worked-example manifests live under `skills/engineering-workflow/templates/manifests/`.

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
├── .agents/plugins/            # Codex local marketplace entry
│   └── marketplace.json
├── .codex-plugin/              # Codex plugin manifest
│   └── plugin.json
├── .claude-plugin/             # Claude Code plugin manifest only
│   ├── plugin.json
│   └── marketplace.json
├── assets/                     # Codex plugin icons
│   ├── agent-protocol.svg
│   └── agent-protocol-small.svg
├── agents/                     # Role-bound sub-agents (Planner / Implementer / Reviewer)
│   ├── planner.md
│   ├── implementer.md
│   └── reviewer.md
├── hooks/                      # Plugin entry point for Claude Code auto-discovery
│   └── hooks.json              # Wires reference-implementations/hooks-claude-code/hooks/*.sh
├── skills/                     # Workflow execution layer
│   └── engineering-workflow/
│       ├── SKILL.md
│       ├── phases/             # Phase 0 – 8 detail
│       ├── references/         # Checklists, decision trees, phase minimums
│       └── templates/          # Spec / plan / test / completion templates
│           └── manifests/      # Change Manifest worked examples (CRUD / mobile-offline / game-gacha / mission-evaluator / multi-agent-handoff / security-sensitive)
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
│   ├── codex-install.md
│   ├── phase-gate-discipline.md  # Per-phase gate + ROADMAP contract
│   ├── adoption-strategy.md
│   ├── glossary.md
│   ├── onboarding/             # Fast-path docs (incl. orientation.md)
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
├── schemas/                    # Change Manifest + surface-map JSON Schemas (dual-format)
│   ├── change-manifest.schema.yaml    # canonical (comments, anchors)
│   ├── change-manifest.schema.json    # generated — Node / browser consumers
│   ├── surface-map.schema.yaml
│   └── surface-map.schema.json
├── reference-implementations/  # Non-normative example validators + hook bundles
│   ├── validator-posix-shell/  # POSIX shell + yq + pluggable schema validator (minimal)
│   ├── validator-python/       # Python 3.10+ validator (covers all rules including 2.4, 2.5, 3.2, 3.4)
│   ├── community/
│   │   └── validator-node/     # community-maintained TypeScript / Node validator (same rule coverage as Python; not officially synced)
│   ├── roles/                  # Runtime-neutral Planner / Implementer / Reviewer role prompts
│   ├── hooks-claude-code/      # Runtime-hook reference bundle + selftest harness
│   ├── hooks-cursor/           # Cursor adapter
│   ├── hooks-gemini-cli/       # Gemini CLI adapter
│   ├── hooks-windsurf/         # Windsurf adapter
│   └── hooks-codex/            # Codex adapter
├── ROADMAP.md                   # Multi-session tracking artifact for in-flight initiatives
├── CHANGELOG.md                 # Human-readable release history (Keep-a-Changelog)
├── CHANGELOG.json               # Generated machine-readable release feed
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

### 30-second lookup

- [`docs/operational-cheat-sheet.md`](./docs/operational-cheat-sheet.md) — per-role top 5 actions + 5-second checks + "when you see X, go to Y" navigation. Use this when you need the decision fast; use the linked docs when you need the reasoning.
- [`docs/decision-trees.md`](./docs/decision-trees.md) — single-page hub for the three most-asked routing decisions: *Need a Change Manifest?*, *Which SoT pattern (1–10 + 4a)?*, *Single-agent or multi-agent role split?* Routes to the canonical source for each.

### Quick start (5 min)

1. [`docs/onboarding/orientation.md`](./docs/onboarding/orientation.md) — canonical single-page onboarding; contains the three-minute and one-page summaries as named sections
2. [`docs/phase-gate-discipline.md`](./docs/phase-gate-discipline.md) — per-phase gate + ROADMAP contract
3. [`docs/onboarding/when-not-to-use-this.md`](./docs/onboarding/when-not-to-use-this.md) — recognise when the methodology is overkill (also covers scenarios where the methodology partially fits but has known gaps — incident response, pure research, A/B tests, etc.)

### Full methodology

See [`AGENTS.md`](./AGENTS.md) "Recommended reading order", or browse the **[`docs/` index](./docs/README.md)** for a 4-tier classification of every methodology document (onboarding / core contract / disciplines / references).

### When your situation matches

- Multiple agents cooperating on one change → [`docs/multi-agent-handoff.md`](./docs/multi-agent-handoff.md) + [`skills/engineering-workflow/templates/manifests/change-manifest.example-multi-agent-handoff.yaml`](./skills/engineering-workflow/templates/manifests/change-manifest.example-multi-agent-handoff.yaml)
- Multi-agent roles on a non-Claude-Code runtime (Cursor / Gemini CLI / Windsurf / Codex) → [`docs/multi-agent-handoff.md`](./docs/multi-agent-handoff.md) §Enforcement across runtimes + [`reference-implementations/roles/`](./reference-implementations/roles/)
- Feature too large to ship as one change → [`docs/change-decomposition.md`](./docs/change-decomposition.md)
- Security / supply-chain / PII path touched → [`docs/security-supply-chain-disciplines.md`](./docs/security-supply-chain-disciplines.md) + [`skills/engineering-workflow/templates/manifests/change-manifest.example-security-sensitive.yaml`](./skills/engineering-workflow/templates/manifests/change-manifest.example-security-sensitive.yaml)
- Team / org-scale concerns (consumer registry, deprecation queue) → [`docs/team-org-disciplines.md`](./docs/team-org-disciplines.md)
- Adoption review — is the team applying the methodology or going through the motions? → [`docs/adoption-anti-metrics.md`](./docs/adoption-anti-metrics.md) (non-normative diagnostic aids)
- Long-lived session or cross-session work → [`docs/ai-project-memory.md`](./docs/ai-project-memory.md)
- Writing a validator / CI gate for this methodology → [`docs/automation-contract.md`](./docs/automation-contract.md) (capability spec) + [`docs/automation-contract-algorithm.md`](./docs/automation-contract-algorithm.md) (normative algorithm) + non-normative language references: first-class [`validator-posix-shell/`](./reference-implementations/validator-posix-shell/) (minimal, zero-dep) and [`validator-python/`](./reference-implementations/validator-python/) (full rule coverage), plus community-maintained [`community/validator-node/`](./reference-implementations/community/validator-node/) — each ships a `DEVIATIONS.md` that maps exactly which rules it closes
- Deprecating a schema field or API surface → [`docs/change-manifest-spec.md` §"Deprecating a field"](./docs/change-manifest-spec.md) (decision table) + `$defs.deprecation` in [`schemas/change-manifest.schema.yaml`](./schemas/change-manifest.schema.yaml) (reusable deprecation marker)
- Writing agent-runtime hooks (pre-tool-use, pre-commit, on-stop) → [Agent-runtime hooks](#agent-runtime-hooks) section below + [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md) + [`reference-implementations/hooks-claude-code/`](./reference-implementations/hooks-claude-code/)

---

## Agent-runtime hooks

Event-driven guardrails that fire **inside the AI agent's own execution loop** — before each tool call, after each edit, at end-of-turn — not in CI. They exist to catch failures early (while the agent can still correct) instead of late (after a PR has shipped). Sibling to [`docs/ci-cd-integration-hooks.md`](./docs/ci-cd-integration-hooks.md), which covers the CI/CD layer; the two share the same exit-code contract (`0 = pass / 1 = block / 2 = warn`).

The primary bundle at [`reference-implementations/hooks-claude-code/`](./reference-implementations/hooks-claude-code/) ships five POSIX-sh hooks (`manifest-required.sh`, `evidence-artifact-exists.sh`, `sot-drift-check.sh`, `consumer-registry-check.sh`, `completion-audit.sh`), a `settings.example.json`, a DEVIATIONS.md, and a hermetic self-test harness. Thin adapter bundles for [Cursor](./reference-implementations/hooks-cursor/), [Gemini CLI](./reference-implementations/hooks-gemini-cli/), [Windsurf](./reference-implementations/hooks-windsurf/), and [Codex](./reference-implementations/hooks-codex/) reuse the same hook scripts under each runtime's native registration format.

**Where to go next:**

- [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md) — **normative contract**: four categories (A phase-gate / B evidence / C drift / D completion-audit), event schema, latency budgets, non-functional requirements.
- [`docs/runtime-hooks-in-practice.md`](./docs/runtime-hooks-in-practice.md) — **how-to guide**: install on Claude Code, wire adapters on other runtimes, configuration knobs, adoption ramp (4-week staging), and the template for writing a custom hook.

### Execution layer

- [`skills/engineering-workflow/SKILL.md`](./skills/engineering-workflow/SKILL.md) — main skill
- [`skills/engineering-workflow/references/startup-checklist.md`](./skills/engineering-workflow/references/startup-checklist.md)
- [`skills/engineering-workflow/references/mode-decision-tree.md`](./skills/engineering-workflow/references/mode-decision-tree.md)

### Stack bridges (pick one when relevant)

- [`docs/bridges/flutter-stack-bridge.md`](./docs/bridges/flutter-stack-bridge.md)
- [`docs/bridges/android-kotlin-stack-bridge.md`](./docs/bridges/android-kotlin-stack-bridge.md)
- [`docs/bridges/android-compose-stack-bridge.md`](./docs/bridges/android-compose-stack-bridge.md)
- [`docs/bridges/ios-swift-stack-bridge.md`](./docs/bridges/ios-swift-stack-bridge.md)
- [`docs/bridges/react-nextjs-stack-bridge.md`](./docs/bridges/react-nextjs-stack-bridge.md)
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
