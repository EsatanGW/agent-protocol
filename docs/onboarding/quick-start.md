# Quick Start

If you only have 3 minutes, start in this order.

## Step 1: Define the change in one sentence
Answer:
- What capability are we actually changing?

Do not answer first:
- Is this frontend or backend?
- Who owns this area?

## Step 2: Tag the four surfaces
Ask yourself quickly:
- User surface: who will see a visible change?
- System-interface surface: which API / event / job / integration changes?
- Information surface: which field / enum / schema / config changes?
- Operational surface: do we need to add log / changelog / rollout / rollback?

## Step 3: Find the source of truth
Ask:
- Where does the authoritative source for this capability actually live?
- Which consumers read from it?

## Step 4: Decide the minimum verification
At minimum, answer:
- How will I know the change actually stands?
- What evidence will I leave behind?

## Step 5: Then decide whether to go through the full workflow
- Small, low-risk → use Lean.
- Multi-surface / public behavior impact / needs handoff → use Full.

## If you only want to read 3 documents first
1. `docs/product-engineering-operating-system.md`
2. `docs/system-change-perspective.md`
3. `docs/examples/worked-example.md`
