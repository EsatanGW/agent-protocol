"""Finding model + severity / exit-code mapping.

The validator speaks in Findings, not strings. Each rule emits a Finding with
a stable ``rule_id``; the exit-code mapper applies the repo's enforcement
level to decide whether it translates into ``warn`` (exit 1) or ``block``
(exit 2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["advisory", "blocking", "waived"]


@dataclass
class Finding:
    rule_id: str
    severity: Severity
    detail: str = ""
    waiver_rule_id: str | None = None
    waiver_expires: str | None = None

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "detail": self.detail,
            "waiver_rule_id": self.waiver_rule_id,
            "waiver_expires": self.waiver_expires,
        }


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def extend(self, items: list[Finding]) -> None:
        self.findings.extend(items)

    def as_dict(self) -> dict:
        return {"findings": [f.as_dict() for f in self.findings]}


def compute_exit_code(report: Report) -> int:
    """Contract-compliant mapping.

    ``0`` = all pass; ``1`` = advisory only; ``2`` = at least one blocking
    finding that was not waived. Waived findings never escalate.
    """
    has_blocking = False
    has_advisory = False
    for f in report.findings:
        if f.severity == "waived":
            continue
        if f.severity == "blocking":
            has_blocking = True
        elif f.severity == "advisory":
            has_advisory = True
    if has_blocking:
        return 2
    if has_advisory:
        return 1
    return 0
