# Summary-vs-Per-Case Consistency Registry

> **Status.** Audit artifact, not normative. Lists every location in this repo where a summary claim (TL;DR, opening rule, or lead sentence) sits next to a per-case / per-item enumeration that could drift. Produced 2026-04-22 as a follow-up to the CCKN query-timing cycle (1.14.0 → 1.14.1 → 1.14.2 → 1.14.3), which exposed summary-vs-per-case drift as a recurring failure mode.
>
> This document **does not modify any normative file**. It classifies observed drift; whether to fix any given item is a separate editorial decision.
>
> **Resolution status (2026-04-22, release 1.14.4):** All eight (a) real-drift findings (A1–A8) below have been resolved by updating the respective TL;DRs to match their bodies. Each (a) entry now carries a **Resolved in 1.14.4** line naming the commit. Findings are kept in place as historical record per the registry's own "don't silently re-ship" rule; the registry itself is a dated audit artifact — re-run it per §Next sweep triggers when conditions fire. Findings (b) and (c) remain as noted.

---

## Purpose

The three CCKN releases each hit the same pattern: a summary rule was updated but the adjacent per-case prose carrying the same framing was not re-scanned, producing contradictions that survived into the shipped docs. This audit asks "where else in the repo does that same pattern sit waiting to drift?"

For every normative doc in `docs/`, the audit asks:

1. Does the file have a summary-shaped claim (TL;DR, opening rule, one-line lead) that **enumerates items** (N categories / stages / modes / axes / hooks / patterns)?
2. Does the body have a corresponding per-case section (numbered, tabled, or sectioned)?
3. Do the two lists match — same count, same names, same ordering?

Three-bucket classification:

- **(a) Real drift** — summary and body disagree on count, names, or ordering in a way that would mislead a reader following only the summary.
- **(b) Legitimate two-level** — summary compresses body; no contradiction, just different granularity.
- **(c) Boundary** — technically different but the gap is defensibly "editorial compression" rather than drift.

Audit scope: the 36 normative files under `docs/` (plus `schemas/change-manifest.schema.yaml`). Skipped: `docs/bridges/`, stack-bridge files, surface-map YAMLs (data / template files, no normative claims), `docs/onboarding/*` (reader-facing intros; summary drift is expected and intentional).

---

## (a) Real drift findings

### A1 — `docs/source-of-truth-patterns.md:4`

- **TL;DR claim.** "*Five common desync anti-patterns and four repair strategies are enumerated.*"
- **Body reality.** §Common desync anti-patterns lists **six** entries (Anti-pattern 1 through 6 at lines 556, 568, 580, 592, 603, 615). Anti-pattern 6 — "*Pipeline order treated as an implementation detail (not a contract)*" — is almost certainly the row that was added when sub-pattern 4a (Pipeline-Order Contract) was introduced, without the TL;DR being updated.
- **Why it matters.** A reader using the TL;DR as a mental index will miss the Pipeline-Order anti-pattern, which is load-bearing for Phase 1 SoT analysis on middleware / interceptor chains.
- **Resolved in 1.14.4.** TL;DR updated to "*Six common desync anti-patterns ... — anti-pattern 6 pairs with sub-pattern 4a*" and clarifies that half-sync gotchas are a callout within Pattern 8, not a separate pattern.

### A2 — `docs/implementation-disciplines.md:4`

- **TL;DR claim.** Six axes: "*contract clarity, layering, data access health, error + observability, **concurrency + lifecycle**, **dependency + environment***".
- **Body reality.** §Primary observation axes has **five** entries: Contract clarity, Clear layering, Data-access health, Errors and observability, **Documentation sync**.
- **Mismatch.** The two TL;DR axes printed in bold ("concurrency + lifecycle", "dependency + environment") do **not exist** in the doc body. The body's fifth axis — "Documentation sync" — is **not** in the TL;DR. The TL;DR describes a doc that was planned but not (fully) written; §When this document applies (line 17) lists "Packages / dependencies / runtime environment" as a trigger, reinforcing that "dependency + environment" was intended as an axis.
- **Why it matters.** The TL;DR's two phantom axes cover concurrency / dep-pinning quality gates that a reviewer expects to find. Their absence is an invisible hole in review-floor coverage.
- **Resolved in 1.14.4.** Took the conservative direction — updated TL;DR to match the body's actual five axes (Contract clarity / Clear layering / Data-access health / Errors and observability / Documentation sync). The TL;DR now also points explicitly at `cross-cutting-concerns.md` as the home of concurrency / cancellation propagation (error-handling sub-section) and dependency / environment (build-time-risk), preserving the signal that those quality gates exist but correctly locating them. Adding them as new axes here would have been a scope expansion, not a drift fix.

### A3 — `docs/user-surface-disciplines.md:4`

- **TL;DR claim.** Six axes: "*flow correctness, contract alignment, **feedback + guidance**, **a11y**, **responsive + device**, analytics + telemetry*".
- **Body reality.** §Primary observation axes has **five** entries: UI flow correctness, Contract alignment, **Internationalization and copy**, **Usability**, **Operational hooks**.
- **Mismatch.** TL;DR names `feedback + guidance`, `a11y`, `responsive + device`, `analytics + telemetry`; body names `i18n and copy`, `Usability`, `Operational hooks`. Only 2 of 6 TL;DR axes match the body verbatim. The body appears to fold a11y + responsive into "Usability" and to surface "Internationalization and copy" as its own axis (the TL;DR demotes i18n to a sub-bullet of "feedback + guidance").
- **Why it matters.** A Phase 5 Reviewer using the TL;DR as a checklist will look for axes (a11y section, responsive section) that don't exist under those names, and will miss the axis (Internationalization) that actually does.
- **Resolved in 1.14.4.** Updated TL;DR to match the body's actual five axes (UI flow correctness / Contract alignment / Internationalization and copy / Usability / Operational hooks). The TL;DR's earlier taxonomy (a11y + responsive as separate axes) is now folded under "Usability" in the body's compact form, and "analytics + telemetry" is generalized to "Operational hooks"; the TL;DR reflects this consolidation rather than promising finer splits the body doesn't deliver.

### A4 — `docs/adoption-strategy.md:4`

- **TL;DR claim.** "*Stage 1 (1-2 weeks) ... Stage 2 (1-2 months) ... Stage 3 (3+ months).*"
- **Body reality.** Section headers read "Stage 1: mindset seeding (1–2 weeks)", "Stage 2: process embedding (**2–4 weeks**)", "Stage 3: institutionalization (**4–8 weeks**)".
- **Mismatch.** Stage 2: TL;DR says 4–8 weeks (1–2 months), body says 2–4 weeks. Stage 3: TL;DR says 12+ weeks (3+ months), body says 4–8 weeks. `docs/diagrams.md:161-162` matches the body (2–4 weeks / 4–8 weeks), so the body is the internally-consistent source; the TL;DR drifted.
- **Why it matters.** Adopting teams plan capacity against these durations; a 2–3× error in the TL;DR is a real planning pitfall.
- **Resolved in 1.14.4.** Updated TL;DR to "Stage 2 (2-4 weeks)" and "Stage 3 (4-8 weeks)" to match body + diagrams. Body stayed authoritative (internally consistent with the `docs/diagrams.md` adoption-phase diagram).

### A5 — `docs/ci-cd-integration-hooks.md:4`

- **TL;DR claim.** "*seven hook points: ... **(6) pre-merge → Change Manifest schema validation** ...*"
- **Body reality.** Section header reads "Hook 6: **completion-report check**" — a different check (verifies a completion report exists, not schema conformance).
- **Mismatch.** TL;DR's Hook 6 description names a check that doesn't exist as Hook 6 in the body; the actual schema-validation work lives in `docs/automation-contract-algorithm.md` Layer 1, not in this document's hook list.
- **Why it matters.** A platform team implementing the seven hooks from the TL;DR alone would build the wrong pre-merge hook and still think they had followed the spec.
- **Resolved in 1.14.4.** Updated TL;DR to match body: "(6) pre-merge → completion-report check (Full-mode PRs)". Also renamed (7) "observation-window start" to "Phase 8 observation reminder" to match the body's section header. Added a clarifying sentence that Change Manifest schema validation itself is separate concern owned by the automation contract's Layer 1 — so a reader following the TL;DR no longer thinks Hook 6 does schema validation.

### A6 — `docs/concurrent-changes.md:4`

- **TL;DR claim.** "*Three coordination patterns: **sequential**, **parallel with shared branch**, **dual-write bridge**.*"
- **Body reality.** §Coordination strategies has **four** entries with different names: Sequencing, Branch isolation + merge-time conflict resolution, Joint design + split implementation, Merge into one ticket.
- **Mismatch.** Count differs (3 vs 4). Only "sequential" / "sequencing" shares a name. "Dual-write bridge" does not appear as a body section at all (though related concepts exist inside breaking-change-framework.md Path B).
- **Why it matters.** The TL;DR names a categorization that doesn't exist in the repo, and hides the actual four-strategy taxonomy the doc enforces.
- **Resolved in 1.14.4.** Updated TL;DR to match body: "Four coordination strategies: sequencing, branch isolation + merge-time conflict resolution, joint design + split implementation, merge into one ticket." Dropped the non-existent "dual-write bridge" label (the dual-write *mechanism* is a breaking-change-framework Path B concern, not a coordination strategy in this doc).

### A7 — `docs/system-change-perspective.md:4` + cross-reference to `docs/surfaces.md`

- **TL;DR claim.** "*Lays out the six unified questions (what capability changed, which surfaces does it cross, where is each SoT, who are the consumers, what evidence proves it's correct, where is desync most likely).*"
- **Body cross-reference (line 9).** "*The canonical four-surface definitions, the extension mechanism, and the six unified analysis questions live in* `docs/surfaces.md`."
- **Target reality.** `docs/surfaces.md` contains (a) a "Six concerns" count — but those are **cross-cutting concerns**, not unified questions (line 200); and (b) a "60-second opener" with **five** questions, none of which match the TL;DR's six questions verbatim.
- **Mismatch.** Two-layer inconsistency: TL;DR says the six questions are here; body says they're in surfaces.md; surfaces.md has "six concerns" (different thing) + five unified-opener questions (different content). The named "six unified analysis questions" as a canonical list does not exist in the repo.
- **Why it matters.** A new reader arriving via this doc is promised a canonical six-question model and cannot locate it anywhere.
- **Resolved in 1.14.4.** Removed the "six unified questions" claim from both the TL;DR (line 4) and the body blockquote (line 8–9). TL;DR now points at "four surface-entry questions that map directly to the four core surfaces" (which the body does lay out, inside §Don't start by asking "whose layer?") and points readers at `surfaces.md §60-second opener` for the full five-question analysis checklist (which does exist in surfaces.md). Both "six unified questions" mentions are gone; the remaining references (four surface-entry questions + five-question §60-second opener) are now grounded in actual content.

### A8 — `docs/change-decomposition.md:4`

- **TL;DR claim.** "*Gives natural fracture lines (**SoT, surface, consumer pace, risk asymmetry**), merge signals, ...*"
- **Body reality.** §Natural fracture lines has **six** entries: SoT boundary, surface cadence differs, consumer cohort separation, asymmetric risk level, **different reversibility**, **delivery-sequencing constraint**.
- **Mismatch.** TL;DR names four fracture lines (the first four of six). The last two — `different reversibility` and `delivery-sequencing constraint` — are not referenced in the TL;DR.
- **Why it matters.** Under-reporting of fracture criteria. A reader deciding "should I split this change?" using the TL;DR misses two legitimate fracture-line triggers.
- **Resolved in 1.14.4.** TL;DR expanded to all six fracture lines (SoT boundary, surface cadence differs, consumer cohort separation, asymmetric risk level, different reversibility, delivery-sequencing constraint) plus the four merge signals (tightly-coupled atomicity, shared evidence, split would fabricate a scheduling dependency, changes are too small) that were previously unnamed in TL;DR. Reader following TL;DR now sees the full decomposition decision surface.

---

## (b) Legitimate two-level (no action)

These files have summary + per-case structure where the summary compresses the body without contradiction. The two levels serve different reader needs (quick scan vs full rule). Drift risk exists in principle but is bounded by small file sizes and stable content.

| File | Summary shape | Per-case shape | Consistency status |
|---|---|---|---|
| `docs/rollback-asymmetry.md` | TL;DR names Mode 1 / 2 / 3 with capsule descriptions | §The three rollback modes detail each mode | TL;DR and body match verbatim on mode names, characteristics, and core preconditions |
| `docs/ai-project-memory.md` | TL;DR describes 3 tiers | §Three-tier memory model (Session / Project / Organizational) with per-tier structure | Internally consistent |
| `docs/surfaces.md` | Intro names 4 core surfaces + extension surfaces | §The four core surfaces + §Composable extension surfaces | Consistent; no count drift (the "six cross-cutting concerns" count at line 200 matches `docs/cross-cutting-concerns.md`) |
| `docs/multi-agent-handoff.md` | TL;DR names Planner / Implementer / Reviewer | §Three canonical roles with per-role detail | Role names and responsibilities align across TL;DR, role sections, and tool-permission matrix |
| `docs/phase-gate-discipline.md` | Six-rule introduction | Rules 1 through 6 sections + Rule 5a insert | Rules all present; Rule 5a's Ceremony scaling (Zero / Lean / Full) matches its summary. **One broken reference** (see §Other drift below) — not a summary-vs-per-case issue |
| `docs/cross-change-knowledge.md` | TL;DR describes CCKN model | §What a CCKN is / §When to query / §Ceremony scaling | Consistent **after 1.14.0–1.14.3 cleanup cycle**; was the driver for this audit |
| `docs/principles.md` | TL;DR "11 non-negotiable rules" | Principle 1 through 11 | 11 principles present, count matches |
| `docs/team-org-disciplines.md` | TL;DR names consumer registry, contract catalog, deprecation queue, roadmap SoT, handoff, ownership | §Four organization-level assets + §Cross-team handoff + §Ownership boundaries | TL;DR lists topics covered (not a count claim); body organizes them as "four assets + other sections" |
| `docs/runtime-hook-contract.md` | TL;DR "four hook categories (phase-gate / evidence / drift / completion-audit)" | §Four hook categories with A / B / C / D | Category names and count both match |
| `docs/adoption-anti-metrics.md` | No TL;DR | Seven anti-metrics numbered 1–7 | No summary claim to drift against |
| `docs/strategic-artifacts.md` | TL;DR describes `strategic_parent` anchor purpose | §The field section | No count claim; narrative-level description matches body |
| `docs/glossary.md` | No TL;DR; entry-per-term | Term entries alphabetical | No summary claim to drift against. CCKN entry verified during the 1.14.0–1.14.3 cycle |
| `docs/automation-contract.md` | TL;DR frames contract role | §Four automation tiers (L0–L3) + §Three mandatory checking tiers + §Evidence tier | Two different "tier" concepts (adoption L0–L3 vs checking Layer 1–3 + Evidence). Both are labeled "tier" which may confuse readers but each is internally consistent |
| `docs/automation-contract-algorithm.md` | TL;DR references three-layer algorithm | §Layer 1 / 2 / 3 sections | Consistent with §Three mandatory checking tiers in `automation-contract.md` |
| `schemas/change-manifest.schema.yaml` | Description block per field | Per-field structure | Descriptions act as per-field summaries; no top-level summary to drift against |

---

## (c) Boundary calls

These are summary-vs-per-case gaps where "drift" depends on how strictly the summary is read. Flagged for visibility; no action recommended unless the summary is being rewritten anyway.

### C1 — `docs/breaking-change-framework.md` — L4 Path C coupling

- **TL;DR claim.** "*three standard migration paths (gray rollout / parallel switch / deprecation cycle + rename-and-coexist for L4).*"
- **Body.** Step 3 decision tree handles L4 inline with "new name + coexistence + old name kept + marked deprecated"; §Path C is titled "Deprecation lifecycle (for L3 and L4)" but its Stage 1–4 doesn't explicitly reinforce the **rename** requirement for L4.
- **Call.** A reader following only Path C could complete a deprecation cycle without explicitly renaming for L4 — the decision tree makes rename mandatory, Path C's detail doesn't reinforce it. Minor coupling risk, but both texts are present; a careful reader assembles the combined rule.

### C2 — `docs/cross-cutting-concerns.md:4` — Build-time risk category count

- **TL;DR claim.** Build-time risk covers "*codegen drift, code shrinker / name mangler classes of toolchains, AOT-compile runtime families, asset pipeline, determinism variance across platforms / hashes / locales / GPU vendors.*" — five named classes.
- **Body reality.** §Common risk categories table has **eight** rows: Codegen drift, Minification / obfuscation, Shrinking / tree-shaking, AOT compile, Asset pipeline, Build-time injection, Dependency version resolution, Platform / architecture differences.
- **Call.** TL;DR names 5; body has 8. The 3 un-named ones in TL;DR are "Shrinking / tree-shaking" (arguably covered under TL;DR's "code shrinker"), "Build-time injection", and "Dependency version resolution" — the latter two are genuinely missing from TL;DR. Closer to real drift than a pure compression, but the TL;DR's prose is phrased as examples ("...") rather than an exhaustive list.

### C3 — `docs/ai-operating-contract.md:4` — §2a and §11 not surfaced in TL;DR

- **TL;DR claim.** "*Covers four categories the human contract already implies plus four AI-specific ones: honest uncertainty reporting, scope discipline with explicit discovery-loop escalation, evidence quality, context hygiene, active escalation triggers, stop conditions, communication style, code conduct, a non-fabrication list, and a pre-delivery self-check.*"
- **Body reality.** Sections 1, 2a, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 — **11 sections** (including the 2a insertion and the later-added §11 Action continuity).
- **Call.** §2a (Reference-existence verification) and §11 (Action continuity — narration is not action) are both substantive normative sections added after the original TL;DR (likely 1.7.3 and 1.10.0 respectively) and are not reflected in the TL;DR. The "four + four = eight categories" framing is also numerically off (11 actual). Reading the TL;DR as a table of contents misses two rules.

### C4 — `docs/post-delivery-observation.md:4` — four loop points vs timeline structure

- **TL;DR claim.** "*four loop points: (1) metric & alert watch ... (2) post-delivery evidence capture ... (3) learning backflow ... (4) closeout.*" Also names specific artifacts: "*first-user-touched timestamp, error budget burn rate.*"
- **Body reality.** Doc uses a timeline structure (§T+24h / §T+72h / §T+7d) + §Feedback loop + §Exit conditions. The four "loop points" can be mapped to sections but the doc is not organized around them. The observation template doesn't require "first-user-touched timestamp" or "error budget burn rate" specifically.
- **Call.** Content overlap exists, but the TL;DR's framing doesn't match the doc's organizational structure. A reader using the TL;DR as a table of contents will not find sections named "metric & alert watch" or "closeout."

### C5 — `docs/playtest-discipline.md:4` — "Three failure modes" not explicitly sectioned

- **TL;DR claim.** "*Three failure modes it prevents: sample-of-one, unstructured ratings, no baseline.*"
- **Body reality.** Doc has §Scoring rubric → Rubric anti-patterns, §Evidence requirements → Anti-patterns, but no section titled "Three failure modes". The three failure modes appear scattered across anti-pattern lists within axes.
- **Call.** Claims are covered but not as a named three-item section. Low-severity framing gap.

### C6 — `docs/security-supply-chain-disciplines.md:4` — TL;DR 6 items vs body 5 steps

- **TL;DR claim.** "*Covers surface-first threat modeling, supply-chain as uncontrolled interface, dependency SoT, secret lifecycle, compliance integration, and incident response.*" — six topics.
- **Body reality.** §Step 1 through §Step 5 — **five** steps. "Dependency SoT" appears as a sub-section within Step 2 ("Supply chain = uncontrolled interface"), not as its own step.
- **Call.** Same content covered, but the TL;DR treats "dependency SoT" as a peer item while the body nests it. Not strictly drift; the TL;DR enumeration sells a six-step model the body doesn't have.

---

## Other drift (not summary-vs-per-case, but observed during the sweep)

- **`docs/phase-gate-discipline.md:95`** — Rule 5a references `templates/lean-spec-template.md`. Actual file location: `skills/engineering-workflow/templates/lean-spec-template.md`. The current path is broken for both reading conventions (relative-to-this-file → `docs/templates/...` doesn't exist; repo-root → `templates/` also doesn't have this file). Not a summary-vs-per-case issue but a real broken link.

---

## What to do with this registry

Per the audit rule agreed at the start of the sweep:

- **audit is audit, not patch.** This file does not fix anything; producing it is the deliverable.
- **(a) findings** are candidates for a later patch release. Each should be evaluated individually — some may be best fixed by rewriting the TL;DR to match the body (the simpler direction), others by adding the missing content to the body.
- **(b) findings** are noted as "safe"; no action.
- **(c) findings** are noted as "watch"; if the summary is rewritten for other reasons, bring it into line; otherwise leave.
- **Broken-reference finding** (phase-gate-discipline.md:95) is a separate drift class; it can be folded into a patch that addresses any of the above or handled independently.

Any future release that touches a file with a finding here should either:

1. Fix the finding as part of that release's scope, or
2. Explicitly acknowledge the finding in the release's ROADMAP Phase log as "still-open."

Either is acceptable; silent re-ship without addressing a known finding is not.

---

## Files audited

36 files read. The checklist below records coverage so a future sweep can spot-check rather than re-read the entire set.

**Found drift (a) or boundary (c):** `cross-cutting-concerns.md`, `source-of-truth-patterns.md`, `implementation-disciplines.md`, `user-surface-disciplines.md`, `adoption-strategy.md`, `ci-cd-integration-hooks.md`, `concurrent-changes.md`, `system-change-perspective.md`, `change-decomposition.md`, `breaking-change-framework.md`, `ai-operating-contract.md`, `post-delivery-observation.md`, `playtest-discipline.md`, `security-supply-chain-disciplines.md`.

**Verified consistent (b):** `rollback-asymmetry.md`, `ai-project-memory.md`, `surfaces.md`, `multi-agent-handoff.md`, `phase-gate-discipline.md` (with one broken link noted), `cross-change-knowledge.md`, `principles.md`, `team-org-disciplines.md`, `runtime-hook-contract.md`, `adoption-anti-metrics.md`, `strategic-artifacts.md`, `glossary.md`, `automation-contract.md`, `automation-contract-algorithm.md`, `runtime-hooks-in-practice.md`, `change-manifest-spec.md`.

**Skipped as reader-facing intro (summary drift expected):** `docs/onboarding/if-you-only-read-one-page.md`, `docs/onboarding/orientation.md`, `docs/onboarding/quick-start.md`.

**Skipped as template / data file:** `docs/stack-bridge-template.md`, `docs/bridges-local-deviations-template.md`, all `docs/*-stack-bridge.md`, all `docs/*-surface-map.yaml`, `docs/diagrams.md`, `docs/product-engineering-operating-system.md` (very short, frame-setting only).

**Schema audited:** `schemas/change-manifest.schema.yaml` — per-field descriptions; no top-level summary claim.

---

## Next sweep triggers

Re-run this audit when:

1. A new normative doc is added to `docs/` with a TL;DR + per-case structure.
2. An existing normative doc's per-case list is extended (new case added) — the TL;DR likely needs the same update.
3. Any release cycle opens ≥ 2 patches on the same normative file (pattern signal that summary-vs-per-case drift is at play).

Audit cost: ~2–3 hours for the full 36-file sweep. Re-run after significant normative churn, not on a fixed cadence.
