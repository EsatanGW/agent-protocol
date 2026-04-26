#!/usr/bin/env python3
"""Verify multi-agent role-contract invariants are echoed in every runtime mirror.

The canonical multi-agent role contract lives in
`docs/multi-agent-handoff.md` (§Tool-permission matrix +
§Single-agent anti-collusion rule). Five runtime mirrors restate the
contract in runtime-specific phrasing:

  - `agents/{planner,implementer,reviewer}.md`           (Claude Code)
  - `.cursor/rules/{planner,implementer,reviewer}.mdc`   (Cursor)
  - `reference-implementations/roles/{planner,implementer,reviewer}.md`
                                                          (Gemini CLI / Windsurf / Codex / generic)

Because the mirrors are not byte-identical (each has runtime-specific
phrasing), this checker validates **semantic invariants** rather than
text equality. Each invariant is a regex that must match somewhere in
every mirror for the given role; failure means a future SoT change has
not been propagated to that mirror.

The checker also validates that every invariant matches the SoT itself,
so the invariants cannot drift away from the canonical document.

Exit codes (matches `validate-cluster-disjointness.py` convention):
  0  every mirror passes every invariant; SoT also passes
  1  at least one invariant violation (in SoT or in a mirror)
  2  tool error (missing file, etc.)

Usage:
    python3 .github/scripts/check-role-consistency.py
    python3 .github/scripts/check-role-consistency.py --self-test-only
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


SOT_PATH = "docs/multi-agent-handoff.md"


@dataclass(frozen=True)
class Surface:
    path: str
    role: str  # "planner" | "implementer" | "reviewer"


@dataclass(frozen=True)
class Invariant:
    invariant_id: str
    description: str
    pattern: str  # regex source (re.IGNORECASE applied uniformly)
    mirror_only: bool = False  # if True, skip when checking the SoT itself


# Mirror files derived from `docs/multi-agent-handoff.md §Enforcement
# across runtimes` and the `agents/` Claude Code bridge.
SURFACES: list[Surface] = [
    Surface("agents/planner.md", "planner"),
    Surface("agents/implementer.md", "implementer"),
    Surface("agents/reviewer.md", "reviewer"),
    Surface(".cursor/rules/planner.mdc", "planner"),
    Surface(".cursor/rules/implementer.mdc", "implementer"),
    Surface(".cursor/rules/reviewer.mdc", "reviewer"),
    Surface("reference-implementations/roles/planner.md", "planner"),
    Surface("reference-implementations/roles/implementer.md", "implementer"),
    Surface("reference-implementations/roles/reviewer.md", "reviewer"),
]


# Each invariant is a phrasing-flexible regex that must match
# (a) the SoT (`docs/multi-agent-handoff.md`) and
# (b) every mirror file declaring the same role.
#
# Invariants are deliberately written to accept multiple phrasings
# already present across the 9 mirrors so the gate detects DRIFT, not
# stylistic variance. To extend: add a new entry; if any current mirror
# fails it, that mirror must be updated alongside the new invariant.
INVARIANTS_BY_ROLE: dict[str, list[Invariant]] = {
    "planner": [
        Invariant(
            "planner-declares-sot",
            "must reference docs/multi-agent-handoff.md as SoT",
            r"docs/multi-agent-handoff\.md",
            mirror_only=True,
        ),
        Invariant(
            "planner-no-write",
            "must declare no write/edit capability",
            r"(no\s+write|no\s+edit|do not edit code|no Edit\s*/\s*Write|"
            r"no write\s*/\s*edit|read[- ]only)",
        ),
    ],
    "implementer": [
        Invariant(
            "implementer-declares-sot",
            "must reference docs/multi-agent-handoff.md as SoT",
            r"docs/multi-agent-handoff\.md",
            mirror_only=True,
        ),
        Invariant(
            "implementer-no-self-review",
            "must declare no self-review (Implementer != Reviewer)",
            r"(self[- ]review|self[- ]approve|"
            r"Implementer\s*[≡=]\s*Reviewer|"
            r"may not also serve as the Reviewer|"
            r"cannot.{0,30}also.{0,30}reviewer|"
            r"review your own)",
        ),
        Invariant(
            "implementer-no-reclassify",
            "must declare no surface re-classification (those are Planner fields)",
            r"(re[- ]classify|change.{0,30}breaking_change\.level|"
            r"planner.s field|planner_disagreement|"
            r"delete or overwrite.{0,30}field.{0,30}planner)",
        ),
    ],
    "reviewer": [
        Invariant(
            "reviewer-declares-sot",
            "must reference docs/multi-agent-handoff.md as SoT",
            r"docs/multi-agent-handoff\.md",
            mirror_only=True,
        ),
        Invariant(
            "reviewer-no-edit",
            "must declare no edit/write capability (single most important rule)",
            r"(no\s+Edit\s*/\s*Write|no\s+write\s*/\s*edit|"
            r"cannot edit|do not edit code|no write|"
            r"absent.{0,30}Edit\s*/\s*Write|"
            r"disables.{0,30}edit|no write\s*/\s*edit capability|"
            r"do not fix it)",
        ),
        Invariant(
            "reviewer-no-self-approve",
            "must declare no self-approval / anti-collusion",
            r"(self[- ]approve|self[- ]review|"
            r"same identity.{0,40}reviewer|"
            r"anti[- ]collusion|"
            r"Implementer.{0,40}Reviewer|"
            r"refuse and escalate)",
        ),
    ],
}


def _check_invariants(text: str, invariants: list[Invariant]) -> list[Invariant]:
    """Return invariants that did NOT match. Empty list == all pass."""
    misses = []
    for inv in invariants:
        if not re.search(inv.pattern, text, flags=re.IGNORECASE | re.DOTALL):
            misses.append(inv)
    return misses


def _verify_sot(repo_root: Path) -> list[str]:
    """Verify every invariant (across all roles) matches the SoT.

    Without this check, an invariant could pass on every mirror while
    the SoT itself never used the concept — meaning a future re-grouping
    of mirrors around a stale invariant would silently succeed.
    """
    sot_path = repo_root / SOT_PATH
    if not sot_path.exists():
        return [f"SoT missing: {SOT_PATH}"]
    sot_text = sot_path.read_text(encoding="utf-8")

    failures = []
    for role, invariants in INVARIANTS_BY_ROLE.items():
        # Mirror-only invariants (e.g. "references the SoT path") are
        # nonsensical when the document being checked IS the SoT.
        applicable = [inv for inv in invariants if not inv.mirror_only]
        missing = _check_invariants(sot_text, applicable)
        for inv in missing:
            failures.append(
                f"SoT ({SOT_PATH}) missing invariant '{inv.invariant_id}' "
                f"({role}): {inv.description}"
            )
    return failures


def _verify_surfaces(repo_root: Path) -> list[str]:
    """Verify each mirror file matches its role's invariants."""
    failures = []
    for surface in SURFACES:
        path = repo_root / surface.path
        if not path.exists():
            failures.append(f"surface missing: {surface.path}")
            continue
        text = path.read_text(encoding="utf-8")
        invariants = INVARIANTS_BY_ROLE[surface.role]
        missing = _check_invariants(text, invariants)
        for inv in missing:
            failures.append(
                f"{surface.path}: missing invariant '{inv.invariant_id}' "
                f"— {inv.description}"
            )
    return failures


def _run_self_test() -> list[str]:
    """Verify the checker on synthetic fixtures.

    Cases:
      1. A mirror with every keyword passes its invariants.
      2. A mirror missing the SoT reference fails.
      3. A Planner mirror missing the no-write declaration fails.
      4. A Reviewer mirror missing the no-edit declaration fails.
      5. A Reviewer mirror with "do not fix it" alone (without other
         no-edit phrasing) STILL passes (anti-rationalization phrasing
         counts because it implies edit-denial).
    """
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # Case 1 — fully-equipped Planner mirror, should pass.
        ok_planner = """
        You are the Planner. See `docs/multi-agent-handoff.md`. You are read-only.
        You do not edit code. No write capability. Anti-collusion: same identity
        cannot also serve as Implementer.
        """
        miss = _check_invariants(ok_planner, INVARIANTS_BY_ROLE["planner"])
        if miss:
            failures.append(
                f"self-test 1 (ok-planner): expected pass, got misses {[m.invariant_id for m in miss]}"
            )

        # Case 2 — missing SoT ref.
        bad_no_sot = """
        Read-only Planner. No write. Anti-collusion enforced.
        """
        miss = _check_invariants(bad_no_sot, INVARIANTS_BY_ROLE["planner"])
        if not any(m.invariant_id == "planner-declares-sot" for m in miss):
            failures.append("self-test 2: expected planner-declares-sot to fail")

        # Case 3 — Planner missing no-write.
        bad_planner_no_write = """
        Planner role; see docs/multi-agent-handoff.md. Anti-collusion: distinct identity.
        """
        miss = _check_invariants(
            bad_planner_no_write, INVARIANTS_BY_ROLE["planner"]
        )
        if not any(m.invariant_id == "planner-no-write" for m in miss):
            failures.append("self-test 3: expected planner-no-write to fail")

        # Case 4 — Reviewer missing no-edit.
        bad_reviewer_no_edit = """
        Reviewer role; see docs/multi-agent-handoff.md. Anti-collusion enforced.
        Self-approve forbidden. Reviewer reads diff and writes review_notes.
        """
        miss = _check_invariants(
            bad_reviewer_no_edit, INVARIANTS_BY_ROLE["reviewer"]
        )
        if not any(m.invariant_id == "reviewer-no-edit" for m in miss):
            failures.append("self-test 4: expected reviewer-no-edit to fail")

        # Case 5 — Reviewer with anti-rationalization "do not fix it" passes.
        ok_reviewer_min = """
        Reviewer role; see docs/multi-agent-handoff.md.
        If you find a bug, do not fix it; record in review_notes and send back.
        Anti-collusion: refuse and escalate if same identity implemented and reviews.
        """
        miss = _check_invariants(ok_reviewer_min, INVARIANTS_BY_ROLE["reviewer"])
        if miss:
            failures.append(
                f"self-test 5 (ok-reviewer-min): expected pass, got misses "
                f"{[m.invariant_id for m in miss]}"
            )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test-only",
        action="store_true",
        help="Run embedded self-test and exit.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repo root (default: inferred from script location).",
    )
    args = parser.parse_args()

    repo_root = args.repo_root or Path(__file__).resolve().parents[2]

    self_test_failures = _run_self_test()
    if self_test_failures:
        print("self-test: FAIL", file=sys.stderr)
        for msg in self_test_failures:
            print(f"  {msg}", file=sys.stderr)
        return 2
    print("self-test: ok (5 cases)")

    if args.self_test_only:
        return 0

    failures: list[str] = []
    failures.extend(_verify_sot(repo_root))
    failures.extend(_verify_surfaces(repo_root))

    if not failures:
        print(
            f"ok   role contract consistent across SoT + {len(SURFACES)} mirrors "
            f"({sum(len(v) for v in INVARIANTS_BY_ROLE.values())} invariants checked)"
        )
        return 0

    print(f"FAIL {len(failures)} role-consistency violation(s):", file=sys.stderr)
    for msg in failures:
        print(f"  {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
