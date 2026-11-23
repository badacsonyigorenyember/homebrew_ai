# Test lesson: a1-05 · Batch tables

## What you will test

| Behaviour | AC | Level | Why this level |
|---|---|---|---|
| A batch with one item and one step, saved through `AppDbContext`, reads back with its item, its step and a real `created_at` | AC3 | Database integration: the app's own `AppDbContext`, as `app_api`, against a1-04's test container | The behaviour is the mapping meeting the real tables: column names, types, `DateOnly`, `jsonb`, the navigations and `[DatabaseGenerated]`. Only the real database proves them together |
| Deleting a batch deletes its items and steps | AC4 | The same | The cascade is in the database (`on delete cascade`), not in C#; it can only be seen there |
| A batch whose status is not a phase is refused | AC4 | The same | The check constraint is in the database too |

These are not HTTP tests: there is no endpoint yet (a1-06). They are not unit tests either: EF
Core's in-memory provider has no check constraints and no database cascades ([Cascade Delete](https://learn.microsoft.com/ef/core/saving/cascade-delete#where-cascading-behaviors-happen),
the note "The EF Core in-memory database does not currently support cascade deletes in the
database"), so a test against it would pass while proving nothing.

What not to test, and why:

- **The grants and the columns (AC2), and running the file twice (AC1).** They are facts about
  the schema; the review checked them with a catalog query and on your stack. AC3's test touches
  all three tables as `app_api` anyway, so a missing grant would fail it.
- **The phase check on `batch_step`.** It is the same mechanism as the status check, and AC4
  names the status. One test of a check constraint shows the pattern; a second shows nothing new.
- **`unique` on `number`.** a1-06's AC2 ("two batches get numbers 1 and 2") tests numbering
  where it is decided.
- **`on delete set null` on `source_item_id`.** No AC asks for it, and no code deletes a recipe
  item.
- **Every column one by one.** A misspelt `[Column]` fails every query on that table, so the
  read-back test catches it without an assertion per column. Assert what a reader would check:
  the values you put in, and the one column the database fills.

## Steps

All three tests go in one new file, `app/api.Tests/Database/BatchTablesTests.cs`, namespace
`HomebrewApp.Tests.Database`, next to `AppApiRoleTests.cs`: the folder is named after what it
tests (the `db/` files), as in a1-04.

1. **Test AC3: a batch with an item and a step reads back.**

   **Read first (about 25 minutes).**
   - [Dependency injection in ASP.NET Core, "Resolve a service at app startup"](https://learn.microsoft.com/aspnet/core/fundamentals/dependency-injection?view=aspnetcore-10.0#resolve-a-service-at-app-startup):
     the one example; `app.Services` there is `factory.Services` here.
   - [.NET dependency injection, "Scope validation"](https://learn.microsoft.com/dotnet/core/extensions/dependency-injection/overview#scope-validation):
     the two checks it lists.
   - [Saving related data, "Adding a graph of new entities"](https://learn.microsoft.com/ef/core/saving/related-data#adding-a-graph-of-new-entities):
     a blog added with its posts in one `Add`.
   - [Eager loading of related data](https://learn.microsoft.com/ef/core/querying/related-data/eager):
     "Eager loading", the first example and the one with two `Include`s.
   - [ExecuteUpdate and ExecuteDelete, "ExecuteDelete"](https://learn.microsoft.com/ef/core/saving/execute-insert-update-delete#executedelete):
     the one-line version.

   **1a. The class.** `public class BatchTablesTests`, with `[Collection(nameof(ApiCollection))]`
   and a primary constructor taking the `ApiFactory`, exactly like `AppApiRoleTests`.
   *Why:* the collection is what starts the container and runs `061` (lesson step 6).

   **1b. A context from the app, inside a scope.** The test is a `[Fact]`, `public async Task`,
   named like `Batch_WithItemAndStep_ReadsBackThroughAppDbContext` (the
   `Subject_Condition_Expectation` shape of a1-03's test lesson). Its first line opens a scope: `await using var` (or an
   `await using (…) { }` block, see 1e), a name, `=`, then `factory.Services.CreateAsyncScope()`.
   Inside it, `scope.ServiceProvider.GetRequiredService<AppDbContext>()` gives the context. Both
   methods are extension methods in `Microsoft.Extensions.DependencyInjection`; add that `using`.
   *Why:* `factory.Services` is the API's own service container, built from `Program.cs` with
   the factory's connection string. A context taken from it is configured exactly like the one a
   request gets: Npgsql, no-tracking, `app_api`, the test container. Building your own
   `DbContextOptions` in the test would copy that configuration, and a copy can drift. a1-03
   registered `AppDbContext` as **scoped**: one per HTTP request. A test has no request, so it
   makes its own scope, a "pretend request" that owns the context and disposes it when the
   `await using` ends.
   *Watch out:* skipping the scope and asking `factory.Services` directly fails every time, with
   (measured) *System.InvalidOperationException : Cannot resolve scoped service
   'HomebrewApp.Data.AppDbContext' from root provider.* That is the scope validation you read
   about: the tests run in `Development`, where it is on. Without the `using`, the build fails with
   (measured) *error CS1061: 'IServiceProvider' does not contain a definition for
   'CreateAsyncScope' …*.

   **1c. Arrange and act: one batch, one item, one step, one save.** Look up a recipe id first:
   `db.Recipes`, `Select` the `Id`, `FirstAsync()`. Then a `new Batch { … }` with every
   `required` property **and `RecipeId`** (a foreign key, so not `required`: the compiler will not
   remind you, and a missing one is `0`, which the database refuses), a batch number no other test uses (say `501`), and `Items` and `Steps`
   each given a one-element collection expression (`[new BatchItem { … }]`), the same `[ … ]`
   you used to initialise them in the entity. Leave `BatchId` out of both children. Add the batch
   to `db.Batches`, `await db.SaveChangesAsync()`, and keep `batch.Id` in a variable.
   *Why:* the recipe id is looked up, not written as `1`: ids are generated by Postgres, and
   a1-04's seed lesson made the same choice for the same reason. Adding the batch with its
   children is the **graph** pattern from the reading: EF Core inserts the batch, gets its id,
   and writes it into each child's `BatchId` (measured in review round 2). It is also how a1-06
   will create a batch, so this test proves a1-06's starting point. The number matters because
   all tests share one database during a run and `number` is `unique`: two tests with the same
   number would fail each other with *duplicate key value violates unique constraint
   "batch_number_key"*.

   **1d. Assert, from a second scope.** Open a second scope (and context) and read the batch
   back: `db.Batches`, `Include` its `Items`, `Include` its `Steps`, then `SingleAsync` on the id
   you kept. Then assert:
   - the name equals the one you gave;
   - `Assert.Single(saved.Items)` — it returns the one element, so you can check its `RawName`
     in the same line; the same for `Steps` and the `Title`;
   - `CreatedAt` is **not** `DateTime.MinValue` (`Assert.NotEqual`).

   *Why:* the second context has never seen this batch, so everything it returns came from the
   database, not from the first context's memory. That is what "read them back" (AC3) means.
   `Include` is **eager loading**: without it the query loads the batch alone and `Items` stays
   the empty `[]` from the entity, so `Assert.Single` would fail even though the rows exist.
   `Assert.Single` fails when there are zero or two, so it checks the count and gives you the
   item in one call. `CreatedAt` is the one value you did not write; checking it is not
   `MinValue` is what proves `[DatabaseGenerated]` works (lesson step 7b), without depending on
   the clock.

   **1e. Clean up.** Last line, still in the second scope: delete the batch with
   `db.Batches.Where(…id…).ExecuteDeleteAsync()`. If you used `await using var` for both scopes,
   the two variable names clash in one method; put each scope in an `await using (…) { … }` block
   instead.
   *Why:* the container lives for the whole test run, so a row one test leaves behind is there
   for every later test. a1-06's numbering test expects the first batch to get number 1; a
   leftover 501 would make it 502. Leaving the database as you found it is a **test pattern**:
   each test owns its data, from insert to delete. `ExecuteDeleteAsync` sends one `DELETE` at
   once, without loading anything, and the database's cascade takes the item and the step.

   **See it fail first.** In `app/api/Features/Batches/Batch.cs`, delete the
   `[DatabaseGenerated(…)]` line and run `dotnet test`. Your test fails with (measured)
   *Assert.NotEqual() Failure: Values are equal · Expected: Not 0001-01-01T00:00:00.0000000 ·
   Actual: 0001-01-01T00:00:00.0000000*: EF Core wrote `-infinity`, which reads back as
   `MinValue`. Put the line back.
   *Check yourself:* `dotnet test` passes 5 tests; `git diff app/api/` shows nothing.
   **Commit:** `git add app/api.Tests/Database/BatchTablesTests.cs`, message
   `Test that a batch reads back through AppDbContext`.

2. **Test AC4, first half: deleting a batch deletes its items and steps.**

   A second `[Fact]` in the same class, named like `DeleteBatch_WithItemAndStep_DeletesThem`.
   One scope is enough. Arrange: a batch with one item and one step, as in 1c, with its own
   number (`502`), saved. Act: `ExecuteDeleteAsync` on that batch, as in 1e. Assert: the count of
   `db.BatchItems` whose `BatchId` is the batch's id is `0`, and the same for `db.BatchSteps`
   (`CountAsync` with a condition).
   *Why:* arrange, act, assert are the three parts of a test (a0-02's pattern), and here the
   delete **is** the act, so this test needs no clean-up. `ExecuteDeleteAsync`, not loading the
   batch and calling `Remove`: with the children loaded, EF Core would delete them itself and the
   test would pass even without the database's cascade ([Cascade Delete](https://learn.microsoft.com/ef/core/saving/cascade-delete#configuring-cascading-behaviors),
   note 3 under "Required relationship with dependents/children loaded"). With nothing loaded,
   only `on delete cascade` can remove them, which is what AC4 is about. Counting through the
   two child sets is why lesson step 8 added `BatchItems` and `BatchSteps`. Count by this batch's
   id, not all rows: other tests' rows must not change this test's answer.

   **See it fail first.** In `db/061_app_batch.sql`, remove `on delete cascade` from
   `batch_item`'s `batch_id` only, and run `dotnet test` (the container copies `db/` at every
   run). Both batch tests now fail with (measured) *Npgsql.PostgresException : 23503: update or
   delete on table "batch" violates foreign key constraint "batch_item_batch_id_fkey" on table
   "batch_item"*: without the cascade, Postgres refuses to delete a batch that still has items.
   Put it back and check `git diff db/` is empty.
   *Watch out:* this edit is for the test run only. Never apply `061` to your stack while it is
   changed; `create table if not exists` would skip it anyway, but the habit matters for files
   that do change things.
   *Check yourself:* `dotnet test` passes 6 tests.
   **Commit:** `git add app/api.Tests/Database/BatchTablesTests.cs`, message
   `Test that deleting a batch deletes its children`.

3. **Test AC4, second half: a status outside the phases is refused.**

   **Read first (about 5 minutes).**
   [`DbUpdateException`](https://learn.microsoft.com/dotnet/api/microsoft.entityframeworkcore.dbupdateexception),
   the one-line description; [`PostgresException`](https://www.npgsql.org/doc/api/Npgsql.PostgresException.html),
   find `SqlState` and `ConstraintName`; [PostgreSQL 15 — Error codes](https://www.postgresql.org/docs/15/errcodes-appendix.html),
   find `23514`.

   A third `[Fact]`, named like `Batch_WithStatusOutsideThePhases_IsRefused`. One scope. Arrange:
   a batch with number `503` and status `"brewing"` (no items or steps needed), added to
   `db.Batches`. Act and assert together: `Assert.ThrowsAsync<DbUpdateException>`, passing a
   lambda that calls `db.SaveChangesAsync()`; it returns the exception. Then
   `Assert.IsType<PostgresException>` on its `InnerException`, which returns it typed, and assert
   its `SqlState` equals `PostgresErrorCodes.CheckViolation` and its `ConstraintName` equals
   `"batch_status_check"`.
   *Why:* this is a1-04's `ThrowsAsync` and `SqlState` pattern, one layer deeper. EF Core does
   not let a database error through as it is: `SaveChanges` wraps it in a
   `DbUpdateException` and keeps the original as the **inner exception**. Checking the code
   (`23514`, a check violation) and the constraint's name proves the row was refused **by the
   status check**, not for any other reason (a forgotten foreign key also throws a
   `DbUpdateException`, with `23503`; measured in review round 1). No clean-up: the insert never
   happened.
   *Watch out:* `Assert.ThrowsAsync<PostgresException>` straight around `SaveChangesAsync` (the
   a1-04 shape) fails with (measured) *Assert.Throws() Failure: Exception type was not an exact
   match · Expected: typeof(Npgsql.PostgresException) · Actual:
   typeof(Microsoft.EntityFrameworkCore.DbUpdateException)*. `ThrowsAsync` wants the exact type
   that was thrown; the Postgres error is one level down.

   **See it fail first.** In `db/061_app_batch.sql`, add `'brewing'` to `app.batch`'s status
   list and run `dotnet test`. Your test fails with (measured) *Assert.Throws() Failure: No
   exception was thrown · Expected: typeof(Microsoft.EntityFrameworkCore.DbUpdateException)*. Put
   it back and check `git diff db/` is empty.
   *Check yourself:* `dotnet test` passes 7 tests.
   **Commit:** `git add app/api.Tests/Database/BatchTablesTests.cs`, message
   `Test that an unknown batch status is refused`.

## Before you ask for a test review

- [ ] Three tests, one per behaviour in the table above, each named `Subject_Condition_Expectation`.
- [ ] You saw each one fail, with the messages above, and undid each break:
      `git diff app/api/ db/` is empty.
- [ ] Each test uses its own batch number, and none leaves a batch behind (the AC3 test deletes
      its batch; the AC4 tests delete it or never insert it).
- [ ] The recipe id is looked up, not written as a number.
- [ ] `dotnet build` reports 0 warnings; `dotnet test` passes 7 tests.
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted.
