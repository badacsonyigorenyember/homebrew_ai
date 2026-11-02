# Lesson: a0-02 · API skeleton

## What you will build

The first piece of the app's backend: an ASP.NET Core web API under `app/api` that you start with
one command and that answers `GET /api/health` with `{"status":"ok"}`. It is tiny on purpose. What
matters is the *shape*: a solution, a project, a `Program.cs` that only wires things up, and one
folder per feature. Every later endpoint (batches, recipes, chat) copies this shape.

It is done when:

- **AC1** `curl http://localhost:5080/api/health` answers 200 with `{"status":"ok"}`.
- **AC2** `/openapi/v1.json` lists `/api/health` with its response type.
- **AC3** `dotnet build` gives no warnings.
- **AC4** `Program.cs` holds no endpoint logic, only setup and the feature's map call.

Tests come after the review, in their own lesson (`test-lesson.md`).

What the template gives you today (measured 2026-11-02 with SDK 10.0.114, in a scratch folder):
`dotnet new webapi --no-https` creates a project with `Program.cs`, `appsettings.json`,
`appsettings.Development.json`, `Properties/launchSettings.json` (one `http` profile on a random
port such as 5032), an `.http` file, and a `/weatherforecast` sample endpoint. The project file
targets `net10.0`, has `Nullable` and `ImplicitUsings` on, and references the package
`Microsoft.AspNetCore.OpenApi` 10.0.14.

## New concepts

All of this ticket is .NET. a0-01 covered the SDK, the runtime and the `dotnet` host; everything
below is new.

### Solution and project

A **project** (`.csproj` file) is one thing that gets built: here, the API. It lists the target
framework (`net10.0`), compiler settings and the NuGet packages it uses. A **solution** is a list
of projects that belong together, so one `dotnet build` or `dotnet test` in its folder covers all
of them. You will have two projects soon: `api` now, `api.Tests` in the test lesson.

In .NET 10, `dotnet new sln` writes the newer **`.slnx`** format (short, readable XML) instead of
the old `.sln`. Rider 2026 reads it. You add a project to it with `dotnet sln add <path>`.
Docs: [`dotnet sln`](https://learn.microsoft.com/dotnet/core/tools/dotnet-sln) ·
[`dotnet new sln` defaults to SLNX](https://learn.microsoft.com/dotnet/core/compatibility/sdk/10.0/dotnet-new-sln-slnx-default).

**Name versus folder.** `dotnet new` has `-n|--name` (the project's name, which also becomes the
root **namespace**, the prefix that groups your C# types) and `-o|--output` (the folder). With only
`-o api`, the project and namespace are both called `api`. C# names namespaces in PascalCase, so a
name like `Api` (or `Brewing.Api`) with output folder `api` reads better in code. The ticket fixes
the folder (`app/api`), not the name; pick one and keep it, because the test project and every
later file will use it.
Docs: [`dotnet new` options](https://learn.microsoft.com/dotnet/core/tools/dotnet-new) ·
[naming guidelines](https://learn.microsoft.com/dotnet/standard/design-guidelines/naming-guidelines).

### ASP.NET Core, Kestrel and minimal APIs

**ASP.NET Core** is .NET's web framework. When the app runs, a built-in web server called
**Kestrel** listens on a port, turns each HTTP request into an object your code can read, and
sends back what your code returns.

There are two styles for writing endpoints. **Controllers** are classes whose methods become
endpoints through attributes. **Minimal APIs** map a URL straight to a function. SYSTEM.md §4 picks
minimal APIs; `dotnet new webapi` creates one unless you pass `--use-controllers`.
Docs: [Minimal APIs overview](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/overview?view=aspnetcore-10.0) ·
[Tutorial: create a minimal API](https://learn.microsoft.com/aspnet/core/tutorials/min-web-api?view=aspnetcore-10.0)
(read "Create an API project" and "Examine the code"; skip the database parts).

### `Program.cs`: builder, app, pipeline

`Program.cs` uses **top-level statements**: code that runs from the top of the file, with no
`class Program` or `Main` written out. It has three parts, always in this order:

1. **Builder.** `WebApplication.CreateBuilder(args)` reads configuration (`appsettings*.json`,
   environment variables) and sets up logging. Here you register **services**, the shared objects
   the app needs (OpenAPI is one), through `builder.Services`.
2. **Build.** `builder.Build()` freezes the services and gives you the `WebApplication`, usually
   called `app`.
3. **App.** On `app` you add **middleware** (code that runs for every request, in order) and map
   **endpoints**; `app.Run()` starts Kestrel and blocks until you stop it.

Registering a service after `Build()`, or mapping an endpoint before it, does not compile or
throws at start. Docs: [WebApplication and WebApplicationBuilder](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/webapplication?view=aspnetcore-10.0).

### Endpoints, route handlers and results

An **endpoint** is a URL pattern plus an HTTP method (`GET /api/health`) plus the function that
answers it, the **route handler**. You create one with `MapGet(pattern, handler)` (and `MapPost`,
`MapPut`, `MapDelete` later). The handler can be a lambda or a named static method; a named method
is easier to read and to test.

What the handler returns becomes the response. Returning an object makes ASP.NET Core write it
as JSON with status 200. Returning an **`IResult`** lets you choose the status code. There are two
factories for results:

- `Results.Ok(...)`, `Results.NotFound()` return the plain interface `IResult`, so nothing outside
  the handler knows what it returns.
- **`TypedResults.Ok(...)`** returns the concrete type `Ok<T>`. Because the type is visible in the
  handler's signature, ASP.NET Core can tell OpenAPI "this endpoint returns 200 with a body of type
  T" without any extra annotation, and a unit test can check the type.

AC2 asks for the response type in the OpenAPI document, which is exactly what `TypedResults` gives
you. When a handler can return more than one kind of result later, its return type becomes
`Results<Ok<T>, NotFound>`; not needed today.
Docs: [Create responses: TypedResults versus Results](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/responses?view=aspnetcore-10.0#typedresults-versus-results) ·
[Route handlers](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/route-handlers?view=aspnetcore-10.0).

### Records and JSON

A **record** is a C# type made for carrying data: you declare its properties in one line, and it
gets equality and a readable `ToString()` for free. It is the usual choice for the body of a
response (a *DTO*, data transfer object). The health response is a record with one `string`
property.

ASP.NET Core turns the record into JSON with `System.Text.Json` using the **web defaults**, which
write property names in camelCase: a C# property `Status` comes out as `"status"`. So you name
properties the C# way and the JSON still matches AC1.
Docs: [Records](https://learn.microsoft.com/dotnet/csharp/fundamentals/types/records) ·
[Web defaults for JsonSerializerOptions](https://learn.microsoft.com/dotnet/standard/serialization/system-text-json/configure-options#web-defaults-for-jsonserializeroptions).

### Static classes and extension methods

An **extension method** is a static method in a static class whose first parameter has `this` in
front of it. It can then be called as if it belonged to that type. `app.MapGet(...)` is one: it is
defined by ASP.NET Core on the interface `IEndpointRouteBuilder`, which `WebApplication`
implements.

You write your own the same way, so `Program.cs` can say `app.MapHealth()` (or whatever you name
it) and the feature keeps its endpoints to itself. The signature has this shape: a `public static`
method, first parameter `this IEndpointRouteBuilder`, returning the same builder (so calls can be
chained) or nothing.
Docs: [Extension methods](https://learn.microsoft.com/dotnet/csharp/programming-guide/classes-and-structs/extension-methods).

**Route groups.** `MapGroup("/api/health")` (an extension method too) returns a builder whose
endpoints all share that prefix. With one endpoint it is optional; once a feature has five, it saves
repeating the prefix and lets you add things to all of them at once (the API key filter in a2-01).
Docs: [Route groups](https://learn.microsoft.com/aspnet/core/fundamentals/routing?view=aspnetcore-10.0#route-groups).

### OpenAPI

**OpenAPI** is a standard JSON description of an HTTP API: every path, method, parameter and
response shape. ASP.NET Core 10 generates it from your endpoints. Two calls do it:
`builder.Services.AddOpenApi()` registers the generator, and `app.MapOpenApi()` serves the
document at `/openapi/v1.json`. The template wraps `MapOpenApi()` in an "is this Development?"
check, so the description is not served in production.

This document matters beyond browsing: in a2-02 the web app generates its TypeScript types from it,
so a wrong or missing response type here becomes a wrong type in the UI.
Docs: [OpenAPI overview](https://learn.microsoft.com/aspnet/core/fundamentals/openapi/overview?view=aspnetcore-10.0) ·
[Include OpenAPI metadata](https://learn.microsoft.com/aspnet/core/fundamentals/openapi/include-metadata?view=aspnetcore-10.0#include-openapi-metadata-for-endpoints).

### Environments and `launchSettings.json`

ASP.NET Core always runs in a named **environment**: `Development`, `Staging` or `Production`
(the default if nothing says otherwise). Code can ask `app.Environment.IsDevelopment()`, and
`appsettings.Development.json` is only read in Development.

`Properties/launchSettings.json` holds **launch profiles** for your own machine only; it is never
used by a published build. `dotnet run` uses the first profile whose `commandName` is `Project`.
In that profile, `applicationUrl` sets the address Kestrel listens on (this is where the fixed
port 5080 goes), and `environmentVariables.ASPNETCORE_ENVIRONMENT` sets the environment to
`Development`.
Docs: [Runtime environments: launchSettings.json](https://learn.microsoft.com/aspnet/core/fundamentals/environments?view=aspnetcore-10.0#set-the-environment-with-the-launch-settings-file-%60launchsettingsjson%60) ·
[`dotnet run`: launch profiles](https://learn.microsoft.com/dotnet/core/tools/dotnet-run#launch-profiles).

### Build warnings

The compiler reports **errors** (the build fails) and **warnings** (it builds, but something is
probably wrong). With `Nullable` on, the compiler warns when a value that may be `null` is used as
if it never were (warnings `CS86xx`). AC3 asks for zero warnings, so each warning gets fixed, not
ignored: a warning you get used to hides the next real one. `dotnet build` prints the count on its
last lines.
Docs: [Nullable reference types](https://learn.microsoft.com/dotnet/csharp/nullable-references).

## Patterns to follow

**Vertical slices: one folder per feature.** Everything about one feature (its endpoints, its
request and response types, later its data access) lives in `Features/<Feature>/`, not spread
across `Controllers/`, `Models/`, `Services/` folders. When you change the health check, you open
one folder. SYSTEM.md §5 fixes this layout. The usual mistake: putting the response record in a
shared `Models/` folder "because it is a model".

**`Program.cs` is a table of contents.** It registers services, adds middleware and calls one
`Map…` method per feature. Reading it tells you which features exist and nothing about how they
work. The usual mistake: a lambda in `Program.cs` "just for this small endpoint"; that is endpoint
logic and fails AC4.

**Named, static handlers.** Map the endpoint to a named `static` method in the feature's class
rather than an inline lambda. The name documents what it does, the method can be called from a
unit test, and the mapping method stays a short list of routes. The usual mistake: a long lambda
inside `MapGet` that grows with each change.

**`TypedResults`, not `Results`.** Return typed results so the OpenAPI document knows the
response type without extra `.Produces<T>()` calls. The usual mistake: returning `Results.Ok(...)`
and then wondering why AC2's schema is empty.

**A record per response.** Return a named record, not an anonymous object (`new { status = "ok" }`).
An anonymous object works at runtime but gives OpenAPI no named schema, and in a2-02 that means no
named TypeScript type.

**Namespaces follow folders.** A file in `Features/Health/` declares the namespace
`<RootName>.Features.Health`. Use a *file-scoped* namespace (one line ending in `;` at the top)
rather than a block that indents the whole file. Rider suggests both.
Docs: [Namespaces](https://learn.microsoft.com/dotnet/csharp/fundamentals/types/namespaces).

**Delete what you don't use.** The template's weather sample and the `summaries` array go. The
`.http` file either goes or is changed to call `/api/health`; a file that calls an endpoint that no
longer exists misleads the next reader.

## Steps

1. **Ignore build output.** In `app/`, run `dotnet new gitignore`. It writes the standard .NET
   `.gitignore`, which keeps `bin/` and `obj/` (compiler output) out of git. The repo's root
   `.gitignore` does not cover them.
   Check yourself: `app/.gitignore` exists and contains `[Bb]in/` and `[Oo]bj/`.

2. **Create the solution.** In `app/`, run `dotnet new sln` with a name of your choice
   (`--name`).
   Check yourself: one `.slnx` file in `app/`; `cat` shows an almost empty `<Solution>` element.

3. **Create the API project.** In `app/`, run `dotnet new webapi` with `--output api`, your
   chosen `--name`, and `--no-https` (the API runs on your LAN over plain HTTP, C2; HTTPS would
   add a second port and a dev certificate for nothing). Then add it to the solution with
   `dotnet sln add`.
   Check yourself: `dotnet sln list` shows the project; `dotnet build` in `app/` ends with
   `0 Warning(s)` and `0 Error(s)`.

4. **Fix the port.** In `app/api/Properties/launchSettings.json`, set the `http` profile's
   `applicationUrl` to port 5080. Leave `ASPNETCORE_ENVIRONMENT` as `Development`.
   Check yourself: `dotnet run --project api` from `app/` prints `Now listening on:
   http://localhost:5080` and `Hosting environment: Development`. Stop it with Ctrl+C.

5. **See the template work once.** Run it again and open `http://localhost:5080/openapi/v1.json`
   in a browser (or `curl` it). Find `/weatherforecast` under `paths` and look at its `responses`:
   this is the part AC2 is about.
   Check yourself: you can point to where the document says what `/weatherforecast` returns.

6. **Create the feature folder and class.** Create `app/api/Features/Health/` and in it one file
   holding: the response record (one `Status` property), and a static class with two static
   methods: the **map method** (an extension method on `IEndpointRouteBuilder` that maps
   `GET /api/health`) and the **handler** (no parameters, returns `Ok<YourRecord>` built with
   `TypedResults.Ok`, status `"ok"`). One file is fine while the feature is this small; split it
   when it grows.
   Check yourself: `dotnet build` passes with no warnings. Nothing is mapped yet, so the
   endpoint does not answer.

7. **Clean `Program.cs`.** Remove the weather sample and its record. Add the one call to your
   map method after `Build()`. Keep `AddOpenApi()` and the Development-only `MapOpenApi()`. If the
   feature's namespace is not found, add a `using` for it at the top.
   Check yourself: `Program.cs` reads as builder → services → build → OpenAPI → your map call →
   run, with no `MapGet` and no lambda that answers a request (AC4).

8. **Try AC1 and AC2.** Run the API. In a second terminal:
   `curl -i http://localhost:5080/api/health`.
   Check yourself: the first line says `HTTP/1.1 200 OK`, `Content-Type` is `application/json`,
   and the body is exactly `{"status":"ok"}` (lowercase key). In `/openapi/v1.json`,
   `/api/health` has a `get` with a `200` response whose content refers to a schema with a
   `status` string. `/weatherforecast` is gone.

9. **Tidy the extras.** Update or delete the `.http` file (Rider can run `.http` files: open it and
   click the green arrow beside a request). Check that `appsettings*.json` holds nothing you need
   to change.
   Check yourself: `git status` in the repo shows only files under `app/` that you meant to add,
   and no `bin/` or `obj/`.

10. **Write "Run the API" in `app/README.md`.** A short section: where to run from, the run
    command, the address and port, the health URL, the OpenAPI URL, and how to stop it. Someone
    who has never seen the project should be able to follow it.
    Check yourself: follow your own section in a fresh terminal, word for word, and get AC1.

11. **Final build.** From `app/`, `dotnet build`.
    Check yourself: `0 Warning(s)`, `0 Error(s)` (AC3). Rider's "Problems" view shows no warnings
    in your files either.

## Files you will touch

- `app/.gitignore`: new, from `dotnet new gitignore`.
- `app/<Name>.slnx`: new, the solution.
- `app/api/<Name>.csproj`: new, from the template; normally no hand edits.
- `app/api/Program.cs`: from the template, then reduced to setup plus your map call.
- `app/api/Features/Health/<File>.cs`: new, the response record, the map method and the handler.
- `app/api/Properties/launchSettings.json`: the port 5080.
- `app/api/appsettings.json`, `app/api/appsettings.Development.json`: from the template, unchanged.
- `app/api/<Name>.http`: from the template; changed to call `/api/health`, or deleted.
- `app/README.md`: the "Run the API" section.

## Pitfalls

- **Running from the wrong folder.** `dotnet run` without `--project` looks for a project in the
  current folder. From `app/` it finds only the solution and says it cannot find a project to run.
  Shows up as: "Couldn't find a project to run."
- **Port already in use.** A second `dotnet run` (or one left in another terminal or in Rider)
  holds 5080. Shows up as: `address already in use` at start. Stop the other one.
- **Old code still running.** `dotnet run` does not reload when you save. Shows up as: your change
  "does nothing". Stop and start again, or use `dotnet watch --project api`, which restarts on save.
- **`/openapi/v1.json` gives 404.** The app is not running in Development (the profile was not
  used, or `ASPNETCORE_ENVIRONMENT` changed), so `MapOpenApi()` was skipped. The start-up log line
  `Hosting environment:` tells you which.
- **Empty response schema in OpenAPI.** The handler returns `IResult` or uses `Results.Ok`, so
  there is no type for OpenAPI to read. Use `TypedResults` and let the return type show it.
- **Extension method not found.** `app.MapHealth()` (your name) does not compile when the class
  is not `static`, the method lacks `this` on its first parameter, or the namespace is not
  imported in `Program.cs`. The error is `CS1061: 'WebApplication' does not contain a definition
  for …`.
- **`"Status"` instead of `"status"`.** Only happens if you serialise the record yourself or turn
  off the web defaults. Let ASP.NET Core write the response.
- **Route typos.** `"api/health"` and `"/api/health"` both work, but `"/api/health/"` with a
  trailing slash in a group prefix plus `"/"` in `MapGet` can give `//`. Check the exact path in
  the OpenAPI document.
- **`bin/` and `obj/` committed.** Happens if step 1 is skipped. Shows up as hundreds of files in
  `git status`.
- **Rider's run button uses another profile.** Rider reads `launchSettings.json` too; pick the
  `http` profile so it uses 5080.

## Before you ask for a review

- [ ] `curl -i http://localhost:5080/api/health` gives 200 and `{"status":"ok"}` (AC1).
- [ ] `/openapi/v1.json` shows `/api/health` with a 200 response and its schema (AC2).
- [ ] `dotnet build` in `app/` reports 0 warnings and 0 errors (AC3).
- [ ] `Program.cs` has no `MapGet` and no request-answering lambda, only setup and one map call
      (AC4).
- [ ] The weather sample is gone everywhere, including the `.http` file.
- [ ] Your work is on branch `a0-02-api-skeleton`, not on `main`, and not committed (ship commits
      it). `git status` shows no `bin/` or `obj/`.
- [ ] `app/README.md` "Run the API" works when followed word for word.
- [ ] Ask yourself: if a second feature (`Batches`) came tomorrow, which files would you add, and
      which line would change in `Program.cs`? The answer should be "one new folder, one new line".
