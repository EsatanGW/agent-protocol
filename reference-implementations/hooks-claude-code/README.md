# Reference Runtime Hooks — Claude Code

> **Not normative.** This directory holds **example** Claude Code runtime hooks that demonstrate `docs/runtime-hook-contract.md`. The methodology layer never ships tool-specific hooks; this directory exists so teams adopting the methodology on Claude Code have a concrete starting point they can copy, customize, and narrow.

These hooks are deliberately **shell scripts with zero runtime dependencies** (POSIX sh + `yq` for YAML reads, nothing else). They are runnable on macOS / Linux / any CI container with `yq` installed. A Node / Python rewrite would fit equally well; the point is the contract, not the language.

---

## What's here

| Hook | Category | Contract trigger | Claude Code event + matcher | Enforcement |
|------|----------|------------------|-----------------------------|-------------|
| [`hooks/manifest-required.sh`](./hooks/manifest-required.sh) | A: phase-gate | `pre-commit` | `PreToolUse` + `matcher: "Bash(git commit*)"` | block (exit 1) |
| [`hooks/evidence-artifact-exists.sh`](./hooks/evidence-artifact-exists.sh) | B: evidence | `pre-commit` | `PreToolUse` + `matcher: "Bash(git commit*)"` | block (exit 1) |
| [`hooks/sot-drift-check.sh`](./hooks/sot-drift-check.sh) | C: drift | `post-tool-use:Edit` | `PostToolUse` + `matcher: "Edit\|Write\|MultiEdit"` | warn (exit 2) |
| [`hooks/drift-doc-refresh.sh`](./hooks/drift-doc-refresh.sh) | C: drift | `post-tool-use:Edit` | `PostToolUse` + `matcher: "Edit\|Write\|MultiEdit"` | warn (exit 2) |
| [`hooks/consumer-registry-check.sh`](./hooks/consumer-registry-check.sh) | C: drift (network) | `pre-tool-use:Bash("git push*")` | `PreToolUse` + `matcher: "Bash(git push*)"` | warn (exit 2) |
| [`hooks/completion-audit.sh`](./hooks/completion-audit.sh) | D: completion-audit | `on-stop` | `Stop` (no matcher) | block (exit 1) |

**Why `PreToolUse` and not `PostToolUse` for commit gating:** Claude Code's `PreToolUse` runs *before* the Bash tool invokes `git commit`; exit code 1 cancels the tool call. `PostToolUse` would fire *after* the commit was already written, giving the hook no blocking power. Use `PreToolUse` for any hook whose purpose is to prevent an action.

All four follow the I/O contract from `docs/runtime-hook-contract.md`: JSON event on stdin, exit code `0 / 1 / 2`, human-readable stderr message on non-zero, optional structured stdout JSON. Each script begins with a contract-stamp header comment that references the category, trigger, and rule IDs it implements.

See [`DEVIATIONS.md`](./DEVIATIONS.md) for known gaps between this reference bundle and the full contract.

---

## How to install

### Option 1: copy into your `.claude/` directory

```bash
cp -r reference-implementations/hooks-claude-code/hooks ~/.claude/agent-protocol-hooks
cp reference-implementations/hooks-claude-code/settings.example.json ~/.claude/settings.json   # or merge manually
```

Then edit `~/.claude/settings.json` so paths resolve to the copied location. The bundled `settings.example.json` uses `${CLAUDE_CONFIG_DIR}/agent-protocol-hooks/...` — keep that pattern so the hooks remain portable.

### Option 2: project-local hooks

```bash
cp -r reference-implementations/hooks-claude-code/hooks <your-project>/.claude/hooks
```

Add the hook block from `settings.example.json` into `<your-project>/.claude/settings.json`. Project-local hooks only fire when Claude Code is run inside that project — useful when a single machine works across multiple repos with different methodology gates.

### Option 3: read only — pick rules, write your own

Open each `.sh` file to see the check logic, then reimplement in whatever language your team already uses (TypeScript, Python, Go, Rust). The rule IDs are declared at the top of each script so your rewrite can claim compatibility with this bundle.

---

## Dependencies

- POSIX-compatible shell (`sh` / `bash` / `zsh`).
- [`yq`](https://github.com/mikefarah/yq) (v4+) for reading the manifest YAML.
- `git` (used only by `sot-drift-check.sh` to compute touched paths).

No Node, no Python, no network, no API keys. If `yq` is missing, hooks exit code `2` with `TOOL_ERROR: yq not found on PATH` — per the contract, tool errors are surfaced as warnings, not rule-violation blocks.

---

## Required environment

Each hook reads these optional env vars to stay contract-compliant when the Claude Code event payload is thin:

| Var | Purpose | Default |
|-----|---------|---------|
| `AGENT_PROTOCOL_MANIFEST_PATH` | Path to the Change Manifest relative to repo root | auto-discover via `git ls-files change-manifest*.yaml \| head -1` |
| `AGENT_PROTOCOL_MIN_EVIDENCE_PER_PRIMARY` | Integer — minimum evidence items per primary surface | `1` |
| `AGENT_PROTOCOL_LEAN_SKIP_MANIFEST` | If set to `1`, `manifest-required.sh` passes when `lean-mode.flag` exists at repo root | unset (manifest always required) |
| `AGENT_PROTOCOL_NET_TIMEOUT` | Seconds before `consumer-registry-check.sh` declares a registry unreachable (never escalates past `exit 2`) | `5` |

Set these in your shell profile or per-project `.envrc` (direnv) — **not** inside the hooks themselves.

---

## Mapping to the contract

| Contract section | How this bundle satisfies it |
|------------------|-----------------------------|
| Four categories (A / B / C / D) | One script per category; no cross-category hooks. |
| JSON-in stdin | Each script parses `$1`-style or stdin-style event payload via `yq -p json`. |
| Exit codes 0 / 1 / 2 | Scripts exit with these codes; never `3+`. |
| Stderr on non-zero | Always a one-sentence message beginning with `[agent-protocol/<rule_id>]`. |
| Stdout JSON (optional) | Emitted only when `AGENT_PROTOCOL_STRUCTURED_OUTPUT=1`. |
| Latency budget | All four scripts complete in < 100 ms on a manifest with ~50 sot_map entries and ~30 evidence items. |
| No side effects | Scripts only read files. They never write, commit, or invoke network. |

---

## Testing

The `selftests/` directory (to be populated) will contain fixture events + fixture manifests. Running `./selftest.sh` (when present) should exercise each hook against pass / fail fixtures and confirm exit codes.

---

## Choosing a scope

Start narrow. Install one or two hooks, see them fire, tune the signal. Common adoption stages:

1. **Observation** — install `sot-drift-check.sh` only, at `warn` level. See what fires for a week.
2. **Gate** — add `manifest-required.sh` at `block` level for pre-commit on non-trivial branches.
3. **Evidence** — add `evidence-artifact-exists.sh` once the team is reliably producing manifests.
4. **Completion** — add `completion-audit.sh` when you're ready for the agent to refuse to say "done" when it isn't.

Skipping straight to stage 4 on day one produces "hook fatigue" — teams disable the whole bundle rather than tune it. Do not.

---

## See also

- [`docs/runtime-hook-contract.md`](../../docs/runtime-hook-contract.md) — capability contract (normative).
- [`docs/automation-contract.md`](../../docs/automation-contract.md) — batch-validator capability contract (sibling).
- [`docs/ci-cd-integration-hooks.md`](../../docs/ci-cd-integration-hooks.md) — CI/CD-layer hook spec (sibling).
- [`reference-implementations/validator-posix-shell/`](../validator-posix-shell/) — batch-validator reference implementation.
