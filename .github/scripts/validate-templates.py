#!/usr/bin/env python3
"""Validate every manifest example under templates/ against
schemas/change-manifest.schema.yaml.

Templates are the repo's worked examples; if one drifts from the
schema, every reader who copies it ends up producing an invalid
manifest. This check catches drift before release.

Exit 0 on success, 1 if any template fails validation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / "schemas" / "change-manifest.schema.yaml"
    templates_dir = repo_root / "templates"

    with schema_path.open() as fh:
        schema = yaml.safe_load(fh)

    validator = Draft202012Validator(schema)

    templates = sorted(templates_dir.glob("change-manifest.example-*.yaml"))
    if not templates:
        print(f"ERROR: no manifest templates under {templates_dir}", file=sys.stderr)
        return 1

    failed = 0
    for tpl in templates:
        rel = tpl.relative_to(repo_root)
        with tpl.open() as fh:
            docs = list(yaml.safe_load_all(fh))
        # Multi-doc YAML is legitimate for templates that show a manifest
        # evolving across phases (e.g. the multi-agent handoff example).
        # Validate each document independently.
        per_doc_errors = []
        for idx, doc in enumerate(docs):
            if doc is None:
                continue
            errs = sorted(validator.iter_errors(doc), key=lambda e: e.path)
            if errs:
                per_doc_errors.append((idx, errs))
        if per_doc_errors:
            failed += 1
            print(f"FAIL {rel}", file=sys.stderr)
            for idx, errs in per_doc_errors:
                prefix = f"doc[{idx}] " if len(docs) > 1 else ""
                for err in errs:
                    loc = "/".join(str(p) for p in err.path) or "<root>"
                    print(f"  {prefix}at {loc}: {err.message}", file=sys.stderr)
        else:
            suffix = f" ({len(docs)} docs)" if len(docs) > 1 else ""
            print(f"ok   {rel}{suffix}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
