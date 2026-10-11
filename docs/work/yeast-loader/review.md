# Review: yeast-loader

Diff: main...yeast-loader at 650a5e8  ·  Verdict: ready for testing

No brief; checked against `plan.md` (6 tasks, all ticked, 6 Deviations) and the user decisions
listed in it.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | docs/RECIPE-ROADMAP.md:52, :240, :290, :307 | The roadmap still names Brewtarget default data as the yeast source (`ref.yeast` ← "Brewtarget data", P1 "Brewtarget yeasts", D8 = Brewtarget). PROJECT.md §7 closes D8 for hopline, and DATABASE.md and FILL-REF-README.md were updated, but this file was not in the plan's Files table. | A reader of the roadmap gets the old source and an open D8 that PROJECT.md says is decided. The user decides whether to update it in this work. |
| 2 | note | tests/test_yeasts.py:216 | No test checks that each `ATTENUATION` range matches its `printed` text. I checked all 93 entries one-off (numbers in `printed` vs `attenuation_pct`, YF-666 aside): all match. | Nothing wrong now. A typo in a future hand-entered figure would not be caught by the suite. |
| 3 | note | db/011_ref_sources.sql:115-119 | The `brewline-catalogue` delete targets a row that `main` never had; it only cleans the running DB, where an earlier Task 6 apply added it. Guarded by `not exists`, so it is harmless. Measured: 16 sources, no `brewline-catalogue`. | None. |

## What was checked

- **Plan:** each task's code matches its text, or the change is recorded in Deviations (labels
  ending at `<br`, `details` added in the yeast fetch only, `BREWLINE_COPIES`, the source
  changes for Fermentis, Mangrove Jack's and Lallemand, Brewfather figures for Brewline,
  YF-666 as `user-supplied`, `brewline-catalogue` removed).
- **User decisions:** Brewline has 10 rows of its own and the 2 g packs are in `raw` of their
  12 g product; 8 non-beer SKUs are in `SKIPPED` with reasons; M20 uses data-block figures and the
  report flags its description; Norse Nectar (17) and YeasterBunny (1) are loaded with
  attenuation `NULL`; Abbey Monk Ale and Pure Hornindal stay `NULL`; Bajor Búza is `brewfather`
  `[73,73]`; YF-666 is `[80,100]` `user-supplied` with `printed` `800-100`.
- **Correctness:** `parse_range` raises on any unit other than the one asked for (°F included),
  and a single figure becomes `[a,a]`; tolerance takes the range top; unknown flocculation words
  and style families raise; an SKU in no map raises in `build`; figures come from the main page
  only. No data-block field holds `""` or `-` on the fetched pages, so the data-block-first rule
  never hides a description value (checked against `hopline_yeasts.json`).
- **DB, measured:** `ref.yeast` 119 rows, temp 119, flocculation 113, alcohol 114,
  attenuation 93; dry 81, liquid 38; attenuation by source brewfather 16, fermentis-datasheets 12,
  lallemand-catalogue 17, mangrovejacks-datasheets 13, user-supplied 1, yeastflow-catalogue 34,
  none 26; type ale 75, kveik 20, lager 17, brett 2, NULL 5; 119 `ingredient` rows of kind
  `yeast`; US-05 `[18,28]` °C, attenuation `[78,82]`.
- **Report:** `report(hopline_yeasts.json)` regenerates `report.md` byte for byte.
- **Tests:** 46 pass (`test_yeasts.py` 10, `test_fetch_hopline.py` 6); each critical behaviour in
  the plan's table has its named test.
- **Safety:** DB changes are in `db/010` and `db/011`; no secrets in the diff; no
  `shared/rag-files/pending/` file committed; no LLM call in the yeast code.
- **Records:** PROJECT.md §4, §5, §7 (D8 removed with its *why* in §5) and §8 updated;
  DATABASE.md and FILL-REF-README.md updated; 8 commits, each one line with no body.

## Re-review 2026-10-11

Diff: d30ba59..yeast-loader at 28c4cf0 (commits 7c310c6, c8fd791, 28c4cf0)  ·  Verdict: ready for testing

Checked against the user's change request, "Don´t use Hungarian words, instead translate
everything to english. Like Bajor búza", read as: every value written outside `raw` and the
printed provenance text is English; parser keys that must match the Hungarian pages may stay.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | note | docs/work/yeast-loader/report.md:15, :72-73 | The report quotes page values as printed, under a line that says so. Flocculation words get the English schema value and the Norse Nectar note is explained, but two quoted values have no English gloss: style family `'Belga Ale'` (Abbey Monk Ale vs BE-256) and Porter&Kvass's `(max tartomány: 16 - 32 °C)` ("max range"). | Within the scope given (quoted page text). The user decides whether the report should gloss these too. |
| 2 | note | docs/work/yeast-loader/verification.md:155 | Verification was written before 28c4cf0: it names "Bajor Búza" and counts 46 tests. | Verification has to be re-run for the change (plan `Stage: review`). |

### What was checked

- **Earlier findings:** #1 fixed in 7c310c6 (RECIPE-ROADMAP.md names hopline as the yeast
  source and lists D8 as decided, as PROJECT.md does). #2 and #3 unchanged, still notes.
- **Request met in the DB, measured:** a regex over `name`, `producer`, `product_id`, `type`,
  `form`, `flocculation` and `field_source` of all 119 yeasts finds no Hungarian letter
  (áéíóőúű) or Hungarian page word; the only non-ASCII names are `Köln`, `YF-110
  Kölschermeister`, `YF-201 St. Cölibate`, `YF-205 Holy Cölibate` (German / the maker's
  spelling). All 119 names read as English or brand names. `field_source` keys and values
  are English column names and source slugs. The 7 yeast-related `ref.source` rows have
  English titles and notes; `hopline-yeasts` names its pages by URL. No `ref.ingredient_tag`
  rows for yeasts.
- **Rename:** Brewline `302170` is id 1819 `Bavarian Wheat` / `bavarianwheat`, `[73,73]`
  `brewfather`; no `bajorbuza` row is left. The `db/011` update is guarded by `not exists`, so
  re-applying it is a no-op, and on a fresh DB it matches nothing and the loader creates
  `Bavarian Wheat` directly. `upsert_ingredient` keys on `(kind, producer_key, name_key)`, so a
  loader run after the rename updates row 1819 instead of adding a 120th.
- **Counts:** 119 rows; temp 119, flocculation 113, alcohol 114, attenuation 93, as before.
- **Code:** `title()` in the report uses the English `YEASTS` name (a 2 g pack: its 12 g
  product's), falls back to hopline's name only for skipped products; `COMPARED_PARAMS` keeps
  the Hungarian keys for matching and prints English labels. `TYPES` keys and `FLOCCULATION`
  keys stay Hungarian (parser keys), their values are English.
- **Report:** `report(hopline_yeasts.json)` regenerates `report.md` byte for byte.
- **Tests:** 47 pass. `test_no_hungarian_outside_raw` checks every `YEASTS` name, producer and
  product id, every `TYPES` and `FLOCCULATION` value, and a built yeast's columns and
  `field_source`; it asserts its own detector flags "Bajor Búza" and not "Köln", so it fails if
  the name is put back.
- **Scope:** only the files the request touches; plan Files table, Deviations (dated entry with
  the user's words) and the critical-behaviour table updated. No secrets; DB change is in a
  `.sql` file.
- **Records:** PROJECT.md §8 has a dated entry with the measured counts and test result;
  28c4cf0 is one line with no body.
