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

Once per machine, give the API its database connection string. The API reads Postgres as the
role `app_api`; how that role and its password are set up is in
[`docs/OPERATIONS.md`](../docs/OPERATIONS.md) §4. The connection string goes into the API's
user secrets, a file in your home folder that is never committed. From the `app/` folder, in
the terminal where `APP_API_PASSWORD` holds the role's password:

```bash
dotnet user-secrets set --project api "ConnectionStrings:App" "Host=localhost;Port=5432;Database=postgres;Username=app_api.<POOLER_TENANT_ID>;Password=$APP_API_PASSWORD"
```

Replace `<POOLER_TENANT_ID>` with the value from the repo root's `.env`
(`grep ^POOLER_TENANT_ID= .env`). `dotnet user-secrets list --project api` shows the stored
value. Without this key the API stops at start-up with an `InvalidOperationException`, and so
does `dotnet test`, because the tests start the API in `Development` too.

Then, from the `app/` folder:

```bash
dotnet run --project api
```

It uses the `http` profile in `api/Properties/launchSettings.json`: it listens on
`http://localhost:5080` and runs in the `Development` environment. Wait for
`Now listening on: http://localhost:5080` in the output.

| What                                | URL                                                                                                                                         |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| Health check                        | `http://localhost:5080/api/health` (answers `{"status":"ok","database":"ok"}`; `"database":"down"` when the API cannot connect to Postgres) |
| OpenAPI document (Development only) | `http://localhost:5080/openapi/v1.json`                                                                                                     |

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

The page asks the API for its health, so start the API too ([Run the API](#run-the-api)); the
order doesn't matter. The dev server forwards every request whose path starts with `/api` to the
API at `http://localhost:5080`, so the page only ever talks to its own address. That address is
set in one place: `server.proxy` in `web/vite.config.ts` (`npm run preview` uses the same
proxy). While the API is stopped, the badge shows "API down" and the dev server's terminal
prints `http proxy error: /api/health` with `ECONNREFUSED`.

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
