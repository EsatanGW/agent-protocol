"""Unit tests for suggest_reentry — the Rule 6 decision-table implementation.

Each test exercises one row of the decision table in
`docs/phase-gate-discipline.md` Rule 6, plus a happy-path case
(no re-entry suggested) and a multi-trigger case (multiple rows fire).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the sibling module importable without a package install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from suggest_reentry import suggest_reentry  # noqa: E402


# ─── Helpers ─────────────────────────────────────────────────────────


def base_manifest() -> dict:
    """A minimal manifest used as the 'before' baseline in each test."""
    return {
        "change_id": "2026-04-21-test",
        "surfaces_touched": [
            {"surface": "user", "role": "primary"},
        ],
        "sot_map": [
            {"info_name": "OrderStatus", "pattern": "3"},
        ],
        "breaking_change": {"level": "L0"},
        "rollback": {"overall_mode": 1},
        "evidence_plan": [
            {"type": "unit_test", "surface": "user", "status": "collected"},
        ],
    }


def phases_in(suggestions: list[dict]) -> list[str]:
    return [s["phase"] for s in suggestions]


# ─── Row-by-row tests ────────────────────────────────────────────────


def test_no_change_no_suggestions():
    old = base_manifest()
    new = base_manifest()
    assert suggest_reentry(old, new) == []


def test_new_surface_triggers_phase_0_clarify():
    old = base_manifest()
    new = base_manifest()
    new["surfaces_touched"].append({"surface": "information", "role": "primary"})
    out = suggest_reentry(old, new)
    assert "0_clarify" in phases_in(out)
    entry = next(s for s in out if s["phase"] == "0_clarify")
    assert "information" in entry["reasons"][0]
    assert "surfaces_touched" in entry["fields_to_rewrite"]
    assert "evidence_plan" in entry["fields_to_rewrite"]


def test_sot_pattern_change_triggers_phase_1_investigate():
    old = base_manifest()
    new = base_manifest()
    new["sot_map"][0]["pattern"] = "6"  # state-machine instead of enum
    out = suggest_reentry(old, new)
    assert "1_investigate" in phases_in(out)
    entry = next(s for s in out if s["phase"] == "1_investigate")
    assert "OrderStatus" in entry["reasons"][0]
    assert "3→6" in entry["reasons"][0]
    assert "sot_map" in entry["fields_to_rewrite"]


def test_breaking_change_rise_triggers_phase_1_investigate():
    old = base_manifest()
    new = base_manifest()
    new["breaking_change"]["level"] = "L2"
    out = suggest_reentry(old, new)
    entries = [s for s in out if s["phase"] == "1_investigate"]
    assert entries
    assert "L0" in entries[0]["reasons"][0] and "L2" in entries[0]["reasons"][0]
    assert "breaking_change" in entries[0]["fields_to_rewrite"]
    # L2+ should also name the migration_plan field
    assert "breaking_change.migration_plan" in entries[0]["fields_to_rewrite"]


def test_breaking_change_unchanged_does_not_trigger():
    old = base_manifest()
    new = base_manifest()
    # level stays L0 — no suggestion
    out = suggest_reentry(old, new)
    assert not any(
        "breaking_change" in s["reasons"][0] for s in out if s["reasons"]
    )


def test_breaking_change_downgrade_does_not_trigger():
    """Rule 6 only fires on *rise*. Downgrades are a different scenario
    (usually mis-judgment correction) and are not covered by this row."""
    old = base_manifest()
    old["breaking_change"]["level"] = "L2"
    new = base_manifest()  # back to L0
    out = suggest_reentry(old, new)
    assert not any(
        s["phase"] == "1_investigate" and "breaking_change" in s["reasons"][0]
        for s in out
    )


def test_rollback_mode_rise_triggers_phase_2_plan():
    old = base_manifest()
    new = base_manifest()
    new["rollback"]["overall_mode"] = 2
    out = suggest_reentry(old, new)
    assert "2_plan" in phases_in(out)
    entry = next(s for s in out if s["phase"] == "2_plan")
    assert "1 to 2" in entry["reasons"][0]
    assert "rollback" in entry["fields_to_rewrite"]


def test_rollback_mode_3_includes_compensation_and_post_delivery():
    old = base_manifest()
    new = base_manifest()
    new["rollback"]["overall_mode"] = 3
    out = suggest_reentry(old, new)
    entry = next(s for s in out if s["phase"] == "2_plan")
    assert "post_delivery" in entry["fields_to_rewrite"]
    assert "rollback.compensation_plan" in entry["fields_to_rewrite"]


def test_rejected_evidence_triggers_phase_4_evidence():
    old = base_manifest()
    new = base_manifest()
    new["evidence_plan"].append(
        {"type": "integration_test", "surface": "user", "status": "rejected"}
    )
    out = suggest_reentry(old, new)
    assert "4_implement_evidence" in phases_in(out)
    entry = next(s for s in out if s["phase"] == "4_implement_evidence")
    assert "integration_test on user" in entry["reasons"][0]
    assert "evidence_plan.artifacts" in entry["fields_to_rewrite"]


def test_appended_evidence_without_higher_severity_triggers_append():
    old = base_manifest()
    new = base_manifest()
    new["evidence_plan"].append(
        {"type": "integration_test", "surface": "user", "status": "collected"}
    )
    out = suggest_reentry(old, new)
    assert "4_implement_append" in phases_in(out)
    entry = next(s for s in out if s["phase"] == "4_implement_append")
    assert "implementation_notes" in entry["fields_to_rewrite"]
    assert "scope_deltas" in entry["fields_to_rewrite"]


def test_appended_evidence_suppressed_when_higher_severity_also_fires():
    """If breaking_change rose AND evidence was added, we only report the
    higher-severity re-entry (Phase 1). The append-only suggestion is
    noise once a Phase 1 re-entry is already necessary."""
    old = base_manifest()
    new = base_manifest()
    new["breaking_change"]["level"] = "L2"
    new["evidence_plan"].append(
        {"type": "integration_test", "surface": "user", "status": "collected"}
    )
    out = suggest_reentry(old, new)
    assert "1_investigate" in phases_in(out)
    assert "4_implement_append" not in phases_in(out)


def test_multiple_triggers_all_reported():
    """New surface + rollback mode rise → both suggestions emitted so the
    operator can see the full list of affected fields."""
    old = base_manifest()
    new = base_manifest()
    new["surfaces_touched"].append({"surface": "information", "role": "primary"})
    new["rollback"]["overall_mode"] = 2
    out = suggest_reentry(old, new)
    assert "0_clarify" in phases_in(out)
    assert "2_plan" in phases_in(out)
