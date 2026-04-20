# agent-protocol

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Plugin: Multi-agent](https://img.shields.io/badge/plugin-multi--agent-blue.svg)](./AGENTS.md)
[![Skill: Engineering Workflow](https://img.shields.io/badge/skill-engineering--workflow-purple.svg)](./skills/engineering-workflow/SKILL.md)
[![Version: 1.5.0](https://img.shields.io/badge/version-1.5.0-brightgreen.svg)](./CHANGELOG.md)
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

4. **Structured AI output contract** — [`schemas/`](./schemas/) + [`templates/`](./templates/)
   Change Manifest JSON Schema and worked example manifests (CRUD, mobile offline, game live-ops, multi-agent handoff progression).

5. **Stack bridges (optional, opt-in)** — [`docs/bridges/`](./docs/bridges/)
   The only place where specific framework / tool / language names appear. Bridges map the tool-agnostic methodology onto a given stack (Flutter, Android Kotlin + XML, Android Jetpack Compose, Ktor, Unity 3D). Add more bridges for your own stack by copying [`docs/stack-bridge-template.md`](./docs/stack-bridge-template.md).

6. **Multi-agent bridge (Claude Code)** — [`.claude-plugin/agents/`](./.claude-plugin/agents/)
   Three role-bound sub-agents — `planner`, `implementer`, `reviewer` — with tool-permission matrices that enforce the multi-agent-handoff contract mechanically (Reviewer has no write tools; Planner has no edit tools; Implementer cannot spawn further sub-agents). See [`docs/multi-agent-handoff.md`](./docs/multi-agent-handoff.md) §tool-permission-matrix. Other runtimes apply the same matrix using their own agent mechanism (see `AGENTS.md` §7).

7. **Runnable starter example** — [`examples/starter-repo/`](./examples/starter-repo/)
   A minimal end-to-end demonstration: a schema-valid Change Manifest for a tiny change (`/healthz` endpoint), cited evidence artifacts, a closed ROADMAP initiative, and a 30-line validator. Clone and run `make validate` to see the full contract execute in under a minute. Use as a seed for your own project.

8. **Agent-runtime hook contract + reference bundle** — [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md) + [`reference-implementations/hooks-claude-code/`](./reference-implementations/hooks-claude-code/)
   A tool-agnostic contract for **event-driven guardrails inside the agent's own loop** (pre-commit, post-tool-use, on-stop). Four categories (phase-gate / evidence / drift / completion-audit), JSON-over-stdin event schema, exit-code semantics `0 = pass / 1 = block / 2 = warn`. A Claude Code reference bundle ships four POSIX-sh hooks wiring these categories onto `PreToolUse` / `PostToolUse` / `Stop` events — see the [Agent-runtime hooks](#agent-runtime-hooks) section below for install steps.

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
├── schemas/                    # Change Manifest JSON Schema
│   └── change-manifest.schema.yaml
├── templates/                  # Change Manifest examples
│   ├── change-manifest.example-crud.yaml
│   ├── change-manifest.example-mobile-offline.yaml
│   ├── change-manifest.example-game-gacha.yaml
│   └── change-manifest.example-multi-agent-handoff.yaml
├── reference-implementations/  # Non-normative example validators + hook bundles
│   ├── validator-posix-shell/  # POSIX shell + yq + pluggable schema validator (minimal)
│   ├── validator-python/       # Python 3.10+ validator (covers all rules including 2.4, 2.5, 3.2, 3.4)
│   ├── hooks-claude-code/      # Runtime-hook reference bundle + selftest harness
│   ├── hooks-cursor/           # Cursor adapter
│   ├── hooks-gemini-cli/       # Gemini CLI adapter
│   ├── hooks-windsurf/         # Windsurf adapter
│   └── hooks-codex/            # Codex adapter
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

1. [`docs/onboarding/orientation.md`](./docs/onboarding/orientation.md)
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
- Writing agent-runtime hooks (pre-tool-use, pre-commit, on-stop) → [Agent-runtime hooks](#agent-runtime-hooks) section below + [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md) + [`reference-implementations/hooks-claude-code/`](./reference-implementations/hooks-claude-code/)

---

## Agent-runtime hooks

**What this is.** Event-driven guardrails that fire **inside the AI agent's own execution loop** — before each tool call, after each edit, at end-of-turn — not in CI. They exist to catch failures early (while the agent can still correct) instead of late (after a PR has shipped). Sibling to [`docs/ci-cd-integration-hooks.md`](./docs/ci-cd-integration-hooks.md), which covers the CI/CD layer; the two share the same exit-code contract (`0 = pass / 1 = block / 2 = warn`).

**Normative contract.** [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md) — defines four categories (A phase-gate / B evidence / C drift / D completion-audit), JSON-over-stdin event schema, latency budgets (< 500 ms for A/B, < 2 s for C), non-functional requirements (offline, deterministic, no side effects, no model-in-hook).

**Reference bundles.** The primary bundle lives at [`reference-implementations/hooks-claude-code/`](./reference-implementations/hooks-claude-code/) and ships five POSIX-sh hooks (`manifest-required.sh`, `evidence-artifact-exists.sh`, `sot-drift-check.sh`, `consumer-registry-check.sh`, `completion-audit.sh`), a `settings.example.json` wiring them to Claude Code's native events, a README, a DEVIATIONS.md, and a hermetic self-test harness under `selftests/`. Thin adapter bundles for [Cursor](./reference-implementations/hooks-cursor/), [Gemini CLI](./reference-implementations/hooks-gemini-cli/), [Windsurf](./reference-implementations/hooks-windsurf/), and [Codex](./reference-implementations/hooks-codex/) reuse the same hook scripts under each runtime's native registration format.

### The five reference hooks

| Hook | Category | Checks | Blocks (exit 1) / Warns (exit 2) |
|---|---|---|---|
| `manifest-required.sh` | A phase-gate | Non-trivial git commits have a staged Change Manifest | Block |
| `evidence-artifact-exists.sh` | B evidence | Every `evidence_plan[].status == collected` has a resolvable `artifact_location` | Block |
| `sot-drift-check.sh` | C drift | Declared `sot_map[].source` files appear in `git diff --name-only` | Warn |
| `consumer-registry-check.sh` | C drift (network) | Each `consumers[].external_registry_url` responds 2xx within `AGENT_PROTOCOL_NET_TIMEOUT` | Warn |
| `completion-audit.sh` | D completion-audit | On-stop: no pending `evidence_plan`, no `accepted_by: unaccepted`, every escalation has `resolved_at`, `phase: observe` has `handoff_narrative` | Block |

### Install on Claude Code

Prerequisites:

- [`yq`](https://github.com/mikefarah/yq) v4+ on PATH (`brew install yq` / `apt install yq`). If missing, hooks exit 2 with `TOOL_ERROR: yq not found on PATH` — they degrade gracefully, they do not spuriously block commits.
- `git` on PATH (already assumed).

**Step 1.** Copy the hooks bundle to a stable location (don't invoke directly from the plugin cache — version bumps move that path):

```bash
mkdir -p ~/.claude/agent-protocol-hooks
cp -r reference-implementations/hooks-claude-code/hooks ~/.claude/agent-protocol-hooks/
```

Or for project-local hooks (only fire inside this repo):

```bash
mkdir -p <your-project>/.claude/hooks
cp reference-implementations/hooks-claude-code/hooks/*.sh <your-project>/.claude/hooks/
```

**Step 2.** Merge the hook block from [`reference-implementations/hooks-claude-code/settings.example.json`](./reference-implementations/hooks-claude-code/settings.example.json) into your `~/.claude/settings.json` (global) or `<your-project>/.claude/settings.json` (project-local). The shape is:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          {"type": "command", "command": "sh ${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/hooks/manifest-required.sh"},
          {"type": "command", "command": "sh ${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/hooks/evidence-artifact-exists.sh"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {"type": "command", "command": "sh ${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/hooks/sot-drift-check.sh"}
        ]
      }
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "sh ${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/hooks/completion-audit.sh"}]}
    ]
  }
}
```

**Step 3.** Reload plugins (`/reload-plugins`). Trigger a test: start a commit with an unrelated file and no manifest — `manifest-required.sh` should fire and exit 1.

### Contract-to-event mapping

| Contract trigger (abstract) | Claude Code native event | Matcher | Why this mapping |
|---|---|---|---|
| `pre-commit` | `PreToolUse` | `Bash(git commit*)` | Fires **before** the Bash tool runs `git commit` — exit 1 cancels the commit before it lands. `PostToolUse` would fire after the commit, giving the hook no blocking power. |
| `post-tool-use:Edit` | `PostToolUse` | `Edit\|Write\|MultiEdit` | Drift checks are informational — they read state after an edit and warn, not block. |
| `on-stop` | `Stop` | (no matcher) | Fires at end-of-turn before the agent surfaces "done" to the user. Exit 1 blocks the turn from completing. |

Other contract triggers (`on-phase-transition`) are not currently mapped by the reference bundle — teams can add custom hooks firing on `UserPromptSubmit` or `SessionStart` per [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md).

### Configuration knobs (environment variables)

| Variable | Default | Effect |
|---|---|---|
| `AGENT_PROTOCOL_MANIFEST_PATH` | `git ls-files change-manifest*.yaml \| head -1` | Point hooks at a specific manifest path; useful when multiple manifests coexist in a monorepo. |
| `AGENT_PROTOCOL_MIN_EVIDENCE_PER_PRIMARY` | `1` | Minimum evidence items required per `role: primary` surface. Raise for stricter gating. |
| `AGENT_PROTOCOL_LEAN_SKIP_MANIFEST` | unset | Set to `1` and create an empty `lean-mode.flag` file at the repo root to let `manifest-required.sh` pass for Lean-mode trivial changes. |
| `AGENT_PROTOCOL_STRUCTURED_OUTPUT` | unset | Set to `1` to emit structured JSON on stdout (per the contract's optional output shape) in addition to stderr messages. Useful for aggregation dashboards. |

Set these in `~/.zshrc`, `~/.bashrc`, or per-project `.envrc` (direnv) — **not** inside the hook scripts themselves.

### Adoption ramp

Don't enable all four hooks on day one. Common staging:

1. **Week 1 — Observe.** Install `sot-drift-check.sh` only (warn-level; can't block). See what fires, tune the manifest if the signal is noisy.
2. **Week 2 — Gate.** Add `manifest-required.sh` at block-level. Creates a forcing function: non-trivial commits now require a manifest.
3. **Week 3 — Evidence.** Add `evidence-artifact-exists.sh`. Catches the "`status: collected` with blank `artifact_location`" failure mode.
4. **Week 4 — Completion.** Add `completion-audit.sh` (on-stop). The highest-leverage hook — refuses to let the agent say "done" when the manifest is materially incomplete.

Skipping straight to stage 4 usually produces "hook fatigue" — teams disable the whole bundle rather than tune it.

### Writing your own hook

The four shipped hooks are ~50–80 lines of POSIX sh each; read them as templates. A custom hook must:

1. Parse the event payload from stdin (or Claude Code env vars; the reference hooks do a best-effort read of both).
2. Read the Change Manifest via `yq` (or any YAML library in your language of choice — hooks aren't required to be shell).
3. Exit `0` / `1` / `2` per the contract. Stderr on non-zero with a one-sentence human message prefixed by `[agent-protocol/<rule_id>]`.
4. Stay offline, deterministic, side-effect-free, and under the latency budget (< 500 ms for A/B; < 2 s for C). **No model-in-hook** — hooks are mechanical decision nodes, not agents.

Register the custom hook by adding another `{"type": "command", "command": "..."}` entry under the appropriate event's `hooks` array in `settings.json`.

See [`docs/runtime-hook-contract.md`](./docs/runtime-hook-contract.md) for the full anti-pattern list (kitchen-sink hooks, silent-swallow, network-gated, side-effect, AI-in-the-loop, hook sprawl).

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
