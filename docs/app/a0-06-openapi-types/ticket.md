# a0-06 · Types generated from the API

Stage: ready
Branch: `a0-06-openapi-types`
Milestone: M0 · Requirements: §4 API types ([SYSTEM.md](../SYSTEM.md))
Blocked by: a0-05

## Goal
The web app's API types come from the API itself, so a change on one side breaks the build on the
other instead of failing at runtime.

## What to build
- The API writes its OpenAPI document to a file at build time (check the current .NET 10 way in the
  Microsoft docs), committed at `app/api/openapi/v1.json`.
- `npm run gen:api` in `app/web` turns that file into types with `openapi-typescript`.
- A typed client with `openapi-fetch` (same project as `openapi-typescript`) that adds the base URL
  and the key in one place.
- `useHealth` uses the typed client.

## Acceptance criteria
- **AC1** Renaming `status` in the health response and rebuilding makes `npm run typecheck` fail
  where the web app uses it (try it, then undo).
- **AC2** The generated file says at the top that it is generated, and nobody edits it by hand.
- **AC3** No `any` in the API client code.
- **AC4** The a0-04 tests still pass.

## Tests
Not needed: the type check is the test; the a0-04 tests cover behaviour.

## Out of scope
- Hand-written API types.

## Notes
- SYSTEM.md §4 names `openapi-typescript`; this ticket adds its sister library `openapi-fetch` (a
  Changes line goes into SYSTEM.md when the ticket ships).

## Deviations

None yet.
