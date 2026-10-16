# Review: s6-style-neighbours

Diff: main...s6-style-neighbours at 2fdb99e  ·  Verdict: ready for testing

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | loaders/style_envelopes.toml:1439, 2180, 2312 | The three applied fixes changed the level or characters but kept the row's old `quote`, which no longer backs the row. D57 (25B body) now has max `medium` under "Light to medium-low body." The backing phrase "Stronger versions can have up to medium body" is in 25B's 2021 mouthfeel but not on the row. D20 (18A malt) adds toasty and biscuit under an aroma quote that names only bread and caramel; the report's backing phrase "bread, toast, biscuit, wheat" is not used. D40 (20B roast) adds acrid under a quote with no burnt or acrid word. | The s3 envelope rule is that each row's levels and characters are backed by its quote. `test_26_styles_reviewed` checks only that the quote is in the 2021 text, so it passes. A reader who checks a row against its quote would find it contradicts D57's max. Pipeline results are not affected. |
| 2 | should-fix | docs/work/s6-style-neighbours/envelope-crosscheck.md:3 | The report still opens with "Nothing in `loaders/style_envelopes.toml` is changed" and "Your decision column is empty on purpose". Since Task 6, the toml has the three fixes and every decision cell is filled. | The record contradicts the branch. The Decisions section at the end is correct. |
| 3 | note | evals/style_neighbours.py:68-73 | `top3` maps a paired BA candidate to its BJCP pair without removing duplicates, so a top 3 can name the same style twice. This affects 10 of 83 Run A briefs and 19 of 61 Run B briefs (e.g. 1B in Run B: `['1B','1B','1B']`). This follows the plan as written. I re-measured with distinct styles from step 2's five candidates: Run A still has 0 top-3 misses and Run B still has 4. | The recorded top-3 figures stand. The label "top 3" sometimes covers fewer than three distinct styles. |
| 4 | note | evals/style_neighbours.toml (e.g. briefs 1A, 1B, 1D) | Some request sentences hold descriptive words beyond the brief's 2–4 words ("very light", "plain", "highly", "pale"). These extra words are not checked against the 2021 entry. | With guide `any` passed, step 2 does not read the request, so the results are unaffected. The request only documents the brief. |

## What was checked

- **Plan.** All six tasks were done as written. The deviations are recorded in plan.md: guide `any` and Runs A/B ("1b", "2c"), 83 not 84 styles, `wheat` added to the barred nouns, and the "card silent" and grouping rules for the cross-check. The brief carries the R1/A1 deviations. The user's decisions (D1 declined; K1, K2 and U kept; C1 applied) are in specialty-entry.md, envelope-crosscheck.md and PROJECT.md §8.
- **Brief.** R1–R7 and A1–A6 are met:
  - A1/A2: `tests/test_style_neighbours.py`, 103 passed against the stack on this review.
  - A3: the runner prints both runs, the gap and the 41 A-only triples. The result is saved in `evals/results/2026-10-16-s6.json`. Its summary (A 75/83 first, 83/83 top 3; B 44/61, 57/61; gap −11/−4) matches PROJECT.md §8.
  - A4: `git diff main -- db/` is empty.
  - A5: 65 rows have decisions, the 3 changes are in the toml, and the envelope, golden, recipe and level tests pass (89 passed on this review).
  - A6: the note exists, and the decision is recorded as declined.
- **Brief words.** On this review, every one of the 291 brief words also scores > 0 against the text step 2 itself reads (overall impression, aroma, flavor, mouthfeel). So the test's wider text field does not hide a word step 2 cannot see.
- **Scope.** Only the planned files changed. Step 2 is unchanged.
- **Correctness and readability.** `measure`, `summarise`, `confusions`, `gap` and `run_b_family` match the plan. BA picks are named, and the gap is computed on the same codes. Each function reads on its own.
- **Safety.** No secrets are in the diff. There are no DB changes. 2008 material is only in the cross-check report.
- **Records.** PROJECT.md §8 has an entry per task, and the §5 2008-aids row is set to done. The commits are one line each, with no body or trailer.
