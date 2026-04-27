# Multi-Agent Handoff

> **English TL;DR**
> Defines how multiple AI agents (or AI + human co-authors) collaborate on the same change through a shared, progressively-filled Change Manifest. Names three canonical roles — Planner, Implementer, Reviewer — purely by responsibility, never by tool or model. Covers manifest progression, read/write ownership per phase, conflict escalation, and the minimum handoff checklist.

This document answers one question: **when a single change is completed by multiple agents (or multiple humans) in sequence, who can write which manifest fields at which phase, and who cannot?**

Without a contract, multi-agent collaboration degrades into:

- Each agent rewrites the whole manifest, the latest overwriting the previous.
- Downstream agents redo judgments upstream already made (e.g. re-locating SoTs).
- Nobody knows "who wrote the current manifest and whether it is true."

This document **does not name any specific agent / model / platform** — it defines role contracts only.

This is the **canonical role contract**. Runtime bridges (`agents/*.md`, `.cursor/rules/{planner,implementer,reviewer}.mdc`, `reference-implementations/roles/*.md`) translate it into runtime-specific agent configuration but do not introduce new normative rules — if a bridge states a rule this document does not, the bridge yields and this document wins. See `AGENTS.md` §File role map for the full ownership table.

---

## Three canonical roles

These roles are **defined by responsibility, not by identity.**
The same agent can play different roles in different phases; a human can play any of these roles too.

**Responsibility, not job title.** The split is by what each role *does* (investigate without writing, write under a fixed plan, audit without writing) and which tool envelope enforces it — not by which human-organization category the role nominally resembles. A pipeline shaped after a human "PM → RD → QA" handoff replicates a knowledge bottleneck the contract above is designed to break: information would flow one way, downstream roles would see only conclusions, and original intent would decay at every transfer. Three properties of the contract below prevent that — every downstream role reads every upstream artifact (no compression at the boundary), differential write permission makes audit value mechanical rather than trust-based (see Reviewer §Must not do), and the three-tier conflict resolution (§Conflict resolution) reopens the upstream phase when scope shifts rather than letting it get overwritten silently. The intent is functional capability + permission boundary + role-specific reasoning posture, not org-chart mimicry.

### Planner

**Responsibilities:**

- Read the requirement and identify surfaces.
- Build the SoT map and consumer list.
- Assess breaking-change level and rollback mode.
- Decide Lean vs Full mode.
- Produce the "front half" of the manifest: identity, surfaces, sot_map, consumers, risk.

**Must not do:**

- Write implementation code (even if it looks trivial).
- Decide implementation details beyond specifying evidence categories.

**Required fields when handing off downstream:**

- `change_id`, `title`, `phase: plan`.
- `surfaces_touched` (every entry has `role` specified).
- `sot_map` (every entry has `pattern` specified).
- `breaking_change.level` if ≥ L1.
- `rollback.mode`.
- `evidence_plan` (categories enumerated; paths not yet required).

#### Task Prompt structure

Alongside the manifest front-half, the Planner produces a **Task Prompt** for the Implementer — the working brief that scopes the Implementer's work. The Task Prompt is referenced by §Pre-handoff self-check (acceptance-criterion coverage Q1) and §Tool-permission matrix (the Planner's non-code output). It is **not** a handoff prompt — handoff prompts are session-to-session pointer blocks (≤400 / 800 words, see `docs/glossary.md` §Resume prompt); a Task Prompt is the working brief between two roles in the same change and may be longer when each column carries content the Implementer cannot derive from the manifest alone.

A Task Prompt has **six required columns**:

| Column | Content |
|---|---|
| **goal** | The intended effect on the system, in one paragraph, in terms of behavior change — not file edits. The Implementer needs intent, not a checklist; intent disambiguates judgment calls the manifest cannot. |
| **scope** | What is in / out of scope, named explicitly. For Pattern C clusters this is the cluster's `scope_files`; for non-cluster changes it names the surfaces the Implementer touches and the ones it must leave alone. |
| **input** | Where the Implementer reads from to start: manifest path, plan / test-plan paths if Full mode, prior-session context to read in full. Makes §Read-in vs write obligations §Downstream agent's minimum actions on handoff mechanically applicable. |
| **expected output** | The deliverables: code diff scope, evidence artifacts (categories from `evidence_plan`, paths to be filled by the Implementer), `implementation_notes` types likely to apply. |
| **acceptance criteria** | Numbered, individually-checkable statements verifiable against a `file:line` and an evidence artifact. §Pre-handoff self-check Q1 cites these directly. A criterion that cannot be cited against `file:line` + evidence is unverifiable — return upstream rather than write a vague AC. |
| **boundaries** | The Implementer's hard "do not do" list: don't write outside `scope_files`; don't change `breaking_change.level`; on Discovery-loop trigger, halt and return. The §Conflict resolution Tier-2 escalation exit valve is named here at spawn time, not discovered late. |

The Task Prompt is **the Planner's output**, not a manifest field. It travels alongside the manifest at spawn time — the sub-agent spawn message in runtimes with sub-agents; the human-paste prompt in runtimes without. It is not a stored artifact unless a project chooses to persist it for audit; the manifest is the durable record.

**Pattern C extension** (Full mode, multi-cluster Implementers): each cluster's Task Prompt adds `cluster_id`, `scope_files` (authoritative write boundary), `task_refs`, `evidence_refs`, the cluster-distinct `assigned_identity`, and the cluster-specific Discovery-loop-halt rule on top of the six columns. Full authority: `skills/engineering-workflow/references/cluster-parallelism.md §2`.

**Mode application.** In Lean mode the six columns collapse into the Lean-spec note's task + boundaries sections — the columns are still answered, just compactly. In Zero-ceremony mode the Planner ≡ Implementer collapse makes the Task Prompt implicit (the agent briefs itself); the columns remain the disciplined questions to answer before starting.

### Implementer

**Responsibilities:**

- Modify code per the Planner's manifest.
- Collect evidence and populate `evidence_plan.artifacts`.
- When a gap in the plan is discovered, **stop** and run the Discovery Loop (see `references/discovery-loop.md`); do not expand the manifest unilaterally.

**Must not do:**

- Re-classify surfaces / re-judge SoT without escalation.
- Change `breaking_change.level` (that is the Planner's judgment).
- Delete any fields the Planner wrote.

**Additional required fields when handing off downstream:**

- `phase: review`.
- `evidence_plan.artifacts` (every entry has a path).
- `implementation_notes` (if any drift from the plan).
- `scope_deltas` (if the Discovery Loop outcome was adopted).

#### Pre-handoff self-check

Before setting `phase: review`, answer each of these three questions in writing. A **vague** or **hedged** answer ("mostly", "should be", "I think", "looks right") is a failing answer — go back to the work and close the gap. Do not hand off.

1. **Coverage.** For every acceptance criterion in the Task Prompt, can you point to (a) a specific `file:line` that implements it AND (b) at least one verification artifact (test, migration dry-run, screenshot, log sample, etc.) whose `artifact_location` is recorded in `evidence_plan.artifacts` (boundary conditions included, not only the happy path)? A criterion missing either leg is unmet.
2. **Reference existence.** For every identifier you cited — function name, type, file path, config key, field, URL — did a code-search (or equivalent capability) confirm it actually exists in the current scope? See `docs/ai-operating-contract.md` §2a (reference-existence verification protocol) and §9 (non-fabrication list).
3. **Pattern alignment + evidence-path completion.** For every primary surface — (a) does every new structure (class, module, schema, endpoint) match the SoT pattern the manifest's `sot_map` points to (or is the delta recorded as `scope_flag` in `implementation_notes`)? AND (b) does every `evidence_plan` entry on that surface have `status: collected` with a real `artifact_location`? Either gap blocks handoff.

This is **not** a summary section — do not write prose here or in the manifest. Capture only the factual results into `implementation_notes` using existing types (`assumption_validated`, `evidence_added`, `scope_flag`, `discovery`). If any of the three questions cannot be answered with a concrete reference, treat it as a Discovery-loop trigger: stop, record, return upstream.

The global self-check in `docs/ai-operating-contract.md` §10 still applies — this section is the **role-specific** addition the Implementer must clear before advancing phase. In Lean mode the three questions still apply (they do not add ceremony — they make honest reporting checkable); in Zero-ceremony mode they collapse to a single question: "can I point at the change and the verification?"

Compaction history: this self-check originally had five questions (1.8.0 form). Q1 + Q2 (acceptance-criterion coverage + verification coverage) were merged into Q1 (coverage); Q4 + Q5 (pattern alignment + evidence-path completion) were merged into Q3. Q2 reference-existence is preserved verbatim because it is the question the merger of the other two cannot replace — it catches fabrication, not gaps. The five-question form's content is preserved 1-for-1; consumers citing "Q1 / Q2" should read it as new Q1, citing "Q4 / Q5" should read it as new Q3.

### Reviewer

**Responsibilities:**

- Verify that the Implementer's evidence actually exists and actually substantiates the claims.
- Check cross-cutting concerns (security, performance, observability, testability, errors, build-time risk).
- Decide sign-off or send back.
- Record residual risk.

**Must not do:**

- Write implementation code (if an issue is found, send back to the Implementer).
- Rewrite the Planner's or Implementer's fields (can only flag disagreement in `review_notes`).

#### Anti-rationalization rules

Even when the Reviewer is mechanically prevented from editing code, a Reviewer can still rationalize approval in language. These four conditions are **hard send-back triggers**; if any applies, do not approve:

1. **Confidence without substantiation.** You are about to assert quality without pointing at an artifact — common surface forms include "no issues found," "everything looks perfect," "looks reasonable," "should be okay," "probably works," and a `residual_risk` of "none identified" or a single sentence (real changes carry at least three evaluable risks). Replace with a concrete citation or a concrete finding; if no finding exists after a real second look, the audit is too shallow.
2. **Unsubstantiated `pass` entries.** A `review_notes` entry with `finding: pass` must cite a specific `artifact_location` from `evidence_plan` or a specific `path:line` from the diff. Hedging language ("mostly fine," "probably works") inside a `pass` cell is the same failure as Rule 1 at the cell level: an assertion without a target. A `pass` with only prose is a rubber stamp.
3. **Read-only review.** You approved without running at least one verification-only command yourself (test run, build, `git log`, migration dry-run replay, artifact open). Reading the Implementer's summary is not verification; it is trust. Verification is you, with a shell.
4. **Editing through the back door.** You found a problem and, in a runtime where the tool-write boundary is prose-only, you fixed it directly or dictated a one-line patch that the Implementer copy-pasted. In a mechanically-enforced runtime this is blocked by tool permissions; in a prose-only runtime it is an explicit rule violation. Send back, do not patch.

These rules are **heuristic failure mirrors**. They do not enumerate every way a review can go wrong; they catch the four patterns most likely to slip past even a careful Reviewer. If none of the four applies and the review still feels shallow, that is itself a signal — re-open the diff. Any one trigger applying is a **mandatory send-back, not a judgment call**.

Compaction history: these were six rules in the 1.8.0 form. Old Rule 1 (perfect-confidence) and old Rule 6 (thin residual-risk) were both forms of *narrative confidence without substantiation* — merged into new Rule 1. Old Rule 2 (hedging language) and old Rule 3 (unsubstantiated `pass`) were both *substantiation gaps* — merged into new Rule 2 with hedging called out as the same failure at the cell level. Old Rules 4 (read-only review) and 5 (back-door edit) are preserved as new Rules 3 and 4 with their original semantics. Consumers citing "Rule 3" (unsubstantiated `pass`) should read it as new Rule 2; "Rule 5" (back-door edit) as new Rule 4; "Rule 6" (thin residual-risk) as new Rule 1.

**Reference-existence sampling right.** The Reviewer may at any point pick any identifier cited in the manifest and require the Implementer to reproduce the exact code-search command that verified it. This is the Reviewer's primary defence against the plausibly-complete narrative failure mode; see `docs/ai-operating-contract.md` §2a for the verification protocol the Implementer is bound to.

**Additional required fields when handing off downstream:**

- `phase: signoff`, or return to `phase: plan / implement`.
- `review_notes`.
- `residual_risk`.
- `approvals` (sign-off record).

---

## Field read/write ownership matrix

Field "ownership" is the key to preventing agents from overwriting each other.

| Field | Planner | Implementer | Reviewer |
|-------|---------|-------------|----------|
| `change_id`, `title` | write | read | read |
| `phase` | write (advance to plan) | write (advance to review) | write (advance to signoff or send back) |
| `surfaces_touched` | write | read + flag discovery | read |
| `sot_map` | write | read | read |
| `breaking_change` | write | read + propose upgrade | read + propose upgrade |
| `rollback` | write | read | read + annotate execution risk |
| `evidence_plan.categories` | write | read | read |
| `evidence_plan.artifacts` | — | write | read + sample-check |
| `implementation_notes` | — | write | read |
| `review_notes` | — | — | write |
| `residual_risk` | draft | augment | finalize |
| `waivers` | — | propose | approve (approver must be human) |

**Rule:** except for `phase`, a downstream role cannot delete or rewrite fields written upstream.
If there is disagreement: **open a new manifest + `supersedes`**, not overwrite in place.

---

## Tool-permission matrix

Field ownership (above) declares *which manifest fields* each role may write. This matrix declares *which capability categories* the host runtime must grant each role. It is the enforcement layer that makes role separation real rather than advisory — a Reviewer without write permission cannot "rubber-stamp then quietly patch," and a Planner without write permission cannot quietly drift into coding.

Capability categories are drawn from the contract in `AGENTS.md` ("file read, code search, shell execution, sub-agent delegation"); each runtime maps them to its own tool names via a bridge (see `/how-to-use-this-plugin-in-different-runtimes` in `AGENTS.md`).

| Capability category | Planner | Implementer | Reviewer |
|---|---|---|---|
| File read | ✅ | ✅ | ✅ |
| Code search (grep / glob) | ✅ | ✅ | ✅ |
| File write / edit | ❌ | ✅ | ❌ |
| Shell execution — read-only (status, list, query) | ✅ | ✅ | ✅ |
| Shell execution — state-changing (install, migrate, deploy) | ❌ | ✅ | ❌ |
| Shell execution — verification-only (run tests, build, lint) | ✅ (optional) | ✅ | ✅ |
| Network fetch (docs lookup, API spec) | ✅ | ✅ | ✅ |
| Canonical-role delegation (spawn another Planner / Implementer / Reviewer) | ✅ (may spawn Implementers only) | ❌ | ❌ |
| Non-canonical sub-agent delegation (research / code-explorer / test-writer / reference-sampler / audit / surface-investigator — `reference-implementations/roles/role-composition-patterns.md` Patterns 1–6) | ✅ (Patterns 1, 2, 5) | ✅ (Pattern 3) | ✅ (Patterns 4, 6) |

**Why each row is shaped this way:**

- **Planner has no write tools** — forces the Planner output into the manifest (fields + Task Prompt), not into code. If the Planner could edit, the temptation to "just fix this small thing" would collapse the Plan/Implement handoff.
- **Reviewer has no write tools** — forces the Reviewer output into `review_notes` + `approvals`, not into code. If the Reviewer could edit, it would become its own Implementer and "self-approve" its fix — nullifying the external-review property. This is the single most important rule in the table.
- **Reviewer may run verification-only shell** — tests / builds / linters are non-mutating and are what the Reviewer is reviewing. Read-only shell (`git log`, `ls`, `kubectl get`) is also allowed.
- **Only Planner may delegate canonical roles** — keeps the canonical-role execution tree flat. Implementers do not recurse into further Implementers; Reviewers do not spawn other Reviewers; if decomposition of a canonical role is needed, return to Plan. This row is about the **Planner → Implementer → Reviewer chain**, not about sub-agents in general. A Planner may spawn **multiple** canonical Implementers in parallel for file-disjoint clusters per **Pattern C** in `skills/engineering-workflow/references/cluster-parallelism.md` (`reference-implementations/roles/role-composition-patterns.md` §Pattern 7); this is canonical-role multi-delegation, distinct from the non-canonical sub-agent fan-out of Patterns 5–6. Under Pattern C the anti-collusion rule applies transitively: each cluster's Implementer identity must differ from the Planner's, from every other cluster's, and from the Reviewer's identity-to-be.
- **Non-canonical sub-agents are a separate capability** — each canonical role may internally delegate to a non-canonical sub-agent per the patterns in `reference-implementations/roles/role-composition-patterns.md`. A non-canonical sub-agent inherits the canonical role's envelope (cannot receive capabilities the parent lacks), uses a distinct identity (anti-collusion), does not write manifest fields directly, and does not count as "another canonical role in the chain." The canonical role remains fully accountable for the output. Runtimes that cannot grant distinct identities cannot support this capability and must collapse it back to serial single-role work.
- **File read / code search / network fetch are universal** — every role needs to understand reality; read capabilities are never the bottleneck.

**Runtime enforcement**: each runtime bridge (Claude Code, Cursor, Gemini CLI, Windsurf, Codex, …) is expected to translate this matrix into that runtime's agent / permission mechanism. See `/how-to-use-this-plugin-in-different-runtimes` in `AGENTS.md`. Where a runtime cannot enforce a column mechanically, the bridge must document the gap and fall back to prose-only enforcement; the methodology still holds, the enforcement guarantee weakens.

### Enforcement across runtimes

Not every runtime offers the same mechanical enforcement surface. The matrix below states honestly what each runtime can enforce and where the fallback is human process.

| Runtime | Mechanism | Planner write-blocked | Reviewer write-blocked | Implementer spawn-blocked | Shipped artifact |
|---|---|---|---|---|---|
| **Claude Code** | Sub-agent definitions with `tools:` frontmatter; runtime refuses non-whitelisted tools | ✅ mechanical | ✅ mechanical | ✅ mechanical | `agents/{planner,implementer,reviewer}.md` |
| **Cursor** | Custom Mode per role (disables edit-class tools) + role-scoped rule file sets system prompt | ✅ mechanical (when Custom Mode configured) | ✅ mechanical (when Custom Mode configured) | ⚠️ partial — Cursor's spawn surface is newer; rule-based refusal is the primary guard | `.cursor/rules/{planner,implementer,reviewer}.mdc` |
| **Gemini CLI** | Persona / session prompt; distinct sessions per role | ⚠️ prose-only — CLI does not gate tool exposure per persona | ⚠️ prose-only | ⚠️ prose-only | [`reference-implementations/roles/*.md`](../reference-implementations/roles/) pasted as session instruction |
| **Windsurf** | Cascade mode / mode-scoped prompt | ⚠️ prose-only — Cascade planning-mode restrictions are advisory, not runtime-enforced on tool access | ⚠️ prose-only | ⚠️ prose-only | [`reference-implementations/roles/*.md`](../reference-implementations/roles/) pasted into the mode prompt |
| **Codex** | Per-profile `instructions` in `~/.codex/config.toml` or `--instructions` per invocation | ⚠️ prose-only — profiles do not limit tool access per se | ⚠️ prose-only | ⚠️ prose-only | [`reference-implementations/roles/*.md`](../reference-implementations/roles/) referenced from the profile |

**What ⚠️ prose-only means in practice.** The role prompt tells the agent it has no write capability. On a runtime that cannot revoke the tool, a compliant agent still refuses when asked to edit; a non-compliant agent may comply with a user request to edit. This is no different from the human-process baseline — if a human reviewer can be talked into patching their own review, the organizational rule, not the tool, is the last line of defense.

**Recommended practice when mechanical enforcement is absent:**

1. **Session isolation.** Run each role in a separate session / profile / window — the reviewer cannot accidentally edit what they cannot open.
2. **OS-level write denial.** Run the Reviewer in a working directory mounted read-only (or on a git worktree branch the reviewer has no write access to push).
3. **Two-party attestation.** Record the session ID / model identity / timestamp in `approvals` so a retroactive audit can spot an Implementer ≡ Reviewer collusion.
4. **Runtime escalation.** If the change is high-risk (security-sensitive, mode-3 rollback) and the runtime cannot mechanically enforce, escalate to a runtime that can. The methodology does not forbid this; it requires honesty about which runtime is being used.

The honest framing: **mechanical enforcement is a property of the runtime, not the methodology.** The methodology defines the roles, boundaries, and anti-collusion rule; which runtime satisfies them mechanically versus by discipline is a deployment choice.

### Capability gating by risk level

The tool-permission matrix above declares the *baseline* envelope per role. The matrix below declares **how that envelope ratchets up** as the change's risk level rises. Risk is the cross-product of `breaking_change.level` (L0–L4 per [`docs/breaking-change-framework.md`](breaking-change-framework.md)) and `rollback_mode` (1 Reversible / 2 Forward-fix / 3 Compensation per [`docs/rollback-asymmetry.md`](rollback-asymmetry.md)).

| Risk profile (`breaking_change.level` × `rollback_mode`) | Additional gating beyond the baseline matrix |
|---|---|
| L0–L1, mode 1 | None. Baseline tool-permission matrix is sufficient. |
| L0–L1, mode 2 | `evidence_plan` must include a `runbook_update` row when an alert is involved (Reviewer-side rejection signal otherwise). |
| L2, mode 1 | Reviewer **must** be a different session / model identity from the Implementer (matrix is `block`-strength on Claude Code / Cursor; prose-only on Gemini / Windsurf / Codex with the §Recommended practice fall-back). |
| L2, mode 2 | The above + `evidence_plan` must include at least one `application-driven` row per [`docs/cross-cutting-concerns.md`](cross-cutting-concerns.md) §Application-driven verification. |
| L2–L3, mode 3 | The above + `approvals[*].approver_role: human` is required for at least one approval (no all-AI approval chain). The rollback plan itself must be dry-run captured as an `evidence_plan` row before Phase 7 sign-off. |
| L3, mode 1–2 | The above (mode 2 row) + `approvals[*].approver_role: human` is required + a deprecation-timeline `breaking_change.deprecation_timeline.hard_cutoff` is set (the change cannot be silently delivered without a removal plan). |
| L3, mode 3 | Strictest: requires (a) `approver_role: human` for at least one approval; (b) a separate `security-reviewer` specialist when the change touches auth / PII / secrets ([`docs/security-supply-chain-disciplines.md`](security-supply-chain-disciplines.md)); (c) a rollback dry-run captured as evidence; (d) the change must consider Pattern C (multiple Implementer identities for file-disjoint clusters) when scope warrants. |
| L4, any mode | Strictest: all of the above + the change must be Pattern C (multiple canonical Implementers in parallel) **and** dual-Reviewer (two distinct Reviewer identities, neither of whom is any Implementer's identity). L4 is *semantic reversal*: the rule that used to hold no longer does, and downstream consumers may rely silently on the old rule. The strictness is proportional. |

**The principle.** Lower-risk changes operate under the baseline envelope. As risk rises, *more* of the role envelope's defaults convert from "may" to "must": evidence rows that were optional become required; reviewer identity that was advised becomes mandated; approvals that were AI-permissible become human-required. The schema's existing `escalations[*].trigger` enum already encodes the leaves (`rollback_mode_3`, `breaking_change_l3_or_l4`, `auth_pii_path_touched`, …); this matrix is the **routing layer** that names which trigger to raise based on the risk profile, so a Planner reading the matrix can resolve "what gating applies" deterministically without re-deriving from first principles each time.

**No new schema fields.** The matrix uses only the schema's existing fields:

- `breaking_change.level` (already required)
- `rollback_mode` (already required)
- `approvals[*].approver_role` (already constrained to enum including `human`)
- `evidence_plan[*].type` and `evidence_plan[*].tier` (already required)
- `escalations[*].trigger` (already required when present)
- The Pattern C / dual-Reviewer rows surface as `parallel_groups[*]` entries that the schema already supports.

**Anti-patterns this matrix rejects.**

- *"L3 with `approver_role: ai` because no human was available."* The L3 row makes the human approval a hard requirement, not an aspiration. Lack of availability is what `escalations[*]` exists to surface, not a bypass condition.
- *"L4 with one Implementer because Pattern C felt like ceremony."* L4's strictness is *proportional* to the blast radius of a semantic-reversal change. Down-shifting to single-Implementer is the silent scope-shrink that [`AGENTS.md §6`](../AGENTS.md) forbids.
- *"L2 with same-session Reviewer because the runtime is prose-only."* Prose-only enforcement still requires honesty about identity. Same-session means same context window; same context window means the Reviewer has read everything the Implementer wrote. The rule degrades to "different session" even on prose-only runtimes.
- *"Mode-3 without rollback dry-run because the rollback plan is documented."* Documentation is the plan; the dry-run is the evidence the plan works. Per [`docs/rollback-asymmetry.md`](rollback-asymmetry.md), Mode-3 (Compensation) is precisely the mode where untested rollback fails most expensively.

The matrix is the canonical source for how risk-level governs role envelope; runtime bridges and `agents/{planner,implementer,reviewer}.md` may *cite* it but must not redeclare it (per [`AGENTS.md §File role map`](../AGENTS.md), normative content lives in exactly one place).

---

## Single-agent anti-collusion rule

**Rule.** Within a single change, the *same* agent identity (same model invocation, same sub-agent spawn, same human account) must not play more than one of `{Planner, Implementer, Reviewer}`.

Specifically forbidden combinations, in order of risk:

1. **Implementer == Reviewer** (highest risk). An agent reviewing its own implementation has no external-review property; it is self-certification. This is the combination the tool-permission matrix exists to block.
2. **Planner == Implementer**. Allowed only in Lean mode (trivial single-surface changes, typo fixes, inline comment updates) where the Planner/Implementer distinction collapses into a single short step. In Full mode, the Planner must hand off to a separate Implementer invocation — even if "separate" means spawning a fresh sub-agent with its own context.
3. **Planner == Reviewer**. Allowed only when the Reviewer is auditing scope / plan coherence rather than implementation evidence; the risk here is circular justification rather than self-patching.

**How to satisfy the rule in practice:**

- In runtimes with sub-agents (Claude Code `Agent` tool, Gemini CLI sub-agents, Cursor agent mode), spawn each role as a distinct sub-agent invocation. The sub-agent's tool permissions are set per the tool-permission matrix above.
- In runtimes without sub-agents, satisfy the rule across sessions or across human/AI pairings (e.g. AI produces the plan; a human — or a different AI session — implements; a third party reviews).
- A human can freely play all three roles sequentially — the rule binds AI agents specifically, because AI self-review is the failure mode the methodology is designed against.

**Rule exceptions — when one agent *may* legitimately wear multiple hats:**

- **Lean mode, single-surface, L0 change** — Planner + Implementer collapse is explicitly permitted (see `skills/engineering-workflow/references/mode-decision-tree.md`).
- **Human operator** — humans are not AI; the anti-collusion rule targets AI self-review failure modes, not human judgment.
- **Emergency hotfix** — exceptions must be recorded in `waivers` with a human approver and an expiry; the next non-emergency change re-applies the rule.
- **Sandbox-fallback takeover (Pattern 8)** — when an Implementer sub-agent halts correctly on a runtime / sandbox limit (Bash blocked, CLI unavailable, network restricted) and re-spawn would face the same limit, the canonical role may take over the Implementer's Phase 4 work as "operating Implementer in sandbox fallback mode" per [`reference-implementations/roles/role-composition-patterns.md`](../reference-implementations/roles/role-composition-patterns.md) §Pattern 8. Hard invariants: (a) only the Implementer slot is relaxed — Reviewer **must** remain a separate sub-agent identity (anti-collusion's most consequential boundary is preserved); (b) sub-agent must have halted correctly (no fabricated evidence); (c) the takeover does **not** exempt the canonical role from §9 non-fabrication — every verification command runs for real, every evidence artifact is real stdout; (d) the takeover decision + commits + non-fabrication attestation are recorded in `implementation_notes[*]` with a `takeover_attestation` sub-field; (e) the Reviewer sub-agent independently re-runs every Implementer verification command and treats any detected fabrication as a HIGH-severity finding.

Violation of this rule during Full-mode changes is a Tier-2 escalation per the Conflict-resolution section: the manifest must be returned to the appropriate upstream phase and re-executed with a fresh agent identity for the downstream role.

---

## Composable specialist sub-agent roles

Some teams want a **named, registry-grade specialist** that a canonical role can fan out to — for example, an "architect" sub-agent under the Planner for SoT-pattern reasoning, a "security-reviewer" sub-agent under the Reviewer for threat-modeling audits, or a "performance-reviewer" sub-agent under the Reviewer for budget audits. The mechanism for this already exists: it is the non-canonical sub-agent composition Patterns 1–6 in [`reference-implementations/roles/role-composition-patterns.md`](../reference-implementations/roles/role-composition-patterns.md). What this section adds is a **registration discipline** that turns ad-hoc Pattern 1 / 2 / 4 / 6 invocations into a named, auditable specialist with a shared envelope contract.

Specialist roles are **not new canonical roles**. The three canonical roles (Planner / Implementer / Reviewer) are unchanged and remain the only roles whose manifest-field ownership is contractually defined. A specialist is a non-canonical sub-agent with a stable name and a fixed parent canonical role.

### What a specialist is

A specialist sub-agent role is a tuple of:

| Property | What it pins | Why |
|---|---|---|
| Name | A short, runtime-neutral identifier (`architect`, `security-reviewer`, `performance-reviewer`). No `$`-syntax in normative content. | Makes the specialist citable from a manifest's `parallel_groups[*].sub_agents[*].identity` or from a `review_notes` entry; makes recurring use auditable. |
| Parent canonical role | Exactly one of `Planner` / `Implementer` / `Reviewer`. | Specialists run under a canonical role's envelope; their work is synthesized by that role. A specialist with two parents is two specialists. |
| Composition pattern | One of Patterns 1, 2, 4, 5, 6 from `role-composition-patterns.md`. (Pattern 3 — test-writer — has its own write capability and is not a typical specialist shape.) | The pattern fixes the timing (serial vs fan-out), the capability envelope, and the synthesis step. |
| Envelope inheritance | Inherits the parent canonical role's tool-permission row from the matrix above; cannot be granted capabilities the parent lacks. | Prevents back-door capability escalation through specialist labeling. |
| Distinct identity | Specialist identity differs from every canonical role identity in the same change (anti-collusion). For Pattern 6 fan-outs, also differs from every other specialist in the same fan-out. | The anti-collusion rule's structural guarantee depends on this. |
| Output slot | Where the specialist's findings land in the manifest. Specialists do not write manifest fields directly; the parent canonical role synthesizes them into its own fields. Typical slots: `parallel_groups[*]` audit trail, `review_notes[*]` (under Reviewer parent), `implementation_notes[*]` (under Planner / Implementer parent), or a CCKN reference. | Pinning the slot prevents specialists from authoring drifted side-channel artifacts. |

A specialist that violates any row of this table is not a specialist — it is either a hidden canonical role (if it writes manifest fields), a permission escalation (if it has capabilities its parent lacks), or self-review (if it shares identity with the role it is auditing). Each case is a contract escape, not a registration question.

### Where specialists are registered

Specialists must be registered **before** they are used in a change — not declared inline per-change. The registration discipline mirrors the `custom` surface escape hatch in [`docs/surfaces.md`](surfaces.md) §Composable extension surfaces: the methodology pins *what a specialist is*, and a registry file declares *which specialists exist for this project / runtime*. There are two registry layers:

1. **Methodology-level starter registry** — [`reference-implementations/roles/specialist-roles-registry.md`](../reference-implementations/roles/specialist-roles-registry.md). Lists `architect`, `security-reviewer`, `performance-reviewer` as starter specialists with their parent role, pattern, envelope, and output slot. Non-normative reference; teams may copy entries into their own registry.
2. **Bridge / project-level registry** — declared in the project's `docs/bridges/<stack>-stack-bridge.md` or in a project-local registry file. This is where new specialists join the project's vocabulary. Like the `custom` surface, registration requires the same fields the methodology table above pins.

Per-change registration is forbidden for the same reason per-change `custom` surfaces are forbidden: a specialist that exists only for one change is unauditable across changes and gives no compounding value. If a specialist is needed only once, use Pattern 1 / 2 / 4 / 6 ad-hoc without registration; if it recurs, register it.

### Anti-collusion specifically here

The single-agent anti-collusion rule applies to specialists with a sharper edge: a specialist auditing a canonical role's output must have a different identity from that role. Specifically:

- A `security-reviewer` specialist (parent: Reviewer) auditing the Implementer's diff must differ in identity from both the Implementer and the Reviewer.
- A `architect` specialist (parent: Planner) consulted on SoT classification must differ in identity from the Planner — which is the standard Pattern 2 rule.
- A specialist *parented under* the Reviewer who finds an issue must report it as a finding for the Reviewer to weigh; it must not be re-parented to the Implementer to "just fix it." That move would route the finding around the Reviewer's audit and trigger Anti-rationalization Rule 4 (editing through the back door) at the structural level.

### What specialists do not change

- **Three canonical roles only.** Adding `architect` and `security-reviewer` to a project does not create five roles. They are sub-agents under Planner / Reviewer respectively; the field-ownership matrix above is unchanged.
- **Tool-permission matrix unchanged.** The matrix grants envelopes per canonical row; specialist envelopes inherit from their parent's row. No new row is added.
- **Manifest schema unchanged.** Specialists land in existing slots (`parallel_groups`, `review_notes`, `implementation_notes`); no new top-level field is needed.
- **Anti-collusion unchanged.** The rule still binds AI agents specifically (humans not subject), still binds within a change, and still applies transitively when fan-out is involved.

### When specialists are appropriate (vs ad-hoc Pattern 1–6)

Register a specialist when:

- The shape recurs across many changes (the same `security-reviewer` audit fan-out is invoked under most Reviewer sessions).
- The shape is non-trivial enough that authors would otherwise re-explain the envelope and output slot every time.
- The runtime supports stable named sub-agent identities (so the registered name maps to a real spawn surface).

Use ad-hoc Pattern 1 / 2 / 4 / 6 instead when:

- The decomposition is one-off (a single change's SoT puzzle warrants a single research sub-agent — register only if it recurs).
- The runtime cannot grant distinct identities — registration without identity separation collapses back into the parent role with extra indirection.

A registry that grows past ~6 specialists is itself a misuse signal — specialist sprawl is the same anti-pattern as surface sprawl, and the project should consolidate before adding more.

---

## Manifest progression phases

A manifest moves from birth to delivery through the following stages, each with a **minimum field threshold**:

```
draft → plan → test_plan → implement → review → signoff → deliver → observe
 │       │         │           │          │        │         │         │
Planner             Planner  Implementer Reviewer Reviewer Implementer  any
 picks up            or       picks up    picks up sign-off  delivery   observer
                    Tech lead
```

Minimum threshold when entering each stage:

| Entering stage | Minimum required |
|----------------|------------------|
| plan | surfaces_touched, sot_map, consumer list |
| test_plan | evidence_plan.categories, acceptance_criteria |
| implement | plan approved, test_plan exists |
| review | all evidence_plan.artifacts have paths |
| signoff | review_notes has no blocking issue |
| deliver | handoff_narrative exists |
| observe | applies only under Phase 8 trigger conditions (see `docs/post-delivery-observation.md` §Phase 8 is not mandatory) |

Threshold not met → the downstream role **must not** take over; send back upstream.

---

## Conflict resolution

When the Implementer finds a problem in the Planner's judgment, or the Reviewer finds the Implementer's evidence insufficient:

### Tier 1: annotate

Do not modify upstream fields; instead **flag disagreement** within your own field:

```yaml
implementation_notes:
  - type: planner_disagreement
    field: sot_map[0]
    original: "schema-defined"
    proposed: "transition-defined"
    rationale: "During implementation, the state transitions turned out
                to be constrained by more than just the schema."
    status: pending_review
```

### Tier 2: escalate

If the disagreement affects scope decisions (breaking level, rollback mode, SoT classification), stop and return to the previous stage:

- Implementer → return `phase: plan` for the Planner to re-evaluate.
- Reviewer → return `phase: implement` or `plan`.

Returning is not failure; it is discipline. The AI agent must **return proactively** and not expand its own role boundary to patch things over.

### Tier 3: supersede

If the entire manifest's premise is wrong (e.g. the requirement itself was misread):
**do not overwrite** — create a new manifest:

```yaml
# new manifest
change_id: 2026-04-20-voucher-expiry-v2
supersedes: [2026-04-17-voucher-expiry]
supersede_reason: "Requirement actually demands tenant-scoped expiry;
                   original manifest assumed global."
```

The original manifest is retained as `status: retired`, not deleted (historical record).

---

## Read-in vs write obligations

### Downstream agent's minimum actions on handoff

**Reading is mandatory (cannot be skipped):**

1. **Declare a resume mode** — Lazy / Targeted / Role-scoped / Full / Minimal — per `skills/engineering-workflow/references/resumption-protocol.md`. Most cross-role handoffs are **Role-scoped** (new role reading Manifest + upstream role's single output).
2. Read the Manifest handed over from upstream in full. The Manifest is the state snapshot.
3. Read only the artifacts the chosen resume mode requires. Do **not** sequential-read every artifact referenced in the Manifest; that is the session-handoff context-collapse failure mode the resume-mode system exists to prevent.
4. Compare the Manifest against repo reality (check for drift: Manifest says "A was changed" but the repo has not moved).
5. If drift exists or the Manifest is insufficient to name the next action without further reads, **stop and report** — do not widen the read set to compensate.

**Prohibited:**

- Reading only the summary because the manifest is long. Conversely: reading every artifact listed because "to be safe" — both are failures.
- Assuming upstream is correct and starting work immediately.
- Treating upstream judgment as unchallengeable.
- Accepting a verbose handoff prompt that re-explains prior phases and lists many files. A handoff prompt beyond roughly 400 words is a signal the Manifest is underfilled; fix the Manifest before proceeding (see `skills/engineering-workflow/templates/handoff-prompt-template.md`).

### Write discipline

- Every time `phase` is advanced, `last_updated` must be updated.
- `authors` array appends (not overwrites); a new agent joining leaves its identifier.
- Any Implementer or Reviewer judgment must be traceable to a specific file path / evidence / commit hash — narrative alone is not enough.

---

## Interface with human co-authors

Humans, within this contract, are also a type of "agent role" subject to the same rules.
The only differences:

- Humans can serve as an `approver` (waivers, breaking-change L3/L4).
- AI cannot.
- A human's `identifier` is a git email or team account; an AI's `identifier` must include model ID / agent name / execution timestamp so we can trace which AI version wrote it.

---

## Anti-patterns

- **Single agent does everything:** one agent writes from Plan through Deliver; the role contract is nullified.
- **Silent takeover:** downstream starts work without reading the upstream manifest.
- **Overwriting fields:** downstream edits upstream fields on disagreement (should go through conflict resolution).
- **AI self-approving:** an AI acting as Reviewer approves itself (approver must be human).
- **Long-stale manifest:** `delivered` but Phase 8 observation is empty a month later.

---

## Relationship to other documents

- `ai-operating-contract.md` — single-agent behavior contract (this document is the inter-agent contract).
- `change-manifest-spec.md` — field semantics.
- `automation-contract.md` — automated verification of each stage threshold.
- `references/resumption-protocol.md` — single-agent takeover after a session break.
- `skills/engineering-workflow/templates/manifests/change-manifest.example-multi-agent-handoff.yaml` — a full-progression example.
