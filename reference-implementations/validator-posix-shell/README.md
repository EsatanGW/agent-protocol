# validator-posix-shell — reference implementation

Minimal POSIX shell implementation of the automation contract. Intended as a **reference**, not a production tool.

## Why this exists

The methodology layer never names a specific tool. But teams adopting the plugin need *something* runnable to start with. This shell script demonstrates that the contract is achievable with widely-available Unix tools, and proves each rule is testable.

## Dependencies

- POSIX-compatible shell (`/bin/sh` or `bash`)
- `yq` (v4+) — YAML/JSON query tool
- `git` — for Layer 3 drift detection (optional)
- A JSON Schema validator for Layer 1 structural validation. The script calls `${SCHEMA_VALIDATOR:-check-jsonschema}` — substitute your own (`ajv`, `yajsv`, `jv`, etc.).

## Usage

```sh
./validate.sh <manifest.yaml> <repo_root> <schema_path> [git_base_ref]
```

Exit codes per `docs/automation-contract-algorithm.md`:
- `0` — no findings, or only waived / L0-disabled
- `1` — advisory warnings only
- `2` — at least one blocking finding

## Rules coverage

Implementation targets methodology version 2.1.x. See `DEVIATIONS.md` for gaps.

## What this is NOT

- Not a substitute for a proper language-native validator for production use
- Not performance-optimized; straightforward linear implementation
- Not a replacement for team-specific stack-bridge validators

Teams should write their own in the language of their tooling stack once they adopt the methodology.
