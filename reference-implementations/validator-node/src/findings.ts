// Finding model + severity / exit-code mapping.
//
// The validator speaks in Findings, not strings. Each rule emits a Finding
// with a stable `rule_id`; the exit-code mapper applies the repo's
// enforcement level to decide whether it translates into `warn` (exit 1) or
// `block` (exit 2). Mirrors validator-python/src/agent_protocol_validate/findings.py.

export type Severity = "advisory" | "blocking" | "waived";

export interface Finding {
  rule_id: string;
  severity: Severity;
  detail: string;
  waiver_rule_id: string | null;
  waiver_expires: string | null;
}

export function makeFinding(
  rule_id: string,
  severity: Severity,
  detail = ""
): Finding {
  return {
    rule_id,
    severity,
    detail,
    waiver_rule_id: null,
    waiver_expires: null,
  };
}

export interface ReportShape {
  findings: Finding[];
}

export class Report {
  findings: Finding[] = [];

  extend(items: Finding[]): void {
    this.findings.push(...items);
  }

  asDict(): ReportShape {
    return { findings: this.findings.map(f => ({ ...f })) };
  }
}

export function computeExitCode(report: Report): number {
  let hasBlocking = false;
  let hasAdvisory = false;
  for (const f of report.findings) {
    if (f.severity === "waived") continue;
    if (f.severity === "blocking") hasBlocking = true;
    else if (f.severity === "advisory") hasAdvisory = true;
  }
  if (hasBlocking) return 2;
  if (hasAdvisory) return 1;
  return 0;
}
