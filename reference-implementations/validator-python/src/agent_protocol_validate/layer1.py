"""Layer 1 — structural validity. Rules 1.1 – 1.4."""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any

from .findings import Finding


_CHANGE_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$")
_ISO_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}"
    r"(?:[T ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?(?:Z|[+-][0-9]{2}:?[0-9]{2})?)?$"
)


def check(
    manifest: dict[str, Any],
    *,
    schema: dict[str, Any] | None = None,
    today: _dt.date | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    today = today or _dt.date.today()

    # 1.1 JSON Schema — delegated when a schema is supplied.
    if schema is not None:
        findings.extend(_run_jsonschema(manifest, schema))

    # 1.2 change_id format
    change_id = manifest.get("change_id", "")
    if not isinstance(change_id, str) or not _CHANGE_ID_RE.match(change_id):
        findings.append(
            Finding(
                rule_id="change_id.format",
                severity="blocking",
                detail=f"change_id={change_id!r} does not match YYYY-MM-DD-slug",
            )
        )

    # 1.3 timestamps must be ISO 8601 where present
    for field_name in ("last_updated", "collected_at", "granted_at", "timestamp", "resolved_at"):
        for loc, value in _iter_field(manifest, field_name):
            if value is None or value == "":
                continue
            if isinstance(value, (_dt.date, _dt.datetime)):
                continue
            if not isinstance(value, str) or not _ISO_RE.match(value):
                findings.append(
                    Finding(
                        rule_id="timestamp.iso8601",
                        severity="blocking",
                        detail=f"{loc} value {value!r} is not ISO 8601",
                    )
                )

    # 1.4 Waivers — approver_role must be "human", expires_at required and unexpired.
    for i, waiver in enumerate(manifest.get("waivers") or []):
        if not isinstance(waiver, dict):
            continue
        loc = f"waivers[{i}]"
        approver = waiver.get("approver_role")
        if approver != "human":
            findings.append(
                Finding(
                    rule_id="waiver.approver_must_be_human",
                    severity="blocking",
                    detail=f"{loc}.approver_role={approver!r}",
                )
            )
        expires = waiver.get("expires_at")
        if not expires:
            findings.append(
                Finding(
                    rule_id="waiver.must_be_time_bounded",
                    severity="blocking",
                    detail=f"{loc}.expires_at missing",
                )
            )
        else:
            expires_date = _coerce_date(expires)
            if expires_date is not None and expires_date < today:
                findings.append(
                    Finding(
                        rule_id="waiver.expired",
                        severity="blocking",
                        detail=f"{loc}.expires_at={expires} already in the past",
                    )
                )

    return findings


def _run_jsonschema(manifest: dict[str, Any], schema: dict[str, Any]) -> list[Finding]:
    try:
        from jsonschema import Draft202012Validator
    except Exception as exc:  # pragma: no cover - import-time configuration issue
        return [
            Finding(
                rule_id="schema.tool_unavailable",
                severity="advisory",
                detail=f"jsonschema import failed: {exc}",
            )
        ]
    validator = Draft202012Validator(schema)
    out: list[Finding] = []
    for err in validator.iter_errors(manifest):
        pointer = "/".join(str(p) for p in err.absolute_path)
        out.append(
            Finding(
                rule_id="schema.violation",
                severity="blocking",
                detail=f"{pointer or '<root>'}: {err.message}",
            )
        )
    return out


def _iter_field(node: Any, target: str, path: str = ""):
    if isinstance(node, dict):
        for k, v in node.items():
            next_path = f"{path}.{k}" if path else k
            if k == target:
                yield next_path, v
            yield from _iter_field(v, target, next_path)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _iter_field(v, target, f"{path}[{i}]")


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


def load_schema(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    import json
    import yaml
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)
