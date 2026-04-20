"""Loader + matcher for per-bridge ``docs/bridges/<stack>-surface-map.yaml``.

The surface-map files are the Group-D artifact that unblocks rule 3.2.
This module converts patterns into ``fnmatch``-style globs and answers
the single question rule 3.2 asks: "for this file path, which surfaces
does the bridge say it belongs to?"
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SurfaceMap:
    stack: str
    patterns_by_surface: dict[str, list[str]]

    def surfaces_for_path(self, path: str) -> list[str]:
        matches: list[str] = []
        for surface, patterns in self.patterns_by_surface.items():
            for pat in patterns:
                if _glob_match(path, pat):
                    matches.append(surface)
                    break
        return matches


def _glob_match(path: str, pattern: str) -> bool:
    if "**" in pattern:
        return _globstar_match(path, pattern)
    return fnmatch.fnmatchcase(path, pattern)


def _globstar_match(path: str, pattern: str) -> bool:
    regex = _pattern_to_regex(pattern)
    import re
    return re.fullmatch(regex, path) is not None


def _pattern_to_regex(pattern: str) -> str:
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                j = i + 2
                if j < len(pattern) and pattern[j] == "/":
                    out.append("(?:.*/)?")
                    i = j + 1
                    continue
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
            i += 1
            continue
        if c == "?":
            out.append("[^/]")
            i += 1
            continue
        if c in ".^$+(){}|\\":
            out.append("\\" + c)
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def load_surface_map(path: Path) -> SurfaceMap:
    with path.open("r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    canonical = raw.get("canonical_surfaces") or {}
    extensions = raw.get("stack_extensions") or {}

    patterns: dict[str, list[str]] = {}
    for name, block in canonical.items():
        if isinstance(block, dict):
            patterns[name] = list(block.get("patterns") or [])
    for name, block in extensions.items():
        if isinstance(block, dict):
            patterns[name] = list(block.get("patterns") or [])

    stack = str(raw.get("stack", ""))
    return SurfaceMap(stack=stack, patterns_by_surface=patterns)
