"""Coverage-focused tests for the language-native validator.

Exercises the four rules the POSIX reference could not implement (2.4,
2.5, 3.2, 3.4) plus a happy-path + waiver sanity check so the exit-code
contract is pinned down.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

from agent_protocol_validate import layer1, layer2, layer3, waivers
from agent_protocol_validate.findings import Report, compute_exit_code
from agent_protocol_validate.loader import find_sibling_manifests, load_yaml
from agent_protocol_validate.surface_map import load_surface_map

FIXTURES = Path(__file__).parent / "fixtures"


def _run_all(path: Path, **kw):
    manifest = load_yaml(path)
    siblings = find_sibling_manifests(path)
    report = Report()
    report.extend(layer1.check(manifest))
    report.extend(layer2.check(manifest, repo_root=path.parent, siblings=siblings, **kw))
    return manifest, report


def test_pass_minimal_has_no_blocking_findings():
    _, report = _run_all(FIXTURES / "pass-minimal.yaml")
    # Pass-minimal touches `artifacts/trace.log` which does not exist on disk;
    # that's an advisory (2.3), not blocking, so the exit code stays at 1 max.
    assert compute_exit_code(report) <= 1
    assert not any(f.severity == "blocking" for f in report.findings)


def test_rule_2_4_detects_direct_cycle():
    _, report = _run_all(FIXTURES / "cycle" / "change-manifest-a.yaml")
    ids = [f.rule_id for f in report.findings]
    assert "decomposition.graph_must_be_acyclic" in ids
    assert compute_exit_code(report) == 2


def test_rule_2_5_fires_when_sibling_is_missing_blocks():
    _, report = _run_all(FIXTURES / "bidirectional-fail" / "change-manifest-a.yaml")
    assert any(
        f.rule_id == "decomposition.relation_must_be_bidirectional"
        for f in report.findings
    )


def test_rule_2_5_silent_when_bidirectional_ok():
    _, report = _run_all(FIXTURES / "bidirectional-pass" / "change-manifest-a.yaml")
    assert not any(
        f.rule_id == "decomposition.relation_must_be_bidirectional"
        for f in report.findings
    )


def test_rule_3_2_fires_when_surface_has_no_matching_file():
    surface_map = load_surface_map(FIXTURES / "surface-map-flutter.yaml")
    manifest = {
        "change_id": "2026-04-20-drift",
        "surfaces_touched": [{"surface": "user", "role": "primary"}],
    }
    findings = layer3._rule_3_2(manifest, surface_map, {"README.md"})
    assert findings and findings[0].rule_id == "drift.primary_surface_no_matching_file_change"


def test_rule_3_2_silent_when_matching_file_changed():
    surface_map = load_surface_map(FIXTURES / "surface-map-flutter.yaml")
    manifest = {
        "change_id": "2026-04-20-drift",
        "surfaces_touched": [{"surface": "user", "role": "primary"}],
    }
    findings = layer3._rule_3_2(manifest, surface_map, {"lib/ui/home_page.dart"})
    assert findings == []


def test_rule_3_4_uses_local_cache(tmp_path: Path):
    cache = tmp_path / "cache.json"
    cache.write_text('{"iface-1": {"last_check": "2026-01-01"}}', encoding="utf-8")
    manifest = {
        "uncontrolled_interfaces": [{"monitoring_channel": "iface-1"}],
    }
    findings = layer3._rule_3_4(
        manifest,
        cache,
        max_age_days=7,
        today=_dt.date(2026, 4, 20),
    )
    assert findings and findings[0].rule_id == "drift.uncontrolled_interface_not_recently_checked"


def test_rule_3_4_silent_when_cache_fresh(tmp_path: Path):
    cache = tmp_path / "cache.json"
    cache.write_text('{"iface-1": {"last_check": "2026-04-19"}}', encoding="utf-8")
    manifest = {
        "uncontrolled_interfaces": [{"monitoring_channel": "iface-1"}],
    }
    findings = layer3._rule_3_4(
        manifest,
        cache,
        max_age_days=7,
        today=_dt.date(2026, 4, 20),
    )
    assert findings == []


def test_waiver_downgrades_blocking_to_waived():
    path = FIXTURES / "waiver" / "change-manifest.yaml"
    manifest = load_yaml(path)
    siblings = find_sibling_manifests(path)
    report = Report()
    report.extend(layer1.check(manifest, today=_dt.date(2026, 4, 20)))
    report.extend(layer2.check(manifest, repo_root=path.parent, siblings=siblings))
    waivers.apply(report.findings, manifest, today=_dt.date(2026, 4, 20))
    waived = [
        f for f in report.findings
        if f.rule_id == "handoff.narrative_required_for_observe"
    ]
    assert waived
    assert all(f.severity == "waived" for f in waived)


@pytest.mark.parametrize(
    "path, expected_pattern",
    [
        ("lib/ui/home_page.dart", "lib/ui/**/*.dart"),
        ("lib/platform/method_channel_bridge.dart", "lib/platform/**/*.dart"),
        ("pubspec.yaml", "pubspec.yaml"),
    ],
)
def test_surface_map_globstar(path, expected_pattern):
    surface_map = load_surface_map(FIXTURES / "surface-map-flutter.yaml")
    assert surface_map.surfaces_for_path(path)
