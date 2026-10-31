# a0-01 · Toolchain

Stage: ready
Branch: `a0-01-toolchain`
Milestone: M0 · Requirements: — (§4, §10) ([SYSTEM.md](../SYSTEM.md))
Blocked by: none

## Goal
Every tool the app needs is installed on your Linux PC, checked, and written down, so later tickets
never stop on setup.

## What to build
- The .NET 10 SDK, next to the .NET 8 SDK already installed (`/usr/lib/dotnet`, Ubuntu packages).
  Install it from the same source as .NET 8 so the two do not fight over `dotnet`.
- Node.js at its current LTS version, through `nvm`, which you already use (Node 22.22.2 now).
- An editor: VS Code with the C# Dev Kit, or JetBrains Rider (free for non-commercial use).
- `csharp-ls` updated to its latest version once the .NET 10 SDK is in (`dotnet tool update --global
  csharp-ls`; 0.16.0 was the newest that installed on .NET 8).
- `app/README.md` with a Toolchain table: each tool, its version and the command you used to install
  it.

## Acceptance criteria
- **AC1** `dotnet --list-sdks` shows a 10.x SDK, and the 8.0 SDK is still there.
- **AC2** `node -v` prints the current LTS version and `npm -v` works.
- **AC3** `csharp-ls --version` prints its latest version.
- **AC4** Your editor opens a `.cs` and a `.tsx` file with highlighting.
- **AC5** `app/README.md` lists every tool, its version and the install command.

## Tests
Not needed: nothing here has behaviour to test.

## Out of scope
- Creating any project (a0-02, a0-03).
- Docker, Postgres and the rest of the stack, which already run.

## Deviations

None yet.
