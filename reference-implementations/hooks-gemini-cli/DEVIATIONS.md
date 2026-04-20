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

## 3. Runtime-wiring selftest is still a per-workspace concern

**Covered since v1.6.0:** the adapter's `parse-event.sh` normalization is
exercised by `selftests/selftest.sh` — a hermetic smoke test that sets
synthetic runtime env vars and asserts `AP_EVENT` / `AP_TOOL` /
`AP_STAGED_FILES` / `AP_PHASE` come out right. Run via:

```sh
sh reference-implementations/hooks-gemini-cli/selftests/selftest.sh
```

CI runs this alongside the Claude Code bundle selftest.

**Still uncovered:** whether Gemini CLI itself invokes the command at
the right moment (i.e. the `settings.example.toml` wiring). That
remains a per-workspace smoke test. A renamed Gemini CLI trigger will
fail this test but not the adapter selftest, which is the gap this
section documents.
