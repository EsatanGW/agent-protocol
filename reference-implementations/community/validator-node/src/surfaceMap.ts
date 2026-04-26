// Loader + matcher for per-bridge `docs/bridges/<stack>-surface-map.yaml`.
//
// Converts glob patterns into regex and answers the single question rule 3.2
// asks: "for this file path, which surfaces does the bridge say it belongs
// to?" Globstar semantics mirror the Python reference.

import { readFileSync } from "node:fs";
import { parse as parseYaml } from "yaml";

export interface SurfaceMap {
  stack: string;
  patternsBySurface: Record<string, string[]>;
  surfacesForPath(path: string): string[];
}

export function loadSurfaceMap(filePath: string): SurfaceMap {
  const raw = readFileSync(filePath, "utf-8");
  const doc = (parseYaml(raw) as Record<string, unknown>) ?? {};

  const canonical = (doc["canonical_surfaces"] as Record<string, unknown>) || {};
  const extensions = (doc["stack_extensions"] as Record<string, unknown>) || {};

  const patterns: Record<string, string[]> = {};
  for (const [name, block] of Object.entries(canonical)) {
    if (block && typeof block === "object") {
      const list = (block as Record<string, unknown>)["patterns"];
      if (Array.isArray(list)) patterns[name] = list.filter(x => typeof x === "string") as string[];
    }
  }
  for (const [name, block] of Object.entries(extensions)) {
    if (block && typeof block === "object") {
      const list = (block as Record<string, unknown>)["patterns"];
      if (Array.isArray(list)) patterns[name] = list.filter(x => typeof x === "string") as string[];
    }
  }

  const stack = typeof doc["stack"] === "string" ? (doc["stack"] as string) : "";

  return {
    stack,
    patternsBySurface: patterns,
    surfacesForPath(p: string): string[] {
      const matches: string[] = [];
      for (const [surface, pats] of Object.entries(patterns)) {
        for (const pat of pats) {
          if (globMatch(p, pat)) {
            matches.push(surface);
            break;
          }
        }
      }
      return matches;
    },
  };
}

export function globMatch(path: string, pattern: string): boolean {
  const regex = new RegExp("^" + patternToRegex(pattern) + "$");
  return regex.test(path);
}

function patternToRegex(pattern: string): string {
  const out: string[] = [];
  let i = 0;
  while (i < pattern.length) {
    const c = pattern[i];
    if (c === "*") {
      if (pattern[i + 1] === "*") {
        if (pattern[i + 2] === "/") {
          out.push("(?:.*/)?");
          i += 3;
          continue;
        }
        out.push(".*");
        i += 2;
        continue;
      }
      out.push("[^/]*");
      i += 1;
      continue;
    }
    if (c === "?") {
      out.push("[^/]");
      i += 1;
      continue;
    }
    if (".^$+(){}|\\".includes(c!)) {
      out.push("\\" + c);
      i += 1;
      continue;
    }
    out.push(c!);
    i += 1;
  }
  return out.join("");
}
