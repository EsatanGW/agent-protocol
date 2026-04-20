# Deviations from the Runtime Hook Contract — Gemini CLI adapter

Known gaps between this adapter and `docs/runtime-hook-contract.md`.

---

## 1. TOML vs. JSON config

Gemini CLI consumes TOML for settings; the contract examples in
`docs/runtime-hook-contract.md` use JSON for illustration. The
`settings.example.toml` in this adapter is semantically equivalent to
the Claude Code `settings.example.json` — same command list, same exit
codes expected — only the serialization differs.

---

## 2. Event-trigger mapping approximates contract triggers

Gemini CLI's hook triggers may not have a 1:1 mapping to the
contract's four abstract triggers. This adapter uses the closest
semantic fit and accepts that some hooks may fire once more or once
less per session than the Claude Code wiring.

| Contract trigger | Gemini CLI closest |
|------------------|--------------------|
| `pre-commit`        | `pre_command` with `matches = "git commit*"` |
| `post-tool-use:Edit`| `post_tool` with `matches = "edit|write"` |
| `pre-push` (net hook) | `pre_command` with `matches = "git push*"` |
| `on-stop`           | `session_end` |

If your Gemini CLI version names these differently, adjust
`settings.example.toml` to match; hook logic stays fixed.

---

## 3. No runtime-level selftest

The hook-logic selftest lives in the Claude Code bundle's `selftests/`
and is runtime-agnostic. Wiring verification (does Gemini CLI actually
invoke the command at the right moment?) requires a per-workspace
smoke test.
