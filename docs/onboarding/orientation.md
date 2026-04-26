# Orientation

A single-page orientation to the methodology. Read this before diving into
any other document in `docs/`. It gives enough structure that the rest of
the repository reads as reinforcement rather than first exposure.

> **60-second lookup.** If you just need the per-role action list and "when you see X, go to Y" navigation (not the reasoning), jump straight to [`docs/operational-cheat-sheet.md`](../operational-cheat-sheet.md). Come back here for the principles.

---

## The one-paragraph version

**This plugin is a methodology for managing change, not for writing code.** Before any non-trivial engineering change, identify (1) the *source of truth* for the capability being changed, (2) the *surfaces* the change will be perceived through (user / system-interface / information / operational), (3) who the *consumers* of that truth are, and (4) what *evidence* will prove the change is actually safely in place. Pick the lightest workflow (Lean / Full / Zero-ceremony) that still produces that evidence, and never claim completion without it. When multiple agents cooperate, they exchange state through a structured **Change Manifest** (`schemas/change-manifest.schema.yaml`). When the stack matters, consult a **stack bridge** in `docs/bridges/`.

> **Want the stack map first?** [`docs/diagrams.md` §6 — All pieces together](../diagrams.md#6-all-pieces-together--how-the-layers-connect) shows on one page how the contract layer, execution layer, carrier artifacts, and mechanical guardrails (runtime hooks + CI hooks) fit together. Useful as a mental frame before reading the per-document detail below.

---

## The five rules that matter most

1. **Manage change, not code.** Code is one of many traces a change leaves. If a change is "done" but has no evidence, no surface coverage, and no handoff narrative, the system is not actually in the state you claim.
2. **Find the source of truth before patching consumers.** Most bugs are "a consumer's assumption about SoT became invalid." Patching the consumer is treating the symptom.
3. **Analyse by surface, not by stack layer.** Frontend/backend/DB slicing hides cross-cutting drift. The four canonical surfaces (user / system-interface / information / operational) force you to see the full impact of a change.
4. **Rollback is a spectrum, not a button.** Stateless server with blue/green is seconds. Mobile binary is days with long tails. Already-sent push / already-paid money is mode-3 compensation. Plan accordingly.
5. **Verification and evidence are designed, not retrofitted.** The time to decide how you will prove a change works is before you implement it, not after.

---

## If you only have 3 minutes

Answer these in order. Do **not** answer the shortcuts — the shortcuts are how the wrong question becomes the wrong answer.

1. **Define the change in one sentence.** "What capability are we actually changing?"
   - Do not answer first: "Is this frontend or backend?" / "Who owns this area?"
2. **Tag the four surfaces.** User (who will see a visible change?) / system-interface (which API / event / job changes?) / information (which field / enum / schema / config changes?) / operational (log / changelog / rollout / rollback?).
3. **Find the source of truth.** Where does the authoritative source actually live? Which consumers read from it?
4. **Decide the minimum verification.** How will I know the change stands? What evidence will I leave behind?
5. **Pick Lean vs Full.** Small, low-risk → Lean. Multi-surface / public behavior impact / needs handoff → Full.

For the 60-second version inside your next task, jump to [The first 60 seconds of any task](#the-first-60-seconds-of-any-task) below.

## If you only read one page

This is that page. The single most important takeaway from the whole repository is the **change-centric perspective** — tech stack does not matter first; "how does this capability pass through the whole system, and how do we prove it was changed safely?" does.

The five rules directly above are the entire load-bearing summary. If the rest of this page disappeared, those five bullets would still carry the methodology.

The two historical onboarding files (`quick-start.md` and `if-you-only-read-one-page.md`) have been merged into this page as the two sections above; those files are now redirect stubs.

---

## Navigation map

**You must read:**
- `AGENTS.md` — universal operating contract
- `docs/surfaces.md` — four-surface model
- `docs/glossary.md` — term definitions
- `docs/ai-operating-contract.md` — AI co-author behavior

**You should read when you hit that situation:**
- `docs/source-of-truth-patterns.md` — 10 SoT patterns
- `docs/breaking-change-framework.md` — L0–L4 severity + consumer classification
- `docs/rollback-asymmetry.md` — rollback modes 1/2/3
- `docs/security-supply-chain-disciplines.md` — threat modeling, supply chain (worked example: `skills/engineering-workflow/templates/manifests/change-manifest.example-security-sensitive.yaml`)
- `docs/change-decomposition.md` — splitting and merging changes
- `docs/team-org-disciplines.md` — consumer registry, contract catalog, deprecation queue
- `docs/multi-agent-handoff.md` — agent roles, manifest progression, **Enforcement across runtimes** (which runtimes enforce mechanically vs prose-only)
- `docs/ai-project-memory.md` — cross-session memory discipline
- `docs/automation-contract.md` — what a validator must guarantee
- `docs/runtime-hook-contract.md` — normative contract for agent-runtime event-driven hooks (categories, event schema, latency budgets); pair with [`docs/runtime-hooks-in-practice.md`](../runtime-hooks-in-practice.md) for install + adoption steps
- `docs/adoption-anti-metrics.md` — **non-normative** diagnostic aids for telling substantive adoption from ceremonial adoption
- `reference-implementations/roles/` — runtime-neutral Planner / Implementer / Reviewer role prompts (paste-ready for Cursor Custom Mode, Gemini CLI session, Windsurf mode, Codex profile)
- `reference-implementations/validator-{posix-shell,python,node}/` — three non-normative language references for the automation contract; the Python and Node references close all rules (including 2.4 / 2.5 / 3.2 / 3.4) and agree on exit codes + rule IDs

**You pick one when relevant to your stack:**
- `docs/bridges/flutter-stack-bridge.md`
- `docs/bridges/android-kotlin-stack-bridge.md`
- `docs/bridges/android-compose-stack-bridge.md`
- `docs/bridges/ios-swift-stack-bridge.md`
- `docs/bridges/react-nextjs-stack-bridge.md`
- `docs/bridges/ktor-stack-bridge.md`
- `docs/bridges/unity-stack-bridge.md`

---

## The first 60 seconds of any task

Before touching code, answer in order:
1. What kind of task is this (feature / bugfix / refactor / migration / investigation)?
2. Which surfaces are affected?
3. Where is the source of truth?
4. Who are the main consumers?
5. Is there public behavior impact?
6. Should this be Lean or Full?
7. What is the minimum artifact set?
8. What evidence must exist before completion?

If you cannot answer (3) with confidence, **stop** and resolve that first. That is the single most important rule of the methodology.

---

## Stop conditions

Do not proceed if any of these are true:
- The source of truth is unclear and you would be guessing.
- Affected surfaces cannot be enumerated.
- A breaking change has no identified migration path.
- Rollback strategy is unknown for a change that needs one.
- Verification evidence cannot be produced.

Stop, state the blocker, and ask.

---

## Behavior boundaries (hard rules)

- Never fabricate file paths, APIs, or library behavior. If unsure, read the code or ask.
- Never claim a fix is verified without running the verification.
- Never expand scope silently. Scope changes require explicit acknowledgment.
- Never bypass CI checks, signing, or hooks without explicit user authorization.
- Never commit secrets, credentials, or local developer config.

---

## Walkthrough: applying the methodology end-to-end

A realistic, stack-neutral example showing every phase. Assume the team ships a service that exposes a "user status" value consumed by three internal services, one mobile app, and a data warehouse.

### The change

A new status value `pending_review` must be introduced; the existing `active` value splits into `active` and `active_pending_review`. The change is triggered by a compliance requirement.

### Phase 0 — Clarify

- Kind: feature + L2 breaking change.
- Surfaces touched: information (enum), system-interface (API contract), operational (dashboards, runbook), process (support SOP).
- Consumers: three internal services, one mobile app, one data warehouse, one support SOP.
- Severity (draft): L1 on the surface, but promoted to **L2 structural** because consumers that do `switch (status)` without default will silently fall through.
- Stop-gate: confirm compliance is the actual driver — not tech-debt cleanup — because that decides whether reversible deferral is allowed.

### Phase 1 — Investigate

- Locate SoT for the enum (pattern 3 — enum registry or schema file).
- Locate all declared consumers via contract catalog (if the team keeps one) or grep + team-org discipline.
- Identify **uncontrolled interface** risk: mobile app has 60-day install-base decay; old versions cannot be recalled.
- Identify **data warehouse** as easy-to-forget consumer — it has no type system to complain.

### Phase 2 — Plan

- Migration path: **parallel switch** (path B from breaking-change-framework).
- Rollback mode: **mode 2 forward-fix** (enum values cannot be retracted from third-party data platforms after being written).
- Agree merge order with any concurrent ticket touching the same SoT.
- Draft the Change Manifest: declare surfaces, SoT, consumers, migration path, rollback mode, evidence plan.

### Phase 3 — Test Plan

- Contract tests for both old and new enum closure.
- Consumer-side tests for mobile fallback ("unknown value treated as active").
- Data-warehouse lineage test (new value appears in target table within SLA).
- Support SOP dry-run with operations team.

### Phase 4 — Implement

- Add new value in SoT file.
- Regenerate codegen artifacts.
- Dual-write both representations during transition.
- Update mobile to treat unknown enum as existing `active`.
- Update data-warehouse schema registry with backfill policy.

### Phase 5 — Review

- Reviewer checks manifest: every declared surface has an evidence artifact; every consumer category is covered; breaking-change migration path matches declared rollback mode; uncontrolled-interface risk has a mitigation (mobile fallback).

### Phase 6 — Merge + Rollout

- Merge order matches `depends_on` in the manifest.
- Gradual rollout with the stop condition pre-declared (error-rate band, consumer-side decode failure count).

### Phase 7 — Deliver

- Completion report attached to manifest: real rollout graph, first observed new-value timestamp, no unknown-value errors from consumers within 24h.

### Phase 8 — Observation

- 30-day window watching the chosen metrics.
- Surprise found (good): support SOP absorbed the new status cleanly because we dry-ran it. Note it as a success case for the failure-mode gallery.
- Surprise found (bad): one downstream analytics query silently coerces unknown values — ticket opened with `part_of` link back to the original manifest.

### What the walkthrough shows

- The methodology does not assume a perfect first pass; it assumes surprises and channels them back into the artifact trail.
- Every decision point names its doc (`breaking-change-framework.md`, `rollback-asymmetry.md`, bridge docs, automation-contract-algorithm.md).
- The Change Manifest is the single carrier artifact connecting all nine phases.

---

## Full file index

Canonical doc list, ordered by when you'll typically read it.

### Entry + philosophy (read first)

- `docs/product-engineering-operating-system.md` — the six preamble principles.
- `docs/system-change-perspective.md` — why surface-first, not layer-first.
- `docs/surfaces.md` — canonical four-surface model + extensions.

### Core methodology (read when you hit the situation)

- `docs/source-of-truth-patterns.md` — 10 SoT patterns.
- `docs/breaking-change-framework.md` — L0-L4 severity matrix + consumer classification.
- `docs/rollback-asymmetry.md` — modes 1 / 2 / 3.
- `docs/cross-cutting-concerns.md` — six concerns applied per-surface.

### Per-surface disciplines

- `docs/user-surface-disciplines.md` — user-surface checklist.
- `docs/implementation-disciplines.md` — implementation checkpoints.
- `docs/operational-disciplines.md` — operational-surface checklist.
- `docs/playtest-discipline.md` — experience-surface verification (for game/consumer apps).

### Process + coordination

- `docs/concurrent-changes.md` — multiple overlapping tickets.
- `docs/adoption-strategy.md` — phased team rollout.
- `docs/post-delivery-observation.md` — Phase 8.
- `docs/ci-cd-integration-hooks.md` — hook-point spec.

### Contract + automation

- `docs/change-manifest-spec.md` — machine-readable output contract (includes the "Deprecating a field" decision table for the schema's `$defs.deprecation` marker).
- `docs/automation-contract-algorithm.md` — normative validator algorithm.
- `docs/runtime-hook-contract.md` + `docs/runtime-hooks-in-practice.md` — normative runtime-hook contract + the how-to companion (install, adapter wiring, adoption ramp).
- `schemas/change-manifest.schema.yaml` + `.json` + `schemas/surface-map.schema.yaml` + `.json` — dual-format schemas; the JSON mirrors are generated from the YAML canonicals and drift-checked in CI.
- `CHANGELOG.json` — generated machine-readable release feed alongside the human `CHANGELOG.md`.
- `reference-implementations/validator-{posix-shell,python,node}/` — non-normative example validators in three languages.

### Stack bridges (pick one for your stack)

- `docs/stack-bridge-template.md` — template for new bridges.
- `docs/bridges/flutter-stack-bridge.md`
- `docs/bridges/android-kotlin-stack-bridge.md`
- `docs/bridges/android-compose-stack-bridge.md`
- `docs/bridges/ios-swift-stack-bridge.md`
- `docs/bridges/react-nextjs-stack-bridge.md`
- `docs/bridges/ktor-stack-bridge.md`
- `docs/bridges/unity-stack-bridge.md`

### Visual + reference

- `docs/diagrams.md` — Mermaid visualizations.
- `docs/glossary.md` — term definitions.

---

## Language policy

All normative content in this repository — the operating contract (`AGENTS.md`), the automation algorithm, reference implementations, methodology documents (every `docs/*.md` page), the engineering-workflow skill, schemas, Change Manifest templates, and the stack bridges — is authored in English. New contributions MUST be English.
