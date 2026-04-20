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

## 3. No runtime-level selftest

The Claude Code bundle's `selftests/` harness is runtime-agnostic — it
invokes hooks directly — so it covers the adapter's hook *logic*. It
does **not** cover the Cursor wiring itself (whether Cursor actually
fires the command at the right moment). That belongs in a per-workspace
smoke test: stage a multi-file diff with no manifest, attempt a commit,
confirm the hook blocks.
