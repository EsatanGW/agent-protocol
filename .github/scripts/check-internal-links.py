#!/usr/bin/env python3
"""Verify every markdown internal-link resolves to an existing file.

The repo cross-references heavily across `docs/`, `skills/`, and
`reference-implementations/`. Renames or moves can leave dangling
links; this checker catches them at PR time.

Scope (deliberately narrow to keep CI offline-safe):
  - Markdown link syntax `[text](target)` and reference-style
    `[text]: target`.
  - Only **internal** targets — those starting with `./`, `../`, or a
    bare relative path (no scheme). External `http(s)://`, `mailto:`,
    `tel:`, fragment-only `#anchor`, and intra-document anchors are
    skipped (out of scope for an offline checker).
  - Anchor fragments (`#section`) are stripped before path resolution;
    we verify the file exists, not that the anchor exists. Anchor-level
    validation requires markdown header parsing; a future enhancement.

Allow-listed link forms that are intentionally non-resolvable:
  - `example.com`, `https://example.com/...` — illustrative only,
    not internal links anyway.

Exit codes (matches `validate-cluster-disjointness.py` convention):
  0  every internal link resolves
  1  at least one broken link
  2  tool error

Usage:
    python3 .github/scripts/check-internal-links.py
    python3 .github/scripts/check-internal-links.py --self-test-only
    python3 .github/scripts/check-internal-links.py --path <single-file>
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path


# Match `[text](target)` (inline) and `[ref]: target` (reference).
# The `target` capture stops at whitespace, `)`, or `>` (for autolinks).
INLINE_LINK_RE = re.compile(r"\[(?:[^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
REF_LINK_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)

# Strip fenced code blocks (```...``` and ~~~...~~~) and inline code
# spans (`...`) before link extraction. Markdown docs frequently
# contain *literal example* link syntax inside code spans (e.g.
# the CHANGELOG entry that documents this very script using
# ``[text](target)`` as a code example); without this strip, the
# checker would chase those examples as real links.
FENCED_CODE_RE = re.compile(r"^([`~]{3,})[^\n]*\n.*?^\1\s*$", re.DOTALL | re.MULTILINE)
# Inline code spans use any run of N backticks as the delimiter, with
# a matching closing run of the same length. Match N=1..3 (covers
# single, double — common for examples that contain backticks — and
# triple-as-inline). Multi-line inline code is rare; we keep the
# pattern single-line for simplicity.
INLINE_CODE_RE = re.compile(r"(`{1,3})(?:(?!\1).)+?\1")


def _strip_code_spans(text: str) -> str:
    """Remove fenced code blocks and inline code spans (replaced by
    single spaces so line numbers are preserved for fenced blocks the
    same row count is retained — but inline-code replacement preserves
    column positions enough for our line-level reporting).
    """
    # Fenced first; replace each match with a same-line-count blank
    # block so subsequent line-number indexing stays stable.
    def _blank_block(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    text = FENCED_CODE_RE.sub(_blank_block, text)
    text = INLINE_CODE_RE.sub(" ", text)
    return text

# Skip prefixes — external schemes, anchor-only.
SKIP_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "ftp://",
    "#",
    "//",  # protocol-relative
)

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


def _should_skip(target: str) -> bool:
    if not target:
        return True
    if target.startswith(SKIP_PREFIXES):
        return True
    # Common URL fragments that aren't really paths.
    if target.startswith("data:"):
        return True
    return False


def _strip_anchor(target: str) -> str:
    """Strip `#anchor` from a link target."""
    if "#" in target:
        return target.split("#", 1)[0]
    return target


def _extract_links(text: str) -> list[str]:
    """Return all link targets from inline + reference-style links."""
    return INLINE_LINK_RE.findall(text) + REF_LINK_RE.findall(text)


def check_file(md_path: Path, repo_root: Path) -> list[tuple[int, str, str]]:
    """Return (line_no, target, reason) for every broken link.

    Empty list = all internal links resolve.
    """
    raw = md_path.read_text(encoding="utf-8")
    text = _strip_code_spans(raw)
    base = md_path.parent

    targets = _extract_links(text)

    broken: list[tuple[int, str, str]] = []
    # We need line numbers; do a second pass on the code-stripped text
    # so the line numbers correspond to lines that still contain real
    # links (fenced blocks were replaced with blank lines preserving
    # line counts; inline spans were replaced with spaces).
    line_index: dict[str, int] = {}
    for line_no, line in enumerate(text.splitlines(), start=1):
        for target in INLINE_LINK_RE.findall(line) + REF_LINK_RE.findall(line):
            if target not in line_index:
                line_index[target] = line_no

    for target in targets:
        if _should_skip(target):
            continue
        path_part = _strip_anchor(target)
        if not path_part:
            # `#anchor` only (intra-document) — skip.
            continue
        # Trailing slash means a directory reference.
        candidate = (base / path_part).resolve()
        try:
            candidate.relative_to(repo_root.resolve())
        except ValueError:
            # Resolved outside repo root — likely path-traversal typo.
            broken.append(
                (line_index.get(target, 0), target, "resolves outside repo")
            )
            continue
        if path_part.endswith("/"):
            if not candidate.is_dir():
                broken.append(
                    (line_index.get(target, 0), target, "directory not found")
                )
        else:
            if not (candidate.exists() and candidate.is_file()):
                # Allow `dir/` style without trailing slash if dir exists.
                if candidate.is_dir():
                    continue
                broken.append(
                    (line_index.get(target, 0), target, "file not found")
                )
    return broken


def _iter_markdown(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        out.append(path)
    return out


def scan_repo(repo_root: Path) -> list[tuple[str, int, str, str]]:
    """Return (rel_path, line_no, target, reason) violations for all md files."""
    results: list[tuple[str, int, str, str]] = []
    for path in _iter_markdown(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        for line_no, target, reason in check_file(path, repo_root):
            results.append((rel, line_no, target, reason))
    return results


def _run_self_test() -> list[str]:
    """Verify the checker on synthetic fixtures.

    Cases:
      1. A markdown file with a valid relative link to an existing file
         passes (no broken links reported).
      2. A markdown file with a broken relative link is reported.
      3. External URL (https://example.com) is skipped, not reported.
      4. Anchor-only link (`#section`) is skipped.
      5. A reference-style link with valid target passes.
      6. Path-traversal that escapes the repo root is reported.
      7. A `[text](target)` example INSIDE inline code spans is NOT
         followed (regression test — see CHANGELOG entry that triggered
         the strip-code-spans fix).
      8. A fenced code block containing example link syntax is NOT
         followed.
    """
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "docs").mkdir()
        (root / "docs" / "target.md").write_text("# Target\n")

        # Case 1+3+4: clean file
        clean = root / "docs" / "clean.md"
        clean.write_text(
            "Link: [target](target.md)\n"
            "External: [ex](https://example.com)\n"
            "Anchor: [a](#section)\n"
        )
        # Case 5: reference-style link
        ref = root / "docs" / "refs.md"
        ref.write_text(
            "Some [text][t1] here.\n\n[t1]: target.md\n"
        )

        # Case 2: broken
        broken = root / "docs" / "broken.md"
        broken.write_text("Bad: [missing](does-not-exist.md)\n")

        # Case 6: path-traversal escape (../../etc/passwd)
        traversal = root / "docs" / "traverse.md"
        traversal.write_text("Bad: [escape](../../etc/passwd)\n")

        # Case 7: link example inside inline code span
        inline_code = root / "docs" / "inline_code.md"
        inline_code.write_text(
            "Documenting our syntax: ``[text](nonexistent.md)`` is the "
            "inline form. The single-backtick `[x](missing.md)` also.\n"
        )

        # Case 8: link example inside fenced code block
        fenced = root / "docs" / "fenced.md"
        fenced.write_text(
            "Example block:\n\n"
            "```markdown\n"
            "[example](does-not-exist.md)\n"
            "```\n\n"
            "End of file.\n"
        )

        results = scan_repo(root)
        rels = {(r, t) for r, _, t, _ in results}

        # Case 1+3+4 (clean.md): no entries
        if any(r == "docs/clean.md" for r, _ in rels):
            failures.append("self-test 1: clean.md should have no broken links")

        # Case 2 (broken.md): does-not-exist.md reported
        if ("docs/broken.md", "does-not-exist.md") not in rels:
            failures.append("self-test 2: broken.md missing target should be reported")

        # Case 5 (refs.md): no entries
        if any(r == "docs/refs.md" for r, _ in rels):
            failures.append("self-test 5: ref-style valid link should pass")

        # Case 6 (traverse.md): reported as outside repo or not found
        if not any(r == "docs/traverse.md" for r, _ in rels):
            failures.append("self-test 6: traversal escape should be reported")

        # Case 7 (inline_code.md): no entries — link examples in inline
        # code must NOT be chased.
        if any(r == "docs/inline_code.md" for r, _ in rels):
            failures.append(
                "self-test 7: inline code-span link example should not be chased"
            )

        # Case 8 (fenced.md): no entries — fenced-code link examples
        # must NOT be chased.
        if any(r == "docs/fenced.md" for r, _ in rels):
            failures.append(
                "self-test 8: fenced code-block link example should not be chased"
            )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        help="Check a single markdown file (skips repo walk).",
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
        print("self-test: ok (8 cases)")

    if args.self_test_only:
        return 0

    if args.path is not None:
        if not args.path.exists():
            print(f"ERROR: path not found: {args.path}", file=sys.stderr)
            return 2
        rel = args.path.resolve().relative_to(repo_root).as_posix()
        violations = check_file(args.path, repo_root)
        for line_no, target, reason in violations:
            print(f"FAIL {rel}:{line_no} → {target} ({reason})", file=sys.stderr)
        return 1 if violations else 0

    violations = scan_repo(repo_root)
    if not violations:
        files_count = len(_iter_markdown(repo_root))
        print(f"ok   no broken internal links across {files_count} markdown files")
        return 0

    print(f"FAIL {len(violations)} broken internal link(s):", file=sys.stderr)
    for rel, line_no, target, reason in violations:
        print(f"  {rel}:{line_no} → {target} ({reason})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
