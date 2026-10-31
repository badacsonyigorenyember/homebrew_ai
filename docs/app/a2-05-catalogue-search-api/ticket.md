# a2-05 · Catalogue search endpoint

Stage: ready
Branch: `a2-05-catalogue-search-api`
Milestone: M2 · Requirements: F2.2 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a2-02

## Goal
The API can search the ingredient catalogue, for the add form's picker.

## What to build
- `GET /api/catalogue?q=&kind=&limit=` returning `id`, `name`, `producer`, `kind`.
- `q` needs at least 2 characters; it matches name or producer, ignoring case; results sorted by
  name; `limit` defaults to 20 and is capped at 50.

## Acceptance criteria
- **AC1** `q=cas` finds Cascade; `kind=yeast` narrows to yeasts.
- **AC2** `q` shorter than 2 characters gives 400 problem details.
- **AC3** `limit=500` returns at most 50.
- **AC4** The query is read-only (no tracking) and runs as one SQL statement (check the SQL EF
  logs).

## Tests
Needed: integration tests: match by name, by producer, kind filter, short `q`, limit cap.

## Out of scope
- Fuzzy or ranked search.

## Deviations

None yet.
