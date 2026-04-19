#!/usr/bin/env sh
# agent-protocol runtime hook
#   category: D (completion-audit)
#   trigger:  on-stop
#   level:    block
#   rule_id:  completion.evidence-complete
#             completion.unaccepted-risk
#             completion.unresolved-escalation
#             completion.observe-needs-narrative
#   see:      docs/runtime-hook-contract.md §category-d-completion-audit-hook
#
# On-stop gate. Refuses to let the agent surface "done" when the manifest
# contains materially false completion signals.

set -eu

MANIFEST_PATH="${AGENT_PROTOCOL_MANIFEST_PATH:-}"
if [ -z "$MANIFEST_PATH" ]; then
  MANIFEST_PATH=$(git ls-files 'change-manifest*.yaml' 2>/dev/null | head -1 || true)
fi

if [ -z "$MANIFEST_PATH" ] || [ ! -f "$MANIFEST_PATH" ]; then
  exit 0
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "[agent-protocol/completion-audit] TOOL_ERROR: yq not found on PATH; skipping completion audit" >&2
  exit 2
fi

fail=0

# Rule 1: all evidence_plan items must be collected or waived.
pending=$(yq -r '[.evidence_plan[] | select(.status != "collected" and .status != "rejected")] | length' "$MANIFEST_PATH" 2>/dev/null || echo 0)
if [ "${pending:-0}" -gt 0 ]; then
  printf '[agent-protocol/completion.evidence-complete] %s evidence_plan entries still pending (status != collected|rejected)\n' "$pending" >&2
  fail=1
fi

# Rule 2: no residual_risks accepted_by = unaccepted.
unaccepted=$(yq -r '[.residual_risks[]? | select(.accepted_by == "unaccepted")] | length' "$MANIFEST_PATH" 2>/dev/null || echo 0)
if [ "${unaccepted:-0}" -gt 0 ]; then
  printf '[agent-protocol/completion.unaccepted-risk] %s residual_risks entries are still unaccepted\n' "$unaccepted" >&2
  fail=1
fi

# Rule 3: every escalation has a resolved_at.
unresolved=$(yq -r '[.escalations[]? | select(.resolved_at == null or .resolved_at == "")] | length' "$MANIFEST_PATH" 2>/dev/null || echo 0)
if [ "${unresolved:-0}" -gt 0 ]; then
  printf '[agent-protocol/completion.unresolved-escalation] %s escalations have no resolved_at\n' "$unresolved" >&2
  fail=1
fi

# Rule 4: phase=observe requires handoff_narrative.
phase=$(yq -r '.phase' "$MANIFEST_PATH" 2>/dev/null || echo "")
if [ "$phase" = "observe" ]; then
  narrative=$(yq -r '.handoff_narrative // ""' "$MANIFEST_PATH" 2>/dev/null || echo "")
  if [ -z "$narrative" ]; then
    printf '[agent-protocol/completion.observe-needs-narrative] phase=observe but handoff_narrative is empty\n' >&2
    fail=1
  fi
fi

if [ "$fail" = "1" ]; then
  exit 1
fi

exit 0
