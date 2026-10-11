# Yeast loader (hopline.hu yeasts) — implementation plan

Stage: verify
Source: [`docs/FILL-REF-README.md`](../../FILL-REF-README.md) (P1a index, item 6), re-scoped by
the user on 2026-10-11 (see Deviations)
Branch: yeast-loader

## Approach

**Which yeasts:** every product on hopline.hu's two yeast pages,
[Száraz élesztő](https://www.hopline.hu/alapanyagok/elesztok/szaraz-eleszto) (dry) and
[Folyékony élesztő](https://www.hopline.hu/alapanyagok/elesztok/folyekony-eleszto) (liquid):
**129 products** (measured 2026-10-11: dry 90, liquid 39). That gives **119 `ref.yeast` rows**:
129 − 2 Brewline 2 g packs (kept in `raw` of their 12 g product) − 8 non-beer yeasts skipped
(whiskey 3, cider 2, mead 2, sake 1; user decision). Brewline, hopline's own repack brand, gets
its own rows, even where its page says it is the same strain as another maker's product (user
decision). Rows per producer: YeastFlow 38, Lallemand 18, Norse Nectar 17, Fermentis 13,
Mangrove Jack's 13, Brewline 10, Gozdawa 9, YeasterBunny 1. Form: dry 81, liquid 38.
The Brewtarget BeerJSON files are not used.

**How the pages are listed:** unlike the malt and hop listings, these two pages render no
product links in their HTML (0 `data-sku` anchors, measured); the browser loads the list with a
GET to the same page URL with `?action=cat_art_list&ajax=1&ajax_nodesign=1&filter=&page=N`,
which returns JSON whose `product_list_content` holds the usual `product__name-link` anchors
(dry: 5 pages, 90 SKUs; liquid: 2 pages, 39; a page past the end repeats the last page, so "stop
when a page adds no new SKU" works). This is not `/shop_ajax/` (robots.txt disallows only that).
The producer subpages (`…/szaraz-eleszto/fermentis-203`, …) do render links, but together they
miss 7 dry products (Brewline and Gozdawa W-34/70 pages), so they are not used.

**What each page holds (measured on all 129):**

| Where on the page | Fields | Coverage |
|---|---|---|
| Data block (`artdet__param-title` / `-value`, "Adatok") | `Stílus` (style family), `Hőmérséklet` (`18 – 28 °C`), `Flokkuláció` (`Alacsony` / `Közepes` / `Magas`), `Alkoholtolarencia` (`9 – 11 v/v%`), `Aroma`, sometimes `Címkék` | Stílus 128, Hőmérséklet 125 (+1 as `Minimum hőmérséklet` 24 / `Maximum hőmérséklet` 30, Suava), Flokkuláció 117, Alkoholtolarencia 117 |
| Long description (`long-description__content`, "Részletek") | a table `Stílus` / `Aroma` / `Flokkuláció` / `Alkoholtolerancia` (88 pages; values like `nagyon magas`, `közepes - magas`, `~12 %`, `12 %+`, `9-11 %`), then `<strong>Label:</strong> value` lines: `Ideális hőmérséklet` 122, `Ajánlott sörtípusok` 123, `Adagolás` 127; a maker data-sheet link on 47 pages | |
| Short spec table (top of page) | `Stílus` + `Aroma` (88) or `Stílus` + `Hőmérséklet` + `Alk. tolarencia` (39, YeastFlow) | 127 |

**Not on any page: attenuation.** No page states an attenuation figure (4 YeastFlow pages mention
it in words only). Attenuation drives FG, so Task 6 takes it from the sources the user named
on 2026-10-11, one per producer:

| Producer (rows) | Attenuation source | Source slug |
|---|---|---|
| YeastFlow (38) | catalogue <https://yeastflow.com/our-strains/> | `yeastflow-catalogue` |
| Lallemand (18) | product catalogue <https://www.lallemandbrewing.com/en/continental-europe/products/brewing-yeast?page=1> (and its further pages); **not** the links on hopline's Lallemand pages, which the user says are wrong | `lallemand-catalogue` |
| Fermentis (13) | the data sheets linked from hopline's Fermentis pages; T-58 `302010` has none, use <https://fermentis.com/en/product/safale-t%e2%80%9158/>; where hopline links another strain's sheet (BE-256 → S-189, S-33 → T-58, BR-8 → W-34/70), the strain's own fermentis.com product page | `fermentis-datasheets` |
| Mangrove Jack's (13) | the product pages linked from hopline's pages; where the link is another strain's page (M20 → M15), a 404 (M47) or the Yeast Range booklet (M84), the strain's page in that booklet | `mangrovejacks-datasheets` |
| Brewline (10) | Brewfather, figures given by the user (below; the catalogue PDF <https://www.brewline.eu/images/EN_CATALOGUE_BREWLINE.pdf> lists none of these products); Abbey Monk Ale `301011` and Pure Hornindal `302310` have none | `brewfather` |
| Gozdawa (9) | Brewfather, figures given by the user (below); W-34/70 `301471` has none | `brewfather` |
| YeastFlow YF-666 `301242` | its page prints `800-100`; the user confirmed 80–100 | `user-supplied` |
| Norse Nectar (17), YeasterBunny (1) | none: the user said to skip them. They are still loaded, with attenuation `NULL` (orchestrator's reading of "skip" / "leave out": no attenuation source, not dropped) | — |

Gozdawa figures from Brewfather, as the user gave them: Czech Pilsner 18 `301491` 76, Old
German Altbier `301571` 78, Porter&Kvass `301531` 72, Pure Ale `301541` 75, "Rochefort" Trappist
Ale `301561` 77, Conan "New England" `301482` 76, Noble Saison `301540` 83, Real Scotland
`301551` 71. Gozdawa W-34/70 `301471` has no figure and stays `NULL`. Brewline figures from
Brewfather, as the user gave them: Belgian Wit `301650` 78, Bajor Búza `302170` 73 (the user's
"german wheat"), British Ale `301021` 75, Czech Lager `301492` 76, German Lager `301101` 81, High
Performance Ale `300091` 81, Köln `300121` 78, U.S. West Coast Ale `301601` 80. Brewfather gives one
figure, so each is stored as the point range `[a,a]`, not widened into a guessed range; the
same goes for any other source that prints one figure.

**Where each field comes from** (source slug `hopline-yeasts`):
- `temp_c` ← data block `Hőmérséklet`, else `Minimum hőmérséklet`–`Maximum hőmérséklet`. Every
  value is in °C (measured), so nothing is converted; any other unit raises.
- `flocculation` ← data block `Flokkuláció`, else the description table's. Hungarian → schema:
  `alacsony` low, `közepes-alacsony` medium low, `közepes` medium, `közepes-magas` /
  `közepes - magas` medium high, `magas` high, `nagyon magas` very high (and `low` low, seen once);
  `-` → `NULL`; anything else raises.
- `alcohol_tolerance_pct` ← the top of the data block's `Alkoholtolarencia` range, else the
  description table's value (top of a range, `~` and `+` dropped). The data block is a range
  (`9 – 11 v/v%`) and the column a single value; on the 81 pages that have both, the range top
  equals the description's figure on 76 (e.g. Nottingham `12 – 14` / `14 %`, CBC-1 `16 – 18` /
  `18 %`).
- `form` ← which of the two pages lists the SKU: `dry` or `liquid`.
- `type` ← data block `Stílus` through a fixed map: `kveik` → `kveik`; `Lager`, `Pilsner` →
  `lager`; `Brett` → `brett`; `Ale`, `English Ale`, `London Ale`, `West Coast Ale`,
  `East Coast Ale`, `Belga Ale`, `Belga Wit`, `Saison`, `Farmhouse`, `Bajor búza`,
  `Amerikai búza`, `Kölsch`, `Barleywine` → `ale`; `sour`, `conditioning` and no `Stílus` →
  `NULL` (the page doesn't say what culture it is); an unknown value raises. (Change the map at
  approval if you want other types.)
- `product_id`, `producer`, ingredient name ← the committed SKU map (`loaders/yeast_products.py`),
  never parsed on the fly.
- `attenuation_pct` ← Task 6, from the producer's source in the table above; `NULL` until then,
  and for Norse Nectar, YeasterBunny, Gozdawa W-34/70 and any strain its source lacks.

Data block first because it has one format on every page; the description fills gaps. Where
the two disagree (measured: temperature on 23 of 121 pages with both, flocculation on 9 of 81,
alcohol on 5 of 81) the report
lists it, so the user can check the page.

**Pieces** (the hop pattern):
1. `loaders/fetch_hopline.py` gets a `--yeasts` mode writing
   `shared/rag-files/pending/hopline_yeasts.json`: raw page facts, no interpretation.
2. `loaders/yeast_products.py` is the committed, explicit map: main SKU → (producer, product id,
   name); Brewline 2 g SKU → its 12 g SKU; skipped SKU → reason. An SKU in none raises.
3. `loaders/yeasts.py` parses (pure, unit tested), builds one `Yeast` per main SKU, writes
   `docs/work/yeast-loader/report.md`, and upserts `ref.ingredient` (kind `yeast`, producer set)
   + `ref.yeast`, with per-field provenance in a new `ref.yeast.field_source` (as `ref.hop` and
   `ref.fermentable` have), because attenuation will come from another source than the rest.

**Rules:** SI units (°C; °F would be converted once, but hopline has none); unknown stays `NULL`,
never 0; a format the parser doesn't know raises; `raw` keeps every hopline record of the yeast
whole (main page and its 2 g pack page, if any); the loader is idempotent; source files are never
committed; nothing calls an LLM.

**Needs:** network access to hopline.hu, and in Task 6 to the attenuation sources above (all
named by the user, so nothing waits on the user any more).

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `loaders/fetch_hopline.py` | changed | `div_content`, `long_description`, `ajax_listing`, `--yeasts` mode |
| `tests/test_fetch_hopline.py` | changed | 2 new tests |
| `db/010_ref_schema.sql` | changed | `ref.yeast.field_source jsonb not null` |
| `db/011_ref_sources.sql` | changed | `hopline-yeasts` source; remove unused `brewtarget-default-data`; 5 attenuation sources (Task 6) |
| `loaders/yeast_products.py` | new | `YEASTS` (119), `PACK_SIZES` (2), `SKIPPED` (8), `BREWLINE_COPIES` (8, report only), later `ATTENUATION` |
| `loaders/yeasts.py` | new | `Yeast`, `parse_range`, `tolerance`, `flocculation`, `TYPES`, `make_yeast`, `build`, `report`, `load`, CLI |
| `tests/test_yeasts.py` | new | 10 tests on inline fixtures |
| `docs/work/yeast-loader/report.md` | new | data block vs description disagreements, the strain each Brewline page says it copies, yeasts without attenuation |
| `docs/FILL-REF-README.md` | changed | item 6 and its source-file rows describe the new input (in the plan commit) |
| `docs/DATABASE.md` | changed | `yeast` row: source and count |
| `docs/RECIPE-ROADMAP.md` | changed | yeast source (hopline, attenuation from the makers and Brewfather) in §2, §6 and P1; D8 moved out of §9 as decided |
| `PROJECT.md` | changed | §5 yeast row, §7 D8 decided, §4 scripts and database rows, §8 |

Not committed (in `shared/rag-files/pending/`, git-ignored): `hopline_yeasts.json`.

## Tasks

### Task 1: Fetch the hopline yeast pages
Why: hopline decides which yeasts are loaded; this captures its pages as raw data.
- [x] In `loaders/fetch_hopline.py` (standard library only, as now):
  - `div_content(html: str, marker: str) -> str | None`: the div walk now inside
    `short_description`, taking the class name as `marker`; `short_description` becomes
    `div_content(html, SHORT_DESCRIPTION)`. Malt and hop output must not change.
  - `long_description(html: str) -> dict | None`: from `div_content(html, "long-description__content")`
    (`None` when absent): `{"table": <first table, read as spec_table reads one (shared helper `table_dict`)>, "labels": {<strong> text without the trailing colon: the text after it (a leading colon dropped) up to the next `<br`, `</p>` or `<strong>`; labels with no text after them left out}, "text": visible_text(...)}`.
    The description starts with a `<style>` block whose CSS mentions `table` and `.mobile-head`;
    it must not end up in `text`.
  - the `--yeasts` product records also carry `details = long_description(html)` (added in
    the yeast fetch, not in `product_page`, so malt and hop output stays unchanged).
  - `ajax_listing(category_url: str) -> list[tuple[str, str]]`: GET
    `category_url + "?action=cat_art_list&ajax=1&ajax_nodesign=1&filter=&page=" + str(n)` for
    n = 1, 2, …, read `json.loads(body)["product_list_content"]` with `listing_links`, stop when
    a page adds no new SKU. Same `fetch` (one request per second, never `/shop_ajax/`).
  - CLI: `--yeasts` (exclusive with `--hops`) reads
    `YEAST_LISTINGS = {"dry": …/alapanyagok/elesztok/szaraz-eleszto, "liquid": …/alapanyagok/elesztok/folyekony-eleszto}`
    with `ajax_listing` and writes
    `{"fetched", "listings": YEAST_LISTINGS, "forms": {"dry": [sku…], "liquid": [sku…]}, "products": [{"sku", "url", "name", "spec", "table", "params", "details"}, …]}`.
- [x] Write the tests first (`tests/test_fetch_hopline.py`, inline HTML) and see them fail:
  - `test_ajax_listing_body`: a JSON body `{"filter_box_content": "…", "product_list_content": "<two product__name-link anchors>"}`
    through the same parse `ajax_listing` uses (factor it as `ajax_links(body: str)`) → both
    `(sku, url)` pairs in order.
  - `test_long_description`: the US-05 shape: `<div class="long-description__content …"><style>table .mobile-head {display:none;}</style><table>` with `<th>` Stílus, Aroma,
    Flokkuláció, Alkoholtolerancia and `<td>` Ale, semleges, közepes, 9-11 %, then
    `<p><strong>Ideális hőmérséklet: </strong>18 - 28 °C</p><p><strong>Adagolás:</strong> 5-8g/10l</p></div>`
    → `table == {"Stílus": "Ale", "Aroma": "semleges", "Flokkuláció": "közepes", "Alkoholtolerancia": "9-11 %"}`,
    `labels == {"Ideális hőmérséklet": "18 - 28 °C", "Adagolás": "5-8g/10l"}`, `text` contains
    `Ideális hőmérséklet` and not `mobile-head`; a page without the div → `None`.
- [x] Implement; `.venv/bin/python -m pytest tests/test_fetch_hopline.py -v` → 6 passed; suite passes.
- [x] Run `.venv/bin/python -m loaders.fetch_hopline --yeasts shared/rag-files/pending/hopline_yeasts.json`.
  Expect 129 products (forms dry 90, liquid 39, no SKU in both), every `name` and `params` set,
  `details` set on all. If the count is not 129, stop and report (the shop changed since 2026-10-11).
Done when: 6 passed and the JSON holds 129 products.
Commit: `Fetch hopline yeast pages`

### Task 2: Yeast source and `ref.yeast.field_source`
Why: every row needs its real source; attenuation will come from a second source, so provenance
is per field.
- [x] `db/010_ref_schema.sql`: add `field_source jsonb not null  -- which source each field was taken from`
  to `create table ref.yeast`, and after the fermentable one add
  `alter table ref.yeast add column if not exists field_source jsonb not null;`
  (`ref.yeast` has 0 rows, measured 2026-10-11).
- [x] `db/011_ref_sources.sql`: add
  `('hopline-yeasts', 'Hopline yeast product pages', 'website, fetched <the "fetched" date in hopline_yeasts.json>', 'Hopline', null, 'https://www.hopline.hu/alapanyagok/elesztok/szaraz-eleszto', 'Dry and liquid yeast pages (szaraz-eleszto, folyekony-eleszto)')`,
  remove the `brewtarget-default-data` row from the insert list, and under the corrections add
  (0 ingredients reference it, measured 2026-10-11):
  `delete from ref.source s where s.slug = 'brewtarget-default-data' and not exists (select 1 from ref.ingredient i where i.source_id = s.id);`
- [x] Apply both twice as `postgres`:
  `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/010_ref_schema.sql` (then `011`).
- [x] Check after each apply: `select slug from ref.source order by id` → 11 rows, includes
  `hopline-yeasts`, no `brewtarget-default-data`; `\d ref.yeast` shows `field_source jsonb not null`.
  Suite still passes.
Done when: both files apply twice without error and give those rows.
Commit: `Add hopline yeast source and yeast field_source`

### Task 3: Parse a yeast (pure, no files, no DB)
Why: temperature and attenuation drive the fermentation step and FG; a wrong unit or a silent 0
corrupts recipes.
- [x] In `loaders/yeasts.py`:
  - `@dataclass Yeast(name, producer, product_id, type, form, attenuation_pct, temp_c, flocculation, alcohol_tolerance_pct, field_source: dict[str, str], raw: dict)`.
  - `parse_range(text: str | None, unit: str) -> Range | None`: decimal comma → point, a leading
    `~` dropped; `a`, `a-b`, `a – b` followed by `unit` (`°C` or `v/v%` or `%`, space optional)
    → `to_range(a, b)`; `None`, `""`, `"-"` → `None`; anything else (including `°F`) →
    `ValueError` naming the text.
  - `tolerance(params: dict, details_table: dict | None) -> Decimal | None`: the upper bound of
    `parse_range(params["Alkoholtolarencia"], "v/v%")`, else of the description table's
    `Alkoholtolerancia` or `Alkohol tolerancia` (a trailing `+` dropped, unit `%`), else `None`.
  - `FLOCCULATION: dict[str, str]` (the map in Approach, keys lowercase) and
    `flocculation(params, details_table) -> str | None`: data block first, then the table; `-`
    → `None`; unknown word → `ValueError`.
  - `TYPES: dict[str, str | None]` (the map in Approach) and `type_of(stilus: str | None)`:
    `None` → `None`; unknown → `ValueError`.
  - `make_yeast(producer, product_id, name, form, main: dict, extras: list[dict]) -> Yeast`:
    `main`/`extras` are product dicts as in `hopline_yeasts.json`; figures from `main` only.
    `temp_c` ← `parse_range(params["Hőmérséklet"], "°C")`, else
    `to_range(params["Minimum hőmérséklet"], params["Maximum hőmérséklet"])`. `field_source` =
    `"hopline-yeasts"` for each of `temp_c`, `flocculation`, `alcohol_tolerance_pct`, `type`,
    `form`, `product_id` that has a value, nothing else. `raw = {"hopline-yeasts": {sku: product, …}}`
    for `main` and every extra. `attenuation_pct = None`.
- [x] Write the tests first (`tests/test_yeasts.py`) and see them fail on import:
  - `test_parse_range`: `"18 – 28 °C"`→`[18,28]`, `"17-22°C"`→`[17,22]`,
    `"15,5 – 17,5 v/v%"`→`[15.5,17.5]` (unit `v/v%`), `"10 – 10 v/v%"`→`[10,10]`,
    `"~12 %"`→`[12,12]` (unit `%`), `None`/`""`/`"-"`→`None`, `"64 – 82 °F"`→`ValueError`,
    `"lots"`→`ValueError`. Compare `Range(D(…), D(…), "[]")`. (The °F case is the guard that
    nothing is ever stored un-converted.)
  - `test_tolerance`: `{"Alkoholtolarencia": "9 – 11 v/v%"}` → `D("11")`; no data block, table
    `{"Alkoholtolerancia": "12 %+"}` → `12`, `"5-5.5%"` → `5.5`, `"17,5 %"` → `17.5`,
    `{"Alkohol tolerancia": "12%"}` → `12`; neither → `None`.
  - `test_flocculation`: `Magas`→high, `Közepes`→medium, `Alacsony`→low; no data block and table
    `nagyon magas`→very high, `közepes - magas`→medium high, `közepes-alacsony`→medium low,
    `-`→`None`; `"sticky"`→`ValueError`.
  - `test_type_of`: `kveik`→kveik, `Pilsner`→lager, `Brett`→brett, `Belga Wit`→ale,
    `sour`→`None`, `None`→`None`, `"Wine"`→`ValueError`.
  - `test_us05`: US-05 `301030` (params `Stílus: Ale`, `Hőmérséklet: 18 – 28 °C`,
    `Flokkuláció: Közepes`, `Alkoholtolarencia: 9 – 11 v/v%`; details table as in
    `test_long_description`), no extras, producer `Fermentis`, product id `US-05`, form `dry` →
    `temp_c == [18,28]`, `flocculation == "medium"`, `alcohol_tolerance_pct == 11`,
    `type == "ale"`, `attenuation_pct is None`, `field_source` has exactly the 6 fields, all
    `"hopline-yeasts"`, `raw == {"hopline-yeasts": {"301030": <the product>}}`.
  - `test_brewline_pack_size`: Brewline U.S. West Coast Ale 12 g `301601` (params only `Címkék`,
    `Stílus: West Coast Ale`, `Hőmérséklet: 18 – 28 °C`; details table `Ale`, `Semleges`,
    `közepes`, `9-11 %`) with extra 2 g `301600` (`Hőmérséklet: 18 – 30 °C`, to prove extras are
    ignored), producer `Brewline`, product id `None` → `temp_c == [18,28]`,
    `flocculation == "medium"`, `alcohol_tolerance_pct == 11` (both from the description),
    `type == "ale"`, `product_id` not in `field_source`,
    `set(raw["hopline-yeasts"]) == {"301601", "301600"}`.
  - `test_description_fills_gaps`: Gozdawa Real Scotland `301551` (data block without
    `Flokkuláció` and `Alkoholtolarencia`, table `magas`, `5-5.5%`) → `high`, `5.5`; Suava
    `302410` (no `Hőmérséklet`, `Minimum hőmérséklet: 24`, `Maximum hőmérséklet: 30`, no
    `Stílus`) → `temp_c == [24,30]`, `type is None`, `type` not in `field_source`.
- [x] Implement; `.venv/bin/python -m pytest tests/test_yeasts.py -v` → 7 passed; suite passes.
Done when: 7 passed, suite green.
Commit: `Parse hopline yeast pages`

### Task 4: The hopline SKU → yeast map
Why: the explicit map decides what each product is, so nothing is merged or named on a guess.
- [x] `loaders/yeast_products.py`, one line per SKU with hopline's product name as a comment:
  - `YEASTS: dict[str, tuple[str, str | None, str]]`: main SKU → (producer, product id, name),
    119 entries. Producer is the brand in hopline's name (`SafAle`/`SafLager` → Fermentis,
    `Lalbrew` → Lallemand, `Mangrove's Jack` → Mangrove Jack's, `Brewline` → Brewline).
    Product id only as hopline's name prints it, normalised to the maker's form (`US-05`,
    `W-34/70`, `BE-256`, `BR-8`, `BRY-97`, `CBC-1`, `M20`, `M44`, `YF-101`, `YB-208`), else
    `None` (Norse Nectar, most Lallemand and Gozdawa); Suava `302410` → `None` (its `WLP079` is
    another maker's code); every Brewline row → `None` (Brewline has no codes; `W34/70` in
    `301101`'s name is the copied strain's). Name: the strain as the maker sells it, product id
    included, without the producer word, "élesztő", "Yeast", "kveik" and the pack size, with
    hopline's spelling fixed (`Mangrove's Jack`): `SafAle US-05`, `SafLager W-34/70`,
    `Nottingham`, `M20 Bavarian Wheat`, `YF-101 Queen of Hearts`, `Hornindal`,
    `YB-208 Tormodgarden`, `W-34/70` (Gozdawa `301471`). The 10 Brewline rows: `301101` German
    Lager, `301492` Czech Lager, `300091` High Performance Ale, `300121` Köln, `301011` Abbey Monk
    Ale, `302310` Pure Hornindal, `302170` Bajor Búza, `301650` Belgian Wit, `301021` British Ale,
    `301601` U.S. West Coast Ale. Each Brewline line's comment names the strain its page says it
    copies (W-34/70, Gozdawa CP18, Nottingham, BE-256, WB-06, T-58, S-04, "US-05 and BRY-97";
    Köln and Pure Hornindal name none).
  - `PACK_SIZES: dict[str, str]`: 2 g SKU → 12 g SKU, 2 entries: `301610` → `301021` (British
    Ale), `301600` → `301601` (U.S. West Coast Ale). The 2 g page is kept in `raw` only.
  - `SKIPPED: dict[str, str]`: 8 non-beer yeasts with the reason: whiskey `301580`, `301560`,
    `301570`; cider `301581`, `300250`; mead `301591`, `300230`; sake `301241`.
- [x] Add `test_yeast_map` to `tests/test_yeasts.py`: 119 `YEASTS` (10 with producer
  `Brewline`), 2 `PACK_SIZES`, 8 `SKIPPED`, no SKU in two of them, every `PACK_SIZES` value is
  in `YEASTS`, and
  `(name_key(producer), name_key(name))` unique across `YEASTS` (two colliding would make the
  upsert overwrite one yeast with another).
- [x] Check against the file (a one-off command, not a test): every SKU in `hopline_yeasts.json`
  is in exactly one map, and every `YEASTS` SKU is in the file. Producer counts as in Approach.
- [x] Suite passes (8 in `test_yeasts.py`).
Done when: the maps cover all 129 SKUs.
Commit: `Map hopline yeast products`

### Task 5: Load yeasts into `ref` and write the report
Why: the yeast catalogue step 6 chooses from.
- [x] In `loaders/yeasts.py` add:
  - `build(hopline: dict) -> list[Yeast]`: an SKU in no map → `ValueError` naming it; `SKIPPED`
    → left out; for each `YEASTS` SKU, `make_yeast(producer, product_id, name, form from hopline["forms"], main, its PACK_SIZES extras)`.
  - `report(hopline: dict) -> str`: Markdown lists: pages where the data block and the
    description disagree on temperature (`Ideális hőmérséklet`), flocculation or alcohol
    (expected 23 / 9 / 5 on all 129 pages, including M20 `302200-H`, whose description shows
    another strain); each Brewline row with the strain its page says it copies and whether its
    data block differs from that strain's page; 2 g pages whose data block differs from the
    12 g page's; yeasts without attenuation; the 3 kveiks whose page says "Lactobacillust tartalmaz!" (`302360`,
    `301170`, `301150`).
  - `load(conn, yeasts) -> int`: `upsert_ingredient(conn, "yeast", name, producer, source_id(conn, "hopline-yeasts"), raw)`,
    then upsert `ref.yeast` on `ingredient_id` (every column, `field_source` as `Jsonb`), one
    transaction, as `loaders/hops.py::load`.
  - CLI `python -m loaders.yeasts --hopline PATH --report PATH`: builds, loads, writes the
    report, prints loaded and skipped counts.
- [x] Add `test_unknown_sku_raises`: `build` with a product whose SKU is in no map → `ValueError`.
  Suite passes (9 in `test_yeasts.py`).
- [x] Run it twice:
  `.venv/bin/python -m loaders.yeasts --hopline shared/rag-files/pending/hopline_yeasts.json --report docs/work/yeast-loader/report.md`
- [x] After each run (expected values measured on the 2026-10-11 pages; record what you get):
  - `select count(*), count(temp_c), count(flocculation), count(alcohol_tolerance_pct), count(attenuation_pct) from ref.yeast` → `119|119|113|114|0`.
  - `select form, count(*) from ref.yeast group by 1 order by 1` → dry 81, liquid 38.
  - `select i.producer, count(*) from ref.yeast y join ref.ingredient i on i.id = y.ingredient_id group by 1 order by 1`
    → the producer counts in Approach.
  - US-05 row: `product_id US-05`, `form dry`, `type ale`, `temp_c [18,28]`, `flocculation medium`,
    `alcohol_tolerance_pct 11.0`, `raw` with 1 SKU.
  - `select count(*) from ref.ingredient where kind = 'yeast' and source_id <> (select id from ref.source where slug = 'hopline-yeasts')` → 0.
- [x] `grep -nwiE "ollama|llm" loaders/yeasts.py loaders/yeast_products.py` → nothing.
- [x] PROJECT.md §5 yeast row ✅ with the measured counts and date, and the line above the table
  (what is in `pending/`); §4 scripts row (yeast loader, map, `--yeasts` fetch) and database row
  (`ref.yeast` count, `field_source`); `docs/DATABASE.md` `yeast` row (source hopline, count);
  §8 entry pointing at `report.md`.
Done when: both runs give the same counts and the US-05 row matches.
Commit: `Load hopline yeasts into ref`

### Task 6: Attenuation from the makers' catalogues
Why: attenuation sets FG; hopline has none. Sources as in the Approach table (user, 2026-10-11).
- [x] `db/011_ref_sources.sql`: add 5 rows, `licence` `NULL`, edition `website, fetched <date>`
  (Brewfather: `website, figures given by the user 2026-10-11`):
  `yeastflow-catalogue` (YeastFlow strain catalogue, YeastFlow, <https://yeastflow.com/our-strains/>),
  `lallemand-catalogue` (Lallemand brewing yeast catalogue, Lallemand Brewing, the URL in Approach),
  `fermentis-datasheets` (Fermentis technical data sheets, Fermentis, <https://fermentis.com/>),
  `mangrovejacks-datasheets` (Mangrove Jack's yeast data sheets, Mangrove Jack's, <https://mangrovejacks.com/>),
  `brewfather` (Brewfather yeast database, Brewfather, <https://brewfather.app/>).
  `user-supplied` (already there) takes YF-666. Apply twice as `postgres`;
  `select count(*) from ref.source` → 16 both times.
- [x] Read each source (fetch into the scratchpad, `pdftotext -layout` for PDFs; one request per
  second, a `User-Agent` naming the project). For each loaded strain, copy the attenuation
  exactly as printed (decimal comma → point; `a-b %` → `(a, b)`, one figure → `(a, a)`), with
  the URL it was read from. A word only ("medium-high") or no figure → no entry; list it in the
  report. Match by product id where the source prints one, else by name; a match you aren't sure
  of → no entry, listed in the report. Afterwards re-read every entry against its source text.
- [x] `loaders/yeast_products.py`: `ATTENUATION: dict[str, dict]`, main SKU →
  `{"attenuation_pct": ("78", "82"), "source": "<slug>", "url": "<page or PDF read>", "printed": "<the text as printed>", "date": "<YYYY-MM-DD>"}`.
  Gozdawa and Brewline entries use source `brewfather`, `url` `None`, `printed` the user's
  figure, e.g. `"76"` for `301491`, date `2026-10-11`. YF-666 uses `user-supplied`, its page URL,
  `printed` `"800-100"` and the user's words.
- [x] `make_yeast` takes `attenuation: dict | None`; when given, `attenuation_pct = to_range(*…)`,
  `field_source["attenuation_pct"] = entry["source"]`, and the entry goes in
  `raw[entry["source"]]`. `build` passes `ATTENUATION.get(sku)`. The load step looks up no
  extra `source_id`: the ingredient's source stays `hopline-yeasts`.
- [x] Tests: `test_attenuation_fill` (a `fermentis-datasheets` range entry fills
  `attenuation_pct` with that source and lands in `raw["fermentis-datasheets"]`; the Gozdawa
  Czech Pilsner 18 entry `76` → `[76,76]` with source `brewfather`; without an entry it stays
  `None` and is not in `field_source`); `test_yeast_map` also checks every `ATTENUATION` key is
  in `YEASTS`, every `source` is one of the 5 slugs or `user-supplied`, no Norse Nectar or YeasterBunny SKU
  has an entry, Bajor Búza is `brewfather` 73 and YF-666 `user-supplied` [80,100] with
  `printed` `800-100`. Suite passes (10 in `test_yeasts.py`).
- [x] Run the loader twice; `count(attenuation_pct)` = number of `ATTENUATION` entries both
  times (measured 93: 119 − 17 Norse Nectar − 1 YeasterBunny − 8 with no figure in their source), other counts
  as in Task 5; `select field_source->>'attenuation_pct', count(*) from ref.yeast group by 1`
  recorded. The report lists every yeast still without attenuation, with the reason. Update
  PROJECT.md §5 / §8 and §4 database row (source count 16).
Done when: both runs give the same counts and every `ATTENUATION` figure is in `ref.yeast`.
Commit: `Add yeast attenuation from maker catalogues`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every yeast SKU is found, though the pages load their list by script | `tests/test_fetch_hopline.py::test_ajax_listing_body` | 1 |
| Description table and labels captured, CSS excluded | `tests/test_fetch_hopline.py::test_long_description` | 1 |
| Temperatures stored in °C as printed; any other unit raises, never stored un-converted | `tests/test_yeasts.py::test_parse_range` | 3 |
| Alcohol tolerance = range top; description only as fallback | `tests/test_yeasts.py::test_tolerance` | 3 |
| Flocculation words → the 7 schema values; unknown raises | `tests/test_yeasts.py::test_flocculation` | 3 |
| Style family → type; unknown raises | `tests/test_yeasts.py::test_type_of` | 3 |
| Figures from the main page only, `field_source` and `raw` complete | `tests/test_yeasts.py::test_us05`, `::test_brewline_pack_size` | 3 |
| Description fills data-block gaps; Min/Max temperature read | `tests/test_yeasts.py::test_description_fills_gaps` | 3 |
| Every SKU decided once; no two yeasts share a key (no silent merge) | `tests/test_yeasts.py::test_yeast_map` | 4 |
| A new hopline product never loads silently | `tests/test_yeasts.py::test_unknown_sku_raises` | 5 |
| Re-running doesn't duplicate | load-twice counts | 5, 6 |
| Attenuation only from a named source, as printed (one figure → `[a,a]`), `field_source` per source | `tests/test_yeasts.py::test_attenuation_fill` | 6 |

## Approved exceptions

## Deviations

- 2026-10-11 · whole plan: input changed from the two Brewtarget BeerJSON files
  (`DefaultContent003`, `DefaultContent004`, 571 entries, deduped on producer + product id) to
  hopline.hu's dry and liquid yeast pages (129 products → 119 yeasts) — the user asked to work
  from these two pages "like you did for malts and hops". The Brewtarget files are no longer
  needed (blocker removed), the dedupe tests are replaced by the explicit SKU map and
  `test_yeast_map`, the `brewtarget-default-data` source is removed, `ref.yeast` gains
  `field_source`, and attenuation, which no hopline page states, becomes Task 6 on the user's
  figures (the user offered to find missing information).
- 2026-10-11 · Approach, Tasks 3–5: Brewline products get their own rows (producer `Brewline`,
  10 rows) instead of being merged into the strain their page says they copy; only the two 2 g
  packs join their 12 g product (`PACK_SIZES`). 111 → 119 rows, dry 73 → 81; `SAME_STRAIN`
  replaced by `PACK_SIZES`, `test_brewline_pack_size` added — the user chose "Separate rows".
  Also decided: non-beer yeasts skipped, M20 loaded with its data-block figures (mismatch in the
  report), attenuation supplied by the user per strain with its source (Task 6).
- 2026-10-11 · Approach, Task 6: attenuation now comes from the sources the user named per
  producer (YeastFlow and Lallemand catalogues, Fermentis and Mangrove Jack's data sheets linked
  from hopline plus Fermentis' T-58 page, the Brewline catalogue PDF, and Brewfather figures the
  user gave for 8 Gozdawa strains), each its own `ref.source` row, instead of a `user-supplied`
  map — the user supplied the sources when approving the plan. Norse Nectar and YeasterBunny get
  no attenuation source ("we can skipp norse nectar", "leave out the yeasterbunny"); read as: still
  loaded, attenuation `NULL`. Gozdawa W-34/70 has no figure and stays `NULL`. Single figures are
  stored as `[a,a]`. The user also confirmed the 2 g packs join their 12 g product.
- 2026-10-11 · Task 1: `details` is added to the product records in the `--yeasts` fetch, not
  returned by `product_page` — malt pages' long descriptions hold a header-less table that
  `table_dict` rejects, so putting it in `product_page` would break the malt fetch. Labels end
  at the next `<br`, `</p>` or `<strong>` (not only `</p>`): many yeast descriptions separate
  their lines with `<br />`. `div_content` returns the content after the opening tag (the
  spec-table output is unchanged, 8 malt and hop pages compared). Measured label coverage with
  this rule: `Ideális hőmérséklet` 123, `Ajánlott sörtípusok` 125, `Adagolás` 128; two pages
  split the temperature label oddly (M54 `302220-H` → `Ideális hőmérséklet: 1` = `8 - 20 °C`,
  M84 `302250-H` → `Erjesztési hőmérséklet`), left raw for Task 5's report to handle.
- 2026-10-11 · Task 5: the report needs to know which strain each Brewline page copies, so
  `loaders/yeast_products.py` gains `BREWLINE_COPIES` (8 Brewline SKUs → the copied strains'
  SKUs; German Lager → SafLager W-34/70 `301100`, U.S. West Coast Ale → US-05 and BRY-97),
  used by the report only. The temperature comparison reads the description's leading figure
  (the Norse Nectar and some Gozdawa lines carry a note after it) from `Ideális hőmérséklet`,
  M84's `Erjesztési hőmérséklet` and M54's split label (`"1" + "8 - 20 °C"`): 125 pages have
  both, 23 disagree (the plan said 121 with both; the 23 / 9 / 5 disagreements match).
- 2026-10-11 · Task 6: three hopline Fermentis links point to another strain's data sheet
  (BE-256 → S-189, S-33 → T-58, BR-8 → W-34/70), so those strains are read from their own
  fermentis.com product page (box "Apparent attenuation"), like T-58; Mangrove Jack's M20
  (hopline links M15's page), M47 (link 404) and M84 (link is the Yeast Range booklet) are read
  from their own page in that booklet; Lallemand figures come from the catalogue's product pages
  (the listing itself shows none), Suava's from the data sheet linked there, since its page has
  words only; YF-107 McGyver from its page under yeastflow.com/our-strains/ although the index
  now lists YF-118 instead. Result: 84 entries, not 100. Brewline gets none: its catalogue PDF
  lists only 500 g strains (ORIGIN AmeriK, CeltiK, Pop Ale, Rock Ale, Folk Ale, Classic Lager,
  Hip-Hop Lager, Jazz Sour, E2F), none matching hopline's 10 Brewline products (question to the
  user). The `brewline-catalogue` source row is added anyway, as the plan says. The report
  gives a reason for each yeast without attenuation (a missing reason raises) and the count per
  source. Task 4's `SafBrew BR-8` and `M36 Liberty Bell Ale` were checked on fermentis.com and
  mangrovejacks.com: both names are right, no change.
- 2026-10-11 · Task 6: the user gave Brewfather figures for 8 Brewline products, loaded as `[a,a]`
  under `brewfather` like the Gozdawa ones; "german wheat" is taken as Bajor Búza `302170`
  (noted in the report); Abbey Monk Ale and Pure Hornindal got none and stay `NULL`. The
  `brewline-catalogue` source, now used by no yeast, is removed from `011_ref_sources.sql` and
  deleted while nothing references it (16 sources). YF-666's printed `800-100` is stored as
  `[80,100]` with source `user-supplied`, as the user confirmed ("Use 80–100"), the printed text
  kept. 84 → 93 entries; 26 yeasts without attenuation.
- 2026-10-11 · Files: `docs/RECIPE-ROADMAP.md` added — review finding 1: it still named
  Brewtarget as the yeast source and D8 as open; it now names hopline's yeasts with attenuation
  from the makers' sources and Brewfather, and lists D8 as decided, as PROJECT.md does (the user
  chose to update it in this work).
