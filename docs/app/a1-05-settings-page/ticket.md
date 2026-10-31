# a1-05 · Settings page

Stage: ready
Branch: `a1-05-settings-page`
Milestone: M1 · Requirements: F1.4 ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-02

## Goal
You set the API address and key in the app, so the desktop and phone builds later need no rebuild to
point at your PC.

## What to build
- The `/settings` view: a form with API address (a URL) and API key, built with React Hook Form and
  validated with a Zod schema.
- Saved values live in `localStorage` (wrapped as in a1-03); the API client reads them, replacing
  `VITE_API_KEY`.
- A "Test connection" button calls `/api/health` with the entered values and shows the result.

## Acceptance criteria
- **AC1** An invalid URL or an empty key shows an error next to its field and does not save.
- **AC2** After saving, the health badge uses the new values without a reload.
- **AC3** "Test connection" shows success with the right key and the 401 message with a wrong one.
- **AC4** `VITE_API_KEY` is no longer read anywhere.

## Tests
Needed: form validation tests; a unit test that the API client uses the saved address and key.

## Out of scope
- Storing the key encrypted (C2: LAN only; revisit with Tauri in M7).

## Deviations

None yet.
