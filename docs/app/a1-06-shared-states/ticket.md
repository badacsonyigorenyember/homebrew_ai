# a1-06 · Shared loading, empty and error states

Stage: ready
Branch: `a1-06-shared-states`
Milestone: M1 · Requirements: F1.6, §9 Errors ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-05

## Goal
Every view shows loading, empty and error the same way, and every API error arrives in the same
shape.

## What to build
- API: problem details for every error: unhandled exceptions become 500 problem details without a
  stack trace outside Development; an unknown `/api` route gives 404 problem details.
- Web: `LoadingState`, `EmptyState` and `ErrorState` components. `ErrorState` shows the problem's
  title and detail and a Retry button.
- The API client turns a problem-details response into one typed error the views can show.
- The health badge area uses `ErrorState` when the API answers with an error.

## Acceptance criteria
- **AC1** An exception thrown in an endpoint gives 500 `application/problem+json` and no stack trace
  (in a non-Development run).
- **AC2** `GET /api/does-not-exist` gives 404 problem details.
- **AC3** `ErrorState` shows the title and detail of a real problem response, and Retry calls the
  request again.
- **AC4** The three components are used from one folder, and no view writes its own spinner.

## Tests
Needed: API integration tests for the 500 and 404 shapes; component tests for `ErrorState` (shows
the detail, Retry calls back).

## Out of scope
- Logging setup beyond the defaults.

## Deviations

None yet.
