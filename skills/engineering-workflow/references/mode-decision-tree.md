# Execution-Mode Decision Tree

Use this tree at the start of Phase 0 (or before any code is touched) to pick a mode. The four canonical modes are **Zero-ceremony, Three-line delivery, Lean, Full** — definitions in `docs/glossary.md §Execution mode`. The decision is not permanent. **Default bias is the lightest mode the scenario tables below allow; upgrade on the spot when in-flight discovery reveals a forced-trigger that was not visible at mode-pick time (see `§Mode upgrade / downgrade` below and `discovery-loop.md`); do not force-fit a lighter mode to hide scope that has already grown — silent scope-shrink is prohibited per `AGENTS.md §6` and `docs/phase-gate-discipline.md §Rule 1`.**

This file is the **execution-layer source of truth** for the Scenarios-that-force-Full list. Other decision aids (`docs/onboarding/when-not-to-use-this.md`, `SKILL.md §Decision table`, `startup-checklist.md §5`) must reference this file rather than maintain a parallel list.

> **Quick decision aid.** For a one-page hub that combines the mode call with the *"do I need a Change Manifest?"* and *"single vs multi-agent role split?"* decisions, see [`docs/decision-trees.md §Tree A`](../../../docs/decision-trees.md#tree-a--need-a-change-manifest). The binding force-Full table stays in this file.

---

## Fast call (30 seconds)

```
Does this change modify any file at all?
├── No (pure Q&A / research / environment check / reading) → Zero-ceremony
└── Yes → continue

Is the diff < 5 lines, with no public behavior impact, not crossing any surface?
├── Yes (typo, trivial CSS, throwaway one-off) → Zero-ceremony
└── No → continue

Does the change involve any forced-Full trigger (see table below)?
├── Yes → Full
└── No → continue

How many surfaces does it touch?
├── 1 surface → continue (Lean or Three-line delivery)
├── 2 surfaces
│   ├── Public behavior changes? → Full
│   └── No public behavior change → Lean
└── 3+ surfaces → Full

How many consumers are affected?
├── 0–1 known consumers → continue
├── 2+ consumers → Full
└── Consumer count uncertain → Full (investigate first; may downgrade to Lean)

One surface, ≤ 1 consumer, verifiable in ≤ 5 minutes?
├── Yes, and the diff is mechanical (config tweak, known-safe dep patch, log add,
│   i18n value change, docs-only edit) → Three-line delivery
└── Otherwise → Lean
```

---

## Scenarios that force Full

The following **must** use Full mode regardless of size. This is the **canonical list**; other documents should cite this section rather than duplicate it.

| Scenario | Reason |
|----------|--------|
| DB / persistent-storage schema migration | Irreversible or expensive rollback — needs full plan + rollback strategy. |
| Public API breaking change (contract / endpoint / payload / status code) | Consumers may be outside your control. |
| Enum / status / discriminated-union change that is consumer-visible | Exhaustiveness on the consumer side silently breaks. |
| Money / payments | Cost of error is extremely high. |
| Auth / authorization / PII / secret handling | Security + compliance requirement. |
| Cross-team delivery requiring handoff | The handoff narrative must be complete. |
| Long-lived feature-flag coexistence | Needs explicit flag lifecycle + cleanup plan. |
| Staged rollout (canary / phased %) | Rollout sequencing is itself a contract. |
| Canonical methodology content edit (L1+) | When this repo's own SoT files (`AGENTS.md`, `docs/*.md`, `schemas/*`, or `skills/**` files listed as canonical per `AGENTS.md §File role map`) are edited at breaking-change level ≥ L1 — changing an existing normative claim, adding a new normative rule to SoT, or renaming a cross-cutting term — force Full. Bridges / consumers cite these files by name; a silent normative change drifts every consumer. L0-additive edits (new non-normative reference file; pointer additions; CHANGELOG-only edits) stay Lean-eligible. |

## Scenarios that force Lean

The following **should not** use Full mode (avoid over-engineering):

| Scenario | Reason |
|----------|--------|
| Single bug fix with a clear root cause, touching 1 surface | Scope is known. |
| Small-scope refactor in a well-tested area | Tests are the verification; no new contract. |
| New log / metric without behavior change | Pure operational-surface enhancement. |
| Retirement of a project-local discipline backed by a recorded `Discipline-provenance sweep` finding (per [`anti-entropy-discipline.md`](../../../docs/anti-entropy-discipline.md) Rule 3) | The sweep finding is the decay evidence; retirement is single-surface, single-consumer, ≤5-min verification (delete the discipline + bridge-pointer cleanup). Adding a new discipline still routes through the canonical-methodology-content row above (L1+ → Full); only sweep-backed *retirement* drops to Lean. This is the asymmetric-cost lever that lets the methodology shed weight over time rather than only accumulate it. Self-applying-methodology check: the retirement change still goes through Phases 0–7; the Lean-mode collapse is on artifact set, not on phase rigour. |

## Scenarios that force Three-line delivery (not Lean, not Full)

The following sit **below** Lean and do not earn the Lean artifact set:

| Scenario | Reason |
|----------|--------|
| i18n key **value** change (same semantics, same key) | No consumer contract change. |
| New log at an existing call site | Downstream dashboards unaffected unless structure changes. |
| Dependency **patch** bump with no API change | Binary-compat shift. |
| README / docstring edit that does not change behavior | Docs as consumer, but narrow scope. |
| Known-safe config tweak (validated key with a short list of allowed values) | Behavior envelope is already bounded. |

## Scenarios that force Zero-ceremony

The following **do not enter any mode**:

| Scenario | Reason |
|----------|--------|
| Pure Q&A / research / reading | No files modified. |
| Typo / single-string copy fix | Diff < 5 lines, no surface crossing. |
| One-off script used once and discarded | No long-lived consumer. |
| Environment check (version, port, log, service state) | Read-only. |
| Explicitly-throwaway experiment (will not land on main) | Tagged throwaway. |

---

## Mode upgrade / downgrade

### Upgrade (Zero-ceremony → Three-line → Lean → Full)

Triggers:
- A new affected surface is discovered during implementation.
- More consumers than expected.
- A schema migration turns out to be required.
- A forced-Full trigger surfaces mid-change (e.g. the fix now touches auth).
- The reviewer judges the risk was under-estimated.

Procedure:
1. Pause implementation.
2. Complete the artifacts required by the **target** mode, re-entering at the target mode's corresponding step / phase (see `glossary.md §Lean → Full step / phase correspondence`).
3. Record the upgrade reason in the target mode's primary artifact (Full: `implementation_notes` entry with `type: plan_delta`; Lean: risk note).
4. Continue from the re-entry point.

### Downgrade (Full → Lean, Lean → Three-line, Three-line → Zero-ceremony)

Triggers:
- Investigation shows the impact is smaller than expected.
- Originally expected a migration, actually none is needed.
- Only one consumer, inside your control.

Procedure:
1. Record the reason for the downgrade in the phase log or delivery note.
2. Simplify the remaining artifacts to the target mode's minimum.
3. Continue normally.

---

## Relationship with other decision aids

| File | Role | How it references this file |
|---|---|---|
| `docs/onboarding/when-not-to-use-this.md` | Gentle onboarding walkthrough for "should I use this methodology at all?" | Uses the same forced-Full list via reference; adds narrative framing and over-use / under-use signals. |
| `SKILL.md §Mode selection` | In-skill execution cue when the skill triggers | Short decision table; points here for full criteria. |
| `startup-checklist.md §5` | 60-second opener item | One-line rule; points here for full criteria. |
| `docs/phase-gate-discipline.md §Ceremony scaling` | How each mode affects phase-gate rules | Uses the mode names defined in `glossary.md §Execution mode`. |

When these files disagree with this file, this file wins for **mode selection logic**; `glossary.md` wins for **mode definitions** themselves.
