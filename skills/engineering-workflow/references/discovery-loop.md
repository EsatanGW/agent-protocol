# Discovery Loop Protocol

The phase structure is a linear 0→7 walk, but real development often surfaces new impact areas in the later phases.
This document defines the standard procedure for "scope expansion discovered during implementation or review."

---

## When the Discovery Loop fires

| Trigger | Example |
|---------|---------|
| Phase 4 implementation uncovers a new affected surface | API change turns out to also need cache-invalidation logic. |
| Phase 4 implementation uncovers a new consumer | Thought only the app used this API, but there's also a webhook consumer. |
| Phase 5 review exposes a planning gap | Reviewer points out the rollback strategy is missing. |
| Phase 5 review exposes a security / performance risk | Cross-cutting checklist surfaces an unconsidered rate-limit requirement. |
| Phase 6 sign-off evidence is insufficient | Cannot prove correct behavior on one of the surfaces. |
| Phase 1 startup detects a sealed-as-stub entry-point body or an incomplete dispatcher case enumeration | A screen-level widget's `build()` returns `SizedBox.shrink()` / empty `Scaffold` / `return null` widget tree after the Stage that was supposed to assemble it has signed off; OR a variant/country dispatcher's `switch` is missing one or more candidate cases relative to the declared `variant_resolution.candidates` set. **Scope cap:** scan only paths declared in the consumer project's surface-map (not the full tree). **Time cap:** 30-second wall-clock per scan; on timeout emit `discovery-loop scan timed out — manual review required` and continue rather than block. **Pattern cap:** look only for the specific markers (`SizedBox.shrink`, empty `Scaffold`, `return null` widget tree, `switch` without a case for every candidate) — not arbitrary code analysis. Evidence base: cckn-008 §Detection protocol D-1 / D-2; Pattern 9 dispatch-class binding rule (1.29.0). |

---

## Discovery Loop procedure

```
A new problem is found during Phase 4 / 5 / 6
│
├── Step 1: assess impact size
│   ├── Small (missed detail within the same surface) → fix in place, update evidence
│   └── Large (new surface / consumer / risk) → go to Step 2
│
├── Step 2: decide the rewind-target phase
│   ├── Need to re-investigate → rewind to Phase 1
│   ├── Need to revise the plan → rewind to Phase 2
│   └── Need to extend the test plan → rewind to Phase 3
│
├── Step 3: record the rewind reason
│   In the current phase's artifact, append:
│   > Discovery Loop: [date]
│   > Reason: [brief description of what was found]
│   > Rewound to: Phase [N]
│   > Impact: [which artifacts need to be updated]
│
├── Step 4: re-advance from the rewind target
│   - Update that phase's artifact.
│   - Pass through each later phase's gate in order.
│   - Do not skip intermediate phases.
│
└── Step 5: return to the trigger point and continue
    - Bring the updated artifact back to where you stopped.
    - Verify the newly discovered problem is now covered.
```

---

## Discovery Loop vs Fix-Retest Loop

| Aspect | Discovery Loop | Fix-Retest Loop |
|--------|----------------|-----------------|
| Trigger | A new unexpected impact is discovered | A test / verification failed |
| Nature | Scope expansion | Implementation-quality fix |
| Rewind depth | May return to Phase 1-3 | Typically stays in Phase 4 |
| Artifact impact | Spec / plan / test plan may need updating | Usually only the test report is updated |
| Reference doc | This document | `fix-retest-loop.md` |

---

## Mode upgrade trigger

The Discovery Loop may trigger a Lean → Full upgrade (see `mode-decision-tree.md`).

Criteria:
- If the new findings push the surface count from 1-2 to 3+ → consider upgrading.
- If the new findings pull in a forced-Full scenario (migration, public API, security) → upgrade is mandatory.
- If the new findings require changing an existing normative claim in canonical methodology content (L1+ canonical edit per `mode-decision-tree.md §Scenarios that force Full`) → upgrade is mandatory.
- If the new findings are just additional detail within the same surface → no upgrade needed.

---

## Preventing infinite loops

### Hard limit
- A single task may trigger the Discovery Loop at most **3 times**.
- On the third trigger, re-evaluate whether the task should be split into multiple independent tickets.

### Self-check questions
Each time the Discovery Loop fires, ask:
1. Was this finding "something Phase 1 should have caught," or is it "a reasonable late-phase discovery"?
2. If the former, the Phase 1 investigation technique needs improvement.
3. If the Discovery Loop fires multiple times back-to-back, the task definition is probably too large.

---

## Simplified version under Lean mode

Lean mode does not need a formal artifact-rewind process:
1. Record the finding (one sentence).
2. Judge whether a Full-mode upgrade is required.
3. If not: fix in place and update evidence.
4. If yes: upgrade first, then run the full Discovery Loop.
