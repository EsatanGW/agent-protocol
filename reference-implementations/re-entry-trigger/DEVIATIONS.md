# Deviations from the canonical Rule 6

Tracks where this reference differs from `docs/phase-gate-discipline.md` Rule 6.

## Implemented

- Six of the seven Rule 6 source variations (1.23.0 doc form: organized as four destination phases — Phase 0 / Phase 1 / Phase 2 / Phase 4 with Phase 4 split into two sub-variants. Source variations preserved verbatim in the doc as `(a)`–`(g)`; this implementation covers (a), (c), (d), (e), (f), (g) — the same coverage as before the 1.23.0 compression):
  - (a) New surface touched → Phase 0 Clarify (`0_clarify`)
  - (c) SoT pattern re-classified → Phase 1 Investigate (`1_investigate`)
  - (d) Breaking-change level rises → Phase 1 Investigate (`1_investigate`; with migration_plan at L2+)
  - (e) Rollback mode rises → Phase 2 Plan (`2_plan`; with compensation_plan + post_delivery at Mode 3)
  - (f) Implementation strategy changes only → Phase 4 Implement append-only (`4_implement_append`)
  - (g) Evidence rejected by Reviewer → Phase 4 Implement evidence replacement (`4_implement_evidence`)
- Pure-function API taking two manifest dicts; no network, no filesystem,
  no git. Runtime-neutral per the automation contract.
- CLI wrapper loading the two manifests from YAML files and emitting
  JSON to stdout; exit codes 0 / 1 / 2 per the automation-contract convention.
- Twelve test cases, one per decision-table row plus happy path, down-
  grade suppression, append-only suppression under higher-severity re-entry,
  and multi-trigger case.

## Not implemented (by design)

| Row / feature | Reason |
|----------------|--------|
| (b) "Spec updated mid-change by user" → Phase 0 Clarify | Requires an external signal (a spec file in the repo changed; this is not derivable from the two manifest dicts alone). Callers can detect this via `git diff --name-only` against spec file globs, then synthesize a suggestion. |
| Git-base-ref auto-loading | Pure-function discipline — users assemble the `old` and `new` dicts themselves. A wrapper layer that calls `git show <ref>:<path>` is a separate concern and can live in validators or hooks. |
| PR-comment posting | Out of scope — the module emits suggestions; posting is a CI platform concern. |
| Severity assignment | Every suggestion is returned uniformly; Rule 6 does not itself specify severity. A validator that wraps this module chooses the severity (advisory for most, blocking when a team policy requires). |

## Behaviour compared to the normative rule

- **Down-grade not suggested.** Rule 6 says "breaking-change level rises" triggers re-entry. If level drops (L2 → L0, for example, due to judgment correction), no re-entry is suggested. That is intentional: down-grades are usually a classification-only change with no consumer impact, and re-opening a phase would be ceremony. If a team wants different behaviour, they should escalate the case rather than make this module detect it.
- **Append-only suggestion suppressed when higher-severity fires.** If both "evidence added" and "breaking-change rose" apply to the same diff, only the Phase 1 Investigate suggestion is emitted — the Phase 4 Implement (append) suggestion would be subsumed by the broader re-entry.
- **SoT pattern-change detection is by `info_name` identity.** A rename of an `info_name` will appear as "old entry removed, new entry added" rather than "pattern changed." That is correct — a rename is usually an SoT migration in its own right and deserves different handling than a pattern re-classification on the same identity.

## Methodology version targeted

1.23.0 — Rule 6 decision table re-organized from seven source variations into four destination-phase rows (Phase 0 / 1 / 2 / 4-with-two-sub-variants). The table form changed; the source variations are preserved as `(a)`–`(g)` sub-cells. This implementation's API is unchanged (same five phase enum values returned: `0_clarify` / `1_investigate` / `2_plan` / `4_implement_append` / `4_implement_evidence`), so consumers do not need to re-pin a different module version.

Originally introduced in 1.8.0 as the seven-row form.
