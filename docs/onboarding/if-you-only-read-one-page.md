# If You Only Read One Page

The most important thing about this methodology is not the tech stack — it is the change-centric perspective.

## The five most important principles

1. Manage the change first, not the code.
   - Code is only one kind of residue left behind by a change.

2. Find the source of truth first, then the consumers.
   - Most bugs come from the two going out of sync.

3. For every change, ask about the four surfaces (full definitions in [`surfaces.md`](../surfaces.md)).
   - User surface
   - System-interface surface
   - Information surface
   - Operational surface

4. Verification and evidence cannot be back-filled after the fact.
   - Decide how you are going to verify it during the plan phase.

5. Done is not the same as merged.
   - Done means: the behavior stands, the consumers are aligned, the evidence exists, and the risks have been stated clearly.

## The one-sentence version

Don't ask "who changes which layer."
Ask first: "how does this capability pass through the whole system, and how do we prove it was changed safely?"
