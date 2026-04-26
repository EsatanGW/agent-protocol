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

## Reading-order guide — three pairs that look duplicative but are not

Several newer rules sit next to older rules that look similar. Readers who skim these easily conclude "I am being asked to do the same thing twice" and drop one. Each pair has a specific distinction; neither member replaces the other.

### Pair 1 — Global self-check vs Pre-handoff self-check

| Layer | Where | When it fires | Scope |
|---|---|---|---|
| Global self-check | [`docs/ai-operating-contract.md`](ai-operating-contract.md) §10 (6 questions) | Any AI co-author, any delivery boundary | Catches fabricated completion claims, hidden scope expansion, rationalized failure |
| Pre-handoff self-check | §Pre-handoff self-check below (5 questions) | Implementer only, before advancing `phase: review` | Catches acceptance-criterion gaps, unverified references, unfilled evidence paths |

**Both apply.** The global check asks "is this delivery honest?"; the Implementer-specific check asks "is the Implementer's specific work complete enough to hand off?" An Implementer must pass both; other roles only pass the global one.

### Pair 2 — Phase re-entry vs Breaking-change migration path

| Layer | Where | Question it answers |
|---|---|---|
| Phase re-entry | [`docs/phase-gate-discipline.md`](phase-gate-discipline.md) Rule 6 | "Which earlier phase must I re-open to fix what I just discovered?" |
| Breaking-change migration path | [`docs/breaking-change-framework.md`](breaking-change-framework.md) Paths A / B / C | "How do new and old coexist across the shipping boundary?" |

**Both may apply to the same change.** Re-entry is about **internal workflow bookkeeping** (which ROADMAP row to open, which manifest fields to rewrite); migration path is about **external consumer handling** (gray rollout, coexistence, deprecation cycle). A change that discovers a higher breaking-change level mid-implementation triggers **both**: re-enter Phase 1 to rewrite `breaking_change`, **and** pick a migration path from Paths A / B / C for the shipping plan.

### Pair 3 — Anti-rationalization rules vs "Rubber-stamp is not a finding"

| Layer | Where | What it does |
|---|---|---|
| "Rubber-stamp is not a finding" | Reviewer's **Must not do** list below | Principle statement — every `pass` cites an artifact |
| Anti-rationalization rules (6 triggers) | §Anti-rationalization rules below | Mechanical heuristic — if any of 6 observable patterns appears, the review is reopened |

**Rules refine the principle, do not replace it.** The principle explains the intent; the 6 rules catch the specific language / behavior patterns most likely to slip past even a careful Reviewer. A Reviewer who only remembers the principle can still rationalize quietly; a Reviewer who only remembers the rules may miss a seventh pattern not listed. Both live together.

### The general instinct

If two rules look redundant, read each one's **trigger condition** carefully. The methodology's newer rules are almost always either (a) a **narrower trigger** for a specific role or phase, or (b) a **mechanical heuristic** for catching a failure mode the older principle couldn't enforce mechanically. Neither replaces the other — they stack.

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

Before setting `phase: review`, answer each of these five questions in writing. A **vague** or **hedged** answer ("mostly", "should be", "I think", "looks right") is a failing answer — go back to the work and close the gap. Do not hand off.

1. **Acceptance-criterion coverage.** For every acceptance criterion in the Task Prompt, can you point to a specific `file:line` that implements it? A criterion without a concrete code location is unmet.
2. **Verification coverage.** For every acceptance criterion, is there at least one verification artifact (test, migration dry-run, screenshot, log sample, etc.) whose `artifact_location` is recorded in `evidence_plan.artifacts`? Boundary conditions included, not only the happy path.
3. **Reference existence.** For every identifier you cited — function name, type, file path, config key, field, URL — did a code-search (or equivalent capability) confirm it actually exists in the current scope? See the reference-existence verification protocol in `docs/ai-operating-contract.md` and the non-fabrication list in that same document.
4. **Pattern alignment.** For every new structure (class, module, schema, endpoint), does it match the SoT pattern the manifest's `sot_map` points to, or is the delta recorded as `scope_flag` in `implementation_notes`?
5. **Evidence-path completion.** Does every `evidence_plan` entry on a primary surface have `status: collected` and a real `artifact_location`? Any entry still `planned` on a primary surface blocks handoff.

This is **not** a summary section — do not write prose here or in the manifest. Capture only the factual results into `implementation_notes` using existing types (`assumption_validated`, `evidence_added`, `scope_flag`, `discovery`). If any of the five questions cannot be answered with a concrete reference, treat it as a Discovery-loop trigger: stop, record, return upstream.

The global self-check in `docs/ai-operating-contract.md` §10 still applies — this section is the **role-specific** addition the Implementer must clear before advancing phase. In Lean mode the five questions still apply (they do not add ceremony — they make honest reporting checkable); in Zero-ceremony mode they collapse to a single question: "can I point at the change and the verification?"

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

Even when the Reviewer is mechanically prevented from editing code, a Reviewer can still rationalize approval in language. These six conditions are **hard send-back triggers**; if any applies, do not approve:

1. **Perfect-confidence hallucination.** You are about to write "no issues found," "everything looks perfect," or equivalent. Real changes carry residual risk; failing to find any usually means you did not look hard enough. Return to the diff and look again.
2. **Hedging language.** You are about to use "mostly fine," "looks reasonable," "should be okay," "probably works," or any phrase that asserts quality without pointing at an artifact. Replace with a concrete citation or a concrete finding.
3. **Unsubstantiated `pass` entries.** A `review_notes` entry with `finding: pass` must cite a specific `artifact_location` from `evidence_plan` or a specific `path:line` from the diff. A `pass` with only prose is a rubber stamp.
4. **Read-only review.** You approved without running at least one verification-only command yourself (test run, build, `git log`, migration dry-run replay, artifact open). Reading the Implementer's summary is not verification; it is trust. Verification is you, with a shell.
5. **Editing through the back door.** You found a problem and, in a runtime where the tool-write boundary is prose-only, you fixed it directly or dictated a one-line patch that the Implementer copy-pasted. In a mechanically-enforced runtime this is blocked by tool permissions; in a prose-only runtime it is an explicit rule violation. Send back, do not patch.
6. **Thin residual-risk section.** `residual_risk` says "none identified" or is a single sentence. A real change has at least three risks that were evaluated and judged acceptable. If you cannot name three, you have not evaluated.

These rules are **heuristic failure mirrors**. They do not enumerate every way a review can go wrong; they catch the six patterns most likely to slip past even a careful Reviewer. If none of the six applies and the review still feels shallow, that is itself a signal — re-open the diff. Any one trigger applying is a **mandatory send-back, not a judgment call**.

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

Violation of this rule during Full-mode changes is a Tier-2 escalation per the Conflict-resolution section: the manifest must be returned to the appropriate upstream phase and re-executed with a fresh agent identity for the downstream role.

---

## Optional machine-readable pre-filter

Some teams want a cheap mechanical check between the Implementer's handoff and the Reviewer's audit — not to *replace* the Reviewer, but to catch structural incompleteness before a human or high-cost reviewer spends time on it. This section defines that optional layer and the hard limits that keep it from drifting into the Reviewer's role.

### What it is

A pre-filter is a sub-agent invocation with capabilities limited to **file read** and **code search** (and optionally **network fetch** for external-reference checks). It runs after `phase: review` is set and before a Reviewer is summoned. Its job is **binary structural verification** — a list of "present / absent" and "resolves / does not resolve" answers.

Typical checks a pre-filter performs:

- Every acceptance criterion in the Task Prompt has a matching `evidence_plan` entry.
- Every `evidence_plan.artifacts[*].artifact_location` resolves to a real file or URL.
- Every identifier cited in `implementation_notes` resolves via code search to an existing `path:line`.
- The five questions of the Implementer's pre-handoff self-check (§Pre-handoff self-check above) have documented answers, not placeholders.
- Declared `surfaces_touched` is consistent with files actually changed in the diff.

### Hard limits

Four rules keep the pre-filter from collapsing into a Reviewer:

1. **Pre-filter is not Reviewer.** A passing pre-filter proves only that the manifest is **structurally complete** — every required field is filled, every path resolves. It does *not* prove the field contents are correct. A Reviewer must still audit.
2. **Pre-filter cannot replace Reviewer.** A Reviewer who writes "pre-filter passed, approving" in their `review_notes` has triggered Anti-Rationalization Rule 4 (read-only review without personal verification; see §Anti-rationalization rules above). The pre-filter's output is an input to the Reviewer's audit, not its output.
3. **Pre-filter outputs binary findings only.** Present / absent, resolves / does not resolve, matches / does not match. A pre-filter that emits a score, a grade, or a subjective quality judgment has exceeded its scope and must be treated as an untrusted input — subjective evaluation is the Reviewer's role.
4. **Pre-filter is disabled in Zero-ceremony and Lean modes.** Adding a pre-filter to a trivial change increases ceremony without reducing risk. Pre-filter is a Full-mode option only.

### Anti-collusion for pre-filter

The pre-filter sub-agent's identity must differ from all three canonical roles (`Planner / Implementer / Reviewer`) in the same change. A pre-filter that shares identity with the Implementer it is checking collapses back into self-review. The anti-collusion rule above extends to the pre-filter without modification.

### When to adopt

A team should consider a pre-filter only if both conditions hold:

- The team is consistently in **Full mode** for most changes (Lean-mode-dominant teams gain nothing).
- Reviewer capacity is a bottleneck, not evidence quality (if evidence quality is the bottleneck, the fix is to tighten the Implementer's pre-handoff self-check, not to add another layer).

A pre-filter adopted for the wrong reason becomes another mechanical box to tick and drifts the team toward ceremony. The Reviewer's anti-rationalization rules exist precisely because mechanical checks cannot substitute for audit; the pre-filter adds **prefix** to that audit, not **replacement**.

### Relation to hooks and validators

The runtime-hook contract (`docs/runtime-hook-contract.md`) and the automation contract (`docs/automation-contract.md`) already provide machine-readable structural checks that run **before** the Implementer advances `phase: review`. A pre-filter invocation is a *separate* check that runs **after** the handoff — its purpose is to confirm the Implementer did not forget the things the pre-handoff hooks were supposed to catch. If a team's hooks are comprehensive and disciplined, the pre-filter is redundant; the option exists for teams whose hook coverage is incomplete.

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
- A specialist *parented under* the Reviewer who finds an issue must report it as a finding for the Reviewer to weigh; it must not be re-parented to the Implementer to "just fix it." That move would route the finding around the Reviewer's audit and trigger Anti-rationalization Rule 5 (editing through the back door) at the structural level.

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
| observe | applies only under Phase 8 trigger conditions (see `phase8-trigger-guide.md`) |

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
