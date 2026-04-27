# Re-entry Trigger

A small, pure-function reference implementation of the `docs/phase-gate-discipline.md` **Rule 6 (Phase Re-entry Protocol)** decision table. Given two manifest states (an old committed state and a new in-progress state), it suggests which phase(s) to re-open, why, and which manifest fields must be rewritten.

**Non-normative.** Consumers may implement the same decision logic in any language or skip it entirely. The normative source is Rule 6 of `docs/phase-gate-discipline.md`; this module exists to make the rule mechanically testable and to give runtimes a minimal reference to embed.

---

## Decision table (from Rule 6, 1.23.0 form)

Rule 6 organizes seven source variations `(a)`–`(g)` into four destination phases. This module returns five phase-enum values (Phase 4 splits into append vs evidence sub-variants). The mapping from source variations to enum values:

| Re-entry phase enum | Source variations covered | Fields rewritten |
|---|---|---|
| `0_clarify` | (a) a new surface is being touched | `surfaces_touched`, `evidence_plan` |
| `1_investigate` | (c) SoT pattern mis-classified; (d) breaking-change level rises | (c) `sot_map`, `consumers`. (d) `breaking_change`, `rollback` (and `breaking_change.migration_plan` at L2+) |
| `2_plan` | (e) rollback mode rises | `rollback` (and `post_delivery`, `rollback.compensation_plan` at Mode 3) |
| `4_implement_append` | (f) implementation strategy changes only | `implementation_notes`, `scope_deltas` |
| `4_implement_evidence` | (g) evidence insufficient per Reviewer | `evidence_plan.artifacts` |

Source variation **(b) "spec updated mid-change by user"** → Phase 0 Clarify is **not detected here** — it requires an external signal (spec-file change from `git diff`) that is not derivable from two manifest dicts alone. Runtimes that want that detection can add it as a wrapper layer; see "Integration with validators" below.

---

## Usage

### As a library

```python
from suggest_reentry import suggest_reentry

with open("manifest-before.yaml") as f:
    old = yaml.safe_load(f)
with open("manifest-after.yaml") as f:
    new = yaml.safe_load(f)

suggestions = suggest_reentry(old, new)
for s in suggestions:
    print(s["phase"], s["reasons"], s["fields_to_rewrite"])
```

Each suggestion is a dict:

```python
{
    "phase": "1_investigate",                                     # enum
    "reasons": ["breaking_change.level rose from L0 to L2"],       # list[str]
    "fields_to_rewrite": ["breaking_change", "rollback",
                          "breaking_change.migration_plan"],       # list[str]
}
```

Phase enum values:
- `0_clarify` — Phase 0 Clarify re-entry
- `1_investigate` — Phase 1 Investigate re-entry
- `2_plan` — Phase 2 Plan re-entry
- `4_implement_append` — Phase 4 Implement append-only (low-severity strategy adjustment)
- `4_implement_evidence` — Phase 4 Implement with evidence replacement (Reviewer send-back)

Multiple rules may fire for one diff; the return list has all suggestions. Callers should open one ROADMAP row per suggestion when more than one phase is involved.

### As a CLI

```sh
python3 suggest_reentry.py <old-manifest.yaml> <new-manifest.yaml>
```

Output: JSON `{"suggestions": [...]}` on stdout. Exit codes:
- `0` — no re-entry suggested (diff is append-only-compatible)
- `1` — one or more re-entry suggestions emitted
- `2` — tool / input error

---

## Integration with validators

The first-class reference validators (`validator-posix-shell`, `validator-python`) and the community-maintained `community/validator-node` implement Layers 1–3 of the automation contract. Rule 6 re-entry detection is **Layer 3-adjacent** — it compares two manifest states, not just one. Integration options:

- **Wrap as a Layer 3 rule.** A validator can invoke `suggest_reentry(git_show(base_ref, manifest_path), current_manifest)` and emit each suggestion as an advisory finding. The rule_id stable name is `drift.phase_reentry_suggested` (reserved for this use).
- **Standalone CI check.** A CI job can run the CLI and post suggestions as a PR comment — useful when the team wants re-entry to be visible but not blocking.
- **Runtime hook.** A pre-commit or on-stop hook (per `docs/runtime-hook-contract.md`) can run this and warn the operator when a re-entry is warranted before the commit lands.

This module is intentionally **not** integrated into the three validators by default — the validators are file-at-a-time tools; Rule 6 needs two files. Runtimes that want the integration should assemble the two manifest states using their own git plumbing.

---

## Tests

```sh
python3 -m pytest reference-implementations/re-entry-trigger/tests/ -q
```

Twelve test cases cover each row of the decision table, the happy path (no suggestion), the down-grade suppression rule, the append-only suppression when higher-severity re-entry also fires, and the multi-trigger case.

---

## Non-functional properties

- **Pure function.** No network, no filesystem access, no git operations. Input = two dicts; output = list of dicts.
- **No runtime dependencies** beyond Python stdlib + PyYAML (only for the CLI's file loading). The core function has zero dependencies.
- **Offline-operable.** Can run in any environment where the two manifest dicts are available.
- **Deterministic.** Same input → same output; sets are sorted before returning strings.

---

## What this module is not

- **Not a replacement for the Reviewer's judgment.** The module suggests re-entry based on field-level diffs; it does not decide whether the re-entry is correct. A Reviewer may still escalate beyond the suggestion (for example, upgrading a `4_implement_append` suggestion to a full Phase 1 re-entry because a subtle SoT issue surfaced).
- **Not a git-aware tool.** Users of this module assemble the old/new manifest dicts themselves. Some callers will use `git show <ref>:<path>` to populate `old`; others will use the prior manifest committed alongside the current change; others will pass two files directly.
- **Not a blocking gate by default.** The suggestions are advisory. Teams may choose to make them blocking in CI per `docs/automation-contract.md` §Four automation tiers.

## See also

- [`docs/phase-gate-discipline.md`](../../docs/phase-gate-discipline.md) Rule 6 — normative decision table
- [`docs/automation-contract-algorithm.md`](../../docs/automation-contract-algorithm.md) — Layer 3 drift-detection section (the sibling concept at the single-manifest level)
- [`agents/reviewer.md`](../../agents/reviewer.md) — the Reviewer's send-back authority references Rule 6 for the re-entry phase
- [`skills/engineering-workflow/phases/fix-retest-loop.md`](../../skills/engineering-workflow/phases/fix-retest-loop.md) — the fix-retest loop defers to Rule 6 when the cause is outside Phase 4
