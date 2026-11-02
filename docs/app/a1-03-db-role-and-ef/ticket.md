# a1-03 · The API's database role and EF Core

Stage: ready
Branch: `a1-03-db-role-and-ef`
Milestone: M1 · Requirements: §8 role, C5 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-02

## Goal
The API reads Postgres as its own role, with EF Core mapping the recipe tables a batch is made
from.

## What to build
- `db/060_app_api_role.sql`: role `app_api` (login), with the password passed in as a `psql`
  variable, never written in the file; usage on schemas `app` and `ref`; select on `app.recipe`,
  `app.recipe_item`, `ref.ingredient` and `ref.beer_style`. Idempotent. Applied as `postgres`
  (OPERATIONS.md §4). The batch tables' grants come with the tables (a1-05).
- The connection string from configuration (`ConnectionStrings:App`, user secrets in development).
- EF Core with Npgsql: an `AppDbContext` mapping `app.recipe`, `app.recipe_item`,
  `ref.ingredient` and `ref.beer_style` (all read-only in code). No EF migrations.
- `/api/health` gains `database`: `ok` or `down`, from a cheap query.
- OPERATIONS.md: the role, how its password is set, and that it must be set again after a password
  rotation.

## Acceptance criteria
- **AC1** The role and its grants are as listed (checked by a catalog query, written in the ticket's
  review).
- **AC2** Running the SQL file twice changes nothing.
- **AC3** `app_api` can read `app.recipe` and cannot update it; it can read `ref.ingredient` and
  cannot insert into it.
- **AC4** With the API running, `/api/health` shows `database: ok`; with a wrong password,
  `database: down` and the API still answers.
- **AC5** No password in any committed file.

## Tests
Needed, but against a throwaway database, which is a1-04. This ticket's tests stage only adds a
health test that does not need the database (the `down` case with an unreachable connection string).

## Out of scope
- The test database (a1-04).
- The batch tables (a1-05) and any endpoint (a1-06).
- Inventory: its grants and mapping come with M7 (a7-01).

## Notes
- Measured 2026-11-02: `app.recipe` has 92 rows, 52 of them with a `process`; `status` is `draft`
  or `final` (the check also allows `brewed`); `style_id` references `ref.beer_style` (`code`,
  `name`). `app.recipe_item` has `id, recipe_id, ingredient_id, raw_name, usage, time_min, pct,
  amount, unit`.
- OPERATIONS.md §2 notes `postgres` is not a superuser here; check it can create roles before
  writing the file.

## Deviations

None yet.
