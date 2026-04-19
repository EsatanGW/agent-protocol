# Reference Implementations

> **Not normative.** This directory holds **example** implementations that demonstrate `docs/automation-contract.md` + `docs/automation-contract-algorithm.md`. The methodology layer (`docs/*.md` outside `docs/bridges/`) never names a specific tool or language; this directory is where concrete implementations live.

Think of this as the runnable counterpart to the stack bridges: bridges map the methodology to a stack, reference implementations show what a validator for that contract actually looks like.

---

## What belongs here

- **One implementation per subdirectory.** Clear naming: `validator-<language-or-toolchain>/`.
- **Each implementation MUST include:**
  - `README.md` — how to run, dependencies, platforms supported
  - `DEVIATIONS.md` — any deviation from the contract's algorithm, with rationale
  - Source code + runnable entry point
  - Self-test suite that checks the implementation against a fixture set of manifests (valid / invalid per each rule)
- **Each implementation MAY include:**
  - Docker / OCI image build for CI use
  - Output formatters (plain text / SARIF / JSON)

## What does NOT belong here

- Manifest examples → `templates/`
- Algorithm specification → `docs/automation-contract-algorithm.md`
- Stack-specific mapping data → each stack bridge under `docs/bridges/`

---

## Current reference implementations

| Directory | Toolchain | Status | Notes |
|-----------|-----------|--------|-------|
| `validator-posix-shell/` | POSIX shell + `yq` + `git` | reference | Minimal Layer 1 + 2 + 3 implementation; useful for CI in any container with these tools. Does NOT include JSON Schema validation of deeply nested conditionals — those require either a real JSON Schema validator binary or a host-language implementation. |
| `hooks-claude-code/` | POSIX shell + `yq` + Claude Code hook wiring | reference | Four agent-runtime hooks covering all four categories (phase-gate / evidence / drift / completion-audit) from `docs/runtime-hook-contract.md`, plus a `settings.example.json` showing how to register them. Scripts parse the manifest with `yq` and emit the contract-compliant exit codes; bundle is plug-and-play for Claude Code, portable to other runtimes via their own event-registration mechanism. |

Teams publishing their own bridges are encouraged to contribute implementations in their preferred language and open PRs. The contract + algorithm are the canonical source; implementations just need to match them.

---

## Choosing an implementation for your team

- If your CI already has a shell environment and you just need gating: start with `validator-posix-shell/` and add a real JSON Schema validator binary (`ajv-cli`, `check-jsonschema`, `yajsv`, etc. — pick one your platform supports).
- If your team already uses a specific language for tooling: write your own (the algorithm doc is detailed enough to translate directly) and add it here as `validator-<your-language>/`.
- If you only need Layer 1: any off-the-shelf JSON Schema validator is enough; set `config.enforcement_level` for Layer 2 / 3 rules to `L0`.

---

## Versioning

Reference implementations track methodology version. When `docs/automation-contract-algorithm.md` changes rule ids or semantics, each implementation should:

1. Update its internal rule mapping.
2. Run its own self-test suite to confirm behavior still matches fixtures.
3. Note the methodology version it targets in its `README.md`.
