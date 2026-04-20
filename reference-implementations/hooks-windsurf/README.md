# Reference Runtime Hooks — Windsurf adapter

> **Not normative.** Thin adapter that reuses the five hook scripts from
> [`../hooks-claude-code/hooks/`](../hooks-claude-code/hooks/) and registers
> them against Windsurf's hook / rule surface.

---

## What's here

| File | Purpose |
|------|---------|
| `settings.example.json` | Copy into your Windsurf workspace rules file |
| `adapter/parse-event.sh` | Windsurf event → `AP_*` env vars |
| `DEVIATIONS.md` | Windsurf-specific quirks vs. the contract |

Hook scripts are not duplicated here. Each registered command shells
out to `../hooks-claude-code/hooks/<name>.sh`.

---

## How to install

1. Locate your Windsurf workspace rules file (commonly
   `.windsurf/rules.json` at the workspace root).
2. Merge `settings.example.json` into it, preserving any existing
   rules. The top-level keys here (`rules`, `hooks`, etc.) are the
   intent; adjust to match your Windsurf version's schema if it
   differs.
3. Confirm the relative path resolves from Windsurf's hook-invocation
   working directory, or replace with absolute paths.

---

## Event normalization

Hooks read from `git` and `$AGENT_PROTOCOL_MANIFEST_PATH`, not from
the Windsurf event payload, so payload translation is not on any
hook's critical path. `adapter/parse-event.sh` provides the cross-
runtime `AP_*` env vars for future payload-aware hooks.

---

## See also

- [`../hooks-claude-code/README.md`](../hooks-claude-code/README.md) —
  canonical install guide.
- [`DEVIATIONS.md`](./DEVIATIONS.md) — Windsurf-specific deviations.
- [`../../docs/runtime-hook-contract.md`](../../docs/runtime-hook-contract.md)
  — capability contract (normative).
