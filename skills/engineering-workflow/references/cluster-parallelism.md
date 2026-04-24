# Cluster Parallelism (Pattern C)

A **Phase 4** parallelism discipline: the Planner declares 2–4 file-disjoint implementation clusters at plan approval, then spawns one canonical Implementer per cluster in a single batch. Each Implementer writes code and collects evidence within its cluster scope. A single Reviewer downstream performs a cross-cluster cross-cutting gap check.

**Why this document exists.** Patterns A and B (`parallelization-patterns.md`) parallelize work by spawning **non-canonical sub-agents** that return findings for the canonical role to synthesize. That mechanism does not apply to implementation: implementation is the canonical Implementer's *own* work, not something a sub-agent returns findings about. The existing `multi-agent-handoff.md` tool-permission matrix already allows Planner-to-Implementer canonical delegation, but until now there has been no discipline for using it *in parallel* safely. This document defines that discipline. Phase 4 becomes the first phase where a parallel pattern exists that is *canonical-role multi-delegation*, not sub-agent fan-out.

**Scope.** Full mode only. Lean and Zero-ceremony have neither the scale nor the artifact trail that Pattern C's coordination requires.

**Relationship to existing patterns.**

| Mechanism | What parallelizes | Who spawns | Who writes manifest |
|---|---|---|---|
| Pattern A (parallelization-patterns.md) | Investigation (Phase 1) | Planner | Planner, from sub-agent findings |
| Pattern B (parallelization-patterns.md) | Audit (Phase 5) | Reviewer | Reviewer, from sub-agent findings |
| **Pattern C (this doc)** | **Implementation (Phase 4)** | **Planner** | **Each canonical Implementer writes its own cluster's fields** |
| Phase overlap zones (phase-overlap-zones.md) | Prep across phase boundaries | — | Canonical role, after prior gate passes |

Pattern C is the only parallel pattern where canonical role identities are spawned in multiples. A and B spawn non-canonical sub-agents.

---

## The core rule

A Pattern C execution has **four invariants**:

1. **File-disjoint scope per cluster.** No two clusters declare `scope_files` patterns that could resolve to the same file. Cluster boundaries are *files*, not concerns — if two clusters "touch the same schema in different ways," that is not disjoint and must be serialized.
2. **Single-batch spawn.** All Implementer invocations are initiated in one tool-call batch per the cache-window rule (`parallelization-patterns.md` §Cache-window rule, applied to canonical delegation). Serial spawn erases the parallelization benefit.
3. **Any cluster's Discovery halts all clusters.** If any Implementer hits the Discovery loop (plan gap, unfamiliar SoT, missing surface), the cluster flips to `status: blocked_discovery` and the Planner pauses all other clusters until Phase 2 is re-opened and the plan is corrected.
4. **Reviewer performs a cross-cluster cross-cutting gap check.** Cluster intersections are where issues hide: cluster A's API field matches cluster B's frontend call, but cluster C's analytics event still references the old field name. No single Implementer will catch that — only the Reviewer, looking at the union, will.

A change that violates any of these has used Pattern C in name only.

---

## When to use Pattern C

All of these must hold:

- The change is Full mode.
- The Phase 2 plan has tasks that decompose into 2–4 genuinely independent clusters.
- The clusters can be pair-wise file-disjoint (no shared file writes).
- The canonical Implementer envelope is acceptable per cluster (this is not a sub-agent envelope reduction — each cluster's Implementer has full write + shell per `multi-agent-handoff.md §Tool-permission matrix`).
- The total serial Phase 4 cost is high enough that parallelization saves more than the coordination overhead (rule of thumb: ≥30 minutes of Phase 4 work per cluster; smaller changes are not worth the setup).

## When NOT to use Pattern C

Any of these is a block:

- **Lean or Zero-ceremony.** Same exclusion as Patterns A/B — parallelism is a Full-mode optimization, never Lean ceremony.
- **Clusters cannot be file-disjoint.** Even "mostly disjoint with one shared file" is not disjoint — merge conflicts become plan drift become gate bypass.
- **Shared test infrastructure that updates per-cluster.** If cluster A's DB migration needs to finish before cluster B's API tests can pass, the clusters are not independent — serialize.
- **Fewer than 2 or more than 4 clusters.** 1 is not parallel; >4 loses cross-cutting visibility at Review just as with Patterns A/B.
- **Changes where the Implementer envelope would need to differ per cluster** (e.g. one cluster needs prod credentials, one does not). Pattern C assumes homogeneous envelopes; heterogeneous-envelope delegation is outside scope.

---

## Execution shape

### 1. Planner declares clusters at Phase 2 plan

The Planner writes `implementation_clusters` per `schemas/change-manifest.schema.yaml`. Each cluster carries:

- `cluster_id` — stable identifier within the change.
- `label` — short descriptive name (e.g. `db-migration`, `api-field`, `frontend-copy`).
- `scope_files` — array of glob patterns the cluster's Implementer may modify. **Cross-cluster pair-wise disjoint.** The validator enforces this.
- `scope_surfaces` — optional narrative tag; surfaces may overlap across clusters (e.g. both A and B touch `system-interface` but in non-overlapping files) provided `scope_files` remain disjoint.
- `task_refs` — references to plan tasks covered by this cluster.
- `evidence_refs` — references to `evidence_plan.artifacts[]` entries the cluster is responsible for populating.
- `independence_rationale` — narrative justification. "No shared state, no ordering dependency, no overlapping test infrastructure" is the honest shape; if the rationale sounds hand-wavy on re-read, the clusters are not independent.
- `assigned_identity` — filled at spawn time (pending until then).
- `status` — `pending` at declaration.

### 2. Planner spawns all Implementers in one batch

Single-batch spawn is required per the cache-window rule. Each Implementer is a **full canonical Implementer** with full Implementer tool envelope (read, write, shell). The Task Prompt per cluster contains:

- The cluster's `cluster_id` and `scope_files` (authoritative write boundary).
- The cluster's `task_refs` from the plan.
- The cluster's `evidence_refs` (evidence entries this Implementer owns and must populate).
- An identity distinct from the Planner's, distinct from every other cluster's `assigned_identity`, and distinct from the Reviewer's identity-to-be (anti-collusion transitively).
- An explicit "**do not write outside `scope_files`**" boundary.
- An explicit "**on Discovery-loop trigger, advance `status: blocked_discovery` and return — do not continue**" boundary.

Each spawned Implementer, at spawn time, causes `implementation_clusters[i].status` to flip `pending → in_progress` and `assigned_identity` to be recorded.

### 3. Implementers work independently within cluster scope

Each Implementer runs its own Phase 4:

- Implements against its cluster's `task_refs`.
- Runs verification.
- Populates `evidence_plan.artifacts[]` entries tagged to this cluster (schema extension: evidence entries gain an optional `cluster_id` field).
- Writes `implementation_notes[]` entries tagged with `cluster_id`.
- Does **not** touch other clusters' fields or files.
- Completes the Implementer pre-handoff self-check (`docs/multi-agent-handoff.md` §Pre-handoff self-check).
- Flips its cluster's `status: in_progress → completed` when done.

### 4. Discovery-loop handling

If any Implementer hits the Discovery loop (missing surface, SoT mis-classification, infeasible approach), it:

- Flips its cluster `status: in_progress → blocked_discovery`.
- Writes an `implementation_notes` entry with `type: discovery` and `cluster_id`.
- Returns without further writes.

The Planner (monitoring cluster statuses) then:

- Pauses any other clusters still `in_progress` (no new manifest writes; work-in-progress files stay uncommitted).
- Reopens Phase 2 per `docs/phase-gate-discipline.md` Rule 6.
- After re-plan, decides whether to restart all clusters (plan materially changed) or resume from the blocked one (plan delta did not affect others).

Default: restart all. Clusters that "kept going" against an invalidated plan produce the worst form of gate bypass — silently-wrong code that passes the cluster's local verification but breaks cross-cluster assumptions.

### 5. Planner assembles and spawns Reviewer

Once every cluster's `status == completed`:

- Planner records the fan-out in `parallel_groups` with `pattern: C_cluster_implementers`. Unlike Patterns A/B, `synthesis.manifest_fields_written` for Pattern C is expected to be `[]` or a short list (`implementation_clusters[*].status`, aggregated field updates) — Implementers wrote their own substantive fields, so the synthesis step is assembly, not content generation. This is recorded honestly rather than padded to look like Pattern A/B-style synthesis.
- Planner advances `phase: implement → review`.
- Planner spawns a single Reviewer canonical role.

### 6. Reviewer cross-cluster cross-cutting gap check

The Reviewer reads the full manifest with all clusters' evidence and asks:

- **Cluster-intersection questions.** Do A's schema changes match B's API consumer expectations? Does C's telemetry reference the new or the old field name? Do A/B/C's migration ordering work end-to-end?
- **Cross-cutting dimension questions.** Did any single cluster's security / performance / observability / testability diligence miss an effect that emerges from the combination?
- **Acceptance-criterion coverage across clusters.** Every AC in the original plan maps to at least one cluster's evidence; no AC is orphaned between clusters.
- **Evidence-tier consistency.** Tier-critical evidence (`schemas/change-manifest.schema.yaml §evidence_plan.tier`) is present in the right cluster's evidence. A cluster that silently downgraded tier for its evidence is a Tier-2 escalation.

Findings go into `review_notes` as usual. A finding whose root cause is "cluster A and cluster B disagreed on X" specifically names the two clusters in the note.

---

## Why each invariant is needed

| Invariant | Specific failure prevented |
|---|---|
| File-disjoint scope | Merge conflicts → implicit serialization + unclear ownership of the conflicted file |
| Single-batch spawn | Cache-window cost hits per-spawn, erasing the parallelization benefit (same argument as Patterns A/B) |
| Discovery-halt-all-clusters | Other clusters building on invalidated plan state → silently-wrong code with clean local verification |
| Cross-cluster cross-cutting gap check | Issues visible only at the intersection of two clusters — the specific failure mode parallel implementation introduces, analogous to §Cross-cutting gap check in Patterns A/B |

---

## Anti-patterns

| Anti-pattern | What breaks |
|---|---|
| Clusters that "mostly" disjoint file scopes, with one shared file | File-disjoint invariant is broken; "mostly" is not disjoint |
| Spawning clusters serially instead of in a single batch | Cache-window rule broken; cost paid without benefit |
| One cluster's Discovery-loop trigger silently ignored by the Planner while other clusters continue | Default-halt-all invariant broken; other clusters produce work based on an invalidated plan |
| Reviewer audits each cluster's evidence independently without a cross-cluster gap check | The exact failure mode Pattern C introduces is left uncaught; degrades to "three separate partial reviews," not one integrated review |
| Cluster Implementer writes to files outside `scope_files` | Cluster boundary violated; later merge produces conflict or silent overwrite |
| >4 clusters per change | Cross-cutting visibility at Review degrades past 3–4 (same reason Patterns A/B cap at 4) |
| Pattern C used in Lean mode | Explicit mode exclusion; ceremony pretending to be optimization |
| Pattern C where the Implementer envelope would need to vary per cluster | Pattern C assumes homogeneous canonical-Implementer envelope; heterogeneous-envelope delegation is a different problem |
| Implementer sub-agent identity shared between two clusters | Anti-collusion violated transitively; a cluster reviewing (even implicitly) its sibling's output is self-review |
| Writing `implementation_clusters` into the manifest **after** spawning Implementers | The declaration is the contract between Planner and each Implementer; retroactive declaration breaks the Task Prompt honesty |

---

## Relation to other documents

| Document | How Pattern C relates |
|---|---|
| `.github/scripts/validate-cluster-disjointness.py` | The repo-level CI validator that enforces file-disjoint `scope_files` across clusters. Runs automatically on push / pull-request via `.github/workflows/validate.yml` (`cluster-disjointness` job) |
| `docs/multi-agent-handoff.md §Tool-permission matrix` | Canonical Planner-to-Implementer delegation is the existing permission Pattern C uses; no new permission introduced |
| `docs/multi-agent-handoff.md §Single-agent anti-collusion rule` | Applies per-cluster transitively: each cluster identity distinct from Planner, Reviewer, and every other cluster |
| `reference-implementations/roles/role-composition-patterns.md` Pattern 7 | Non-normative companion — acknowledges that Pattern C exists alongside Patterns 1–6 but is canonical-role multi-delegation, not sub-agent composition |
| `skills/engineering-workflow/references/parallelization-patterns.md` | Pattern C is listed in the phase-applicability table as Phase 4's parallel pattern. The two documents cover different mechanisms |
| `docs/phase-gate-discipline.md` Rule 6 (phase re-entry) | Invoked when any cluster triggers Discovery-loop halt |
| `schemas/change-manifest.schema.yaml §implementation_clusters` + §parallel_groups | `implementation_clusters` is the substantive record of Pattern C; `parallel_groups` with `pattern: C_cluster_implementers` is the audit breadcrumb that points at it |
| `agents/planner.md`, `agents/implementer.md` | Role files gain "Optional: Pattern C" sections naming the Planner's declare-and-spawn duties and the Implementer's cluster-scoped execution duty |
| `skills/engineering-workflow/references/phase-overlap-zones.md` | Orthogonal: Pattern C is within-Phase-4 parallelism; overlap zones are between-phase prep. The two stack — e.g. Pattern C's Phase 4 runs in parallel while Phase 5 Reviewer's context pack is being pre-distilled in overlap |
| `skills/engineering-workflow/references/long-running-delegation.md` | The Planner's monitoring of cluster statuses (§4 halt trigger and §5 completion detection) is a D3 non-idle instance — the Planner reads each cluster's session-scoped status artifact (D2) rather than polling by re-invocation. A cluster whose planned scope would exceed one cache window is a D1 decomposition problem, not a halt problem |

---

## What this document is not

- **Not a license to spawn canonical Implementers without cluster scope.** Pattern C is specifically about file-disjoint clusters declared at plan time, not about "just spawn 4 Implementers and split the work."
- **Not a replacement for Pattern 3 (serial Implementer + test-writer sub-agent).** Pattern 3 decomposes *within* a single cluster's Implementer (serial helper sub-agent). Pattern C parallelizes *across* clusters. Both may occur on the same change: Pattern C at the cluster level, Pattern 3 within one cluster's Implementer.
- **Not a way to route around the Implementer's Pre-handoff self-check.** Each cluster's Implementer still runs the 5-question self-check in `docs/multi-agent-handoff.md` §Pre-handoff self-check; there are no abbreviated cluster-scoped versions.
- **Not a way to skip cross-cutting concerns.** Each cluster runs its own cross-cutting checks per `docs/cross-cutting-concerns.md`, and the Reviewer then runs the cross-cluster gap check on top. The gap check is additional, not a replacement.
- **Not intended for general use.** Default on every Full-mode change is single-Implementer serial execution. Pattern C is an opt-in speedup for changes where clusters genuinely decompose and the wall-clock cost of serial is high enough to justify the coordination overhead.
