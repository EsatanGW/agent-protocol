# Reference Runtime Hooks — Codex adapter

> **Not normative.** Thin adapter that reuses the six hook scripts from
> [`../hooks-claude-code/hooks/`](../hooks-claude-code/hooks/) and registers
> them against Codex's tool / command surface.

---

## What's here

| File | Purpose |
|------|---------|
| `settings.example.json` | Merge into your Codex hook config |
| `hooks.example.json` | Opt-in Codex plugin-style hook example; not loaded by default |
| `adapter/parse-event.sh` | Codex event → `AP_*` env vars |
| `DEVIATIONS.md` | Codex-specific quirks vs. the contract |

Hook scripts are not duplicated here. Each registered command shells
out to `../hooks-claude-code/hooks/<name>.sh`.

---

## How to install

These hooks are opt-in. The repository's `.codex-plugin/plugin.json`
intentionally does **not** point at a root `hooks.json`, because the
reference hooks may block `git commit` or warn on `git push` until a
project has adopted Change Manifest and evidence artifacts.

1. Locate the settings file your Codex install reads on startup.
2. Merge `settings.example.json` into it. Adjust key names to the
   Codex version's schema — keep the commands and their ordering.
3. Confirm the relative path resolves from the working directory Codex
   uses when spawning hook commands; prefer absolute paths for
   installs outside the repo root.

If your Codex install supports plugin-local hook files, copy
`hooks.example.json` to the hook path your install expects only after
you intentionally choose to enable the checks.

---

## Event normalization

Hooks read from `git` and `$AGENT_PROTOCOL_MANIFEST_PATH`, not from a
Codex event payload, so no translation is required for the four
reference hooks. `adapter/parse-event.sh` exposes cross-runtime
`AP_*` env vars for future payload-aware hooks.

---

## See also

- [`../hooks-claude-code/README.md`](../hooks-claude-code/README.md) —
  canonical install guide.
- [`DEVIATIONS.md`](./DEVIATIONS.md) — Codex-specific deviations.
- [`../../docs/runtime-hook-contract.md`](../../docs/runtime-hook-contract.md)
  — capability contract (normative).
