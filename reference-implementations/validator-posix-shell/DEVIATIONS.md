# Deviations from the canonical algorithm

Tracks where this POSIX-shell reference differs from `docs/automation-contract-algorithm.md`.

## Implemented

- Layer 1: all rules (1.1 – 1.4). JSON Schema validation is delegated to an external validator binary; all other Layer-1 rules are implemented directly.
- Layer 2: rules 2.1, 2.2, 2.3, 2.6, 2.7, 2.8, 2.9, 2.10.
- Layer 3: rules 3.1, 3.3, 3.5.
- Waiver filtering: full.
- Exit code mapping: full.

## Not implemented (gaps)

| Rule | Reason | Workaround |
|------|--------|------------|
| 2.4 Decomposition graph acyclicity | Cycle detection with pure shell requires a topo-sort step that is awkward in POSIX shell without arrays beyond basic use. | Pair with a language-native validator that includes this check, or pre-compute with `tsort`. |
| 2.5 `depends_on` ↔ `blocks` bidirectional mirror check | Needs to load sibling manifests and compare — extra I/O loop; deferred to language-native implementations. | Run a separate script that loads all manifests in `templates/` and checks the mirror. |
| 3.2 Surface ↔ file pattern drift | Requires parsing a stack-bridge mapping file, which each bridge must publish in a machine-readable form (e.g. `bridges/<stack>/surface-map.yaml`). Most bridges do not yet ship this artifact. | Add once bridges expose `surface-map.yaml`. |
| 3.4 Uncontrolled interface monitoring-channel staleness | Needs access to the monitoring channel's last-check timestamp, which varies by provider. | Out of scope for offline POSIX reference; expect language-native tooling. |

## Non-functional

- **Runtime limit:** meets (≤60s typical).
- **Reproducibility:** meets.
- **Offline operability:** meets (Layer 3 rule 3.4 is skipped if no cache is present).
- **Exit code stability:** meets.
- **Isolation:** meets (no remote I/O unless Layer 3 rule 3.4 is explicitly enabled).

## Methodology version targeted

2.1.x.
