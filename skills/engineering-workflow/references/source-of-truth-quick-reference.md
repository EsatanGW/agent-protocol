# Source of Truth Quick Reference

Before implementation, identify which pattern(s) you are dealing with:
- Schema-defined truth — DB schema / API spec is the canonical source
- Config-defined truth — feature flag / config service decides the answer
- Enum / status-defined truth — a fixed set of values is the canonical source
- Contract-defined truth — agreement between two systems (OpenAPI, event schema)
- UI-defined truth — design spec is the canonical source (rare but real)
- **Transition-defined truth** — the legal state-transition graph is the source, not the current value
- **Temporal-local truth** — client / edge holds authoritative state until sync (offline-first apps, CRDTs)

It is normal for one feature to combine 2–3 patterns simultaneously.

Watch for anti-patterns:
- Dual write without coordination
- Consumer deriving its own truth
- Stale cache treated as truth
- Docs drifting from implementation
- Translation keys drifting from canonical copy
- Treating a temporal-local store as if it were a regular cache
- Mutating state directly into a legal-looking value via an illegal transition

If you cannot clearly name the source of truth, you are not ready to patch safely.
