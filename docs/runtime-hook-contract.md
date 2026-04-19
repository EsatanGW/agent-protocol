# Runtime Hook Contract

> **English TL;DR**
> A capability contract for **agent-runtime hooks** — event-triggered scripts that fire inside an AI coding agent's execution loop (pre-tool-use, post-tool-use, pre-commit, on-stop, etc.). Sibling to `automation-contract.md`: that doc covers batch validators (manifest-shape, cross-reference, drift); this doc covers event-driven hooks (every tool call, every commit, every response). Defines four hook categories (phase-gate / evidence / drift / completion-audit), a tool-agnostic I/O contract (JSON event in, exit-code + stderr out), and exit-code semantics (0 pass, 1 fail-block, 2 warn). Tool-neutral — runtime bridges (Claude Code, Cursor, etc.) map these categories into runtime-native hook formats. Reference implementation: `reference-implementations/hooks-claude-code/`.

This document covers **agent-runtime** hooks, not CI/CD hooks. The two are intentionally separate:

| Document | Runs where | Triggered by | Typical latency budget |
|---|---|---|---|
| `ci-cd-integration-hooks.md` | CI/CD platform | PR events, merge events | seconds to minutes |
| `runtime-hook-contract.md` (this doc) | AI agent's execution environment | Tool use, response completion, commit | sub-second |
| `automation-contract.md` | Any validator | Batch invocation | seconds |

All three share the **same exit-code semantics** so a hook that works in one layer can be re-used in another with minimal glue.

---

## Why this contract exists

Without a contract, agent-runtime hooks degrade along three paths:

- **Language lock-in.** One runtime ships JS hooks, another ships Python — the same discipline gets reimplemented twice and drifts.
- **Event lock-in.** Hooks depend on runtime-specific event payload shapes; moving between Claude Code / Cursor / Gemini CLI requires rewriting every hook.
- **Silent bypass.** A hook fails, the runtime swallows the error, the agent continues. No one knows the guardrail fired.

The contract locks down "what a runtime hook must at minimum look like" while leaving "what runtime it plugs into" to each bridge.

---

## Four hook categories

Every runtime hook must fit into exactly one of these four categories. A hook that spans two belongs in two separate scripts.

### Category A: phase-gate hook

**Purpose:** block progression between methodology phases until the exit criteria are met.

**Typical triggers:**
- Pre-commit (before the commit that closes a phase lands)
- On `phase` field transition in the manifest
- On "task completed" claim from the agent

**Example checks:**
- Manifest exists when a non-trivial change is being committed.
- Every primary surface has at least one `evidence_plan` entry with `status: collected`.
- `phase: deliver` has at least one human approval.
- Branch protection (no direct commits to main / master / production / release).

**Contract-required behavior:** on failure, exit code 1 (block). Fail-open is not acceptable for this category.

### Category B: evidence hook

**Purpose:** verify that a claimed evidence artifact actually exists and is well-formed.

**Typical triggers:**
- Post-tool-use after the agent writes or updates an evidence artifact
- Pre-commit, when evidence paths are recorded in the manifest

**Example checks:**
- `evidence_plan.artifacts[].location` paths resolve to real files.
- A `screenshot_diff` artifact is a real image file, not an empty placeholder.
- A `unit_test` artifact is a real test file, not a stub.
- A `migration_dry_run` artifact contains a dry-run log with expected structure.

**Contract-required behavior:** on missing artifact, exit code 1 (block); on well-formed-but-dubious artifact (e.g. test file exists but has no assertions), exit code 2 (warn).

### Category C: drift hook

**Purpose:** detect when the manifest's claims diverge from repo reality.

**Typical triggers:**
- Post-tool-use after any edit
- Periodic (on response completion) for long sessions

**Example checks:**
- Manifest says `phase: signoff` but files continue to be edited.
- Manifest declares an SoT file that no longer exists in the repo.
- A surface declared `role: primary` but no files in its region were touched.
- `last_updated` older than N minutes despite recent edits.

**Contract-required behavior:** exit code 2 (warn) is the default; exit code 1 (block) only for cases the runtime explicitly opts into.

### Category D: completion-audit hook

**Purpose:** verify an agent's "I'm done" claim before it surfaces to the user.

**Typical triggers:**
- On-stop (when the agent reaches end-of-turn)
- Before a PR description or completion message is surfaced

**Example checks:**
- Every `evidence_plan` item is `status: collected` or waived.
- No `residual_risks` entries are `accepted_by: unaccepted`.
- `handoff_narrative` is present when `phase == observe`.
- No `escalations[*].resolved_at` is empty.

**Contract-required behavior:** exit code 1 (block) if the completion claim is materially false; exit code 2 (warn) if the claim is optimistic but not fabricated.

---

## I/O contract

Hooks must accept a JSON event on stdin and emit a structured result. The schema below is the minimum; runtimes may extend it additively.

### Input schema (stdin)

```json
{
  "hook_category": "phase-gate | evidence | drift | completion-audit",
  "event": {
    "trigger": "pre-tool-use | post-tool-use | pre-commit | on-stop | on-phase-transition",
    "timestamp": "<ISO 8601>",
    "runtime": "claude-code | cursor | gemini-cli | windsurf | codex | other",
    "runtime_version": "<semver or commit-sha>"
  },
  "manifest": {
    "path": "<path to the Change Manifest, if one is applicable>",
    "change_id": "<from the manifest>",
    "phase": "<current phase>"
  },
  "context": {
    "changed_files": ["<repo-relative paths>"],
    "tool_name": "<runtime-native tool identifier, optional>",
    "surfaces_touched": ["<surface names from the manifest>"]
  }
}
```

Fields a hook does not need may be absent — the hook must not crash on missing optional fields.

### Output contract

- **Exit code** — the primary signal:
  - `0` — pass (no issues; continue normally)
  - `1` — fail (block; the agent or commit must stop)
  - `2` — warn (non-blocking; surface to the user but continue)
- **Stderr** — human-readable reason, one sentence, always written when exit is non-zero.
- **Stdout** — optional structured JSON for aggregation / dashboards. Shape:
  ```json
  {
    "hook_id": "<stable identifier>",
    "verdict": "pass | fail | warn",
    "findings": [
      {
        "rule_id": "<stable ID, shared with automation-contract.md if applicable>",
        "severity": "info | low | medium | high | critical",
        "message": "<short>",
        "location": "<file:line, URL, or null>",
        "fix_hint": "<optional>"
      }
    ]
  }
  ```

### Exit-code stability

Exit-code semantics are **identical** to `automation-contract.md` so a rule engine built for one can be reused in the other. If a hook fails because of a tool / input error (not a rule violation), exit with code 2 and stderr `"TOOL_ERROR: <reason>"` — runtimes distinguish rule violations from infrastructure failures.

---

## Non-functional requirements

- **Latency budget** — phase-gate and evidence hooks on a single commit / response must complete in **< 500 ms p95**; drift hooks in **< 2 s p95**. Hooks that exceed budget must run asynchronously (runtime emits them to a queue; the agent does not block on them).
- **No network dependency** — same as `automation-contract.md`: hooks must run offline. Network-dependent checks must degrade to `exit 2` (warn), never block.
- **Determinism** — same input ⇒ same output. No reliance on wall-clock for logic (timestamps are inputs, not side channels).
- **No side effects** — hooks must not modify files, open PRs, post to Slack, or mutate runtime state. Reporting is the runtime's job.
- **No AI escalation inside hooks** — hooks are decision *nodes*, not agents; they must not call a model to "decide" whether to block. Model-based judgment belongs in the agent loop, not the hook.

---

## Hook registration

Each runtime has its own registration mechanism; the contract only requires that **every registered hook declares three things**:

1. Its **category** (A / B / C / D above).
2. Its **trigger event** (from the `trigger` enum).
3. Its **enforcement level** (`block` = exit-1 stops execution; `warn` = exit-2 only surfaces a message; `advisory` = even exit-1 is downgraded to a warning).

Runtime bridges map this to their native configuration. Example (Claude Code):

```json
{
  "hooks": {
    "pre-commit": [
      {"script": "hooks/phase-gate/manifest-required.sh", "category": "phase-gate", "level": "block"}
    ],
    "post-tool-use:Edit": [
      {"script": "hooks/drift/sot-consumer-check.js", "category": "drift", "level": "warn"}
    ]
  }
}
```

---

## Requirements on runtime bridges

Each bridge (Claude Code, Cursor, Gemini CLI, Windsurf, Codex) that wants to support runtime hooks must document:

1. **Event mapping** — which native event fires each of `pre-tool-use / post-tool-use / pre-commit / on-stop / on-phase-transition`.
2. **Stdin convention** — how the native event payload is converted into the contract's JSON schema.
3. **Exit-code handling** — how `0 / 1 / 2` translate into runtime-level behavior.
4. **Registration format** — the native configuration file for hooks.
5. **At least one reference hook** — one concrete, runnable example per category A / D at minimum; B / C encouraged.

Bridge-level hooks **may** name specific tools (that is precisely why bridges exist); but their I/O interface still follows this contract.

---

## Anti-patterns

- **Kitchen-sink hooks** — one script that checks 12 things. If it fails, no one knows why. Split by rule.
- **Silent-swallow** — `exit 0` at the end of every hook regardless of outcome. The check was theater.
- **Network-gated hooks** — a slow or flaky network breaks the agent loop. Degrade to warn.
- **Hooks that modify state** — writing the thing you claimed to check passed. Breaks the "no side effects" rule.
- **AI-in-the-loop hooks** — a hook that spawns a model to decide fail/pass. The model should be the main loop; hooks should be mechanical.
- **Hook sprawl** — fifteen hooks all firing on every tool use, each contributing 100 ms. Total latency kills the agent. Budget: the cumulative hook latency budget per event is ≤ 1 s p95.

---

## Relationship to other documents

- `ci-cd-integration-hooks.md` — the CI/CD-layer counterpart. Same exit-code contract; different runtime.
- `automation-contract.md` — the batch-validator capability contract. Rule IDs are shared with runtime hooks where applicable.
- `automation-contract-algorithm.md` — normative algorithm; runtime hooks can reuse rule IDs from there.
- `multi-agent-handoff.md` — phase-gate hooks are the primary enforcement mechanism for the phase-transition rules in that document.
- `reference-implementations/hooks-claude-code/` — the non-normative reference bridge.
