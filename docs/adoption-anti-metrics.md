# Adoption anti-metrics

> **This document is non-normative.**
> Nothing in it is a gate. Every item is a *diagnostic aid* for a team
> that wants to tell the difference between "applying the methodology"
> and "going through the motions." Operationalizing these as CI failures
> would itself be a ceremonial move — the measurement would become the
> target, the target would stop measuring discipline, and the team
> would land in exactly the failure mode this document is about.

---

## Why this document exists

The methodology gives a team a lot of artifacts: manifests, evidence
plans, review notes, phase gates, surfaces, SoT maps. A team that
fills every field with the same three symbols looks **identical at the
CI layer** to a team that actually thinks about the change. CI enforces
*syntactic* conformance; the cost of syntactic conformance is low and
drops to zero once a template exists. If the methodology is going to
pay off, someone has to be able to tell — from the artifacts alone —
whether the team is thinking or checking boxes.

Anti-metrics are the "smell signals" of ceremonial adoption. Each one:

- describes an observable pattern in the artifacts themselves,
- explains **why the pattern shows up** (the root incentive the team is
  responding to), and
- pairs with a **counter-signal** — a pattern a thinking team produces
  instead.

Fix the incentive, not the symptom.

---

## How to use this list

- **Not as a CI check.** A gate that fails on "too many rollback mode 1
  declarations" would immediately be gamed — teams would flip rollback
  mode by coin toss to stay green. Gating an anti-metric creates a new
  Goodhart target.
- **As a review conversation.** Surface one anti-metric in a
  retrospective; ask "why does this pattern show up here?"; decide
  whether the root incentive needs changing.
- **As an adopter's self-check.** Teams introducing the methodology can
  read their own recent manifests against this list and flag for
  themselves, before external review is involved.
- **As an input to a human-run spot-check.** If an external auditor /
  staff engineer / tech-lead wants to sample whether discipline is
  genuine, these are the patterns to look for first.

Detection sketches are given where they are tractable (they are mostly
one-liner `yq` / `grep` / histograms over the manifest corpus). Keep
them as **queries a human runs to inform a conversation**, not as jobs
that block merges.

---

## Anti-metrics

### 1. Rollback mode is always 1

**Signal.** Every manifest in the corpus declares
`rollback.overall_mode: 1`. No mode 2, no mode 3 — ever.

**Why this happens.** Mode 2 and mode 3 require real thought about
compensation, forward-fix, side-effect externality. Mode 1 is the
"revertable" default, and it is the least uncomfortable answer to a
question the author does not want to think about. The review either
does not catch it or does not push back.

**Counter-signal.** Rollback-mode distribution in the corpus tracks the
breaking-change distribution. A team that ships L2–L3 breaking changes
and no compensation-mode rollbacks is either extraordinarily lucky or
not being honest.

**Root cause to fix.** The Planner role has no prompt that
operationalizes `docs/rollback-asymmetry.md`. Add it, or pair the
author with the relevant rollback examples in the worked-example set
before they declare mode.

**Detection sketch.**
`yq '.rollback.overall_mode' change-manifest*.yaml | sort | uniq -c`
over the last N manifests and compare against
`yq '.breaking_change.level'` from the same set.

---

### 2. `surfaces_touched` is always 4 of 4 (or always 1 of 4)

**Signal (a).** Every manifest marks all four canonical surfaces as
touched, even when the change is a one-line copy edit.

**Signal (b).** Every manifest marks exactly one surface, even when the
change visibly crosses user-visible UI and a migration.

**Why this happens.**
- (a) is cargo-culting: "more surfaces = more thorough = safer review."
- (b) is scope-minimizing: "I only changed the button label, therefore
  only the user surface."

Both defeat surface-first analysis — the discipline that exists because
the real cost of a change is in the surfaces the author failed to
notice.

**Counter-signal.** A histogram of `surfaces_touched.length` across the
corpus has a long tail — many changes touch 1–2 surfaces, fewer touch
3, a few touch 4. Most changes are asymmetric across surfaces, and
that asymmetry is visible in the artifacts.

**Root cause to fix.** Most likely, `docs/surfaces.md` is not being
read — the author is filling `surfaces_touched` from a template, not
from a decision. Add a "what surfaces did you touch, and why those?"
question to the Planner's working prompt; reject manifests where
`role: primary` doesn't match the files in the diff.

---

### 3. Evidence paths all point at the same artifact

**Signal.** Across multiple changes, `evidence_plan[*].artifact_location`
is always `CI/LAST_RUN.txt`, or always `docs/evidence.md`, or always
the same screenshot path.

**Why this happens.** Someone wrote a template where the evidence path
is a string constant, and nobody pushed back when subsequent manifests
re-used it without updating. The Reviewer looked at the path, saw a
file existed, and signed off — the check "does the artifact
substantiate *this specific claim*?" was skipped.

**Counter-signal.** Evidence paths are distinct per change, and
substantiate the specific surface / invariant they claim to. Paths may
share a **directory** (e.g. `evidence/2026-04/`), but the file names
are change-specific.

**Root cause to fix.** Reviewer prompt does not explicitly require
**opening** the evidence artifact before marking `pass`. Every `pass`
in `review_notes` should cite the artifact it read. "Looks good" is
not a finding.

**Detection sketch.**
`yq -r '.evidence_plan[].artifact_location' change-manifest*.yaml | sort | uniq -c`
over recent changes. If one path has a count > 1, open both manifests
and compare claims.

---

### 4. Review notes are always `LGTM` (or always `pass` with no citation)

**Signal.** `review_notes[*].finding` is always `pass`, and the
`detail` field is either empty, `LGTM`, `looks good`, or a single
sentence that does not cite an artifact.

**Why this happens.** The Reviewer read the diff, formed a gestalt
impression, and checked the box. The prompt did not force them to
**read the evidence and cite it**. This is how review becomes
rubber-stamping.

**Counter-signal.** Every `pass` in `review_notes` cites the artifact
that substantiates it. A corpus has a distribution of findings —
`pass`, `pass_with_followup`, occasional `fail` and `needs_human_decision`.
A Reviewer who always passes provides zero audit value.

**Root cause to fix.** Reviewer role prompt (or `.cursor/rules/reviewer.mdc`,
`reference-implementations/roles/reviewer.md`) is not being read at
session start, or the runtime's tool surface allows the Reviewer to
edit, which destroys the audit property before review even begins.

**Detection sketch.**
`yq -r '.review_notes[].finding' change-manifest*.yaml | sort | uniq -c`
— the ratio of `pass` to everything else is the signal. 100% `pass`
across 20+ changes is an adoption smell.

---

### 5. Phase gates are checked off faster than commits land

**Signal.** The phase log shows P0 → P1 → P2 → P3 → P4 → P5 → P6
transitions all happening within a single commit, or within minutes of
each other, across the entire sprint.

**Why this happens.** The phase gates were filled in retroactively,
after the work was already done, to satisfy a template requirement.
The discipline they exist to enforce — "stop at each gate, verify
evidence, then move forward" — was not applied.

**Counter-signal.** Phase transitions are roughly commensurate with
the work. A P1 that shipped 500 lines of new code and evidence should
not transition in the same commit as a 3-line P0 ROADMAP entry.

**Root cause to fix.** The ROADMAP phase table is being used as a
post-hoc summary, not as a working checklist. Move the phase
transition to a **separate commit per phase** — if nothing else, it
makes the gap visible in `git log`.

**Detection sketch.** Inspect `git log --oneline <roadmap-entry-range>`;
phases should map to distinct commits. If one commit touches six
phase-table rows simultaneously, discipline was probably not applied
per-phase.

---

### 6. Manifests are copy-pasted across unrelated changes

**Signal.** Two manifests from different changes have near-identical
field content — same `sot_map`, same `evidence_plan.categories`, same
`cross_cutting.security` answers, only the change title differs.

**Why this happens.** The template was copied from a previous change
and adapted only where forced. Fields that the author doesn't
understand (SoT pattern, cross-cutting security) got left at whatever
the previous change said.

**Counter-signal.** Manifests vary across changes — because the
changes vary. Two user-surface-only tweaks should have similar shape;
a user-surface tweak and a schema migration should not.

**Root cause to fix.** The team is using the manifest as paperwork, not
as thinking. Require that any manifest adapted from a previous change
explain **in `implementation_notes`** which fields were kept and which
were re-evaluated. A manifest with no `implementation_notes`
`type: assumption_validated` / `assumption_invalidated` entries across
20 changes is a red flag.

---

### 7. `cross_cutting.*` is always the same boilerplate answer

**Signal.** Every manifest's `cross_cutting.security`,
`cross_cutting.performance`, `cross_cutting.observability` has the same
text across all changes — often "no impact" or "N/A".

**Why this happens.** The author treats cross-cutting concerns as
boilerplate to dismiss, not as a real review. The Planner prompt did
not force per-change reasoning; the Reviewer did not push back.

**Counter-signal.** A change that touches authentication declares
`security.supply_chain_review_needed: true` and cites why. A change
that adds a new ingestion path declares `performance.budget_impact`
with a target. Most changes have **some** cross-cutting answer that is
not "no impact."

**Root cause to fix.** `docs/cross-cutting-concerns.md` is not a
checklist the author reads against the diff. Either require the author
to open it, or bind the cross-cutting fields to the surface types — if
`user_surface` is primary, `performance` cannot be blanket "no impact."

---

## What is deliberately NOT on this list

- **Manifest count per change.** Higher manifest count ≠ better
  discipline. A one-line typo does not need a manifest.
- **Review-note length.** Verbose review notes can be just as
  ceremonial as terse ones. What matters is whether findings cite
  artifacts.
- **Template coverage.** "Did every field get filled?" is already
  covered by schema validation; it does not measure whether the
  *values* mean anything.

These omissions are intentional. The goal of this document is to make
adoption-honesty legible, not to add more fields to the template.

---

## Relationship to other documents

- `docs/automation-contract.md` §Anti-patterns — lists automation-layer
  ceremonial failure modes (over-automation, silent skipping, false-positive
  fatigue, covert bypass). This document is the **artifact-layer**
  counterpart: what the output looks like when the human process is
  going through the motions.
- `docs/operational-disciplines.md` — evidence / rollback / handoff
  quality floors. The anti-metrics here detect violations of those
  floors that schema validation cannot catch.
- `docs/adoption-strategy.md` — counter-metric monitoring for
  `[skip ci]` and `--no-verify` bypass rates; that is also a
  ceremonial-adoption signal, but at the automation bypass layer.
- `docs/ai-operating-contract.md` §5 — AI self-waivers are a specific
  anti-pattern; this document generalizes to the human-process case
  around the AI.
