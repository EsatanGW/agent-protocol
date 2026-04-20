"""Suggest the correct phase re-entry given an old and a new manifest.

Implements the decision table in `docs/phase-gate-discipline.md` Rule 6
as a pure function. Given two manifest dicts (an old committed state and
a new in-progress state), returns a list of re-entry suggestions — which
phase to re-open, why, and which manifest fields must be rewritten.

Runtime-neutral: no network, no filesystem outside the two input dicts,
no git operations. Runtimes that want git-diff-aware detection should
assemble (old_manifest, new_manifest) using their own git plumbing and
then call this function.

Usage as a library:

    from suggest_reentry import suggest_reentry

    suggestions = suggest_reentry(old_manifest, new_manifest)
    for s in suggestions:
        print(s["phase"], s["reasons"], s["fields_to_rewrite"])

Usage as a CLI:

    python3 suggest_reentry.py <old-manifest.yaml> <new-manifest.yaml>

Exits:
    0 — no re-entry suggested
    1 — one or more re-entry suggestions emitted
    2 — tool / input error (missing file, unparseable YAML)

Rule 6 decision table (from docs/phase-gate-discipline.md):

    Variation type                          | Re-entry phase
    ----------------------------------------|----------------
    A new surface is being touched           | Phase 0 Clarify
    SoT pattern was mis-classified           | Phase 1 Investigate
    Breaking-change level rises              | Phase 1 Investigate
    Rollback mode rises                      | Phase 2 Plan
    Implementation strategy changes only     | Phase 4 Implement (append)
    Evidence is insufficient per Reviewer    | Phase 4 Implement
    Spec updated mid-change by user          | Phase 0 Clarify (external signal)

The last row ("spec updated") requires an external signal that is not
derivable from two manifest dicts alone. It is therefore not detected
here — the caller provides a separate input for this case. Everything
else is pure-function derivable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# Breaking-change levels as comparable rankings.
_BREAKING_ORDER: dict[str, int] = {
    "L0": 0,
    "L1": 1,
    "L2": 2,
    "L3": 3,
    "L4": 4,
}


def _breaking_rank(level: Any) -> int:
    """Return the rank for a breaking-change level. Missing / unknown = 0."""
    if not isinstance(level, str):
        return 0
    return _BREAKING_ORDER.get(level.upper(), 0)


def _surfaces_of(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    """Return the set of (surface, role) tuples declared in surfaces_touched."""
    out: set[tuple[str, str]] = set()
    for s in manifest.get("surfaces_touched") or []:
        if not isinstance(s, dict):
            continue
        surf = s.get("surface")
        role = s.get("role")
        if isinstance(surf, str) and isinstance(role, str):
            out.add((surf, role))
    return out


def _surface_names(manifest: dict[str, Any]) -> set[str]:
    return {surf for surf, _role in _surfaces_of(manifest)}


def _sot_fingerprint(manifest: dict[str, Any]) -> dict[str, str]:
    """Return {info_name: pattern} for entries in sot_map.

    A pattern change on an existing info_name, or a new info_name without
    a matching old entry, indicates an SoT re-classification.
    """
    out: dict[str, str] = {}
    for sot in manifest.get("sot_map") or []:
        if not isinstance(sot, dict):
            continue
        name = sot.get("info_name")
        pattern = sot.get("pattern")
        if isinstance(name, str):
            out[name] = str(pattern) if pattern is not None else ""
    return out


def _rollback_mode(manifest: dict[str, Any]) -> int:
    rb = manifest.get("rollback") or {}
    if not isinstance(rb, dict):
        return 0
    mode = rb.get("overall_mode") or rb.get("mode")
    try:
        return int(mode) if mode is not None else 0
    except (TypeError, ValueError):
        return 0


def _evidence_fingerprint(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    """Return (type, surface) pairs from evidence_plan — used to detect
    new evidence entries appended after the Reviewer flagged insufficiency.
    """
    out: set[tuple[str, str]] = set()
    for ev in manifest.get("evidence_plan") or []:
        if not isinstance(ev, dict):
            continue
        typ = ev.get("type")
        surf = ev.get("surface")
        if isinstance(typ, str) and isinstance(surf, str):
            out.add((typ, surf))
    return out


def _rejected_evidence(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (type, surface) pairs with status=rejected."""
    out: list[tuple[str, str]] = []
    for ev in manifest.get("evidence_plan") or []:
        if not isinstance(ev, dict):
            continue
        if ev.get("status") == "rejected":
            typ = str(ev.get("type") or "")
            surf = str(ev.get("surface") or "")
            out.append((typ, surf))
    return out


def suggest_reentry(
    old_manifest: dict[str, Any],
    new_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return re-entry suggestions for the diff between two manifest states.

    Each suggestion is a dict with keys:
        phase               — one of "0_clarify", "1_investigate",
                              "2_plan", "4_implement_append",
                              "4_implement_evidence"
        reasons             — list of strings explaining why the phase is
                              suggested
        fields_to_rewrite   — list of manifest field names that Rule 6
                              says must be rewritten at that re-entry
    """
    suggestions: list[dict[str, Any]] = []

    # ─── Row 1 — new surface touched → Phase 0 Clarify ───────────────
    old_surfaces = _surface_names(old_manifest)
    new_surfaces = _surface_names(new_manifest)
    added_surfaces = sorted(new_surfaces - old_surfaces)
    if added_surfaces:
        suggestions.append(
            {
                "phase": "0_clarify",
                "reasons": [
                    f"new surface(s) touched: {', '.join(added_surfaces)}"
                ],
                "fields_to_rewrite": ["surfaces_touched", "evidence_plan"],
            }
        )

    # ─── Row 2 — SoT pattern mis-classified → Phase 1 Investigate ────
    old_sot = _sot_fingerprint(old_manifest)
    new_sot = _sot_fingerprint(new_manifest)
    changed_sot: list[str] = []
    for name, pattern in new_sot.items():
        if name in old_sot and old_sot[name] != pattern:
            changed_sot.append(f"{name} ({old_sot[name]}→{pattern})")
    if changed_sot:
        suggestions.append(
            {
                "phase": "1_investigate",
                "reasons": [
                    f"SoT pattern re-classified: {'; '.join(changed_sot)}"
                ],
                "fields_to_rewrite": ["sot_map", "consumers"],
            }
        )

    # ─── Row 3 — breaking-change level rises → Phase 1 Investigate ───
    old_breaking = (old_manifest.get("breaking_change") or {}).get("level")
    new_breaking = (new_manifest.get("breaking_change") or {}).get("level")
    if _breaking_rank(new_breaking) > _breaking_rank(old_breaking):
        fields = ["breaking_change", "rollback"]
        if _breaking_rank(new_breaking) >= 2:
            fields.append("breaking_change.migration_plan")
        suggestions.append(
            {
                "phase": "1_investigate",
                "reasons": [
                    f"breaking_change.level rose from "
                    f"{old_breaking or 'unset'} to {new_breaking}"
                ],
                "fields_to_rewrite": fields,
            }
        )

    # ─── Row 4 — rollback mode rises → Phase 2 Plan ──────────────────
    old_mode = _rollback_mode(old_manifest)
    new_mode = _rollback_mode(new_manifest)
    if new_mode > old_mode and new_mode >= 1:
        fields = ["rollback"]
        if new_mode == 3:
            fields.extend(["post_delivery", "rollback.compensation_plan"])
        suggestions.append(
            {
                "phase": "2_plan",
                "reasons": [
                    f"rollback.overall_mode rose from {old_mode} to {new_mode}"
                ],
                "fields_to_rewrite": fields,
            }
        )

    # ─── Row 5/6 — evidence deltas → Phase 4 Implement ───────────────
    old_evidence = _evidence_fingerprint(old_manifest)
    new_evidence = _evidence_fingerprint(new_manifest)
    added_evidence = sorted(new_evidence - old_evidence)
    rejected = _rejected_evidence(new_manifest)

    if rejected:
        # Reviewer rejected some evidence — Phase 4 Implement to collect
        # replacement artifacts.
        names = ", ".join(f"{t} on {s}" for t, s in rejected)
        suggestions.append(
            {
                "phase": "4_implement_evidence",
                "reasons": [f"evidence rejected by Reviewer: {names}"],
                "fields_to_rewrite": ["evidence_plan.artifacts"],
            }
        )
    elif added_evidence and not suggestions:
        # Pure implementation-strategy adjustment — evidence was added but
        # no higher-severity field moved. Suggested append-only re-entry
        # at Phase 4.
        suggestions.append(
            {
                "phase": "4_implement_append",
                "reasons": [
                    f"evidence_plan extended without surface/SoT/breaking"
                    f"/rollback change (implementation-strategy adjustment)"
                ],
                "fields_to_rewrite": ["implementation_notes", "scope_deltas"],
            }
        )

    return suggestions


# ─── CLI ─────────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        print(
            "ERROR: PyYAML is required to parse manifest files. "
            "Install with `pip install pyyaml`.",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(2)
    except yaml.YAMLError as exc:
        print(f"ERROR: {path} is not valid YAML: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print(f"ERROR: {path} top-level is not a mapping", file=sys.stderr)
        sys.exit(2)
    return data


def _main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "usage: suggest_reentry.py <old-manifest.yaml> <new-manifest.yaml>",
            file=sys.stderr,
        )
        return 2
    old_path = Path(argv[0])
    new_path = Path(argv[1])
    old_manifest = _load_yaml(old_path)
    new_manifest = _load_yaml(new_path)
    suggestions = suggest_reentry(old_manifest, new_manifest)
    print(json.dumps({"suggestions": suggestions}, indent=2, ensure_ascii=False))
    return 1 if suggestions else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
