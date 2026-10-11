# Review: test-briefs

Diff: main...test-briefs at a847715  ·  Verdict: ready for testing

Checked: all three tasks are ticked, and their output matches the plan, or the difference is under
Deviations. `pytest -q` gives 61 passed. `pytest -s tests/test_recipe_briefs.py` gives 10 passed,
and every A3 count is at or above its minimum (16 categories, 3 stouts/porters, 4 lagers,
2 Belgian, 2 wheat/sour, 3 hop-forward, every adjunct ≥ 1, ingredient 3, number 3, mismatch 1,
conflict 1, guidance off 1, exclusions 2, inventories 2, every hint row ≥ 1, 4 batch sizes,
0 non-gravity words). The A4 range grep finds nothing. All 20 `style` codes and both `alt_styles`
codes, and every code used by the style buckets, exist in `ref.beer_style` for bjcp-2021
(queried 2026-10-11). The file has no secrets, the DB was only read, and each commit is one line
with no trailer. §2, §3 and §6 are unchanged.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | PROJECT.md:181 (§7 D1) | The new R3 rule is recorded only in the brief and plan. The user agreed it on 2026-10-11: base style by default, but when the request makes an adjunct a prominent feature, the specialty code with the base style as the alternative. PROJECT.md's §8 entry gives only b12's reason. D1's leaning still says "classifying to the base style". This is not a direct conflict: the parenthetical describes the first build, D1 asks BJCP vs BA, and D7's "specialty styles use the base style" fits 31B on an 18A base. But D1 is the only place PROJECT.md states a classification rule. | P4 scores "right style" against these briefs. A reader who takes D1 as the rule would build step 1 to return 18A for b12. One clause in D1's leaning text would fix this, and it touches §7 only, not §2, §3 or §6. |
| 2 | note | tests/test_recipe_briefs.py:146 | For R3, the test checks only that the codes exist. It does not check the mechanical half of the new rule, which says a specialty `style` must list its base style in `alt_styles`. This is recorded in the plan's Task 2 deviation ("Test unchanged"). | If someone drops 18A from b12, every test still passes. Whether an adjunct is "prominent" is a judgement and cannot be tested. |
| 3 | note | docs/work/test-briefs/plan.md (Deviations) | The first Task 2 line says b12's deviation "stays kind `ingredient`, so R7 keeps 3". The next line removes that deviation and moves the count to b16. | Both lines are history, read in order. The current plan text (spread table, counts) is correct. |
| 4 | note | PROJECT.md:114, :195 | Both link `docs/work/test-briefs/`. | dev-ship moves the folder to `docs/finished/`, so these links need updating then. |
| 5 | note | user auto-memory (outside the repo) | The note "BJCP style = base style … 26D, not 30A" no longer matches R3 for prominent adjuncts. | Future sessions may apply the old rule. The note was not changed. |
