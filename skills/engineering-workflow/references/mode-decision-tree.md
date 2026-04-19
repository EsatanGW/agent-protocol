# Lean / Full Mode Decision Tree

Use this tree at the start of Phase 0 to pick a mode.
The decision is not permanent — if the scope grows during implementation, upgrade (see `discovery-loop.md`).

---

## Fast call (30 seconds)

```
Does this change involve any of the following?
├── Schema / DB migration → Full
├── Public API contract change → Full
├── Payments / auth / PII → Full
├── Cross-team handoff required → Full
└── None of the above → continue

How many surfaces does it touch?
├── 1 surface → Lean
├── 2 surfaces
│   ├── Public behavior changes?
│   │   ├── Yes → Full
│   │   └── No  → Lean
│   └──
└── 3+ surfaces → Full

How many consumers are affected?
├── 0-1 known consumers → Lean
├── 2+ consumers → Full
└── Consumer count uncertain → Full (investigate first; may downgrade to Lean)
```

---

## Scenarios that force Full

The following must use Full mode **regardless of size**:

| Scenario | Reason |
|----------|--------|
| DB schema migration | Irreversible or expensive rollback — needs a full plan + rollback strategy. |
| Public API breaking change | Consumers may be outside your control. |
| Money / payments | Cost of error is extremely high. |
| Auth / authorization / PII | Security + compliance requirement. |
| Cross-team delivery | The handoff narrative must be complete. |
| Long-lived feature-flag coexistence | Needs an explicit flag lifecycle + cleanup plan. |

## Scenarios that force Lean

The following **should not** use Full mode (avoid over-engineering):

| Scenario | Reason |
|----------|--------|
| Copy / translation fix | Single surface, no logic change. |
| CSS / style tweak | Single surface, no contract impact. |
| Dependency patch bump | No behavior change. |
| Single bug fix with a clear root cause | Scope is known. |
| New log / metric (no behavior change) | Pure operational-surface enhancement. |

## Scenarios where no mode applies

See misuse-signal #4 in `misuse-signals.md`:
- Pure research / Q&A / environment inspection.
- One-off scripts / tool invocations.
- Code exploration (no changes).

---

## Mode upgrade / downgrade

### Lean → Full (upgrade)
Triggers:
- A new affected surface is discovered during implementation.
- More consumers than expected.
- A schema migration turns out to be required.
- The reviewer judges the risk was under-estimated.

Procedure:
1. Pause implementation.
2. Complete the Full-mode artifacts (spec → plan → test plan).
3. Re-enter from the current phase.

### Full → Lean (downgrade)
Triggers:
- Investigation shows the impact is smaller than expected.
- Originally expected a migration, actually none is needed.
- Only one consumer, inside your control.

Procedure:
1. Record the reason for the downgrade.
2. Simplify the remaining artifacts to Lean standards.
3. Continue normally.

---

## Relationship with `startup-checklist.md`

Item 5 of `startup-checklist.md` ("Mode selection") should use this tree.
This file provides the precise judgment criteria; the startup checklist gives the end-to-end overview.
