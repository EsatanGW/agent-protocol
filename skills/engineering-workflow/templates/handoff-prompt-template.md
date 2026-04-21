# Handoff Prompt Template

Skeleton for the **outgoing session** to produce when handing a change to the next session (same role across a session break, or a downstream role taking over). The incoming session will read this prompt first and decide its resume mode from it.

---

## Why this template exists

Without a template, an outgoing session tends to produce a verbose "here is everything you might need to know" prompt — re-explaining prior phases, inlining decisions the Manifest already records, and listing a long set of files to re-read. The incoming session then sequentially reads every listed file as its first action, exhausting context before any real work begins. This is the session-handoff context-collapse failure mode.

The template below makes the outgoing session produce a **compact pointer block**, not a re-briefing. The rule is: *everything the incoming session needs to act is in the Manifest; the prompt only points there*.

---

## Budget

- **Soft cap: 400 words** (roughly 600 tokens).
- **Hard cap: 800 words.** Exceeding this is a signal that content belongs in the Manifest, not in the prompt.

Word count is a deliberately tool-agnostic proxy — token counts vary by tokenizer, word counts do not.

---

## The prompt must include

1. **Identity header** — `change_id`, current `phase`, absolute path to the Change Manifest.
2. **Resume mode** — one of `Lazy`, `Targeted`, `Role-scoped`, `Full`, `Minimal` — with a one-sentence reason.
3. **Next action** — `<verb> <object> → <expected artifact>`. One line.
4. **Open items** — at most 3 bullets. Each bullet names the short label and points to the Manifest field that carries the detail (`Manifest.escalations[0]`, `Manifest.review_notes[2]`, etc.).
5. **ROADMAP reference** — path to the ROADMAP file + the row ID the initiative corresponds to.
6. **Read block** — at most **3** path entries, listed only when the next action genuinely requires them. Fewer is better. If this block would hold more than 3 entries, the Manifest is incomplete — go fix the Manifest, then regenerate this prompt.

## The prompt must NOT include

- Re-explanations of prior phases (they are in the Manifest).
- Inline copies of the spec, plan, test report, or other artifacts (they are referenced by path).
- Re-statements of methodology rules (SoT patterns, breaking-change levels, anti-collusion rules — the incoming session already has the skill loaded).
- A long "background context" preamble or a "welcome back, here is what we did last time" block.
- File-path lists longer than 3 entries.

A prompt that contains any of the above is failing the compaction rule. Reduce it before sending.

---

## Skeleton

Copy the skeleton below, fill each line, then check the budget and the MUST / MUST NOT rules before sending.

```
Change: <change_id> | Phase: <N> <phase_name> | Manifest: <absolute path>
Resume mode: <Lazy|Targeted|Role-scoped|Full|Minimal> — <one-sentence reason>
Next action: <verb> <object> → <expected artifact>
Open items (≤ 3):
  - <short label> — Manifest.<field-path>
  - <short label> — Manifest.<field-path>
ROADMAP row: <path to ROADMAP>#<row-id>
Read (≤ 3 paths, only if required for next action):
  - <absolute path>
If this prompt is insufficient, read the Manifest. If the Manifest is insufficient, stop and report drift — do not widen the read set.
```

---

## Lean-mode variant

Lean-mode handoffs are rare (Lean usually finishes in a single session), but for multi-session Lean work the compaction discipline still applies. The only differences:

- `Manifest` is the Lean-spec note path (Lean mode does not carry a full Change Manifest).
- `Resume mode` should usually be `Minimal`.
- The read block is capped at **1** path — the current task-list item.

```
Change: <lean-spec filename> | Phase: <lean-phase-name> | Lean-spec: <absolute path>
Resume mode: Minimal — <reason>
Next action: <verb> <object> → <expected artifact>
Open items (≤ 2):
  - <short label>
Read (≤ 1 path):
  - <absolute path>
```

---

## Worked example (Targeted mode, Phase 3 → Phase 4 handoff, Full mode change)

```
Change: 2026-04-21-voucher-enum-split | Phase: 4 Implement | Manifest: /repo/manifests/2026-04-21-voucher-enum-split.yaml
Resume mode: Targeted — advancing from Phase 3 Test Plan to Phase 4 Implement; need plan + test plan.
Next action: implement the three consumer migrations → /repo/src/voucher/*.go diff
Open items (≤ 3):
  - Mobile long-tail cache TTL — Manifest.rollback.long_lived_client_notes
  - Contract-test flake in staging — Manifest.escalations[1]
ROADMAP row: /repo/ROADMAP.md#voucher-enum-split-P4
Read (≤ 3 paths, only if required for next action):
  - /repo/manifests/2026-04-21-voucher-enum-split.plan.md
  - /repo/manifests/2026-04-21-voucher-enum-split.test-plan.md
If this prompt is insufficient, read the Manifest. If the Manifest is insufficient, stop and report drift — do not widen the read set.
```

Word count of the example: 94 words. Comfortably under the 400-word soft cap.

---

## What the outgoing session must do before sending

1. Confirm the Manifest is up to date — every decision made during this session is recorded.
2. Confirm `phase` in the Manifest matches the header of this prompt.
3. Confirm the read block contains only paths the incoming session will *definitely* need.
4. Count words. If over 400, compact. If over 800, reject and recompact.

---

## What the incoming session does on receipt

See [`../references/lazy-resume-checklist.md`](../references/lazy-resume-checklist.md). The incoming session's first action is **not** to read every path listed — it is to declare the resume mode and apply the per-mode read list.

## See also

- [`../references/resumption-protocol.md`](../references/resumption-protocol.md) — the incoming session's protocol.
- [`../references/lazy-resume-checklist.md`](../references/lazy-resume-checklist.md) — per-mode checklist.
- [`../../../docs/change-manifest-spec.md`](../../../docs/change-manifest-spec.md) — Manifest field semantics, including §State-snapshot discipline.
- [`../../../docs/multi-agent-handoff.md`](../../../docs/multi-agent-handoff.md) — cross-role handoff rules.
