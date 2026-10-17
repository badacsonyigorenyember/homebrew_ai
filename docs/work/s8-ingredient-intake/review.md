# Review: s8-ingredient-intake

Diff: main...s8-ingredient-intake at cb49b2e  ·  Verdict: fixes needed

The tasks are done as the plan says. The five work test files pass (122 passed: `test_extra_ingredients`,
`test_ingredient_resolver`, `test_tags`, `test_fermentable_facts`, `test_step3`). Live `ref` has 0
intake rows and 0 aliases. `ref.ingredient_alias`, `app.resolve_ingredient` and
`app.resolve_ingredient_by_name` are owned by `postgres`. The hopline product-map keys equal the 289
fermentable, hop and yeast keys in the DB, and there are no secrets in the diff. Findings 1–3 come
from probes I ran on the fixtures in rolled-back transactions.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | must-fix | loaders/extra_ingredients.py:505 (`write_kind_row` gets only the not-None values) | Re-loading after a field is cleared keeps the old value. I loaded the fixtures, set `ebc = []` and `ebc_ref = ""` in `fixture-crystal.toml`, and loaded again. `ref.fermentable.ebc` was still `[230,270]`, `field_source` no longer had an `ebc` key, and `raw.intake.fields.ebc` was `[]`. | Clearing a value is how you fix a figure the source doesn't state. After that the row holds a figure with no source that disagrees with its own `raw`, which breaks the `ref` rules (every value sourced, unknown stays NULL). |
| 2 | must-fix | loaders/extra_ingredients.py:413-420 (`check_aliases`) and 580-586 (`load`) | An alias that equals the name of another file in the same set passes both `--check` and the load, and then takes over that product's name. I set the fixture hop's alias to `"Fixture Ale FA-1"`: `--check` found no errors, the load succeeded, and `app.resolve_ingredient('Fixture Ale FA-1')` returned only `Fixture Hop` (rule `alias`). `check_aliases` checks names only through `resolve_ingredient_by_name` on rows already in the DB. The load-time check resolves aliases but not product names. | A product you just added can't be found by its own name. This breaks R6 ("only that product") and A11 (each product resolves for its name). The implementers' point 3 is real and goes further than they said: the load-time check misses it too. |
| 3 | should-fix | loaders/extra_ingredients.py:406-412, 421-425 | `check_aliases` compares alias words in the order they were written: `app.ingredient_words` does not sort, so `{crystal,fixture}` ≠ `{fixture,crystal}`. It also ignores the kind-word form. The resolver sorts the words and removes kind words. So `"crystal fixture"` on the hop, next to the fermentable's `"fixture crystal"`, passes `--check`. The load then raises `RuntimeError` and rolls back (probed). | Nothing wrong is written, but R6 says `--check` refuses such an alias. Today `--check` says ok and only the load fails. |
| 4 | should-fix | tests/test_extra_ingredients.py:262 (`test_load_twice_same_rows`) | Loading twice uses the same files, so the test still passes with the alias `delete` removed (implementers' point 3), and it can't catch finding 1. No test loads, edits a file (clears a field, drops an alias) and loads again. | Re-loading an edited file is the normal way to correct an entry, and that path has no test. |
| 5 | should-fix | loaders/extra_ingredients.py:11-22 | The module docstring still says "The load follows in a later task", and its Usage shows only `--check`. | The docstring is where a reader learns what the module does, and it describes the module as it was before Task 5 (implementers' point 5). |
| 6 | note | full `pytest` (implementers' point 1) | The 3 failures (`test_formulation_check::test_mash_mapping`, `test_reference_recipes[b12]`, `[b22]`) are not caused by this work and pass on `main`. The branch was cut at `beabf3d`, before `s5-mash-attenuation` was merged into `main` (`e8dcd2b` "Replace mash mapping with Troester's curve" changed `app.mash_attenuation`, `test_mash_mapping` and `mash_c` of b12 and b22). The live DB already runs s5's `db/032`, but the branch still has the old tests: `mash_attenuation('[78,82]', 64)` gives 80, the old test expects 82. I ran `main`'s `test_formulation_check.py` and `test_reference_recipes.py` on the live DB: these three pass (61 passed; the 2 that failed failed only because the copy lacked `shared/contracts/`). Task 1 cannot be the cause: `resolve_ingredient_by_name` is `main`'s `resolve_ingredient` body unchanged, and with 0 live aliases `resolve_ingredient` returns the same result. | The 3 failures go away once `main` is merged into the branch. The PROJECT.md §8 2026-10-17 entries will conflict in that merge, because both sides added lines there. |
| 7 | note | shared/ingredients/_templates/*.toml (header comment) | Implementers' point 2: `<field>_source` is an allowed extra key that the templates mention only in a header comment. The plan's format table says every key is present in the template. `test_template_filled_from_fixture_passes` holds only because no fixture uses a `_source` key. | Harmless now. The s10 form, which builds on this contract, has to know about this key. |
| 8 | note | tests/test_extra_ingredients.py:405; tests/test_tags.py, tests/test_fermentable_facts.py | Implementers' point 4: I checked that the Task 6 tests do fail without the edits. With the fixtures loaded in a rolled-back transaction, `main`'s versions of `test_every_hop_tagged_or_flagged`, `test_file_matches_the_database`, `test_db_roles` and `test_db_descriptions` fail, and the branch's versions of all 11 G10 DB tests pass. `test_g10_counts_ignore_intake_rows` also asserts 90 hops in all, so it proves the fixture rows are there. The filter in `test_db_max_pct` is not exercised, because the fixture fermentable has a `max_pct`. | None needed. |
| 9 | note | loaders/extra_ingredients.py:347-353, 375-379 | The clash key includes the producer. An intake hop named `Citra` with a non-empty producer is not refused (hopline hops have producer `""`), and `resolve_ingredient('citra')` then returns both. | This is within R2's wording ("(kind, producer, name)"). It is a way to get a near-duplicate hop. |
| 10 | note | commit 2c34372 | The draft briefs for s9 and s10 are committed on this branch. They are not in the s8 plan. | Docs only, and recorded in PROJECT.md §8. |

## Fixes (2026-10-17)

Main was merged first (e495ab2), so the 3 old failing tests pass. Full pytest: 778 passed.

- 1 fixed: `write_ingredient` now writes every column, so a cleared field goes back to NULL and
  `field_source` loses its key. Test: `test_reload_after_editing_files` (also drops an alias).
- 2 fixed: `check_aliases` refuses an alias equal to another file's product name, and `load` raises
  when a product's name finds another ingredient by an alias. Tests:
  `test_alias_equal_to_another_files_name_refused`, `test_alias_equal_to_another_files_name_rolls_back`.
- 3 fixed: alias words are compared sorted, and with the kind word removed as the resolver does
  (`alias_matches`). Test: `test_alias_same_words_other_order_or_kind_word_refused` (3 cases).
- 4 fixed: `test_reload_after_editing_files` loads, edits the files (clears fields, drops an alias) and loads again.
- 5 fixed: the module docstring now describes the load and shows both commands.

## Re-review 2026-10-17

Diff: main...s8-ingredient-intake at d8d5678  ·  Verdict: ready for testing

Checked: findings 1–5 against d8d5678, the merge e495ab2, and the rest of the fix commit. `main`
has no commits the branch lacks. The merge conflicted only in PROJECT.md, and the resolution keeps
both sides (main's s5 entries and the Scripts row text, plus the s8 lines). Full `pytest`:
778 passed (182 s). Live `ref` still has 0 intake rows and 0 aliases after the run and after my
probes, which ran in rolled-back transactions.

- 1 fixed. `write_ingredient` passes every column to `write_kind_row`, so a cleared field is
  written as NULL and `field_sources` leaves its key out. With the old not-None filter put back,
  `test_reload_after_editing_files` fails.
- 2 fixed. `check_aliases` refuses an alias whose sorted words equal another file's name, and
  `load` raises when a product's name finds another ingredient by an alias. With both checks
  switched off, the two new tests fail.
- 3 fixed. `alias_words` sorts, and `alias_matches` applies the resolver's kind-word rule in
  both directions between files and against stored aliases. It matches `app.resolve_ingredient`
  in db/036. With the sort removed, 2 of the 3 new cases fail. The third case (`Fixture Crystal Malt`)
  passes either way, but it covers the kind-word rule.
- 4 fixed. `test_reload_after_editing_files` loads, clears `ebc`/`ebc_ref`, drops the hop's alias,
  loads again, and checks the column, `field_source`, `raw` and the alias count.
- 5 fixed. The docstring describes the load and shows both commands.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 11 | should-fix | loaders/extra_ingredients.py:432-434 (`check_aliases`, name check) | The name check compares sorted words only. It misses the kind-word form that the resolver and the load check apply. Probe: the yeast `fixture-ale.toml` renamed to `Fixture Ale FA-1 Yeast` and `fixture-lacto.toml` given the alias `"fixture ale fa-1"`. `--check` found no errors, and the load raised `name: 'Fixture Ale FA-1 Yeast' finds ingredient id … by an alias` and rolled back. The plan.md deviation and the PROJECT.md §8 line say `--check` refuses this form too. | Nothing wrong gets written, because the load refuses it. This is the same gap as finding 3, for names: `--check` says ok and only the load fails, and the record claims more than the code does. |
| 12 | note | PROJECT.md §4 Scripts row | It still says `tests/test_extra_ingredients.py` 52 passed. The file now has 58 tests. | A stale count. dev-verify can refresh it with its measured run. |
