# M2 follow-up · Adjunct role from step 1, not from word rules

Status: approved
Slug: m2-adjunct-role · Branch: m2-adjunct-role
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M2 (G1, G2) · PROJECT.md §5 (style-guide
rule, specialty pick) and the known limitation in the §8 entry "Shipped `m2-best-fit-style`"
Needs: `m2-best-fit-style` shipped ([docs/finished/m2-best-fit-style/](../../finished/m2-best-fit-style/plan.md))

## Why
Step 2 (`app.step2_best_style`, `db/022_step2.sql`) picks a specialty style when an adjunct is a
prominent feature of the request (b12 honey that "shines" → 31B) and the base style when it is
minor (b19 "some honey" → 17C). That decision is a hand-made English parser in SQL
(`app.adjunct_cue`, `app.adjunct_is_prominent`): cue stems, dampers, joining words that end a
damper's reach, `DAMPER_GAP` and clause rules. It does not generalise: each m2 review round found a
new wording and added a word (findings 4, 12, 15, 19 in
[review.md](../../finished/m2-best-fit-style/review.md)), and open findings 16 and 17 show more gaps.
Whether the user wants an adjunct to stand out is language understanding, which is step 1's job;
the project rule only keeps the LLM away from brewing maths.

## Goal
Step 1 gives every ingredient it extracts as wanted a role, `feature` or `background`, checked by
its output contract. Step 2 reads that role by code, and the word-rule parser and its tests are
gone. This happens only after a measurement shows step 1's roles are accurate and consistent
enough on the local D2 model (the gate below).

## Scope
In:
- Step 1: a role per wanted item in the output contract (`shared/contracts/step1.output.schema.json`),
  the prompt (`shared/prompts/step1.system.md`), the answer check (`app.step1_read_answer`) and the
  step 1 grader (`evals/grade.py`), with expected roles in `evals/recipe_briefs.toml`.
- A role measurement set (the wordings listed under R5) kept in the repo, a way to run step 1 on it
  N times through the real workflow, and a saved result.
- The gate: measure first; stop and ask the user if the bar is not met.
- After the gate: step 2 reads the role, its input contract text is updated, the reason cites the
  role, and `app.adjunct_cue`, `app.adjunct_is_prominent`, the cue, damper and joining-word lists,
  `DAMPER_GAP` and their tests are deleted (in the repo and in the database).
- PROJECT.md (§4, §5, §8, the known limitation), `docs/DATABASE.md` (signal-function line) and
  WORKFLOW-ROADMAP G1/G2 "Measured" lines.

Out:
- The other hard-coded lists in step 2: style aliases, BJCP catch-all codes, style pairs, the
  specialty list (`app.specialty_style`). They are guideline facts and stay.
- Open findings 14 and 18 of the m2 review.
- Any other step 2 behaviour: guide override, style pairs, catch-all exception, tight-fit number
  score, `NO_NAME_FACTOR`, alternatives window.
- Using the role anywhere other than step 2's specialty pick (steps 3+ are not built).
- Changing the D2 model or step 1's call settings (temperature 0, seed 42).

## Requirements
R1. Each `wanted` item in step 1's output is an object `{"item": "<the user's words>", "role":
    "feature" | "background"}` (user decision). The step 1 output contract rejects an item without
    `item` or `role`, a role outside those two values, and extra keys.
R2. Meaning of the roles, written into the prompt: `feature` = the user wants this ingredient to be
    noticeable and to define the beer (stand out, lead, be tasted clearly). `background` = it is in
    the beer but minor, supporting, or there for a function (body, dryness, colour), or the user
    does not say it should stand out. `background` is the default, so a plain "with honey" is
    `background` and keeps the base style (PROJECT.md §5).
R3. The 22 test briefs carry an expected role for each wanted item, and the step 1 grade of
    `wanted` counts the role: an item with the right words and the wrong role fails `wanted`
    (user decision: inside `wanted`, so it counts in G1). Expected roles (user decision): b12
    honey `feature`; b02 oats, b06 rice, b07 corn, b16 rice, b19 honey, b20 lactose `background`.
R4. Measurement before any deletion: step 1 with the new field runs on the role measurement set
    (R5) on the D2 model through the real step 1 workflow, 3 runs per wording, at the pipeline's
    settings (temperature 0, seed 42); this is the gated run. A second, report-only run does the
    same at temperature 0.8 with 3 different seeds, to show how close answers are to flipping; it
    is not part of the bar (user decision). The result reports, for both runs and per wording, the
    role given to the scored adjunct in each run, accuracy against the expected role, run-to-run
    consistency, and, for reference only, what the current word rule (`app.adjunct_is_prominent`)
    says on the same set.
    A wording where step 1 leaves the adjunct out of `wanted` counts as wrong. The result is saved
    in `evals/results/<date>-<label>.json`.
R5. The role measurement set holds b12, b19 and every adjunct wording from the m2 review
    (findings 4, 12, 15, 16, 17, 19), with these expected roles for honey:
    - `feature` (14): b12; "A blonde ale where the honey really shines."; "A honey ale that
      showcases the honey."; "Honey-forward, with some citrus hops."; "Plenty of honey and some
      citrus."; "Lots of honey and a little lemon zest."; "Honey forward and some citrus."; "I want
      some citrus and honey forward."; "Honey forward with some citrus."; "Lots of honey with a
      little lemon zest."; "Honey up front with a hint of ginger."; "A honey-forward ale with a
      touch of spice."; "Plenty of honey, with a little lemon."; "I want the honey to shine with a
      bit of orange peel."
    - `background` (7): b19; "A 5% blonde ale with honey that is subtle, with the hops up front.";
      "I want honey that is subtle, with the hops up front."; "The honey should be subtle and the
      hops forward."; "Honey in a slight supporting role while the hops dominate."; "A blonde with
      honey that stays slight, hop flavour forward."; "A pale ale with honey, but keep it subtle,
      and citrus hops up front."
    - ambiguous, finding 17 (3), reported but not scored for accuracy (user decision): "A pale ale
      with a touch of orange blossom honey that you can taste."; "A little bit of orange blossom
      honey, you should taste it."; "a touch of wildflower honey I can taste"
    - held out (10, user decision; the bar in R6 is out of 10): fresh wordings written in the plan
      before the prompt is changed, with their expected roles approved by the user together with
      the plan, and never used to tune the prompt. They include molasses and a few non-specialty adjuncts (fruit,
      spice, coffee), scored on that adjunct's role.
R6. Gate (bar decided by the user): on the gated run (temperature 0, seed 42, 3 runs) all of
    these hold:
    - b12 is `feature` and b19 is `background` in every run;
    - at least 20 of the 21 clear-cut wordings are right in every run;
    - every wording (clear-cut, ambiguous and held out) gets the same role in all 3 runs;
    - at least 9 of 10 held-out wordings are right in every run.
    Only then does the work go past the measurement. If any point fails, the flow stops and
    reports the result to the user; nothing is deleted and step 2 is not changed.
R7. After the gate, step 2 picks the specialty style when a wanted item that has a specialty style
    for the base's guide (`app.specialty_style`) has role `feature`, and the base style otherwise.
    It no longer reads the request text for prominence (it still reads it for a named guide).
R8. The specialty reason names the adjunct and cites step 1's role instead of a cue word, e.g.
    `Picked 31B Alternative Sugar Beer: honey has the role "feature" in step 1's brief; base style 18A.`
R9. `app.adjunct_cue`, `app.adjunct_is_prominent`, the CUES, DAMPERS and joining-word lists,
    `DAMPER_GAP` and the tests that exercise them are deleted from the repo, and the two functions
    are dropped from the database by a `.sql` file.
R10. No regression: step 2 passes 22/22 on `evals/recipe_briefs.toml` on the real pipeline,
    including b05 15B (mismatch 20C), b12 31B, b19 17C, b17 8B; step 1 is not worse than the last
    measured run (21/22, only b05 `hints` wrong, `evals/results/2026-10-13-m2-fix3.json`), with
    roles now counted; all other step 2 tests still pass.

## Constraints
- Brewing maths stays deterministic code; the role is language understanding, not maths
  (CLAUDE.md). Step 2 stays deterministic: it reads the role, no LLM call (PROJECT.md §6.7).
- Small LLM step with a checkable contract (§6.2): the role is checked by the step 1 contract with
  `pg_jsonschema`, by n8n and by tests. `background` is the legal default answer (§6.3).
- Measure before and after (§6.6): the gate measurement before deletion, G1/G2 re-run after.
- Readable over optimal (§6.8, CLAUDE.md).
- DB changes are `.sql` files applied with `psql` as `postgres` (OPERATIONS.md §4); the Supabase
  MCP is read-only. Dropping functions goes in a `.sql` file too.
- Workflows are edited in n8n and exported to `n8n/workflows/` (`python -m evals.workflows`); the n8n
  MCP drops `onError` (PROJECT.md §8, m2 Task 6).
- Contracts live in `shared/contracts/`, the prompt in `shared/prompts/`. Eval results go to
  `evals/results/<date>-<label>.json`.
- No git worktrees; plain branch `m2-adjunct-role`.

## Assumptions
- At temperature 0 and seed 42, D2 gives the same answer in every run, as the m1 benchmark found
  (run counts identical across 3 runs). So 3 runs at pipeline settings test consistency only
  weakly *(unverified for the new field)*; hence the report-only run at temperature 0.8 (R4).
- Adding the role does not push step 1's median time far above 12.5 s *(unverified)*.
- Nothing outside step 2, the step 1 check, the graders and tests reads `wanted` yet (checked by
  grep: `db/022_step2.sql`, `evals/grade.py`, `tests/`); steps 3+ are not built.
- `app.specialty_style` (honey, molasses for BJCP 31B; honey for BA `specialty-honey-beer`) is the
  whole list of adjuncts with a specialty style (checked in `db/022_step2.sql`).
- Both functions to delete exist in the database, owned by `postgres` (checked in `pg_proc`,
  2026-10-13).

## Acceptance criteria
A1. The step 1 output contract requires each wanted item to be `{"item", "role"}` with role in
    {`feature`, `background`}; contract tests reject a plain string item, a missing role and an
    unknown role (R1).
A2. The step 1 prompt defines both roles and the `background` default as in R2; `tests/test_prompt.py`
    or a new test checks the prompt names both values (R2).
A3. Every wanted item in `evals/recipe_briefs.toml` has an expected role; a grader test shows a
    wrong role fails `wanted` (R3).
A4. A results file in `evals/results/` holds the role measurement for the gated run and the
    report-only temperature 0.8 run: per wording, the expected role (or "ambiguous"), the role in
    each of 3 runs, accuracy, consistency and the word rule's answer; its numbers and the R6
    verdict, point by point, are copied into `plan.md` and PROJECT.md §8 (R4, R5, R6).
A5. The measurement set is a versioned file in the repo holding every wording in R5 with its
    expected role, and marks which wordings are fresh (held out) (R5).
A6. The gate decision is recorded in `plan.md` before any deletion commit: bar met, or the flow
    stopped and the user was asked (git history shows no deletion commit before it) (R6).
A7. With a hand-made brief whose wanted honey has role `feature` and a request that has no cue
    word, step 2 picks 31B with base 18A as an alternative; with role `background` and the b12
    request text, it picks 18A (R7).
A8. The b12 specialty reason contains `feature` and no quoted cue word (R8).
A9. `grep -rn "adjunct_cue\|adjunct_is_prominent\|DAMPER" db tests evals shared n8n` finds nothing,
    and `pg_proc` has no `app.adjunct_cue` or `app.adjunct_is_prominent` (R9).
A10. G2 re-run on the real pipeline (`evals.run --save`): step 2 22/22 with b05 15B + mismatch
    20C, b12 31B, b19 17C, b17 8B; step 1 ≥ 21/22 with roles counted; `pytest` all passed (R10).

## Open questions
None. The six questions of the first draft were answered by the user on 2026-10-13 and are folded
in: gate bar (R6), ambiguous finding-17 wordings reported, not scored (R5), `{item, role}` objects
(R1), role graded inside `wanted` with the listed expected roles (R3), gated run at pipeline
settings plus a report-only run at temperature 0.8 (R4), 10 held-out wordings with labels
approved with the plan (R5).

## Deviations
