// Layer 2 — cross-reference consistency. Rules 2.1 – 2.11.
//
// 2.11 (evidence tier floor under high-severity conditions) was added in the
// 1.8 schema revision and is enforced identically across all three validators.

import * as path from "node:path";
import { existsSync } from "node:fs";

import { makeFinding, type Finding } from "./findings.js";
import type { Manifest } from "./loader.js";

export function check(
  manifest: Manifest,
  opts: { repoRoot: string; siblings?: Record<string, Manifest> }
): Finding[] {
  const siblings = opts.siblings ?? {};
  const out: Finding[] = [];
  out.push(...rule2_1(manifest));
  out.push(...rule2_2(manifest, opts.repoRoot));
  out.push(...rule2_3(manifest, opts.repoRoot));
  out.push(...rule2_4(manifest, siblings));
  out.push(...rule2_5(manifest, siblings));
  out.push(...rule2_6(manifest));
  out.push(...rule2_7(manifest));
  out.push(...rule2_8(manifest));
  out.push(...rule2_9(manifest));
  out.push(...rule2_10(manifest));
  out.push(...rule2_11(manifest));
  return out;
}

function looksLikePath(v: unknown): boolean {
  if (typeof v !== "string" || v === "") return false;
  if (v.startsWith("http://") || v.startsWith("https://")) return false;
  return v.includes("/") || v.includes(".");
}

function rule2_1(manifest: Manifest): Finding[] {
  const surfaces = (manifest["surfaces_touched"] as unknown[]) || [];
  const primary = new Set<string>();
  for (const s of surfaces) {
    if (s && typeof s === "object" && !Array.isArray(s)) {
      const rec = s as Record<string, unknown>;
      if (rec["role"] === "primary" && typeof rec["surface"] === "string") {
        primary.add(rec["surface"] as string);
      }
    }
  }
  const covered = new Set<string>();
  const ev = (manifest["evidence_plan"] as unknown[]) || [];
  for (const e of ev) {
    if (e && typeof e === "object" && !Array.isArray(e)) {
      const surf = (e as Record<string, unknown>)["surface"];
      if (typeof surf === "string") covered.add(surf);
    }
  }
  const missing = [...primary].filter(p => !covered.has(p)).sort();
  return missing.map(s =>
    makeFinding(
      "evidence.primary_surface_required",
      "blocking",
      `primary surface ${JSON.stringify(s)} has no evidence_plan entry`
    )
  );
}

function rule2_2(manifest: Manifest, repoRoot: string): Finding[] {
  const out: Finding[] = [];
  const sots = (manifest["sot_map"] as unknown[]) || [];
  for (const s of sots) {
    if (!s || typeof s !== "object" || Array.isArray(s)) continue;
    const src = (s as Record<string, unknown>)["source"];
    if (!looksLikePath(src)) continue;
    const filePart = String(src).split(":", 1)[0]!;
    if (!existsSync(path.join(repoRoot, filePart))) {
      out.push(
        makeFinding(
          "sot.source_file_missing",
          "blocking",
          `${filePart} referenced in sot_map but not found`
        )
      );
    }
  }
  return out;
}

function rule2_3(manifest: Manifest, repoRoot: string): Finding[] {
  const out: Finding[] = [];
  const ev = (manifest["evidence_plan"] as unknown[]) || [];
  for (const e of ev) {
    if (!e || typeof e !== "object" || Array.isArray(e)) continue;
    const rec = e as Record<string, unknown>;
    if (rec["status"] !== "collected") continue;
    const loc = rec["artifact_location"];
    if (!loc) {
      out.push(
        makeFinding(
          "evidence.collected_requires_location",
          "blocking",
          "status=collected with empty artifact_location"
        )
      );
      continue;
    }
    if (typeof loc === "string" && looksLikePath(loc)) {
      if (!existsSync(path.join(repoRoot, loc))) {
        out.push(
          makeFinding(
            "evidence.artifact_missing",
            "advisory",
            `artifact_location ${loc} does not resolve`
          )
        );
      }
    }
  }
  return out;
}

function edgesFor(m: Manifest): Set<string> {
  let deps = m["depends_on"];
  if (typeof deps === "string") deps = [deps];
  if (!Array.isArray(deps)) return new Set();
  return new Set(deps.filter((d): d is string => typeof d === "string"));
}

function rule2_4(
  manifest: Manifest,
  siblings: Record<string, Manifest>
): Finding[] {
  const graph = new Map<string, Set<string>>();
  const selfId = manifest["change_id"];
  if (typeof selfId === "string" && selfId.length > 0) {
    graph.set(selfId, edgesFor(manifest));
  }
  for (const [cid, m] of Object.entries(siblings)) {
    graph.set(cid, edgesFor(m));
  }
  const cycle = findCycle(graph);
  if (cycle) {
    return [
      makeFinding(
        "decomposition.graph_must_be_acyclic",
        "blocking",
        "cycle: " + cycle.join(" -> ")
      ),
    ];
  }
  return [];
}

function findCycle(graph: Map<string, Set<string>>): string[] | null {
  const WHITE = 0,
    GRAY = 1,
    BLACK = 2;
  const color = new Map<string, number>();
  const parent = new Map<string, string | null>();
  for (const node of graph.keys()) {
    color.set(node, WHITE);
    parent.set(node, null);
  }
  const nodes = [...graph.keys()].sort();
  for (const start of nodes) {
    if (color.get(start) !== WHITE) continue;
    const result = dfs(graph, start, color, parent);
    if (result) return result;
  }
  return null;
}

function dfs(
  graph: Map<string, Set<string>>,
  start: string,
  color: Map<string, number>,
  parent: Map<string, string | null>
): string[] | null {
  const GRAY = 1,
    BLACK = 2;
  const stack: Array<{ node: string; it: Iterator<string> }> = [
    { node: start, it: [...(graph.get(start) ?? new Set())].sort()[Symbol.iterator]() },
  ];
  color.set(start, GRAY);
  while (stack.length > 0) {
    const frame = stack[stack.length - 1]!;
    const { value: nxt, done } = frame.it.next();
    if (done) {
      color.set(frame.node, BLACK);
      stack.pop();
      continue;
    }
    if (!graph.has(nxt)) continue;
    if (color.get(nxt) === GRAY) {
      const cyc: string[] = [nxt, frame.node];
      let cur = parent.get(frame.node) ?? null;
      while (cur !== null && cur !== nxt) {
        cyc.push(cur);
        cur = parent.get(cur) ?? null;
      }
      cyc.push(nxt);
      cyc.reverse();
      return cyc;
    }
    if (color.get(nxt) === 0) {
      color.set(nxt, GRAY);
      parent.set(nxt, frame.node);
      stack.push({
        node: nxt,
        it: [...(graph.get(nxt) ?? new Set())].sort()[Symbol.iterator](),
      });
    }
  }
  return null;
}

function rule2_5(
  manifest: Manifest,
  siblings: Record<string, Manifest>
): Finding[] {
  const out: Finding[] = [];
  const selfId = manifest["change_id"];
  if (typeof selfId !== "string") return out;
  const deps = (manifest["depends_on"] as unknown[]) || [];
  for (const depId of deps) {
    if (typeof depId !== "string" || !(depId in siblings)) continue;
    const blocks = (siblings[depId]!["blocks"] as unknown[]) || [];
    if (!blocks.includes(selfId)) {
      out.push(
        makeFinding(
          "decomposition.relation_must_be_bidirectional",
          "advisory",
          `${depId}.blocks is missing ${selfId}`
        )
      );
    }
  }
  return out;
}

function rule2_6(manifest: Manifest): Finding[] {
  const breaking = (manifest["breaking_change"] as Record<string, unknown>) || {};
  const level = breaking["level"];
  if (level === "L3" || level === "L4") {
    const hasTimeline = Boolean(breaking["deprecation_timeline"]);
    const hasDeprecation = Boolean(breaking["deprecation"]);
    if (!(hasTimeline || hasDeprecation)) {
      return [
        makeFinding(
          "breaking_change.l3_l4_requires_deprecation",
          "blocking",
          `breaking_change.level=${level} with neither deprecation_timeline nor deprecation marker`
        ),
      ];
    }
  }
  return [];
}

function rule2_7(manifest: Manifest): Finding[] {
  const rb = (manifest["rollback"] as Record<string, unknown>) || {};
  const mode = rb["overall_mode"] ?? rb["mode"];
  if (mode === 3 && !rb["compensation_plan"]) {
    return [
      makeFinding(
        "rollback.mode_3_requires_compensation",
        "blocking",
        "rollback.overall_mode=3 with no compensation_plan"
      ),
    ];
  }
  return [];
}

function rule2_8(manifest: Manifest): Finding[] {
  if (manifest["phase"] !== "deliver" && manifest["status"] !== "delivered") return [];
  const approvals = (manifest["approvals"] as unknown[]) || [];
  const human = approvals.some(
    a => a && typeof a === "object" && (a as Record<string, unknown>)["role"] === "human"
  );
  if (human) return [];
  return [
    makeFinding(
      "approval.human_required_for_delivery",
      "blocking",
      "phase=deliver but no approvals with role=human"
    ),
  ];
}

function rule2_9(manifest: Manifest): Finding[] {
  const surfaces = (manifest["surfaces_touched"] as unknown[]) || [];
  const hasExperience = surfaces.some(
    s => s && typeof s === "object" && (s as Record<string, unknown>)["surface"] === "experience"
  );
  if (hasExperience && !manifest["playtest"]) {
    return [
      makeFinding(
        "playtest.required_for_experience_surface",
        "blocking",
        "experience surface touched without playtest block"
      ),
    ];
  }
  return [];
}

function rule2_10(manifest: Manifest): Finding[] {
  if (manifest["phase"] === "observe" && !manifest["handoff_narrative"]) {
    return [
      makeFinding(
        "handoff.narrative_required_for_observe",
        "blocking",
        "phase=observe requires handoff_narrative"
      ),
    ];
  }
  return [];
}

// Rule 2.11 — evidence tier floor under high-severity conditions.
// At least one evidence_plan entry must be tier=critical when: breaking_change
// level >= L2, rollback mode 3, or a high-risk surface (compliance /
// real_world / experience) is touched with role=primary. Missing `tier` is
// treated as "standard" for backward compatibility with pre-1.8 manifests.

const HIGH_RISK_SURFACES = new Set(["compliance", "real_world", "experience"]);
const HIGH_BREAKING_LEVELS = new Set(["L2", "L3", "L4"]);

export function rule2_11(manifest: Manifest): Finding[] {
  const breaking = (manifest["breaking_change"] as Record<string, unknown>) || {};
  const rollback = (manifest["rollback"] as Record<string, unknown>) || {};
  const rollbackMode = rollback["overall_mode"] ?? rollback["mode"];

  const surfaces = (manifest["surfaces_touched"] as unknown[]) || [];
  const highRiskSurfacePrimary = surfaces.some(s => {
    if (!s || typeof s !== "object" || Array.isArray(s)) return false;
    const rec = s as Record<string, unknown>;
    return rec["role"] === "primary" && HIGH_RISK_SURFACES.has(rec["surface"] as string);
  });

  const highSeverity =
    HIGH_BREAKING_LEVELS.has(breaking["level"] as string) ||
    rollbackMode === 3 ||
    highRiskSurfacePrimary;

  if (!highSeverity) return [];

  const evidence = (manifest["evidence_plan"] as unknown[]) || [];
  const hasCritical = evidence.some(ev => {
    if (!ev || typeof ev !== "object" || Array.isArray(ev)) return false;
    return (ev as Record<string, unknown>)["tier"] === "critical";
  });
  if (hasCritical) return [];

  const triggers: string[] = [];
  if (HIGH_BREAKING_LEVELS.has(breaking["level"] as string)) {
    triggers.push(`breaking_change.level=${breaking["level"]}`);
  }
  if (rollbackMode === 3) triggers.push("rollback.overall_mode=3");
  if (highRiskSurfacePrimary) triggers.push("high-risk surface touched with role=primary");

  return [
    makeFinding(
      "evidence.critical_required_for_high_severity",
      "blocking",
      `at least one evidence_plan entry must be tier=critical when ${triggers.join(" / ")}`
    ),
  ];
}
