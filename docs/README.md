# `docs/` — Methodology Documentation Index

This directory holds the **canonical methodology layer** of the engineering-workflow plugin. The execution layer lives under [`../skills/engineering-workflow/`](../skills/engineering-workflow/); runtime-glue lives under [`../reference-implementations/`](../reference-implementations/) (see its [`INVENTORY.md`](../reference-implementations/INVENTORY.md) for classification).

If you are **using** the plugin, start at the repo root [`README.md`](../README.md) and the operating contract [`AGENTS.md`](../AGENTS.md). This file is for **navigating** the docs once you need to look up a rule.

> **Routing aid.** For the three most-asked decisions (Need a Change Manifest? / Which SoT pattern? / Single vs multi-agent?), [`decision-trees.md`](decision-trees.md) is the one-page hub.

---

## Tier 1 — Start here (onboarding)

If you have never read this docs tree before, read these in order. They cover the methodology in 30–60 minutes.

| File | Purpose |
|------|---------|
| [`onboarding/if-you-only-read-one-page.md`](onboarding/if-you-only-read-one-page.md) | Single-page summary of the methodology. Read this first. |
| [`onboarding/orientation.md`](onboarding/orientation.md) | The shape of the methodology (surfaces, SoT, evidence, phase gates). |
| [`onboarding/quick-start.md`](onboarding/quick-start.md) | First-change walkthrough using a Change Manifest. |
| [`onboarding/when-not-to-use-this.md`](onboarding/when-not-to-use-this.md) | The four execution modes and when each applies. Cites [`mode-decision-tree`](../skills/engineering-workflow/references/mode-decision-tree.md). |
| [`decision-trees.md`](decision-trees.md) | Routing hub for *manifest needed?* / *which SoT pattern?* / *single vs multi-agent?*. |

---

## Tier 2 — Core contract

These files define the methodology's normative claims. Cite them; do not redefine them elsewhere.

| File | Role |
|------|------|
| [`glossary.md`](glossary.md) | **Authoritative term definitions.** When two docs disagree, fix the glossary first. |
| [`principles.md`](principles.md) | First principles the methodology is derived from. |
| [`product-engineering-operating-system.md`](product-engineering-operating-system.md) | The "operating system" framing — system-change perspective + four-layer model. |
| [`system-change-perspective.md`](system-change-perspective.md) | Why "every change is a change to a system, not a unit of code." |
| [`surfaces.md`](surfaces.md) | The four canonical surfaces (Code / Data / Operations / Documentation) + extension surface mechanism. |
| [`source-of-truth-patterns.md`](source-of-truth-patterns.md) | The 10 SoT patterns + sub-pattern 4a, anti-patterns, repair strategies. |
| [`breaking-change-framework.md`](breaking-change-framework.md) | L0–L4 levels + judgment criteria (judge by worst case). |
| [`rollback-asymmetry.md`](rollback-asymmetry.md) | Rollback modes 1 (Reversible) / 2 (Forward-fix) / 3 (Compensation-only). |
| [`cross-cutting-concerns.md`](cross-cutting-concerns.md) | Security / performance / observability / testability / error-handling / build-time risk audit dimensions. |
| [`evidence-…`](automation-contract.md) (see `automation-contract.md` §Evidence tier) | Evidence tiers and what counts as substantiation. |
| [`change-manifest-spec.md`](change-manifest-spec.md) | Field-by-field manifest specification + minimum threshold per phase. |
| [`automation-contract.md`](automation-contract.md) | The contract any validator must implement. |
| [`automation-contract-algorithm.md`](automation-contract-algorithm.md) | The reference algorithm reference implementations target. |
| [`phase-gate-discipline.md`](phase-gate-discipline.md) | Six rules (Phase 0–7 + re-entry) for phase-gate hygiene. |
| [`phase-command-vocabulary.md`](phase-command-vocabulary.md) | Runtime-neutral phase command vocabulary. |
| [`multi-agent-handoff.md`](multi-agent-handoff.md) | Three canonical roles (Planner / Implementer / Reviewer), tool-permission matrix, anti-collusion rule, role-composition patterns. |
| [`ai-operating-contract.md`](ai-operating-contract.md) | AI-specific failure modes (plausibly-complete narrative, perfect-confidence hallucination) + verification protocol. |
| [`agent-persona-discipline.md`](agent-persona-discipline.md) | Canonical SoT for `AGENTS.md §9`. The *domain-expert persona* (system architect / motion designer / UX designer / deck designer / …) every AI invocation reasons from — selected by the medium of the output, orthogonal to the canonical role, never a permission escalation. |
| [`output-craft-discipline.md`](output-craft-discipline.md) | Canonical SoT for `AGENTS.md §10`. Three rules every AI output must clear: every element earns its place; output adapts to its medium (AI default styling rejected); summaries are caveats + next steps, not recap. |
| [`ai-project-memory.md`](ai-project-memory.md) | How AI agents should treat persistent project memory. |
| [`runtime-hook-contract.md`](runtime-hook-contract.md) | The four hook categories (phase-gate / evidence / drift / completion-audit) + exit-code contract. Includes the *risky-action interception list* (Category-A extension) and the *back-pressure pattern* (Category-D extension). |
| [`runtime-hooks-in-practice.md`](runtime-hooks-in-practice.md) | Practical hook patterns and their failure modes. |
| [`repo-as-context-discipline.md`](repo-as-context-discipline.md) | Repo as system of record. *Anything an agent cannot reach in-context effectively does not exist.* External knowledge (chat / docs / verbal decisions) must be transcoded into repo-resident artifacts before it can govern agent behaviour. |
| [`mechanical-enforcement-discipline.md`](mechanical-enforcement-discipline.md) | The three axes of mechanical enforcement (architecture invariants / taste invariants / documentation freshness) and which capability contract each axis maps to. |
| [`tool-design-principles.md`](tool-design-principles.md) | Five tool-design principles: less is more, examples beat schemas, error codes are stable, composability through narrowness, context-budget honesty. |
| [`change-decomposition.md`](change-decomposition.md) | When to split one change into many; cross-change knowledge cost. |
| [`cross-change-knowledge.md`](cross-change-knowledge.md) | The cost of context switching between concurrent changes; bundling rules. |
| [`concurrent-changes.md`](concurrent-changes.md) | Coordinating multiple in-flight changes that touch overlapping surfaces. |

---

## Tier 3 — Disciplines (situational rules)

These activate when the change touches a specific dimension. Skip the ones that don't apply.

| File | Activates when |
|------|----------------|
| [`situational-disciplines.md`](situational-disciplines.md) | The change touches one or more of the user / implementation / operational surfaces. Three sections (`#user-surface`, `#implementation-surface`, `#operational-surface`) replace the three sibling discipline files merged in 1.20.0. |
| [`team-org-disciplines.md`](team-org-disciplines.md) | The change crosses team / org boundaries; handoff is needed. |
| [`security-supply-chain-disciplines.md`](security-supply-chain-disciplines.md) | Auth / PII / secrets / dependency provenance is in scope. |
| [`playtest-discipline.md`](playtest-discipline.md) | Game / interactive / experience-driven changes need playtest evidence. |
| [`post-delivery-observation.md`](post-delivery-observation.md) | Phase 8 observation: production findings, metrics, continuous-evidence. |
| [`anti-entropy-discipline.md`](anti-entropy-discipline.md) | Time-driven garbage-collection sweeps for accumulated drift (stale CCKNs, expired deprecations, doc-reference rot). Complements the edit-boundary mechanical enforcement and the delivery-event Phase 8 observation. |
| [`adoption-strategy.md`](adoption-strategy.md) | Rolling out the methodology to a team that isn't using it yet. |
| [`adoption-anti-metrics.md`](adoption-anti-metrics.md) | How to recognize fake adoption (compliance theatre). |
| [`ci-cd-integration-hooks.md`](ci-cd-integration-hooks.md) | Wiring methodology gates into CI/CD pipelines. |
| [`strategic-artifacts.md`](strategic-artifacts.md) | Mission, roadmap, and other strategic-tier artifacts. |
| [`operational-cheat-sheet.md`](operational-cheat-sheet.md) | One-page operational reminders. |
| [`diagrams.md`](diagrams.md) | Methodology diagrams (concept maps, flow diagrams). |

---

## Tier 4 — References (catalogues you read on demand)

| Subdirectory / file | Purpose |
|---------------------|---------|
| [`bridges/`](bridges/) | Stack bridges (Android / iOS / Flutter / Ktor / React-Next.js / Unity) — how to map this methodology onto a specific stack. Each bridge has a `.md` description + a `.yaml` surface-map. |
| [`bridges-local-deviations-howto.md`](bridges-local-deviations-howto.md) + [`bridges-local-deviations-template.md`](bridges-local-deviations-template.md) | When and how to deviate from a bridge for a local context. |
| [`stack-bridge-template.md`](stack-bridge-template.md) | Template for authoring a new bridge. |
| [`examples/`](examples/) | Worked examples per scenario type (bugfix / refactor / migration / mobile-offline / ML / liveops / etc.). Read the example closest to your change. |
| [`evidence-quality-per-type.md`](evidence-quality-per-type.md) | Per-type artefact-shape and rejection-signal appendix to [`change-manifest-spec.md`](change-manifest-spec.md). Covers all 18 `evidence_plan[*].type` values; non-normative companion. |
| [`codex-install.md`](codex-install.md) | Codex-specific installation notes. |

---

## How to extend this index

When you add a new `*.md` to `docs/`:

1. Pick a tier:
   - Tier 1 if a new contributor must read it on day 1.
   - Tier 2 if it defines a normative claim other docs cite.
   - Tier 3 if it activates only for certain change types.
   - Tier 4 if it is a catalogue, template, or worked example.
2. Add a row in this file with the same one-line description style as its tier.
3. Avoid creating a new tier; the four are deliberately stable.

When you rename a `*.md` in `docs/`, the rename is a breaking-change event for cross-references — see [`change-manifest-spec.md`](change-manifest-spec.md) and the file-naming rule in [`../CONTRIBUTING.md`](../CONTRIBUTING.md). Update this index in the same change.

If a doc is no longer relevant, the right move is usually to **shrink it down to a redirect stub pointing at its replacement**, rather than deleting it — external bookmarks and cross-references in older versions of the methodology may still resolve to the old name.
