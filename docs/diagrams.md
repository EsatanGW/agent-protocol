# Visual Overview

> **English TL;DR**
> Mermaid diagrams that visualize the methodology's core shapes, for readers who prefer pictures to prose. Six diagrams: (1) **four surfaces + cross-cutting concerns** mesh, (2) **nine-phase pipeline** (Phase 0-8) with decision gates, (3) **SoT pattern taxonomy** showing which pattern covers which kind of asset, (4) **breaking change severity × migration path** decision tree, (5) **rollback mode selection** flow (mode 1 reversible / 2 forward-fix / 3 compensation), (6) **agent handoff** (Planner → Implementer → Reviewer) with the Change Manifest as the carrier artifact. Non-normative — use these to onboard new team members or to anchor workshop discussions; the text files remain authoritative.

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

## How to use these diagrams

- New-hire onboarding → start with diagram 2 (phase flow) and diagram 3 (mode decision).
- Every task start → consult diagram 3 to choose mode; consult diagram 1 to confirm surface coverage.
- During Phase 1 investigation → use diagram 4 as a template for building your own source-of-truth map.
- Team rollout → use diagram 5 to explain adoption cadence to stakeholders.
