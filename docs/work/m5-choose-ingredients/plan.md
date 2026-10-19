# M5 · Steps 6–9: choose yeast, fermentables, hops and extras — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: m5-choose-ingredients

## Approach

- **Code builds a candidate table, the LLM picks from it, code checks and finishes the picks.**
  `app.choose_table(brief, style, targets, frame)` (new `db/042_choose_table.sql`) lists, per brief,
  every product the LLM may pick, with the fields the brief names and its style level at each
  usage choice. `app.choose_read_answer` (new `db/043_choose_check.sql`) checks the LLM's
  proposal against that table (R1–R7) and returns errors that start with `step 6:` … `step 9:`.
  `app.choose_outputs` (new `db/044_choose_outputs.sql`) turns a passed proposal into the four
  step outputs: each pick with its level, `because` and (step 9) the code-set dose. The LLM writes
  only ids, usages, percentages, hop minutes and shares, and a purpose; never a dose (R7, §6.7).
- **Levels in the check are the table's levels**, from the same machinery as step 3
  (`app.ingredient_choices` + `app.style_level`, no dose): what the model sees is what the check
  enforces. Pipeline picks are rated in **step 4's style used** (`targets.style.code`, e.g. 20B
  for b23); a wanted item is rated in **step 2's style** (`style.style.code`, the style step 3
  rated it in) and must reach `app.rate_wanted`'s best level (R4). The level of the full recipe
  with amounts is M6's `app.style_fit_recipe`.
- **Table size.** With guidance on, a product is listed when at least one of its choices is
  required, typical or allowed in the style used, or when it is wanted or in the inventory
  (marked, any level). With guidance off (b18) every product is listed. Excluded products and
  their siblings (same name once form words like `LUPOMAX` are removed) are never listed (R2).
  Measured while planning in 21A: 65 fermentables, 89 hops, 62 yeasts in style (215 rows), and the
  81 fermentable descriptions alone are 14,179 characters. So the one-call prompt likely does not
  fit `num_ctx` 8192; the fit test measures it.
- **Order: the fit test comes as early as it can (user decision 1).** It needs the table, the
  prompt and the check (R13: "passes this step's check (R1–R7)"), and the check needs the
  catalogue fixes for b10 (dark candi sugar) and b14 (lacto) to judge R3 and R5. So: Tasks 1–2
  catalogue words, Task 3 table and prompt text, Task 4 proposal contract, system prompt and
  check, **Task 5 the fit test and its decision gate**. Everything after Task 5 is written for
  the one-call shape (Task 7a); Task 7b is the per-step shape, used only if the fit test fails
  and you then agree to the extra LLM calls (R13).
- **Step contracts do not depend on the shape.** Step N's logged input is code-built (its kind's
  table rows and frame parts), and its output is the finished picks. In the one-call shape the
  pipeline logs four rows from one call; the call's details sit in step 6's `llm` column.
- **Graders stay independent of the check SQL** (as m4): `evals/run.py` reads ingredient facts
  from `ref` tables and the logged candidate rows; `evals/grade.py` checks A1–A9, A15, A16 and
  the `needs` classes from a reviewed class map, `evals/needs_classes.toml` (R10).

**Readings of the brief, decided by the user 2026-10-18 (option a each):**
1. R5's attenuation band: the yeast is compared with step 5's **yeast band**
   (`attenuation.yeast_low_pct`–`yeast_high_pct`, a yeast's own figure range at this mash),
   not the beer band `low_pct`–`high_pct`. They differ only for b03 and b20 (mash 68.5 °C), by
   0.83 points (measured on the s9 runs). Brief R5 and A5 updated.
2. "Lactobacillus finds type lacto" is a resolver rule: a word that names a culture type finds
   every yeast of that type (`app.yeast_type_word()`), used only when aliases and names find
   nothing. Not aliases on YF-998 and YF-999.
3. A `needs` class with a product in the candidate table that no pick covers is a **gap** and
   fails that brief's needs grade; a class with no product in the table counts as reported
   absent, with the reason (A10, G5 bar).

**Measured while planning (2026-10-18, read-only):** `ref.yeast.type` ale 75, kveik 20, lager
17, brett 2, null 5 (YF-998, YF-999, CBC-1, Philly Sour, Suava Ale); no check constraint on
`type`; hopline's YF-998 text says "Lactobacillus Plantarius törzs", YF-999 "lactobacillus
brevis", both `Stílus` `sour` (→ `TYPES["sour"] = None` in `loaders/yeasts.py`). The intake
tagger already maps type `lacto` → family `sour`. `ref.ingredient_alias` holds only the 10
intake misc aliases; `app.resolve_ingredient` reads aliases first. "dark candi sugar",
"Lactobacillus" and "Special B" resolve to nothing; "candi sugar" finds Brown Candi Sugar (3396,
225 EBC); "Munich malt" 4 products, "abbey yeast" 3 (Abbaye 1845 typical in 26B, Abbey Monk Ale
1817, M47 1872), "crystal malt" 11, "Maris Otter" 1 (13), "East Kent Goldings" 1 (474). Only
LUPOMAX names are hop siblings (Citra 470 → Citra LUPOMAX 471, Mosaic 488 → 489, plus Amarillo,
Azacca, Huell Melon). `ref.style_ingredient` has required yeast family rows: 10A `wheat`, 1B
and 5D `lager`, 26B `belgian`; lager styles are BJCP styles whose `raw->>'tags'` contains
`bottom-fermented` (1B, 2A, 5D, 6A, 8B, …) and BA styles whose `category` contains `LAGER`
(b22's `mexican-style-amber-lager`). Only 23A (min 4) and 25B (min 0) have a `sourness` row in
`ref.style_sensory`. In 10A only Munich Classic and Wit are typical; 35 yeasts (mostly YeastFlow,
incl. ale and lager families) are allowed, so R5's weizen yeast for b13 needs the required-family
rule. `app.style_level` over every product and choice in 21A took 0.36 s. The s9 runs 3874–3897
(`evals/results/2026-10-18-s9.json`) hold ok steps 0–5 for all 24 briefs. `test_step5.py::
test_excluded_and_inventory` asserts that "dark candi sugar" resolves to nothing (Task 2 changes
it). `test_contracts.py` lists contracts for steps 0–5 only. `app.solve_hops` needs `share_pct,
alpha_pct, minutes, usage` per item and a boil item when the IBU target is above 0.
**Context7 could not be used:** `npx ctx7@latest library Ollama …` failed with "Invalid API key"
(run `npx ctx7@latest login` or set `CONTEXT7_API_KEY`). Ollama's behaviour below (truncation
beyond `num_ctx`, `prompt_eval_count` with a cached prompt prefix, a reload when `num_ctx`
changes) is from memory and **unverified**; Task 5 guards against each one by measurement.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `loaders/yeast_products.py`, `loaders/yeasts.py` | changed | `LACTO` map: YF-998, YF-999 get type `lacto`, quoted from their hopline text |
| `db/036_ingredient_resolver.sql` | changed | `app.yeast_type_word()`; third fallback in `app.resolve_ingredient` |
| `loaders/adjunct_products.py`, `loaders/adjuncts.py` | changed | `ALIASES`: "dark candi sugar" → Brown Candi Sugar, written by the adjunct loader |
| `db/042_choose_table.sql` | new | `app.hop_form_word`, `app.choose_excluded`, `app.choose_table`, `app.choose_prompt`, and their helpers (`app.choose_levels`, `choose_keeps_best`, `choose_yeast_rules`, `choose_fit_reason`, `choose_row_line` …) |
| `db/043_choose_check.sql` | new | `app.misc_dose`, `app.step6_errors` … `app.step9_errors`, `app.choose_check`, `app.choose_read_answer` |
| `db/044_choose_outputs.sql` | new | `app.step6_output` … `app.step9_output`, `app.choose_outputs` |
| `shared/contracts/choose.proposal.schema.json` | new | the LLM's `format` and the shape the check reads |
| `shared/contracts/choose.input.schema.json` | new | input of the steps 6–9 sub-workflow |
| `shared/contracts/step6…step9.{input,output}.schema.json` | new | logged step rows |
| `shared/prompts/choose.system.md` | new | system prompt for steps 6–9 |
| `evals/fit_test.py` | new | R13 fit test (`python -m evals.fit_test`) |
| `docs/work/m5-choose-ingredients/fit-test.md` | new | fit test numbers and the shape it picked (A14) |
| `evals/results/<date>-m5-fit.json`, `evals/results/<date>-m5.json` | new | fit test and G5 results |
| `n8n/workflows/steps-6-9-choose-ingredients.json` | new | sub-workflow `Steps 6–9 · choose ingredients` (Task 7a) |
| `n8n/workflows/recipe-pipeline.json` | changed | steps 6–9 after step 5, four log rows |
| `evals/needs_classes.toml` | new | class map for `needs` (R10), reviewed by you |
| `evals/grade.py`, `evals/run.py` | changed | `grade_step6` … `grade_step9`, `grade_needs`; facts; columns; LLM calls per run |
| `tests/test_yeasts.py`, `tests/test_ingredient_resolver.py`, `tests/test_adjuncts.py`, `tests/test_step5.py` | changed | Tasks 1–2 |
| `tests/test_choose_table.py`, `tests/test_choose_check.py`, `tests/test_choose_outputs.py`, `tests/test_fit_test.py` | new | Tasks 3–6 |
| `tests/step69_sample.json` | new | sample input for the sub-workflow's Test data note |
| `tests/test_contracts.py`, `tests/test_workflows.py`, `tests/test_pipeline.py`, `tests/test_grade.py`, `tests/test_run.py` | changed | as each task says |
| `docs/RECIPE-ROADMAP.md`, `docs/WORKFLOW-ROADMAP.md`, `docs/DATABASE.md`, `docs/OPERATIONS.md` | changed | Task 10 |
| `PROJECT.md` | changed | §4 rows, §8 per task |

Apply command for every SQL file (OPERATIONS §4), run twice to show it is idempotent, then check
owners with `select proname, pg_get_userbyid(proowner) from pg_proc where pronamespace =
'app'::regnamespace and proname = any(<names>)`:
`docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`
Each new SQL file gets the header the others have (purpose, work folder, needs, apply command,
idempotent).

## Tasks

### Task 1: YF-998 and YF-999 are lacto cultures, and "Lactobacillus" finds them
Why: R5, A15. Step 6's souring rule and the b14 needs class read `type = 'lacto'`.
- [x] `loaders/yeast_products.py`: `LACTO: dict[str, str]` from SKU to the quote that names the
      culture: `"301244": "Lactobacillus Plantarius törzs"`, `"301245": "A lactobacillus brevis"`
      (exact words from `details.text` in `hopline_yeasts.json`). Comment: hopline files these
      under `Stílus` `sour`, which says no culture type; the text does (user decision
      2026-10-18).
- [x] `loaders/yeasts.py`: `make_yeast` takes the type from `LACTO` when the SKU is in it
      (`field_source["type"]` stays `hopline-yeasts`), else from `type_of(Stílus)` as now; the
      report lists the two with their quote. `TYPES["sour"]` stays `None` (Philly Sour and others
      keep NULL).
- [x] Write `tests/test_yeasts.py::test_lacto_cultures` (no stack): a product dict shaped like
      `US05` with SKU 301244, `Stílus` `sour` and the text gives type `lacto` with field source
      `hopline-yeasts`; the same dict with SKU 301030 gives None. See it fail first.
- [x] Reload: `.venv/bin/python -m loaders.yeasts --hopline shared/rag-files/hopline/hopline_yeasts.json --report <scratchpad>/yeast-report.md`
      (a path outside the repo: the shipped report in `docs/finished/yeast-loader/` stays as it
      is). Run it twice. Expect `select type, count(*) from ref.yeast group by type`: ale 75,
      kveik 20, lager 17, brett 2, lacto 2, null 3; `ref.ingredient_tag` row count unchanged
      (the hopline tagger reads `Stílus`, not `type`).
- [x] `db/036_ingredient_resolver.sql`: `app.yeast_type_word() returns table (word text, type text)`,
      immutable, values `('lactobacillus', 'lacto'), ('lacto', 'lacto')`; comment: a word that
      names a culture type, never a product. `app.resolve_ingredient` gains a third branch, rule
      `'yeast type'`: when the alias branch and `app.resolve_ingredient_by_name` both find
      nothing, and the query's words (`app.ingredient_words`, kind word `yeast` removed when
      another word remains) equal the words of one `yeast_type_word` row, return every
      `ref.yeast` of that type. Keep the `order by 3, 1`.
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_ingredient_resolver.py::test_lactobacillus_finds_lacto_cultures` (stack):
      "Lactobacillus" and "lacto yeast" give YF-998 and YF-999 with rule `yeast type`;
      "lactose" still gives Lactose only.
      `test_type_words_change_no_brief_word`: every wanted, excluded and inventory word of
      b01–b24 resolves to the same ids as `app.resolve_ingredient_by_name` or the alias branch
      did before (compare with the rule column: no row has rule `yeast type`).
- [x] Run `.venv/bin/pytest tests/test_yeasts.py tests/test_ingredient_resolver.py tests/test_step3.py tests/test_step5.py`, expect all pass.
- [x] `docs/DATABASE.md`: `ref.yeast` row (type values incl. `lacto`, 2 rows), resolver line.
      PROJECT.md §8 entry with the measured type counts.
Done when: YF-998 and YF-999 are `lacto` after two reloads, and "Lactobacillus" resolves to them.
Commit: `Mark lacto cultures and resolve Lactobacillus`

### Task 2: "dark candi sugar" finds Brown Candi Sugar
Why: R3, A16 (user decision 4). b10's inventory word must resolve before the table is built.
- [x] `loaders/adjunct_products.py`: `ALIASES: dict[str, tuple[str, ...]] = {"Brown Candi Sugar":
      ("dark candi sugar",)}` with the comment: the brewer's common name for this product (user
      decision 2026-10-18); add a name only for a word that names this product.
- [x] `loaders/adjuncts.py` `load`: after each upsert, `delete from ref.ingredient_alias where
      ingredient_id = %s`, then insert that product's `ALIASES` (as `loaders/extra_ingredients.py`
      `load_ingredient` does), so a re-run gives the same rows. After the loop, each alias must
      resolve to its product only (`select ingredient_id from app.resolve_ingredient(%s)`), else
      raise (the connection rolls back).
- [x] Write `tests/test_adjuncts.py::test_aliases_name_mapped_products` (no stack: every key of
      `ALIASES` is a product name in `PRODUCTS`) and `test_dark_candi_sugar_alias` (stack:
      "dark candi sugar" → [3396's id] with rule `alias`; "candi sugar" still finds it by name).
      See the stack test fail first.
- [x] Reload: `.venv/bin/python -m loaders.adjuncts --hopline shared/rag-files/hopline/hopline_adjuncts.json`,
      twice; `select count(*) from ref.ingredient_alias` is 11 both times.
      `.venv/bin/python -m loaders.extra_ingredients --check` still ok (its alias check reads
      the stored alias and must not complain).
- [x] `tests/test_step5.py::test_excluded_and_inventory`: b10's "dark candi sugar" now has refs
      `[Brown Candi Sugar]` and `from` `request`.
- [x] Run `.venv/bin/pytest tests/test_adjuncts.py tests/test_step5.py tests/test_ingredient_resolver.py tests/test_extra_ingredients.py`, expect all pass.
- [x] `docs/DATABASE.md` `ingredient_alias` row (11, one from the adjunct loader). PROJECT.md §8.
Done when: the alias is written by the adjunct loader on every run and b10's frame lists Brown
Candi Sugar.
Commit: `Add dark candi sugar alias to the adjunct loader`

### Task 3: code builds the candidate table and its prompt text
Why: R1, R2, R3, R4, R5, R8, R9 (the facts code adds); scope "candidate table".
- [x] `db/042_choose_table.sql` (needs 034, 036, 037, 041):
      - `app.hop_form_word() returns table (word text, note text)`: `('lupomax', 'LUPOMAX pellets:
        concentrated lupulin of the same variety')`.
      - `app.choose_excluded(frame jsonb) returns jsonb`: every product in `frame.excluded[].refs`
        plus its siblings: products of the same kind whose `app.ingredient_words(name)`, with the
        form words removed on both sides, equal the excluded product's (so Citra excludes Citra
        LUPOMAX and Citra LUPOMAX excludes Citra). Each as `{ingredient_id,
        name, word, why}` (`why`: `excluded in the request` or `sibling of <name>`).
      - `app.choose_table(brief jsonb, style jsonb, targets jsonb, frame jsonb) returns jsonb`.
        Keys:
        `style_used` (`targets.style.code`), `wanted_style` (`style.style.code`), `guidance`,
        `targets` (`og`, `fg`, `ibu`, `srm` values), `band` (`frame.attenuation.yeast_low_pct`,
        `yeast_high_pct`), `excluded` (from `app.choose_excluded`), and the rows
        `fermentables`, `hops`, `yeasts`, `misc`. Every row: `ingredient_id`, `name`,
        `producer`, `levels` (one `{choice, usage, minutes, level, because}` per
        `app.ingredient_choices(id, role)` choice, rated with `app.style_level(style_used, …)`),
        `best_level`, `inventory` (the word, or null), `wanted` (the item, or null), and for a
        wanted row `keeps_best`: the choices whose level in `wanted_style` reaches
        `app.rate_wanted(wanted_style, item, role)`'s level. Kind fields: fermentable `role`,
        `max_pct`, `ebc` `{low, high}`, `fermentability`, `description`; hop `purpose`, `alpha`
        `{low, high}`, `origins`, character tags; yeast `type`, `form`, `attenuation` `{low, high}`
        or null, `temp_c`, `flocculation`, `alcohol_tolerance_pct`, family and character tags,
        `overlaps_band` (true, false, or null when no figure); misc `category`, `usages`,
        `time_min`, `dose` (`app.step5_misc`'s `dose_g_per_l`). Filter as in the Approach; misc
        rows only for wanted or inventory misc. Excluded ids never appear.
        `yeast_rules`: `lager` (the style used is a lager style, as measured above), `families`
        (required yeast family tags of the style used from `ref.style_ingredient`), `souring`
        (the style used has `sourness` with `min_level >= 1`). With guidance off `lager` and
        `families` are false / empty.
        `slots`: per frame slot `{item, role, kind, ids}` (ids of its refs that are in the table),
        `inventory_words`: per inventory word `{word, ids, fits}` (fits = some product is in
        the table at a level other than `out_of_style`/`changes_style`, and a yeast also meets
        `lager` and `families`), `absent`: `{word, kind, reason}` for a slot or inventory word
        with no product (`kind` null, reason `no product in the catalogue matches "<word>"`) or
        whose products are all excluded, `unused_inventory`: `{word, reason}` for a word that does
        not fit (the level and its `because`, or "the recipe has no extras" for misc when no misc
        is wanted).
      - `app.choose_prompt(tbl jsonb, brief jsonb) returns text`: the user message. Plain text,
        one line per row (`id | name | fields | levels as choice=level`), grouped by kind, with
        headings; then the brief's wanted, excluded and inventory words; the style used, its
        name and `characteristic_ingredients`; the targets; the band; the yeast rules; the slots,
        absents and unused inventory. Levels as words (`typical`). No JSON; every number comes
        from `tbl`.
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_choose_table.py` (stack; inputs via `tests.test_step4.step4` and
      `tests.test_step5.step5`, step 2 via `app.step2_best_style`). See each fail first:
      `test_b16_excludes_siblings` (A2: no 470, 471, 488, 489 in any row; `excluded` names
      471 and 489 as siblings); `test_b08_has_no_saaz` (A2); `test_inventory_marked_and_fitting`
      (A3: b10 rows 3396, the four Munich ids and the three abbey ids carry their inventory
      word, `inventory_words` all fit; b15 13, the crystal ids and 474 likewise);
      `test_guidance_filters_rows` (b01: every non-wanted, non-inventory row has a choice that
      is required, typical or allowed; b18 lists every product but the excluded);
      `test_wanted_rows_keep_best` (b23: coffee rows have `keeps_best` from 30A, not 20B);
      `test_yeast_rules` (b06, b08, b09, b17, b22 `lager` true; b13 `families` = `{wheat}`;
      b14 `souring` true and both lacto ids listed; b11 `souring` false);
      `test_made_up_word_is_absent` (A8: b01 with an extra wanted `{item: "unobtainium", role:
      background}` gives one `absent` row with the reason, and every other part equals b01's
      table); `test_prompt_uses_table_numbers` (every number in the prompt text is a number in
      the table JSON or the brief).
- [x] Measure and write in the PROJECT.md §8 entry: rows per kind and prompt characters for
      b01, b18 (guidance off, the largest) and b23.
Done when: the table tests pass and the largest prompt's size is recorded.
Commit: `Build the steps 6-9 candidate table`

### Task 4: the proposal contract, the system prompt and the check
Why: R1–R8; A1, A2, A3, A5, A6, A7. The fit test's quality half needs this check (R13).
- [x] `shared/contracts/choose.proposal.schema.json` (the `format` sent to Ollama; every property
      required, `additionalProperties: false` at every level):
      `yeast {main {ingredient_id integer, purpose string}, souring {ingredient_id, purpose} or null}`;
      `fermentables [{ingredient_id, usage enum mash|boil, pct number > 0, purpose}]`;
      `hops [{ingredient_id, usage enum boil|whirlpool|dry_hop, minutes number >= 0, share_pct
      number > 0, purpose}]`; `extras [{ingredient_id, usage string, purpose}]`. No dose field
      anywhere.
- [x] `shared/prompts/choose.system.md`: what each step picks and from where (only ids in the
      table), the rules the check applies (below) in plain words, prefer `typical` over
      `allowed`, use marked inventory, put each wanted item at a `keeps_best` choice, write a
      short purpose, never a dose or an amount.
- [x] `db/043_choose_check.sql` (needs 042):
      - `app.misc_dose(product_id bigint, role text) returns jsonb` → `{g_per_l, because}`: a
        one-point range gives that value ("one sourced dose"); `background` (and a null role)
        the low end, `feature` the high end ("<role>: low/high end of the sourced range");
        no range gives `g_per_l` null, "no sourced dose". User decision 5.
      - `app.step6_errors(tbl, yeast)`, `app.step7_errors(tbl, fermentables)`,
        `app.step8_errors(tbl, hops)`, `app.step9_errors(tbl, extras)` each `returns text[]`,
        every entry starting with `step N: `. Rules (guidance off skips the level, lager and
        family rules):
        - all steps: the id is a row of that kind in `tbl` (R1); an excluded id gets its own
          message naming the excluded word (R2); a pipeline pick's level at its choice is
          required, typical or allowed (R4); a wanted pick is at a `keeps_best` choice (R4);
          every fitting inventory word of that kind has one of its ids picked (R3; for yeasts
          one fitting yeast word is enough, the others go to `unused_inventory` as "one main
          yeast"); every slot of that kind with ids has one of them picked (R6, R7).
        - step 6: the main yeast is not `lacto`; `lager` → type `lager`; every `families` tag on
          the main yeast; if it has an attenuation figure that does not overlap `band` while some
          table yeast does, error (R5); `souring` → `souring` is a `lacto` row, else `souring`
          is null unless a wanted or inventory word named it.
        - step 7: each id once; pct sum 100 ± 0.1; pct ≤ `max_pct` when set (R6).
        - step 8: share sum 100 ± 0.1; minutes: boil 0–90, whirlpool 0–60, dry_hop 0 (contact
          time is M7's); a boil item when the IBU target is above 0 (`app.solve_hops` needs one).
        - step 9: usage is one of the row's `usages`; one extra per misc slot (R7).
      - `app.choose_check(tbl, proposal) returns text[]`: the four lists joined, step order.
      - `app.choose_read_answer(content text, contract json, tbl jsonb) returns table (proposal
        jsonb, errors text[])`, as `app.step1_read_answer`: not JSON → one error; contract
        errors (`extensions.jsonschema_validation_errors`) prefixed `contract: `; then
        `app.choose_check`.
- [x] Apply twice; owners `postgres`.
- [x] Write `tests/test_choose_check.py` (stack). A helper builds a good proposal from a table
      (first in-style rows, wanted and inventory ids, shares 100). Tests, each seen failing
      first: the good proposals for b01, b08, b10, b14, b15, b16, b23 pass; and one test per
      rule, each with the smallest change to a good proposal: invented id (A1), excluded Saaz
      in b08 and Citra LUPOMAX in b16 (A2), b10 without Brown Candi Sugar and b15 without 474
      (A3), an out-of-style pipeline pick and a wanted pick off `keeps_best` (A4), an ale yeast
      in b08 and an ale-family yeast in b13 (A5), b14 without a souring culture, pct sum 99,
      pct above `max_pct`, hops with no boil item in b01, dry_hop minutes 3 (A6), an extra with
      `dose_g_per_l` (A7: refused as a contract error), an extra usage not in the row (A7);
      `test_misc_dose_rule` (A16: b23 coffee whole beans `feature` 3.0, vanilla `background`
      0.05, orange peel 2.64, a fixture misc with no dose null); `test_guidance_off_allows_any_level`
      (b18).
- [x] `tests/test_contracts.py`: `NAMES` gains `choose.proposal` (Task 6 adds the rest).
- [x] Run `.venv/bin/pytest tests/test_choose_check.py tests/test_choose_table.py tests/test_contracts.py`, expect all pass.
- [x] PROJECT.md §8 entry.
Done when: every rule has a failing-proposal test and the good proposals pass.
Commit: `Add the steps 6-9 proposal check`

### Task 5: fit test: does one call for steps 6–9 fit and work? (decision gate)
Why: R13, A14 (user decision 1). Its result picks Task 7a or 7b.
- [x] `evals/fit_test.py` (`python -m evals.fit_test [--runs evals/results/2026-10-18-s9.json]
      [--num-ctx 8192] [--brief b01] [--save]`). For each brief: read the run's stored outputs of
      steps 0, 1, 2 and 4 from `app.run_step` (run ids from the results file), rebuild step 5 with
      `app.step5_frame` (so Tasks 1–2 count), build `app.choose_table` and `app.choose_prompt`,
      and call Ollama as step 1 does (`POST /api/chat`, model D2, think false, temperature 0,
      seed 42, `format` = `choose.proposal`, `num_ctx` = the option, `num_predict` 4096,
      `stream` false). Check with `app.choose_read_answer`; on errors, retry once with the
      errors (step 1's retry message). Reuse `evals.benchmark.ollama_post`, `unload_all`,
      `processor_split`.
      **Exact token counts:** unload the model (`unload_all`) before every call, so a cached
      prompt prefix cannot shrink `prompt_eval_count`. A call **fits** when `prompt_eval_count +
      4096 <= num_ctx` (a truncated prompt can never meet this) and `docker logs ollama --since
      <call start>` has no line with `truncat`; try 2 must fit too. Record per brief and try:
      `prompt_tokens`, `output_tokens`, `done_reason`, `load_ms`, `llm_ms`, fits, errors; per
      option the `ollama ps` processor split. A brief **passes** when every try it made fits and
      a try's proposal has no errors.
- [x] Write `tests/test_fit_test.py` (no stack): the fit rule on numbers (8192: 4096 fits,
      4097 does not), the truncation line makes it not fit, a brief passes on try 2, a brief
      whose try 2 does not fit fails.
- [x] Run with `--num-ctx 8192` on all 24 (long: start it in the background and wait on its
      results file, not on the process). If every brief fits and passes, stop here: one call at
      8192. If some do not fit, run again with 16384, then 32768, but count an option only when
      the model loads and answers (record its processor split and median `llm_ms`, and the
      `load_ms` a step-1-to-step-6 switch costs, since step 1 stays at 8192). If the fits pass but
      the check fails, you may revise `choose.system.md` at most twice (each time re-run all 24 at
      that option and keep both results); the brief's table fields are not cut.
- [x] Save `evals/results/<date>-m5-fit.json` and write `fit-test.md`: per brief the prompt
      tokens, output budget, context used, tries and pass; the worst case; each option's split and
      timing; the shape picked and the `num_ctx` it runs at. PROJECT.md §8 entry with the same
      numbers and the choice (R13).
- [x] **Gate.** Pass → write the shape and `num_ctx` into the `Shape:` line below and go on with
      Task 6 and Task 7a. Fail → stop and hand back `needs-input`: the numbers, and the question
      whether to build one call per step (5 LLM calls through stage D, above the P5/G6 bar of
      "≤ 2 plus tie-breaks"), with options. PROJECT.md §2, §3, §6 are not changed.
Shape: **one call for steps 6-9 at `num_ctx` 32768** (Task 7a). 24 of 24 briefs fit and pass within two tries (worst prompt 26,554 tokens + 4096 = 30,650); 8192 and 16384 fit none. See [`fit-test.md`](fit-test.md).
Done when: `fit-test.md` records the numbers and the choice, and the gate is passed or handed back.
Commit: `Add the steps 6-9 fit test and its result`

### Task 6: code finishes the picks and the step contracts
Why: R7, R8, R9, R11; A7, A8, A9.
- [ ] `db/044_choose_outputs.sql` (needs 043):
      - `app.step6_output(tbl, yeast)`, `app.step7_output(tbl, fermentables)`,
        `app.step8_output(tbl, hops)`, `app.step9_output(tbl, extras)` each `returns jsonb`.
        Each pick is read **only** from its `tbl` row by id (an id not in `tbl` raises
        `step N: id % is not in the candidate table`, R1), with the LLM's `usage`, `pct` /
        `minutes` and `share_pct`, `purpose`, and code's facts: `level` and `level_because` (the
        row's choice; for a yeast the best ferment choice, naming its temperature), `inventory`,
        `wanted`, `slot`, and `because`: one sentence joining the purpose and those facts (R9).
        Step 6 `{yeast, souring, attenuation {band, yeast, overlaps, because}, unused_inventory,
        absent}` (a yeast with no figure: overlaps null, "no attenuation figure; not assumed");
        step 7 `{fermentables, absent}` (role, `max_pct`, EBC, fermentability per pick); step 8
        `{hops, absent}` (alpha per pick, the `app.solve_hops` inputs); step 9 `{extras, absent}`
        with `dose_g_per_l` and `dose_because` from `app.misc_dose(id, wanted role)` and the row's
        `time_min`. `absent` per kind; absents with kind null go in step 9's (R8).
      - `app.choose_outputs(tbl, proposal) returns jsonb` → `{step6, step7, step8, step9}`.
- [ ] Contracts: `step6.input` … `step9.input` = `{run_id, style_used, wanted_style, guidance,
      candidates (that kind's rows), slots, inventory_words, excluded}`, step 6 adds `band`,
      `targets` and `yeast_rules`, step 8 adds `targets`; `step6.output` … `step9.output` as
      above. `choose.input` = `{run_id, brief, style, profile, targets, frame, model, think,
      temperature, seed}` (all required). `tests/test_contracts.py`: `NAMES` covers steps 0–9,
      `choose.input`, `choose.proposal`; `ABSENT_SLOTS` gains `step6.output` (`souring` null,
      `absent` array), `step7.output` and `step8.output` (`absent` array), `step9.output`
      (`extras.dose_g_per_l` null, `absent` array).
- [ ] Apply twice; owners `postgres`.
- [ ] Write `tests/test_choose_outputs.py` (stack), each seen failing first:
      `test_outputs_use_table_rows_only` (A1/R1: an output built from a proposal with an id not
      in the table raises; for the good proposals of Task 4 every output id is a table id and
      every name, alpha, EBC equals its `ref` row); `test_outputs_meet_contracts` (all four
      outputs and inputs of the 7 good proposals); `test_every_pick_has_because_and_level` (A9);
      `test_dose_set_by_code` (A7, A16: b23 3.0 and 0.05, b24 2.64);
      `test_made_up_word_absent_rest_chosen` (A8); `test_yeast_without_figure_reported` (R5).
- [ ] Run `.venv/bin/pytest tests/test_choose_outputs.py tests/test_choose_check.py tests/test_contracts.py`, expect all pass.
- [ ] `docs/DATABASE.md` §5: the functions of `db/042`–`044`. PROJECT.md §8.
Done when: outputs meet their contracts and carry only table rows.
Commit: `Finish steps 6-9 picks and add their contracts`

### Task 7a (one call): steps 6–9 run in the pipeline
Why: R11, A11. Only if Task 5 picked one call.
- [ ] Sub-workflow `Steps 6–9 · choose ingredients` (id `ST69chooseingr01`), written as JSON from
      `n8n/workflows/step-1-read-request.json`'s pattern and imported with the n8n CLI
      (OPERATIONS §5; the pipeline needs `onError`, so the pipeline goes this way too):
      trigger with the `choose.input` fields → `Check contract` (`choose.input`) → Postgres
      `select app.choose_table($1, $2, $3, $4)` and `app.choose_prompt` → read
      `/data/shared/prompts/choose.system.md` and `/data/shared/contracts/choose.proposal.schema.json`
      → `Build model request` (`num_ctx` = Task 5's value, `num_predict` 4096, temperature and
      seed from the input) → `Ask model` → Postgres `app.choose_read_answer` → ok? →
      Postgres `app.choose_outputs` → four `Check contract` calls (`step6.output` … `step9.output`)
      → return `{table, step6, step7, step8, step9, llm}`; else retry once as step 1; a second
      failure stops with `steps 6-9 answer failed twice: try 1: …; try 2: …`. `llm` as step 1's
      plus `num_ctx` and `steps: [6, 7, 8, 9]`. Sticky note and a `Test data` note with
      `tests/step69_sample.json` (b01's inputs from Task 3's helpers, `run_id` 0).
- [ ] `Recipe pipeline`: `Step 5 · log ok` → `Steps 6–9 · input` → `Steps 6–9 · choose
      ingredients` (continueErrorOutput) → `Step 6 · log ok` (input `step6.input` built from
      `table`, output `step6`, `tokens` and `llm` from the call) → `Step 7 · log ok` →
      `Step 8 · log ok` → `Step 9 · log ok` (no `llm`) → `Finish run`. Error branch:
      `Steps 6–9 · log failure` writes the row for the lowest `step N:` in the error text (6 when
      none) → `Finish run (failed, steps 6–9)` → `Respond failed` with that `failed_step`. Update
      the per-step sticky note (steps 0–9 built).
- [ ] Import both, publish the sub-workflow first, then the pipeline (MCP), delete the copies in
      `shared/`; `.venv/bin/python -m evals.workflows`.
- [ ] `tests/test_workflows.py`: `SAMPLES` and `CONTRACT_OF` (`choose.input`) for the new file;
      `test_choose_num_ctx_matches_fit_test` (the `Build model request` holds `num_ctx:
      <evals.fit_test.CHOOSE_NUM_CTX>`; set that constant to Task 5's value).
      `tests/test_pipeline.py`: `test_steps_6_to_9_logged` (b01: four ok rows, inputs and
      outputs valid against their contracts, step 6 `llm.tries` 1 or 2, steps 7–9 `llm` null),
      `test_step_5_logged` unchanged; time the file (each run now has a second LLM call).
- [ ] Run `.venv/bin/pytest tests/test_workflows.py tests/test_pipeline.py`, expect all pass.
- [ ] `docs/OPERATIONS.md` §5: nine workflows, the new one, its `num_ctx`, the reload cost if
      it differs from step 1's. PROJECT.md §4 Orchestration row and §8.
Done when: a webhook run of b01 logs ok rows for steps 0–9.
Commit: `Run steps 6-9 in the recipe pipeline`

### Task 7b (one call per step): only if Task 5 failed and you chose this
Why: R11, R13. Replaces 7a.
- [ ] Split `choose.proposal` into `step6.proposal` … `step9.proposal` (its four properties) and
      `choose.system.md` into `step6.system.md` … `step9.system.md`; `app.stepN_read_answer`
      (same pattern, `app.stepN_errors` only). Each step's prompt has its kind's rows plus the
      picks of the earlier steps; measure each prompt against `num_ctx` 8192 as in Task 5.
- [ ] Four sub-workflows `Step 6 · choose yeast`, `Step 7 · choose fermentables`, `Step 8 · choose
      hops`, `Step 9 · choose extras`, each like `Step 1 · read request`; each logs its own
      `llm`. Pipeline blocks as for steps 2–5. Tests as 7a, per step.
Done when: as 7a, with four calls.
Commit: `Run steps 6-9 in the recipe pipeline`

### Task 8: graders for steps 6–9 and the needs class map
Why: R10, A1–A11, A15, A16.
- [ ] `evals/needs_classes.toml`: one `[[class]]` per needs word of `fermentables`, `hops`, `yeast`
      and `misc` (48 words, water salts are M7's): `word`, `kind`, and either `names` (product
      names that count) or a conjunction of `role`, `ebc` `[low, high]` (overlaps the product's
      EBC), `family` (yeast family tag), `type` (yeast type), `origin`, `purpose`, `category`;
      plus `why`. Special B = `names = ["Special W", "Caraaroma"]` (the dark-crystal class, user
      decision 3); Lactobacillus = `type = "lacto"`; Tettnang = `names =
      ["Tettnanger"]`; the yeast class words by family tag.
- [ ] **Gate:** hand back `needs-input` with the class map for your review (A10) before the G5
      run; record your answer in the PROJECT.md §8 entry.
- [ ] `evals/run.py`: `GRADED_STEPS` 2–9; `read_run` reads `llm` of every step; `read_facts`
      adds, for steps 6–9, the `ref` facts of every picked id (exists, kind, name, type, family
      tags, role, `max_pct`, EBC, alpha, origins, misc usages and dose), the excluded ids with
      siblings by name (Python, form word `lupomax`), the style used's lager and sourness facts and
      required families (read from `ref.beer_style`, `ref.style_sensory`, `ref.style_ingredient`),
      and the candidate ids from each logged step input. `table` and `totals` gain step 6–9 and
      `needs` columns and `calls` (sum of `llm.tries` over the run's rows).
- [ ] `evals/grade.py`: `grade_step6` … `grade_step9` (pure Python): every id exists and is a
      candidate (A1); none excluded (A2); fitting inventory used (A3); lager / family / souring
      (A5, A15); shares and `max_pct`, hop fields (A6); doses equal the role rule from the misc
      facts (A7, A16); every pick has `because` and `level` (A9); with guidance on no pipeline pick
      `out_of_style` or `changes_style` (A4). `grade_needs(brief, steps, facts, classes)` →
      per word `covered` / `absent: <reason>` / `gap`.
- [ ] Tests in `tests/test_grade.py` (no stack), each seen failing when its grader check is
      broken: one passing output per step, and one failing case per check above; `grade_needs`
      on Special B covered by Special W, Lactobacillus by a lacto pick, a gap.
      `tests/test_run.py`: the new columns, `calls`, not-run steps count as failed.
- [ ] Run `.venv/bin/pytest tests/test_grade.py tests/test_run.py`, expect all pass.
- [ ] PROJECT.md §8.
Done when: the graders and the class map are in, and you have reviewed the map.
Commit: `Grade steps 6-9 and needs classes`

### Task 9: G5 on the real pipeline
Why: G5; A1–A16.
- [ ] `.venv/bin/python -m evals.run --save --label m5` (background; wait on the results file).
      Expect 24/24 for steps 1–9 and needs, 0 invented, 0 excluded, `calls` = 2 per run in the
      one-call shape (plus retries). A miss is fixed in its task's code or prompt and the run
      repeated; record each miss and its fix.
- [ ] Measure for the §8 entry: A11 (all 24 step 6–9 rows ok and valid against their
      contracts, `extensions.jsonschema_validation_errors`), b08's late hop and its level in 5D
      (A6), b10 and b15 inventory picks (A3), b14 yeasts (A15), b23 and b24 doses (A16), the
      needs table (A10), LLM calls per run (A11, A14), run time per brief.
- [ ] **Gate (A12):** hand back `needs-input` with the picks of 3 briefs (b03, b10, b16: stout,
      inventory, exclusions) for your direction check; record your answer.
- [ ] `docs/WORKFLOW-ROADMAP.md` G5 `Measured:` line (Decided left for you).
Done when: the results file is saved and the gates are answered.
Commit: `Measure G5 on 24 briefs`

### Task 10: the docs describe stage C as built
Why: R12, A13.
- [ ] `docs/RECIPE-ROADMAP.md` §3: the stage C subgraph title "LLM picks from the table, code
      checks" and the 6–9 nodes as `llm` + check; rows 6–9 say what is built (table, one call or
      four, the check rules, the dose rule) with no "corpus popularity"; the `T` tie-break edge
      to S7 removed if no tie-break exists. `docs/WORKFLOW-ROADMAP.md`: M5 row ("LLM picks from a
      code-built table, checked by code"), G5 Decide line ("are the LLM's picks from the table
      what a brewer would choose?"), the M5 risk row (Special B, Lactobacillus) marked decided.
- [ ] `grep -n "popularity\|scored by code" docs/RECIPE-ROADMAP.md docs/WORKFLOW-ROADMAP.md` finds
      nothing about stage C.
- [ ] PROJECT.md §3 stays as it is (it already says what is built); §4 rows (Database functions,
      Scripts: `evals/fit_test.py`, the test count from a full `pytest` run with the stack up) and
      §8.
Done when: A13's grep is clean and the full suite passes.
Commit: `Describe stage C as built`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| YF-998, YF-999 load as `lacto` | `test_yeasts.py::test_lacto_cultures` | 1 |
| "Lactobacillus" finds the lacto cultures, brief words unchanged | `test_ingredient_resolver.py::test_lactobacillus_finds_lacto_cultures`, `test_type_words_change_no_brief_word` | 1 |
| "dark candi sugar" → Brown Candi Sugar | `test_adjuncts.py::test_dark_candi_sugar_alias` | 2 |
| Excluded products and siblings never reach the table | `test_choose_table.py::test_b16_excludes_siblings`, `test_b08_has_no_saaz` | 3 |
| A word with no product is absent, the rest is chosen | `test_choose_table.py::test_made_up_word_is_absent`, `test_choose_outputs.py::test_made_up_word_absent_rest_chosen` | 3, 6 |
| Every check rule refuses its bad proposal | `test_choose_check.py` (one test per rule) | 4 |
| The LLM cannot set a dose; code's dose follows the role rule | `test_choose_check.py` dose test, `test_misc_dose_rule`, `test_choose_outputs.py::test_dose_set_by_code` | 4, 6 |
| Fit rule: prompt + 4096 ≤ num_ctx, no truncation, both tries | `test_fit_test.py` | 5 |
| Outputs carry only table rows | `test_choose_outputs.py::test_outputs_use_table_rows_only` | 6 |
| Steps 6–9 logged with valid contracts | `test_pipeline.py::test_steps_6_to_9_logged` | 7a/7b |
| Graders catch each A-criterion | `test_grade.py` step 6–9 and needs tests | 8 |

## Approved exceptions

None needed: imports go through the n8n CLI as OPERATIONS §5 says; no container is recreated.

## Deviations
- 2026-10-18 · Approach, Tasks 3, 4, 6: R5 checks the yeast against step 5's yeast band
  (`yeast_low_pct`–`yeast_high_pct`), not the beer band the brief first named — user decision
  (brief R5, A5 and Deviations updated). The resolver's culture-type word rule (Task 1) and the
  needs gap rule (Task 8) are confirmed by the user as planned.
- 2026-10-18 · Task 2: after reloading the adjunct loader, `loaders.fermentable_facts` is re-run (twice) — the adjunct loader nulls `max_pct`/`field_source` (documented load order); no plan text changed.
- 2026-10-18 · Task 3: `app.choose_table` also returns `style_name` and `characteristic_ingredients` (the prompt shows them and every prompt number must come from the table), `kind` on each `slots` and `inventory_words` entry, and `db/042` holds helper functions beyond the four listed — implementation detail, no scope change.
- 2026-10-18 · Task 4: R5's band rule skips a wanted or inventory yeast and applies only when a usable (non-lacto, lager/family-fitting) yeast reaches the band, so it cannot clash with R3; a hop's boil minutes map to the table's own boil choice (largest `minutes` not above); `db/043` also holds helpers `choose_row`, `choose_names`, `choose_pick_errors` — implementation detail, no scope change.
- 2026-10-19 · Task 5: the one call runs at `num_ctx` 32768, not 8192 — the prompts are 16.6k-26.6k tokens and Ollama refuses (HTTP 400) a prompt longer than `num_ctx`, so 8192 and 16384 fit none of 24; `evals/fit_test.py` counts that refusal as a try that does not fit. `shared/prompts/choose.system.md` was revised once (zero pct/share, roasted-malt maximum) after 22 of 24 passed; revision 1 passes 24 of 24. The step-1 to step-6 model switch costs about 4 s of reload.
