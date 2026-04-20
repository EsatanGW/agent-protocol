#!/usr/bin/env sh
# Codex event → AP_* normalization.
#
# Exports:
#   AP_EVENT         — one of: pre-commit, post-tool-use, pre-push, on-stop
#   AP_TOOL          — native tool name, else ""
#   AP_STAGED_FILES  — newline-separated, may be empty
#   AP_PHASE         — manifest phase, else ""

set -u

AP_EVENT="${CODEX_HOOK_EVENT:-}"
AP_TOOL="${CODEX_TOOL_NAME:-}"
AP_PHASE=""

AP_STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)

if [ -n "${AGENT_PROTOCOL_MANIFEST_PATH:-}" ] && [ -f "$AGENT_PROTOCOL_MANIFEST_PATH" ] && command -v yq >/dev/null 2>&1; then
  AP_PHASE=$(yq -r '.phase // ""' "$AGENT_PROTOCOL_MANIFEST_PATH" 2>/dev/null || true)
fi

export AP_EVENT AP_TOOL AP_STAGED_FILES AP_PHASE
