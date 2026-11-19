# Review: a1-04 · Test database

## Round 1 · 2026-11-19 · e9ea21c

Checks: `dotnet format HomebrewApp.slnx --verify-no-changes` ok · `dotnet build HomebrewApp.slnx -warnaserror`
ok (0 warnings, 0 errors) · `dotnet test HomebrewApp.slnx --no-build` 4 passed · `dotnet test` with
`HOME` set to an empty folder (no user secrets) 4 passed · the saved process equals recipe 1155's
on the stack (`process = <file>::jsonb` is `t`; the file is pretty-printed, 10128 bytes, the
`jsonb` text 7758 in both).

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | stack `select count(*) from app.recipe` 93 before and after `dotnet test`; 15 s after the run `docker ps -a --filter label=org.testcontainers=true` lists nothing |
| AC2 | yes | `AppApi_SelectRecipes_ReturnsSeededRows` and `AppApi_UpdateRecipes_IsRefused` pass; whether they fail on a wrong grant is the test review's check |
| AC3 | yes | `HealthEndpoint_DatabaseReachable_ReturnsOkWithDatabaseOk` passes; with the wrong username (`api_app`, fixed on 2026-11-18) it saw `"down"` |
| AC4 | yes | `app/api.Tests/ApiFactory.cs:39-44`: 010, 015, 060 in order, a comment on each |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | should fix | `app/.editorconfig:258-261` | Commit `bc7cb17` changed the rule for private constants from PascalCase to `_camelCase` so that `private const string _password` fits, and left a stray line holding only `_` (258). Go back to main's four lines (`git diff main -- .editorconfig` shows them) and name the constant in PascalCase, such as `AppApiPassword`. | The .NET convention is PascalCase for every constant, private ones included; `_` marks a field that can change. Changing the shared rule to fit one name moves the whole app off the convention the docs and your later code use, and it is outside this ticket. | [C# identifier naming conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/identifier-names#naming-conventions), item 10 |
| 2 | Standards | nice to have | `app/api.Tests/ApiFactory.cs:46` | `var seed` holds the process JSON, not the seed. | Line 47 then reads `"process=" + seed`, which looks like the bug from 2026-11-18 (reading `seed.sql`) even though it is now right. A name that says what it holds, `process`, makes that line obviously correct. | — |
| 3 | Standards | nice to have | `app/api.Tests/Database/AppApiRoleTests.cs:27` | The `update` runs with `ExecuteScalarAsync`. | It works, because the error comes before any result, but `ExecuteScalarAsync` is for a query returning one value; `ExecuteNonQueryAsync` is the call for a statement that returns no rows (lesson 6c), and says so to the reader. | [Npgsql — Basic usage](https://www.npgsql.org/doc/basic-usage.html) |

Done well:
- The role tests check `SqlState` against `PostgresErrorCodes.InsufficientPrivilege` and count
  with `2L`: they pass only for the right reason, and a typo in the table name would not hide.
- The SQL file list is the smallest that works (three files), and each comment names what the API
  needs from it, so a later ticket knows where to add `054` when it maps `sheet`.
- The process file is the real saved process, checked equal to the stack's.

Verdict: ready for tests. This ticket has no test lesson (Deviations, 2026-11-18): the next step
is the test review.

## Round 2 · 2026-11-19 · uncommitted

Checks: `dotnet format HomebrewApp.slnx --verify-no-changes` ok · `dotnet build HomebrewApp.slnx -warnaserror`
ok (0 warnings, 0 errors) · `dotnet test HomebrewApp.slnx --no-build` 4 passed.

Round 1:

| # | Status | How checked |
|---|---|---|
| 1 | won't fix | your choice: `app/.editorconfig`'s naming rules stay as you set them, `_password` included |
| 2 | fixed | `app/api.Tests/ApiFactory.cs:46-48` reads the JSON into `process` |
| 3 | fixed | `app/api.Tests/Database/AppApiRoleTests.cs:27` uses `ExecuteNonQueryAsync` |

No new findings. ACs unchanged from round 1.

Verdict: ready for tests. The next step is the test review (no test lesson, Deviations
2026-11-18).

# Test review

## Round 1 · 2026-11-19 · uncommitted

Checks: `dotnet build HomebrewApp.slnx -warnaserror` ok (0 warnings, 0 errors) ·
`dotnet test HomebrewApp.slnx --no-build` 4 passed, after every break below was undone
(`git diff -- db/060_app_api_role.sql app/api/Features/Health/HealthEndpoints.cs` empty before and after).

| Test | Behaviour | Broke | Failed? | Needed | Reliable |
|---|---|---|---|---|---|
| `AppApi_SelectRecipes_ReturnsSeededRows` | AC2: the role can read `app.recipe`, and the rows are the container's (2, not the stack's 93) | `db/060:23`: `app.recipe` taken out of the grant | yes: *42501: permission denied for table recipe* | yes | yes; the `2L` holds while no test in the collection writes recipes |
| `AppApi_UpdateRecipes_IsRefused` | AC2: the role cannot update `app.recipe`, and the refusal is a permission error (`SqlState` 42501) | `db/060:23`: `grant select, update` | yes: *Assert.Throws() Failure: No exception was thrown* | yes | yes; `where false` changes no row even when the grant is wrong |
| `HealthEndpoint_DatabaseReachable_ReturnsOkWithDatabaseOk` | AC3: `/api/health` answers `database: ok` against the container | `HealthEndpoints.cs:21`: `"ok"` and `"down"` swapped | yes: *Expected "ok", Actual "down"* | yes | yes |
| `HealthEndpoint_DatabaseUnreachable_ReturnsOkWithDatabaseDown` | the API stays up and says `database: down` when Postgres is unreachable | the same swap | yes: *Expected "down", Actual "ok"* | yes: the only test of the `down` branch | yes: port 1 on `127.0.0.1` refuses at once, no real network |

No findings.

Done well:
- Every test checks what a user of the API or the database sees (a count, a refused update, the
  health answer), not how the code gets there.
- The update test cannot pass for the wrong reason: a typo in the table name gives `42P01`, not
  `42501`, and the `where false` keeps the database unchanged even if the grant is wrong.

Verdict: ready to ship.
