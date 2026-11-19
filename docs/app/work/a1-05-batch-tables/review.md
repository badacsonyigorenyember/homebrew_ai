# Review: a1-05 · Batch tables

## Round 1 · 2026-11-19 · 503202c + staged `AppDbContext.cs`

`db/061_app_batch.sql` was written by Claude at your request in this session; it is reviewed here
like the rest. The entity classes came from the Rider generator script (outside the repo).

Checks: `dotnet build` ok (0 warnings, 0 errors) · `dotnet format --verify-no-changes` ok ·
`dotnet test` 4 passed · `[Column]` names against the catalog: 40 of 40 match · no web changes.
`app/api/Data/AppDbContext.cs` (step 8) is staged but not committed yet.

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
item and step through `Batch.Items`). Then commit step 8 too.
