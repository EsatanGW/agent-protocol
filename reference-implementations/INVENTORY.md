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
| `validator-posix-shell/` | 3 | **runtime-glue** | POSIX shell + `yq` + `git` reference validator (Layer 1+2+3, minus deeply nested JSON Schema). |
| `validator-node/` | 25 | **runtime-glue** | Node.js reference validator with full unit tests. |
| `validator-python/` | 23 | **runtime-glue** | Python reference validator with full unit tests. |
| `re-entry-trigger/` | 4 | **runtime-glue** | Re-entry trigger reference + tests (cited from `docs/re-entry-trigger.md`). |
| `roles/README.md` | 1 | **documentation** | Index for paste-ready role prompts; mirrors `docs/multi-agent-handoff.md` §tool-permission-matrix in prose. Kept here because the prompts ship paste-ready to runtimes that cannot consume `docs/`. |
| `roles/planner.md` | 1 | **documentation** | Paste-ready Planner prompt. SoT remains `docs/multi-agent-handoff.md`; this file is a runtime-consumable mirror. |
| `roles/implementer.md` | 1 | **documentation** | Paste-ready Implementer prompt. Same caveat as Planner. |
| `roles/reviewer.md` | 1 | **documentation** | Paste-ready Reviewer prompt. Same caveat as Planner. |
| `roles/role-composition-patterns.md` | 1 | **documentation** | Catalogue of role-composition patterns; no code. Candidate for future relocation if it grows or stops being runtime-paste material. |
| `roles/specialist-roles-registry.md` | 1 | **documentation** | Registry of specialist sub-agent roles; no code. Same candidacy as composition-patterns. |

Total: 146 files. **runtime-glue:** 139 files across 9 directories. **documentation:** 7 files inside `roles/`.

---

## Implications for new contributions

- **New hook adapter, validator, or runtime-specific selftest** → here (this directory), under the appropriate subtree.
- **New methodology principle or normative rule** → `docs/` (canonical layer); cite from here if a runtime needs the rule mirrored as paste-ready prose.
- **New role prompt** → here under `roles/`, but its **SoT is `docs/multi-agent-handoff.md`** (or its successor). Drift detection between SoT and the mirror is owned by a CI gate (see `docs/multi-agent-handoff.md` cross-references and the planned role-consistency check in `.github/workflows/validate.yml`).

---

## Validator parity note (1.19.1)

`validator-python/` and `validator-node/` are **functionally equivalent parallel implementations** of the canonical algorithm in `docs/automation-contract-algorithm.md`:

- Same rule-ID coverage (Layer 1 + 2 + 3 in full).
- Same exit-code contract (`0` / `1` / `2`; harness `64`).
- Same default cache-file shape (`.agent-protocol/monitoring-cache.json`) for rule 3.4.
- `validator-node/tests/fixtures/` are byte-for-byte copies of `validator-python/tests/fixtures/` so the two test suites exercise identical manifests; any divergence is a bug in whichever reference is wrong (the canonical algorithm is the tiebreaker).

**Adopters need only one of the two language-native validators** — pick the reference whose runtime your CI already provides:

| Reference | Pick when | Trade-off |
|-----------|-----------|-----------|
| `validator-python/` | CI already has Python 3.10+; your team is Python/ML/data-pipeline-leaning. | Slightly slower (`~400 ms` end-to-end on a 2023-era laptop). |
| `validator-node/` | CI already has Node 20+; your team is JS/TS/web-leaning, or you want editor integrations. | Slightly faster (`~200 ms`). |

`validator-posix-shell/` covers a different niche (zero-runtime-dep portability with a documented coverage gap on rules 2.4 / 2.5 / 3.2 / 3.4) and is **not** equivalent to either language-native reference; see its `DEVIATIONS.md`.

This file is intentionally non-normative; do not cite it from `docs/`. Its only consumer is reviewers asking "should this new file live here?" and audit tooling that wants a structured view of the directory.
