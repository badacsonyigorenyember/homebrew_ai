# Test lesson: a0-02 · API skeleton

Your first .NET test project. It starts the API inside the test process, sends it a real HTTP
request, and checks the answer. Every later API ticket adds tests to this project in the same way.

What the tools give you today (measured 2026-11-02 with SDK 10.0.114, in a scratch folder):
`dotnet new xunit` creates a project targeting `net10.0` with the packages `xunit` 2.9.3,
`xunit.runner.visualstudio` 3.1.4, `Microsoft.NET.Test.Sdk` 17.14.1 and `coverlet.collector`, plus
an empty `UnitTest1.cs`. `dotnet add package Microsoft.AspNetCore.Mvc.Testing` picks 10.0.14, the
same version as your OpenAPI package. In the scratch copy, a test using
`WebApplicationFactory<Program>` built and ran against your API with nothing added to `Program.cs`.

## What to test

| Behaviour | AC | Level | Why this level |
|---|---|---|---|
| `GET /api/health` answers status 200 with a JSON body whose `status` is `"ok"` | AC1 | API integration: a real HTTP request through the in-memory server | The behaviour *is* the HTTP answer: the route, the status code and the JSON key name. Only a request through the whole pipeline (routing, handler, JSON writer) proves all three |

Status 200 and the body together are one behaviour ("the health check says the API is healthy"),
so one test checks both. Check the key as `status`, lowercase and exact: AC1 says
`{"status":"ok"}`, and a client written in TypeScript (a0-04) reads `status`, not `Status`.

## What not to test

- **The OpenAPI document (AC2).** ASP.NET Core generates it; a test would mostly test Microsoft's
  generator. You checked AC2 by hand, and a2-02 will use the document for real.
- **`dotnet build` warnings (AC3) and the shape of `Program.cs` (AC4).** These are checked by the
  build and by review, not by tests.
- **The private handler on its own.** It is `private`, so a test can't call it, and the
  integration test already runs it. Testing it separately would test the same line twice.
- **That System.Text.Json writes camelCase**, or that `TypedResults.Ok` gives 200. Framework
  behaviour; your test sees both anyway through the real answer.

## New concepts

### Test project and project reference

Tests live in their own **test project**, `app/api.Tests`, next to the API, so test code and test
packages never end up in the API you run. The test project points at the API with a **project
reference** (`dotnet add reference`): it builds the API first and can use its public types, such
as your `HealthResponse` record. Add the test project to the solution so one `dotnet test` in
`app/` finds it.

As with the API, `-o` sets the folder (`api.Tests`, fixed by the ticket) and `-n` the name and root
namespace. Name it after the API project, with `.Tests` added.
Docs: [`dotnet new` templates: xunit](https://learn.microsoft.com/dotnet/core/tools/dotnet-new-sdk-templates#xunit) ·
[`dotnet reference add`](https://learn.microsoft.com/dotnet/core/tools/dotnet-reference-add).

### xUnit and `dotnet test`

**xUnit** is the test framework: it finds your tests, runs them and reports the results. A test is
a public method marked **`[Fact]`** (a test with no inputs) in a public class. Inside it, **`Assert`**
methods check results: `Assert.Equal(expected, actual)` fails the test with a message showing both
values when they differ. xUnit creates a **new instance of the test class for every test**, so tests
can't leak state into each other through fields.

**`dotnet test`** builds the solution and runs every test it finds, then prints
`Passed!` or `Failed!` with counts. Rider runs the same tests from the green arrows beside each
test, or from its Unit Tests window.
Docs: [Unit testing C# with xUnit](https://learn.microsoft.com/dotnet/core/testing/unit-testing-csharp-with-xunit) ·
[`dotnet test`](https://learn.microsoft.com/dotnet/core/tools/dotnet-test).

### `async`, `await` and `Task`

Sending an HTTP request takes time, so the methods that do it are **asynchronous**: they return a
**`Task`** (or `Task<T>` for a value) straight away, and **`await`** pauses your method until the
result is there, without blocking a thread. A method that uses `await` is marked **`async`**, and
an `async` test method returns `Task` instead of `void`; xUnit waits for that task. Never call
`.Result` or `.Wait()` on a task in a test; `await` it.
Docs: [Asynchronous programming with async and await](https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/).

### `WebApplicationFactory` and the in-memory test server

The package **`Microsoft.AspNetCore.Mvc.Testing`** gives you **`WebApplicationFactory<TEntryPoint>`**.
It runs your real `Program.cs` inside the test process, but on a **`TestServer`** instead of Kestrel:
no port is opened, nothing is listening on 5080, and requests travel in memory. So the tests work
whether or not the API is also running in a terminal or in Rider, and they're fast.

`TEntryPoint` is any type from the API project; the usual choice is `Program`, the class the
compiler makes from your top-level statements. Until .NET 9 that class was `internal` and you had to
add `public partial class Program { }` to `Program.cs`. **In .NET 10 a source generator makes it
public for you**, and an analyzer suggests removing the line if you add it. So `Program.cs` stays
as it is.

`factory.CreateClient()` gives you an **`HttpClient`** already pointed at the test server: you call
it with a relative path like `/api/health`. The app runs in the `Development` environment unless
you change it.
Docs: [Integration tests in ASP.NET Core (xUnit)](https://learn.microsoft.com/aspnet/core/test/integration-tests?view=aspnetcore-10.0&pivots=xunit)
(read "Introduction", "Test app prerequisites" and "Basic tests with the default
WebApplicationFactory"; skip the Razor Pages and database parts) ·
[Unit and integration tests in Minimal API apps](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/test-min-api?view=aspnetcore-10.0) ·
[What's new in .NET 10: testing apps with top-level statements](https://learn.microsoft.com/aspnet/core/release-notes/aspnetcore-10.0?view=aspnetcore-10.0#better-support-for-testing-apps-with-top-level-statements).

### Class fixtures: one factory for the whole class

Starting the app takes a moment, so you don't want a new factory per test. A test class that
implements **`IClassFixture<WebApplicationFactory<Program>>`** gets one shared factory, created
before the first test in the class and disposed after the last. xUnit hands it to the class
through its **constructor**: the class declares a constructor parameter of that type and keeps it
(a C# 12 *primary constructor* on the class declaration does this in one line). Each test then
calls `CreateClient()` on it.
Docs: [xUnit: shared context, class fixtures](https://xunit.net/docs/shared-context#class-fixture) ·
[Primary constructors](https://learn.microsoft.com/dotnet/csharp/whats-new/tutorials/primary-constructors).

### Reading the JSON answer

The response body arrives as `HttpContent`. Two ways to read it, and the difference matters for
AC1:

- `ReadFromJsonAsync<HealthResponse>()` (namespace `System.Net.Http.Json`) turns it into your
  record. It uses the **web defaults**, where property names are **case-insensitive**, so it reads
  `{"Status":"ok"}` just as happily as `{"status":"ok"}`. It can't catch a wrong key casing.
- `JsonDocument` (namespace `System.Text.Json`) parses it into a tree, and
  `RootElement.GetProperty("status")` looks the key up **case-sensitively**: it throws if the key
  is `Status`. This checks the exact contract.

For this test the second checks what AC1 actually promises. The first is fine later, when a test
cares about the values and not the spelling. (`JsonDocument` should be disposed: declare it with
`using`.)
Docs: [Web defaults for JsonSerializerOptions](https://learn.microsoft.com/dotnet/standard/serialization/system-text-json/configure-options#web-defaults-for-jsonserializeroptions) ·
[`JsonElement.GetProperty`](https://learn.microsoft.com/dotnet/api/system.text.json.jsonelement.getproperty) ·
[Use a JSON DOM](https://learn.microsoft.com/dotnet/standard/serialization/system-text-json/use-dom).

## Patterns

**Arrange, act, assert.** Each test has three parts, in this order, separated by a blank line:
*arrange* (get a client), *act* (send the one request), *assert* (check the answer). One act per
test; if you find a second request, it's a second test.

**One behaviour per test.** A test checks one thing the API does for its user. When it fails, its
name alone tells you what broke. Several `Assert` lines are fine when they check one behaviour (here:
status and body of the same answer).

**Names that state the behaviour.** The method name says what is requested and what should come
back, for example in the `Request_Expectation` shape. Avoid `Test1`, `HealthTest` or names that
describe code (`CallsHandler`). The class is named after what it tests, with `Tests` added.

**Test folders mirror the API.** `HealthEndpoints` lives in `api/Features/Health/`, so its tests
live in `api.Tests/Features/Health/`, with the same namespace shape. When Batches arrives, its tests
go in `api.Tests/Features/Batches/`.

**Expected values are literals in the test.** Write `"ok"`, `"/api/health"` and the status code in
the test itself, not taken from the API's code. If the test reused the API's own constant, a wrong
value in the API would be wrong in the test too, and the test would still pass.

**No real network, no sleeping.** The factory's in-memory client is the only way the test talks to
the API. Never call `http://localhost:5080` from a test (it would depend on something you started
by hand), and never wait with `Thread.Sleep` or `Task.Delay`.

## Steps

1. **Create the test project.** In `app/`, run `dotnet new xunit` with `--output api.Tests` and
   `--name` set to your API project's name plus `.Tests`. Add it to the solution with
   `dotnet sln add`.
   Check yourself: `dotnet sln list` shows both projects; `dotnet test` in `app/` runs the
   template's one empty test and prints `Passed!`.

2. **Connect it to the API.** From `app/`, add a project reference from the test project to
   `api/<YourName>.csproj` (`dotnet add api.Tests reference …`), and add the package
   `Microsoft.AspNetCore.Mvc.Testing` to the test project (`dotnet add api.Tests package …`).
   Check yourself: the test `.csproj` has a `ProjectReference` to the API and a `PackageReference`
   to `Microsoft.AspNetCore.Mvc.Testing` 10.0.x; `dotnet build` in `app/` shows 0 warnings.

3. **Lay out the test class.** Delete `UnitTest1.cs`. Create
   `api.Tests/Features/Health/HealthEndpointsTests.cs` with a public class that implements the
   class fixture for `WebApplicationFactory<Program>` and receives the factory in its
   constructor. No tests in it yet.
   Check yourself: it builds. If `Program` or `WebApplicationFactory` is not found, check the
   project reference and the `using` for `Microsoft.AspNetCore.Mvc.Testing`.

4. **Write the test.** One `async Task` method marked `[Fact]`: arrange a client from the
   factory; act by sending `GET /api/health`; assert the status code is `HttpStatusCode.OK` and
   that the body's `status` property (looked up case-sensitively) is the string `"ok"`.
   Check yourself: `dotnet test` in `app/` prints `Passed!  - Failed: 0, Passed: 1`.

5. **See it fail.** The endpoint already works, so the test passed first time. A test you have
   never seen fail could be checking nothing. Break the API briefly, one change at a time, and
   run the test after each:
   - change the handler's `"ok"` to another word;
   - change the route in `MapGet` to another path;
   - change the record's property name `Status` to something else (this is the case that
     `ReadFromJsonAsync` alone would not catch).

   Check yourself: each break makes the test fail with a message that tells you what was wrong
   (expected vs actual status code, expected vs actual value, or the missing key). Undo each break
   and check `git diff app/api` is empty afterwards.

6. **Run everything.** From `app/`: `dotnet build`, then `dotnet test`.
   Check yourself: 0 warnings, 0 errors, all tests pass. The API you may have running on 5080
   doesn't affect the result (stop it and run again if you want to see that).

## Before you ask for a test review

- [ ] `app/api.Tests` exists, is in the solution, references the API and
      `Microsoft.AspNetCore.Mvc.Testing`; `UnitTest1.cs` is gone.
- [ ] `dotnet test` in `app/` passes; `dotnet build` shows 0 warnings.
- [ ] The test checks status 200 and the exact `status` key with value `"ok"`, using literals.
- [ ] You saw it fail for each of the three breaks in step 5, and `git diff app/api` is empty.
- [ ] The test is arrange-act-assert, its name says the behaviour, and it lives in
      `api.Tests/Features/Health/`.
- [ ] `Program.cs` is unchanged (no `public partial class Program`).
- [ ] `git status` shows no `bin/` or `obj/` from the test project (the `app/.gitignore` covers
      it).
- [ ] Ask yourself: if someone renamed the route to `/api/healthz` by mistake, which line of your
      test would fail, and what would its message say?
