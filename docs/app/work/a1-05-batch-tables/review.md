# Review: a1-05 · Batch tables

## Round 1 · 2026-11-19 · 503202c + staged `AppDbContext.cs`

`db/061_app_batch.sql` was written by Claude at your request in this session; it is reviewed here
like the rest. The entity classes came from the Rider generator script (outside the repo).

Checks: `dotnet build` ok (0 warnings, 0 errors) · `dotnet format --verify-no-changes` ok ·
`dotnet test` 4 passed · `[Column]` names against the catalog: 40 of 40 match · no web changes.
`app/api/Data/AppDbContext.cs` (step 8) was staged during the review and committed as 319918c.

AC2's catalog query, run on the stack:

```sql
select table_name, column_name, data_type, numeric_precision, numeric_scale, is_nullable,
       column_default, is_identity
from information_schema.columns
where table_schema = 'app' and table_name like 'batch%'
order by table_name, ordinal_position;

select conrelid::regclass, conname, pg_get_constraintdef(oid)
from pg_constraint
where connamespace = 'app'::regnamespace and conrelid::regclass::text like 'app.batch%'
order by 1, 2;

select table_name, string_agg(privilege_type, ',' order by privilege_type)
from information_schema.role_table_grants
where grantee = 'app_api' and table_schema = 'app' and table_name like 'batch%'
group by 1;

select relname, relacl from pg_class
where relkind = 'S' and relnamespace = 'app'::regnamespace and relname like 'batch%';
```

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | You applied the file twice on the stack: the second run printed only the five *already exists, skipping* notices, no `ERROR`. |
| AC2 | yes | The query above: 16 + 11 + 13 columns with the lesson's types, nullability and defaults; `batch_status_check` and `batch_step_phase_check` list the seven phases; `batch_number_key` unique; `batch_recipe_id_fkey`; both `batch_id` foreign keys `ON DELETE CASCADE`, `source_item_id` `ON DELETE SET NULL`; the two `batch_id` indexes; `app_api` has `DELETE,INSERT,SELECT,UPDATE` on each table and nothing on the three sequences. |
| AC3 | yes (by hand) | Throwaway container from the stack's image with `010`, `015`, `060`, `061` and the seed; a scratch program using **your** `AppDbContext` as `app_api` inserted a batch, then an item and a step, and read them back: `created` came back as the database's `now()` in UTC. The test lesson turns this into a test. |
| AC4 | yes (by hand) | Same container, as `app_api`: deleting the batch left 0 items and 0 steps; status `brewing` was refused by `batch_status_check`. |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | should fix | `app/api/Features/Batches/Batch.cs`, `BatchItem.cs` | The navigations from lesson steps 7c–7d are missing: `Batch.Recipe`, `Batch.Items`, `Batch.Steps`, and `BatchItem.Ingredient`. Measured: EF Core's model has **0** foreign keys for `BatchItem`, so to EF `BatchId` is just a number. | Without them a1-06 cannot add a batch with its items and steps in one `Add` and one `SaveChanges` (one transaction, the ticket's "in one transaction"), and a1-09 cannot `Include` a batch's steps. And because `BatchId` is not `required` (the generator assumes the navigations exist), an item with a forgotten `BatchId` compiles and fails only in the database (measured: *23503: … violates foreign key constraint "batch_item_batch_id_fkey"*). With `Batch.Items`, EF Core fills `BatchId` itself. | [One-to-many relationships](https://learn.microsoft.com/ef/core/modeling/relationships/one-to-many) (the first example); [Saving related data, "Adding a graph of new entities"](https://learn.microsoft.com/ef/core/saving/related-data#adding-a-graph-of-new-entities) |
| 2 | Standards | nice to have | `app/api.Tests/ApiFactory.cs:45` | The comment says what the file contains, not why the tests need it; the three comments above it give the reason (a1-04's AC4: "a comment on why each is needed"). | The next reader asks "why here, after 060?": because the file grants to `app_api`, and the batch tests write to these tables. | a1-04 lesson step 3 |
| 3 | Standards | nice to have | `app/api/Features/Batches/BatchItem.cs:30` | `Pct` here, `Percentage` on `RecipeItem` for the same copied column. | a1-06 copies one into the other; the same name on both sides makes the copy read as a copy (`Percentage = item.Percentage`). | — |

Done well:
- `OG`, `FG`, `ABV`, `IBU`, `SRM` renamed to match `Recipe`, so a1-06's copy lines up name for name.
- `[DatabaseGenerated(DatabaseGeneratedOption.Identity)]` on `CreatedAt`: the read-back shows a real UTC `now()`, not `-infinity`.
- The fixture runs `061` right after `060`, in the one list of SQL files (a1-04's pattern kept).

Verdict: fixes needed (finding 1, before the test lesson: its AC3 test inserts a batch with its
item and step through `Batch.Items`).

## Round 2 · 2026-11-20 · 2939fb1

Checks: `dotnet build` ok (0 warnings, 0 errors) · `dotnet format --verify-no-changes` ok ·
`dotnet test` 4 passed · no web changes.

Round 1:

| # | Status |
|---|---|
| 1 | fixed: `Batch.Recipe`, `Batch.Items`, `Batch.Steps` and `BatchItem.Ingredient` are in. EF Core's model now has 1 foreign key on `Batch`, 2 on `BatchItem`, 1 on `BatchStep`. |
| 2 | still open (nice to have): the `061` comment in `ApiFactory.cs:45` says what, not why. |
| 3 | fixed: `Percentage`, as on `RecipeItem`. |

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `061` unchanged since round 1. |
| AC2 | yes | `061` unchanged since round 1; the round 1 catalog query stands. |
| AC3 | yes (by hand) | Throwaway container from the stack's image (`010`, `015`, `060`, `061`, seed), your `AppDbContext` as `app_api`: **one** `Add` of a batch with an item and a step in `Items` and `Steps`, one `SaveChanges`; EF Core filled both `BatchId`s with the new id. Read back with `Include(Recipe).ThenInclude(Style)`, `Include(Items).ThenInclude(Ingredient)` and `Include(Steps)`: style, ingredient name, `Percentage` 90.00 and the step all came back; `CreatedAt` in UTC. |
| AC4 | yes (by hand) | Same run: `ExecuteDeleteAsync` on the batch left 0 items and 0 steps (the database's cascade; EF Core loaded none of them). Status check unchanged since round 1. |

No new findings.

Outside the ticket: commit 38baf68 (`db/059_home_profile_efficiency.sql`, `docs/RECIPE-ROADMAP.md`)
is on this branch and will be merged with a1-05.

Done well:
- The navigations sit next to their foreign key properties (`Recipe` under `RecipeId`,
  `Ingredient` under `IngredientId`), so each relationship reads in one place.
- `Recipe Recipe = null!` and the two `= []` lists follow a1-03's pattern exactly.

Verdict: ready for tests.

# Test review

## Round 1 · 2026-11-23 · 511db97

Checks: `dotnet build` ok (0 warnings, 0 errors) · `dotnet format --verify-no-changes` ok ·
`dotnet test` 7 passed · no web changes.

| AC | Met | How checked |
|---|---|---|
| AC3 | yes | `Batch_WithItemAndStep_ReadsBackThroughAppDbContext` passes. Broke it: `[DatabaseGenerated]` commented out on `Batch.CreatedAt` → the test failed (*Assert.NotEqual() Failure … Not 0001-01-01*). |
| AC4 | yes | `DeleteBatch_WithItemAndStep_DeletesThem` and `Batch_WithStatusOutsideThePhases_IsRefused` pass. Broke them in `061`, one at a time: `on delete cascade` removed from `batch_item.batch_id` → failed (*23503 … "batch_item_batch_id_fkey"*); the same on `batch_step.batch_id` → failed (*23503 … "batch_step_batch_id_fkey"*); `'brewing'` added to the status check → the status test failed (*Assert.Throws() Failure: No exception was thrown*). Every edit undone; `git diff` empty afterwards. |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | should fix | `app/api.Tests/Database/BatchTablesTests.cs:68-71`, `:133-134` | The tests read whole tables instead of their own batch: the read-back uses `SingleAsync()` on all batches, the delete test counts all batches and all steps. The three tests share one database, so one test's leftover breaks the others. Measured twice in the break-the-code runs: with `CreatedAt` broken, the read-back failed before its clean-up, and its batch 501 then failed the delete test too (*Expected: 0*); with `'brewing'` allowed, batch 503 was saved and the read-back failed with *Sequence contains more than one element*. | One real failure shows up as two or three, and the extra ones point at the wrong test. Every database test from a1-06 on shares this database. Test lesson 1c/1d: keep `batch.Id` and read by it (items and steps by their `BatchId`). | [xUnit shared context](https://xunit.net/docs/shared-context) |
| 2 | Spec | nice to have | `app/api.Tests/Database/BatchTablesTests.cs:133-134` | The delete test is named for items and steps, and AC4 says both, but it counts only steps. | Today the missing item cascade is still caught, by the delete's *23503* exception rather than by an assertion; checking items too makes the test say what AC4 says. | — |
| 3 | Standards | nice to have | `app/api.Tests/Database/BatchTablesTests.cs` | The same batch, item and step are written out three times (502 and 503 also keep the name "Read back"). | The helper you planned (a valid batch, with the number and status as parameters) leaves each test showing only what it is about. | — |

Done well:
- The status test checks `SqlState` and `ConstraintName`, not only that something failed: it
  fails for the right reason or not at all.
- The read-back uses two scopes, so it reads from the database, not from the first context's
  tracked objects.
- Every value is fixed (date 2026-01-01, recipe looked up), nothing from the clock.

Verdict: fixes needed (finding 1).
