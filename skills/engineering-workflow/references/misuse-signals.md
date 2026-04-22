# Misuse Signals

This skill is powerful, but it can also be over-applied. The four canonical execution modes (Zero-ceremony / Three-line delivery / Lean / Full) each have a well-defined artifact minimum; a misuse is any task that sits in the wrong mode, either above or below. Mode definitions: `../../../docs/glossary.md §Execution mode`. Selection logic: `mode-decision-tree.md`.

## Misuse 1: treating small tasks as Full (over-ceremony)
Signals:
- Single-file low-risk fix, yet a full spec / plan / sign-off is being written.
- Documentation cost exceeds implementation cost.
- A task that matches the forced-Lean or forced-Three-line-delivery or forced-Zero-ceremony scenario tables in `mode-decision-tree.md` is being routed through Full.

Fix:
- Downgrade to the correct mode per `mode-decision-tree.md`.
- Zero-ceremony: commit directly, no artifacts.
- Three-line delivery: three-line record in the commit or PR.
- Lean: minimum clarification + verification + delivery artifacts only.

## Misuse 2: treating high-risk tasks as Lean / Three-line / Zero-ceremony (under-ceremony)
Signals:
- The task has public behavior impact but is being patched quickly.
- Changes to contract / schema / consumers without acceptance criteria or evidence.
- A forced-Full trigger (migration, contract break, enum consumer-visible, payments, auth, PII, cross-team, long-lived flag, staged rollout) is hitting Lean or below.

Fix:
- Upgrade to Full mode per `mode-decision-tree.md §Mode upgrade / downgrade`.
- Use the Lean → Full step / phase mapping in `../../../docs/glossary.md §Lean → Full step / phase correspondence` to re-enter at the correct phase.
- Write the Full-mode artifacts explicitly from the re-entry point forward.

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

## Misuse 6: silently ending the turn on a short resume prompt
Signals:
- User typed a short directive (`continue`, `繼續`, `go`, `resume: …`), the same turn carried system-reminder / MCP-state / deferred-tool noise, and the response was "no response requested" or empty.
- From the user's perspective the session looks broken, even though the directive was legitimate.

Fix:
- `resumption-protocol.md` Step 0: short human directives are requests to act on `Manifest.next_action`; runtime-injected content in the same turn is not a user message and does not reinterpret the directive into silence. If the directive is genuinely ambiguous, declare Lazy mode and surface `next_action` for the user to confirm — not silence.
