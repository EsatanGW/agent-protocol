# `QUALITY_SCORE.md` — Template

> **Status.** Non-normative example template. The `anti-entropy-discipline.md §Quality score (optional, non-mandatory)` section names this artefact's posture; this file is a fillable layout consumers can copy into their own `docs/QUALITY_SCORE.md`. The template is **not** a contract — teams may adapt the dimensions, the grade scale, and the cadence as their domain demands.

The template lives under `docs/examples/` so it does not become a normative requirement of the methodology — adoption is opt-in, recorded in the team's `adoption-strategy.md` entry.

---

## When to use this template

A consumer project benefits from a `QUALITY_SCORE.md` when:

- The team runs at autonomy ladder rung L2 or higher (per [`../autonomy-ladder-discipline.md`](../autonomy-ladder-discipline.md)) — agents are authoring most changes, and human review bandwidth is the throughput constraint.
- The codebase has at least three identifiable business domains; below three, gap-tracking is more naturally captured in a single phase-log.
- The team has adopted at least one weekly anti-entropy sweep (per [`../anti-entropy-discipline.md`](../anti-entropy-discipline.md)) — the quality score is the natural artefact such sweeps produce.

A team that does not satisfy these does not need the template; producing a `QUALITY_SCORE.md` without the operational rhythm to update it is ceremony.

---

## Template body (copy into `docs/QUALITY_SCORE.md`)

```markdown
# Quality Score

> Last sweep: <YYYY-MM-DD> · Next sweep: <YYYY-MM-DD>
>
> Per-domain × per-surface grading. Updated by the weekly anti-entropy sweep
> (see `docs/anti-entropy-discipline.md` §Sweeps). Each cell is graded on a
> three-tier scale (good / partial / weak). A weak cell is a candidate for
> the next refactor / hardening sprint.

## Grade legend

- **good** — meets the per-surface bar in `docs/cross-cutting-concerns.md`; no open gap-finding.
- **partial** — meets the bar in most cells of the surface; at least one open gap-finding.
- **weak** — does not meet the bar; at least three open gap-findings or one critical-severity finding.

Cells with no entry are out of scope for the domain (the domain does not touch that surface).

## Per-domain × per-surface grades

| Domain | User surface | System interface | Information surface | Operational surface | Last audited | Open gaps |
|---|---|---|---|---|---|---|
| <domain-1> | <good/partial/weak> | <good/partial/weak> | <good/partial/weak> | <good/partial/weak> | <YYYY-MM-DD> | <link-to-issue-list> |
| <domain-2> | … | … | … | … | … | … |
| <domain-3> | … | … | … | … | … | … |

## Open gap-findings

| ID | Domain | Surface | Severity | Opened | Owner | Description |
|---|---|---|---|---|---|---|
| <id> | <domain> | <surface> | <critical/high/medium/low> | <YYYY-MM-DD> | <role> | <one-line> |

## Recently closed gap-findings

| ID | Closed | Resolution |
|---|---|---|
| <id> | <YYYY-MM-DD> | <closing change-id or PR ref> |

## Trend

- Sweeps performed: <N> in the last 90 days.
- Average open-gap count: <N>.
- Average gap-resolution time: <N days>.
- Surfaces with consistent partial / weak grades over 4+ sweeps: <list>.
```

---

## How to fill it (procedure)

1. **Enumerate domains.** A domain is a coherent slice of business logic — typically named by user-facing function ("billing", "auth", "notifications") rather than by technical layer.
2. **Enumerate surfaces.** Use the four canonical surfaces from [`../surfaces.md`](../surfaces.md). Domains that do not touch a surface leave the cell blank.
3. **Run the sweep.** A sweep reads the cross-cutting checklist in [`../cross-cutting-concerns.md`](../cross-cutting-concerns.md) for each (domain × surface) cell and counts open findings. The grade is computed mechanically from the count.
4. **Open gap-findings as issues.** Each finding is a separate trackable issue, owned by a role (typically the domain's tech lead or a security/performance specialist). The issue's link goes in the cell's `Open gaps` column.
5. **Close findings as part of regular work.** Findings are not their own change — they are discovered during sweeps and addressed inside whichever change next touches the relevant cell.

---

## Anti-patterns

- **Grade inflation to avoid hard conversations.** A "good" grade on a domain that has open critical-severity findings is grade fraud, not optimism. The `anti-entropy-discipline.md` sweep that computes the grade is the audit trail; manually overriding the grade is a `phase_log` finding in itself.
- **Sweeps as ceremony.** A sweep that produces grades but never closes findings is decorative — the file accumulates "weak" cells indefinitely without remediation. The `Recently closed gap-findings` table is the indicator: if it has fewer than one entry per sweep, the sweep is performative.
- **Weekly sweep + monthly review.** The sweep cadence and the prioritisation cadence must be linked; sweeping weekly and only triaging monthly produces a backlog the team cannot work through. Match the cadences.
- **Grading by line count or test count.** "We have 90% test coverage on this domain, so it is good." Coverage is one signal; per [`../evidence-quality-per-type.md §Coverage by counting`](../evidence-quality-per-type.md), counting alone does not establish quality. Each surface has its own per-surface bar in `cross-cutting-concerns.md`.
- **Quality score as performance review.** The score grades the **system**, not the **engineers**. Tying grades to individual performance reviews collapses the discipline — engineers will optimise for the grade rather than the system. The score is for prioritisation; performance review is a separate process.
- **One sweep per quarter.** The sweep cadence must be small enough that the gap-findings stay actionable; a quarterly sweep produces 90 days of accumulated drift that no team can triage in one sitting. Weekly is the recommended floor.

---

## Cross-references

- [`../anti-entropy-discipline.md`](../anti-entropy-discipline.md) §Quality score — the optional formulation this template instantiates.
- [`../cross-cutting-concerns.md`](../cross-cutting-concerns.md) — the per-surface bar each grade is computed against.
- [`../surfaces.md`](../surfaces.md) — the four canonical surfaces the columns enumerate.
- [`../evidence-quality-per-type.md`](../evidence-quality-per-type.md) — the anti-patterns list (decorative evidence, coverage by counting) the grade computation must avoid.
- [`./consumer-docs-scaffolding.md`](./consumer-docs-scaffolding.md) — the surrounding repo layout where `QUALITY_SCORE.md` lives.
- [`../adoption-strategy.md`](../adoption-strategy.md) — the adoption record where opt-in is documented.
