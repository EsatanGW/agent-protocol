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

## Multi-agent role separation (Full mode)

For non-trivial changes, `AGENTS.md` §7 defines three role identities with enforced tool-permission matrices:

- **Planner** — read-only + spawn; no write/edit tools.
- **Implementer** — read + write + shell; no sub-agent spawn.
- **Reviewer** — read + verification-only shell; **no write/edit tools** (enforced; self-review is the failure mode the methodology is designed against).

Gemini CLI does not gate tool exposure per persona, so enforcement of the above is **prose-only** plus session isolation. Recommended practice:

1. Open a distinct Gemini CLI session per role (not just distinct prompts within one session — each persona must have its own conversation history).
2. Paste the role prompt at session start:
   - Planner: [`reference-implementations/roles/planner.md`](./reference-implementations/roles/planner.md)
   - Implementer: [`reference-implementations/roles/implementer.md`](./reference-implementations/roles/implementer.md)
   - Reviewer: [`reference-implementations/roles/reviewer.md`](./reference-implementations/roles/reviewer.md)
3. For the Reviewer, consider running in a read-only working-directory or git-worktree so the absence of write capability is OS-enforced, not purely prose-enforced.
4. Record session / model identity in `approvals` so retroactive audit can spot Implementer ≡ Reviewer collusion.

Full enforcement matrix across runtimes: `docs/multi-agent-handoff.md` §Enforcement across runtimes.

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
