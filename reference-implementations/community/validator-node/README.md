# Reference Validator — TypeScript / Node (community-maintained)

> **Not normative. Community-maintained.** Functional sibling to the
> first-class [`validator-python/`](../../validator-python/) reference.
> Both implement the same algorithm in
> [`docs/automation-contract-algorithm.md`](../../../docs/automation-contract-algorithm.md)
> with byte-for-byte equivalent fixtures (see
> `tests/fixtures/`). Per `INVENTORY.md` §Validator parity note, adopters
> need only one language-native reference; this one was demoted from
> first-class to community-maintained in 1.20.0 to remove the implicit
> three-way official-sync obligation. Rule parity with `validator-python`
> is **not guaranteed** going forward — if you adopt this reference, run
> the test suite under `tests/` against your manifest as part of CI.
> Recommended for JS/TS/web-leaning pipelines or editor integrations
> that already ship with a Node runtime.

---

## What's here

```
validator-node/
├── package.json
├── tsconfig.json
├── src/
│   ├── cli.ts          # CLI entry point
│   ├── index.ts        # library entry (re-exports)
│   ├── layer1.ts       # rules 1.1 – 1.4
│   ├── layer2.ts       # rules 2.1 – 2.10 (including gap rules 2.4 and 2.5)
│   ├── layer3.ts       # rules 3.1 – 3.5 (including gap rules 3.2 and 3.4)
│   ├── surfaceMap.ts   # loader for docs/bridges/<stack>-surface-map.yaml
│   ├── waivers.ts      # human-authorized downgrade of specific findings
│   ├── findings.ts     # Finding / Report / exit-code mapping
│   └── loader.ts       # YAML + sibling-manifest discovery
└── tests/              # node --test suite covering every closed-gap rule
```

---

## Install

```sh
npm install
npm run build
```

Runtime deps: `yaml`, `ajv`, `glob`. No network. No system packages. Dev dep
is `typescript` + `@types/node`; both live in `devDependencies` so
`npm install --production` installs only the three runtime deps.

---

## Run

```sh
npm run build
node dist/src/cli.js <manifest> \
  --schema      ../../../schemas/change-manifest.schema.yaml \
  --surface-map ../../../docs/bridges/flutter-surface-map.yaml \
  --base-ref    origin/main
```

Or once installed globally:

```sh
agent-protocol-validate <manifest> --schema ... --surface-map ... --base-ref ...
```

All options are optional; Layer 1 + Layer 2 run with just `<manifest>`.
Layer 3 (drift) only runs when `--base-ref` is supplied. Rule 3.2 only
runs when `--surface-map` is supplied. Rule 3.4 only runs when a
monitoring cache file exists at `--monitoring-cache` (default
`<repo-root>/.agent-protocol/monitoring-cache.json`).

---

## Exit codes

Identical to the POSIX and Python references and to every other
implementation of the automation contract:

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
| 1 | 1.1 JSON Schema (2020-12)            | yes (when `--schema` supplied; ajv2020, `strict: false`) |
| 1 | 1.2 change_id format                 | yes |
| 1 | 1.3 ISO 8601 timestamps              | yes |
| 1 | 1.4 Waiver invariants                | yes |
| 2 | 2.1 Primary surface has evidence     | yes |
| 2 | 2.2 SoT source file exists           | yes |
| 2 | 2.3 Collected evidence has location  | yes |
| 2 | 2.4 Decomposition acyclicity         | **yes** (iterative-DFS cycle detection) |
| 2 | 2.5 depends_on / blocks mirror       | **yes** (sibling-manifest scan) |
| 2 | 2.6 L3/L4 requires deprecation       | yes (accepts either `deprecation_timeline` or `deprecation` per `$defs.deprecation`) |
| 2 | 2.7 Rollback mode 3 compensation     | yes |
| 2 | 2.8 phase=deliver human approval     | yes |
| 2 | 2.9 experience surface playtest      | yes |
| 2 | 2.10 phase=observe handoff           | yes |
| 3 | 3.1 declared SoT not in diff         | yes |
| 3 | 3.2 Surface ↔ file pattern drift     | **yes** (when `--surface-map` supplied) |
| 3 | 3.3 codegen touched without diff     | yes (when surface map declares `__generated__`) |
| 3 | 3.4 Monitoring channel staleness     | **yes** (local cache; network opt-in; matches Python default path) |
| 3 | 3.5 manifest older than code         | yes (when inside a git repo) |

Waiver filtering and exit-code mapping are complete.

---

## Running the test suite

```sh
npm test
```

`npm test` compiles TypeScript to `dist/` then runs Node's built-in
test runner against `dist/tests/**/*.test.js`. Thirteen tests covering
every rule the POSIX reference defers, plus a happy-path fixture, a
waiver downgrade case, and the globstar pattern parametrization.

---

## How rule 3.2 consumes the surface map

Identical semantics to the Python reference. `--surface-map` expects one
of the per-bridge artifacts published under `docs/bridges/`. The loader
reads `canonical_surfaces.<name>.patterns` plus any
`stack_extensions.<name>.patterns` as the glob list for that surface.
Globs are matched with `**` globstar semantics (one `**` component can
match multiple path segments).

---

## How rule 3.4 stays offline

Reads a local cache at `.agent-protocol/monitoring-cache.json` (or the
path given by `--monitoring-cache`). Entries older than
`--uncontrolled-max-age` days (default 7) emit an advisory finding.
Missing cache file → rule is skipped, not failed, so adopters can ignore
the rule entirely by leaving the file unwritten. A network-probing
plugin interface is on the roadmap, but the default is deliberately
offline — consistent with the contract's offline-operability
requirement.

---

## See also

- [`../../validator-python/`](../../validator-python/) — first-class
  Python reference; functional sibling of this implementation with
  byte-for-byte equivalent fixtures.
- [`../../validator-posix-shell/`](../../validator-posix-shell/) —
  first-class POSIX-shell reference; supported rule set is a strict
  subset of this one.
- [`DEVIATIONS.md`](./DEVIATIONS.md) — precise gap map.
- [`../../../docs/automation-contract.md`](../../../docs/automation-contract.md)
  — capability contract (normative).
- [`../../../docs/automation-contract-algorithm.md`](../../../docs/automation-contract-algorithm.md)
  — algorithm spec (normative).
