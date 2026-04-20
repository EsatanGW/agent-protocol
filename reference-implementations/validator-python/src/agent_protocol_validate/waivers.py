"""Waiver filtering.

A finding whose ``rule_id`` matches an active, human-authorized, unexpired
waiver is downgraded to ``severity="waived"`` so the exit-code mapper
ignores it. Expired or AI-authored waivers have no effect.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any

from .findings import Finding


def apply(
    findings: list[Finding],
    manifest: dict[str, Any],
    *,
    today: _dt.date | None = None,
) -> list[Finding]:
    today = today or _dt.date.today()
    waivers = manifest.get("waivers") or []
    active: dict[str, dict[str, Any]] = {}
    for w in waivers:
        if not isinstance(w, dict):
            continue
        if w.get("approver_role") != "human":
            continue
        expires = w.get("expires_at")
        expires_date = _coerce_date(expires)
        if expires_date is None or expires_date < today:
            continue
        rule_id = w.get("rule_id")
        if isinstance(rule_id, str):
            active[rule_id] = w
    if not active:
        return findings
    for f in findings:
        w = active.get(f.rule_id)
        if w is not None:
            f.severity = "waived"
            f.waiver_rule_id = w.get("rule_id")
            f.waiver_expires = str(w.get("expires_at"))
    return findings


def _coerce_date(value: Any) -> _dt.date | None:
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, str):
        try:
            return _dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return _dt.date.fromisoformat(value[:10])
            except ValueError:
                return None
    return None
