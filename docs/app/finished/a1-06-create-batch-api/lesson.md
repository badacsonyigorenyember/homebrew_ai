# Lesson: a1-06 · Create a batch from a recipe

## What you will build

The API's first endpoints that write. `GET /api/recipes/brewable` lists the recipes a batch can be
made from; `POST /api/batches` makes a batch from one of them, as a copy (its numbers, its
`process` and one `batch_item` per recipe item); `GET /api/batches` lists the batches. a1-07 builds
the batches page and the new-batch dialog on these three, and a1-08 adds the brew-day steps to the
create.

It is done when:

- **AC1** A new batch's items match the recipe's items; changing the recipe's item afterwards (in
  the test database) does not change the batch's.
- **AC2** Two batches get numbers 1 and 2.
- **AC3** A recipe without a `process` gives 400 problem details saying so; an unknown recipe gives
  404.
- **AC4** A missing name or brew date gives 400 with a message per field.
- **AC5** `GET /api/batches` lists the new batch.

The ACs are proven by integration tests, written after the review from `test-lesson.md`. In this
lesson you check them by hand with `curl` against your stack.

**How the pieces fit.** Two feature folders, each with one endpoints class, as `Features/Health/`:

```
Program.cs ── AddProblemDetails, AddValidation (step 2)
   ├─ MapRecipeEndpoints ── GET  /api/recipes/brewable ──► app.recipe + ref.beer_style  (read)
   └─ MapBatchEndpoints  ── GET  /api/batches          ──► app.batch + recipe + style   (read)
                          └ POST /api/batches          ──► validation filter (400 per field)
                                                          ► one transaction:
                                                             read the recipe and its items
                                                             next number = highest + 1
                                                             insert app.batch + app.batch_item
                                                          ◄ 201 Created, Location, the batch
```

The reads turn a LINQ query into one SQL query and return small response records. The create
reads the recipe with its items, copies every value it needs into a new `Batch` with new
`BatchItem`s, and saves them in one go. No number is computed anywhere (C4): every value is copied.

What the tools look like today (measured 2026-11-23 on your stack, and in a scratch API with SDK
10.0.115, `Npgsql.EntityFrameworkCore.PostgreSQL` 10.0.3 and `Microsoft.AspNetCore.OpenApi`
10.0.14 against a throwaway Postgres; every error and response quoted below comes from those runs):

| Thing | Value | Note |
|---|---|---|
| Recipes with a `process` on your stack | 53, newest first is 1489 (10A Weissbier, 4 items) | what `brewable` returns |
| A recipe without a `process` | 163 | for the 400 check |
| Batches on your stack | 0 | step 7 makes two and deletes them again |
| Built-in validation in .NET 10 | `AddValidation()` + `[Required]`; no package, no project setting | step 2 |

## Steps

1. **Check where you are.** From the repo root, run `git branch --show-current` and `git status`.
   *Why:* the work belongs on the ticket's branch, and a clean start keeps the review diff to this
   ticket.
   *Check yourself:* the branch is `a1-06-create-batch-api`; `git status` is clean.
   No commit.

2. **Register problem details and validation** in `app/api/Program.cs`.

   **Read first (about 20 minutes).**
   - [Handle errors in ASP.NET Core APIs, "Problem details"](https://learn.microsoft.com/aspnet/core/fundamentals/error-handling-api?view=aspnetcore-10.0#problem-details):
     the *Minimal APIs* tab, the first paragraph and the list of middleware that writes problem
     details.
   - [Minimal APIs quick reference, "Validation support in Minimal APIs"](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis?view=aspnetcore-10.0#validation-support-in-minimal-apis):
     up to "Disable validation for specific endpoints".
   - [RFC 9457, section 3](https://www.rfc-editor.org/rfc/rfc9457#section-3): the five members
     `type`, `status`, `title`, `detail`, `instance`. Skim.

   Two calls with the other `builder.Services` lines: `AddProblemDetails()` and
   `AddValidation()`. Neither takes an argument.

   *Why:* SYSTEM.md §9 says every API error is RFC 9457 **problem details**: a JSON body with a
   fixed shape (`type`, `title`, `status`, `detail`), sent with the content type
   `application/problem+json`, so the UI can show any error the same way (a2-06).
   `AddProblemDetails` registers the service that writes that shape for the framework's own
   errors. **Validation** is .NET 10's built-in check of a request before your handler runs: you
   put attributes such as `[Required]` on the request record (step 5), and a filter in front of
   the endpoint answers 400 with one message per field when a rule fails, so the handler never
   sees a bad request (AC4). `AddValidation` turns that filter on; a source generator finds the
   request types at build time, which is why nothing else needs registering.
   Both go in now, before any endpoint uses them, because they change how *every* error looks.
   Measured, a request missing its fields: with only `AddValidation`, the 400 is
   `application/json` with just `title` and `errors`; with `AddProblemDetails` as well, it is
   `application/problem+json` with `type`, `title`, `status`, `errors` and a `traceId`.
   *Check yourself:* `dotnet build` in `app/` with no warnings; `dotnet test` green;
   `/api/health` answers as before. Nothing else changes yet.
   **Commit:** `git add app/api/Program.cs`, message `Register problem details and validation`.

3. **`GET /api/recipes/brewable`**, in a new folder `app/api/Features/Recipes/`.

   **Read first (about 30 minutes).**
   - [LINQ overview](https://learn.microsoft.com/dotnet/csharp/linq/): the introduction, and
     [Projection operations](https://learn.microsoft.com/dotnet/csharp/linq/standard-query-operators/projection-operations)
     up to "SelectMany" (`Select` only).
   - [How queries work (EF Core)](https://learn.microsoft.com/ef/core/querying/how-query-works):
     the whole page is short; the point is "LINQ becomes SQL, run at `ToListAsync`".
   - [Efficient querying, "Project only properties you need"](https://learn.microsoft.com/ef/core/performance/efficient-querying#project-only-properties-you-need).
   - [Route groups](https://learn.microsoft.com/aspnet/core/fundamentals/routing?view=aspnetcore-10.0#route-groups):
     the first example.

   Why `Features/Recipes/` when the Recipes feature is M4: the URL says recipes, and M4's list
   and detail endpoints go next to this one. A feature folder holds what belongs to one feature
   (a0-02's vertical slices); the entities stay in `Data/` (a1-03 step 7).

   **3a. The response record.** In a new file `RecipeEndpoints.cs`, namespace
   `HomebrewApp.Features.Recipes`, a record at the top, as `HealthResponse` sits at the top of
   `HealthEndpoints.cs`. Name it for what it is (for example `BrewableRecipeResponse`), with
   these properties in this order: `Id` (`long`), `StyleCode` (`string`), `StyleName`
   (`string?`), `OG`, `FG`, `ABV`, `IBU` (`decimal?` each), `BatchL` (`decimal`), `CreatedAt`
   (`DateTime`).
   *Why:* a record per response (a0-02), not the `Recipe` entity: the entity carries `process`
   (a long JSON string the dropdown does not need) and navigations, and returning it would tie the
   API's JSON to the table. The types copy the entity's, nullability included: a recipe may have
   no `og` yet, and a style may have no name. JSON names come out camelCase (a0-02): measured,
   `OG` is written `og`, `BatchL` `batchL`, `StyleCode` `styleCode`.

   **3b. The handler.** A static class `RecipeEndpoints` and in it a `private static async`
   handler that takes an `AppDbContext` and a `CancellationToken` and returns
   `Task<Ok<List<…>>>` with your record. Its body is one query on `Recipes`, in this order:
   - `Where`: the recipe's `Process` is not null;
   - `OrderByDescending` on `CreatedAt` (newest first);
   - `Select`: a lambda that turns each recipe into your record, taking `StyleCode` and
     `StyleName` through the `Style` navigation;
   - `ToListAsync`, with the token;

   then `TypedResults.Ok` with the list.
   *Why:* **LINQ** (Language Integrated Query) is C#'s set of methods for asking questions of a
   sequence: `Where` keeps the items a condition holds for, `OrderByDescending` sorts, `Select`
   turns each item into something else (a **projection**). On a `DbSet` none of these run in C#:
   EF Core collects the whole chain and, at `ToListAsync`, translates it into **one** SQL query
   with a `where`, a join to `ref.beer_style`, an `order by` and only the columns your record
   names. That is also why no `Include` is needed: a navigation used inside `Select` becomes a
   join by itself; `Include` is for loading whole entities (step 6). `Process != null` becomes
   `process is not null` in SQL.
   *Watch out:* a call EF Core cannot turn into SQL (one of your own C# methods inside `Where`)
   builds fine and fails only when the request runs, with an exception saying the LINQ expression
   could not be translated. Keep the lambdas to properties, comparisons and `new` of the record.

   **3c. Map it.** A `public static` extension method `MapRecipeEndpoints` on
   `IEndpointRouteBuilder` (the shape of `MapHealthEndpoint`), which makes a route group for
   `/api/recipes` with `MapGroup` and maps `GET /brewable` on the group to your handler. Then one
   line in `Program.cs` next to `MapHealthEndpoint`.
   *Why:* a0-02 met route groups as optional; from now on each feature has several endpoints
   under one prefix, so the group says the prefix once, and a2-01 hangs the API key check on it.
   Measured: a group endpoint mapped as `"/"` answers both with and without the trailing slash,
   and OpenAPI lists it without one.
   *Check yourself:* `dotnet build` with no warnings; run the API (`dotnet run --project api` from
   `app/`); `curl -s http://localhost:5080/api/recipes/brewable` returns a list of 53 entries
   whose first has `"id":1489` and `"styleCode":"10A"`; no entry has a `process`. Add the same
   request to `app/api/HomebrewApp.http`, under the health one, separated by `###`.
   **Commit:** `git add app/api/Features/Recipes/ app/api/Program.cs app/api/HomebrewApp.http`,
   message `Add GET /api/recipes/brewable`.

4. **`GET /api/batches`**, in a new file `app/api/Features/Batches/BatchEndpoints.cs`, namespace
   `HomebrewApp.Features.Batches`, next to the entity classes from a1-05.

   **4a. The response record**, one row of the list: `Id` (`long`), `Number` (`int`), `Name`,
   `StyleCode` (`string`), `StyleName` (`string?`), `BrewDate` (`DateOnly`), `Status` (`string`).
   *Why:* the ticket's columns plus `Id`, which a1-07 needs to open `/batches/:id`. Code and name,
   as in step 3, so the page can show either. A `DateOnly` is written as `"2026-12-05"`
   (measured), a calendar date with no time zone (SYSTEM.md §9).

   **4b. The handler**, as in 3b: a query on `Batches` with `OrderByDescending` on `BrewDate`,
   then `ThenByDescending` on `Number`, a `Select` into the record (the style through
   `Recipe.Style`, two navigations deep), `ToListAsync`, `TypedResults.Ok`.
   *Why:* latest brew date first (the ticket). `ThenByDescending` breaks a tie between two
   batches brewed the same day, so the order never changes between two calls; without it, Postgres
   may return equal rows in any order.

   **4c. Map it.** `MapBatchEndpoints`, as 3c: a group for `/api/batches` and `GET /` on it; one
   line in `Program.cs`.
   *Check yourself:* build with no warnings; `curl -s http://localhost:5080/api/batches` returns
   `[]` (no batches yet). Add the request to the `.http` file.
   **Commit:** `git add app/api/Features/Batches/BatchEndpoints.cs app/api/Program.cs app/api/HomebrewApp.http`,
   message `Add GET /api/batches`.

5. **The create's request and response records**, at the top of `BatchEndpoints.cs`. Nothing
   uses them yet, so the build stays green.

   **Read first (about 15 minutes).**
   - [Validation in ASP.NET Core](https://learn.microsoft.com/aspnet/core/fundamentals/validation?view=aspnetcore-10.0):
     "How validation runs", the "Minimal API parameter validation" and "Model validation order"
     lists.
   - [`RequiredAttribute`](https://learn.microsoft.com/dotnet/api/system.componentmodel.dataannotations.requiredattribute):
     the Remarks (what counts as missing for a string).
   - [Nullable value types](https://learn.microsoft.com/dotnet/csharp/language-reference/builtin-types/nullable-value-types):
     the first two sections.

   **5a. The request record**, the JSON body of the POST: `RecipeId`, `Name` and `BrewDate`. Each
   gets the attribute `[Required]` (namespace `System.ComponentModel.DataAnnotations`) in front of
   it, inside the record's parentheses, and each is **nullable**: `long?`, `string?`,
   `DateOnly?`.
   *Why:* `[Required]` fails for a property that is `null`, and for a string that is empty or only
   spaces (measured: `""` and `"  "` both give *The Name field is required.*). A value type such
   as `DateOnly` is never null: when the JSON leaves it out, it is simply `0001-01-01`. So the
   `?` is what lets "not sent" be seen at all: `DateOnly?` is a **nullable value type**, a
   `DateOnly` that can also be `null`.
   *Watch out:* written as `[Required] DateOnly BrewDate`, without the `?`, a body with no brew
   date passes validation and the batch gets brewed in year 1 (measured: `{}` gave an error for
   `Name` only, and the date read as `"0001-01-01"`). With no attributes at all, `{}` is accepted
   with 200.

   **5b. The response records.** One for the batch: `Id`, `Number`, `Name`, `RecipeId`,
   `BrewDate`, `Status`, `BatchL`, `EfficiencyPct`, `OG`, `FG`, `ABV`, `IBU`, `SRM` and `Items`,
   a list of a second record. That one, for an item: `Id`, `SourceItemId`, `IngredientId`,
   `RawName`, `Usage`, `TimeMin`, `Percentage`, `Amount`, `Unit`. Types as in the entities.
   *Why:* the ticket's "201 with the batch": the caller gets what was saved, ids included, without
   a second request. `Process` stays out: it is a JSON string in C# (a1-05), and returned as a
   string property it would reach the UI as one long escaped text; a1-08 turns it into steps,
   which are what the UI shows. `LockedAt`, `CreatedAt`, `Changed` stay out until a ticket needs
   them.
   *Check yourself:* `dotnet build` with no warnings.
   **Commit:** `git add app/api/Features/Batches/BatchEndpoints.cs`, message
   `Add the create batch request and response records`.

6. **`POST /api/batches`**: the handler, in `BatchEndpoints.cs`, then its mapping. Step 6 is one
   commit; the build may complain between sub-steps until 6g maps the handler and the body is
   complete.

   **Read first (about 35 minutes).**
   - [Create responses, "TypedResults versus Results" and "Results<TResult1, TResultN>"](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/responses?view=aspnetcore-10.0#resultstresult1-tresultn):
     how one handler declares several possible results.
   - [Eager loading of related data](https://learn.microsoft.com/ef/core/querying/related-data/eager):
     the first example (`Include`).
   - [Using transactions](https://learn.microsoft.com/ef/core/saving/transactions): "Default
     transaction behavior" and "Controlling transactions".
   - [Saving related data, "Adding a graph of new entities"](https://learn.microsoft.com/ef/core/saving/related-data#adding-a-graph-of-new-entities).
   - [Handle errors in ASP.NET Core APIs, "Returning multiple result types with TypedResults"](https://learn.microsoft.com/aspnet/core/fundamentals/error-handling-api?view=aspnetcore-10.0#returning-multiple-result-types-with-typedresults):
     why some results need `ProducesProblem`.

   **6a. The signature.** A `private static async` handler that takes your request record, an
   `AppDbContext` and a `CancellationToken`, and returns
   `Task<Results<Created<…>, ProblemHttpResult>>` with your batch response record.
   *Why:* a0-02 said a handler that can answer in more than one way returns `Results<…>` with each
   possible result type inside. Here: `Created<T>` (201 with a body) or `ProblemHttpResult` (an
   error as problem details, used for both 404 and 400). ASP.NET Core sees that the request
   record is not a service and not a route value, so it reads it from the JSON body; the
   validation filter from step 2 checks it before your body runs.

   **6b. Start a transaction.** First line of the body: `await using var` a variable, `=`, `await`
   the context's `Database.BeginTransactionAsync`, with the token.
   *Why:* a **transaction** (a1-05 step 5, in psql) makes several statements one unit: all or
   nothing. The ticket asks for one around the whole create: read the highest number, insert the
   batch, insert its items. `SaveChangesAsync` alone already wraps its own inserts in a
   transaction (the EF docs' "Default transaction behavior"); the explicit one makes the read of
   the number part of the same unit, and keeps a1-08's steps inside it too. `await using` (met in
   the a1-05 tests for scopes) disposes the transaction when the handler ends, and disposing one
   that was never committed **rolls it back**: any early `return` or exception leaves the
   database as it was, with no `try`/`catch`.
   What it does not do: two requests at the same moment can still both read 4 as the highest.
   Then the `unique` constraint on `number` (a1-05) refuses the second insert, and that request
   fails with a 500 instead of creating a duplicate. With one user (C1) that is the right amount
   of protection; a lock or a stricter isolation level would be machinery for a case that does
   not happen here.

   **6c. Load the recipe, or 404.** Query `Recipes` with `Include` of its `Items`, then
   `SingleOrDefaultAsync` with a lambda matching the request's recipe id, and the token. When the
   result is `null`, return `TypedResults.Problem` with a `detail` naming the recipe id and
   `statusCode` set to `StatusCodes.Status404NotFound`.
   *Why:* **`Include`** loads the items together with the recipe, as whole entities, because 6f
   copies every field of them. `SingleOrDefaultAsync` returns the one match or `null`; it would
   throw if two rows matched, which cannot happen with an id. `TypedResults.Problem` writes RFC
   9457 itself, so the 404 has a body saying *which* recipe (AC3). Measured: `{"type":
   "https://tools.ietf.org/html/rfc9110#section-15.5.5","title":"Not Found","status":404,
   "detail":"Recipe 999 does not exist."}` with content type `application/problem+json`.

   **6d. No `process`, 400.** When the loaded recipe's `Process` is `null`, return
   `TypedResults.Problem` with a `detail` that says the recipe has no process and so cannot be
   brewed, and status 400.
   *Why:* `app.batch.process` is `not null` (a1-05): without this check the insert would fail
   with a database error and a 500. A 400 with a sentence tells the caller what is wrong (AC3),
   and a1-07 shows it. After this `if`, the compiler knows `Process` is not null, so 6f can copy
   it into the `required string` without a warning.

   **6e. The next number.** `MaxAsync` on `Batches` with a lambda that selects `Number` **cast to
   `int?`** (the type in parentheses before the value), then `??` 0 (a1-03 step 9a), then plus 1.
   *Why:* `max(number)` in SQL is `null` when the table is empty, and an `int` cannot hold `null`.
   The cast makes the query's result an `int?`, so "no batches" comes back as `null`, and `??`
   turns it into 0, so the first batch is 1 (AC2).
   *Watch out:* without the cast, the first create fails with a 500 and (measured)
   *System.InvalidOperationException: Nullable object must have a value.* in the API's log. It
   works again once one batch exists, so it is easy to miss; the test lesson comes back to it for
   AC2.

   **6f. Build the batch.** A `new Batch { … }` with: the number from 6e; `Name` and `BrewDate`
   from the request; `RecipeId` from the recipe; `Status` `"plan"`; `BatchL`, `EfficiencyPct`,
   `Process`, `OG`, `FG`, `ABV`, `IBU`, `SRM` copied from the recipe; and `Items` set to the
   recipe's items turned into new `BatchItem`s with `Select` (a lambda that does `new BatchItem {
   … }` with every copied field, `SourceItemId` from the recipe item's `Id`, `Changed` `false`)
   followed by `ToList()`.
   *Why:* this is F4.1's copy: every value is taken from the recipe as it is, none is computed
   (C4), so the batch keeps its numbers whatever later happens to the recipe (AC1).
   `SourceItemId` is the only link back, for M3's "changed" marks. The `Select` here runs in C#,
   not in SQL: `recipe.Items` is a list already in memory, so this is plain LINQ, and `ToList()`
   (not `ToListAsync`) turns the result into the `List<BatchItem>` the property wants.
   Do not set `BatchId` on the items or `Id` anywhere: EF Core fills them when it saves (a1-05
   step 7c).
   *Watch out:* `Name` and `BrewDate` are nullable in the request, so the build fails under
   `-warnaserror` with (measured) *warning CS8601: Possible null reference assignment.* for the
   name and *warning CS8629: Nullable value type may be null.* for `.Value` of the date. The
   validation filter has already made sure both are there, but the compiler cannot know that; the
   null-forgiving `!` after each (a1-03's `null!`) tells it so. Use it only on these two, where
   validation guarantees the value.

   **6g. Save, commit, answer.** `Add` the batch to `Batches`, `await` `SaveChangesAsync` with the
   token, then `await` the transaction's `CommitAsync` with the token. Build your response record
   from the saved batch (its items with a `Select`, as in 6f) and return `TypedResults.Created`
   with the location `/api/batches/` followed by the batch's id, and the response.
   *Why:* `Add` on the batch adds the whole graph: EF Core inserts the batch, reads its new id,
   then inserts each item with that `BatchId` (the EF page "Adding a graph"). `Add` tracks what
   it adds even though the context is no-tracking by default (a1-03 step 9b), which only applies
   to queries. After `SaveChangesAsync` the batch's and the items' `Id`s are filled in, so the
   response has real ids. Nothing is permanent until `CommitAsync`. **201 Created** is the HTTP
   answer for "a new thing exists now", and its `Location` header says where it lives. Nothing
   answers at that address yet: `GET /api/batches/{id}` comes with a1-09, and a1-07 uses the id
   from the body.

   **6h. Map it**, in `MapBatchEndpoints`: `MapPost("/", …)` on the group, followed by
   `.ProducesValidationProblem()` and `.ProducesProblem(StatusCodes.Status404NotFound)`.
   *Why:* `Created<T>` describes itself to OpenAPI; `ProblemHttpResult` and the validation filter
   do not. Measured: without the two calls, `/openapi/v1.json` lists only `201` for this
   endpoint; with them, `400` (`HttpValidationProblemDetails`) and `404` (`ProblemDetails`) too.
   a2-02 generates the UI's types from that document, so a missing response here is a missing
   type there. The 400 for "no process" is a plain problem, also covered by the 400 entry.

   *Check yourself (whole step):* build with no warnings, `dotnet test` green. Then step 7.
   **Commit:** `git add app/api/Features/Batches/BatchEndpoints.cs`, message
   `Add POST /api/batches`.

7. **Check every AC by hand, then delete the trial batches.** Run the API. Each request below with
   `curl -s -i -H 'Content-Type: application/json' -d '<body>' http://localhost:5080/api/batches`,
   and the same requests in the `.http` file:

   - `{}`: 400, `application/problem+json`, `errors` with one message each for `RecipeId`, `Name`
     and `BrewDate` (AC4). The keys are the C# names, `Name` and `BrewDate` (measured); a1-07
     matches them to its fields.
   - `{"recipeId": 999999, "name": "Trial", "brewDate": "2026-12-05"}`: 404 with your detail.
   - recipe 163 (no process), same name and date: 400 with your detail (AC3).
   - recipe 1489, name `Trial 1`, brew date `2026-12-05`: 201, a `Location: /api/batches/<id>`
     header, `"number":1`, `"status":"plan"`, `"og":1.0481` and four items, each with a
     `sourceItemId`.
   - recipe 1489 again, name `Trial 2`, brew date `2026-12-12`: `"number":2` (AC2).
   - `GET /api/batches`: `Trial 2` first, then `Trial 1` (AC5).
   - In psql as `postgres` (`docker exec -it supabase-db psql -U postgres -d postgres`):
     `select raw_name, usage, time_min, pct, amount, unit from app.recipe_item where recipe_id =
     1489 order by id;` and the same columns from `app.batch_item` for the first trial batch's id:
     the same four rows (the first half of AC1). The second half, changing the recipe item
     afterwards, is for the test database only; never change a real recipe for it.

   Then, still in psql: `delete from app.batch where name like 'Trial%';` (the items go with them,
   a1-05's cascade), and `select count(*) from app.batch;` is `0`.
   *Why:* the tests come after the review; trying it now shows the whole create working against
   the real data. The delete matters: the next number is the highest plus one, so with the trial
   batches gone your first real batch is number 1.
   *Watch out:* a brew date in any other form than `yyyy-mm-dd` (for example `05/12/2026`) is not
   a validation error but a JSON reading error: a 400 whose `title` is
   *Microsoft.AspNetCore.Http.BadHttpRequestException* and no `errors` per field (measured, in
   Development). The UI always sends the ISO form, so this is fine; just don't read it as a bug in
   your validation.
   **Commit** (only if you added requests to the `.http` file in this step):
   `git add app/api/HomebrewApp.http`, message `Add batch requests to the .http file`.

## Files you will touch

- `app/api/Program.cs`: `AddProblemDetails`, `AddValidation`, and the two new `Map…` calls.
- `app/api/Features/Recipes/RecipeEndpoints.cs`: new; `GET /api/recipes/brewable` and its record.
- `app/api/Features/Batches/BatchEndpoints.cs`: new; `GET` and `POST /api/batches`, the request
  and response records.
- `app/api/HomebrewApp.http`: the new requests.

## Before you ask for a review

- [ ] Step 7's requests gave the answers listed there: 400 per field (AC4), 404 and the "no
      process" 400 (AC3), numbers 1 and 2 (AC2), the list (AC5), and the same items as the recipe
      (AC1).
- [ ] The trial batches are deleted; `select count(*) from app.batch;` on the stack is `0`.
- [ ] No number is computed anywhere in the create: every batch value comes from the recipe or the
      request (C4).
- [ ] `/openapi/v1.json` shows `201`, `400` and `404` for `POST /api/batches`, and a schema for
      each new record.
- [ ] `dotnet build` in `app/` reports 0 warnings and 0 errors; `dotnet format --verify-no-changes`
      and `dotnet test` pass.
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted.
