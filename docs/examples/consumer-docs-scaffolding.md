# Consumer `docs/` Scaffolding — Example

> **Status.** Non-normative example. This file is **not** the methodology's own `docs/` structure (the methodology's structure is flat, by design — methodology content has different shape from product content). It is a worked layout for a *consumer project* — an application or service that adopts agent-protocol — to organise its repo-resident knowledge so an agent can navigate from a small entry point to deeper sources of truth without loading the whole tree.

The scaffolding draws on the structure pattern named by the harness-engineering article (OpenAI, 2026-02). Names are illustrative; teams should adapt to their own taxonomy.

---

## Why this is a worked example, not a normative rule

The methodology repository has a flat `docs/` because methodology content is *cross-cutting by definition* — every doc applies to every change. A consumer project's content is *change-scoped* — each design doc, exec plan, or generated artefact applies to a specific feature, sprint, or domain. The two shapes are different; collapsing the consumer pattern into the methodology repo would dilute both.

The scaffolding is therefore a **starting layout** — a team that adopts agent-protocol can copy the structure, adapt the names, and extend per their domain. Teams with existing `docs/` layouts should map their existing structure onto this scaffold rather than rename everything; mapping is enough, the names do not have to match.

---

## The reference layout

```
<repo-root>/
├── AGENTS.md                              ~100 lines, table of contents
├── ARCHITECTURE.md                        top-level architecture map
├── docs/
│   ├── design-docs/
│   │   ├── index.md                       catalogue of every design doc
│   │   ├── core-beliefs.md                team's agent-first operating principles
│   │   └── <one file per design decision>
│   ├── exec-plans/
│   │   ├── active/                        in-flight Change Manifests + plans
│   │   └── completed/                     archived plans (per phase-gate-discipline.md Rule 5)
│   ├── generated/
│   │   ├── db-schema.md                   regenerated from canonical schema
│   │   └── <other artefacts derived from machine SoT>
│   ├── product-specs/
│   │   ├── index.md
│   │   └── <one file per user-facing feature>
│   ├── references/
│   │   ├── design-system-reference.md
│   │   └── <library / framework reference distillations>
│   ├── DESIGN.md                          design decisions / trade-offs log
│   ├── FRONTEND.md                        UI / interaction specifics
│   ├── PLANS.md                           initiative-level plans
│   ├── PRODUCT_SENSE.md                   product strategy / north star
│   ├── QUALITY_SCORE.md                   per-domain grading (see quality-score-template.md)
│   ├── RELIABILITY.md
│   └── SECURITY.md
└── ...
```

---

## What each path is for

### `AGENTS.md` (root)

A small, stable entry point — typically under 200 lines. Functions as a **table of contents**, not an encyclopedia. Lists the repo's normative claims by name and points at the deeper sources of truth elsewhere. New agents read this first; they descend into `docs/*.md` only when the task requires it.

The methodology's own `AGENTS.md` is the canonical model — see [`../../AGENTS.md`](../../AGENTS.md) for the shape.

### `ARCHITECTURE.md` (root)

A top-level map of domains and their cross-cutting boundaries. Names which surfaces (per `docs/surfaces.md`) the application exposes. Lists the major business domains and their dependency directions. Functions as the first read for a new contributor (human or agent) who needs to know "what does this system do, at the highest level."

Maps onto agent-protocol's surface model: an architecture chapter per surface, with per-domain entries underneath.

### `docs/design-docs/`

Where design decisions live as first-class artefacts. Each decision is one file (an ADR or design doc) with a stable filename so agents can cross-reference. The `index.md` enumerates every decision so agents can grep for "did we decide X" without reading the whole tree.

The `core-beliefs.md` file is the team's high-level operating principles — agent-first defaults, what trade-offs are accepted as policy. Agent-protocol's [`docs/principles.md`](../principles.md) is the methodology-side analogue.

### `docs/exec-plans/active/` and `docs/exec-plans/completed/`

Where Change Manifests and execution plans live, separated by lifecycle:

- **`active/`** — in-flight manifests. An agent picking up a stalled change reads this directory first. Per `phase-gate-discipline.md` Rule 5, phase records are written at boundaries; `active/` is where those records accumulate during a change.
- **`completed/`** — archived after Phase 7 / Phase 8 closes. The archive is searchable; an agent investigating a regression can find the original change's manifest, evidence, and decision log.

### `docs/generated/`

Artefacts derived from a canonical machine SoT (database schemas, OpenAPI definitions, generated TypeScript types in markdown form for agent reading). The directory's contents are **regenerated**, not hand-edited; a generator script (Phase 4 / Phase 6 hook) keeps the markdown current with the canonical SoT.

Maps onto agent-protocol's `docs/source-of-truth-patterns.md` Pattern 4a (dual-representation): the canonical machine form is the SoT; the generated markdown is for agent legibility.

### `docs/product-specs/`

User-facing feature specifications, indexed by feature name. Each spec describes the user surface, the intended behaviour, and the acceptance criteria. An agent picking up a feature change reads the relevant spec before drafting the manifest.

### `docs/references/`

Distilled references for libraries, frameworks, design systems, or external APIs the project depends on. Keeps the agent's context small — instead of fetching upstream docs at session start, the team distils the relevant subset into a markdown that the agent can load quickly.

The `*-llms.txt` naming convention named in the harness-engineering article is one way to mark these files; teams may use any naming convention they prefer.

### `docs/DESIGN.md`, `FRONTEND.md`, `PLANS.md`, `PRODUCT_SENSE.md`, `RELIABILITY.md`, `SECURITY.md`

Domain-level policy documents. Each one is a small (one-page) file naming the team's policy on its dimension and pointing into deeper sources where applicable. They are the second-level entry points after `AGENTS.md`; an agent working on a security-sensitive change reads `SECURITY.md` early.

### `docs/QUALITY_SCORE.md`

Per-domain grading of code quality / coverage / test depth / observability. Updated by an `anti-entropy-discipline.md`-shaped sweep (typically weekly). The file is non-normative — it tracks gaps over time, surfacing them for prioritisation. See [`quality-score-template.md`](quality-score-template.md) for a fillable template.

---

## Mapping to agent-protocol concepts

The scaffolding's slots resolve onto agent-protocol's existing artefacts:

| Scaffolding slot | Agent-protocol concept |
|---|---|
| `AGENTS.md` (root) | Operating contract entry — same role as the methodology's [`AGENTS.md`](../../AGENTS.md) |
| `ARCHITECTURE.md` | Domain map across `docs/surfaces.md` surfaces |
| `docs/design-docs/index.md` | Index over the team's design decisions; analogue of [`docs/README.md`](../README.md) for the methodology |
| `docs/design-docs/core-beliefs.md` | Team's analogue of [`docs/principles.md`](../principles.md) |
| `docs/exec-plans/active/` | In-flight Change Manifests (per [`change-manifest-spec.md`](../change-manifest-spec.md)) |
| `docs/exec-plans/completed/` | Archive of closed manifests + ROADMAP closures |
| `docs/generated/` | SoT Pattern 4a generated artefacts (per [`source-of-truth-patterns.md`](../source-of-truth-patterns.md)) |
| `docs/product-specs/` | User-surface specifications (per [`surfaces.md`](../surfaces.md)) |
| `docs/references/` | External-knowledge distillations (per [`repo-as-context-discipline.md`](../repo-as-context-discipline.md)) |
| `docs/QUALITY_SCORE.md` | Per-domain quality grading (per [`anti-entropy-discipline.md §Quality score`](../anti-entropy-discipline.md)) |

---

## What does NOT belong in this scaffold

- **Vendor-specific tool layouts.** The scaffolding names categories (`design-docs/`, `references/`), not vendors. A team using a specific CMS or design-system tool maps that tool's output into one of the scaffold's directories rather than naming the tool in the directory.
- **Cross-cutting methodology content.** Methodology rules (surfaces, SoT patterns, breaking-change levels) live in agent-protocol's `docs/`, not in the consumer's. The consumer's `docs/` are change-scoped and product-specific.
- **Living chat threads.** Per `repo-as-context-discipline.md`, knowledge in chat / Slack / Google Docs is not in-context. The scaffold's role is to provide a place to **transcode** that knowledge into repo-resident form — not to mirror chat verbatim.
- **The whole production runbook.** Operations documentation belongs in the operational surface; the scaffold's `RELIABILITY.md` is a one-page policy pointer, not the runbook itself.

---

## Adoption procedure

1. **Map first, rename second.** The scaffold's slots map onto most existing layouts. Identify which directory in your existing repo plays each slot's role; rename only when the existing name is structurally misleading.
2. **Add the entry points first.** `AGENTS.md`, `ARCHITECTURE.md`, and `docs/design-docs/index.md` are the highest-leverage additions; an agent that has these three is already mostly oriented.
3. **Migrate active changes incrementally.** Existing in-flight changes do not need to be relocated mid-flight. New manifests open in `docs/exec-plans/active/`; closed ones move to `completed/`.
4. **Quality-score sweep at week 4.** After four weeks of operating with the scaffold, run a `QUALITY_SCORE.md` sweep — the gaps it surfaces reveal which slots are underused or misnamed.

---

## Cross-references

- [`../repo-as-context-discipline.md`](../repo-as-context-discipline.md) — the discipline this scaffold operationalises.
- [`../change-manifest-spec.md`](../change-manifest-spec.md) — the manifest format that lives in `docs/exec-plans/`.
- [`../source-of-truth-patterns.md`](../source-of-truth-patterns.md) — Pattern 4a is the basis for `docs/generated/`.
- [`../anti-entropy-discipline.md`](../anti-entropy-discipline.md) — the sweeps that maintain `QUALITY_SCORE.md`.
- [`./quality-score-template.md`](./quality-score-template.md) — fillable template for `docs/QUALITY_SCORE.md`.
- [`../surfaces.md`](../surfaces.md) — the surface model `ARCHITECTURE.md` maps onto.
