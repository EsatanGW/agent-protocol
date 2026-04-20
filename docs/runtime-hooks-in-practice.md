# Runtime Hooks in Practice

> Companion to [`runtime-hook-contract.md`](./runtime-hook-contract.md) (the normative capability contract) and the reference bundles under [`reference-implementations/hooks-*`](../reference-implementations/). This page is the how-to: which hooks exist, how to install them on Claude Code, how to wire adapters on other runtimes, how to stage adoption, and how to write your own hook without re-inventing the contract.

---

## What runtime hooks are

Event-driven guardrails that fire **inside the AI agent's own execution loop** — before each tool call, after each edit, at end-of-turn — not in CI. They exist to catch failures early (while the agent can still correct) instead of late (after a PR has shipped).

Sibling to [`ci-cd-integration-hooks.md`](./ci-cd-integration-hooks.md), which covers the CI/CD layer. The two share the same exit-code contract: `0 = pass / 1 = block / 2 = warn`.

## The five reference hooks

Ship at [`reference-implementations/hooks-claude-code/hooks/`](../reference-implementations/hooks-claude-code/hooks/):

| Hook | Category | Checks | Blocks (exit 1) / Warns (exit 2) |
|---|---|---|---|
| `manifest-required.sh` | A phase-gate | Non-trivial git commits have a staged Change Manifest | Block |
| `evidence-artifact-exists.sh` | B evidence | Every `evidence_plan[].status == collected` has a resolvable `artifact_location` | Block |
| `sot-drift-check.sh` | C drift | Declared `sot_map[].source` files appear in `git diff --name-only` | Warn |
| `consumer-registry-check.sh` | C drift (network) | Each `consumers[].external_registry_url` responds 2xx within `AGENT_PROTOCOL_NET_TIMEOUT` | Warn |
| `completion-audit.sh` | D completion-audit | On-stop: no pending `evidence_plan`, no `accepted_by: unaccepted`, every escalation has `resolved_at`, `phase: observe` has `handoff_narrative` | Block |

## Install on Claude Code

Prerequisites:

- [`yq`](https://github.com/mikefarah/yq) v4+ on PATH (`brew install yq` / `apt install yq`). If missing, hooks exit 2 with `TOOL_ERROR: yq not found on PATH` — they degrade gracefully, they do not spuriously block commits.
- `git` on PATH (already assumed).

**Step 1.** Copy the hooks bundle to a stable location (don't invoke directly from the plugin cache — version bumps move that path):

```bash
mkdir -p ~/.claude/agent-protocol-hooks
cp -r reference-implementations/hooks-claude-code/hooks ~/.claude/agent-protocol-hooks/
```

Or for project-local hooks (only fire inside this repo):

```bash
mkdir -p <your-project>/.claude/hooks
cp reference-implementations/hooks-claude-code/hooks/*.sh <your-project>/.claude/hooks/
```

**Step 2.** Merge the hook block from [`reference-implementations/hooks-claude-code/settings.example.json`](../reference-implementations/hooks-claude-code/settings.example.json) into your `~/.claude/settings.json` (global) or `<your-project>/.claude/settings.json` (project-local). The shape is:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit*)",
        "hooks": [
          {"type": "command", "command": "sh ${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/hooks/manifest-required.sh"},
          {"type": "command", "command": "sh ${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/hooks/evidence-artifact-exists.sh"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {"type": "command", "command": "sh ${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/hooks/sot-drift-check.sh"}
        ]
      }
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "sh ${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/hooks/completion-audit.sh"}]}
    ]
  }
}
```

**Step 3.** Reload plugins (`/reload-plugins`). Trigger a test: start a commit with an unrelated file and no manifest — `manifest-required.sh` should fire and exit 1.

## Install on other runtimes

The shipped hooks are runtime-agnostic shell scripts. The four adapter bundles under `reference-implementations/hooks-{cursor,gemini-cli,windsurf,codex}/` each ship:

- A runtime-native settings example (JSON for Cursor / Windsurf / Codex, TOML for Gemini CLI).
- An `adapter/parse-event.sh` that normalizes the runtime's event payload into the same `AP_EVENT` / `AP_TOOL` / `AP_STAGED_FILES` / `AP_PHASE` env vars the shared hooks read.
- A `DEVIATIONS.md` pinning the runtime-specific caveats.
- A hermetic selftest at `selftests/selftest.sh` that asserts the adapter wiring is correct without exercising the runtime itself.

The hook scripts themselves are not duplicated — adapter settings point back at the Claude Code bundle's `hooks/` directory so a regression fix propagates everywhere with a single edit.

## Contract-to-event mapping

| Contract trigger (abstract) | Claude Code native event | Matcher | Why this mapping |
|---|---|---|---|
| `pre-commit` | `PreToolUse` | `Bash(git commit*)` | Fires **before** the Bash tool runs `git commit` — exit 1 cancels the commit before it lands. `PostToolUse` would fire after the commit, giving the hook no blocking power. |
| `post-tool-use:Edit` | `PostToolUse` | `Edit\|Write\|MultiEdit` | Drift checks are informational — they read state after an edit and warn, not block. |
| `on-stop` | `Stop` | (no matcher) | Fires at end-of-turn before the agent surfaces "done" to the user. Exit 1 blocks the turn from completing. |

Other contract triggers (`on-phase-transition`) are not currently mapped by the reference bundle — teams can add custom hooks firing on `UserPromptSubmit` or `SessionStart` per [`runtime-hook-contract.md`](./runtime-hook-contract.md).

## Configuration knobs (environment variables)

| Variable | Default | Effect |
|---|---|---|
| `AGENT_PROTOCOL_MANIFEST_PATH` | `git ls-files change-manifest*.yaml \| head -1` | Point hooks at a specific manifest path; useful when multiple manifests coexist in a monorepo. |
| `AGENT_PROTOCOL_MIN_EVIDENCE_PER_PRIMARY` | `1` | Minimum evidence items required per `role: primary` surface. Raise for stricter gating. |
| `AGENT_PROTOCOL_LEAN_SKIP_MANIFEST` | unset | Set to `1` and create an empty `lean-mode.flag` file at the repo root to let `manifest-required.sh` pass for Lean-mode trivial changes. |
| `AGENT_PROTOCOL_STRUCTURED_OUTPUT` | unset | Set to `1` to emit structured JSON on stdout (per the contract's optional output shape) in addition to stderr messages. Useful for aggregation dashboards. |
| `AGENT_PROTOCOL_NET_TIMEOUT` | `5` | Seconds for the `consumer-registry-check.sh` network probe before the hook degrades to advisory. |

Set these in `~/.zshrc`, `~/.bashrc`, or per-project `.envrc` (direnv) — **not** inside the hook scripts themselves.

## Adoption ramp

Don't enable all four hooks on day one. Common staging:

1. **Week 1 — Observe.** Install `sot-drift-check.sh` only (warn-level; can't block). See what fires, tune the manifest if the signal is noisy.
2. **Week 2 — Gate.** Add `manifest-required.sh` at block-level. Creates a forcing function: non-trivial commits now require a manifest.
3. **Week 3 — Evidence.** Add `evidence-artifact-exists.sh`. Catches the "`status: collected` with blank `artifact_location`" failure mode.
4. **Week 4 — Completion.** Add `completion-audit.sh` (on-stop). The highest-leverage hook — refuses to let the agent say "done" when the manifest is materially incomplete.

Skipping straight to stage 4 usually produces "hook fatigue" — teams disable the whole bundle rather than tune it.

## Writing your own hook

The four shipped hooks are ~50–80 lines of POSIX sh each; read them as templates. A custom hook must:

1. Parse the event payload from stdin (or Claude Code env vars; the reference hooks do a best-effort read of both).
2. Read the Change Manifest via `yq` (or any YAML library in your language of choice — hooks aren't required to be shell).
3. Exit `0` / `1` / `2` per the contract. Stderr on non-zero with a one-sentence human message prefixed by `[agent-protocol/<rule_id>]`.
4. Stay offline, deterministic, side-effect-free, and under the latency budget (< 500 ms for A/B; < 2 s for C). **No model-in-hook** — hooks are mechanical decision nodes, not agents.

Register the custom hook by adding another `{"type": "command", "command": "..."}` entry under the appropriate event's `hooks` array in `settings.json`.

See [`runtime-hook-contract.md`](./runtime-hook-contract.md) for the full anti-pattern list (kitchen-sink hooks, silent-swallow, network-gated, side-effect, AI-in-the-loop, hook sprawl).

## See also

- [`runtime-hook-contract.md`](./runtime-hook-contract.md) — normative capability contract (event schema, latency budgets, category definitions).
- [`ci-cd-integration-hooks.md`](./ci-cd-integration-hooks.md) — sibling CI-layer discipline; same exit codes, different trigger surface.
- [`../reference-implementations/hooks-claude-code/`](../reference-implementations/hooks-claude-code/) — primary bundle (five hooks + settings + selftests).
- [`../reference-implementations/hooks-cursor/`](../reference-implementations/hooks-cursor/), [`hooks-gemini-cli/`](../reference-implementations/hooks-gemini-cli/), [`hooks-windsurf/`](../reference-implementations/hooks-windsurf/), [`hooks-codex/`](../reference-implementations/hooks-codex/) — adapter bundles.
