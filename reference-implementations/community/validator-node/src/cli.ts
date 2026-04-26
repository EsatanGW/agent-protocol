#!/usr/bin/env node
// Command-line entry point.
//
// Usage:
//   agent-protocol-validate <manifest> [options]
//
// Options mirror the Python reference:
//   --schema PATH             JSON Schema file (YAML or JSON). Enables rule 1.1.
//   --surface-map PATH        Per-bridge surface-map.yaml. Enables rule 3.2.
//   --repo-root PATH          Repository root. Defaults to CWD.
//   --base-ref REF            Git base ref for drift detection. Enables Layer 3.
//   --monitoring-cache PATH   Local cache file for rule 3.4. Defaults to
//                             <repo-root>/.agent-protocol/monitoring-cache.json.
//   --uncontrolled-max-age N  Staleness threshold in days for rule 3.4 (default 7).
//   --report PATH             Write JSON report to PATH. Defaults to stdout.
//
// Exit codes:
//   0 — every finding waived or no findings.
//   1 — at least one advisory finding, no blocking findings.
//   2 — at least one blocking finding that was not waived.
//   64 — harness / argument error (stderr explains).

import { existsSync, writeFileSync, mkdirSync } from "node:fs";
import * as path from "node:path";
import * as process from "node:process";

import * as layer1 from "./layer1.js";
import * as layer2 from "./layer2.js";
import * as layer3 from "./layer3.js";
import { Report, computeExitCode } from "./findings.js";
import { findSiblingManifests, loadYaml } from "./loader.js";
import { loadSurfaceMap, type SurfaceMap } from "./surfaceMap.js";
import { applyWaivers } from "./waivers.js";

interface ParsedArgs {
  manifest: string;
  schema?: string;
  surfaceMap?: string;
  repoRoot: string;
  baseRef?: string;
  monitoringCache?: string;
  uncontrolledMaxAge: number;
  report?: string;
}

function parseArgs(argv: string[]): ParsedArgs {
  const out: Partial<ParsedArgs> = {
    repoRoot: process.cwd(),
    uncontrolledMaxAge: 7,
  };
  const positional: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!;
    switch (a) {
      case "--schema": out.schema = argv[++i]; break;
      case "--surface-map": out.surfaceMap = argv[++i]; break;
      case "--repo-root": out.repoRoot = argv[++i]!; break;
      case "--base-ref": out.baseRef = argv[++i]; break;
      case "--monitoring-cache": out.monitoringCache = argv[++i]; break;
      case "--uncontrolled-max-age":
        out.uncontrolledMaxAge = Number(argv[++i]);
        break;
      case "--report": out.report = argv[++i]; break;
      default:
        if (a.startsWith("--")) {
          throw new Error(`unknown flag ${a}`);
        }
        positional.push(a);
    }
  }
  if (positional.length !== 1) {
    throw new Error("expected exactly one manifest argument");
  }
  out.manifest = positional[0]!;
  return out as ParsedArgs;
}

export function main(argv: string[] = process.argv.slice(2)): number {
  let args: ParsedArgs;
  try {
    args = parseArgs(argv);
  } catch (e) {
    process.stderr.write(`${(e as Error).message}\n`);
    return 64;
  }

  if (!existsSync(args.manifest)) {
    process.stderr.write(`manifest not found: ${args.manifest}\n`);
    return 64;
  }

  const manifest = loadYaml(args.manifest);
  const schema = args.schema ? layer1.loadSchema(args.schema) : null;
  const surfaceMap: SurfaceMap | null = args.surfaceMap
    ? loadSurfaceMap(args.surfaceMap)
    : null;
  const siblings = findSiblingManifests(args.manifest);

  const repoRoot = path.resolve(args.repoRoot);
  let cachePath = args.monitoringCache ?? null;
  if (cachePath === null) {
    const def = path.join(repoRoot, ".agent-protocol", "monitoring-cache.json");
    if (existsSync(def)) cachePath = def;
  }

  const report = new Report();
  report.extend(layer1.check(manifest, { schema: schema ?? undefined }));
  report.extend(layer2.check(manifest, { repoRoot, siblings }));
  report.extend(
    layer3.check(manifest, {
      repoRoot,
      baseRef: args.baseRef,
      surfaceMap: surfaceMap ?? null,
      monitoringCache: cachePath,
      uncontrolledInterfaceMaxAgeDays: args.uncontrolledMaxAge,
    })
  );
  applyWaivers(report.findings, manifest);

  const payload = JSON.stringify(report.asDict(), null, 2) + "\n";
  if (args.report) {
    mkdirSync(path.dirname(args.report), { recursive: true });
    writeFileSync(args.report, payload, "utf-8");
  } else {
    process.stdout.write(payload);
  }

  return computeExitCode(report);
}

const isMain = import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  process.exit(main());
}
