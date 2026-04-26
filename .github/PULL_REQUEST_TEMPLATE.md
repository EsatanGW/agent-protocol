<!--
This repository's own PRs follow the methodology this repository defines:

  1. Declare scope and surfaces BEFORE implementation.
  2. Point at the Source of Truth and list consumer updates.
  3. Attach the evidence that shows the change is actually in place.

Non-trivial changes SHOULD link a Change Manifest (in-tree or in PR body).
Trivial changes (typo, single-line doc fix, dependency bump) can skip the
manifest but still fill in the Surfaces and Evidence sections below.
-->

## Summary

<!-- 1–3 sentences. What changed and why. Reader should not need to read the
     diff to understand intent. -->

## Scope classification

- [ ] Lean — single surface, ≤ 1 consumer, no public behavior change.
- [ ] Full — multiple surfaces, public behavior change, new contract, or any breaking change.
- [ ] Trivial — typo / comment / single-file doc fix / chore.

## Surfaces touched

<!-- Check every surface the change will be PERCEIVED through.
     "Touched" means a consumer of this repo would notice a difference. -->

- [ ] User surface (UI, copy, routes, a11y, i18n)
- [ ] System-interface surface (schemas, APIs, event shapes, public contracts, hook contracts)
- [ ] Information surface (config, flags, enums, validation rules)
- [ ] Operational surface (CI, release process, runbook, observability)

Rationale for the surfaces checked (one sentence each is enough):

- …

## Source of Truth impact

<!-- Which canonical file owns the concept you changed?
     If you changed it, did you update every consumer the repo references? -->

- SoT file(s): `docs/…` / `schemas/…` / `skills/…`
- Consumer updates in this PR: `docs/…`, `skills/engineering-workflow/templates/…`, `reference-implementations/…`
- Known consumers NOT updated and why: 

## Evidence

<!-- For a doc/skill change, quote the renamed passage or cite the new file.
     For a schema/template change, attach or reference a passing validator run.
     For a reference-hook change, attach selftest output. -->

- [ ] Ran `python3 .github/scripts/validate-schema-syntax.py`
- [ ] Ran `python3 .github/scripts/validate-templates.py`
- [ ] Ran `sh .github/scripts/check-version-consistency.sh`
- [ ] Ran `sh reference-implementations/hooks-claude-code/selftests/selftest.sh` (if hook bundle touched)
- [ ] Ran `pytest` in `reference-implementations/validator-python/` (if validator touched)
- [ ] Visual diagrams render in GitHub preview (if `docs/diagrams.md` touched)

Evidence artifacts (paste relevant output or link to CI run):

```
…
```

## Breaking-change level

- [ ] L0 — additive, no consumer action required.
- [ ] L1 — additive + deprecation, opt-in migration.
- [ ] L2 — structural, consumers must adapt.
- [ ] L3 — removal / renaming with migration path.
- [ ] L4 — removal / renaming without migration path (avoid — requires explicit justification).

If ≥ L1, link the migration guidance (usually `CHANGELOG.md` under `Changed` / `Removed` or a dedicated doc section).

## Rollback mode

- [ ] Mode 1 — reversible by revert (most doc / code changes here).
- [ ] Mode 2 — forward-fix (e.g. schema version bump that already shipped).
- [ ] Mode 3 — compensation required (rare in this repo; call it out).

## Cross-cutting concerns

Only check items that changed. Leave unchecked if this PR does not touch them.

- [ ] **Security** — touches `reference-implementations/hooks-*`, CI workflow, or anything in `.github/`. Confirm no untrusted event inputs, no side effects, no network-in-hook.
- [ ] **Observability** — touches logging / telemetry / metrics surfaces that adopters rely on.
- [ ] **Testability** — adds or removes CI jobs, selftests, or validator coverage.
- [ ] **Performance** — changes anything with a declared latency budget (runtime hooks < 500 ms / 2 s per contract).

## Change Manifest (Full mode)

<!-- Full-mode changes in the host adopting project SHOULD ship with a
     Change Manifest. Inside this repo the equivalent is an entry in
     ROADMAP.md under "Active initiatives" — link it here. -->

- ROADMAP initiative: 
- Or attached manifest:
- Or N/A (trivial / single-surface Lean):

## Checklist before requesting review

- [ ] Scope matches the ROADMAP row (or this is a trivial change with no row).
- [ ] No drive-by refactors; no opportunistic cleanup outside the declared scope.
- [ ] No vendor / model / framework names introduced into normative content (bridges excepted).
- [ ] No CHANGELOG rewrites of past entries — the new entry appended, old entries left as historical fact.
- [ ] `CLAUDE.md` §5 observed: if a cross-cutting term changed, all consumers updated.

---

By submitting this PR you confirm: the changes are your own, MIT-compatible, and free of secrets or proprietary content.
