# Resumption Protocol

When an agent takes over the same engineering task after an interruption, follow this protocol to rebuild context before doing anything else.

## Step 1: confirm that this is actually the same task
- Is the task name the same?
- Is the source of truth the same?
- Are the affected surfaces the same?

If not, treat it as a new task — do not reuse the old artifacts directly.

## Step 2: read the existing artifacts
### Lean mode
Re-read at minimum:
- The minimal clarification.
- The minimal plan / task list.
- The verification summary.
- The delivery summary (if one exists).

### Full mode
Re-read at minimum:
- The spec.
- The plan.
- The test plan.
- The latest test report.
- The completion report (if one exists).

## Step 3: determine the current mode
- Is this task still Lean?
- Or has the scope grown enough to warrant Full?

## Step 4: determine current progress
At minimum, answer:
- Which tasks are complete?
- What evidence already exists?
- What verification is still missing?
- Has residual risk changed?

## Step 5: decide whether any phase must be re-run
Rewind is required when:
- Scope has expanded.
- New public-behavior impact has appeared.
- The source of truth has changed.
- A new consumer has been discovered.
- Existing evidence has been invalidated.

## Step 6: restate what comes next
Do not just resume patching.
State explicitly:
- Current mode.
- Current phase.
- Next action.
- Missing evidence.
