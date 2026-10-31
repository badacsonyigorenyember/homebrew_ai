# a2-07 · Add item form

Stage: ready
Branch: `a2-07-inventory-add-ui`
Milestone: M2 · Requirements: F2.2 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a2-04, a2-06

## Goal
You add items from the Inventory view: pick from the catalogue, or type a name that is not listed.

## What to build
- An "Add item" button opening a dialog (a full-screen sheet on narrow screens).
- A catalogue picker that searches `GET /api/catalogue` as you type, with a "not in the catalogue:
  use this name" option.
- Amount and unit fields; React Hook Form with a Zod schema that mirrors the API's rules.
- On success the dialog closes and the list refreshes (query invalidation, not a page reload).

## Acceptance criteria
- **AC1** Adding Cascade from the picker shows it in the list with the catalogue name.
- **AC2** Adding a free-text name shows it with kind `other`.
- **AC3** Client-side errors show next to their fields before sending; a 400 from the API shows its
  messages on the same fields.
- **AC4** The dialog works by keyboard alone and is labelled for screen readers.

## Tests
Needed: component tests with MSW: catalogue pick, free text, client validation, server validation
shown on fields.

## Out of scope
- Editing (a2-09).

## Deviations

None yet.
