# Phase Command Vocabulary

> **English TL;DR**
> A runtime-neutral alias registry mapping the methodology's phase / role / mode vocabulary onto names that runtime bridges can surface as slash commands, Custom Modes, plugin commands, or prompt fragments. The aliases use only existing names from `skills/engineering-workflow/phases/`, `docs/multi-agent-handoff.md`, and `reference-implementations/roles/specialist-roles-registry.md` — this document is an assembly of those names, not a new vocabulary. Normative content forbids any runtime-specific syntax (no `$verb`, no `/verb`, no shell shorthand); concrete syntax appears only in the §Bridge surfacing examples appendix.

---

## Why this exists

Every runtime bridge invents its own way to invoke a phase: Codex plugins surface slash commands, Cursor surfaces Custom Modes, Claude Code surfaces sub-agent definitions and `/`-prefixed commands, Gemini CLI surfaces persona prompts, plain Aider surfaces prompt templates. Without a shared **alias registry**, every bridge re-derives names from first principles, drifts, and the methodology gains no compounding effect from the user-facing surface.

The alias registry pins:

- **Which canonical phase** an alias refers to.
- **Which canonical role** is invoked (for role-bound aliases).
- **Which specialist sub-agent role** is invoked (when applicable).
- **Which mode** is consistent with the alias (Zero-ceremony / Three-line / Lean / Full / any).

A bridge then maps each alias to its native command surface — but every bridge maps the same alias to the same canonical phase + role + mode, so users moving between runtimes see consistent behavior under different syntaxes.

This document is **assembly, not invention**. Every name it uses is already defined elsewhere:

- Phase names from [`skills/engineering-workflow/phases/`](../skills/engineering-workflow/) (`phase0-clarify.md` … `phase7-deliver.md`).
- Canonical role names from [`docs/multi-agent-handoff.md`](multi-agent-handoff.md) (`Planner` / `Implementer` / `Reviewer`).
- Specialist names from [`reference-implementations/roles/specialist-roles-registry.md`](../reference-implementations/roles/specialist-roles-registry.md) (`architect` / `security-reviewer` / `performance-reviewer`) — registry-bound; new specialists registered there flow into this table.
- Mode names from [`docs/glossary.md`](glossary.md) §Execution mode (`Zero-ceremony` / `Three-line` / `Lean` / `Full`).

If an alias here references a name that does not appear in one of those four sources, **this document is wrong**, not the source. Update the source first; the alias table reflects the source.

---

## Naming rules

The alias table below follows three rules:

1. **Lowercase kebab-case identifiers.** Aliases look like `clarify`, `plan`, `review-as-security`. Underscore-separated names (`plan_as_architect`) and PascalCase names are not used.
2. **Role suffix for role-bound variants.** When an alias names a phase that is canonical-role-bound and the role is not implied by the phase, the alias may use the suffix `-as-<role>` (`plan-as-architect`, `review-as-security`). The implicit-role case (where a phase is owned by exactly one canonical role) does not carry the suffix.
3. **No runtime syntax in the alias_id.** No `$`, no `/`, no `:`, no `--`. Bridges add those when they translate an alias to their own command surface.

Aliases that violate any of these rules are not registered.

---

## The alias registry

| `alias_id` | Canonical phase | Canonical role | Specialist | Mode constraint | What invocation does |
|---|---|---|---|---|---|
| `clarify` | clarify (Phase 0) | any | — | any | Open the Phase 0 / Lean-0 clarify step. Identify ambiguities, surface unknowns, decide whether the request is shaped for Zero-ceremony / Three-line / Lean / Full per `references/mode-decision-tree.md`. |
| `investigate` | investigate (Phase 1) | Planner | — | Lean / Full | Open the Phase 1 / Lean-1 investigate step. Identify surfaces, build SoT-map candidates, query CCKN precedent per `phases/phase1-investigate.md`. |
| `investigate-as-architect` | investigate (Phase 1) | Planner | architect | Full | Same as `investigate` but invokes the registered `architect` specialist as a Pattern 2 / Pattern 5 sub-agent for non-obvious SoT classification. Specialist returns a structured draft; Planner synthesizes. Forbidden in Lean (no fan-out per `role-composition-patterns.md`). |
| `plan` | plan (Phase 2) | Planner | — | Lean / Full | Open the Phase 2 / Lean-2 plan step. Produce the Change Manifest front-half and Task Prompt per `phases/phase2-plan.md`. |
| `plan-as-architect` | plan (Phase 2) | Planner | architect | Full | Plan with `architect` specialist consulted on SoT pattern selection. Same envelope and synthesis rules as `investigate-as-architect`. |
| `testplan` | test_plan (Phase 3) | Planner | — | Full | Open the Phase 3 test_plan step. Enumerate evidence categories and acceptance criteria per `phases/phase3-testplan.md`. (Lean collapses test_plan into Lean-2; no separate alias.) |
| `implement` | implement (Phase 4) | Implementer | — | any | Open the Phase 4 / Lean-3 implement step. Modify code per the manifest and Task Prompt; collect evidence; populate `evidence_plan.artifacts` per `phases/phase4-implement.md`. |
| `review` | review (Phase 5) | Reviewer | — | Lean / Full | Open the Phase 5 / Lean-4 review step. Audit evidence, check cross-cutting concerns, write `review_notes` per `phases/phase5-review.md`. |
| `review-as-security` | review (Phase 5) | Reviewer | security-reviewer | Full | Review with `security-reviewer` specialist as a Pattern 6 audit sub-agent. Specialist returns findings; Reviewer synthesizes into `review_notes`. Forbidden in Lean. |
| `review-as-performance` | review (Phase 5) | Reviewer | performance-reviewer | Full | Review with `performance-reviewer` specialist as a Pattern 6 audit sub-agent. Same envelope and synthesis rules as `review-as-security`. |
| `signoff` | signoff (Phase 6) | Reviewer | — | Lean / Full | Open the Phase 6 / Lean-5 sign-off step. Record `approvals`, finalize `residual_risk`, advance `phase: signoff` per `phases/phase6-signoff.md`. |
| `deliver` | deliver (Phase 7) | Implementer | — | any | Open the Phase 7 deliver step. Produce the completion report and `handoff_narrative` per `phases/phase7-deliver.md`. |
| `observe` | observe (Phase 8) | any observer | — | Full (gated by trigger) | Open the Phase 8 observe step. Append `production_findings` over the declared `review_horizon`. Applies only under the trigger conditions in [`post-delivery-observation.md`](post-delivery-observation.md) §Phase 8 is not mandatory. |

### Lean-mode collapse

Per [`references/mode-decision-tree.md`](../skills/engineering-workflow/references/mode-decision-tree.md), Lean mode collapses the eight phases into six steps (Lean-0 … Lean-5). The aliases above map naturally:

| Lean step | Alias | Notes |
|---|---|---|
| Lean-0 Clarify | `clarify` | Same alias; mode is selected at Phase 0 anyway. |
| Lean-1 Investigate | `investigate` | Specialist variants are Full-only. |
| Lean-2 Minimal Plan | `plan` | `testplan` is folded into Lean-2 — no separate alias in Lean. |
| Lean-3 Implement | `implement` | |
| Lean-4 Review | `review` | Specialist variants are Full-only. |
| Lean-5 Sign-off | `signoff` | |

Zero-ceremony mode does not invoke phase aliases at all — by definition it is below the artifact threshold. A bridge that exposes a `clarify` command in Zero-ceremony has crossed into a higher tier.

### Forbidden alias forms

The following alias shapes are explicitly **not registered** and bridges that surface them are non-conformant:

- `plan-as-implementer`, `review-as-planner`, etc. — combinations that violate the field-ownership matrix in `docs/multi-agent-handoff.md`.
- `plan-as-architect-and-security` — chained specialists in one alias; a single alias names exactly one specialist (or none).
- `super-review`, `deep-review`, `architect-mode`, etc. — alias names that imply a quality grade or new role rather than a phase + role + specialist tuple.
- `$plan`, `/plan`, `--plan` — syntax-prefixed forms; the bridge adds syntax, the alias does not.
- Vendor or model names (`claude-plan`, `codex-plan`, `gpt-plan`) — aliases must be runtime-neutral.

---

## Bridge surfacing examples

> **Status:** the examples below are **non-normative**. Each bridge chooses how to surface the alias on its own runtime; what is normative is the alias_id and the canonical phase + role + specialist + mode tuple it represents. The examples illustrate plausible mappings, not required ones.

### Codex CLI

A Codex plugin can surface aliases as plugin commands. A plausible mapping:

```
$clarify
$investigate
$investigate-as-architect          (Full mode only)
$plan
$plan-as-architect                 (Full mode only)
$testplan                          (Full mode only — no Lean collapse)
$implement
$review
$review-as-security                (Full mode only)
$review-as-performance             (Full mode only)
$signoff
$deliver
$observe                           (gated by trigger)
```

A Codex plugin that surfaces an alias not in the registry, or under a different canonical phase, is non-conformant — it is inventing methodology.

### Claude Code

Claude Code can surface aliases as a combination of slash commands and sub-agent invocations. A plausible mapping:

```
/clarify                     → opens Phase 0 prompt
/plan                        → spawns the planner sub-agent (agents/planner.md)
/plan-as-architect           → spawns planner with the architect specialist
                               registered in specialist-roles-registry.md
/implement                   → spawns the implementer sub-agent
/review                      → spawns the reviewer sub-agent
/review-as-security          → spawns reviewer with security-reviewer
                               specialist Pattern 6 fan-out
```

The slash command's frontmatter / definition cites the alias_id from this registry.

### Cursor

Cursor surfaces aliases as Custom Modes or rule-file activations. A plausible mapping:

```
Custom Mode "Planner"             → activates .cursor/rules/planner.mdc
                                    + disables edit-class tools
Custom Mode "Reviewer"            → activates .cursor/rules/reviewer.mdc
                                    + disables ALL write tools
Custom Mode "Reviewer + Security" → activates reviewer.mdc with the
                                    security-reviewer specialist invocation
                                    pre-described in the mode prompt
```

### Gemini CLI / Windsurf

Gemini and Windsurf surface aliases as persona prompts or session-mode names. A plausible mapping:

```
gemini --persona reviewer.md         → loads reference-implementations/roles/reviewer.md
gemini --persona reviewer.md \
       --specialist security-reviewer
                                       → loads reviewer.md plus the specialist-roles-registry.md
                                         security-reviewer entry as a sub-prompt
```

Bridges that paste the runtime-neutral role prompt also surface the alias_id in the session header so an audit can trace which alias was active.

### Plain `AGENTS.md`-only runtimes (Aider / OpenCode)

Runtimes that only consume `AGENTS.md` and have no native command surface can surface aliases as **prompt prefixes** the user types:

```
clarify: <user request>
plan: <user request>
review: <change_id>
```

The agent reads the prefix, looks up the alias_id in this registry, applies the canonical phase + role + specialist + mode, and proceeds.

---

## How a runtime registers a new alias

Aliases are added in three steps:

1. **Confirm the underlying phase / role / specialist exists** in `skills/engineering-workflow/phases/`, `docs/multi-agent-handoff.md`, or `reference-implementations/roles/specialist-roles-registry.md`. If the underlying name does not exist, register it there first; do not invent it in this table.
2. **Add the row to the alias registry** above. The row pins the canonical phase + role + specialist + mode tuple. If a specialist is involved, the specialist must already be registered in `specialist-roles-registry.md`.
3. **Update bridges** that wish to surface the new alias. Each bridge maps the alias_id to its native command surface independently; mapping consistency is the alias's job, not the bridge's.

A new alias whose underlying phase / role / specialist / mode tuple is already covered by an existing alias is a duplicate — consolidate before adding.

---

## Anti-patterns

- **Alias as marketing.** `super-plan`, `deep-investigate`, `pro-review` — alias names that imply a quality grade are not registrations; they are marketing on the user's command line. Reject.
- **Alias as scope creep.** Adding aliases for phases that do not exist in the methodology (`refine`, `polish`, `harden`) is a request to extend the methodology, not the alias table. If a new phase is genuinely needed, propose it in `docs/` first.
- **Alias as runtime privilege.** A runtime-specific alias that has no equivalent in other bridges fragments the methodology surface. Either every bridge can reasonably map it, or it is not an alias — it is a runtime feature and belongs in that runtime's own configuration, not in this registry.
- **Alias as anti-collusion bypass.** A bridge that exposes both `plan-as-implementer` and `plan` such that the user can shortcut Planner-Implementer separation is using the alias surface to violate the field-ownership matrix. The alias table forbids these forms.
- **Specialist sprawl in aliases.** A registry of specialists past ~6 (per `specialist-roles-registry.md` §Anti-patterns) generates 2N+ aliases (one bare phase + one per specialist) and overloads the user-facing surface. Consolidate specialists before adding aliases.

---

## Relationship to other documents

- [`skills/engineering-workflow/phases/`](../skills/engineering-workflow/) — source of canonical phase names; this registry consumes those names.
- [`docs/multi-agent-handoff.md`](multi-agent-handoff.md) — source of canonical role names; this registry consumes those names.
- [`reference-implementations/roles/specialist-roles-registry.md`](../reference-implementations/roles/specialist-roles-registry.md) — source of specialist names; this registry consumes those names.
- [`skills/engineering-workflow/references/mode-decision-tree.md`](../skills/engineering-workflow/references/mode-decision-tree.md) — source of mode names and Lean / Full collapse rules.
- [`docs/glossary.md`](glossary.md) — defines "Phase command alias" with this file as the SoT pointer.
