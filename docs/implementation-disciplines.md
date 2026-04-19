# Implementation Disciplines

> **English TL;DR**
> Language-agnostic checkpoints for *any* implementation change — APIs, business logic, data access, external integrations, package/dep changes. Main observation axes: **contract clarity** (typed payloads, versioning, deprecation path), **layering** (entry / business / persistence / integration responsibilities not mixed), **data access health** (hot-path patterns like N+1, cache/index/migration impact visible), **error + observability** (classification, propagation, structured logs, traces at boundaries), **concurrency + lifecycle** (scope, cancellation propagation, resource ownership), **dependency + environment** (explicit version pinning, reproducible install, environment-sensitive behavior flagged). Companion to `user-surface-disciplines.md` and `operational-disciplines.md`. Used during Phase 3 (plan) and Phase 5 (review) to evaluate whether an implementation change meets the quality floor regardless of stack.

This document provides general-purpose review checkpoints for any change that touches the **implementation surface**.
It is not specific to any language, framework, or project structure.

## When this document applies

Apply this discipline whenever a change touches any of the following:

- API / event / job / outward-facing contract
- Business logic / flow
- Data access / schema / migration
- Cache / search / external integration
- Packages / dependencies / runtime environment

## Primary observation axes

### Contract clarity

- request / response / event payloads have explicit types or schemas.
- No uncontrolled, loosely typed payloads.
- A versioning strategy is explicit (backward compatibility / deprecation).

### Clear layering

- Entry point / business logic / persistence / integration responsibilities are not mixed.
- A given layer does not do work that belongs elsewhere.

### Data-access health

- Obvious inefficient patterns (e.g. N+1 or full-table scans on hot paths) are either absent or explicitly called out.
- cache / index / migration impact is stated, not implicit.

### Errors and observability

- Foreseeable errors have explicit handling paths.
- logs / metrics are sufficient for another engineer to reconstruct the scene.

### Documentation sync

- Changes to public interfaces are reflected in outward docs and changelogs.
- Changes to internal contracts have corresponding consumer-side follow-up.

## General review checklist

- [ ] Contract is explicit; payload shape is predictable.
- [ ] Naming matches project conventions.
- [ ] No layering confusion.
- [ ] No obvious data-access inefficiency.
- [ ] schema / index / cache / search / integration impact has been assessed.
- [ ] Error handling and logging are sufficient.
- [ ] Verification method is reproducible.
- [ ] Public-interface changes are documented.

## Verification methods

Combine as appropriate for the project:

- build / compile / typecheck
- unit / integration / contract tests
- schema or migration verification
- request/response or event-payload verification
- log / metric / queue observation

Do not treat a single command as the only valid verification — choose whatever the actual repo can run and reproduce.
