# Misuse Signals

This skill is powerful, but it can also be over-applied.

## Misuse 1: treating small tasks as Full
Signals:
- Single-file low-risk fix, yet a full spec / plan / sign-off is being written.
- Documentation cost exceeds implementation cost.

Fix:
- Switch to Lean mode.
- Keep only the minimum clarification / verification / delivery.

## Misuse 2: treating high-risk tasks as Lean
Signals:
- The task has public behavior impact but is being patched quickly.
- Changes to contract / schema / consumers without acceptance criteria or evidence.

Fix:
- Upgrade to Full mode.
- Write the artifacts explicitly.

## Misuse 3: treating the skill as bureaucracy
Signals:
- Writing documentation for the sake of documentation.
- Forgetting that source of truth / consumers / evidence are the core.

Fix:
- Return to the four core questions:
  1. Which capability is changing?
  2. Which surfaces does it touch?
  3. Who is the source of truth?
  4. What is the evidence?

## Misuse 4: applying an engineering workflow to a non-engineering task
Signals:
- Pure research / pure Q&A / pure environment inspection is forced through the workflow.

Fix:
- Don't trigger the skill, or keep only a minimal framing.

## Misuse 5: resuming by immediately patching
Signals:
- Returning from a break and patching straight away without reading the artifacts.

Fix:
- Run `resumption-protocol.md` first.
