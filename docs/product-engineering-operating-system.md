# Product Engineering Operating System

> **English TL;DR**
> The plugin's *preamble* — the six principles every other doc inherits. (1) **We manage changes, not code** — code is one of several traces a change leaves; managing only code leads to "looks done, isn't consistent." (2) **We don't slice the world by stack** — surfaces beat layers; cross-surface desync is the primary failure mode. (3) **Source of truth per informational asset** — exactly one authoritative origin; everything else re-syncs. (4) **Breaking change is defined by worst-case consumer** — not by "does it compile." (5) **Rollback is asymmetric to rollout** — some changes are reversible, some require forward-fix, some require compensation; choose the mode at plan time, not at incident time. (6) **Delivery is phase-gated, evidence-driven** — Phase 0-8 with explicit evidence at each gate; the Change Manifest is the evidence carrier. If you only read one file to understand the philosophy, read this one after `system-change-perspective.md`.

This document is the preamble for the entire plugin — the orientation every other document inherits from.

## 1. We are managing changes, not code

Code is only one of the traces a change leaves behind. A real requirement-driven change typically touches all of the following simultaneously:

- The behavior the user perceives
- The interface the system exposes to the outside world
- The definitions of internal data and state
- The cost of operations and handoff

If you manage only the code and ignore those other traces, you end up in the "it looks done but the system is not actually consistent" state.

## 2. We do not slice the world by stack

Slicing the world by stack tends to produce:

- Each person only looking at their own layer
- Problems being locally optimized at the expense of the whole
- Contracts, enums, validation, and docs drifting apart from each other
- "Delivery" degenerating into "my side is done"

This plugin slices the world by **capability and surface** instead.

## 3. The four surfaces of a mature change

> Full definitions, the composable-surface system, and extension rules live in [`docs/surfaces.md`](./surfaces.md).

### User surface

What a human user actually sees, clicks, waits for, errors on, and interprets.

### System interface surface

How the system talks to other systems and modules.

### Information surface

Data structure, field semantics, state definitions, validation rules, configuration keys.

### Operational surface

Logs, audit trail, observability, documentation, migration, rollout, rollback, handoff.

## 4. A good delivery is more than "the feature works"

A good delivery means:

- The source of truth is unambiguous.
- Consumers have not been broken by accident.
- The verification approach was designed, not improvised.
- Evidence is sufficient to back the completion claim.
- When something goes wrong, there is a way to investigate, roll back, and hand off.

## 5. The role of AI in this system

AI in this plugin is not a substitute for local coding. Its value lies in:

- Helping you see the change completely.
- Helping you enumerate the full impact.
- Helping you design verification and evidence correctly.
- Making delivery traceable, reviewable, and operable.

## 6. The most important outputs of this plugin

The output of this methodology is not a code diff. It is whether the following five artifacts are complete and coherent:

1. Problem definition
2. Change map
3. Verification plan
4. Evidence trail
5. Handoff narrative
