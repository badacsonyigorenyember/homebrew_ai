# a0-05 · API key and CORS

Stage: ready
Branch: `a0-05-api-key-and-cors`
Milestone: M0 · Requirements: §9 Security ([SYSTEM.md](../SYSTEM.md))
Blocked by: a0-04

## Goal
Only the app can call the API: every `/api` request needs the key, and only the app's origins pass
CORS.

## What to build
- A check on every `/api` route that the `X-Api-Key` header equals the configured key (an endpoint
  filter on a route group, or middleware; the lesson compares them).
- The key comes from configuration (`App:ApiKey`: user secrets in development, an environment
  variable later), never from a committed file.
- Missing or wrong key: 401 as problem details (`application/problem+json`).
- CORS: allowed origins from configuration (`App:AllowedOrigins`), for Tauri later.
- The web app sends the key from `VITE_API_KEY` in a local Vite env file that git ignores
  (`app/web/.env.local`); the settings page replaces this in a1-05.

## Acceptance criteria
- **AC1** No key → 401 problem details; wrong key → 401; right key → 200.
- **AC2** No real key in any committed file (`git grep` for it finds nothing).
- **AC3** A CORS preflight from an allowed origin passes; from another origin it is refused.
- **AC4** The page still shows `ok` with the API running.

## Tests
Needed: integration tests for the three key cases and the two CORS cases.

## Out of scope
- Users and logins (C1: one user, LAN only).

## Notes
- The project's guard hook blocks Claude from printing env files; nothing in this ticket needs that.

## Deviations

None yet.
