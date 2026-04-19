#!/usr/bin/env sh
# agent-protocol runtime hook
#   category: B (evidence)
#   trigger:  pre-commit, post-tool-use:Edit
#   level:    block on missing path; warn on well-formed-but-empty
#   rule_id:  evidence.artifact-exists
#   see:      docs/runtime-hook-contract.md §category-b-evidence-hook
#
# For every evidence_plan entry with status=collected, verify that
# artifact_location resolves to a real file or URL. Empty locations or
# dangling paths fail the hook.

set -eu

MANIFEST_PATH="${AGENT_PROTOCOL_MANIFEST_PATH:-}"
if [ -z "$MANIFEST_PATH" ]; then
  MANIFEST_PATH=$(git ls-files 'change-manifest*.yaml' 2>/dev/null | head -1 || true)
fi

if [ -z "$MANIFEST_PATH" ] || [ ! -f "$MANIFEST_PATH" ]; then
  exit 0
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "[agent-protocol/evidence.artifact-exists] TOOL_ERROR: yq not found on PATH; skipping evidence check" >&2
  exit 2
fi

missing=""
empty_location=""

# Iterate every evidence_plan entry. Each entry is emitted as: <status>|<location>
yq -r '.evidence_plan[] | [.status, (.artifact_location // "")] | @tsv' "$MANIFEST_PATH" 2>/dev/null | while IFS="	" read -r status location; do
  if [ "$status" = "collected" ]; then
    if [ -z "$location" ]; then
      printf '[agent-protocol/evidence.artifact-exists] status=collected but artifact_location is empty in %s\n' "$MANIFEST_PATH" >&2
      exit 1
    fi
    case "$location" in
      http://*|https://*)
        ;;
      *)
        if [ ! -e "$location" ]; then
          printf '[agent-protocol/evidence.artifact-exists] artifact_location missing: %s (referenced in %s)\n' "$location" "$MANIFEST_PATH" >&2
          exit 1
        fi
        ;;
    esac
  fi
done

exit 0
