# Review: m3-deviations

Diff: main...m3-deviations at df256bc  ·  Verdict: ready for testing

Checked: the diff of all 8 branch commits against brief.md (R1–R8, A1–A9) and plan.md (Tasks
1–6); `pytest` run on the stack, 709 passed (168 s); the 12 new `app` functions are owned by
`postgres` (`pg_proc`); `ref.beer_style` ranges are inclusive or open-ended (12 SRM ranges have
no upper end, written `N+`), `ref.yeast.temp_c` is inclusive for all 119 yeasts, no
`ref.ingredient` row has a null producer, and no style code is duplicated across guides; the
G3 results file shows step 1, 2 and 3 at 22/22. No secrets in the diff; DB changes are `.sql`
files; commits are one line each with no body.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | note | db/036_ingredient_resolver.sql:18 | The `caramel` → `crystal` synonym makes "crystal malt" resolve to 11 fermentables (the 9 Weyermann `Caramel N Malt` products plus Crystal T50 and Crystal Extra Dark), measured. | Fits the best-case decision (the word is rated at its best product, and M5 must then pick one that keeps it in style), and A7's test only needs Crystal T50 among fermentables. Worth knowing when M5 extends the resolver: "crystal malt" names a family, not one product. |
| 2 | note | db/037_step3.sql:53 | The knob labels ("mash temperature", "BU:GU") live in a second `values` list inside `app.step3_conflicts`, not in `app.hint_knob()`; the plan said `because` is "built from the table". No Deviations line. | Harmless: an implementation detail, the list sits next to the code that uses it and the tests check the text. Only the record is missing. |
| 3 | note | db/037_step3.sql:197 | The yeast choices include the warm-step temperature itself (21 °C), but `app.style_level` raises esters and phenols only when `ferm_c > 21`, so 21 °C rates the same as the lower end. | No effect on results: the level is a step at 21 °C, and the upper end of the range covers the warm side whenever the range crosses it (`test_yeast_best_over_its_temperature_range` passes at 26 °C). The 21 °C choice is redundant, not wrong. |
| 4 | note | db/037_step3.sql:240 | `app.rate_wanted` calls `app.style_level` twice per product and choice (once in the select list, once in `order by`). | Double work only; step 3 runs in milliseconds on the briefs and no need to optimise was measured. |
| 5 | note | n8n/workflows/recipe-pipeline.json (`Step 3 · input`) | The step 3 brief is taken from `Step 2 · input`.brief rather than from the step 1 node output, as the plan worded it. | Same value: `test_step_3_logged` asserts the logged brief equals step 1's output, and it passes. |

No must-fix or should-fix findings. Every plan task is done as written; the one recorded
deviation (`tests/step3_sample_style.json`) is in the plan's Deviations. All brief requirements
have code and a test: R2 numbers (edges, `batch_l`, 31B), R3 conflicts (dry/full-chewy,
bitter/malty, stronger/session, same side, unrelated), R4 best case (several products, yeast
`temp_c`, feature hop late only, unrated words and styles without an envelope), R5 excluded,
R6 guidance off, R7 pipeline logging and contracts, R8 no style; A9 is in WORKFLOW-ROADMAP G3,
RECIPE-ROADMAP P4 and PROJECT.md §4 and §8.
