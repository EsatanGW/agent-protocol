# Strategic Artifacts

> **English TL;DR**
> Agent-protocol's Change Manifest covers implementation-level work (Phase 0 through Phase 8). Work that happens *before* an implementation starts — strategy, architecture decisions, cross-team alignment, OKR-level commitments — is out of scope for the manifest but not out of scope for the methodology. Instead of inventing a new "Phase -1 strategy template," agent-protocol provides an anchor: the `strategic_parent` field on Change Manifests points at an external artifact in whatever format your organization already uses (ADR, RFC, OKR, design doc, external ticket). This document defines what the anchor field expects and what it deliberately does *not* define.

---

## What this is

Most non-trivial changes do not drop out of the sky. Something upstream — a compliance requirement, a migration mandate, an architecture review, a quarterly goal — decided that this change should happen. That upstream decision rarely fits into a single Change Manifest: it spans multiple slices of work, lives on a different timescale (quarters, not sprints), and is usually debated before any implementation is scheduled.

`strategic_parent` is the field where a Change Manifest says: "I exist because of *that* decision, recorded in *that* document."

A change has a `strategic_parent` when all of these are true:

1. The change is a slice of a larger initiative.
2. The initiative has its own authoritative document somewhere (ADR, RFC, OKR rollup, design doc, RFC-in-a-wiki, Jira epic).
3. The motivation for the current change is *not* self-contained in the manifest — a reader would need to open the parent document to understand why the change exists.

If all three are true, set `strategic_parent` in the manifest. If any is false, you don't need this field — `part_of` (internal epic ID) or plain `title` + prose context is enough.

---

## What this is NOT

Agent-protocol deliberately does **not** define:

- **The format of the parent artifact.** ADRs, RFCs, OKRs, design docs, external tickets all have mature, well-documented formats in their respective communities. Reinventing them inside this methodology would be scope creep and would fragment teams' existing processes.
- **A "Phase -1" or "Phase 0" ceremony for strategy.** The methodology's phases 0–8 cover implementation. Strategic deliberation runs on a different cadence (quarters, committees, human-only review) and does not benefit from phase-gate artifacts.
- **A template for ADRs / RFCs / etc.** Use your organization's existing templates. If you don't have one, `https://adr.github.io` (for ADRs) and [IETF RFC 2119 guidance](https://www.rfc-editor.org/rfc/rfc2119) (for RFCs) are widely used starting points — again, not maintained here.
- **A validation check on the parent artifact's contents.** Automation (see `docs/automation-contract.md` §tier-2) confirms `strategic_parent.location` is resolvable; it does not inspect what the parent says.

The anchor field is a pointer, not a container.

---

## The field

See `schemas/change-manifest.schema.yaml` for the authoritative definition. Example:

```yaml
strategic_parent:
  kind: adr
  location: docs/adr/0042-auth-compliance-rewrite.md
  summary: >
    Comply with 2026 audit requirements by rewriting session-token storage
    off legacy in-memory cache onto an audited KV store. This manifest
    covers the token-store slice only; migration, client-rollout, and
    auth-provider swap are separate manifests under the same initiative_id.
  initiative_id: AUTH-REWRITE-2026Q2
```

### Field semantics

| Field | Required | Purpose |
|-------|----------|---------|
| `kind` | yes | Category so consumers know what format to expect. Enum: `adr` / `rfc` / `okr` / `design_doc` / `external_ticket` / `other`. |
| `location` | yes | Repo-relative path, absolute path, or URL. Must resolve; an unresolvable location is a drift signal. |
| `summary` | no (but recommended) | ≤ 400 chars on *what the parent requires of this change*. Not a title of the parent doc — a motivation sentence. |
| `initiative_id` | no | Stable identifier shared across every manifest under the same parent. Enables aggregation queries. |

### Aggregation

When `initiative_id` is set on multiple manifests, it becomes possible to answer questions like:

- "Show me every Change Manifest delivered under `AUTH-REWRITE-2026Q2`."
- "What's the rollback exposure of the entire `MOBILE-RELEASE-BRANCH-2026-04` initiative?"
- "Which manifests under `GDPR-COMPLIANCE-PHASE-2` are still in `phase: implement`?"

Aggregation is out of scope for this document — any tool that reads the schema can build it. The anchor is enough.

---

## Relationship to `part_of`

Both fields describe "this change is part of something bigger" but answer different questions:

| Field | Answers | Example |
|-------|---------|---------|
| `part_of` | *Which internal epic does this slice belong to?* | `2026-Q2-auth-overhaul` |
| `strategic_parent` | *Which external authoritative decision motivates this change?* | `docs/adr/0042-auth-compliance-rewrite.md` |

They are **complementary, not alternatives**. A change can have both: `part_of: 2026-Q2-auth-overhaul` (internal epic ID used by the team's tracker) and `strategic_parent: { kind: adr, location: docs/adr/0042-... }` (the decision record the epic was scoped against).

- Use `part_of` alone when the internal epic is self-documenting (team-internal plan, small initiative).
- Use `strategic_parent` alone when the external decision is the only scaffolding (the epic is just "do what the ADR says").
- Use both when an internal epic implements an external decision.

---

## Anti-patterns

- **Back-filling `strategic_parent` with the PR description URL.** The anchor should point at an *authoritative* decision document, not a narration of work-in-progress.
- **`kind: other` without a reason.** If you reach for `other`, first check whether the artifact is really one of the named kinds under a different name. ADRs are still ADRs whether called "Decision Record," "Tech Decision," or "Architecture Note."
- **Setting `strategic_parent` on trivial Lean-mode changes.** The field is for work that *requires* external context to understand. Bug fixes, typo corrections, dependency bumps don't need it — they're self-contained.
- **Treating `strategic_parent.location` as documentation.** Consumers (reviewers, later agents, future-you) will open the parent. If the parent is a stub, a Slack thread, or a dead link, the reference is worse than useless. Keep strategic artifacts current or do not cite them.

---

## Relationship to other documents

- `schemas/change-manifest.schema.yaml` — authoritative field definition.
- `docs/change-manifest-spec.md` — field-level semantics for the manifest (this field's entry).
- `docs/change-decomposition.md` — how to split large changes across manifests; strategic parent is the natural grouping anchor when one initiative spans multiple decompositions.
- `docs/team-org-disciplines.md` — how strategic decisions propagate through consumer registry and deprecation queue at team / org scale.
- `docs/phase-gate-discipline.md` — the ROADMAP initiative-level artifact is closer in spirit to a strategic parent than a single Change Manifest; ROADMAP rows can reference the same `initiative_id` as manifests.
