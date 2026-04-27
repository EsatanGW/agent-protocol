# Automation Contract — Reference Algorithm

> **English TL;DR**
> Companion to `docs/automation-contract.md`. That document defines WHAT a validator must guarantee; this document specifies HOW, as a language-neutral algorithm in pseudo-code. It is prescriptive enough that two independent implementations in any language should behave identically on the same input.

This document is the algorithm specification that accompanies `docs/automation-contract.md`. It defines — as runtime-neutral pseudo-code — how the three checking tiers must execute, so that implementations in any language produce equivalent behavior.

**This document contains no source code in any concrete language.** Reference implementations live in `reference-implementations/`.

---

## Execution model

```
input:
  - manifest_path        : path to the Change Manifest file to validate
  - repo_root            : project root (used for cross-reference resolution)
  - schema_path          : path to the Change Manifest JSON Schema file
  - config               : enforcement level per check (L0 / L1 / L2 / L3)
  - git_base_ref         : comparison base for drift detection (optional)

output:
  - report               : structured check results
  - exit_code            : determined by the highest blocking level observed

flow:
  1. Parse the manifest (YAML → structured object).
  2. Layer 1: structural validation.
  3. Layer 2: cross-reference validation.
  4. Layer 3: drift detection (only if git_base_ref is supplied).
  5. Apply waiver filtering.
  6. Derive exit code from the enforcement levels in config.
```

---

## Layer 1 — Structural validity

**Goal:** does the manifest itself conform to the schema (shape correct, enums legal, required fields present, conditional-required satisfied)?

```pseudo
function check_layer_1(manifest, schema):
    errors = []

    # 1.1 JSON Schema validation (2020-12 draft)
    schema_errors = jsonschema_validate(manifest, schema)
    errors.extend(schema_errors)

    # 1.2 change_id format (YYYY-MM-DD-slug)
    if not matches(manifest.change_id, "^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$"):
        errors.append({ rule: "change_id.format", severity: "blocking" })

    # 1.3 timestamps must be ISO 8601
    for field in [last_updated, collected_at, granted_at, timestamp, resolved_at]:
        if present(field) and not iso8601(field):
            errors.append({ rule: "timestamp.iso8601", severity: "blocking" })

    # 1.4 Waiver approver role invariant
    for waiver in manifest.waivers:
        if waiver.approver_role != "human":
            errors.append({ rule: "waiver.approver_must_be_human", severity: "blocking" })
        if not present(waiver.expires_at):
            errors.append({ rule: "waiver.must_be_time_bounded", severity: "blocking" })
        if waiver.expires_at < today():
            errors.append({ rule: "waiver.expired", severity: "blocking" })

    return errors
```

---

## Layer 2 — Cross-reference consistency

**Goal:** semantic consistency between the manifest's own declarations and between the manifest and real files in the repo.

```pseudo
function check_layer_2(manifest, repo_root):
    errors = []

    # 2.1 Every primary surface must have evidence
    primary_surfaces = [s.surface for s in manifest.surfaces_touched if s.role == "primary"]
    evidence_surfaces = [e.surface for e in manifest.evidence_plan]
    for p in primary_surfaces:
        if p not in evidence_surfaces:
            errors.append({
                rule: "evidence.primary_surface_required",
                severity: "blocking",
                detail: "primary surface " + p + " has no evidence_plan entry"
            })

    # 2.2 SoT source files declared in sot_map must exist
    for sot in manifest.sot_map:
        if looks_like_path(sot.source):
            if not file_exists(repo_root + "/" + sot.source):
                errors.append({
                    rule: "sot.source_file_missing",
                    severity: "blocking",
                    detail: sot.source + " referenced but not found"
                })

    # 2.3 Collected evidence artifacts must have a resolvable location
    for ev in manifest.evidence_plan:
        if ev.status == "collected":
            if not present(ev.artifact_location):
                errors.append({ rule: "evidence.collected_requires_location", severity: "blocking" })
            elif looks_like_path(ev.artifact_location):
                if not file_exists(repo_root + "/" + ev.artifact_location):
                    errors.append({ rule: "evidence.artifact_missing", severity: "advisory" })

    # 2.4 Decomposition graph acyclicity
    graph = build_dependency_graph(manifest, sibling_manifests(repo_root))
    if has_cycle(graph):
        errors.append({ rule: "decomposition.graph_must_be_acyclic", severity: "blocking" })

    # 2.5 depends_on / blocks must be mirrored
    for dep_id in manifest.depends_on:
        sibling = load_manifest(dep_id)
        if sibling and manifest.change_id not in sibling.blocks:
            errors.append({
                rule: "decomposition.relation_must_be_bidirectional",
                severity: "advisory",
                detail: dep_id + ".blocks is missing " + manifest.change_id
            })

    # 2.6 Breaking changes at L3/L4 must declare a deprecation path.
    #     Accept EITHER the legacy `deprecation_timeline` (dates only)
    #     OR the richer `deprecation` marker (introduced in schema 1.7.0;
    #     $ref → $defs.deprecation: {since, remove_in, use_instead,
    #     migration_note, announce_date, sunset_date, escalation_contact}).
    #     Both are equally accepting; prefer `deprecation` for new work.
    if manifest.breaking_change.level in ["L3", "L4"]:
        has_timeline = present(manifest.breaking_change.deprecation_timeline)
        has_deprecation = present(manifest.breaking_change.deprecation)
        if not (has_timeline or has_deprecation):
            errors.append({ rule: "breaking_change.l3_l4_requires_deprecation", severity: "blocking" })

    # 2.7 Rollback mode 3 must carry a compensation_plan
    if manifest.rollback.overall_mode == 3 and not present(manifest.rollback.compensation_plan):
        errors.append({ rule: "rollback.mode_3_requires_compensation", severity: "blocking" })

    # 2.8 phase=deliver requires at least one human approval
    if manifest.phase == "deliver" or manifest.status == "delivered":
        human_approvals = [a for a in manifest.approvals if a.role == "human"]
        if len(human_approvals) == 0:
            errors.append({ rule: "approval.human_required_for_delivery", severity: "blocking" })

    # 2.9 Experience-surface changes must include a playtest block
    if any(s.surface == "experience" for s in manifest.surfaces_touched):
        if not present(manifest.playtest):
            errors.append({ rule: "playtest.required_for_experience_surface", severity: "blocking" })

    # 2.10 phase=observe requires a handoff_narrative
    if manifest.phase == "observe" and not present(manifest.handoff_narrative):
        errors.append({ rule: "handoff.narrative_required_for_observe", severity: "blocking" })

    # 2.11 High-severity conditions require at least one tier=critical evidence.
    #      Tier is an optional field on each evidence_plan item; absent tier
    #      is treated as "standard" for backward compatibility with pre-1.8
    #      manifests. Rule 2.11 only fires when the manifest itself declares
    #      a high-severity condition.
    high_severity = (
        manifest.breaking_change.level in ["L2", "L3", "L4"]
        or manifest.rollback.overall_mode == 3
        or any(
            s.role == "primary"
            and s.surface in ["compliance", "real_world", "experience"]
            for s in manifest.surfaces_touched
        )
    )
    if high_severity:
        has_critical = any(
            ev.tier == "critical"
            for ev in manifest.evidence_plan
        )
        if not has_critical:
            errors.append({
                rule: "evidence.critical_required_for_high_severity",
                severity: "blocking",
                detail: "high-severity conditions require ≥1 evidence with tier=critical"
            })

    # 2.12 Manifest size within ceiling.
    #      Mechanical enforcement of the prose ceiling at
    #      docs/change-manifest-spec.md §State-snapshot discipline §Manifest
    #      size ceiling. A manifest above the ceiling stops working as a state
    #      snapshot — incoming sessions cannot open it in one read, and
    #      grep / offset-read fallbacks defeat the "one file answers what
    #      comes next" guarantee. Severity ladder uses lines as the
    #      tokenizer-agnostic proxy for the ~25,000-token single-file read
    #      ceiling common to AI runtimes (typical 12–13 tokens per line of
    #      YAML manifest content).
    manifest_lines = count_lines(manifest_path)
    if manifest_lines > 2000:
        errors.append({
            rule: "manifest.size_within_ceiling",
            severity: "blocking",
            detail: "manifest is " + manifest_lines + " lines; ceiling is 2000 (≈25,000 tokens). Compact in place (move verbose narrative into structured note fields) or split via part_of per docs/change-manifest-spec.md §Manifest size ceiling. grep / offset-read workarounds are explicitly prohibited."
        })
    elif manifest_lines > 1500:
        errors.append({
            rule: "manifest.size_within_ceiling",
            severity: "advisory",
            detail: "manifest is " + manifest_lines + " lines; approaching ceiling at 2000. Consider compacting structured note fields or splitting via part_of before the next session boundary."
        })

    return errors
```

---

## Layer 3 — Drift detection

**Goal:** catch cases where the manifest declares A but the diff actually did B. This layer needs access to git history and the repo's current state.

```pseudo
function check_layer_3(manifest, repo_root, git_base_ref):
    errors = []

    if not present(git_base_ref):
        return errors  # drift detection is optional

    diff = git_diff(git_base_ref, "HEAD")
    changed_files = files_in(diff)

    # 3.1 SoT-declared files must appear in diff (or be explicitly marked read-only)
    for sot in manifest.sot_map:
        if sot.role_in_change != "read_only" and looks_like_path(sot.source):
            if sot.source not in changed_files:
                errors.append({
                    rule: "drift.declared_sot_not_modified",
                    severity: "advisory",
                    detail: "declared SoT " + sot.source + " not in diff"
                })

    # 3.2 Surface declared but no consistent file family changed
    # Each stack bridge defines which path patterns correspond to which surface.
    bridge_mapping = load_stack_bridge_surface_map(repo_root)
    for s in manifest.surfaces_touched:
        if s.role == "primary":
            expected_patterns = bridge_mapping.get(s.surface, [])
            if expected_patterns and not any(matches_pattern(f, expected_patterns) for f in changed_files):
                errors.append({
                    rule: "drift.primary_surface_no_matching_file_change",
                    severity: "advisory",
                    detail: "surface " + s.surface + " declared primary but no file matching " + expected_patterns + " changed"
                })

    # 3.3 Codegen touched but generated artifacts not in diff
    if manifest.cross_cutting?.build_time_risk?.codegen_touched:
        if manifest.cross_cutting.build_time_risk.codegen_artifacts_committed:
            generated_patterns = bridge_mapping.get("__generated__", [])
            if generated_patterns and not any(matches_pattern(f, generated_patterns) for f in changed_files):
                errors.append({
                    rule: "drift.codegen_touched_but_no_generated_diff",
                    severity: "advisory"
                })

    # 3.4 Uncontrolled interface monitoring channel staleness
    for iface in manifest.uncontrolled_interfaces:
        last_check = get_last_check_timestamp(iface.monitoring_channel)
        if last_check and (today() - last_check) > config.uncontrolled_interface_max_age_days:
            errors.append({
                rule: "drift.uncontrolled_interface_not_recently_checked",
                severity: "advisory"
            })

    # 3.5 Manifest last_updated vs latest code commit
    latest_code_commit = git_log(repo_root, max_age_days=30).first
    if manifest.last_updated < latest_code_commit.timestamp:
        errors.append({
            rule: "drift.manifest_older_than_latest_code",
            severity: "advisory"
        })

    return errors
```

---

## Waiver filtering

**Goal:** let human-authorized waivers downgrade specific errors, without ever letting AI waive its own failures.

```pseudo
function apply_waivers(errors, manifest):
    filtered = []
    for err in errors:
        waiver = find_matching_waiver(err.rule, manifest.waivers)
        if waiver and waiver.approver_role == "human" and waiver.expires_at >= today():
            err.severity = "waived"
            err.waiver_id = waiver.rule_id
            err.waiver_expires = waiver.expires_at
        filtered.append(err)
    return filtered
```

**Invariants:**
- A waiver with `approver_role == "ai"` never takes effect (the schema enforces this too, but the validator must re-check it because the schema can be bypassed).
- Expired waivers do not take effect.
- Waivers only change whether the severity blocks; they do not erase the finding. The report must still mark the entry as `waived` for audit purposes.

---

## Exit code mapping

```pseudo
function compute_exit_code(errors, config):
    max_severity = none
    for err in errors:
        if err.severity == "waived": continue
        level = config.enforcement_level_for(err.rule)   # L0 / L1 / L2 / L3
        if level == "L0": continue                        # disabled
        if level in ["L2", "L3"] and err.severity == "blocking":
            max_severity = max(max_severity, "block")
        elif level == "L3" and err.severity == "advisory":
            max_severity = max(max_severity, "block")
        else:
            max_severity = max(max_severity, "warn")

    if max_severity == "block": return 2
    if max_severity == "warn":  return 1
    return 0
```

---

## Non-functional requirements

| Property | Requirement | Rationale |
|----------|-------------|-----------|
| Execution time ceiling | A single validation completes in ≤ 60 s (2000-line manifest, 10k-file repo). | A timeout is an implementation defect, not a user problem. |
| Reproducibility | Same input + same schema + same git ref → same output. | Eliminates non-determinism from time or thread scheduling. |
| Offline operability | Layer 1 & Layer 2 must run fully offline; Layer 3 may at most need a local git repo — never a remote API. | The methodology must not be captured by a vendor. |
| Exit-code stability | Only the three values 0 / 1 / 2. `1` = advisory warning, `2` = blocking. | CI engines only see the exit code; its semantics must not drift. |
| Error-message consistency | Each rule's `rule_id` is stable across versions; the message format always includes `rule_id`. | Enables downstream automation to track findings. |
| Isolation | Must not write files outside the repo; must not make remote requests unless the user explicitly opts into the Layer 3 monitoring-channel check. | Safe to run inside a sandboxed CI runner. |

---

## Division of labor with stack bridges

- **This contract (algorithm):** defines *what* to check, *how* to check it, and *how* failure signals are reported.
- **Stack bridge:** defines the `bridge_mapping` from surfaces to file-path patterns, the `__generated__` path rules, and the codegen tool association.
- **Reference implementation:** turns the algorithm above into an executable validator in a concrete language; see `reference-implementations/`.

Minimum obligations for a validator author:
1. Implement all three layers from this document.
2. Load the mapping provided by the stack bridge (do not hard-code it).
3. Honor the non-functional requirements.
4. Emit the report in a machine-readable format (JSON / SARIF / etc.).

---

## Usage rules

1. This document is a normative algorithm spec; any implementation deviation must be explicitly listed in `reference-implementations/<impl>/DEVIATIONS.md`.
2. Adding a rule: place it in the appropriate layer; rule IDs must never be reused.
3. Modifying an existing rule: bump the rule's version number and keep the old ID marked `deprecated` for at least one release.
4. Schema updates: Layer 1 picks them up automatically; Layer 2 / 3 must be reviewed in sync to see whether new fields require additional cross-reference rules.
