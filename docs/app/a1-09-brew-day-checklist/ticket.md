# a1-09 · Brew-day checklist

Stage: ready
Branch: `a1-09-brew-day-checklist`
Milestone: M1 · Requirements: F4.8, F4 layout ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-07, a1-08

## Goal
On brew day you open the batch and tick off each step as you do it.

## What to build
- `GET /api/batches/{id}`: the batch (number, name, style, brew date, status, OG, FG, ABV, IBU,
  SRM), its items grouped as fermentables, hops, yeast and extras, and its brew-day steps in order.
- `PATCH /api/batches/{id}/steps/{stepId}` with `done`: true sets `done_at` to now (UTC), false
  clears it; it returns the step. a1-10 adds more fields to the same endpoint.
- The `/batches/:id` view: the key numbers at the top, "Brew day · 3/14", and the steps as a
  checklist (tick box, title, planned values on one line, the time when ticked). The batch recipe
  sits beside the checklist on wide screens and below it on narrow ones.
- Tap targets at least 44 px high, for wet hands and a tablet on the bench.

## Acceptance criteria
- **AC1** Ticking a step shows its time and moves the count; a reload keeps both.
- **AC2** Unticking clears the time.
- **AC3** An unknown batch, or a step of another batch, gives 404; the view shows "batch not found".
- **AC4** A failed tick shows a message and the box goes back to how it was.
- **AC5** At phone width the recipe is below the checklist and nothing scrolls sideways.

## Tests
Needed: integration tests for get, tick, untick and the 404 cases; component tests with MSW for
ticking and a failed tick.

## Out of scope
- The stepper and the other phases, the lock and timers (M3).

## Deviations

None yet.
