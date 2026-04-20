# Reference Validator — Python

> **Not normative.** Language-native sibling to `validator-posix-shell/`.
> Both implement the algorithm in
> [`docs/automation-contract-algorithm.md`](../../docs/automation-contract-algorithm.md).
> This implementation closes the four rules the POSIX reference defers
> (2.4, 2.5, 3.2, 3.4) and is the recommended choice for CI pipelines
> that already have a Python interpreter available.

---

## What's here

```
validator-python/
├── pyproject.toml
├── src/agent_protocol_validate/
│   ├── __main__.py     # CLI entry point
│   ├── layer1.py       # rules 1.1 – 1.4
│   ├── layer2.py       # rules 2.1 – 2.10 (including the gap rules 2.4 and 2.5)
│   ├── layer3.py       # rules 3.1 – 3.5 (including the gap rules 3.2 and 3.4)
│   ├── surface_map.py  # loader for docs/bridges/<stack>-surface-map.yaml
│   ├── waivers.py      # human-authorized downgrade of specific findings
│   ├── findings.py     # Finding / Report / exit-code mapping
│   └── loader.py       # YAML + sibling-manifest discovery
└── tests/              # pytest suite covering every closed-gap rule
```

---

## Install

```sh
pip install -e .
```

Runtime deps: `PyYAML`, `jsonschema`. No network. No system packages.

---

## Run

```sh
python -m agent_protocol_validate <manifest> \
  --schema      schemas/change-manifest.schema.yaml \
  --surface-map docs/bridges/flutter-surface-map.yaml \
  --base-ref    origin/main
```

All options are optional; Layer 1 + Layer 2 run with just `<manifest>`.
Layer 3 (drift) only runs when `--base-ref` is supplied. Rule 3.2 only
runs when `--surface-map` is supplied. Rule 3.4 only runs when a
monitoring cache file exists at `--monitoring-cache` (default
`<repo-root>/.agent-protocol/monitoring-cache.json`).

---

## Exit codes

Identical to the POSIX reference and to every other implementation of
the automation contract:

| Code | Meaning |
|------|---------|
| `0`  | No unwaived findings. |
| `1`  | At least one advisory finding; no blocking findings. |
| `2`  | At least one blocking finding that was not waived. |
| `64` | Harness / argument error (stderr explains). |

---

## Rule coverage

| Layer | Rule | Covered? |
|-------|------|----------|
| 1 | 1.1 JSON Schema (2020-12)            | yes (when `--schema` supplied) |
| 1 | 1.2 change_id format                 | yes |
| 1 | 1.3 ISO 8601 timestamps              | yes |
| 1 | 1.4 Waiver invariants                | yes |
| 2 | 2.1 Primary surface has evidence     | yes |
| 2 | 2.2 SoT source file exists           | yes |
| 2 | 2.3 Collected evidence has location  | yes |
| 2 | 2.4 Decomposition acyclicity         | **yes** (DFS cycle detection) |
| 2 | 2.5 depends_on / blocks mirror       | **yes** (sibling manifest scan) |
| 2 | 2.6 L3/L4 requires deprecation       | yes |
| 2 | 2.7 Rollback mode 3 compensation     | yes |
| 2 | 2.8 phase=deliver human approval     | yes |
| 2 | 2.9 experience surface playtest      | yes |
| 2 | 2.10 phase=observe handoff           | yes |
| 3 | 3.1 declared SoT not in diff         | yes |
| 3 | 3.2 Surface ↔ file pattern drift     | **yes** (when `--surface-map` supplied) |
| 3 | 3.3 codegen touched without diff     | yes (when surface map declares `__generated__`) |
| 3 | 3.4 Monitoring channel staleness     | **yes** (local cache; network opt-in) |
| 3 | 3.5 manifest older than code         | yes (when inside a git repo) |

Waiver filtering and exit-code mapping are complete.

---

## How rule 3.2 consumes the surface map

`--surface-map` expects one of the per-bridge artifacts published under
`docs/bridges/`. The loader reads `canonical_surfaces.<name>.patterns`
plus any `stack_extensions.<name>.patterns` as the glob list for that
surface. Globs are matched with `**` globstar semantics (one `**`
component can match multiple path segments).

For every primary surface in `surfaces_touched`, rule 3.2 asserts that
at least one file in `git diff --name-only <base>...HEAD` matches that
surface's glob list. Missing matches emit an **advisory** finding — a
warning, not a block — so hand-rolled commits that touch exotic paths
can still pass with `-1` exit code and a visible signal.

---

## How rule 3.4 stays offline

The monitoring-channel staleness check reads a local cache at
`.agent-protocol/monitoring-cache.json`. Shape:

```json
{
  "pager-duty-incident-feed": { "last_check": "2026-04-15" },
  "cloudwatch-alarm-stream":  { "last_check": "2026-04-19T03:00:00Z" }
}
```

Your monitoring-refresh job (scheduled separately, outside the
validator) updates this file. The validator only reads it — never
writes. Entries older than `--uncontrolled-max-age` days (default `7`)
emit an advisory finding. Missing cache file → no findings (rule is
skipped, not failed), so adopters can ignore the rule entirely by
leaving the file unwritten.

A network-probing plugin interface is on the roadmap, but the default
implementation is deliberately offline — consistent with the contract's
offline-operability requirement.

---

## See also

- [`../validator-posix-shell/`](../validator-posix-shell/) — minimal
  reference; supported rule set is a strict subset of this one.
- [`DEVIATIONS.md`](./DEVIATIONS.md) — precise gap map.
- [`../../docs/automation-contract.md`](../../docs/automation-contract.md)
  — capability contract (normative).
- [`../../docs/automation-contract-algorithm.md`](../../docs/automation-contract-algorithm.md)
  — algorithm spec (normative).
