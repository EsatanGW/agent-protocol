# Reference Implementations — Inventory

> **Purpose.** Classify each entry under `reference-implementations/` as either **runtime-glue** (concrete code or runtime-specific configuration that must live outside `docs/`) or **documentation** (prose that mirrors normative content and could potentially relocate to `docs/` in a future Change Manifest). This is **inventory only** — no relocation is performed by this file.

The classification supports the `tier` / `audience` doc-frontmatter taxonomy used by the canonical methodology layer (`docs/`) and gives reviewers a quick lens for the question: *should new content live here, or under `docs/`?*

---

## Classification rubric

| Category | Definition | Examples |
|----------|------------|----------|
| **runtime-glue** | Executable code, shell scripts, hook adapters, or runtime-specific config files. Cannot move into `docs/` without losing executability. | hook scripts, validator source, selftest fixtures, runtime adapter glue |
| **documentation** | Prose that explains a methodology concept and could in principle live under `docs/`. Currently kept here either because it ships paste-ready for runtimes that cannot consume `docs/` directly, or because it is co-located with its concrete implementation for proximity. | role prompts, role-composition pattern catalogues, registry-style indices |

A file flagged `documentation` is **not** automatically a relocation candidate. Relocation is a separate decision governed by a future Change Manifest that weighs:

1. Does the file need to ship paste-ready to a runtime that does not consume `docs/`?
2. Does keeping it next to its referenced code reduce cross-change knowledge cost (per `docs/cross-change-knowledge.md`)?
3. Would moving it create more cross-cutting drift than it removes?

---

## Inventory

| Path | Files | Category | Notes |
|------|-------|----------|-------|
| `hooks-claude-code/` | 59 | **runtime-glue** | Phase-gate / evidence / drift / completion-audit hook scripts + `settings.example.json` for Claude Code wiring. Selftests verify exit-code contract from `docs/runtime-hook-contract.md`. |
| `hooks-codex/` | 7 | **runtime-glue** | Codex profile adapter + selftests. |
| `hooks-cursor/` | 6 | **runtime-glue** | Cursor Custom Mode adapter + selftests. |
| `hooks-gemini-cli/` | 6 | **runtime-glue** | Gemini CLI session adapter + selftests. |
| `hooks-windsurf/` | 6 | **runtime-glue** | Windsurf mode adapter + selftests. |
| `validator-posix-shell/` | 3 | **runtime-glue** (first-class) | POSIX shell + `yq` + `git` reference validator (Layer 1+2+3, minus deeply nested JSON Schema). |
| `validator-python/` | 23 | **runtime-glue** (first-class) | Python reference validator with full unit tests. |
| `community/validator-node/` | 25 | **runtime-glue** (community-maintained, demoted in 1.20.0) | Functional sibling to `validator-python/` with byte-for-byte equivalent fixtures. Rule parity with the canonical algorithm is verified by adopters via the bundled `tests/`, not by this repository's CI. |
| `re-entry-trigger/` | 4 | **runtime-glue** | Re-entry trigger reference + tests (cited from `docs/re-entry-trigger.md`). |
| `roles/README.md` | 1 | **documentation** | Index for paste-ready role prompts; mirrors `docs/multi-agent-handoff.md` §tool-permission-matrix in prose. Kept here because the prompts ship paste-ready to runtimes that cannot consume `docs/`. |
| `roles/planner.md` | 1 | **documentation** | Paste-ready Planner prompt. SoT remains `docs/multi-agent-handoff.md`; this file is a runtime-consumable mirror. |
| `roles/implementer.md` | 1 | **documentation** | Paste-ready Implementer prompt. Same caveat as Planner. |
| `roles/reviewer.md` | 1 | **documentation** | Paste-ready Reviewer prompt. Same caveat as Planner. |
| `roles/role-composition-patterns.md` | 1 | **documentation** | Catalogue of role-composition patterns; no code. Candidate for future relocation if it grows or stops being runtime-paste material. |
| `roles/specialist-roles-registry.md` | 1 | **documentation** | Registry of specialist sub-agent roles; no code. Same candidacy as composition-patterns. |

Total: 146 files. **runtime-glue:** 139 files (first-class: 114 across 8 directories; community-maintained: 25 in `community/validator-node/`). **documentation:** 7 files inside `roles/`.

---

## Implications for new contributions

- **New hook adapter, validator, or runtime-specific selftest** → here (this directory), under the appropriate subtree.
- **New methodology principle or normative rule** → `docs/` (canonical layer); cite from here if a runtime needs the rule mirrored as paste-ready prose.
- **New role prompt** → here under `roles/`, but its **SoT is `docs/multi-agent-handoff.md`** (or its successor). Drift detection between SoT and the mirror is owned by a CI gate (see `docs/multi-agent-handoff.md` cross-references and the planned role-consistency check in `.github/workflows/validate.yml`).

---

## Validator classes (1.20.0)

This repository ships two **first-class** reference validators plus one **community-maintained** alternative. All three implement the canonical algorithm in `docs/automation-contract-algorithm.md`; first-class references are kept in sync with the spec by this repo, community-maintained references are not.

### First-class

`validator-posix-shell/` and `validator-python/` are **first-class** — kept in sync with the canonical algorithm by this repo. Pick whichever your CI already accommodates:

| First-class reference | Pick when | Trade-off |
|-----------------------|-----------|-----------|
| `validator-posix-shell/` | CI must run with zero runtime dependencies beyond POSIX shell + `yq` + `git`. | Documented coverage gap on rules 2.4 / 2.5 / 3.2 / 3.4 (see its `DEVIATIONS.md`). |
| `validator-python/` | CI already has Python 3.10+; your team is Python/ML/data-pipeline-leaning; full rule coverage is required. | Slightly slower (`~400 ms` end-to-end on a 2023-era laptop) than the Node alternative. |

### Community-maintained

`community/validator-node/` was demoted from first-class to community-maintained in 1.20.0. It is a **functional sibling** to `validator-python/` (same rule-ID coverage in principle, same exit-code contract, same default cache-file shape, fixtures byte-for-byte equal at demotion time) but is **not** kept in sync with future spec changes by this repository's CI. Adopters who pick this one should run the bundled `tests/` against their manifests and treat any divergence from `validator-python/` behavior as a bug in this implementation.

| Community reference | Pick when | Caveat |
|---------------------|-----------|--------|
| `community/validator-node/` | CI already has Node 20+; your team is JS/TS/web-leaning or wants editor integrations; you accept the responsibility to verify rule parity with `docs/automation-contract-algorithm.md`. | Rule parity not guaranteed going forward; not covered by `role-consistency` or any official sync gate. |

### Why the demotion

Maintaining three validators of the canonical algorithm in lock-step is a real cost: every rule-semantics change required syncing three codebases. The 1.19.1 release acknowledged that `validator-python` and `validator-node` were functionally equivalent; 1.20.0 acts on that observation by formally selecting Python as the first-class language-native reference. The Node implementation is preserved verbatim under `community/` for users who already depend on it.

This file is intentionally non-normative; do not cite it from `docs/`. Its only consumer is reviewers asking "should this new file live here?" and audit tooling that wants a structured view of the directory.
