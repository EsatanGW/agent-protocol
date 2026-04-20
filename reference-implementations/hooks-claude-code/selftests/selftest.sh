#!/usr/bin/env sh
# Entry point for the hook bundle self-test. Walks every directory under
# selftests/fixtures/<hook-name>/<case-name>/ and dispatches it to run-case.sh.
#
# Exit codes:
#   0   all cases pass
#   1   one or more cases failed
#   64  harness misuse (missing files, non-executable hook, etc.)
#
# Output is a TAP-ish stream:
#   ok 3 - manifest-required/pass-docs-only
#   not ok 4 - evidence-artifact-exists/fail-blank-location
# followed by a short summary line.

set -eu

selftests_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
fixtures_dir="$selftests_dir/fixtures"
runner="$selftests_dir/run-case.sh"

if [ ! -x "$runner" ]; then
  chmod +x "$runner" 2>/dev/null || true
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "# warning: yq not found on PATH; evidence / sot-drift / completion-audit cases" >&2
  echo "#          will exercise the TOOL_ERROR degradation branch (exit=2)" >&2
fi

# Ensure stub and hooks are executable even on a fresh clone.
chmod +x "$selftests_dir/stubs"/* 2>/dev/null || true
chmod +x "$selftests_dir/../hooks"/*.sh 2>/dev/null || true

total=0
failed=0
index=0

for hook_case_dir in "$fixtures_dir"/*/; do
  [ -d "$hook_case_dir" ] || continue
  hook_dir_name=$(basename "$hook_case_dir")
  hook_script="$hook_dir_name.sh"

  for case_dir in "$hook_case_dir"*/; do
    [ -d "$case_dir" ] || continue
    case_name=$(basename "$case_dir")
    index=$((index + 1))
    total=$((total + 1))
    label="$hook_dir_name/$case_name"

    if "$runner" "$hook_script" "$case_dir" >/tmp/selftest-case.out 2>&1; then
      printf 'ok %s - %s\n' "$index" "$label"
    else
      failed=$((failed + 1))
      printf 'not ok %s - %s\n' "$index" "$label"
      sed 's/^/#   /' /tmp/selftest-case.out
    fi
  done
done

rm -f /tmp/selftest-case.out

printf '# %s cases, %s failed\n' "$total" "$failed"

if [ "$failed" -gt 0 ]; then
  exit 1
fi
exit 0
