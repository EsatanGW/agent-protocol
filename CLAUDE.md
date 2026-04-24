# CLAUDE.md

Guidance for Claude Code when working **on** this repository (i.e. when a contributor clones this repo and uses Claude Code to edit the plugin itself).

> If you are **using** this plugin in your own project, read [`AGENTS.md`](./AGENTS.md) instead — it is the runtime operating contract that applies to all AI agents, including Claude Code.

---

## Repository role

This repo is a **tool-agnostic engineering workflow plugin**, not a codebase for any specific product or stack. Its role is to define methodology (`docs/`) and execution guidance (`skills/`) that other AI runtimes can consume.

---

## Rules for editing this repo

### 1. Default to documentation-type edits

- You may edit `docs/`, `skills/`, `templates/`, `schemas/`, and repo-level markdown.
- Do **not** invent unrelated code changes. This repo does not have an application runtime — almost all work is markdown, YAML, and JSON.

### 2. Do not neutralize into branded tools

- This repo is deliberately tool-agnostic. Do **not** introduce vendor names, model names, framework names, or product names into normative content.
- Capabilities must be named as categories (file read, code search, shell execution, sub-agent delegation), not as specific tools.

### 3. Do not rewrite historical CHANGELOG entries

- CHANGELOG is a factual record. If a past entry used an old term, leave it as a historical fact and explain the rename in the new entry.

### 4. Follow the operating contract

The runtime operating contract in [`AGENTS.md`](./AGENTS.md) also applies to Claude Code while editing this repo:

- Honest reporting, no fabricated completion
- Scope discipline, no opportunistic cleanup
- Surface-first analysis before proposing changes
- Source-of-truth discipline (e.g. if a term is defined in `docs/glossary.md`, do not redefine it in another file)
- Change Manifest for non-trivial edits (see `docs/change-manifest-spec.md`)

### 5. When you touch a cross-cutting term

If you change a term that appears in multiple files (e.g. a canonical name in `docs/glossary.md`, a surface definition in `docs/surfaces.md`, a phase file name in `skills/`), **find and update all consumers** in the same change. Drift between canonical source and consumers is the anti-pattern this repo most often warns against; do not create it here.

**Mode implication.** A canonical methodology content edit at breaking-change level ≥ L1 (changing an existing normative claim, adding a new normative rule to SoT, or renaming a cross-cutting term) is a forced-Full trigger — see the "Canonical methodology content edit (L1+)" row in [`skills/engineering-workflow/references/mode-decision-tree.md §Scenarios that force Full`](./skills/engineering-workflow/references/mode-decision-tree.md). Purely additive L0 edits (new non-normative reference files, pointer additions, CHANGELOG entries) remain Lean-eligible. Default to the lightest mode the scenario tables allow; upgrade on discovery rather than force-fitting the original pick. The upgrade procedure lives in `mode-decision-tree.md §Mode upgrade / downgrade`; silent scope-shrink to avoid the upgrade is prohibited per `AGENTS.md §6`.

---

## Multi-agent packaging

This repo is simultaneously a:

1. **Claude Code plugin** — via `.claude-plugin/` + `skills/`
2. **Agents.md-compatible plugin** — via `AGENTS.md` (Codex, Aider, OpenCode, Windsurf, etc.)
3. **Cursor rules bundle** — via `.cursor/rules/`
4. **Gemini CLI instruction set** — via `GEMINI.md`
5. **Windsurf rules** — via `.windsurfrules`

When you change something that affects the operating contract or skill structure, update **all** entry points so they stay consistent. The canonical content lives in `AGENTS.md` + `skills/` + `docs/`; the other entry points are thin bridges that point back here.

---

## See also

- [`AGENTS.md`](./AGENTS.md) — runtime operating contract (start here)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — contribution policy
- [`VERSIONING.md`](./VERSIONING.md) — version strategy
- [`CHANGELOG.md`](./CHANGELOG.md) — version history
