# a1-03 · Review

## Round 1 · 2026-11-18 · 2c57617

Checks: `dotnet build` ok (0 warnings, 0 errors) · `dotnet test` ok (1 passed) · the EF model
built in a scratch program against the real database as `app_api` (with your user secret):
`Recipes` with `Style` 93 rows, `BeerStyles` 285, `Ingredients` 301, `RecipeItems` **fails**
(finding 1) · every mapped property's nullability compared with `information_schema.columns`:
all 33 match · the API run twice for AC4 · `docker logs supabase-db`: no `alter role` line, so the
password is not in the log (the 5 `app_api` lines are failed logins from the password debugging).

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `pg_roles`: `app_api` can log in, no superuser, create-role, create-db or bypass-RLS, member of no role. `nspacl` of `app` and `ref`: `app_api=U/postgres`. `relacl` of the four tables: `app_api=r/postgres`. `role_table_grants` for `app_api`: 4 rows, all `SELECT`. |
| AC2 | yes | Not rerun by me (it needs the password). You ran the file several times while we debugged the password, without an error: the stored password hash changed between two of my checks (each run stores a new salt), and the catalog still shows one role and exactly the grants above. |
| AC3 | yes | As `app_api`: `select count(*) from app.recipe` → 93, from `ref.ingredient` → 301; `update app.recipe set status = status where false` → `permission denied for table recipe`. `has_table_privilege`: `INSERT` on `ref.ingredient` false; `INSERT`/`UPDATE`/`DELETE` false on all four; nothing on `app.brewer_profile`. |
| AC4 | yes | `dotnet run --project api`: `200 OK` `{"status":"ok","database":"ok"}`. With `ConnectionStrings__App` set to your connection string with `Password=wrong`: `200 OK` `{"status":"ok","database":"down"}`. |
| AC5 | yes | `git log -p main..` has no `Password=` followed by a value; `git grep -i "password="` outside docs shows only `docker-compose.yml`'s `${…}` references. |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec | must fix | `app/api/Data/RecipeItem.cs:5` | `[Table("app.recipe_item")]` puts the schema into the table name. EF Core maps it to one table literally named `app.recipe_item` in the default schema, and the query fails: `42P01: relation "app.recipe_item" does not exist` (measured; the generated SQL is `FROM "app.recipe_item"`). The other three classes do it right. | The build and the health check cannot see this: it fails only when a query touches the table, which is a1-06's first endpoint. | [Entity types, "Table schema"](https://learn.microsoft.com/ef/core/modeling/entity-types#table-schema) (Data Annotations tab) |
| 2 | Standards | should fix | `app/api/Program.cs:7-8` | The fail-fast message is `"Missing key"`, and the variable holding the connection string is called `config`. Lesson step 9a asked for a message naming the key. | Failing fast is only useful if the message says what to fix: which key (`ConnectionStrings:App`) and where it goes (user secrets, see the README). A name that says what the variable holds (the connection string, not the configuration) reads correctly at `UseNpgsql(…)`. | [`??` operator](https://learn.microsoft.com/dotnet/csharp/language-reference/operators/null-coalescing-operator) |
| 3 | Spec | should fix | `app/api/Data/Ingredient.cs:9` | `Id` has `{ get; set; }`; every other property in the four classes has `{ get; init; }`. | The ticket says the entities are read-only in code; one `set` lets any code change a loaded ingredient's id. | [`init` accessor](https://learn.microsoft.com/dotnet/csharp/language-reference/keywords/init) |
| 4 | Standards | nice to have | `app/api/Data/Recipe.cs:14` | `Style` is `required BeerStyle Style { get; init; }` instead of the lesson's `= null!` (step 7c). | `required` means every `new Recipe { … }` must supply a whole `BeerStyle`, which the test data in a1-04 and a1-06 will then have to build. It also suggests `Style` is always there, while EF Core fills it only when the query has `Include(r => r.Style)`. | [Nullable reference types, "Required navigation properties"](https://learn.microsoft.com/ef/core/miscellaneous/nullable-reference-types#required-navigation-properties) |

Outside the ticket, in separate commits: `app/.editorconfig` (moved up from `app/api/`) and
`app/HomebrewApp.sln.DotSettings` (the `OG` abbreviation). Both are fine. At your request I changed
the EditorConfig: `insert_final_newline` is now `true` (it was `false`, which is why the new `.cs`
files end without a newline) and `trim_trailing_whitespace = true`, both for `*.cs`. I also wrote
the docs from lesson steps 12 and 13: the `app_api` bullet in `docs/OPERATIONS.md` §4 and the
connection string setup in `app/README.md`. None of these three files is committed yet.

Done well:
- Every mapped column has the right C# type and nullability: all 33 match the catalog, including
  `decimal?` for the nullable numerics and `string?` for `process` and `beer_style.name`.
- `060` keeps the password out of every file and every log, and the role has exactly the four
  `SELECT`s and two `USAGE`s the ticket lists.
- The health handler is short and does what it should: it takes the context and the request's
  `CancellationToken` from DI, and `CanConnectAsync` keeps the API answering when the database
  is down.

Verdict: fixes needed

## Round 2 · 2026-11-18 · c466b2e

Checks: `dotnet build` ok (0 warnings, 0 errors) · `dotnet test` ok (1 passed) · the scratch EF
program against the real database as `app_api`: the model maps all four classes to the right
schema and table (`RecipeItem` → `app.recipe_item`, SQL `FROM app.recipe_item`); `Recipes` with
`Style` 93 rows, `RecipeItems` 530 (the catalog count is 530), `BeerStyles` 285, `Ingredients`
301, and `Recipes` with `Style`, `Items` and `Items.Ingredient` in one query: 530 items · the
API started without user secrets (`--no-launch-profile`, so `Production`) stops with
`InvalidOperationException: Connection string 'ConnectionStrings:App' is not set. In development,
store it in the API's user secrets; see app/README.md, "Run the API".` · the docs commit
(`eb44ef3`) holds only placeholders and `$APP_API_PASSWORD`, no password.

AC1–AC5: unchanged since round 1, still met. The changes touch only the entity classes, the
start-up message and the EditorConfig; none of them changes the role, the grants or the health
handler.

| # | Round 1 finding | Status |
|---|---|---|
| 1 | `RecipeItem` table name with the schema in it | fixed: `[Table("recipe_item", Schema = "app")]`; queries read all 530 rows |
| 2 | Fail-fast message `"Missing key"`, variable `config` | fixed: the message names the key and the README section; the variable is `conn` |
| 3 | `Ingredient.Id` with `set` | fixed: `init` |
| 4 | `required BeerStyle Style` | fixed: `= null!` |

No new findings. The files now end with a newline, as the EditorConfig asks.

Done well:
- Every finding was fixed in the way its "why" asked, in one commit, without touching anything
  else.
- The fail-fast message gives the exact key and where the setup is written down, and it holds
  nothing secret.

Verdict: ready for tests
