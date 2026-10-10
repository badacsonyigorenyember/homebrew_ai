# Hop loader (hopline.hu hops) — implementation plan

Stage: implementing
Brief: [brief.md](brief.md) · Index: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a item 5)
Branch: hop-loader

## Approach

**Which hops:** every product on [hopline.hu › Komlók › Összes komló](https://www.hopline.hu/alapanyagok/komlok/osszes-komlo):
106 products (measured 2026-10-10) = 85 varieties + 5 LUPOMAX products + 16 extra pack sizes.
That gives **90 `ref.hop` rows**. LUPOMAX products are their own hops (`Citra LUPOMAX`), never
merged with the pellet. The three old JSON sources are not used (user decision, see brief).

**Where the figures come from:** hopline only, source slug `hopline-hops`. Each product page has
an HTML spec table (`<th>` Alfa-sav, Béta-sav, Co-Humolone, Olaj tartalom; `<td>` cells, which
start with a duplicate `<span class="mobile-head">` label) and a data block of
`artdet__param-title` / `artdet__param-value` pairs (Címkék, Kiszerelés, Évjárat, Ország,
Alfasav, Komló aroma). Measured on all 106 pages: every table parses, header and cell counts
always match. `alpha_pct` comes from the table, and from the data block's `Alfasav` only when
the table has none. Purpose comes from hopline's three subcategory listings.

**Pieces:**
1. `loaders/fetch_hopline.py` gets a `--hops` mode: it saves each hop page's raw facts (name,
   spec text, spec table, data block) plus the SKUs of the three subcategories to
   `shared/rag-files/pending/hopline_hops.json`. No interpretation. The malt mode is unchanged.
2. `loaders/hop_products.py` is the committed, explicit map: main SKU → hop name (90), extra
   pack-size SKU → main SKU (16), and the 2 hops whose page shows another hop's content (Delta,
   Lotus) → reason. An SKU in none raises.
3. `loaders/hops.py` parses figures, origin and purpose (pure, unit tested), builds one `Hop`
   per main SKU, writes `docs/work/hop-loader/report.md`, and upserts `ref.ingredient` (kind
   `hop`, producer `''`) + `ref.hop`.

**Rules:** unknown stays `NULL`, never 0; a figure format the parser doesn't know raises (so a
new format gets a decision, not a silent `NULL`); an unknown country raises; the loader is
idempotent; source files are never committed; nothing calls an LLM. Total oil is stored as
mL/100 g (hopline writes `%` or `ml`; brief assumption, unverified).

**Needs:** network access to hopline.hu (robots.txt only disallows `/shop_ajax/*`).

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `loaders/fetch_hopline.py` | changed | non-numeric SKUs, `spec_table`, `params`, `listing`, `--hops` mode |
| `tests/test_fetch_hopline.py` | changed | 2 new tests |
| `db/011_ref_sources.sql` | changed | `hopline-hops` source; remove unused `hops-json`, `hopslist` |
| `loaders/hop_products.py` | new | `HOPS` (90), `PACK_SIZES` (16), `NULL_FIGURES` (2) |
| `loaders/hops.py` | new | `Hop`, `parse_figure`, `ORIGIN_CODES`, `origin_codes`, `purpose_of`, `make_hop`, `build`, `report`, `load`, CLI |
| `tests/test_hops.py` | new | 8 tests on inline fixtures |
| `docs/work/hop-loader/report.md` | new | hops loaded without figures, pack-size disagreements, LUPOMAX pages equal to the pellet page |
| `docs/work/fill-ref/README.md` | changed | item 5 and its source rows describe the new input (in the plan commit) |
| `PROJECT.md` | changed | §5 hop row, §4 scripts row, §8 |

Not committed (in `shared/rag-files/pending/`, git-ignored): `hopline_hops.json`.

## Tasks

### Task 1: Fetch the hopline hop pages
Why: hopline decides which hops are loaded; this captures its pages as raw data (R1, A1).
- [x] In `loaders/fetch_hopline.py` (standard library only, as now):
  - `LINK`: accept any SKU, `data-sku="([^"]+)"` (hop SKUs look like `200020-cs`,
    `200712-masolata-1`; with `\d+` only 28 of 106 are found).
  - `spec_table(html: str) -> dict[str, str] | None`: the first `<table>` inside
    `artdet__short-descripton-content`; `<th>` texts as keys, `<td>` texts as values, in order,
    each `<span class="mobile-head">…</span>` removed first, text through `visible_text`.
    `None` when there is no table; `ValueError` when the header and cell counts differ.
  - `params(html: str) -> dict[str, str]`: every `artdet__param-title` → the following
    `artdet__param-value`, both through `visible_text`.
  - `product_page` also returns `table` and `params` (the malt output only gains two keys).
  - `listing(first_url: str) -> list[tuple[str, str]]`: the paging loop now in `main`
    (`first_url`, then `first_url,2`, `,3`, … until a page adds no new SKU), reused for every
    listing.
  - CLI: `python -m loaders.fetch_hopline OUT.json` stays the malt run. With `--hops` it reads
    `HOP_LISTING_URL = …/alapanyagok/komlok/osszes-komlo` and the three category listings
    `HOP_CATEGORIES = {"aroma": …/komlok/aroma-komlok, "bittering": …/komlok/keseru-komlo, "dual": …/komlok/kettos-felhasznalasu-komlo}`,
    and writes `{"fetched", "listing", "categories": {"aroma": [sku…], "bittering": […], "dual": […]}, "products": [{"sku", "url", "name", "spec", "table", "params"}, …]}`.
    One request per second, the `User-Agent` names the project (make it say "hopline loader",
    not "malt loader"), never `/shop_ajax/`.
- [x] Write the tests first (`tests/test_fetch_hopline.py`, inline HTML) and see them fail:
  - `test_listing_links_any_sku`: anchors with `data-sku="200020-cs"` and
    `data-sku="200712-masolata-1"` → both pairs, in order.
  - `test_spec_table_and_params`: the East Kent Golding table shape
    (`<th>` Alfa-sav, Béta-sav, Co-Humolone, Olaj tartalom; first `<td>` `5-6 %`, the others
    starting with a `mobile-head` span, e.g. `<span class="mobile-head">Béta-sav</span><span>2-3 %</span>`)
    → `{"Alfa-sav": "5-6 %", "Béta-sav": "2-3 %", "Co-Humolone": "29 %", "Olaj tartalom": "0,85 %"}`;
    a data block with `Évjárat`/`2025` and `Ország`/`USA` pairs → `{"Évjárat": "2025", "Ország": "USA"}`.
- [x] Implement; `.venv/bin/python -m pytest tests/test_fetch_hopline.py -v` → 4 passed; suite passes.
- [x] Run `.venv/bin/python -m loaders.fetch_hopline --hops shared/rag-files/pending/hopline_hops.json`.
  Expect 106 products, every `name` set, every `table` set, categories aroma 101, bittering 60,
  dual 56. If the product count is not 106, stop and report (the shop changed since 2026-10-10).
Done when: 4 passed and the JSON holds 106 products.
Commit: `Fetch hopline hop pages`

### Task 2: Hop source row
Why: every hop row needs its real source; the old hop sources are unused (R6, A7).
- [x] `db/011_ref_sources.sql`: add
  `('hopline-hops', 'Hopline hop product pages', 'website, fetched <the "fetched" date in hopline_hops.json>', 'Hopline', null, 'https://www.hopline.hu/alapanyagok/komlok/osszes-komlo', null)`,
  and remove the `hops-json` and `hopslist` rows from the insert list. Under the corrections at
  the end add (0 ingredients reference them, measured 2026-10-10):
  `delete from ref.source s where s.slug in ('hops-json', 'hopslist') and not exists (select 1 from ref.ingredient i where i.source_id = s.id);`
  Leave `brewtarget-default-data` as it is (`yeast-loader` uses it).
- [x] Apply twice as `postgres`:
  `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/011_ref_sources.sql`
- [x] Check after each apply: `select slug from ref.source order by id` → 10 rows, includes
  `hopline-hops`, no `hops-json` / `hopslist`. Suite still passes.
Done when: the file applies twice without error and gives those rows.
Commit: `Add hopline hop source`

### Task 3: Parse a hop (pure, no files, no DB)
Why: alpha acids feed IBU in P2; a wrong figure or a silent 0 corrupts recipes (R3–R6, R9, A4, A5).
- [x] In `loaders/hops.py`:
  - `@dataclass Hop(name, origins: list[str] | None, purpose: str | None, alpha_pct, beta_pct, total_oil_ml_100g, field_source: dict[str, str], raw: dict)`.
  - `parse_figure(text: str | None) -> Range | None`: decimal comma → point, a leading `~` and
    surrounding space dropped; then `a`, `a-b`, `a - b` or `a – b` followed by `%` or `ml`
    (with or without a space) → `to_range(a, b)` (single → `[a,a]`); `None`, `""`, `"%"`,
    `"? %"`, `"- %"` → `None`; anything else → `ValueError` naming the text.
  - `ORIGIN_CODES: dict[str, str]`, hopline's country names → ISO 3166 alpha-2:
    `USA`→`US`, `Németország`→`DE`, `Új-Zéland`→`NZ`, `Anglia`→`GB`, `Csehország`→`CZ`,
    `Dél-Afrika`→`ZA`, `Szlovénia`→`SI`, `Ausztrália`→`AU`, `Franciaország`→`FR`, `Japán`→`JP`
    (every name measured on 2026-10-10). `origin_codes(country: str | None) -> list[str] | None`:
    `None` → `None`; unknown name → `ValueError` naming it.
  - `purpose_of(skus: list[str], categories: dict[str, list[str]]) -> str | None`, over all SKUs
    of one hop: in `dual`, or in both `aroma` and `bittering` → `"dual"`; only `bittering` →
    `"bittering"`; only `aroma` → `"aroma"`; none → `None`.
  - `make_hop(name: str, main: dict, extras: list[dict], categories: dict, null_figures: bool = False) -> Hop`:
    `main` and `extras` are product dicts as in `hopline_hops.json`. Figures come from `main`'s
    table: `alpha_pct` ← `Alfa-sav`, else `params["Alfasav"]`; `beta_pct` ← `Béta-sav`;
    `total_oil_ml_100g` ← `Olaj tartalom`. With `null_figures` all three stay `None`.
    `origins` ← `origin_codes(main["params"].get("Ország"))`; `purpose` ← `purpose_of` over
    `main` and `extras`. `field_source` = `"hopline-hops"` for each of those five fields that has
    a value, nothing else. `raw = {"hopline-hops": {sku: product, …}}` for `main` and every extra.
- [x] Write the tests first (`tests/test_hops.py`) and see them fail on import:
  - `test_parse_figure`: `"10-15 %"`→`[10,15]`, `"9.5 - 11.5 %"`→`[9.5,11.5]`,
    `"5.8-6.3%"`→`[5.8,6.3]`, `"0,85 %"`→`[0.85,0.85]`, `"~ 18.5 %"`→`[18.5,18.5]`,
    `"16,5%"`→`[16.5,16.5]`, `"1.6-2.5 ml"`→`[1.6,2.5]`, `"2,5 – 5 %"`→`[2.5,5]`,
    `"? %"`/`"%"`/`""`/`None`→`None`, `"lots"`→`ValueError`. Compare `Range(D(…), D(…), "[]")`.
  - `test_origin_codes`: `"Anglia"`→`["GB"]`, `"USA"`→`["US"]`, `None`→`None`, `"Mars"`→`ValueError`.
  - `test_purpose_of`: in `dual` → dual; in `aroma` and `bittering` → dual; only `bittering` →
    bittering; only `aroma` → aroma; none → `None`; the 100 g SKU only in `aroma` and its 1 kg
    SKU only in `bittering` → dual.
  - `test_citra`: Citra 100g (`200750-cs`, table `10-15 %`, `3-4.5 %`, `20-35 %`, `1.5-3 %`,
    params `Ország: USA`, `Alfasav: 11 – 13 %`, in `aroma`, `bittering` and `dual`) →
    `alpha_pct == [10,15]`, `beta_pct == [3,4.5]`, `total_oil_ml_100g == [1.5,3]`,
    `origins == ["US"]`, `purpose == "dual"`, `field_source` has exactly the 5 fields, all
    `"hopline-hops"`, `raw == {"hopline-hops": {"200750-cs": <the product>}}`.
  - `test_alpha_falls_back_to_data_block`: table `Alfa-sav: "? %"`, params `Alfasav: "11 – 13 %"`
    → `alpha_pct == [11,13]`; table `? %` and no `Alfasav` → `None`, not in `field_source`.
  - `test_pack_sizes_and_null_figures`: Nectaron 100 g (`9.5 - 11.5 %`) as `main`, 50 g and
    30 g (`9.5 - 13 %`) as extras → `alpha_pct == [9.5,11.5]`, `set(raw["hopline-hops"])` has
    all 3 SKUs; Delta (`200269`, table `9.5-12 %`) with `null_figures=True` → all three figures
    `None`, `origins` and `purpose` still set.
- [x] Implement; `.venv/bin/python -m pytest tests/test_hops.py -v` → 6 passed; suite passes.
Done when: 6 passed, suite green.
Commit: `Parse hopline hop pages`

### Task 4: The hopline SKU → hop map
Why: the explicit map decides what each product is, so nothing is merged on a guess (R1, R2, R7, R8, A2).
- [x] `loaders/hop_products.py`, one line per SKU with hopline's product name as a comment:
  - `HOPS: dict[str, str]`: main SKU → hop name, 90 entries. The main SKU is the `-cs` (100 g)
    page where the variety has one, else its only page. The name is hopline's without
    "komló", the pack size, an alpha in the name and ™ (`Hallertau Opal komló 1kg  9.00%` →
    `Hallertau Opal`, `Waimea™ komló 30g` → `Waimea`), with hopline's misspellings fixed:
    `Colombus` → `Columbus`, `Comet koml?` → `Comet`, `Loral koml?` → `Loral`,
    `Brewer&#039;s Gold` → `Brewer's Gold`. LUPOMAX: `Amarillo LUPOMAX`, `Azacca LUPOMAX`,
    `Citra LUPOMAX`, `Mosaic LUPOMAX`, `Huell Melon LUPOMAX` (`200810`; its URL says
    mandarina-bavaria, its page is Huell Melon). `Saphir` is `200550-cs` (URL says sabro, page is
    Saphir). Delta is `200269`, Lotus `200669` (their URLs say Falconer's Flight / Taurus).
  - `PACK_SIZES: dict[str, str]`: extra SKU → main SKU, 16 entries: El Dorado `200259`,
    Hallertau Hersbrücker `200329`, Hallertau Tradition `200349`, Magnum `200429`, Mandarina
    Bavaria `200439`, Nectaron `200880` and `200872`, Northern Brewer `200483`, Riwaka `200899`,
    Styrian Golding `200639`, Waimea `200712-masolata-1`, Willamette `200749`, Hallertau Callista
    `200999`, Hallertau Opal `200989`, Southern Star `200609`, Zappa `200779`.
  - `NULL_FIGURES: dict[str, str]`: `200269` → "page shows Falconer's Flight (tags, text and
    figures)", `200669` → "page shows Taurus (tags and text)". User decision 2026-10-10.
- [x] Add `test_hop_map` to `tests/test_hops.py`: 90 `HOPS`, 16 `PACK_SIZES`, every
  `PACK_SIZES` value is in `HOPS`, no SKU in both, every `NULL_FIGURES` key is in `HOPS`, 5 names
  end in ` LUPOMAX`, and `name_key(name)` is unique across `HOPS` (two names colliding would make
  the upsert overwrite one hop with another).
- [x] Check against the file (a one-off command, not a test): every SKU in `hopline_hops.json`
  is in `HOPS` or `PACK_SIZES`, and every `HOPS` SKU is in the file.
- [x] Suite passes (7 in `test_hops.py`).
Done when: the map covers all 106 SKUs.
Commit: `Map hopline hop products`

### Task 5: Load hops into `ref` and write the report
Why: the hop catalogue the recipe steps choose from (R2, R8, A3, A5, A6, A8, A9).
- [ ] In `loaders/hops.py` add:
  - `build(hopline: dict) -> list[Hop]`: an SKU in neither `HOPS` nor `PACK_SIZES` →
    `ValueError` naming it; for each `HOPS` SKU, `make_hop(name, main, its PACK_SIZES extras,
    hopline["categories"], null_figures=sku in NULL_FIGURES)`.
  - `report(hopline: dict) -> str`: Markdown with three lists: hops loaded without figures
    (`NULL_FIGURES` with reasons, and any hop whose alpha is `None`); pack sizes whose table
    differs from the main page's (expected: Nectaron); LUPOMAX pages whose table equals the
    pellet's (expected: Amarillo, Mosaic).
  - `load(conn, hops) -> int`: `upsert_ingredient(conn, "hop", name, "", source_id(conn, "hopline-hops"), raw)`,
    then upsert `ref.hop` on `ingredient_id` (`origins`, `purpose`, `alpha_pct`, `beta_pct`,
    `total_oil_ml_100g`, `field_source` as `Jsonb`; `oils_pct` stays `NULL`), one transaction,
    as `loaders/malts.py::load`.
  - CLI `python -m loaders.hops --hopline PATH --report PATH`: builds, loads, writes the report,
    prints the loaded count.
- [ ] Add `test_unknown_sku_raises`: `build` with a product whose SKU is in neither map →
  `ValueError`. Suite passes (8 in `test_hops.py`).
- [ ] Run it twice:
  `.venv/bin/python -m loaders.hops --hopline shared/rag-files/pending/hopline_hops.json --report docs/work/hop-loader/report.md`
- [ ] After each run (expected values measured on the 2026-10-10 pages; record what you get):
  - `select count(*), count(*) filter (where i.name like '% LUPOMAX') from ref.hop h join ref.ingredient i on i.id = h.ingredient_id` → `90|5`.
  - `select purpose, count(*) from ref.hop group by 1 order by 1` → aroma 34, bittering 4,
    dual 51, `NULL` 1 (Enigma).
  - `select i.name from ref.hop h join ref.ingredient i on i.id = h.ingredient_id where h.alpha_pct is null order by 1`
    → Delta, Lotus, Sterling.
  - `select count(*) from ref.hop where origins is null` → 1 (Dolcita).
  - Citra row: `origins {US}`, `purpose dual`, `alpha_pct [10,15]`, `beta_pct [3,4.5]`,
    `total_oil_ml_100g [1.5,3]`, `field_source` as in `test_citra`.
  - `select count(*) from ref.ingredient where kind = 'hop' and source_id <> (select id from ref.source where slug = 'hopline-hops')` → 0.
- [ ] `grep -niE "ollama|llm" loaders/hops.py loaders/hop_products.py` → nothing.
- [ ] PROJECT.md §5: replace the "Hop data (`hops.json`, `hops.hopslist.json`)" part of the row
  with the hopline hop list, ✅ with the measured counts and date (keep `beer_faults.json`
  as ⬜); update the line above the table (what is in `pending/`). §4 scripts row: the hop
  loader, map and `--hops` fetch. §4 database row: `ref.hop` count. §8 entry pointing at
  `report.md`.
Done when: both runs give the same counts and the Citra row matches.
Commit: `Load hopline hops into ref`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every hop SKU is found on the listing, including `-cs` SKUs | `tests/test_fetch_hopline.py::test_listing_links_any_sku` | 1 |
| Spec table read by column, `mobile-head` labels dropped | `tests/test_fetch_hopline.py::test_spec_table_and_params` | 1 |
| Figure formats → ranges; `?` stays `NULL`, never 0; unknown format raises | `tests/test_hops.py::test_parse_figure` | 3 |
| Country → ISO code; unknown country raises | `tests/test_hops.py::test_origin_codes` | 3 |
| Purpose rule from hopline's categories | `tests/test_hops.py::test_purpose_of` | 3 |
| Table wins, data-block alpha only as fallback, `field_source` and `raw` complete | `tests/test_hops.py::test_citra`, `::test_alpha_falls_back_to_data_block` | 3 |
| Pack sizes become one hop with the main page's figures; Delta/Lotus figures stay `NULL` | `tests/test_hops.py::test_pack_sizes_and_null_figures` | 3 |
| Every SKU decided once; no two hops share a name key (no silent merge) | `tests/test_hops.py::test_hop_map` | 4 |
| A new hopline product never loads silently | `tests/test_hops.py::test_unknown_sku_raises` | 5 |
| Re-running doesn't duplicate | load-twice counts | 5 |

## Approved exceptions

## Deviations

- 2026-10-10 · whole plan: rewritten. Input changed from three hop JSON files (`hops.json`,
  `hops.hopslist.json`, Brewtarget, merged with a precedence and a near-duplicate report) to
  hopline.hu's hop pages only — the user asked for the malt approach with hopline's data.
  The precedence question and the near-duplicate report are gone: the explicit SKU map and
  `test_hop_map` replace them. User decisions: hopline only; table alpha first; Delta and Lotus
  loaded with `NULL` figures; LUPOMAX as 5 separate hops with their page figures.
