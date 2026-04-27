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
- **Doc-refresh drift** — a file declared in `sot_map[*].source` was edited in the current diff, but no documentation, spec, or manifest file (`.md`, `docs/**`, `change-manifest*.yaml`) was edited alongside. SoTs are by definition documented surfaces; an edit to one without a paired doc update is either (a) a documentation drift that future readers will hit, or (b) a registration gap (the file should not have been registered as an SoT). Reference implementation: `reference-implementations/hooks-claude-code/hooks/drift-doc-refresh.sh`.

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

## Risky-action interception list

This list extends Category A (phase-gate). It enumerates classes of action that, when initiated by an agent, must be intercepted **before** the action lands — even if no manifest gate fires. The list is the methodology-level minimum; runtime bridges may extend it (a deployment runtime may add "production database migration"; a payments runtime may add "money-movement endpoint"). The list is canonical for Tree D (HITL escalation, [`docs/decision-trees.md`](decision-trees.md)) — every row a Tree D leaf may invoke is enumerated here.

| Risky action class | What triggers it | Default behavior |
|---|---|---|
| Force-push or rewrite history on a protected branch | `git push --force` / `--force-with-lease` to `main` / `master` / `production` / `release` / any branch with branch protection | Block at hook; require explicit user confirmation. The reference implementation `hooks-claude-code/hooks/risky-bash-block.sh` covers the local case |
| Bulk filesystem deletion | `rm -rf <path>` where `<path>` is the repo root, an ancestor of the repo root, or a directory > 100 files | Block at hook; require explicit user confirmation in stderr |
| Production-credential touch | Read or write of a path matching `*production*credentials*`, `~/.aws/credentials`, `*.pem` outside `tests/`, or a runtime-declared secret store | Block at hook; the change must declare the credential touch in `evidence_plan` (or `waivers[]`) before the hook is allowed to pass |
| Production data-store write | Direct `psql`, `mysql`, `mongo`, `redis-cli` etc. against a host whose hostname matches a production-host pattern | Block at hook; production writes must come from a reviewed deploy pipeline, not an agent's shell |
| Money-movement / payment endpoint | Tool call whose target URL or tool name matches a payments-domain pattern declared by the runtime bridge | Block at hook; this row maps to Tree D's "Auth / PII / secrets" + the schema's `escalations[*].trigger: money_movement` |
| Auth / PII / secret-path edit | File edit under a path declared as auth / PII / secrets in `docs/security-supply-chain-disciplines.md` | Block at hook; require Reviewer confirmation that the edit was reviewed by the security-reviewer specialist |
| Major-version dependency bump that crosses a deprecation boundary | Lockfile diff that bumps a package across a major version | Warn at hook (exit 2); the change must register the bump in the manifest's `breaking_change` and / or `uncontrolled_interfaces[*].known_deprecation` before progressing past Phase 4 |
| Deletion of an in-flight manifest or its evidence directory | `rm` / `git rm` on a path matching `*change-manifest*.yaml` or its declared `evidence_plan[*].artifact_location` directory | Block at hook; in-flight manifests are state snapshots, not disposable working files |

**The two enforcement modes.**

- **Mechanical block.** When the runtime supports `pre-tool-use` interception with stdin payload, a hook in `reference-implementations/hooks-<runtime>/hooks/risky-*.sh` returns exit 1 and the action does not land. This is the strong form.
- **Prose-only refuse.** When the runtime cannot intercept a tool call (no hook surface, or the action is initiated outside the agent loop), the discipline degrades to a refusal in the agent's text output: the agent narrates that the action falls in the risky-action list, lists the row, and stops without taking the action. This is the weak form. It depends on the agent's compliance with [`AGENTS.md §Stop conditions`](../AGENTS.md), and is therefore enforceable only in the same way other prose-level rules are.

**Anti-patterns.**

- *Treating the list as exhaustive.* The list is the methodology minimum; production environments add their own. The runtime bridge owns its extensions. A blank extension list is a signal the bridge has not done the threat-modelling exercise, not that the runtime is risk-free.
- *Asking the user to "type yes to confirm" for every block.* If the same risky action recurs every session, the underlying workflow is wrong — surface to the user and request a runbook, not a per-occurrence rubber-stamp.
- *Silencing the block by editing the hook.* The hook is the enforcement; if it fails wrongly on a legitimate path (e.g. a `production` substring in a non-production directory name), the fix is a more precise pattern, not deletion.

---

## Back-pressure pattern

This pattern extends Category D (completion-audit). It addresses the most common failure mode of on-stop hooks: hooks that print "all checks passed" after every turn produce a noisy, low-information log that the agent and the user both stop reading; the next time a real failure fires, it is buried in the same template. Back-pressure inverts the default — hooks are **silent on success and surfaced on failure**.

### The principle

A Category D hook's job is to *push back* on a premature "I'm done" claim. When there is nothing to push back on, the hook produces no output. When a real check fails, the hook surfaces a short, specific failure message and exits non-zero. The agent re-enters its loop with the failure as the next fact, and re-attempts; the user sees a single failure message rather than a wall of "ok / ok / ok / failure / ok."

### Concrete shape

A back-pressure-shaped on-stop hook:

- **Exit 0 silent.** No `stdout`, no `stderr`. The runtime treats this as the default; the user never sees a turn-end "all good" message.
- **Exit 1 / 2 surfaces a one-line cause.** `stderr` carries one short sentence: what failed, where, and a pointer to fix. No "running checks…" preamble; no recap of which checks passed.
- **Cumulative latency stays under the Category D budget.** Multiple back-pressure hooks chained together must sum to less than the section's latency budget; if they exceed, fold them into one hook or split off the slowest into Category C (drift, warn-only).

### Why this matters

The signal-to-noise ratio of a turn-end log is what determines whether the agent's next turn re-reads it. A hook that prints anything on success poisons the channel: the agent learns the channel is for chatter, and treats real failures the same way. A hook that prints only on failure stays meaningful — the failure is the entire signal.

This is the runtime-side counterpart of [`docs/output-craft-discipline.md`](output-craft-discipline.md): every element of agent-visible output must earn its place. Hook output is no exception.

### Anti-patterns the pattern rejects

- *Printing "all 12 checks passed" at every turn end.* The agent stops reading the channel; the next real failure is buried.
- *Echoing each check's name even on success.* "Running drift check… ok. Running evidence check… ok." The 9 lines tell the agent nothing it did not already assume.
- *Surfacing a 30-line stack trace from a failed check.* The agent's context is now full of trace; the next-turn cause-of-failure summary is overshadowed. Exit non-zero with a one-line cause; put the trace in a side-channel artifact (file under the working space, per `docs/phase-gate-discipline.md` Rule 5a) and reference it by path.
- *Treating exit 2 as "definitely OK."* Exit 2 is a warn — the user should still see the cause once. The pattern is "silent on 0; one line on 2; one line on 1," not "silent on anything below failure."

### Reference

A worked walk-through of building a back-pressure-shaped completion-audit hook lives in [`skills/engineering-workflow/references/back-pressure-loop.md`](../skills/engineering-workflow/references/back-pressure-loop.md). The reference is non-normative; the contract above is the binding shape.

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

Runtime bridges map this to their native configuration. Example (Claude Code — uses native PascalCase events `PreToolUse` / `PostToolUse` / `Stop`, grouped by `matcher`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          {
            "type": "command",
            "command": "sh hooks/phase-gate/manifest-required.sh",
            "agentProtocol": {"category": "phase-gate", "level": "block"}
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "node hooks/drift/sot-consumer-check.js",
            "agentProtocol": {"category": "drift", "level": "warn"}
          }
        ]
      }
    ]
  }
}
```

Note the mapping: the contract's abstract `pre-commit` trigger maps to `PreToolUse` with `matcher: "Bash(git commit*)"` (so exit code 1 blocks the Bash invocation before the commit is written); the contract's `post-tool-use:Edit` maps to `PostToolUse` with `matcher: "Edit|Write|MultiEdit"`. Each bridge is free to pick the native event that best preserves blocking semantics.

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
- `reference-implementations/hooks-claude-code/` — the primary non-normative reference bridge (hosts the hook scripts).
- `reference-implementations/hooks-cursor/`, `hooks-gemini-cli/`, `hooks-windsurf/`, `hooks-codex/` — thin adapter bundles that reuse the Claude Code hook scripts under each runtime's native registration format.
