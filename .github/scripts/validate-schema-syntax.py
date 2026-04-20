#!/usr/bin/env python3
"""Validate that every schema in schemas/ is a well-formed JSON Schema
2020-12 document.

Both the canonical YAML form (`*.yaml`) and the generated JSON form
(`*.json`) are checked. The generator in `generate-schema-json.py`
keeps the two in sync; this check ensures both are individually
meta-valid so a consumer reading either form gets a valid schema.

This is the "schema-of-the-schema" check: it does not validate any
manifest or instance document against the schemas — that is the
validator test suite's job.

Exit 0 on success, 1 on any schema failing the meta-schema check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def _load(path: Path):
    if path.suffix == ".json":
        with path.open() as fh:
            return json.load(fh)
    with path.open() as fh:
        return yaml.safe_load(fh)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    schemas_dir = repo_root / "schemas"

    schemas = sorted(
        list(schemas_dir.glob("*.yaml")) + list(schemas_dir.glob("*.json"))
    )
    if not schemas:
        print(f"ERROR: no schemas found under {schemas_dir}", file=sys.stderr)
        return 1

    failed = 0
    for schema_path in schemas:
        rel = schema_path.relative_to(repo_root)
        try:
            doc = _load(schema_path)
            Draft202012Validator.check_schema(doc)
            print(f"ok  {rel}")
        except Exception as exc:  # noqa: BLE001 - report everything
            print(f"FAIL {rel}: {exc}", file=sys.stderr)
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
