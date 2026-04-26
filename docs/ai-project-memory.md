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
