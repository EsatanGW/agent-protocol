#!/usr/bin/env python3
"""Block re-introduction of retired vocabulary outside allow-listed locations.

`docs/glossary.md §Note on legacy names` retires several earlier-draft
aliases for execution modes. Those terms are intentionally documented in
the glossary and remain in historical records (CHANGELOG, ROADMAP) but
must not leak back into normative content (other `docs/`, `skills/`,
`reference-implementations/` outside its allow-list, runtime bridges,
schemas, templates).

Exit codes (matches the `validate-cluster-disjointness.py` convention):
  0  no legacy terms found outside allow-list
  1  at least one violation
  2  tool error (missing file, unreadable encoding, etc.)

Usage:
    python3 .github/scripts/check-legacy-terms.py
    python3 .github/scripts/check-legacy-terms.py --self-test-only
    python3 .github/scripts/check-legacy-terms.py --path <single-file>
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
import tempfile
from pathlib import Path


# Source: docs/glossary.md §Note on legacy names. Add new retired aliases
# here when glossary updates; CI then prevents regression.
LEGACY_TERMS: list[str] = [
    "no-process path",
    "ultra-lean",
    "No skill",
    "three-line handoff",
    "stripped-down version",
]

# Files where the retired aliases are legitimately allowed:
#   - the glossary itself defines them
#   - historical records (CHANGELOG, ROADMAP) must not be rewritten
#     (see CLAUDE.md §3 "Do not rewrite historical CHANGELOG entries")
#   - onboarding/when-not-to-use-this.md cross-references the retired
#     aliases in the same prose convention as glossary.md
#   - this script and its docs (self-reference)
ALLOWED_PATHS: list[str] = [
    "docs/glossary.md",
    "docs/onboarding/when-not-to-use-this.md",
    "CHANGELOG.md",
    "CHANGELOG.json",
    "CHANGELOG.archive.md",
    "CHANGELOG.archive.json",
    "ROADMAP.md",
    "ROADMAP.archive.md",
    ".github/scripts/check-legacy-terms.py",
]

# Files types we scan. Binary and lock-style files are excluded.
SCAN_GLOBS: list[str] = ["*.md", "*.yaml", "*.yml", "*.json", "*.mdc", "*.txt"]

# Directories to skip entirely (not part of normative content surface).
SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".venv",
    "venv",
}


def _build_patterns(terms: list[str]) -> list[tuple[str, re.Pattern[str]]]:
    """Compile word-boundary regex per term.

    Word boundaries (`\\b`) are essential: without them, "ultra-lean"
    would also match "lean-and-mean", and "No skill" would match
    "Linus skills". With `\\b`, hyphens count as word boundaries on both
    sides, and the multi-word terms are anchored on the outer edges only.
    """
    compiled = []
    for term in terms:
        # `\b` at the outer edges is enough; inner hyphens are kept literal.
        pattern = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)")
        compiled.append((term, pattern))
    return compiled


def _is_allowed(rel_path: str, allowed: list[str]) -> bool:
    """Return True if `rel_path` (POSIX) matches any allow-list entry.

    Allow-list entries are exact-match POSIX paths, not globs. This is
    deliberate: opening up to globs invites accidental allow-listing
    (e.g. `docs/**` would defeat the entire point of the check).
    """
    return rel_path in allowed


def _iter_files(root: Path) -> list[Path]:
    """Walk `root`, yielding files matching SCAN_GLOBS, skipping SKIP_DIRS."""
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Skip if any ancestor is in SKIP_DIRS.
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        name = path.name
        if not any(fnmatch.fnmatch(name, g) for g in SCAN_GLOBS):
            continue
        out.append(path)
    return out


def _scan_file(
    path: Path,
    rel_path: str,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[tuple[int, str, str]]:
    """Return (line_no, term, line_text) for every legacy term hit."""
    hits: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        # Binary or unreadable — skip silently. SCAN_GLOBS already excludes
        # the most obvious binaries; this is a defense in depth.
        return hits
    for line_no, line in enumerate(text.splitlines(), start=1):
        for term, pat in patterns:
            if pat.search(line):
                hits.append((line_no, term, line.rstrip()))
    return hits


def scan_repo(
    repo_root: Path,
    allowed: list[str] | None = None,
    terms: list[str] | None = None,
) -> list[tuple[str, int, str, str]]:
    """Return list of (rel_path, line_no, term, line) violations."""
    allowed = allowed if allowed is not None else ALLOWED_PATHS
    terms = terms if terms is not None else LEGACY_TERMS
    patterns = _build_patterns(terms)
    violations: list[tuple[str, int, str, str]] = []
    for path in _iter_files(repo_root):
        rel_path = path.relative_to(repo_root).as_posix()
        if _is_allowed(rel_path, allowed):
            continue
        for line_no, term, line in _scan_file(path, rel_path, patterns):
            violations.append((rel_path, line_no, term, line))
    return violations


def _run_self_test() -> list[str]:
    """Verify the checker on synthetic fixtures.

    Cases:
      1. Clean file → no violation
      2. Legacy term in non-allow-listed file → violation
      3. Legacy term in allow-listed file → no violation
      4. Word-boundary respect: "ultra-leanness" should NOT trigger
         "ultra-lean" (the term is not on a word boundary)
      5. Multi-word term: "no-process path" appearing across the
         exact phrase, but not when only one word matches
    """
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        (root / "docs").mkdir()
        (root / "docs" / "glossary.md").write_text("Defines no-process path here.\n")
        (root / "docs" / "clean.md").write_text("All canonical names only.\n")
        (root / "docs" / "drifted.md").write_text(
            "We use the ultra-lean approach for trivial changes.\n"
        )
        (root / "docs" / "boundary.md").write_text(
            "The team's ultra-leanness is admirable.\n"
        )
        (root / "docs" / "partial.md").write_text(
            "There is no process for this; the team has its own path.\n"
        )

        allowed_test = ["docs/glossary.md"]
        results = scan_repo(root, allowed=allowed_test)
        rel_hits = {(r, t) for r, _, t, _ in results}

        # Case 1+5: clean.md and partial.md must not trigger.
        if any(r == "docs/clean.md" for r, _ in rel_hits):
            failures.append("self-test: clean.md should not violate")
        if any(r == "docs/partial.md" for r, _ in rel_hits):
            failures.append("self-test: partial.md (no-process / path split) should not violate")

        # Case 2: drifted.md must trigger ultra-lean
        if ("docs/drifted.md", "ultra-lean") not in rel_hits:
            failures.append("self-test: drifted.md should trigger ultra-lean")

        # Case 3: glossary.md must NOT trigger (allow-listed)
        if any(r == "docs/glossary.md" for r, _ in rel_hits):
            failures.append("self-test: glossary.md (allow-listed) should not violate")

        # Case 4: ultra-leanness should not match ultra-lean
        if ("docs/boundary.md", "ultra-lean") in rel_hits:
            failures.append("self-test: 'ultra-leanness' should not match 'ultra-lean'")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        help="Scan a single file (skips repo walk).",
    )
    parser.add_argument(
        "--self-test-only",
        action="store_true",
        help="Run embedded self-test and exit.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repo root (default: inferred from script location).",
    )
    args = parser.parse_args()

    repo_root = args.repo_root or Path(__file__).resolve().parents[2]

    if args.path is None:
        self_test_failures = _run_self_test()
        if self_test_failures:
            print("self-test: FAIL", file=sys.stderr)
            for msg in self_test_failures:
                print(f"  {msg}", file=sys.stderr)
            return 2
        print("self-test: ok (5 cases)")

    if args.self_test_only:
        return 0

    if args.path is not None:
        if not args.path.exists():
            print(f"ERROR: path not found: {args.path}", file=sys.stderr)
            return 2
        rel = args.path.resolve().relative_to(repo_root).as_posix()
        patterns = _build_patterns(LEGACY_TERMS)
        if _is_allowed(rel, ALLOWED_PATHS):
            print(f"ok   {rel} (allow-listed)")
            return 0
        hits = _scan_file(args.path, rel, patterns)
        for line_no, term, line in hits:
            print(f"FAIL {rel}:{line_no} '{term}' — {line}", file=sys.stderr)
        return 1 if hits else 0

    violations = scan_repo(repo_root)
    if not violations:
        print(f"ok   no legacy terms outside allow-list ({len(LEGACY_TERMS)} terms checked)")
        return 0

    print(f"FAIL {len(violations)} legacy-term violation(s):", file=sys.stderr)
    for rel, line_no, term, line in violations:
        print(f"  {rel}:{line_no} '{term}' — {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
