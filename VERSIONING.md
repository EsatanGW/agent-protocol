# Versioning Policy

This project uses a practical documentation-and-skill versioning model.

## Principles

- Public documentation and the engineering-workflow skill may evolve together, but releases should describe both clearly.
- Version bumps reflect user-visible changes to structure, meaning, or recommended usage.

## Recommended bump rules

### Patch
Use for:
- wording clarifications
- typo fixes
- small examples fixes
- non-semantic template improvements

### Minor
Use for:
- new examples
- new templates
- new workflow guidance
- improved trigger logic
- additional references or publication assets

### Major
Use for:
- changes to the core worldview
- incompatible restructuring of the workflow
- changes that require users to relearn the mode-selection or artifact model

## Release notes should always answer

- What changed in the public method layer?
- What changed in the execution-skill layer?
- Does this affect existing usage patterns?
- Are there any migration notes?

## Release pre-push checklist

The version string is declared in **five** places (this is a fan-out consumer registry — see [`docs/sot-desync-anti-patterns.md §Anti-pattern 6`](docs/sot-desync-anti-patterns.md)). All five must agree at the SHA tagged for release; CI fails otherwise. Run these checks **before** pushing the release commit and tag:

```sh
# 1. All five version declarations agree
sh .github/scripts/check-version-consistency.sh

# 2. CHANGELOG.json is regenerated and in sync with CHANGELOG.md
python3 .github/scripts/generate-changelog-json.py --check
```

If either fails, fix in place — do not push expecting a follow-up commit. Force-pushing a release tag forward to a corrective commit is destructive (already-fetched clones see the wrong SHA) and is the failure mode this checklist is designed to prevent.

Bridge / index consumers updated by L1+ changes (canonical methodology content edits) are governed by [`AGENTS.md §File role map`](AGENTS.md) and verified by `.github/scripts/check-role-consistency.py` and `check-internal-links.py` — run them too if the release touched bridges or index files.
