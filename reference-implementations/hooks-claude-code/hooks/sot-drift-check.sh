#!/usr/bin/env sh
# agent-protocol runtime hook
#   category: C (drift)
#   trigger:  post-tool-use:Edit
#   level:    warn
#   rule_id:  drift.sot-file-must-move
#   see:      docs/runtime-hook-contract.md §category-c-drift-hook
#
# Warns when the manifest declares an SoT source file but the current diff
# never touches that file — the hallmark of consumer-patching-without-SoT-fix.
# Non-blocking by design: edits-in-progress often haven't reached the SoT yet;
# this hook surfaces the risk, it doesn't gate the edit.

set -eu

MANIFEST_PATH="${AGENT_PROTOCOL_MANIFEST_PATH:-}"
if [ -z "$MANIFEST_PATH" ]; then
  MANIFEST_PATH=$(git ls-files 'change-manifest*.yaml' 2>/dev/null | head -1 || true)
fi

if [ -z "$MANIFEST_PATH" ] || [ ! -f "$MANIFEST_PATH" ]; then
  exit 0
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "[agent-protocol/drift.sot-file-must-move] TOOL_ERROR: yq not found on PATH; skipping drift check" >&2
  exit 2
fi

touched=$(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null)
if [ -z "$touched" ]; then
  exit 0
fi

sot_sources=$(yq -r '.sot_map[].source' "$MANIFEST_PATH" 2>/dev/null | grep -v '^null$' | grep -v '^$' || true)
if [ -z "$sot_sources" ]; then
  exit 0
fi

warn_count=0
for src in $sot_sources; do
  # Strip any "field:" suffix (e.g. "app/models/voucher.py:expiry_at") down to the filename.
  file_part=$(printf '%s\n' "$src" | cut -d: -f1)
  if [ -z "$file_part" ]; then continue; fi
  if ! printf '%s\n' "$touched" | grep -Fxq "$file_part"; then
    warn_count=$((warn_count + 1))
    printf '[agent-protocol/drift.sot-file-must-move] SoT source declared but not touched: %s\n' "$file_part" >&2
  fi
done

if [ "$warn_count" -gt 0 ]; then
  exit 2
fi

exit 0
