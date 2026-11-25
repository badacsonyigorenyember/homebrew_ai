# Test lesson: a1-06 · Create a batch from a recipe

## What you will test

| Behaviour | AC | Level | Why this level |
|---|---|---|---|
| Two creates on an empty table get numbers 1 and 2 | AC2 | API integration: an `HttpClient` from `ApiFactory` calling the real endpoint, on a1-04's test container | Numbering is "the highest so far plus one", a `max` query on the real table inside the real transaction. Only the database shows it |
| A new batch's items are the recipe's items, with their source ids | AC1 | The same, then a read through `AppDbContext` | The copy is what the endpoint saves; reading the rows back proves what is in the database, not only what the response says |
| Changing a recipe item afterwards leaves the batch's copy as it was | AC1 | The same, plus an admin connection to the container | `app_api` may not change a recipe (a1-03), so the test changes it as the container's admin |
| A recipe without a `process` gives 400 problem details; an unknown one 404 | AC3 | API integration | The status, the content type and the body are what the caller (a1-07) sees |
| A request without a name or brew date gives 400 with a message per field | AC4 | API integration | Validation runs in a filter in front of the endpoint; only a real request goes through it |
| A created batch is in `GET /api/batches` | AC5 | API integration | Create and list together, as a1-07 uses them |

All of them are HTTP tests: no handler is called directly. The endpoints are `private`, and what
matters is what a caller gets back, through routing, the validation filter, JSON and the database.

What not to test, and why:

- **`GET /api/recipes/brewable`.** No AC names it; you checked it on the stack (53 recipes, 1489
  first), and a1-07's dialog uses it in its own tests.
- **The `Location` header.** No caller follows it yet; a1-09 adds `GET /api/batches/{id}`, and a
  test there can follow the header to a real answer.
- **The exact wording of messages.** `"The Name field is required."` is the framework's text, not
  yours. Test that a field has a message, and that your own `detail` mentions the process.
- **Every copied batch value (`og`, `batch_l`, …).** AC1 asks about items. The batch's numbers
  are plain assignments, which the review checked; a test per property would test C#'s `=`.
- **Two creates at the same moment.** The `unique` constraint covers it (lesson step 6b), and one
  user (C1) never does it.

## Steps

All tests go in one new file, `app/api.Tests/Features/Batches/BatchEndpointsTests.cs`, namespace
`HomebrewApp.Tests.Features.Batches`: the folder mirrors `app/api/Features/Batches/`, as
`Features/Health/HealthEndpointsTests.cs` mirrors the health feature. The class is
`[Collection(nameof(ApiCollection))]` with a primary constructor taking the `ApiFactory`, like
every test class so far.

Every step ends with `dotnet test` green and a commit. "See it fail" means breaking the API's
code for one run, then putting it back exactly; check `git diff app/api/` is empty before you
commit.

1. **Test AC2: two batches get numbers 1 and 2.**

   **Read first (about 20 minutes).**
   - [Integration tests in ASP.NET Core, "Basic tests with the default WebApplicationFactory"](https://learn.microsoft.com/aspnet/core/test/integration-tests?view=aspnetcore-10.0#basic-tests-with-the-default-webapplicationfactory):
     the example test only; you met `CreateClient` in a0-02's test lesson.
   - [`HttpClientJsonExtensions`](https://learn.microsoft.com/dotnet/api/system.net.http.json.httpclientjsonextensions):
     the summaries of `PostAsJsonAsync` and `GetFromJsonAsync`.
   - [`HttpContentJsonExtensions.ReadFromJsonAsync`](https://learn.microsoft.com/dotnet/api/system.net.http.json.httpcontentjsonextensions.readfromjsonasync):
     the summary, and the remark that it uses the web defaults (camelCase).

   **1a. Arrange: an empty table and the recipe id.** A `[Fact]`, named like
   `CreateBatch_TwiceOnEmptyTable_NumbersOneAndTwo`. In a scope with a context (a1-05's test
   lesson, step 1b): delete **all** batches with `ExecuteDeleteAsync` on `Batches` (no `Where`),
   and look up the id of the seeded recipe that has a `process` (`Where` on `Process`, `Select`
   the id, `SingleAsync`). Keep the id in a variable declared before the scope.
   *Why:* all test classes share one container for the whole run, and the order they run in is
   not fixed. "Numbers 1 and 2" is only true on an empty table, so this test makes it empty
   instead of hoping it is. `app_api` may delete batches (a1-05's grant), and the cascade takes
   their items. The seed has exactly one recipe with a `process` and one without (a1-04), so
   `SingleAsync` both finds it and fails loudly if the seed ever changes.

   **1b. Act: two POSTs.** `factory.CreateClient()`, then twice `PostAsJsonAsync` to
   `/api/batches` with a `new CreateBatchRequest(…)`: the recipe id, a name, a brew date (`new
   DateOnly(…)`). Add `using System.Net.Http.Json;` for the method and `using
   HomebrewApp.Features.Batches;` for the record.
   *Why:* `PostAsJsonAsync` writes the object as JSON with the web defaults and sends it with the
   content type `application/json`: the same body the dialog in a1-07 will send. Using the API's
   own `CreateBatchRequest` (the test project references the API project) means a renamed field
   is a build error here, not a test that quietly sends the old name.
   *Watch out:* without the `using`, the build fails with (measured) *error CS1061: 'HttpClient'
   does not contain a definition for 'PostAsJsonAsync' and no accessible extension method
   'PostAsJsonAsync' …*. The tests project's implicit usings include `System.Net.Http`, not its
   `Json` sub-namespace.

   **1c. Assert: status first, then the body.** For each response: `Assert.Equal` on
   `HttpStatusCode.Created` and the `StatusCode`; then `ReadFromJsonAsync<BatchResponse>()` on its
   `Content`, and assert the `Number`s are 1 and 2. The result of `ReadFromJsonAsync` is nullable;
   a `!` where you use it (a1-03's `null!` reason: you just asserted 201).
   *Why:* reading into `BatchResponse` gives typed properties instead of the health tests'
   `JsonDocument`/`GetProperty` walk; the camelCase JSON fits the record because the reader uses
   the same web defaults as the API. **Status before body** is the pattern: when the create
   fails, the test then says what happened.
   *Watch out:* read the body first and a failed create reports the wrong problem. Measured, with
   the `+ 1` removed: this test says *Expected: Created · Actual: InternalServerError*, but
   another test that read the body without checking the status said *System.Text.Json.JsonException
   : The JSON value could not be converted to HomebrewApp.Features.Batches.BatchResponse*, a
   message about JSON for a bug in numbering.

   **See it fail first.** In `BatchEndpoints.cs`, drop the `+ 1` from the number and run
   `dotnet test`: (measured) *Assert.Equal() Failure: Values differ · Expected: Created ·
   Actual: InternalServerError* (the first batch gets 0, the second 0 again, and the `unique`
   constraint refuses it). Put it back.
   *Check yourself:* `dotnet test` passes 8 tests; `git diff app/api/` is empty.
   **Commit:** `git add app/api.Tests/Features/Batches/BatchEndpointsTests.cs`, message
   `Test that batches are numbered from 1`.

2. **Test AC1, first half: the batch's items are the recipe's items.**

   **Read first (10 minutes).**
   [Tuple types, "Tuple equality"](https://learn.microsoft.com/dotnet/csharp/language-reference/builtin-types/value-tuples#tuple-equality).

   A second `[Fact]`, named like `CreateBatch_FromRecipe_CopiesItsItems`.

   **2a. Arrange: what the copy should be.** In a scope: the recipe id as in 1a, then the
   recipe's items (`RecipeItems` where `RecipeId` is that id, ordered by `Id`, `ToListAsync`),
   turned with a `Select` into a list of **tuples** holding the item's `Id`, `IngredientId`,
   `RawName`, `Usage`, `TimeMin`, `Percentage`, `Amount` and `Unit`.
   *Why:* a tuple is a small unnamed group of values, written in parentheses separated by commas;
   two tuples are equal when each value is equal, so two lists of them compare field by field in
   one `Assert.Equal`. The recipe item's `Id` stands where the batch item's `SourceItemId` will be:
   that is the link the copy must keep. The recipe's items go into the tuple **after**
   `ToListAsync`, in C#, so EF Core does not have to translate tuples to SQL.
   *Watch out:* `SourceItemId` is `long?` and a recipe item's `Id` is `long`. Lists of tuples with
   different types are different types; cast the `Id` to `long?` inside the tuple so both sides
   match.

   **2b. Act and assert.** POST as in 1b (assert 201, read the `BatchResponse`). Then, in a
   second scope, read the saved items: `BatchItems` where `BatchId` is the new batch's id, ordered
   by `SourceItemId`, into the same tuple shape with `SourceItemId` first. `Assert.Equal` the two
   lists. Last, delete the batch (`ExecuteDeleteAsync` by its id), as a1-05's tests do.
   *Why:* the response is built from the same objects, so reading the **database** is what
   proves the copy was saved. Ordering both sides makes the comparison independent of insert
   order. Clean-up: this test does not need an empty table, but leaves it as it found it.
   Once a third test needs "the id of the recipe with a process" or "post a valid batch and read
   it", a small private helper at the bottom of the class is fine, like `CreateBatch` in
   `BatchTablesTests`.

   **See it fail first.** In `BatchEndpoints.cs`, copy `Amount = 0` instead of the recipe item's
   amount: (measured) *Assert.Equal() Failure: Collections differ*, with an arrow at position 0
   and the two lists printed: `3.350` expected, `0.000` actual. Put it back.
   *Check yourself:* `dotnet test` passes 9 tests.
   **Commit:** `git add app/api.Tests/Features/Batches/BatchEndpointsTests.cs`, message
   `Test that a batch copies its recipe's items`.

3. **Test AC1, second half: changing the recipe afterwards does not change the batch.**

   **Read first (15 minutes).** [Npgsql basic usage](https://www.npgsql.org/doc/basic-usage.html):
   "Parameters" (positional and named) and "Transactions".

   **3a. An admin connection string in `ApiFactory`.** A second public property next to
   `AppApiConnectionString`, for example `AdminConnectionString`, that returns the container's own
   connection string (`_container.GetConnectionString()`, the `supabase_admin` login the
   container is built with).
   *Why:* `app_api` has only `select` on `app.recipe_item` (a1-03), and the test should not need
   more rights than the API: the API never changes a recipe. The container's admin can, and that
   login exists only in the throwaway container.
   *Check yourself:* `dotnet build` with no warnings; nothing uses it yet.

   **3b. The test.** A `[Fact]`, named like
   `CreateBatch_RecipeItemChangedAfterwards_BatchItemKeepsItsValue`. Arrange: POST a batch (201,
   read the response) and take its first item. Then an `NpgsqlConnection` with the admin string,
   opened, and a transaction on it (`BeginTransactionAsync`). Act: an `NpgsqlCommand` on that
   connection **and** transaction that adds 1 to the `amount` of the recipe item whose id is the
   item's `SourceItemId`, with the id as a **parameter** (`@id` in the SQL,
   `Parameters.AddWithValue` with the value). Assert: a second command, same connection and
   transaction, `select amount from app.batch_item` for the item's own `Id`; `ExecuteScalarAsync`
   returns it, and it equals the item's `Amount` from the response. Finish with the transaction's
   `RollbackAsync`, then delete the batch as in 2b.
   *Why:* a **parameter** sends the value apart from the SQL text, so a value can never change
   what the SQL means; that is the habit for every value you put into SQL, even an id in a test.
   The transaction is a1-05 step 5's trick: inside it, the recipe item really has the new amount
   (any view or trigger linking the batch to the recipe would see it), and the rollback puts the
   seed back, so later tests see the recipe as seeded even if this test fails halfway. Reading
   the batch item on the same transaction is what makes the read see the change.
   Passing the transaction to each command is for the reader: measured, Npgsql runs a command
   in the connection's open transaction even without it, and the test passes either way.

   **See it fail first.** This copy cannot be broken in the API without breaking the first half
   too: the batch item is its own row. Instead, prove the test can tell the difference: point
   the second command at `app.recipe_item` and the `SourceItemId` instead. Measured: *Assert.Equal()
   Failure: Values differ · Expected: 3.350 · Actual: 4.350*, so the update really happened
   inside the transaction. Put the test back.
   *Check yourself:* `dotnet test` passes 10 tests; run it twice in a row (the rollback keeps the
   seed as it was).
   **Commit:** `git add app/api.Tests/ApiFactory.cs app/api.Tests/Features/Batches/BatchEndpointsTests.cs`,
   message `Test that a recipe change leaves the batch alone`.

4. **Test AC3: no process gives 400, an unknown recipe 404, both as problem details.**

   **Read first (5 minutes).** [`ProblemDetails`](https://learn.microsoft.com/dotnet/api/microsoft.aspnetcore.mvc.problemdetails):
   its properties.

   Two `[Fact]`s, named like `CreateBatch_RecipeWithoutProcess_Returns400Problem` and
   `CreateBatch_UnknownRecipe_Returns404Problem`.
   - Without process: look up the seeded recipe whose `Process` is null, POST with it. Assert the
     status is `BadRequest`, the content type is `application/problem+json`
     (`response.Content.Headers.ContentType?.MediaType`), and `ReadFromJsonAsync<ProblemDetails>`
     gives a `Detail` that contains `"process"` (`Assert.Contains` on a string).
   - Unknown: POST with `long.MaxValue` as the recipe id. Assert `NotFound` and the same content
     type.

   `ProblemDetails` lives in `Microsoft.AspNetCore.Mvc`; add that `using`.
   *Why:* the content type is what makes a body problem details (RFC 9457); a1-07 and a2-06
   decide how to show an error by it. `Detail` containing "process" checks your sentence says
   *why*, without copying it word for word into the test. `long.MaxValue` is an id no identity
   column will reach. No clean-up: neither request creates anything.
   *Watch out:* without the `using`, (measured) *error CS0246: The type or namespace name
   'ProblemDetails' could not be found*.

   **See it fail first.** Turn the "no process" `if` into one that is never true (`if (false)`):
   (measured) *Expected: BadRequest · Actual: InternalServerError*: the batch cannot be saved
   without a `process`. Put it back; do the same with the `recipe is null` check: *Expected:
   NotFound · Actual: InternalServerError*. Put it back.
   *Check yourself:* `dotnet test` passes 12 tests.
   **Commit:** `git add app/api.Tests/Features/Batches/BatchEndpointsTests.cs`, message
   `Test the no-process and unknown recipe problems`.

5. **Test AC4: a missing name and brew date give a message per field.**

   **Read first (5 minutes).** [`HttpValidationProblemDetails`](https://learn.microsoft.com/dotnet/api/microsoft.aspnetcore.http.httpvalidationproblemdetails):
   the `Errors` property, a dictionary from field name to its messages.

   A `[Fact]`, named like `CreateBatch_WithoutNameAndBrewDate_Returns400PerField`. POST a
   `CreateBatchRequest` with a recipe id and `null` for the name and the date. Assert
   `BadRequest`, read `HttpValidationProblemDetails` (namespace `Microsoft.AspNetCore.Http`), and
   assert its `Errors` has exactly the keys `Name` and `BrewDate` (for example, the keys sorted,
   compared with a two-element collection), with one message each (`Assert.Single`).
   *Why:* "a message per field" (AC4) is the dictionary: one entry per failing field, so the UI
   can put each message under its input (a1-07's AC3). "Exactly these keys" also shows nothing
   else failed: the recipe id was valid. `null` in the record is the same to the API as a field
   left out of the JSON (measured: a body of only `{"recipeId":1}` gives the same two keys), and
   the record keeps the test readable. The recipe does not even need to exist: validation answers
   before the handler runs.

   **See it fail first.** Remove `[Required]` from `Name` in `CreateBatchRequest`: (measured)
   *Assert.Equal() Failure: Collections differ*, expected `["BrewDate", "Name"]`, actual
   `["BrewDate"]`. Put it back.
   *Check yourself:* `dotnet test` passes 13 tests.
   **Commit:** `git add app/api.Tests/Features/Batches/BatchEndpointsTests.cs`, message
   `Test that missing fields give a message each`.

6. **Test AC5: the new batch is in the list.**

   A `[Fact]`, named like `ListBatches_AfterCreate_ContainsTheBatch`. POST a batch (201, read
   it), then `GetFromJsonAsync<List<BatchSummaryResponse>>` on `/api/batches`, and
   `Assert.Contains` with the list and a lambda that matches the created batch's `Id` and name.
   Delete the batch at the end.
   *Why:* `GetFromJsonAsync` is the GET, the status check and the JSON read in one call (it
   throws on a non-success status). `Assert.Contains` with a condition finds *this* batch among
   whatever else the shared table holds, so the test does not depend on other tests.

   **See it fail first.** Add a `Where` to `ListBatches` that leaves out status `plan`:
   (measured) *Assert.Contains() Failure: Filter not matched in collection · Collection: []*.
   Put it back.
   *Check yourself:* `dotnet test` passes 14 tests; `git diff app/api/` is empty.
   **Commit:** `git add app/api.Tests/Features/Batches/BatchEndpointsTests.cs`, message
   `Test that a created batch is listed`.

## Before you ask for a test review

- [ ] Seven tests, one behaviour each, named `Subject_Condition_Expectation`: AC2, AC1 twice,
      AC3 twice, AC4, AC5.
- [ ] You saw each fail with the message above, and undid each break: `git diff app/api/` is
      empty.
- [ ] Every create asserts 201 before reading the body.
- [ ] Recipe ids are looked up, never written as numbers; the AC2 test empties the table itself;
      every other test deletes the batch it made.
- [ ] The recipe change runs on the admin connection inside a transaction that is rolled back,
      with the id as a parameter.
- [ ] `dotnet build` reports 0 warnings; `dotnet format --verify-no-changes` passes; `dotnet test`
      passes 14 tests, also when run twice.
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted.
