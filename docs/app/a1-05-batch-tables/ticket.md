# a1-05 · Batch tables

Stage: ready
Branch: `a1-05-batch-tables`
Milestone: M1 · Requirements: §8 `app.batch`, `app.batch_item`, `app.batch_step`, C5 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-04

## Goal
The tables a batch lives in exist, and the API can read and write them.

## What to build
- `db/061_app_batch.sql`: `app.batch`, `app.batch_item` and `app.batch_step` with every column §8
  lists, including the ones M3 uses (dates, pins, timers, `locked_at`), so M3 needs no `alter`.
  Checks: batch `status` and step `phase` are the stepper's phases (`plan`, `prep`, `brew_day`,
  `ferment`, `condition`, `package`, `done`); `batch.number` is unique; `batch.recipe_id`
  references `app.recipe`; items and steps are deleted with their batch.
- The same file grants `app_api` select, insert, update and delete on the three tables, and the
  sequence rights inserts need. Idempotent, with a `Needs` line, applied as `postgres`.
- `AppDbContext` maps the three tables, in `Features/Batches/`.
- The test fixture (a1-04) applies the file.

## Acceptance criteria
- **AC1** Running the SQL file twice changes nothing.
- **AC2** The columns and grants are as listed (a catalog query, written in the ticket's review).
- **AC3** In the test database, `app_api` can insert a batch with an item and a step, and read
  them back through `AppDbContext`.
- **AC4** Deleting a batch deletes its items and steps; a status outside the phases is refused.

## Tests
Needed: integration tests on the test database for AC3 and AC4.

## Out of scope
- Any endpoint (a1-06).

## Deviations

None yet.
