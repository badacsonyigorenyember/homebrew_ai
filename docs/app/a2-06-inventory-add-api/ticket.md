# a2-06 · Add inventory item endpoint

Stage: ready
Branch: `a2-06-inventory-add-api`
Milestone: M2 · Requirements: F2.2 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a2-03, a2-05

## Goal
The API adds an item, from the catalogue or as free text, and rejects bad input clearly.

## What to build
- `POST /api/inventory` with `ingredientId` or `rawName` (exactly one), `amount` and `unit`.
- Rules: `amount` ≥ 0; `unit` one of `g`, `kg`, `ml`, `l`, `pack` (the table's check); an
  `ingredientId` must exist, and its catalogue name is stored as `raw_name`.
- 201 Created with a `Location` header and the new item in the a2-03 shape.
- 400 validation problem details with one message per field.

## Acceptance criteria
- **AC1** A catalogue item and a free-text item can both be added, and both appear in `GET
  /api/inventory`.
- **AC2** Sending both `ingredientId` and `rawName`, or neither, gives 400 with a field message.
- **AC3** An unknown `ingredientId` gives 400, not 500.
- **AC4** A negative amount and an unknown unit give 400 with their field names.

## Tests
Needed: integration tests for each rule and both success cases.

## Out of scope
- Merging duplicates (adding Cascade twice gives two rows; revisit if it gets in the way).

## Deviations

None yet.
