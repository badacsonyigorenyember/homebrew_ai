# Recipe test briefs (P0) — implementation plan

Stage: review
Brief: [brief.md](brief.md)
Branch: test-briefs

## Approach

One TOML file, `evals/recipe_briefs.toml`, holds the 20 briefs as `[[brief]]` tables. TOML,
because a person can review it like a document (comments, multi-line strings, no quoting
noise) and Python 3.12 reads it with the standard library `tomllib`, so no new dependency.
`tests/test_recipe_briefs.py` loads it and checks shape and coverage (R1–R3, R5–R11): one
test per requirement, each failing with the measured count in its message, and a printed
coverage summary (`pytest -s`). The style buckets the test counts (lagers, Belgian,
wheat/sour, hop-forward, stout/porter) are explicit code sets in the test file, readable on
their own (§6.8). The R3 check queries `ref.beer_style` for source `bjcp-2021` through
`loaders.db.connect()`, so that test needs the running stack and fails loudly without it,
instead of trusting codes written from memory. Style ranges never enter the file (R4): the
schema check rejects any key outside the R2 field list. After the briefs are written, the
user reviews all 20 (A5), and only then are PROJECT.md and RECIPE-ROADMAP updated.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `evals/recipe_briefs.toml` | new | the 20 test briefs (R1, R2) |
| `tests/test_recipe_briefs.py` | new | shape, style-code and coverage checks (R12) |
| `PROJECT.md` | changed | §4 Scripts row, §7 D7/D9 notes, §8 entry (R13) |
| `docs/RECIPE-ROADMAP.md` | changed | §8 P0 row done, D7/D9 moved to P3, link to the file (R13) |

## The brief format

Every `[[brief]]` has exactly these keys; empty values are `""`, `[]` or `{}`:

| Key | Type | Holds |
|---|---|---|
| `id` | string | `b01` … `b20`, unique |
| `request` | string | the user's words, English, 1–3 sentences |
| `why` | string | one line: what this brief tests |
| `style` | string | expected best-fit BJCP 2021 code, e.g. `"16B"`: the base style, or the specialty code when the request makes an adjunct a prominent feature (R3) |
| `alt_styles` | list of codes | only where the request is genuinely ambiguous |
| `deviations` | list of `{ kind, what, from }` | `kind` is one of `ingredient`, `number`, `mismatch`, `conflict`; `what` names what deviates, `from` names what it deviates from (e.g. `"16B ingredients"`, `"8B ABV range"`) |
| `stated` | inline table | only numbers the user stated; keys from `batch_l`, `abv`, `og`, `ibu`, `srm` |
| `hints` | list | words from the §7 hint vocabulary: `bitter`, `hoppy`, `juicy`, `dry`, `crisp`, `full`, `chewy`, `malty`, `darker`, `stronger`, `session` |
| `wanted` | list | ingredients the user asked for, generic names |
| `excluded` | list | ingredients the user ruled out |
| `inventory` | list | ingredients the user says they have |
| `guidance` | bool | style guidance on (`true`, default) or off |
| `needs` | table (`[brief.needs]` sub-table) | `{ fermentables = [...], hops = [...], yeast = [...], water_salts = [...] }`, generic names (`"flaked oats"`, `"Saaz"`, `"abbey ale yeast"`) — the four keys are the only allowed ones, which is how R11 is enforced by shape |

The six adjuncts use these exact names in `needs.fermentables`, so the test can count them:
`flaked oats`, `candi sugar`, `flaked corn`, `flaked rice`, `lactose`, `honey`.

## Proposed spread (the user approves it with this plan; wording follows in Task 1)

| id | Style | Tests | Adjunct | Other cases |
|---|---|---|---|---|
| b01 | 21A American IPA | hop-forward, `bitter` | | |
| b02 | 21C Hazy IPA | hop-forward, `juicy`/`hoppy` | flaked oats (typical) | |
| b03 | 16B Oatmeal Stout | `full`/`chewy` | flaked oats (typical) | |
| b04 | 16A Sweet Stout | milk stout | lactose (typical) | |
| b05 | 15B Irish Stout, alt 20C | "4 % imperial stout" | | mismatch; ABV 4 stated |
| b06 | 1B American Lager | lager, `crisp`/`dry` | flaked rice (typical) | |
| b07 | 1C Cream Ale | | flaked corn (typical) | |
| b08 | 5D German Pils | lager, `bitter` | | IBU 50 (range 22–40): number deviation; excludes Saaz; 10 L |
| b09 | 6A Märzen | lager, `malty` | | |
| b10 | 26B Belgian Dubbel | Belgian | candi sugar (typical) | inventory ("I have …") |
| b11 | 25B Saison | Belgian, `dry` + `full`/`chewy` | | conflict: bone dry vs full and chewy |
| b12 | 31B Alternative Sugar Beer, alt 18A | prominent honey makes it a specialty | honey | no deviation |
| b13 | 10A Weissbier | wheat | | 15 L |
| b14 | 23A Berliner Weisse | sour, `session` | | ABV 3 stated |
| b15 | 11B Best Bitter | | | inventory; 23 L |
| b16 | 18B American Pale Ale | hop-forward, `crisp` | flaked rice | ingredient deviation; excludes Citra and Mosaic |
| b17 | 8B Schwarzbier | lager | | ABV 7 (range 4.4–5.4): number deviation |
| b18 | 15A Irish Red Ale | `darker` | | guidance off; SRM 20 (range 9–14), accepted and listed |
| b19 | 17C Wee Heavy | `malty`, `stronger` | honey | ingredient deviation; 10 L |
| b20 | 19C American Brown Ale | `full` | lactose | ingredient deviation |

Counts this gives (the test measures the real file): 16 BJCP categories; 3 stouts/porters;
4 lagers; 2 Belgian; 2 wheat/sour; 3 hop-forward; every adjunct ≥ 1 (oats 2, lactose 2, rice 2,
honey 2); 3 ingredient deviations (b16, b19, b20), 3 number deviations (b08, b17, b18), 1 mismatch, 1 guidance
off, 1 conflict; 2 exclusions, 2 inventories; every §7 hint row ≥ 1; batch sizes 10, 15, 20,
23 L; no fruit and no non-gravity extras. Ranges quoted above were read from `ref.beer_style`
on 2026-10-11 and stay out of the file.

## Tasks

### Task 1: Write the 20 briefs and the test that checks them
Why: R1–R12, A1–A4, A7.
- [x] Create `evals/recipe_briefs.toml`: a short header comment (what the file is, that style
  ranges come from `ref.beer_style`, link to `docs/work/test-briefs/brief.md`), then the 20
  briefs from the spread table above in the format above. Requests read like a user typing:
  1–3 sentences, English, no style codes unless the user would say them. Each `deviations`
  entry names what and from what. No fruit, spice, herb, coffee, vanilla, cacao or wood anywhere.
- [x] Write `tests/test_recipe_briefs.py`. Module-level: `BRIEFS = tomllib.load(...)["brief"]`;
  the explicit code sets `LAGERS`, `BELGIAN`, `WHEAT_OR_SOUR`, `HOP_FORWARD`,
  `STOUT_OR_PORTER`; `ADJUNCTS` (the six names); `HINT_ROWS` (the seven §7 rows as word sets);
  `NON_GRAVITY_WORDS` (fruit names, `fruit`, `spice`, `cinnamon`, `coriander`, `herb`, `coffee`,
  `vanilla`, `cacao`, `cocoa`, `oak`, `wood`, `barrel` — not `chocolate`, which is a malt);
  `coverage(briefs) -> dict[str, int]`. Tests:
  - `test_twenty_briefs_with_every_field`: exactly 20, unique ids, each brief's keys equal the
    R2 key set, types as in the format table, `stated` keys ⊆ the five, `needs` keys ⊆ the four,
    `request` non-empty and at most 3 sentences (R1, R2, R4 by shape).
  - `test_style_codes_exist_in_ref`: every `style` and `alt_styles` code is in
    `select b.code from ref.beer_style b join ref.source s on s.id = b.source_id where s.slug = 'bjcp-2021'`
    via `loaders.db.connect()` (R3).
  - `test_style_spread` (R5), `test_adjuncts_needed` (R6), `test_guidance_cases` (R7),
    `test_constraint_cases` (R8), `test_hint_rows` (R9), `test_batch_sizes` (R10),
    `test_no_fruit_or_non_gravity_extras` (R11: no `NON_GRAVITY_WORDS` as whole words in
    `request`, `wanted` or any `needs` list; every `wanted` item appears in `needs`). Each
    asserts against `coverage()` with the measured count in the message.
  - `test_print_coverage`: prints `coverage(BRIEFS)` so `pytest -s` shows the A3 numbers.
- [x] Check each bucket set and each expected code against the DB before relying on them:
  `docker exec -i supabase-db psql -U postgres -d postgres -c "select code, name from ref.beer_style where guide = 'BJCP' order by code"`.
- [x] Run `.venv/bin/python -m pytest -s tests/test_recipe_briefs.py -v`, expect 10 passed and
  the coverage dict meeting every A3 minimum.
- [x] Prove the checks bite: temporarily delete one brief, and separately change one adjunct
  name; each run must fail with the count in the message. Restore the file.
- [x] A4: `grep -nE '[0-9]+(\.[0-9]+)? *(–|-|to) *[0-9]' evals/recipe_briefs.toml` finds no
  range; every number in the file is in a `stated` table, an `id`, or the user's own words.
- [x] Run the whole suite: `.venv/bin/python -m pytest -q`, expect 61 passed (51 + 10).
Done when: the file holds 20 briefs, the 10 new tests pass, the suite passes.
Commit: `Add 20 recipe test briefs with coverage test`

### Task 2: User review of the 20 briefs
Why: A5. The expected style and deviations are judgement calls, and the user's call wins.
**Needs the user.**
- [x] Report `needs-input` with a table per brief: id, request, expected style (and alts),
  deviations. Ask the user to approve or correct each one.
- [x] Apply every correction in `evals/recipe_briefs.toml`. If a correction drops a count below
  an R5–R10 minimum, say which and propose a replacement brief before writing it.
- [x] Re-run `.venv/bin/python -m pytest -q`, expect 61 passed.
Done when: the user has approved all 20 briefs and the suite passes.
Commit: `Apply user review to test briefs` (skip the commit if nothing changed, and say so)

### Task 3: Record P0 in PROJECT.md and RECIPE-ROADMAP
Why: R13, A6.
- [x] `docs/RECIPE-ROADMAP.md` §8: P0 row reads "20 test briefs …" with ✅ done and the date,
  links `../evals/recipe_briefs.toml`, and says D7 and D9 moved to P3 (P3's "Do" cell gains
  "Settle D7, D9"). §9 table: note "decided in P3" on D7 and D9. Do not touch §3–§7.
- [x] `PROJECT.md`: §4 Scripts row gains the briefs file and test with the measured test count;
  §7 D7 and D9 rows note "belongs to P3 (moved from P0, <date>)", status stays `open`; §8 dated
  entry (newest first) linking `docs/work/test-briefs/`, with the measured A3 counts and the
  suite result. §2, §3 and §6 unchanged.
- [x] Run `.venv/bin/python -m pytest -q`, expect 61 passed.
Done when: both docs show P0 done with measured numbers and the link.
Commit: `Record P0 test briefs in PROJECT and roadmap`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every expected style code really exists in BJCP 2021 (a wrong code would score P4 against the wrong target) | `tests/test_recipe_briefs.py::test_style_codes_exist_in_ref` | 1 |
| Every brief has every R2 field and no style-range keys (P4/P5 readers depend on the shape) | `tests/test_recipe_briefs.py::test_twenty_briefs_with_every_field` | 1 |
| The six adjuncts stay needed (`adjunct-fermentables` reads `needs` for its gap report) | `tests/test_recipe_briefs.py::test_adjuncts_needed` | 1 |
| No brief needs an ingredient outside fermentable/hop/yeast/salt | `tests/test_recipe_briefs.py::test_no_fruit_or_non_gravity_extras` | 1 |
| Coverage minimums R5, R7–R10 | the five coverage tests in `tests/test_recipe_briefs.py` | 1 |

## Approved exceptions

## Deviations
- 2026-10-11 · Task 1: `needs` is written as a `[brief.needs]` sub-table, not an inline table — the one-line inline form ran past 150 characters; the parsed shape is the same.
- 2026-10-11 · Task 2: R3 changed by the user (prominent adjunct → specialty code, base style as
  alternative); b12 reworded to make the honey prominent and now expects 31B, alt 18A. Its
  deviation stays kind `ingredient`, so R7 keeps 3. b19, b20 stay base style; b14 keeps
  Lactobacillus under `needs.yeast` (read as the culture slot). Test unchanged: it never
  enforced the base-style rule.
- 2026-10-11 · Task 2: b12's deviation removed (the re-labelling to 31B is not a deviation);
  b16 reworded to add a bit of rice, an ingredient deviation on 18B, so R7 ingredient
  deviations are b16, b19, b20 — user review. b16 also gains the `crisp` hint and needs flaked
  rice (rice now in 2 briefs).
