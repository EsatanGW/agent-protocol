# Decision Trees

> **Purpose.** Single-page entry to the three decisions an agent makes most often when starting a change: *Do I need a Change Manifest? Which SoT pattern fits this surface? Should this run as one agent or as multiple roles?* Each tree gives a fast call in 30–60 seconds, then routes to the canonical doc that owns the rule.
>
> **Status.** Non-normative routing aid. The canonical sources cited under each tree are the binding rules; this file is allowed to *condense*, never to *override*. If a tree disagrees with its source, the source wins and this file should be edited.

---

## How to use this page

1. Pick the tree that matches what you are trying to decide.
2. Walk top-to-bottom. The first row that matches is your answer; don't keep walking.
3. Click through to the canonical source for the binding rule + edge cases.

If your situation matches none of the rows, treat it as a force-escalate: surface to the upstream phase (Plan if you are Implementing; Plan-with-human if you are Planning) rather than guessing.

---

## Tree A — Need a Change Manifest?

**Use this when:** you have a change in mind and want to know whether to write a Change Manifest before writing code.

```
START
  │
  ├─ Does the change match any "force Full" row in
  │  skills/engineering-workflow/references/mode-decision-tree.md
  │  §Scenarios that force Full?
  │   (DB schema; public API breaking; enum/status consumer-visible;
  │   money/payments; auth/PII/secrets; cross-team handoff;
  │   long-lived feature-flag; staged rollout;
  │   canonical methodology content edit at L1+)
  │   ─── YES ──▶ FULL mode → Change Manifest required.
  │                Schema: schemas/change-manifest.schema.yaml
  │                Spec:   docs/change-manifest-spec.md
  │
  ├─ Does the change touch 2+ surfaces, OR introduce an SoT trade-off,
  │  OR carry a breaking change at L1 or higher, OR have rollback
  │  considerations beyond "just revert the commit"?
  │   ─── YES ──▶ FULL mode → Change Manifest required (same refs).
  │
  ├─ Single surface, ≤ 1 consumer, verifiable in ≤ 5 minutes,
  │  non-trivial behavior change?
  │   ─── YES ──▶ LEAN mode → Lean artifact (not a full manifest);
  │                see skills/engineering-workflow/SKILL.md
  │                §Lean workflow.
  │
  ├─ Single surface, behavior bounded (i18n value tweak, new log,
  │  patch dependency bump, docstring fix, validated config tweak)?
  │   ─── YES ──▶ THREE-LINE DELIVERY → commit / PR description IS
  │                the artifact. No manifest, no Lean record.
  │
  └─ Truly trivial (typo, single comment, formatting)?
      ─── YES ──▶ ZERO-CEREMONY → just do the work.
```

**Canonical source:** [`skills/engineering-workflow/references/mode-decision-tree.md`](../skills/engineering-workflow/references/mode-decision-tree.md). The four-mode definitions live in [`docs/glossary.md §Execution mode`](glossary.md). Manifest schema fields and minimum thresholds per phase: [`docs/change-manifest-spec.md`](change-manifest-spec.md). Force-Full triggers for canonical methodology edits: same `mode-decision-tree.md §Scenarios that force Full`.

**Common pitfalls.**

- *L0-additive edits to canonical methodology files* (new non-normative reference file, pointer additions, CHANGELOG-only edits) stay **Lean-eligible** even though the file is canonical; only L1+ edits force Full. Don't escalate every doc edit.
- *Worst-case judgment.* Breaking-change level is judged by the worst case the change can produce, not the most common case. Pattern: "if the bad outcome is L2, this is L2 even though most flows are L0."
- *Silent scope-shrink to avoid Full is forbidden* — if the situation is actually Full, do Full. See [`AGENTS.md §6`](../AGENTS.md).

---

## Tree B — Which Source-of-Truth pattern?

**Use this when:** you have identified a surface and need to declare its `sot_map[*].pattern` in the manifest. Walk the questions in order; the first matching answer is the pattern.

| # | Question (yes if any clause is true) | Pattern |
|---|---|---|
| 1 | Is the truth a database schema, an API spec / OpenAPI, or a typed contract artifact? | **1 — Schema-Defined** |
| 2 | Is the truth a config file, env var registry, or a feature-flag system entry? | **2 — Config-Defined** |
| 3 | Is the truth a closed set of named values (enum / status / discriminated-union tag) consumed by switch / match / pattern-match logic? | **3 — Enum / Status-Defined** |
| 4a | Is the truth an **execution order** between steps that must run in a fixed sequence (pipeline stage order, migration ordering, init sequence)? | **4a — Pipeline-Order Contract** |
| 4 | Is the truth an agreement between two systems — API contract, event schema, shared types — but **not** purely a stored schema (#1) or pure ordering (#4a)? | **4 — Contract-Defined** |
| 5 | Does the **UI** definitively define the truth (design-system component spec; rare)? | **5 — UI-Defined** |
| 6 | Is the truth not the current value but the **set of legal transitions** between values (state machine; "how did `status` get to `shipped` legally")? | **6 — Transition-Defined** |
| 7 | Does authority live **temporarily** at the client / edge / offline node, with a sync handoff to a central authority later? | **7 — Temporal-Local** |
| 8 | Does the truth exist in **two simultaneous representations** that must stay in sync (e.g. binary + JSON; UI tree + serialized form; read model + write model)? | **8 — Dual-Representation** |
| 9 | Is the truth picked at **runtime** from a candidate set by a resolution rule (locale variants; A/B variants; per-region values; per-platform overrides)? | **9 — Resolved / Variant** |
| 10 | Is authority bound to a **platform / host lifecycle** that can be killed, suspended, or cold-started without warning (browser tab; mobile background process; serverless cold start)? | **10 — Host-Lifecycle** |

If two patterns seem to apply, declare the more specific one and note the secondary in the same `sot_map` row's notes. If you genuinely cannot tell, **stop and escalate**; misdeclaring SoT pattern propagates errors into evidence planning and rollback assessment.

**Canonical source:** [`docs/source-of-truth-patterns.md`](source-of-truth-patterns.md). Anti-patterns and standard repair strategies for each pattern live there. Glossary entry: [`docs/glossary.md §Source of truth`](glossary.md).

---

## Tree C — Single-agent or multi-agent role split?

**Use this when:** the runtime supports sub-agents (Claude Code Task tool; Cursor Custom Modes; Gemini CLI sessions; Windsurf modes; Codex profiles) and you need to decide whether to run this change as one agent or as `Planner → Implementer → Reviewer`.

```
START
  │
  ├─ Tree A above said FULL mode?
  │   ─── YES ──▶ Multi-agent role split REQUIRED if the runtime
  │                supports sub-agents. Three identities:
  │                Planner / Implementer / Reviewer.
  │                Anti-collusion: same identity must not play
  │                more than one role.
  │                Spec: docs/multi-agent-handoff.md
  │                       §Tool-permission matrix
  │                       §Single-agent anti-collusion rule
  │
  ├─ Tree A said LEAN mode?
  │   ─── YES ──▶ Planner ≡ Implementer collapse is permitted
  │                (single identity may plan and implement).
  │                Implementer ≡ Reviewer is STILL forbidden —
  │                a separate Reviewer identity (or a separate
  │                session) must verify evidence.
  │
  ├─ Tree A said THREE-LINE DELIVERY or ZERO-CEREMONY?
  │   ─── YES ──▶ No role split. The commit / PR description
  │                is the artifact; the merge gate (CI + human
  │                review) is the verification.
  │
  └─ Runtime does NOT support sub-agents?
      ─── YES ──▶ Methodology still applies; mechanical
                  enforcement weakens. Use session isolation +
                  OS-level write denial for the Reviewer step
                  (see docs/multi-agent-handoff.md §Enforcement
                  across runtimes).
```

**Canonical source:** [`docs/multi-agent-handoff.md`](multi-agent-handoff.md) §Tool-permission matrix + §Single-agent anti-collusion rule. Runtime-specific enforcement matrix: same file §Enforcement across runtimes. Per-runtime mirrors (validated in CI by `.github/workflows/validate.yml` `role-consistency`): [`agents/{planner,implementer,reviewer}.md`](../agents/), [`.cursor/rules/{planner,implementer,reviewer}.mdc`](../.cursor/rules/), [`reference-implementations/roles/`](../reference-implementations/roles/).

**Common pitfalls.**

- *Implementer ≡ Reviewer is the highest-risk collusion combination and is forbidden outright*, even in Lean mode. The cheapest fix is to open a fresh session / window / profile for the review step.
- *Pattern C cluster-parallelism* (multiple canonical Implementers in parallel for file-disjoint clusters) is a Full-mode-only optimization, not a different mode. The anti-collusion rule applies transitively across clusters; see [`skills/engineering-workflow/references/cluster-parallelism.md`](../skills/engineering-workflow/references/cluster-parallelism.md).
- *Specialist sub-agents* (security-reviewer, performance-reviewer, etc.) are non-canonical: they inherit their parent canonical role's tool envelope and never write manifest fields directly. See [`reference-implementations/roles/role-composition-patterns.md`](../reference-implementations/roles/role-composition-patterns.md).

---

## Tree D — When must a human review before action?

**Use this when:** an Implementer or Reviewer is about to take an action and needs to know whether the agent may proceed alone, or whether a human reviewer must be looped in *before* the action lands. Walk top-to-bottom; the first matching row decides.

```
START — about to perform an action / approve a manifest field
  │
  ├─ Is the action on the runtime's risky-action list?
  │  (force-push to a protected branch; rm -rf or equivalent
  │   bulk delete; production-credential touch; production
  │   data-store write; money/payment endpoint; auth / PII /
  │   secret path; dependency major-version bump that crosses
  │   a deprecation boundary; deletion of an in-flight manifest)
  │   ─── YES ──▶ HUMAN REVIEW REQUIRED before the action.
  │                Stop, surface the action + blast radius, wait.
  │                Source: AGENTS.md §Stop conditions
  │                        + docs/security-supply-chain-disciplines.md
  │                        (auth/PII rows)
  │
  ├─ Is the change's breaking_change.level ≥ L2
  │  (Structural / Removal / Semantic Reversal)?
  │   ─── YES ──▶ HUMAN APPROVAL on the manifest's `approvals`
  │                array required before Phase 7 sign-off.
  │                Reviewer alone may NOT approve L3+ removal
  │                or L4 semantic reversal — at least one
  │                approver_role must be human.
  │                Source: docs/breaking-change-framework.md
  │                        §Severity ladder + §Migration path
  │
  ├─ Is the change's rollback_mode = 3 (Compensation)?
  │   ─── YES ──▶ HUMAN APPROVAL on the rollback plan
  │                required — compensation paths cannot be
  │                rolled back by reverting the commit.
  │                Source: docs/rollback-asymmetry.md
  │                        §Mode 3 — Compensation
  │
  ├─ Does the change touch the auth / PII / secrets path,
  │  OR introduce a new external trust boundary?
  │   ─── YES ──▶ Specialist review (security-reviewer
  │                sub-agent if the runtime supports it; otherwise
  │                a separate human) required before Phase 5
  │                sign-off. Reviewer's sampling right also extends
  │                to re-running the security check.
  │                Source: docs/security-supply-chain-disciplines.md
  │
  ├─ Is the change a canonical methodology content edit
  │  at L1+ in this repository
  │  (modifies an existing normative claim, adds a new
  │   normative rule to a SoT file, or renames a
  │   cross-cutting term)?
  │   ─── YES ──▶ Reviewer must be a different identity from the
  │                Implementer (anti-collusion remains the
  │                hard rule). Tree A already forced Full;
  │                Tree D adds: Reviewer must be human-in-the-loop
  │                or a fresh session whose context window does
  │                not overlap the Implementer's.
  │                Source: CLAUDE.md §5 + docs/multi-agent-handoff.md
  │                        §Single-agent anti-collusion rule
  │
  └─ None of the above?
      ─── YES ──▶ Agent may proceed under the standard role
                  envelope. Reviewer audit at Phase 5 / sign-off
                  at Phase 6 still applies; no extra HITL gate.
```

**Canonical source.** Tree D is a *routing aid* that condenses rules already binding in the cited sources. The leaf actions resolve to fields and triggers already declared in the manifest schema (`escalations[*].trigger`, `approvals[*].approver_role`, `breaking_change.level`, `rollback_mode`); Tree D never invents a new escalation type. If a situation does not match any row, treat it as an unknown action — escalate per [`AGENTS.md §Stop conditions`](../AGENTS.md) rather than guess.

**Common pitfalls.**

- *Treating Tree D as exhaustive.* Tree D covers the recurring HITL triggers; runtime-specific risky-action lists may be longer (a deployment runtime may add "production database migration" or "API gateway rule change"). The runtime bridge owns those extensions; this tree owns the methodology-level minimum.
- *Collapsing approver_role into "Reviewer".* When a row says "human approval", the manifest's `approvals[*].approver_role` must literally be `human` (or a runtime-mapped equivalent), not the canonical `Reviewer` identity which may itself be an AI session. The two columns answer different questions.
- *Skipping Tree D because Tree A already chose Full.* Tree A decides the *artifact* (manifest vs lean vs three-line); Tree D decides *who must look at it before action*. A Full-mode change can still be entirely agent-executed if no Tree D row matches; conversely, a Lean-mode change can require human approval if it touches the auth/PII path.

---

## Where this page sits

This file is the **routing hub** that consolidates pointers between the three decision-aids that previously cross-cited each other:

- `docs/glossary.md` (canonical term definitions)
- `docs/source-of-truth-patterns.md` (pattern catalogue)
- `skills/engineering-workflow/references/mode-decision-tree.md` (Lean / Full)

By concentrating decision flow here, the canonical sources can each focus on rules within their domain and stop having to cross-link to each other for "and-then-decide-X." If a future edit grows a fourth decision, add a new tree to this file rather than reinstating cross-doc loops.
