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

# shellcheck disable=SC1007  # `CDPATH= cd` is the POSIX idiom to neutralize $CDPATH.
selftests_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
fixtures_dir="$selftests_dir/fixtures"
runner="$selftests_dir/run-case.sh"

if [ ! -x "$runner" ]; then
  chmod +x "$runner" 2>/dev/null || true
fi

have_yq=1
yq_skip_reason="yq not on PATH"
if ! command -v yq >/dev/null 2>&1; then
  have_yq=0
else
  # Hook scripts use mikefarah/yq (Go) syntax — `--front-matter=extract`,
  # `.. | select(has(...))`, `-p json`. The other yq on PATH is the Python
  # `kislyuk/yq` wrapper around jq, which has different semantics: `has()` errors
  # on primitives during recursive descent, and `--front-matter=extract` is not
  # a recognised option. Treat that variant as "yq absent" for selftest purposes
  # so a contributor running locally with the wrong yq sees a clean SKIP plus a
  # remediation pointer rather than spurious FAILs.
  #
  # mikefarah/yq prints `mikefarah/yq` or `version v4.x.x` (older builds print
  # `yq (https://github.com/mikefarah/yq/) version 4.x.x`); kislyuk/yq prints
  # `yq <version>` followed by its jq dependency. Match the former cheaply via
  # the substring `mikefarah` — it appears in every mikefarah variant's version
  # string and never in kislyuk's.
  yq_version_line=$(yq --version 2>/dev/null || true)
  case "$yq_version_line" in
    *mikefarah*)
      ;;
    *)
      have_yq=0
      yq_skip_reason="yq is not mikefarah/yq (Go); see reference-implementations/hooks-claude-code/README.md §Dependencies"
      ;;
  esac
fi

# Hook directories whose fixtures exercise mikefarah/yq-specific manifest
# queries. When the right yq is absent the hooks correctly degrade to
# TOOL_ERROR/exit=2 (or silently mis-classify, in the case of frontmatter
# parsing); fixtures assert the success path which assumes the right yq is
# present — so we skip them cleanly rather than emit spurious FAILs. Mirrors
# the adapter selftests' `# SKIP yq not on PATH` pattern.
#
# The list must be kept in sync with the set of hooks that use mikefarah-only
# yq syntax. As of 1.31.1: cckn-canonical-sync-check uses `--front-matter=extract`;
# consumer-registry-check uses `.. | select(has(...))`. Other yq-using hooks
# (drift-doc-refresh, manifest-required, evidence-artifact-exists, etc.) use
# the dialect-portable subset and pass under either variant — but they remain
# in the list as a precaution against future syntax additions.
yq_dependent_dirs="cckn-canonical-sync-check completion-audit consumer-registry-check evidence-artifact-exists sot-drift-check"

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
      printf 'ok %s - %s # SKIP %s\n' "$index" "$label" "$yq_skip_reason"
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
