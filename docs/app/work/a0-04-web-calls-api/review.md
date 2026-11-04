# Review: a0-04 · The page calls the API

## Round 1 · 2026-11-04 · db87fd5

Checks (in `app/web`, Node 26.13.0, project TypeScript 6.0.3; working tree clean):
`npm run lint` ok ·
`npm run typecheck` ok, also `npx tsc -b --force` (not a cached result) ·
`npm test -- --run` 3 passed (the `StatusBadge` tests, unchanged) ·
`npm run build` ok ·
`npx prettier . --check` "All matched files use Prettier code style!" ·
language server: the editor runs the same checker as `tsc -b`, which reports nothing ·
`web-design-guidelines` and `vercel-composition-patterns`: not run; the page is still one heading
and one `<span>`.

AC1 was tried on your own `app/web` (a Vite dev server on port 5199, against the API you had
running). AC2 was tried on a scratch copy of your files whose proxy pointed at an empty port
(5081), which is what a stopped API looks like to Vite (connection refused, 502), so your running
API was not stopped and your files were not touched.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | `curl http://localhost:5199/api/health` returned `{"status":"ok"}` through the proxy; the page shows "API ok" |
| AC2 | no | page loaded with the API unreachable: "API status unknown" at 0.1 s, "API down" at 7.2 s. That is the library's default (3 retries, waiting 1 s, 2 s, 4 s); no retry settings are chosen and there is no comment (#1). The "API stops while the page is open" case was not tried: with no `refetchInterval`, nothing asks again until the window is refocused |
| AC3 | yes | `grep -rn "useEffect" src` prints nothing |
| AC4 | yes | `grep -rn --exclude-dir=node_modules --exclude-dir=dist "5080" .` finds only `vite.config.ts:14` |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec | must fix | `app/web/src/features/health/useHealth.ts:20` | The query has no `retry`, `retryDelay` or `refetchInterval`, and no comment explaining the numbers. So `down` takes about 7 s on load, and a page that was showing `ok` keeps showing it after the API stops. | AC2 asks for both: chosen retry settings and a comment saying why. Lesson step 9 has the arithmetic to do first. | [Query retries](https://tanstack.com/query/latest/docs/framework/react/guides/query-retries), [Important defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults), [`useQuery` reference](https://tanstack.com/query/latest/docs/framework/react/reference/useQuery); lesson step 9 |
| 2 | Standards | should fix | `app/web/src/features/health/useHealth.ts:8` | `fetch('api/health')` has no leading slash, so the browser resolves it against the current page's path. On `/` that gives `/api/health`, which is why it works today; on a page like `/batches/12` (routes come in a1-02) it gives `/batches/api/health`, which the proxy never sees. | A path that starts with `/` is relative to the origin, not to the page, so it is the same from every route. This is the "one address" pattern you will use for every API call. | [MDN — Resolving relative references to a URL](https://developer.mozilla.org/en-US/docs/Web/API/URL_API/Resolving_relative_references); lesson step 4c |
| 3 | Standards | should fix | `app/web/src/features/health/useHealth.ts:20` | The query key is `['data']`. It doesn't say which data. | The key *is* the cache entry: any later query that also uses `['data']` would get the health answer back, and the other way round. Name it after what it fetches; keys get more parts later (`['batches', id]`). | [Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys) |
| 4 | Standards | nice to have | `app/web/src/App.tsx:6` | The comment "Adjust 'unknown' or 'down' based on your exact ticket instructions" is a leftover note. The ticket says `unknown` while loading, which is what the line does. | A comment should explain the code, not ask the reader to check it. | — |
| 5 | Standards | nice to have | `app/web/src/features/health/useHealth.ts:12` | The error message uses `response.statusText`. Use `response.status` (the number) instead, or both. | `statusText` is the server's optional text after the number; over HTTP/2 it is always empty, so the message would end in nothing. The number is always there. | [MDN — `Response.statusText`](https://developer.mozilla.org/en-US/docs/Web/API/Response/statusText) |
| 6 | Standards | nice to have | `app/web/src/App.tsx:1-3` | Two import lines from `./components/StatusBadge`, and one import written with `.ts` on the end while the others have no extension. One line can import both: `type` in front of the one name that is a type, inside the braces. Then pick one style for extensions. | Small, but every file grows imports; one line per module and one style keep them easy to scan. | [TypeScript — type-only imports](https://www.typescriptlang.org/docs/handbook/modules/reference.html#type-only-imports-and-exports) |

Not a finding: `app/README.md` now says that `/api` is proxied and that the API has to run for
the badge to say `ok`. You asked for that in this conversation, so I wrote it. It's uncommitted;
read it and commit it with your next change.

Done well:
- The query function throws when `ok` is false. That is what turns the proxy's 502 into
  `'error'`; without it the badge would say `ok` with the API stopped.
- The `Record<'pending' | 'error' | 'success', ApiStatus>` lookup, indexed by the query's
  `status`: the a0-03 pattern used again, and a missing or misspelled status is a type error.
- One `QueryClient`, created once at the top of `main.tsx`, with the provider around `App`; the hook
  in `src/features/health/`; the type exported from `StatusBadge` and imported with `import type`.
  The install is its own commit, separate from the code.

Verdict: fixes needed

## Round 2 · 2026-11-04 · 70b2468

Checks (in `app/web`; working tree clean):
`npm run lint` ok ·
`npm run typecheck` ok, also `npx tsc -b --force` ·
`npm test -- --run` 3 passed ·
`npm run build` ok ·
`npx prettier . --check` "All matched files use Prettier code style!"

Tried on a fresh scratch copy of your committed `src/` and `vite.config.ts`, so your files were not
touched. For AC2 its proxy pointed at an empty port (5081), as in round 1. For AC1 I started the
API from `app/` (yours was not running) and stopped it afterwards.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | API running: the page shows "API ok" |
| AC2 | no | API unreachable: the page still showed "API status unknown" after 20 s, with 18 requests to `/api/health`, one a second. It never reaches "API down" (#1) |
| AC3 | yes | `grep -rn "useEffect" src` prints nothing |
| AC4 | yes | `5080` appears only in `vite.config.ts:14` |

Round 1 findings:

| # | Status | Note |
|---|---|---|
| 1 | open | changed, but AC2 is now further away; see below |
| 2 | fixed | `fetch('/api/health')` |
| 3 | fixed | `queryKey: ['health']` |
| 4 | open | the "Adjust 'unknown' or 'down'…" comment is still on `App.tsx:5` |
| 5 | fixed | the message uses `response.status` |
| 6 | fixed | one import line from `StatusBadge`, no extensions |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec | must fix | `app/web/src/features/health/useHealth.ts:23-25` | `retry: true` means *retry forever*. The query never gives up, so `status` never becomes `'error'` and the badge never says `down`. `retryOnMount: true` is the default already and is about something else (retrying a query that is in error when a component mounts), so it changes nothing here. There is still no `refetchInterval` (a page showing `ok` doesn't notice the API stopping) and no comment explaining the numbers. | AC2 needs a *limit*: a number of retries, so the query fails after a known time. The comment says what your numbers add up to, for the reload case and for the page-already-open case. | [`useQuery` reference: `retry`, `retryDelay`, `retryOnMount`, `refetchInterval`](https://tanstack.com/query/latest/docs/framework/react/reference/useQuery); lesson step 9 |
| 4 | Standards | nice to have | `app/web/src/App.tsx:5` | The leftover "Adjust 'unknown' or 'down'…" comment (round 1). | — | — |

Done well:
- Every round 1 finding except the two above is fixed, each the way it was meant.
- `retryDelay: 1000` is a fixed wait, which keeps the arithmetic simple once `retry` is a number.

Verdict: fixes needed

## Round 3 · 2026-11-04 · 8f5c2a6

Checks (in `app/web`; working tree clean):
`npm run lint` ok ·
`npm run typecheck` ok, also `npx tsc -b --force` ·
`npm test -- --run` 3 passed ·
`npm run build` ok ·
`npx prettier . --check` "All matched files use Prettier code style!"

Tried on a scratch copy of your committed `src/` and `vite.config.ts`, against an API I started
from `app/` and then stopped (yours was not running); your files were not touched.

| AC | Met | How checked |
|---|---|---|
| AC1 | yes | API running: "API ok" |
| AC2 | partly | **Page open, then API stopped:** "API down" 4.0 s after the stop, and it stays down (worst case by your numbers: one 5 s interval + 3 × 1 s ≈ 8 s). **Page loaded with the API already stopped:** "API down" at 3.1 s, then it **cycles**: "API status unknown" for 3 s, "API down" for 5 s, again and again (watched for 32 s: unknown at 8.1, 16.1, 24.1, 32.1 s). No comment explains the numbers. See #1 and #7 |
| AC3 | yes | `grep -rn "useEffect" src` prints nothing |
| AC4 | yes | `5080` appears only in `vite.config.ts:14` |

Round 2 findings:

| # | Status | Note |
|---|---|---|
| 1 | open | `retry: 3`, `retryDelay: 1000` and `refetchInterval: 5000` are good choices and add up as they should; the comment explaining them is still missing |
| 4 | fixed | the leftover comment is gone |

| # | Axis | Severity | Where | Finding | Why it matters | Learn more |
|---|---|---|---|---|---|---|
| 1 | Spec | must fix | `app/web/src/features/health/useHealth.ts:23-25` | No comment says what the three numbers add up to. One or two lines above them: how long until `down` on a fresh load and with the page open, and why you think that is fast enough. | AC2 asks for the settings "chosen and explained in the code". Without the comment, the next reader sees three bare numbers. | lesson step 9 |
| 7 | Spec | must fix | `app/web/src/App.tsx:5`, with `useHealth.ts:25` | While the API is down and the page has **never** had an answer, the badge says `unknown` for 3 of every 8 seconds. Why: when a query that has never had data starts a new fetch, TanStack Query sets its `status` back to `'pending'` and clears `error` (`node_modules/@tanstack/query-core/build/modern/query.js:566-575`, `fetchState`). Your `refetchInterval` starts such a fetch every 5 s, and the 3 retries keep it pending for 3 s. With data already there, `status` stays `'error'` during the refetch, which is why the page-open case is steady. | The badge says "unknown" about an API it already knows is down. This one is on the lesson, not you: it says "read `status`", and that is only true once data has arrived. The fix is in what `App` reads: `status` alone can't tell "nothing has finished yet" from "the last attempt failed and a new one is running". Look at the other fields of the query result (`fetchStatus`, `dataUpdatedAt`, `errorUpdatedAt`) and ask which of them still remembers the failure while the next fetch runs. Check yourself the same way: load with the API stopped and watch the badge for 20 s. | [`useQuery` reference, "Returns"](https://tanstack.com/query/latest/docs/framework/react/reference/useQuery); [Queries, "FetchStatus"](https://tanstack.com/query/latest/docs/framework/react/guides/queries#fetchstatus) |

Done well:
- The numbers are a limit now: `retry: 3` with a fixed 1 s wait, so the first `down` arrives at a
  time you can work out, and it did (3.1 s).
- `refetchInterval` was added, and the page-open case works as planned (4.0 s, within the 8 s worst
  case).
- Small commits, each naming the change (`finetune retry`, `remove comment`).

Verdict: fixes needed
