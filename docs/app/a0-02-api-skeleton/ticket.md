# a0-02 · API skeleton

Stage: ready
Branch: `a0-02-api-skeleton`
Milestone: M0 · Requirements: — (§3, §5) ([SYSTEM.md](../SYSTEM.md))
Blocked by: a0-01

## Goal
An ASP.NET Core API runs on your PC and answers one endpoint, laid out the way every later feature
will be.

## What to build
- A solution under `app/` and the API project in `app/api`, created with `dotnet new` (minimal API,
  not controllers).
- `GET /api/health` answers 200 with `{ "status": "ok" }`.
- The endpoint lives in `app/api/Features/Health/`, mapped from `Program.cs` by one call, so
  `Program.cs` stays a list of features.
- The OpenAPI document is served in Development at `/openapi/v1.json`.
- A fixed development port (for example 5080) in `launchSettings.json`.
- `app/README.md` gains "Run the API".

## Acceptance criteria
- **AC1** `curl http://localhost:5080/api/health` answers 200 with `{"status":"ok"}`.
- **AC2** `/openapi/v1.json` lists `/api/health` with its response type.
- **AC3** `dotnet build` gives no warnings.
- **AC4** `Program.cs` holds no endpoint logic, only setup and the feature's map call.

## Tests
Needed. First .NET test lesson: an xUnit project `app/api.Tests` that starts the API in memory with
`WebApplicationFactory` and checks `GET /api/health` returns 200 and status `ok`.

## Out of scope
- The API key, CORS (a0-05) and the database (a2-01).

## Deviations

None yet.
