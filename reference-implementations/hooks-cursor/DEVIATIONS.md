# Deviations from the Runtime Hook Contract — Cursor adapter

Known gaps between this adapter and `docs/runtime-hook-contract.md`.

---

## 1. Event-trigger mapping is approximate

Cursor's hook / rule surface has changed several times across releases
and does not publish a stable enumeration of trigger points. This
adapter maps the contract's abstract triggers onto the closest
available Cursor construct:

| Contract trigger | Cursor construct used |
|------------------|-----------------------|
| `pre-commit`        | Workspace rule + pre-commit shell command |
| `post-tool-use:Edit`| Workspace rule + on-file-change hook |
| `on-stop`           | End-of-session hook |

If Cursor removes or renames any of these, adjust the wiring in
`settings.example.json` — the hook scripts themselves do not change.

---

## 2. Event-payload contract is not enforced

Cursor does not pass a JSON event payload on stdin in the same shape
as Claude Code. The four reference hooks do not depend on the payload
(they read from `git` and `$AGENT_PROTOCOL_MANIFEST_PATH`), so this is
not currently a blocker. Hooks that do depend on payload fields must
read the normalized `AP_*` env vars exported by
`adapter/parse-event.sh`.

---

## 3. Runtime-wiring selftest is still a per-workspace concern

**Covered since v1.6.0:** the adapter's `parse-event.sh` normalization is
exercised by `selftests/selftest.sh` — a hermetic smoke test that sets
synthetic runtime env vars and asserts `AP_EVENT` / `AP_TOOL` /
`AP_STAGED_FILES` / `AP_PHASE` come out right. Run via:

```sh
sh reference-implementations/hooks-cursor/selftests/selftest.sh
```

CI runs this alongside the Claude Code bundle selftest.

**Still uncovered:** whether Cursor itself invokes the command at the
right moment (i.e. the `settings.example.json` wiring). That remains a
per-workspace smoke test — stage a multi-file diff with no manifest,
attempt a commit, confirm the hook blocks. A renamed Cursor trigger
will fail this test but not the adapter selftest, which is the gap this
section documents.
