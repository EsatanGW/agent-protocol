#!/usr/bin/env sh
# Check that the version string is consistent across the five places
# that independently declare it:
#   1. .claude-plugin/plugin.json      -> .version
#   2. .claude-plugin/marketplace.json -> .metadata.version
#   3. README.md                       -> the "Version: X.Y.Z" badge
#   4. CHANGELOG.md                    -> the most recent non-Unreleased section
#   5. CHANGELOG.json                  -> first non-Unreleased release's .version (generated)
#
# Drift between these is the single most common release-hygiene bug.
# This check is cheap and catches it before a release tag lands.
#
# CHANGELOG.json is included because it is a generated artifact; a drift
# here almost always means "bumped CHANGELOG.md but forgot to run
# generate-changelog-json.py". The schema-drift CI job catches
# schemas/*.json drift the same way.
#
# Exit codes:
#   0 all five agree
#   1 at least one disagrees
#   2 tool error (jq missing, file unreadable)

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_root"

if ! command -v jq >/dev/null 2>&1; then
  echo "TOOL_ERROR: jq not found on PATH" >&2
  exit 2
fi

plugin_version=$(jq -r '.version' .claude-plugin/plugin.json)
marketplace_version=$(jq -r '.metadata.version' .claude-plugin/marketplace.json)

readme_version=$(grep -oE 'version-[0-9]+\.[0-9]+\.[0-9]+' README.md | head -1 | sed 's/version-//')

changelog_version=$(grep -oE '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' CHANGELOG.md | head -1 | sed 's/^## \[\(.*\)\]/\1/')

if [ -f CHANGELOG.json ]; then
  # Filter out an Unreleased entry — the generator (generate-changelog-json.py)
  # keeps [Unreleased] in .releases[] when it has sections, so .releases[0] is
  # not guaranteed to be a numbered release. Symmetric with line 38 which
  # already filters Unreleased out of the CHANGELOG.md comparison.
  changelog_json_version=$(jq -r '[.releases[] | select(.version != "Unreleased")][0].version' CHANGELOG.json 2>/dev/null || echo "")
else
  changelog_json_version="<missing>"
fi

fail=0
report() {
  printf '  %-36s %s\n' "$1" "$2"
}

echo "Version consistency check:"
report "plugin.json .version" "$plugin_version"
report "marketplace.json .metadata.version" "$marketplace_version"
report "README.md badge" "$readme_version"
report "CHANGELOG.md latest release" "$changelog_version"
report "CHANGELOG.json first non-Unreleased" "$changelog_json_version"

if [ "$plugin_version" != "$marketplace_version" ]; then
  echo "DRIFT: plugin.json vs marketplace.json" >&2
  fail=1
fi
if [ "$plugin_version" != "$readme_version" ]; then
  echo "DRIFT: plugin.json vs README badge" >&2
  fail=1
fi
if [ "$plugin_version" != "$changelog_version" ]; then
  echo "DRIFT: plugin.json vs CHANGELOG latest release" >&2
  fail=1
fi
if [ "$plugin_version" != "$changelog_json_version" ]; then
  echo "DRIFT: plugin.json vs CHANGELOG.json first non-Unreleased release" >&2
  echo "  Hint: regenerate with 'python3 .github/scripts/generate-changelog-json.py'" >&2
  fail=1
fi

if [ $fail -eq 0 ]; then
  echo "OK: all five declarations agree on $plugin_version"
fi
exit $fail
