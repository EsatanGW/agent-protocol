# Hook bundle self-test

A hermetic, framework-free fixture runner for the five hooks in
`../hooks/`. The harness shims `git` and injects `AGENT_PROTOCOL_*`
environment variables so every run is deterministic and repo-state
independent.

## Run

```sh
./selftest.sh
```

Exit code `0` means every fixture passed. Any failure prints the
expected-vs-actual diff and a non-zero aggregate exit code.

## Requirements

- POSIX `sh` (tested on `bash`, `dash`, `ash`).
- `yq` on `PATH` — optional for fixtures that only exercise
  `manifest-required.sh`, required for fixtures that exercise any other
  hook. Without `yq`, the harness emits `# SKIP yq not on PATH` for every
  case under the four yq-dependent hook directories (`completion-audit`,
  `consumer-registry-check`, `evidence-artifact-exists`, `sot-drift-check`)
  so local runs without `yq` stay quiet and the TAP summary reports
  `N cases, 0 failed, K skipped`. CI (`.github/workflows/validate.yml`
  → `hooks-selftest`) installs `yq` explicitly, so every case executes on
  every push / PR.

## Directory layout

```
selftests/
├── selftest.sh             # orchestrator, TAP-ish output
├── run-case.sh             # runs one fixture against one hook
├── stubs/git               # test double for the hook's git invocations
└── fixtures/
    └── <hook-name>/
        └── <case-name>/
            ├── expected    # required: exit=<code>, stderr~=, stdout~=
            ├── event.json  # optional: piped to the hook on stdin
            ├── staged      # optional: returned by git diff --cached --name-only
            ├── unstaged    # optional: returned by git diff --name-only
            ├── ls-files    # optional: returned by git ls-files 'change-manifest*.yaml'
            ├── manifest.yaml # optional: exported as AGENT_PROTOCOL_MANIFEST_PATH
            └── env         # optional: sourced before invoking the hook
```

The harness always `cd`s into the case directory before invoking the
hook, so relative paths in `manifest.yaml` (such as `artifact_location`
or the `lean-mode.flag` file) resolve against the fixture, never against
the caller's working tree.

## `expected` file grammar

```
exit=<code>            # required, exactly one line
stderr~=<pattern>      # optional, zero or more lines, ERE
stdout~=<pattern>      # optional, zero or more lines, ERE
# comment lines start with a '#' and are ignored
```

Patterns are evaluated with `grep -E`. A case fails if any declared line
does not match.

## Adding a new case

1. Create `fixtures/<hook-name>/<case-name>/`.
2. Drop in the fixture files you need (manifest, staged list, env).
3. Author `expected` with the contract you are asserting.
4. Run `./selftest.sh` and confirm the new case is emitted.

## Minimum coverage

| Hook | Cases |
|---|---|
| `manifest-required.sh` | 5 |
| `evidence-artifact-exists.sh` | 2 |
| `sot-drift-check.sh` | 2 |
| `completion-audit.sh` | 2 |
| `consumer-registry-check.sh` | 3 |

Fourteen cases total. Anything below that floor is a regression in the
bundle's observable contract.
