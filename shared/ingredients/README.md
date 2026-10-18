# Adding an ingredient by hand (fermentable, hop, yeast, misc)

One TOML file per ingredient, one per new source. No code, no LLM. The checks live in
[`loaders/extra_ingredients.py`](../../loaders/extra_ingredients.py); the design is in
[`docs/INGREDIENT-INTAKE.md`](../../docs/INGREDIENT-INTAKE.md).

## Folders

| Folder | Holds |
|---|---|
| `_templates/` | commented templates to copy: `fermentable.toml`, `hop.toml`, `yeast.toml`, `misc-flavour.toml`, `misc-process.toml`, `source.toml` |
| `fermentable/`, `hop/`, `yeast/` | one file per ingredient (empty today: no real item has been added yet) |
| `misc/` | one file per form of a spice, herb, fruit, coffee, vanilla, wood, smoke, or a process aid (4 today: coffee whole beans, coffee cold brew, vanilla bean, orange peel) |
| `sources/` | one file per source that is not already in `ref.source` |

## Adding a misc

A misc is an added product with no gravity data. Use `_templates/misc-flavour.toml` for a spice,
herb, fruit, wood, coffee, cacao, vanilla, smoke or other flavour, and
`_templates/misc-process.toml` for a fining, nutrient, enzyme, acid or other process aid. Copy it
to `misc/<name>.toml`. The same steps below apply; these points are specific to misc:

- **One file per form** of a product (coffee whole beans and coffee cold brew are two files), because
  each form has its own usage, dose and time.
- A flavour misc needs `descriptors` (they become its character tags); a process aid must leave
  them empty and gets no tags and no style rating.
- `usages` are any of `mash`, `boil`, `whirlpool`, `ferment`, `secondary`, `packaging`. `dose_g_per_l`
  is `[low, high]` in grams per litre of finished beer. Leave the dose empty when no source gives
  one: the recipe then says "no sourced dose", and the style fit does not check its intensity.
  A flavour misc is rated against its own sourced dose ([`docs/STYLE-FIT.md`](../../docs/STYLE-FIT.md) §4).
- **Waits lines.** `--check` and the load report "waits" for three cases. A liquid extract dosed in
  mL (`dose_ml_per_l`) passes `--check` but is **not loaded**. An `enzyme` or an `acid` (changes the
  numbers) and a fruit with a `sugar_pct` (fruit as a fermentable is decided with M6) are loaded and
  listed as "waits for maths". None of them enters OG, IBU or SRM.
- The category sets the specialty style step 2 picks when the misc is a featured extra (for example
  coffee, vanilla and spice → 30A), so a new file needs no change elsewhere.


## Steps

1. Find a source that states the figures. Nothing is guessed: leave a key empty (`""` or `[]`)
   when the source does not say, and every filled figure needs its `<field>_ref` (page or URL).
2. Copy `_templates/<kind>.toml` to `<kind>/<name>.toml` and fill it. Ranges are `[low, high]`
   (one value: `[x, x]`). Units: %, EBC, °C, mL/100 g, minutes. A source not in `ref.source`:
   copy `_templates/source.toml` to `sources/<slug>.toml` (the file name is the slug).
3. Descriptor words must be a tag name or a synonym in
   [`loaders/style_fit_vocab.toml`](../../loaders/style_fit_vocab.toml); to use a new word, add it there first.
4. Check, which prints every problem as `<file>: <field>: <problem>` and writes nothing:

   ```
   .venv/bin/python -m loaders.extra_ingredients --check
   ```

5. Load. This one command writes sources, ingredients and aliases, re-runs the tagger and
   prints the report (rows loaded, tagged or flagged for review, aliases checked, rows that wait
   for the brewing maths). Any failure rolls the whole run back.

   ```
   .venv/bin/python -m loaders.extra_ingredients
   ```

6. Run `.venv/bin/pytest`, then commit the file(s) and update the counts in `PROJECT.md` and
   `docs/DATABASE.md` from the report (the spot-check, `db/checks/ref_spotcheck.sql`, lists the misc rows).

Never point the load command at `tests/fixtures/ingredients/`: those files are test data and
would be committed into the live `ref` schema. The tests load them only inside a rolled-back transaction.
