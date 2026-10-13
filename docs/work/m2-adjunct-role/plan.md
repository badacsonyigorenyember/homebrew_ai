# M2 follow-up · Adjunct role from step 1 — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: m2-adjunct-role

## Approach
Step 1's `wanted` items become `{"item", "role"}` objects. The contract, the prompt and the grader
change first, and step 2 keeps its word rule but reads the item word from the new shape
(`w ->> 'item'`). This changes the shape it reads, not how it decides, so the pipeline keeps working
whatever the gate says. A small eval tool (`evals/roles.py`) then sends the role measurement set
(`evals/role_wordings.toml`) through the real pipeline webhook, at the pipeline settings and at
temperature 0.8. For that, the webhook gains optional `temperature` and `seed` fields that reach
step 1's Ollama call; the defaults stay 0 and 42. The tool works out the R6 verdict in tested code.
**Task 6 is the gate and a hard stop point.** Only when the bar is met does step 2 switch to the
role (Task 7). The word rule is deleted after that (Task 8), and G1/G2 are measured again (Task 9).
The held-out wordings are written below, before any prompt change, and committed in Task 1. They
run only in the full measurement, so the prompt can't be tuned on them.

## Role measurement set (R5)
The ids are the ones `evals/role_wordings.toml` uses. `adjunct` is the word whose role is scored.
Sets: `clear` (scored), `ambiguous` (reported, not scored), `held_out` (scored, out of 10).

| Id | Set | Adjunct | Expected | Wording |
|---|---|---|---|---|
| r01 | clear | honey | feature | b12's request (copied from `recipe_briefs.toml`) |
| r02 | clear | honey | feature | A blonde ale where the honey really shines. |
| r03 | clear | honey | feature | A honey ale that showcases the honey. |
| r04 | clear | honey | feature | Honey-forward, with some citrus hops. |
| r05 | clear | honey | feature | Plenty of honey and some citrus. |
| r06 | clear | honey | feature | Lots of honey and a little lemon zest. |
| r07 | clear | honey | feature | Honey forward and some citrus. |
| r08 | clear | honey | feature | I want some citrus and honey forward. |
| r09 | clear | honey | feature | Honey forward with some citrus. |
| r10 | clear | honey | feature | Lots of honey with a little lemon zest. |
| r11 | clear | honey | feature | Honey up front with a hint of ginger. |
| r12 | clear | honey | feature | A honey-forward ale with a touch of spice. |
| r13 | clear | honey | feature | Plenty of honey, with a little lemon. |
| r14 | clear | honey | feature | I want the honey to shine with a bit of orange peel. |
| r15 | clear | honey | background | b19's request (copied from `recipe_briefs.toml`) |
| r16 | clear | honey | background | A 5% blonde ale with honey that is subtle, with the hops up front. |
| r17 | clear | honey | background | I want honey that is subtle, with the hops up front. |
| r18 | clear | honey | background | The honey should be subtle and the hops forward. |
| r19 | clear | honey | background | Honey in a slight supporting role while the hops dominate. |
| r20 | clear | honey | background | A blonde with honey that stays slight, hop flavour forward. |
| r21 | clear | honey | background | A pale ale with honey, but keep it subtle, and citrus hops up front. |
| r22 | ambiguous | honey | – | A pale ale with a touch of orange blossom honey that you can taste. |
| r23 | ambiguous | honey | – | A little bit of orange blossom honey, you should taste it. |
| r24 | ambiguous | honey | – | a touch of wildflower honey I can taste |
| h01 | held_out | molasses | feature | A dark brown porter built around molasses, I want its flavour front and centre. |
| h02 | held_out | molasses | background | An old ale with a spoonful of molasses for colour. |
| h03 | held_out | raspberry | feature | A wheat beer bursting with raspberry, it should taste like fresh fruit. |
| h04 | held_out | cherry | background | A pale ale with a little cherry in the secondary, but the hops are the point. |
| h05 | held_out | coffee | feature | A stout where the coffee is the main event, like an iced latte. |
| h06 | held_out | coffee | background | A brown ale with a little coffee to dry out the finish. |
| h07 | held_out | cinnamon | feature | A winter warmer where cinnamon leads the aroma and the taste. |
| h08 | held_out | cinnamon | background | A dunkel with a pinch of cinnamon that nobody should notice. |
| h09 | held_out | honey | feature | A golden ale made to show off wildflower honey. |
| h10 | held_out | honey | background | An amber ale with honey added for a drier finish. |

The held-out wordings and labels (h01–h10) were approved as written by the user on 2026-10-13 (brief R5).

## Files
| Path | New / changed | Purpose |
|---|---|---|
| `evals/role_wordings.toml` | new | The role measurement set above (R5, A5) |
| `tests/test_role_wordings.py` | new | Shape and counts of the set; b12/b19 match the briefs |
| `tests/test_prompt.py` | changed | Prompt names both roles; quotes no measurement wording |
| `shared/contracts/step1.input.schema.json` | changed | Optional `temperature`, `seed` |
| `shared/contracts/step1.output.schema.json` | changed | `wanted` items are `{item, role}` (R1) |
| `shared/contracts/step2.input.schema.json` | changed | Description: `request` is read for guide words only (Task 7) |
| `shared/prompts/step1.system.md` | changed | Role definitions and the `background` default (R2) |
| `n8n/workflows/step-1-read-request.json` | changed (export) | Uses `temperature`/`seed` and logs them in `llm` |
| `n8n/workflows/recipe-pipeline.json` | changed (export) | Webhook `temperature`/`seed` → step 1 |
| `db/020_step1.sql` | changed | Header comment: `wanted` holds objects (no logic change) |
| `db/022_step2.sql` | changed | Read `item` (Task 4), pick by role (Task 7), word rule removed (Task 8) |
| `db/023_drop_adjunct_rule.sql` | new | Drops the two word-rule functions (R9) |
| `evals/recipe_briefs.toml` | changed | `wanted` entries carry the expected role (R3) |
| `evals/grade.py` | changed | `wanted` graded on (item, role) pairs (R3) |
| `evals/run.py` | changed | `send()` takes optional `temperature`, `seed` |
| `evals/roles.py` | new | Runs the measurement set, computes the R6 verdict, saves the result |
| `tests/test_roles.py` | new | Scored-role lookup and gate verdict (unit) |
| `tests/test_grade.py`, `tests/test_recipe_briefs.py`, `tests/test_contracts.py`, `tests/test_step1_check.py`, `tests/test_pipeline.py`, `tests/test_step2_pick.py`, `tests/test_step2_signals.py`, `tests/test_run.py` | changed | Follow the new shape; new role tests; word-rule tests removed |
| `evals/results/<date>-m2-role-g1.json`, `<date>-m2-role-gate.json`, `<date>-m2-role.json` | new | Measured results |
| `docs/OPERATIONS.md` | changed | §5 webhook body and the Ollama options line: `temperature`, `seed` |
| `docs/DATABASE.md` | changed | Signal-function line (Task 8) |
| `docs/WORKFLOW-ROADMAP.md` | changed | G1/G2 Measured lines (Task 9) |
| `PROJECT.md` | changed | §4, §5, §8 per task |

## Tasks

### Task 1: The role measurement set is in the repo
Why: R5, A5. The held-out wordings must be fixed before the prompt changes.
- [x] Write `evals/role_wordings.toml` with one `[[wording]]` per row of the table above:
      `id`, `set` (`clear` / `ambiguous` / `held_out`), `adjunct`, `expected` (`feature` /
      `background`, or `""` for ambiguous), `source` (`b12`, `b19`, `m2 review`, `m2 review
      finding 17`, `held out`), `request`. For r01 and r15, copy b12's and b19's request text exactly.
      Add a header comment that says what the file is for, and that held-out wordings must never be
      used to tune the prompt.
- [x] Write `tests/test_role_wordings.py` (no stack): ids are unique. The counts are 21 clear
      (14 feature, 7 background), 3 ambiguous (expected `""`) and 10 held out (5 feature,
      5 background). Each `adjunct` appears in its request as a whole word (case ignored, hyphens
      read as spaces). r01 and r15 equal b12's and b19's requests. The held-out set includes
      `molasses` and at least three non-specialty adjuncts.
- [x] Extend `tests/test_prompt.py::test_prompt_quotes_no_brief` (or add a sibling test) so the
      prompt quotes no 5-word run from any measurement wording either.
- [x] Run `.venv/bin/pytest tests/test_role_wordings.py tests/test_prompt.py`, expect all passed.
Done when: the file holds the 34 wordings with the labels the user approved, and the tests pass.
Commit: `Add role measurement set`

### Task 2: The webhook can set step 1's temperature and seed
Why: R4. The report-only run at temperature 0.8 with 3 seeds goes through the real workflow. The
defaults stay temperature 0 and seed 42 (brief Out: call settings unchanged).
- [x] `shared/contracts/step1.input.schema.json`: add optional properties `temperature`
      (`number`, 0 to 2) and `seed` (`integer`). Leave them out of `required`, so the existing
      Test data samples stay valid.
- [x] `Step 1 · read request` (it has no `onError` node, so the n8n MCP `update_workflow` is
      safe here). The trigger gains the inputs `temperature` (number) and `seed` (number). `Check
      step 1 input` passes them in its `value`. `Build model request` uses
      `temperature: <input> ?? 0, seed: <input> ?? 42` (a missing sub-workflow input arrives as
      missing, OPERATIONS §5). `Return first answer` and `Return second answer` add
      `temperature` and `seed` to `llm`, read from `Build model request`'s `options`, so the log
      shows what was sent. Publish it.
- [x] `Recipe pipeline` has `onError` nodes, so use the JSON route in OPERATIONS §5: edit
      `n8n/workflows/recipe-pipeline.json`, copy it to `shared/`, run `import:workflow`, publish
      through the MCP, then delete the copy. `Run settings` adds
      `temperature: $json.body?.temperature ?? 0` and `seed: $json.body?.seed ?? 42`. `Step 1 ·
      input`, the `Step 1 · read request` call's inputs, and both step 1 log nodes' `input` JSON
      carry them. Publish step 1 before the pipeline.
- [x] Run `python -m evals.workflows` to re-export the workflows.
- [x] `evals/run.py`: `send()` gains keyword arguments `temperature=None, seed=None`, and adds
      them to the body only when they are given.
- [x] Tests: in `tests/test_contracts.py`, a good `step1.input` with `temperature` 0.8 and `seed`
      1, and a bad one with `seed` 1.5. In `tests/test_pipeline.py`, update
      `test_b01_logs_step_1`'s expected `step_input`, which now holds `temperature: 0, seed: 42`.
      New `test_default_temperature_and_seed` (no fields sent: `llm.temperature == 0`,
      `llm.seed == 42`) and `test_temperature_and_seed_reach_step_1` (sent 0.8 and 1: step 1's
      input and `llm` both show 0.8 and 1).
- [x] Update `docs/OPERATIONS.md` §5 (the webhook body line, and the Ollama options line) and the
      PROJECT.md §4 `Recipe pipeline` webhook fields.
- [x] Run `.venv/bin/pytest`, expect all passed (`test_repo_files_match_n8n` included).
Done when: a webhook call with `temperature`/`seed` logs those values in step 1's `llm`, and a
call without them logs 0 and 42.
Commit: `Let the webhook set step 1 temperature and seed`

### Task 3: Briefs carry expected roles and the grader counts them
Why: R3, A3.
- [x] `evals/recipe_briefs.toml`: each `wanted` entry becomes an inline table
      `{ item = "...", role = "..." }`, with b12 honey `feature`; b02 oats, b06 rice, b07 corn,
      b16 rice, b19 honey, b20 lactose `background`. Update the header comment for `wanted`
      (an item and its role; what each role means, as in R2).
- [x] `evals/grade.py`: `wanted` is right when the set of `(clean item, role)` pairs equals the
      brief's set. Clean items with `_clean_set`'s rules, so the synonym and form-word rules still
      apply. A plain-string item or a missing role counts as wrong. `excluded` and `inventory` are
      unchanged.
- [x] `tests/test_recipe_briefs.py`: the shape check accepts `wanted` items as tables with exactly
      `item` (non-empty string) and `role` (`feature` / `background`). `coverage`,
      `test_no_fruit_or_non_gravity_extras` and `test_words_are_the_users` read `item`.
- [x] `tests/test_grade.py`: `right_step1` keeps the objects. `test_step1_each_field_can_fail` uses
      `[{"item": "x", "role": "background"}]`. Update the synonym and form-word tests to objects.
      New `test_wrong_role_fails_wanted` (b12 with honey `background` → `wanted` False) and
      `test_right_role_passes_wanted`.
- [x] `tests/test_step2_pick.py`: `brief_of` passes the objects through, and the smoke porter brief
      uses `[{"item": "smoked malt", "role": "background"}]`. `tests/test_run.py`: the fake step 1
      output uses an object item.
- [x] Run `.venv/bin/pytest`, expect all passed. Do not run `evals.run` until Task 4 is done (a
      live run would grade old-shape answers as wrong).
Done when: a wrong role fails `wanted` in a unit test, and the suite passes.
Commit: `Grade wanted items with their role`

### Task 4: Step 1 gives every wanted item a role
Why: R1, R2, A1, A2.
- [x] `shared/contracts/step1.output.schema.json`: `wanted.items` becomes
      `{"type": "object", "required": ["item", "role"], "additionalProperties": false,
      "properties": {"item": {"type": "string", "minLength": 1}, "role": {"enum": ["feature",
      "background"]}}}`. Put `item` before `role`, so the model writes the item first. Keep
      `uniqueItems` and `maxItems`.
- [x] `shared/prompts/step1.system.md`: in the `wanted` paragraph, each item is
      `{"item": <user's words>, "role": ...}`. Define `` `feature` `` and `` `background` `` as in
      R2, with general wording only (no measurement wording, no brief text). Say that
      `background` is the default when the user does not say the ingredient should stand out.
- [x] `db/020_step1.sql`: update the header comment (repeats in `wanted` are exact repeats of an
      item-and-role object). Re-apply it with the OPERATIONS §4 command.
- [x] `db/022_step2.sql` step 7: read the item word with
      `jsonb_array_elements(coalesce(brief -> 'wanted', '[]'::jsonb)) w` and
      `lower(w ->> 'item')`. The word rule and the reason stay as they are. Re-apply with the
      OPERATIONS §4 command. The pipeline then keeps picking as before.
- [x] Tests: in `tests/test_contracts.py`, `BRIEF.wanted` becomes
      `[{"item": "rice", "role": "background"}]`. New bad examples: a plain string item, a missing
      `role`, role `"main"`, an extra key, an exact repeated object. In
      `tests/test_step1_check.py`, `test_role_objects_pass` and `test_plain_string_item_fails`. In
      `tests/test_prompt.py`, `test_prompt_names_every_role` (each role enum value appears in
      backticks).
- [x] Run `.venv/bin/pytest`, expect all passed. Then smoke-check one live call:
      `python -m evals.run --brief b12`. Step 1 should return honey with a role, and the contract
      should pass.
Done when: the live b12 run logs `wanted` as `{item, role}` objects, and the suite passes.
Commit: `Add role to step 1 wanted items`

### Task 5: The role measurement tool
Why: R4, R6, A4.
- [x] `evals/roles.py`, run as `python -m evals.roles [--sets clear ambiguous] [--ids r01 ...]
      [--settings gated hot] [--runs 3] [--save --label m2-role-gate]`.
      - Settings: `gated` = temperature 0, seed 42 for every run; `hot` = temperature 0.8, seeds
        1, 2, 3. Both are the default.
      - Each wording is sent once per run through `run.send(..., temperature=, seed=)` with
        `brief_id = "role-<id>"`. The tool reads step 1's output and `llm` back with
        `run.read_run`. It uses step 1's row even if a later step failed.
      - If `llm.temperature` and `llm.seed` differ from what was sent, the tool stops with an
        error, so a setting that silently failed to apply cannot produce a result.
      - Scored role (`scored_role(brief, adjunct)`): the role of each `wanted` item that contains
        the adjunct as a whole word, after `grade.normalise`, with a plain plural allowed (`s`,
        `es`, `y`→`ies`). No such item gives `None`. Matching items that disagree give `"mixed"`.
        `None` and `"mixed"` count as wrong.
      - Word rule, for reference: `select app.adjunct_is_prominent(request, adjunct)` once per
        wording, stored as `word_rule` (`feature` / `background`). Do not write the function's name
        into the results file.
      - Per wording and setting, the tool stores roles (one per run), run ids,
        `right_every_run`, `consistent`, and the median `llm_ms`.
      - `gate(wordings)` is a pure function on the gated results. It returns the four R6 points
        (`b12_b19`, `clear` as n/21, `consistent` (every wording, all sets), `held_out` as
        n/10) and `met` (all four).
      - `--save` writes `evals/results/<date>-<label>.json` with the date, label, model, the
        prompt and contract sha256 (as `evals/benchmark.py` does), the settings, the wordings,
        the summaries per setting, and the gate. It prints a per-wording table and the verdict.
      - Held-out wordings run only in a full run (no `--sets` and no `--ids` given), so a smoke run
        can never show them.
- [x] `tests/test_roles.py` (no stack): `scored_role` finds `orange blossom honey`, accepts
      `raspberries` for `raspberry`, gives `None` when the adjunct is missing and `"mixed"` on
      disagreement. `gate` is met on an all-right fixture, and fails on each point alone: b19
      once `feature`; 2 clear wordings wrong; an ambiguous wording that flips between runs; 2
      held-out wordings wrong. `--sets clear` never selects a held-out wording.
- [x] Dry run (not the measurement): `python -m evals.roles --ids r01 r15 --settings gated
      --runs 1`. Expect a table with 2 rows and no error.
- [x] Run `.venv/bin/pytest`, expect all passed.
Done when: the tool runs end to end on 2 wordings, and the gate logic is covered by unit tests.
Commit: `Add role measurement tool`

### Task 6: Measure and decide the gate — STOP POINT
Why: R4, R6, A4, A6. Nothing is deleted and step 2's decision is not changed before this task's
result is in `plan.md`.
- [x] Optional prompt check, before freezing. Run
      `python -m evals.roles --sets clear ambiguous --settings gated --runs 1`. You may make at
      most 2 general wording changes to the role paragraph of `shared/prompts/step1.system.md`.
      Never quote a wording or name a specific adjunct case. Record each change as a line in
      Deviations. Held-out wordings are not run here.
- [x] Freeze the prompt (commit it if it changed). Check G1:
      `python -m evals.run --save --label m2-role-g1`. Expect step 1 ≥ 21/22 with roles counted,
      and step 2 22/22 (the word rule still decides).
- [x] The measurement, run once with the frozen prompt:
      `python -m evals.roles --save --label m2-role-gate`. That is 34 wordings × 6 runs ≈ 204
      pipeline calls, roughly an hour. Run it in the background and wait on the saved file, not
      on the process.
- [x] Add a `## Gate result` section to this plan, above Deviations. It holds the file path,
      each R6 point with its measured value and pass/fail, the verdict, the hot-run summary
      (accuracy, wordings that flipped across seeds), the ambiguous wordings' roles, the word
      rule's score on the same set (for reference), the median step 1 time against 12.5 s, and the
      G1 result. Add the same numbers to a PROJECT.md §8 line.
- [ ] Commit the result files, the plan and PROJECT.md.
- [ ] **Stop and ask the user** when any R6 point fails, or when G1 step 1 is below 21/22. In
      that case leave `Stage: implementing`, report `needs-input` with the Gate result, and do
      not start Task 7. Do not re-tune the prompt and re-measure without the user's go-ahead.
      If everything is met, continue with Task 7.
Done when: `## Gate result` is in `plan.md` and committed, and the verdict is either met (go on) or
the user has been asked.
Commit: `Measure adjunct roles against the gate`

### Task 7: Step 2 picks the specialty style from the role
Why: R7, R8, A7, A8. Only after Task 6 says the gate is met.
- [ ] `db/022_step2.sql` step 7: the specialty adjunct is a `wanted` item whose `item` names an
      `app.specialty_style()` adjunct for the base's guide, with `w ->> 'role' = 'feature'`. If
      several items match, use the first adjunct in name order, as now. The `request` stays only
      for `app.guide_from_request`. The reason becomes
      `Picked <code> <name>: <adjunct> has the role "feature" in step 1's brief; base style <base>.`
      Drop `spec_cue`. Update the comment above step 7. Re-apply with the OPERATIONS §4 command.
- [ ] `shared/contracts/step2.input.schema.json` description: `request` is the user's text, used
      for guide words. The adjunct's role comes from `brief.wanted`.
- [ ] `tests/test_step2_pick.py`: new `test_feature_role_without_cue_word_picks_specialty` (honey
      `feature`, request "A blonde ale with honey." → 31B, `alt_styles[0] == "18A"`).
      `test_background_role_keeps_base_even_with_cue_words` (b12's request, honey `background` →
      18A, no 31B in the pick). `test_b12_reason_cites_the_role` (reason contains `"feature"`, and
      no `("` quote). Existing b12 and b19 tests stay, and now pass because of the briefs' roles.
- [ ] Run `.venv/bin/pytest`, expect all passed.
Done when: the role alone moves the pick between 31B and 18A in SQL tests.
Commit: `Pick specialty style from step 1 role`

### Task 8: The word rule is gone
Why: R9, A9.
- [ ] `db/022_step2.sql`: delete `app.adjunct_cue`, `app.adjunct_is_prominent` and their comment
      block, including the CUES, DAMPERS, joining-word pattern and `DAMPER_GAP`.
- [ ] New `db/023_drop_adjunct_rule.sql`: a header (purpose, apply command, idempotent) and
      `drop function if exists app.adjunct_is_prominent(text, text);` then
      `drop function if exists app.adjunct_cue(text, text);`. Apply it twice with the OPERATIONS §4
      command, then check `pg_proc`: neither function exists in `app`.
- [ ] `tests/test_step2_signals.py`: delete the `prominent` helper and every test that calls it
      or `app.adjunct_cue`.
- [ ] `evals/roles.py`: remove the word-rule lookup (the saved gate result keeps its
      `word_rule` values). Remove its test, if Task 5 added one.
- [ ] `docs/DATABASE.md`: drop the two functions from the step 2 signal-function line.
- [ ] Run `grep -rn "adjunct_cue\|adjunct_is_prominent\|DAMPER" db tests evals shared n8n`. Expect
      only the two `drop function` lines in `db/023_drop_adjunct_rule.sql` (A9 as amended
      2026-10-13).
- [ ] Run `.venv/bin/pytest`, expect all passed.
Done when: the functions are gone from the repo and the database, and the suite passes.
Commit: `Remove adjunct word rule`

### Task 9: G1 and G2 measured again, docs current
Why: R10, A10.
- [ ] `python -m evals.run --save --label m2-role`. Expect step 2 22/22 with b05 15B and mismatch
      20C, b12 31B (alternative 18A), b19 17C, b17 8B, and step 1 ≥ 21/22 with roles counted.
- [ ] `.venv/bin/pytest`, expect all passed. Record the count.
- [ ] PROJECT.md: rewrite the §5 style-guide sentence on adjuncts (the specialty code is picked
      when step 1 gives a wanted adjunct the role `feature`). In the 2026-10-13 "Shipped
      `m2-best-fit-style`" entry, mark the known limitation as resolved by `m2-adjunct-role`. Add a
      §8 line with the measured numbers. `docs/WORKFLOW-ROADMAP.md`: add Measured lines to G1
      (roles counted) and G2.
Done when: the results file shows the R10 numbers, and the docs cite it.
Commit: `Measure G1 and G2 with adjunct roles`

## Critical behaviour and its tests
| Behaviour | Test | Task |
|---|---|---|
| Held-out wordings fixed and never in the prompt | `tests/test_role_wordings.py`, `tests/test_prompt.py::test_prompt_quotes_no_brief` (extended) | 1 |
| Temperature/seed actually reach the Ollama call; defaults stay 0/42 | `tests/test_pipeline.py::test_temperature_and_seed_reach_step_1`, `::test_default_temperature_and_seed` | 2 |
| A wrong role fails `wanted` (G1 counts roles) | `tests/test_grade.py::test_wrong_role_fails_wanted` | 3 |
| The contract rejects plain strings, missing or unknown roles, extra keys | `tests/test_contracts.py::test_bad_examples` (new cases), `tests/test_step1_check.py::test_plain_string_item_fails` | 4 |
| Prompt defines both roles | `tests/test_prompt.py::test_prompt_names_every_role` | 4 |
| Scored role and the R6 verdict computed correctly | `tests/test_roles.py` (scored role, each gate point failing alone) | 5 |
| A setting that failed to apply cannot produce a result | `evals/roles.py` stops on an `llm` mismatch (checked in Task 5 dry run) | 5 |
| Role alone decides specialty vs base | `tests/test_step2_pick.py::test_feature_role_without_cue_word_picks_specialty`, `::test_background_role_keeps_base_even_with_cue_words` | 7 |
| Reason cites the role | `tests/test_step2_pick.py::test_b12_reason_cites_the_role` | 7 |
| No regression on the 22 briefs | `tests/test_step2_pick.py::test_briefs_reach_the_bar`, `evals.run --label m2-role` | 7, 9 |

## Approved exceptions
None.

## Gate result
Measured 2026-10-13 with the frozen Task 4 prompt (no prompt edit kept): [`evals/results/2026-10-13-m2-role-gate.json`](../../../evals/results/2026-10-13-m2-role-gate.json). **Verdict: NOT MET.**

| R6 point | Measured | Result |
|---|---|---|
| b12 and b19 right every run | r01 feature x3, r15 background x3 | pass |
| Clear-cut right every run (≥20/21) | **19/21** (r07 and r12: step 1 left `wanted` empty and put "honey forward" / "honey-forward" in `unknown`, so no role; 57/63 runs right) | **fail** |
| Same role in all 3 gated runs, every wording | 34/34 consistent (the 3 gated runs share temperature 0 and seed 42) | pass |
| Held-out (≥9/10) | 10/10 (30/30 runs) | pass |

- Hot runs (temperature 0.8, seeds 1-3, report only): clear 59/63 runs right, 18/21 wordings right every run; held-out 27/30 runs, 8/10 wordings. Flipped across seeds: r12, r15, r18, h03, h04 (r15 and r18 flipped to `feature` or no item; h03 and h04 lost the item in one or two seeds).
- Ambiguous wordings (reported, not scored): r22 feature, r23 feature, r24 feature, in all runs.
- Word rule on the same set (reference): 28/31 scored wordings right (clear 20/21, held-out 8/10). It misses r21 and h05, h09.
- Step 1 median `llm_ms`: 13.97 s over the wordings (gated), 12.70 s (hot), against 12.5 s.
- G1 (`evals.run --save --label m2-role-g1`, [`evals/results/2026-10-13-m2-role-g1.json`](../../../evals/results/2026-10-13-m2-role-g1.json)): step 1 21/22 (b05 `hints` only; roles counted) so the step 1 bar holds. Step 2 **21/22**, not the expected 22/22: b05's step 1 gave hint `session`, step 2 picked 15A instead of 15B (the word rule is unchanged; the earlier m2 runs also had a wrong b05 `hints` but still picked 15B).
- Prompt smoke runs (clear + ambiguous, gated, 1 run): first run 20/21 (r12 failed); one general edit was tried and reverted (see Deviations). Held-out wordings were not run before the freeze.

Task 6 is stopped here for the user's decision. Task 7 is not started and nothing is deleted.

## Deviations
- 2026-10-13 · Task 8 / A9: the grep may find the two `drop function` lines in `db/023_drop_adjunct_rule.sql`, and nothing else — the drop file R9 asks for has to name the functions (user decision; brief A9 amended).
- 2026-10-13 · Task 2: both workflows (`Step 1 · read request` too) were edited in JSON and imported with `n8n import:workflow`, not through the MCP — one route for both, and the export stays the source. `tests/test_contracts.py` (required = properties) and `tests/test_workflows.py` (sample keys = declared inputs) now treat `temperature` and `seed` as optional.
- 2026-10-13 · Task 6: prompt edit 1 (general: an ingredient inside a describing compound goes to `wanted`, not `unknown`) was tried after the first smoke run left r12 with no wanted item. The re-run lost b19 (r15: wanted empty, everything in `unknown`), so the edit was reverted; the prompt stays as committed in Task 4. 1 of 2 allowed edits used; no further edits.
