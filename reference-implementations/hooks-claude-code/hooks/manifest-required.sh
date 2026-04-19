#!/usr/bin/env sh
# agent-protocol runtime hook
#   category: A (phase-gate)
#   trigger:  pre-commit
#   level:    block
#   rule_id:  phase-gate.manifest-required
#   see:      docs/runtime-hook-contract.md §category-a-phase-gate-hook
#
# Blocks the commit if the staged diff looks non-trivial and no Change Manifest
# is present or staged. Lean-mode trivial changes (single-file typos, docs-only
# commits) are exempt.

set -eu

MANIFEST_PATH="${AGENT_PROTOCOL_MANIFEST_PATH:-}"
if [ -z "$MANIFEST_PATH" ]; then
  MANIFEST_PATH=$(git ls-files 'change-manifest*.yaml' 2>/dev/null | head -1 || true)
fi

LEAN_FLAG="${AGENT_PROTOCOL_LEAN_SKIP_MANIFEST:-0}"

staged_files=$(git diff --cached --name-only 2>/dev/null || true)
if [ -z "$staged_files" ]; then
  exit 0
fi

staged_count=$(printf '%s\n' "$staged_files" | wc -l | tr -d ' ')

is_docs_only=1
printf '%s\n' "$staged_files" | while IFS= read -r f; do
  case "$f" in
    *.md|docs/*|*.txt|CHANGELOG*|LICENSE*|.gitignore) ;;
    *) exit 1 ;;
  esac
done && is_docs_only=1 || is_docs_only=0

if [ "$staged_count" -eq 1 ] || [ "$is_docs_only" = "1" ]; then
  exit 0
fi

if [ "$LEAN_FLAG" = "1" ] && [ -f "lean-mode.flag" ]; then
  exit 0
fi

if [ -z "$MANIFEST_PATH" ] || [ ! -f "$MANIFEST_PATH" ]; then
  echo "[agent-protocol/phase-gate.manifest-required] Non-trivial commit (staged files: $staged_count) has no Change Manifest. Create one per schemas/change-manifest.schema.yaml, or set AGENT_PROTOCOL_LEAN_SKIP_MANIFEST=1 with a lean-mode.flag file for trivial work." >&2
  exit 1
fi

exit 0
