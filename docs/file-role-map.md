# File Role Map

> **English TL;DR**
> Where every normative claim in this repo is **allowed to live**, indexed by file. The runtime entry-point table in [`AGENTS.md`](../AGENTS.md) tells you which file each runtime loads first; this map tells you which file each rule's *source of truth* lives in. Drift between duplicated rules is the anti-pattern this repo most often warns against; this map is the index that prevents it.

This doc is the **single source of truth** for the per-file role classification. [`AGENTS.md`](../AGENTS.md) carries a one-paragraph pointer to here; every other entry-point file inherits the classification by reference.

---

## Why this exists

A normative rule (e.g. "Reviewer has no write tools", "Pattern 9 binds dispatch-class names", "evidence_plan rows need provenance") must appear in **exactly one** file. Every other file that touches the rule cites that source by name. When two files state the same rule in different words, one of them is wrong; the file role map is the index that says which one.

Without the map, the same rule drifts across `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/*.mdc`, `agents/*.md`, and `reference-implementations/roles/*.md`. Each restatement is a chance for the wording to shift. The map fixes the canonical home and makes every other appearance a citation.

---

## The map

| File / directory | Role | Normative weight |
|---|---|---|
| [`AGENTS.md`](../AGENTS.md) | SoT — operating contract (the 10 core rules) | Canonical; all runtimes inherit from here |
| [`multi-agent-handoff.md`](multi-agent-handoff.md) | SoT — role contract (Planner / Implementer / Reviewer definitions, field-ownership matrix, tool-permission matrix, anti-collusion, handoff minima, Task Prompt structure) | Canonical for multi-agent discipline; `agents/`, `.cursor/rules/`, `reference-implementations/roles/` all point back here |
| `docs/*.md` (other) | SoT — topic-specific definitions ([`surfaces.md`](surfaces.md), [`source-of-truth-patterns.md`](source-of-truth-patterns.md), [`breaking-change-framework.md`](breaking-change-framework.md), [`rollback-asymmetry.md`](rollback-asymmetry.md), [`phase-gate-discipline.md`](phase-gate-discipline.md), [`ai-operating-contract.md`](ai-operating-contract.md), [`agent-persona-discipline.md`](agent-persona-discipline.md), [`output-craft-discipline.md`](output-craft-discipline.md), [`glossary.md`](glossary.md), [`phase-command-vocabulary.md`](phase-command-vocabulary.md), [`repo-as-context-discipline.md`](repo-as-context-discipline.md), [`mechanical-enforcement-discipline.md`](mechanical-enforcement-discipline.md), [`tool-design-principles.md`](tool-design-principles.md), [`anti-entropy-discipline.md`](anti-entropy-discipline.md), [`autonomy-ladder-discipline.md`](autonomy-ladder-discipline.md), [`observability-legibility-discipline.md`](observability-legibility-discipline.md), [`throughput-first-merge-philosophy.md`](throughput-first-merge-philosophy.md), …) | Canonical per topic; referenced from the contracts above |
| [`skills/engineering-workflow/SKILL.md`](../skills/engineering-workflow/SKILL.md) + `skills/**` | SoT — execution layer (modes, phases, templates, references) | Canonical for workflow execution |
| [`schemas/`](../schemas/) + [`skills/engineering-workflow/templates/manifests/`](../skills/engineering-workflow/templates/manifests/) | SoT — machine-readable Change Manifest contract + worked examples | Canonical structural output |
| [`CLAUDE.md`](../CLAUDE.md) | Thin-bridge — Claude Code entry; points at [`AGENTS.md`](../AGENTS.md) + `skills/` | Onboarding only, no new normative content |
| [`GEMINI.md`](../GEMINI.md) | Thin-bridge — Gemini CLI entry | Same |
| `.windsurfrules` | Thin-bridge — Windsurf entry | Same |
| `.codex-plugin/plugin.json` | Thin-bridge — Codex plugin manifest | Metadata and UI entry only; execution rules remain in [`AGENTS.md`](../AGENTS.md) + `skills/` |
| `.agents/plugins/marketplace.json` | Thin-bridge — Codex local marketplace entry | Points Codex at the repository root plugin; no new normative content |
| `.cursor/rules/engineering-workflow.mdc` | Thin-bridge with `alwaysApply: true` — Cursor repo-level onboarding | Condensed summary only; every bullet must defer to a `docs/` source |
| `.cursor/rules/{planner,implementer,reviewer}.mdc` | Runtime role-spec — Cursor Custom Mode system prompts | Must remain self-contained because Cursor does not auto-resolve Markdown path references; normative rules are mirrored **from** [`multi-agent-handoff.md`](multi-agent-handoff.md), never authored here |
| `agents/{planner,implementer,reviewer}.md` | Runtime role-spec — Claude Code sub-agent definitions with mechanical `tools:` enforcement | Role behaviour must cite [`multi-agent-handoff.md`](multi-agent-handoff.md) as the source; runtime-specific supplements (Lean-mode collapse, tool-permission rows) are allowed, new normative rules are not |
| `reference-implementations/roles/*.md` | Reference wrappers — runtime-neutral paste-ready prompts for Gemini / Windsurf / Codex / Aider | Never introduce normative content; if the wrapper says something [`multi-agent-handoff.md`](multi-agent-handoff.md) does not, one of them is wrong |
| `reference-implementations/roles/specialist-roles-registry.md` | Reference wrapper — starter registry for specialist sub-agent roles (`architect`, `security-reviewer`, `performance-reviewer`) per [`multi-agent-handoff.md`](multi-agent-handoff.md) §Composable specialist sub-agent roles | Non-normative reference; bridges may copy / extend / replace entries. Specialist contract itself lives in [`multi-agent-handoff.md`](multi-agent-handoff.md); this file lists which specialists exist |
| `reference-implementations/validator-{posix-shell,python}/` | First-class reference wrappers — executable validators for the automation contract | Track the spec in [`automation-contract.md`](automation-contract.md) / [`automation-contract-algorithm.md`](automation-contract-algorithm.md); `DEVIATIONS.md` is the gap record |
| `reference-implementations/community/validator-node/` | **Community-maintained** reference wrapper (demoted from first-class in 1.20.0); functional sibling to `validator-python/` for JS/TS/web-leaning CI. Rule parity not guaranteed; adopters verify via the bundled tests | Non-normative; not covered by official `role-consistency` / parity gates |
| `reference-implementations/INVENTORY.md` | Non-normative classifier — flags each entry under `reference-implementations/` as `runtime-glue` (executable / runtime-specific config) or `documentation` (prose mirror, future-relocatable to `docs/`) | Reviewer / audit aid only; not cited from `docs/` |
| [`README.md`](README.md) | Non-normative — 4-tier index of every methodology file under `docs/` (onboarding / core contract / disciplines / references) | Discoverability layer; renames in `docs/` must update this index in the same change |
| [`decision-trees.md`](decision-trees.md) | Non-normative — 4 routing decisions (manifest-needed / SoT pattern / single vs multi-agent / HITL escalation), each routing to its canonical source | Quick decision hub; binding rules stay in the canonical sources it cites |
| [`change-manifest-spec-cookbook.md`](change-manifest-spec-cookbook.md) | Non-normative companion to [`change-manifest-spec.md`](change-manifest-spec.md) — CI integration recipes, AI usage modes, mission-shaped manifests, example tour | Spec wins on contradiction; cookbook holds applied material only |
| [`sot-desync-anti-patterns.md`](sot-desync-anti-patterns.md) | Non-normative diagnostic appendix to [`source-of-truth-patterns.md`](source-of-truth-patterns.md) — 7 anti-patterns + 4 repair strategies + mapping | Identification stays in the spec; diagnosis lives in the appendix |
| [`evidence-quality-per-type.md`](evidence-quality-per-type.md) | Non-normative companion appendix to [`change-manifest-spec.md`](change-manifest-spec.md) — per-type artefact-shape and rejection-signal guidance for all `evidence_plan[*].type` enum values | Companion only; per-type rules in the appendix do not bind unless promoted to schema |
| [`examples/consumer-docs-scaffolding.md`](examples/consumer-docs-scaffolding.md) + [`examples/quality-score-template.md`](examples/quality-score-template.md) | Non-normative examples — reference layout for a consumer project's repo and a fillable `QUALITY_SCORE.md` template | Example-tier; teams adapt without methodology approval |

---

## Where a new rule belongs

- New **operating-contract rule** (applies to every runtime) → extend §Core operating contract in [`AGENTS.md`](../AGENTS.md); bridges and role-spec files inherit automatically.
- New **multi-agent / role-boundary rule** → [`multi-agent-handoff.md`](multi-agent-handoff.md) first; update every consumer that cites it in the same change (per [`../CLAUDE.md`](../CLAUDE.md) §5).
- New **topic-specific definition** (a surface type, an SoT pattern, a breaking-change level, a rung threshold, an observability-legibility rule) → its own `docs/*.md` file or section; contracts reference it.
- New **runtime-specific shim** (Cursor quirk, Gemini session idiom, Claude Code frontmatter field) → thin-bridge or runtime role-spec file only; never in `docs/` or [`AGENTS.md`](../AGENTS.md).
- New **reference implementation** → `reference-implementations/…` with `README.md` + `DEVIATIONS.md`. Always non-normative.

---

## The invariant this map enforces

A normative claim appears in **exactly one** SoT file. Every consumer cites that section by name. When two files state the same rule in different words, the thin-bridge / runtime role-spec / reference wrapper yields; the SoT file wins.
