# Deviations from the Runtime Hook Contract

Known gaps between this reference bundle and `docs/runtime-hook-contract.md`. Documenting them openly rather than claiming full conformance.

---

## 1. No selftest suite (yet)

The contract's "requirements on bridges" section asks for at least one runnable example per category. This bundle ships one example per category (A / B / C / D), but does **not** ship a fixture-based selftest harness.

**Mitigation:** each script is small (< 80 lines) and the rule IDs are declared in the header, so a team can write fixture tests by hand. A future release will add `selftest.sh` + `selftests/fixtures/`.

**Impact:** moderate. Teams adopting these hooks should spot-check on known-good and known-bad manifests before enabling `block`.

---

## 2. Event-payload schema is inferred, not declared

The contract defines a JSON input schema on stdin. Claude Code's actual event payloads are runtime-defined and have evolved across versions. This bundle does a best-effort parse:

- Tries stdin first, then argv.
- Falls back to env var `CLAUDE_TOOL_NAME` etc. if the payload is missing fields.
- Uses `yq -p json` to read the payload, which is permissive about missing fields.

**Mitigation:** every script tolerates absent optional fields per the contract ("fields a hook does not need may be absent — the hook must not crash on missing optional fields").

**Impact:** low for the four hooks shipped. Higher for hooks that need precise trigger provenance (e.g. distinguishing a `post-tool-use:Edit` from `post-tool-use:MultiEdit`).

---

## 3. Structured stdout is opt-in, not default

The contract declares structured stdout as **optional**. These hooks gate it behind `AGENT_PROTOCOL_STRUCTURED_OUTPUT=1` so that default use (plain stderr message) stays ergonomic for terminal users. Automation platforms that want to aggregate findings set the env var.

**Impact:** none — this is an allowed deviation (the contract marks stdout as optional).

---

## 4. No network-check degradation

The contract requires that "checks that genuinely require network must degrade to advisory." None of the four shipped hooks make network calls, so this clause is vacuously satisfied. A future `consumer-registry-check.sh` hook (not yet written) would test remote registry lookup and would need to degrade to `exit 2` on timeout.

**Impact:** none today. Flagged so future additions keep the rule in mind.

---

## 5. Only Claude Code is covered

The contract describes a runtime-neutral hook model. This directory ships only the Claude Code bridge. Cursor, Gemini CLI, Windsurf, and Codex bridges are not yet written.

**Mitigation:** each hook is pure shell + `yq`. Re-registering the same scripts under a different runtime's event mechanism should work; only the event-payload parsing at the top of each script needs to change.

**Impact:** medium. Teams on other runtimes have a template to follow but no ready-to-copy bundle.
