"""Command-line entry point.

Usage
-----
    python -m agent_protocol_validate <manifest> [options]

Options
-------
    --schema PATH           JSON Schema file (YAML or JSON). Enables rule 1.1.
    --surface-map PATH      Per-bridge surface-map.yaml. Enables rule 3.2.
    --repo-root PATH        Repository root. Defaults to CWD.
    --base-ref REF          Git base ref for drift detection. Enables Layer 3.
    --monitoring-cache PATH Local cache file for rule 3.4. Defaults to
                            <repo-root>/.agent-protocol/monitoring-cache.json.
    --uncontrolled-max-age  Staleness threshold in days for rule 3.4 (default 7).
    --report PATH           Write JSON report to PATH. Defaults to stdout.

Exit codes
----------
    0 — every finding waived or no findings.
    1 — at least one advisory finding, no blocking findings.
    2 — at least one blocking finding that was not waived.
    64 — harness / argument error (stderr explains).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import layer1, layer2, layer3, waivers
from .findings import Report, compute_exit_code
from .loader import find_sibling_manifests, load_yaml
from .surface_map import load_surface_map


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-protocol-validate")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--schema", type=Path, default=None)
    parser.add_argument("--surface-map", dest="surface_map", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--monitoring-cache", type=Path, default=None)
    parser.add_argument("--uncontrolled-max-age", type=int, default=7)
    parser.add_argument("--report", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.manifest.exists():
        print(f"manifest not found: {args.manifest}", file=sys.stderr)
        return 64

    manifest = load_yaml(args.manifest)
    schema = layer1.load_schema(args.schema) if args.schema else None
    surface_map = load_surface_map(args.surface_map) if args.surface_map else None
    siblings = find_sibling_manifests(args.manifest)

    repo_root = args.repo_root.resolve()
    cache_path = args.monitoring_cache
    if cache_path is None:
        default = repo_root / ".agent-protocol" / "monitoring-cache.json"
        cache_path = default if default.exists() else None

    report = Report()
    report.extend(layer1.check(manifest, schema=schema))
    report.extend(layer2.check(manifest, repo_root=repo_root, siblings=siblings, manifest_path=args.manifest))
    report.extend(
        layer3.check(
            manifest,
            repo_root=repo_root,
            base_ref=args.base_ref,
            surface_map=surface_map,
            monitoring_cache=cache_path,
            uncontrolled_interface_max_age_days=args.uncontrolled_max_age,
        )
    )
    waivers.apply(report.findings, manifest)

    payload = json.dumps(report.as_dict(), indent=2, sort_keys=True)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    else:
        print(payload)

    return compute_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
