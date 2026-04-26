# Reference Runtime Hooks — Cursor adapter

> **Not normative.** Thin adapter that reuses the six hook scripts from
> [`../hooks-claude-code/hooks/`](../hooks-claude-code/hooks/) and registers
> them against Cursor's native rule / command model. Hook logic lives in
> exactly one place — this directory only knows how to wire it up.

---

## What's here

| File | Purpose |
|------|---------|
| `settings.example.json` | Copy into `.cursor/config.json` (workspace) or the user-level equivalent |
| `adapter/parse-event.sh` | Cursor event → `AP_*` env vars (stub today; active once hooks consume `AP_*`) |
| `DEVIATIONS.md` | Cursor-specific quirks vs. the capability contract |

The hook scripts themselves are **not** duplicated here. Each entry in
`settings.example.json` shells out to `../hooks-claude-code/hooks/<name>.sh`,
so a regression fix to `manifest-required.sh` propagates everywhere with
a single edit.

---

## How to install

1. Copy this directory next to your Cursor workspace root, or symlink it
   from `~/.cursor/hooks/agent-protocol`.
2. Merge `settings.example.json` into your Cursor config (workspace-level
   `.cursor/config.json` or the user-level equivalent in your Cursor data
   directory). Cursor config formats evolve faster than this document; if
   the keys look wrong, treat the example as the normative shape and let
   Cursor's current schema override the concrete key names.
3. Confirm the relative path `../hooks-claude-code/hooks/` resolves from
   the config's working directory. Absolute paths are also fine and
   remove the coupling to this directory layout.

---

## Event normalization

Each hook already pulls its inputs from `git` and
`$AGENT_PROTOCOL_MANIFEST_PATH`, so Cursor's event payload format is not
on any hook's critical path. `adapter/parse-event.sh` exists as an
extension point: future hooks that want richer event context should read
the `AP_EVENT`, `AP_TOOL`, `AP_STAGED_FILES`, and `AP_PHASE` variables
this script exports — same contract across every runtime adapter.

---

## See also

- [`../hooks-claude-code/README.md`](../hooks-claude-code/README.md) —
  canonical install guide; most of it applies unchanged.
- [`DEVIATIONS.md`](./DEVIATIONS.md) — Cursor-specific deviations.
- [`../../docs/runtime-hook-contract.md`](../../docs/runtime-hook-contract.md)
  — capability contract (normative).
