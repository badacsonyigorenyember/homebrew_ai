# Review: adjunct-fermentables

Diff: main...adjunct-fermentables at 388c772  ·  Verdict: ready for testing

Checked: the plan's 5 tasks against the diff (all done as written, no deviations needed), the
brief's R1–R8 and A1–A8, scope (only the plan's Files table changed), the loader code, the
tests, the SQL files, PROJECT.md / DATABASE.md / STYLE-FIT.md, and the 7 commits (one line
each, no body). Measured on 2026-10-11: `pytest` 68 passed; the 7 loaded rows match `build`
and the plan (ids 3392–3398, fermentability `normal` 78 / `full` 2 / `none` 1, 18 sources,
`misc_category_check` without lactose); the coverage command prints `47 names; missing: []`;
Palmer's printed values in `how_to_brew.pdf` (Table 18.5 PDF p. 315, Table 24.1 PDF p. 462)
match `PALMER` (oats 70 %, corn 84 %, rice 82 %, barley 70 %; table sugar 46 / 100 %,
lactose 46 / "…", honey 38 / 95 %). `hopline_adjuncts.json` is gitignored; no secrets in the
diff; DB changes are `.sql` files.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | loaders/adjuncts.py:48, docs/DATABASE.md:221 | The sugar and honey extracts come from Palmer's as-sold PPG ÷ 46, so honey's 82.6 includes its water (Palmer's note under Table 24.1 says moisture is subtracted for powders). They are stored in `extract_dbfg_pct`, a column named and described as dry basis, next to the flakes' and malts' true FGDB figures. Nothing records that the sugar and honey values are as-sold. | Harmless now (P2 not built, no moisture stored). If P2 applies a dry-basis-to-as-is moisture correction to every fermentable, honey's gravity would be counted low. A one-line note in DATABASE.md's rule (or the docstring) settles it for P2. |
| 2 | note | loaders/adjunct_products.py:64 | Brown Candi Sugar takes its colour from hopline (225 EBC) but its extract and `full` fermentability from Palmer's white "Table sugar" row. Approved in the plan; recorded here only so P2 knows the extract and fermentability are a sucrose proxy. | No action. |

## Re-review 2026-10-11

Diff: main...adjunct-fermentables at d2c892a  ·  Verdict: ready for testing

Checked: the new commit d2c892a against finding 1, and that the rest of main...adjunct-fermentables
is unchanged since 388c772 (d2c892a touches only PROJECT.md, docs/DATABASE.md, plan.md and the
`loaders/adjuncts.py` docstring; no code, SQL or data). Measured on 2026-10-11: `pytest` 68 passed.

| # | Earlier finding | Status | Evidence |
|---|---|---|---|
| 1 | should-fix: sugar/honey extracts are as-sold, undocumented | fixed | docs/DATABASE.md:226 adds the rule under the fermentable rule ("as-sold PPG ÷ 46 (water included), not dry basis: apply no moisture correction"); loaders/adjuncts.py:9 says the same for every Table 24.1 extract, which also covers lactose and Brown Candi Sugar; plan.md Deviations has a dated line; PROJECT.md §8 has a dated entry saying docs only, no data changed. Commit is one line, no body. |
| 2 | note: Brown Candi Sugar uses Palmer's table-sugar row | unchanged | No action was asked. |

No new findings.
