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

## 2. Runtime-wiring selftest is still a per-environment concern

**Covered since v1.6.0:** the adapter's `parse-event.sh` normalization is
exercised by `selftests/selftest.sh` — a hermetic smoke test that sets
synthetic runtime env vars and asserts `AP_EVENT` / `AP_TOOL` /
`AP_STAGED_FILES` / `AP_PHASE` come out right. Run via:

```sh
sh reference-implementations/hooks-codex/selftests/selftest.sh
```

CI runs this alongside the Claude Code bundle selftest.

**Still uncovered:** whether Codex itself invokes the command at the
right moment (i.e. the `settings.example.json` wiring). That remains a
per-environment smoke test. A renamed Codex trigger will fail this
test but not the adapter selftest, which is the gap this section
documents.
