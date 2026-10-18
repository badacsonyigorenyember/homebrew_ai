# S9 · Misc extras: spices, fruit, coffee and process aids through the pipeline — implementation plan

Stage: approved
Brief: [brief.md](brief.md)
Branch: s9-misc-extras

## Approach

- **Sources first (B3, PROJECT.md §6.7).** Task 1 is a doc → calc pass written to
  [`doc-calc.md`](doc-calc.md): what Janish and *How to Brew* state about coffee, vanilla and
  orange peel doses; whether BJCP 2021 files coffee, cacao and vanilla under 30A; the BA styles
  that match each category; the subtle / aggressive cut points. **You review it and accept it
  before Tasks 6, 8 and 11 start**; they take their numbers and style codes from it. Tasks 2–5
  need nothing from it and may run while you read it.
- **Schema in place, in the shipped files.** `ref.misc` gains its columns in `db/012`
  (idempotent `alter table … add column if not exists`). Every function change goes into the
  file that already holds the function (`db/022`, `033`, `034`, `036`, `037`, `041`), as s8 did
  with `db/036`. No new SQL file. Each changed file is applied twice as `postgres`
  (docs/OPERATIONS.md §4) and its functions checked for owner `postgres` in `pg_proc`.
- **Intake.** `misc/` becomes a fourth kind of s8's loader: `check_misc` (required fields by
  `purpose`), `load_misc`, two templates (`misc-flavour.toml`, `misc-process.toml`). Three things
  load but are reported as waiting: an `enzyme` or `acid` (changes the numbers), a fruit with a
  sourced `sugar_pct` (fruit as a fermentable is decided with M6). A file with `dose_ml_per_l`
  (a true liquid extract) passes `--check`, is reported "waits" and is **not** loaded.
  Page refs stay in `raw.intake` (as in s8); `ref.misc` holds the figures and `field_source`.
- **Tags.** A flavour misc gets a family tag named after its category (9 new family tags) and
  character tags from its `descriptors`. A process aid gets no tags, no `ingredient_review` row,
  and is not "flagged" in the summary.
- **Style fit (layer 2) is its own branch in `app.style_level`**, so a misc is never scored
  through its tags. The dimension comes from a `kind = 'misc'` row of `app.usage_effects()`
  keyed by **category** (spice, herb, coffee, cacao, vanilla → `spice`; fruit → `fruit`; wood →
  `wood`; smoke → `smoke`; none for `other`), `carries_character = false`. In order:
  1. process aid → `allowed`, "no flavour effect" (any style, before the envelope check);
  2. no reviewed envelope → not rated (as today); an explicit `ref.style_rule` still wins (as today);
  3. category `other` → level `null`, "no added-character dimension";
  4. the style's envelope has no row for the dimension → `out_of_style`, "specialty <dim> on
     <style>" (today's wording for a silent specialty dimension);
  5. the row's `dose_g_per_l` is null → "no sourced dose", intensity not checked; no `g_per_l`
     in the dose → "dose not given", intensity not checked;
  6. else the dose is read **against the row's own sourced dose**: below `M1 × lower` subtle,
     above `M2 × upper` aggressive, else noticeable; the word maps to a 0–7 level (`M3`); above
     the envelope's `max_level` → `out_of_style` "too much";
  7. otherwise `typical` when the envelope asks for the dimension (`min_level ≥ 1`), else `allowed`
     (decided by you, 2026-10-18).

  M1, M2 and M3 live in `app.style_fit_cut_points()` under `misc_dose`, each with its basis
  (Task 1). The dose is read against each entry's own sourced dose (decided by you, 2026-10-18),
  so a new spice needs only its file (Goal).
- **Step 3** rates a misc at one choice per usage of its row, with no dose (as hops are rated at
  whirlpool and dry hop today), so the level is "is this sensation in the style", and a chosen
  dose is M5's job. `app.style_fit_recipe(recipe, extras default '[]')` rates each extra with
  its grams; the formulation-check contract is not touched (brief Out).
- **Step 2 (layer 1).** `app.specialty_style()` gets a `category` column next to `adjunct`:
  honey and molasses rows keep `adjunct`, the new rows name a misc category and a code per guide.
  Section 7 of `app.step2_best_style` keeps the word rule for adjuncts and adds: a `feature` item
  whose products (`app.resolve_ingredient`) include a misc product with a mapped category → that
  code, base style first in `alt_styles`. The first misc product in the resolver's order decides.
- **Step 5** gives every ref a `misc` object (null for other kinds): purpose, category, usages,
  time, sourced dose range, and a `because` that says "no sourced dose" when there is none.
- **Measured last.** The 30A envelope (you review it), the three real products, the two new
  test briefs (you approve them), then `python -m evals.run` on all 24 briefs.

Each task adds a dated PROJECT.md §8 line in its own commit (CLAUDE.md, PROJECT.md §10).

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `docs/work/s9-misc-extras/doc-calc.md` | new | Task 1: doses, BJCP/BA mapping, cut points, with quotes and arithmetic |
| `db/012_style_fit.sql` | changed | `ref.misc` columns and checks (R1) |
| `shared/ingredients/_templates/misc-flavour.toml`, `misc-process.toml` | new | the two misc templates |
| `shared/ingredients/misc/` | new | the real coffee, vanilla and orange peel files (Task 11) |
| `shared/ingredients/README.md` | changed | misc steps |
| `loaders/extra_ingredients.py` | changed | `check_misc`, `load_misc`, waits lines, summary |
| `loaders/tags.py` | changed | misc branch |
| `loaders/style_fit_vocab.toml` | changed | 9 misc family tags; character tags the entries need |
| `db/checks/ref_spotcheck.sql` | changed | misc rows |
| `db/036_ingredient_resolver.sql` | changed | misc kind words |
| `db/033_style_fit_effects.sql` | changed | misc rows in `app.usage_effects()`, `misc_dose` cut points |
| `db/034_style_level.sql` | changed | misc branch in `app.style_level`; `app.style_fit_recipe(recipe, extras)` |
| `db/037_step3.sql` | changed | misc choices in `app.ingredient_choices` |
| `db/022_step2.sql` | changed | `app.specialty_style()` by category; step 2 section 7 |
| `db/041_step5.sql` | changed | `misc` object in `app.step5_refs` / `app.step5_refs_of_id` |
| `shared/contracts/step5.output.schema.json` | changed | the `misc` object on each ref |
| `loaders/style_envelopes.py`, `loaders/style_envelopes.toml` | changed | 30A added and reviewed |
| `evals/recipe_briefs.toml` | changed | b23, b24 |
| `tests/fixtures/ingredients/misc/*.toml` | new | misc fixtures (listed in Task 3) |
| `tests/test_extra_ingredients.py`, `tests/test_tags.py` | changed | misc checks, load, tags, summary |
| `tests/test_misc.py` | new | schema, resolver, style level, step 3, step 2, step 5 with misc fixtures |
| `tests/test_ingredient_resolver.py`, `test_style_fit_effects.py`, `test_step2_signals.py`, `test_step5.py`, `test_style_envelopes.py`, `test_recipe_briefs.py`, `test_reference_recipes.py`, `test_step3.py` | changed | as named in the tasks |
| `docs/DATABASE.md`, `docs/STYLE-FIT.md`, `docs/RECIPE-ROADMAP.md`, `docs/WORKFLOW-ROADMAP.md`, `docs/INGREDIENT-INTAKE.md`, `PROJECT.md` | changed | Task 14 (PROJECT.md every task) |

## Tasks

### Task 1: the doc → calc pass says what each source states (review point)
Why: B3; R5, R8, R11, R14, R15 take their figures from it (PROJECT.md §6.7).
- [ ] Write `docs/work/s9-misc-extras/doc-calc.md` with `Status: waiting for your review` and
      these sections, each figure with its quote (under 15 words where it is copyrighted text),
      page or URL, and arithmetic (1 US gal = 3.785 L, 5 gal = 18.93 L, 1 oz = 28.35 g):
  - **A. BJCP filing.** Does BJCP 2021 put coffee, cacao and vanilla under 30A? Read
    `shared/rag-files/styles/bjcp_2021_introductions.md` (the Specialty-Type list of ingredient
    kinds, line ~369: "yeast/bacteria, smoke, wood, fruit, spice, grain, or sugar"), the 30A,
    30D and 33A text in `ref.beer_style.raw` and their commercial examples, and search `kb.chunk`
    (`app.kb_search`, sources `bjcp-2021-introductions`, `bjcp-exam-study-guide-2017`) for
    coffee, chocolate, cocoa, vanilla. Measured while planning: the introductions do not name
    coffee; 33A names vanilla, coffee and cocoa as wood-derived flavours. Say what is stated and
    what is your reading; if nothing states it, the rule is recorded as "set by the user".
  - **B. BA codes per category.** From `ref.beer_style.raw` (`ba-2026`): proposed `fruit →
    american-style-fruit-beer`, `spice`, `herb`, `vanilla → herb-and-spice-beer`, `coffee →
    coffee-beer`, `cacao → chocolate-or-cocoa-beer`, `wood → wood-and-barrel-aged-beer`,
    `smoke → smoke-beer`; quote the line of each that supports it, or say none does.
  - **C. Doses.** Coffee: Janish (`janish-coffee-beers`, `shared/rag-files/articles/janish_coffee_beers.md`)
    dry-beaned whole beans 2 oz / 5 gal for 48 h (3.0 g/L, 2880 min), cold brew 4 oz coarse
    ground in 1,200 mL for 16 h (6.0 g/L of dry coffee; when it goes in the beer); *How to Brew*
    p. 225 (`palmer-how-to-brew`, chunk "Brewing with Spices"): coffee and cocoa 60–225 g per
    5 gal (3.2–11.9 g/L). Vanilla: *How to Brew* p. 225, "most spices, such as cinnamon,
    vanilla …" 1–10 g per batch (0.05–0.53 g/L at 19 L), vanilla after fermentation. Orange
    peel: *How to Brew* recipe notes (pp. ~227–228 and the witbier recipe), about 50 g of fresh
    peel, hot-steeped 15 min after the boil; read the recipe tables in the PDF
    (`shared/rag-files/books/how_to_brew.pdf`, e.g. `pdftotext -f 225 -l 230 -layout`) for the
    batch size, because those tables were cut from `kb` (BOOKS.md §3). For each figure say what
    it stands for: a "noticeable" anchor, a usual range, or a recipe amount.
  - **D. Cut points.** `M1` (subtle below `M1 × lower` of the row's sourced dose), `M2`
    (aggressive above `M2 × upper`) and `M3` (subtle, noticeable, aggressive → a 0–7 level,
    proposed 2 low, 4 medium, 6 high, the scale of `loaders/style_envelopes.py` `SCALE`). Use a
    second source where one exists (e.g. *How to Brew*'s coffee range against Janish's
    points); otherwise propose a value marked "set by the user, <date>", as s3 did.
  - **E. The entries.** One table row per file of Task 11: file name, name, form, category,
    usages, `time_min`, `dose_g_per_l`, each `<field>_ref`, description (one to three sentences,
    from the source), descriptors (existing tags: `coffee`, `vanilla`, `orange`, `citrus`, …),
    aliases. Proposed: `coffee-whole-beans.toml` (secondary, dry-beaned), `coffee-cold-brew.toml`
    (packaging or secondary, as the source says), `vanilla-bean.toml` (secondary),
    `orange-peel.toml` (whirlpool). A figure no source gives stays empty (R15).
  - **F. Not taken.** Figures read but not used, and why (e.g. a liquid extract dosed in mL).
- [ ] Stop and report `needs-approval` with `doc-calc.md`. **Review point (you):** accept or
      change sections A–E. On acceptance set `Status: accepted <date>` and commit.
Done when: `doc-calc.md` is accepted by you.
Commit: `Add doc-calc pass for s9 misc doses and styles`

### Task 2: `ref.misc` holds the misc fields
Why: R1, A1.
- [ ] In `db/012_style_fit.sql`, after the `ref.misc` table: `add column if not exists`
      `purpose text`, `usages text[]`, `time_min integer`, `dose_g_per_l numrange`,
      `description text`, `field_source jsonb`. `purpose` and `usages` are not null on new rows
      (the table has 0 rows, measured 2026-10-18); use `not null` with the add. Replace
      `misc_category_check` with the 14 categories of R1 (drop `fining` from the flavour list,
      add `nutrient`, `enzyme`, `acid`, `other-process`; keep `fining`) and add checks:
      `misc_purpose_check` (`flavour`, `process`); `misc_category_purpose_check` (flavour
      categories only with `flavour`, process categories only with `process`);
      `misc_usages_check` (`cardinality(usages) > 0 and usages <@ array['mash','boil','whirlpool','ferment','secondary','packaging']`);
      `time_min >= 0`; `lower(dose_g_per_l) >= 0`. Each `drop constraint if exists` before its
      `add`, as the file already does.
- [ ] Write `tests/test_misc.py::test_misc_columns_and_checks` (stack, rolled back): the
      columns and types from `information_schema`, owner `postgres`, and that an insert with a
      flavour category under `process`, an unknown usage, an empty usages array, or category
      `fining` under `flavour` each fails.
- [ ] Apply `db/012` twice; run `pytest tests/test_misc.py tests/test_style_fit_effects.py`, expect pass.
Done when: the test passes and `\d ref.misc` shows the columns.
Commit: `Add misc fields to ref.misc`

### Task 3: misc files pass the checker
Why: R2, R13, R14, A2 (checks), A13, A14 (check side). No database in this task.
- [ ] `loaders/extra_ingredients.py`: `KINDS` gains `misc`; remove the "misc arrives in s9"
      refusal (and change `test_misc_file_refused` to a test that a misc file is checked).
      `KIND_KEYS["misc"]`: `purpose`, `category`, `usages`, `time_min`, `dose_g_per_l`,
      `dose_ml_per_l`, `sugar_pct`. `FIGURES["misc"]`: `time_min`, `dose_g_per_l`,
      `dose_ml_per_l`, `sugar_pct` (each needs `<field>_ref` when filled, s8's rule).
      New sets `MISC_PURPOSES`, `FLAVOUR_CATEGORIES` (9), `PROCESS_CATEGORIES` (5),
      `CHANGES_THE_NUMBERS = {"enzyme", "acid"}`, `MISC_USAGES` (6).
- [ ] `check_misc(p, f)`: always `purpose`, `category`, `usages`; category must belong to the
      purpose; usages from `MISC_USAGES`; `time_min` a whole number ≥ 0; `dose_g_per_l` a range
      in 0–1000; `dose_ml_per_l` a range; both doses filled → refused; `sugar_pct` only for
      category `fruit`, 0–100. Flavour: `descriptors` required. Process: `descriptors` must be
      empty ("a process aid has no flavour"). `producer` optional.
- [ ] A function `misc_waits(item) -> str | None` gives the one waiting reason of a misc file:
      "liquid extract dosed in mL/L, not loaded until a later work item adds mL/L" (filled
      `dose_ml_per_l`), "changes the numbers (<category>): waits for maths" (enzyme, acid), "fruit
      sugar: waits for maths; TODO: fruit as a fermentable is decided with M6" (fruit with
      `sugar_pct`). `--check` prints these lines and still exits 0.
- [ ] Templates `shared/ingredients/_templates/misc-flavour.toml` and `misc-process.toml`, in
      the style of `hop.toml` (every key, comments: required, unit g/L or minutes, "leave empty
      when the source does not say").
- [ ] Fixtures in `tests/fixtures/ingredients/misc/`, all with `source = "fixture-data-sheet"`:
      `fixture-spice.toml` (spice, whirlpool + secondary, dose [0.5, 1.0], descriptors
      `["spicy"]`, one alias), `fixture-spice-citrus.toml` (same category and dose, descriptors
      `["citrus"]`), `fixture-coffee-beans.toml` and `fixture-coffee-cold-brew.toml` (coffee, two
      forms, own dose, time, usages), `fixture-no-dose.toml` (herb, no dose), `fixture-fruit.toml`
      (fruit, `sugar_pct` with ref), `fixture-other.toml` (flavour `other`),
      `fixture-irish-moss.toml` (process, fining, boil), `fixture-enzyme.toml` (process,
      enzyme), `fixture-vanilla-extract.toml` (vanilla, `dose_ml_per_l`).
- [ ] Tests in `tests/test_extra_ingredients.py`: misc fixtures pass `check_files`; each
      template filled from a fixture passes and the empty template is refused (extend
      `test_template_filled_from_fixture_passes`); new `REFUSALS` rows: missing `purpose`,
      missing `usages`, flavour without descriptors, process with descriptors, category not of
      its purpose, unknown usage, both doses filled, `sugar_pct` on a non-fruit, `dose_g_per_l`
      without its ref; `test_misc_waits_reasons` (the three reasons, and none for
      `fixture-spice`). Update s8's fixture counts (`len(ingredients) == 4` and the like).
- [ ] Run `pytest -m "not stack" tests/test_extra_ingredients.py`, expect pass.
Done when: `python -m loaders.extra_ingredients --check tests/fixtures/ingredients` prints ok
plus the three waits lines, and a refused file names file and field.
Commit: `Check misc intake files`

### Task 4: misc files load, tag and report
Why: R2, R3, R13, R14, R15; A2, A3, A13, A14, A15.
- [ ] `load_misc(conn, item)`: `ref.ingredient` (kind `misc`) and the `ref.misc` row through
      `write_ingredient` (every column written, so a cleared field becomes NULL), aliases as s8.
      `load` loads misc after yeast and **skips** a file whose `misc_waits` is the liquid-extract
      reason (its aliases are not stored or checked). `sugar_pct` stays in `raw.intake` only.
- [ ] `loaders/style_fit_vocab.toml`: 9 family tags named after the flavour categories
      (`spice`, `herb`, `fruit`, `wood`, `coffee`, `cacao`, `vanilla`, `smoke`, `other`).
      Family and character tags may share a name (`ref.tag` is unique per facet); `app.style_level`
      never reads a misc's tags (Task 6), so no clash.
- [ ] `loaders/tags.py` misc branch: for each `ref.misc` row, flavour → family tag = category,
      character tags from `descriptors` through `resolve_intake` (unknown words to
      `ingredient_review`, as s8); process → nothing saved, no review row. Docstring updated.
- [ ] `summary` / `print_summary`: `loaded` counts misc; a process aid is neither tagged nor
      flagged (no "no tags derived"); `waits_for_maths` lists the enzyme/acid and fruit-sugar
      lines with their reasons; a new `waits` list names skipped liquid extracts; `--check`'s ok
      line counts misc.
- [ ] `db/checks/ref_spotcheck.sql`: `misc` moves to the `intake` group; a section "Intake misc
      rows" with purpose, category, usages, time_min, dose_g_per_l, source and file.
- [ ] Tests (stack, `rw` rolled back): misc fixtures load, a second load gives the same rows
      (extend `test_load_twice_same_rows` and `intake_snapshot` with `ref.misc`); every filled
      column has a `field_source` entry; `fixture-no-dose` has `dose_g_per_l` NULL (A15);
      the two coffee forms are two rows with their own dose and time (A14); the vanilla extract
      is not in `ref.ingredient` and is in the summary's `waits` (A14); the fruit loads and is in
      `waits_for_maths` with "decided with M6" (A13); in `tests/test_tags.py`
      `test_misc_tags`: `fixture-spice` has family `spice` and character `spicy`, Irish moss
      has no tag and no `ingredient_review` row, and is not in `flagged` (A3).
- [ ] Run `pytest tests/test_extra_ingredients.py tests/test_tags.py`; run
      `docker exec -i supabase-db psql -U postgres -d postgres < db/checks/ref_spotcheck.sql`,
      expect the misc lines (0 rows on the live database).
Done when: the tests pass and the live `ref.misc` still has 0 rows.
Commit: `Load and tag misc intake files`

### Task 5: misc kind words find misc products
Why: R4, A4.
- [ ] `db/036_ingredient_resolver.sql` `app.ingredient_kind_word()`: add `('spice','misc')`,
      `('herb','misc')`, `('fruit','misc')`. Not `wood` (measured: "Smoked Malt (cherry wood)"
      and "(pear wood)" would be read as misc, because the first kind word wins), not `smoke`
      (brewers type it for smoked malt), not `coffee`, `cacao`, `vanilla` (product words). Decided by
      you, 2026-10-18: these three only.
- [ ] Tests in `tests/test_misc.py` (fixtures loaded, rolled back): `app.resolve_ingredient`
      finds `fixture-spice` by its name and by its alias, finds `fixture-no-dose` by its kind
      word plus name ("herb fixture no dose"), and a kind word with another kind's name
      ("spice fixture hop") finds nothing; in `tests/test_ingredient_resolver.py`, every b01–b22 wanted word still resolves to
      the same products, and "smoked malt cherry wood" still finds only the fermentable.
- [ ] Apply `db/036` twice; run `pytest tests/test_ingredient_resolver.py tests/test_misc.py tests/test_extra_ingredients.py`.
Done when: A4 holds and the resolver tests pass unchanged.
Commit: `Add misc kind words to the resolver`

### Task 6: `app.style_level` rates a flavour misc and a process aid
Why: R5, R6, R15; A5, A6, A15. Needs Task 1 accepted (M1–M3).
- [ ] `db/033_style_fit_effects.sql`: 8 rows in `app.usage_effects()`, `kind = 'misc'`,
      `applies_to` = the category, `usage` null, `carries_character` false:
      spice, herb, coffee, cacao, vanilla → `spice`; fruit → `fruit`; wood → `wood`; smoke → `smoke`.
      `app.style_fit_cut_points()` gains `misc_dose`: `{"subtle_below": {"id": "M1", "ratio": …,
      "basis": …}, "aggressive_above": {"id": "M2", "ratio": …, "basis": …}, "levels": {"id": "M3",
      "subtle": …, "noticeable": …, "aggressive": …, "basis": …}}`, values and bases from
      `doc-calc.md` §D.
- [ ] `db/034_style_level.sql` `app.style_level`: accept `ing.kind = 'misc'` with a usage in
      the row's `usages` (else raise "usage % is not a usage of %"); the misc branch of the
      Approach, steps 1–7, before section "2. adjunct or sugar". A process aid returns before
      the "rated at all?" check. The because names the dimension, the intensity word, the dose
      and the sourced range ("3.0 g/L against the sourced 3.0–3.0 g/L"), and quotes the envelope
      row where one is used.
- [ ] Tests in `tests/test_misc.py` (fixtures loaded, rolled back; 25B is the reviewed envelope
      with a `spice` row, measured): for each usage of `fixture-spice`, a level and a because in
      25B; doses below, inside and above the sourced range give subtle, noticeable, aggressive,
      and the because names M1/M2's basis; `fixture-spice` and `fixture-spice-citrus` at the same
      dose get the same level (A5); inside the range it is `allowed` in 25B (spice min none) and
      `typical` once a rolled-back test sets 25B's spice `min_level` to 1; 18B (no `spice` row) gives `out_of_style` "specialty spice";
      Irish moss and the enzyme are `allowed` "no flavour effect" in every style with a reviewed
      envelope and in a style with none (A6); `fixture-no-dose` with a `g_per_l` says "no sourced dose"
      (A15); `fixture-other` gives level null "no added-character dimension"; a usage not in the
      row raises; `tests/test_style_fit_effects.py` keeps passing (misc dimensions exist).
- [ ] Apply `db/033`, `db/034` twice; run `pytest tests/test_misc.py tests/test_style_level.py tests/test_style_fit_effects.py tests/test_style_fit_golden.py tests/test_style_fit_recipe.py`, expect pass (the golden results for hops, malts and yeasts unchanged).
Done when: A5, A6 and the style-level part of A15 hold, and the existing style-fit tests pass.
Commit: `Rate flavour misc and process aids in style_level`

### Task 7: step 3 rates misc words; the recipe check takes extras
Why: R7, R9; A7 (SQL level), A9.
- [ ] `db/037_step3.sql` `app.ingredient_choices`: for a misc, one choice per entry of its
      `usages`, dose `'{}'`, label = the usage (e.g. "secondary"), in the order of `MISC_USAGES`.
- [ ] `db/034_style_level.sql`: `drop function if exists app.style_fit_recipe(jsonb)`, then
      `app.style_fit_recipe(recipe jsonb, extras jsonb default '[]')`. `extras` is
      `[{ingredient_id, usage, g}]` (`g` optional); each line goes through `app.style_level`
      with `g_per_l = g / batch volume`, and is added to `lines` as
      `{kind: 'misc', ingredient_id, name, usage, level, because}`. A one-argument call works as
      before. Check first that nothing in `n8n/workflows/` calls `style_fit_recipe` (none did,
      2026-10-18).
- [ ] Tests in `tests/test_misc.py`: `app.rate_wanted('25B', 'fixture spice', 'background')`
      gives a level, not null; in 18B it is `out_of_style` and `app.step3_deviations` lists it as
      an ingredient deviation from "18B … ingredients"; Irish moss in a brief gives no deviation;
      `app.style_fit_recipe` on reference recipe b16 with extras = one `fixture-spice` (g given)
      and one Irish moss returns a line for each (A9), and the other lines equal the one-argument
      call.
- [ ] Apply `db/037`, `db/034` twice; run `pytest tests/test_misc.py tests/test_step3.py tests/test_style_fit_recipe.py`.
Done when: A9 holds and step 3's b01–b22 outputs are unchanged (`test_step3.py` passes).
Commit: `Rate misc in step 3 and in style_fit_recipe`

### Task 8: a featured misc moves step 2 to its specialty style
Why: R8, A8 (SQL level). Needs Task 1 accepted (§A, §B).
- [ ] `db/022_step2.sql`: `drop function if exists app.specialty_style()` and recreate it as
      `(adjunct text, category text, guide text, code text, source text)`: the 3 honey/molasses
      rows keep `adjunct` (category null); one BJCP row per mapped flavour category (fruit 29A;
      spice, herb, coffee, cacao, vanilla 30A; wood 33A; smoke 32A) and one BA row per category
      from `doc-calc.md` §B, `adjunct` null, `source` = the quote or "set by the user, <date>".
      No row for `other`.
- [ ] Section 7 of `app.step2_best_style`: keep the adjunct word match; when it finds nothing,
      take the first `feature` item (in brief order) whose first misc product (resolver order)
      has a category row for `base.guide`; style = that code, `alt_styles` = base first, as for
      honey; reason: "Picked 30A …: coffee (Fixture Coffee Beans, category coffee) has the role
      "feature" in step 1's brief; base style 20B."
- [ ] Tests: `tests/test_step2_signals.py::test_every_alias_has_a_source` reads the new columns
      (every row has a source and an existing code; each row has exactly one of adjunct or
      category); in `tests/test_misc.py`: a brief "an American stout" with
      `wanted = [{item: "fixture coffee beans", role: "feature"}]` gives 30A with 20B first in
      `alt_styles`; the same item as `background` keeps 20B; a `feature` `fixture-other` keeps
      the base; b12 (honey) still gives 31B (`tests/test_step2_pick.py` passes).
- [ ] Apply `db/022` twice; run `pytest tests/test_misc.py tests/test_step2_pick.py tests/test_step2_signals.py tests/test_step3.py`.
Done when: the featured misc test passes and step 2's b01–b22 picks are unchanged.
Commit: `Pick the specialty style by misc category in step 2`

### Task 9: a misc product in a step 5 slot carries its misc fields
Why: R12, R15; A12, A15 (step 5 part).
- [ ] `db/041_step5.sql`: `app.step5_refs` and `app.step5_refs_of_id` add `misc` to every ref:
      null when the product is not misc; else `{purpose, category, usages, time_min,
      dose_g_per_l: {low_g_per_l, high_g_per_l} | null, because}`. `because` is "sourced dose from
      <slug> <ref>" or "no sourced dose".
- [ ] `shared/contracts/step5.output.schema.json`: the ref object (in `slots`, `excluded`,
      `inventory`) gets required `misc`: null or an object with those keys
      (`additionalProperties: false`, usages enum of the 6 usages, purpose enum).
- [ ] `tests/test_step5.py`: `ALLOWED_NUMBERS` gains `time_min`, `low_g_per_l`,
      `high_g_per_l` (sourced row figures, not ratio numbers; R10 of m4 is about recipe
      ratios). In `tests/test_misc.py`: a frame with `fixture-coffee-beans` wanted has its
      `misc` fields equal to the row, `fixture-no-dose` says "no sourced dose", and both frames
      meet `step5.output` (A12, A15).
- [ ] Apply `db/041` twice; run `pytest tests/test_step5.py tests/test_misc.py tests/test_workflows.py tests/test_contracts.py`.
Done when: A12 holds on fixtures and the 22 frames still meet the contract.
Commit: `Carry misc fields in the step 5 slot`

### Task 10: 30A has a reviewed envelope (review point)
Why: B4, D9; R5 and R10 need 30A's `spice` row for the coffee-vanilla brief.
- [ ] Add `"30A"` to `S3_STYLES` in `loaders/style_envelopes.py` (comment: the specialty style
      of b23) and update `tests/test_style_envelopes.py::test_s3_styles_are_the_26` to the new
      set and count (27 styles; briefs counted after Task 12, so write the expected set out).
- [ ] Extract offline with the D2 model: `.venv/bin/python -m loaders.style_envelopes --extract <scratchpad>/30A.toml --style 30A`
      (Ollama on the host, `NUM_CTX` as set). Paste the draft style into
      `loaders/style_envelopes.toml` with `reviewed = false`.
- [ ] Stop and report `needs-approval`. **Review point (you):** review the 30A rows (the `spice`
      min and max from "subtle to aggressive", and which other rows to keep, since 30A's other
      sensations "vary by base style"), edit as you decide, set `reviewed = true`.
- [ ] Load: `.venv/bin/python -m loaders.style_envelopes`, twice; the counts in
      `ref.style_sensory` are equal after both runs. Run `pytest tests/test_style_envelopes.py tests/test_style_fit_golden.py`.
Done when: 30A is reviewed and loaded, and the envelope tests pass.
Commit: `Add the reviewed 30A envelope`

### Task 11: the coffee, vanilla and orange peel entries are in `ref`
Why: R11, R14, A11. Needs Task 1 accepted (§E) and Tasks 3–4.
- [ ] Write the files of `doc-calc.md` §E in `shared/ingredients/misc/` from
      `misc-flavour.toml`, every figure exactly as accepted, sources `janish-coffee-beers` and
      `palmer-how-to-brew` (both already in `ref.source`, measured). A descriptor word that is
      not a tag yet is added to `loaders/style_fit_vocab.toml` first (one line).
- [ ] `.venv/bin/python -m loaders.extra_ingredients --check`, then without `--check`; paste the
      summary into the PROJECT.md line.
- [ ] Test `tests/test_misc.py::test_live_misc_entries` (stack, read only): each accepted file
      has its `ref.misc` row with every filled figure in `field_source`; the live `ref.misc` has
      no `purpose = 'process'` row (A11); "coffee", "vanilla" and "orange peel" each resolve to
      their entries only.
- [ ] Run `pytest tests/test_misc.py tests/test_extra_ingredients.py tests/test_tags.py tests/test_fermentable_facts.py`.
Done when: A11 holds on the live database.
Commit: `Add coffee, vanilla and orange peel misc entries`

### Task 12: two test briefs with extras (review point)
Why: B4, R10; A7, A8, A12 at SQL level.
- [ ] **Review point (you), before writing them:** approve or change these two briefs.
  - `b23`: request "An American stout with the coffee up front and a little vanilla in the
    background."; named "American stout"; style `30A`; alt_styles `["20B"]`; deviations `[]`;
    wanted `[{coffee, feature}, {vanilla, background}]`; why "A featured coffee moves the style to
    30A on a 20B base; vanilla is a background spice inside 30A."; needs fermentables
    `["pale ale malt", "roasted barley", "chocolate malt"]`, hops `["Cascade"]`, yeast
    `["American ale yeast"]`, misc `["coffee", "vanilla beans"]`.
  - `b24`: request "An American pale ale with a little orange peel for a hint of citrus.";
    named "American pale ale"; style `18B`; deviations `[{ingredient, "orange peel", "18B
    ingredients"}]`; wanted `[{orange peel, background}]`; why "A background extra keeps the base
    style; 18B is silent on spice, so the peel is a deviation."; needs fermentables
    `["pale ale malt", "crystal malt"]`, hops `["Cascade", "Centennial"]`, yeast
    `["American ale yeast"]`, misc `["orange peel"]`.
- [ ] Add them to `evals/recipe_briefs.toml` (file header: 24 briefs, `needs.misc`).
      `tests/test_recipe_briefs.py`: 24 briefs, `NEEDS_KEYS` gains `misc`, docstring. `tests/test_reference_recipes.py`
      keeps one recipe per brief for b01–b22 and its docstring says why (decided by you,
      2026-10-18): b23/b24 recipes come with M6, when `app.check_recipe` takes extras (Later TODO,
      Task 14). `tests/test_step3.py`
      `ALL_IDS` and `tests/test_step4.py` / `test_step5.py` (they iterate all briefs) run on 24.
- [ ] SQL-level checks (step 1's expected brief through steps 2–5, as `tests/test_step5.py::test_briefs_reach_the_bar` does):
      b23 step 2 gives 30A with 20B first; step 3 rates coffee and vanilla, none unrated (A7) and
      no deviation; step 4 uses 20B's ranges (`from base_style`); step 5's coffee slot has
      `misc` filled (A12). b24 keeps 18B and lists "orange peel" as an ingredient deviation (A8).
      Grade with `evals.grade`.
- [ ] Run `pytest -m "not stack"` and `pytest tests/test_recipe_briefs.py tests/test_step3.py tests/test_step4.py tests/test_step5.py tests/test_reference_recipes.py tests/test_style_envelopes.py tests/test_prompt.py`.
Done when: both briefs pass steps 2–5 at SQL level and the brief tests pass.
Commit: `Add test briefs b23 and b24 with extras`

### Task 13: steps 1–5 are measured on all 24 briefs
Why: R10, A10 (PROJECT.md §6.6).
- [ ] `.venv/bin/python -m evals.run --save --label s9` (D2 model, the live pipeline; no
      workflow change is needed, the step functions keep their signatures; confirm with
      `grep -l` on `n8n/workflows/`).
- [ ] Expect b23 and b24 to pass steps 1–5, and steps 1–5 each 22/22 on b01–b22. A miss is
      recorded with its step and output, and reported before any change (a step 1 prompt
      change is outside this brief and needs your answer).
Done when: `evals/results/2026-10-<dd>-s9.json` is saved with A10 met, or the misses are reported.
Commit: `Measure steps 1-5 on 24 briefs (s9)`

### Task 14: the docs describe misc as built
Why: brief Scope (docs), R13 (TODO).
- [ ] `docs/DATABASE.md`: the `ref.misc` row (columns, categories, usages, `field_source`),
      fill order (misc through intake), spot-check section.
- [ ] `docs/STYLE-FIT.md` §2 (misc row: category → family tag, descriptors → character tags,
      process aids none), §3 (the 8 misc rows, `carries_character` false), §4 (dose against the
      row's sourced dose, M1–M3), and a short "three layers" paragraph (category → step 2,
      one dimension scored, tags never scored).
- [ ] `docs/RECIPE-ROADMAP.md`: step 9 reads `ref.misc` usages and sourced doses (no "corpus
      misc usage stats"); Later list: "TODO: fruit as a fermentable is decided with M6 (s9,
      decision 2)" and "TODO: reference recipes for b23 and b24 with M6, when `app.check_recipe`
      takes extras (s9)".
- [ ] `docs/WORKFLOW-ROADMAP.md`: rows for s8 (shipped), s9 and s10 in the path table, and
      their node in the diagram.
- [ ] `docs/INGREDIENT-INTAKE.md` §12: Q2, Q3, Q5 move to Made with their one-line why; §11
      rows marked done in s9; §13 checklist names the misc templates.
- [ ] `shared/ingredients/README.md`: adding a misc (both templates, waits lines).
Done when: each doc names what was built and links the work folder.
Commit: `Document misc extras (s9)`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| A category that does not fit the purpose, or an unknown usage, cannot be stored | `tests/test_misc.py::test_misc_columns_and_checks` | 2 |
| A misc file missing a field for its purpose is refused, naming file and field | `tests/test_extra_ingredients.py::test_refusal` (misc rows) | 3 |
| A liquid extract is not loaded; enzyme, acid and fruit sugar load and are marked waiting | `test_misc_waits_reasons`, load tests | 3, 4 |
| Re-loading misc gives the same rows; a cleared dose becomes NULL | `test_load_twice_same_rows`, `test_reload_after_editing_files` (misc) | 4 |
| A process aid gets no tags and no review row | `tests/test_tags.py::test_misc_tags` | 4 |
| A misc kind word finds only misc; smoked malts still resolve as malt | `tests/test_ingredient_resolver.py`, `tests/test_misc.py` | 5 |
| Character tags never change a misc's level | `tests/test_misc.py` (two spice fixtures, same dose) | 6 |
| A process aid is `allowed` in every style; `other` is not rated; no dose says so | `tests/test_misc.py` | 6 |
| Existing hop, malt and yeast levels are unchanged | `tests/test_style_fit_golden.py`, `test_style_level.py` | 6 |
| A background or `other` misc keeps the base style; a featured one moves to its specialty style with the base first | `tests/test_misc.py`, `tests/test_step2_pick.py` | 8 |
| Step 5's misc fields equal the row and meet the contract | `tests/test_misc.py`, `tests/test_step5.py` | 9 |
| Steps 1–5 stay at 22/22 on b01–b22 and pass b23, b24 | `python -m evals.run`, `tests/test_step5.py::test_briefs_reach_the_bar` | 12, 13 |

## Approved exceptions

None.

## Deviations
- 2026-10-18 · Approach (style fit step 6), Task 1 §D, Task 6: a misc dose is read against each
  entry's own sourced dose, with M1–M3 set in Task 1, not fixed g/L cut points per dimension. — your answer to plan question 1.
- 2026-10-18 · Task 12, Task 14: the one-reference-recipe-per-brief test stays on b01–b22; a
  RECIPE-ROADMAP Later TODO adds b23/b24 recipes with M6. — your answer to plan question 2.
- 2026-10-18 · Task 5: the misc kind words are `spice`, `herb` and `fruit` only. — your answer to
  plan question 3.
- 2026-10-18 · Approach (style fit step 7), Task 6: a flavour misc within the envelope's range is
  `typical` when the envelope's `min_level` is at least 1, else `allowed`. — your answer to plan
  question 4.
