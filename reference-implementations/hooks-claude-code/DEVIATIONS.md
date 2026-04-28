# Deviations from the Runtime Hook Contract

Known gaps between this reference bundle and `docs/runtime-hook-contract.md`. Documenting them openly rather than claiming full conformance.

---

## 1. Selftest suite — resolved

Originally flagged as a gap. As of v1.3.0 the bundle ships a hermetic
fixture-based harness at `selftests/selftest.sh` with eleven cases
covering every category (A / B / C / D). See `selftests/README.md` for
the `expected` grammar and how to add new cases. Teams enabling these
hooks in `block` mode should run `./selftests/selftest.sh` in CI on any
PR that edits `hooks/` or `selftests/`.

---

## 2. Event-payload schema is inferred, not declared

The contract defines a JSON input schema on stdin. Claude Code's actual event payloads are runtime-defined and have evolved across versions. This bundle does a best-effort parse:

- Tries stdin first, then argv.
- Falls back to env var `CLAUDE_TOOL_NAME` etc. if the payload is missing fields.
- Uses `yq -p json` to read the payload, which is permissive about missing fields.

**Mitigation:** every script tolerates absent optional fields per the contract ("fields a hook does not need may be absent — the hook must not crash on missing optional fields").

**Impact:** low for the four hooks shipped. Higher for hooks that need precise trigger provenance (e.g. distinguishing a `post-tool-use:Edit` from `post-tool-use:MultiEdit`).

### 2.1 Historical note (resolved in 1.2.1)

v1.2.0's `settings.example.json` used invented event names (`preCommit` / `postToolUse` / `stop`) that do not exist in Claude Code's hook runtime. The correct native events are `PreToolUse` / `PostToolUse` / `Stop` (PascalCase), grouped by matcher per Claude Code's hooks schema. 1.2.1 rewrote the example file and the `docs/runtime-hook-contract.md` example to use the real format. Teams that hand-copied the 1.2.0 example need to re-copy from 1.2.1 — the old keys were silently ignored by Claude Code, so the hooks never actually fired.

---

## 3. Structured stdout is opt-in, not default

The contract declares structured stdout as **optional**. These hooks gate it behind `AGENT_PROTOCOL_STRUCTURED_OUTPUT=1` so that default use (plain stderr message) stays ergonomic for terminal users. Automation platforms that want to aggregate findings set the env var.

**Impact:** none — this is an allowed deviation (the contract marks stdout as optional).

---

## 4. Network-check degradation — implemented

As of v1.3.0 the bundle ships `hooks/consumer-registry-check.sh`, the
reference implementation of the contract's network-degradation clause.
The hook walks every `.consumers[].external_registry_url` in the
manifest, probes each with `curl -fsS --max-time ${AGENT_PROTOCOL_NET_TIMEOUT:-5}`,
and emits `exit 2` (warn) — never `exit 1` — on timeout, DNS failure,
non-HTTP URL, or non-2xx response. Missing `curl` or `yq` degrades to
`exit 2` via the same `TOOL_ERROR` path used elsewhere in this bundle.

Selftest fixtures under `selftests/fixtures/consumer-registry-check/`
exercise the no-consumers, reachable, and unreachable branches by way
of a `curl` stub that honors a per-fixture `curl-exit` file. A real
end-to-end smoke (against a reachable vs. deliberately-invalid host)
remains outside the selftest because CI sandboxes typically block
arbitrary egress.

---

## 7. yq variant — mikefarah-only (1.31.1 hardening)

Two distinct binaries ship under the `yq` name. The hooks here use mikefarah-only syntax:

- `cckn-canonical-sync-check.sh` uses `yq --front-matter=extract '<expr>' <md-file>` for CCKN frontmatter parsing. The Python `kislyuk/yq` (a jq-wrapper) does not implement `--front-matter=extract` and exits with `Unknown option`.
- `consumer-registry-check.sh` uses `yq -r '.. | select(has("external_registry_url")) | .external_registry_url' <yaml>`. Recursive descent (`..`) visits primitives, and `kislyuk/yq` errors with `Cannot check whether string has a string key` on those primitives.

A repo running with the wrong `yq` variant on `PATH` will see the cckn drift signal silently fail-open (frontmatter parse returns empty → "no mirrors declared" branch → exit 0) and the consumer-registry probe silently fail-closed (recursive descent error → empty URL list → no probe runs → exit 0). The user-visible hook output is "everything passed" — exactly the outcome the back-pressure pattern is designed to surface honestly.

**Mitigation in 1.31.1.** `selftests/selftest.sh` now distinguishes the two variants by reading `yq --version` and matching `mikefarah` / `github.com/mikefarah` in the output. When the wrong variant is on `PATH`, the harness skips the affected fixture cases with `# SKIP yq is not mikefarah/yq (Go); see ... §Dependencies` and points the contributor at the README's `§Dependencies` block, which now carries an explicit installation pointer to the Go binary. CI installs the Go binary explicitly, so the production gate always exercises the full suite.

**Why detect at the harness rather than at the hook.** The hook itself uses the contract's `TOOL_ERROR` path when `yq` is missing entirely (`command -v yq` fails). Distinguishing variants inside the hook would add 5–10 ms of variant-detection overhead to every hook invocation, in service of an environment-pollution problem that affects local development only. The harness-side check costs nothing in production and produces an instructive remediation message (per the §Remediation-injection contract added in 1.31.0) the moment a contributor tries to run the suite locally with the wrong yq.

**Open follow-ups.** A future patch may add a startup `yq --version` probe to the install-time docs (`README.md §How to install`) so the wrong-variant case is caught before the first hook fires, not at first selftest run.

---

## 6. CCKN canonical-mirror sync check — implemented (1.27.0)

`hooks/cckn-canonical-sync-check.sh` is the reference implementation of the CCKN ↔ canonical-SoT drift signal defined in `docs/cross-change-knowledge.md §Mirroring canonical methodology SoT`. The hook walks the project's CCKN directory (default `docs/knowledge/`; override via `CCKN_DIR`), parses each CCKN's `mirrors_canonical` frontmatter, and warns (`exit 2` — never blocks) when:

- The SoT file at `mirrors_canonical[i].path` has commits in its git history strictly after the CCKN's `updated` date, or
- The CCKN declares `mirrors_canonical[i].methodology_version` and the value does not match the `AGENT_PROTOCOL_VERSION` env var (the consumer project's pinned methodology version).

Wired in `settings.example.json` under the `Bash(git push*)` matcher so drift warnings surface at pre-push time, alongside `consumer-registry-check.sh`. Selftest fixtures cover four cases: absent CCKN dir, CCKN without `mirrors_canonical`, stale-mirror by mtime, version-mismatch. The git stub at `selftests/stubs/git` was extended to handle the `log -1 --format=%cI -- <path>` invocation; fixtures supply the SoT mtime via a `sot-mtime-<basename>.txt` file.

Limitations: the hook compares `git log -1 --format=%cI` mtimes at file level, not section level. A SoT file change that doesn't touch the `mirrors_canonical[i].section` will still trip the warning. Deferred: section-level diff requires parsing markdown headings out of `git diff`, which is out of scope for a runtime hook (better suited to a dedicated CI lint).

---

## 5. Cross-runtime coverage — partial

As of v1.4.0 the repo ships thin adapter bundles for four additional
runtimes:

- [`../hooks-cursor/`](../hooks-cursor/) — Cursor (JSON config)
- [`../hooks-gemini-cli/`](../hooks-gemini-cli/) — Gemini CLI (TOML config)
- [`../hooks-windsurf/`](../hooks-windsurf/) — Windsurf (JSON config)
- [`../hooks-codex/`](../hooks-codex/) — Codex (JSON config)

Each adapter ships a README, its own DEVIATIONS, a runtime-native
settings example, and an `adapter/parse-event.sh` that normalizes the
runtime's event payload into cross-runtime `AP_*` env vars. The hook
scripts themselves remain in this (the Claude Code) bundle — the
adapters point back via relative or absolute paths, so a regression
fix to `manifest-required.sh` propagates everywhere with a single
edit. **Still outstanding:** runtime-wiring smoke tests per adapter
(the `selftests/` harness exercises hook logic, not hook registration).
