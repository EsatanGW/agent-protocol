# Engineering Workflow Startup Checklist

After loading `engineering-workflow` and before formally starting the work, walk through this checklist.

## 1. Task type
- Is this a feature / bugfix / refactor / migration / investigation?

## 2. Affected surfaces
- User surface?
- System-interface surface?
- Information surface?
- Operational surface?

## 3. Public behavior impact
- Is any externally observable behavior changing?
- If yes, acceptance criteria and evidence are not optional.

## 4. Source of truth and consumers
- Where is the source of truth?
- Who are the primary consumers?
- Are multiple consumers affected together?

## 5. Mode selection
- Single point, low risk → Lean.
- Multiple surfaces / multiple consumers / handoff required → Full.

## 6. Minimum artifacts
### Lean
- Minimal clarification.
- Minimal task list.
- Verification summary.
- Delivery summary.

### Full
- Spec.
- Plan.
- Test plan.
- Test report.
- Completion report.

## 7. Tool-capability setup

List the **capability categories**; the executor maps each one onto the concrete tools provided by the current runtime:

- Clarify / Investigate: file read, code search.
- Planning: task list, file write.
- Implement: file edit / patch, file write, shell execution.
- Review: code search, file read, sub-agent delegation (when needed).

## 8. Exit condition
Before starting, define:
- What state counts as done?
- What evidence will be left behind?
- Which residual risks must be called out at delivery?
