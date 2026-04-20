# Deviations from the Runtime Hook Contract — Windsurf adapter

Known gaps between this adapter and `docs/runtime-hook-contract.md`.

---

## 1. Event-trigger mapping is approximate

Windsurf's hook surface evolves; the names used in
`settings.example.json` reflect current best-guess mappings:

| Contract trigger | Windsurf closest |
|------------------|------------------|
| `pre-commit`         | `beforeCommand` with `command = "git commit*"` |
| `post-tool-use:Edit` | `afterEdit` |
| `pre-push` (net hook)| `beforeCommand` with `command = "git push*"` |
| `on-stop`            | `sessionEnd` |

If your Windsurf version renames these, adjust
`settings.example.json` — hook logic stays fixed.

---

## 2. Runtime-wiring selftest is still a per-workspace concern

**Covered since v1.6.0:** the adapter's `parse-event.sh` normalization is
exercised by `selftests/selftest.sh` — a hermetic smoke test that sets
synthetic runtime env vars and asserts `AP_EVENT` / `AP_TOOL` /
`AP_STAGED_FILES` / `AP_PHASE` come out right. Run via:

```sh
sh reference-implementations/hooks-windsurf/selftests/selftest.sh
```

CI runs this alongside the Claude Code bundle selftest.

**Still uncovered:** whether Windsurf itself invokes the command at the
right moment (i.e. the `settings.example.json` wiring). That remains a
per-workspace smoke test. A renamed Windsurf trigger will fail this
test but not the adapter selftest, which is the gap this section
documents.
