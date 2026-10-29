# S11 · Brew day: brew from the sheet and log every step

Status: draft
Slug: s11-brew-day · Branch: s11-brew-day
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) S11, checkpoint **G7** (the brew part) ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §8 P8
Needs: [`m8-recipe-sheet-chat`](../m8-recipe-sheet-chat/brief.md) shipped (an accepted recipe
with a saved sheet)

## Why
G7's bar ends with "you brew one": the sheet is only proven when a real batch is brewed from it.
m8 writes the sheet; it does not cover the brew itself (moved out of m8 on 2026-10-29). Your
words: "I will brew my next beer using this, so we could create a controlled
environment/session where I would brew the beer, and mark down every step, every temp, every
time, etc." Without a log made from the sheet, the brew leaves no record of where the plan and
the real batch differed.

## Goal
You brew one accepted recipe in a Claude session that walks the sheet step by step. Each step's
planned and actual temperature, time and gravity are in a log file under `docs/brews/`, and the
outcome is in PROJECT.md §8. This closes G7.

## Scope
In:
- A brew-day log made from a saved recipe and its sheet: one Markdown file under `docs/brews/`,
  with every step from water to packaging, the planned values from the saved recipe, and empty
  places for the actual values and notes. Starting point, carried over from the m8 plan's former
  Task 12: `evals/brew_log.py` (`python -m evals.brew_log <recipe_id> [--out PATH]`, a pure
  `render(recipe, items, process)`), file name `docs/brews/<date>-<style>-r<id>.md`, one table
  `Step | Planned temp | Planned time | Planned gravity | Actual temp | Actual time | Actual
  gravity | Notes`. Rows: water and salts (grams per water), strike (temperature, litres), each
  mash step, sparge (litres), pre-boil (volume), boil (minutes) and each addition, chill and
  pitch (OG, yeast amount), each fermentation step (temperature, days, the `move_on` trigger in
  Notes), dry hops, secondary, conditioning or lagering (FG on the last fermentation row),
  packaging (CO₂ volumes, priming sugar grams).
- A controlled Claude session for brew day: Claude reads the log, takes you through it one step
  at a time, and writes what you report (temperature, clock time, gravity, notes) into the file
  as you go. Fermentation and packaging take days to weeks, so the same log is picked up again
  in later sessions.
- Recording the outcome in PROJECT.md §8 and marking G7 met in WORKFLOW-ROADMAP.

Out:
- The database batch log and "learn from the results" (Priority 2, PROJECT.md §2).
- Live corrections computed in the session (for example a gravity or volume fix): brewing maths
  is deterministic, tested code and is never asked of the LLM (CLAUDE.md). The session records
  the miss and points to the sheet.
- Changing the recipe, the sheet or the pipeline from what the brew shows; those findings become
  TODOs in RECIPE-ROADMAP §8 Later.
- Post-brew tasting and comparing the result with the sheet (Open question 3).

## Requirements
R1. `python -m evals.brew_log <recipe_id>` writes the log for a recipe that has a sheet. It
    refuses a recipe without a sheet, and never overwrites an existing log.
R2. The log has a row for every water, mash, boil, fermentation and packaging step of the saved
    `process`, in brewing order. Each planned value equals the saved one; a value the recipe
    does not have is `—`. OG and FG sit on their rows. The actual columns start empty.
R3. The log's header names the recipe id, style, batch size, the sheet's date and how the log is
    filled in during a Claude session.
R4. On brew day, a Claude session fills the log step by step from what you report: actual
    temperature, clock time and gravity, or a note why a value was not taken. Claude writes only
    what you report and computes nothing.
R5. The filled log is committed, and PROJECT.md §8 records the brew and its outcome (G7).

## Constraints
- CLAUDE.md: brewing maths is deterministic, tested code; the LLM never computes gravity, IBU,
  colour or scaling, and a skill is never a substitute for that code.
- PROJECT.md §6.8: readable over optimal; the log script readable from its own file.
- §6.9: where the session explains a step, *How to Brew* first.
- The log reads the saved recipe only (`app.recipe`, `recipe_item`, `process`, `sheet`); no
  database writes, unless Open question 2 says otherwise.

## Assumptions
- m8 ships with `app.recipe.sheet` and accepted (`final`) recipes *(unverified until m8 ships)*.
- The saved `process` holds every planned value the log needs except pre-boil gravity, which no
  step saves (it has `volumes.preboil_l`, measured in `shared/contracts/process.output.schema.json`
  2026-10-29); see Open question 1.
- You have a thermometer, a clock and a hydrometer or refractometer, and report gravity as SG
  *(unverified)*.

## Acceptance criteria
A1. `python -m evals.brew_log <id>` on an accepted m8 recipe writes
    `docs/brews/<date>-<style>-r<id>.md`; run again, it refuses to overwrite; on a recipe without
    a sheet it refuses (R1).
A2. `tests/test_brew_log.py`: every mash, boil, fermentation and packaging step of a saved m7
    process has a row with its saved temperature and time, OG and FG are on their rows, and the
    actual columns are empty (R2, R3).
A3. After brew day and packaging, the committed log has an actual value or a note on every row
    (R4, R5).
A4. PROJECT.md §8 records the brew and its outcome, and WORKFLOW-ROADMAP marks G7's "you brew
    one" met (R5).

## Open questions
1. Pre-boil gravity — options: a) compute it in code from the saved OG and volumes with s1's
   functions and show it as planned; b) leave it `—` and record only the actual reading —
   recommend a: it is the most useful check on brew day, and the maths library already has the
   gravity and volume functions.
2. How the session is run — options: a) a small project skill `brew-day` that opens the log and
   walks it row by row; b) instructions in the log's header only; c) b plus setting the recipe's
   `status` to `brewed` at the end — recommend a: the same steps every brew day, and the skill
   holds no maths.
3. After the brew — options: a) add tasting notes and a planned-vs-actual summary (OG, FG, ABV
   from the readings) to the same log, still in s11; b) leave them to the Priority 2 batch log —
   recommend a for tasting notes only; the summary numbers need code, which belongs with the
   batch log.

## Deviations
- 2026-10-29 · Created from m8: the brew-day log (m8 R13), the brew (m8 A9) and m8 plan Tasks 12
  and 14 moved here, your decision ("move brew day ... into its own side track s11-brew-day").
