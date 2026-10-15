# Review: s2-formulation-rules

Diff: main...s2-formulation-rules at 9e6264b  ·  Verdict: fixes needed

Checked: brief R1–R21 and A1–A16, plan Tasks 1–9 and Deviations, the full diff, the live catalog
(roles 81/81, `max_pct` 81/81, `min_boil_min` 60 ×74 / 90 ×7, descriptions 81, 27 pairs,
623 style rows; new tables, view and functions owned by `postgres`), and commit subjects (one
line each, no body). The five test files of this work were run with the stack up: 124 passed.
To check the rule 8–13 cases, a scratch script ran each failing case through `app.check_recipe`
and listed every rule's status (the live functions were not changed).

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | `db/032_formulation_check.sql:505-506` | Rule 10's band for a stated FG or ABV is a literal `0.002`. The rule 10 sentence (`db/031_formulation_rules.sql`) prints `midpoint_tolerance.fg` from `app.formulation_limits()`. `test_text_uses_the_limits` checks only the text side, so it does not catch this. | This breaks R9: "thresholds the code checks taken from the same place, so the text and the check cannot disagree". If the limit changes, the sentence the LLM reads changes and the check does not. The numbers are equal today, so no result is wrong yet. |
| 2 | must-fix (user to confirm the reading) | `db/032_formulation_check.sql:457`; `db/031_formulation_rules.sql` rule 9 sentence; `plan.md` Task 7 rule 9 bullet | With `guidance` false, the check skips the midpoint test for every unstated target. The rule 9 sentence still says without condition that an unstated target "is the style's midpoint". The plan's Task 7 bullet still describes the old logic. The deviation is logged as an "implementation detail", and the brief has no Deviations line for it. The code's reading is the only one that gives R10 rule 9's "or guidance is off" any effect: under the literal reading an unstated target is always the midpoint, so it is never outside the range. It also matches Task 7's planned test ("out-of-range SRM with guidance off passes"). | The text and the check disagree (R9). The LLM is told to keep unstated targets at the midpoint when guidance is off, but the check accepts any value. Rule 9 is the user's decision B, so changing its wording needs the user's answer. |
| 3 | should-fix | `db/032_formulation_check.sql:502` | When the mash temperature is below 64 °C, the rule 10 failure gives `limit` = 69 (`mash_max_c`). Measured: mash 63 gives `value 63, limit 69`. | A9 says a failure names the limit. The message text has both bounds, but the structured `limit` points the wrong way. |
| 4 | should-fix | `PROJECT.md:116`, `docs/DATABASE.md:442` | The §4 Database row still says "`ref` 15 tables … all 31" and "`ref.source` 18 rows". Measured now: 17 `ref` tables (33 in all) and 19 sources. The same row has a broken code span with no full stop (``` ``tests/fixtures/reference_recipes.toml` all pass Known gaps: ```). Both files list "`fermentable.role` was filled 2026-10-15" under Known gaps / Gaps. | PROJECT.md facts must be measured and current (CLAUDE.md, §10). |
| 5 | should-fix | `tests/test_formulation_check.py:361-479` | The fail cases for rules 9, 10, 11 and 13 assert only their own rule's status. Unlike rules 1–6, 8 and 12, they do not check that the other rules pass. Measured: each of these rules has at least one case that fails only that rule (IBU off-midpoint, mash 63, high FG, ferm 10 °C, boil 60/45), so A8 holds today. But the stated-FG rule 10 case also fails rule 9, and the 13 % ABV rule 11 case also fails rule 10. The mash limits 64 and 69 are never checked for pass/fail status. `test_rule_9_unknown_without_style_range` accepts `fail` as well as `unknown` (today it gets `unknown`, on 28A). | A8 asks for a case that "fails exactly that rule". A change that made these cases fail extra rules, or an off-by-one at 64 or 69 °C, would go unnoticed. |
| 6 | note | `db/032_formulation_check.sql:671-675`; 8 reference recipes | SRM is `null`, with `ref.fermentable.ebc` listed as missing, whenever the grist holds a fermentable without EBC: Enzyme Malt, the 4 flakes, Honey or Lactose. The plan's Approach decided this, and no checked rule reads SRM. | m6's colour solver will need a colour for these 7 rows, or a stated rule for them. |
| 7 | note | `db/032_formulation_check.sql:435-477` | Rule 9 does not check that a stated target equals the stated number. Rule 9 as worded in the brief also has no "ABV counts as stated when OG or FG is stated". So a user who states only the OG gets midpoint FG and ABV targets that cannot both hold. None of the 22 briefs states OG or FG; the test `test_recipe_follows_its_brief` pins stated = target for the fixtures. | Harmless now, because m4 sets the targets, not the LLM. Worth settling when m4 is worked on. |
| 8 | note | `tests/test_formulation_check.py` (Task 7) | The Task 7 implementer did not see the rule 8–13 tests fail first. By reading: each of rules 8–13 has asserted fail cases and pass cases, so a rule that always passes or always fails would break its test. Rule 8's 15-minute limit, rule 9's tolerance, and rule 13's 60- and 90-minute limits are tested at the boundary. | No action beyond #5. |
| 9 | note | scope and safety | Nothing is outside the brief and plan. The deleted `docs/work/s2-corpus/brief.md` and the STYLE-PROFILES note are recorded in the brief's Deviations. DB changes are `.sql` files plus the loader. There are no secrets in the diff. The RECIPE-ROADMAP "multi-step mash profiles" TODO is the user's request (plan Deviations). | — |

## Questions for the user

1. Finding 2, rule 9 with guidance off. Options:
   a) Keep the check (guidance off means unstated targets may sit anywhere) and reword the
      sentence, for example: "When style guidance is on, a target … that the user did not state
      is the style's midpoint …; a target is outside the style's range only when the user stated
      it or style guidance is off". Record it in the brief's Deviations.
   b) Keep the sentence and change the check so unstated targets are always the midpoint. The
      brief's "or guidance is off" then has no effect, and the planned guidance-off SRM test must
      change.
   Recommend a): it is the only reading in which R10 rule 9's guidance clause does anything, and
   it matches the test the plan asked for.
