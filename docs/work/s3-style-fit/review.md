# Review: s3-style-fit

Diff: main...s3-style-fit at d6141e6  ·  Verdict: fixes needed

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | `db/034_style_level.sql:377`, `tests/test_style_fit_recipe.py:287`, PROJECT.md §8 (Task 10 entry) | `app.check_recipe` returns `srm` null for **11 of 22** reference recipes, not 3 as Task 9 reported: b02, b03, b04, b05, b06, b07, b12, b16, b19, b20, b22 (`numbers.missing = ref.fermentable.ebc`). The flakes, Honey and Lactose have no `ebc` row, so the R7 colour check is skipped on half the reference recipes. A rolled-back trial that gave the flakes 2–4 EBC and honey and lactose 0–1 EBC (*estimate*) computes **b19 at 26.7 SRM, above 17C's range of 14–25**. With colour checked, b19's Caramunich Type 2 and Roasted Barley would be ⚠️ "too much colour", outside the accepted deviations. Honey can only add colour, so 26.7 is a lower bound (the fixture's own target is 19.5). Neither report.md nor PROJECT.md mentions the skip, and PROJECT.md says "G-S: met … every reference-recipe line is rated". | A9 passes partly because the check never runs. One reference recipe probably breaks R9. PROJECT.md states as measured something that is not verified (CLAUDE.md). The user chooses the fix: give the 7 fermentables a colour (a data change outside this brief), or record the gap as unverified and settle b19 (change the recipe or accept it). |
| 2 | should-fix | `db/034_style_level.sql:197-198` | When the recipe's SRM cannot be computed, the because says "colour: dose not given, dose check skipped." The real cause is that a fermentable has no colour (the recipe passed every dose). | The because sends a reader looking for the wrong cause (R5: the because names what was used). |
| 3 | should-fix | `db/034_style_level.sql:310-313` | Every yeast without character tags gets "no character tags (needs review).", printed twice (esters and phenols). That includes clean yeasts that are not in `ref.ingredient_review`, e.g. b01, b07 and b12 SafAle US-05 and b08 SafLager W-34/70. Plan step 3 asks for this text. But the plan's own decision says a yeast without an ester tag "carries no character", and "needs review" elsewhere means an `ingredient_review` row. No level changes. | The text contradicts the review flag: a user would think US-05 is unreviewed data. |
| 4 | should-fix | `db/034_style_level.sql:201-202` | The "too much" text prints the unrounded numeric. Measured for b08: "too much bitterness: 48.638715818210258234615922002886059812427492490029310245066863800… IBU is above German Pils (5D)'s 22-40." The oil and roast notes are rounded (lines 233, 244). | Hard to read in a because shown to the user. |
| 5 | should-fix | `db/034_style_level.sql:114, 228, 239, 259, 286, 472-473` | Readability (§6.8). `v_oil` (numrange) holds the hop's oil range and later the fermentable's EBC range. `v_dose_key` holds the warm-step temperature. `e.dimension not in ('caramel')` at 286 never matters, because caramel has no scale. The two branches of the role-requirement because (472-473) are identical. | In a 280-line function, a reader has to trace what each variable really holds. |
| 6 | note | `db/034_style_level.sql:187-188` | A boil time strictly between 4 and 5 or between 29 and 30 min (e.g. 4.5) matches no `usage_effects` row and rates as "no sensation … conflicts". `style_fit_recipe` treats anything under 30 as late. Every recipe and golden case uses whole minutes. | Harmless today. |
| 7 | note | `tests/test_style_fit_recipe.py:242-248` | `ACCEPTED_LINES` is keyed on (brief, ingredient name), so it would also accept a later, different failure on those 5 lines (e.g. b18 Roasted Barley too much roast). The user accepted only the IBU/SRM reason. | The acceptance is wider than the decision. |
| 8 | note | `db/034_style_level.sql:191-205` | Colour and bitterness are checked against the upper bound only, as the plan decided. Measured below the range: b11 3.8 SRM vs 25B 5–22. Estimated with the trial colours: b05 22.2 vs 15B 25–40, b22 6.4 vs 7–15. | By design; listed so the user knows. |
| 9 | note | `tests/test_style_level.py:99-106` | The needs-review case of `test_yeast_too_little` puts a temporary `ingredient_review` row on US-05. The plan named a YeastFlow yeast. Same behaviour tested; the change is not recorded in Deviations. | Harmless. |
| 10 | note | `docs/DATABASE.md` §2, §7 row 4 | Judged as asked: the "31 → 35 tables" line is part of Task 10's "the two new tables" and matches the catalog (35, `ref` 19). In scope. Separately, `ref.style_ingredient` (characteristic ingredients) now shares its name with `corpus.style_ingredient` (corpus profile), which §7 row 4 still lists. | No action; the same name in two schemas could confuse a reader. |

## What was checked

- **Plan:** all 10 tasks ticked and present in the diff. User-approved deviations are recorded in plan.md and brief.md: Sterling, the min-tolerance rule, step 0, b08/b18, b10/b07/b12, the b22 roast min and the s2 path fix. Task 8's helpers `level_word` and `tag_under` are recorded. The only unrecorded difference is #9.
- **Brief:** A1 (89/89 hops have a character tag, 38 yeasts flagged), A2, A3, A4, A5 (53 cases, no `style_rule` for the 8 pairs), A6, A7, A8 and A10 hold, each with a test or the grep. A9 holds as tested but rests on the skipped colour check (#1).
- **Scope:** Sterling, the fixture edits, the s2 path fix and the DATABASE.md count line are all user-approved or part of a task. Nothing else is outside the brief or plan.
- **Correctness:** the deployed `style_level`, `style_fit_recipe` and `tag_match` bodies match the repo files byte for byte. The step order matches STYLE-FIT §5 as amended. The ester/phenol bases, warm step and one-level tolerance match the cut points. All 10 functions are owned by `postgres`. The row counts in PROJECT.md and DATABASE.md match the catalog (tag 69, synonym 239, ingredient_tag 806, review 38, sensory 189, character 237, style_ingredient 116, `ref` 19 tables, 35 in all).
- **Tests:** the 6 s3 files plus test_hops pass (111). Full `pytest` passes: 531 passed in 133 s (measured at d6141e6).
- **Safety:** no secrets in the diff. DB changes are `.sql` files (`012`, `033`, `034`, `035`). The extraction is offline only (`test_extraction_not_in_pipeline`).
- **Records:** PROJECT.md §8 has an entry per task and the §4 status is updated. Every commit is one line, at most 60 characters, with no body or trailer.

## Re-review 2026-10-15

Diff: 9fc35ca..fadabd2 (845e219, 4a7934d, 1abfe1c, fadabd2)  ·  Verdict: ready for testing

### Earlier findings

| # | Status | Checked |
|---|---|---|
| 1 | fixed | The four flakes have a sourced EBC in the DB (Barley and Oats [0,3.2], Corn 1.576, Rice 1.97; Honey, Lactose, Enzyme Malt NULL; 78 of 81 fermentables with EBC, measured). `style_fit_recipe` solves the grist with the colourless fermentables at 0 EBC, with the same `solve_grist` → `grist_mcu` → `srm` call as `check_recipe` (032:663-676), so it is a true floor. Over the 22 recipes: b04 31.9, b19 18.8, b20 25.0 are lower bounds and none is above its style max; b12 (Honey) has SRM null but no line with a colour effect, so colour is not checked there, as designed. With b19's old grist the lower bound is 26.7 and `test_reference_recipe_lines` fails on Caramunich Type 2 and Roasted Barley (measured), so the recipe change is what makes it pass. report.md §7, PROJECT.md §8 and plan.md Deviations record the skip and the correction. |
| 2 | fixed | 034:200-202: colour says "a fermentable has no colour"; bitterness has its own text. |
| 3 | fixed | 034:324-327: said only when `v_review` is true and only once. Measured: US-05 unflagged gives no "needs review"; with a temporary review row it gives the text once. |
| 4 | fixed | 034:206: IBU rounded to a whole number, SRM to 0.1. |
| 5 | fixed | `v_oil_range`, `v_ebc_range`, `v_warm_above_c`; the `caramel` test and the duplicate case branch are gone. |

**Would the new tests fail if the fix were reverted?** Measured by loading the 9fc35ca `034_style_level.sql` into an open transaction (rolled back) and running the tests on that connection: `test_null_srm_names_the_colourless_fermentable`, `test_needs_review_only_for_flagged_yeasts`, `test_too_much_text_is_rounded` and `test_colour_lower_bound` all fail; the older tests still pass. On the current code all pass. The `test_formulation_check` switch from Flaked Rice to Lactose is right: Rice now has colour, Lactose has none, and the test still checks SRM null with `ref.fermentable.ebc` missing. `test_adjuncts` asserts the four ranges and their `field_source`, so reverting 845e219 fails it.

Full `pytest`: 535 passed in 134 s (measured at fadabd2). Deployed `style_level`, `style_fit_recipe`, `tag_match`, `level_word`, `tag_under` match the repo file byte for byte (md5 of the bodies), all owned by `postgres`.

### New findings

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 11 | should-fix | `loaders/adjunct_products.py:77-82` | The new `field_source` slugs `simpsons-malt-nov25` and `briess-flakes-web` are not in `ref.source`. They are the only `field_source` values in `ref.fermentable`, `ref.hop` and `ref.yeast` that do not resolve (measured). The Simpsons Nov 2025 range is already `ref.source` row `simpsons-malt-2025`, and the Briess page has no row (URL and fetch date). | DATABASE.md "Every loaded row is sourced": a reader following the slug finds nothing. The URL and printed text are kept in `raw.colour`, so nothing is lost. |
| 12 | should-fix | `docs/DATABASE.md:210` | The `fermentable` row still says "74 with EBC"; the catalog has 78. | A stated count that no longer matches the DB (CLAUDE.md: facts are measured). |
| 13 | should-fix | `docs/work/s3-style-fit/brief.md` Deviations, `docs/STYLE-FIT.md:102-104` | The lower-bound colour rule and the flake colour data, which plan.md calls "outside the brief's scope", have no line in brief.md's Deviations. STYLE-FIT §4 still says the SRM comes from `app.check_recipe`, with no word about the lower bound. | The conventions want a scope or requirement change in brief.md too. A reader of STYLE-FIT will not know the colour check can run on a floor. |
| 14 | should-fix | `docs/WORKFLOW-ROADMAP.md:146` | The G-S line now says "re-measured 2026-10-15" but keeps "Full `pytest` 531 passed"; the measured count is 535. | Same sentence, two different measurements. |
| 15 | note | `tests/test_style_level.py:175` | The flagged half asserts `count(...) <= 1`, so it would also pass if the note stopped appearing for a flagged yeast. It fails against the old code (two copies), and today it appears once (measured). | Weaker than the decision; harmless today. |
| 16 | note | `tests/test_style_fit_recipe.py` | With the four flakes' `ebc` set back to NULL in a transaction, `test_reference_recipe_lines`, `test_deviation_lines_are_flagged` and `test_colour_lower_bound` still pass, because the lower bound covers them. Only `test_adjuncts` (loader code, no DB) guards the flake colours. | A DB that was not reloaded would not be caught by the suite. |

Earlier notes 6-10 are unchanged. Nothing else in the four commits is outside what the user approved.
