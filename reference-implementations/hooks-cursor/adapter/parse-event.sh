#!/usr/bin/env sh
# Cursor event → AP_* normalization.
#
# Not invoked directly by the reference hooks today — they read git /
# manifest instead of the event payload. Sourced by any future hook
# that wants a stable cross-runtime event shape:
#
#   . ./reference-implementations/hooks-cursor/adapter/parse-event.sh
#
# Exports:
#   AP_EVENT         — one of: pre-commit, post-file-edit, pre-push, on-stop
#   AP_TOOL          — runtime-native tool name if discoverable, else ""
#   AP_STAGED_FILES  — newline-separated list, may be empty
#   AP_PHASE         — manifest phase if discoverable, else ""

set -u

AP_EVENT="${CURSOR_HOOK_TRIGGER:-}"
AP_TOOL="${CURSOR_TOOL:-}"
AP_PHASE=""

AP_STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)

if [ -n "${AGENT_PROTOCOL_MANIFEST_PATH:-}" ] && [ -f "$AGENT_PROTOCOL_MANIFEST_PATH" ] && command -v yq >/dev/null 2>&1; then
  AP_PHASE=$(yq -r '.phase // ""' "$AGENT_PROTOCOL_MANIFEST_PATH" 2>/dev/null || true)
fi

export AP_EVENT AP_TOOL AP_STAGED_FILES AP_PHASE
