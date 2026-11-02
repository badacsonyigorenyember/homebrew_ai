# Review: a0-02 · API skeleton

## Round 1 · 2026-11-02 · ce0b1d3

Reviewed: everything on `a0-02-api-skeleton` against `main`: `app/.gitignore`,
`app/HomebrewApp.slnx`, all of `app/api/`, read in full. Also the uncommitted "Run the API" section
in `app/README.md`, which Claude wrote at your request in this session (so it isn't judged as your
work, only checked against what runs).

Checks: `dotnet build --no-incremental` in `app/`: ok, 0 warnings, 0 errors · `dotnet test`: no
test project yet (comes with the test lesson) · `dotnet run --project api`: listens on
`http://localhost:5080`, environment `Development` · csharp-ls resolves `app.Map()` in
`Program.cs` to your extension method, no errors · `git ls-files app`: no `bin/` or `obj/`, and
`app/.idea/` stays ignored by the root `.gitignore` · skill `dotnet-aspnetcore:dotnet-webapi` not
needed beyond the minimal-API docs linked below, as there is one endpoint.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `curl -i http://localhost:5080/api/health`: `HTTP/1.1 200 OK`, `Content-Type: application/json; charset=utf-8`, body `{"status":"ok"}` |
| AC2 | yes | `/openapi/v1.json` (OpenAPI 3.1.1): `paths./api/health.get.responses.200` refers to `#/components/schemas/HealthResponse`, an object with a required `status` string. `/weatherforecast` is gone |
| AC3 | yes | `dotnet build --no-incremental`: `0 Warning(s)`, `0 Error(s)` |
| AC4 | yes | `Program.cs` has builder, `AddOpenApi()`, `Build()`, Development-only `MapOpenApi()`, one feature call, `Run()`. No `MapGet`, no lambda |

Nothing outside the ticket was built.

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | should fix | `app/api/Features/Health/Health.cs:9`, `app/api/Program.cs:17` | The feature's map method is called `Map`. In `Program.cs` the line reads `app.Map();`, which doesn't say which feature it maps, and ASP.NET Core already has its own `Map(...)` methods on the same builder. Checked in a scratch copy: adding a second feature (`Batches`) with the same `Map` name and its `using` makes `Program.cs` fail with `CS0121: The call is ambiguous between … Health.Map(…) and … Batches.Map(…)`. Give the method a name that carries the feature (the `Map<Feature>` shape the lesson used, e.g. `MapHealth`). | `Program.cs` is meant to be a table of contents. With one generic name per feature it can't be read, and the second feature (a1-06) won't compile. | [Extension methods: binding at compile time](https://learn.microsoft.com/dotnet/csharp/programming-guide/classes-and-structs/extension-methods#binding-extension-members-at-compile-time) · [CS0121](https://learn.microsoft.com/dotnet/csharp/misc/cs0121) |
| 2 | Standards | should fix | `app/api/Features/Health/Health.cs:3, 7` | The class `Health` sits in the namespace `HomebrewApp.Features.Health`: a type with the same name as its own namespace. .NET's design guidelines say not to do this, because code outside the namespace (your test project in the next step, for one) has to fully qualify the type when `Health` could mean either. A name that says what the class holds, such as `HealthEndpoints`, avoids it and is a pattern every feature folder can copy. After renaming, check the OpenAPI `tags` entry: it is `Health` now and seems to come from the class name, so the rename may change it; `WithTags` sets it explicitly if you want to keep `Health`. | Every feature will repeat this layout (`Features/Batches/…`), so the naming choice is made once for all of them. | [Names of namespaces](https://learn.microsoft.com/dotnet/standard/design-guidelines/names-of-namespaces) ("DO NOT use the same name for a namespace and a type in that namespace") · [CA1724](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1724) · [WithTags](https://learn.microsoft.com/aspnet/core/fundamentals/openapi/include-metadata?view=aspnetcore-10.0#tags) |
| 3 | Standards | nice to have | `app/api/HomebrewApp.http:3` | The request calls `/api/health/` with a trailing slash. It works (it answers 200), but the endpoint, the OpenAPI document and the README all say `/api/health`. | The `.http` file is a small piece of documentation; it should show the exact path. | — |
| 4 | Standards | nice to have | `app/api/Program.cs:19`, `app/api/Features/Health/Health.cs:20` | Both files end without a final newline (the same thing came up in a0-01). Rider can add it on save: Settings → Editor → General → "Ensure every saved file ends with a line break". | Without it, the next line added at the end shows the old last line as changed too. | — |

Done well:

- `TypedResults.Ok` with a named record (`HealthResponse`) gives AC2 for free: OpenAPI has a named,
  reusable schema with `status` marked required. That is what a2-02 will turn into a TypeScript type.
- The handler is a named `private static` method, mapped by a method group rather than a lambda,
  and `Program.cs` lost the whole weather sample. The template comments you kept are still true.
- You ran `dotnet new gitignore` before the first build and created the project with `--no-https`,
  so the branch has no build output and only the one port the ticket asks for.

Verdict: ready for tests. Findings 1 and 2 are best fixed before you write the test, since they
rename what the test project will see; say "tests" when you want the test lesson.

## Round 2 · 2026-11-02 · bc68e62

Reviewed: `2bb0cc4 rename class and methods`, `bc68e62 remove tailing slash to match README`, and
`a1b53d4`, which commits the README section from round 1. Read in full: `Program.cs`,
`Features/Health/HealthEndpoints.cs`, `HomebrewApp.http`.

Checks: `dotnet build --no-incremental` in `app/`: ok, 0 warnings, 0 errors · `dotnet run
--project api`: listens on `http://localhost:5080`, environment `Development` · all three changed
files end with a newline · `dotnet test`: no test project yet.

Round 1 findings:

| # | Status |
|---|---|
| 1 | fixed: `MapHealthEndpoint`, so `Program.cs` reads `app.MapHealthEndpoint();` and a second feature's map method no longer clashes |
| 2 | fixed: the class is `HealthEndpoints` (file renamed to match), so it no longer shares its namespace's name |
| 3 | fixed: the `.http` request calls `/api/health` |
| 4 | fixed: final newlines in `Program.cs` and `HealthEndpoints.cs` |

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `curl -i http://localhost:5080/api/health`: `HTTP/1.1 200 OK`, body `{"status":"ok"}` |
| AC2 | yes | `/openapi/v1.json`: `/api/health` `get` 200 refers to `#/components/schemas/HealthResponse` |
| AC3 | yes | `0 Warning(s)`, `0 Error(s)` |
| AC4 | yes | `Program.cs`: setup, Development-only `MapOpenApi()`, `app.MapHealthEndpoint();`, `Run()` |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 5 | Standards | nice to have | `app/api/Features/Health/HealthEndpoints.cs:11` | As round 1 guessed, the OpenAPI tag followed the class name: `/openapi/v1.json` now lists the endpoint under the tag `HealthEndpoints`. If you'd rather the document group it as `Health`, `WithTags` on the mapped endpoint sets that. | Tags are how OpenAPI viewers group endpoints. It changes nothing at runtime. | [Tags](https://learn.microsoft.com/aspnet/core/fundamentals/openapi/include-metadata?view=aspnetcore-10.0#tags) |

Done well:

- You renamed the file with the class, so `HealthEndpoints.cs` holds `HealthEndpoints`. That's what
  you'll look for when the folder gets a second file.
- Each fix is its own small commit with a message that says what changed.

Verdict: ready for tests

# Test review

## Round 1 · 2026-11-02 · 7c7929d

Reviewed: `3523ed9 init tests project` and `7c7929d add healthcheck test`: `app/HomebrewApp.slnx`,
`app/api.Tests/HomebrewApp.Tests.csproj`, `app/api.Tests/Features/Health/HealthEndpointTests.cs`,
read in full.

Checks: `dotnet build --no-incremental` in `app/`: ok, 0 warnings, 0 errors · `dotnet test`:
`Passed! - Failed: 0, Passed: 1` · `Program.cs` unchanged (no `public partial class Program`) ·
no `bin/` or `obj/` tracked · `dotnet nuget why … Newtonsoft.Json`: only through
`Microsoft.NET.Test.Sdk` → `Microsoft.TestPlatform.TestHost` → `Newtonsoft.Json` 13.0.3.

Break-the-code check, one change at a time in `app/api/Features/Health/HealthEndpoints.cs`, the
file copied first and copied back after each run; `git diff` on it was empty again at the end:

| # | Break | Test result | Should it fail? |
|---|---|---|---|
| B1 | handler returns `"okay"` instead of `"ok"` | failed: `Assert.Equal() Failure: Strings differ`, expected `"ok"`, actual `"okay"` | yes, and the message says exactly what broke |
| B2 | route changed to `/api/healthz` | failed: `Assert.NotNull() Failure: Value is null` | yes, but the message hides the cause (a 404) |
| B3 | JSON key written as `"Status"` (a `JsonPropertyName("Status")` on the record) | **passed** | yes: AC1 promises `{"status":"ok"}` |
| B4 | answer is status 202 with the same body | **passed** | yes: AC1 and the ticket's `## Tests` ask for 200 |

| Test | Behaviour | Would it fail? | Needed? | Reliable? |
|---|---|---|---|---|
| `HealthCheckTest` | half of AC1: checks the value, not the status code or the exact key | for B1 and B2; not for B3 or B4 | yes, it is the ticket's one test | yes: in-memory server, no time, order or network |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec | must fix | `app/api.Tests/Features/Health/HealthEndpointTests.cs:14-21` | The test never checks the status code. B4 shows it: with 202 the test still passes. With a status check placed straight after the request (before reading the body), B2 would also fail with `Expected: OK, Actual: NotFound` instead of `Value is null`. | The ticket's `## Tests` asks for "returns 200 and status `ok`", and AC1 says 200. A failing test's first message should name the cause. | [test lesson, step 4](test-lesson.md#steps) · [Integration tests: basic tests](https://learn.microsoft.com/aspnet/core/test/integration-tests?view=aspnetcore-10.0&pivots=xunit#basic-tests-with-the-default-webapplicationfactory) |
| 2 | Spec | must fix | `HealthEndpointTests.cs:3, 17` | The body is read with Newtonsoft.Json (`JsonConvert.DeserializeObject`). Two problems. Newtonsoft matches property names case-insensitively by default, so B3 (`"Status"`) passes, and AC1's exact key is not checked. And the package isn't in your `.csproj`: it compiles only because the test SDK happens to bring it along (`Microsoft.TestPlatform.TestHost` depends on it), so a test SDK update could drop it and break the build. The app itself uses System.Text.Json. Read the body with `System.Text.Json` and look the key up case-sensitively, as the test lesson describes. | A TypeScript client (a0-04) reads `status`; a test that accepts `Status` lets that break through. And depending on a package by accident means a build that can break without any change of yours. | [test lesson, "Reading the JSON answer"](test-lesson.md#reading-the-json-answer) · [`JsonElement.GetProperty`](https://learn.microsoft.com/dotnet/api/system.text.json.jsonelement.getproperty) ("ordinal, case-sensitive comparison") · [`dotnet nuget why`](https://learn.microsoft.com/dotnet/core/tools/dotnet-nuget-why) |
| 3 | Standards | should fix | `HealthEndpointTests.cs:10` | `HealthCheckTest` names the area, not the behaviour. When it fails, the name should already say what was expected, for example request plus expected answer. | With a hundred tests in M1, the names in the failure list are what you read first. | [test lesson, Patterns](test-lesson.md#patterns) · [Unit testing best practices: naming](https://learn.microsoft.com/dotnet/core/testing/unit-testing-best-practices#follow-test-naming-standards) |
| 4 | Standards | nice to have | `HealthEndpointTests.cs:14` | `client.SendAsync(new HttpRequestMessage(HttpMethod.Get, …))` does what `client.GetAsync("/api/health")` does in one call, and the `HttpRequestMessage` is never disposed. | Shorter act line; nothing left undisposed. | [`HttpClient.GetAsync`](https://learn.microsoft.com/dotnet/api/system.net.http.httpclient.getasync) |
| 5 | Standards | nice to have | `HealthEndpointTests.cs:7`, `HomebrewApp.Tests.csproj:26` | The class under test is `HealthEndpoints`, so its tests read best as `HealthEndpointsTests` (and the file to match). The `.csproj` has no final newline. | Finding a class's tests by name stays mechanical. | — |

Done well:

- The class fixture with a primary constructor is exactly the pattern from the lesson: one factory
  for the class, `CreateClient()` per test, no port, no `Program.cs` change.
- The test lives in `api.Tests/Features/Health/` with the namespace
  `HomebrewApp.Tests.Features.Health`, mirroring the API. Every later feature can copy it.
- The expected value `"ok"` and the path are literals in the test, so B1 and B2 are caught.

Verdict: fixes needed

## Round 2 · 2026-11-02 · a8b93af

Reviewed: `9a8905b add status code assertion`, `bc6680f use not typed json deserializing …`,
`2c33376 rename class and use simpler fetching`, `a8b93af add new line`.
Read in full: `app/api.Tests/Features/Health/HealthEndpointsTests.cs`,
`app/api.Tests/HomebrewApp.Tests.csproj`.

Checks: `dotnet build --no-incremental` in `app/`: ok, 0 warnings, 0 errors · `dotnet test`:
`Passed! - Failed: 0, Passed: 1` · no Newtonsoft left in the tests.

Break-the-code check, same four breaks as round 1, same copy-and-restore; `git diff` on
`HealthEndpoints.cs` empty at the end:

| # | Break | Round 1 | Round 2 |
|---|---|---|---|
| B1 | `"okay"` instead of `"ok"` | failed | failed: `Strings differ`, expected `"ok"`, actual `"okay"` |
| B2 | route `/api/healthz` | failed (`Value is null`) | failed: `Assert.True() Failure, Expected: True, Actual: False` |
| B3 | JSON key `"Status"` | passed | **failed**: `KeyNotFoundException` from `GetProperty("status")` |
| B4 | status 202, same body | passed | **still passed** |

Round 1 findings:

| # | Status |
|---|---|
| 1 | still open: see finding 6 |
| 2 | fixed: System.Text.Json with `JsonDocument` and a case-sensitive `GetProperty`; B3 now fails |
| 3 | still open: the method is still `HealthCheckTest` |
| 4 | fixed: `GetAsync`, no undisposed request message |
| 5 | fixed: `HealthEndpointsTests` (file renamed too); final newline in the `.csproj` |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 6 | Spec | must fix | `app/api.Tests/Features/Health/HealthEndpointsTests.cs:15` | `Assert.True(response.IsSuccessStatusCode)` accepts every 2xx status, so B4 (202) still passes. AC1 and the ticket's `## Tests` ask for 200 exactly. Compare the response's `StatusCode` with `HttpStatusCode.OK` using `Assert.Equal`; that also turns B2's message into `Expected: OK, Actual: NotFound` instead of `Expected: True, Actual: False`. | A test should fail when the promise it covers is broken, and its message should name what changed. | [`HttpResponseMessage.IsSuccessStatusCode`](https://learn.microsoft.com/dotnet/api/system.net.http.httpresponsemessage.issuccessstatuscode) ("in the range 200-299") · [`HttpStatusCode`](https://learn.microsoft.com/dotnet/api/system.net.httpstatuscode) |
| 3 | Standards | should fix | `HealthEndpointsTests.cs:9` | Still open from round 1: the name `HealthCheckTest` doesn't say what is expected. | The failure list shows names first. | [Unit testing best practices: naming](https://learn.microsoft.com/dotnet/core/testing/unit-testing-best-practices#follow-test-naming-standards) |
| 7 | Standards | nice to have | `HealthEndpointsTests.cs:20, 23` | The comment says `'Status' (case-sensitive)` while the code looks up `status`: the comment names the wrong key. Line 23 ends with `}    }` (the method's closing brace on the assertion line), and lines 14, 16, 19, 21 and 22 carry trailing spaces. Rider's Reformat Code fixes the layout. | A comment that contradicts the code costs the next reader more than no comment. | [Rider: apply formatting rules](https://www.jetbrains.com/help/rider/Enforcing_Code_Formatting_Rules.html) |

Done well:

- `JsonDocument` with `using` and `GetProperty("status")`: the exact-key contract is now tested,
  and your commit message says why (what the TypeScript client will do).
- One fix per commit, each message saying what changed.

Verdict: fixes needed

## Round 3 · 2026-11-02 · 2c25555

Reviewed: `2c25555 improve health check test`. Read in full:
`app/api.Tests/Features/Health/HealthEndpointsTests.cs`.

Checks: `dotnet build --no-incremental` in `app/`: 0 errors, **1 warning** (`xUnit2000`, finding 8)
· `dotnet test`: `Passed! - Failed: 0, Passed: 1` · no trailing spaces, final newline present.

Break-the-code check, same four breaks, same copy-and-restore; `git diff` on `HealthEndpoints.cs`
empty at the end:

| # | Break | Round 2 | Round 3 |
|---|---|---|---|
| B1 | `"okay"` instead of `"ok"` | failed | failed: expected `"ok"`, actual `"okay"` |
| B2 | route `/api/healthz` | failed (`Expected: True`) | failed, but reads `Expected: NotFound, Actual: OK` (backwards, finding 8) |
| B3 | JSON key `"Status"` | failed | failed: `KeyNotFoundException` |
| B4 | status 202, same body | passed | **failed**, but reads `Expected: Accepted, Actual: OK` (backwards, finding 8) |

All four breaks now fail.

Earlier findings:

| # | Status |
|---|---|
| 3 | fixed: `HealthEndpoint_ReturnsOkWithStatusOk` says the request and the expected answer |
| 6 | fixed in behaviour: the status code is compared with `HttpStatusCode.OK`, and B4 fails. The argument order is wrong, see finding 8 |
| 7 | fixed: the comment names `status`, the layout is clean |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 8 | Spec | must fix | `app/api.Tests/Features/Health/HealthEndpointsTests.cs:18` | `Assert.Equal(response.StatusCode, HttpStatusCode.OK)` passes the actual value first. `Assert.Equal` takes `(expected, actual)`, so a failure reports them swapped: B2 says "Expected: NotFound, Actual: OK", which is the opposite of what happened. xUnit's analyzer catches it as warning `xUnit2000`, so `dotnet build` is no longer warning-free, and AC3 (no warnings) fails. Swap the two arguments, as line 26 already does. | A failure message that says the opposite of the truth sends you looking in the wrong place. AC3 covers the whole solution build. | [xUnit2000](https://xunit.net/xunit.analyzers/rules/xUnit2000) |
| 9 | Standards | nice to have | `HealthEndpointsTests.cs:3` | `using Microsoft.AspNetCore.Builder;` looks unused: nothing in the file uses a type from it. Rider greys out unused `using` lines; "Optimize Imports" removes them. | Unused imports suggest a dependency that isn't there. | — |

Done well:

- Every break now fails, so the test protects all of AC1: route, status code, exact key, value.
- The test name states the request and the expected answer.

Verdict: fixes needed (one swap, then it is ready to ship)
