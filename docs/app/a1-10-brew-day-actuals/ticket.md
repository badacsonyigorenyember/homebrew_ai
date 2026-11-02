# a1-10 · Actual values and notes

Stage: ready
Branch: `a1-10-brew-day-actuals`
Milestone: M1 · Requirements: F4.9, F4.11 (OG) ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-09

## Goal
You write down what really happened on each step, so the brew log keeps planned and actual side by
side.

## What to build
- Tapping a step expands it in place: each planned value with an actual field beside it, and a
  free-text note. An empty actual means "as planned", so the field starts with the planned number.
- Save sends `actual` and `note` through the a1-09 `PATCH`. Only keys from the step's planned
  values are accepted, and each must be a number.
- A step whose actual differs from its planned value shows "differs from plan" when collapsed.
- The measure-OG step's actual gravity is the batch's measured OG, shown in the header beside the
  planned OG.

## Acceptance criteria
- **AC1** Changing the rest temperature to 67 saves it, the step shows "differs from plan", and a
  reload keeps both.
- **AC2** A note is saved and shown.
- **AC3** An unknown key or a non-number gives 400 with a field message.
- **AC4** Enter saves, Escape cancels and restores the old values.
- **AC5** Entering an OG on the measure-OG step shows it in the header.

## Tests
Needed: integration tests for saving actuals and a note, an unknown key and a non-number; component
tests with MSW for expand, edit, the "differs" mark and cancel.

## Out of scope
- Timers (M3).
- Measured ABV and attenuation, which need the FG and `app.abv` (M3).

## Notes
- To use the checklist from a tablet or phone on brew day, run the Vite dev server with `--host`;
  the proxy (a0-04) keeps one origin. Until a2-01 the API has no key, so do this only on your home
  network.

## Deviations

None yet.
