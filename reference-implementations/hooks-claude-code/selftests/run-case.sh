#!/usr/bin/env sh
# Runs a single fixture case against a hook.
# Usage: run-case.sh <hook-name> <case-dir>
#
# Each case-dir is expected to contain:
#   expected      — required. Lines of the form:
#                     exit=<code>
#                     stderr~=<extended-regex>      (optional, may repeat)
#                     stdout~=<extended-regex>      (optional, may repeat)
#   event.json    — optional. Piped on stdin to the hook.
#   staged        — optional. Returned by `git diff --cached --name-only`.
#   unstaged      — optional. Returned by `git diff --name-only`.
#   ls-files      — optional. Returned by `git ls-files 'change-manifest*.yaml'`.
#   manifest.yaml — optional. Path exported as AGENT_PROTOCOL_MANIFEST_PATH.
#   env           — optional. Sourced before invoking the hook.

set -eu

if [ $# -lt 2 ]; then
  echo "usage: run-case.sh <hook-name> <case-dir>" >&2
  exit 64
fi

hook_name="$1"
case_dir="$2"

# shellcheck disable=SC1007  # `CDPATH= cd` is the POSIX idiom to neutralize $CDPATH.
selftests_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck disable=SC1007
bundle_dir=$(CDPATH= cd -- "$selftests_dir/.." && pwd)
hook_path="$bundle_dir/hooks/$hook_name"

if [ ! -x "$hook_path" ]; then
  echo "run-case.sh: hook not executable: $hook_path" >&2
  exit 64
fi
if [ ! -d "$case_dir" ]; then
  echo "run-case.sh: case dir missing: $case_dir" >&2
  exit 64
fi
if [ ! -f "$case_dir/expected" ]; then
  echo "run-case.sh: expected file missing in $case_dir" >&2
  exit 64
fi

# shellcheck disable=SC1007
SELFTEST_CASE_DIR=$(CDPATH= cd -- "$case_dir" && pwd)
export SELFTEST_CASE_DIR

PATH="$selftests_dir/stubs:$PATH"
export PATH

if [ -f "$case_dir/manifest.yaml" ]; then
  AGENT_PROTOCOL_MANIFEST_PATH="$SELFTEST_CASE_DIR/manifest.yaml"
  export AGENT_PROTOCOL_MANIFEST_PATH
else
  unset AGENT_PROTOCOL_MANIFEST_PATH || true
fi

if [ -f "$case_dir/env" ]; then
  # shellcheck disable=SC1091
  . "$case_dir/env"
fi

tmp_out=$(mktemp)
tmp_err=$(mktemp)
trap 'rm -f "$tmp_out" "$tmp_err"' EXIT

stdin_file="/dev/null"
if [ -f "$case_dir/event.json" ]; then
  stdin_file="$SELFTEST_CASE_DIR/event.json"
fi

set +e
(cd "$SELFTEST_CASE_DIR" && "$hook_path" < "$stdin_file" > "$tmp_out" 2> "$tmp_err")
actual_exit=$?
set -e

failures=""
expected_exit=""

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    ""|"#"*) ;;
    "exit="*)
      expected_exit=${line#exit=}
      ;;
    "stderr~="*)
      pattern=${line#stderr~=}
      if ! grep -Eq "$pattern" "$tmp_err"; then
        failures="$failures stderr-missing:$pattern"
      fi
      ;;
    "stdout~="*)
      pattern=${line#stdout~=}
      if ! grep -Eq "$pattern" "$tmp_out"; then
        failures="$failures stdout-missing:$pattern"
      fi
      ;;
  esac
done < "$case_dir/expected"

if [ -z "$expected_exit" ]; then
  echo "run-case.sh: no exit=<code> line in $case_dir/expected" >&2
  exit 64
fi

if [ "$actual_exit" != "$expected_exit" ]; then
  failures="$failures exit-mismatch:expected=$expected_exit:actual=$actual_exit"
fi

if [ -n "$failures" ]; then
  printf 'FAIL %s/%s\n' "$hook_name" "$(basename "$case_dir")"
  printf '  reasons:%s\n' "$failures"
  if [ -s "$tmp_err" ]; then
    printf '  stderr: '
    sed 's/^/    /' "$tmp_err"
  fi
  exit 1
fi

exit 0
