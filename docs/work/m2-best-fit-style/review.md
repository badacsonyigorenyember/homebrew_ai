# Review: m2-best-fit-style

Diff: main...m2-best-fit-style at 86e173c  ·  Verdict: fixes needed

Checked: all 7 tasks against plan and brief; `db/021_style_pairs.sql` and `db/022_step2.sql`
(deployed function bodies match the files by md5; all 15 `app` functions owned by `postgres`);
both workflow files (the n8n state matches the files, per `test_repo_files_match_n8n`); contracts;
tests; PROJECT.md, DATABASE.md, OPERATIONS.md and WORKFLOW-ROADMAP.md; the G2 results file against
the logged `app.run_step` rows (runs 842–863). `.venv/bin/pytest`: 206 passed (rerun here,
since Task 7 did not rerun it). There are no secrets in the diff, every commit is one line, and
DB changes are `.sql` files.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | docs/work/m2-best-fit-style/brief.md:88-92, tests/test_step2_pick.py:69-75 | A4's example is not met as written. "A strong stout with vanilla, tonka bean and lots of lactose" without the words "pastry stout" gives 20C (named "stout") or 27I (named null), not `dessert-stout-or-pastry-beer`. The test passes only because its brief and request name "pastry stout". `wanted` items never reach the word signal (`app.brief_words` reads only `hints` and `unknown`), so the ingredients can't move the pick. No Deviations line records this. | An acceptance criterion and the code disagree, with no record. A fix is either a scoring change or a deviation that rewords A4's example to a request that names the style, and either one needs the user's answer. The catch-all rule itself works and is tested. |
| 2 | should-fix | tests/test_step2_pick.py:103-104 | `test_briefs_reach_the_bar` counts a hit when the expected code appears anywhere in the output's `style` + `alt_styles`. The G2 grader (`evals/grade.py:78`) and the plan check that the picked `style.code` is in the brief's `style` + `alt_styles`. | The SQL-level A1 test is looser than A1. With up to 4 loose alternatives (see #3), a wrong pick that keeps the right style among its alternatives still passes. Today all 20 are exact picks, so nothing is hidden yet. |
| 3 | should-fix | db/022_step2.sql:265-268, 369-379 | On the real b05 run, 15B wins by 0.05 (2.12 against 3A Czech Pale Lager 2.07 and 1A 2.06), and `alt_styles` is `["3A", "1A", "16A", "16B"]`. Two pale lagers are listed as alternatives to a stout request, because a 0.25 partial name ("stout") is worth 1 and number fit alone nearly matches it. With the BJCP-only setting, b21 (session IPA) picks 3A Czech Pale Lager, with a mismatch naming "12C English IPA" as the style the user named. | It passes the bar, but A2's b05 rests on a very thin margin. Alternatives that are not the same kind of beer will be shown to the user later (M3/M8). |
| 4 | should-fix | db/022_step2.sql:186-200 | Prominence cues match whole words only, and a damper anywhere in the sentence vetoes. "the honey really shines" → false; "a honey ale that showcases the honey" → false; "honey-forward, with some citrus hops" → false (the "some" belongs to the hops). b12 passes only because its second clause says "taste". | The specialty rule (R7) misses ordinary wordings of the same intent. The user asked for general rules, not wording that happens to fit one brief. The plan specified whole-word matching, so this follows the plan. |
| 5 | note | db/022_step2.sql:103-104 | A zero-width range (lower = upper) would divide by zero inside `style_number_score`. The catalog has none today (checked on all four ranges). | Only matters if a later load adds such a range. |
| 6 | note | docs/DATABASE.md:410 | The signal-function line leaves out `app.adjunct_cue` (added in Task 5, recorded in Deviations). | The DB doc is incomplete by one function. |
| 7 | note | PROJECT.md §4 Scripts row | The row still says "`pytest` gives 122 passed … (measured 2026-10-12)" and "`tests/test_recipe_briefs.py` (10 tests)". Now 206 pass and the brief tests number 11. The new step 2 and style-pair test files are not listed. The row is dated, so it is stale rather than false. | The status column is behind the measured state. |
| 8 | note | docs/work/m2-best-fit-style/plan.md Deviations | Two lines describe the name-matching script that Task 2 later removed (the `same_word` 0.85 threshold, and "pairs proposed by Claude …" before the delegation). | History only. The current plan text is right. |
| 9 | note | — | Process: Tasks 1, 2, 3 and 5 partly skipped writing the test first (implementer's note). The critical-behaviour tests listed in the plan all exist, and each fails if its behaviour breaks: checked by reading the assertions. | No gap in what is tested. |

## Re-review 2026-10-13

Diff: 86e173c..2f56b5a (fixes for findings 1-4)  ·  Verdict: fixes needed

Checked: the fix commit against findings 1-4; the deployed `app.step2_best_style`,
`app.adjunct_cue` and `app.style_name_covers` match `db/022_step2.sql` by md5 and are owned by
`postgres`; `.venv/bin/pytest` 215 passed (rerun here); the logged b12 step 2 output (run 899).
To check the new scoring for regressions, the pre-fix function was rebuilt as a session-only
`pg_temp` copy (`NO_NAME_FACTOR` 1, no `covers` condition) and both were run on all 22 distinct
step 2 inputs logged in `app.run_step` and on 27 probe briefs. On the 22 logged inputs only b05
changes (its pale lagers leave `alt_styles`, as intended). Commit is one line, no secrets.

Earlier findings:
- **1 (A4 example): fixed.** A4 and its Deviations line now use the smoke porter;
  `test_smoke_porter_keeps_the_ba_style` checks `smoke-porter` is kept and the reason names 32A.
- **2 (bar test looser than A1): fixed.** `test_briefs_reach_the_bar` checks the picked
  `style.code` against `style` + `alt_styles`, as `evals/grade.py` does.
- **3 (b05 margin, pale lager alternatives): fixed for b05, but the rule breaks the mismatch case
  in general.** See new finding 10.
- **4 (prominence wording): partly fixed.** Word forms now count and a damper far from the
  adjunct no longer vetoes, but see new findings 11 and 12.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 10 | must-fix | db/022_step2.sql:354-355 | `NO_NAME_FACTOR` halves numbers and words for every style that shares no word with the name. That is exactly the style a mismatch needs: the named style is ruled out by a number and the fitting style has another name. b05 works only because 15B happens to share "stout". Same shape, other styles (pre-fix → now): "a 5% barleywine" 8B + mismatch 22C → **unknown**; "a 4% tripel" 1A + mismatch 26C → **unknown**; "a classic German pils at 80 IBU" 22A + mismatch 5D → **unknown**; "an 8% kolsch" 9C + mismatch 5B → **5B, no mismatch**; "a 4% doppelbock" → **9A, no mismatch**; "an 8% berliner weisse" → **23A, no mismatch**. "A 9% roasty lager" now picks the BA catch-all `other-strong-ale-or-lager` at exactly MIN_SCORE (1.00), on the word "lager" alone. | R4 ("a stated number that rules out the named style produces the mismatch") now holds only when the fitting style shares a name word, and R8's unknown result is returned for requests that name a real style. The rule fixes b05 rather than the general case, which the user ruled out. The pre-fix picks for these probes were weak too, but they were picks with the mismatch reported. Possible fixes, for the user to choose: apply the factor only when choosing `alt_styles` (pick, unknown and mismatch as before; b05's margin stays 0.05), or drop it and accept finding 3. |
| 11 | should-fix | db/022_step2.sql:229-231 | `adjunct_cue` returns the captured stem, not the word in the request. The logged b12 run (899) gives the reason `honey is prominent in the request ("shin")`; "taste" would show as "tast". | The reason quotes text that is not in the request. Capturing the whole word (`'\m(' \|\| cue \|\| '\w*)'`) would fix it. |
| 12 | should-fix | db/022_step2.sql:222 | The damper check also looks after the adjunct (`adj \|\| gap \|\| damp`), where a damper almost always belongs to the next item, and DAMPER_GAP = 2 is the exact edge of the new test. Measured: "Plenty of honey and some citrus." → not prominent; "Lots of honey and a little lemon zest." → not; "Honey forward and some citrus." → not; "I want some citrus and honey forward." → not, while the tested "I want some citrus hops and honey forward." (3 words between) → prominent. | Finding 4's case (a damper that belongs to another ingredient) still vetoes in ordinary wordings. R7 misses them; the gap was set where the test passes rather than from a general rule. |
| 13 | note | tests/test_step2_pick.py:79-88 | `test_b05_wins_clearly_and_lists_no_pale_lager` requires a lead of ≥ 0.1; the measured lead is 0.12. It adds the hint `session` to copy step 1's wrong b05 output. | The threshold is set from one measurement of one brief; small weight changes will trip it. |
| 14 | note | db/022_step2.sql:63-75 | `style_name_covers` is stricter than the name score: one extra word in `named` that no style name holds ("classic German pils") means no style covers it, so no mismatch can be reported for it. ("Dry Irish stout" still reports 15B, through BA Irish-Style Dry Stout and its pair.) The b21 case it was written for is right. | Depends on step 1 keeping adjectives out of `named`; not measured. |
