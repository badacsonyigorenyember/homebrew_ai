# Review: m8-recipe-sheet-chat

Diff: main...m8-recipe-sheet-chat at 4ec49fa  ·  Verdict: ready for testing

Checked: all 18 branch commits, the SQL (`db/022`, `054`–`057`), the three workflows, the contracts and
prompt, `evals/run.py` / `evals/grade.py`, the new and changed tests, the docs and PROJECT.md. Read-only on
the stack: every new `app` function and `app.recipe` are owned by `postgres`, `app.recipe.sheet` exists,
one `app.step2_best_style` remains; recipe 1159 is `final` with its sheet. Fast test files run once
(`test_sheet_check`, `test_sheet_markdown`, `test_recipe_sheet`, `test_step2_pick`, `test_step3`,
`test_grade`, `test_run`, `test_contracts`, `test_workflows`): 359 passed in 1 min 55 s. The pipeline,
`test_sheet_facts` and full-run tests were not re-run here (dev-verify does that).

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | db/022_step2.sql:368 | A `style` sent with a request where step 2 finds no pick (the "unknown" early return) is dropped without a word: the function returns `style` null and never reaches the 7b override at line 488. The header comment (line 259) says the chosen style "wins". PROJECT.md §8 Task 2 notes it as not covered. | R5 says step 2 obeys `style`. The chat never sends `style` without a mismatch, so it is harmless today; a webhook caller who sets `style` on a vague request gets no style and no error. |
| 2 | should-fix | db/057_sheet_markdown.sql:40 | `sheet_amount` shows kg at 2 decimals, so recipes 1148 and 1158 print their saved 0.001 kg Brown Candi Sugar as "0.00 kg". The plan's precision rule gives this result, and `test_quantities_equal_saved_rows` compares at display precision, so it passes. | R1 says code writes each quantity from the saved value. A brewer reading "0.00 kg" sees a line that cannot be weighed. The tiny amount itself comes from step 11 (out of scope); how the sheet shows it is m8's. Showing g below 0.1 kg, or the stored value, would fix it. |
| 3 | should-fix | PROJECT.md:121, :256 | The §4 Orchestration row still says `Recipe chat` is "built, hand test pending", and the Task 9 §8 entry ends "Not verified: the Task 9 results are not yet approved by you". No later entry records the approval. Task 12 said the §4 rows were "unchanged (still right)". | CLAUDE.md: PROJECT.md is the single source of truth and must state measured facts. Both lines are now out of date. |
| 4 | should-fix | commit 0bdc04a | `Record the m8 full brief run` has a `Co-Authored-By` trailer. The other 17 commits have none. | conventions.md says one line, "no trailer lines (no `Co-Authored-By`)". The branch is not pushed, so it can still be reworded. Rewording rewrites the four commits after it, so you decide. |
| 5 | should-fix | plan.md:260 (Task 5) | The plan says "Seen failing first", but the Task 5 tests were written after the functions. §8 says so honestly: the number test was seen failing with the rounding check turned off. There is no Deviations line for it. | Review check 1: a difference from the plan is recorded under Deviations. The tests do catch the behaviour (the mutation shows it), so the only gap is the record. |
| 6 | note | plan.md:340 (Task 7) | The two new pipeline tests were written first but not run before the workflow existed. §8 records this. Task 7 does not ask for "seen failing first", so it is not a deviation. `test_sheet_fails_twice_without_sources` and the row-16 checks in `test_b01_validates_and_saves` assert the R7 / R6 behaviour. | No action. |
| 7 | note | n8n/workflows/recipe-chat.json (`Chat: step 2 failed`, `Chat: pipeline call failed`) | The failure sends beyond the plan are recorded in the 2026-10-31 Task 10 Deviation. They serve R4 ("a failed run shows the failed step and its error"), so they are within scope. | No action. |
| 8 | note | n8n/workflows/recipe-chat.json (`Style choice`, `Accepted?`) | Both read `$json.data?.approved`. Runs 5708 (Keep) and 5709 (Take) and the accept of recipe 1159 confirm the field. `Not now` (or the 2 h timeout) ends the execution with no message, and the recipe stays `draft`. | No action. R9 only asks for the offer to accept. |
| 9 | note | n8n/workflows/step-16-recipe-sheet.json (`Save sheet` → `Check step 16 output`, `Check answer`, `Check step 16 input`) | These nodes have no error output. If `Check step 16 output` fails, the sheet is already saved but the run ends `failed_step` 16 with no row 16. If the input check or a check query raises, the run also has no row 16. Neither case has happened (19/19 and 5/5 chat runs logged row 16). | Only an edge of R7 ("no sheet" on failure) and of R4's row shape. No run hit it. |
| 10 | note | n8n/workflows/step-16-recipe-sheet.json:457 | `Step 16 · log failed answer` builds the same `llm` object literal three times in one expression, to get `prompt_tokens`, `output_tokens` and the object. The ok path uses a `Step 16 · llm` Set node. | Readability (§6.8): hard to follow, but it works. |
| 11 | note | db/055_sheet_facts.sql:135, :152 | Choice order is `1 + kind·1000 + min(recipe_item.id)` for items and `90000 + n` for sections. Once `recipe_item.id` passes about 86,000 (now 4,715), the process keys sort before the items. | This only reorders the prompt's key list and the citation numbering, not the sheet's sections. It is latent, not a current bug. |
| 12 | note | recipe 1148 sheet | An LLM typo ("Abbayye") in a why line. Neither the number check nor the citation check can catch spelling. | No action. |
| 13 | note | commit da6b9c4 | `Add pause-work skill and resume from paused.md` changes `.claude/skills/` (dev-flow tooling). It is not in the brief or plan. | Scope: it rides on this branch into main at ship. Fine if you meant it to. |
| 14 | note | Task 12 commit | Amended once before any push. | No pushed history was rewritten. No action. |
| 15 | note | n8n/workflows/recipe-chat.json (`Chat: building`) | "Building the recipe; this takes a few minutes" is sent after step 1's model call, step 2 and any mismatch question, not straight away. | R4's "answers at once" holds loosely. The hand test accepted it. |

Plan: all 12 tasks are done as written or covered by the Deviations, except #5. Brief: R1–R12 and A1–A8
and A10 are met by the code and the recorded measurements (A9 moved to s11). R5 has the gap in #1.
Safety: no secrets in the diff, DB changes are `.sql` files, and the guard rules were respected.
