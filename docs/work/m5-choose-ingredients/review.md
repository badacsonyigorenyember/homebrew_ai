# Review: m5-choose-ingredients

Diff: main...m5-choose-ingredients at fe30fa2  ·  Verdict: fixes needed

Commit 4b67c26 (CLAUDE.md and `.claude/skills/dev-flow/*`, "open files beside chat") is a separate
user request on this branch and is not reviewed against the brief.

Checked: brief R1–R13 and A1–A16, plan Tasks 1–10 and Deviations, `db/036`, `db/042`–`044`,
loaders, contracts, both workflow files, `evals/grade.py`, `evals/run.py`, `evals/needs_classes.toml`,
PROJECT.md and the docs. The stored G5 runs 4174–4197 and `ref` were read (read-only). The
new and changed test files (choose table, check, outputs, grade, run, contracts, fit test, workflows,
yeasts, adjuncts, resolver, step 5) give **280 passed** (2026-10-21, 80 s); `tests/test_pipeline.py`
was not re-run (the 1033-pass full run of 2026-10-21 is recorded in PROJECT.md §4).

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | `db/042_choose_table.sql:304-305`, `evals/run.py:163` | A style with no reviewed envelope sets `v_guidance` false, and `app.choose_yeast_rules(v_style_used, v_guidance)` then switches the **lager and family rules off** as well. 96 lager styles are unrated (BJCP 21, BA 75), e.g. 4A Munich Helles, 2A, 3A: measured `app.choose_yeast_rules('4A', false)` gives `lager: false`, so an ale yeast passes the check. The grader reads `guidance` from the logged step 6 input, so it would pass it too. The lager rule reads tags and category, not levels, so it does not need a rated style. The plan's Deviations record this as "an implementation detail, no scope change". It also says "any Brewers Association style" is unrated, but 3 BA styles are rated, b22's `mexican-style-amber-lager` among them. | Brief R5 says lager styles get a lager yeast, defined by the BJCP `bottom-fermented` tag or a BA lager category. That breaks for 96 styles, and neither the check nor G5 would show it, because all 24 briefs use rated styles. Turning guidance off for 259 of 285 styles also changes how R4 behaves. Conventions say a requirement change needs the user's answer first. |
| 2 | must-fix | `evals/grade.py:493-506`, `evals/needs_classes.toml:178` | In `stands_in`, the hop's purpose is compared with **each** class row, so a class that lists one `dual` hop lets any hop of the same origin stand in, even a bittering-only one. The widened Hallertau Mittelfrüh class includes Tettnanger (dual, DE), so Magnum (bittering, DE, a single 60-minute addition) counts as `substituted: Magnum` in b13, b14, b17 and b22. Reproduced on the real class map. `test_hop_stand_in_needs_same_origin_and_a_fitting_purpose` asserts "bittering for aroma" is a gap, but only for a one-name class, so it misses this. | Brief R10 asks for "a fitting purpose". If a bittering-only hop may not stand in for the aroma-hop class, b13, b17 and b22 become gaps (b14 already fails), so needs is **15/24, not 18/24**. The user's recorded G5 decision ("Accept G5 needs at 18/24") was made on the higher number. |
| 3 | should-fix | `evals/grade.py:502-503`, `evals/results/2026-10-19-m5.json` (b10) | b10's Special B verdict is `substituted: Caraamber`. Caraamber is a crystal malt of EBC 60–80, and the Special B class is Special W (280–320) or Caraaroma (350–450). The fermentable stand-in rule checks role only, so any crystal malt stands in for the dark-crystal class. | A16 says b10's Special B need is "covered by Special W or Caraaroma". It is not, and nothing records it as unmet. b10 fails needs anyway (pilsner malt, Styrian Golding), so the 18/24 count does not change. |
| 4 | should-fix | `db/043_choose_check.sql:200-203`, `evals/grade.py` `step6_problems` | b14's main yeast is Philly Sour (`type` null, family `sour`), with YF-998 as the lacto culture. The check and the grader only require that the main yeast is not `lacto`, so step 6 is graded a pass. | A15 says b14 has "its ale yeast and one lacto culture". The ale-yeast half is unmet. It shows only indirectly, as the needs gap "German ale yeast", while step 6 reports 24/24. |
| 5 | should-fix | `PROJECT.md:288` | The m4-targets-blueprint Task 6 entry (dated 2026-10-17) was edited in fe30fa2 and now says `db/042`–`044` were added there. The Task 10 entry says "§4 Database, Scripts rows updated", but the §4 Database row did not change. | §8 is a dated log, and the m4 entry is now false. The §4 update the plan asked for (Task 10, "Database functions") went into the wrong place. |
| 6 | should-fix | `PROJECT.md:249` (Task 9 entry) | Plan Task 9 asks for these measurements in the §8 entry: b08's late hop and its level in 5D (A6), the b10 and b15 inventory picks (A3), the b14 yeasts (A15), the b23 and b24 doses (A16), and run time per brief. Only totals are recorded. Measured now from runs 4181, 4183, 4187, 4188, 4196 and 4197: b08 Magnum boil 60 (allowed) and Tettnanger boil 15 (typical, rated at the table's "boil 5 min" choice); b10 Munich Malt Type 1, Abbaye and Brown Candi Sugar from inventory; b15 Maris Otter, Crystal T50 and East Kent Golding from inventory; b14 Philly Sour and YF-998; doses b23 coffee 3, vanilla 0.05, b24 orange peel 2.64. | PROJECT.md facts should be measured and present. A6's b08 clause is not checked by the grader (#7), so the record is the only evidence for it. |
| 7 | note | `evals/grade.py:318-340` | The A4 check reads `level` from the step output (built by `db/044`), not from the logged candidate rows or `ref`, and it skips wanted picks. A4's "a wanted item keeps step 3's best level" is enforced only by the SQL check. A6's "✅ or 👍" for b08's late hop is not graded either: the grader rejects only `out_of_style` and `changes_style`. Both match plan Task 8's list. | Low risk on the measured run (b08's Tettnanger is typical). A fault in `db/044`'s choice mapping would not be caught by G5. |
| 8 | note | n8n's own Postgres (`aihomebrewassistant-postgres-1`) | The debug workflow `DBGtmp0000000001` was deleted directly from n8n's database. Checked read-only: 0 rows for `DBG%` in `workflow_entity`, `shared_workflow`, `execution_entity`, `webhook_entity` and `workflow_history`. This is not the app database, so the `.sql` rule does not apply, and the guard was not involved. It is not recorded in OPERATIONS.md. | No data left behind. "MCP cannot archive a workflow" is an operational trap that OPERATIONS.md does not yet name. |
| 9 | note | `docs/DATABASE.md:212, 495` | A reload of the adjunct loader nulls `max_pct`, so `loaders.fermentable_facts` must run after it. The load order is documented in both places, and today 0 fermentables have a null `max_pct`. | No action. |
| 10 | note | `evals/grade.py:493` | `stands_in` is deterministic (picks sorted by id), pure Python and tested by kind. Columbus for Simcoe in b01 (US, dual and dual) and Flaked Rice for Flaked Corn in b22 (both `adjunct`) follow the brief's revised R10 as written. The rule never consults the style, although the brief's 2026-10-19 Deviation speaks of "a gap the style explains". | Matches R10 and A10. The leniency is the user's call, apart from #2 and #3. |

## Re-review 2026-10-23

Diff: main...m5-choose-ingredients at e411c39  ·  Verdict: fixes needed

Checked: the six earlier findings against fix commits 555dcb7, 5a5e12b and e411c39, plus the code
paths those fixes touch. The live database has the fixed `app.choose_table` and `app.step6_errors`
(read with `pg_get_functiondef`), `app` has 129 functions, all owned by `postgres`. The affected
test files (grade, choose check, choose table, run, choose outputs, contracts, workflows, yeasts)
give **249 passed** (2026-10-23, 50 s). The re-graded `evals/results/2026-10-19-m5.json` gives
needs 15/24, 12 gaps, steps 6-9 24/24, 56 calls, as recorded.

Earlier findings:

| # | Status | Evidence |
|---|---|---|
| 1 | resolved | `db/042_choose_table.sql:306` passes the brief's guidance to `app.choose_yeast_rules`. Live: `app.choose_yeast_rules('4A', true)` gives `lager: true`. `evals/run.py:165` reads step 1's `guidance` (required in `step1.output`). The plan's Task 7a Deviation is corrected. Tests: `test_unrated_lager_style_keeps_the_yeast_rules`, `test_unrated_lager_style_still_needs_a_lager_yeast`, `test_choose_facts_keep_lager_rule_for_an_unrated_style`. |
| 2 | resolved | `evals/grade.py:514-517`: the pick needs the class member's purpose or must be `dual`. b13, b14, b17 and b22 are now gaps. The test runs against the real class map. |
| 3 | resolved | `evals/grade.py:495-501` `_colour_fits`, called at `:512`. b10's Special B is now `gap`. |
| 4 | resolved, with a regression | `db/043_choose_check.sql:203-205` and `evals/grade.py:360-361` require an `ale`, `lager` or `kveik` main yeast. b14 was re-run (run 4246: Munich Classic and YF-998). The new rule conflicts with the inventory and wanted rules: see #11. |
| 5 | resolved | The m4 Task 6 entry matches `main` again. The §4 Database row (`PROJECT.md:119`) now names `db/042`-`044` and the 129 functions. |
| 6 | resolved | The Task 9 entry (`PROJECT.md:250`) now holds the b08, b10, b15, b14, b23 and b24 measures and the run time. |

New findings:

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 11 | must-fix | `db/043_choose_check.sql:203-205` against `:243-268` (inventory) and `:159` (wanted); `db/042_choose_table.sql:215-224` | The new main-yeast type rule refuses 5 catalogue yeasts as the main yeast: CBC-1, Suava Ale and Philly Sour (type null) and YF-801 and SafBrew BR-8 (type `brett`). The table still marks them as fitting (`app.choose_fit_reason` does not check type), and the souring slot takes only `lacto`, so a fitting inventory or wanted yeast of these 5 has no slot it can fill. Reproduced on b01 (21A): with "CBC-1" in the inventory, CBC-1 as the main yeast gets "is not a brewing yeast", and SafAle US-05 gets "the inventory has a yeast that fits ... must be one of them: 1848 CBC-1". With Philly Sour or CBC-1 wanted, the main yeast gets either "not a brewing yeast" or "the wanted ... has no pick". No proposal passes, so the run stops with `steps 6-9 answer failed twice`. The R5 band check (`:216-224`) still counts these yeasts as usable too. The prompt (`shared/prompts/choose.system.md`, `db/042_choose_table.sql:560-567`) does not name the type rule, so the LLM learns it only from a retry. | R3 and the wanted-slot rule (R4) break for these inputs. Before 555dcb7 they passed. None of the 24 briefs hits this, so G5 does not show it. "I have CBC-1" or "use Philly Sour" in a sour is a realistic request. |
<!-- resolved 2026-10-23, user decision "Brewer's choice wins": `db/043_choose_check.sql` step6_errors and the R5 usable test, `evals/grade.py` step6_problems; brief.md Deviations. -->
| 12 | should-fix | `PROJECT.md:246` | The review-fixes entry says the tests pass "(see the commit)". Commits are one line by convention, so there is no count to see. Measured now: 249 passed on the affected files. | PROJECT.md facts should be measured and written in the file. |
<!-- resolved 2026-10-23: the 2026-10-21 review-fixes entry in `PROJECT.md` holds the test counts. -->
| 13 | note | `docs/WORKFLOW-ROADMAP.md:186`, `PROJECT.md:250` | The roadmap says "b08 has no late hop (Magnum 60 min, Tettnanger 15 min boil)". The new PROJECT.md text says "its late hop is Tettnanger in 5D". The roadmap line is older than the fix commits. | The two records disagree on A6's b08 clause. |
<!-- resolved 2026-10-23: roadmap and `PROJECT.md` both say Magnum boil 60 min, Tettnanger boil 15 min (run 4181). -->
| 14 | note | `evals/grade.py:511-513`, `evals/results/2026-10-19-m5.json:551, 554` | Fermentables still stand in through each class row, by role. Melanoidin Malt (kilned) stands in for "Vienna malt" through Munich Light Malt (kilned), in b09 and one other brief. In b09, Herkules (dual, DE) stands in for Hallertau Mittelfrüh, which the per-member purpose rule allows. Neither verdict changes a count: Pilsner Malt (base) also stands in each time. | This leniency is the user's call (R10, earlier #10). |
<!-- resolved 2026-10-23, user chose to tighten: `evals/grade.py` `_colour_fits` (kilned) and `_alpha_fits`; needs now 14/24. -->
