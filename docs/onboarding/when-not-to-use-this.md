# When Not to Use This

This methodology is powerful, but it is not meant to be applied in full to every task.
Over-applying it will make the team resent the methodology, which is worse than not using it at all.

---

## 60-second decision flow

```
Task arrives
  │
  ├─ Q1: Does this change any behavior that a third party / user / another module will perceive?
  │   │
  │   ├─ No  → take the "no-process" path (below)
  │   │
  │   └─ Yes → Q2
  │
  ├─ Q2: Single surface + single consumer + can be verified in ≤ 5 minutes?
  │   │
  │   ├─ Yes → Lean mode (minimum triple: surface tagging, verification, evidence)
  │   │
  │   └─ No  → Q3
  │
  └─ Q3: Does it touch schema / contract / enum / payments / auth / migration / rollout?
      │
      ├─ Yes → Full mode
      │
      └─ No  → Lean mode, with risks explicitly listed
```

---

## No-process path (zero ceremony)

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

## The stripped-down version

For the gray zone between "no process" and "full Lean," use a **three-line handoff**:

```
What changed:  <one sentence>
How verified:  <one command or one screenshot>
Residual risk: <one sentence, or "none">
```

Applicable when:
- There is a bit of public impact, but it reaches only one surface.
- A small refactor in a familiar area (already protected by tests).
- A small config tweak (a known-validated config key).

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
| Change the value of an i18n key (same semantics) | Three-line handoff |
| Rename an i18n key | Lean (consumers will break) |
| Add a new log | Three-line handoff |
| Change an existing log's structure | Lean (downstream dashboards / alerts are consumers) |
| Edit README | No process |
| Edit an API's README description but not the code | Three-line handoff (docs are consumers) |
| Bump a dependency (patch) | Three-line handoff + verification |
| Bump a dependency (major) | Full |
| Delete a "nobody uses it" function | Lean (first prove nobody uses it) |

---

## Final word

> The point of the methodology is to remove the need to **re-decide from scratch each time** whether to be careful.
> If you are spending a lot of time on "should I use the flow or not," that means the decision threshold isn't sharp enough — fix the rules instead of agonizing over each case.
