# Review: a1-06 · Create a batch from a recipe

## Round 1 · 2026-11-24 · 567baff + staged step 6

Step 6 (`POST /api/batches`) is staged, not committed; it is reviewed here with the rest of the
branch.

Checks: `dotnet build -warnaserror` ok (0 warnings, 0 errors) · `dotnet format
--verify-no-changes` **3 errors** (`WHITESPACE` at `BatchesEndpoints.cs` lines 53, 55, 59) ·
`dotnet test` 7 passed · no web changes. Endpoints called with `curl` on the API running against
the stack (nothing was written: the create failed before its commit). To get past the first
failure, a copy of the API in the scratchpad, with one finding fixed at a time, ran against a
throwaway Postgres with `db/061`'s tables; your files were not changed.

| AC | Met | How checked |
|---|---|---|
| AC1 | no | `POST` with recipe 1489 → 500 (finding 1). In the copy with findings 1 and 2 fixed: 201, two items with `sourceItemId` 1 and 2 and the recipe's values. |
| AC2 | no | First create → 500, *System.InvalidOperationException: Nullable object must have a value.* (finding 1). In the fixed copy: numbers 1 and 2. |
| AC3 | yes | Recipe 999999 → 404 `application/problem+json`, *There is no recipe with id: 999999*; recipe 163 → 400, *The recipe has no process and so cannot be brewed.* |
| AC4 | yes | `{}` → 400 with one message each for `RecipeId`, `Name`, `BrewDate`. |
| AC5 | no | `GET /api/batches` answers `[]`, but no batch can be created yet. In the fixed copy it listed `Trial 2`, then `Trial 1`. |

Also checked: `GET /api/recipes/brewable` → 53 recipes, 1489 first, no `process`; OpenAPI lists
201, 400 and 404 for the POST.

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec | must fix | `app/api/Features/Batches/BatchesEndpoints.cs:85` | `(int?)b.Number ?? 0 + 1` is read as `(int?)b.Number ?? (0 + 1)`: `+` binds tighter than `??`. The `+ 1` ends up inside the lambda, the lambda's type is `int` again, so the cast does nothing (measured: the first create fails with *Nullable object must have a value.*, exactly lesson 6e's *Watch out*). With batches present it would return the current highest number, not the next one, and the `unique` constraint would refuse the insert (by reading; not run). | The create cannot make the first batch, and could not make any later one. The `MaxAsync` call should give back the highest number (or null); the `?? 0` and the `+ 1` belong outside it, on the awaited result. | [C# operator precedence](https://learn.microsoft.com/dotnet/csharp/language-reference/operators/#operator-precedence) |
| 2 | Spec | must fix | `BatchesEndpoints.cs:106` | `Id = i.Id` gives each new batch item the recipe item's id. `batch_item.id` is `generated always as identity`, so Postgres refuses any id sent to it: measured, with finding 1 fixed, *428C9: cannot insert a non-DEFAULT value into column "id"* and a 500. The recipe item's id already goes where it belongs, in `SourceItemId`. | Even with a free id it would be wrong: the batch item would claim the recipe item's identity. A new row's id always comes from the database (lesson 6f, "Do not set … `Id` anywhere"). | [PostgreSQL 15 — `GENERATED ALWAYS AS IDENTITY`](https://www.postgresql.org/docs/15/sql-createtable.html) |
| 3 | Standards | must fix | `BatchesEndpoints.cs:53, 55, 59` | The three blank lines in `MapBatchesEndpoints` contain spaces. `dotnet format --verify-no-changes` reports `WHITESPACE` for each. | The pre-commit hook runs that check first, so step 6 cannot be committed as it is. `dotnet format` (without `--verify-no-changes`) in `app/` fixes them. | [`dotnet format`](https://learn.microsoft.com/dotnet/core/tools/dotnet-format) |
| 4 | Standards | should fix | `BatchesEndpoints.cs:91` | `BrewDate = batchRequest.BrewDate ?? new DateOnly()` falls back to `0001-01-01` when the date is null. Validation makes that impossible today, so the fallback never runs, but if it ever does (validation switched off for this endpoint, the handler called from a test), the batch is silently brewed in year 1: the very bug the nullable request record exists to prevent. | Prefer failing loudly over a made-up default. The `!` you used for `Name` on line 90 says "validation guarantees this"; written the same way for the date, a broken guarantee throws instead of saving a wrong date. | [Null-forgiving operator](https://learn.microsoft.com/dotnet/csharp/language-reference/operators/null-forgiving) |
| 5 | Standards | should fix | `BatchesEndpoints.cs:56, 63` and `:21` | Two names say something else than the code does. **`GetBatch`** is the handler of a `POST` that *creates* a batch; a1-09 adds a real "get one batch" (`GET /api/batches/{id}`), and then two methods would claim the same job. Name a handler for its action: `CreateBatch`, as `ListBatches` already is. **`Request`** is too general for a type: it becomes the OpenAPI schema `Request` (measured), and in a2-02 a TypeScript type `Request` would clash with the browser's built-in `Request` (the one `fetch` uses). Name a request for the action it asks for: `CreateBatchRequest`. | A name is read far more often than written; the next reader (you in a1-09, or the generated types in a2-02) trusts it. | [.NET naming guidelines](https://learn.microsoft.com/dotnet/standard/design-guidelines/naming-guidelines) |
| 6 | Standards | nice to have | `BatchesEndpoints.cs` | The other names, for consistency: `BatchesEndpoints` / `MapBatchesEndpoints` (and the file name) beside `RecipeEndpoints` / `MapRecipeEndpoints`: one form, the singular as the lesson had it (`BatchEndpoints`). `BatchListResponse` is one row, not the list: `BatchSummaryResponse` (or `BatchListItemResponse`). `ItemResponse` is a batch's item, and M7 brings inventory items: `BatchItemResponse`. Locals: `batchRequest` → `request`, `responseBatch` → `response`, `number` → `nextNumber`. | Consistent names let you guess a name before you look it up. | — |
| 7 | Standards | nice to have | `BatchesEndpoints.cs:12-48` | The four records are nested inside the static class here, but sit at namespace level in `RecipeEndpoints.cs` and `HealthEndpoints.cs`. OpenAPI names them the same either way (measured), so it is only about consistency: from a test they would have to be written `BatchesEndpoints.BatchResponse`. | One place for response records across features. | — |
| 8 | Standards | nice to have | `app/api/HomebrewApp.http` | Still only the health request; lesson steps 3, 4 and 7 add the new ones. | Rider runs them with one click; quicker than retyping `curl` for every check in the test lesson and later tickets. | — |

Done well:
- The transaction with `await using` and plain early `return`s: no `try`/`catch`, and a 404 or 400
  leaves nothing behind (the failed creates above wrote nothing to the stack).
- Both lists project with `Select` straight into the response record: one SQL query each, no
  `Include`, no `process` sent to the dropdown. `ThenByDescending` makes the batch order stable.
- `ProducesValidationProblem` and `ProducesProblem(404)`: the OpenAPI document already describes
  every answer the POST can give.

Verdict: fixes needed (findings 1, 2, 3; 4 and 5 before the tests build on these names).

## Round 2 · 2026-11-24 · 60aac31

Checks: `dotnet build -warnaserror` ok (0 warnings, 0 errors) · `dotnet format
--verify-no-changes` ok · `dotnet test` 7 passed · no web changes. The creates ran on your built
API pointed at a throwaway Postgres with `db/061`'s tables (environment variable
`ConnectionStrings__App`); the reads and the "no process" 400 ran on the stack, which still has
no batches.

Round 1:

| # | Status |
|---|---|
| 1 | fixed: the cast stays inside `MaxAsync`, `?? 0` and `+ 1` are on the result. |
| 2 | fixed: no `Id` on the new items; they get their own ids (1 and 2 below). |
| 3 | fixed: `dotnet format --verify-no-changes` passes. |
| 4 | fixed: `request.BrewDate!.Value`. |
| 5 | fixed: `CreateBatch` and `CreateBatchRequest` (OpenAPI schema `CreateBatchRequest`). |
| 6 | partly: `BatchSummaryResponse`, `BatchItemResponse`, `MapBatchEndpoints`, `request`, `response` done; the class and file are still `BatchesEndpoints` (new finding 1). |
| 7 | fixed: the records sit at namespace level, as in the other features. |
| 8 | open (new finding 2). |

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | Create from recipe 1 → 201, two items with `sourceItemId` 1 and 2 and the recipe's values. Then `update app.recipe_item set amount = 9.999 where id = 1`: the recipe item reads `9.999`, both batches' copies still `3.350`. |
| AC2 | yes | Two creates on an empty table → `"number":1`, then `"number":2`. |
| AC3 | yes | Recipe 999 → 404 *There is no recipe with id: 999*; a recipe without `process` → 400 *The recipe has no process and so cannot be brewed.* (also on the stack with recipe 163). |
| AC4 | yes | `{}` → 400 with a message each for `RecipeId`, `Name`, `BrewDate`; `"name":" "` and no date → messages for `Name` and `BrewDate`. |
| AC5 | yes | `GET /api/batches` → `Trial 2` (2026-12-12), then `Trial 1`. |

Also: `Location: /api/batches/1` on the 201; `GET /api/recipes/brewable` on the stack → 53
recipes, 1489 first, no `process`; OpenAPI lists 201, 400 and 404 for the POST and a schema per
record; no exception in the API's log.

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | nice to have | `app/api/Features/Batches/BatchesEndpoints.cs:48, 85` | The class and file are still `BatchesEndpoints` while the method is now `MapBatchEndpoints` and the other features use `RecipeEndpoints` and `HealthEndpoints`. And `nextNumber` holds the *highest* number so far (or null); the next one is computed on line 89. `highestNumber` says what it holds. | Names that match what they hold, and one form across features. | — |
| 2 | Standards | nice to have | `app/api/HomebrewApp.http` | Still only the health request (lesson steps 3, 4, 7). | The test lesson's checks are quicker with the requests saved. | — |

Done well:
- Every round 1 finding acted on, and each fix is the small one: one line moved, one line
  removed, nothing rewritten around it.
- `(nextNumber ?? 0) + 1` with the parentheses: the order of operations is written out, so nobody
  has to remember that `+` binds tighter than `??`.
- The response is built from the saved `batch`, so its ids are the database's.

Verdict: ready for tests.
