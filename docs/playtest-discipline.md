# Playtest Discipline

> **English TL;DR**
> Actionable verification discipline for the *experience surface* (feel, pacing, reward rhythm, difficulty curve, immersive UX that automated tests can't catch). Without this, "validate by playtest" degrades into "asked two teammates, felt OK." Defines a minimum skeleton: **sample size** (≥ N independent participants, target-persona-matched), **scoring rubric** (dimension-weighted Likert with per-dimension anchors — not a single overall "fun" score), **regression baseline** (compare against a fixed build snapshot, not "last sprint"), **evidence artifacts** (session recording or structured note + rubric scores + freeform comments). Three failure modes it prevents: sample-of-one, unstructured ratings, no baseline. Required whenever manifest declares `experience` surface as primary.

> **Purpose:** provide actionable verification discipline for the *experience surface*.
> When other documents in this repo (`surfaces.md`, `cross-cutting-concerns.md`, game / interactive-app examples)
> say "verify by playtest," this document defines the minimum skeleton of a playtest —
> sample size, scoring rubric, regression baseline, evidence requirements.
>
> Without that skeleton, "verify by playtest" degrades into "got two teammates to try it, felt OK."

---

## Why this needs to be its own discipline

The experience surface (see the extended surfaces in `docs/surfaces.md`) covers:
physical feel, animation feedback, sound-effect rhythm, difficulty curve, pacing, the satisfaction of rewards,
narrative immersion, and the parts of UX flow that **automated tests cannot catch**.

Things in this category **have no pass/fail** — only "better than baseline / worse / no difference."
But a playtest without discipline produces three classic failures:

1. **Sample too small** ("I tried it myself, felt OK") — personal preference gets promoted to fact.
2. **Unstructured scoring** ("everyone said it was fun") — you cannot tell which dimension is weak.
3. **No baseline** ("smoother than last time") — no comparable reference point; judgment becomes emotion.

This document defines the minimum bar for all three.

---

## Playtest tiers

Different changes require different playtest scales. Do not drag every change into the heaviest process.

| Tier | When it applies | Sample | Form | Deliverables |
|------|-----------------|--------|------|--------------|
| **L0 — Smoke** | Tweaks to visuals / sound / animation parameters | 1–2 | Self-test + recording | Recording diff + subjective notes |
| **L1 — Focused** | A single interaction / a single scene | 3–5 | Guided session, ≥ 3 runs per participant | Rubric scores + recording + verbatim observations |
| **L2 — Feature** | New feature / new level / new system integration | 5–8 | Mixed backgrounds (veteran / new / target persona), ≥ 5 runs each | Rubric + recording + debrief interview |
| **L3 — Release gate** | Major release / paid feature / live-ops headliner | 10–15, batched | Multiple sessions, covering device tiers, locales, skill tiers | Rubric + recording + baseline diff + objective metrics + decision log |

### Tier selection principles

- Change only touches the visual surface → L0 / L1.
- Change forms new player expectations or habits → at least L2.
- Change is irreversible after shipping (rewards granted, announcement posted) → L3 mandatory (pairs with `rollback-asymmetry.md` mode 3).

### Sample-size boundaries

- **Fewer than 3 participants** is not a playtest — it is self-testing. Self-test conclusions cannot clear a release gate.
- **More than 15 participants** has diminishing marginal value for early verification; at that point, shift to A/B test or closed beta (Phase 8 production feedback — see `docs/post-delivery-observation.md`).
- L1 through L3 samples must **cover the target-player distribution**: do not recruit only colleagues from one office — cover at minimum "target persona + non-target persona" as two cohorts.

---

## Scoring rubric

Every L1+ playtest must use a structured rubric, not open-ended impressions.
Common requirements for any rubric:

- **Score each dimension independently** (not a single "overall experience" score).
- **Use a 5-point Likert scale** (1 = strongly negative, 3 = no impression, 5 = strongly positive) — the odd midpoint allows "no impression" and avoids forced positions.
- **Every score must have a one-sentence rationale** (unannotated scores are not counted).
- **Pass thresholds per dimension are defined ahead of time**, not after seeing the scores.

### Common dimensions (every experience playtest scores these)

| Dimension | What it measures | Typical pass threshold |
|-----------|------------------|------------------------|
| **Comprehension** | Does the user know what happened and what to do next? | Median ≥ 4 |
| **Feedback clarity** | Does the action have clear feedback (visual / audio / haptic)? | Median ≥ 4, nobody ≤ 2 |
| **Pacing** | Is the process too long / too short / well-paced? | Median ≥ 3, nobody ≤ 2 |
| **Meeting expectation** | Does the outcome match what the user expected before pressing the button? | Median ≥ 4 |
| **Willingness to repeat** | Do they want to play / use it again? | Median ≥ 3 |

### Domain-specific dimensions (add by context)

**Games / reward systems:**

- Anticipation (before the action).
- Satisfaction (on success / rare events).
- Consolation (on failure / miss) — avoid excessive frustration.

**Narrative / content:**

- Immersion.
- Tension/release cadence.
- Readability of character motivations.

**UX flow / tools:**

- Shortest path (how many steps to reach the goal).
- Error recoverability (how easy to recover from a mistake).
- Learning curve (how much faster the second run is than the first).

### Rubric anti-patterns

- ❌ "Overall 1–10 score" — cannot localize weakness.
- ❌ "Did you like it? Yes / No" — a binary scale hides nuance.
- ❌ "How would you change it?" — collects suggestions but does not measure experience; the player is not the designer.
- ❌ Setting pass thresholds after seeing the results.

---

## Regression baseline

Experience degrades. Something you got right today can be degraded by the next change.
The purpose of a regression baseline: every playtest compares against an **explicit reference version**, not against memory.

### Baseline kinds

| Baseline | What it compares against | Used for |
|----------|--------------------------|----------|
| **Golden build** | The last version the team agreed was "the experience is good enough" | Long-term regression — guarding against slow drift |
| **Previous release** | The last production version | Pre-release confirmation that the experience has not regressed |
| **A/B control** | A control cohort run in parallel | Validates whether a change produced a real improvement or a placebo |
| **Designer intent** | The target-experience narrative documented in design | Validates whether the implementation met the designed intent |

### How to use it

1. **The baseline must have been scored first.** Without "baseline rubric scores" there is nothing to compare against.
2. **Use the same rubric.** Do not add a dimension this time and drop one next time.
3. **Record differences, not absolutes.**
   - `Comprehension −0.6 / Pacing +0.4 / Satisfaction +1.1` is far more useful than `3.8 / 4.2 / 4.5`.
4. **Define tolerated regression ranges:**
   - Any primary dimension regresses ≥ 1.0 → **must block release**; redesign that dimension.
   - Any primary dimension regresses 0.5–1.0 → entered as a known regression; decide explicitly whether to accept.
   - Regression < 0.5 → treat as noise (unless the same direction is regressing repeatedly; then it is no longer noise).

### Maintaining a golden build

- At the end of every major version, nominate an "experience baseline" version and tag it (git tag / build archive).
- Keep the rubric scores and player recordings of the baseline in `docs/` or a dedicated baseline directory.
- Every 3–6 months, review whether the baseline still represents your players — update if the player cohort or product direction has shifted.

---

## Playtest session flow

Every L1+ session follows this skeleton:

```
1. Brief (2–5 minutes)
   - Tell the participant what we are testing AND what we are not.
   - Do not hint at the right answer; do not disclose expected results.
   - Confirm device / version / locale.

2. Baseline warm-up (optional, L2+)
   - Let the participant play the baseline version for 1–2 runs.
   - Purpose: establish a reference + eliminate the "first-run friction on any version"
     novice bias.

3. Run (primary data collection)
   - Each participant completes at least the rubric-mandated minimum runs.
   - Observer logs "where they got stuck, where they laughed, where they complained,
     where it went quiet for too long."
   - Recording / audio with consent.

4. Rubric scoring
   - Participant fills it in independently after each run (not seeing others' scores).
   - Every score has a one-sentence rationale.

5. Debrief (5–15 minutes)
   - Open questions: "what was the most memorable moment?" "what did you most
     want to skip?"
   - Do NOT ask "how would you change it?" — the player is not the designer.

6. Facilitator notes
   - Nonverbal signals observed (frowns, sighs, repeated attempts).
   - Inconsistencies between what the participant said vs. what they did.
```

### Facilitator rules

- Do not explain the UI for the participant (except for features explicitly out of test scope).
- When they are stuck, silently count to 30 seconds before intervening.
- Do not comment on scores ("oh that's pretty low" will skew the next run).
- Do not exceed 90 minutes in a session — fatigue distorts later data.

---

## Evidence requirements

Matching Phase 6 (Sign-off) evidence, the experience surface must include at least:

- [ ] The playtest tier run (L0 / L1 / L2 / L3).
- [ ] Sample composition (count, background distribution, device distribution).
- [ ] Rubric scores (per-dimension median, distribution, annotations).
- [ ] Diff against the baseline (regression items must be called out).
- [ ] Representative recording clips (key moments + stuck points).
- [ ] Known regressions (if any) and decision log.
- [ ] Objective metrics (L3 only: completion rate, retry rate, drop-off points, session length).

### Anti-patterns

- ❌ "Got a few colleagues to try it, everyone said it was fine" — no tier, no rubric, no baseline.
- ❌ "Scores look great" with no baseline diff.
- ❌ "Recording exists but nobody watched it" — recordings must have observer notes to count as evidence.
- ❌ Discovering a regression in a dimension only after release — L3 without a baseline diff.

---

## When playtest is not enough and Phase 8 production feedback must take over

Fundamental limits of playtest:

- Small sample, short time, artificial environment.
- Participants know they are being observed; behavior shifts.
- Cannot cover long-tail devices / network states / user flow states.

Therefore, passing an L3 playtest ≠ the experience is genuinely fine.
The following situations require an additional feedback loop per `docs/post-delivery-observation.md`:

- Systems that form long-term player habits (daily login, gacha cadence, quest loops).
- Experiences that influence purchase behavior (storefront, paywall prompts, reward distribution).
- Experiences that interact with real community dynamics (leaderboards, guilds, PvP).
- Onboarding for new users (playtest participants have already been taught by you — they are not real novices).

Playtest is a **pre-release gate**, not a **post-release free pass**.

---

## Relationship to other documents

- `docs/surfaces.md` — defines what the experience surface is; this document defines how to verify it.
- `docs/cross-cutting-concerns.md` — the testability axis mentions "regression of visual / interaction behavior"; this document is the experience-surface version of that regression discipline.
- `docs/post-delivery-observation.md` — long-term post-playtest observation joins at Phase 8.
- `docs/rollback-asymmetry.md` — experience regressions are hard to roll back, which is why playtest as a gate is especially important.
- `docs/examples/game-liveops-example.md` / `docs/examples/game-dev-example.md` — worked examples applying this discipline.
