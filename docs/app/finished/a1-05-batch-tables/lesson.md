# Lesson: a1-05 · Batch tables

## What you will build

The three tables a batch lives in: `app.batch` (one row per brew), `app.batch_item` (the batch's
own copy of the recipe's ingredients) and `app.batch_step` (the checklist). One new SQL file
creates them, with every column the app will need up to M3, and lets `app_api` read and write
them. The test database builds them too, and `AppDbContext` maps them to three C# classes, so
a1-06 can create a batch and later tickets can tick its steps.

It is done when:

- **AC1** Running the SQL file twice changes nothing.
- **AC2** The columns and grants are as listed (the review checks them with a catalog query).
- **AC3** In the test database, `app_api` can insert a batch with an item and a step, and read
  them back through `AppDbContext`.
- **AC4** Deleting a batch deletes its items and steps; a status outside the phases is refused.

AC3 and AC4 are proven by integration tests, written after the review from `test-lesson.md`. In
this lesson you check them by hand.

**How the pieces fit.** `db/061_app_batch.sql` runs by hand as `postgres` on your stack, like
`060`. A batch points at the recipe it was made from; its items and steps point at the batch, and
go when it goes. The test fixture (`ApiFactory`, a1-04) runs the same file in the test container,
after `060`, so the test database has the tables and `app_api` has its rights there too. In the
API, three entity classes in `Features/Batches/` describe the tables, and `AppDbContext` gets a
`DbSet` for each; a1-06 is the first code that uses them.

```
app.recipe ◄── app.batch ◄── app.batch_item   (on delete cascade)
                    ▲    ◄── app.batch_step   (on delete cascade)
                    │
 AppDbContext: Batches ── Batch.Items / Batch.Steps  (Features/Batches/)
```

What the tools look like today (measured 2026-11-19 in a scratch container from the stack's image
`supabase/postgres:15.8.1.085`, and a scratch console project with SDK 10.0.115 and
`Npgsql.EntityFrameworkCore.PostgreSQL` 10.0.3; every error quoted below comes from those runs):

| Thing | Value | Note |
|---|---|---|
| `app.batch` on your stack | does not exist yet | `to_regclass('app.batch')` is null |
| Recipes with a `process` | 53, newest id 1489 | the ones a batch can be made from |
| Inserting into an identity column as `app_api` | works with **no** grant on its sequence | step 4 explains why |
| `date` in Npgsql 10 | reads as `DateOnly` | before 10.0 it was `DateTime` |

## Steps

1. **Check where you are.** From the repo root, run `git branch --show-current` and `git status`.
   *Why:* the work belongs on the ticket's branch, and a clean start keeps the review diff to this
   ticket.
   *Check yourself:* the branch is `a1-05-batch-tables`; `git status` is clean.
   No commit.

2. **Start `db/061_app_batch.sql` with `app.batch`.**

   **Read first (about 35 minutes).**
   - `db/015_app.sql`, lines 48–76: `app.recipe` and `app.recipe_item`. Your tables follow the
     same style (lower-case SQL, one column per line, a short comment where a column needs one).
   - [PostgreSQL 15 — Constraints](https://www.postgresql.org/docs/15/ddl-constraints.html):
     5.4.1 Check Constraints (the first example and what happens on a failing row), 5.4.2
     Not-Null, 5.4.3 Unique, 5.4.5 Foreign Keys (up to and including `ON DELETE CASCADE` and
     `SET NULL`).
   - [PostgreSQL 15 — `CREATE TABLE`](https://www.postgresql.org/docs/15/sql-createtable.html):
     the parameters `IF NOT EXISTS`, `DEFAULT` and `GENERATED { ALWAYS | BY DEFAULT } AS
     IDENTITY`. Skim; the examples at the bottom are the useful part.
   - [PostgreSQL 15 — Date/Time Types](https://www.postgresql.org/docs/15/datatype-datetime.html):
     the first table, the rows `timestamp with time zone` and `date`.

   **2a. The header.** The comment block every `db/` file has (copy its shape from
   `db/058_home_profile.sql`): what the file does (the batch tables and `app_api`'s rights on
   them), a `Needs` line (`db/015_app.sql` for `app.recipe`, `app.recipe_item` and
   `ref.ingredient`; `db/060_app_api_role.sql` for the role step 4 grants to), the apply line from
   OPERATIONS.md §4 with this file's name, and `Idempotent: safe to re-run.`
   *Why:* the `Needs` line is the only place that says in which order the files run; the test
   fixture (step 6) and anyone rebuilding the stack follow it.

   **2b. The table.** `create table if not exists app.batch (…)` with these columns, in this order:

   | Column | Type | Rule | Why |
   |---|---|---|---|
   | `id` | `bigint` | identity, primary key | as every `app` table |
   | `number` | `integer` | not null, unique | "Batch 7", given by a1-06 as the highest plus one |
   | `name` | `text` | not null | |
   | `recipe_id` | `bigint` | not null, references `app.recipe (id)` | the recipe it was copied from |
   | `brew_date` | `date` | not null | a calendar date, not a moment (SYSTEM.md §9) |
   | `status` | `text` | not null, default `'plan'`, check: one of the seven phases | F4.12 |
   | `batch_l` | `numeric(5, 1)` | not null | copied from the recipe |
   | `efficiency_pct` | `numeric(4, 1)` | not null | copied |
   | `process` | `jsonb` | not null | copied; a1-06 refuses a recipe without one |
   | `og`, `fg` | `numeric(5, 4)` | nullable | copied (planned values) |
   | `abv` | `numeric(4, 1)` | nullable | copied |
   | `ibu`, `srm` | `numeric(5, 1)` | nullable | copied |
   | `locked_at` | `timestamptz` | nullable | M3 (F4.3): set when the first Brew day step is ticked |
   | `created_at` | `timestamptz` | not null, default `now()` | |

   The seven phases, in the stepper's order: `plan`, `prep`, `brew_day`, `ferment`, `condition`,
   `package`, `done`. The check is `status in (…)` with the seven in single quotes, the same form
   as `app.recipe`'s `status` check.

   *Why:* every column §8 lists is here now, including M3's `locked_at`, so M3 needs no `alter
   table` (the ticket). The copied columns have **exactly** `app.recipe`'s types and nullability:
   a copy can then never be refused or rounded on the way in. A **check constraint** makes the
   database refuse a row whose status is not a phase, whatever code wrote it (AC4); the C# code
   can have bugs, the constraint holds for every writer. **`unique`** on `number` does the same
   for "no two batches share a number": a1-06 picks the number, but if two requests ever pick the
   same one, the second insert fails instead of creating a duplicate. The **foreign key** to
   `app.recipe` has no `on delete` rule, so the default applies: a recipe with batches cannot be
   deleted. That is what you want, since the batch says where it came from. `timestamptz` (short
   for `timestamp with time zone`) stores a moment in UTC; `date` stores a day with no time, so a
   brew date never shifts by a time zone.
   *Watch out:* `create table if not exists` skips the whole statement when the table exists. If
   you apply the file, then add or change a column, the second run says (measured)
   *NOTICE: relation "batch" already exists, skipping* and the table stays as it was: the change
   is silently not applied. While this ticket is open the tables are new and empty, so the fix is
   to drop them by hand as `postgres` (`drop table app.batch_step, app.batch_item, app.batch;`,
   children first) and apply the file again. Once a1-06 has made a real batch, never do this; a
   change then is an `alter table`.

   **2c. Apply it, twice.** Run the apply line from your header, then run it again.
   *Check yourself:* the first run prints `CREATE TABLE`; the second prints the *already exists,
   skipping* notice and `CREATE TABLE`, and no `ERROR` (AC1 for this table). In psql as
   `postgres` (`docker exec -it supabase-db psql -U postgres -d postgres`), `\d app.batch` shows
   the sixteen columns, `batch_number_key` under *Indexes*, `batch_status_check` under *Check
   constraints* and `batch_recipe_id_fkey` under *Foreign-key constraints*. Postgres made up those
   names from the table, the column and the kind of constraint; you will see them in error
   messages.
   **Commit:** `git add db/061_app_batch.sql`, message `Add the app.batch table`.

3. **Add `app.batch_item` and `app.batch_step`** to the same file, after `app.batch`.

   **3a. `app.batch_item`**, the batch recipe (F4.2): the columns of `app.recipe_item`, with the
   same types, `batch_id` in place of `recipe_id`, and two more.

   | Column | Type | Rule | Why |
   |---|---|---|---|
   | `id` | `bigint` | identity, primary key | |
   | `batch_id` | `bigint` | not null, references `app.batch (id)` **on delete cascade** | AC4 |
   | `source_item_id` | `bigint` | nullable, references `app.recipe_item (id)` **on delete set null** | the recipe item it was copied from (a1-06) |
   | `ingredient_id` | `bigint` | nullable, references `ref.ingredient (id)` | as in `recipe_item` |
   | `raw_name`, `usage` | `text` | not null | |
   | `time_min` | `numeric(6, 1)` | nullable | |
   | `pct` | `numeric(5, 2)` | nullable | |
   | `amount` | `numeric(10, 3)` | not null | |
   | `unit` | `text` | not null | |
   | `changed` | `boolean` | not null, default `false` | M3: the item was edited in Plan or Prep |

   Then an index on `batch_id`, written like `recipe_item_recipe_id_idx` in `015`: `create index
   if not exists batch_item_batch_id_idx on …`.

   *Why:* **`on delete cascade`** tells Postgres that an item cannot exist without its batch:
   deleting the batch deletes its items in the same statement (AC4), so no orphan rows are left
   and no code has to remember to clean up. `source_item_id` uses **`on delete set null`**
   instead: the copy is the point of a batch (F4.1), so if the recipe item ever goes, the batch
   keeps its item and only forgets where it came from. Postgres does not index a foreign key
   column by itself, and both "the items of batch 7" and the cascade look rows up by `batch_id`;
   the index makes that a lookup instead of a full table scan.

   **3b. `app.batch_step`**, the checklist (F4.4–F4.10):

   | Column | Type | Rule | Why |
   |---|---|---|---|
   | `id` | `bigint` | identity, primary key | |
   | `batch_id` | `bigint` | not null, references `app.batch (id)` on delete cascade | AC4 |
   | `phase` | `text` | not null, check: one of the seven phases | the stepper phase it belongs to |
   | `position` | `integer` | not null | order within its phase |
   | `title` | `text` | not null | "Mash in 5.7 kg" |
   | `planned` | `jsonb` | not null, default `'[]'` | a1-08: a list of `{ key, label, value, unit }` |
   | `actual` | `jsonb` | not null, default `'{}'` | a1-10: key → number; empty means as planned |
   | `step_date` | `date` | nullable | F4.6; a Done step may have none |
   | `date_pinned` | `boolean` | not null, default `false` | F4.6: the date was set by hand |
   | `source` | `text` | not null | `mash.steps[0]`, `user` or `ai` (F4.4) |
   | `done_at` | `timestamptz` | nullable | F4.8: when it was ticked; null is not ticked |
   | `note` | `text` | nullable | F4.9 |
   | `timer_started_at` | `timestamptz` | nullable | F4.10 |

   And an index on `batch_id`, as in 3a.

   *Why:* `step_date`, not `date`: `date` is also the name of a type, and `date date` reads badly
   in every query. `planned` and `actual` are `jsonb` because each step has different values
   (a rest has a temperature and minutes, a hop addition grams): one column holds any set of them,
   and a1-08 and a1-10 settle their shape. A `jsonb` default is written as a JSON text in single
   quotes. `done_at` is a time, not a `done` flag: "is it ticked" is "is it not null", and the time
   comes for free (F4.8). The phase check repeats the seven names; one list in two places is fine
   for two columns, and a separate lookup table would be machinery this ticket does not need.

   **3c. Apply it twice**, as in 2c.
   *Check yourself:* no `ERROR` on either run. `\d app.batch_item` and `\d app.batch_step` show the
   columns, the index on `batch_id`, and the foreign keys ending in `ON DELETE CASCADE` (and
   `ON DELETE SET NULL` for `source_item_id`).
   **Commit:** `git add db/061_app_batch.sql`, message `Add the batch item and step tables`.

4. **Grant `app_api` its rights**, at the end of the file.

   **Read first (about 10 minutes).**
   [PostgreSQL 15 — Privileges](https://www.postgresql.org/docs/15/ddl-priv.html): the list of
   privileges, `SELECT`, `INSERT`, `UPDATE`, `DELETE`, and for sequences `USAGE`.
   [Sequence Manipulation Functions](https://www.postgresql.org/docs/15/functions-sequence.html):
   the sentence under `nextval` on the privilege it needs.

   One `grant` statement: `select, insert, update, delete` on the three tables, to `app_api`. No
   grant on any sequence.

   *Why:* a1-03's least privilege, one step further: the API now writes batches, so it gets the
   four rights it needs on these three tables and still only `select` on recipes. It needs
   `delete` too (AC4, and deleting a batch in M3). Behind every identity column is a
   **sequence**, a counter object that hands out the next id (`\dp app.batch*` lists them as
   `batch_id_seq` and so on). An old-style `serial` column calls `nextval` on its sequence as the
   inserting role, which needs `usage` on it; an identity column draws the number as part of the
   insert itself, and the insert privilege is enough. Measured both ways: an identity table with
   no sequence grant takes `app_api`'s insert; a `serial` table refuses it with *ERROR: permission
   denied for sequence serial_demo_id_seq*. So "the sequence rights inserts need" (the ticket) are
   none, and granting them anyway would be a right nobody uses. No `references` privilege either:
   that one is for *creating* a foreign key, which `postgres` does; inserting a row that points at
   a recipe needs none.
   *Watch out:* `usage` on schema `app` is already granted by `060`; don't repeat it here. Each
   right is granted in one file, so `grep` finds where it comes from.
   *Check yourself:* apply twice (no `ERROR`; `GRANT` on both runs). `\dp app.batch*` shows
   `app_api=arwd/postgres` on the three tables (`a` insert, `r` select, `w` update, `d` delete)
   and nothing on the three sequences. That is AC1 and AC2.
   **Commit:** `git add db/061_app_batch.sql`, message `Grant app_api access to the batch tables`.

5. **Check AC4 by hand, as `app_api`, and leave nothing behind.**

   **Read first (5 minutes).** [PostgreSQL 15 — Transactions](https://www.postgresql.org/docs/15/tutorial-transactions.html):
   what `BEGIN` and `ROLLBACK` do.

   Open psql as the role: `docker exec -it supabase-db psql -h 127.0.0.1 -U app_api -d postgres`.
   Then, in one session:
   - `begin;`
   - insert a batch for recipe 1489 (or any recipe with a `process`), giving every not-null
     column without a default, and end the statement with `returning id` to see the id it got;
   - insert one item and one step for that batch id (only the not-null columns without a default);
   - `delete from app.batch where id = …;`
   - count the rows of `app.batch_item` and `app.batch_step` for that batch id;
   - insert a batch with status `brewing`;
   - `rollback;`

   *Why:* the catalog says what was granted; trying it shows the rights, the cascade and the check
   working together, as the API will use them. A **transaction** groups statements so they take
   effect together or not at all; `rollback` undoes all of them, so your stack keeps no test
   batch and batch numbers stay free for real ones. The bad status goes last because of the next
   point.
   *Watch out:* after any error inside a transaction, Postgres refuses every further statement
   with (measured) *ERROR: current transaction is aborted, commands ignored until end of
   transaction block* until you `rollback`. Ids are not rolled back: the next real batch may get
   id 2, not 1. That is normal; ids are names, not counts, which is why `number` is its own
   column.
   *Check yourself:* the three inserts succeed; the counts after the delete are both `0`; the
   `brewing` insert fails with (measured) *ERROR: new row for relation "batch" violates check
   constraint "batch_status_check"*. After the rollback, `select count(*) from app.batch;` is `0`.
   No commit.

6. **Build the tables in the test database.** In `app/api.Tests/ApiFactory.cs`, `InitializeAsync`
   runs one more file, `/db/061_app_batch.sql`, right after `060`, with a one-line comment above
   it like the other three (what the file gives the tests).
   *Why:* the test container is built only from what the fixture runs (a1-04's AC4: the list of
   files is in one place, each with a comment). Without this line, the test lesson's AC3 tests
   would fail with *ERROR: relation "app.batch" does not exist*. After `060`, because the grants
   name `app_api` and the role must exist first; before the seed, because the seed comes last.
   *Check yourself:* `dotnet test` in `app/` passes, as before. Then break it once: misspell a
   table name in the file's `grant` (do not apply it to the stack); `dotnet test` fails in the
   fixture with *…061_app_batch.sql failed with error: …ERROR: relation "…" does not exist*. Put
   it back.
   **Commit:** `git add app/api.Tests/ApiFactory.cs`, message `Apply the batch tables in the test database`.

7. **Write the three entity classes** in a new folder `app/api/Features/Batches/`, namespace
   `HomebrewApp.Features.Batches`, one file each: `Batch.cs`, `BatchItem.cs`, `BatchStep.cs`. They
   follow `Data/Recipe.cs` and `Data/RecipeItem.cs` (a1-03 step 7: `[Table]`, `[Column]`, `long`
   ids, `decimal` for numerics, `string` with `TypeName = "jsonb"` for JSON, `{ get; init; }`,
   `required` on every value the code must give). This step covers only what is new.
   None is used yet, so the build stays green as long as all three exist by the end of the step.

   **Read first (about 20 minutes).**
   - [EF Core — Generated Values](https://learn.microsoft.com/ef/core/modeling/generated-properties):
     "Default values" and "Explicitly configuring value generation" (the *Data Annotations* tab).
   - [EF Core — Additional Change Tracking Features, "Working with default values"](https://learn.microsoft.com/ef/core/change-tracking/miscellaneous#working-with-default-values):
     the first paragraph and the `Token` example.
   - [Npgsql — Date and Time Handling](https://www.npgsql.org/doc/types/datetime.html): the mapping
     table (look for `date`) and the paragraph on `-infinity`.
   - [EF Core — Cascade Delete, "Where cascading behaviors happen"](https://learn.microsoft.com/ef/core/saving/cascade-delete#where-cascading-behaviors-happen):
     the first example, where the database deletes the children EF Core never loaded.

   Why `Features/Batches/` and not `Data/`: a1-03 put the recipe classes in `Data/` because those
   tables existed already and several features read them. These three are made for the batch
   feature and written only by it, so they live with its endpoints (a1-06) and its step generator
   (a1-08), as SYSTEM.md §5 lays out: one folder per feature.

   **7a. `Batch`: the columns.** Table `app.batch`, one property per column. The new types:
   `integer` (here `number`, and `position` in 7e) is `int`; `date` is **`DateOnly`**; `boolean`
   is `bool`; a nullable `timestamptz` is `DateTime?`.
   *Why:* `DateOnly` is .NET's type for a day with no time, the exact match of `date`; Npgsql 10
   reads `date` as `DateOnly` by default. `required` goes on every property a1-06 must set
   (number, name, recipe id, brew date, status, the copied numbers that are not null, process),
   not on `Id` or `CreatedAt`, which the database fills.

   **7b. `Batch.CreatedAt`: let the database fill it.** Besides `[Column]`, the attribute
   `[DatabaseGenerated(DatabaseGeneratedOption.Identity)]` (namespace
   `System.ComponentModel.DataAnnotations.Schema`, already imported for `[Table]`).
   *Why:* a database default only applies when an insert leaves the column out, and EF Core
   writes **every** mapped property on insert unless it is told the database generates it.
   `Identity` here means "the database gives this a value when the row is added" (not an identity
   column); EF Core then leaves it out of the insert and reads the value back. The `Id` property
   needs no attribute: EF Core assumes that for a `long` key by convention.
   *Watch out:* without the attribute nothing fails. EF Core sends `CreatedAt`'s default,
   `DateTime.MinValue`, and Npgsql stores that as `-infinity`; measured: the row's `created_at`
   reads `-infinity` in psql, and `now()` is never used. The test lesson's read-back test is where
   you would see it.

   **7c. `Batch`: the navigations.** `Recipe`, of type `Recipe` (from `HomebrewApp.Data`; add
   that `using`), initialised to `null!` exactly as `Recipe.Style`; `Items`, a `List<BatchItem>`,
   and `Steps`, a `List<BatchStep>`, both initialised to `[]` exactly as `Recipe.Items`.
   *Why:* a1-06 lists batches with their recipe's style (`Batch.Recipe.Style`), and a1-09 loads a
   batch with its items and steps. With `Items` and `Steps` you can also add a batch together
   with its children in one `Add`: EF Core inserts the batch first, then fills each child's
   `BatchId` with the new id. Both relationships are **required** (`BatchId` is not nullable), so
   EF Core assumes cascade delete, which matches the `on delete cascade` from step 3.

   **7d. `BatchItem`.** Table `app.batch_item`, all eleven columns, with the same types as
   `RecipeItem` for the copied ones; `SourceItemId` is `long?`; `Changed` is a `bool`. One
   navigation, `Ingredient?`, as in `RecipeItem`. No navigation to the source recipe item: nothing
   needs to load it; the id is enough.

   **7e. `BatchStep`.** Table `app.batch_step`, all thirteen columns: `Planned` and `Actual` are
   `string` with `TypeName = "jsonb"`, as `Recipe.Process`; `StepDate` is `DateOnly?`;
   `DatePinned` is a `bool`; `DoneAt` and `TimerStartedAt` are `DateTime?`.
   *Why:* `Planned` and `Actual` stay JSON strings for now, as `process` did in a1-03: a1-08 and
   a1-10 decide how to read them. `DatePinned` and `Changed` need no `[DatabaseGenerated]`: C#'s
   default for a `bool` is `false`, the same as the column's default, so sending it changes
   nothing. `{ get; init; }` like the recipe classes: a1-09 is the first ticket that changes a
   saved step, and it decides then how.

   *Check yourself (whole step):* `dotnet build` in `app/` ends with `0 Warning(s)` and
   `0 Error(s)`. Compare each `[Column]` with `\d` of its table: a misspelt name builds fine and
   only fails when a query runs, which the test lesson's tests will be the first to do.
   **Commit:** `git add app/api/Features/Batches/`, message `Add entity classes for batches`.

8. **Add the three sets to `AppDbContext`.** Three more `DbSet<T>` properties in
   `app/api/Data/AppDbContext.cs`, written as the existing four: `Batches`, `BatchItems`,
   `BatchSteps`, with a `using` for `HomebrewApp.Features.Batches`.
   *Why:* until a class is reachable from the context, EF Core does not know it is part of the
   model (a1-03 step 8b). `Batches` is where a1-06 adds a batch and a1-09 reads one; the two child
   sets let a test or an endpoint go straight to a step without loading its batch.
   *Check yourself:* `dotnet build` with no warnings and `dotnet test` green. The mapping is
   proven by the test lesson's first test (AC3), which inserts and reads back through these sets.
   **Commit:** `git add app/api/Data/AppDbContext.cs`, message `Map the batch tables in AppDbContext`.

## Files you will touch

- `db/061_app_batch.sql`: new; the three tables, their indexes and `app_api`'s grants.
- `app/api.Tests/ApiFactory.cs`: runs `061` after `060`.
- `app/api/Features/Batches/Batch.cs`, `BatchItem.cs`, `BatchStep.cs`: new entity classes.
- `app/api/Data/AppDbContext.cs`: three more sets.

## Before you ask for a review

- [ ] The file ran twice on the stack without an `ERROR` (AC1), and `\d` of each table and
      `\dp app.batch*` show the columns, constraints and grants of steps 2–4 (AC2).
- [ ] Step 5's transaction: the inserts worked, the delete took the item and step with it, the
      `brewing` status was refused, and after the rollback `app.batch` is empty (AC4).
- [ ] `Batch.CreatedAt` has `[DatabaseGenerated(DatabaseGeneratedOption.Identity)]`.
- [ ] Each `[Column]` name matches `\d` of its table.
- [ ] `dotnet build` in `app/` reports 0 warnings and 0 errors; `dotnet test` passes.
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted.
