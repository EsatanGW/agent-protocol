# Adapter self-test — Cursor

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
| 1 | `unset-env-yields-empty-ap-vars` | When `CURSOR_HOOK_TRIGGER` / `CURSOR_TOOL` / `AGENT_PROTOCOL_MANIFEST_PATH` are all unset, every `AP_*` is empty (no crash) |
| 2 | `runtime-env-maps-to-event-and-tool` | `CURSOR_HOOK_TRIGGER=pre-commit` → `AP_EVENT=pre-commit`; `CURSOR_TOOL=Edit` → `AP_TOOL=Edit` |
| 3 | `manifest-yaml-populates-phase` | When `yq` is on PATH and `AGENT_PROTOCOL_MANIFEST_PATH` points at a YAML with `phase: implement`, `AP_PHASE=implement`. Skipped when `yq` is missing |
| 4 | `missing-manifest-leaves-phase-empty` | When `AGENT_PROTOCOL_MANIFEST_PATH` points at a non-existent file, `AP_PHASE` stays empty and the adapter does not error |

## Scope — what this does NOT test

- Whether Cursor actually invokes `parse-event.sh` at the right moment.
  That is a per-workspace smoke test — see `../DEVIATIONS.md`.
- The downstream hooks that read `AP_*`. They are runtime-agnostic and
  tested by the Claude Code bundle's selftest harness.

The selftest deliberately exercises **only the adapter layer**, because
that is the layer a renamed runtime env var would silently break.

## Requirements

- POSIX `sh` (tested on `bash`, `dash`).
- `yq` on `PATH` — optional; its absence triggers the SKIP path on the
  one case that needs it.
