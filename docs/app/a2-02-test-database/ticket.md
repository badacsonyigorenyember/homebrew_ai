# a2-02 · Test database

Stage: ready
Branch: `a2-02-test-database`
Milestone: M2 · Requirements: §4 API tests ([SYSTEM.md](../SYSTEM.md))
Blocked by: a2-01

## Goal
API tests run against a real Postgres that is created for the test run and thrown away after, never
against your stack.

## What to build
- A shared xUnit fixture that starts a Testcontainers Postgres from the same image as the stack
  (`supabase/postgres:15.8.1.085`), because the app's tables need its extensions (`pg_jsonschema`,
  `vector`).
- The fixture applies the `db/*.sql` files the API's tables need, in order (work out the list from
  their `Needs` lines), then `db/060_app_api_role.sql`, and seeds a few `ref.ingredient` rows.
- `WebApplicationFactory` points the API at the container, connecting as `app_api`.

## Acceptance criteria
- **AC1** `dotnet test` starts the container, runs, and removes it; your running stack is untouched.
- **AC2** A test proves `app_api` can read `ref.ingredient` and cannot insert into it.
- **AC3** A test proves `/api/health` shows `database: ok` against the container.
- **AC4** The list of applied SQL files is in one place in the fixture, with a comment on why each
  is needed.

## Tests
This ticket is test infrastructure: its implementation is the test lesson. The test review checks
the two tests fail when the grant is wrong.

## Out of scope
- Seeding inventory rows (each feature's tests seed their own).

## Deviations

None yet.
