#!/usr/bin/env sh
# agent-protocol runtime hook
#   category: C (drift)
#   trigger:  post-tool-use:Edit | pre-tool-use:Bash("git commit*")
#   level:    warn
#   rule_id:  drift.doc-refresh-missing
#   see:      docs/runtime-hook-contract.md §category-c-drift-hook
#             docs/automation-contract.md §Tier 3
#
# Warns when a file declared in sot_map[*].source is being edited in the
# current diff but no documentation, spec, or manifest file is being edited
# alongside. SoTs are by definition documented surfaces — an edit to one
# without a paired doc update is either a documentation drift that future
# readers will hit, or a registration gap (the file should not have been
# registered as an SoT). Non-blocking by design: many in-flight edits
# legitimately precede the doc update; this hook surfaces the risk, it does
# not gate the edit.

set -eu

MANIFEST_PATH="${AGENT_PROTOCOL_MANIFEST_PATH:-}"
if [ -z "$MANIFEST_PATH" ]; then
  MANIFEST_PATH=$(git ls-files 'change-manifest*.yaml' 2>/dev/null | head -1 || true)
fi

if [ -z "$MANIFEST_PATH" ] || [ ! -f "$MANIFEST_PATH" ]; then
  exit 0
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "[agent-protocol/drift.doc-refresh-missing] TOOL_ERROR: yq not found on PATH; skipping doc-refresh check" >&2
  exit 2
fi

touched=$(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null)
if [ -z "$touched" ]; then
  exit 0
fi

# Find SoT source files actually touched in this diff.
# Iterate via newline-delimited read so paths with whitespace are handled as
# data, not shell tokens.
sot_touched=$(yq -r '.sot_map[].source' "$MANIFEST_PATH" 2>/dev/null \
  | grep -v '^null$' | grep -v '^$' \
  | while IFS= read -r src; do
      # Strip any "field:" suffix (e.g. "app/models/voucher.py:expiry_at") down to the filename.
      file_part=${src%%:*}
      [ -z "$file_part" ] && continue
      if printf '%s\n' "$touched" | grep -Fxq -- "$file_part"; then
        printf '%s\n' "$file_part"
      fi
    done)

if [ -z "$sot_touched" ]; then
  # No declared SoT source files were edited in this diff; nothing to check.
  exit 0
fi

# A documentation refresh in this diff is any of:
#   - any *.md file
#   - any file under docs/
#   - any change-manifest*.yaml
# This list intentionally errs broad — the cost of a false-pass (treating a
# trivial doc edit as a refresh) is much lower than a false-warn that trains
# users to ignore the hook.
doc_touched=$(printf '%s\n' "$touched" \
  | grep -E '\.md$|^docs/|change-manifest.*\.yaml$' \
  || true)

if [ -n "$doc_touched" ]; then
  exit 0
fi

# SoT source(s) edited, no doc/manifest update in the same diff.
{
  printf '[agent-protocol/drift.doc-refresh-missing] declared SoT source(s) edited without paired doc/spec/manifest update:\n'
  printf '  edited SoT files:\n'
  printf '%s\n' "$sot_touched" | sed 's/^/    - /'
  printf '  remediation: update the relevant docs/, *.md, or change-manifest*.yaml in the same change.\n'
  printf '  see: docs/runtime-hook-contract.md §Category C, docs/automation-contract.md §Tier 3.\n'
} >&2
exit 2
