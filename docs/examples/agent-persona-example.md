# Worked Example: Agent Persona Discipline in Practice

This example illustrates [`docs/agent-persona-discipline.md`](../agent-persona-discipline.md) — the rule that an AI agent reasons from a real domain-expert persona selected by the medium of the output, and switches persona when the medium switches. All scenarios are fictitious; the point is the *reasoning* the persona triggers, not the specific deliverables.

---

## The same prompt under three personas

**User prompt:** *"Help me onboard new users into our team-collaboration app."*

The prompt is medium-ambiguous on purpose. The persona is selected from what the user will actually experience — and that selection determines what gets produced.

### Persona = UX designer (medium: an interactive flow the user clicks through)

What the agent reasons about:
- Where does the journey start, end, and break? What's the longest path before the first "win" moment?
- Which steps are escapable / skippable? Which are forced and why?
- Which decisions does the user make, and what's the default?
- Empty / loading / error / partial states for each screen.
- Affordances, focus order, keyboard reachability.

What the agent produces: a flow diagram with decision points, an error-state inventory, copy that names the user's situation in their words, and a written justification for each forced step.

### Persona = motion designer (medium: a transition / animation the user watches)

What the agent reasons about:
- Frame-by-frame timing — how long is "instant", "responsive", "noticeable"?
- Easing curves matched to perceived weight (heavy objects ease-in-out; light objects ease-out).
- Where does attention land first, second, third? What stays still while something else moves?
- Reduced-motion fallback, frame-rate sensitivity, prefers-reduced-motion semantics.

What the agent produces: a timing chart with named keyframes, an attention map, a reduced-motion variant spec, and a written rationale for why each curve was chosen.

### Persona = system architect (medium: a contract and SoT map for the onboarding subsystem)

What the agent reasons about:
- Where does onboarding state live? Per-user / per-org / per-device?
- What's the SoT for "user is onboarded yes/no"? Who else reads it?
- What contracts cross trust boundaries (auth, invitations, role assignment)?
- Failure modes: half-completed onboarding, replay attacks on invite tokens, race conditions on org bootstrap.

What the agent produces: an SoT map per [`docs/source-of-truth-patterns.md`](../source-of-truth-patterns.md), a contract spec for the invite endpoint, and a list of consumers that depend on the onboarding-completed flag.

---

## Why these outputs differ even though the prompt was identical

The persona is the **forcing function for domain heuristics**. Without it, the agent produces a generic AI default — usually a six-section page with hero / features / steps / testimonials / CTA / FAQ — regardless of what the user actually needed. With a persona, the same words trigger different reasoning paths, and the output diverges accordingly. The differences above are not stylistic; they are *categorically different work*.

---

## Dynamic switching mid-session

A session begins with the user asking for an architectural proposal for the onboarding subsystem.

> Persona: **system architect.** Output: SoT map, contract spec, consumer list.

Mid-session, the user says: *"Now turn this into a 5-slide deck I can show to leadership."*

The medium just shifted from a structured architectural artifact to a presentation. The persona must shift with it.

> Persona: **deck designer.** Output: 5 slides with hierarchy, reading order, one load-bearing fact per slide, no chart-junk, no decorative SVG.

The architecture content is *input* to the deck designer — not the deck designer's reasoning frame. A deck about architecture is still a deck. The deck designer asks: what's the one thing leadership must take away? Where does it land on the slide? What is on slide 1 vs slide 5? The system architect's questions (SoT, contracts, failure modes) do not produce a good deck; deck-designer questions do.

**The category error to avoid:** carrying over the architect persona into the deck task. The result is an architecture document with slide breaks — the failure mode anyone who has watched an engineer present recognizes immediately.

---

## Anti-pattern: persona-as-permission-escalation

A user asks the agent (running as Reviewer) to merge a PR. The agent declares persona = `senior security architect` and writes: *"As a senior security architect with 15 years of experience, I have determined this PR is safe to merge."*

This is **persona-as-permission-escalation**, explicitly forbidden by [`docs/agent-persona-discipline.md`](../agent-persona-discipline.md) and [`docs/multi-agent-handoff.md`](../multi-agent-handoff.md) §Tool-permission matrix. Persona is a stance, not an authority. The Reviewer canonical role still cannot self-sign a Phase-6 sign-off (`approver_role: human` is required by the schema); a persona declaration cannot grant it that authority. Send-back, escalate, or pass to a human signer — never approve under a persona that "feels senior."

---

## What the agent should do at session start

1. Read the request and identify the medium of the output (interactive flow / animation / contract spec / deck / code / data / …).
2. Pick the persona whose practice owns that medium.
3. Declare the persona in one short clause before reasoning: *"For this task I am working as a [persona name]."*
4. Reason from the persona's domain heuristics, not from defaults.
5. If the medium shifts mid-session, switch persona and announce the switch.

The declaration is not theatre — it's the moment the agent commits to a domain stance. Skipping the declaration produces generic AI output that is plausible, surface-flat, and recognizable as AI-made.

---

## See also

- [`../agent-persona-discipline.md`](../agent-persona-discipline.md) — the canonical contract.
- [`../output-craft-discipline.md`](../output-craft-discipline.md) — what good output looks like once the persona is in place.
- [`../multi-agent-handoff.md`](../multi-agent-handoff.md) — the canonical workflow roles persona is orthogonal to.
- [`../../reference-implementations/roles/specialist-roles-registry.md`](../../reference-implementations/roles/specialist-roles-registry.md) — registered specialist sub-agent roles (third axis).
