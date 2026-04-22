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

CCKNs serve two asymmetric operations: **write** (when a change produces reusable knowledge — covered in §Relation to the Change Manifest §3 and §Ceremony scaling) and **query** (when a change might benefit from pre-existing reusable knowledge). This section defines the query-side timing rule. Without it, the write side produces notes no one reads — the cost CCKN exists to eliminate is paid anyway.

The rule is: **query at Phase 1 Investigate startup; write during Phase 1 — at initial Investigate per §Ceremony scaling, or at re-entry after a Phase 4 Discovery loop per §Relation to the Change Manifest §3. Phase 4 Discovery triggers re-entry; it does not itself write.**

### At Phase 1 Investigate startup

Before tracing the main flow — i.e. as step 0 of Phase 1 — the Planner (or the Phase-1 investigator sub-agent under Pattern A in `skills/engineering-workflow/references/parallelization-patterns.md`) greps the repo's CCKN directory (default: `docs/knowledge/` per §Location and naming) for `topics` overlap with:

- The change's anticipated `surfaces_touched`.
- Any `uncontrolled_interfaces` the change will depend on (third-party SDKs, external APIs, platform behaviors).
- The libraries, frameworks, or domain rules the change will touch.

One grep, one pass, before the investigation proper begins. If the CCKN directory does not exist (e.g. first use of this methodology in a repo), the grep is a no-op and the change proceeds as if no match was found — an absent directory is not a failure. Querying late (e.g. at Phase 4 mid-implementation) has the same failure mode as late schema discovery — the investigation has already decided against the fact the CCKN would have supplied, and the cost of Phase 1 from zero has already been paid.

### What to do on a match

**Fresh match** (CCKN `updated` within 12 months and every `Verified references.Last verified` row within 12 months):

- Cite the CCKN inline where its content is load-bearing for the Phase 1 output — typically in `sot_map[].notes` (with the prose `see: docs/knowledge/<slug>.md` convention) or in a later phase's `implementation_notes`.
- Skip re-discovery of the aspect the CCKN covers. The Phase 1 output records "covered by CCKN `<path>`" as the impact row for that aspect.
- If this change also extends the CCKN (new gotcha row, new verified reference, etc.), add the note path to `knowledge_notes_touched[]` and append to the CCKN's changelog.

**Stale match** (the CCKN itself or any cited reference is > 12 months old per §Not a free pass for stale claims):

- Still cite, but the referencing change inherits the refresh obligation. Refreshing the stale references is part of this change's Phase 1 work, not a deferred follow-up.
- Log the refresh in the CCKN's changelog with this change's `change_id` and add the CCKN path to `knowledge_notes_touched[]`. This is mandatory — silent acceptance of stale claims is the anti-pattern §Not a free pass for stale claims specifically forbids.

**Partial match** (the CCKN covers some but not all of the relevant facet):

- Cite for what it covers; Phase 1 still investigates the uncovered portion normally.
- If the investigation of the uncovered portion turns up additional reusable knowledge that generalizes to the same topic, the Planner extends the CCKN (new changelog row, new gotcha / reference / constraint) as part of this change and records the path in `knowledge_notes_touched[]`.

### What to do on no match

Continue with the full Phase 1 investigation per `skills/engineering-workflow/phases/phase1-investigate.md`. The write-side rule stated in the summary above still applies — no match does not unlock an end-of-change write path. If Phase 1 itself surfaces reusable knowledge, the Planner writes the CCKN during this Phase 1 per §Ceremony scaling. If a Phase 4 Discovery loop later uncovers reusable knowledge, the returning Planner writes during Phase 1 re-entry per §Relation to the Change Manifest §3. If neither happens, this change produces no CCKN.

No match is a valid outcome, not a signal to invent a shallow CCKN pre-emptively. CCKNs are for *discovered* reusable knowledge, not for speculatively-future knowledge.

### Anti-patterns specific to query timing

| Anti-pattern | What breaks |
|---|---|
| Skipping the startup query and re-discovering a fact a CCKN already documents | The cost CCKN exists to eliminate is paid anyway; CCKN infrastructure sits unused on the query side |
| Querying mid-implementation (Phase 4) instead of at Phase 1 startup | Cost paid twice — investigation happened without the CCKN, then the CCKN is cited retroactively after decisions that should have been informed by it are already made |
| Citing a stale CCKN without triggering the refresh obligation | Silent acceptance of unverified claims; directly contradicts §Not a free pass for stale claims |
| Using CCKN query absence as license to skip Phase 1 investigation | CCKN covers *reusable* facts; the change's *specific* SoT map, consumer list, and impact are still Phase 1 deliverables |
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

Ceremony scaling governs the **write** side. The Phase 1 startup **query** (§When to query) is a cheap grep and runs in every non-Zero-ceremony change regardless of tier — the table below states where the query also turns off.

- **Zero-ceremony mode** — CCKN does not apply: neither the Phase 1 startup query nor the write side runs. A task small enough to skip the methodology is too small to produce reusable knowledge worth a separate artifact.
- **Lean mode** — the Phase 1 startup query still runs; a CCKN *write* is optional. If the discovered knowledge will obviously recur (e.g. a documented third-party quirk), create the note during the same Phase 1 that discovered it, or — if discovery only happens at a Phase 4 Discovery loop — at Phase 1 re-entry per §Relation to the Change Manifest §3. If the knowledge is purely local, an `implementation_notes` entry is sufficient and no CCKN is written.
- **Full mode** — the Phase 1 startup query runs. The Planner *evaluates* during Phase 1 Investigate whether the change's learning content belongs in a CCKN; a positive evaluation then *writes* under one of two timings: (a) if the knowledge is already available at Phase 1 (e.g. the change itself is *about* documenting a library quirk), the CCKN is written during this Phase 1, or (b) if the knowledge only surfaces later, write is deferred to Phase 1 re-entry after a Phase 4 Discovery loop per §Relation to the Change Manifest §3 — Phase 4 itself never writes. Treating every discovery as change-specific is a known drift pattern (see the anti-metrics in `docs/adoption-anti-metrics.md`).

---

## See also

- [`docs/ai-project-memory.md`](ai-project-memory.md) — the three-tier temporal memory model (session / project / organizational); CCKN sits adjacent to Tier 2
- [`docs/glossary.md`](glossary.md) — "Cross-Change Knowledge Note (CCKN)" entry
- [`schemas/change-manifest.schema.yaml`](../schemas/change-manifest.schema.yaml) — `knowledge_notes_touched` optional field
- [`docs/source-of-truth-patterns.md`](source-of-truth-patterns.md) — distinguishes SoT (this change's truth) from reference knowledge (reusable fact)
