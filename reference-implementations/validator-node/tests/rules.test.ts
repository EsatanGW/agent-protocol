// Coverage-focused tests for the language-native Node validator.
//
// Exercises the four rules the POSIX reference could not implement (2.4,
// 2.5, 3.2, 3.4) plus a happy-path + waiver sanity check so the exit-code
// contract is pinned down. Matches validator-python/tests/test_rules.py
// one-for-one so the two language references stay behaviour-compatible.

import { describe, it } from "node:test";
import * as assert from "node:assert/strict";
import * as path from "node:path";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";
import { mkdtempSync } from "node:fs";

import * as layer1 from "../src/layer1.js";
import * as layer2 from "../src/layer2.js";
import * as layer3 from "../src/layer3.js";
import { Report, computeExitCode } from "../src/findings.js";
import { findSiblingManifests, loadYaml } from "../src/loader.js";
import { loadSurfaceMap } from "../src/surfaceMap.js";
import { applyWaivers } from "../src/waivers.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
// Tests run from dist/tests/, so fixtures are one hop up from src:
// dist/tests/rules.test.js → ../../tests/fixtures/
const FIXTURES = path.resolve(HERE, "..", "..", "tests", "fixtures");

function runAll(manifestPath: string) {
  const manifest = loadYaml(manifestPath);
  const siblings = findSiblingManifests(manifestPath);
  const report = new Report();
  report.extend(layer1.check(manifest));
  report.extend(
    layer2.check(manifest, { repoRoot: path.dirname(manifestPath), siblings })
  );
  return { manifest, report };
}

describe("pass-minimal", () => {
  it("has no blocking findings", () => {
    const { report } = runAll(path.join(FIXTURES, "pass-minimal.yaml"));
    assert.ok(computeExitCode(report) <= 1);
    assert.ok(!report.findings.some(f => f.severity === "blocking"));
  });
});

describe("rule 2.4 — decomposition acyclicity", () => {
  it("detects a direct cycle", () => {
    const { report } = runAll(
      path.join(FIXTURES, "cycle", "change-manifest-a.yaml")
    );
    const ids = report.findings.map(f => f.rule_id);
    assert.ok(ids.includes("decomposition.graph_must_be_acyclic"));
    assert.equal(computeExitCode(report), 2);
  });
});

describe("rule 2.5 — depends_on / blocks mirror", () => {
  it("fires when sibling is missing blocks", () => {
    const { report } = runAll(
      path.join(FIXTURES, "bidirectional-fail", "change-manifest-a.yaml")
    );
    assert.ok(
      report.findings.some(
        f => f.rule_id === "decomposition.relation_must_be_bidirectional"
      )
    );
  });

  it("silent when bidirectional ok", () => {
    const { report } = runAll(
      path.join(FIXTURES, "bidirectional-pass", "change-manifest-a.yaml")
    );
    assert.ok(
      !report.findings.some(
        f => f.rule_id === "decomposition.relation_must_be_bidirectional"
      )
    );
  });
});

describe("rule 3.2 — surface / file-pattern drift", () => {
  it("fires when a surface has no matching file", () => {
    const sm = loadSurfaceMap(path.join(FIXTURES, "surface-map-flutter.yaml"));
    const manifest = {
      change_id: "2026-04-20-drift",
      surfaces_touched: [{ surface: "user", role: "primary" }],
    };
    const findings = layer3.rule3_2(manifest, sm, new Set(["README.md"]));
    assert.ok(findings.length > 0);
    assert.equal(
      findings[0]!.rule_id,
      "drift.primary_surface_no_matching_file_change"
    );
  });

  it("silent when matching file changed", () => {
    const sm = loadSurfaceMap(path.join(FIXTURES, "surface-map-flutter.yaml"));
    const manifest = {
      change_id: "2026-04-20-drift",
      surfaces_touched: [{ surface: "user", role: "primary" }],
    };
    const findings = layer3.rule3_2(
      manifest,
      sm,
      new Set(["lib/ui/home_page.dart"])
    );
    assert.deepEqual(findings, []);
  });
});

describe("rule 3.4 — monitoring channel staleness", () => {
  it("uses local cache and emits advisory when stale", () => {
    const dir = mkdtempSync(path.join(tmpdir(), "ap-node-"));
    const cache = path.join(dir, "cache.json");
    writeFileSync(
      cache,
      JSON.stringify({ "iface-1": { last_check: "2026-01-01" } }),
      "utf-8"
    );
    const manifest = {
      uncontrolled_interfaces: [{ monitoring_channel: "iface-1" }],
    };
    const findings = layer3.rule3_4(
      manifest,
      cache,
      7,
      new Date(Date.UTC(2026, 3, 20))
    );
    assert.ok(findings.length > 0);
    assert.equal(
      findings[0]!.rule_id,
      "drift.uncontrolled_interface_not_recently_checked"
    );
  });

  it("silent when cache is fresh", () => {
    const dir = mkdtempSync(path.join(tmpdir(), "ap-node-"));
    const cache = path.join(dir, "cache.json");
    writeFileSync(
      cache,
      JSON.stringify({ "iface-1": { last_check: "2026-04-19" } }),
      "utf-8"
    );
    const manifest = {
      uncontrolled_interfaces: [{ monitoring_channel: "iface-1" }],
    };
    const findings = layer3.rule3_4(
      manifest,
      cache,
      7,
      new Date(Date.UTC(2026, 3, 20))
    );
    assert.deepEqual(findings, []);
  });
});

describe("waivers", () => {
  it("downgrade blocking findings to waived", () => {
    const manifestPath = path.join(FIXTURES, "waiver", "change-manifest.yaml");
    const manifest = loadYaml(manifestPath);
    const siblings = findSiblingManifests(manifestPath);
    const report = new Report();
    report.extend(
      layer1.check(manifest, { today: new Date(Date.UTC(2026, 3, 20)) })
    );
    report.extend(
      layer2.check(manifest, {
        repoRoot: path.dirname(manifestPath),
        siblings,
      })
    );
    applyWaivers(report.findings, manifest, {
      today: new Date(Date.UTC(2026, 3, 20)),
    });
    const waived = report.findings.filter(
      f => f.rule_id === "handoff.narrative_required_for_observe"
    );
    assert.ok(waived.length > 0);
    assert.ok(waived.every(f => f.severity === "waived"));
  });
});

describe("surface map globstar matching", () => {
  const cases = [
    { path: "lib/ui/home_page.dart" },
    { path: "lib/platform/method_channel_bridge.dart" },
    { path: "pubspec.yaml" },
  ];
  for (const c of cases) {
    it(`matches ${c.path}`, () => {
      const sm = loadSurfaceMap(path.join(FIXTURES, "surface-map-flutter.yaml"));
      assert.ok(sm.surfacesForPath(c.path).length > 0);
    });
  }
});

describe("exit-code mapping", () => {
  it("blocking beats advisory beats waived", () => {
    const report = new Report();
    report.extend([
      { rule_id: "x", severity: "advisory", detail: "", waiver_rule_id: null, waiver_expires: null },
    ]);
    assert.equal(computeExitCode(report), 1);
    report.extend([
      { rule_id: "y", severity: "blocking", detail: "", waiver_rule_id: null, waiver_expires: null },
    ]);
    assert.equal(computeExitCode(report), 2);
    const all = new Report();
    all.extend([
      { rule_id: "z", severity: "waived", detail: "", waiver_rule_id: null, waiver_expires: null },
    ]);
    assert.equal(computeExitCode(all), 0);
  });
});

// ─── Rule 2.11 — evidence tier floor under high-severity conditions ─────

const RULE_2_11_ID = "evidence.critical_required_for_high_severity";

function manifestWith(opts: {
  breakingLevel?: string;
  rollbackMode?: number;
  surfaces?: Array<{ surface: string; role: string }>;
  evidence?: Array<Record<string, unknown>>;
}) {
  return {
    change_id: "2026-04-21-rule-2-11-test",
    breaking_change: { level: opts.breakingLevel ?? "L0" },
    rollback: { overall_mode: opts.rollbackMode ?? 1 },
    surfaces_touched: opts.surfaces ?? [{ surface: "user", role: "primary" }],
    evidence_plan: opts.evidence ?? [],
  };
}

describe("rule 2.11 — evidence tier floor", () => {
  it("fires on L2 without tier=critical", () => {
    const findings = layer2.rule2_11(
      manifestWith({
        breakingLevel: "L2",
        evidence: [{ type: "unit_test", surface: "user", status: "collected", tier: "standard" }],
      })
    );
    assert.ok(findings.some(f => f.rule_id === RULE_2_11_ID && f.severity === "blocking"));
  });

  it("fires on rollback mode 3 without tier=critical", () => {
    const findings = layer2.rule2_11(
      manifestWith({
        rollbackMode: 3,
        evidence: [{ type: "unit_test", surface: "user", status: "collected" }],
      })
    );
    assert.ok(findings.some(f => f.rule_id === RULE_2_11_ID));
  });

  it("fires on compliance-primary surface without tier=critical", () => {
    const findings = layer2.rule2_11(
      manifestWith({
        surfaces: [{ surface: "compliance", role: "primary" }],
        evidence: [{ type: "changelog_entry", surface: "compliance", status: "planned" }],
      })
    );
    assert.ok(findings.length > 0 && findings[0]!.rule_id === RULE_2_11_ID);
  });

  it("silent when tier=critical is present", () => {
    const findings = layer2.rule2_11(
      manifestWith({
        breakingLevel: "L3",
        rollbackMode: 3,
        evidence: [
          { type: "unit_test", surface: "user", status: "collected", tier: "standard" },
          { type: "migration_dry_run", surface: "information", status: "collected", tier: "critical" },
        ],
      })
    );
    assert.deepEqual(findings, []);
  });

  it("silent when no high-severity condition applies (backward compat)", () => {
    const findings = layer2.rule2_11(
      manifestWith({
        breakingLevel: "L0",
        rollbackMode: 1,
        surfaces: [{ surface: "user", role: "primary" }],
        evidence: [{ type: "unit_test", surface: "user", status: "collected" }],
      })
    );
    assert.deepEqual(findings, []);
  });

  it("silent when high-risk surface is in consumer role (not primary)", () => {
    const findings = layer2.rule2_11(
      manifestWith({
        surfaces: [
          { surface: "user", role: "primary" },
          { surface: "compliance", role: "consumer" },
        ],
        evidence: [{ type: "unit_test", surface: "user", status: "collected" }],
      })
    );
    assert.deepEqual(findings, []);
  });
});
