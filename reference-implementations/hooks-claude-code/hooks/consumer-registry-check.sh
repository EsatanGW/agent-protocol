#!/usr/bin/env sh
# agent-protocol runtime hook
#   category: C (drift)
#   trigger:  pre-tool-use:Bash("git push*"), or manual invocation
#   level:    warn (never block; network is not a correctness authority)
#   rule_id:  drift.consumer-registry-stale
#   see:      docs/runtime-hook-contract.md §category-c-drift-hook
#             docs/runtime-hook-contract.md §network-degradation-clause
#
# For every consumer in the manifest that declares an `external_registry_url`,
# probe the URL with curl. Unreachable or non-2xx responses emit an advisory
# and the hook exits with 2 (warn) — never 1 (block). This is the reference
# implementation of the contract's "checks that genuinely require network must
# degrade to advisory" clause.

set -eu

MANIFEST_PATH="${AGENT_PROTOCOL_MANIFEST_PATH:-}"
if [ -z "$MANIFEST_PATH" ]; then
  MANIFEST_PATH=$(git ls-files 'change-manifest*.yaml' 2>/dev/null | head -1 || true)
fi

if [ -z "$MANIFEST_PATH" ] || [ ! -f "$MANIFEST_PATH" ]; then
  exit 0
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "[agent-protocol/drift.consumer-registry-stale] TOOL_ERROR: yq not found on PATH; skipping consumer-registry probe" >&2
  exit 2
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[agent-protocol/drift.consumer-registry-stale] TOOL_ERROR: curl not found on PATH; skipping consumer-registry probe" >&2
  exit 2
fi

timeout_s="${AGENT_PROTOCOL_NET_TIMEOUT:-5}"

# Iterate URLs via newline-delimited read instead of unquoted word splitting,
# so URLs containing whitespace or glob metacharacters are handled as data.
# Warnings emitted on stdout inside the pipeline subshell are captured into
# $warns so the counter survives.
warns=$(yq -r '.. | select(has("external_registry_url")) | .external_registry_url' "$MANIFEST_PATH" 2>/dev/null \
  | grep -v '^$' \
  | while IFS= read -r url; do
      case "$url" in
        http://*|https://*) ;;
        *)
          # Informational: non-HTTP URL is skipped, but it does NOT count as a
          # warning. Send straight to the real stderr so it bypasses the
          # captured-stdout warning channel.
          printf '[agent-protocol/drift.consumer-registry-stale] non-HTTP consumer URL skipped: %s\n' "$url" >&2
          continue
          ;;
      esac

      if curl -fsS --max-time "$timeout_s" -o /dev/null "$url" 2>/dev/null; then
        continue
      fi

      printf '[agent-protocol/drift.consumer-registry-stale] consumer registry unreachable or non-2xx within %ss: %s\n' "$timeout_s" "$url"
    done)

if [ -n "$warns" ]; then
  printf '%s\n' "$warns" >&2
  exit 2
fi

exit 0
