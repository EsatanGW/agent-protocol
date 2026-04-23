# When Not to Use This

This methodology is powerful, but it is not meant to be applied in full to every task.
Over-applying it will make the team resent the methodology, which is worse than not using it at all.

---

## Four canonical modes

The methodology has **four execution modes**, ordered by rising ceremony: **Zero-ceremony, Three-line delivery, Lean, Full**. Canonical definitions: [`../glossary.md §Execution mode`](../glossary.md). Mode-selection logic: [`../../skills/engineering-workflow/references/mode-decision-tree.md`](../../skills/engineering-workflow/references/mode-decision-tree.md) — that file is the execution-layer source of truth for the forced-Full / forced-Lean / forced-Three-line-delivery / forced-Zero-ceremony scenario tables.

This file keeps the onboarding-oriented view: when *not* to use the methodology at all, and why over-use / under-use are both failure modes.

---

## 60-second decision flow

For the canonical Fast-call decision tree and all forced-mode scenario tables, go to [`../../skills/engineering-workflow/references/mode-decision-tree.md §Fast call`](../../skills/engineering-workflow/references/mode-decision-tree.md). This onboarding document no longer duplicates the flow — maintaining two copies produced the forced-Full divergence that 1.15.0 resolved.

---

## Zero-ceremony (no process, just the work)

These situations **do not go through the methodology at all** — just do the work:

### 1. Pure Q&A / research
- Explaining a concept, comparing frameworks, summarizing reference material.
- Decision rule: **no files will be modified.**

### 2. Tiny, low-risk fixes
- Typo, single-string copy fix, minor formatting adjustment.
- Decision rule: **diff < 5 lines + no public behavior impact + does not cross surfaces.**

### 3. One-off low-risk scripts
- Ad-hoc log-probe one-liner, one-time data cleanup, purely local tooling.
- Decision rule: **will not be reused by anyone / any system, no long-lived consumer.**

### 4. Pure environment checks
- Check a version, port, log, service state.
- Decision rule: **read-only.**

### 5. Exploratory learning / experiments
- A throwaway test to understand an API.
- Decision rule: **explicitly tagged as throwaway, will not land on main.**

---

## Three-line delivery

For the gray zone between Zero-ceremony and Lean, use a **three-line record** (kept next to the commit or in the PR description):

```
What changed:  <one sentence>
How verified:  <one command or one screenshot>
Residual risk: <one sentence, or "none">
```

Applicable when:
- There is a bit of public impact, but it reaches only one surface.
- A small refactor in a familiar area (already protected by tests).
- A small config tweak (a known-validated config key).

Canonical definition: [`../glossary.md §Three-line delivery`](../glossary.md). Legacy aliases (retired): *three-line handoff*, *stripped-down version*.

---

## Situations where the methodology does not apply (organization / phase level)

Even if the task itself would fit, these situations should **pause or skip** the methodology:

| Situation | Reason | Alternative |
|-----------|--------|-------------|
| In the middle of a P0 incident | Firefighting first — evidence comes later | Stop the bleeding first; post-mortem within 72h |
| Team of ≤ 2 people | Voice + commit message is enough | Keep only the "surface tagging" habit |
| Pure prototype / PoC | The goal is to validate an idea, not ship stably | Explicitly mark the end-of-life |
| Team already has a mature equivalent | Different terminology does not mean missing coverage | Do a gap analysis first, then decide |
| One-off migration script (run once + delete) | No long-lived consumer | Keep the runbook and rollback |

---

## Scenarios where the methodology partially fits but has known gaps

Different from the table above (those situations **skip** the methodology). These are scenarios where part of the methodology applies but some mechanism does not yet have a natural home, so mechanically filling every manifest field feels forced. The table says what gap exists and what to do pragmatically while the methodology evolves.

| Scenario | Why it doesn't cleanly fit | Pragmatic path today |
|----------|---------------------------|---------------------|
| **Incident response / hotfix under pressure** | Change Manifest + phase gates are too slow when production is actively burning | Stop the bleeding first with whatever is fastest; after stabilization, backfill a Lean manifest as the post-mortem record (within 72h). Do not try to fill Full mode during the incident. |
| **Pure research / exploratory work** | Methodology presumes clear acceptance criteria; research outcome is "what we learned," not "what we delivered" | Record findings as a Cross-Change Knowledge Note (CCKN — see [`../cross-change-knowledge.md`](../cross-change-knowledge.md)) or equivalent reference doc. Do not open a Change Manifest for a research question unless a concrete change follows. |
| **A/B test / experiment design** | Evidence semantics misalign — the experiment itself generates the evidence, not a separate verification artifact | Open a Lean manifest at experiment *kickoff* (declaring surface, evidence = experiment result, rollback mode). Record the actual result in a separate observation doc once data is in. Do not try to pre-declare a screenshot-diff artifact for something whose result is unknown. |
| **Pure content / i18n / copy-only changes** | Full evidence / rollback / breaking change is overkill for a string change | Use the Three-line delivery form above. Escalate to Lean only when the string rename crosses a consumer (renaming an i18n key, changing an enum label consumed by telemetry). |
| **AI agent / prompt system's own development** | When the *target* of the change is an agent (prompt changes, tool additions, workflow edits), the four-surface map does not cleanly capture "the agent's behavior changed" | Treat agent behavior as a variant of the user or information surface (whichever the change most affects) and document the gap. A dedicated "agent surface" extension is a candidate for a future revision. |
| **UI / UX design iteration** | Acceptance criteria cannot be written up-front because the design is *being discovered* | Run the design-spike phase outside the methodology. Once a direction is picked and a real surface change is proposed, enter Lean mode for the implementation phase. Do not force acceptance criteria onto a spike. |
| **ML model training / hyperparameter iteration** | The Model surface exists, but per-iteration evidence is "experiment log + metric delta," not the standard evidence types | Per-iteration: keep experiment logs as the evidence artifact; skip breaking-change / rollback fields that do not apply. At the **ship-to-production event** for a new model version, run Full mode including rollback (mode 2 or 3 is typical for deployed models). |
| **Open-source library's own development** | Consumers are unpredictable third parties; breaking-change severity is always "worst-case" by definition | Bias toward L2+ for any public-API change; use longer deprecation windows; treat the public API as a hard permanent contract. Consumer classification collapses to "third-party" for every consumer. |

**What this table is not:** a promise that these scenarios will be fixed soon. Each one is a known limitation. The point of listing them is so a reader whose work falls here does not conclude "the methodology does not work" — the honest statement is "this specific fit is evolving; here is the pragmatic path today."

**What this table is:** an invitation to contribute. If your work consistently falls in one of these rows, documenting how you currently handle it (as a CCKN or a bridge doc) is a direct input to the next methodology revision.

---

## Five signals of over-use

When you see these signals, **immediately downgrade or drop the flow**:

1. **Docs are longer than the code** — 10 lines of code producing 300 lines of spec.
2. **Process cost > task cost** — more time spent walking the phases than implementing.
3. **Artifacts produced just to be produced** — plans / reports nobody will read and nobody will use.
4. **Phases don't meaningfully differ** — Phase 1 and Phase 2 restate the same thing in different words.
5. **Team begins bypassing the flow and submitting quietly** — the flow has lost trust.

Any one of these signals is cause to stop and ask: should we *not* use it this time?

---

## Five signals of under-use

Conversely, these signals mean the flow should be **upgraded**:

1. "We also changed something similar last time, but nobody remembers why."
2. "After this shipped, X broke — nobody realized those two were linked."
3. A hotfix is needed within 24 hours of release.
4. Reviewer asks "why was this changed this way?" and nobody can answer.
5. The same bug is fixed a second or third time.

These are evidence that discipline is insufficient — not that the task was too small.

---

## Edge-case quick reference

| Situation | Path |
|-----------|------|
| Change the value of an i18n key (same semantics) | Three-line delivery |
| Rename an i18n key | Lean (consumers will break) |
| Add a new log | Three-line delivery |
| Change an existing log's structure | Lean (downstream dashboards / alerts are consumers) |
| Edit README | Zero-ceremony |
| Edit an API's README description but not the code | Three-line delivery (docs are consumers) |
| Bump a dependency (patch) | Three-line delivery + verification |
| Bump a dependency (major) | Full |
| Delete a "nobody uses it" function | Lean (first prove nobody uses it) |

---

## Final word

> The point of the methodology is to remove the need to **re-decide from scratch each time** whether to be careful.
> If you are spending a lot of time on "should I use the flow or not," that means the decision threshold isn't sharp enough — fix the rules instead of agonizing over each case.
