# a1-08 · Brew-day step generator

Stage: ready
Branch: `a1-08-brew-day-steps`
Milestone: M1 · Requirements: F4.4, §7 Brew day row ([SYSTEM.md](../SYSTEM.md))
Blocked by: a1-06

## Goal
A new batch gets its brew-day checklist, generated from the recipe's saved `process`.

## What to build
- A pure C# function in `Features/Batches/` that takes a batch's `process` and items and returns
  the Brew day steps in §7's order. No database and no clock: data in, list of steps out.
- Each step has a title, its planned values as a list of `{ key, label, value, unit }` (so a1-10
  can show any step's fields the same way) and its source path, for example `mash.steps[0]`.
- The `process` is read into small typed records for the keys the brew-day row uses (the lesson
  compares this with reading `JsonElement` directly).
- Every number is copied from the `process`; none is computed (C4). The measure-OG step's planned
  gravity is the batch's `og`.
- Creating a batch (a1-06) now saves the steps as `batch_step` rows: phase `brew_day`, position in
  order, date the brew date, the source path, no actual values yet.
- A key the brew-day row needs that is missing fails batch creation with 400 naming its path, so a
  change in the pipeline's output is noticed. An empty list (no mash additions, no whirlpool) gives
  no steps, not an error.

## Acceptance criteria
- **AC1** For recipe 1349's process (the test fixture's), the steps are, in order: strike water
  salts, sparge water salts, heat 17.1 L strike water to 72.7 °C, mash in 5.7 kg, saccharification
  rest 66.5 °C 60 min, mash-out 77 °C 10 min, sparge 14.6 L, pre-boil volume 26 L, boil 60 min,
  Columbus 37 g at 60 min, whirlpool Citra 28 g, chill, measure OG, pitch SafAle US-05 23 g.
- **AC2** Boil additions come longest first, whatever their order in the `process`.
- **AC3** A process without `mash.volumes.strike_l` fails with that path in the message.
- **AC4** A created batch has its brew-day steps, and every step's source path points to a value
  that exists in the batch's `process`.

## Tests
Needed: unit tests on the pure function (the full process, empty lists, a missing key, boil order)
and one integration test that creating a batch saves its steps.

## Out of scope
- Ferment, Condition and Package steps, and dates other than the brew date (M3).
- Your own steps (M3).

## Deviations

None yet.
