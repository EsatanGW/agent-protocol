#!/usr/bin/env python3
"""Validate that every schema in schemas/*.yaml is itself a well-formed
JSON Schema 2020-12 document.

This is the "schema-of-the-schema" check: it does not validate any
manifest or instance document against the schemas — that is the
validator-python test suite's job. This check only asserts that the
shipped schemas are syntactically valid JSON Schema.

Exit 0 on success, 1 on any schema failing the meta-schema check.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    schemas_dir = repo_root / "schemas"

    schemas = sorted(schemas_dir.glob("*.yaml"))
    if not schemas:
        print(f"ERROR: no schemas found under {schemas_dir}", file=sys.stderr)
        return 1

    failed = 0
    for schema_path in schemas:
        rel = schema_path.relative_to(repo_root)
        try:
            with schema_path.open() as fh:
                doc = yaml.safe_load(fh)
            Draft202012Validator.check_schema(doc)
            print(f"ok  {rel}")
        except Exception as exc:  # noqa: BLE001 - report everything
            print(f"FAIL {rel}: {exc}", file=sys.stderr)
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
