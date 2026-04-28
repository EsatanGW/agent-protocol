# Anti-Entropy Discipline

> **English TL;DR**
> A repository accumulates drift over time even when every individual change is correct. Stale CCKNs, abandoned feature flags, doc references to renamed files, retired manifests still cited as live, deprecation timelines past their hard cutoff, mechanical-enforcement rules that no longer fire — these are the by-products of forward motion. Anti-entropy is the discipline of *continuous garbage collection*: time-driven sweeps that find drift, propose cleanups, and submit them as small reviewable changes. It complements [`docs/mechanical-enforcement-discipline.md`](mechanical-enforcement-discipline.md) (which catches drift at the edit boundary) and Phase 8 post-delivery observation (which is event-driven). Tool-agnostic.

---

## Why this discipline exists

Mechanical enforcement at the edit boundary catches the violation that lands in front of you. It does not catch the violation that landed correctly six months ago and has since become drift because the surrounding code moved. A correct edit at time *t₀* can become a stale reference at *t₀ + N* without anyone editing the reference itself.

Examples of *single-change-correct, long-run-drifted* state in this repository's terms:

- A CCKN written 14 months ago, still cited from a recent manifest, whose `last_verified` field is past the 12-month re-verification window from [`docs/ai-project-memory.md`](ai-project-memory.md) §Adjacent artifact.
- A `breaking_change.deprecation_timeline` declared in a manifest whose `hard_cutoff` is 2025-12-01; today is 2026-04 and the deprecated path is still in source.
- A bridge file (`docs/bridges/*-stack-bridge.md`) referencing a runtime version that has been retired upstream.
- A reference-implementations entry whose underlying runtime API has shifted (the wrapper still passes its own selftests, but the runtime no longer behaves as the wrapper assumes).
- A `docs/decision-trees.md` row pointing at a `references/*.md` file that has since been renamed.
- A `validator-python` rule whose Tier-2 cross-reference fires zero times across the last 50 PRs — either covered a now-extinct failure mode or is silently bypassed.

None of these break the change that is being delivered today. Each erodes the repository's reliability the next time someone reads the artifact in good faith.

---

## The discipline (3 rules)

### Rule 1 — Sweeping is read-only and proposal-shaped

A sweep finds drift and *proposes* a cleanup; it does not silently fix. The proposal is a small, scoped change that goes through the normal Phase 0 → Phase 7 lifecycle (Lean mode for most cases — single surface, one consumer, ≤ 5-minute verification). A sweep agent that auto-applies fixes is a high-blast-radius bot and is forbidden under [`AGENTS.md §Stop conditions`](../AGENTS.md): the cleanup is itself a change, and changes go through the methodology.

The sweep agent's output is one of:

- A pull request / branch / patch with the proposed cleanup, or
- An issue / ticket / log entry naming the drift and where to find it, or
- An entry in a project-memory log per [`docs/ai-project-memory.md`](ai-project-memory.md) §Recommended on-disk layout (the *Escalation log* role is appropriate).

The proposal must include the **drift cause** (what was correct, what changed around it), the **scope** (which artifacts / files / fields are affected), and the **proposed fix** (what to delete, rename, update, or extend).

### Rule 2 — Sweeps are time-driven; Phase 8 is event-driven

Phase 8 (Post-Delivery Observation, [`docs/post-delivery-observation.md`](post-delivery-observation.md)) catches *delivery-event* drift: T+24h / T+72h / T+7d after a specific change lands, watch for fallout. The event is the change.

Anti-entropy sweeps are *time-driven*: weekly / monthly / per-release-cycle, scan the repository for accumulated drift independent of any specific delivery. The triggering event is the calendar.

The two are complementary, not redundant:

| Mechanism | Trigger | Scope | Owner |
|---|---|---|---|
| Mechanical enforcement (edit-boundary) | Tool use / commit / response | The diff in front of you | Implementer's runtime hooks |
| Phase 8 post-delivery observation | Delivery event + observation cadence | The delivered change's blast radius | The change's Reviewer / Observer |
| Anti-entropy sweep | Calendar | The whole repository | A scheduled agent or maintainer rotation |

A repository that has only the first two will accumulate drift in the long tail; one that has only the third will miss the change-specific fallout; one that has all three is closest to coherent.

### Rule 3 — Sweeps stay scoped; one drift class per sweep

A sweep that surveys *every* form of drift in one pass produces an unreviewable proposal. The discipline is one drift class per sweep:

- **CCKN-staleness sweep.** Find every CCKN with `last_verified` older than 12 months; output a list with re-verification owners.
- **Deprecation-cutoff sweep.** Find every `breaking_change.deprecation_timeline.hard_cutoff` past today; output the manifests that need to remove the deprecated path or extend the timeline.
- **Doc-reference-rot sweep.** Find every `docs/**/*.md` link that no longer resolves to a real file or section; output the file:line list with the broken target.
- **Retired-manifest-cite sweep.** Find every `references` field across `docs/`, `skills/`, and live manifests that points at a manifest with `status: retired`; flag for re-pointing or removal.
- **Reference-implementation drift sweep.** Find every `reference-implementations/*/DEVIATIONS.md` that has not been touched in N versions while the upstream `docs/` source has moved; flag for re-validation.
- **Mechanical-rule no-fire sweep.** Find every rule in `automation-contract*.md` / `runtime-hook-contract.md` Category B–D that has produced zero findings across the last *K* changes; flag for review (the rule is either covering an extinct case or silently bypassed).
- **Rung-claim-evidence sweep.** Find every change in the most recent release whose claimed autonomy rung (per [`autonomy-ladder-discipline.md`](autonomy-ladder-discipline.md)) does not match the rung's minimum evidence shape; output the change ID, the claimed rung, and the missing evidence categories — propose either downgrading the rung claim for that change or backfilling the missing evidence. Closes the detector role declared at [`autonomy-ladder-discipline.md §Anti-patterns`](autonomy-ladder-discipline.md) (Rung-claiming).
- **Discipline-provenance sweep.** Find every project-local discipline / extension (in consumer `docs/`, `skills/`, or bridge-adjacent locations — *not* this repo's canonical principles or canonical disciplines, which are origins by definition) whose originating-incident link is absent. Cross-reference with the usage signal across the last *K* changes: signal present → propose re-anchor (find and cite the originating incident); signal absent → propose retirement. Both proposal shapes share one drift class because both follow from missing provenance. Distinguished from the Mechanical-rule no-fire sweep above: that sweep targets rules that *never* fire; this one targets disciplines that *always* fire but whose justification is no longer locatable. See [`docs/glossary.md §Provenance drift`](glossary.md).

A sweep that covers two or more classes is a sweep that will not be reviewed; split it.

---

## Cadence

Each drift class has its own natural cadence; the discipline does not mandate exact frequencies, only the *order of magnitude*:

| Drift class | Suggested cadence | Why |
|---|---|---|
| CCKN-staleness | Monthly | The 12-month staleness model gives 12 monthly sweeps before the first re-verification is due |
| Deprecation-cutoff | Per release cycle | Cutoffs are usually expressed in release-relative terms |
| Doc-reference-rot | Weekly | Renames / moves are frequent; freshness windows are short |
| Retired-manifest-cite | Quarterly | Retirement events are infrequent |
| Reference-implementation drift | Per upstream-version-change | Triggered by upstream events, not calendar |
| Mechanical-rule no-fire | Per minor version | A rule that has not fired in a minor version's worth of PRs deserves a look |
| Rung-claim-evidence | Per minor version | One-change-per-release sample is enough to detect rung-claim drift; minor-version cadence aligns with the mechanical-rule re-eval rhythm so both axes share one calendar slot |
| Discipline-provenance | Per minor version | A discipline whose originating incident is no longer locatable after a minor version's worth of changes is a candidate for re-anchoring or retirement; the sweep is the asymmetric retirement pathway's input (see [`mode-decision-tree.md §Scenarios that force Lean`](../skills/engineering-workflow/references/mode-decision-tree.md)) |

A repository that picks cadences should write them down (in `docs/bridges/*-stack-bridge.md` or a project-local equivalent) so that the schedule is itself transcoded per [`docs/repo-as-context-discipline.md`](repo-as-context-discipline.md).

---

## Quality score (optional, non-mandatory)

A repository may choose to track a per-domain *quality score* that summarises the open-drift count across the sweep classes. The score is descriptive, not normative — it gives a single number per domain (`auth/`, `data-pipeline/`, `ui/`, …) that maintainers can watch over time.

A simple shape:

```
quality_score(domain, t) =
  100
  - 5 * count(open_cckn_staleness in domain at t)
  - 3 * count(open_doc_reference_rot in domain at t)
  - 10 * count(open_deprecation_cutoff_past in domain at t)
  - 2 * count(open_retired_manifest_cite in domain at t)
  - …
```

This document does **not** mandate the formula, the units, or the storage location. A bridge or project that adopts a quality score should document its formula alongside the cadence schedule. A score is not a substitute for the sweeps themselves — fixing the score's number without resolving the underlying drift is the anti-pattern this rule is most often gamed by.

---

## Anti-patterns

- *"Sweep agent auto-applies the fix."* The sweep is a finding, not a fix. Auto-apply turns a drift detector into a high-blast-radius bot; every cleanup is a change, every change goes through the methodology.
- *"Run all sweeps in one pass weekly."* The combined output is unreviewable. One sweep, one drift class, one proposal at a time.
- *"Sweep without a proposed fix."* A finding without a fix is a backlog; backlogs grow. The sweep names the drift *and* names the cleanup.
- *"Quality score replaces sweeping."* The score summarises sweeps; it does not perform them. A repository whose score is "green" but has not run sweeps in three months has a stale score.
- *"Sweep agent runs 24/7."* The sweep is calendar-driven; running continuously is a different discipline (drift detection, not anti-entropy GC) and incurs continuous cost. Calendar cadence is the contract; continuous polling is at most an optimization.
- *"Sweep findings live only in chat."* Findings are external knowledge until transcoded; per [`docs/repo-as-context-discipline.md`](repo-as-context-discipline.md), they must land in a repo-resident artifact (issue, ticket, branch, log) before they govern future behaviour.

---

## Phase hookup

Anti-entropy sweeps are themselves changes — they go through Phase 0 → Phase 7 like any other. The hookup below is for the *target change* (the change that closes the drift), not for the sweep itself.

- **Phase 0 (Clarify).** The sweep finding is the input. The change's title is `"Resolve <drift-class> finding for <scope>"`; the body cites the sweep's proposal.
- **Phase 1 (Investigate).** Confirm the drift is still present (a sweep finding can be stale by the time the cleanup starts) and identify the SoT for the artifact being cleaned up.
- **Phase 2–4 (Plan / Test plan / Implement).** Lean mode unless the cleanup itself crosses surfaces — most cleanups do not.
- **Phase 5 (Review).** Reviewer confirms (a) the drift is closed, and (b) no new drift was introduced (the cleanup itself can be drift if it pulls a still-live consumer along incorrectly).
- **Phase 7 (Deliver).** The completion report references the sweep finding by ID, closing the loop. The sweep's log of open findings now shows this finding as `resolved`.
- **Phase 8 (Observe).** Most cleanups do not need an observation window — the drift was the failure mode and is now closed. Cleanups that *cross* surfaces (e.g. removing a deprecated API) do need the observation window per [`docs/post-delivery-observation.md`](post-delivery-observation.md).

---

## Relationship to other documents

- [`docs/mechanical-enforcement-discipline.md`](mechanical-enforcement-discipline.md) — the edit-boundary counterpart; covers the single-change axis. This document covers the time axis.
- [`docs/post-delivery-observation.md`](post-delivery-observation.md) — the delivery-event counterpart; covers the per-change axis. This document covers the calendar axis.
- [`docs/ai-project-memory.md`](ai-project-memory.md) §Memory decay — names the staleness model for CCKNs and retired manifests; this discipline operationalises that model into time-driven sweeps.
- [`docs/repo-as-context-discipline.md`](repo-as-context-discipline.md) — the *what should be in the repo* discipline; this discipline is the *what should still be true about what is in the repo* discipline.
- [`docs/adoption-anti-metrics.md`](adoption-anti-metrics.md) — the over-enforcement counter-pressure; sweep volume itself can become an anti-metric if a repository measures by sweep count rather than drift closed.
- [`docs/breaking-change-framework.md`](breaking-change-framework.md) §Deprecation timelines — the source of the deprecation-cutoff sweep target.
- [`docs/autonomy-ladder-discipline.md`](autonomy-ladder-discipline.md) §Anti-patterns — defines the rung-claim and rung-skipping anti-patterns; the Rung-claim-evidence sweep above is the time-driven detector for the former (the latter is caught at the change boundary, not on calendar).
- [`skills/engineering-workflow/references/mode-decision-tree.md`](../skills/engineering-workflow/references/mode-decision-tree.md) §Scenarios that force Lean — the asymmetric retirement-cost row that lets sweep-backed retirements drop to Lean mode while additions stay Full per L60. This is what makes the methodology able to *shed* weight rather than only accumulate; the Discipline-provenance sweep above produces the finding that the row consumes.
- [`docs/glossary.md §Provenance drift`](glossary.md) — the term defined for the failure mode the Discipline-provenance sweep targets.
