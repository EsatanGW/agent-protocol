#!/usr/bin/env python3
"""Regenerate schemas/*.json from the canonical schemas/*.yaml.

The YAML form stays authoritative (comments, anchors, readability).
The JSON form is generated so runtimes without a YAML parser
(Node / browser tooling, actions/github-script, various CI linters)
can consume the schema directly.

Usage:
    python3 .github/scripts/generate-schema-json.py          # rewrite
    python3 .github/scripts/generate-schema-json.py --check  # drift check

Exit 0 on success (or on --check when no drift).
Exit 1 on --check when regeneration would change the committed JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def _load(path: Path):
    with path.open() as fh:
        return yaml.safe_load(fh)


def _render(doc) -> str:
    # indent=2 + sort_keys=False + trailing newline so diffs stay minimal
    # and ordering matches the YAML source as authored.
    return json.dumps(doc, indent=2, sort_keys=False) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if regeneration would change any committed JSON file",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    schemas_dir = repo_root / "schemas"

    yaml_files = sorted(schemas_dir.glob("*.yaml"))
    if not yaml_files:
        print(f"ERROR: no YAML schemas found under {schemas_dir}", file=sys.stderr)
        return 1

    drift = 0
    for yaml_path in yaml_files:
        json_path = yaml_path.with_suffix(".json")
        rendered = _render(_load(yaml_path))
        rel_yaml = yaml_path.relative_to(repo_root)
        rel_json = json_path.relative_to(repo_root)

        if args.check:
            if not json_path.exists():
                print(f"DRIFT {rel_json}: missing (regenerate)", file=sys.stderr)
                drift += 1
                continue
            existing = json_path.read_text()
            if existing != rendered:
                print(f"DRIFT {rel_json}: out of sync with {rel_yaml}", file=sys.stderr)
                drift += 1
            else:
                print(f"ok    {rel_json}")
        else:
            json_path.write_text(rendered)
            print(f"wrote {rel_json}")

    if args.check and drift:
        print(
            "\nRegenerate with: python3 .github/scripts/generate-schema-json.py",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
