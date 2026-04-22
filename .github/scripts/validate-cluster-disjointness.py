#!/usr/bin/env python3
"""Validate Pattern C `implementation_clusters` for pair-wise file
disjointness.

Pattern C (see `skills/engineering-workflow/references/cluster-parallelism.md`
and `schemas/change-manifest.schema.yaml §implementation_clusters`)
declares that clusters must have file-disjoint `scope_files` patterns —
no two clusters may resolve to the same file. This check is declared
as "validator-level, not expressible in pure JSON Schema"; this script
is that validator.

What this script checks:
  For every manifest with a non-empty `implementation_clusters` field:
    Expand each cluster's `scope_files` globs against a file universe
    (the repo root by default). If any two clusters share any file,
    that is a disjointness violation.

Scope:
  1. Every manifest template under `templates/` with
     `implementation_clusters` filled.
  2. Every manifest under `examples/starter-repo/` (when present).
  3. An embedded self-test (synthetic fixtures in a tmpdir) — always
     runs, ensures the checker itself works regardless of repo content.

Exit codes (matches the `validate-schema-syntax.py` convention):
  0  all clusters pair-wise disjoint (or no `implementation_clusters`
     declared anywhere)
  1  at least one disjointness violation
  2  tool error (missing file, YAML parse error, etc.)

Usage:
    python3 .github/scripts/validate-cluster-disjointness.py
    python3 .github/scripts/validate-cluster-disjointness.py --self-test-only
    python3 .github/scripts/validate-cluster-disjointness.py --manifest <path>
"""

from __future__ import annotations

import argparse
import glob as _glob
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import yaml


def _expand_globs(patterns: Iterable[str], root: Path) -> set[str]:
    """Expand glob patterns against ``root``.

    Uses ``glob.glob(..., root_dir=root, recursive=True)`` so ``**`` is
    honored. Returns a set of repo-relative POSIX paths of matching
    files (not directories; directories are excluded because the
    disjointness invariant is over writable files).
    """
    matched: set[str] = set()
    for pattern in patterns:
        for hit in _glob.glob(pattern, root_dir=str(root), recursive=True):
            abs_path = root / hit
            if abs_path.is_file():
                matched.add(Path(hit).as_posix())
    return matched


def check_disjointness(clusters: list[dict], root: Path) -> list[str]:
    """Return a list of violation messages.

    Empty list == pair-wise disjoint. Each violation names the two
    clusters and up to three shared paths (a sample is sufficient for
    diagnosis; printing 300 shared paths is just noise).
    """
    if not clusters:
        return []

    expansions: dict[str, set[str]] = {}
    for cluster in clusters:
        cid = cluster.get("cluster_id", "<unnamed>")
        patterns = cluster.get("scope_files", []) or []
        expansions[cid] = _expand_globs(patterns, root)

    violations: list[str] = []
    cluster_ids = [c.get("cluster_id", "<unnamed>") for c in clusters]
    for i in range(len(cluster_ids)):
        for j in range(i + 1, len(cluster_ids)):
            a = cluster_ids[i]
            b = cluster_ids[j]
            shared = expansions[a] & expansions[b]
            if shared:
                sample = sorted(shared)[:3]
                more = "" if len(shared) <= 3 else f" (+{len(shared) - 3} more)"
                violations.append(
                    f"overlap between clusters '{a}' and '{b}': "
                    f"shared paths {sample}{more}"
                )
    return violations


def _load_manifest_docs(path: Path) -> list[dict]:
    """Return every non-None YAML document in ``path``.

    Manifests may be single-document (most templates) or multi-document
    (the multi-agent-handoff example shows progression across phases).
    """
    with path.open() as fh:
        return [d for d in yaml.safe_load_all(fh) if d]


def _scan_manifests(repo_root: Path) -> list[tuple[Path, int, list[str]]]:
    """Scan every known manifest location; return violations per-doc.

    Each tuple: (manifest path, doc index, violation messages).
    Only returns manifests that actually have `implementation_clusters`
    — unrelated manifests produce no output.
    """
    results: list[tuple[Path, int, list[str]]] = []
    candidates: list[Path] = []

    templates_dir = repo_root / "templates"
    if templates_dir.is_dir():
        candidates.extend(sorted(templates_dir.glob("change-manifest.example-*.yaml")))

    starter_repo_dir = repo_root / "examples" / "starter-repo"
    if starter_repo_dir.is_dir():
        candidates.extend(sorted(starter_repo_dir.rglob("change-manifest.*.yaml")))

    for path in candidates:
        docs = _load_manifest_docs(path)
        for idx, doc in enumerate(docs):
            clusters = doc.get("implementation_clusters")
            if not clusters:
                continue
            violations = check_disjointness(clusters, repo_root)
            results.append((path, idx, violations))
    return results


def _run_self_test() -> list[str]:
    """Exercise the checker on synthetic fixtures in a tmpdir.

    Returns a list of failure messages; empty list == self-test passed.
    The fixtures are the minimal set that would have caught the Pattern
    C design's explicit invariant (file-disjoint clusters):

      1. Disjoint clusters (different top-level dirs)        → OK
      2. Disjoint clusters (same dir, different subdirs)     → OK
      3. One cluster's pattern subsumes another (db/** vs db/migrations/*) → OVERLAP
      4. Identical patterns in two clusters                  → OVERLAP
      5. No `implementation_clusters` field                   → OK (no-op)
      6. Glob hits a file outside both cluster scopes         → not counted as overlap
    """
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        files = [
            "db/migrations/001_init.sql",
            "db/migrations/002_index.sql",
            "db/seeds/dev.sql",
            "services/api/handler.py",
            "services/api/routes.py",
            "services/worker/run.py",
            "apps/web/src/vouchers/list.tsx",
            "apps/web/src/vouchers/detail.tsx",
            "apps/web/locales/en/voucher.json",
            "unrelated/README.md",
        ]
        for rel in files:
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).touch()

        def case(label: str, clusters: list[dict], expect_violation: bool) -> None:
            vs = check_disjointness(clusters, root)
            if expect_violation and not vs:
                failures.append(f"self-test '{label}': expected violation, got none")
            elif not expect_violation and vs:
                failures.append(f"self-test '{label}': expected OK, got {vs}")

        case(
            "disjoint — top-level dirs",
            [
                {"cluster_id": "db", "scope_files": ["db/**"]},
                {"cluster_id": "api", "scope_files": ["services/api/**"]},
                {"cluster_id": "web", "scope_files": ["apps/web/src/**"]},
            ],
            expect_violation=False,
        )
        case(
            "disjoint — same parent, different subdirs",
            [
                {"cluster_id": "api", "scope_files": ["services/api/**"]},
                {"cluster_id": "worker", "scope_files": ["services/worker/**"]},
            ],
            expect_violation=False,
        )
        case(
            "overlap — subsuming pattern",
            [
                {"cluster_id": "db-all", "scope_files": ["db/**"]},
                {"cluster_id": "db-migrations", "scope_files": ["db/migrations/*.sql"]},
            ],
            expect_violation=True,
        )
        case(
            "overlap — identical patterns",
            [
                {"cluster_id": "a", "scope_files": ["apps/web/src/vouchers/*.tsx"]},
                {"cluster_id": "b", "scope_files": ["apps/web/src/vouchers/*.tsx"]},
            ],
            expect_violation=True,
        )
        case(
            "no-op — empty field",
            [],
            expect_violation=False,
        )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Check only this manifest file (skips repo scan).",
    )
    parser.add_argument(
        "--self-test-only",
        action="store_true",
        help="Run embedded self-test and exit (skip repo scan).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repo root (default: inferred from script location).",
    )
    args = parser.parse_args()

    repo_root = args.repo_root or Path(__file__).resolve().parents[2]

    # Self-test always runs unless --manifest narrows the scope.
    if args.manifest is None:
        self_test_failures = _run_self_test()
        if self_test_failures:
            print("self-test: FAIL", file=sys.stderr)
            for msg in self_test_failures:
                print(f"  {msg}", file=sys.stderr)
            return 2
        print("self-test: ok (5 cases)")

    if args.self_test_only:
        return 0

    # Scan mode
    if args.manifest is not None:
        if not args.manifest.exists():
            print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
            return 2
        try:
            docs = _load_manifest_docs(args.manifest)
        except yaml.YAMLError as exc:
            print(f"ERROR: invalid YAML in {args.manifest}: {exc}", file=sys.stderr)
            return 2
        results = []
        for idx, doc in enumerate(docs):
            clusters = doc.get("implementation_clusters")
            if not clusters:
                continue
            results.append((args.manifest, idx, check_disjointness(clusters, repo_root)))
    else:
        results = _scan_manifests(repo_root)

    if not results:
        print("no manifests with implementation_clusters found — nothing to check")
        return 0

    failed = 0
    for path, idx, violations in results:
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            rel = path  # manifest outside repo_root — print as-is
        suffix = f" doc[{idx}]" if idx > 0 else ""
        if violations:
            failed += 1
            print(f"FAIL {rel}{suffix}", file=sys.stderr)
            for v in violations:
                print(f"  {v}", file=sys.stderr)
        else:
            print(f"ok   {rel}{suffix}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
