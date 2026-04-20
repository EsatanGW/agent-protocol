// Manifest + sibling-manifest loader. Kept thin on purpose. YAML parsing is
// delegated to the `yaml` package; everything else operates on plain objects.

import { readFileSync } from "node:fs";
import * as path from "node:path";
import { parse as parseYaml } from "yaml";
import { globSync } from "glob";

export type Manifest = Record<string, unknown>;

export function loadYaml(filePath: string): Manifest {
  const raw = readFileSync(filePath, "utf-8");
  const doc = parseYaml(raw);
  if (doc == null || typeof doc !== "object" || Array.isArray(doc)) {
    return {};
  }
  return doc as Manifest;
}

export function findSiblingManifests(
  manifestPath: string
): Record<string, Manifest> {
  const dir = path.dirname(path.resolve(manifestPath));
  const self = path.resolve(manifestPath);
  const siblings: Record<string, Manifest> = {};
  const candidates = globSync("change-manifest*.yaml", { cwd: dir }).sort();
  for (const name of candidates) {
    const abs = path.resolve(dir, name);
    if (abs === self) continue;
    let doc: Manifest;
    try {
      doc = loadYaml(abs);
    } catch {
      continue;
    }
    const cid = doc["change_id"];
    if (typeof cid === "string" && cid.length > 0) {
      siblings[cid] = doc;
    }
  }
  return siblings;
}
