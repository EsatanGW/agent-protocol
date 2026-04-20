# Adapter self-test — Codex

Hermetic smoke test for `../adapter/parse-event.sh`. Exercises the
runtime-env → `AP_*` normalization that any hook using the adapter
relies on.

## Run

```sh
./selftest.sh
```

Exit code `0` means every case passed (or was skipped with `# SKIP`);
non-zero means at least one failure. Output is TAP-ish so CI can parse
it.

## Cases

| # | Case | Asserts |
|---|------|---------|
| 1 | `unset-env-yields-empty-ap-vars` | When `CODEX_HOOK_EVENT` / `CODEX_TOOL_NAME` / `AGENT_PROTOCOL_MANIFEST_PATH` are all unset, every `AP_*` is empty (no crash) |
| 2 | `runtime-env-maps-to-event-and-tool` | `CODEX_HOOK_EVENT=pre-commit` → `AP_EVENT=pre-commit`; `CODEX_TOOL_NAME=edit` → `AP_TOOL=edit` |
| 3 | `manifest-yaml-populates-phase` | When `yq` is on PATH and `AGENT_PROTOCOL_MANIFEST_PATH` points at a YAML with `phase: signoff`, `AP_PHASE=signoff`. Skipped when `yq` is missing |
| 4 | `missing-manifest-leaves-phase-empty` | When `AGENT_PROTOCOL_MANIFEST_PATH` points at a non-existent file, `AP_PHASE` stays empty and the adapter does not error |

## Scope — what this does NOT test

- Whether Codex actually invokes `parse-event.sh` at the right moment.
  That is a per-environment smoke test — see `../DEVIATIONS.md`.
- The downstream hooks that read `AP_*`. They are runtime-agnostic and
  tested by the Claude Code bundle's selftest harness.

## Requirements

- POSIX `sh` (tested on `bash`, `dash`).
- `yq` on `PATH` — optional.
