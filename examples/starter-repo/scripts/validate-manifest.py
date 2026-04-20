#!/usr/bin/env python3
"""Validate the starter-repo's Change Manifest against the upstream schema.

This is the minimal CI shape: load the YAML manifest, load the YAML schema,
validate one against the other. In a real project you would:

1. Copy this script into your own repo (under `.github/scripts/` or similar).
2. Copy the schema file to a stable path inside your own repo.
3. Wire `python3 scripts/validate-manifest.py` into pre-commit + CI.

The intent is to keep CI validation under 30 lines so a team without prior
agent-protocol exposure can read it end-to-end during onboarding.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def main() -> int:
    here = Path(__file__).resolve().parent
    manifest_path = here.parent / "change-manifest.yaml"
    schema_path = here.parent.parent.parent / "schemas" / "change-manifest.schema.yaml"

    with schema_path.open() as fh:
        schema = yaml.safe_load(fh)
    with manifest_path.open() as fh:
        manifest = yaml.safe_load(fh)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))

    if errors:
        print(f"FAIL {manifest_path.name}", file=sys.stderr)
        for err in errors:
            loc = "/".join(str(p) for p in err.path) or "<root>"
            print(f"  at {loc}: {err.message}", file=sys.stderr)
        return 1

    print(f"ok   {manifest_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
