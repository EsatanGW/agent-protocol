# AI Project Memory

> **English TL;DR**
> Addresses the cross-session gap in `ai-operating-contract.md`: what should an AI co-author remember from past manifests, how does memory decay, what must be preserved first when context is compressed, and how past decisions become constraints on future ones. Tool-agnostic.

`ai-operating-contract.md` governs AI behavior **in the moment.**
This document fills the remaining gap: across **sessions, across changes, across months**, how does the AI accumulate / use / retire project memory.

---

## Why project memory is needed

Without a cross-session memory mechanism:

- Every new conversation, the AI re-greps the whole repo from scratch.
- Proposals that were escalated and rejected last time get re-proposed this time.
- Decisions like "the owner of this SoT is team A" are forgotten next session.
- When the context window is compressed, key facts that were never written back to files are lost.

Memory is not a nice-to-have; it is a necessary condition for long-running projects.

---

## Three-tier memory model

AI memory splits into three tiers, differing in origin, lifespan, and intended use.

### Tier 1: Session memory (short term)

**What it is:** the current conversation's context window.
**Lifespan:** minutes to hours.
**Sources:** user input, tool returns, AI output.
**Characteristics:**

- Fast, low latency, directly usable.
- **But can be compressed or truncated** — do not assume it is stable.

**Discipline:**

- Important decisions must simultaneously be **written to files** (spec / plan / manifest), not left only in the conversation.
- When a compression event is imminent, the AI must **proactively produce a state snapshot** first (see §pre-compression protection list below).

### Tier 2: Project memory (medium term)

**What it is:** artifacts accumulated in this repo:

- Delivered manifest files.
- Historical specs / plans / completion reports / test reports.
- `docs/bridges/*` and stack-bridge records in this repo.
- The repo's own CLAUDE-like / AGENTS-like project instruction files.

**Lifespan:** as long as the repo lives (readable while the repo exists).
**Sources:** existing artifacts + newly produced content written back.
**Characteristics:**

- Slow — must be read from disk; scattered across files.
- Stable, traceable, auditable.

**Discipline:**

- When taking over a task, **first** read the relevant historical manifests from project memory before starting work (`resumption-protocol.md`).
- A new decision that contradicts a historical manifest must be **explicitly flagged** — not silently overwritten.
- The format of the project-memory index (e.g. `.ai-memory/index.md` or equivalent) is chosen by the project bridge — this document only requires that it "exists." A non-mandatory layout sketch by *role* (active manifests, retired manifests, CCKN, completion reports, escalation log, supervision log) is given in §Recommended on-disk layout (non-mandatory) below; concrete bridge examples live in [`docs/bridges/project-memory-layout-examples.md`](bridges/project-memory-layout-examples.md).

### Tier 3: Organizational memory (long term)

**What it is:** shared memory across repos, across projects, across years:

- Organization-level roadmap SoT.
- Cross-team consumer registry.
- Organizational standards (e.g. methodology documents like those in `docs/` themselves).
- Post-mortems of past incidents.

**Lifespan:** organizational; may outlive individual repos.
**Sources:** maintained by the organization; the AI is a reader.
**Characteristics:**

- AI typically has no direct write access.
- High read cost (may span repos / platforms).
- Highest authority.

**Discipline:**

- AI **reads but does not write** this tier.
- If a session decision might affect organizational memory (e.g. a roadmap adjustment), **escalate to a human** rather than modify it autonomously.

---

## Mapping to other memory taxonomies

Other agent-engineering communities classify memory along axes that differ from this document's lifespan-based three-tier split. The following table maps the most commonly encountered taxonomies onto the canonical Tier 1 / Tier 2 / Tier 3 + CCKN axes so that a bridge document, sub-agent prompt, or external resumption note that uses different terminology can still resolve unambiguously.

The mapping is **descriptive, not prescriptive** — this document's three-tier + CCKN axes remain the canonical structure; the mapping exists so a takeover AI can translate external vocabulary onto canonical disciplines without inventing new ones.

| External taxonomy | Term | Closest tier in this document | Notes |
|---|---|---|---|
| Lifespan-based community shorthand (*core / archival / recall*) | core | Tier 1 (session) | "Core" emphasises must-be-resident facts; this document calls these the **pre-compression protection list top priority** (§Pre-compression protection list). |
| | archival | Tier 2 (project) | "Archival" emphasises slow-but-stable on-disk artifacts; this document calls these **manifests / specs / completion reports / CCKNs** (§Recommended on-disk layout). |
| | recall | Tier 3 (organizational) | "Recall" emphasises retrieval across history; this document scopes Tier 3 as cross-repo / cross-project memory with the read-only boundary. |
| Cognitive-science analogy (*working / episodic / semantic*) | working | Tier 1 (session) | Working memory ≈ context window. |
| | episodic | Tier 2 (project) — manifest history axis | Episodic ≈ "what happened in change X six months ago"; this is the temporal axis of Tier 2, surfaced via §Cross-session resumption. |
| | semantic | CCKN | Semantic memory ≈ topical knowledge reusable across episodes; CCKN is the canonical artifact for this (see [`docs/cross-change-knowledge.md`](cross-change-knowledge.md)). |
| Two-tier shorthand (*short-term / long-term*) | short-term | Tier 1 (session) | — |
| | long-term | Tier 2 + Tier 3 | The two-tier shorthand collapses the project / organizational distinction; this document keeps them separate to preserve the **organizational-memory write boundary** (§Tier 3 — *AI reads but does not write*). |

A consequence of this mapping: when an external prompt or sub-agent return slot says "promote this fact to core," "store in archival," or "this is semantic," the takeover AI translates the action onto the disciplines already specified above (§Pre-compression protection list, §Minimum write-to-disk at session end, §Cross-Change Knowledge Notes), rather than introducing a parallel storage convention.

---

## Adjacent artifact: Cross-Change Knowledge Notes

The three tiers above classify memory by **lifespan** (session / project-lifetime / organizational). A separate artifact classifies knowledge by **topic**: a Cross-Change Knowledge Note (CCKN) records a fact that applies to many changes within a project — library gotchas, third-party API quirks, platform-specific behavior — and is referenced by any Change Manifest that needs it.

CCKNs sit adjacent to Tier 2 (project memory) but are not the same thing:

| Dimension | Tier 2 project memory | CCKN |
|---|---|---|
| Organizing axis | Temporal (when was this decided / observed) | Topical (what library / API / domain does this describe) |
| Granularity | Per-change-manifest history | Per-topic note, reusable across many manifests |
| Retrieval | "What did we decide for change X six months ago?" | "What do we know about library Y right now?" |
| Staleness model | Historical — old manifests stay as they were | Live — references older than 12 months must be re-verified |

A Tier 2 manifest *references* a CCKN when the CCKN contains the reusable knowledge the manifest needs; the CCKN does not replace the manifest's own `sot_map` or `implementation_notes`. Full definition and worked example: [`docs/cross-change-knowledge.md`](cross-change-knowledge.md).

---

## What is memory-worthy

Not everything needs to be remembered. The AI should retain:

### Worth long-term memory

- **Decisions and their rationale:** "Chose A over B because X."
- **Scope boundaries:** "This system's SoT is X, owned by team Y."
- **Red lines and taboos:** "Do not add caching on this path." "This field must not be removed."
- **Already-escalated disputes and rulings:** "Previously proposed removing the legacy endpoint; user asked to retain it through next year."
- **Repeatedly-wrong assumptions:** "This enum appears to have 5 values; at runtime there are actually 2 legacy values not visible in code."

### Not worth long-term memory

- Intermediate tool outputs.
- Details of a one-shot conversation.
- Stale judgments already superseded by later decisions (mark retired, do not preserve).
- Narrative of the user's personal style (that is conversational style, not project fact).

### The test for memory-worthiness

In one line: **if the next person (human or AI) taking over would get something wrong by not knowing this, it is worth remembering.**

---

## User-supplied reference materials

A specific subclass of memory-worthy content deserves its own discipline because it is the most common silent-drift trigger across sessions: **external reference materials the user provides during the change** — design files (Figma, Canva, Sketch, or equivalents), prototype links, requirement documents, mockup screenshots, transcripts, PDFs, and any URL or file the change must conform to.

These references pass the §The test for memory-worthiness ("the next person taking over would get something wrong by not knowing this"). They differ from other memory-worthy content along two axes:

- **They originate outside the repo.** Decisions, scope boundaries, and red lines accumulate inside the workflow; reference materials arrive from external tools (design platforms, document hosts, the user's clipboard) and are not automatically captured by the AI's normal artifacts (manifest, plan, completion report).
- **They live in volatile media.** A design URL is a Tier 1 fact unless persisted; an inline PDF the user pasted is a context-window string that vanishes on compression. Without explicit capture, the reference is gone the moment the session ends.

### Mandatory capture protocol

When the user provides any external reference material, **before acting on it**, the AI must:

1. **For URL-based references** — record the URL, fetch date, accessing identity, and a substantive summary of the contents (frames / pages / sections relevant to the change, not the URL string alone). Save under a tracked path in the project's project-memory layout (e.g. a `docs/references/<topic>.md` file, or the equivalent location chosen per §Recommended on-disk layout).
2. **For file-based references** (PDFs, screenshots, design exports, transcripts, mockups pasted inline) — persist the file under a tracked path. Cite it from the active manifest's appropriate field.
3. **For inline design intent stated in chat** — extract the constraints and intent into a written reference note. The conversation will compress; the note will not.
4. **Cite the captured reference** from the active manifest, plan, or ROADMAP row so downstream roles (Reviewer, takeover sessions) discover it through the artifact, not through scrollback.

The summary is not optional. A bare URL with no extracted contents is functionally a citation-by-link to a moving target — design files are reorganised, access is revoked, hosting providers expire links. The captured summary survives all three failure modes.

### Why this is a discipline-level rule

- A Reviewer cannot verify a change against a reference it cannot see (`ai-operating-contract.md` §3 evidence quality requires the reference to be inspectable).
- A downstream session resuming the change cannot re-verify against a URL that exists only in a previous AI's compressed context — the reference becomes an invisible source of silent drift, and the symptoms surface as "the second AI ignored the design."
- Asking the user to re-paste the same material across sessions is itself a §Anti-patterns violation (*Conversation treated as SoT*) and an `ai-operating-contract.md` §7 communication-style failure (asking the user to do work the AI was supposed to do).

### Forbidden patterns

- **Act-then-capture.** Beginning implementation against a Figma / Canva / prototype URL before persisting it. Capture is a precondition, not a follow-up.
- **Citation-by-URL-only.** Recording only the URL with no summary. URLs rot and access-control changes; a captured summary survives both.
- **Conversation-as-archive.** Treating "the user pasted the design earlier in the chat" as the persistent record. The conversation is Tier 1 memory.
- **Re-prompting for the same material.** Asking the user to re-paste a reference they already provided in a previous session because the AI did not persist it the first time.

### Relationship to other rules

- [`AGENTS.md`](../AGENTS.md) §11 — the operating-contract summary; this section is its source of truth.
- [`ai-operating-contract.md`](ai-operating-contract.md) §4 Context hygiene — captures the general rule that important facts must be written to files; this section names the specific class of facts that fail the discipline most often.
- [`ai-operating-contract.md`](ai-operating-contract.md) §1 Honest uncertainty reporting + §9 Non-fabrication list — without the captured reference, every later citation of "the design says X" becomes a fabrication or an uncited assumption.
- [`multi-agent-handoff.md`](multi-agent-handoff.md) §Reviewer — the Reviewer's right to verify references is contingent on capture; an unpersisted reference is not reviewable.

---

## Minimum write-to-disk at session end

Before the session ends, or before compression hits, the AI must ensure the following have been written to files:

1. **Current phase and manifest status** — save if the manifest has changed.
2. **Actual progress on plan / spec** — tick completed items; scope changes reflected in the artifact.
3. **Open questions / blockers** — if awaiting user confirmation, produce a handoff note.
4. **Escalated-but-unresolved items** — list form, visible at first glance next round.
5. **Actual evidence paths** — not "will save later"; "is at <path>."

Only after all five may the session be ended / compressed.

---

## Pre-compression protection list

When the AI detects an imminent context compression (nearing window limits), rescue in priority order:

**Top priority (must not be dropped):**

1. The current change's `change_id` and `phase`.
2. The last 3 explicit user instructions (especially "don't do X" red lines).
3. Items escalated but unresolved.
4. Tasks remaining in the plan.
5. Any in-flight stop condition (items the AI has declared it is awaiting user decision on).

**Secondary priority (save if possible):**

6. Surface-analysis conclusions.
7. SoT map.
8. Key consumer list.

**Discardable (OK to lose in compression):**

9. Intermediate search results (re-searchable).
10. Decisions already written to files (the file is the SoT; the conversation is a copy).
11. Early exploratory discussion (already converged, no longer referenced).

Protection method: **write to files immediately** (if not already written), or **restate near the tail of the conversation** so it escapes the compression zone.

---

## Cross-session resumption

This section extends `references/resumption-protocol.md`: that document covers **how** to resume; this section covers **how memory enters** after resuming.

### Standard resumption flow

1. **Read the repo's AI entry-point file** (CLAUDE-like / AGENTS-like / GEMINI-like, per the runtime).
2. **Read the latest change manifest** (if one is in flight).
3. **Read the most recent completion report or phase snapshot.**
4. **Scan the project-memory index** and pull historical manifests relevant to the current task.
5. **Explicitly declare**: "I read these files, drew these conclusions, still have these open questions."

The last step is critical — **an AI that takes over without declaring what it read has not actually taken over.**

---

## Memory conflict resolution

When session memory, project memory, and organizational memory contradict each other:

| Conflict type | Priority | Reason |
|---------------|----------|--------|
| Project memory vs session memory | Project wins | Files are the SoT. |
| Organizational memory vs project memory | Organizational wins | Organization-level SoT is more authoritative. |
| Two project-memory items conflict | Newer and non-retired wins | Resolved via `supersedes` chain. |
| Live user instruction vs project memory | **Stop and escalate** | The user may be challenging an existing memory; a human must rule. |

**The AI must not autonomously overwrite higher-priority memory.** On conflict: flag → escalate.

---

## Memory decay

More memory is not better. Stale memory is worse than no memory (it misleads).

### Automatic decay conditions

- Manifest enters `status: retired` → its decisions are no longer active memory.
- Manifest superseded via a `supersedes` chain → historical record only; not an active reference.
- Deprecation-queue item past hard cutoff → remove "still supported" memory.

### Manual decay required

- "Owner of this SoT is team A" — if team A is dissolved, update; do not retain.
- Red lines / taboos — if organizational policy changed, update.
- Lessons from past incidents — if root cause has been systemically fixed, move from active memory to archive.

**Discipline:** every time a new task is picked up, the AI **must** verify that key memories are still true — not trust them blindly.

---

## Runtime requirements

This methodology does **not** mandate a particular storage mechanism (key-value store, vector DB, RAG, MCP, file system, etc.).
This methodology **does require**:

1. **Memory is writable** — new decisions / new facts can be persisted.
2. **Memory is retrievable** — later sessions can fetch by category.
3. **Memory is versioned** — `active` vs `retired` is distinguishable.
4. **Memory is traceable** — every entry records "who wrote it, when, and why."

Actual implementation is left to each runtime / stack bridge.

---

## Recommended on-disk layout (non-mandatory)

This section is **non-normative**. The runtime requirements above are the binding contract; what follows is a layout sketch that several stack bridges have converged on, organized by the **role** each subdirectory plays. The directory *name* is a runtime / bridge choice — what is pinned here is the role split.

A bridge that adopts a different layout is fully compliant as long as the four runtime requirements (writable, retrievable, versioned, traceable) hold.

### Role-based subdirectories

| Subdirectory role | What it holds | Memory tier |
|---|---|---|
| Active manifests | Change Manifests with `status` ∈ {`draft`, `in_progress`, `delivered`} that are still being acted on or observed (Phase 8 not yet closed). One file per `change_id`. | Tier 2 |
| Retired manifests | Change Manifests with `status: retired` (delivered + observation closed, or superseded). Read for historical context; not active references. | Tier 2 |
| Cross-Change Knowledge Notes (CCKN) | Topical notes per [`docs/cross-change-knowledge.md`](cross-change-knowledge.md). Referenced from active manifests; staleness model differs from manifest history. | Tier 2 (adjacent) |
| Completion reports | Phase 7 reports per [`skills/engineering-workflow/templates/completion-report-template.md`](../skills/engineering-workflow/templates/completion-report-template.md). One per delivered manifest. | Tier 2 |
| Escalation log | Append-only record of escalations (`change_id`, trigger, resolution, resolver, timestamp) drawn from `escalations[]` entries across all manifests. Lets the next session see "what has been escalated and how was it resolved" without scanning every manifest. | Tier 2 (index) |
| Supervision log | Append-only record of long-running sub-agent / multi-worker delegations: `keep / discard / stop` decisions per [`skills/engineering-workflow/references/long-running-delegation.md`](../skills/engineering-workflow/references/long-running-delegation.md). Distinct from the escalation log because supervision is about *which exploratory branches were retained* rather than which decisions needed human judgment. | Tier 2 (index) |
| Index | Top-level `index.md` (or equivalent) that points at the above subdirectories and gives a session a one-file overview of project memory. | Tier 2 (entry point) |

### Why role split, not directory dictate

A bridge that pins the *names* (`.foo-memory/active/`, `.foo-memory/retired/`) over-constrains downstream projects whose existing repo conventions clash with the chosen names. A bridge that pins the *roles* lets each project map roles to whatever directory structure already exists — a monorepo may collapse all six roles into one directory with naming prefixes; a polyrepo may scatter them across per-repo directories with a federated index; a Git LFS-friendly project may segregate large evidence artifacts under a separate prefix while keeping role identity through metadata.

Concrete examples — including the three patterns above — are in [`docs/bridges/project-memory-layout-examples.md`](bridges/project-memory-layout-examples.md).

### Retention and decay

Layout choice does not relax the memory-decay discipline (see §Memory decay above). Specifically:

- Retiring a manifest is a *status flip*, not a directory move. A bridge that uses a separate "retired" directory must perform the move atomically with the status flip; otherwise drift between filesystem location and `status` field becomes a SoT contradiction.
- Escalation- and supervision-log entries are append-only. A bridge that compacts them must preserve the original entry in an archive, not silently delete.
- The index is regenerated on demand. Bridges should not require humans to hand-edit the index — the four runtime requirements (writable, retrievable, versioned, traceable) imply the index is derivable from the manifests themselves.

### What this section does not specify

- A directory name. Pick one that fits your repo's conventions.
- A storage backend. Filesystem, key-value store, vector DB, RAG, MCP server — any backend that satisfies the runtime requirements is conformant.
- An access protocol. Whether project memory is read via shell, MCP tool calls, or HTTP API is a runtime decision; this layout sketch describes *what is stored*, not *how it is read*.

---

## Anti-patterns

- **Memory as log dump:** raw-store every conversation "just in case" — unfindable and unusable later.
- **Never decays:** a decision from two years ago still treated as truth.
- **Session memory mistaken for project memory:** assuming a conclusion in the context window will persist automatically.
- **AI updating organizational memory on its own:** out of scope.
- **Failing to declare what was read:** pretending "I've read that" on takeover when only filenames were scanned.
- **Conversation treated as SoT:** conversation is input; files are product; decisions are grounded in files.

---

## Relationship to other documents

- `ai-operating-contract.md` §4 — in-the-moment context hygiene; this document is the cross-session extension.
- `references/resumption-protocol.md` — the checklist for a single takeover.
- `team-org-disciplines.md` — the source of organizational memory.
- `automation-contract.md` tier 3 — drift detection helps the AI notice divergence between memory and reality.
- `multi-agent-handoff.md` — the contract for passing memory between agents.
