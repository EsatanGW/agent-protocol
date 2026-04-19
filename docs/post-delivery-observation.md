# Post-Delivery Observation (Phase 8)

> **English TL;DR**
> Phase 7 (Deliver) proves the change was correct *at delivery*; Phase 8 proves it stays correct under real traffic. Defines a time-boxed observation window keyed per-change (days-to-weeks depending on risk profile), with four loop points: (1) **metric & alert watch** — which pre-declared metrics must stay in band; what anomaly triggers an incident vs. a learning note; (2) **post-delivery evidence capture** — actual rollout graphs, first-user-touched timestamp, error budget burn rate, attached to manifest; (3) **learning backflow** — surprises (good and bad) feed back into bridge files, breaking-change framework examples, or a failure-mode gallery; (4) **closeout** — either the change is declared stable and archived, or a follow-up ticket is opened with `part_of` link back to the original manifest. Prevents the common anti-pattern where "delivered" gets conflated with "done" and defects discovered at T+72h are treated as unrelated new work.

Phase 7 (Deliver) closes "delivery," but not "completion."
This document defines the post-delivery observation, feedback, and learning mechanism —
promoting the methodology from "got it right once" to "gets more right each time."

---

## Why Phase 8 is needed

The Phase 7 completion report proves "everything was correct at the moment of delivery."
But the real world also has:

- Edge cases exposed only after shipping.
- User behavior different from expectations.
- Real-traffic performance characteristics.
- Interaction with other features that shipped in the same window.

Without Phase 8, these lessons never feed back into the methodology,
and the team keeps making the same mistakes in the same blind spots.

---

## Phase 8 is not mandatory

| Change type | Needs Phase 8? |
|-------------|----------------|
| Public behavior change | Recommended |
| Money / payments involved | Strongly recommended |
| Schema migration | Recommended (observe data integrity) |
| Pure refactor (no behavior change) | Not needed |
| Copy / styling fixes | Not needed |
| New functionality behind a feature flag | Recommended (observe flag effect) |

---

## Observation timeline

### T+24h (one day post-release)

**Goal:** confirm nothing exploded immediately.

Checks:

- [ ] Any abnormal error-rate spike?
- [ ] Any change in latency on key APIs?
- [ ] Any drop in crash-free rate?
- [ ] Any anomalous user reports?

### T+72h (three days post-release)

**Goal:** confirm stability under normal usage patterns.

Checks:

- [ ] Does feature usage match expectation?
- [ ] Any edge-case bug reports?
- [ ] Do analytics event numbers look reasonable?
- [ ] Any performance-degradation trend?

### T+7d (one week post-release)

**Goal:** collect learnings, feed back into the methodology.

Checks:

- [ ] Did the feature achieve its original goal (conversion rate, usage metric)?
- [ ] Any unexpected usage patterns?
- [ ] Any follow-up work required?
- [ ] Any improvement opportunities in this delivery's methodology flow?

---

## Observation record template

```markdown
# Post-Delivery Observation: [Ticket ID / Feature Name]

## Basics
- Release date:
- Observer:
- Change summary:

## T+24h
- Error rate: normal / abnormal (describe)
- Latency: normal / abnormal (describe)
- Crash-free rate: normal / abnormal (describe)
- User reports: none / present (describe)

## T+72h
- Feature usage rate: meets expectation / below / above
- Bug reports: none / present (describe)
- Analytics: normal / abnormal (describe)
- Performance trend: stable / degrading (describe)

## T+7d
- Goal achieved: yes / no / partial
- Unexpected behavior: none / present (describe)
- Follow-up work: none / present (describe)

## Methodology feedback
- Was anything missed in Phase 0-7?
- Any cross-cutting checklist items to add?
- Was the Source of Truth map accurate?
- Was the evidence sufficient in hindsight?
```

---

## Feedback loop: how learnings return to the methodology

### Per-case feedback

If observation surfaces a blind spot in the methodology:

1. Record it in the "methodology feedback" section of the observation.
2. Assess whether the cross-cutting checklist, surface definitions, or phase requirements should be updated.
3. If yes, submit a change back to the `agent-protocol` repo.

### Aggregate feedback

Monthly / quarterly, review all Phase 8 records:

- Which surface produced the most defects? → strengthen that surface's checklist.
- Which phase most often bounced back via the discovery loop? → strengthen that phase's minimum requirements.
- Which change type most often needed a hotfix? → consider adding a mandatory Full-mode trigger for that type.

### Metric feedback

Phase 8 data feeds directly into the metrics in `docs/adoption-strategy.md`:

- Rollback / hotfix frequency.
- Post-delivery bug-discovery rate.
- Cross-surface desync incidents.

---

## Integration with A/B tests

If the change carries A/B-test characteristics:

1. Define the experiment hypothesis and success metrics in Phase 2 (Plan).
2. Record experiment start in Phase 7 (Deliver).
3. Collect experiment results at Phase 8 T+7d.
4. Based on results, decide:
   - Full rollout (remove feature flag).
   - Adjust and re-experiment.
   - Roll back.

---

## Exit conditions for Phase 8

Phase 8 ends when any of the following is met:

- T+7d observation is complete with no anomalies.
- All follow-up work has been recorded as independent tickets.
- Methodology feedback has been submitted (if any).

Only after Phase 8 closes does the change's lifecycle truly end.
