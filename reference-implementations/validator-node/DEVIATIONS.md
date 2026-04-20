# Deviations from the canonical algorithm

Tracks where this TypeScript / Node reference differs from
`docs/automation-contract-algorithm.md`.

## Implemented

- Layer 1: all rules (1.1 – 1.4). JSON Schema validation runs when a
  schema file is supplied via `--schema`; other Layer-1 rules run
  unconditionally.
- Layer 2: all rules (2.1 – 2.10), including the two rules the POSIX
  reference defers (2.4 graph acyclicity via iterative DFS, 2.5
  `depends_on` ↔ `blocks` bidirectional mirror via sibling-manifest
  scan).
- Layer 3: rules 3.1, 3.2, 3.3, 3.5. Rule 3.4 ships a default local-
  cache implementation (reads `.agent-protocol/monitoring-cache.json`;
  never writes, never touches the network).
- Waiver filtering: full (`approver_role == "human"`, unexpired only).
- Exit code mapping: full (0 / 1 / 2; harness errors 64).

## Not implemented (by design)

| Rule / feature | Reason |
|----------------|--------|
| Rule 3.4 network probe | Default implementation reads a local cache. A network-probing plugin interface is out of scope for the reference validator; adopters should register their own probe that writes the cache on a schedule. |
| SARIF output | JSON output is provided; SARIF mapping is left to downstream integrations since SARIF's schema is stable and mechanical to produce from the finding list. |
| `format: date` / `format: date-time` assertions under ajv | The canonical schema carries `format` annotations on timestamp fields. ajv's default configuration treats these as ignored-with-warning; this validator runs ajv with `strict: false, logger: false` to avoid both false-positives and stderr noise. Rule 1.3 (`timestamp.iso8601`) covers the actual format-assertion responsibility via a regex that is identical to the Python reference, so nothing is missed — the coverage simply moves from ajv to the rule layer. |

## Non-functional

- **Runtime limit:** comfortably under 60 s for manifests of 2000 lines
  in a 10 k-file repo. Measured on a 2023-era laptop: ~200 ms end-to-end
  including build + `git diff`.
- **Reproducibility:** deterministic given a fixed manifest, schema, and
  base ref. Sibling-manifest discovery uses `glob().sort()` for order
  stability (matches the Python reference's `sorted(glob())`).
- **Offline operability:** Layer 1 and Layer 2 need no network. Layer 3
  requires a local git repo. No rule makes a remote request. The three
  runtime deps (`yaml`, `ajv`, `glob`) all work offline.
- **Exit code stability:** strict 0 / 1 / 2 contract; nothing else.
- **Isolation:** read-only. The validator writes exactly one file, and
  only when `--report <path>` is supplied.

## Behaviour parity with validator-python

The Node and Python references target the same rule IDs, the same exit
codes, the same glob semantics, and the same cache file shape. Fixture
files under `tests/fixtures/` are byte-for-byte copies of the Python
reference's fixtures so the two test suites exercise identical
manifests. Any divergence should be treated as a bug in whichever
reference is wrong — the canonical algorithm in
`docs/automation-contract-algorithm.md` is the tiebreaker.

## Methodology version targeted

2.1.x. Matches both the POSIX and Python references; all three agree on
every shared rule by design.
