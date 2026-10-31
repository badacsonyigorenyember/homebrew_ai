# a2-01 · The API's database role and EF Core

Stage: ready
Branch: `a2-01-db-role-and-ef`
Milestone: M2 · Requirements: §8 role, C5 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-06

## Goal
The API reads and writes Postgres as its own role, with EF Core mapping the existing tables it
needs.

## What to build
- `db/060_app_api_role.sql`: role `app_api` (login), with the password passed in as a `psql`
  variable, never written in the file; usage on schemas `app` and `ref`; select, insert, update,
  delete on `app.inventory`; select on `app.brewer_profile` and `ref.ingredient`; the sequence
  rights inserts need. Idempotent. Applied as `postgres` (OPERATIONS.md §4).
- The connection string from configuration (`ConnectionStrings:App`, user secrets in development).
- EF Core with Npgsql: an `AppDbContext` mapping `app.inventory`, `app.brewer_profile` and
  `ref.ingredient` (read-only in code). No EF migrations.
- `/api/health` gains `database`: `ok` or `down`, from a cheap query.
- OPERATIONS.md: the role, how its password is set, and that it must be set again after a password
  rotation.

## Acceptance criteria
- **AC1** The role and its grants are as listed (checked by a catalog query, written in the ticket's
  review).
- **AC2** Running the SQL file twice changes nothing.
- **AC3** `app_api` can read `ref.ingredient` and cannot insert into it.
- **AC4** With the API running, `/api/health` shows `database: ok`; with a wrong password,
  `database: down` and the API still answers.
- **AC5** No password in any committed file.

## Tests
Needed, but against a throwaway database, which is a2-02. This ticket's tests stage only adds a
health test that does not need the database (the `down` case with an unreachable connection string).

## Out of scope
- The test database (a2-02).
- Any inventory endpoint (a2-03).

## Notes
- Measured 2026-10-31: `ref.ingredient` has `id, kind, name, name_key, producer, producer_key,
  source_id, raw`; `kind` is one of fermentable 81, hop 89, misc 4, water_salt 8, yeast 119;
  `app.inventory` has 0 rows.
- OPERATIONS.md §2 notes `postgres` is not a superuser here; check it can create roles before
  writing the file.

## Deviations

None yet.
