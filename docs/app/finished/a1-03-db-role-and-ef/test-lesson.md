# Test lesson: a1-03 · The API's database role and EF Core

## What you will test

| Behaviour | AC | Level | Why this level |
|---|---|---|---|
| When the database cannot be reached, `GET /api/health` still answers `200` with `status` `"ok"` and `database` `"down"` | AC4, second half | API integration: a real request through the in-memory test server, as in a0-02 | The behaviour is the HTTP answer of the whole app: the connection string from configuration, the registered `AppDbContext`, the handler and the JSON names. Only a request through the full pipeline proves them together |

The status code, `status` and `database` belong to one behaviour ("the API stays up and says the
database is down"), so one test checks all three.

The test makes the database unreachable on purpose by giving the app a connection string that
points nowhere. It needs no database, no password and no user secrets for its answer, so it
gives the same result on any machine, including one where the stack isn't running.

What not to test, and why:

- **The `database: ok` case.** It needs a real database with the `app_api` role and its
  password, which is what a1-04's test database is for. You checked it by hand (AC4, first half,
  review round 1). The existing test also connects to your real database today: the tests run in
  `Development`, so they read your user secrets (lesson step 9).
- **The role and its grants (AC1–AC3).** These are database facts. The review checked them with
  catalog queries, and tests against a database come with a1-04.
- **The fail-fast exception at start-up.** It is one `??` line, and the review saw its message.
  A test would mostly test that `throw` throws.
- **That `CanConnectAsync` catches connection errors.** That is EF Core's documented behaviour.
  Your test sees it anyway, through the `"down"` in the answer.
- **The entity mapping.** It is proved by queries that read rows, which arrive with a1-06's first
  endpoint and a1-04's test database.

## Steps

1. **Test the `down` answer with an unreachable connection string**, as a second test in
   `app/api.Tests/Features/Health/HealthEndpointsTests.cs`.

   **Read first (about 15 minutes).**
   - [Integration tests in ASP.NET Core (xUnit)](https://learn.microsoft.com/aspnet/core/test/integration-tests?view=aspnetcore-10.0&pivots=xunit):
     "Customize the client with WithWebHostBuilder", and in "Customize the `WebApplicationFactory`
     with test configurations", point 2's last sentence (configuration added that way "will not be
     available" before `Build`).
   - [`IWebHostBuilder.UseSetting`](https://learn.microsoft.com/dotnet/api/microsoft.aspnetcore.hosting.iwebhostbuilder.usesetting):
     the one-line summary.
   - Your own a0-02 test lesson, "Reading the JSON answer" and "Patterns"
     (`docs/app/finished/a0-02-api-skeleton/test-lesson.md`): the test reads JSON the same way
     and follows the same patterns.

   **1a. The test method.** In the same class, below the existing test: a `[Fact]`, `public async
   Task`, with a name in the `Request_Condition_Expectation` shape that says what happens when the
   database is unreachable, for example `HealthEndpoint_DatabaseUnreachable_ReturnsOkWithDatabaseDown`.
   *Why:* same class, because it tests the same endpoint and shares the class fixture's factory
   (a0-02). The name carries the condition, because two tests of one endpoint differ by exactly
   that, and a failing name alone should tell you which case broke.

   **1b. Arrange: a client whose app has a different connection string.** Call
   `factory.WithWebHostBuilder(…)` with a lambda that receives the web host builder and calls
   `UseSetting` on it with two strings: the key `"ConnectionStrings:App"` and an unreachable
   connection string. Then call `CreateClient()` on the factory it returns. The connection string is
   a literal in the test, written like your user secret but pointing nowhere: host `127.0.0.1`,
   port `1`, database `postgres`, and a made-up user name and password such as `nobody` and
   `none`.
   *Why:*
   - **`WithWebHostBuilder`** makes a new factory from the class fixture's one, with your extra
     configuration on top. It starts its own copy of the app, so the existing test keeps the
     normal app.
   - **`UseSetting`** adds or replaces one configuration value. A setting given this way reaches
     the app before `Program.cs` runs, so `GetConnectionString("App")` at its top already sees the
     test's value instead of your user secret. (Measured in a scratch copy of your API: the
     override wins over the user secret, and the test also passes with the app in `Production`,
     where no user secrets are read at all.)
   - **Port 1 on `127.0.0.1`:** nothing listens there (a normal program can't even open a port
     below 1024 without root), so the connection is refused at once instead of waiting for a
     timeout. In the scratch run the request took about 5 ms. `127.0.0.1` is your own machine, so
     nothing goes out on the network, and the made-up user name and password keep every secret
     out of the test file (AC5).
   - **Not an environment variable** as in lesson step 11: environment variables belong to the
     whole test process, so one test would change the configuration of every other test that
     starts while it runs. A setting on the factory affects only that one app.

   *Watch out:* the docs show a second way, `ConfigureAppConfiguration` with an in-memory
   collection. Here it **silently has no effect**: it is added only after `Build()`, but your
   `Program.cs` reads the connection string before that. Measured in the scratch copy: with
   `ConfigureAppConfiguration` the app still used your user secret, and the test failed with
   *Assert.Equal() Failure: Strings differ · Expected: "down" · Actual: "ok"*. On a machine
   without a running database it would have **passed**, for the wrong reason. That is why step 1d
   breaks the test on purpose.

   **1c. Act.** One `GetAsync` of `/api/health` on that client, as in the first test.

   **1d. Assert.** Three checks on the one answer: the status code is `HttpStatusCode.OK`; the JSON
   property `status` is `"ok"`; the JSON property `database` is `"down"`. Read the body with
   `JsonDocument` and `GetProperty`, as in the first test, so the key names are checked exactly as
   the web page reads them (lower case).
   *Why:* `200` plus `status: "ok"` is the "API still answers" half of AC4; `database: "down"` is
   the other half. Expected values are literals (a0-02's pattern), never taken from the API's code.
   The two tests now share the reading of the JSON body. Two copies are fine; extract a helper
   only when a third test needs it, so each test still reads from top to bottom on its own.

   *Check yourself:*
   - `dotnet test` in `app/`: `Passed! - Failed: 0, Passed: 2`.
   - **Break the setup:** replace the `WithWebHostBuilder(…)` client with a plain
     `factory.CreateClient()` and run the tests. With your stack running, the new test fails with
     *Assert.Equal() Failure: Strings differ*, *Expected: "down"*, *Actual: "ok"*: without the
     override, the app reaches your real database. This shows the `down` comes from the test's
     connection string, not from luck. Put it back.
   - **Break the code:** in `HealthEndpoints.cs`, make the handler always answer `"ok"` for
     `Database` (replace the `? :` with `"ok"`). The new test fails with the same message (measured
     in the scratch copy). Undo it exactly, and check with `git diff app/api` that nothing in the
     API changed.
   - Run `dotnet test` once more: 2 passed.

   **Commit:** `git add app/api.Tests/Features/Health/HealthEndpointsTests.cs`, message
   `Test the health check with the database down`.

## Before you ask for a test review

- [ ] `dotnet build` in `app/` has 0 warnings and `dotnet test` passes with 2 tests.
- [ ] Both breaks in step 1 made the new test fail with *Expected: "down"*, *Actual: "ok"*, and
      `git diff app/api` is empty afterwards.
- [ ] The test file holds no real password or tenant id: the connection string is the made-up one
      on port 1 (AC5).
- [ ] The test is named after the behaviour, follows arrange-act-assert with blank lines between
      the three parts, and makes exactly one request.
- [ ] Every step is committed: `git status` shows nothing of this ticket left uncommitted.
- [ ] Ask yourself: why would the test pass on a machine with no database even if the override
      were missing, and which check in step 1 protects you from that?
