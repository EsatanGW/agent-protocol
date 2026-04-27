# Specialist Sub-Agent Roles — Starter Registry

> **Status:** non-normative reference. The normative contract for specialist sub-agent roles lives in [`docs/multi-agent-handoff.md`](../../docs/multi-agent-handoff.md) §Composable specialist sub-agent roles. This file is a *starter registry* — projects may copy these entries into their own bridge / project-local registry, modify them, or replace them entirely.

---

## What this file is

A registry of named specialist sub-agent roles a project can fan out to from a canonical role (Planner / Implementer / Reviewer). Each entry pins:

- **Name** — runtime-neutral identifier; no `$`-syntax.
- **Parent canonical role** — exactly one of Planner / Implementer / Reviewer.
- **Pattern** — which Pattern from [`role-composition-patterns.md`](role-composition-patterns.md) this specialist instantiates.
- **Capability envelope** — must inherit from the parent role's row in [`docs/multi-agent-handoff.md`](../../docs/multi-agent-handoff.md) §Tool-permission matrix; cannot exceed it.
- **Output slot** — where the specialist's findings land (`review_notes`, `implementation_notes`, `parallel_groups[*]`, CCKN reference).
- **Anti-collusion note** — identity constraints specific to this specialist.

A specialist that does not satisfy every row above is not a specialist; see [`docs/multi-agent-handoff.md`](../../docs/multi-agent-handoff.md) §Composable specialist sub-agent roles for the contract escapes registration prevents.

---

## Entry: `architect`

**Parent canonical role:** Planner
**Pattern:** Pattern 2 (code-explorer sub-agent) or Pattern 5 (surface-parallel investigators) under fan-out.
**Capability envelope:** file read, code search, network fetch (read-only). Inherits from Planner row in [`docs/multi-agent-handoff.md`](../../docs/multi-agent-handoff.md) §Tool-permission matrix; no Edit / Write / state-changing shell.
**Output slot:** structured draft returned to the Planner; the Planner synthesizes into `sot_map`, `surfaces_touched`, `consumers`. Recorded in `parallel_groups[*]` if fan-out per Pattern 5; in `implementation_notes[*].type: discovery` if the architect's investigation produced a fact the Planner is encoding mid-Phase 2.
**Anti-collusion:** identity must differ from the Planner, the Implementer-to-be, and the Reviewer-to-be. A repeated `architect` invocation across phases must rotate identity if the runtime supports it; otherwise the Pattern 2 invariant is preserved by clean context.

**When to use:** the change touches an unfamiliar codebase region or an SoT classification is non-obvious (e.g. "is this Pattern 4 Contract-Defined or Pattern 8 Dual-Representation?"). The architect produces a structured map; the Planner decides what to encode. Do not register an architect to "speed up" simple plans — that is ceremony.

**When not to use:** Lean-mode changes, single-surface bug fixes, plans whose SoT pattern is obvious to the Planner. Per [`role-composition-patterns.md`](role-composition-patterns.md) §When role composition is appropriate, composition is never a Lean-mode optimization.

---

## Entry: `security-reviewer`

**Parent canonical role:** Reviewer
**Pattern:** Pattern 6 (specialized audit fan-out) — typically as one of several parallel audit sub-agents under the Reviewer in Phase 5.
**Capability envelope:** file read, code search, verification-only shell (run security tests, open SAST artifacts, query secrets-store metadata read-only), network fetch. No Edit / Write / state-changing shell. Inherits from Reviewer row in [`docs/multi-agent-handoff.md`](../../docs/multi-agent-handoff.md) §Tool-permission matrix.
**Output slot:** findings returned to the Reviewer with severity classification; the Reviewer decides whether each becomes a `review_notes[*]` entry. Fan-out itself is recorded in `parallel_groups[*]` per the schema's audit trail. The security-reviewer never writes `review_notes` directly.
**Anti-collusion:** identity must differ from the Implementer (whose diff is being audited), the Reviewer (whose audit this contributes to), and every other audit sub-agent in the same fan-out. Sharing identity with the Implementer collapses the audit into Anti-rationalization Rule 4 (editing through the back door) at the structural level.

**When to use:** changes touching authentication, authorization, PII, secret material, regulatory compliance, or any surface whose `cross_cutting.security.impact` is medium / high. The security-reviewer audits the threat-model diff, validates the SAST artifact, samples secret-handling paths, and reports findings.

**When not to use:** changes whose `cross_cutting.security.impact` is `none` or `low` and which do not touch any auth / PII / secret path. A security-reviewer fan-out for a UI copy change is ceremony; the Reviewer's normal cross-cutting check covers the surface.

---

## Entry: `performance-reviewer`

**Parent canonical role:** Reviewer
**Pattern:** Pattern 6 (specialized audit fan-out) — as one of the parallel audits under the Reviewer.
**Capability envelope:** file read, code search, verification-only shell (run benchmarks, open profiler output, query metric dashboards read-only), network fetch. No Edit / Write / state-changing shell.
**Output slot:** findings returned to the Reviewer (typical: budget-violation reports, regression deltas, memory / latency observations). The Reviewer synthesizes into `review_notes[*]` if material; into `residual_risk` if the finding is a follow-up rather than a blocker. Fan-out recorded in `parallel_groups[*]`.
**Anti-collusion:** identity must differ from the Implementer (especially when the implementer wrote the perf benchmark), the Reviewer, and every other audit sub-agent.

**When to use:** changes whose `cross_cutting.performance.impact` is medium / high, changes that declare an explicit `performance.budget`, changes whose surfaces include the performance-budget extension surface from [`docs/surfaces.md`](../../docs/surfaces.md). The performance-reviewer validates that the benchmark is honest (production-shaped corpus, not a microbenchmark), the budget is real (not a number invented to pass), and the rollback plan handles a perf regression discovered post-deploy.

**When not to use:** changes with no perf surface and no declared budget. A performance-reviewer fan-out without a budget to compare against is unscoped; the Reviewer should require the Planner to declare a budget first, then fan out.

---

## How to add a new specialist

To register a new specialist for your project:

1. **Confirm recurrence.** Has this specialist shape appeared in ≥ 3 recent changes? If not, use Pattern 1 / 2 / 4 / 6 ad-hoc — registration without recurrence is ceremony.
2. **Identify parent canonical role.** A specialist with two parent roles is two specialists; pick one.
3. **Pick a pattern from [`role-composition-patterns.md`](role-composition-patterns.md).** If none of Patterns 1, 2, 4, 5, 6 fits, the proposal is probably a hidden canonical role — escalate to a methodology-level discussion before registering.
4. **Fill the entry template below.** Add it to your bridge file (`docs/bridges/<stack>-stack-bridge.md`) or your project-local registry.
5. **Confirm registry size.** A registry past ~6 specialists is a sprawl signal; consolidate before adding more.

### Entry template

```markdown
## Entry: `<specialist-name>`

**Parent canonical role:** <Planner | Implementer | Reviewer>
**Pattern:** Pattern <N> (<short pattern name>) — see role-composition-patterns.md
**Capability envelope:** <list capabilities; must be ⊆ parent's row in tool-permission matrix>
**Output slot:** <where findings land; do not name a new manifest field>
**Anti-collusion:** <identity constraints specific to this specialist>

**When to use:** <recurrence-confirmed scenario>
**When not to use:** <Lean-mode / single-surface / obvious cases>
```

---

## Anti-patterns specific to specialist registries

- **Per-change registration.** A specialist that exists only for one change is unauditable across changes and provides no compounding value; either drop the registration and use ad-hoc Pattern 1 / 2 / 4 / 6, or wait until recurrence is confirmed.
- **Two parents.** A specialist that is "Planner-or-Reviewer depending on phase" is two specialists with the same name — register them as two entries.
- **Capability inflation.** A specialist envelope that exceeds the parent's tool-permission row is a permission escalation, not a specialist. The contract escape lives in the envelope row.
- **Output slot drift.** A specialist that writes manifest fields directly has escaped composition — the canonical role must always perform synthesis. Output slot rows that name `review_notes[*]` directly (rather than "findings the Reviewer synthesizes into `review_notes`") are a misregistered specialist.
- **Sprawl.** A registry past ~6 specialists fragments the audit surface. Consolidate (e.g. `security-reviewer` covers what `pii-reviewer` and `auth-reviewer` would otherwise split) before adding more.
- **Vendor names in entries.** Specialist names must be runtime-neutral; do not embed vendor / model / framework names in the registered identifier.

---

## Relationship to other documents

- [`docs/multi-agent-handoff.md`](../../docs/multi-agent-handoff.md) §Composable specialist sub-agent roles — normative contract for what a specialist is and is not.
- [`role-composition-patterns.md`](role-composition-patterns.md) — Patterns 1–7 the registered specialists instantiate.
- [`../../skills/engineering-workflow/references/parallelization-patterns.md`](../../skills/engineering-workflow/references/parallelization-patterns.md) — execution discipline for Patterns 5 / 6 fan-outs (cache-window, context-pack, cross-cutting gap check).
- [`../../docs/surfaces.md`](../../docs/surfaces.md) §Composable extension surfaces — structural model this registry mirrors. Specialists are to roles what extension surfaces are to surfaces: a registered, contract-bound extension that does not change the canonical core.
- [`../../docs/glossary.md`](../../docs/glossary.md) — defines "Specialist sub-agent role".
