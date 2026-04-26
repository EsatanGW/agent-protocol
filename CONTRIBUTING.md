# Contributing

Thank you for contributing.

This repository has two distinct outputs:
1. Public engineering method documentation
2. Tool-agnostic execution skill (`engineering-workflow`)

Please keep that separation explicit in every change.

## Before opening a PR

Check whether your change belongs to:
- `docs/` → public, agent-agnostic method
- `skills/engineering-workflow/` → execution guidance (still tool-agnostic; describes capability categories, not specific tool names)

If a change affects both layers, explain why.

## Contribution principles

1. Do not reintroduce company-specific or confidential content
2. Do not assume a specific framework unless the file is explicitly framework-scoped
3. Keep the public layer tool-agnostic
4. Keep the skill layer operational and execution-oriented, but still tool-agnostic — refer to capability categories (file read, code search, shell, browser, sub-agent delegation), not vendor-specific tool names
5. Do not name specific AI agents, products, or vendors in normative content
6. Prefer examples that illustrate patterns, not real proprietary systems

## Suggested PR structure

- Problem statement
- Why this belongs in the public layer, skill layer, or both
- What files changed
- Whether behavior changed, wording changed, or only structure changed
- Any follow-up work left open

## Style guidelines

- Prioritize clarity over cleverness
- Use the system-change perspective consistently
- Prefer "source of truth", "consumer", "affected surfaces", and "evidence" framing
- Avoid stack-first framing unless the document is explicitly about implementation disciplines
- Avoid agent-specific or tool-specific framing in normative docs

## File-naming conventions

To keep cross-references stable and grep-friendly, follow these rules when creating files under `docs/` or `skills/engineering-workflow/references/`:

- **Use `kebab-case`** (lowercase, hyphens between words). No spaces, underscores, or camelCase.
- **Head noun last** — the rightmost word should be the document's primary noun (the *what*); preceding words are modifiers. Examples:
  - `parallelization-patterns.md` (head: patterns)
  - `phase-overlap-zones.md` (head: zones, modifier: phase-overlap)
  - `cluster-parallelism.md` (head: parallelism, modifier: cluster)
  - `mode-decision-tree.md` (head: tree, modifiers: mode-decision)
- **Avoid trailing `-spec`, `-doc`, `-readme`** — the file's role is conveyed by its location and frontmatter, not its suffix. Exceptions: well-established names already in use (e.g. `change-manifest-spec.md`).
- **Stable filenames are SoT addresses.** Renaming a file invalidates every cross-reference; treat it as a breaking change requiring a Change Manifest (see [`docs/change-manifest-spec.md`](docs/change-manifest-spec.md)). Prefer adding a new file over renaming an old one when scope shifts.

## Good changes

- Add a new worked example for a common engineering scenario
- Improve Lean / Full decision guidance
- Clarify capability-category usage in workflow phases
- Improve publication quality, onboarding, or handoff clarity

## Changes to avoid

- Reintroducing internal product names, ticket IDs, or private payloads
- Naming specific AI agents, models, or vendors in normative content
- Naming specific tool APIs (e.g. a particular `read_file` / `search_files` function) — use capability categories instead
- Making the public docs depend on execution-layer concepts
- Making the skill depend on a single framework, language, or runtime
