# System Change Perspective

> **English TL;DR**
> The shared mental model behind every other doc: **do not start by asking "which layer?" — start by asking "which surfaces?"** Layer-first thinking (frontend / backend / DB) makes each contributor see only their slice and lets cross-surface desync slip through. Surface-first thinking forces you to see the full trace of a change before it's coded. This file defends the *why* with four surface-entry questions that map directly to the four core surfaces (what does the user see, what did the system expose outward, what changed in the shape of our information, what does operations now carry that it didn't before). The canonical surface definitions and the full five-question §60-second opener analysis checklist live in `surfaces.md`. Read this before any other doc if you are new to the methodology.

This document defines the shared perspective the rest of the plugin is written from.

> The canonical four-surface definitions, the extension mechanism, and the §60-second opener analysis checklist live in [`docs/surfaces.md`](./surfaces.md).
> This file only defends the perspective; it deliberately does not redefine surfaces, so the two files cannot drift.

---

## Don't start by asking "whose layer?"

Do not start with:

- Is this a frontend problem?
- Is this a backend problem?
- Is this a database problem?

Start with:

- What does the user see?
- What did the system expose to the outside world?
- What changed in the shape of our information?
- What does operations and maintenance now have to carry that it didn't before?

These four questions map directly to the four core surfaces (definitions in `surfaces.md`).

---

## Why layer-first thinking misses things

Slicing the world as "frontend / backend / DB" produces recurring symptoms:

| Symptom | Root cause |
|---------|------------|
| Contract inconsistency | Each side only looks at its own layer; nobody owns the middle API contract |
| Enum / status desync | The information surface crosses layers and has no single owner |
| Validation fragmented | Frontend validates one way, backend another, the DB adds its own constraints |
| Docs drift from implementation | The operational surface is always the last thing anyone remembers |
| "My side is done" | Delivery gets cut into local completions while the whole never actually completes |

The point of a surface-first perspective is not to replace division of labor — it is to **force the cross-layer seams to be visible**.

---

## Perspective vs. process

- **Perspective** (this file + `surfaces.md`): how to look at a change.
- **Process** (`product-engineering-operating-system.md`, the phase docs): how to execute once you've seen.
- **Automation / execution layer** (optional): if the team uses AI agents or any other process automation, that automation sits on top of this perspective.

Perspective comes first; without it, process turns into ceremony.
