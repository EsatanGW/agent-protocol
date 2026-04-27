# Deviations from the canonical algorithm

Tracks where this Python reference differs from
`docs/automation-contract-algorithm.md`.

## Implemented

- Layer 1: all rules (1.1 – 1.4). JSON Schema validation runs when a
  schema file is supplied via `--schema`; other Layer-1 rules run
  unconditionally.
- Layer 2: all rules (2.1 – 2.12), including the two rules the POSIX
  reference defers (2.4 graph acyclicity via DFS, 2.5 `depends_on` ↔
  `blocks` bidirectional mirror via sibling-manifest scan), the 1.8
  rule (2.11 evidence tier floor under high-severity conditions), and
  the 1.26 rule (2.12 manifest size within ceiling — `wc -l` proxy for
  the ~25,000-token AI-runtime read ceiling, blocking >2000 / advisory
  1500-2000).
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

## Non-functional

- **Runtime limit:** comfortably under 60 s for manifests of 2000 lines
  in a 10 k-file repo (measured on a 2023-era laptop: ~400 ms end-to-end
  including `git diff`).
- **Reproducibility:** deterministic given a fixed manifest, schema, and
  base ref. Sibling-manifest discovery uses `sorted(glob())` for order
  stability.
- **Offline operability:** Layer 1 and Layer 2 need no network. Layer 3
  requires a local git repo. No rule makes a remote request.
- **Exit code stability:** strict 0 / 1 / 2 contract; nothing else.
- **Isolation:** read-only. The validator writes exactly one file, and
  only when `--report <path>` is supplied.

## Methodology version targeted

1.26.x. Rule 2.12 (manifest size within ceiling) added in 1.26.0; the
POSIX reference implements the same rule. Matches POSIX on every shared
rule by design and is exercised against the same fixtures where feasible.
