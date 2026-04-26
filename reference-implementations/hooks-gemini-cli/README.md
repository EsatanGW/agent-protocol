# Reference Runtime Hooks — Gemini CLI adapter

> **Not normative.** Thin adapter that reuses the six hook scripts from
> [`../hooks-claude-code/hooks/`](../hooks-claude-code/hooks/) and registers
> them against Gemini CLI's hook / command surface.

---

## What's here

| File | Purpose |
|------|---------|
| `settings.example.toml` | Merge into the Gemini CLI settings file (TOML) |
| `adapter/parse-event.sh` | Gemini CLI event → `AP_*` env vars |
| `DEVIATIONS.md` | Gemini CLI-specific quirks vs. the contract |

The hook scripts are **not** duplicated here. Each registered command
shells out to `../hooks-claude-code/hooks/<name>.sh`.

---

## How to install

1. Locate your Gemini CLI settings file. The location depends on your
   install (`~/.config/gemini-cli/settings.toml` is typical; if yours
   differs, adjust accordingly).
2. Merge `settings.example.toml` into that file. Existing `[hooks.*]`
   sections take precedence over new ones with the same name; rename if
   you need both.
3. Confirm the relative path resolves from the working directory the
   Gemini CLI uses when it spawns hook commands. Absolute paths work
   and avoid layout coupling.

---

## Event normalization

The hooks already read `git` and `$AGENT_PROTOCOL_MANIFEST_PATH`, not
the Gemini event payload, so no payload translation is required for
the four reference hooks. `adapter/parse-event.sh` exposes the
cross-runtime `AP_*` env vars for any future hook that needs them.

---

## See also

- [`../hooks-claude-code/README.md`](../hooks-claude-code/README.md) —
  canonical install guide.
- [`DEVIATIONS.md`](./DEVIATIONS.md) — Gemini CLI-specific deviations.
- [`../../docs/runtime-hook-contract.md`](../../docs/runtime-hook-contract.md)
  — capability contract (normative).
