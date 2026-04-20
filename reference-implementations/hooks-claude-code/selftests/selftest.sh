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

have_yq=1
if ! command -v yq >/dev/null 2>&1; then
  have_yq=0
fi

# Hook directories whose fixtures exercise yq-parsed manifest queries.
# When yq is absent the hooks correctly degrade to TOOL_ERROR/exit=2, but
# fixtures assert specific exit codes (0 or 1) that assume yq is present —
# so we skip them cleanly rather than emit spurious FAILs. Mirrors the
# adapter selftests' `# SKIP yq not on PATH` pattern.
yq_dependent_dirs="completion-audit consumer-registry-check evidence-artifact-exists sot-drift-check"

# Ensure stub and hooks are executable even on a fresh clone.
chmod +x "$selftests_dir/stubs"/* 2>/dev/null || true
chmod +x "$selftests_dir/../hooks"/*.sh 2>/dev/null || true

total=0
failed=0
skipped=0
index=0

for hook_case_dir in "$fixtures_dir"/*/; do
  [ -d "$hook_case_dir" ] || continue
  hook_dir_name=$(basename "$hook_case_dir")
  hook_script="$hook_dir_name.sh"

  needs_yq=0
  for d in $yq_dependent_dirs; do
    [ "$d" = "$hook_dir_name" ] && needs_yq=1
  done

  for case_dir in "$hook_case_dir"*/; do
    [ -d "$case_dir" ] || continue
    case_name=$(basename "$case_dir")
    index=$((index + 1))
    total=$((total + 1))
    label="$hook_dir_name/$case_name"

    if [ "$needs_yq" = 1 ] && [ "$have_yq" = 0 ]; then
      skipped=$((skipped + 1))
      printf 'ok %s - %s # SKIP yq not on PATH\n' "$index" "$label"
      continue
    fi

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

if [ "$skipped" -gt 0 ]; then
  printf '# %s cases, %s failed, %s skipped\n' "$total" "$failed" "$skipped"
else
  printf '# %s cases, %s failed\n' "$total" "$failed"
fi

if [ "$failed" -gt 0 ]; then
  exit 1
fi
exit 0
