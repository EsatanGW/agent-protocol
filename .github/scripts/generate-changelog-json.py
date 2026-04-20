#!/usr/bin/env python3
"""Regenerate CHANGELOG.json from the canonical CHANGELOG.md.

CHANGELOG.md stays authoritative (humans edit it); CHANGELOG.json is
generated so release automation, version-consistency checks, and
downstream dashboards get a stable API instead of having to parse
Markdown.

Shape:

    {
      "releases": [
        {
          "version": "1.7.0",
          "date": "2026-04-20",
          "sections": {
            "added":   [{"title": "...", "body": "..."}, ...],
            "changed": [...],
            "fixed":   [...],
            "removed": [...],
            "deprecated": [...],
            "security":   [...],
            "notes":      [...]
          }
        },
        ...
      ]
    }

Known subsections (Added / Changed / Fixed / Removed / Deprecated /
Security) land in their lowercased key. Any other subsection falls
into `notes` with a `subsection` field, so the parser is forgiving —
unknown subsection headings do not fail the build.

Usage:
    python3 .github/scripts/generate-changelog-json.py          # rewrite
    python3 .github/scripts/generate-changelog-json.py --check  # drift check

Exit 0 on success (or on --check when no drift).
Exit 1 on --check when regeneration would change the committed JSON.
Exit 1 on any parse failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_RELEASE_HEADING = re.compile(
    r"^## \[(?P<version>[^\]]+)\](?:\s*-\s*(?P<date>\d{4}-\d{2}-\d{2}))?\s*$"
)
_SUBSECTION_HEADING = re.compile(r"^### (?P<name>.+?)\s*$")
_BULLET_TITLE = re.compile(r"^\s*-\s*\*\*(?P<title>[^*]+?)\*\*\s*(?:—|-)?\s*(?P<body>.*)$")
_BULLET_PLAIN = re.compile(r"^\s*-\s+(?P<body>.+)$")

_KNOWN_SECTIONS = {
    "added", "changed", "fixed", "removed", "deprecated", "security"
}


def _parse(text: str) -> dict:
    releases: list[dict] = []
    current_release: dict | None = None
    current_subsection: str | None = None
    current_bullet: dict | None = None

    def flush_bullet() -> None:
        nonlocal current_bullet
        if current_bullet is None:
            return
        if current_release is None or current_subsection is None:
            current_bullet = None
            return
        sections = current_release["sections"]
        key = current_subsection if current_subsection in _KNOWN_SECTIONS else "notes"
        if key == "notes" and current_subsection not in _KNOWN_SECTIONS:
            current_bullet["subsection"] = current_subsection
        sections.setdefault(key, []).append(current_bullet)
        current_bullet = None

    for raw in text.splitlines():
        line = raw.rstrip()

        m = _RELEASE_HEADING.match(line)
        if m:
            flush_bullet()
            current_release = {
                "version": m.group("version"),
                "date": m.group("date"),
                "sections": {},
            }
            releases.append(current_release)
            current_subsection = None
            continue

        if current_release is None:
            continue

        m = _SUBSECTION_HEADING.match(line)
        if m:
            flush_bullet()
            current_subsection = m.group("name").strip().lower()
            continue

        if current_subsection is None:
            continue

        bt = _BULLET_TITLE.match(raw)
        if bt:
            flush_bullet()
            current_bullet = {
                "title": bt.group("title").strip(),
                "body": bt.group("body").strip(),
            }
            continue

        bp = _BULLET_PLAIN.match(raw)
        if bp:
            flush_bullet()
            current_bullet = {
                "title": None,
                "body": bp.group("body").strip(),
            }
            continue

        if current_bullet is not None and line.strip():
            current_bullet["body"] = (
                (current_bullet["body"] + " " + line.strip()).strip()
            )

    flush_bullet()
    # Drop empty "Unreleased" placeholders so consumers that want the
    # latest versioned release can just take releases[0]. An Unreleased
    # entry with actual bullets is kept.
    pruned = [
        r for r in releases
        if not (r["version"].lower() == "unreleased" and not r["sections"])
    ]
    return {"releases": pruned}


def _render(doc: dict) -> str:
    return json.dumps(doc, indent=2, sort_keys=False, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if regeneration would change CHANGELOG.json",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    md_path = repo_root / "CHANGELOG.md"
    json_path = repo_root / "CHANGELOG.json"

    if not md_path.exists():
        print(f"ERROR: {md_path} not found", file=sys.stderr)
        return 1

    doc = _parse(md_path.read_text())
    if not doc["releases"]:
        print("ERROR: parsed zero releases from CHANGELOG.md", file=sys.stderr)
        return 1

    rendered = _render(doc)

    if args.check:
        if not json_path.exists():
            print(f"DRIFT {json_path.name}: missing (regenerate)", file=sys.stderr)
            return 1
        if json_path.read_text() != rendered:
            print(
                f"DRIFT {json_path.name}: out of sync with CHANGELOG.md\n"
                "Regenerate with: python3 .github/scripts/generate-changelog-json.py",
                file=sys.stderr,
            )
            return 1
        print(f"ok    {json_path.name}")
        return 0

    json_path.write_text(rendered)
    print(f"wrote {json_path.name} ({len(doc['releases'])} releases)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
