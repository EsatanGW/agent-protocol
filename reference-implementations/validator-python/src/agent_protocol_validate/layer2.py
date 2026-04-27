"""Layer 2 — cross-reference consistency. Rules 2.1 – 2.12.

2.4 (decomposition acyclicity) and 2.5 (depends_on / blocks mirror) are the
two rules flagged as gaps in the POSIX reference; both are implemented here.
2.11 (evidence tier floor under high-severity conditions) was added in the
1.8 schema revision and is enforced identically across all three validators.
2.12 (manifest size within ceiling) was added in 1.26.0 to mechanically enforce
the prose ceiling at docs/change-manifest-spec.md §State-snapshot discipline
§Manifest size ceiling. Counts lines in the manifest file as the
tokenizer-agnostic proxy for the ~25,000-token AI-runtime read ceiling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .findings import Finding


def check(
    manifest: dict[str, Any],
    *,
    repo_root: Path,
    siblings: dict[str, dict[str, Any]] | None = None,
    manifest_path: Path | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    siblings = siblings or {}

    findings.extend(_rule_2_1(manifest))
    findings.extend(_rule_2_2(manifest, repo_root))
    findings.extend(_rule_2_3(manifest, repo_root))
    findings.extend(_rule_2_4(manifest, siblings))
    findings.extend(_rule_2_5(manifest, siblings))
    findings.extend(_rule_2_6(manifest))
    findings.extend(_rule_2_7(manifest))
    findings.extend(_rule_2_8(manifest))
    findings.extend(_rule_2_9(manifest))
    findings.extend(_rule_2_10(manifest))
    findings.extend(_rule_2_11(manifest))
    if manifest_path is not None:
        findings.extend(_rule_2_12(manifest_path))

    return findings


def _looks_like_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith(("http://", "https://")):
        return False
    return "/" in value or "." in value


def _rule_2_1(manifest: dict[str, Any]) -> list[Finding]:
    primary = {
        s.get("surface")
        for s in (manifest.get("surfaces_touched") or [])
        if isinstance(s, dict) and s.get("role") == "primary"
    }
    evidence_surfaces = {
        e.get("surface")
        for e in (manifest.get("evidence_plan") or [])
        if isinstance(e, dict)
    }
    missing = primary - evidence_surfaces - {None}
    return [
        Finding(
            rule_id="evidence.primary_surface_required",
            severity="blocking",
            detail=f"primary surface {s!r} has no evidence_plan entry",
        )
        for s in sorted(missing)
    ]


def _rule_2_2(manifest: dict[str, Any], repo_root: Path) -> list[Finding]:
    out: list[Finding] = []
    for sot in manifest.get("sot_map") or []:
        if not isinstance(sot, dict):
            continue
        src = sot.get("source")
        if not _looks_like_path(src):
            continue
        file_part = str(src).split(":", 1)[0]
        if not (repo_root / file_part).exists():
            out.append(
                Finding(
                    rule_id="sot.source_file_missing",
                    severity="blocking",
                    detail=f"{file_part} referenced in sot_map but not found",
                )
            )
    return out


def _rule_2_3(manifest: dict[str, Any], repo_root: Path) -> list[Finding]:
    out: list[Finding] = []
    for ev in manifest.get("evidence_plan") or []:
        if not isinstance(ev, dict) or ev.get("status") != "collected":
            continue
        loc = ev.get("artifact_location")
        if not loc:
            out.append(
                Finding(
                    rule_id="evidence.collected_requires_location",
                    severity="blocking",
                    detail="status=collected with empty artifact_location",
                )
            )
            continue
        if isinstance(loc, str) and _looks_like_path(loc):
            if not (repo_root / loc).exists():
                out.append(
                    Finding(
                        rule_id="evidence.artifact_missing",
                        severity="advisory",
                        detail=f"artifact_location {loc} does not resolve",
                    )
                )
    return out


def _rule_2_4(
    manifest: dict[str, Any], siblings: dict[str, dict[str, Any]]
) -> list[Finding]:
    graph: dict[str, set[str]] = {}

    def edges_for(m: dict[str, Any]) -> set[str]:
        deps = m.get("depends_on") or []
        if isinstance(deps, str):
            deps = [deps]
        return {d for d in deps if isinstance(d, str)}

    self_id = manifest.get("change_id")
    if isinstance(self_id, str) and self_id:
        graph[self_id] = edges_for(manifest)
    for cid, m in siblings.items():
        graph[cid] = edges_for(m)

    cycle = _find_cycle(graph)
    if cycle:
        return [
            Finding(
                rule_id="decomposition.graph_must_be_acyclic",
                severity="blocking",
                detail="cycle: " + " -> ".join(cycle),
            )
        ]
    return []


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    parent: dict[str, str | None] = {node: None for node in graph}

    def dfs(start: str) -> list[str] | None:
        stack: list[tuple[str, iter]] = [(start, iter(sorted(graph.get(start, set()))))]
        color[start] = GRAY
        while stack:
            node, it = stack[-1]
            try:
                nxt = next(it)
            except StopIteration:
                color[node] = BLACK
                stack.pop()
                continue
            if nxt not in graph:
                continue
            if color[nxt] == GRAY:
                cyc = [nxt, node]
                cur = parent[node]
                while cur is not None and cur != nxt:
                    cyc.append(cur)
                    cur = parent[cur]
                cyc.append(nxt)
                cyc.reverse()
                return cyc
            if color[nxt] == WHITE:
                color[nxt] = GRAY
                parent[nxt] = node
                stack.append((nxt, iter(sorted(graph.get(nxt, set())))))
        return None

    for node in sorted(graph):
        if color[node] == WHITE:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


def _rule_2_5(
    manifest: dict[str, Any], siblings: dict[str, dict[str, Any]]
) -> list[Finding]:
    out: list[Finding] = []
    self_id = manifest.get("change_id")
    if not isinstance(self_id, str):
        return out
    for dep_id in manifest.get("depends_on") or []:
        if not isinstance(dep_id, str) or dep_id not in siblings:
            continue
        blocks = siblings[dep_id].get("blocks") or []
        if self_id not in blocks:
            out.append(
                Finding(
                    rule_id="decomposition.relation_must_be_bidirectional",
                    severity="advisory",
                    detail=f"{dep_id}.blocks is missing {self_id}",
                )
            )
    return out


def _rule_2_6(manifest: dict[str, Any]) -> list[Finding]:
    breaking = manifest.get("breaking_change") or {}
    level = breaking.get("level")
    if level in ("L3", "L4"):
        has_timeline = bool(breaking.get("deprecation_timeline"))
        has_deprecation = bool(breaking.get("deprecation"))
        if not (has_timeline or has_deprecation):
            return [
                Finding(
                    rule_id="breaking_change.l3_l4_requires_deprecation",
                    severity="blocking",
                    detail=(
                        f"breaking_change.level={level} with neither "
                        "deprecation_timeline nor deprecation marker"
                    ),
                )
            ]
    return []


def _rule_2_7(manifest: dict[str, Any]) -> list[Finding]:
    rollback = manifest.get("rollback") or {}
    mode = rollback.get("overall_mode") or rollback.get("mode")
    if mode == 3 and not rollback.get("compensation_plan"):
        return [
            Finding(
                rule_id="rollback.mode_3_requires_compensation",
                severity="blocking",
                detail="rollback.overall_mode=3 with no compensation_plan",
            )
        ]
    return []


def _rule_2_8(manifest: dict[str, Any]) -> list[Finding]:
    if manifest.get("phase") != "deliver" and manifest.get("status") != "delivered":
        return []
    approvals = [
        a
        for a in (manifest.get("approvals") or [])
        if isinstance(a, dict) and a.get("role") == "human"
    ]
    if not approvals:
        return [
            Finding(
                rule_id="approval.human_required_for_delivery",
                severity="blocking",
                detail="phase=deliver but no approvals with role=human",
            )
        ]
    return []


def _rule_2_9(manifest: dict[str, Any]) -> list[Finding]:
    has_experience = any(
        isinstance(s, dict) and s.get("surface") == "experience"
        for s in (manifest.get("surfaces_touched") or [])
    )
    if has_experience and not manifest.get("playtest"):
        return [
            Finding(
                rule_id="playtest.required_for_experience_surface",
                severity="blocking",
                detail="experience surface touched without playtest block",
            )
        ]
    return []


def _rule_2_10(manifest: dict[str, Any]) -> list[Finding]:
    if manifest.get("phase") == "observe" and not manifest.get("handoff_narrative"):
        return [
            Finding(
                rule_id="handoff.narrative_required_for_observe",
                severity="blocking",
                detail="phase=observe requires handoff_narrative",
            )
        ]
    return []


_HIGH_RISK_SURFACES = frozenset({"compliance", "real_world", "experience"})
_HIGH_BREAKING_LEVELS = frozenset({"L2", "L3", "L4"})


def _rule_2_11(manifest: dict[str, Any]) -> list[Finding]:
    """At least one tier=critical evidence is required when high-severity
    conditions apply: breaking_change >= L2, rollback mode 3, or a high-risk
    surface (compliance / real_world / experience) touched with role=primary.

    A missing `tier` field is treated as "standard" — pre-1.8 manifests remain
    valid. The rule fires only when the manifest itself declares high severity.
    """
    breaking = manifest.get("breaking_change") or {}
    rollback = manifest.get("rollback") or {}
    rollback_mode = rollback.get("overall_mode") or rollback.get("mode")

    high_risk_surface_primary = any(
        isinstance(s, dict)
        and s.get("role") == "primary"
        and s.get("surface") in _HIGH_RISK_SURFACES
        for s in (manifest.get("surfaces_touched") or [])
    )

    high_severity = (
        breaking.get("level") in _HIGH_BREAKING_LEVELS
        or rollback_mode == 3
        or high_risk_surface_primary
    )
    if not high_severity:
        return []

    has_critical = any(
        isinstance(ev, dict) and ev.get("tier") == "critical"
        for ev in (manifest.get("evidence_plan") or [])
    )
    if has_critical:
        return []

    triggers = []
    if breaking.get("level") in _HIGH_BREAKING_LEVELS:
        triggers.append(f"breaking_change.level={breaking.get('level')}")
    if rollback_mode == 3:
        triggers.append("rollback.overall_mode=3")
    if high_risk_surface_primary:
        triggers.append("high-risk surface touched with role=primary")
    return [
        Finding(
            rule_id="evidence.critical_required_for_high_severity",
            severity="blocking",
            detail=(
                "at least one evidence_plan entry must be tier=critical when "
                + " / ".join(triggers)
            ),
        )
    ]


_CEILING_BLOCKING_LINES = 2000
_CEILING_ADVISORY_LINES = 1500


def _rule_2_12(manifest_path: Path) -> list[Finding]:
    """Manifest size within ceiling. Mechanical enforcement of the prose
    ceiling at docs/change-manifest-spec.md §State-snapshot discipline
    §Manifest size ceiling. Lines are the tokenizer-agnostic proxy for the
    ~25,000-token AI-runtime read ceiling (typical 12-13 tokens per line of
    YAML manifest content).

    Severity ladder:
      > 2000 lines → blocking
      1500–2000   → advisory
      ≤ 1500      → none
    """
    try:
        line_count = sum(1 for _ in manifest_path.open("r", encoding="utf-8"))
    except OSError:
        return []

    if line_count > _CEILING_BLOCKING_LINES:
        return [
            Finding(
                rule_id="manifest.size_within_ceiling",
                severity="blocking",
                detail=(
                    f"manifest is {line_count} lines; ceiling is "
                    f"{_CEILING_BLOCKING_LINES} (≈25,000 tokens). Compact in "
                    "place (move verbose narrative into structured note "
                    "fields) or split via part_of per "
                    "docs/change-manifest-spec.md §Manifest size ceiling. "
                    "grep / offset-read workarounds are explicitly prohibited."
                ),
            )
        ]
    if line_count > _CEILING_ADVISORY_LINES:
        return [
            Finding(
                rule_id="manifest.size_within_ceiling",
                severity="advisory",
                detail=(
                    f"manifest is {line_count} lines; approaching ceiling at "
                    f"{_CEILING_BLOCKING_LINES}. Consider compacting "
                    "structured note fields or splitting via part_of before "
                    "the next session boundary."
                ),
            )
        ]
    return []
