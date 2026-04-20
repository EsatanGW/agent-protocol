# Deviations from the Runtime Hook Contract

Known gaps between this reference bundle and `docs/runtime-hook-contract.md`. Documenting them openly rather than claiming full conformance.

---

## 1. Selftest suite — resolved

Originally flagged as a gap. As of v1.3.0 the bundle ships a hermetic
fixture-based harness at `selftests/selftest.sh` with eleven cases
covering every category (A / B / C / D). See `selftests/README.md` for
the `expected` grammar and how to add new cases. Teams enabling these
hooks in `block` mode should run `./selftests/selftest.sh` in CI on any
PR that edits `hooks/` or `selftests/`.

---

## 2. Event-payload schema is inferred, not declared

The contract defines a JSON input schema on stdin. Claude Code's actual event payloads are runtime-defined and have evolved across versions. This bundle does a best-effort parse:

- Tries stdin first, then argv.
- Falls back to env var `CLAUDE_TOOL_NAME` etc. if the payload is missing fields.
- Uses `yq -p json` to read the payload, which is permissive about missing fields.

**Mitigation:** every script tolerates absent optional fields per the contract ("fields a hook does not need may be absent — the hook must not crash on missing optional fields").

**Impact:** low for the four hooks shipped. Higher for hooks that need precise trigger provenance (e.g. distinguishing a `post-tool-use:Edit` from `post-tool-use:MultiEdit`).

### 2.1 Historical note (resolved in 1.2.1)

v1.2.0's `settings.example.json` used invented event names (`preCommit` / `postToolUse` / `stop`) that do not exist in Claude Code's hook runtime. The correct native events are `PreToolUse` / `PostToolUse` / `Stop` (PascalCase), grouped by matcher per Claude Code's hooks schema. 1.2.1 rewrote the example file and the `docs/runtime-hook-contract.md` example to use the real format. Teams that hand-copied the 1.2.0 example need to re-copy from 1.2.1 — the old keys were silently ignored by Claude Code, so the hooks never actually fired.

---

## 3. Structured stdout is opt-in, not default

The contract declares structured stdout as **optional**. These hooks gate it behind `AGENT_PROTOCOL_STRUCTURED_OUTPUT=1` so that default use (plain stderr message) stays ergonomic for terminal users. Automation platforms that want to aggregate findings set the env var.

**Impact:** none — this is an allowed deviation (the contract marks stdout as optional).

---

## 4. Network-check degradation — implemented

As of v1.3.0 the bundle ships `hooks/consumer-registry-check.sh`, the
reference implementation of the contract's network-degradation clause.
The hook walks every `.consumers[].external_registry_url` in the
manifest, probes each with `curl -fsS --max-time ${AGENT_PROTOCOL_NET_TIMEOUT:-5}`,
and emits `exit 2` (warn) — never `exit 1` — on timeout, DNS failure,
non-HTTP URL, or non-2xx response. Missing `curl` or `yq` degrades to
`exit 2` via the same `TOOL_ERROR` path used elsewhere in this bundle.

Selftest fixtures under `selftests/fixtures/consumer-registry-check/`
exercise the no-consumers, reachable, and unreachable branches by way
of a `curl` stub that honors a per-fixture `curl-exit` file. A real
end-to-end smoke (against a reachable vs. deliberately-invalid host)
remains outside the selftest because CI sandboxes typically block
arbitrary egress.

---

## 5. Cross-runtime coverage — partial

As of v1.4.0 the repo ships thin adapter bundles for four additional
runtimes:

- [`../hooks-cursor/`](../hooks-cursor/) — Cursor (JSON config)
- [`../hooks-gemini-cli/`](../hooks-gemini-cli/) — Gemini CLI (TOML config)
- [`../hooks-windsurf/`](../hooks-windsurf/) — Windsurf (JSON config)
- [`../hooks-codex/`](../hooks-codex/) — Codex (JSON config)

Each adapter ships a README, its own DEVIATIONS, a runtime-native
settings example, and an `adapter/parse-event.sh` that normalizes the
runtime's event payload into cross-runtime `AP_*` env vars. The hook
scripts themselves remain in this (the Claude Code) bundle — the
adapters point back via relative or absolute paths, so a regression
fix to `manifest-required.sh` propagates everywhere with a single
edit. **Still outstanding:** runtime-wiring smoke tests per adapter
(the `selftests/` harness exercises hook logic, not hook registration).
