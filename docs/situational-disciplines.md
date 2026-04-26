# Situational Disciplines

> **English TL;DR**
> Per-change quality floors for the three situational surfaces, merged into a single discipline file in 1.20.0 (previously `operational-disciplines.md`, `implementation-disciplines.md`, `user-surface-disciplines.md`). Activate the section that matches the surface(s) the change touches; skip the rest. Each section keeps its own observation axes, "when this applies" trigger list, and review checklist. Cross-cutting concerns (security, performance, observability, testability, error handling, build-time risk) are covered uniformly in [`cross-cutting-concerns.md`](cross-cutting-concerns.md), not duplicated here.

This file replaces three sibling documents that each covered one situational surface. The merge is structural — section bodies are preserved verbatim — and is part of the over-design audit captured in 1.20.0. Anchors below are stable for the foreseeable future:

- [`#user-surface`](#user-surface) — the user-visible surface (UI, copy, A/B variant)
- [`#implementation-surface`](#implementation-surface) — APIs, business logic, data access, integrations
- [`#operational-surface`](#operational-surface) — logs, audit, telemetry, rollout, rollback, handoff

Applied during Phase 3 (plan) and Phase 5 (review). Each section can be read standalone; activate only the sections whose triggers match the change at hand.

---

## User surface

> Per-change checklist for the *user surface* — what a human actually sees, clicks, waits for, and interprets. Five observation axes: **UI flow correctness** (can the user complete the requested journey end-to-end; entry/action/result/feedback/errors stay consistent), **contract alignment** (component data shape matches SoT; loading/empty/error/partial states all handled), **internationalization and copy** (every new or changed string has an i18n key; every supported locale has a matching value), **usability** (keyboard reachable + focus visible + semantic markup correct; color contrast + responsive behavior reasonable), **operational hooks** (critical actions captured by logging/telemetry; dangerous actions gated by explicit confirmation). Applies to route / page / component / form / table / modal / drawer / state store / query layer / i18n / design system changes.

This section provides general-purpose review checkpoints for any change that touches the **user surface**.

### When this section applies

Apply this discipline whenever a change touches any of the following:

- route / page / component
- form / table / modal / drawer
- state store / query layer / API client
- i18n / copy
- design system / theme
- a11y / responsive / keyboard / focus
- analytics / telemetry hooks

### Primary observation axes

#### UI flow correctness

- The user can complete the full path described in the requirements.
- Entry points, actions, results, feedback, and errors all exist and stay consistent.

#### Contract alignment

- The data shape a component reads matches the source of truth.
- Loading / empty / error / partial states are all handled.

#### Internationalization and copy

- Every new or changed string has an i18n key.
- Every supported locale has a corresponding value.

#### Usability

- Keyboard reachable, focus visible, semantic markup correct.
- Color contrast and responsive behavior are reasonable.

#### Operational hooks

- Critical actions are captured by logging / telemetry.
- Dangerous actions have an explicit confirmation flow.

### General review checklist

- [ ] UI flow matches the requirements.
- [ ] component / route / state / API-client wiring is correct.
- [ ] i18n keys are complete across all supported locales.
- [ ] validation / error / empty / loading states are complete.
- [ ] Accessibility is reasonable.
- [ ] No leftover debug / mock / placeholder data.
- [ ] lint / test / build passes.
- [ ] Deliverable visual evidence exists (screenshot, recording, or equivalent).

### Verification methods

Combine as appropriate for the project:

- lint / test / build
- component / integration / e2e tests
- Browser interaction verification
- Screenshot / recording
- Console / network inspection
- a11y checks

---

## Implementation surface

> Language-agnostic checkpoints for *any* implementation change — APIs, business logic, data access, external integrations, package/dep changes. Five observation axes: **contract clarity** (typed payloads, versioning, deprecation path), **clear layering** (entry / business / persistence / integration responsibilities not mixed), **data-access health** (hot-path patterns like N+1, cache/index/migration impact visible), **errors and observability** (foreseeable errors have explicit handling paths; logs/metrics sufficient to reconstruct the scene), **documentation sync** (public-interface changes reflected in outward docs and changelogs; internal-contract changes carry consumer-side follow-up). Concurrency / cancellation propagation and dependency / environment concerns are covered cross-cuttingly in [`cross-cutting-concerns.md`](cross-cutting-concerns.md) (error-handling cancellation sub-section and build-time-risk respectively), not as axes here. Used during Phase 3 (plan) and Phase 5 (review) to evaluate whether an implementation change meets the quality floor regardless of stack.

This section provides general-purpose review checkpoints for any change that touches the **implementation surface**. It is not specific to any language, framework, or project structure.

### When this section applies

Apply this discipline whenever a change touches any of the following:

- API / event / job / outward-facing contract
- Business logic / flow
- Data access / schema / migration
- Cache / search / external integration
- Packages / dependencies / runtime environment

### Primary observation axes

#### Contract clarity

- request / response / event payloads have explicit types or schemas.
- No uncontrolled, loosely typed payloads.
- A versioning strategy is explicit (backward compatibility / deprecation).

#### Clear layering

- Entry point / business logic / persistence / integration responsibilities are not mixed.
- A given layer does not do work that belongs elsewhere.

#### Data-access health

- Obvious inefficient patterns (e.g. N+1 or full-table scans on hot paths) are either absent or explicitly called out.
- cache / index / migration impact is stated, not implicit.

#### Errors and observability

- Foreseeable errors have explicit handling paths.
- logs / metrics are sufficient for another engineer to reconstruct the scene.

#### Documentation sync

- Changes to public interfaces are reflected in outward docs and changelogs.
- Changes to internal contracts have corresponding consumer-side follow-up.

### General review checklist

- [ ] Contract is explicit; payload shape is predictable.
- [ ] Naming matches project conventions.
- [ ] No layering confusion.
- [ ] No obvious data-access inefficiency.
- [ ] schema / index / cache / search / integration impact has been assessed.
- [ ] Error handling and logging are sufficient.
- [ ] Verification method is reproducible.
- [ ] Public-interface changes are documented.

### Verification methods

Combine as appropriate for the project:

- build / compile / typecheck
- unit / integration / contract tests
- schema or migration verification
- request/response or event-payload verification
- log / metric / queue observation

Do not treat a single command as the only valid verification — choose whatever the actual repo can run and reproduce.

---

## Operational surface

> Per-change checklist for the *operational surface* — the most commonly under-invested one. Four questions every delivery must answer: **who can trace it if it fails** (logs, audit, correlation id), **how is it rolled back** (rollback mode 1/2/3 plus exact steps), **what does the next handoff see** (changelog, handoff note, migration note), **where is the evidence** (test output, metric snapshot, screenshot, telemetry link). Covers per-item quality floors: structured logs (not string concat), audit trail for state-changing ops, telemetry with metric names not ad-hoc strings, changelog entries that say *why* not just *what*, migration notes that include reversal path, rollout plan with a *stop condition*.

This section covers the operational surface — the surface every task touches and the one most often under-invested.

### When this section applies

Almost every change will touch at least one of:

- log / audit
- telemetry / monitoring / alerting
- rollout / migration / rollback
- docs / changelog / handoff
- evidence preservation

### Questions that must be answered at delivery

- If it breaks, who can trace it?
- If it must be rolled back, how?
- If it must be handed off, what does the next person look at?
- If it must be verified, where is the evidence kept?

### Primary observation axes

#### Traceable

- Critical changes leave behind operational records or diagnostic signals.
- When something goes wrong, event ordering can be reconstructed.

#### Rollback-able

- The change has a reversal path or a safe degradation strategy.
- Switch points for migrations / feature flags are explicit.

#### Hand-off-able

- The completion report is directly usable by whoever picks up next.
- Key decisions, constraints, and risks are recorded.

#### Evidence preserved

- Verification outputs, screenshots, and payloads can be cited.
- Evidence does not vanish when the session ends.

### General review checklist

- [ ] Significant changes leave operational records.
- [ ] Outward-facing behavior changes are documented or changelog'd.
- [ ] rollout / rollback strategy can be stated.
- [ ] The completion report has genuine handoff value.
- [ ] Monitoring / alerts have been adjusted where needed.

### See also (operational-specific)

- [`adoption-anti-metrics.md`](adoption-anti-metrics.md) — **non-normative** diagnostic aids for catching ceremonial adoption of the above checklist (evidence paths all pointing at the same artifact, `rollback.overall_mode` always 1, LGTM-only review notes). Not CI gates — review conversations.
