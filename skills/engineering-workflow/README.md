# engineering-workflow

A high-level engineering-workflow skill. Tool-agnostic and platform-agnostic; usable in any AI runtime that supports skill / rule loading.

It builds on the public methodology and supplies what the execution layer actually needs:
- When to trigger.
- When not to trigger.
- The **four execution modes** (Zero-ceremony / Three-line delivery / Lean / Full) and how to pick among them.
- Which **capability categories** each phase should prefer (file read/write, code search, shell execution, etc. — not specific tool names).
- When to produce spec / plan / test / completion artifacts.
- How to resume safely after an interruption.
- How to avoid over-applying the skill.

## Recommended companion reading

Public examples:
- `docs/examples/worked-example.md`
- `docs/examples/bugfix-example.md`
- `docs/examples/refactor-example.md`
- `docs/examples/migration-rollout-example.md`

Startup aids:
- `references/startup-checklist.md`
- `references/session-opener-snippet.md`
- `references/resumption-protocol.md`
- `references/misuse-signals.md`
- `references/mode-decision-tree.md` — canonical decision tree for the four execution modes.
- `references/discovery-loop.md` — rewind mechanism for scope growth discovered during implementation.

Phase minimums:
- `SKILL.md §Phase minimums` — inline Lean-vs-Full phase × mode matrix.

Lean templates:
- `templates/lean-spec-template.md`
- `templates/lean-verification-template.md`
- `templates/lean-delivery-template.md`

The goal of this skill is not to freeze every task into the same shape,
but to let the executor pick a workflow that is sufficient but not excessive for the engineering task at hand.
