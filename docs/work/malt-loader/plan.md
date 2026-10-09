# Malt loader (hopline malts + maltster catalogues) — implementation plan

Stage: implementing
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 4; was Task 5),
re-scoped by the user on 2026-10-09 (see Deviations)
Branch: malt-loader

## Approach

**Which malts:** exactly the grain malts that [hopline.hu](https://www.hopline.hu/alapanyagok/malatak/osszes-malata)
sells from Weyermann (37), Viking Malt (32) and Simpsons Malt (5): 74 rows. The other 8 listed
products are left out on purpose: Sladovna (2), BestMalz (1) and the malt extracts (5).
`malts.json` (still in `pending/`) is no longer used.

**Where the figures come from:** the maltster catalogue wins; hopline only fills a field the
catalogue lacks. `ref.fermentable.field_source` records the source slug of each filled field
(same idea as `ref.hop.field_source`), and `ref.ingredient.raw` keeps both source records whole,
keyed by source slug.

**Pieces:**
1. `loaders/fetch_hopline.py` fetches the listing and the product pages and writes the raw
   page facts (SKU, URL, name, spec text) to `shared/rag-files/pending/hopline_malts.json`.
   It does no interpretation.
2. `shared/rag-files/pending/malt_catalogue.json` is **hand-built** from the three PDFs: one
   entry per catalogue product that hopline sells, figures copied as printed, with the page
   number so each one can be checked. Parsing the PDFs with code was rejected: Weyermann and
   Viking print the spec table beside the prose in two columns, so a parser would be fragile
   and hard to read (§6.8). Both JSON files are source data and are never committed.
3. `loaders/malt_products.py` is the committed, explicit map: hopline SKU → (producer,
   catalogue product or `None`, ingredient name), plus the 8 skipped SKUs with a reason. An
   SKU in neither raises, so a new hopline product never loads without a decision.
4. `loaders/malts.py` parses the hopline spec text, merges each mapped product with its
   catalogue entry (pure, unit tested), then upserts `ref.ingredient` + `ref.fermentable`.

**Maths (tested code, never an LLM):** `ppg = extract_pct / 100 × 46.214`,
`potential_sg = 1 + ppg / 1000` rounded half-up to 4 places, from the dry-basis fine-grind
extract (Weyermann "Extract (dry substance)", Viking "EXTRACT FINE % dm", hopline
"Kihozatal: min X%"). Simpsons prints no extract, so Crystal T50, DRC and Crystal Extra Dark
get `NULL` potential; hopline's flat "min 70%" for these three is ignored (user decision). `max_pct` is the stated upper usage limit (catalogue usage text, else
hopline "Felhasználás"), `NULL` where neither states one; this replaces the earlier "stays NULL
until P3". `type` stays `NULL` until P3. Moisture, protein and origin are kept only in `raw`;
Lovibond is not stored (derived from EBC at display time, not in this work).

**Needs:** network access to hopline.hu (robots.txt only disallows `/shop_ajax/*`); the three
PDFs, now in `~/Downloads`: `WEYERMANN-PRODUCTS-Brewery-EN.pdf` (Crop 2026),
`VikingMalt_Standard_Portfolio_2023.pdf`, `simpsons-malt-nexthop-product-range-nov25.pdf`.

Rules: SI units (SG, EBC); unknown stays `NULL`; the loader is idempotent; source files are
never committed; nothing calls an LLM.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/010_ref_schema.sql` | changed | `ref.fermentable.field_source jsonb not null`; `max_pct` comment |
| `db/011_ref_sources.sql` | changed | 4 malt sources replace the 2 unused `malts.json` ones |
| `loaders/fetch_hopline.py` | new | `listing_links`, `product_page`, CLI writing `hopline_malts.json` |
| `loaders/malt_products.py` | new | `PRODUCTS` (74 SKUs), `SKIPPED` (8 SKUs), `IGNORE_HOPLINE_EXTRACT` (3 SKUs) |
| `loaders/malts.py` | new | spec parsing, `potential_sg`, `max_pct_from_text`, `merge`, `load`, CLI |
| `tests/test_fetch_hopline.py` | new | 2 tests on inline HTML |
| `tests/test_malts.py` | new | 8 tests on inline fixtures |
| `docs/work/fill-ref/README.md` | changed | item 4 and its source-file row describe the new inputs (done in the plan commit) |
| `PROJECT.md` | changed | §5 malt row, §4 scripts row, §8 |

Not committed (in `shared/rag-files/pending/`, already git-ignored): `hopline_malts.json`,
`malt_catalogue.json` and copies of the three PDFs.

## Tasks

### Task 1: Fetch the hopline malt pages
Why: hopline decides which malts are loaded; this captures its pages as raw data.
- [x] `loaders/fetch_hopline.py`, standard library only (`urllib.request`, `re`, `html`, `json`):
  - `listing_links(html: str) -> list[tuple[str, str]]`: `(sku, url)` from every
    `class="product__name-link ..." data-sku="NNNNNN" href="..."` anchor, in page order, no repeats.
  - `product_page(html: str) -> dict`: `name` = text of the `<h1 class='artdet__name ...'>`;
    `spec` = the visible page text (scripts and styles dropped, tags removed, entities
    unescaped, whitespace collapsed) from the first `Főkategória` up to the first `Bővebben`
    after it, or `None` if either marker is missing. The breadcrumb is `Alapanyagok Maláták`
    on most pages but `Feltöltött termékek` on the Simpsons crystal pages, so don't match on it.
  - CLI `python -m loaders.fetch_hopline OUT.json`: fetch `…/osszes-malata`, then
    `…/osszes-malata,2`, `,3`, … until a page adds no new SKU; then each product page. One
    request per second, a `User-Agent` naming this project, never `/shop_ajax/`. Writes
    `{"fetched": "<YYYY-MM-DD>", "listing": "<first listing URL>", "products": [{"sku", "url", "name", "spec"}, …]}`.
- [x] Write the tests first (`tests/test_fetch_hopline.py`, inline HTML) and see them fail:
  - `test_listing_links`: two anchors plus a repeat of the first → 2 pairs in order.
  - `test_product_page`: an `<h1 class='artdet__name x'>Simpsons Crystal T50 maláta</h1>`, a
    `<script>` containing `EBC: 1`, and `Főkategória Feltöltött termékek Simpsons Crystal T50 maláta EBC: 139 - 154 … Bővebben` →
    `name == "Simpsons Crystal T50 maláta"`, `spec` starts with `Főkategória`, contains
    `EBC: 139 - 154`, has no script text and no `Bővebben`.
- [x] Implement; `.venv/bin/python -m pytest tests/test_fetch_hopline.py -v` → 2 passed.
- [x] Run `.venv/bin/python -m loaders.fetch_hopline shared/rag-files/pending/hopline_malts.json`.
  Expect 82 products, every `name` set, `spec` set for all 74 SKUs Task 4 maps. If the count is
  not 82, stop and report (the shop changed since 2026-10-09).
Done when: 2 passed and the JSON holds 82 products.
Commit: `Add hopline malt page fetcher`

### Task 2: Malt sources and the `field_source` column
Why: every row needs its real source; per-field provenance needs a column.
- [x] `db/010_ref_schema.sql`: add `field_source jsonb not null  -- which source each field was taken from`
  to `create table ref.fermentable`; change the `max_pct` comment to
  `-- stated maximum share of the grist, %`; and at the end add
  `alter table ref.fermentable add column if not exists field_source jsonb not null;`
  (the table has 0 rows, measured 2026-10-09, so `not null` without a default works).
- [x] `db/011_ref_sources.sql`: replace the `weyermann-specs` and `viking-malt-2020` rows with:

  | slug | title | edition | publisher | url |
  |---|---|---|---|---|
  | `hopline-malts` | Hopline malt product pages | `website, fetched <the "fetched" date in hopline_malts.json>` | Hopline | `https://www.hopline.hu/alapanyagok/malatak/osszes-malata` |
  | `weyermann-2026` | Weyermann products, brewery (EN) | `Crop 2026` | Weyermann Specialty Malts | `https://www.weyermannmalt.com/` |
  | `viking-malt-2023` | Viking Malt Standard Product Portfolio | `2023` | Viking Malt | `https://www.vikingmalt.com/` |
  | `simpsons-malt-2025` | Simpsons Malt product range (NextHop) | `November 2025` | Simpsons Malt | `https://www.simpsonsmalt.co.uk/` |

  `licence` stays `NULL` (not checked).
  Under the corrections at the end, remove the two old rows (no row references them; measured
  0 ingredients on 2026-10-09):
  `delete from ref.source s where s.slug in ('weyermann-specs', 'viking-malt-2020') and not exists (select 1 from ref.ingredient i where i.source_id = s.id);`
- [x] Apply both twice as `postgres`:
  `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/010_ref_schema.sql` (then `011`).
- [x] Check: `select slug from ref.source order by id` → the 6 non-malt slugs plus the 4 new
  ones, 10 rows, no `weyermann-specs` / `viking-malt-2020`; `\d ref.fermentable` shows
  `field_source jsonb not null`; same after the second apply. Suite still passes.
Done when: both files apply twice without error and give the rows above.
Commit: `Add malt sources and fermentable field_source`

### Task 3: Parse and merge (pure, no files, no DB)
Why: potential and colour feed the gravity and colour maths in P2; a wrong merge corrupts recipes.
- [x] In `loaders/malts.py`:
  - `@dataclass Fermentable(name, producer, source_slug, potential_sg, extract_dbfg_pct, ebc, max_pct, field_source: dict[str, str], raw: dict)`.
  - `potential_sg(extract_pct: Decimal | None) -> Decimal | None` with the formula in Approach.
  - `max_pct_from_text(text: str | None) -> Decimal | None`, in this order: the first
    "up to N%", "max N%", "max. N%" or "<N%" → N; else a range "A-B%" or "A–B %" → B; else
    text that starts with "N %" or "N%" → N; else `None`.
  - `parse_hopline_spec(spec: str | None) -> dict` with `ebc` (`Range`; "a - b", "a-b",
    single "a" → `[a,a]`, "max a" → `(,a]`, "-" or missing → `None`, via `to_range`),
    `extract_pct` (the number after "Kihozatal :" and "min"/"min."; "? %", "- %" or missing →
    `None`) and `max_pct` (the text after "Felhasználás" up to "Származási" through
    `max_pct_from_text`; the colon may be spaced oddly, e.g. `Felhasználá s: 100 %`).
  - `merge(item: dict, producer: str, catalogue: dict | None, name: str, *, ignore_hopline_extract: bool = False) -> Fermentable`: each of
    `ebc`, `extract_dbfg_pct`, `max_pct` from the catalogue entry when it has a value, else from
    hopline; `potential_sg` follows `extract_dbfg_pct` and gets the same `field_source`.
    `ignore_hopline_extract=True` drops hopline's extract, so it stays `NULL` without a
    catalogue extract (used for the 3 Simpsons crystals, see Deviations).
    `field_source` lists only fields that have a value. `source_slug` = the producer's
    catalogue slug (`Weyermann` → `weyermann-2026`, `Viking Malt` → `viking-malt-2023`,
    `Simpsons Malt` → `simpsons-malt-2025`) when `catalogue` is given, else `hopline-malts`.
    `raw = {"hopline-malts": item, <catalogue slug>: catalogue}` (catalogue key only when given).
  - Catalogue entry fields used: `extract_pct`, `ebc_min`, `ebc_max`, `usage` (verbatim text
    through `max_pct_from_text`). The shape is fixed in Task 4.
- [x] Write the tests first (`tests/test_malts.py`) and see them fail on import:
  - `test_potential_sg`: `80.5` → `D("1.0372")`, `79` → `D("1.0365")`, `None` → `None`.
  - `test_max_pct_from_text`: `"100%"`→100, `"100 %"`→100, `"max. 10%"`→10, `"max 15%"`→15,
    `"1-2%"`→2, `"10-15 %"`→15, `"50% (20%ban prémium lágerekben)"`→50, `"? %"`→None,
    `"- %"`→None, `"Recommended addition: up to 100%"`→100,
    `"Dosage rate up to 20% (30%.)"`→20, `"Use in small amounts (<10%)."`→10,
    `"Typical rate of usage is around 50% of the grist"`→None, `None`→None.
  - `test_hopline_spec`: the Viking Pilsner spec (`EBC: 3.0 - 4.2 … Kihozatal: min 80% Felhasználás: 100% Származási hely: Finnország`)
    → `ebc == Range(D("3.0"), D("4.2"), "[]")`, extract 80, max 100; plus `EBC: 4.0` →
    `[4.0,4.0]`, `EBC: max 2.0` → `(,2.0]`, `EBC: -` → `None`, `Kihozatal : ? %` → `None`,
    `Felhasználá s: 100 %` → 100.
  - `test_catalogue_wins_hopline_fills`: Simpsons Maris Otter, catalogue
    `{ebc_min: 4.4, ebc_max: 6.6, extract_pct: None, usage: None}`, hopline spec
    `EBC: 5.5 - 7.5 … Kihozatal : min 79 % Felhasználás : 100 %` → `ebc == [4.4,6.6]`,
    `extract_dbfg_pct == 79`, `potential_sg == D("1.0365")`, `max_pct == 100`,
    `field_source == {"ebc": "simpsons-malt-2025", "extract_dbfg_pct": "hopline-malts", "potential_sg": "hopline-malts", "max_pct": "hopline-malts"}`,
    `set(raw) == {"hopline-malts", "simpsons-malt-2025"}`, `source_slug == "simpsons-malt-2025"`.
  - `test_no_extract_stays_null`: Crystal T50 (catalogue EBC 139–154, no extract) with a hopline
    spec without Kihozatal, and with the real spec (`Kihozatal : min 70 %`) and
    `ignore_hopline_extract=True` → both times `extract_dbfg_pct is None`, `potential_sg is None`,
    neither key in `field_source`.
  - `test_hopline_only`: Viking Sprau Malt, no catalogue (`EBC: 4.0 … Kihozatal : min 81% Felhasználás : max 15%`)
    → `source_slug == "hopline-malts"`, every `field_source` value `"hopline-malts"`, `max_pct == 15`.
- [x] Implement; `.venv/bin/python -m pytest tests/test_malts.py -v` → 6 passed; whole suite passes.
Done when: 6 passed, suite green.
Commit: `Parse and merge hopline and catalogue malts`

### Task 4: Catalogue figures and the hopline → catalogue map
Why: the catalogue supplies the figures; the explicit map decides which product each SKU is.
- [ ] Copy the three PDFs from `~/Downloads` to `shared/rag-files/pending/` (not committed).
  Get text with `pdftotext -layout` into the scratchpad.
- [ ] Build `shared/rag-files/pending/malt_catalogue.json`: a list with one entry per
  catalogue product that a hopline SKU maps to, nothing else:
  `{"maltster": "Weyermann" | "Viking Malt" | "Simpsons Malt", "product": "<name as printed, without the maltster word>", "page": <PDF page>, "extract_pct": <number or null>, "ebc_min": <number or null>, "ebc_max": <number or null>, "moisture_max_pct": <number or null>, "protein_pct": "<as printed or null>", "usage": "<the usage sentence verbatim, or null>"}`.
  Copy figures exactly (decimal comma → point). Extract: Weyermann "Extract (dry substance)",
  Viking "EXTRACT FINE % dm" (the Caramel group rows apply to each Caramel malt in the group),
  Simpsons none. Colour: a "max."/"<" value gives only `ebc_max`. Usage: Weyermann
  "Recommended addition: …", Viking the "Dosage/Usage rate …" sentence, Simpsons the bracket in
  Characteristics (e.g. "Use in small amounts (<10%).") or `null`. Moisture and protein are kept
  for `raw` only. After building, re-read every entry against its page text and fix mismatches.
- [ ] `loaders/malt_products.py`:
  - `PRODUCTS: dict[str, tuple[str, str | None, str]]`: SKU → (producer, catalogue product or
    `None`, ingredient name), one line per SKU with the hopline name as a comment. The name is
    the catalogue product, except where two SKUs share one product. Known matches:
    `100160` Viking Coffee maláta → Chocolate Light Malt; `100170` Viking Chocolate maláta →
    Chocolate Dark Malt; `100380` / `100381` cherry-wood / pear-wood smoked pilsner → catalogue
    `Smoked Malt` (Viking makes it with cherry and pear wood, among others), names
    `Smoked Malt (cherry wood)` / `Smoked Malt (pear wood)`; `101480` Viking Sprau Malt → `None`
    (not in the 2023 portfolio), name `Sprau Malt`; `101290` "Simpsons Marris Otter" (bag label
    Simpsons Maris Otter; the page text mentions Crisp, but the product and label are
    Simpsons) → `Finest Pale Ale Maris Otter`; `101310` → `Finest Pale Ale Golden Promise`.
    The other Weyermann and Viking SKUs match by name (Hungarian: Bécsi = Vienna,
    Búzamaláta = Wheat, pörkölt árpa = Roasted Barley, Keksz = Cookie, savas = Acidulated,
    rozs = Rye, füstölt = Smoked). If one cannot be matched with confidence, map it to `None`
    and record it in Deviations.
  - `IGNORE_HOPLINE_EXTRACT: set[str]`: `101510` Crystal Extra Dark, `101520` Crystal T50,
    `101530` DRC, with a comment giving the user's decision.
  - `SKIPPED: dict[str, str]`: `101000` BestMalz, `101440` / `101450` Sladovna, `101300`,
    `101330`, `101332`, `101333`, `101334` malt extracts, each with the reason.
- [ ] Add to `tests/test_malts.py`:
  - `test_product_map`: 74 `PRODUCTS` (Weyermann 37, Viking Malt 32, Simpsons Malt 5),
    8 `SKIPPED`, no SKU in both, and `name_key(name)` unique per producer (two names colliding
    would make the upsert overwrite one malt with another).
- [ ] Check against the files (a one-off command, not a test): every SKU in
  `hopline_malts.json` is in `PRODUCTS` or `SKIPPED`, and every non-`None` catalogue product
  exists in `malt_catalogue.json` exactly once.
- [ ] `.venv/bin/python -m pytest -v` → suite passes (7 in `test_malts.py`).
Done when: the map covers all 82 SKUs and every mapped product has a catalogue entry.
Commit: `Map hopline malts to catalogue products`

### Task 5: Load malts into `ref`
Why: the fermentable catalogue the recipe steps choose from (Review focus 4).
- [ ] In `loaders/malts.py` add `build(hopline: dict, catalogue: list[dict]) -> list[Fermentable]`
  (for each hopline product: in `SKIPPED` → skip; in `PRODUCTS` → `merge` with its catalogue
  entry looked up by `(producer, product)` and `ignore_hopline_extract=sku in IGNORE_HOPLINE_EXTRACT`, `KeyError` naming it if missing; otherwise
  `ValueError` naming the SKU), `load(conn, items) -> int` (`upsert_ingredient` with kind
  `fermentable`, producer and the source's id, then upsert `ref.fermentable` on
  `ingredient_id`, all columns including `field_source` as `Jsonb`; one transaction) and the CLI
  `python -m loaders.malts --hopline PATH --catalogue PATH`, which prints loaded and skipped counts.
- [ ] Add `test_unknown_sku_raises` to `tests/test_malts.py`: `build` with a hopline product
  whose SKU is in neither map → `ValueError`. Suite passes (8 in `test_malts.py`).
- [ ] Run it twice:
  `.venv/bin/python -m loaders.malts --hopline shared/rag-files/pending/hopline_malts.json --catalogue shared/rag-files/pending/malt_catalogue.json`
- [ ] After each run:
  - `select i.producer, count(*) from ref.ingredient i join ref.fermentable f on f.ingredient_id = i.id group by 1 order by 1`
    → `Simpsons Malt|5`, `Viking Malt|32`, `Weyermann|37`.
  - `select s.slug, count(*) from ref.ingredient i join ref.source s on s.id = i.source_id where i.kind = 'fermentable' group by 1 order by 1`
    → `hopline-malts|1` (Sprau Malt), `simpsons-malt-2025|5`, `viking-malt-2023|31`, `weyermann-2026|37`.
  - `select i.name from ref.fermentable f join ref.ingredient i on i.id = f.ingredient_id where f.potential_sg is null order by 1`
    → Crystal Extra Dark, Crystal T50, DRC (Simpsons names as printed). Any other row must
    have no extract in either source; list it in the PROJECT.md entry.
  - Maris Otter row: `ebc [4.4,6.6]`, `extract_dbfg_pct 79.0`, `potential_sg 1.0365`,
    `max_pct 100.0`, `field_source` as in `test_catalogue_wins_hopline_fills`.
  - Record (measured, not predicted): `count(ebc)`, `count(max_pct)`, and the
    `field_source->>'max_pct'` split by source.
- [ ] PROJECT.md §5: replace the `malts.json` row with "Malt data: hopline.hu malt list +
  Weyermann (Crop 2026), Viking Malt (2023), Simpsons (Nov 2025) catalogues", ✅ with the
  measured counts and date, and update the line above the table (what is in `pending/`).
  §4 scripts row: add the malt loader and fetcher. §8 entry.
Done when: both runs give the same counts and the Maris Otter row matches.
Commit: `Load hopline malts into ref`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Hopline page facts captured, script text excluded, works on both breadcrumb kinds | `tests/test_fetch_hopline.py::test_product_page` | 1 |
| Extract % → SG (`ppg = extract/100 × 46.214`), rounded to 4 places | `tests/test_malts.py::test_potential_sg` | 3 |
| Only a stated upper limit becomes `max_pct` | `tests/test_malts.py::test_max_pct_from_text` | 3 |
| Hopline formats: ranges, single, `max`, `-`, `?` | `tests/test_malts.py::test_hopline_spec` | 3 |
| Catalogue wins, hopline fills gaps, `field_source` and `raw` record both | `tests/test_malts.py::test_catalogue_wins_hopline_fills` | 3 |
| No extract anywhere (or hopline's ignored) stays `NULL`, never 0 | `tests/test_malts.py::test_no_extract_stays_null` | 3 |
| Unmatched product is sourced to hopline, never to a guessed catalogue | `tests/test_malts.py::test_hopline_only` | 3 |
| Every SKU decided once; no two malts share a name key | `tests/test_malts.py::test_product_map` | 4 |
| A new hopline product never loads silently | `tests/test_malts.py::test_unknown_sku_raises` | 5 |
| Re-running doesn't duplicate | load-twice counts | 5 |

## Approved exceptions

## Deviations

- 2026-10-09 · whole plan: input changed from `malts.json` (77 Weyermann + Viking rows) to the
  hopline.hu malt list plus the Weyermann, Viking and Simpsons catalogues — the user no longer
  supplies `malts.json` and wants only what hopline sells, with the missing fields added.
  Decided by the user: Sladovna, BestMalz and malt extracts left out; catalogue wins, hopline
  fills gaps, provenance per field; `max_pct` filled now (was "NULL until P3").
- 2026-10-09 · Task 3: `merge` takes `ignore_hopline_extract`, and `test_no_extract_stays_null`
  also checks it on the real Crystal T50 spec; Task 4 adds `IGNORE_HOPLINE_EXTRACT` (101510,
  101520, 101530) and Task 5's `build` passes it — hopline lists "Kihozatal: min 70%" for
  Simpsons Crystal T50, DRC and Crystal Extra Dark, and the user decided to keep their extract
  and potential `NULL` ("Keep them NULL").
