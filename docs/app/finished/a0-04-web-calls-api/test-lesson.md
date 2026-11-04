# Test lesson: a0-04 · The page calls the API

You test the page the way you checked it by hand in the review rounds: draw `App`, let it ask
`/api/health`, and read the badge. The API is not running during tests; a library called MSW
answers `/api/health` instead, with whatever answer each test needs.

What the tools look like today (measured 2026-11-04 in a scratch copy of your `app/web`, with the
round 4 code; every error message and timing below comes from that run):

| Thing | Version | Note |
|---|---|---|
| `msw` | 3.0.3 | needs Node 22.12+ and TypeScript 5.9+; you have 26 and 6.0.3. Installed with no conflict |
| MSW 3 vs most tutorials | — | tutorials show MSW 2. In 3: `http` and `HttpResponse` are imported from `msw/http`, and the listen option `onUnhandledRequest` is now **`onUnhandledFrame`** (the old name is a type error, step 3) |
| Your test run | 7 tests, about 2.4 s | the two `down` tests take about 1 s each, because of your 1 s `retryDelay` |

## What you will test

| Behaviour | AC / ticket | Level | Why this level |
|---|---|---|---|
| Before the API answers, the badge says "API status unknown" | "What to build" | component | the user sees it; the first draw is the only moment to check it |
| The API answers 200 → "API ok" | AC1 | component | the whole chain runs: `App` → `useHealth` → `fetch` → the answer → the lookup → the badge |
| The proxy answers 502 (the API is stopped) → "API down", within 2 s | AC2 | component | this is exactly what Vite sends when the API is stopped (measured in the lesson) |
| The API answers 500 *with a JSON body* → "API down", within 2 s | AC2 | component | the only test that fails when the `ok` check in `fetchHealth` is missing (measured, step 7) |

All four are *component tests*: draw `App` inside a `QueryClientProvider`, fake the network, read
the screen. Testing `useHealth` alone, or `fetchHealth` alone, would check pieces the component
tests already run, and would tie the tests to how the code is split instead of to what the page
shows.

What not to test:

- **TanStack Query itself**: that it retries, caches or refetches. Its own tests cover that. You
  test what *your* settings mean for the badge (down within 2 s), not that `retry` works.
- **That `fetch` was called with `/api/health`.** That's how, not what. If MSW's handler for
  `/api/health` answers and the badge changes, the URL was right.
- **`StatusBadge`'s labels.** a0-03's three tests already do that; your `App` tests use the
  labels but don't need to cover every one again.
- **The "stays down while checking again" fix** (round 4, `App.tsx`). Measured: removing it
  breaks none of these four tests. Catching it needs the next refetch (5 s) plus a retry (1 s) to
  happen during the test, so either 6 s or more of real waiting in every run, or *fake timers*,
  which make the clock jump forward but don't work with Testing Library's `findBy` without extra
  setup. Neither is worth it here; the comment in `App.tsx` explains the case instead.
- **The proxy.** `vite.config.ts`'s `server.proxy` only runs in the dev server; tests never use
  it.

## Steps

**0. Commit the round 4 change first.**
`git status` shows `App.tsx` and `useHealth.ts` changed (the fixes from review round 4). Read the
diff, then commit those two files on their own.
*Why:* the test commit should hold only tests. If the code fix and the tests are in one commit, a
reader can't tell which line made which test pass.
*Check yourself:* `git status` is clean before you start step 1.

**Read first (about 40 minutes, in this order).** Each item is the background for a step below.
- [MSW — Quick start](https://mswjs.io/docs/quick-start), up to and including *Integrate*: the
  three parts (handlers, a server, the test-runner hooks). Look for the Vitest setup file.
- [MSW — Node.js integration](https://mswjs.io/docs/integrations/node), *Test runner*: the three
  lifecycle calls and why each exists.
- [MSW — Mocking responses](https://mswjs.io/docs/http/mocking-responses), the first sections:
  `HttpResponse.json(...)` and a response with a status.
- [MSW — Network behavior overrides](https://mswjs.io/docs/best-practices/network-behavior-overrides):
  `server.use` in one test; that's how one test gets a 502 while the others get 200.
- [Testing Library — Async methods](https://testing-library.com/docs/dom-testing-library/api-async),
  *`findBy` Queries* and the `timeout` option of *`waitFor`*.
- [MDN — `async function`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
  (you read it for the lesson): the same `async` and `await`, now in a test.

**1. Install MSW.** In `app/web`: `npm install --save-dev msw`.
*Why:* MSW (Mock Service Worker) catches requests your code makes and answers them from *handlers*
you write: "for GET `/api/health`, answer `{"status":"ok"}`". Your code doesn't know: `fetch` gets
a normal response. That is better than replacing `fetch` or `useHealth` with a fake, because the
real `fetchHealth`, the real `ok` check and the real TanStack Query run, so the test proves they
work together. In Node (where Vitest runs) MSW hooks into Node's own request code; in a browser it
would use a service worker, which you don't need here. It is a `--save-dev` package: only tests use
it.
*Check yourself:* `npm ls msw` shows `msw@3.0.x` (it also appears under `vitest`, which uses it
internally; that's the same copy, *deduped*).

**2. The server with one handler.** Create `src/test/server.ts`.
- **2a.** Import `setupServer` from `msw/node`, and `http` and `HttpResponse` from `msw/http`.
- **2b.** An exported `const`, for example `server`, set to `setupServer(...)` with one argument:
  `http.get('/api/health', ...)`. Its second argument is an arrow function (no parameters) that
  returns `HttpResponse.json(...)` with an object literal like the real API's answer.

*Why:* this is the *default handler*, the "happy path": every test gets a healthy API unless it
says otherwise. It lives in its own file, beside the setup file, so the setup file can start it and
a test can import the same `server` to override it (step 6). The path is relative, like in
`fetchHealth`; under jsdom, relative URLs work (measured), because jsdom gives the page an address.
*Watch out:* this file only *creates* the server. Nothing catches requests until `listen` runs
(step 3).
*Check yourself:* `npm run typecheck` passes.

**3. Start and stop the server around the tests.** In `src/test/setup.ts`, which you wrote in a0-03.
- **3a.** Import `server` from `./server`, and add `beforeAll` and `afterAll` to the import from
  `vitest`.
- **3b.** `beforeAll` with an arrow function that calls `server.listen(...)` with an options object:
  `onUnhandledFrame` set to `'error'`.
- **3c.** A second `afterEach` (keep the `cleanup` one) that calls `server.resetHandlers()`.
- **3d.** `afterAll` that calls `server.close()`.

*Why:* the three calls from the MSW docs. `listen` before any test starts catching requests;
`resetHandlers` after each test removes whatever that test added with `server.use`, so a 502 from
one test never leaks into the next; `close` gives Node its normal request code back. `'error'` for
unhandled requests means a request your handlers don't cover is reported as an error instead of
going out to the real network (the default is a warning).
*Watch out:* `onUnhandledRequest`, the name in MSW 2 tutorials, is a type error in MSW 3:
*Object literal may only specify known properties, and 'onUnhandledRequest' does not exist in
type 'PartialObjectDeep<SharedOptions, ...>'*.
*Check yourself:* `npm run typecheck` and `npm run lint` pass; `npm test -- --run` still shows the
three `StatusBadge` tests passing (they make no requests, so MSW changes nothing for them).

**4. A test file and a way to draw `App`.** Create `src/App.test.tsx`, beside `App.tsx`.
- **4a.** Imports: `QueryClient` and `QueryClientProvider` from `@tanstack/react-query`; `render`
  and `screen` from `@testing-library/react`; `describe`, `it` and `expect` from `vitest`; `App`
  from `./App` (a *default* export, so no curly braces, as in `main.tsx`).
- **4b.** A function `renderApp()`, no parameters, not exported: it creates a `new QueryClient()`
  in a `const` and calls `render` with `<App />` inside a `QueryClientProvider` that gets that
  client, the same wrapping as `main.tsx`.
- **4c.** `describe('App', ...)` with an arrow function, for the tests.

*Why:* `App` calls `useHealth`, which needs a `QueryClient` from context (lesson, "QueryClient and
QueryClientProvider"). Each test calls `renderApp()` and so gets a **new, empty** client: no answer
cached by an earlier test can show up in the next one, so each test starts from "nothing known
yet", like a fresh page load. One small helper keeps that wrapping in one place instead of copied
into every test (the same "one place" idea as the proxy).
*Watch out:* without the provider in the helper, every test fails with *No QueryClient set, use
QueryClientProvider to set one*, the same message as in the lesson's step 6.
*Check yourself:* `npm run typecheck` says *'renderApp' is declared but its value is never read*,
and the same for `screen`, `it` and `expect`: expected until step 5 uses them.

**5. The `unknown` and `ok` tests.**
- **5a. Unknown.** `it` named for the behaviour (for example *shows "API status unknown" before the
  API answers*). Arrange: `renderApp()`. Assert, after a blank line: `screen.getByText` with the
  unknown label, `.toBeInTheDocument()`.
  *Why `getByText` here:* `render` draws once and returns before any answer can arrive, so right
  after it the badge must say unknown. `getBy` looks *now*, which is the point of this test.
- **5b. Ok.** A second `it` (for example *shows "API ok" when the API answers*), whose arrow
  function is marked `async` (the word `async` before the brackets). Arrange: `renderApp()`.
  Assert: `expect(await screen.findByText(...)).toBeInTheDocument()` with the ok label.
  *Why `findBy` and `await`:* the answer arrives a moment after the first draw. A `findBy` query
  keeps looking (by default for up to 1000 ms) and returns a promise that resolves with the element
  once it appears; `await` waits for it, which is why the test function must be `async`. This is
  the "act" part of arrange-act-assert done by time instead of a click: you wait for the page to
  change.

*Watch out:*
- `getByText` for ok fails in 3 ms with *Unable to find an element with the text: API ok*, and the
  printed page shows `API status unknown`: it looked before the answer came.
- `findByText` without `await`: *received value must be an HTMLElement or an SVGElement* (you
  handed `expect` the promise, not the element), plus an *Unhandled Errors* section.
- `await` without `async` on the test's arrow function: `npm run typecheck` says *'await'
  expressions are only allowed within async functions and at the top levels of modules*.

*Check yourself, and see each fail:* `npm test -- --run` passes both. Then in `App.tsx`'s lookup,
set `pending` to `'down'` for a moment: the unknown test fails with *Unable to find an element with
the text: API status unknown*. Undo it, set `success` to `'down'`: the ok test fails after about
1000 ms (`findBy` gave up). Undo it.

**6. The `down` test for a stopped API (502).** A third `async` test (for example *shows "API
down" when the API is stopped*).
- **6a.** Add imports at the top: `http` and `HttpResponse` from `msw/http`, and `server` from
  `./test/server`.
- **6b.** Arrange, first line: `server.use(...)` with an `http.get` for `/api/health` whose arrow
  function returns `new HttpResponse(null, { status: 502 })`: no body, status 502, which is what
  Vite's proxy sends when the API is stopped. Then `renderApp()`.
- **6c.** Assert: `await screen.findByText(...)` with the down label, and a third argument, an
  options object with `timeout` set to `2000`.

*Why `server.use`:* it puts a handler *in front of* the default one for this test only (step 3's
`resetHandlers` removes it afterwards), so this test reads as one story: "the API answers 502, the
badge says down". *Why the timeout:* your query retries once after 1 s before it gives up, so
`down` appears after about 1 s, right at `findBy`'s default limit. Measured: without the timeout,
this test fails at 1003 ms with the page still saying `API status unknown`. The 2000 is not a
guess: it is AC2's promise written as a number ("down within 2 s"; your comment says about 1 s, so
2 s leaves room for a slow machine). Measured: with `retry: 2`, `down` takes 2 s and this test
fails; with `retry: 3`, 3 s and it fails. So if someone makes the health check slower, a test says
so.
*Watch out:* put `server.use` *before* `renderApp()`. After it, the first request has already gone
to the default handler.
*Check yourself:* it passes in about 1 s. Then set `error` to `'ok'` in `App.tsx`'s lookup: it
fails with *Unable to find an element with the text: API down*. Undo it.

**7. The `down` test for an error answer with a body (500).** A fourth `async` test (for example
*shows "API down" when the API answers 500*), the same shape as step 6, but the override returns
`HttpResponse.json(...)` with a small problem-details object (a `title` and a `status`, like
SYSTEM.md §9's error format) **and** a second argument, `{ status: 500 }`.
*Why a second down test:* the 502 test can't tell whether your `ok` check works. Measured: delete
the `if (!response.ok) { ... }` block in `fetchHealth`, and the 502 test **still passes**:
`response.json()` on an empty body throws by itself, so the query fails anyway. A 500 with a JSON
body parses fine, so without the `ok` check the query *succeeds* and the badge says `ok`. This test
is the one that guards that check, and it is a real case: the API answers errors as problem details
(SYSTEM.md §9).
*Check yourself:* it passes. Then delete the `ok` check in `useHealth.ts` (save a copy first):
this test fails after 2000 ms with *Unable to find an element with the text: API down*, and the
502 test passes. Put the check back exactly.

**8. See what MSW's `'error'` setting does.** Temporarily make `server.ts`'s `setupServer()` have
no handler (cut the `http.get(...)` out, keep it to paste back).
*Check yourself:* the ok test fails, and above the failure MSW prints *[MSW] Error: intercepted a
request without a matching request handler: • GET /api/health*. That is `onUnhandledFrame:
'error'` naming the request nobody answered, instead of a silent wait. Paste the handler back.

**9. Run every check.** `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`,
`npx prettier . --check`.
*Check yourself:* *Tests 7 passed (7)* (three `StatusBadge`, four `App`) in about 2.5 s; everything
else passes; `dist/assets/` has no test code (MSW is not in the built app, because nothing
`main.tsx` imports uses it).

## Before you ask for a test review

- [ ] The round 4 fix is its own commit, before the tests.
- [ ] Four `App` tests, each named for the behaviour it checks, each with one `renderApp()` and one
      `expect`.
- [ ] The unknown test uses `getByText`; the other three use `await` with `findByText`; the two
      `down` tests have the 2 s timeout, and you could say why it is 2000.
- [ ] Each override uses `server.use` before `renderApp()`; the default handler is in
      `src/test/server.ts`; `setup.ts` has `listen` with `onUnhandledFrame: 'error'`,
      `resetHandlers` and `close`.
- [ ] You saw each test fail once (steps 5, 6, 7) and pass after; your code is back exactly as
      it was (`git diff` shows only test files and `package.json`/`package-lock.json`).
- [ ] `npm run lint`, `npm run typecheck`, `npm test -- --run` and `npm run build` pass.
- [ ] If you renamed `fetchHealth` or moved the lookup into `useHealth`, would every test still
      pass? (It should: the tests only know the URL and the labels.)

Then say "review the tests".
