#!/usr/bin/env sh
# agent-protocol runtime hook
#   category: C (drift)
#   trigger:  pre-tool-use:Bash(git push*) or session-stop
#   level:    warn (exit 2 — never blocks)
#   rule_id:  drift.cckn-mirrors-canonical-stale
#   see:      docs/cross-change-knowledge.md §Mirroring canonical methodology SoT
#
# Walks the project's CCKN directory, parses each CCKN's frontmatter, and
# warns when a CCKN that declares `mirrors_canonical` has drifted relative
# to the canonical SoT it mirrors. Drift signals:
#
#   1. The SoT file at `path` has commits in its git history strictly after
#      the CCKN's `updated` date.
#   2. The `methodology_version` field, if present, does not match the
#      version pinned in the consumer project (env var
#      AGENT_PROTOCOL_VERSION; if unset, version-mismatch check is skipped).
#
# Non-blocking by design: drift is a signal for the human author to decide
# whether to refresh, supersede, or accept; the hook does not gate work.

set -eu

CCKN_DIR="${CCKN_DIR:-docs/knowledge}"
PINNED_VERSION="${AGENT_PROTOCOL_VERSION:-}"

if [ ! -d "$CCKN_DIR" ]; then
  # Absent CCKN directory is not a failure (consistent with the
  # methodology's "absent directory = no-op" convention).
  exit 0
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "[agent-protocol/drift.cckn-mirrors-canonical-stale] TOOL_ERROR: yq not found on PATH; skipping CCKN sync check" >&2
  exit 2
fi

if ! command -v git >/dev/null 2>&1; then
  # Without git, we cannot compute SoT mtime; skip gracefully.
  exit 0
fi

warns=""

# Walk every .md file in the CCKN directory; parse frontmatter; check mirror
# entries. yq's --front-matter=extract reads YAML frontmatter directly out of
# a markdown file, which is the exact shape CCKN frontmatter uses.
for cckn in "$CCKN_DIR"/*.md; do
  [ -f "$cckn" ] || continue

  # When the .md file has no frontmatter at all (e.g. a README.md beside the
  # CCKN files), yq with --front-matter=extract returns empty, not "0". Treat
  # empty as "no mirrors declared" so the loop skips the file silently rather
  # than mis-report it as "declares mirrors_canonical but has no updated date".
  mirror_count=$(yq --front-matter=extract '.mirrors_canonical | length // 0' "$cckn" 2>/dev/null || echo 0)
  [ -z "$mirror_count" ] && mirror_count=0
  [ "$mirror_count" = "0" ] && continue

  cckn_updated=$(yq --front-matter=extract '.updated' "$cckn" 2>/dev/null || echo "")
  if [ -z "$cckn_updated" ] || [ "$cckn_updated" = "null" ]; then
    warns="${warns}[agent-protocol/drift.cckn-mirrors-canonical-stale] $cckn declares mirrors_canonical but has no \`updated\` date — cannot compute drift
"
    continue
  fi

  # Iterate each mirror entry. yq's index iteration via .[] gives us one
  # YAML doc per entry; --front-matter=extract isolates the frontmatter.
  i=0
  while [ "$i" -lt "$mirror_count" ]; do
    sot_path=$(yq --front-matter=extract ".mirrors_canonical[$i].path" "$cckn" 2>/dev/null || echo "")
    sot_section=$(yq --front-matter=extract ".mirrors_canonical[$i].section // \"\"" "$cckn" 2>/dev/null || echo "")
    sot_methodology_version=$(yq --front-matter=extract ".mirrors_canonical[$i].methodology_version // \"\"" "$cckn" 2>/dev/null || echo "")
    i=$((i + 1))

    [ -z "$sot_path" ] || [ "$sot_path" = "null" ] && continue

    # Drift signal 1: SoT file has commits after CCKN's `updated` date.
    if [ -f "$sot_path" ]; then
      sot_last_commit=$(git log -1 --format=%cI -- "$sot_path" 2>/dev/null || echo "")
      if [ -n "$sot_last_commit" ]; then
        # Compare ISO 8601 dates lexicographically — works for full timestamps
        # and for date-only strings (CCKN uses YYYY-MM-DD; git log gives full
        # timestamp, so we truncate the git output to date-only for fair
        # comparison). POSIX sh has no defined `>` operator on strings
        # (shellcheck SC3012); emulate via `sort` so the check stays
        # `-s sh` clean across the runtime-hook bundle.
        sot_date=$(echo "$sot_last_commit" | cut -c1-10)
        newest=$(printf '%s\n%s\n' "$cckn_updated" "$sot_date" | sort | tail -n 1)
        if [ "$newest" = "$sot_date" ] && [ "$sot_date" != "$cckn_updated" ]; then
          where=""
          [ -n "$sot_section" ] && [ "$sot_section" != "null" ] && where=" $sot_section"
          warns="${warns}[agent-protocol/drift.cckn-mirrors-canonical-stale] $cckn mirrors $sot_path$where — SoT last touched $sot_date, CCKN updated $cckn_updated
"
        fi
      fi
    else
      warns="${warns}[agent-protocol/drift.cckn-mirrors-canonical-stale] $cckn mirrors $sot_path which does not exist (typo or moved file)
"
    fi

    # Drift signal 2: methodology_version mismatch (only if both sides set).
    if [ -n "$PINNED_VERSION" ] && [ -n "$sot_methodology_version" ] && [ "$sot_methodology_version" != "null" ]; then
      if [ "$sot_methodology_version" != "$PINNED_VERSION" ]; then
        warns="${warns}[agent-protocol/drift.cckn-mirrors-canonical-stale] $cckn declares methodology_version=$sot_methodology_version but project is pinned to $PINNED_VERSION
"
      fi
    fi
  done
done

if [ -n "$warns" ]; then
  printf '%s' "$warns" >&2
  exit 2
fi

exit 0
