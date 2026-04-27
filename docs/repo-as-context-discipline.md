# Repo-as-Context Discipline

> **English TL;DR**
> Anything an agent cannot reach from inside the repository while running, effectively does not exist for that change. External-only knowledge (Slack threads, hallway decisions, private docs, ticket comments) must be **transcoded** into repo-resident artifacts before it can govern an agent's behaviour. AGENTS.md is the repo's *table of contents* — short, pointer-heavy — not its encyclopaedia. This document defines the discipline, the transcoding rules, and the per-Phase enforcement points.

---

## Why this discipline exists

An agent's effective working set on a given turn is whatever is actually loaded in its context window plus whatever it can fetch with the capabilities the runtime grants it. Knowledge that lives anywhere else — a private Slack channel, a Google Doc, an internal wiki, a verbal hallway decision, a comment buried in a closed PR — is invisible. *Invisible knowledge does not steer behaviour.* It also does not survive Reviewer audit (the Reviewer's sampling right per [`docs/ai-operating-contract.md`](ai-operating-contract.md) only extends to artifacts the reviewer can read).

Two failure modes follow from violating the discipline:

1. **Phantom rule.** A maintainer says "but we agreed in the meeting that…" — the agent neither saw the meeting nor sees the resulting rule, and produces a change that contradicts it. Re-work is needed; the agent is blamed for "not knowing." The discipline reframes this: the rule was never made *durable*; the omission is upstream of the agent.
2. **Phantom rationale.** A historical decision (an enum's odd values, an API quirk, a deprecation freeze) is preserved only as a Slack thread; the agent re-proposes the change that was previously rejected for that reason. The rejection cycles forever because the *reason* never landed in the repo.

Both failures dissolve when the rule lives in a repo-resident artifact the agent can read.

---

## The discipline (3 rules)

### Rule 1 — Repo is the system of record

Any rule, decision, deprecation, exception, or constraint that must govern an agent's behaviour for this change must be readable from a repo-local file (markdown, YAML, JSON, source code, schema, or template) before the agent acts on it. If it is only in a chat / doc / ticket / verbal channel, it must first be transcoded (Rule 3) — *or* the change must escalate per [`AGENTS.md §Stop conditions`](../AGENTS.md), naming the missing context as the blocker.

This rule does not require the repo to *contain* every project fact (overkill, and a context-pollution anti-pattern). It requires that *facts which are about to govern this change* are repo-resident at the moment of governance.

### Rule 2 — AGENTS.md is a table of contents, not an encyclopaedia

The runtime operating contract in [`AGENTS.md`](../AGENTS.md) is read by every session, every runtime. Every paragraph that lives there is paid for in cache cost, attention budget, and review burden across every consumer. Therefore:

- **A new normative rule** is added to AGENTS.md only if it cannot live in a topic-specific `docs/*.md` file. Most rules can; the §File role map already catalogs canonical SoT homes for surfaces, SoT patterns, breaking change, rollback, phase gate, multi-agent handoff, output craft, and so on.
- **A pointer** to a `docs/*.md` section beats inlining the section's content into AGENTS.md.
- **AGENTS.md grows** when there is no canonical home and one needs to be created. In that case, the change creates the new `docs/*.md` and AGENTS.md gets a pointer, not the body.

The current AGENTS.md size is descriptive, not aspirational: when AGENTS.md grows past what a fresh session can read in one go, the reflexive remedy is to lift content into a topic-specific doc and leave a pointer behind. This document does *not* mandate a hard line-count ceiling — it does mandate the *direction of travel* (pointers up, body out).

### Rule 3 — External knowledge is transcoded before it governs

Knowledge that originates outside the repository (chat threads, private docs, verbal decisions, ticket comments) is transcoded into a repo-resident artifact before the agent acts on it. The transcoded artifact is the **system of record** going forward; the original external source is treated as the historical witness, not the authority.

| External source | Transcoded into | Why this target |
|---|---|---|
| Decision in a chat thread (Slack, Discord, group DM) — about how to handle a recurring kind of change | A Cross-Change Knowledge Note ([`docs/cross-change-knowledge.md`](cross-change-knowledge.md)) | CCKNs cover topical knowledge that applies across changes; this is exactly the kind |
| Decision in a chat thread — specific to one in-flight change | A field in that change's manifest (`implementation_notes[]`, `escalations[]`, or a dedicated `decisions[]` entry) | The manifest is the change's state snapshot; cross-change CCKN would over-broaden |
| Spec or design in an external doc | A `docs/*.md` page (or a sub-section of an existing page) under a SoT-tier home | Spec content is normative; it must live where Reviewers and future agents will look |
| Conclusion in a ticket / issue comment | The change manifest (if scoped to one change) or ROADMAP (if it spans multiple changes) | Ticket comments are not durable in the way `git log` is; lift into the artifact whose discipline the conclusion governs |
| Verbal hallway decision | First, a transcoded note in one of the four targets above. If the decision is significant enough to alter `AGENTS.md` or a `docs/*.md` SoT, also a Change Manifest at L1+ per [`CLAUDE.md §5`](../CLAUDE.md). | Verbal decisions are the most fragile; always transcode before acting |

A transcoded artifact must include: the **decision** (what was decided), the **rationale** (why), the **scope** (which changes / surfaces / consumers it governs), and a **provenance pointer** if available (link back to the chat thread or doc, knowing the link may rot — the transcoded text is the SoT, the link is the witness). Without rationale and scope, the artifact is only marginally better than the un-transcoded source.

---

## Per-phase enforcement

### Phase 0 (Clarify)

When the user references external context ("we discussed in the standup," "see the Notion page," "Alice mentioned"), the first question is *whether the referenced context is already transcoded*. If not, transcoding is part of Phase 0 — not a separate optional step. The agent does not start Phase 1 until either (a) the relevant external knowledge is transcoded, or (b) the agent has explicitly recorded that the change does not depend on that context.

### Phase 1 (Investigate)

Surface-mapping and SoT-mapping read only repo-resident sources. If the investigator finds that the answer to "where does this surface's truth live?" is *only* in an external system, that surface's `sot_map` row cannot be filled honestly — the investigator must escalate (Discovery Loop, [`skills/engineering-workflow/references/discovery-loop.md`](../skills/engineering-workflow/references/discovery-loop.md)) and request transcoding before continuing.

### Phase 5 (Review)

The Reviewer's audit reads only repo-resident sources. If the manifest cites an external source as the authority for a decision (e.g. a Slack link as the rationale for a breaking-change waiver), the audit treats this as a Rule 3 violation: the decision is not durable, the artifact is incomplete, and the Reviewer either sends back for transcoding or accepts the gap as an explicit `waivers[]` entry whose `expires_at` forces re-transcoding within a bounded window.

### Phase 7 (Deliver) and Phase 8 (Observe)

The completion report and post-delivery observation read only repo-resident artifacts. A completion report that says "see the Slack thread for the production roll-out plan" is incomplete — the roll-out plan must be in the manifest or in a linked `docs/` artifact, not external.

---

## Anti-patterns

- *"I'll add it to the doc later."* Later is when the rule has already failed to govern this change. Transcode before acting on the rule, not after.
- *"It's in the Slack thread."* The thread is the *witness*; the system of record is the transcoded artifact. The thread answers "did this conversation happen?" — it does not answer "is this decision binding?"
- *"AGENTS.md is the place for everything important."* AGENTS.md is the place for the operating contract. Topic-specific rules belong to topic-specific `docs/*.md` files (per AGENTS.md §File role map); inline accumulation in AGENTS.md is a slow erosion of the file's role as a *table of contents*.
- *"The README has a link to the doc."* A link to an external doc is a dependency on a source the agent cannot read. Transcode the doc's binding portions; leave the link as a witness pointer.
- *"Memory will retain it."* Project memory ([`docs/ai-project-memory.md`](ai-project-memory.md) §Tier 2) is a transcoded artifact, not a substitute for one. Saving the rule as a memory note is fine *and* the rule lives in a repo-resident artifact at the same time; either alone is not enough.
- *"It's institutional knowledge."* Institutional knowledge that governs agent behaviour is exactly what this discipline targets. Either transcode it or make explicit that the change does not depend on it.

---

## Relationship to other documents

- [`AGENTS.md`](../AGENTS.md) §File role map — catalogues canonical SoT homes; this discipline is what makes the catalog mean something at runtime.
- [`docs/ai-project-memory.md`](ai-project-memory.md) §Three-tier memory model — Tier 2 (project memory) is the durable form of transcoded knowledge.
- [`docs/cross-change-knowledge.md`](cross-change-knowledge.md) — the canonical artifact for topical knowledge that spans changes; this discipline names CCKN as the default transcoding target for cross-change Slack decisions.
- [`skills/engineering-workflow/SKILL.md`](../skills/engineering-workflow/SKILL.md) §On-demand reading — describes which repo-resident artifacts are loaded when; this discipline answers *what should exist as a repo-resident artifact in the first place*.
- [`docs/change-manifest-spec.md`](change-manifest-spec.md) §Manifest size ceiling — the artifact-side enforcement of the same principle: too-large manifests stop being state snapshots; too-large external dependencies stop being governable.
