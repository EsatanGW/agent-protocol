// Layer 1 — structural validity. Rules 1.1 – 1.4.

import { readFileSync } from "node:fs";
import Ajv2020 from "ajv/dist/2020.js";
import { parse as parseYaml } from "yaml";

import { makeFinding, type Finding } from "./findings.js";
import type { Manifest } from "./loader.js";
import { coerceDateKey } from "./waivers.js";

const CHANGE_ID_RE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$/;
const ISO_RE =
  /^[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[T ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?(?:Z|[+-][0-9]{2}:?[0-9]{2})?)?$/;

export function check(
  manifest: Manifest,
  opts: { schema?: unknown; today?: Date } = {}
): Finding[] {
  const today = opts.today ?? new Date();
  const todayKey = toDateKey(today);
  const findings: Finding[] = [];

  // 1.1 JSON Schema
  if (opts.schema !== undefined && opts.schema !== null) {
    findings.push(...runJsonSchema(manifest, opts.schema));
  }

  // 1.2 change_id format
  const cid = manifest["change_id"];
  if (typeof cid !== "string" || !CHANGE_ID_RE.test(cid)) {
    findings.push(
      makeFinding(
        "change_id.format",
        "blocking",
        `change_id=${JSON.stringify(cid)} does not match YYYY-MM-DD-slug`
      )
    );
  }

  // 1.3 timestamps must be ISO 8601 where present
  const TIMESTAMP_FIELDS = new Set([
    "last_updated",
    "collected_at",
    "granted_at",
    "timestamp",
    "resolved_at",
  ]);
  for (const { loc, value } of iterFields(manifest, TIMESTAMP_FIELDS)) {
    if (value === undefined || value === null || value === "") continue;
    if (value instanceof Date) continue;
    if (typeof value !== "string" || !ISO_RE.test(value)) {
      findings.push(
        makeFinding(
          "timestamp.iso8601",
          "blocking",
          `${loc} value ${JSON.stringify(value)} is not ISO 8601`
        )
      );
    }
  }

  // 1.4 Waivers
  const waivers = (manifest["waivers"] as unknown[]) || [];
  waivers.forEach((wRaw, i) => {
    if (!wRaw || typeof wRaw !== "object") return;
    const w = wRaw as Record<string, unknown>;
    const loc = `waivers[${i}]`;
    if (w["approver_role"] !== "human") {
      findings.push(
        makeFinding(
          "waiver.approver_must_be_human",
          "blocking",
          `${loc}.approver_role=${JSON.stringify(w["approver_role"])}`
        )
      );
    }
    const expires = w["expires_at"];
    if (!expires) {
      findings.push(
        makeFinding(
          "waiver.must_be_time_bounded",
          "blocking",
          `${loc}.expires_at missing`
        )
      );
    } else {
      const expiresKey = coerceDateKey(expires);
      if (expiresKey !== null && expiresKey < todayKey) {
        findings.push(
          makeFinding(
            "waiver.expired",
            "blocking",
            `${loc}.expires_at=${expires} already in the past`
          )
        );
      }
    }
  });

  return findings;
}

function runJsonSchema(manifest: Manifest, schema: unknown): Finding[] {
  const ajv = new (Ajv2020 as unknown as new (opts?: unknown) => {
    compile: (s: unknown) => (d: unknown) => boolean;
  })({ strict: false, allErrors: true, logger: false });
  let validate: (d: unknown) => boolean;
  try {
    validate = ajv.compile(schema);
  } catch (e) {
    return [
      makeFinding(
        "schema.tool_unavailable",
        "advisory",
        `ajv.compile failed: ${(e as Error).message}`
      ),
    ];
  }
  if (validate(manifest)) return [];
  const errors = ((validate as unknown) as { errors?: AjvErr[] }).errors || [];
  return errors.map(err =>
    makeFinding(
      "schema.violation",
      "blocking",
      `${err.instancePath || "<root>"}: ${err.message ?? "schema violation"}`
    )
  );
}

interface AjvErr {
  instancePath?: string;
  message?: string;
}

export function loadSchema(filePath: string): unknown {
  const text = readFileSync(filePath, "utf-8");
  if (filePath.endsWith(".yaml") || filePath.endsWith(".yml")) {
    return parseYaml(text);
  }
  return JSON.parse(text);
}

function* iterFields(
  node: unknown,
  targets: Set<string>,
  path = ""
): Generator<{ loc: string; value: unknown }> {
  if (node !== null && typeof node === "object" && !Array.isArray(node)) {
    for (const [k, v] of Object.entries(node as Record<string, unknown>)) {
      const next = path ? `${path}.${k}` : k;
      if (targets.has(k)) yield { loc: next, value: v };
      yield* iterFields(v, targets, next);
    }
  } else if (Array.isArray(node)) {
    for (let i = 0; i < node.length; i++) {
      yield* iterFields(node[i], targets, `${path}[${i}]`);
    }
  }
}

function toDateKey(d: Date): string {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
