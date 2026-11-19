# Lesson: a1-04 · Test database

## What you will build

Today `dotnet test` reaches your real database: the tests start the API in `Development`, so it
reads your user secret and connects to the stack. After this ticket every API test talks to its
own Postgres instead, a Docker container started at the beginning of the test run from the same
image as the stack, filled with the tables the API reads and two seeded recipes, and deleted at
the end. The API in the tests connects to it as `app_api`, exactly as it connects to the stack.

It is done when:

- **AC1** `dotnet test` starts the container, runs, and removes it; your running stack is
  untouched.
- **AC2** A test proves `app_api` can read `app.recipe` and cannot update it.
- **AC3** A test proves `/api/health` shows `database: ok` against the container.
- **AC4** The list of applied SQL files is in one place in the fixture, with a comment on why each
  is needed.

This ticket is test code from start to finish (its `## Tests` says so), so this lesson teaches the
tests too: there is no separate test lesson. After the code review comes the test review, which
breaks the grant in `db/060_app_api_role.sql` and checks that your two tests notice.

**How the pieces fit.** xUnit creates one `ApiFactory` for the whole test run. Before the first
test, the factory starts a container from `supabase/postgres:15.8.1.085`, copies the repo's `db/`
folder and your test data into it, and runs `psql` *inside the container* as `postgres` on each
SQL file in turn: the two that create the tables, `060` with a made-up password, then your seed.
The factory is also a `WebApplicationFactory`, so when a test asks it for a client it starts the
API in memory with `ConnectionStrings:App` pointing at the container as `app_api`. A test of the
role skips the API and opens its own connection as `app_api`. When the run ends, the factory
deletes the container.

```
dotnet test
  └─ xUnit: one ApiFactory for every class in the collection
       ├─ InitializeAsync ─► container supabase/postgres (random port on 127.0.0.1)
       │     psql as postgres: 010 · 015 · 060 (password variable) · seed (process variable)
       ├─ CreateClient ─► the API in memory ─► ConnectionStrings:App = container, as app_api
       │     HealthEndpointsTests ─► GET /api/health ─► {"status":"ok","database":"ok"}
       ├─ AppApiRoleTests ─► its own connection as app_api ─► select ok · update refused
       └─ DisposeAsync ─► container deleted
```

What the tools look like today (measured 2026-11-18 in a scratch copy of your API outside the
repo, with the SDK installed here, 10.0.115; every error quoted below comes from those runs):

| Thing | Value | Note |
|---|---|---|
| `Testcontainers.PostgreSql` | 4.17.0 | the newest; it brings `Testcontainers` 4.17.0 |
| xUnit | 2.9.3 (already in the test project) | v2: its `IAsyncLifetime` has its own `DisposeAsync` |
| The image | `supabase/postgres:15.8.1.085` | already on your PC (the stack uses it), 3 GB |
| Container start | about 3.4 s | the whole `dotnet test` about 5–6 s |
| `postgres` in a fresh container | not a superuser, may create roles | the same as in the stack |
| Recipe 1349 (the ticket's note) | **does not exist** | 93 recipes, ids 112–1489. The newest with salts, two mash steps, one boil hop, one whirlpool hop and one yeast is **1155** (2026-10-30, Session IPA): Columbus at 60, Citra in the whirlpool, US-05, a Cascade dry hop. This lesson uses 1155 |

## Steps

1. **Check where you are.** From the repo root, run `git branch --show-current` and `git status`.
   *Why:* the work belongs on the ticket's branch, and a clean start keeps the review diff to this
   ticket.
   *Check yourself:* the branch is `a1-04-test-database`; `git status` is clean.
   No commit.

2. **Add Testcontainers.** From `app/`:
   `dotnet add api.Tests package Testcontainers.PostgreSql`.
   *Why:* **Testcontainers** is a library that starts Docker containers from test code and
   removes them afterwards, so a test can use a real database instead of a fake one. A fake (an
   in-memory database) would not have `pg_jsonschema`, the `app_api` role or Postgres's
   permission checks, and AC2 is exactly a permission check. The `PostgreSql` module adds a
   builder that knows how to start Postgres, wait until it accepts connections and hand out a
   connection string. It goes into the **test** project only: the API itself never starts
   containers.
   Docs: [Testcontainers for .NET — PostgreSQL module](https://dotnet.testcontainers.org/modules/postgres/)
   (5 minutes).
   *Check yourself:* `app/api.Tests/HomebrewApp.Tests.csproj` has a `PackageReference` to
   `Testcontainers.PostgreSql` version 4.17.0; `dotnet build` in `app/` ends with `0 Warning(s)`
   and `0 Error(s)`.
   **Commit:** `git add app/api.Tests/HomebrewApp.Tests.csproj`, message
   `Add Testcontainers for PostgreSQL`.

3. **Write `ApiFactory`: the container and the SQL files.** A new file
   `app/api.Tests/ApiFactory.cs`, namespace `HomebrewApp.Tests`, at the root of the test project:
   every feature's tests will use it, so it belongs to no feature folder. No test uses it yet, so
   no container starts in this step; the check is the build.

   **Read first (about 40 minutes).**
   - [xUnit — Sharing context between tests](https://xunit.net/docs/shared-context): "Constructor
     and Dispose" (only the note on `IAsyncLifetime`, and that v2 differs from v3), then "Collection
     Fixtures" in full. Look for who creates the fixture, how often, and how a test class gets it.
   - [Integration tests in ASP.NET Core, "Customize WebApplicationFactory"](https://learn.microsoft.com/aspnet/core/test/integration-tests?view=aspnetcore-10.0#customize-webapplicationfactory):
     point 1 only (inherit and override `ConfigureWebHost`).
   - [Testcontainers — Creating a container, "Copying directories or files to the container"](https://dotnet.testcontainers.org/api/create_docker_container/):
     the `WithResourceMapping` examples with `DirectoryPath.Of`.
   - [Testcontainers — Resource reaper](https://dotnet.testcontainers.org/api/resource_reaper/):
     the first two paragraphs (what Ryuk is).
   - C#: [Explicit interface implementation](https://learn.microsoft.com/dotnet/csharp/programming-guide/interfaces/explicit-interface-implementation)
     (the first example) and [`params`](https://learn.microsoft.com/dotnet/csharp/language-reference/keywords/method-parameters#params-modifier).

   **3a. The class.** `public class ApiFactory`, deriving from `WebApplicationFactory<Program>`
   (the class your health tests use today) and implementing xUnit's `IAsyncLifetime`: after the
   colon, the base class first, then a comma, then the interface.
   *Why:* one object that both owns the database and starts the API keeps the two in step: the
   API's connection string is known only once the container runs. A **fixture** is an object
   xUnit creates for tests and hands to them; this one is expensive (a container), so it is
   created once per run (3h) instead of once per test. `IAsyncLifetime` is how a fixture gets
   asynchronous set-up and clean-up (`InitializeAsync`, `DisposeAsync`): a constructor cannot
   `await`, and starting a container takes seconds.
   *Expected failure:* the build now says the class does not implement `InitializeAsync` and
   `DisposeAsync`; 3c and 3f add them.

   **3b. The container, as a `private readonly` field.** Of type `PostgreSqlContainer`, made by a
   chain of builder calls that starts with `new PostgreSqlBuilder(…)` with the image name and tag
   from the ticket and ends with `.Build()`. In between, three calls, each on its own line:
   - `WithUsername` with `"supabase_admin"`;
   - `WithCommand` with two strings, `"-c"` and `"config_file=/etc/postgresql/postgresql.conf"`;
   - `WithResourceMapping` with two `DirectoryPath.Of(…)` values (namespace
     `DotNet.Testcontainers.Builders`): the repo's `db` folder on your disk, and `"/db/"` inside
     the container. For the repo's folder, `CommonDirectoryPath.GetGitDirectory()` (same namespace)
     finds the repo root, the folder with `.git` in it, from where your test file lives; its
     `DirectoryPath` property is that folder as a string, and `Path.Combine` adds `db`.

   *Why:* the **builder pattern**: a long list of optional settings is set one call at a time, and
   `Build()` turns them into the finished object. Building it does not start anything yet; 3c
   does. Each call is there for a reason measured in the scratch run:
   - **The stack's image**, not `postgres:15`: `db/015_app.sql` creates `pg_jsonschema`, which
     only Supabase's image has (SYSTEM.md §12, 2026-10-31).
   - **`supabase_admin`:** the module sets the image's first user to `postgres` by default, but
     Supabase's own start-up scripts log in as `supabase_admin`, create `postgres` themselves and
     then take its superuser right away, exactly as in your stack. With the module's default the
     container stops during start-up.
   - **`config_file`:** the module replaces the image's start command (to switch off disk syncing,
     which makes a throwaway database faster) and with it the image's `-D /etc/postgresql`, so
     Postgres starts without Supabase's configuration. That configuration loads `supautils`, the
     extension that lets the non-superuser `postgres` create `pg_jsonschema`. Giving the config
     file back with `-c` keeps the module's speed settings and Supabase's configuration.
   - **The whole `db/` folder**, copied into the container before it starts: 624 KB, and it means
     the list of files to run lives in one place only, in 3e (AC4), not also here.
   - **`GetGitDirectory`** instead of a path you type: it works from any folder `dotnet test` is
     started in, and on any clone of the repo.

   *Watch out:* the docs' older overload of `WithResourceMapping` takes a `DirectoryInfo` and a
   string. It still compiles, with (measured) *warning CS0618: '…WithResourceMapping(DirectoryInfo,
   string, uint, uint, UnixFileModes)' is obsolete: 'Use WithResourceMapping(DirectoryPath,
   DirectoryPath, UnixFileModes) instead.'*, and the hook builds with `-warnaserror`, so the
   commit is refused. Use the `DirectoryPath` one.

   **3c. `InitializeAsync`.** `public async Task InitializeAsync()`. For now its body is one
   line: await the container's `StartAsync()`. 3e adds the SQL files below it.
   *Why:* xUnit calls it once, before the first test that uses the fixture, and waits for it.
   `StartAsync` returns when the module's readiness check passes (it runs `pg_isready` inside the
   container every second, about three times in the scratch run). The container gets a random
   free port on `127.0.0.1`, never 5432, so it cannot collide with the pooler of your stack
   (AC1).

   **3d. A helper that runs one SQL file with `psql`.** A private method with this signature:
   `private async Task RunSqlFileAsync(string pathInContainer, params string[] variables)`.
   Its body, in words: make a list of strings that starts with the `psql` command and its options
   (`-U postgres`, `-d postgres`, `-v ON_ERROR_STOP=1`, `-f` and the path), add `-v` and the
   variable for each entry of `variables`, run the list with the container's `ExecAsync`, and if
   the result's `ExitCode` is not 0, throw an `InvalidOperationException` whose message holds the
   file name and the result's `Stderr`.
   *Why:*
   - **Inside the container**, with `ExecAsync`: `psql` is there (the test machine needs no
     Postgres client), and `060` needs it, because `:'app_api_password'` is a `psql` variable
     (a1-03 lesson step 3c); a plain `NpgsqlCommand` would send the colon to the server as SQL.
   - **As `postgres`**, not `supabase_admin`: CLAUDE.md's rule, so the tables get the same owner
     as in the stack, and so a file that only works as a superuser fails here too, before it
     fails on the stack.
   - **A list of separate strings**, not one command line: `ExecAsync` runs the program directly,
     without a shell, so a value with spaces or quotes (the JSON in step 5) arrives as one
     argument and needs no escaping.
   - **`ON_ERROR_STOP` and the exit code check.** Without `ON_ERROR_STOP`, `psql` prints an error,
     goes on with the next statement and exits with 0. Measured with the files in the wrong order
     and no `ON_ERROR_STOP`: set-up "succeeded", and the tests failed later with *42P01: relation
     "app.recipe" does not exist*, far from the cause. With both, the run stops at the cause:
     *InvalidOperationException : /db/015_app.sql failed (3): psql:/db/015_app.sql:36: ERROR:
     schema "ref" does not exist*. This is **failing fast** again (a1-03 step 9a).
   - **`params string[]`** lets a caller pass zero, one or more variables as plain arguments:
     `RunSqlFileAsync("/db/015_app.sql")` or with one `"name=value"` string after the path.

   **3e. The list of SQL files (AC4).** In `InitializeAsync`, after `StartAsync`, one
   `await RunSqlFileAsync(…)` per file, in the order they must run, each with a `//` comment
   above it saying what the API needs from that file. The last one is
   `/db/060_app_api_role.sql`, with the variable `app_api_password=` followed by a password you
   keep in a `private const string` in the class.
   *Why:* which files? Work it out from their `Needs` lines (the ticket asks you to): start at
   `060`'s header, read the `Needs` line of every file it names, and so on until a file needs
   nothing. Then check the answer: `grep -n "create table\|add column" db/*.sql | grep
   "app.recipe\b\|app.recipe_item\|ref.ingredient \|ref.beer_style"` shows every file that
   creates one of the four tables or adds a column to it; every column your entity classes map
   (`app/api/Data/`) must come from a file in your list. A later file that only adds columns you
   don't map (there are two) is not needed today; a1-05 adds its own file to this list. The
   comments are what makes the list readable in a year: "why is `015` here?" is answered on the
   line above it.
   The password is a made-up literal, and that is fine here: the container lives for a few
   seconds, only on `127.0.0.1`, and holds no real data. It is not your `app_api` password and
   must not look like one (AC5 of a1-03 still holds).
   *Watch out:* the order matters. `015` before `010` stops with the *schema "ref" does not exist*
   error above.

   **3f. `DisposeAsync`, as an explicit interface implementation.** No access modifier; the
   return type `Task`, then `IAsyncLifetime.DisposeAsync()` as the name. Its body awaits the
   container's `DisposeAsync()`, then `base.DisposeAsync()` (the factory's own clean-up, which
   stops the API).
   *Why:* `WebApplicationFactory` already has a public `DisposeAsync` that returns a `ValueTask`,
   and xUnit v2's `IAsyncLifetime` wants one that returns a `Task`. Two methods cannot differ only
   by return type, so a public `DisposeAsync` here builds with (measured) *warning CS0114:
   'ApiFactory.DisposeAsync()' hides inherited member 'WebApplicationFactory<Program>.DisposeAsync()'.
   To make the current member override that implementation, add the override keyword. Otherwise
   add the new keyword.*, which the hook refuses. Neither suggestion is right: writing the
   interface's name before the method name makes it the interface's own method, which xUnit
   calls, while the factory's public one stays as it is. Disposing the container is what deletes
   it (AC1). If the test process is killed before that, Testcontainers' second safety net, a small
   container called Ryuk, deletes it a few seconds later.

   **3g. The connection string as `app_api`.** A public read-only property
   `AppApiConnectionString`, a `string`, written as an expression-bodied property (`=>`, met in
   a1-03 step 8b). It makes a new `NpgsqlConnectionStringBuilder` (namespace `Npgsql`, which the
   test project already has through the API project) from the container's
   `GetConnectionString()`, sets `Username` to `app_api` and `Password` to your constant in an
   **object initializer** (curly braces after the constructor call, with `Name = value,` pairs),
   and returns its `ConnectionString`.
   *Why:* the container's own connection string has the right host and the random port, but logs
   in as `supabase_admin`, a superuser: a test that used it would pass every permission check.
   Changing only the user and password keeps the host and port Testcontainers chose. A builder is
   safer than gluing strings: it knows the key names and quotes values that need it.
   Docs: [`NpgsqlConnectionStringBuilder`](https://www.npgsql.org/doc/api/Npgsql.NpgsqlConnectionStringBuilder.html) ·
   [object initializers](https://learn.microsoft.com/dotnet/csharp/programming-guide/classes-and-structs/object-and-collection-initializers).
   *Watch out:* the property can be read only after `StartAsync`: before that the container has no
   port, and reading it throws. Tests read it after `InitializeAsync`, so this never happens in a
   test.

   **3h. Point the API at the container.** Override `ConfigureWebHost`:
   `protected override void ConfigureWebHost(IWebHostBuilder builder)`, with one call in its body:
   `UseSetting` with `"ConnectionStrings:App"` and `AppApiConnectionString`.
   *Why:* this is a1-03's test lesson step 1b moved into the factory, so every test gets it
   without repeating it. `UseSetting` reaches the app before `Program.cs` reads the connection
   string; `ConfigureAppConfiguration` would silently be too late (measured in a1-03). The
   factory calls this when the first client is created, which is after `InitializeAsync`, so
   the port is known. Your "database down" test keeps working: its own `WithWebHostBuilder`
   setting comes after this one and wins (measured).

   **3i. The collection.** A second new file, `app/api.Tests/ApiCollection.cs`: a class
   `ApiCollection` that implements `ICollectionFixture<ApiFactory>` and has no body (a semicolon
   instead of braces), with the attribute `[CollectionDefinition(nameof(ApiCollection))]` above
   it.
   *Why:* a **collection fixture** is created once and shared by every test class that joins the
   collection, so one container serves the whole run instead of one per class. The definition
   class is never created; it only carries the attribute and the interface (the xUnit page's
   `DatabaseCollection`). `nameof(ApiCollection)` instead of a typed string: a test class joins
   with the same `nameof`, so a typo is a build error instead of a test that silently starts a
   fixture of its own. xUnit runs the tests of one collection one after another, which is what you
   want with one shared database.

   *Check yourself (whole step):* `dotnet build` in `app/` ends with `0 Warning(s)` and
   `0 Error(s)`. `dotnet test` still passes the two health tests, against your stack as before:
   nothing uses the factory yet.
   **Commit:** `git add app/api.Tests/ApiFactory.cs app/api.Tests/ApiCollection.cs`, message
   `Add ApiFactory with a throwaway Postgres`.

4. **Move the health tests onto the container and test `database: ok` (AC3).** In
   `app/api.Tests/Features/Health/HealthEndpointsTests.cs`.

   **4a. Join the collection.** Replace the class's `IClassFixture<WebApplicationFactory<Program>>`
   with the attribute `[Collection(nameof(ApiCollection))]` above the class, and change the
   primary constructor's parameter type to `ApiFactory`. Remove the `using` lines that are no
   longer needed (Rider greys them out).
   *Why:* the class now gets the shared factory from the collection instead of making its own
   plain one, so its requests reach an API that talks to the container. That is the "your stack is
   untouched" half of AC1: before this step, this class connected to your stack.
   *Watch out:* forget the attribute and every test in the class fails with (measured) *The
   following constructor parameters did not have matching fixture data: ApiFactory factory*.

   **4b. The first test checks the database too.** Rename it after the case it covers, as in
   a1-03 (`HealthEndpoint_DatabaseReachable_ReturnsOkWithDatabaseOk`, the mirror of the `down`
   test), and add a second assertion: the JSON property `database` is `"ok"`.
   *Why:* AC3 is "the API reaches the container's database as `app_api`": the connection string
   from the factory, the role's login and the password all have to work for `"ok"`. One test
   checks the two properties of one answer, like the `down` test.
   **See it fail first.** In `ApiFactory`'s `ConfigureWebHost`, add one character to the
   password (append `+ "x"` after `AppApiConnectionString`) and run `dotnet test`. The renamed test
   fails with (measured) *Assert.Equal() Failure: Strings differ · Expected: "ok" · Actual:
   "down"*. This proves the `ok` comes from the container through your factory, not from luck.
   Undo it exactly.

   *Check yourself:* `dotnet test` passes 2 tests, and the output shows no `InvalidOperationException`
   from the fixture. Run `docker ps` in a second terminal while the tests run: a
   `supabase/postgres:15.8.1.085` container with a random name and a `testcontainers-ryuk-…` one
   appear and are gone again afterwards. The first run is the slowest; after that about 5–6 s.
   **Commit:** `git add app/api.Tests/Features/Health/HealthEndpointsTests.cs`, message
   `Run the health tests against the test database`.

5. **Seed two recipes.** Test data in a new folder `app/api.Tests/TestData/`.

   **5a. Save recipe 1155's process as a file.** From the repo root:
   `docker exec -i supabase-db psql -X -U postgres -d postgres -At -c "select process from app.recipe where id = 1155" > app/api.Tests/TestData/recipe-1155-process.json`.
   *Why:* `-A` (unaligned) and `-t` (tuples only) print the bare value, with no header or
   padding, so the file is exactly the stored JSON (7770 bytes, one line). A real saved process,
   not a hand-made one, because a1-08's generator must cope with what the pipeline really writes.
   Keeping it in a file, not inside the SQL, keeps `seed.sql` readable and lets a1-08's unit tests
   read the same file.
   *Watch out:* the JSON still holds the stack's ingredient ids (`"ingredient_id": 472`). They
   will not match the ids your seed gets, and nothing joins on them today; the generator copies
   names and numbers (SYSTEM.md §7).

   **5b. Write `app/api.Tests/TestData/seed.sql`.** Plain `insert` statements, in this order,
   because each row needs the ones before it:
   1. one `ref.source` row (only `slug` is required);
   2. one `ref.beer_style` (recipe 1155's: guide `BA`, its code and name);
   3. one `ref.ingredient` per ingredient of 1155 (six: two malts, three hops, one yeast, with
      their `kind`, `name` and `producer`; `name_key` and `producer_key` in lower case);
   4. one `app.brief`;
   5. two `app.recipe` rows: the first with 1155's numbers and `process` set to `:'process'`, the
      second the same without a `process`;
   6. the first recipe's six `app.recipe_item` rows, copied from 1155; the second recipe gets a
      few items too (the ticket: "with their items").

   Look up the values with read-only queries on the stack (`docker exec -i supabase-db psql -X -U
   postgres -d postgres -c "…"`): `app.recipe` and `app.recipe_item` where the recipe id is 1155,
   and `ref.ingredient` and `ref.beer_style` by the ids they point to. `\d <table>` shows which
   columns are `not null`; give those a value and leave the rest out.
   For every foreign key, use a subquery by a natural key instead of a number:
   `style_id` is `(select id from ref.beer_style where code = '…')`, and so on.
   *Why:* the tables' ids are `generated always as identity`: Postgres picks them, and an insert
   that names an id is refused. Subqueries by name say what they point to and do not depend on
   which number Postgres picked. `:'process'` is the same `psql` variable syntax as the password
   in `060`; step 5c passes the file's text in. `raw` (`not null`) can be `'{}'`: nothing reads
   it. Small and visible test data is a **test pattern**: anyone reading a test can open this one
   file and see what the database holds.
   *Watch out:* the seed runs only in the container, never on the stack. Don't run it with the
   apply line from OPERATIONS.md.

   **5c. Apply it.** Map the `TestData` folder into the container like `db/` (a second
   `WithResourceMapping`, to `"/seed/"`; `CommonDirectoryPath.GetProjectDirectory()` finds the test
   project's folder). At the end of `InitializeAsync`, read the JSON file into a string with
   `File.ReadAllTextAsync` and run `/seed/seed.sql` with the variable `process=` followed by that
   string.
   *Why:* after `060`, so the role exists; the order of the seed and the role does not matter for
   the grants (a `grant select` on a table covers rows inserted later), but data last is the
   usual order. Passing 7.7 KB as one argument works (measured): Linux allows 128 KB per
   argument, and `ExecAsync` does no shell quoting (3d).
   *Check yourself:* `dotnet test` passes. Then break the seed once: misspell one column name.
   Every test fails with (measured, with `efficiency` for `efficiency_pct`)
   *InvalidOperationException : /seed/seed.sql failed (3): psql:/seed/seed.sql:8: ERROR: column
   "efficiency" of relation "recipe" does not exist*. Undo it.
   **Commit:** `git add app/api.Tests/TestData/ app/api.Tests/ApiFactory.cs`, message
   `Seed two recipes in the test database`.

6. **Test the role (AC2).** A new file `app/api.Tests/Database/AppApiRoleTests.cs`, namespace
   `HomebrewApp.Tests.Database`: the folder is named after what it tests (`db/060`), as
   `Features/Health/` is.

   **Read first (about 15 minutes).**
   - [Npgsql — Basic usage](https://www.npgsql.org/doc/basic-usage.html): "Connecting",
     "Executing a command" and "Getting a single value" (look for `ExecuteScalarAsync`).
   - [C# — the `using` statement](https://learn.microsoft.com/dotnet/csharp/language-reference/statements/using):
     the `await using` form.
   - [`PostgresErrorCodes`](https://www.npgsql.org/doc/api/Npgsql.PostgresErrorCodes.html) and
     [PostgreSQL 15 — Error codes](https://www.postgresql.org/docs/15/errcodes-appendix.html):
     find `42501`.

   **6a. The class.** `public class AppApiRoleTests`, in the collection like the health tests,
   with a primary constructor taking the `ApiFactory`.
   *Why:* these tests do not call the API (it has no endpoint that writes, and the point is what
   the **role** allows, whatever the API's code does), so they use only the factory's
   `AppApiConnectionString`. Being in the collection still matters: it is what starts the
   container and seeds it.

   **6b. Reading is allowed.** A `[Fact]`, `public async Task`, named like
   `AppApi_SelectRecipes_ReturnsSeededRows`. Arrange: a new `NpgsqlConnection` with the
   factory's connection string, declared with `await using`, then `OpenAsync()`. Act: an
   `NpgsqlCommand` (also `await using`) that counts the rows of `app.recipe`, run with
   `ExecuteScalarAsync()`. Assert: the result equals `2L`.
   *Why:* `await using` closes the connection when the test ends, even when an assertion fails,
   so a failed test leaves no open connection behind. `count(*)` returns a Postgres `bigint`, which
   arrives as a C# `long` in an `object`; the `L` makes the expected value a `long` too. Two is
   the seed's number (a literal, a0-02's pattern). It also proves the test reads the container:
   your stack has 93.
   *Watch out:* with `2` instead of `2L` the test fails with the confusing (measured)
   *Assert.Equal() Failure: Values differ · Expected: 2 · Actual: 2*: a boxed `int` 2 is not
   equal to a boxed `long` 2.

   **6c. Updating is refused.** A second `[Fact]`, named like
   `AppApi_UpdateRecipe_IsRefused`. The same connection; the command is the safe update from
   a1-03's lesson step 4 (`status` set to itself `where false`). Assert with
   `Assert.ThrowsAsync<PostgresException>`, passing a lambda that runs the command's
   `ExecuteNonQueryAsync()`; it returns the exception. Then assert that its `SqlState` equals
   `PostgresErrorCodes.InsufficientPrivilege`.
   *Why:* `ThrowsAsync` fails the test when nothing is thrown, which is exactly what a wrong grant
   looks like. Checking `SqlState` (the five-character error code, `42501`) proves it is a
   **permission** error: a typo in the table name also throws a `PostgresException`, but with
   `42P01`, and the test would pass for the wrong reason. The message, for comparison, is
   (measured) *42501: permission denied for table recipe*. The named constant reads better than
   `"42501"` and cannot be mistyped.

   **See both fail first.** In the working tree, change the `select` grant in
   `db/060_app_api_role.sql` (the container copies the file at every run):
   - add `update` next to `select`: `AppApi_UpdateRecipe_IsRefused` fails with (measured)
     *Assert.Throws() Failure: No exception was thrown · Expected: typeof(Npgsql.PostgresException)*;
   - instead, take `app.recipe` out of the grant: `AppApi_SelectRecipes_ReturnsSeededRows` fails
     with (measured) *Npgsql.PostgresException : 42501: permission denied for table recipe*.

   Undo it exactly, and check `git diff db/` is empty. This is what the test review will repeat.
   *Watch out:* this edit is for the test run only. Never run `060`'s apply line against the stack
   while the file is changed.

   *Check yourself:* `dotnet test` passes 4 tests.
   **Commit:** `git add app/api.Tests/Database/AppApiRoleTests.cs`, message
   `Test what the app_api role may do`.

7. **Check AC1 by hand.** With your stack running:
   - before the run, note `docker exec -i supabase-db psql -X -U postgres -d postgres -Atc "select count(*) from app.recipe"`
     (93 on 2026-11-18);
   - run `dotnet test` in `app/`;
   - 15 seconds later, `docker ps -a --filter label=org.testcontainers=true` lists nothing (the
     database container goes at the end of the run, Ryuk a few seconds after it; measured);
   - the count is unchanged, and `docker ps` shows your stack's containers as before.

   *Why:* AC1 has three parts, and only "it runs" is visible in the test output. The filter finds
   containers Testcontainers made, by the label it puts on all of them.
   No commit.

8. **Update `app/README.md`.** Two changes: in "Run the API", the sentence saying `dotnet test`
   stops without the user secret is no longer true; and next to the pre-commit table (or in a
   short "API tests" paragraph), say that the API tests need Docker running, start a throwaway
   `supabase/postgres:15.8.1.085` container (the image the stack already pulled), and never touch
   the stack.
   *Why:* a0-02's rule for the README: someone who has never seen the project can follow it.
   Every commit now runs a container through the hook, so "Docker must be running" is the first
   thing a failed commit needs to tell you.
   *Check yourself:* read both changes against what steps 4–7 showed you.
   **Commit:** `git add app/README.md`, message `Say the API tests need Docker`.

## Files you will touch

- `app/api.Tests/HomebrewApp.Tests.csproj`: the `Testcontainers.PostgreSql` package (step 2).
- `app/api.Tests/ApiFactory.cs`: new; the container, the SQL file list, the seed, the `app_api`
  connection string and the API's configuration.
- `app/api.Tests/ApiCollection.cs`: new; the collection definition.
- `app/api.Tests/Features/Health/HealthEndpointsTests.cs`: joins the collection; the first test
  checks `database: ok`.
- `app/api.Tests/TestData/recipe-1155-process.json`: new; recipe 1155's process.
- `app/api.Tests/TestData/seed.sql`: new; source, style, ingredients, brief, two recipes, items.
- `app/api.Tests/Database/AppApiRoleTests.cs`: new; read allowed, update refused.
- `app/README.md`: the tests need Docker, not the user secret.
- `db/060_app_api_role.sql`: changed briefly in step 6, and back to unchanged.

## Before you ask for a review

- [ ] `dotnet build` in `app/` reports 0 warnings and 0 errors; `dotnet test` passes 4 tests.
- [ ] The fixture lists its SQL files in one place, in order, with a comment on each (AC4), and
      you can say why no later `db/` file is in the list.
- [ ] Step 4's broken password made the health test say `"down"`, and step 6's two grant changes
      made the two role tests fail as described; `git diff db/` is empty afterwards (AC2, AC3).
- [ ] After a run, `docker ps -a --filter label=org.testcontainers=true` is empty and the stack's
      recipe count is unchanged (AC1).
- [ ] No real password in any file: the test password is a made-up literal, and the connection
      strings come from the container.
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted.
- [ ] Ask yourself: a1-05 adds `db/061_app_batch.sql` with the batch tables and their grants to
      `app_api`. Where in the fixture does it go, before or after `060`, and why?
