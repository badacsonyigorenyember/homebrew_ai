This folder will hold the desktop and mobile app for the homebrew assistant.
Currently, I'm using Ubuntu 26.04 as operating system and all the tools are installed to that.

## Toolchain

| Tool                       | Version  | Install command                                                                                                                                                                                  | Version command          |
|----------------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------|
| .NET SDK                   | 10.0.114 | `sudo apt-get install -y dotnet-sdk-10.0`                                                                                                                                                        | `dotnet --list-sdks`     |
| nvm                        | 0.40.3   | `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh \| bash`                                                                                                              | `nvm --version`          |
| Node.js                    | 26.13.0  | `nvm install 26.13.0` <br> `nvm alias default 26`                                                                                                                                                | `node -v`                |
| npm                        | 11.20.0  | comes with Node.js                                                                                                                                                                               | `npm -v`                 |
| typescript                 | 7.0.2    | `npm install -g typescript`                                                                                                                                                                      | `npm ls -g --depth=0`    |
| typescript-language-server | 6.0.3    | `npm install -g typescript-language-server`                                                                                                                                                      | `npm ls -g --depth=0`    |
| csharp-ls                  | 0.28.0   | `dotnet tool install --global csharp-ls`                                                                                                                                                         | `csharp-ls --version`    |
| IDE (Rider)                | 2026.2.4 | install tar from [website](https://www.jetbrains.com/rider/download/?section=linux) <br> `sudo tar -xzf jetbrains-rider-*.tar.gz -C /opt/` <br> start: `"/opt/JetBrains Rider-2026.2.4/bin/rider.sh"` | Help > About             |

## Run the API

From the `app/` folder:

```bash
dotnet run --project api
```

It uses the `http` profile in `api/Properties/launchSettings.json`: it listens on
`http://localhost:5080` and runs in the `Development` environment. Wait for
`Now listening on: http://localhost:5080` in the output.

| What | URL |
|---|---|
| Health check | `http://localhost:5080/api/health` (answers `{"status":"ok"}`) |
| OpenAPI document (Development only) | `http://localhost:5080/openapi/v1.json` |

Check it from a second terminal with `curl http://localhost:5080/api/health`, or open
`api/HomebrewApp.http` in Rider and run the request. Stop the API with Ctrl+C.

`dotnet run` doesn't reload code changes; stop and start it again, or use
`dotnet watch --project api`, which restarts on save.

## Run the web app

From the `app/web/` folder, once after cloning or after `package-lock.json` changes:

```bash
npm ci
```

Then start the dev server:

```bash
npm run dev
```

It serves the page at `http://localhost:5173` and updates it on save. Stop it with Ctrl+C.

| Script | What it does |
|---|---|
| `npm run dev` | dev server with hot reload; does not check types |
| `npm run build` | type-checks, then writes the optimised app to `dist/` |
| `npm run preview` | serves the built `dist/` to look at it |
| `npm run lint` | ESLint over the project |
| `npm run typecheck` | the TypeScript type check on its own, no output files |
| `npm run format` | Prettier rewrites every file in its layout |
| `npm test` | Vitest in watch mode: runs the tests, then again on every save; quit with `q` |
| `npm test -- --run` | runs the tests once and exits (what the review and ship checks use) |
| `npm run cleanup` | lint, typecheck, tests once, build, then format; stops at the first that fails |

The project pins TypeScript `~6.0.3` in `package.json`, not the global 7.0.2 from the Toolchain
table: `typescript-eslint` 8.72 supports TypeScript below 6.1 only. Scripts and `npx tsc` use the
project's version; a bare `tsc` in the terminal uses the global one.

Tests sit next to the component they test (`StatusBadge.test.tsx` beside `StatusBadge.tsx`).
They run in jsdom, a browser page simulated inside Node, so no browser is needed;
`src/test/setup.ts` loads the jest-dom matchers and clears the page after each test.
