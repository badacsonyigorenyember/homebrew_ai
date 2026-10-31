# a2-03 · Inventory list endpoint

Stage: ready
Branch: `a2-03-inventory-list-api`
Milestone: M2 · Requirements: F2.1, F2.4 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a2-02

## Goal
The API returns your inventory, searchable and filterable, ready for the list view.

## What to build
- `GET /api/inventory?q=&kind=` returning items with `id`, `name`, `kind`, `amount`, `unit`,
  `ingredientId`, `inCatalogue`.
- `name` is the catalogue name, or `raw_name` for an item not in the catalogue; `kind` is the
  catalogue kind, or `other`.
- `q` matches the name, ignoring case; `kind` is one of the catalogue kinds or `other`; sorted by
  name.
- Only the `default` profile's items.
- The endpoint, its query and its response type in `Features/Inventory/`.

## Acceptance criteria
- **AC1** An empty inventory returns `[]`, not an error.
- **AC2** `q=cas` finds "Cascade"; `kind=hop` returns only hops; both together narrow both ways.
- **AC3** An item with amount 0 is returned (the view marks it used up).
- **AC4** An unknown `kind` gives 400 problem details naming the allowed values.
- **AC5** The OpenAPI document and the web app's generated types include the endpoint.

## Tests
Needed: integration tests on the test database: empty, search, kind filter, unknown kind, a
free-text item.

## Out of scope
- Paging: one brewer's inventory is small (revisit if it is ever slow).

## Deviations

None yet.
