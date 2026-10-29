# Review: m7-process

Diff: main...m7-process at 3d56f46  ·  Verdict: fixes needed

Checked: the whole branch diff (20 commits, 49 files) against [brief.md](brief.md), [plan.md](plan.md)
(Tasks 1-12 and 11a) and [doc-calc.md](doc-calc.md). I read `db/048`-`053`, the step contracts, the
`Steps 12–15 · process` sub-workflow, `evals/grade.py` / `run.py`, and the new tests. I also ran
read-only queries on the live stack. The full suite without `tests/test_pipeline.py` passes:
1367 passed in 4 min 13 s, 2026-10-29. All 24 new or changed `app` functions and `ref.water_profile`
are owned by `postgres`. No secrets are in the diff, and every commit subject is one line of 60
characters or fewer.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | `db/053_package.sql:11-31` (`app.residual_co2`), `db/052_ferment.sql:219-220` (`max_temp_c`) | Step 15 raises `residual_co2: N C is outside HTB Table 10.3 (5 to 30 C)` whenever step 14's `max_temp_c` rounds above 30 °C. Step 14 reaches that from ordinary step 6 options. Measured over every `app.ingredient_choices` ferment option: 25 of 53 kveik schedules (19 of 20 kveik yeasts) and 6 of 207 ale schedules go above 30 °C. The 6 ale schedules are Belle Saison and YF-208 Priest Passion at 35 °C, Porter&Kvass, Pure Ale and M29 French Saison at 32 °C, and YF-503 Hotspur Viking at 38 °C. `select app.residual_co2(32)` raises. Belle Saison is b11's yeast: this run picked its cool option (max 19 °C), but step 6 can also pick 35 °C. No test feeds step 15 a temperature above 30 °C. | R6 / A2: a recipe that passed step 11 then fails at step 15, and **nothing is saved**, because the pipeline saves only after steps 12-15. A brief with a saison or kveik yeast at its warm option loses its validated recipe. A fix needs a decision: either clamp to the 30 °C row (HTB's table ends there; a higher temperature has less residual CO₂, so clamping slightly under-primes, the safe side) and say so in `because`, or extend the residual from Table 10.3's source. Either way it needs a test at about 35 °C. |
| 2 | should-fix | `db/050_water.sql:388-426` (`app.malt_acidity`), doc-calc §7 | `role` is used only for `roast` and `sugar`. Every crystal and kilned malt takes the non-roast Table 21.4 row nearest in °L, whether that row is caramel or not. Measured on `ref.fermentable`: 10 of 27 crystal malts land on base or kilned rows: Carapils → Brewers Malt (+5.0 mEq/kg), Carahell → Bonlander Munich (+2.6), 4 CaraBody-type malts → Ashburne Mild (+2.6), Caramel 50 Malt → Victory (−0.9). Meanwhile 4 kilned malts (Abbey and Melanoidin among them) land on Caramel 20L and Caramel 40L rows (−21 to −30). HTB's own table shows that crystal and kilned malt of the same colour differ: Caramel 40L −30.4, Special Roast 40L −13.0. The approved doc-calc text describes this nearest-°L rule, so it is your call. | The estimate now drives the alkalinity dose (outside review 2026-10-28) as well as the acid line. Light crystal is read as alkaline, so the pH comes out high and more acid is reported. Kilned malts are read as caramel, so the pH comes out low and baking soda or lime may be dosed that the grist does not need. One option is to pick among the Caramel rows for `crystal` and among the other rows for `base` / `kilned` / `adjunct`. The model is already marked unverified against Bru'n Water. |
| 3 | note | `db/050_water.sql:647-651, 665, 704` | `target.outside_row` holds the calcium notes from `app.salt_additions` ("both salts raised by x…", "calcium below the row: …") as well as the `outside_row:` notes. The plan's step 12 shape has no separate `notes` field, so those notes ended up there. | A reader of the saved process finds calcium dosing notes under a key named `outside_row`. Harmless. |
| 4 | note | `docs/work/m7-process/doc-calc.md:3` | The status line still says "**waiting for your review** (second pass…)". The plan's Task 1 is ticked, and the gate answers are recorded in doc-calc's own "Decisions" section and the plan's Deviations. | It is a stale record in a file the plan links as the source of every formula. |
| 5 | note | `tests/test_ferment.py:122-127` | `test_every_ferment_temp_in_range` (A4) covers yeast types ale, kveik and lager only. Brett and untyped yeasts use the same ale schedule. I checked their 12 schedules on the stack: all are inside their ranges. | A4 holds today. The test would not catch a regression for those two groups. |

Plan and brief coverage: every task, including 11a, is done as written or recorded under the plan's
Deviations. The brief's R1-R7 are met, and A1-A12 are each met or covered by a named test or the
Task 11 measurement. The exception is A2/R6 for warm yeasts (finding 1). Known items, documented
and accepted: the mash pH model is unverified against Bru'n Water (doc-calc §16), the sub-workflow's
failure path inside n8n is unverified, and b23 has no process because it failed at step 11. The
saved `evals/results/2026-10-28-m7.json` shows `process ok` 7/9. The 8/9 the user approved comes
from the unsaved Task 11a re-run, and PROJECT.md §8 says so.
