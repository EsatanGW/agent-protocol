# Hook bundle self-test

A hermetic, framework-free fixture runner for the four hooks in
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
  hook. Without `yq`, the hooks emit their own `TOOL_ERROR` path (exit 2);
  the harness prints a warning so this case is visible.

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

Eleven cases total. Anything below that floor is a regression in the
bundle's observable contract.
