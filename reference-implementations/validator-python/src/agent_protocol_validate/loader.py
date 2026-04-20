"""Manifest + sibling-manifest loader.

Kept thin on purpose. YAML parsing is delegated to PyYAML; everything else
(schema, graph building, drift) operates on plain dicts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def find_sibling_manifests(manifest_path: Path) -> dict[str, dict[str, Any]]:
    """Return ``{change_id: manifest_dict}`` for every other manifest in
    the same directory. Used for the 2.5 bidirectional-mirror check.
    """
    siblings: dict[str, dict[str, Any]] = {}
    for candidate in sorted(manifest_path.parent.glob("change-manifest*.yaml")):
        if candidate.resolve() == manifest_path.resolve():
            continue
        try:
            data = load_yaml(candidate)
        except yaml.YAMLError:
            continue
        change_id = data.get("change_id")
        if isinstance(change_id, str) and change_id:
            siblings[change_id] = data
    return siblings
