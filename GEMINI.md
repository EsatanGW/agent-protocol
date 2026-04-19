# Gemini CLI Instructions

This repository ships a tool-agnostic engineering workflow plugin. The runtime operating contract lives in [`AGENTS.md`](./AGENTS.md) and applies to all AI agents, including Gemini.

## Read first

1. [`AGENTS.md`](./AGENTS.md) — operating contract (honest reporting, scope discipline, SoT, surface-first analysis, evidence, Change Manifest)
2. [`skills/engineering-workflow/SKILL.md`](./skills/engineering-workflow/SKILL.md) — the workflow execution layer (Lean / Full modes, phase minimums, artifact templates)

## Key references for any non-trivial task

- `docs/surfaces.md` — four canonical surfaces
- `docs/source-of-truth-patterns.md` — SoT patterns and desync repair
- `docs/breaking-change-framework.md` — breaking change severity matrix
- `docs/rollback-asymmetry.md` — rollback modes
- `docs/cross-cutting-concerns.md` — security, performance, observability, testability, error handling
- `schemas/change-manifest.schema.yaml` — structured AI output contract
- `templates/change-manifest.example-*.yaml` — worked examples

## Tool capability mapping

The skill names **capability categories** (file read, code search, shell execution, sub-agent delegation). Map each category to whatever Gemini CLI provides at runtime. Do not assume specific tool names.

## Before producing code

Answer these in order, per `skills/engineering-workflow/SKILL.md` "First 60 seconds":

1. Task kind (feature / bugfix / refactor / migration / investigation)
2. Affected surfaces
3. Source of truth
4. Main consumers
5. Public behavior impact
6. Lean or Full mode
7. Minimum artifact set
8. Required evidence before completion

If any answer is uncertain, stop and ask.
