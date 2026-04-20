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

## 2. No runtime-level selftest

The hook-logic selftest lives in the Claude Code bundle's `selftests/`
and is runtime-agnostic. Wiring verification (does Windsurf actually
invoke the command at the right moment?) requires a per-workspace
smoke test.
