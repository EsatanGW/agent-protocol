// Layer 3 — drift detection. Rules 3.1 – 3.5.

import { spawnSync } from "node:child_process";
import { readFileSync, existsSync } from "node:fs";

import { makeFinding, type Finding } from "./findings.js";
import type { Manifest } from "./loader.js";
import { globMatch, type SurfaceMap } from "./surfaceMap.js";

export interface Layer3Options {
  repoRoot: string;
  baseRef?: string | null;
  surfaceMap?: SurfaceMap | null;
  monitoringCache?: string | null;
  uncontrolledInterfaceMaxAgeDays?: number;
  today?: Date;
}

export function check(manifest: Manifest, opts: Layer3Options): Finding[] {
  const baseRef = opts.baseRef ?? null;
  if (!baseRef) return [];
  const today = opts.today ?? new Date();
  const maxAge = opts.uncontrolledInterfaceMaxAgeDays ?? 7;

  const changed = gitDiffNameOnly(opts.repoRoot, baseRef);
  const out: Finding[] = [];
  out.push(...rule3_1(manifest, changed));
  if (opts.surfaceMap) {
    out.push(...rule3_2(manifest, opts.surfaceMap, changed));
  }
  out.push(...rule3_3(manifest, opts.surfaceMap ?? null, changed));
  out.push(...rule3_4(manifest, opts.monitoringCache ?? null, maxAge, today));
  out.push(...rule3_5(manifest, opts.repoRoot, today));
  return out;
}

function gitDiffNameOnly(repoRoot: string, baseRef: string): Set<string> {
  const res = spawnSync(
    "git",
    ["diff", "--name-only", `${baseRef}...HEAD`],
    { cwd: repoRoot, encoding: "utf-8", timeout: 30_000 }
  );
  if (res.status !== 0 || !res.stdout) return new Set();
  return new Set(res.stdout.split("\n").filter(Boolean));
}

function rule3_1(manifest: Manifest, changed: Set<string>): Finding[] {
  const out: Finding[] = [];
  const sots = (manifest["sot_map"] as unknown[]) || [];
  for (const s of sots) {
    if (!s || typeof s !== "object" || Array.isArray(s)) continue;
    const rec = s as Record<string, unknown>;
    if (rec["role_in_change"] === "read_only") continue;
    const src = rec["source"];
    if (
      typeof src !== "string" ||
      !src ||
      src.startsWith("http://") ||
      src.startsWith("https://")
    ) continue;
    const filePart = src.split(":", 1)[0]!;
    if (!changed.has(filePart)) {
      out.push(
        makeFinding(
          "drift.declared_sot_not_modified",
          "advisory",
          `declared SoT ${filePart} not in diff`
        )
      );
    }
  }
  return out;
}

export function rule3_2(
  manifest: Manifest,
  surfaceMap: SurfaceMap,
  changed: Set<string>
): Finding[] {
  const out: Finding[] = [];
  const surfaces = (manifest["surfaces_touched"] as unknown[]) || [];
  for (const s of surfaces) {
    if (!s || typeof s !== "object" || Array.isArray(s)) continue;
    const rec = s as Record<string, unknown>;
    if (rec["role"] !== "primary") continue;
    const name = rec["surface"];
    if (typeof name !== "string") continue;
    const patterns = surfaceMap.patternsBySurface[name];
    if (!patterns || patterns.length === 0) continue;
    const matched = [...changed].some(f => surfaceMap.surfacesForPath(f).includes(name));
    if (!matched) {
      out.push(
        makeFinding(
          "drift.primary_surface_no_matching_file_change",
          "advisory",
          `surface ${JSON.stringify(name)} declared primary but no file matching ${JSON.stringify(patterns)} changed`
        )
      );
    }
  }
  return out;
}

function rule3_3(
  manifest: Manifest,
  surfaceMap: SurfaceMap | null,
  changed: Set<string>
): Finding[] {
  const cross = (manifest["cross_cutting"] as Record<string, unknown>) || {};
  const risk = (cross["build_time_risk"] as Record<string, unknown>) || {};
  if (!risk["codegen_touched"]) return [];
  if (!risk["codegen_artifacts_committed"]) return [];
  if (!surfaceMap) return [];
  const patterns = surfaceMap.patternsBySurface["__generated__"];
  if (!patterns || patterns.length === 0) return [];
  const hit = [...changed].some(f => patterns.some(p => globMatch(f, p)));
  if (hit) return [];
  return [
    makeFinding(
      "drift.codegen_touched_but_no_generated_diff",
      "advisory",
      "codegen_touched=true but no generated artifacts in diff"
    ),
  ];
}

export function rule3_4(
  manifest: Manifest,
  cachePath: string | null,
  maxAgeDays: number,
  today: Date
): Finding[] {
  if (!cachePath || !existsSync(cachePath)) return [];
  let cache: unknown;
  try {
    cache = JSON.parse(readFileSync(cachePath, "utf-8"));
  } catch {
    return [];
  }
  if (!cache || typeof cache !== "object" || Array.isArray(cache)) return [];
  const out: Finding[] = [];
  const todayMs = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  const ifaces = (manifest["uncontrolled_interfaces"] as unknown[]) || [];
  for (const i of ifaces) {
    if (!i || typeof i !== "object" || Array.isArray(i)) continue;
    const channel = (i as Record<string, unknown>)["monitoring_channel"];
    if (typeof channel !== "string" || !channel) continue;
    const entry = (cache as Record<string, unknown>)[channel];
    if (!entry || typeof entry !== "object") continue;
    const stamp = (entry as Record<string, unknown>)["last_check"];
    if (typeof stamp !== "string") continue;
    const m = stamp.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) continue;
    const lastMs = Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    const ageDays = Math.floor((todayMs - lastMs) / 86_400_000);
    if (ageDays > maxAgeDays) {
      out.push(
        makeFinding(
          "drift.uncontrolled_interface_not_recently_checked",
          "advisory",
          `monitoring_channel=${channel} last checked ${ageDays}d ago (> ${maxAgeDays}d)`
        )
      );
    }
  }
  return out;
}

function rule3_5(manifest: Manifest, repoRoot: string, today: Date): Finding[] {
  const lastUpdated = manifest["last_updated"];
  if (!lastUpdated) return [];
  const md = String(lastUpdated).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!md) return [];
  const manifestMs = Date.UTC(Number(md[1]), Number(md[2]) - 1, Number(md[3]));
  const res = spawnSync(
    "git",
    ["log", "-1", "--format=%cI"],
    { cwd: repoRoot, encoding: "utf-8", timeout: 10_000 }
  );
  if (res.status !== 0) return [];
  const raw = res.stdout.trim();
  const cd = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!cd) return [];
  const commitMs = Date.UTC(Number(cd[1]), Number(cd[2]) - 1, Number(cd[3]));
  if (manifestMs < commitMs) {
    const fmt = (ms: number) => {
      const d = new Date(ms);
      const y = d.getUTCFullYear();
      const mo = String(d.getUTCMonth() + 1).padStart(2, "0");
      const da = String(d.getUTCDate()).padStart(2, "0");
      return `${y}-${mo}-${da}`;
    };
    return [
      makeFinding(
        "drift.manifest_older_than_latest_code",
        "advisory",
        `manifest.last_updated=${fmt(manifestMs)} older than latest code commit ${fmt(commitMs)}`
      ),
    ];
  }
  // keep `today` referenced to silence unused-param lint
  void today;
  return [];
}
