# a0-04 · The page calls the API

Stage: ready
Branch: `a0-04-web-calls-api`
Milestone: M0 · Requirements: — ([SYSTEM.md](../SYSTEM.md))
Blocked by: a0-02, a0-03

## Goal
The page shows whether the API is up, using TanStack Query instead of hand-written fetching.

## What to build
- TanStack Query set up at the root of the app (one `QueryClient`).
- A `useHealth` hook that calls `GET /api/health`.
- The page's `StatusBadge` shows `unknown` while loading, `ok` on success and `down` on an error.
- Vite's dev server proxies `/api` to the API's port, so the browser sees one origin in development.

## Acceptance criteria
- **AC1** With the API running, the badge shows `ok`.
- **AC2** With the API stopped, the badge shows `down` within a few seconds (retry settings chosen
  and explained in the code).
- **AC3** No `fetch` inside a `useEffect` anywhere.
- **AC4** The API address is not hard-coded in components (one place: the proxy or a config module).

## Tests
Needed: MSW fakes `/api/health`; component tests for `ok` and `down`.

## Out of scope
- The API key (a0-05).
- Generated types (a0-06).

## Deviations

None yet.
