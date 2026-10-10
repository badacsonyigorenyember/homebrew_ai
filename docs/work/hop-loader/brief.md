# Hop loader (hopline.hu hops)

Status: approved
Slug: hop-loader · Branch: hop-loader

## Why
`ref.hop` is empty (0 rows, checked 2026-10-10), so the recipe pipeline has no hops to choose
from (step 8) and no alpha acids for IBU. The draft plan merged three JSON files of unknown
provenance (`hops.json`, `hops.hopslist.json`, Brewtarget), which are not in `pending/` any more.
The user wants the same approach as the malts instead: the hops hopline.hu sells, with their
figures, so the catalogue matches what can actually be bought.

## Goal
`ref.hop` holds one row per hop listed under
[hopline.hu › Alapanyagok › Komlók](https://www.hopline.hu/alapanyagok/komlok): 85 varieties
plus 5 LUPOMAX products, 90 rows. Origin, purpose and acid/oil ranges come from hopline's pages
only, each field's source recorded. The loader can be re-run without duplicates.

## Measured on 2026-10-10 (read-only fetch into the scratchpad, 1 request per second)
- The list is `…/komlok/osszes-komlo`, 6 pages, **106 products**. These are **85 varieties**,
  **5 LUPOMAX** products (Amarillo, Azacca, Citra, Mosaic, Huell Melon) and 16 extra pack sizes
  of a variety already listed (1 kg, 50 g, 30 g).
- SKUs are not all numeric (`200020-cs`, `200712-masolata-1`), so the malt fetcher's link pattern
  finds only 28 of the 106. The fetcher needs a small change.
- Each product page has two blocks of figures:
  - a **spec table** (`Alfa-sav`, `Béta-sav`, `Co-Humolone`, `Olaj tartalom`, as ranges like
    `10-15 %`, single values, `~ 18.5 %` or `? %`), plus `Felhasználás` (beer styles) and
    `Aroma` (descriptors). Alpha found on 102 pages, beta 81, co-humulone 89, oil 85; layout varies.
  - a **data block** (`Adatok`): `Címkék` (tags), `Kiszerelés` (pack), `Évjárat` (crop year),
    `Ország` (105 of 106), a second `Alfasav` range (93 pages) and `Komló aroma`.
- The two alpha ranges disagree on about 70 pages (Citra 10–15 vs 11–13; Southern Star 12–14 vs
  15.5–18.5).
- Pack-size pages of one variety carry the same figures, except Nectaron (100 g: alpha 9.5–11.5;
  50 g and 30 g: 9.5–13).
- Pages carrying another hop's content: **Delta 1kg** (tags, text and figures are Falconer's
  Flight) and **Lotus 1kg** (tags and text are Taurus). **Mosaic LUPOMAX** repeats the Mosaic
  pellet figures (alpha 11.5–13.5) rather than LUPOMAX's own. **Sterling 1kg** shows only `?`.
- Purpose: hopline has subcategories *Aroma komlók* (101), *Keserű komló* (60) and *Kettős
  felhasználású komló* (56), overlapping. The page tags (`aroma`, `keserű`) are missing on 20 pages.
- Countries are Hungarian names: USA, Németország, Új-Zéland, Anglia, Csehország, Dél-Afrika,
  Szlovénia, Ausztrália, Franciaország, Japán. Dolcita has none.
- `ref.source` still has the unused `hops-json` and `hopslist` rows (0 ingredients reference
  them). `brewtarget-default-data` stays: `yeast-loader` uses it.

## Scope
In:
- A fetcher for the hopline hop list and product pages, writing the raw page facts to
  `shared/rag-files/pending/hopline_hops.json` (not committed).
- An explicit, committed map: every hopline SKU → a hop (with its clean name) or, for an extra
  pack size, the hop it belongs to. An unknown SKU stops the load.
- LUPOMAX products as their own hops (`Citra LUPOMAX` …), with the figures their pages show.
- Parsing and loading into `ref.ingredient` (kind `hop`) + `ref.hop`, with `field_source`.
- A `hopline-hops` source row; removing the unused `hops-json` and `hopslist` rows.
- A short report (`docs/work/hop-loader/report.md`) listing pages whose figures were not used
  or disagree.

Out:
- `hops.json`, `hops.hopslist.json` and Brewtarget hop data (no longer used for hops).
- Grower data sheets (Yakima Chief, BarthHaas, Hopsteiner, NZ Hops …) as a second source
  (user decision 2026-10-10: hopline only). Can be added later the way the malt catalogues were.
- Individual oils (`oils_pct`: myrcene, humulene …): hopline doesn't give them, they stay `NULL`.
- A co-humulone column: co-humulone is kept in `raw` only.
- Flavour tagging of the aroma descriptors (P3). They are kept in `raw`.
- Stock, price and crop year as columns (kept in `raw` only).

## Requirements
R1. Every product on hopline's hop list maps to exactly one hop; a SKU not in the map stops the
    load.
R2. One `ref.hop` row per hop. Pack sizes of the same variety become one row, with figures from
    one chosen page (the 100 g page where there is one), and every page of it kept in `raw`.
    LUPOMAX products are separate hops (`<Variety> LUPOMAX`), never merged with the pellet.
R3. `alpha_pct`, `beta_pct` and `total_oil_ml_100g` are `numrange`s parsed from the page's spec
    table (a single value `v` becomes `[v,v]`, `~ v` is read as `v`); `alpha_pct` falls back to
    the data block's `Alfasav` only when the spec table has none. `?`, `-` or a missing figure
    stays `NULL`, never 0.
R4. `origins` holds ISO 3166 alpha-2 codes mapped from hopline's country name (Anglia → `GB`);
    an unknown country name stops the load; no country → `NULL`.
R5. `purpose` is `aroma`, `bittering` or `dual`, derived by a fixed rule from hopline's own
    classification (subcategories); a hop hopline doesn't classify stays `NULL`.
R6. `field_source` names the source of every filled field; `raw` keeps the page facts,
    including co-humulone, style use, aroma descriptors, crop year and the other alpha range.
R7. Delta and Lotus, whose pages carry Falconer's Flight / Taurus content, are loaded with
    name, origin and purpose but `NULL` acid and oil figures, and listed in the report (their
    page facts stay in `raw`).
R8. Loading twice gives the same rows; nothing is merged on a guess
    (different names stay different hops).
R9. No LLM is used; parsing and the purpose rule are tested code.

## Constraints
- CLAUDE.md: DB changes are `.sql` files applied with `psql` as `postgres`; the Supabase MCP is
  read-only. No git worktree. Brewing maths is tested code.
- PROJECT.md §6.1 and §6.3: structured data stays exact, unknown stays `NULL`. §6.8 readable over
  optimal: an explicit SKU map, not generic machinery.
- Fetching: robots.txt only disallows `/shop_ajax/*`; one request per second, a `User-Agent`
  naming the project, as in `loaders/fetch_hopline.py`.
- Source files are never committed (`shared/rag-files/pending/` is git-ignored).
- Global review focus 3 (`fill-ref/README.md`): `Saaz` and `Saaz (US)`-style names are never
  merged automatically.

## Assumptions
- hopline's `Olaj tartalom … %` is total oil in mL/100 g (the usual unit; the values 0.4–4.6
  fit it) *(unverified)*.
- The spec-table figures describe the variety, not one lot *(unverified)*.
- Hop varieties have no producer: `ref.ingredient.producer` stays `''` *(unverified that P2 needs
  none)*.
- The hopline list is the same when the plan runs as on 2026-10-10 (106 products); the plan
  stops and reports if it differs.

## Acceptance criteria
A1. `hopline_hops.json` holds 106 products (or the plan stops and reports), every name set (R1).
A2. A test shows the map has 90 hops, every extra pack size points at one of them, and no two
    hop names share a `name_key`; a one-off check shows every SKU in the fetched file is in the
    map (R1, R2, R8).
A3. After loading twice, `select count(*) from ref.hop` is 90 both times, 5 of them named
    `… LUPOMAX` (R2, R8).
A4. Tests on inline fixtures cover: range, single, `~ v`, `? %` and decimal-comma figures (R3);
    country → ISO and unknown country raises (R4); the purpose rule (R5).
A5. The Citra row reads `origins {US}`, `purpose dual`, `alpha_pct [10,15]`, and `field_source`
    names `hopline-hops` for each filled field (R3–R6).
A6. `select count(*) from ref.hop where alpha_pct is null` is recorded; the rows it lists are
    Delta, Lotus and hops with no alpha on their page (Sterling) (R3, R7).
A7. `ref.source` has `hopline-hops` and no `hops-json` / `hopslist` (R6).
A8. `report.md` lists Delta and Lotus, the pack-size disagreements (Nectaron), and the LUPOMAX
    pages whose figures equal the pellet page's (Mosaic) (R2, R7).
A9. `grep -ri "ollama\|llm" loaders/hops.py` finds nothing; the suite passes (R9).

## Decisions (user, 2026-10-10)
1. Figures from hopline only; no second source in this work.
2. Alpha from the spec table; the data block's `Alfasav` only when the table has none. Both in `raw`.
3. Delta and Lotus: loaded, acid and oil figures `NULL`, listed in the report.
4. LUPOMAX: 5 separate hops with the figures their pages show.

## Open questions
None.

## Deviations
- 2026-10-10 · whole brief: input changed from three hop JSON files (`hops.json`,
  `hops.hopslist.json`, Brewtarget) to hopline.hu's hop pages — the user asked for the malt
  approach with hopline's hop data.
