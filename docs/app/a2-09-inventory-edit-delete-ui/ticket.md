# a2-09 · Edit and delete in the list

Stage: ready
Branch: `a2-09-inventory-edit-delete-ui`
Milestone: M2 · Requirements: F2.3 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a2-07, a2-08

## Goal
You change amounts and remove items in the list, the same tap-to-expand way the batch steps will
work.

## What to build
- Tapping or clicking an item expands it in place, with amount and unit fields and Save and Cancel.
- A delete button that asks for confirmation first.
- After either, the list refreshes; while saving, the buttons show it and cannot be pressed twice.

## Acceptance criteria
- **AC1** Editing an amount to 0 shows the item as used up.
- **AC2** Cancel restores the old values.
- **AC3** Delete asks first; confirming removes the row; refusing keeps it.
- **AC4** Works by keyboard: Enter expands, Escape cancels.

## Tests
Needed: component tests with MSW: edit, cancel, delete confirmed and refused.

## Out of scope
- Undo after delete.
- Optimistic updates (the lesson explains the trade-off; not built).

## Deviations

None yet.
