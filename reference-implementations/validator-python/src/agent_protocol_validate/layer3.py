"""Layer 3 — drift detection. Rules 3.1 – 3.5.

3.2 consumes the per-bridge ``docs/bridges/<stack>-surface-map.yaml`` artifact
via :mod:`agent_protocol_validate.surface_map`. 3.4 is a plugin point with a
default cache-file implementation (``.agent-protocol/monitoring-cache.json``);
remote calls stay opt-in behind ``--enable-network``.
"""

from __future__ import annotations

import datetime as _dt
import json
import subprocess
from pathlib import Path
from typing import Any

from .findings import Finding
from .surface_map import SurfaceMap


def check(
    manifest: dict[str, Any],
    *,
    repo_root: Path,
    base_ref: str | None,
    surface_map: SurfaceMap | None = None,
    monitoring_cache: Path | None = None,
    uncontrolled_interface_max_age_days: int = 7,
    today: _dt.date | None = None,
) -> list[Finding]:
    if base_ref is None:
        return []
    today = today or _dt.date.today()

    changed = _git_diff_name_only(repo_root, base_ref)

    findings: list[Finding] = []
    findings.extend(_rule_3_1(manifest, changed))
    if surface_map is not None:
        findings.extend(_rule_3_2(manifest, surface_map, changed))
    findings.extend(_rule_3_3(manifest, surface_map, changed))
    findings.extend(_rule_3_4(manifest, monitoring_cache, uncontrolled_interface_max_age_days, today))
    findings.extend(_rule_3_5(manifest, repo_root, today))
    return findings


def _git_diff_name_only(repo_root: Path, base_ref: str) -> set[str]:
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return set()
    return {line for line in out.stdout.splitlines() if line}


def _rule_3_1(manifest: dict[str, Any], changed: set[str]) -> list[Finding]:
    out: list[Finding] = []
    for sot in manifest.get("sot_map") or []:
        if not isinstance(sot, dict):
            continue
        if sot.get("role_in_change") == "read_only":
            continue
        src = sot.get("source")
        if not isinstance(src, str) or not src or src.startswith(("http://", "https://")):
            continue
        file_part = src.split(":", 1)[0]
        if file_part not in changed:
            out.append(
                Finding(
                    rule_id="drift.declared_sot_not_modified",
                    severity="advisory",
                    detail=f"declared SoT {file_part} not in diff",
                )
            )
    return out


def _rule_3_2(
    manifest: dict[str, Any], surface_map: SurfaceMap, changed: set[str]
) -> list[Finding]:
    out: list[Finding] = []
    for s in manifest.get("surfaces_touched") or []:
        if not isinstance(s, dict) or s.get("role") != "primary":
            continue
        name = s.get("surface")
        if not isinstance(name, str):
            continue
        patterns = surface_map.patterns_by_surface.get(name)
        if not patterns:
            continue
        if not any(name in surface_map.surfaces_for_path(f) for f in changed):
            out.append(
                Finding(
                    rule_id="drift.primary_surface_no_matching_file_change",
                    severity="advisory",
                    detail=(
                        f"surface {name!r} declared primary but no file matching "
                        f"{patterns} changed"
                    ),
                )
            )
    return out


def _rule_3_3(
    manifest: dict[str, Any], surface_map: SurfaceMap | None, changed: set[str]
) -> list[Finding]:
    cross = manifest.get("cross_cutting") or {}
    risk = cross.get("build_time_risk") or {}
    if not risk.get("codegen_touched"):
        return []
    if not risk.get("codegen_artifacts_committed"):
        return []
    if surface_map is None:
        return []
    patterns = surface_map.patterns_by_surface.get("__generated__") or []
    if not patterns:
        return []
    from .surface_map import _glob_match

    if any(any(_glob_match(f, p) for p in patterns) for f in changed):
        return []
    return [
        Finding(
            rule_id="drift.codegen_touched_but_no_generated_diff",
            severity="advisory",
            detail="codegen_touched=true but no generated artifacts in diff",
        )
    ]


def _rule_3_4(
    manifest: dict[str, Any],
    cache_path: Path | None,
    max_age_days: int,
    today: _dt.date,
) -> list[Finding]:
    if not cache_path or not cache_path.exists():
        return []
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(cache, dict):
        return []
    out: list[Finding] = []
    for iface in manifest.get("uncontrolled_interfaces") or []:
        if not isinstance(iface, dict):
            continue
        channel = iface.get("monitoring_channel")
        if not isinstance(channel, str) or not channel:
            continue
        entry = cache.get(channel)
        if not isinstance(entry, dict):
            continue
        stamp = entry.get("last_check")
        try:
            last = _dt.date.fromisoformat(str(stamp)[:10])
        except ValueError:
            continue
        age_days = (today - last).days
        if age_days > max_age_days:
            out.append(
                Finding(
                    rule_id="drift.uncontrolled_interface_not_recently_checked",
                    severity="advisory",
                    detail=(
                        f"monitoring_channel={channel} last checked {age_days}d ago "
                        f"(> {max_age_days}d)"
                    ),
                )
            )
    return out


def _rule_3_5(
    manifest: dict[str, Any], repo_root: Path, today: _dt.date
) -> list[Finding]:
    last_updated = manifest.get("last_updated")
    if not last_updated:
        return []
    try:
        manifest_date = _dt.date.fromisoformat(str(last_updated)[:10])
    except ValueError:
        return []
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return []
    raw = out.stdout.strip()
    if not raw:
        return []
    try:
        latest_commit_date = _dt.date.fromisoformat(raw[:10])
    except ValueError:
        return []
    if manifest_date < latest_commit_date:
        return [
            Finding(
                rule_id="drift.manifest_older_than_latest_code",
                severity="advisory",
                detail=(
                    f"manifest.last_updated={manifest_date} older than latest code "
                    f"commit {latest_commit_date}"
                ),
            )
        ]
    return []
