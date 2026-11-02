# Review: a0-01 · Toolchain

## Round 1 · 2026-11-02 · 00cb34c (on local `main`, not on the ticket branch)

Reviewed: `app/README.md` as committed in `00cb34c app init` in the main checkout. Nothing for this
ticket is on branch `a0-01-toolchain` yet except the lesson.

Checks (all run in a fresh login shell, not an inherited one):
`dotnet --list-sdks` 8.0.133 and 10.0.114 · `dotnet --version` (home folder) 10.0.114 ·
`node -v` v26.13.0 · `npm -v` 11.20.0 · `nvm alias default` 26 · `npm ls -g --depth=0` on Node 26
lists `typescript` 7.0.2 and `typescript-language-server` 6.0.3 · `csharp-ls --version` 0.28.0, the
newest on NuGet today · Rider 2026.2.4 in the Toolbox apps folder · `app/.idea/` is ignored by
`.gitignore:58` · no `dotnet build`, `npm` scripts or language-server diagnostics apply yet (no
projects).

Found on the way: the PC is now on **Ubuntu 26.04.1** (upgraded today, 16:36), so .NET 10 came
from the 26.04 feed (`resolute-updates`), not the 24.04 one the lesson describes. Recorded in
`ticket.md` § Deviations.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `dotnet --list-sdks` shows `8.0.133` and `10.0.114`, both in `/usr/lib/dotnet/sdk` |
| AC2 | yes | fresh shell: `node -v` v26.13.0 (Latest LTS, Lithium), `npm -v` 11.20.0 |
| AC3 | yes | `csharp-ls --version` 0.28.0; NuGet's version list ends at 0.28.0 |
| AC4 | not checked | Rider 2026.2.4 is installed and has opened `app/`; I can't see your screen. Confirm a `.cs` and a `.tsx` file show colours |
| AC5 | no | see findings 2 and 3 |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Standards | must fix | `00cb34c` on local `main` | The README is committed straight to `main` in the main checkout, with the message `app init`. The ticket's work belongs on branch `a0-01-toolchain` and is committed at ship, with the ticket's title as the message. The commit is not pushed, so nothing is lost and it can be undone. | `main` is what every other session and ticket branches from; work on it skips review and the ship checks. It also makes your `main` differ from `origin/main`, so the next `git pull --ff-only` on `main` is refused. | [dev-flow conventions, Commits](../../../.claude/skills/dev-flow/conventions.md) |
| 2 | Spec | must fix | `app/README.md:5-9` | Rows are missing: the .NET 8 SDK (AC1 keeps it), npm, nvm, `typescript-language-server` and your editor (Rider, and how you installed it). | AC5 asks for every tool. The table is what you'd follow to set up the Windows machine in M8, and a missing row is a missing step. | [lesson, step 6](lesson.md#steps) |
| 3 | Spec | must fix | `app/README.md:7-9` | The versions are patterns (`10.0.*`, `26.*`, `0.28`), not what the checks printed (`10.0.114`, `v26.13.0`, `0.28.0`). The Node install command doesn't match what you ran: `nvm install 26` alone wouldn't carry over `typescript-language-server`, but your Node 26 has it, so you also migrated the global packages. | A pattern can't tell you later which exact version worked. A command that isn't the one you ran won't give the same result. | [lesson, "Write down what you did"](lesson.md#patterns-to-follow) |
| 4 | Standards | should fix | `app/README.md:7` | The .NET row doesn't say which Ubuntu version the command is for. On 26.04 `dotnet-sdk-10.0` comes from the built-in feed and .NET 8 is only in the backports PPA; on 24.04 both are built in. | The install command depends on the Ubuntu version, so the row only works on the version it names. | [Install .NET on Ubuntu](https://learn.microsoft.com/en-us/dotnet/core/install/linux-ubuntu-install) |
| 5 | Standards | nice to have | `app/README.md:8`, end of file | `</br>` should be `<br>`; the file has no final newline (the last table row runs into whatever comes next). | Some Markdown renderers drop `</br>`. A missing final newline makes every later diff of that line noisy. | [GFM tables](https://github.github.com/gfm/#tables-extension-) |
| 6 | Standards | nice to have | `app/README.md:5, 8` | Header cells are wrapped in `*…*` (italic), and the tool is written `NODE`. Plain headers and the tool's own name (`Node.js`) read better. | Small, but this README is the first file in `app/`. | — |

Not a finding, for you to know: the .NET 8 SDK package on your PC was installed for Ubuntu 24.04
and has no source on 26.04, so it gets no more updates. .NET 8 support ends on 2026-11-10
([Releases and support for .NET](https://learn.microsoft.com/en-us/dotnet/core/releases-and-support)).
AC1 still asks you to keep it; nothing in the app needs it now that csharp-ls runs on .NET 10.

Done well:

- You migrated your global npm packages to Node 26 (`typescript-language-server` is there, at a newer
  version) and pinned the default to `26`, not `lts/*`. Claude's TypeScript plugin keeps working.
- You kept one package source per tool: .NET from Ubuntu's feed, Node from nvm, csharp-ls from
  `dotnet tool`. No PPA or Microsoft repository added.
- `.idea/` stays out of git (the root `.gitignore` already covers it). Keep IDE folders out of commits.

Verdict: fixes needed
