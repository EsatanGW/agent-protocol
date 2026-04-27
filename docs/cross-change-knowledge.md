# Cross-Change Knowledge Notes (CCKN)

> **English TL;DR**
> A lightweight artifact pattern for knowledge that applies to **many changes** in a project but does not belong to any single Change Manifest: library gotchas, third-party API quirks, platform-specific behavior, domain rules discovered once and referenced repeatedly. Distinct from the Change Manifest (which is per-change) and from session / project / organizational memory (which describe temporal tiers, not reusable knowledge). Tool-agnostic; no runtime dependency.

`ai-project-memory.md` defines the **temporal** memory tiers (session / project / organizational) — how long something should be kept and by whom. This document defines a **topical** artifact — reusable technical knowledge that spans multiple changes. The two sit next to each other, not on top of each other.

---

## Why CCKN exists

Without a cross-change knowledge artifact, every new Change Manifest re-discovers the same facts:

- "This third-party SDK silently truncates strings > 255 chars on Android."
- "The `OrderStatus` enum's legacy values are emitted by one downstream job we can't modify."
- "This payment gateway returns `2xx` with an error body in some failure modes — check body, not status."

These are **not change-specific**. They apply to any change that touches the same library / API / domain. Putting them in a Change Manifest's `implementation_notes` buries them under a single change's history; rediscovering them each time burns hours per initiative.

CCKN fills the gap: write once, reference from any manifest that needs the knowledge.

---

## What a CCKN is

A CCKN is a single Markdown file — human-authored, human-readable, plain prose. Frontmatter gives it identity; the body carries the knowledge.

### Minimal frontmatter

```yaml
---
title: [Human-readable title]
topics: [keyword, keyword, keyword]      # for future-change lookup
scope: library | domain-rule | external-api | platform-quirk
created: 2026-04-21                      # ISO 8601
updated: 2026-04-21                      # ISO 8601
supersedes: []                           # optional; list of replaced note paths
mirrors_canonical: []                    # optional; see §Mirroring canonical methodology SoT
---
```

### Required body sections

1. **Overview** — two to three sentences stating the single fact the note captures. A reader who does not read the rest of the note should still leave with the core fact.
2. **Known constraints & gotchas** — a table of `Problem | Impact | Mitigation` rows covering the behaviors that generalize.
3. **Verified references** — URL or local-path pointers with the **date last verified**. Every external claim cites a source; unverified claims are not allowed.
4. **Changelog** — append-only log of `Date | Change | Triggering change_id`. Each extension to the note is tied back to the change manifest that discovered the new information.

### Optional body sections

- **Code snippets** — minimal, illustrative, not task-specific. If the snippet exists only to explain the gotcha, it belongs; if it is copy-pasted from a specific change's implementation, it does not.
- **Related notes** — hyperlinks to other CCKNs on adjacent topics.

---

## Location and naming

CCKN location is a team decision; this document only requires three properties:

- Notes live in a discoverable directory checked into the repo (suggested: `docs/knowledge/<topic-slug>.md`).
- Note filenames are stable — renaming a CCKN requires a `supersedes:` frontmatter entry in the replacement.
- The directory is indexed somewhere a Planner can find it in under 30 seconds (a README index or a skill-layer lookup is sufficient).

---

## Mirroring canonical methodology SoT

Some CCKNs serve as a project-local distillation of canonical methodology content — for example, a CCKN summarising `docs/phase-gate-discipline.md §Rule 6` (the phase re-entry decision table) or `docs/multi-agent-handoff.md §Anti-rationalization rules` (the four hard send-back triggers). These mirror-CCKNs are useful for the same reason any reference summary is useful: a reader can re-derive the rule at the cost of one CCKN read instead of fetching, paging, and re-orienting against the full canonical doc.

The failure mode (1.27.0 codification): when canonical methodology is edited, mirror-CCKNs **drift silently**. The user has no signal that the CCKN is stale until a later change is made against the wrong rule version.

### `mirrors_canonical` frontmatter field

A CCKN that mirrors canonical methodology content **declares the mirror in frontmatter**:

```yaml
---
title: Phase Re-entry decision table (1.23.0 form: 4 destination phases)
topics: [discovery-loop, phase-reentry, planner-restart]
scope: domain-rule
created: 2026-04-23
updated: 2026-04-27
mirrors_canonical:
  - path: docs/phase-gate-discipline.md
    section: "§Rule 6 — Phase re-entry protocol"
    methodology_version: "1.23.0"
---
```

Each `mirrors_canonical` entry has:

| Field | Required | Meaning |
|---|---|---|
| `path` | yes | Repo-relative path to the canonical SoT being mirrored. Typically a file in the agent-protocol plugin's `docs/` (e.g. `docs/phase-gate-discipline.md`); may be the consumer project's own canonical content if the CCKN mirrors a project-local SoT. |
| `section` | optional | Section anchor inside the SoT that the CCKN mirrors. Useful when the SoT is large and only one section is the mirror target. |
| `methodology_version` | optional | The agent-protocol version (`1.23.0`, `1.26.0`, …) the CCKN was last synced against. Lets a stale-detection check fire on version mismatch even when no file mtime delta exists (e.g. a project pinned to 1.22.0 importing a CCKN written against 1.18.0). |

A CCKN may declare zero, one, or multiple `mirrors_canonical` entries. Zero is the default — most CCKNs document library / API / domain-rule knowledge that is not a methodology mirror, and they should not list canonical methodology paths just for cross-reference (that's what inline `see:` prose is for).

### Stale-detection signal

A CCKN declaring `mirrors_canonical` is stale when **any** of these conditions hold:

1. The SoT file at `path` has commits in its git history *after* the CCKN's `updated` date.
2. The `section` anchor is named in commits to the SoT *after* the CCKN's `updated` date.
3. The `methodology_version` does not match the agent-protocol version the consumer project is currently pinned to.

A stale CCKN is **advisory only** — citing it is not forbidden, but the citing change must either (a) refresh the CCKN to match the new canonical content, or (b) explicitly note in `implementation_notes` that the stale CCKN is being cited against an older methodology version with a justification.

### Reference implementation

A reference hook ships at `reference-implementations/hooks-claude-code/hooks/cckn-canonical-sync-check.sh` (since 1.27.0). The hook:

- Walks the project's CCKN directory (default `docs/knowledge/`; configurable via `CCKN_DIR` env var).
- For each CCKN with `mirrors_canonical` frontmatter, compares `git log -1 --format=%cI -- <path>` with the CCKN's `updated` date.
- Emits a warning (exit 2 — advisory) for each stale CCKN; never blocks (no exit 1).

Cross-runtime adapters (`hooks-cursor` / `hooks-gemini-cli` / `hooks-windsurf` / `hooks-codex`) point at the same hook script per the existing adapter pattern; no per-runtime fork required.

### What `mirrors_canonical` does *not* do

- Does not turn the CCKN into a sub-document of the canonical SoT — the CCKN remains independently authored, the canonical SoT remains independently authored, and the field declares the relationship without enforcing content equivalence.
- Does not auto-sync content. Mechanical sync of canonical content into a project-local CCKN would defeat CCKN's purpose (a project-local distillation chosen for its specific consumer audience). The hook flags drift; the human author decides whether to refresh, supersede, or accept the drift.
- Does not constrain what mirror-CCKNs can contain. A mirror-CCKN may add project-specific context, examples, or cross-references that the canonical SoT does not carry — the `mirrors_canonical` field declares the originating reference, not a containment relationship.

---

## Relation to the Change Manifest

A Change Manifest **references** CCKNs; it does not own them. Three integration points:

### 1. Manifest field — `knowledge_notes_touched`

Any change that creates a new CCKN, extends an existing CCKN, or supersedes an existing CCKN records the touched note paths in the manifest's `knowledge_notes_touched` field. This enables reverse-lookup: given a CCKN, one can trace every change that contributed to it.

```yaml
knowledge_notes_touched:
  - docs/knowledge/android-sdk-string-truncation.md
  - docs/knowledge/payment-gateway-2xx-errors.md
```

The field is optional; a change that references existing CCKNs without modifying them does not need to fill it.

### 2. Inline references inside manifest fields

Any manifest field that benefits from pre-existing knowledge cites the CCKN by path:

```yaml
sot_map:
  - info_name: OrderStatus enum
    pattern: 3
    source: services/orders/enums.py
    consumers: [...]
    desync_risk: medium
    notes: "Legacy values enumerated per see: docs/knowledge/orderstatus-legacy-values.md"
```

The `see:` convention is prose, not a schema requirement — it exists so human readers can find the reference.

### 3. Discovery-loop output

When the Implementer's Discovery loop uncovers reusable knowledge (not just a scope issue), the returning Planner creates or extends a CCKN **as part of the Phase 1 Investigate re-entry**, not as a side effect of Phase 4. The knowledge outlives the change; treating it as change-specific buries it.

---

## When to query a CCKN

CCKNs are queried **opportunistically**, not as a mandatory phase step (1.25.0 demotion from the 1.14.0 mandatory-startup-query rule). If the change's anticipated `surfaces_touched`, libraries, or external APIs overlap with topics catalogued in the CCKN directory (default: `docs/knowledge/`), the Planner reads the matching CCKNs as part of Phase 1 Investigate. If no overlap exists, no query is needed; absent directory = no-op.

The write-side timing rule is unchanged: writes happen during Phase 1 — at initial Investigate or at re-entry after a Phase 4 Discovery loop per §Relation to the Change Manifest §3. Phase 4 itself never writes.

### What to do on a match

**Fresh match** (CCKN `updated` within 12 months and every cited reference within 12 months): cite inline — typically `sot_map[].notes` with `see: docs/knowledge/<slug>.md`, or `implementation_notes`. Skip re-discovering the aspect the CCKN covers. If this change extends the CCKN, add the path to `knowledge_notes_touched[]` and append to the CCKN's changelog.

**Stale match** (CCKN or any cited reference > 12 months old per §Not a free pass for stale claims): still cite, but the referencing change **inherits the refresh obligation** — re-verify the cited references, append to the CCKN's changelog with this change's `change_id`, and add the path to `knowledge_notes_touched[]`. Silent acceptance of stale claims is forbidden by §Not a free pass for stale claims.

**Partial match**: cite what the CCKN covers; investigate the remainder normally. If the remainder generalizes to the same topic, the Planner extends the CCKN as part of this change.

**No match**: continue Phase 1 normally per `skills/engineering-workflow/phases/phase1-investigate.md`. No match is a valid outcome, not a signal to invent a speculative CCKN — CCKNs document *discovered* knowledge with verified references.

### Anti-patterns specific to query timing

| Anti-pattern | What breaks |
|---|---|
| Citing a stale CCKN without triggering the refresh obligation | Silent acceptance of unverified claims; directly contradicts §Not a free pass for stale claims |
| Creating a speculative CCKN pre-emptively "in case it is useful later" | CCKNs document *discovered* knowledge with verified references; speculative notes cannot satisfy the §Verified references requirement |

---

## What a CCKN is not

To prevent CCKN from drifting into a catch-all dumping ground, four hard limits apply:

### Not task-specific

A CCKN never names the change that produced it except in its changelog. If a note says "for the dark-mode-toggle feature we…," rewrite it until the fact stands independent of that feature, or move it back to the originating manifest's `implementation_notes`.

### Not a replacement for the SoT map

`sot_map` in a Change Manifest records **this change's authoritative sources**. A CCKN records **background knowledge about a library or domain**. If a CCKN starts describing where the authoritative source of a specific capability lives in the current change, that content belongs in `sot_map`, not in the CCKN.

### Not a substitute for Change Manifest evidence

A CCKN never counts as an `evidence_plan.artifacts` entry. Evidence is produced by running something; a CCKN is a reference. A change that tries to cite a CCKN as its verification artifact is failing verification, not passing it.

### Not a free pass for stale claims

Every verified-reference entry has a date. If the date is older than 12 months, the reference is treated as stale until re-verified. Stale CCKNs that are still being referenced by new changes must be re-verified as part of the referencing change; the cost is real and that is the point.

---

## Reviewer's role

The Reviewer has standing to inspect any CCKN cited by the manifest under review, and to:

- Reject a cited CCKN as a **task-specific pollution** (see "Not task-specific" above) and send the change back.
- Require a stale-reference refresh when a CCKN cites sources older than 12 months.
- Reject a CCKN that attempts to replace what belongs in `sot_map` or `evidence_plan.artifacts`.

Reviewer rejections of CCKN content are recorded in `review_notes` with `finding: fail` and a pointer to the offending section.

---

## Worked example

A project discovers that a particular third-party analytics SDK silently drops events when the app backgrounds on iOS 17+. The discovery happened during change `2026-03-12-ios-analytics-audit`. The resulting CCKN at `docs/knowledge/analytics-sdk-ios17-background-drop.md`:

```markdown
---
title: Analytics SDK — iOS 17 background event drop
topics: [analytics, ios, third-party-sdk, mobile]
scope: platform-quirk
created: 2026-03-12
updated: 2026-03-12
---

## Overview

The analytics SDK (v8.x) silently drops events queued during iOS 17+ background transitions because the SDK's own flush path is suspended before the system grants the background task extension. Symptom: intermittent missing events for sessions that end on app close.

## Known constraints & gotchas

| Problem | Impact | Mitigation |
|---|---|---|
| Events queued mid-background-transition lost | Metrics under-count; funnel drop-off miscalculated | Call `sdk.flushBlocking()` in `applicationDidEnterBackground` before returning |
| Only observable in production | Staging's analytics pipeline buffers differently | Cannot catch in CI; must watch post-deploy telemetry for the first 24h |

## Verified references

| Reference | Type | Last verified |
|---|---|---|
| https://sdk-vendor.example/docs/ios-lifecycle | Official doc | 2026-03-12 |
| services/mobile-ios/analytics/FlushPolicy.swift:42 | Local anchor | 2026-03-12 |

## Changelog

| Date | Change | Triggering change_id |
|---|---|---|
| 2026-03-12 | Created | 2026-03-12-ios-analytics-audit |
```

Any subsequent iOS analytics change can now reference this CCKN in its `sot_map` or `implementation_notes` without rediscovering the flush behavior, and any extension (e.g. iOS 18 validates the same or differs) appends a new changelog row with the triggering change_id.

---

## Ceremony scaling

Both query and write sides are opportunistic across all modes — neither is unconditionally mandatory. Ceremony scaling governs whether CCKN applies at all.

- **Zero-ceremony mode** — CCKN does not apply. A task small enough to skip the methodology is too small to produce reusable knowledge worth a separate artifact.
- **Lean mode** — query when the change's surfaces / libraries overlap CCKN topics; write is optional and only when discovered knowledge will obviously recur. Otherwise an `implementation_notes` entry is sufficient.
- **Full mode** — query per §When to query; the Planner *evaluates* during Phase 1 Investigate whether the change's learning content belongs in a CCKN. Writes happen during Phase 1 (initial or re-entry after a Phase 4 Discovery loop per §Relation to the Change Manifest §3); Phase 4 itself never writes. Treating every discovery as change-specific is a known drift pattern (see anti-metrics in `docs/adoption-anti-metrics.md`).

---

## See also

- [`docs/ai-project-memory.md`](ai-project-memory.md) — the three-tier temporal memory model (session / project / organizational); CCKN sits adjacent to Tier 2
- [`docs/glossary.md`](glossary.md) — "Cross-Change Knowledge Note (CCKN)" entry
- [`schemas/change-manifest.schema.yaml`](../schemas/change-manifest.schema.yaml) — `knowledge_notes_touched` optional field
- [`docs/source-of-truth-patterns.md`](source-of-truth-patterns.md) — distinguishes SoT (this change's truth) from reference knowledge (reusable fact)
