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
