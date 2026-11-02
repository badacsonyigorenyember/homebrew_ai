# Lesson: a0-01 · Toolchain

## What you will build

No app code yet. You install the tools every later ticket needs: the .NET 10 SDK beside the .NET 8
one you have, the current Node.js LTS through `nvm`, an editor that understands C# and TypeScript,
and the latest `csharp-ls`. Then you write down what you installed, so the setup can be repeated.

It is done when:

- **AC1** `dotnet --list-sdks` shows a 10.x SDK, and the 8.0 SDK is still there.
- **AC2** `node -v` prints the current LTS version and `npm -v` works.
- **AC3** `csharp-ls --version` prints its latest version.
- **AC4** Your editor opens a `.cs` and a `.tsx` file with highlighting.
- **AC5** `app/README.md` lists every tool, its version and the install command.

What your PC has now (measured 2026-11-02, so you know the starting point):

| Tool | Now | Target |
|---|---|---|
| Ubuntu | 24.04.5 LTS | — |
| .NET SDK | 8.0.133, Ubuntu packages in `/usr/lib/dotnet` | add 10.0 (`dotnet-sdk-10.0`, candidate 10.0.114 in `noble-updates`) |
| nvm | 0.40.3 | — |
| Node.js | v22.22.2 (nvm default `22`) | v26, codename Lithium (`nvm ls-remote --lts` marks it "Latest LTS") |
| Global npm packages on Node 22 | `typescript`, `typescript-language-server` | the same, on Node 26 |
| csharp-ls | 0.16.0 | 0.28.0 (newest on NuGet) |
| Editor | `cursor` installed; no `code` or `rider` on the PATH | VS Code + C# Dev Kit, or Rider |

## New concepts

### .NET

**SDK, runtime and the `dotnet` command.** The *runtime* is what runs a finished .NET program. The
*SDK* (software development kit) is what builds one: compiler, project templates, `dotnet build`,
`dotnet test`, and it includes a runtime. The *ASP.NET Core runtime* is the extra layer for web APIs,
which the SDK also includes. The `dotnet` command itself is a small program called the *host* (or
*muxer*): it looks in its install folder (`/usr/lib/dotnet` for you), finds every SDK and runtime
there, and hands your command to the right one. That is why several versions can sit side by side
in one folder. You develop with the SDK, so the SDK is what you install.
Docs: [How to check that .NET is installed](https://learn.microsoft.com/en-us/dotnet/core/install/how-to-detect-installed-versions).

**Which SDK runs.** With several SDKs installed, the host picks the newest one, unless a
`global.json` file in the current folder (or a parent) asks for another. After this ticket, plain
`dotnet` commands use the 10 SDK. A .NET 10 SDK can still build projects that target .NET 8, so
nothing you already have breaks. Docs: [Select the .NET version to use](https://learn.microsoft.com/en-us/dotnet/core/versions/selection).

**LTS and STS.** .NET ships one major version a year. Even numbers (8, 10) are *long-term support*,
supported for three years; odd numbers are *standard-term*. The app uses .NET 10 because it is the
current LTS (SYSTEM.md §4).

**Package sources, and why you must stick to one.** On Ubuntu, .NET can come from three places:
Ubuntu's own feed (built by Canonical), the Ubuntu .NET backports PPA, or the older Microsoft package
repository. Each builds the same version differently, and installing pieces from two sources makes
the host find a half-installed SDK (the "package mix-up"). Your .NET 8 came from Ubuntu's feed, and
on Ubuntu 24.04 that feed also has .NET 10, so you add nothing new: no PPA, no Microsoft repository.
Docs: [Install .NET on Ubuntu](https://learn.microsoft.com/en-us/dotnet/core/install/linux-ubuntu-install)
(pick the 24.04 tab) and [.NET package mix-ups on Linux](https://learn.microsoft.com/en-us/dotnet/core/install/linux-package-mixup).

**.NET global tools.** A *tool* is a .NET console program shipped as a NuGet package and installed
with `dotnet tool install`. A *global* tool goes into `~/.dotnet/tools` and runs from any folder.
`csharp-ls` is one. Docs: [.NET tools](https://learn.microsoft.com/en-us/dotnet/core/tools/global-tools).

**Language servers.** An editor learns a language from a *language server*: a separate program that
reads your code and answers "what is this symbol", "where is it defined", "what is wrong here" over
the Language Server Protocol (LSP). `csharp-ls` is a C# language server, and `typescript-language-server`
is the TypeScript one. Claude Code's `csharp-lsp` and `typescript-lsp` plugins (see
[`app/.claude/README.md`](../../../app/.claude/README.md)) run exactly these two, so Claude's reviews
can see the same errors your editor shows. `csharp-ls` 0.16.0 is the last version that ran on .NET 8;
from 0.21.0 it needs the .NET 10 runtime
([changelog](https://github.com/razzmatazz/csharp-language-server/blob/main/CHANGELOG.md)), which is
why it is updated after the SDK.

### Node.js and TypeScript

**Node.js and npm.** Node.js runs JavaScript outside a browser. You need it for the frontend's
*tooling*, not for the app itself: Vite (the dev server and bundler), the TypeScript compiler, the
linter and the tests all run on Node. `npm` ships with Node and installs JavaScript packages. Docs:
[Node.js — introduction](https://nodejs.org/en/learn/getting-started/introduction-to-nodejs).

**Node release lines.** A new major version comes out every six months. Even-numbered ones become
LTS in October and get a codename: 22 Jod, 24 Krypton, 26 Lithium. Tools such as Vite support only
the maintained lines, so you follow the newest LTS. Docs:
[Node.js releases](https://nodejs.org/en/about/previous-releases).

**nvm.** `nvm` installs each Node version into its own folder under `~/.nvm/versions/node/` and
switches between them by changing your `PATH` in the shell. Two things follow from that:

- the *default* alias is the version a new terminal starts with; `nvm use` only changes the
  current terminal;
- **global npm packages belong to one Node version.** Your `typescript-language-server` lives under
  Node 22's folder; Node 26 starts without it unless you ask nvm to copy the list over.

Docs: [nvm README, "Long-term support" and "Migrating global packages"](https://github.com/nvm-sh/nvm#long-term-support).

### Editor

**VS Code + C# Dev Kit.** VS Code highlights and checks TypeScript out of the box. For C# it needs
Microsoft's *C# Dev Kit* extension (it installs the *C#* extension with it): solution explorer, test
explorer, debugging. It is free for personal, academic and open-source work
([Dev Kit FAQ](https://code.visualstudio.com/docs/csharp/cs-dev-kit-faq)); the getting-started page
says it asks you to sign in with a Microsoft account
([Getting started with C# in VS Code](https://code.visualstudio.com/docs/csharp/get-started)).
Install VS Code itself from [Visual Studio Code on Linux](https://code.visualstudio.com/docs/setup/linux).

**JetBrains Rider.** A full .NET IDE that also handles TypeScript and React, free for
non-commercial use. Heavier than VS Code, with stronger refactoring and debugging for C#. Install
it through the JetBrains Toolbox App ([Rider](https://www.jetbrains.com/rider/)).

Either works for the whole app. Choose one; you can change later.

## Patterns to follow

- **One package source per tool.** .NET from Ubuntu's feed, Node from nvm, global tools from
  `dotnet tool`. *Why:* each manager only knows about what it installed. *Usual mistake:* following
  an old blog post that adds the Microsoft repository "to get .NET 10", which mixes sources and
  leaves `dotnet` unable to find an SDK.
- **Check with the command, not from memory.** Every AC is a command; run it and read the output.
  *Why:* `apt` or `nvm` can report success while the shell still runs an old binary.
  *Usual mistake:* checking in the terminal you installed from, where the old `PATH` is still active.
  Open a new terminal for each check.
- **Write down what you did, as you do it.** Copy the exact command and the version it printed into
  the README table straight away. *Why:* the table is how this setup gets repeated on another PC
  (and on Windows in M8). *Usual mistake:* writing "latest" instead of a version number.
- **No `sudo` with npm or nvm.** nvm installs into your home folder. *Why:* `sudo npm install -g`
  writes root-owned files into it and breaks later installs.

## Steps

1. **Note the starting point.** Run `dotnet --list-sdks`, `dotnet --list-runtimes`, `node -v`,
   `npm ls -g --depth=0` and `csharp-ls --version`.
   *Check yourself:* the output matches the "Now" column above. If it does not, ask before going on.

2. **Install the .NET 10 SDK** from Ubuntu's feed: `sudo apt-get update`, then
   `sudo apt-get install -y dotnet-sdk-10.0`. Read the list of packages apt wants to install before
   saying yes: they should all be `dotnet-*`, `aspnetcore-*` and `netstandard-*` packages at 10.0 or
   at the 8.0 version you already have, and none should be removed.
   *Check yourself:* in a new terminal, `dotnet --list-sdks` shows an `8.0.*` and a `10.0.*` line,
   both in `/usr/lib/dotnet/sdk`; `dotnet --version` in your home folder prints `10.0.*` (AC1).

3. **Install the Node LTS and carry your global packages over.** Follow the nvm README's
   "Migrating global packages" section: install `lts/*`, reinstalling the packages from your current
   version. Then point the `default` alias at the major version (`26`), not at `lts/*`, so a new
   LTS next October does not switch it for you without notice.
   *Check yourself:* in a new terminal, `node -v` prints `v26.*`, `npm -v` prints a version, `nvm
   alias default` shows `26`, and `npm ls -g --depth=0` lists `typescript` and
   `typescript-language-server` (AC2).

4. **Update csharp-ls:** `dotnet tool update --global csharp-ls`.
   *Check yourself:* `csharp-ls --version` prints `0.28.0` or newer (AC3). If it says a framework
   was not found, step 2 is not finished.

5. **Install your editor.** VS Code (`.deb` or snap from its Linux page) plus the C# Dev Kit
   extension; or Rider through the Toolbox App.
   *Check yourself:* make a scratch folder **outside the repo**, put an empty-ish `Hello.cs` and
   `Hello.tsx` in it, open both. Keywords are coloured in both files (AC4). Delete the folder
   afterwards.

6. **Write `app/README.md`.** A short intro line saying what the folder will hold, then a
   `## Toolchain` table with the columns *Tool*, *Version*, *Install command* and *Check command*,
   one row each for the .NET SDK (both 8 and 10), Node.js, npm, nvm, csharp-ls,
   typescript-language-server and your editor (with its C# extension). Use the versions the check
   commands printed, not the ones in this lesson.
   *Check yourself:* every tool in AC1–AC4 has a row, and every version is a number (AC5).

7. **Ask for a review** (say "review a0-01").

## Files you will touch

- `app/README.md` — new: what `app/` is for, and the Toolchain table.

Nothing else in the repo changes. The installs themselves live on your PC, not in git.

## Pitfalls

- **Old `PATH` in an open terminal.** After `nvm` or `apt`, a terminal that was already open can keep
  running the old binary. Shows up as `node -v` still printing `v22` right after the install. Open a
  new terminal.
- **Installing `dotnet-sdk-10.0` from a PPA or the Microsoft repository.** Shows up as `dotnet
  --list-sdks` printing only one of the two SDKs, or "A fatal error occurred. The folder
  [/usr/share/dotnet/host/fxr] does not exist". The Ubuntu feed already has 10.0; nothing needs to be
  added.
- **Global npm packages missing on the new Node.** Shows up later as Claude's TypeScript plugin
  failing to start, or `typescript-language-server: command not found`. Step 3's reinstall flag
  prevents it; if you skipped it, run `nvm reinstall-packages 22` while on Node 26.
- **`nvm alias default lts/*`.** Works today, but moves to a new major version on its own next
  October. Pin `26`.
- **`dotnet tool update` before the SDK.** `csharp-ls` from 0.21.0 needs the .NET 10 runtime; on
  .NET 8 alone the update either refuses or installs a tool that cannot start.
- **Cursor is not VS Code.** It is installed on your PC and looks the same, but it is a fork with its
  own extension store, and the C# Dev Kit is published for VS Code. If you want to use Cursor for C#,
  read the [Dev Kit licence](https://aka.ms/vs/csdevkit/license) first; the safe choice for this
  course is VS Code itself or Rider.
- **`.cs` file with no colours in VS Code.** The C# extension is not installed or not enabled; check
  the Extensions view.

## Before you ask for a review

- [ ] AC1: `dotnet --list-sdks` shows 8.0 and 10.0, in a new terminal.
- [ ] AC2: `node -v` is `v26.*`, `npm -v` works, `nvm alias default` is `26`.
- [ ] AC3: `csharp-ls --version` is the newest on NuGet.
- [ ] AC4: a `.cs` and a `.tsx` file are highlighted in your editor.
- [ ] AC5: `app/README.md` has a row per tool, real version numbers, the exact commands.
- [ ] `npm ls -g --depth=0` on Node 26 still lists `typescript-language-server`.
- [ ] `git status` shows only `app/README.md` as new; no scratch files in the repo.
- [ ] Could someone repeat your setup on a fresh Ubuntu 24.04 from the table alone?
