# Visual Overview

> **English TL;DR**
> Mermaid diagrams that visualize the methodology's core shapes, for readers who prefer pictures to prose. Six diagrams: (1) **four surfaces + cross-cutting concerns** mesh, (2) **nine-phase pipeline** (Phase 0-8) with Discovery Loop + Fix-Retest Loop, (3) **Lean / Full mode decision tree** anchored on surface count, consumer count, and forced triggers, (4) **source-of-truth relationships** — how contracts, DBs, and configs fan out to their consumers, (5) **team adoption stages** (mindset → process → institutionalization), (6) **all-pieces-together stack map** connecting the contract layer, execution layer, carrier artifacts, and mechanical guardrails (runtime hooks + CI hooks). Non-normative — use these to onboard new team members or to anchor workshop discussions; the text files remain authoritative.

This document presents the methodology's core structure as Mermaid diagrams to lower the reading barrier.

---

## 1. Four surfaces and their relationship to cross-cutting concerns

```mermaid
graph TB
    subgraph "Core surfaces"
        U["User surface<br/>UI / route / i18n / a11y"]
        S["System-interface surface<br/>API / event / job / contract"]
        I["Information surface<br/>schema / enum / config / flag"]
        O["Operational surface<br/>log / audit / rollout / docs"]
    end

    subgraph "Cross-cutting"
        SEC["Security"]
        PERF["Performance"]
        OBS["Observability"]
        TEST["Testability"]
    end

    subgraph "Composable extensions"
        EXT["Asset surface / experience surface / performance-budget surface / ..."]
    end

    SEC -.-> U
    SEC -.-> S
    SEC -.-> I
    SEC -.-> O
    PERF -.-> U
    PERF -.-> S
    PERF -.-> I
    PERF -.-> O
    OBS -.-> U
    OBS -.-> S
    OBS -.-> I
    OBS -.-> O
    TEST -.-> U
    TEST -.-> S
    TEST -.-> I
    TEST -.-> O
    EXT -.-> U
    EXT -.-> O
```

---

## 2. Phase 0→8 full flow (including the Discovery Loop and Fix-Retest Loop)

```mermaid
graph TD
    P0["Phase 0: Clarify<br/>Clarify requirement + surface + mode"]
    P1["Phase 1: Investigate<br/>Source of Truth + Consumer Map"]
    P2["Phase 2: Plan<br/>Change plan + dependency order"]
    P3["Phase 3: Test Plan<br/>Verification methods + evidence design"]
    P4["Phase 4: Implement<br/>Implementation + verification"]
    P5["Phase 5: Review<br/>Correctness / Security / UX / Ops"]
    P6["Phase 6: Sign-off<br/>Per-criterion acceptance + evidence"]
    P7["Phase 7: Deliver<br/>Completion report + handoff"]
    P8["Phase 8: Observe<br/>T+24h / T+72h / T+7d"]

    P0 --> P1 --> P2 --> P3 --> P4 --> P5 --> P6 --> P7 --> P8

    P4 -- "New surface/consumer discovered<br/>(Discovery Loop)" --> DL{"Impact size?"}
    P5 -- "Plan gap discovered<br/>(Discovery Loop)" --> DL
    DL -- "Small: same-surface detail" --> P4
    DL -- "Large: re-investigate" --> P1
    DL -- "Large: update plan" --> P2
    DL -- "Large: update test plan" --> P3

    P4 -- "Test failed<br/>(Fix-Retest Loop)" --> FRL["Fix → re-run verification"]
    FRL --> P4

    P8 -- "Methodology feedback" --> FEEDBACK["Update checklist / surface definitions / phase requirements"]
```

---

## 3. Lean / Full mode decision tree

```mermaid
graph TD
    START["Change arrives"]
    FORCE_FULL{"Forced Full?<br/>migration / public API /<br/>payment / auth / PII / cross-team"}
    SURFACES{"How many surfaces touched?"}
    PUBLIC{"Public<br/>behavior change?"}
    CONSUMERS{"Consumer count?"}
    FORCE_LEAN{"Forced Lean?<br/>copy / styling / patch bump /<br/>clearly scoped single bug"}
    SKIP{"Skip the workflow?<br/>pure research / Q&A / exploration"}

    FULL["Full Mode"]
    LEAN["Lean Mode"]
    NONE["Not triggered"]

    START --> SKIP
    SKIP -- "yes" --> NONE
    SKIP -- "no" --> FORCE_LEAN
    FORCE_LEAN -- "yes" --> LEAN
    FORCE_LEAN -- "no" --> FORCE_FULL
    FORCE_FULL -- "yes" --> FULL
    FORCE_FULL -- "no" --> SURFACES
    SURFACES -- "1" --> LEAN
    SURFACES -- "2" --> PUBLIC
    SURFACES -- "3+" --> FULL
    PUBLIC -- "yes" --> FULL
    PUBLIC -- "no" --> CONSUMERS
    CONSUMERS -- "0-1" --> LEAN
    CONSUMERS -- "2+" --> FULL
    CONSUMERS -- "unsure" --> FULL
```

---

## 4. Source of Truth and consumer relationships

```mermaid
graph LR
    subgraph "Source of Truth"
        DB["DB Schema"]
        CONFIG["Config Service"]
        SPEC["API Spec"]
    end

    subgraph "Consumers"
        API["API Response"]
        CACHE["Redis Cache"]
        UI["Frontend UI"]
        SEARCH["Search Index"]
        DOCS["API Docs"]
        ANALYTICS["Analytics"]
    end

    DB --> API
    DB --> CACHE
    API --> UI
    CONFIG --> API
    CONFIG --> UI
    SPEC --> API
    SPEC --> DOCS
    DB --> SEARCH
    API --> ANALYTICS

    style DB fill:#e1f5fe
    style CONFIG fill:#e1f5fe
    style SPEC fill:#e1f5fe
```

---

## 5. Team adoption — three stages

```mermaid
graph LR
    S1["Stage 1<br/>Mindset seeding<br/>1-2 weeks"]
    S2["Stage 2<br/>Process embedding<br/>2-4 weeks"]
    S3["Stage 3<br/>Institutionalization<br/>4-8 weeks"]

    S1 -- "PRs mark surfaces<br/>source of truth spoken aloud" --> S2
    S2 -- "Lean mode trial<br/>gaps caught" --> S3
    S3 -- "Bridge docs<br/>completion reports<br/>metric feedback" --> DONE["Continuous improvement"]
```

---

## 6. All pieces together — how the layers connect

The methodology has four layers: a **normative layer** (what you must do), an **execution layer** (how you do it), a **carrier artifact layer** (what you produce), and a **mechanical-enforcement layer** (what catches you when you skip a step). This diagram shows how they plug together so a reader can see the full stack on one page.

```mermaid
graph TB
    subgraph NORM["Normative layer — contracts"]
        AGENTS["AGENTS.md<br/>runtime operating contract"]
        SCHEMA["schemas/change-manifest.schema.yaml<br/>artifact contract"]
        HOOKSPEC["docs/runtime-hook-contract.md<br/>+ docs/ci-cd-integration-hooks.md<br/>hook category + exit-code contract"]
    end

    subgraph EXEC["Execution layer — skill + phases"]
        SKILL["skills/engineering-workflow/SKILL.md<br/>Lean / Full mode selection"]
        PHASES["Phase 0 → 8<br/>gate minimums + evidence rules"]
        SKILL --> PHASES
    end

    subgraph CARRIER["Carrier artifacts — produced per change"]
        MANIFEST["change-manifest.yaml<br/>structured state per phase"]
        EVIDENCE["evidence/*<br/>logs / tests / screenshots"]
        ROADMAP["ROADMAP.md<br/>cross-session tracker"]
    end

    subgraph GUARDS["Mechanical enforcement — automated checks"]
        RUNTIME["Runtime hooks<br/>PreToolUse / PostToolUse / Stop<br/>fires inside the agent loop"]
        CI["CI hooks<br/>GitHub Actions / GitLab / ...<br/>fires at PR + pre-merge"]
    end

    AGENTS --> SKILL
    SCHEMA --> MANIFEST
    HOOKSPEC --> RUNTIME
    HOOKSPEC --> CI

    PHASES -->|produce + update| MANIFEST
    PHASES -->|produce + cite| EVIDENCE
    PHASES -->|tracked in| ROADMAP

    MANIFEST -->|read by| RUNTIME
    EVIDENCE -->|resolved by| RUNTIME
    MANIFEST -->|read by| CI
    EVIDENCE -->|resolved by| CI

    RUNTIME -. "exit 1 blocks<br/>exit 2 warns" .-> PHASES
    CI -. "fails pipeline" .-> MANIFEST
```

**How to read this diagram.**

- The **normative layer** is spec-only; nothing there produces artifacts. It answers "what must be true."
- The **execution layer** operationalizes the contract through mode selection and phase gates. It answers "in what order do I work."
- The **carrier layer** is where all state lives between phases and between sessions. The Change Manifest is the single connecting artifact — every phase reads and updates it; every hook reads it.
- The **enforcement layer** has two tiers: runtime hooks catch failures *while the agent can still correct* (cheap), CI hooks catch failures *before they ship* (authoritative). Both share the same `0 = pass / 1 = block / 2 = warn` exit-code contract and the same manifest-as-input shape.

The dashed arrows back into the execution and carrier layers show the **feedback direction**: when a guard fires, the fix happens inside the phase loop, not in the guard. Hooks do not edit manifests — they refuse to let incomplete ones proceed.

See also: [`AGENTS.md`](../AGENTS.md) §7 (multi-agent), [`docs/runtime-hook-contract.md`](./runtime-hook-contract.md), [`docs/ci-cd-integration-hooks.md`](./ci-cd-integration-hooks.md), [`schemas/change-manifest.schema.yaml`](../schemas/change-manifest.schema.yaml), [`examples/starter-repo/`](../examples/starter-repo/) for a working end-to-end instantiation.

---

## How to use these diagrams

- New-hire onboarding → start with diagram 6 (stack map) for the big picture, then diagram 2 (phase flow) and diagram 3 (mode decision).
- Every task start → consult diagram 3 to choose mode; consult diagram 1 to confirm surface coverage.
- During Phase 1 investigation → use diagram 4 as a template for building your own source-of-truth map.
- Team rollout → use diagram 5 to explain adoption cadence to stakeholders.
- Explaining the plugin to a skeptical reviewer or stakeholder → diagram 6 shows, in one frame, where every mechanism lives and why each layer is necessary.
