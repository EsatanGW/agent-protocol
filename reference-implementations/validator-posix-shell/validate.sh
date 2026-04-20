#!/bin/sh
# validate.sh — reference implementation of the automation contract
#
# Reference: docs/automation-contract-algorithm.md
# Deviations: ./DEVIATIONS.md
#
# Exit codes:
#   0 = clean (or only waived / L0-disabled findings)
#   1 = advisory warnings
#   2 = blocking findings

set -eu

if [ "$#" -lt 3 ]; then
    echo "usage: $0 <manifest.yaml> <repo_root> <schema_path> [git_base_ref]" >&2
    exit 64
fi

MANIFEST="$1"
REPO_ROOT="$2"
SCHEMA="$3"
BASE_REF="${4:-}"
SCHEMA_VALIDATOR="${SCHEMA_VALIDATOR:-check-jsonschema}"

TODAY=$(date -u +%Y-%m-%d)

findings=""
worst_severity=0   # 0=clean, 1=advisory, 2=blocking

emit() {
    # emit <severity> <rule_id> <detail>
    sev="$1"; rule="$2"; detail="$3"
    findings="${findings}${sev}\t${rule}\t${detail}\n"
    case "$sev" in
        blocking)
            [ "$worst_severity" -lt 2 ] && worst_severity=2 || true ;;
        advisory)
            [ "$worst_severity" -lt 1 ] && worst_severity=1 || true ;;
    esac
}

q() { yq -r "$1" "$MANIFEST" 2>/dev/null || echo ""; }
qn() { yq "$1" "$MANIFEST" 2>/dev/null || echo "null"; }

# ─── Layer 1: structural validity ──────────────────────────────────────────

# 1.1 JSON Schema
if command -v "$SCHEMA_VALIDATOR" >/dev/null 2>&1; then
    if ! "$SCHEMA_VALIDATOR" --schemafile "$SCHEMA" "$MANIFEST" >/dev/null 2>&1; then
        emit blocking "schema.validation_failed" "manifest does not satisfy $SCHEMA"
    fi
else
    emit advisory "schema.validator_missing" "$SCHEMA_VALIDATOR not installed; skipping Layer 1.1"
fi

# 1.2 change_id format
cid=$(q '.change_id')
echo "$cid" | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$' \
    || emit blocking "change_id.format" "change_id '$cid' does not match YYYY-MM-DD-slug"

# 1.4 Waiver invariants
waiver_count=$(q '.waivers | length')
i=0
while [ "$i" -lt "${waiver_count:-0}" ]; do
    role=$(q ".waivers[$i].approver_role")
    expires=$(q ".waivers[$i].expires_at")
    rule=$(q ".waivers[$i].rule_id")

    [ "$role" = "human" ] \
        || emit blocking "waiver.approver_must_be_human" "waiver on rule=$rule has approver_role=$role"
    [ -z "$expires" ] \
        && emit blocking "waiver.must_be_time_bounded" "waiver on rule=$rule has no expires_at"
    if [ -n "$expires" ] && [ "$expires" \< "$TODAY" ]; then
        emit blocking "waiver.expired" "waiver on rule=$rule expired $expires"
    fi
    i=$((i + 1))
done

# ─── Layer 2: cross-reference consistency ─────────────────────────────────

# 2.1 Primary surface → evidence_plan coverage
primary=$(q '.surfaces_touched[] | select(.role == "primary") | .surface' | sort -u)
evidence_surfaces=$(q '.evidence_plan[].surface' | sort -u)
for p in $primary; do
    echo "$evidence_surfaces" | grep -qx "$p" \
        || emit blocking "evidence.primary_surface_required" "primary surface '$p' has no evidence_plan entry"
done

# 2.2 SoT source file existence (when source looks like a path)
sot_count=$(q '.sot_map | length')
i=0
while [ "$i" -lt "${sot_count:-0}" ]; do
    src=$(q ".sot_map[$i].source")
    if echo "$src" | grep -Eq '^[a-zA-Z0-9_./-]+$' && echo "$src" | grep -q '/'; then
        [ -e "$REPO_ROOT/$src" ] \
            || emit blocking "sot.source_file_missing" "$src referenced but not found"
    fi
    i=$((i + 1))
done

# 2.3 Collected evidence must have artifact_location
ev_count=$(q '.evidence_plan | length')
i=0
while [ "$i" -lt "${ev_count:-0}" ]; do
    st=$(q ".evidence_plan[$i].status")
    loc=$(q ".evidence_plan[$i].artifact_location")
    if [ "$st" = "collected" ] && [ -z "$loc" ]; then
        emit blocking "evidence.collected_requires_location" "evidence[$i] status=collected but no artifact_location"
    fi
    if [ "$st" = "collected" ] && [ -n "$loc" ]; then
        if echo "$loc" | grep -Eq '^[a-zA-Z0-9_./-]+$' && echo "$loc" | grep -q '/'; then
            [ -e "$REPO_ROOT/$loc" ] \
                || emit advisory "evidence.artifact_missing" "artifact $loc not found"
        fi
    fi
    i=$((i + 1))
done

# 2.6 Breaking change L3/L4 requires a deprecation path.
#     Accept either `deprecation_timeline` (legacy, dates only) or
#     `deprecation` (structured marker introduced in schema 1.7.0).
level=$(q '.breaking_change.level')
if [ "$level" = "L3" ] || [ "$level" = "L4" ]; then
    tl=$(qn '.breaking_change.deprecation_timeline')
    dep=$(qn '.breaking_change.deprecation')
    if [ "$tl" = "null" ] && [ "$dep" = "null" ]; then
        emit blocking "breaking_change.l3_l4_requires_deprecation" "level=$level but neither deprecation_timeline nor deprecation"
    fi
fi

# 2.7 Rollback mode 3 requires compensation_plan
mode=$(q '.rollback.overall_mode')
if [ "$mode" = "3" ]; then
    cp=$(q '.rollback.compensation_plan')
    [ -z "$cp" ] \
        && emit blocking "rollback.mode_3_requires_compensation" "rollback mode=3 but no compensation_plan"
fi

# 2.8 Delivered status requires human approval
status=$(q '.status')
phase=$(q '.phase')
if [ "$status" = "delivered" ] || [ "$phase" = "deliver" ]; then
    humans=$(q '.approvals[] | select(.role == "human") | .approver' | wc -l)
    [ "${humans:-0}" -eq 0 ] \
        && emit blocking "approval.human_required_for_delivery" "delivered without human approval"
fi

# 2.9 Experience surface requires playtest
has_experience=$(q '.surfaces_touched[] | select(.surface == "experience") | .surface' | head -n1)
if [ -n "$has_experience" ]; then
    pt=$(qn '.playtest')
    [ "$pt" = "null" ] \
        && emit blocking "playtest.required_for_experience_surface" "experience surface touched but no playtest block"
fi

# 2.10 Observe phase requires handoff_narrative
if [ "$phase" = "observe" ]; then
    hn=$(q '.handoff_narrative')
    [ -z "$hn" ] \
        && emit blocking "handoff.narrative_required_for_observe" "phase=observe but no handoff_narrative"
fi

# 2.11 Evidence tier floor under high-severity conditions.
#      Added in schema 1.8. If breaking_change.level >= L2, rollback mode 3,
#      or a high-risk surface (compliance / real_world / experience) is
#      touched with role=primary, at least one evidence entry must have
#      tier=critical. Missing `tier` is treated as standard (pre-1.8
#      manifests remain valid — the rule only fires when the manifest
#      itself declares high severity).
high_severity=0
case "$level" in
    L2|L3|L4) high_severity=1 ;;
esac
[ "$mode" = "3" ] && high_severity=1
hr_primary=$(q '.surfaces_touched[] | select(.role == "primary") | select(.surface == "compliance" or .surface == "real_world" or .surface == "experience") | .surface' | head -n1)
[ -n "$hr_primary" ] && high_severity=1

if [ "$high_severity" = "1" ]; then
    has_critical=$(q '.evidence_plan[] | select(.tier == "critical") | .tier' | head -n1)
    if [ -z "$has_critical" ]; then
        # Build detail with the triggers that fired.
        triggers=""
        case "$level" in
            L2|L3|L4) triggers="breaking_change.level=$level" ;;
        esac
        if [ "$mode" = "3" ]; then
            [ -n "$triggers" ] && triggers="$triggers / rollback.overall_mode=3" \
                || triggers="rollback.overall_mode=3"
        fi
        if [ -n "$hr_primary" ]; then
            [ -n "$triggers" ] && triggers="$triggers / high-risk surface '$hr_primary' with role=primary" \
                || triggers="high-risk surface '$hr_primary' with role=primary"
        fi
        emit blocking "evidence.critical_required_for_high_severity" \
            "at least one evidence_plan entry must be tier=critical when $triggers"
    fi
fi

# ─── Layer 3: drift detection (optional, requires base ref) ───────────────

if [ -n "$BASE_REF" ] && command -v git >/dev/null 2>&1; then
    ( cd "$REPO_ROOT" && git rev-parse "$BASE_REF" >/dev/null 2>&1 ) || BASE_REF=""
fi

if [ -n "$BASE_REF" ]; then
    changed=$( cd "$REPO_ROOT" && git diff --name-only "$BASE_REF" HEAD )

    # 3.1 Declared SoT not modified
    sot_count=$(q '.sot_map | length')
    i=0
    while [ "$i" -lt "${sot_count:-0}" ]; do
        src=$(q ".sot_map[$i].source")
        if echo "$src" | grep -Eq '^[a-zA-Z0-9_./-]+$' && echo "$src" | grep -q '/'; then
            echo "$changed" | grep -qFx "$src" \
                || emit advisory "drift.declared_sot_not_modified" "SoT $src declared but not in diff"
        fi
        i=$((i + 1))
    done

    # 3.5 Manifest last_updated vs latest code commit
    mf_ts=$(q '.last_updated')
    if [ -n "$mf_ts" ]; then
        latest_commit_ts=$( cd "$REPO_ROOT" && git log -1 --format=%cI HEAD )
        if [ -n "$latest_commit_ts" ] && [ "$mf_ts" \< "$latest_commit_ts" ]; then
            emit advisory "drift.manifest_older_than_latest_code" "manifest last_updated ($mf_ts) < latest commit ($latest_commit_ts)"
        fi
    fi
fi

# ─── Report ───────────────────────────────────────────────────────────────

printf "%b" "$findings" | awk -F'\t' 'NF >= 3 { printf "[%s] %s — %s\n", $1, $2, $3 }'

case "$worst_severity" in
    0) echo "OK — no findings"; exit 0 ;;
    1) echo "WARN — advisory findings only"; exit 1 ;;
    2) echo "FAIL — blocking findings"; exit 2 ;;
esac
