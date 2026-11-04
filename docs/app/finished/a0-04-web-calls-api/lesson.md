# Lesson: a0-04 · The page calls the API

## What you will build

The page asks the API whether it is up and shows the answer in your `StatusBadge`. The asking is
done by TanStack Query, a library that fetches data for React components and keeps track of
"still loading", "worked" and "failed" for you. In development, Vite's server passes every `/api`
request on to the API, so the page only ever talks to its own address.

It is done when:

- **AC1** With the API running, the badge shows `ok`.
- **AC2** With the API stopped, the badge shows `down` within a few seconds (retry settings chosen
  and explained in the code).
- **AC3** No `fetch` inside a `useEffect` anywhere.
- **AC4** The API address is not hard-coded in components (one place: the proxy or a config
  module).

What the tools look like today (measured 2026-11-03 in a scratch copy of your `app/web`, with your
TypeScript 6.0.3 and Vite 8.3; every error message quoted below comes from that run):

| Thing | Version | Note |
|---|---|---|
| `@tanstack/react-query` | 5.105.3 | installed next to your packages with no conflict; goes in `dependencies` |
| Vite's proxy | built into Vite 8.3 | when the API is stopped, it answers the page with **502 Bad Gateway** |
| The library's retry default | 3 retries, waiting 1 s, 2 s, 4 s | with the API stopped, the badge showed `down` about **7 s** after the page loaded |

## New concepts

### The web

**Origin.** An *origin* is the scheme, host and port of an address: `http://localhost:5173` (the
page) and `http://localhost:5080` (the API) are two different origins, because the port differs.
Browsers block a page from reading answers from another origin unless that server allows it (CORS,
which is ticket a2-01). The proxy below avoids the question in development: the page asks its own
origin, and Vite forwards.
Docs: [MDN — Same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy).

**Vite's dev-server proxy.** `server.proxy` in `vite.config.ts` is an object whose keys are path
beginnings and whose values say where to send them. A request from the page to
`http://localhost:5173/api/health` starts with `/api`, so Vite sends it to the target
(`http://localhost:5080/api/health`) and hands the answer back to the page. The simplest form is
the *string shorthand*: the key, then the target origin as a string. The path is kept as it is, which
is what you want, because the API's route already starts with `/api`. If the target does not answer,
Vite logs `http proxy error` in its terminal and gives the page a 502. The proxy exists only in
`vite` (dev) and `vite preview` (which copies `server.proxy` by default); a built app served some
other way needs its own answer, which comes with Tauri in M8.
Docs: [Vite — `server.proxy`](https://vite.dev/config/server-options#server-proxy),
[`preview.proxy`](https://vite.dev/config/preview-options#preview-proxy).

**`fetch`, promises, `async` and `await`.** `fetch(url)` is the browser's built-in way to make an
HTTP request. It does not wait: it returns a *promise*, an object that stands for a result that
arrives later. Inside a function marked `async`, the keyword `await` before a promise pauses that
function until the result is there, and gives you the result. An `async` function itself always
returns a promise. Two awaits are needed here: one for the response (status and headers) and one
for its body, `response.json()`, which reads the body and turns the JSON text into a JavaScript
object.
Docs: [MDN — Using promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises),
[`async function`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function),
[Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch).

**`fetch` does not fail on an error status.** A 404, 500 or 502 is still an answer, so `fetch`
gives you a normal response for it; only "no answer at all" (network down) makes its promise fail.
The response's `ok` field is `true` for statuses 200 to 299. To turn an error status into a
failure, you check `ok` and `throw` an `Error` yourself. `throw` stops the function, and the promise
it returned fails with that error.
Docs: [MDN — `Response.ok`](https://developer.mozilla.org/en-US/docs/Web/API/Response/ok),
[`throw`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/throw).

### React and TypeScript

**Hooks.** Functions whose names start with `use` (`useState`, `useEffect`, `useQuery`) are
*hooks*: they let a component keep data between renders and react to things. React has two rules
for them: call them only at the top level of a component or of another hook (never inside an `if`,
a loop or a nested function), and only from components or hooks. The `react-hooks` lint rule you
already have checks this. A *custom hook* is your own function that calls other hooks; its name
must also start with `use`, so the rules (and the lint rule) apply to it. `useHealth` is one.
Docs: [react.dev — Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks),
[Reusing logic with custom hooks](https://react.dev/learn/reusing-logic-with-custom-hooks).

**Why not `fetch` in `useEffect` (AC3).** `useEffect` runs code after React draws a component. You
can fetch there and store the result in state, and many tutorials do. But then you write by hand:
the loading flag, the error flag, ignoring an answer that arrives after the component is gone,
retrying, refreshing, and not fetching the same thing twice when two components need it. Each
hand-written copy gets one of those wrong. react.dev itself says to use a data-fetching library
instead.
Docs: [react.dev — You might not need an Effect, "Fetching data"](https://react.dev/learn/you-might-not-need-an-effect#fetching-data).

**TanStack Query.** A library that owns *server state*: data that lives on the server and that the
page only holds a copy of. You give it two things per piece of data, and it does the rest:

- a **query key**, an array that names the data (`['health']`). Same key, same data: two
  components asking for `['health']` share one request and one cached answer.
- a **query function**, an `async` function that fetches the data and either returns it or throws.
  The library calls it; you never call it yourself.

`useQuery({ queryKey, queryFn, ...options })` returns a result object. The fields you need:
`status`, which is exactly one of `'pending'` (no answer yet), `'error'` (the query function threw,
after all retries) or `'success'` (it returned), and the matching booleans `isPending`, `isError`,
`isSuccess`. `data` holds the last answer. Measured: when a later refetch fails, `status` becomes
`'error'` even though `data` still holds the old answer, so read `status`, not "is there data".
Docs: [Overview](https://tanstack.com/query/latest/docs/framework/react/overview),
[Queries](https://tanstack.com/query/latest/docs/framework/react/guides/queries),
[Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys),
[Query functions, "Handling and throwing errors" and "Usage with fetch"](https://tanstack.com/query/latest/docs/framework/react/guides/query-functions).

**`QueryClient` and `QueryClientProvider`.** The cache that holds every query's answer is a
`QueryClient` object. You create **one**, once, outside any component, and make it available to
every component by wrapping the app in `<QueryClientProvider client={...}>`. The provider uses
React *context*: a value a parent puts in place that any component below it can read without
passing props down. `useQuery` looks the client up through that context, so a `useQuery` outside
the provider fails (Pitfalls has the exact message).
Docs: [Quick start](https://tanstack.com/query/latest/docs/framework/react/quick-start),
[`QueryClientProvider`](https://tanstack.com/query/latest/docs/framework/react/reference/QueryClientProvider),
[react.dev — Passing data deeply with context](https://react.dev/learn/passing-data-deeply-with-context).

**Retries and refetching.** By default a failed query is retried 3 times, waiting longer each time
(1 s, 2 s, 4 s, capped at 30 s), and only then does `status` become `'error'`. That is why the
default takes about 7 s to show `down`. Three options change this, set on the query:

- `retry`: how many times to retry (a number, or `false` for none).
- `retryDelay`: how long to wait before each retry, in milliseconds (a number for a fixed wait).
- `refetchInterval`: ask again every so many milliseconds. Without it, a page that loaded while the
  API was up keeps showing `ok` after the API stops, until something else triggers a refetch (by
  default, focusing the browser window again). With it, a stopped API is noticed while you watch.

The time to `down` is roughly the sum of the waits before the last attempt (plus, for a page already
open, up to one interval). Choosing these numbers is part of AC2, and the comment in the code says
why you picked them.
Docs: [Query retries](https://tanstack.com/query/latest/docs/framework/react/guides/query-retries),
[Important defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults),
[`useQuery` reference (`retry`, `retryDelay`, `refetchInterval`)](https://tanstack.com/query/latest/docs/framework/react/reference/useQuery).

**Typing a promise.** `Promise<HealthResponse>` reads "a promise that will give a
`HealthResponse`". The angle brackets are a *type parameter*: `Promise` is a type that wraps another
type. You write it as the return type of the query function, after the parameter list, a colon and
then the type. `useQuery` reads that type, so its `data` is typed `HealthResponse` without you
saying it again. `response.json()` itself is typed `any` (TypeScript cannot know what the server
sends), so this return type is where you state what you expect. Generated types replace the
hand-written one in a2-02.
Docs: [TypeScript — Return type annotations, "Functions which return promises"](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#functions-which-return-promises).

**Exporting and importing a type.** `ApiStatus` in `StatusBadge.tsx` is local to that file today.
To use it elsewhere, put `export` in front of its `type` line. Your project has
`verbatimModuleSyntax` on, which means an import that brings in *only* a type must say so: the word
`type` after `import`, so the line disappears from the JavaScript.
Docs: [TypeScript — `verbatimModuleSyntax`](https://www.typescriptlang.org/tsconfig/#verbatimModuleSyntax),
[Type-only imports](https://www.typescriptlang.org/docs/handbook/modules/reference.html#type-only-imports-and-exports).

## Patterns to follow

- **One address, in one place.** The page asks for relative paths (`/api/health`, starting with a
  slash and no host); the only place that knows `localhost:5080` is the proxy in `vite.config.ts`.
  *Why:* when the API moves (LAN address in M2's settings, Tauri in M8), one line changes.
  *Usual mistake:* `fetch('http://localhost:5080/api/health')` in the hook: it works only through
  CORS, which the API does not allow yet, and breaks AC4.
- **Feature folders.** The hook goes in `src/features/health/`, mirroring the API's
  `Features/Health/` (SYSTEM.md §5). `StatusBadge` stays in `src/components/`, because it is a
  shared display piece that knows nothing about the API. *Why:* later features (`batches`,
  `recipes`) each get their own folder with their hooks beside them.
- **A hook per query, the query function beside it.** Components call `useHealth()`; they never see
  the query key, the URL or the retry settings. *Why:* every component that needs the health gets
  the same key and settings, and the URL is in one file. *Usual mistake:* calling `useQuery`
  directly in `App` with the options written inline.
- **The query function throws on failure.** Check `ok` and throw; return only real data. *Why:*
  throwing is how TanStack Query learns it failed; a function that returns normally on a 502 makes
  the query `'success'`.
- **Settings for one query live on that query.** Put the retry options on `useHealth`'s query, not
  as defaults on the `QueryClient`. *Why:* a health check wants to fail fast; the batches and
  recipes queries later want the library's patient defaults.
- **Create the `QueryClient` once, at module level.** A `const` at the top of `main.tsx`, outside
  any function. *Why:* code in a component body runs on every render; a client created there is a
  new, empty cache each time.
- **Map a union to a union with a `Record`.** The query's `status` has three values and your
  `ApiStatus` has three; a `Record` from one to the other is the same safety net as the labels in
  a0-03: forget a key and the type check says so. *Usual mistake:* a chain of `if`s with a final
  `else` that returns `'ok'`.
- **Explain chosen numbers in a comment.** A comment above the retry options says what the numbers
  add up to and why that is fast enough. *Why:* AC2 asks for it, and a bare `1000` tells the next
  reader nothing.

## Steps

1. **Check where you are.** Run `git branch --show-current`. Start the API (`dotnet run --project
   api` from `app/`) and check `curl http://localhost:5080/api/health`.
   *Check yourself:* the branch is `a0-04-web-calls-api`; curl prints `{"status":"ok"}`.

2. **Add the proxy.** In `vite.config.ts`, add a `server` key to the object passed to
   `defineConfig`, next to `plugins` and `test`. Its value is an object with a `proxy` key, whose
   value is an object with one entry: the key `'/api'` and, as the value, the API's origin as a
   string (the string shorthand from the Vite docs' first example). Start `npm run dev` in `app/web`.
   *Check yourself:* `http://localhost:5173/api/health` in the browser shows `{"status":"ok"}`.
   Stop the API: the same address now gives a 502, and the Vite terminal prints
   *http proxy error: /api/health* and *connect ECONNREFUSED 127.0.0.1:5080*. Start the API again.
   To see the type check guard the config: put the port as a bare number instead of the string,
   and `npm run typecheck` says *Type 'number' is not assignable to type 'string | ProxyOptions'*.
   Put the string back.

3. **Install TanStack Query.** In `app/web`: `npm install @tanstack/react-query`. It is shipped with
   the app, so no `--save-dev`.
   *Check yourself:* `package.json` lists it under `dependencies`; `npm ls @tanstack/react-query`
   shows `5.105.x`.

4. **Write the query function**, in small steps. Read the background first.

   **Read first (about 45 minutes, in this order).** Try each piece in the
   [TypeScript Playground](https://www.typescriptlang.org/play) where you can (it knows `fetch`).
   - [MDN — Using promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises),
     the introduction and *Chaining*: what a promise is. Skim the rest.
   - [MDN — `async function`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function),
     *Description* and the first example: what `await` does inside it.
   - [MDN — Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch),
     *Making a request* and *Checking response status*: why you test `ok` yourself.
   - [TypeScript — Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html),
     *Return Type Annotations* and *Functions Which Return Promises*.
   - [TanStack Query — Query functions](https://tanstack.com/query/latest/docs/framework/react/guides/query-functions),
     *Handling and Throwing Errors* and *Usage with fetch and other clients that do not throw by
     default*. Its example is the closest one to your query function: an `async` function, an
     `ok` check that throws, then the JSON.

   **4a. The file.** Create `src/features/health/useHealth.ts`. `.ts`, not `.tsx`: this file has no
   JSX.
   *Check yourself:* the folder is beside `src/components/`, not inside it.

   **4b. The response type.** A `type` alias, for example `HealthResponse`, for the JSON the API
   sends: an object type with one field, `status`, of type `string`. Look at the curl output from
   step 1: the field name is lower case, because ASP.NET Core writes JSON in camelCase.
   *Check yourself:* `npm run typecheck` says *'HealthResponse' is declared but never used.* That is
   expected; 4c uses it.

   **4c. The signature.** A function that is not exported (only this file uses it), marked `async`,
   named for example `fetchHealth`, with no parameters, and the return type
   `Promise<HealthResponse>` after the brackets and a colon. Start the body with the `await` of a
   `fetch` of the relative path `/api/health`, stored in a `const` (for example `response`).
   *Check yourself:* `npm run typecheck` says *'fetchHealth' is declared but its value is never
   read*: expected until step 5 uses it. Remove `async` for a moment and the message becomes
   *'await' expressions are only allowed within async functions and at the top levels of modules*.
   Put `async` back.

   **4d. Fail on an error status.** An `if` on the response *not* being `ok` (the `!` operator in
   front of `response.ok`), whose body throws a `new Error(...)` with a message that names the
   status, so a failure in the console says what happened. A *template literal* (backticks, with
   `${...}` around a value) puts the status number into the text.
   Docs: [MDN — Template literals](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals).
   *Check yourself:* the editor shows no new errors.

   **4e. Return the data.** Return the result of `response.json()`. The `Promise<HealthResponse>`
   from 4c tells TypeScript what it is.
   *Check yourself:* only the "never read" message from 4c is left.

5. **Write the hook `useHealth`.** In the same file: `export function useHealth()`, no parameters,
   and no return type (TypeScript works it out from `useQuery`). Import `useQuery` by name from
   `@tanstack/react-query` at the top. The body returns a call to `useQuery` with one object: the
   `queryKey` (an array with one string naming the data) and the `queryFn` (the function from step 4,
   by name, **without** round brackets: you hand the library the function, it calls it). Leave
   the retry options for step 9.
   Docs: [Queries](https://tanstack.com/query/latest/docs/framework/react/guides/queries), the first
   example has the same shape.
   *Check yourself:* `npm run typecheck` passes (the 4c message is gone: `fetchHealth` is used).
   Remove `queryKey`: the error ends with *Property 'queryKey' is missing in type*. Write
   `fetchHealth()` with brackets: *Type 'Promise<HealthResponse>' is not assignable to type
   'QueryFunction<...>'*. Undo both. The long *No overload matches this call* line above each message
   is normal for `useQuery` errors; the real reason is in the last indented line.

6. **Call the hook from the page.** In `App.tsx`, import `useHealth` from
   `./features/health/useHealth`, and on the first line of `App`'s body store its result in a
   `const` (for example `health`). Leave the badge's `status="ok"` for now.
   *Check yourself:* `npm run typecheck` says *'health' is declared but its value is never read*:
   expected until step 8. Open the page: it is **blank**, and the browser console (F12) shows
   *Uncaught Error: No QueryClient set, use QueryClientProvider to set one*. Also expected: step 7
   fixes it.

7. **Provide the `QueryClient`.** In `main.tsx`:
   - **7a.** Import `QueryClient` and `QueryClientProvider` by name from `@tanstack/react-query`.
   - **7b.** Below the imports, outside any function, a `const` (for example `queryClient`) set to
     `new QueryClient()` (`new` creates an object from a class; no options needed).
   - **7c.** Inside `<StrictMode>`, wrap `<App />` in a `QueryClientProvider` element with its
     `client` prop set to that const, in curly braces.
   Docs: [Quick start](https://tanstack.com/query/latest/docs/framework/react/quick-start), the
   `App` function there has the same wrapping.
   *Check yourself:* the page is back, with the heading and the badge. The Network tab (F12, filter
   `health`) shows a request to `/api/health` with status 200.

8. **Turn the query's status into the badge's status.**
   - **8a.** In `StatusBadge.tsx`, put `export` in front of the `ApiStatus` type. Import it in
     `App.tsx` with a type-only import (`import type`, the name in curly braces, `from`, the path).
     *Check yourself:* with a plain `import` instead, `npm run typecheck` says *'ApiStatus' is a type
     and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled*; without
     the `export`, it says *declares 'ApiStatus' locally, but it is not exported*.
   - **8b.** In `App.tsx`, outside the `App` function, a `const` lookup object typed
     `Record<'pending' | 'error' | 'success', ApiStatus>`, with one pair per query status: which
     badge status does each one mean? (The ticket says.) Keep it in `App.tsx`: an exported
     non-component in `StatusBadge.tsx` makes `npm run lint` say *Fast refresh only works when a file
     only exports components*.
     *Check yourself:* remove a pair: *Property '...' is missing*. Put it back.
   - **8c.** Set the badge's `status` prop to the lookup, with the query result's `status` in
     square brackets (the same bracket lookup as a0-03's step 9f), all inside curly braces.
     *Check yourself:* `npm run typecheck` and `npm run lint` pass. With the API running, the badge
     shows `ok` (AC1). Reload with the API stopped: `unknown` first, then `down` after about 7 s.
     That is the library's default; step 9 makes it faster.

9. **Choose the retry settings (AC2).** On `useHealth`'s query, add `retry`, `retryDelay` and
   `refetchInterval`, with a comment above them that says what they add up to. Work out first, on
   paper: with your numbers, how long after the API stops until the badge says `down`, (a) when you
   load the page with the API already stopped, (b) when the page was open and showing `ok`? "A few
   seconds" is your call; also think about how often you want the page to ask while everything is
   fine.
   *Check yourself:* both cases, timed with a clock: (a) stop the API, reload the page; (b) load
   the page with the API up, then stop it. Each reaches `down` in the time you worked out. Start the
   API again: the badge goes back to `ok` within one interval.

10. **Check AC3 and AC4 by search.** From `app/web`: `grep -rn "useEffect" src` and
    `grep -rn "5080" src`.
    *Check yourself:* both print nothing. `grep -rn --exclude-dir=node_modules --exclude-dir=dist
    "5080" .` finds only `vite.config.ts`.

11. **Update `app/README.md`.** In "Run the web app": the API must be running for the badge to say
    `ok`, and the dev server forwards `/api` to `http://localhost:5080` (where that is set).
    *Check yourself:* someone reading only the README knows to start both, and in which order it
    does not matter.

12. **Run every check and ask for a review** (say "review a0-04").
    *Check yourself:* the list under "Before you ask for a review" is all ticked.

## Files you will touch

- `app/web/vite.config.ts` — the `server.proxy` entry for `/api`.
- `app/web/package.json`, `app/web/package-lock.json` — `@tanstack/react-query` added by npm.
- `app/web/src/features/health/useHealth.ts` — new: the response type, the query function and the
  `useHealth` hook with its retry settings and comment.
- `app/web/src/main.tsx` — one `QueryClient`, and `QueryClientProvider` around `App`.
- `app/web/src/App.tsx` — calls `useHealth`, maps its status, passes it to the badge.
- `app/web/src/components/StatusBadge.tsx` — `export` on `ApiStatus`, nothing else.
- `app/README.md` — the proxy and "start the API too" in "Run the web app".

## Pitfalls

- **A blank page and *No QueryClient set, use QueryClientProvider to set one*.** A component calls
  `useQuery` (through `useHealth`) but is not inside `QueryClientProvider`. Check that the provider
  wraps `<App />` in `main.tsx`.
- **The badge says `ok` while the API is down.** The query function returned normally on the 502.
  Check the `ok` test and the `throw` (step 4d).
- **The badge stays `ok` after you stop the API.** No `refetchInterval`: the page asked once and is
  happy with its answer until you leave and refocus the window. Step 9.
- **`down` shows only after about 7 s.** No retry options yet, so the defaults apply. Step 9.
- **A 404 from `localhost:5173/api/health`.** The proxy is not active: the key is not `'/api'`, the
  `server` key is inside `test` instead of beside it, or Vite did not restart after the change
  (stop it and run `npm run dev` again to be sure).
- **The target has a path or a trailing `/api`.** `'http://localhost:5080/api'` as the target sends
  the browser's `/api/health` to `/api/api/health`, and the API answers 404. The target is only the
  origin.
- **`queryFn: fetchHealth()`.** With brackets, you call the function once while the page draws and
  hand the library a promise instead of a function. The type check refuses it (step 5).
- **`Type 'string' is not assignable to type 'ApiStatus'`.** You built the status in a `let`
  variable and changed it later; `let` widens `'ok'` to `string`. Use the `Record` lookup (step 8).
- **The `QueryClient` created inside a component.** It works, but each render gets a new empty
  cache. Keep it at the top of `main.tsx`.
- **The existing `StatusBadge` tests.** They should still pass unchanged: this ticket does not touch
  what the badge shows. If one fails, a label changed.

## Before you ask for a review

- [ ] AC1: with the API running, the badge shows `ok`.
- [ ] AC2: with the API stopped, `down` within the time you worked out, both on reload and while
      the page is open; a comment explains the retry numbers.
- [ ] AC3: `grep -rn "useEffect" src` in `app/web` prints nothing.
- [ ] AC4: the only place with `5080` in `app/web` (outside `node_modules`) is `vite.config.ts`.
- [ ] `npm run lint`, `npm run typecheck`, `npm test -- --run` and `npm run build` all pass.
- [ ] `npx prettier . --check` passes.
- [ ] `app/README.md` says the API must run and that `/api` is proxied.
- [ ] `git status` shows only the files listed above.
- [ ] Could a second component show the API status by calling `useHealth()`, with no copy of the
      URL or the retry settings?
