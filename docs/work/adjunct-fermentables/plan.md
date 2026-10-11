# Adjunct fermentables — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: adjunct-fermentables

## Approach

The branch was rebased onto `main` on 2026-10-11 (user decision; the brief commit is now
`3168c4e`). So the 20 approved briefs (`evals/recipe_briefs.toml`, merged in `8c7c6ba`) and the
current PROJECT.md are on the branch. `pytest` gives 61 passed there.

The adjuncts load like the malts, with an explicit, hand-checked map and a loader:

- `loaders/fetch_hopline.py --adjuncts` fetches hopline's three adjunct listings (flakes,
  fermentable sugars, non-fermentable sugars: 14 products, measured 2026-10-11). It stores each
  page's visible text, because these pages have no `EBC:`/`Kihozatal:` spec line to parse.
- `loaders/adjunct_products.py` holds the explicit data:
  - `PALMER`: the rows of Palmer's Tables 18.5 and 24.1 this work uses, as printed.
  - `PRODUCTS`: hopline SKU → ingredient name + Palmer row + the few figures hopline prints.
    Each of those figures is stored with the page's own words.
  - `PACK_SIZES`, `SKIPPED`, and `PALMER_ONLY` (honey: hopline sells none).
- `loaders/adjuncts.py` merges the two sources. Hopline wins, Palmer fills the gaps, and
  `field_source` names the source of each field. `build` refuses an unmapped SKU, and a hopline
  figure whose quoted words are not on the fetched page.
- A new column `ref.fermentable.fermentability` (`full` | `normal` | `none`) defaults to
  `normal`. The 74 malts get `normal` from the default without being reloaded.
- PPG from Table 24.1 becomes extract % as `PPG / 46 × 100`, rounded to 0.1. 46 PPG is the
  sucrose reference Palmer gives in the table's note, so 46 → 100.0 and 38 → 82.6. This is a
  unit conversion, tested in code.

Decided here, as the brief asked:

- **Candi sugar uses Palmer's "Table sugar" row** (46 PPG, 100 %), not "Belgian candi syrup"
  (32 PPG, ~50–80 %). Hopline sells crystals (kandiscukor, i.e. sucrose), not syrup. The
  syrup row's yield includes water, and its range doesn't fit one category. A4 already expects
  `full`. The colour, 225 EBC, comes from hopline's page.
- **Fermentability `normal` needs no source.** It means "follows the yeast's attenuation", the
  same as every malt. Only `full` and `none` are stated by a source and get a `field_source`
  entry:
  - lactose `none`: hopline's page says "nem erjeszthető" (non-fermentable). Palmer's comment
    agrees and is kept in `raw`.
  - honey `full`: Palmer, 95 %.
  - candi sugar `full`: Palmer's table sugar row, 100 %.
- **The test-brief gap that this work adds is flaked barley** (b05). Hopline sells it (SKU
  `400110`) and Palmer's Table 18.5 prints it (70 %). Every other brief ingredient is already
  in `ref` or is left out with a reason (Task 5). Lactobacillus (b14) is left out (user
  decision, 2026-10-11): it is a bacterium for `ref.yeast`, and adding it means extending the
  yeast loader, which is separate work.

Measured while planning (2026-10-11):

- Palmer is the **Fourth edition 2017**, Brewers Publications (copyright page). Table 18.5 is
  on book p. 289 (PDF p. 315), Table 24.1 on book p. 436 (PDF p. 462).
- What the hopline pages print:
  - oat, corn and barley flakes: no figures.
  - rice flakes: "akár 40%-ban" (up to 40 %).
  - brown candi: "Szín: 225 EBC".
  - lactose: "nem erjeszthető".
- `ref.misc` is empty. Its check is named `misc_category_check`.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/010_ref_schema.sql` | changed | `fermentability` column on `ref.fermentable` |
| `db/011_ref_sources.sql` | changed | sources `palmer-how-to-brew` and `hopline-adjuncts` |
| `db/012_style_fit.sql` | changed | `ref.misc` category check without `lactose` |
| `loaders/fetch_hopline.py` | changed | `--adjuncts` mode, `page_text` |
| `loaders/adjunct_products.py` | new | the explicit Palmer rows and hopline SKU map |
| `loaders/adjuncts.py` | new | `extract_pct_from_ppg`, `build`, `load`, CLI |
| `tests/test_fetch_hopline.py` | changed | test for `page_text` |
| `tests/test_adjuncts.py` | new | tests for the loader |
| `docs/DATABASE.md` | changed | fermentability, where lactose and honey live, counts (R5) |
| `docs/STYLE-FIT.md` | changed | §1 misc row: drop the `lactose → sweetness` example (follows from R5) |
| `docs/work/adjunct-fermentables/report.md` | new | gap report (R6), and the NULLs with reasons (A3) |
| `PROJECT.md` | changed | §4, §5 status, §8 entries |
| `shared/rag-files/pending/hopline_adjuncts.json` | new, not committed (gitignored, like the other fetched files) | fetched pages |

## Tasks

### Task 1: `ref` can store fermentability, and lactose is no longer a misc category
Why: R4, R5, R7 (Palmer source row).
- [x] `db/010_ref_schema.sql`: append, with a comment saying the 74 malts take the default:
      `alter table ref.fermentable add column if not exists fermentability text not null default 'normal' check (fermentability in ('full', 'normal', 'none'));`
- [x] `db/012_style_fit.sql`: remove `'lactose'` from the `create table ref.misc` check list.
      Then add an idempotent block that brings an existing table up to date:
      `alter table ref.misc drop constraint if exists misc_category_check, add constraint misc_category_check check (category in ('spice', 'herb', 'fruit', 'wood', 'coffee', 'cacao', 'vanilla', 'smoke', 'fining', 'other'));`
- [x] `db/011_ref_sources.sql`: add to the insert list
      `('palmer-how-to-brew', 'How to Brew', 'Fourth edition 2017', 'Brewers Publications', null, null, 'Table 18.5 (p. 289) and Table 24.1 (p. 436) only; file shared/rag-files/pending/how_to_brew.pdf')`.
- [x] Apply in this order, each as `postgres` (OPERATIONS.md §4):
      `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/010_ref_schema.sql`,
      then `011_ref_sources.sql`, then `012_style_fit.sql`. Run all three a second time: no
      error (idempotent).
- [x] Check:
      `select fermentability, count(*) from ref.fermentable group by 1;` → `normal | 74`.
      `select pg_get_constraintdef(oid) from pg_constraint where conname = 'misc_category_check';`
      → no `lactose`.
      `select count(*) from ref.source;` → 17.
- [x] `docs/DATABASE.md` (R5):
  - mermaid `fermentable`: add `text fermentability "full|normal|none"`.
  - table row `fermentable`: name the column.
  - table row `misc`: category list without lactose.
  - "Rules for `ref`": replace the extras rule with two rules.
    1. Anything with gravity (malts, flakes, sugars, lactose, honey) is a `fermentable` and enters
       OG through its extract. Its `fermentability` says how much of that extract yeast can
       ferment: `full` all of it, `normal` follows the yeast's attenuation (grain malts and
       flakes, the default, needs no source), `none` none of it (lactose stays whole in FG).
       `full` and `none` must be stated by a source and recorded in `field_source`.
    2. Extras without gravity data (cinnamon, vanilla) are `misc` and never enter the
       OG/IBU/SRM maths.
- [x] `docs/STYLE-FIT.md` line 55: drop `*lactose → sweetness*` from the misc example list.
      Lactose is a fermentable now. Its style fit comes through tags, like any fermentable's.
- [x] Run `.venv/bin/python -m pytest`, expect 61 passed (nothing reads the new column yet).
Done when: the three checks above return the stated results, and the 74 malts are unchanged
apart from the new column.
Commit: `Add fermentability column and Palmer source to ref`

### Task 2: hopline's adjunct pages are fetched
Why: R7 (hopline data from hopline's pages), R8.
- [x] `loaders/fetch_hopline.py`:
  - `ADJUNCT_LISTINGS = {"flakes": ".../alapanyagok/malatak/pelyhek-199", "fermentable sugars": ".../alapanyagok/cukrok-edesitoszerek-244/erjesztheto-250", "non-fermentable sugars": ".../alapanyagok/cukrok-edesitoszerek-244/nem-erjesztheto"}`
    (full `https://www.hopline.hu` URLs).
  - `page_text(html) -> str | None`: `visible_text(html)` from the first `"Főkategória"` up
    to the next `"Vélemények"`, stripped; `None` when either marker is missing.
  - `fetch_adjuncts(out)`: each listing through the existing `listing()` (paged, stops when a
    page adds no new SKU). Then each product page once, as
    `{"sku", "url", "name" (from NAME), "text": page_text(html)}`. Writes
    `{"fetched", "listings": ADJUNCT_LISTINGS, "categories": {listing: [sku, ...]}, "products": [...]}`.
  - A third option `--adjuncts` in the mutually exclusive group. Update the module docstring's
    Run lines.
  - Do not use `product_page` or `long_description` for these pages: `long_description` raises
    on the barley flake page (a table with 0 headers), and `product_page`'s spec is `None` on
    the candi and lactose pages.
- [x] Write test `tests/test_fetch_hopline.py::test_page_text_runs_from_main_category_to_reviews`:
      an inline HTML fixture with a `<script>`, a "Főkategória … Szín: 225 EBC …" block and a
      "Vélemények" footer. The text has the block, and neither the script nor the footer. A page
      without "Vélemények" gives `None`.
- [x] `db/011_ref_sources.sql`: add
      `('hopline-adjuncts', 'Hopline flake and sugar product pages', 'website, fetched <fetch date>', 'Hopline', null, 'https://www.hopline.hu/alapanyagok/malatak/pelyhek-199', 'Flakes (this URL) and the fermentable and non-fermentable sugar pages (https://www.hopline.hu/alapanyagok/cukrok-edesitoszerek-244/erjesztheto-250 and https://www.hopline.hu/alapanyagok/cukrok-edesitoszerek-244/nem-erjesztheto)')`.
      Use the date the fetch below runs. Apply it as in Task 1. `ref.source` → 18 rows.
- [x] Run `.venv/bin/python -m loaders.fetch_hopline --adjuncts shared/rag-files/pending/hopline_adjuncts.json`.
      Expect 14 products: flakes 9, fermentable sugars 3, non-fermentable sugars 2. Every
      product has a non-null `text`. A different count is fine if every SKU is then mapped in
      Task 3. A new product that is a fermentable this work's scope might cover is a question
      for the user, not a silent `SKIPPED` entry.
- [x] Run `.venv/bin/python -m pytest tests/test_fetch_hopline.py`, expect pass.
Done when: the JSON file exists with 14 products, all with text, and the test passes.
Commit: `Fetch hopline adjunct pages`

### Task 3: the adjunct loader builds sourced fermentables
Why: R1–R4, R7. A wrong extract or fermentability would corrupt every recipe's OG/FG.
- [ ] `loaders/adjunct_products.py`, module docstring in the style of `malt_products.py`.
  - `PALMER: dict[str, dict]` keyed by the row name as printed. Each entry has `table`,
    `page` and the printed values as strings, and for sugars the category next to the printed
    fermentability:
    - Table 18.5, p. 289 (`fgdb`): `"Oatmeal (flaked)"` 70 %, `"Corn (flaked)"` 84 %,
      `"Rice (flaked)"` 82 %, `"Barley (flaked)"` 70 %.
    - Table 24.1, p. 436 (`ppg`, `fermentability_printed`, `fermentability`, and `comment`
      where it states fermentability):
      - `"Table sugar"`: 46, "100%" → `full`.
      - `"Lactose"`: 46, "…" → `none`, comment "Lactose is an unfermentable sugar".
      - `"Honey"`: 38, "95%" → `full`.
  - `PRODUCTS: dict[str, tuple[str, str, dict]]`: SKU → (ingredient name, Palmer row, hopline
    figures). Each hopline figure is `field: (value, words copied from the fetched text)`.
    - `400150` Flaked Oats / Oatmeal (flaked) / {}
    - `400270` Flaked Corn / Corn (flaked) / {}
    - `400100` Flaked Rice / Rice (flaked) / `{"max_pct": ("40", <the "akár 40%-ban …" words>)}`
    - `400110` Flaked Barley / Barley (flaked) / {}
    - `400091-cs` Brown Candi Sugar / Table sugar / `{"ebc": ("225", "Szín: 225 EBC")}`
    - `400030-cs` Lactose / Lactose / `{"fermentability": ("none", <the "nem erjeszthető cukrok" words>)}`
  - `PACK_SIZES = {"400031-cs": "400030-cs"}` (lactose 1 kg). Its page goes into `raw` only.
  - `PALMER_ONLY = {"Honey": "Honey"}` (ingredient name → Palmer row): hopline sells no honey
    (R7, user decision 2026-10-11).
  - `SKIPPED`, with reasons from the brief's Out list:
    - rye flakes `400120`, wheat flakes `400130`, chit malt flakes `400290`, white candi
      `400081-cs`, fructose `400370`: other adjuncts, no test brief needs them.
    - rice hulls `400160`, `400161-cs`: process aid.
- [ ] `loaders/adjuncts.py`, module docstring saying what comes from where.
  - `HOPLINE = "hopline-adjuncts"`, `PALMER_SLUG = "palmer-how-to-brew"`.
  - `@dataclass Adjunct`: `name`, `source_slug`, `extract_dbfg_pct`, `ebc`, `max_pct`,
    `fermentability`, `field_source`, `raw`.
  - `extract_pct_from_ppg(ppg: Decimal) -> Decimal`: `ppg / 46 * 100`, quantized to `0.1`
    `ROUND_HALF_UP`. Docstring cites Table 24.1's note (sucrose = 46 PPG).
  - `make_adjunct(name, palmer_row, page=None, hopline_figures={}, extra_pages=[])`. Hopline
    first: `ebc` via `to_range(v, v)`, `max_pct` via `num`, `fermentability` as given. Then
    Palmer for each field still empty:
    - extract: `fgdb` as is, or `extract_pct_from_ppg(ppg)`.
    - fermentability: the Palmer category when not `normal`.
    - else `normal` with no `field_source` entry.
    Palmer gives no colour and no max %. `field_source` gets a key for every filled
    `extract_dbfg_pct`, `ebc`, `max_pct`, and for `fermentability` when it is not `normal`.
    `raw = {HOPLINE: page, PALMER_SLUG: palmer row}` (hopline part only when there is a page,
    plus pack pages under `"hopline-adjuncts pack sizes"`).
    `source_slug` is `HOPLINE` for a hopline product, `PALMER_SLUG` for honey.
    Ingredient `producer` is `""`: hopline does not name a maker.
  - `build(hopline: dict) -> list[Adjunct]`, in the style of `malts.build`.
    - Every product SKU must be in `PRODUCTS`, `PACK_SIZES` or `SKIPPED`, else `ValueError`
      naming the SKU and name.
    - For each hopline figure, its words must occur in the page's `text`, else `ValueError`.
      This catches a figure typed by hand that the page doesn't say.
    - Then append each `PALMER_ONLY` entry.
  - `load(conn, items) -> int`: `upsert_ingredient(conn, "fermentable", name, "", source_id(...), raw)`,
    then `insert into ref.fermentable (ingredient_id, extract_dbfg_pct, ebc, max_pct, fermentability, field_source) … on conflict (ingredient_id) do update set …`
    (all five columns). Same transaction pattern as `malts.load`.
  - `main()`: `--hopline PATH`, prints `loaded: N adjuncts` and
    `skipped: N hopline products (see SKIPPED in loaders/adjunct_products.py)`.
- [ ] Write tests in `tests/test_adjuncts.py`. Inline fixture: a hopline dict with the 14 SKUs,
      each `text` shortened but holding the quoted words.
  - `test_extract_pct_from_ppg`: 46 → `Decimal("100.0")`, 38 → `Decimal("82.6")`. Pins the
    conversion and its rounding.
  - `test_build_values_per_adjunct`: the 7 items and their values.
    - Flakes: oats 70.0, corn 84.0, rice 82.0, barley 70.0; ebc None; `normal`; rice
      `max_pct` 40 from hopline.
    - Brown Candi Sugar: extract 100.0 from Palmer, ebc `[225,225]` from hopline, `full` from
      Palmer.
    - Lactose: extract 100.0 from Palmer, `none` from hopline.
    - Honey: extract 82.6, `full`, both from Palmer, `source_slug` palmer.
  - `test_every_filled_field_has_a_source`: for every built item, the `field_source` keys are
    exactly the filled fields (fermentability only when not `normal`). Protects R2.
  - `test_unmapped_sku_raises`: an extra SKU → `ValueError`.
  - `test_hopline_figure_not_on_page_raises`: rice page text without the "40%" words →
    `ValueError`.
  - `test_maps_do_not_overlap`: `PRODUCTS`, `PACK_SIZES`, `SKIPPED` keys are disjoint. Every
    Palmer row named in `PRODUCTS` and `PALMER_ONLY` exists in `PALMER`.
- [ ] Run `.venv/bin/python -m pytest tests/test_adjuncts.py`, expect pass. Then
      `.venv/bin/python -c "import json; from loaders.adjuncts import build; print(len(build(json.load(open('shared/rag-files/pending/hopline_adjuncts.json')))))"`
      → `7` against the real fetched file. This also proves every quoted wording is on the real
      pages.
Done when: the tests pass and `build` on the real file gives 7 items without error.
Commit: `Add adjunct fermentable loader with tests`

### Task 4: the adjuncts are in `ref`, and loading twice changes nothing
Why: R1–R4, R8; A1–A4, A8.
- [ ] Run `.venv/bin/python -m loaders.adjuncts --hopline shared/rag-files/pending/hopline_adjuncts.json`.
      Expect `loaded: 7 adjuncts`, `skipped: 7 hopline products`.
- [ ] Fingerprint query (new rows):
      `select count(*), md5(string_agg(i.name || i.raw::text || f::text, '|' order by i.name)) from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id join ref.source s on s.id = i.source_id where s.slug in ('hopline-adjuncts', 'palmer-how-to-brew');`
      Note the result, run the loader again, and run the query again: same count (7) and same
      md5 (A8).
- [ ] A1: the 7 names (Flaked Oats, Flaked Corn, Flaked Rice, Flaked Barley, Brown Candi Sugar,
      Lactose, Honey) each have an `ingredient` row of kind `fermentable` and a `fermentable`
      row.
- [ ] A2: `select count(*) from ref.ingredient where source_id is null;` → 0. And this returns
      0 rows:
      ```sql
      select i.name, v.k
        from ref.ingredient i
        join ref.fermentable f on f.ingredient_id = i.id
        join ref.source s on s.id = i.source_id
       cross join lateral (values ('extract_dbfg_pct', f.extract_dbfg_pct is not null),
                                  ('ebc', f.ebc is not null),
                                  ('max_pct', f.max_pct is not null),
                                  ('fermentability', f.fermentability <> 'normal')) v(k, filled)
       where s.slug in ('hopline-adjuncts', 'palmer-how-to-brew')
         and v.filled and not f.field_source ? v.k;
      ```
- [ ] A4: `select fermentability, count(*) from ref.fermentable group by 1;` → `normal` 78
      (74 malts + 4 flakes), `full` 2, `none` 1.
- [ ] `.venv/bin/python -m pytest` in full, expect all pass.
- [ ] `docs/DATABASE.md`:
  - table rows `source` 18, `ingredient` and `fermentable` with the measured counts.
  - "Filled from" for `fermentable`: add hopline flake and sugar pages + Palmer Tables
    18.5/24.1.
  - §7 fill-order row 2: the measured counts, and the "no sugars, adjuncts" gap replaced by
    what is now there.
- [ ] `PROJECT.md`:
  - §4 Database row: sources 18, the `ref.fermentable` count and the adjunct rows with their
    sources.
  - §4 Scripts row: `loaders/adjuncts.py`, `fetch_hopline --adjuncts`, test counts as
    measured.
  - §5: the Palmer row gets "🟡 doc→calc: only Table 18.5 (4 flake rows) and Table 24.1
    (3 sugar rows) loaded into `ref.fermentable` (adjunct-fermentables)". Add a hopline
    adjunct row in the style of the malt row.
  - §8: a dated entry with the measured numbers.
Done when: A1, A2, A4 and A8 hold as measured above, and the full suite passes.
Commit: `Load adjunct fermentables into ref`

### Task 5: the gap report covers every test-brief ingredient
Why: R6, A3, A6.
- [ ] Write `docs/work/adjunct-fermentables/report.md`. It has two parts.
  - Part 1, the gap table. One row per distinct ingredient named anywhere in
    `evals/recipe_briefs.toml` (`needs.*`, `wanted`, `excluded`, `inventory`), with columns:
    name · kind · briefs · status (`found` / `added` / `left out`) · `ref` id(s) · reason or
    note.
    - Found by querying `ref.ingredient` (name `ilike`, and for generic names the matching
      products, e.g. "crystal malt" → the Caramel/Crystal/Cara malts).
    - Name variants count as found, with a note: "Tettnang" → Tettnanger, "East Kent Goldings"
      → East Kent Golding.
    - Expected from planning, to confirm by query:
      - added: the 6 adjuncts and flaked barley.
      - left out: Special B (b10). Hopline sells no Special B (R7); the nearest in `ref` is
        Weyermann Special W, noted with its id.
      - left out: Lactobacillus (b14). Reason: it is a bacterium, so it would go in
        `ref.yeast`. Hopline sells cultures (LP-582, LP-652, Helveticus Pitch), but adding them
        means extending the yeast loader, which is separate work (user decision, 2026-10-11).
      - everything else found.
  - Part 2, NULLs (A3). Every `NULL` extract, colour or max % of the 7 new rows, with the
    reason:
    - flakes' colour: neither hopline nor Table 18.5 prints one.
    - lactose's and honey's colour: Table 24.1 has no colour column, and the lactose page
      prints none.
    - max %: no source states one (rice: 40 % from hopline).
    - honey's NHB percentages (Palmer p. 437) are flavour bands, not a grist maximum.
- [ ] Check coverage with a one-off command (not a permanent test: the folder moves to
      `docs/finished/` on ship):
      ```bash
      .venv/bin/python -c "
      import tomllib, re
      briefs = tomllib.load(open('evals/recipe_briefs.toml','rb'))['brief']
      names = {n for b in briefs for n in [*b['wanted'], *b['excluded'], *b['inventory'], *[x for v in b['needs'].values() for x in v]]}
      report = open('docs/work/adjunct-fermentables/report.md', encoding='utf-8').read()
      missing = sorted(n for n in names if not re.search(r'\|\s*' + re.escape(n) + r'\s*\|', report))
      print(len(names), 'names;', 'missing:', missing)"
      ```
      Expect `missing: []`.
- [ ] `PROJECT.md` §8: one line linking the report, with the found / added / left-out counts.
Done when: the coverage command prints `missing: []`, and every row has a status and, for
left out, a reason.
Commit: `Add adjunct gap report`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Palmer PPG → extract % (46 → 100.0, 38 → 82.6) | `tests/test_adjuncts.py::test_extract_pct_from_ppg` | 3 |
| Each adjunct gets the printed extract, colour, max % and the right fermentability (lactose `none`, honey and candi `full`, flakes `normal`) | `tests/test_adjuncts.py::test_build_values_per_adjunct` | 3 |
| Every filled field names its source; `normal` needs none | `tests/test_adjuncts.py::test_every_filled_field_has_a_source` | 3 |
| A new hopline product never loads without a decision | `tests/test_adjuncts.py::test_unmapped_sku_raises` | 3 |
| A hand-typed hopline figure must be on the page | `tests/test_adjuncts.py::test_hopline_figure_not_on_page_raises` | 3 |
| The maps are consistent | `tests/test_adjuncts.py::test_maps_do_not_overlap` | 3 |
| The page text the adjunct figures are read from | `tests/test_fetch_hopline.py::test_page_text_runs_from_main_category_to_reviews` | 2 |
| The 74 malts become `normal` without reloading; misc rejects lactose | catalog queries in Task 1 | 1 |
| Loading twice gives identical rows | fingerprint query in Task 4 | 4 |

## Approved exceptions

None.

## Deviations
