# a1-04 · Test database

Stage: implementing
Branch: `a1-04-test-database`
Milestone: M1 · Requirements: §4 API tests ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-03

## Goal
API tests run against a real Postgres that is created for the test run and thrown away after, never
against your stack.

## What to build
- A shared xUnit fixture that starts a Testcontainers Postgres from the same image as the stack
  (`supabase/postgres:15.8.1.085`), because the app's tables need its extensions (`pg_jsonschema`,
  `vector`).
- The fixture applies the `db/*.sql` files the API's tables need, in order (work out the list from
  their `Needs` lines), then `db/060_app_api_role.sql`.
- It seeds two recipes with their items, styles and ingredients: one with a `process` (a real
  saved recipe's process, kept as a JSON file in the test project), one without.
- `WebApplicationFactory` points the API at the container, connecting as `app_api`.

## Acceptance criteria
- **AC1** `dotnet test` starts the container, runs, and removes it; your running stack is untouched.
- **AC2** A test proves `app_api` can read `app.recipe` and cannot update it.
- **AC3** A test proves `/api/health` shows `database: ok` against the container.
- **AC4** The list of applied SQL files is in one place in the fixture, with a comment on why each
  is needed.

## Tests
This ticket is test infrastructure: its implementation is the test lesson. The test review checks
the two tests fail when the grant is wrong.

## Out of scope
- Seeding batches (each feature's tests seed their own).

## Notes
- The seeded process can be recipe 1349's (the newest on 2026-11-02): it has salts, two mash
  steps, one boil hop, one whirlpool hop and one yeast, so a1-08's generator is tested on a full
  brew day.

## Deviations

- 2026-11-18 · Recipe 1349 (Notes) does not exist: the stack has 93 recipes, ids 112–1489. The
  seeded process is recipe 1155's (2026-10-30), the newest with salts, two mash steps, one boil hop
  (Columbus), one whirlpool hop (Citra) and one yeast (US-05); it also has a Cascade dry hop.
- 2026-11-18 · The tests are taught in `lesson.md` (the ticket is test code throughout), so there
  is no `test-lesson.md`: the code review is followed directly by the test review.
- 2026-11-19 · Lesson step 8 (`app/README.md`) was done by Claude, not you: from this ticket on,
  Claude writes the docs before shipping (`app-ticket` Ship step 2).
