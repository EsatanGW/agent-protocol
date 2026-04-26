// Waiver filtering.
//
// A finding whose `rule_id` matches an active, human-authorized, unexpired
// waiver is downgraded to `severity="waived"` so the exit-code mapper ignores
// it. Expired or AI-authored waivers have no effect.

import type { Finding } from "./findings.js";
import type { Manifest } from "./loader.js";

export function applyWaivers(
  findings: Finding[],
  manifest: Manifest,
  opts: { today?: Date } = {}
): Finding[] {
  const today = opts.today ?? new Date();
  const todayKey = toDateKey(today);
  const waivers = (manifest["waivers"] as unknown[]) || [];
  const active: Record<string, Record<string, unknown>> = {};
  for (const wRaw of waivers) {
    if (!wRaw || typeof wRaw !== "object") continue;
    const w = wRaw as Record<string, unknown>;
    if (w["approver_role"] !== "human") continue;
    const expires = w["expires_at"];
    const expiresKey = coerceDateKey(expires);
    if (expiresKey === null || expiresKey < todayKey) continue;
    const rid = w["rule_id"];
    if (typeof rid === "string") active[rid] = w;
  }
  if (Object.keys(active).length === 0) return findings;
  for (const f of findings) {
    const w = active[f.rule_id];
    if (w !== undefined) {
      f.severity = "waived";
      f.waiver_rule_id = typeof w["rule_id"] === "string" ? (w["rule_id"] as string) : null;
      f.waiver_expires = w["expires_at"] == null ? null : String(w["expires_at"]);
    }
  }
  return findings;
}

function toDateKey(d: Date): string {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function coerceDateKey(value: unknown): string | null {
  if (value instanceof Date && !isNaN(value.getTime())) return toDateKey(value);
  if (typeof value === "string") {
    const m = value.match(/^(\d{4}-\d{2}-\d{2})/);
    if (m) return m[1]!;
  }
  return null;
}
