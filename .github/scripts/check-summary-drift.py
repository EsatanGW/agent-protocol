#!/usr/bin/env python3
"""Pre-release lint for TL;DR-vs-body count drift in docs/.

Replaces `docs/audits/summary-vs-per-case-registry.md` (retired in
1.15.x). The manual audit was a snapshot that aged; this script re-runs
on every push/PR so the drift class is caught at commit time rather than
accumulating until a human audit.

Heuristic: for each top-level doc, if the TL;DR contains a
"<number> <noun>" claim (e.g. "five axes", "six anti-patterns"), count
the matching structural entries in the body and flag mismatches.

Scope matches the original audit (docs/*.md top-level; subdirectories and
narrative onboarding files excluded).

Exit 0 on clean, 1 on any drift, 2 on tool error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}

# Nouns the audit actually caught drifting, paired with a body counter
# strategy. Each counter returns (count, evidence-string) or (None, reason)
# when the body has no recognizable shape to count — in which case the
# check is skipped for that claim (conservative: prefer miss over false
# positive).

def _count_numbered_headings(body: str, keyword_re: str) -> tuple[int, str]:
    """Count ### headings that begin with a keyword like 'Pattern N',
    'Step N', 'Rule N', 'Principle N', 'Anti-pattern N'. Falls back to
    bare numbered headings (`## 1. X`, `### 1. X`) when the keyword form
    has no matches — some files number their items without the keyword."""
    kw_pattern = re.compile(rf"^#+\s+{keyword_re}\s+\d+\b", re.MULTILINE)
    kw_matches = kw_pattern.findall(body)
    if kw_matches:
        return len(kw_matches), f"^#+ {keyword_re} N headings"
    bare_pattern = re.compile(r"^#{2,3}\s+\d+\.\s+\S", re.MULTILINE)
    bare_matches = bare_pattern.findall(body)
    if bare_matches:
        return len(bare_matches), "^## N. X headings (bare numbered)"
    return 0, f"^#+ {keyword_re} N headings"

def _count_section_rows(body: str, section_re: str) -> tuple[int | None, str]:
    """Find a section header matching section_re, count ### subheadings
    or table rows inside it until the next ## boundary."""
    sec = re.search(rf"^##\s+.*({section_re}).*$", body, re.MULTILINE | re.IGNORECASE)
    if not sec:
        return None, f"no ## section matching /{section_re}/"
    start = sec.end()
    next_h2 = re.search(r"^##\s", body[start:], re.MULTILINE)
    end = start + next_h2.start() if next_h2 else len(body)
    segment = body[start:end]
    # Count ### subheadings first; if zero, count non-header markdown
    # table rows (excluding the header + separator rows).
    sub = re.findall(r"^###\s+", segment, re.MULTILINE)
    if sub:
        return len(sub), f"### subheadings inside §{sec.group(1)}"
    # Table rows: lines starting with `|` that are not the two-line
    # header (header-row + separator-row).
    all_pipe = [l for l in segment.splitlines() if l.lstrip().startswith("|")]
    if len(all_pipe) >= 3:
        # Drop header + separator.
        return len(all_pipe) - 2, f"table rows inside §{sec.group(1)}"
    return None, f"§{sec.group(1)} has no ### or table rows"

COUNTERS = {
    # noun (singular or plural form as appears in TL;DR) -> counter fn
    "axes":            lambda b: _count_section_rows(b, r"(?:Primary )?[Oo]bservation axes|[Pp]rimary observation axes"),
    "anti-patterns":   lambda b: _count_numbered_headings(b, r"[Aa]nti-pattern"),
    "patterns":        lambda b: _count_numbered_headings(b, r"[Pp]attern"),
    "steps":           lambda b: _count_numbered_headings(b, r"[Ss]tep"),
    "stages":          lambda b: _count_numbered_headings(b, r"[Ss]tage"),
    "rules":           lambda b: _count_numbered_headings(b, r"[Rr]ule"),
    "principles":      lambda b: _count_numbered_headings(b, r"[Pp]rinciple"),
    "fracture lines":  lambda b: _count_section_rows(b, r"[Nn]atural fracture lines|[Ff]racture lines"),
    "coordination strategies": lambda b: _count_section_rows(b, r"[Cc]oordination strategies|[Cc]oordination patterns"),
    "hook points":     lambda b: _count_numbered_headings(b, r"[Hh]ook"),
}


def extract_tldr(text: str) -> str:
    """Extract the TL;DR block: the first blockquote or first paragraph
    after the # title, up to the first blank line or ## / --- marker."""
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start = i + 1
            break
    # Skip any leading blank lines.
    while start < len(lines) and not lines[start].strip():
        start += 1
    end = start
    while end < len(lines):
        stripped = lines[end].strip()
        if end > start and (stripped.startswith("## ") or stripped.startswith("---")):
            break
        end += 1
    return "\n".join(lines[start:end])


def find_claims(tldr: str) -> list[tuple[int, str, str]]:
    """Return [(claimed_n, noun, matched_phrase), ...] for every
    "<number> <noun>" pattern we can count."""
    out: list[tuple[int, str, str]] = []
    # Build alternation covering each known noun phrase.
    nouns_re = "|".join(re.escape(n) for n in COUNTERS)
    num_re = r"(?:\d+|" + "|".join(NUM_WORDS) + ")"
    pattern = re.compile(
        rf"\b({num_re})\s+({nouns_re})\b",
        re.IGNORECASE,
    )
    for m in pattern.finditer(tldr):
        raw_num = m.group(1).lower()
        noun = m.group(2).lower()
        n = int(raw_num) if raw_num.isdigit() else NUM_WORDS[raw_num]
        out.append((n, noun, m.group(0)))
    return out


def check_file(path: Path) -> list[str]:
    text = path.read_text()
    tldr = extract_tldr(text)
    body = text[text.find(tldr) + len(tldr):] if tldr else text
    findings: list[str] = []
    for n, noun, phrase in find_claims(tldr):
        actual, evidence = COUNTERS[noun](body)
        if actual is None:
            continue  # Nothing countable in body; skip rather than flag.
        if actual != n:
            findings.append(
                f"{path}: TL;DR says '{phrase}' but body has {actual} via {evidence}"
            )
    return findings


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    docs_dir = repo_root / "docs"
    if not docs_dir.is_dir():
        print(f"ERROR: {docs_dir} not found", file=sys.stderr)
        return 2
    # Scope: top-level docs/*.md only; subdirectories (bridges, examples,
    # onboarding, audits) are out per the original audit's scope.
    targets = sorted(p for p in docs_dir.glob("*.md"))
    all_findings: list[str] = []
    for path in targets:
        all_findings.extend(check_file(path))
    if all_findings:
        print("Summary-vs-body drift detected:", file=sys.stderr)
        for f in all_findings:
            print(f"  {f}", file=sys.stderr)
        print(
            "\nFix: update the TL;DR to match the body (conservative), or add the"
            " missing cases to the body. Silent re-ship is not acceptable.",
            file=sys.stderr,
        )
        return 1
    print(f"ok    {len(targets)} docs, no TL;DR-vs-body drift")
    return 0


if __name__ == "__main__":
    sys.exit(main())
