# Fix-Retest Loop

Entered when any TC fails during Phase 4 test execution.

- Classify the failure cause.
- Fix based on cause.
- Spot-check standards.
- Re-run all impacted verification.
- Create a NEW test report entry or file.

After three failures of the same category, stop and re-examine the approach instead of stacking more patches.

## When the cause is not inside Phase 4

If the failure traces back to a wrong plan, wrong SoT classification, new surface being touched, or a mis-judged breaking-change level, this is no longer a fix-retest case — it is a **phase re-entry** case. Apply `docs/phase-gate-discipline.md` Rule 6: pick the correct re-entry phase from the decision table, open a new ROADMAP row with a `phase_reentry` marker, update the manifest fields the rule names, and let the Implementer's pre-handoff self-check (`docs/multi-agent-handoff.md` §Pre-handoff self-check) close the loop. Do not patch around a planning defect inside Phase 4.
