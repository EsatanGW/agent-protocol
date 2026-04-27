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


# ─── Rule 2.11 — evidence tier floor under high-severity conditions ─────

RULE_2_11_ID = "evidence.critical_required_for_high_severity"


def _manifest_with(
    *,
    breaking_level: str = "L0",
    rollback_mode: int = 1,
    surfaces: list[dict] | None = None,
    evidence: list[dict] | None = None,
) -> dict:
    return {
        "change_id": "2026-04-21-rule-2-11-test",
        "breaking_change": {"level": breaking_level},
        "rollback": {"overall_mode": rollback_mode},
        "surfaces_touched": surfaces or [{"surface": "user", "role": "primary"}],
        "evidence_plan": evidence or [],
    }


def test_rule_2_11_fires_on_l2_without_critical():
    manifest = _manifest_with(
        breaking_level="L2",
        evidence=[{"type": "unit_test", "surface": "user", "status": "collected", "tier": "standard"}],
    )
    findings = layer2._rule_2_11(manifest)
    assert any(f.rule_id == RULE_2_11_ID and f.severity == "blocking" for f in findings)


def test_rule_2_11_fires_on_mode_3_without_critical():
    manifest = _manifest_with(
        rollback_mode=3,
        evidence=[{"type": "unit_test", "surface": "user", "status": "collected"}],  # no tier == standard
    )
    findings = layer2._rule_2_11(manifest)
    assert any(f.rule_id == RULE_2_11_ID for f in findings)


def test_rule_2_11_fires_on_compliance_primary_without_critical():
    manifest = _manifest_with(
        surfaces=[{"surface": "compliance", "role": "primary"}],
        evidence=[{"type": "changelog_entry", "surface": "compliance", "status": "planned"}],
    )
    findings = layer2._rule_2_11(manifest)
    assert findings and findings[0].rule_id == RULE_2_11_ID


def test_rule_2_11_silent_when_critical_present():
    manifest = _manifest_with(
        breaking_level="L3",
        rollback_mode=3,
        evidence=[
            {"type": "unit_test", "surface": "user", "status": "collected", "tier": "standard"},
            {"type": "migration_dry_run", "surface": "information", "status": "collected", "tier": "critical"},
        ],
    )
    findings = layer2._rule_2_11(manifest)
    assert findings == []


def test_rule_2_11_silent_when_no_high_severity_condition():
    """Backward compat: L0 / Mode 1 / non-high-risk surface with no tier field
    on any evidence entry (pre-1.8 manifest shape) must not trigger the rule.
    """
    manifest = _manifest_with(
        breaking_level="L0",
        rollback_mode=1,
        surfaces=[{"surface": "user", "role": "primary"}],
        evidence=[{"type": "unit_test", "surface": "user", "status": "collected"}],
    )
    findings = layer2._rule_2_11(manifest)
    assert findings == []


def test_rule_2_11_silent_when_high_risk_surface_is_not_primary():
    """A high-risk surface in the `consumer` role does not trigger 2.11."""
    manifest = _manifest_with(
        surfaces=[
            {"surface": "user", "role": "primary"},
            {"surface": "compliance", "role": "consumer"},
        ],
        evidence=[{"type": "unit_test", "surface": "user", "status": "collected"}],
    )
    findings = layer2._rule_2_11(manifest)
    assert findings == []


def _write_manifest_lines(tmp_path: Path, line_count: int) -> Path:
    """Create a synthetic manifest file of the requested line count for
    Rule 2.12 size-ceiling tests. Content is irrelevant for the rule (it
    measures lines, not parses YAML); a header + N filler lines suffice.
    """
    p = tmp_path / "fake-manifest.yaml"
    body = "change_id: 'fake'\n"
    body += "\n".join(f"# filler line {i}" for i in range(line_count - 1))
    body += "\n"
    p.write_text(body, encoding="utf-8")
    return p


def test_rule_2_12_silent_within_budget(tmp_path: Path):
    p = _write_manifest_lines(tmp_path, 1000)
    findings = layer2._rule_2_12(p)
    assert findings == []


def test_rule_2_12_silent_at_advisory_boundary(tmp_path: Path):
    p = _write_manifest_lines(tmp_path, 1500)
    findings = layer2._rule_2_12(p)
    assert findings == []


def test_rule_2_12_advisory_fires_above_1500(tmp_path: Path):
    p = _write_manifest_lines(tmp_path, 1700)
    findings = layer2._rule_2_12(p)
    assert len(findings) == 1
    assert findings[0].rule_id == "manifest.size_within_ceiling"
    assert findings[0].severity == "advisory"
    assert "1700" in findings[0].detail


def test_rule_2_12_advisory_at_blocking_boundary(tmp_path: Path):
    p = _write_manifest_lines(tmp_path, 2000)
    findings = layer2._rule_2_12(p)
    assert len(findings) == 1
    assert findings[0].severity == "advisory"


def test_rule_2_12_blocking_fires_above_2000(tmp_path: Path):
    p = _write_manifest_lines(tmp_path, 2100)
    findings = layer2._rule_2_12(p)
    assert len(findings) == 1
    assert findings[0].rule_id == "manifest.size_within_ceiling"
    assert findings[0].severity == "blocking"
    assert "2100" in findings[0].detail


def test_rule_2_12_missing_path_returns_empty():
    findings = layer2._rule_2_12(Path("/nonexistent/path/manifest.yaml"))
    assert findings == []


# ─── Rule 2.13 — dispatch-class binding (schema-enforced via Layer 1) ────────
#
# The dispatch-class binding rule is enforced at Layer 1 via a JSON Schema
# conditional under sot_map[*].allOf (introduced in 1.29.0). These tests
# exercise the schema conditional directly via layer1._run_jsonschema and the
# loaded schema, confirming the six cases specified in the evidence_plan.
#
# Layer 2 needs no new _rule_2_13() function because the rule is pure-schema
# (AS-2 spike outcome: lowercase regex passes both jsonschema + check-jsonschema).

RULE_DISPATCH_ID = "schema.violation"

_DISPATCH_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "schemas" / "change-manifest.schema.yaml"
)


def _sot_entry(**kwargs) -> dict:
    """Build a minimal sot_map entry with required fields, overridable via kwargs."""
    base = {
        "info_name": "order_status",
        "pattern": 2,
        "source": "lib/model.dart",
        "consumers": [{"name": "app", "kind": "code"}],
        "desync_risk": "low",
    }
    base.update(kwargs)
    return base


def _manifest_with_sot(sot_entry: dict) -> dict:
    return {
        "change_id": "2026-04-27-dispatch-binding-test",
        "title": "test",
        "phase": "plan",
        "status": "proposed",
        "last_updated": "2026-04-27T00:00:00Z",
        "authors": [{"name": "tester", "role": "human", "identifier": "t@t.com"}],
        "surfaces_touched": [{"surface": "information", "role": "primary"}],
        "sot_map": [sot_entry],
        "cross_cutting": {
            "security": {"impact": "none"},
            "performance": {"impact": "none"},
            "observability": {"impact": "none"},
            "testability": {"impact": "none"},
            "error_handling": {"impact": "none"},
            "build_time_risk": {"impact": "none"},
        },
        "breaking_change": {"level": "L0", "self_assessed_vs_worst_case": "matches"},
        "rollback": {"overall_mode": 1},
        "evidence_plan": [
            {"type": "contract_test", "surface": "information", "status": "planned", "summary": "x"}
        ],
    }


@pytest.fixture(scope="module")
def dispatch_schema():
    """Load the schema once per module; skip tests if schema file absent."""
    if not _DISPATCH_SCHEMA_PATH.exists():
        pytest.skip(f"schema not found at {_DISPATCH_SCHEMA_PATH}")
    import yaml
    with open(_DISPATCH_SCHEMA_PATH) as f:
        return yaml.safe_load(f)


def _run_schema_check(manifest: dict, schema: dict) -> list:
    """Return schema violations for the manifest."""
    return layer1._run_jsonschema(manifest, schema)


def test_dispatch_binding_case1_no_match_silent(dispatch_schema):
    """(1) info_name='lib/foo.dart' — does not match heuristic; pattern:2 is silent."""
    manifest = _manifest_with_sot(_sot_entry(info_name="lib/foo.dart", pattern=2))
    findings = _run_schema_check(manifest, dispatch_schema)
    dispatch_findings = [f for f in findings if "pattern" in f.detail and "9" in f.detail]
    assert dispatch_findings == [], f"Unexpected dispatch finding: {dispatch_findings}"


def test_dispatch_binding_case2_match_blocks(dispatch_schema):
    """(2) info_name='country_scaffold_provider', pattern:2 — rule fires."""
    manifest = _manifest_with_sot(
        _sot_entry(info_name="country_scaffold_provider", pattern=2)
    )
    findings = _run_schema_check(manifest, dispatch_schema)
    assert any(RULE_DISPATCH_ID in f.rule_id and "9" in f.detail for f in findings), (
        "Expected dispatch-binding schema violation for pattern:2 with dispatcher name"
    )


def test_dispatch_binding_case3_match_pattern9_silent(dispatch_schema):
    """(3) info_name='country_scaffold_provider', pattern:9 + variant_resolution — silent."""
    entry = _sot_entry(
        info_name="country_scaffold_provider",
        pattern=9,
        variant_resolution={
            "candidates": ["PH scaffold", "VN scaffold"],
            "resolution_rule": "switch on countryTheme",
        },
    )
    manifest = _manifest_with_sot(entry)
    findings = _run_schema_check(manifest, dispatch_schema)
    dispatch_findings = [f for f in findings if "9" in f.detail and "pattern" in f.detail]
    assert dispatch_findings == [], f"Unexpected dispatch finding: {dispatch_findings}"


def test_dispatch_binding_case4_opt_out_with_rationale_silent(dispatch_schema):
    """(4) info_name matches, pattern:2, dispatch_binding_opt_out:true + rationale — silent."""
    entry = _sot_entry(
        info_name="country_scaffold_provider",
        pattern=2,
        dispatch_binding_opt_out=True,
        opt_out_rationale="This entry is a config-flag selector, not a variant resolver.",
    )
    manifest = _manifest_with_sot(entry)
    findings = _run_schema_check(manifest, dispatch_schema)
    dispatch_findings = [
        f for f in findings
        if "9" in f.detail and "pattern" in f.detail
    ]
    assert dispatch_findings == [], f"Unexpected finding with opt-out: {dispatch_findings}"


def test_dispatch_binding_case5_opt_out_empty_rationale_blocks(dispatch_schema):
    """(5) info_name matches, dispatch_binding_opt_out:true, opt_out_rationale:'' — fires."""
    entry = _sot_entry(
        info_name="country_scaffold_provider",
        pattern=2,
        dispatch_binding_opt_out=True,
        opt_out_rationale="",
    )
    manifest = _manifest_with_sot(entry)
    findings = _run_schema_check(manifest, dispatch_schema)
    assert any("non-empty" in f.detail or "minLength" in f.detail or "should be non-empty" in f.detail for f in findings), (
        f"Expected empty-rationale schema violation; got: {[f.detail for f in findings]}"
    )


def test_dispatch_binding_case6_false_positive_boundary_silent(dispatch_schema):
    """(6) info_name='locale_dispatcher_test_helper' — suffix is _test_helper, not locale_dispatcher; silent."""
    manifest = _manifest_with_sot(
        _sot_entry(info_name="locale_dispatcher_test_helper", pattern=2)
    )
    findings = _run_schema_check(manifest, dispatch_schema)
    dispatch_findings = [f for f in findings if "9" in f.detail and "pattern" in f.detail]
    assert dispatch_findings == [], (
        f"False-positive: locale_dispatcher_test_helper should not match suffix heuristic; got: {dispatch_findings}"
    )
