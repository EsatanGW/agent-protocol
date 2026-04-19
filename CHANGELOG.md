# Changelog

All notable changes to this project will be documented in this file.

Format inspired by Keep a Changelog; versioning policy in `VERSIONING.md`.

## [1.0.0] - 2026-04-19

Initial public release. Tool-agnostic engineering workflow plugin for AI coding agents, usable across Claude Code, Cursor, Gemini CLI, Windsurf, Codex, Aider, OpenCode, or any AI runtime that reads `AGENTS.md`.

### Included

- **Operating contract** — `AGENTS.md` defines the universal runtime contract: honest reporting, scope discipline, source-of-truth rules, surface-first analysis, evidence requirements, Change Manifest contract, phase-gate discipline.
- **Engineering workflow skill** — `skills/engineering-workflow/` provides Lean and Full modes, phase minimums for Phase 0 through Phase 8, capability-category guidance, and spec / plan / test / completion templates. Supporting references cover the mode decision tree, discovery loop, resumption protocol, startup checklist, and misuse signals.
- **Methodology documentation** — `docs/` contains the four canonical surfaces plus nine extension surfaces (asset, experience, performance-budget, data-quality, compliance, hardware-interface, real-world, model, uncontrollable-external), ten Source-of-Truth patterns, the L0–L4 breaking-change severity matrix, three rollback modes (Reversible / Forward-fix / Compensation-only), cross-cutting concerns, the AI operating contract, security and supply-chain disciplines, change decomposition, team / org-scale disciplines, AI project memory, multi-agent handoff, automation contract, and phase-gate discipline.
- **Change Manifest contract** — `schemas/change-manifest.schema.yaml` plus four worked example manifests (CRUD, mobile offline, game gacha, multi-agent handoff progression). The schema enforces human-approver waivers, expiry timestamps, bidirectional decomposition links, and phase-appropriate narrative fields.
- **Stack bridges** — `docs/bridges/` maps the tool-agnostic methodology to concrete stacks: Flutter, Android Kotlin + XML, Ktor, Unity 3D. Bridge files are the only place where specific vendor / framework / language names appear. The stack-bridge template (`docs/stack-bridge-template.md`) supports adding your own stack.
- **Automation contract** — capability-level specification (`docs/automation-contract.md`) plus normative algorithm (`docs/automation-contract-algorithm.md`) defining three forced check layers (structural / cross-reference / drift), exit-code stability, and offline operability. A non-normative reference validator (`reference-implementations/validator-posix-shell/`) built on POSIX shell plus `yq` plus a pluggable schema validator illustrates the contract.
- **Worked examples** — `docs/examples/` covers ten domains: worked (batch-resend invoices), bugfix (pagination-filter desync), refactor (order-status canonical alignment), migration-rollout (structured-preferences SoT transition), game-dev (in-game shop), game-liveops (three-track asset/config/binary strategy), mobile-offline-feature, ml-model-training, data-pipeline, embedded-firmware (OTA with hardware-interface + real-world surfaces).
- **Multi-agent entry points** — packaged simultaneously as a Claude Code plugin (`.claude-plugin/`), a Cursor rules bundle (`.cursor/rules/`), a Gemini CLI instruction set (`GEMINI.md`), Windsurf rules (`.windsurfrules`), and an AGENTS.md-compatible contract for Codex / Aider / OpenCode.

### Design invariants

- **English-only.** All normative content — methodology, skills, schemas, templates, operating contract, READMEs — is English. No mixed-language documents; no translation companions.
- **Tool-agnostic.** Specific vendor, model, framework, or product names appear only in `docs/bridges/` and `reference-implementations/`, both of which are explicitly marked non-normative. Methodology docs, the skill layer, the schema, and the Change Manifest templates remain stack-neutral.
- **Capability categories, not tool names.** Every operational instruction names a category (file read, file write, code search, shell execution, sub-agent delegation) rather than a specific tool, so the plugin ports cleanly between AI runtimes.
- **Canonical terminology held fixed.** Severity L0–L4 (Additive / Behavioral / Structural / Removal / Semantic-reversal), rollback modes 1/2/3 (Reversible / Forward-fix / Compensation-only), four canonical surfaces plus extension surfaces, SoT patterns addressed by number, automation tiers L0–L3, three multi-agent roles by responsibility (Planner / Implementer / Reviewer).

### License

MIT. Fork, localize, customize internally.
