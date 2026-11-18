# Lesson: a1-03 · The API's database role and EF Core

## What you will build

The API gets its own way into Postgres. A new SQL file creates the role `app_api`, which may log
in and may only *read* the four tables a batch is made from. The API connects as that role, with
the connection string kept in .NET's user secrets, never in the repo. EF Core, .NET's
object-relational mapper, maps the four tables to C# classes, so a1-06 can read a recipe with its
items as objects. `/api/health` also reports whether the database answers.

It is done when:

- **AC1** The role and its grants are as listed in the ticket (the review checks them with a
  catalog query).
- **AC2** Running the SQL file twice changes nothing.
- **AC3** `app_api` can read `app.recipe` and cannot update it; it can read `ref.ingredient` and
  cannot insert into it.
- **AC4** With the API running, `/api/health` shows `database: ok`; with a wrong password,
  `database: down`, and the API still answers.
- **AC5** No password in any committed file.

Tests come after the review, in `test-lesson.md` (only the `down` case this time; tests against a
real database need a1-04's throwaway database).

**How the pieces fit.** `db/060_app_api_role.sql` runs once by hand as `postgres` and creates
`app_api`. The password is not in the file: you pass it in on the `psql` command line. The same
password goes into the API's connection string, which lives in your user secrets
(`~/.microsoft/usersecrets/…`, outside the repo). At start-up, `Program.cs` reads the connection
string from configuration and registers `AppDbContext`, your EF Core class, with the app's
*dependency injection* container. When a request comes in for `/api/health`, ASP.NET Core creates
an `AppDbContext` and hands it to the health handler, which asks it whether it can connect.

```
psql as postgres ──► db/060_app_api_role.sql ──► role app_api (login, select on 4 tables)
                                                          ▲
user secrets: ConnectionStrings:App ──► Program.cs ──► AppDbContext ──► localhost:5432 (pooler) ──► Postgres
                                                          ▲
                                         GET /api/health ─┘  { "status": "ok", "database": "ok" }
```

What the tools and the stack look like today (measured 2026-11-11 in a scratch project outside
the repo, with your SDK 10.0.114; every error message quoted below comes from those runs):

| Thing | Value | Note |
|---|---|---|
| `Npgsql.EntityFrameworkCore.PostgreSQL` | 10.0.3 | the newest 10.x; it brings EF Core 10 with it |
| Postgres | 15.8 | `postgres` is not a superuser, but has *Create role* |
| Port 5432 on your PC | `supabase-pooler` (Supavisor 2.9.5) | not `supabase-db`, whose port is not published |
| `app.recipe` | 93 rows, 53 with a `process` | no row-level security on the four tables |

## Steps

1. **Check where you are.** From the repo root, run `git branch --show-current` and `git status`.
   *Why:* the work belongs on the ticket's branch, and a clean start keeps the review diff to this
   ticket.
   *Check yourself:* the branch is `a1-03-db-role-and-ef`; `git status` is clean.
   No commit.

2. **Make a password, and find the pooler's tenant id.**
   - Make a random password with `openssl rand -hex 24` and save it in your password manager as
     "app_api, homebrew Postgres".
   - Look up the tenant id with `grep ^POOLER_TENANT_ID= .env` in the repo root. Note the value;
     it is not a secret, but it lives only in `.env`.

   *Why:* the role needs a password that is never written into a file in the repo (AC5), and you
   need it twice: once for the SQL file, once for the connection string. Hex, not base64, because
   base64 can contain `=`, `+` and `/`, and `=` and `;` have meaning inside a connection string.
   The tenant id is needed because port 5432 on your PC is not Postgres itself but
   **Supavisor**, Supabase's connection *pooler*: a program that sits in front of Postgres and
   shares a few real database connections among many clients. One Supavisor can serve many
   databases ("tenants"), so it needs to know which one you mean: you add the tenant id to the
   user name, `app_api.<tenant id>`. n8n does not need this because it talks to `supabase-db`
   directly inside Docker's network; the API runs on your PC, outside that network.
   No commit.

3. **Write `db/060_app_api_role.sql`**, the role and its grants.

   **Read first (about 25 minutes).**
   - [PostgreSQL 15 — Database Roles](https://www.postgresql.org/docs/15/database-roles.html) and
     [Role Attributes](https://www.postgresql.org/docs/15/role-attributes.html) ("login
     privilege", "password"): what a role is, and why a role that can log in is what other
     databases call a user.
   - [PostgreSQL 15 — Privileges](https://www.postgresql.org/docs/15/ddl-priv.html): the first
     four paragraphs, and the table of privileges (look for `USAGE` on a schema and `SELECT` on
     a table).
   - [PostgreSQL 15 — `DO`](https://www.postgresql.org/docs/15/sql-do.html): the description and
     the example.
   - [psql — SQL Interpolation](https://www.postgresql.org/docs/15/app-psql.html#APP-PSQL-INTERPOLATION):
     the paragraph on `:'name'`, and the sentence saying that interpolation is not done inside
     quoted literals.
   - [psql — `ON_ERROR_STOP`](https://www.postgresql.org/docs/15/app-psql.html#APP-PSQL-VARIABLES-ON-ERROR-STOP).

   **3a. The header.** Open the file with the same comment block the other `db/` files have (look
   at `db/058_home_profile.sql`): what the file does, which file it needs first (`db/015_app.sql`
   and `db/010_ref_schema.sql`, which create the tables), how to apply it, and that it is
   idempotent. The apply line is OPERATIONS.md §4's command with one more option,
   `-v app_api_password="$APP_API_PASSWORD"`, and a note that the variable is read with `read`
   (step 3e).
   *Why:* a reader who finds this file in a year should know from its first lines how to run it
   and that running it again is safe.

   **3b. Create the role only if it is missing.** `CREATE ROLE` has no `IF NOT EXISTS`: run twice,
   it fails the second time. So wrap it in a **`DO` block**: an anonymous piece of PL/pgSQL
   (Postgres's own procedural language) that runs once and is not stored. Inside it, an `if not
   exists (…) then … end if;` that looks for `app_api` in the catalog view `pg_roles` (column
   `rolname`) and, only when it is not there, runs `create role app_api login`. The block's body
   is written between `$$` and `$$` (a *dollar-quoted* string, so the body can contain single
   quotes).
   *Why:* **idempotent** means running it again leaves everything as it was (AC2). The usual
   alternative, `drop role if exists` followed by `create role`, is not idempotent in the way that
   matters: dropping the role fails while it owns or has grants on objects, and it would drop the
   grants a1-05 adds.
   *Check yourself:* not yet; step 3e runs the file.

   **3c. Set the password, outside the `DO` block.** One `alter role app_api with login password`
   statement whose password is the psql variable, written `:'app_api_password'`: a colon, then the
   variable name in single quotes. psql replaces it with the value as a properly quoted SQL
   string, so a password with a `'` in it cannot break the statement.
   *Why:* this is how the password stays out of the file (AC5). It runs on every run, so running
   the file with a new password is also how you **change** the password later. `login` is
   repeated here so a role that existed without it gets it.
   *Watch out:* psql does not substitute variables inside a quoted body, and a `DO` body is one.
   Put `:'app_api_password'` inside the `DO` block, or forget the `-v` option, and you get
   (measured) *ERROR: syntax error at or near ":"*, and with `ON_ERROR_STOP` psql stops there with
   exit code 3. That is the behaviour you want: no password, no change.

   **3d. The grants.** Two `grant` statements, nothing more:
   - `usage` on the schemas `app` and `ref` to `app_api`;
   - `select` on `app.recipe`, `app.recipe_item`, `ref.ingredient` and `ref.beer_style` to
     `app_api`.

   *Why:* this is the **principle of least privilege**: the API gets exactly what it needs today
   and nothing else, so a bug or a stolen password cannot change a recipe or read the pipeline's
   run logs. Grants are added ticket by ticket (a1-05 adds the batch tables'). A schema is like a
   folder: `usage` lets the role look inside, `select` lets it read a table. You need both: with
   `select` but no `usage` the role gets (measured, with another role) *ERROR: permission denied
   for schema app*. `GRANT` is idempotent by itself: granting what is already granted changes
   nothing. Not `grant all`, and not `alter default privileges`, which would hand over every
   future table too.
   *Watch out:* a typo in a table name stops the file at that statement, after the role has
   already been created. That is fine: fix the name and run the file again; that is what
   idempotent is for.

   **3e. Apply it, twice.** In a terminal at the repo root:
   - `read -rs APP_API_PASSWORD` and paste the password (nothing is shown; `-s` is *silent*,
     `-r` keeps backslashes). Then `export APP_API_PASSWORD`. The variable lives in this terminal
     only, and the password is not in your shell history.
   - Run the apply line from your header.
   - Run it a second time.

   *Watch out:* the database logs every DDL statement (`log_statement` is `ddl`, checked
   2026-11-11), and `alter role … password '…'` is DDL, so the password can end up in
   `docker logs supabase-db`. On 2026-11-11 those logs showed no statement lines at all, so check
   it yourself after the run: `docker logs supabase-db 2>&1 | grep -c app_api` should print `0`.
   If it does not, tell me in this session before going on.
   *Check yourself:* both runs print the same four lines, `DO`, `ALTER ROLE`, `GRANT`, `GRANT`,
   and no `ERROR` (the `DO` block creates the role on the first run only, but reports `DO` both
   times). Then look at the result in psql as `postgres`
   (`docker exec -it supabase-db psql -U postgres -d postgres`): `\du app_api` shows the role with
   no attributes except that it can log in (no *Cannot login*), `\dn+ app` and `\dn+ ref` show
   `app_api=U/postgres` among the access privileges, and `\dp app.recipe` shows
   `app_api=r/postgres` (`r` is *read*, i.e. select). That is AC1 and AC2.

   **Commit:** `git add db/060_app_api_role.sql`, message `Add the app_api role and its grants`.

4. **Check AC3 by hand, as `app_api`.** Open psql as the new role:
   `docker exec -it supabase-db psql -h 127.0.0.1 -U app_api -d postgres`. Then try four things:
   count the rows of `app.recipe`; an `update` of `app.recipe` that changes nothing (set `status`
   to itself `where false`); count the rows of `ref.ingredient`; an `insert` of one made-up row
   into `ref.ingredient`.
   *Why:* the catalog says what was granted; trying it shows what the role can really do. The
   `update … where false` would change no row even if it were allowed, so the check is safe:
   Postgres checks privileges before it looks at any row. psql does not ask for a password here:
   inside the container, `pg_hba.conf` trusts connections from `127.0.0.1`. So this checks the
   grants, not the password; step 10 checks the password, through the pooler, like the API.
   *Check yourself:* the two counts answer (93 recipes on 2026-11-11); the `update` and the
   `insert` each fail with a *permission denied* error that names the table.
   No commit.

5. **Add the EF Core provider for Postgres.** From `app/`:
   `dotnet add api package Npgsql.EntityFrameworkCore.PostgreSQL`.
   *Why:* an **ORM** (object-relational mapper) turns rows into objects and C# queries into SQL,
   so the API's code works with a `Recipe` object instead of reading columns by name from a raw
   result. **EF Core** is .NET's ORM (SYSTEM.md §4); it talks to each database through a
   *provider*, and Npgsql's is the one for Postgres. The provider package depends on EF Core
   itself, so one package brings both. Docs:
   [EF Core overview](https://learn.microsoft.com/ef/core/) (5 minutes) ·
   [Npgsql EF Core provider](https://www.npgsql.org/efcore/).
   SYSTEM.md C5 says EF Core maps tables and never creates them: no `Microsoft.EntityFrameworkCore.Design`
   package and no `dotnet ef` tool, because those are for migrations, which this project does not
   use.
   *Check yourself:* `HomebrewApp.csproj` has a `PackageReference` to
   `Npgsql.EntityFrameworkCore.PostgreSQL` version 10.0.3; `dotnet build` in `app/` ends with
   `0 Warning(s)` and `0 Error(s)`.
   **Commit:** `git add app/api/HomebrewApp.csproj`, message `Add the Npgsql EF Core provider`.

6. **Put the connection string in user secrets.**

   **Read first (about 15 minutes).**
   [Safe storage of app secrets in development](https://learn.microsoft.com/aspnet/core/security/app-secrets?view=aspnetcore-10.0):
   "Enable secret storage", "Set a secret", "Read the secret via the configuration API" and
   "List the secrets". Look for where the file lives and in which environment it is read.

   - From `app/`: `dotnet user-secrets init --project api`.
   - In a terminal where `APP_API_PASSWORD` is set (step 3e), from `app/`:
     `dotnet user-secrets set --project api "ConnectionStrings:App" "Host=localhost;Port=5432;Database=postgres;Username=app_api.<tenant id>;Password=$APP_API_PASSWORD"`,
     with your tenant id from step 2. The double quotes let the shell put the password in.

   *Why:* the API needs the password, and AC5 says no committed file may hold it, so it cannot go
   into `appsettings.json`. **User secrets** are a JSON file per project in your home folder
   (`~/.microsoft/usersecrets/<UserSecretsId>/secrets.json`); `init` writes only the
   `UserSecretsId`, a random id, into the project file. `WebApplication.CreateBuilder` reads that
   file automatically, but only in the `Development` environment, so a published build never uses
   it. The key `ConnectionStrings:App` is the configuration path `ConnectionStrings` → `App`; the
   colon separates the levels. `GetConnectionString("App")` (step 9) is a shortcut for exactly that
   path. Port 5432 is Supavisor's *session* mode, which gives the API one real connection for as
   long as it holds it; 6543 is *transaction* mode, which can swap the connection between
   statements, and Npgsql's prepared statements do not survive that.
   Docs: [Npgsql connection string parameters](https://www.npgsql.org/doc/connection-string-parameters.html)
   ("Basic connection").
   *Watch out:* without `.<tenant id>` in the user name, the pooler answers (measured)
   *XX000: (ENOIDENTIFIER) no tenant identifier provided (external_id or sni_hostname required)*.
   With a tenant id but a role it does not know: *XX000: (EAUTHQUERY) user not found in the
   database*. With a wrong password: *28P01: password authentication failed for user "…"*. You
   see these only when you open a connection yourself; step 10's health check hides them and
   says `down`.
   *Check yourself:* `dotnet user-secrets list --project api` shows one line,
   `ConnectionStrings:App = Host=localhost;…` with the password in it (this is your own
   terminal; don't paste that line anywhere). `git diff app/api/HomebrewApp.csproj` shows only a
   new `UserSecretsId` line. `git status` shows no `secrets.json`.
   **Commit:** `git add app/api/HomebrewApp.csproj`, message `Enable user secrets for the API`.

7. **Write the four entity classes** in a new folder `app/api/Data/`, namespace
   `HomebrewApp.Data`, one file per class: `Recipe.cs`, `RecipeItem.cs`, `BeerStyle.cs`,
   `Ingredient.cs`. None is used yet, so the build stays green while you write them, as long as
   all four exist by the end of the step (they refer to each other).

   **Read first (about 30 minutes).**
   - [EF Core — Entity types, "Table name" and "Table schema"](https://learn.microsoft.com/ef/core/modeling/entity-types#table-name):
     the *Data Annotations* tab.
   - [EF Core — Entity properties, "Column names" and "Column data types"](https://learn.microsoft.com/ef/core/modeling/entity-properties#column-names):
     the *Data Annotations* tab.
   - [EF Core — Working with nullable reference types](https://learn.microsoft.com/ef/core/miscellaneous/nullable-reference-types):
     "Non-nullable properties and initialization" and "Required navigation properties".
   - [EF Core — One-to-many relationships](https://learn.microsoft.com/ef/core/modeling/relationships/one-to-many):
     the first example only (a `Blog` with a `Posts` collection, a `Post` with `BlogId` and
     `Blog`).
   - [Npgsql — Supported types](https://www.npgsql.org/doc/types/basic.html): the "Read mappings"
     table.
   - C#: [`required` members](https://learn.microsoft.com/dotnet/csharp/language-reference/keywords/required)
     and [`init` accessors](https://learn.microsoft.com/dotnet/csharp/language-reference/keywords/init).

   Why `Data/` and not a feature folder: these four classes describe tables that already exist
   and that several features read (Batches in a1-06, Recipes in M4, Inventory in M7). A feature
   folder holds what belongs to one feature only; the shared database model gets one shared
   place, next to `AppDbContext` (step 8).

   **7a. `Recipe`: the class and its table.** A `public class Recipe` with the attribute
   `[Table("recipe", Schema = "app")]` above it (the attribute lives in
   `System.ComponentModel.DataAnnotations.Schema`; add a `using`).
   *Why:* an **entity** is a class EF Core maps to a table: one object per row, one property per
   column. By default EF Core would look for a table named like the class (`Recipe`) in the
   default schema; Postgres names are lower-case `snake_case` here and live in `app` and `ref`,
   so every name is given explicitly. An *attribute* (the square brackets) is a label on a class
   or property that a library reads at run time; EF Core calls these *data annotations*. They sit
   next to what they describe, so each class reads on its own, which is why they are used here
   rather than the alternative, a long `OnModelCreating` method in the context.

   **7b. `Recipe`: the columns.** One property per column the API will read, each with
   `[Column("<column name>")]`: `id`, `style_id`, `status`, `batch_l`, `efficiency_pct`, `og`,
   `fg`, `abv`, `ibu`, `srm`, `process`, `created_at`. Leave out `brief_id`, `parent_id`,
   `targets`, `calc_version` and `sheet`: EF Core ignores columns a class does not mention, and a
   later ticket adds a property when it needs one. Pick each C# type from the column's type
   (`\d app.recipe` in psql shows them) and the Npgsql table:

   | Postgres | C# | |
   |---|---|---|
   | `bigint` | `long` | ids |
   | `text` | `string` | |
   | `numeric(p,s)` | `decimal` | exact, never `double`, for gravities and amounts |
   | `timestamp with time zone` | `DateTime` | Npgsql gives it `Kind = Utc` |
   | `jsonb` | `string` | with `TypeName = "jsonb"` in the `[Column]` attribute |

   A column marked `not null` gets a plain type; a nullable one gets `?` after the type
   (`decimal?`, `string?`). Every property is `{ get; init; }`, and every non-nullable `string`
   is `required`.
   *Why:* `long` and `decimal` match the columns exactly; a `double` is a binary fraction and
   cannot hold most decimal values such as 1.0485 exactly. `process` stays a string of JSON for now: a1-06 only copies it, and a1-08 decides
   how to read it. `init` instead of `set` means a property can be given a value only when the
   object is created, by EF Core while reading a row or by an object initializer; no code can
   change a loaded recipe afterwards. That is the "read-only in code" of the ticket. `required`
   tells the compiler that whoever creates a `Recipe` must give `Status` a value, which is how a
   non-nullable `string` can exist without a constructor; EF Core fills it from the row.
   *Watch out:* a non-nullable `string` without `required` builds with (measured)
   *warning CS8618: Non-nullable property 'Status' must contain a non-null value when exiting
   constructor. Consider adding the 'required' modifier or declaring the property as nullable.*
   A warning fails nothing, but a0-02 set the rule: zero warnings.
   *Check yourself:* remove `required` from `Status` once, run `dotnet build`, see the warning,
   put it back.

   **7c. `Recipe`: the two navigations.** A **navigation** is a property that holds another
   entity instead of a column value. `Style`, of type `BeerStyle`, initialised to `null!`; and
   `Items`, a `List<RecipeItem>` initialised to an empty list (`[]`). Both `{ get; init; }`, no
   `[Column]`.
   *Why:* navigations let a1-06 load a recipe with its style and items in one query (`Include`).
   EF Core works out the foreign key by name: a navigation `Style` plus a property `StyleId`
   means `StyleId` holds the id of the `BeerStyle`. A navigation is filled only when the query asks
   for it, so the compiler cannot know it is set; `= null!` (the *null-forgiving* operator) tells
   it "trust me, EF Core sets this", which is the EF docs' recommended way for a required
   reference navigation. A collection is never null, only empty, so it starts as `[]`.

   **7d. `RecipeItem`.** Table `app.recipe_item`, all nine columns: `id`, `recipe_id`,
   `ingredient_id`, `raw_name`, `usage`, `time_min`, `pct`, `amount`, `unit`. Then one navigation,
   `Ingredient`, of type `Ingredient?`.
   *Why:* `ingredient_id` is nullable (a free-text item has no catalogue entry and keeps its
   `raw_name`), so the property is `long?` and the navigation is nullable too, which makes the
   relationship optional. That is why this navigation needs no `null!`: null is a real value
   here. No `Recipe` navigation back is needed; `RecipeId` plus `Recipe.Items` is enough for EF
   Core to see the one-to-many relationship.

   **7e. `BeerStyle` and `Ingredient`.** `BeerStyle` on `ref.beer_style`: `id`, `code`, `name`
   (`name` is nullable). `Ingredient` on `ref.ingredient`: `id`, `kind`, `name`, `producer`. No
   navigations.

   *Check yourself (whole step):* `dotnet build` in `app/` ends with `0 Warning(s)` and
   `0 Error(s)`. Compare each `[Column]` name with `\d` of its table in psql: a misspelt name
   builds fine and only fails when a query runs (a1-06), so read them once now.
   **Commit:** `git add app/api/Data/`, message `Add entity classes for recipes and catalogue`.

8. **Write `AppDbContext`** in `app/api/Data/AppDbContext.cs`.

   **Read first (about 15 minutes).**
   [DbContext lifetime, configuration and initialization](https://learn.microsoft.com/ef/core/dbcontext-configuration/):
   "The DbContext lifetime" and "ASP.NET Core dependency injection".

   **8a. The class.** `public class AppDbContext`, deriving from `DbContext` (namespace
   `Microsoft.EntityFrameworkCore`), with a primary constructor (met in a0-02's test lesson) that
   takes one `DbContextOptions<AppDbContext>` and passes it on to the base class: the colon after
   the class name, `DbContext`, and the parameter in parentheses.
   *Why:* a **`DbContext`** is your session with the database: it holds the connection, knows the
   model (which class is which table) and turns queries into SQL. It gets its settings (provider,
   connection string) from outside, through those options, so the class itself contains no
   connection string; step 9 provides them.

   **8b. The four sets.** One `DbSet<T>` property per entity, named in the plural (`Recipes`,
   `RecipeItems`, `BeerStyles`, `Ingredients`), each written as an expression-bodied property
   that returns `Set<T>()`: the name, `=>`, then the call.
   *Why:* a `DbSet<T>` is the starting point of a query on one table (`db.Recipes.Where(…)`).
   Listing the four also tells EF Core which classes belong to the model. The `=> Set<T>()` form
   has no setter, so nothing can replace a set, and the compiler does not ask for an initial
   value. Docs: [Working with nullable reference types, "DbContext and DbSet"](https://learn.microsoft.com/ef/core/miscellaneous/nullable-reference-types#dbcontext-and-dbset).

   No `OnConfiguring` and no `OnModelCreating`: the annotations from step 7 carry the mapping,
   and the configuration comes from step 9.
   *Check yourself:* `dotnet build` passes with no warnings. Nothing uses the context yet.
   **Commit:** `git add app/api/Data/AppDbContext.cs`, message `Add AppDbContext`.

9. **Register the context in `Program.cs`.**

   **Read first (about 20 minutes).**
   [Dependency injection in ASP.NET Core](https://learn.microsoft.com/aspnet/core/fundamentals/dependency-injection?view=aspnetcore-10.0):
   "Overview of dependency injection" and "Service lifetimes" (what *scoped* means).

   **9a. Read the connection string, or stop.** After `CreateBuilder`, one line that reads
   `builder.Configuration.GetConnectionString("App")` into a variable, followed by `??` and a
   `throw new InvalidOperationException(…)` with a message naming the missing key.
   *Why:* `GetConnectionString` returns `null` when the key is missing. Passed on as `null`, the
   API would start, and every health check would say `down` with no hint why (measured: EF Core's
   connection check returns false for a null connection string). Stopping at start-up with a
   clear message is called **failing fast**: a configuration mistake shows up at once, in plain
   words, at the place it happened. `??` (the *null-coalescing* operator) returns its left side
   unless that is null, and then evaluates its right side; a `throw` is allowed there as an
   expression. Docs: [`??` operator](https://learn.microsoft.com/dotnet/csharp/language-reference/operators/null-coalescing-operator).

   **9b. Register `AppDbContext`.** With the other `builder.Services` calls:
   `AddDbContext<AppDbContext>(…)`, whose argument is a lambda that receives an options builder
   and calls `UseNpgsql` with the connection string, then
   `UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking)` on the result.
   *Why:* **dependency injection** (DI) means a class does not create what it needs; it asks for
   it, and the app's *service container* hands it over. You register a service once here, and
   from then on any route handler that names `AppDbContext` as a parameter gets one (step 10).
   `AddDbContext` registers it as **scoped**: a new context per HTTP request, disposed when the
   request ends, so two requests never share one (a `DbContext` is not safe to use from two
   threads at once). **No-tracking** means EF Core does not keep a copy of every loaded object
   to detect changes for `SaveChanges`: faster for reads, and together with `init` properties a
   second guard that this code only reads. The real guard is still the role's grants (AC3).
   Docs: [Tracking vs. No-Tracking Queries, "Configuring the default tracking behavior"](https://learn.microsoft.com/ef/core/querying/tracking#configuring-the-default-tracking-behavior).
   *Check yourself:* `dotnet run --project api` starts as before, and `/api/health` answers as
   before. Then break it once: start it with the key misspelt in `GetConnectionString`; it stops
   at start-up with your exception's message. Put it back.
   `dotnet test` still passes: the tests start the API in `Development`, so they read your user
   secrets too (measured in a scratch project: with the secret removed, the same kind of test
   fails with the start-up exception).
   **Commit:** `git add app/api/Program.cs`, message `Register AppDbContext with the connection string`.

10. **`/api/health` reports the database**, in `Features/Health/HealthEndpoints.cs`.

    **Read first (about 10 minutes).**
    [Parameter binding in minimal APIs](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/parameter-binding?view=aspnetcore-10.0):
    "Parameter binding with dependency injection" and "Special types" (`CancellationToken`).
    [`DatabaseFacade.CanConnectAsync`](https://learn.microsoft.com/dotnet/api/microsoft.entityframeworkcore.infrastructure.databasefacade.canconnectasync?view=efcore-10.0):
    the Remarks.

    **10a. The response record.** `HealthResponse` gets a second property, `Database`, a
    `string`.
    *Expected failure:* the handler's `new HealthResponse("ok")` no longer compiles (one argument
    missing) until 10c.

    **10b. The handler's parameters and return type.** The handler takes an `AppDbContext` and a
    `CancellationToken`, becomes `async`, and returns `Task<Ok<HealthResponse>>` instead of
    `Ok<HealthResponse>`. `async`, `await` and `Task` are the ones from a0-02's test lesson.
    *Why:* ASP.NET Core sees that `AppDbContext` is a registered service and passes the request's
    context in; you never write `new AppDbContext`. The `CancellationToken` is a special type it
    fills with the request's own token: when the caller hangs up, the token is cancelled, and the
    database call can stop instead of finishing for nobody. A handler that waits on the database
    must not block a thread while it waits, so it is asynchronous, and its result is wrapped in a
    `Task`.

    **10c. The check.** `await` the context's `Database.CanConnectAsync`, passing the token, and
    build the response with `"ok"` as `Status` and `"ok"` or `"down"` as `Database`, from the
    `bool` it returns (a conditional `? :` fits on one line).
    *Why:* `CanConnectAsync` opens a connection and closes it again: about the cheapest thing that
    proves the server, the pooler, the user name and the password all work. It catches every
    connection error and returns `false` instead (the docs' Remarks; measured for a wrong
    password, a role the pooler does not know, a closed port and a null connection string), so
    the handler needs no `try`/`catch`, and the API still answers 200 when the database is down
    (AC4). `Status` stays `"ok"`: it says the API is up; `Database` says what the API can reach.
    What it does **not** prove is that the grants or the mapping are right; AC3 checks the
    grants, and a1-06's tests check the mapping.
    *Check yourself:* `dotnet build` with no warnings and `dotnet test` green (the existing test
    checks `status` only). Run the API; `curl -i http://localhost:5080/api/health` gives
    `200 OK` and `{"status":"ok","database":"ok"}` (AC4, first half). In `/openapi/v1.json`, the
    `HealthResponse` schema lists `status` and `database`. The web page still shows "API ok": it
    reads only `status`.
    **Commit:** `git add app/api/Features/Health/HealthEndpoints.cs`, message
    `Report database status in /api/health`.

11. **Check the `down` case (AC4, second half).** Stop the API. Start it again from `app/` with
    an environment variable in front of the command, on one line:
    `ConnectionStrings__App="Host=localhost;Port=5432;Database=postgres;Username=app_api.<tenant id>;Password=wrong" dotnet run --project api`.
    Then `curl -i http://localhost:5080/api/health`.
    *Why:* configuration has layers, and later ones win: `appsettings.json`, then
    `appsettings.Development.json`, then user secrets, then environment variables, then the command
    line. So an environment variable overrides your secret for this one run without touching it.
    `__` (two underscores) stands for the `:` in the key, because shells do not allow `:` in a
    variable name. Docs:
    [Configuration in ASP.NET Core, "Default application configuration sources"](https://learn.microsoft.com/aspnet/core/fundamentals/configuration/?view=aspnetcore-10.0#default-application-configuration-sources).
    *Check yourself:* `200 OK` with `{"status":"ok","database":"down"}`, after about a second
    (measured: a wrong password takes about 1 s at the pooler). Stop it and start it normally;
    `database` is `ok` again.
    No commit.

12. **Write the role down in `docs/OPERATIONS.md` §4.** A new bullet next to the read-only role's
    bullet: that `app_api` is the API's login role and what it may do (with a pointer to
    `db/060_app_api_role.sql` for the list); how its password is set (the `read -rs` line and the
    apply command with `-v app_api_password=…`); where the API keeps it (user secrets,
    `ConnectionStrings:App`, user name `app_api.<POOLER_TENANT_ID>` because port 5432 is the
    pooler); and that after a password change, or after the database volume is recreated, the
    file must be run again with the password **and** the user secret updated to match, or the
    health check shows `database: down`. Mark it with today's date, as the other facts there are.
    *Why:* OPERATIONS.md is where the stack's traps live (CLAUDE.md). In six months the question
    will be "why is the API's database down?", and the answer must be findable without this
    lesson.
    *Check yourself:* `grep -n "060\|password" docs/OPERATIONS.md` and the file holds no password.
    **Commit:** `git add docs/OPERATIONS.md`, message `Document the app_api role in OPERATIONS`.

13. **Update "Run the API" in `app/README.md`.** Since step 9 the API stops at start-up without
    its connection string, so the section needs a one-time setup before the run command: the
    secret's key and the shape of its value (with placeholders, never the password), pointing to
    OPERATIONS.md for the role. And the health line now answers `{"status":"ok","database":"ok"}`.
    *Why:* a0-02's rule for that section: someone who has never seen the project can follow it
    word for word.
    *Check yourself:* `dotnet user-secrets list --project api` shows what the section says should
    be there; follow the section in a fresh terminal and get `database: ok`.
    **Commit:** `git add app/README.md`, message `Explain the API's connection string setup`.

## Files you will touch

- `db/060_app_api_role.sql`: new; the role, its password from a psql variable, the grants.
- `app/api/HomebrewApp.csproj`: the Npgsql package (step 5) and the `UserSecretsId` (step 6).
- `app/api/Data/Recipe.cs`, `RecipeItem.cs`, `BeerStyle.cs`, `Ingredient.cs`: new entity classes.
- `app/api/Data/AppDbContext.cs`: new; the context with four sets.
- `app/api/Program.cs`: the connection string (fail fast) and `AddDbContext`.
- `app/api/Features/Health/HealthEndpoints.cs`: `Database` in the response; the handler checks the
  connection.
- `docs/OPERATIONS.md`: the `app_api` bullet in §4.
- `app/README.md`: the connection string setup in "Run the API".
- Outside the repo: your user secrets file, which is never committed.

## Before you ask for a review

- [ ] The file ran twice without an error, and `\du app_api`, `\dn+ app`, `\dn+ ref`,
      `\dp app.recipe` show what step 3e describes (AC1, AC2).
- [ ] As `app_api`, both counts answer and the `update` and `insert` are refused (AC3).
- [ ] `/api/health` gives `database: ok`, and `database: down` with a wrong password while still
      answering 200 (AC4).
- [ ] In a terminal where `APP_API_PASSWORD` is set: `git log -p main.. | grep -c "$APP_API_PASSWORD"`
      prints `0`, and `git grep -n -i "password=" -- . ':!*.md'` shows no real password (AC5).
- [ ] `docker logs supabase-db 2>&1 | grep -c app_api` printed `0` after step 3e.
- [ ] `dotnet build` in `app/` reports 0 warnings and 0 errors; `dotnet test` passes.
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted.
- [ ] Ask yourself: a1-05 adds the batch tables, which the API must write. Which file gets the
      new grants, and why is the answer not "turn `060`'s `select` into `all`"?
