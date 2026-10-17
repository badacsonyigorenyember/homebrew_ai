# Adding an ingredient by hand (fermentable, hop, yeast)

One TOML file per ingredient, one per new source. No code, no LLM. The checks live in
[`loaders/extra_ingredients.py`](../../loaders/extra_ingredients.py); the design is in
[`docs/INGREDIENT-INTAKE.md`](../../docs/INGREDIENT-INTAKE.md).

## Folders

| Folder | Holds |
|---|---|
| `_templates/` | commented templates to copy: `fermentable.toml`, `hop.toml`, `yeast.toml`, `source.toml` |
| `fermentable/`, `hop/`, `yeast/` | one file per ingredient (empty today: no real item has been added yet) |
| `sources/` | one file per source that is not already in `ref.source` |

`misc` (adjunct non-fermentables, water additions) is not supported yet.

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
   `docs/DATABASE.md` from the report.

Never point the load command at `tests/fixtures/ingredients/`: those files are test data and
would be committed into the live `ref` schema. The tests load them only inside a rolled-back transaction.
