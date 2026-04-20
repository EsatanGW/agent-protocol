# Deviations from the Runtime Hook Contract — Codex adapter

Known gaps between this adapter and `docs/runtime-hook-contract.md`.

---

## 1. Event-trigger mapping is approximate

Codex's hook surface — and any wrapper CLI around it — varies by
deployment. The `settings.example.json` mapping:

| Contract trigger | Codex closest |
|------------------|---------------|
| `pre-commit`          | `preExec` matching `git commit*` |
| `post-tool-use:Edit`  | `postExec` matching `edit|write` |
| `pre-push` (net hook) | `preExec` matching `git push*` |
| `on-stop`             | `onComplete` |

If your Codex install uses a different event taxonomy, keep the
contract's abstract triggers in mind and wire the same commands onto
the equivalent native events.

---

## 2. No runtime-level selftest

The hook-logic selftest lives in the Claude Code bundle's
`selftests/` and is runtime-agnostic. Wiring verification (does Codex
actually invoke the command at the right moment?) is a per-
environment smoke test.
