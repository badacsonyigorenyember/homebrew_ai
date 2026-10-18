# Review: s9-misc-extras

Diff: main...s9-misc-extras at 4634d82  ·  Verdict: ready for testing

Checked against [brief.md](brief.md) (R1–R15, A1–A15), [plan.md](plan.md) (Tasks 1–14 and their
Deviations) and [doc-calc.md](doc-calc.md) (§A–§E). Full `pytest` on the live stack at 4634d82:
**899 passed** (275 s, measured 2026-10-18 during this review).

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | PROJECT.md:127 (§4 Scripts row) | The status column still says `evals/recipe_briefs.toml` has "22 briefs" and `tests/test_extra_ingredients.py` "59 passed, measured 2026-10-17"; the intake entry does not say misc is loaded. Only §8 and "Last updated" were changed. | CLAUDE.md and PROJECT.md §10 ask for the status columns the work touches to be updated with measured facts; this row now describes the pre-s9 state. |
| 2 | should-fix | loaders/style_envelopes.toml:2404 | The 30A comment says the hand-written spice row "waits for review", but the style has `reviewed = true` and you approved it (Task 10, PROJECT.md §8). | A reader of the reviewed envelope file is told the row is unreviewed. No effect on what loads. |
| 3 | should-fix | tests/test_ingredient_resolver.py:127 | `test_misc_kind_words_leave_brief_words_alone` only asserts that no b01–b22 wanted word resolves to a misc. Plan Task 5 asks that every word "still resolves to the same products". A word containing `spice`, `herb` or `fruit` that used to find a hop or yeast would now find nothing, and the test would still pass. Today no b01–b22 wanted, excluded or inventory word contains a misc kind word (checked), so nothing is broken. | The test would not catch the one regression the new kind words can cause. |
| 4 | note | tests/test_extra_ingredients.py (counts 17 / 13), tests/test_misc.py::test_live_misc_entries | Several intake tests count the 4 live misc entries in their totals (recorded Task 11 deviation). | Adding a fifth real misc file will break these counts. That is recorded, and it is your call. |
| 5 | note | n8n/workflows/ | Task 13's `grep` was not run. I ran it: no workflow file names `style_fit_recipe`, `specialty_style`, `step5_refs`, `ingredient_choices` or `ingredient_kind_word`. The step functions the workflow calls keep their signatures. | Closes the gap in the implementation notes. |
| 6 | note | PROJECT.md §8 Task 14 entry | The entry says the full suite was not re-run after the test fix. It has now been run: 899 passed at 4634d82. | Closes the gap. dev-verify can record the measured number. |
| 7 | note | loaders/extra_ingredients.py:369, live `ref.ingredient.raw` | `usages_ref` is accepted (`<key>_ref` for any misc key) and stored in `raw.intake.fields` (live: cold brew, vanilla bean, orange peel). `field_source` holds slugs only, as for s8. | Answers Task 11's note: the page refs are not lost. |
| 8 | note | docs/STYLE-FIT.md §3 | The old row "spice · fruit · wood · smoke · ✅" became "any · tag `smoke` · ❌". That matches `app.usage_effects()` (`('any','smoke',…,false)`) and falls within Task 14's §3 scope. | No action. The doc now matches the code. |
| 9 | note | loaders/extra_ingredients.py `check_aliases` | `--check` still checks a liquid extract's aliases, but `load` skips them (plan Task 4: "not stored or checked", on the load side). | Harmless. A future extract alias that clashes with a loaded product is refused early. |
| 10 | note | tests/test_misc.py::test_process_aids_are_allowed_everywhere | A6 is tested on 5 enveloped styles plus 1 style with no envelope, not on every style. The process-aid return comes before any style lookup in `app.style_level`, so A6 holds by construction. | No action. |

## What was checked

- **Plan:** Tasks 1–14 are done as written, or the difference is in Deviations: the alias "coffee"
  was dropped, the 30A ingredient-row exemption added, `test_contracts.py` changed, the
  one-recipe rule kept for b01–b22, and the brief-word test skips b23/b24. Task 3's tests were
  written after its code. The tests now present cover every refusal row and `misc_waits` reason
  the plan names.
- **Brief:**
  - R1: the `db/012` columns and the five checks. Owner is `postgres` for the table and for every
    changed function (live `pg_proc`).
  - R2–R3: `check_misc`, `load_misc`, the summary lines, the spot-check section, the tagger
    branch, and process aids not flagged.
  - R4: three kind words.
  - R5–R6: the misc branch of `app.style_level` follows Approach steps 1–7. M1 0.5, M2 2.0 and
    M3 2/4/6 each carry a basis. A boundary dose stays in its band. Tags are never read.
  - R7, R9: `ingredient_choices` gives one choice per usage. `style_fit_recipe` gained `extras`,
    and the one-argument call is unchanged.
  - R8: `specialty_style()` has the doc-calc §A/§B codes. Section 7 picks the first feature item
    and the first misc product in resolver order (`resolve_ingredient` orders by name, id), base
    style first.
  - R10: `evals/results/2026-10-18-s9.json` has steps 1–5 at 24/24, 0 not run.
  - R11, R14: the four live rows match doc-calc §E exactly, there are no process rows, and the
    vanilla extract fixture is not loaded.
  - R12, R15: `app.step5_misc`, the schema in all three ref places, and "no sourced dose".
  - R13: the TODO in the summary and on the RECIPE-ROADMAP Later list.
- **Correctness:** doses are g/L and times are minutes. `g / volume_l` is used in
  `style_fit_recipe`. Ranges are closed `[lo, hi]` (`to_range`), so a point anchor such as
  `[3.0,3.0]` is not empty. A one-sided range cannot pass `check_range`. No brewing maths is
  left to the LLM.
- **Safety:** no secrets in the diff. DB changes are `.sql` files applied as `postgres`. No
  guard-rule workaround.
- **Records:** 18 commits, each a single line of at most 60 characters, with no body or trailer.
  §8 has a dated entry per task. See finding 1 for the status column.
