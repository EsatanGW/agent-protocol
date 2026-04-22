# Context Pack — Template

Fillable skeleton for a context pack distributed to fan-out sub-agents. Produced by the canonical role (Planner for Pattern A, Reviewer for Pattern B) immediately before the fan-out batch.

**Budget:** under 400 words in normal use; hard cap 800. If you cannot fit this change's context into the budget, the fan-out is over-scoped — reduce scope per sub-agent, or return to serial execution.

**Scope:** Full mode only. Do not produce a context pack for Lean / Zero-ceremony.

**See:** [`../references/context-pack.md`](../references/context-pack.md) for the full discipline; [`../references/parallelization-patterns.md`](../references/parallelization-patterns.md) for the two canonical fan-out patterns.

---

```markdown
# Context Pack: <change_id>

## Identity

- change_id: <YYYY-MM-DD-slug>
- title: <one line>
- phase: <investigate | review>
- fan-out pattern: <A: surface-parallel investigators | B: specialized audit>
- owning role / identity: <planner | reviewer> / <identity>
- produced at: <ISO 8601>

## SoT candidates (already classified)

<only the SoT candidates this fan-out operates on; not the full sot_map>

- <symbol / field / enum> → pattern <n> (<brief note>)
- <symbol / field / enum> → pattern <n> (<brief note>)

## Surfaces in scope

| Surface | Owning sub-agent identity | Scope boundary |
|---|---|---|
| <user / system-interface / information / operational / extension> | <sub-agent identity> | <one-line description of what this sub-agent is and is not responsible for> |

Pattern A: one row per investigator. Pattern B: one row per audit concern.

## Terminology snapshot

<only the glossary terms this fan-out actually uses; ~5-10 entries>

- <term>: <short definition or glossary pointer>

## Hard boundaries (apply to every sub-agent)

- Return findings only; do **not** write manifest fields.
- Do **not** spawn further sub-agents.
- Do **not** cross into another sub-agent's surface / audit scope.
- <any change-specific boundary>

## Return-slot shape (required structure of each sub-agent's return)

```yaml
findings:
  sub_agent_identity: <string>
  scope: <string>
  items:
    - kind: <observation | risk | evidence_pointer | contradiction>
      surface: <surface or N/A>
      location: <file:line or artifact_location>
      summary: <one line>
      severity: <info | warn | blocking>   # Pattern B only
  scope_completeness: <complete | partial — with reason>
  unresolved_questions:
    - <one line>
```

Sub-agents whose returns do not match this shape will be rejected at fan-in.

## Cross-change references (optional)

- CCKN: <id> — <why this pack references it>

---

End of pack. (Word count: <n>.)
```
