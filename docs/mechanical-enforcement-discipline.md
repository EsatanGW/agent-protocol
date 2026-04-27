# Mechanical Enforcement Discipline

> **English TL;DR**
> Three axes of mechanical enforcement that a methodology-conformant repository should cover, one way or another: **architecture invariants** (dependency direction, layer boundaries, file-size limits), **taste invariants** (log format, naming, comment style, structural conventions), and **documentation freshness** (a SoT edit comes with the doc edit; a CCKN does not silently expire). Each axis maps onto existing capability contracts in this repository (`runtime-hook-contract.md`, `automation-contract.md`) — the discipline does not introduce a new enforcement engine, it specifies *which class of check belongs where* so that the three axes are covered without overlap or gap.

---

## Why this discipline exists

A methodology that depends on agents and humans remembering rules at the right moment fails the moment attention wanders. The repair is not to remind harder — it is to lift the rule into a **mechanical check** that fires regardless of attention. Mechanical enforcement is the cheapest reliable form of governance: a check that runs in CI / pre-commit / on-stop has uniform coverage, no fatigue, and produces durable evidence (the check log).

But mechanical enforcement is not free. A check that fires too often, too verbosely, or on too many false positives turns into noise (`docs/runtime-hook-contract.md` §Anti-patterns *Hook sprawl*; `docs/adoption-anti-metrics.md` *Ceremony accumulation*). A check that fires on the wrong axis (a "taste" rule masquerading as an "architecture" rule) confuses Reviewer audit. The discipline therefore answers two questions:

1. **What classes of rule should a project enforce mechanically?** (Three axes, below.)
2. **Where does each class of check belong?** (Mapping to existing capability contracts, below.)

It does *not* prescribe specific lint rules, test frameworks, or CI tools. The methodology is tool-agnostic; the runtime bridge picks the implementation.

---

## The three axes

### Axis 1 — Architecture invariants

**What it covers.** Rules that bind the *shape* of the codebase: which package may depend on which, which layer is allowed to import which, what the maximum size of a single file / module / function is, where boundary types are allowed to leak.

**Examples.**

- *Dependency direction.* A `domain/` package must not import from `infrastructure/`. A `service/` package must not import from `ui/`.
- *Layer boundaries.* The dependency graph is acyclic; no two packages mutually import.
- *File / module size.* No source file exceeds N lines (project-specific, but the ceiling exists).
- *Public-API surface.* No symbol leaves the `internal/` package via re-export.
- *SoT pattern 4a (Pipeline-Order Contract) sequence.* Pipeline stages execute in the order declared in the contract file; no reordering at runtime.

**Why mechanical, not human.** Architecture violations compound silently. A single off-direction import does not break a build, but ten of them turn a layered architecture into a ball of mud. Catching the first import at the moment it lands is at least 100× cheaper than refactoring ten.

**Where it belongs.**

| Capability contract | Mode | Typical trigger |
|---|---|---|
| [`docs/automation-contract.md`](automation-contract.md) Tier 1 (manifest-shape) | Validator | Pre-commit; CI on every push |
| [`docs/runtime-hook-contract.md`](runtime-hook-contract.md) Category C (drift) | Hook | Post-tool-use after edits |
| [`docs/ci-cd-integration-hooks.md`](ci-cd-integration-hooks.md) | CI gate | PR open / push |

Architecture rules are *blocking* by default — exit 1 (block) per the runtime hook contract. A repository that downgrades architecture rules to warn-only is signalling that the rule is aspirational, not invariant.

### Axis 2 — Taste invariants

**What it covers.** Rules that bind the *style* of the codebase: log format, naming, comment style, formatting, structural conventions that do not change behaviour but that a future reader (human or agent) relies on for predictability.

**Examples.**

- *Log format.* All structured log entries include `change_id`, `surface`, and `correlation_id` fields.
- *Identifier conventions.* Public types use `PascalCase`; constants use `SCREAMING_SNAKE`; test files end with `_test.go` / `.test.ts` / `_spec.rb` per language convention.
- *Error wrapping convention.* Errors crossing a layer boundary are wrapped with the boundary's name (no raw infrastructure errors leaking into the domain layer's caller).
- *Comment minimalism.* Code comments follow the project's discipline (no narrative comments restating what well-named identifiers already say; comments justify *why*, never *what*).
- *Manifest-line discipline.* Every `evidence_plan[*]` row uses one of the canonical types from the schema enum, never a bespoke string.

**Why mechanical, not human.** Taste violations are easy to ignore individually and corrosive in aggregate. A reviewer who flags every log-format slip looks pedantic; a hook that flags it stays neutral. The discipline shifts the social cost from human-to-human to human-to-machine.

**Where it belongs.**

| Capability contract | Mode | Typical trigger |
|---|---|---|
| [`docs/runtime-hook-contract.md`](runtime-hook-contract.md) Category C (drift) | Hook | Post-tool-use after edits, exit 2 (warn) by default |
| [`docs/automation-contract.md`](automation-contract.md) Tier 2 (cross-reference) | Validator | Periodic / on-PR |
| Project-local linter / formatter | Pre-commit | Every commit |

Taste rules are *warn* by default — exit 2 — because a hard block on every formatting mismatch is friction without proportional gain. They escalate to *block* when the rule is structural (e.g. evidence type must be from the enum; a free-string is a manifest validity violation, not a taste violation).

### Axis 3 — Documentation freshness

**What it covers.** Rules that bind the *currency* of the repo's prose: a SoT change is paired with the doc edit that updates downstream consumers; a CCKN that has aged past its re-verification window is flagged for review; a deprecated path's removal date is honoured.

**Examples.**

- *Doc-refresh drift* (already canonical in [`docs/runtime-hook-contract.md`](runtime-hook-contract.md) §Category C). When a file declared in `sot_map[*].source` is edited, *some* documentation file must also be edited in the same diff.
- *CCKN expiry.* A CCKN whose `last_verified` field is more than 12 months old (per [`docs/ai-project-memory.md`](ai-project-memory.md) §CCKN staleness model) requires re-verification before further reference.
- *Deprecation timeline observance.* A deprecation declared in `breaking_change.deprecation_timeline` with `hard_cutoff < today` must either be removed or its timeline updated; it cannot silently linger.
- *ROADMAP synchronization.* A ROADMAP row claiming `phase: deliver` whose linked manifest is still in `phase: implement` is a freshness drift.
- *AGENTS.md / CLAUDE.md / GEMINI.md mirror parity.* Same-content rules in thin-bridge files must not drift from the canonical `docs/` source ([`AGENTS.md §File role map`](../AGENTS.md)).

**Why mechanical, not human.** Documentation freshness has the longest decay half-life of the three axes. By the time a human notices that the README is six versions out of date, the cost of bringing it current may exceed the cost of rewriting it. A mechanical check fires at the edit boundary — when bringing the doc current is still cheap.

**Where it belongs.**

| Capability contract | Mode | Typical trigger |
|---|---|---|
| [`docs/runtime-hook-contract.md`](runtime-hook-contract.md) Category C (drift) | Hook | Pre-commit; on-stop |
| [`docs/automation-contract.md`](automation-contract.md) Tier 3 (cross-doc consistency) | Validator | Scheduled (daily / weekly) |
| [`docs/ci-cd-integration-hooks.md`](ci-cd-integration-hooks.md) | CI gate | Periodic |

Documentation rules are *warn* by default; they escalate to *block* when the freshness gap is structural (e.g. a SoT edit with no doc change in the same diff is hard-blocked at pre-commit).

---

## How much enforcement is right

A repository can over-enforce as easily as it can under-enforce. The signals that you are over-enforcing:

- **Hook sprawl** ([`docs/runtime-hook-contract.md`](runtime-hook-contract.md) §Anti-patterns). Cumulative hook latency exceeds the 1-second-p95 budget.
- **Ceremony accumulation** ([`docs/adoption-anti-metrics.md`](adoption-anti-metrics.md)). The number of mandatory checks grows monotonically with no corresponding reduction in defect rate.
- **Reviewer fatigue.** Hook output is dismissed unread; the channel is no longer high-signal.
- **Bypass culture.** Engineers learn to land changes via shells / sessions / branches that skip the hooks.

The signals that you are under-enforcing:

- **Recurring same-shape failures** that a one-line check would have caught.
- **Reviewer effort going to mechanical issues.** Every review surfaces lint / format / doc-stale comments — those are not Reviewer's job.
- **Drift between SoT files and consumers** showing up in production. The doc-refresh drift is the canonical case.

The right answer is between these. Concretely:

- Cover all three axes with at least *one* check each — uniform coverage beats deep coverage on one axis with nothing on the others.
- Default architecture rules to *block*, taste / freshness rules to *warn*. Promote freshness to *block* only for structural cases (the SoT-with-no-doc edit case).
- Apply the back-pressure pattern ([`docs/runtime-hook-contract.md`](runtime-hook-contract.md) §Back-pressure pattern) to every Category C / D hook: silent on success, one line on failure.
- Re-evaluate the rule set every minor version: rules that have not fired in N versions either covered a now-extinct failure mode (delete) or are silently bypassed (investigate).

---

## Anti-patterns

- *Reverse-axis enforcement.* A taste rule treated as architecture (block on every log-format slip) erodes credibility; an architecture rule treated as taste (warn on a layer-boundary violation) becomes a leak. The axis dictates the default severity.
- *One check across all three axes.* A mega-check that "validates the codebase" answers nothing specific when it fails. Split by axis; each axis has its own rules with their own severities.
- *Documentation freshness covered only by humans.* "Reviewers will catch it" is the failure mode this axis exists to prevent. Reviewers catch *some* drift; the long tail goes uncaught for months.
- *Architecture rules with no test fixture.* An architecture rule expressed only as a hook is invisible at refactor time. Pair it with a structural test that runs in CI on every PR.
- *Taste rules expressed inconsistently across runtimes.* The same lint rule diverges between a pre-commit hook, a CI step, and an editor extension; the three contradict each other and the developer learns to ignore all of them. Single-source the rule set; reference it from each runtime.
- *Freshness rules without a "why this changed" path.* A doc-refresh hook that blocks the commit but does not explain *which* doc to update sends the developer to grep blindly. The hook's stderr must include the missing-doc target by path.

---

## Phase hookup

- **Phase 0 (Clarify).** When the change is mode-Lean or higher, confirm which axes the change is touching. A user-surface change touches mostly taste; a refactor touches mostly architecture; a SoT-renaming touches all three.
- **Phase 1 (Investigate).** The SoT map identifies which axis-1 (architecture) rules govern the SoTs in scope. Implementer surfaces this in the manifest's `implementation_notes[]` if a rule will need an exception (waiver).
- **Phase 4 (Implement).** Mechanical checks fire at edit boundary; the back-pressure-shaped output keeps signal high. Implementer addresses each surfaced finding before the next turn.
- **Phase 5 (Review).** Reviewer's audit explicitly checks that all three axes' rules ran (and produced expected verdicts) for this change. A pass without any axis-3 (freshness) check having fired on a SoT-touching change is a Reviewer-side red flag.
- **Phase 7 (Deliver).** The completion report references the rule IDs that fired during the change; this is the audit trail per [`docs/automation-contract.md`](automation-contract.md).

---

## Relationship to other documents

- [`docs/runtime-hook-contract.md`](runtime-hook-contract.md) — the event-driven enforcement layer; this discipline names which axis each Category covers.
- [`docs/automation-contract.md`](automation-contract.md) + [`docs/automation-contract-algorithm.md`](automation-contract-algorithm.md) — the batch-validator layer; this discipline names which Tier each axis maps to.
- [`docs/ci-cd-integration-hooks.md`](ci-cd-integration-hooks.md) — the CI/CD layer; identical axis-to-mode mapping, different runtime.
- [`docs/adoption-anti-metrics.md`](adoption-anti-metrics.md) — the over-enforcement counter-pressure; Hook sprawl and Ceremony accumulation are the two anti-metrics this discipline most often risks tripping.
- [`docs/output-craft-discipline.md`](output-craft-discipline.md) — the output-side counterpart; mechanical-enforcement output is held to the same earn-its-place rule.
- [`docs/anti-entropy-discipline.md`](anti-entropy-discipline.md) — the time-axis counterpart; mechanical enforcement catches single-edit drift, anti-entropy catches accumulated drift across many edits.
