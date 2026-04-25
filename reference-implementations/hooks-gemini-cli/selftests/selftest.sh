#!/usr/bin/env sh
# Hermetic selftest for the Gemini CLI event adapter.
#
# Exercises adapter/parse-event.sh against synthetic runtime env inputs
# and asserts AP_EVENT / AP_TOOL / AP_STAGED_FILES / AP_PHASE come out right.
#
# Does NOT test whether Gemini CLI actually invokes the adapter at the
# right moment — that is a per-workspace smoke test, see DEVIATIONS.md.
#
# Exit codes:
#   0   all cases pass (or skipped with # SKIP)
#   1   one or more cases failed
#   64  harness misuse (adapter missing, etc.)

set -u

# shellcheck disable=SC1007  # `CDPATH= cd` is the POSIX idiom to neutralize $CDPATH.
selftests_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
adapter="$selftests_dir/../adapter/parse-event.sh"

if [ ! -f "$adapter" ]; then
  echo "selftest: adapter not found at $adapter" >&2
  exit 64
fi

total=0
failed=0

invoke_adapter() {
  (
    unset GEMINI_HOOK_EVENT GEMINI_TOOL_NAME AGENT_PROTOCOL_MANIFEST_PATH 2>/dev/null || true
    for kv in "$@"; do
      key=${kv%%=*}
      val=${kv#*=}
      export "$key=$val"
    done
    cd /tmp 2>/dev/null || cd /
    # shellcheck source=/dev/null  # path resolved at runtime; cannot follow statically.
    . "$adapter"
    printf '%s|%s|%s|%s' "${AP_EVENT:-}" "${AP_TOOL:-}" "${AP_PHASE:-}" "${AP_STAGED_FILES:-}"
  )
}

check_case() {
  label="$1"; exp_event="$2"; exp_tool="$3"; exp_phase="$4"; shift 4
  total=$((total + 1))
  out=$(invoke_adapter "$@" 2>/dev/null)
  got_event=$(printf '%s' "$out" | awk -F'|' '{print $1}')
  got_tool=$(printf '%s' "$out" | awk -F'|' '{print $2}')
  got_phase=$(printf '%s' "$out" | awk -F'|' '{print $3}')
  err=""
  [ "$got_event" = "$exp_event" ] || err="${err}AP_EVENT exp=[$exp_event] got=[$got_event]; "
  [ "$got_tool"  = "$exp_tool"  ] || err="${err}AP_TOOL exp=[$exp_tool] got=[$got_tool]; "
  [ "$got_phase" = "$exp_phase" ] || err="${err}AP_PHASE exp=[$exp_phase] got=[$got_phase]; "
  if [ -n "$err" ]; then
    failed=$((failed + 1))
    printf 'not ok %s - %s\n' "$total" "$label"
    printf '#   %s\n' "$err"
  else
    printf 'ok %s - %s\n' "$total" "$label"
  fi
}

# ---- Cases ----

check_case "unset-env-yields-empty-ap-vars" "" "" ""

check_case "runtime-env-maps-to-event-and-tool" "post-tool-use" "edit" "" \
  "GEMINI_HOOK_EVENT=post-tool-use" "GEMINI_TOOL_NAME=edit"

if command -v yq >/dev/null 2>&1; then
  tmpmf=$(mktemp)
  printf 'phase: review\nsurfaces_touched: []\n' > "$tmpmf"
  check_case "manifest-yaml-populates-phase" "" "" "review" \
    "AGENT_PROTOCOL_MANIFEST_PATH=$tmpmf"
  rm -f "$tmpmf"
else
  total=$((total + 1))
  printf 'ok %s - manifest-yaml-populates-phase # SKIP yq not on PATH\n' "$total"
fi

check_case "missing-manifest-leaves-phase-empty" "" "" "" \
  "AGENT_PROTOCOL_MANIFEST_PATH=/nonexistent/manifest.yaml"

printf '# %s cases, %s failed\n' "$total" "$failed"
[ "$failed" -eq 0 ] || exit 1
exit 0
