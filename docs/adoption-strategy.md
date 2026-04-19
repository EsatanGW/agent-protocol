# Team Adoption Strategy

> **English TL;DR**
> Phased adoption playbook so teams can land the methodology without a big-bang rewrite. Three stages — **Stage 1 (1-2 weeks)**: introduce *surface language* into existing PRs (one extra line naming affected surfaces; no process change). **Stage 2 (1-2 months)**: introduce Change Manifest for *high-risk* changes only (breaking changes, cross-surface migrations); keep low-risk changes lightweight. **Stage 3 (3+ months)**: manifest becomes default + CI gate + cross-team shared vocabulary. Measurement: count of rollback events, count of forgotten-consumer incidents, review cycle time, onboarding time. Common objections answered: "too heavy for small changes" (apply only to non-trivial), "slows us down" (measure rollback-avoidance payoff), "just another doc" (manifest is the *compressed* output, not extra writing). Pairs with `ci-cd-integration-hooks.md` for automation pacing.

How to adopt this methodology progressively, and how to measure whether it works.

---

## Core principles

1. **Don't adopt everything at once** — start with one concept, show the effect, then expand.
2. **Start from pain** — identify the team's most painful issue and use the methodology to fix that specific one.
3. **Measurement-driven** — if you can't measure improvement, you can't persuade the team to keep going.

---

## Three-stage rollout

### Stage 1: mindset seeding (1–2 weeks)

**Goal:** get the team thinking in *surface* language.

**How:**
- In existing code reviews or PR descriptions, add one line:
  "Surfaces this change touches: user / system-interface / information / operational."
- No process change is required — only one extra labeled line.

**Success criteria:**
- Team members naturally ask "where does this bug's source of truth live?"
- PR descriptions begin mentioning affected surfaces.

**Common pushback and responses:**

| Pushback | Response |
|----------|----------|
| "Isn't this just one extra line?" | Yes — and that one line tells the reviewer what to look at. |
| "We already split frontend / backend." | Surfaces don't replace the split; they fill gaps the split cannot see. |

---

### Stage 2: process embedding (2–4 weeks)

**Goal:** insert surface checks at key moments.

**How:**
- Each delivery cycle, pick 1–2 larger tickets and run them through Lean mode end-to-end.
- In the delivery-cycle retrospective, compare tickets that went through the flow with those that didn't — look at delivery quality.
- Introduce the cross-cutting checklist (security / performance), but only require it when the change touches auth or a hot path.

**Success criteria:**
- At least one case of "the surface check caught something in review that would otherwise have been missed."
- Team members start proactively asking "was the operational surface handled for this change?"

**Common pushback and responses:**

| Pushback | Response |
|----------|----------|
| "Lean mode is still too heavy." | Trim Lean to three items only: affected surfaces + source of truth + evidence. |
| "A small bug doesn't need this." | Agreed. Use it only for cross-surface changes. |

---

### Stage 3: institutionalization (4–8 weeks)

**Goal:** the methodology becomes the team's default way of working.

**How:**
- Publish the project's stack bridge document.
- Large features run Full mode; small changes run Lean mode; trivial fixes skip the flow.
- The completion report becomes part of the PR-merge checklist.
- Metric review happens on a regular cadence.

**Success criteria:**
- New hires understand the team's way of working within one day (via bridge doc + onboarding docs).
- Rollback frequency goes down.
- "Shipped but forgot to update X" events become rarer.

---

## Metrics

> **Core principle:** measure the baseline *before* adoption — otherwise you have no way to judge "did this help."
> Every metric needs a **current value** before the methodology rolls out; at minimum, collect 2 delivery cycles of pre-existing data as a control.

### Direct metrics (quantifiable)

| Metric | Formula / measurement | Baseline advice | Target direction | Data source |
|--------|----------------------|-----------------|------------------|-------------|
| Hotfix rate | `hotfix PRs / total releases` | Measure current value across 2 delivery cycles first | ≥ −30% indicates the methodology is working | Git / PR labels |
| PR rework rate | `PRs returned at least once / total PRs` | Measure current value first | Declines 3 delivery cycles after adoption | Code review tool |
| Post-delivery bug rate | `bugs reported within 7 days after release / tickets in that release` | Measure current value first | Should decline | Issue tracker |
| Cross-surface desync incidents | Manually classify "API changed but UI / docs / enum did not follow" bugs | Manually tag 2 delivery cycles | Decline to single digits per month | Post-mortems / bug classification |
| Mean time to verify | Elapsed time from PR open until a reviewer can say "I see what needs verifying" | Requires your own instrumentation | Should decline | Code-review timestamps |
| Evidence coverage | `PRs with verification evidence attached / PRs that should be Lean+` | ≈ 0% before adoption | > 70% after adoption | PR-template checkboxes |

### Indirect metrics (qualitative observation)

| Metric | How to observe | Optional quantitative proxy |
|--------|----------------|-----------------------------|
| New-hire ramp-up | How quickly a new team member can deliver a full ticket independently | Onboarding days until first independently merged PR |
| PR review efficiency | Whether reviewers can grasp change scope faster | Median number of review-comment rounds |
| Cross-function communication quality | Whether cross-layer / cross-role "are you done yet?" messages drop | Count of "blocked by" messages in team channels |
| Incident recovery speed | How quickly root cause is found when something breaks | MTTR (mean time to resolve) |
| Trust index | Whether the team volunteers to follow the flow vs. is forced to | Anonymous 1–5 survey |

### Measurement cadence

- **2 delivery cycles before adoption:** collect baseline only; change no process.
- **Every delivery cycle:** compute direct metrics; spend a few minutes in the regular retrospective reviewing one representative number.
- **Monthly:** review indirect metrics; adjust the tightness of the process.
- **Quarterly:** decide whether to adjust surface definitions or the Lean/Full switch criteria.

### Reference health ranges

These are **reference anchors**, not hard thresholds — baselines vary a lot across teams.

| Metric | Green | Yellow | Red |
|--------|-------|--------|-----|
| Hotfix rate | < 5% | 5–15% | > 15% |
| PR rework rate | < 20% | 20–40% | > 40% |
| Cross-surface desync / month | < 2 | 2–5 | > 5 |
| Evidence coverage | > 70% | 40–70% | < 40% |

### Counter-metrics (guard against wrong optimization)

The following "looks better" signals can instead indicate the methodology is being **misused**:

- PR count explodes but per-PR line count shrinks → probably slicing work artificially to "go through the flow."
- Spec / plan word count explodes → likely producing artifacts no one reads.
- Review time lengthens → reviewers reading ritual text instead of the diff.
- Automated-check pass rate at 100% → rules are too weak, or are being bypassed.

When you see a counter-metric, investigate — don't celebrate.

---

## When not to use

See `docs/onboarding/when-not-to-use-this.md`.

Additional notes:
- **The team is firefighting** — put out the fire first; don't push a new methodology during a P0 incident.
- **Team ≤ 2 people** — two-person teams are more efficient over voice; no formal evidence trail is needed.
- **Pure prototype / PoC** — the goal is to validate an idea quickly, not to deliver stably.
- **The team already has a mature equivalent** — if the existing process already covers checks across all four surfaces (even with different terminology), don't force-swap.

---

## Common pivots from pushback to acceptance

> "It's not that we disagree — we just don't have time."
> → Do only Stage 1 (one labeled line). No extra time cost.

> "This is too heavy for small changes."
> → Agreed. Small changes don't go through the flow. The methodology has explicit out-of-scope cases.

> "Our problem isn't lack of process, it's too many requirements."
> → The methodology doesn't reduce requirement volume, but it reduces "done but needs redoing" waste.

> "I tried it once and didn't feel it helped."
> → One run isn't enough. Track a delivery cycle of metrics before judging.

---

## Methodology-decay monitoring (reverse feedback loop)

> Forward metrics tell you "is the methodology helping?"
> Reverse metrics tell you "is the methodology itself rotting?"
> **A methodology without a reverse loop eventually becomes ritual no one argues with.**

### Why a reverse loop matters

A methodology can fail in two ways:
1. **Adoption fails** — forward metrics catch this (baseline does not shift).
2. **Adoption succeeded, but discipline has hollowed out** — forward metrics may still look good while the substance is already gone.

The second kind is the more dangerous one: everything looks normal.

### Decay counter-metrics

These are counter-metrics for **the methodology itself**, not for product quality.
They should have automated collection channels — as a capability, not as a specific tool.

| Counter-metric | Definition | Red-light threshold | Meaning |
|----------------|------------|---------------------|---------|
| Ceremony Rate | Unnecessary artifacts / all artifacts | > 20% | The methodology is being used for show. |
| Manifest Drift Rate | Cases where manifest claims do not match actual diff | > 10% | Plan and implementation are decoupled. |
| Artifact Rot Rate | Artifacts marked `in_progress` that have not been updated in a long time | > 15% | The methodology is being abandoned. |
| Waiver Abuse Rate | Same `rule_id` being waived repeatedly | Same `rule_id` more than 3× in a month | The rule should be adjusted — not waived indefinitely. |
| Bypass Rate | Changes that skip the CI gate (skip flags, force push, ad-hoc workarounds) | > 5% | Discipline is being bypassed. |
| Zero-Evidence Delivery Rate | Changes declared complete with empty evidence fields | > 2% | Definition of done has broken down. |
| Escalation Avoidance Rate | Cases where AI should have escalated but didn't, discovered after the fact | > 1% | AI contract is being bypassed. |
| SoT Orphan Rate | SoTs with no owner | > 0 (any occurrence is a warning) | Organizational memory is decaying. |
| Deprecation Slip Rate | Items still not migrated past their hard cutoff | > 5% | Queue discipline has failed. |

### Automation collection requirements

The methodology **does not mandate** any specific collection tool, but requires implementations to have the following **capabilities**:

1. **Manifest diffing capability** — ability to diff different phase snapshots of the same `change_id`.
2. **Repo-history scanning capability** — ability to scan the `main` branch at least weekly to find orphans and rot.
3. **Waiver tracking capability** — ability to aggregate waiver counts and time distribution for the same `rule_id`.
4. **Alerting capability** — when a counter-metric breaches threshold, the owner is notified — not merely recorded in a report.

Concrete implementations (cron jobs, CI scheduled workflows, dashboards, alert channels) are the stack bridge's responsibility; see `docs/bridges/`.

### Decay Intervention Playbook

A breached counter-metric is **not a cue to add more rules** — it is a cue to diagnose:

| Counter-metric | Diagnose first | Common intervention |
|----------------|----------------|---------------------|
| Ceremony Rate ↑ | Which kind of artifact is overproduced? | Downgrade that artifact class to Lean or make it optional. |
| Manifest Drift Rate ↑ | Is the Planner sloppy, or is the Implementer drifting? | Strengthen Discovery Loop discipline / raise Plan review bar. |
| Artifact Rot Rate ↑ | Abandoned work or excessive context-switching? | Cap number of in-flight changes; require phase-boundary status updates. |
| Waiver Abuse Rate ↑ | Is the rule too strict or miscalibrated? | Adjust the rule or downgrade its enforcement level — don't keep forcing it. |
| Bypass Rate ↑ | Who is bypassing, and why? | Interview them — the rule itself may be unreasonable. |
| Zero-Evidence ↑ | Is the verification tool broken, or have people given up? | Fix the former / re-train on the latter. |
| Escalation Avoidance ↑ | Has the AI-contract prompt drifted? | Review and reinforce the clarity of AI entry-point files. |
| Orphan Rate > 0 | Has the ownership audit process failed? | Assign an owner immediately + schedule a recurring audit. |
| Deprecation Slip ↑ | Does the hard cutoff have real enforcement? | Raise the authorization level that enforces the cutoff. |

### Measurement cadence

- **Monthly**: snapshot all counter-metrics into `docs/adoption/metrics-log.md` or equivalent.
- **Quarterly**: compare trends; trigger the intervention playbook if any red light appears.
- **Annually**: compare against the prior year and reassess thresholds (the methodology itself must evolve too).

### Counter-counter-metrics (guarding against over-monitoring)

The following signals indicate **the monitoring of the methodology** has itself grown too heavy, and should be trimmed:

- Time spent collecting counter-metrics exceeds time spent deciding with them.
- A counter-metric never triggers an intervention (meaning the threshold is meaningless).
- The team begins to shape behavior to satisfy the counter-metric rather than to improve substance.

Monitoring itself must be monitored — otherwise methodology improvement just becomes another ceremony layer.

---

## Relationship to other documents

- `docs/principles.md` principle 10 — "A methodology must be measurable; otherwise it cannot improve" — is the upstream reasoning for this chapter.
- `docs/automation-contract.md` Tier 3 drift detection — partial automated collection for counter-metrics depends on this layer.
- `docs/team-org-disciplines.md` organization-level asset metrics — complement the counter-metrics in this chapter.
- `docs/ai-operating-contract.md` §10 self-check checklist — the AI-role entry point for counter-metrics.
