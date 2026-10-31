# a2-08 · Edit and delete endpoints

Stage: ready
Branch: `a2-08-inventory-edit-delete-api`
Milestone: M2 · Requirements: F2.3 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a2-06

## Goal
The API changes an item's amount and unit, and deletes items.

## What to build
- `PUT /api/inventory/{id}` with `amount` and `unit` (the a2-06 rules); sets `updated_at`.
- `DELETE /api/inventory/{id}`: 204.
- An unknown id gives 404 problem details on both.

## Acceptance criteria
- **AC1** An edit returns the updated item, and `GET` shows it.
- **AC2** `updated_at` changes on edit.
- **AC3** Delete removes it from `GET`; deleting again gives 404.
- **AC4** Invalid amount or unit gives 400 with field messages.

## Tests
Needed: integration tests for edit, delete, unknown id and validation.

## Out of scope
- Changing which ingredient an item is (delete and add instead).

## Deviations

None yet.
