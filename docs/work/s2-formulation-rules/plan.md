# S2 · Formulation rules and ingredient data — implementation plan

Stage: implementing
Brief: [brief.md](brief.md)
Branch: s2-formulation-rules

## Approach

Three pieces, built in this order, each with its own tests:

1. **Ingredient data.** `ref.fermentable` gets `enzyme_activity`, `min_boil_min`, `description`
   and `description_ref` (page or URL inside the description's source); two new tables hold the
   substitute pairs and each malt's typical styles. `role` already exists (`db/012_style_fit.sql`,
   0/81 filled). Every value is typed into one hand-checked data file,
   `loaders/fermentable_facts.toml`, and loaded by `loaders/fermentable_facts.py`, the same way
   `loaders/malt_products.py` holds the malt map. The loader writes only its own columns, merges
   its keys into `field_source` (`field_source || new`), and is re-runnable. **Load order:**
   `loaders.malts` and `loaders.adjuncts` rewrite `max_pct` and `field_source` wholesale, so
   `loaders.fermentable_facts` must run after them (said in its docstring and in DATABASE.md).
2. **The rules, written once.** `db/031_formulation_rules.sql` holds `app.formulation_limits()`
   (every threshold, as jsonb) and `app.formulation_rules()` (one row per rule: number, checked
   or not, sentence). Each sentence is built with `format()` from the limits, so the text and the
   check cannot disagree (R9). PROJECT.md links this file.
3. **The check.** `db/032_formulation_check.sql` has small helpers (`app.ebc_mid`,
   `app.mash_attenuation`), one function per checked rule (`app.check_rule_1` … `_13`, no rule 7)
   and `app.check_recipe(recipe jsonb) returns jsonb`, which resolves the `ref` rows, computes
   OG, FG, ABV, SRM and IBU with s1's functions only (`solve_grist`, `og`, `fg`, `abv`,
   `grist_mcu`, `srm`, `preboil_volume`, `boil_gravity`, `ibu`), then calls each rule. Each rule
   is explicit SQL a reader can follow (§6.8); there is no rule table. Input and output have JSON
   Schemas in `shared/contracts/formulation_check.*.schema.json`.

The 22 reference recipes are a TOML fixture in `tests/fixtures/`, naming ingredients by
producer and name; the test resolves them to ids and runs the check. The roadmap and brief notes
(R17, R19–R21) are docs only and go first.

Two **stop points** where the implementing subagent returns `needs-input` and waits for the
orchestrator to ask the user: Task 4 (Sprau's role, every `min_boil_min` above 60, the style
name → code mapping) and Task 8 (the 22 reference recipes and any rule failure). Nothing in
those tasks is loaded or committed before the answer.

### Decisions this plan makes (implementation details, open to change at approval)

- **Weyermann "medium" enzyme activity → `normal`.** The brief's scale is none · low · normal ·
  high; Weyermann prints none · low · medium · high. Acidulated's line ("increases enzyme
  activity by optimal mash pH") states no level, so it stays empty and is listed.
- **`min_boil_min` proposal:** `role = 'base'` and EBC midpoint below 5 → 90, else 60 (HTB
  p. 177: "A 90-min. boil is recommended for pale lagers that use a majority of Pilsner malt";
  p. 59: "60–90 minutes is considered the norm"). Both cite `palmer-how-to-brew`. A row with no
  EBC gets 60. The user confirms every 90 at the Task 4 stop.
- **Sources:** chart-group roles cite the new chart source; R1's list placements, adjunct and
  sugar roles, the 18 `max_pct` values and the user-decision substitutes cite `user-supplied`.
- **Rule 9's "is the midpoint"** allows a rounding tolerance equal to s1's test tolerances
  (OG 0.001, FG 0.002, ABV 0.1, IBU 1, SRM 1). These numbers are in the limits and the text.
- **Rule 10's "target FG range"** is the style's FG range, or the target FG ± 0.002 when the
  user stated the FG or the ABV (user decision, 2026-10-15).
- **Numbers.** `mashed` is false for role `sugar`, true otherwise (brief Assumption). Colour
  uses the EBC midpoint; when any fermentable has no EBC, SRM is `null` and the missing field is
  named. IBU needs hop amounts, which the LLM does not propose: each hop item may carry `g`, and
  IBU is computed only when every hop has it (hop `alpha_pct` midpoint), else `null`. No rule
  reads SRM or IBU. Mash temperatures outside 64–69 °C fail rule 10, and the numbers then use
  the nearest bound.
- **Bad input raises** (as s1's functions do): an unknown or wrong-kind `ingredient_id`, a
  duplicate fermentable, a style code not in `ref.beer_style`, or fermentable percentages whose
  sum is more than 0.1 away from 100.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `docs/RECIPE-ROADMAP.md` | changed | §9 D7 row decided (R17); §8 Later as a list (R20) |
| `docs/WORKFLOW-ROADMAP.md` | changed | S2 row and node point to this work (R19); s2 → s3 arrow and chain text marked (R21) |
| `docs/work/m4-targets-blueprint/brief.md`, `docs/work/m5-choose-ingredients/brief.md`, `docs/work/s3-style-fit/brief.md` | changed | one line under Needs (R21) |
| `db/010_ref_schema.sql` | changed | new columns, `ref.fermentable_substitute`, `ref.fermentable_substitutes` view, `ref.fermentable_style` |
| `db/011_ref_sources.sql` | changed | `ref.source` row for the substitution chart |
| `loaders/fermentable_facts.toml` | new | roles, 18 `max_pct`, enzyme activity, long boils, substitutes, descriptions, style names and the name → code map |
| `loaders/fermentable_facts.py` | new | reads the TOML, checks it, loads it (`python -m loaders.fermentable_facts`) |
| `db/031_formulation_rules.sql` | new | `app.formulation_limits()`, `app.formulation_rules()` |
| `db/032_formulation_check.sql` | new | helpers, rule functions, `app.check_recipe` |
| `shared/contracts/formulation_check.input.schema.json`, `…output.schema.json` | new | check contract (R15) |
| `tests/test_fermentable_facts.py` | new | data and load tests (A1–A6) |
| `tests/test_formulation_rules.py` | new | rule text tests (A7) |
| `tests/test_formulation_check.py` | new | check tests (A8–A11, A14, A15) |
| `tests/fixtures/reference_recipes.toml` | new | 22 reference recipes (R16) |
| `tests/test_reference_recipes.py` | new | fixtures pass the check (A12) |
| `tests/test_contracts.py` | changed | knows the two new contract files |
| `docs/work/s2-formulation-rules/report.md` | new | data report: rows with no enzyme activity, confirmed long boils, dropped style names, fixture review |
| `docs/DATABASE.md`, `PROJECT.md` | changed | status, new columns and tables, rule list link, §8 entries |

## Tasks

### Task 1: Roadmaps and draft briefs record that s2-corpus is gone
Why: R17, R19, R20, R21 (A13, A16). Docs only, no dependency on code.
- [x] `docs/RECIPE-ROADMAP.md` §9: D7 row says decided 2026-10-14, in PROJECT.md §3's words: no
      ratio corpus; the LLM proposes, code scales and checks; revisit if test briefs show a need.
      Link [`s2-formulation-rules`](work/s2-formulation-rules/brief.md).
- [x] `docs/RECIPE-ROADMAP.md` §8 table, row **Later**: turn the "Do" cell into a short list
      (`<br>`-separated bullets in the cell): keep inventory-first mode, substitutions, batch
      log → feedback, whirlpool and dry-hop IBU; add "an enzyme rule using `enzyme_activity`",
      "the ratio corpus (old s2), revisited only if test-brief results show generic or off
      recipes", and "TODO: replace rule 10's uncited linear mash-temperature mapping with a cited
      model of mash temperature's effect on attenuation (for example *How to Brew*'s mash
      chapter, via a doc → calc pass)".
- [x] `docs/WORKFLOW-ROADMAP.md` §1 table: S2 row links
      [`s2-formulation-rules`](work/s2-formulation-rules/brief.md); Builds = "Fermentable roles,
      limits, enzyme activity, minimum boil, substitutes, descriptions; 13 formulation rules and
      the rule check; 22 reference recipes (D7 decided)"; Needs = s1; Checkpoint = "— (brief
      A1–A16)". Mermaid node `S2` label becomes `s2 · Formulation rules + ingredient data (D7)`.
- [x] Same file: the `S2 --> S3` edge becomes
      `S2 -. "s2-corpus abandoned 2026-10-14; revisit in s3" .-> S3`, and the sentence
      "s1 → s2 → s3 is a chain (…)" gets "(s2-corpus abandoned 2026-10-14; revisit in s3)" after
      "chain".
- [x] Add exactly the line `s2-corpus abandoned 2026-10-14; revisit in this brief` directly under
      the `Needs:` line (line 7) of the m4, m5 and s3 briefs. Nothing else in those files.
- [x] Run `git diff --stat docs/work/m4-targets-blueprint docs/work/m5-choose-ingredients docs/work/s3-style-fit`,
      expect 3 files, 3 insertions, 0 deletions; `test -d docs/work/s2-corpus` fails;
      `grep -n "D7" PROJECT.md` shows no §7 row.
- [x] PROJECT.md §8 line.
Done when: A13 (except the data parts) and A16 hold.
Commit: `Record D7 and s2-corpus notes in roadmaps`

### Task 2: Schema for the new fermentable data
Why: R3, R4, R5, R6, R7, R8 (A3 constraints).
- [x] Append to `db/010_ref_schema.sql` (idempotent, `if not exists` / `drop … if exists`):
  ```sql
  alter table ref.fermentable
      add column if not exists enzyme_activity text
          check (enzyme_activity in ('none', 'low', 'normal', 'high')),
      add column if not exists min_boil_min integer check (min_boil_min between 60 and 120),
      add column if not exists description text,
      add column if not exists description_ref text;  -- page or URL inside field_source.description
  -- One row per substitute pair, stored once (smaller id first); counts both ways, never chains.
  create table if not exists ref.fermentable_substitute (
      fermentable_id bigint not null references ref.fermentable (ingredient_id) on delete cascade,
      substitute_id  bigint not null references ref.fermentable (ingredient_id) on delete cascade,
      source_id      bigint not null references ref.source (id),
      note           text   not null,  -- chart row ("1C row 9") or "user decision D, 2026-10-14"
      primary key (fermentable_id, substitute_id),
      check (fermentable_id < substitute_id));
  create or replace view ref.fermentable_substitutes as  -- both directions
      select fermentable_id, substitute_id, source_id, note from ref.fermentable_substitute
      union all
      select substitute_id, fermentable_id, source_id, note from ref.fermentable_substitute;
  -- Typical styles a maltster names for a malt, mapped to our style rows (R7).
  create table if not exists ref.fermentable_style (
      ingredient_id bigint not null references ref.fermentable (ingredient_id) on delete cascade,
      style_id      bigint not null references ref.beer_style (id),
      source_id     bigint not null references ref.source (id),
      primary key (ingredient_id, style_id));
  ```
- [x] Append to `db/011_ref_sources.sql`'s insert: slug `malt-substitution-2025`, title
      `PrimeTime Malt Substitution Chart`, edition `2025 (short)`, publisher `Hops Shop BG`
      (printed "© Hops Shop BG, 2025"), url null, notes
      `shared/rag-files/pending/PrimeTime Malt Substitution Chart 2025 short.pdf`.
- [x] Apply both files twice as `postgres` (OPERATIONS §4); no errors.
- [x] Write stack test `tests/test_fermentable_facts.py::test_schema`: the 4 columns exist, the
      two check constraints reject `'medium'` and `30` (inside a rolled-back transaction), both
      tables and the view exist and are owned by `postgres`, the chart source row exists.
- [x] Run `pytest tests/test_fermentable_facts.py`, expect pass.
- [x] DATABASE.md: `fermentable` row lists the new columns; add rows for the two tables and the
      view. PROJECT.md §8 line.
Done when: the catalog shows the columns, constraints, tables and view, owned by `postgres`.
Commit: `Add fermentable formulation columns and tables`

### Task 3: Loader with roles, limits, enzyme activity and substitutes
Why: R1, R2, R3, R4, R5, R8 (A1, A2, A3, A4 data side). Not loaded yet.
- [x] Create `loaders/fermentable_facts.toml`. One `[[fermentable]]` table per row of the 81,
      keyed by `producer` (`""` for the 7 adjuncts) and `name` exactly as in `ref.ingredient`.
      Fields: `role`, `role_source`, `role_note` (chart group and row, or "R1 list"),
      optional `max_pct` + `max_pct_basis` (only the 18), optional `enzyme_activity` +
      `enzyme_source` + `enzyme_ref`, optional `min_boil_min` (only confirmed values above 60),
      and (Task 4) `description`, `description_source`, `description_ref`, `style_names`,
      `styles_source`. Then `[[substitute]]` tables: `a = [producer, name]`, `b = [...]`,
      `source`, `note`.
- [x] **Roles** (R1). Chart groups, read from the chart PDF (`pdftotext -layout`; page 1 rows
      5–6 of 1D are one merged cell, checked as an image): 1A → base, 1B → kilned, 1C → crystal,
      1D → roast, source `malt-substitution-2025`:
      - base (1A): Weyermann Extra Pale Premium Pilsner, Pilsner, Vienna, Pale Ale; Viking
        Pilsner, Vienna, Pale Ale.
      - kilned (1B): Weyermann Munich Type 1, Munich Type 2, Melanoidin, Abbey, Beech Smoked
        Barley; Viking Munich Light, Munich Dark, Red Active, Red Ale.
      - crystal (1C): Weyermann Carapils, Carahell, Carabelge, Carared, Caraamber, Caramunich
        Type 1/2/3, Carabohemian, Special W, Caraaroma; Viking CaraBody, Caramel Pale, Golden
        Ale, Dextrin, Caramel 30, 50, 100, 150, 300, 400, 600.
      - roast (1D): Weyermann Carafa Type 1/2/3, Carafa Special Type 1/2/3, Roasted Barley;
        Viking Cookie, Chocolate Light, Chocolate Dark, Black, Roasted Barley.

      R1 list, source `user-supplied`, note "R1 list (user decision Q2, 2026-10-15)":
      - base: Weyermann Wheat Malt Pale, Rye Malt Pale, Spelt, Oak Smoked Wheat, Eraclea
        Pilsner, Bohemian Pilsner; Viking Wheat, Rye, Smoked Wheat, Lightly Peated, Enzyme;
        Simpsons Finest Pale Ale Golden Promise, Finest Pale Ale Maris Otter.
      - kilned: Weyermann Wheat Malt Dark, Acidulated; Viking Smoked Malt (cherry wood),
        Smoked Malt (pear wood).
      - crystal: Weyermann Carawheat; Viking Caramel 200; Simpsons Crystal Extra Dark,
        Crystal T50, DRC.
      - roast: Weyermann Chocolate Wheat Malt.
      - adjunct: Flaked Oats, Flaked Barley, Flaked Corn, Flaked Rice. sugar: Honey, Brown Candi
        Sugar, Lactose.
      - Viking Sprau Malt: left without `role` until the Task 4 stop.

      Expected counts with Sprau open: base 20, kilned 13, crystal 27, roast 13, adjunct 4,
      sugar 3.
- [x] **max_pct** (R2), exactly decision E, `max_pct_source = "user-supplied"` and a
      `max_pct_basis` per value: Viking Munich Light 100, Munich Dark 100,
      Lightly Peated 100, Smoked Wheat 100; Caramel 30 and 50 → 20; Caramel 100, 150, 200 → 15;
      Caramel 300, 400, 600 → 10; Flaked Oats 30, Flaked Barley 20, Flaked Corn 20, Honey 20,
      Brown Candi Sugar 20, Lactose 10. The user has not given the per-value basis yet: draft
      each `max_pct_basis` from what the repo and catalogues show (one of Viking catalogue,
      *How to Brew* estimate, forum consensus, recipe range, with the page or text where found),
      or `"unplaced"` when nothing supports one. The user confirms them at the Task 4 stop;
      `check()` raises on `"unplaced"`, so nothing loads before that.
- [x] **Enzyme activity** (R3) from the Weyermann catalogue's "Enzyme activity:" line per malt
      (none, low, high as printed; medium → normal) with the page as `enzyme_ref`; from the
      Viking text: Munich Light/Dark "clearly reduced" → low (p. 23), Caramel 30–600 "zero" →
      none (p. 24), plus any other Viking page that states a level in words. Every other row has
      no `enzyme_activity`.
- [x] **Substitutes** (R5). Chart pairs, source `malt-substitution-2025`, note = group and row
      (19): 1A Pilsner↔Pilsner (row 2), Vienna↔Vienna (4), Pale Ale↔Pale Ale (5); 1B Munich
      Type 1↔Munich Light (1), Munich Type 2↔Munich Dark (2), Melanoidin↔Red Ale (5); 1C
      Carapils↔CaraBody (1), Carahell↔Caramel 30 (5), Carared↔Caramel 50 (7), Caramunich Type
      1↔Caramel 100 (9), Caramunich Type 3↔Caramel 150 (11), Special W↔Caramel 300 (13),
      Caraaroma↔Caramel 400 (14); 1D Carafa Type 1↔Chocolate Dark (4), Carafa Type 2↔Black
      (5–6, merged cell), Carafa Type 3↔Black (5–6), Roasted Barley↔Roasted Barley (9); 2A
      Wheat Malt Pale↔Wheat Malt (2); 2B Rye Malt Pale↔Rye Malt (1). (Left side Weyermann,
      right side Viking.) User decision D, source `user-supplied`, note "user decision D,
      2026-10-14": Eraclea Pilsner↔Viking Pilsner, Bohemian Pilsner↔Viking Pilsner, Crystal
      Extra Dark↔Caraaroma, DRC↔Special W, Golden Promise↔Weyermann Pale Ale, Golden
      Promise↔Viking Pale Ale, Maris Otter↔Weyermann Pale Ale, Maris Otter↔Viking Pale Ale
      (both Pale Ales, user decision 2026-10-15). 27 pairs in all. None for Viking Caramel 200,
      the smoked malts, Sprau, Crystal T50.
- [x] Create `loaders/fermentable_facts.py`: `read(path) -> dict`; `check(data, rows)` raises on
      a name not in `ref.ingredient`, a role/enzyme value outside the allowed sets, a source slug
      not in `ref.source`, a `max_pct` on a row that is not one of the 18, a `min_boil_min` above
      60 that `propose_min_boil` did not propose, a pair listed twice or with itself;
      `propose_min_boil(role, ebc) -> int` (Approach rule); `load(conn, data)` updates only the
      loader's columns, `field_source = field_source || <its keys>`, writes `max_pct` only for
      the 18 and raises if one of them already holds a value from another source, replaces the
      two tables' rows from the file (delete + insert inside the transaction), and sets
      `min_boil_min` on every row (60 unless the file says otherwise, source
      `palmer-how-to-brew`). `main()` with `--propose-min-boil` prints the rows the proposal sets
      above 60 and loads nothing. Docstring states the load order.
- [x] Write unit tests in `tests/test_fermentable_facts.py`: `test_roles_match_r1` (the full
      expected role per row from the lists above, and the counts), `test_max_pct_is_decision_e`
      (exactly the 18 values), `test_substitute_pairs` (exactly the 27 pairs above, no
      duplicates, none for the R5 no-substitute rows), `test_enzyme_medium_is_normal`,
      `test_propose_min_boil` (Pilsner 3.5 base → 90, Pale Ale 6.5 base → 60, crystal 3 → 60,
      no EBC → 60, open range `(,8]` uses 8), `test_every_value_names_a_source`,
      `test_check_rejects_unknown_name`.
- [x] Run `pytest tests/test_fermentable_facts.py`, expect pass. PROJECT.md §8 line.
Done when: the data file holds every decided value and the tests pass; nothing is loaded.
Commit: `Add fermentable facts loader and decided data`

### Task 4: Descriptions and typical styles; review stop; load
Why: R1 (Sprau), R4, R6, R7, R8 (A1–A6).
- [x] **Descriptions** (R6), one to three sentences in English, what the malt adds and causes and
      its recommended use, never copied at length:
      - Weyermann (37): description, sensory, typical styles, recommended addition and enzyme
        activity from `WEYERMANN-PRODUCTS-Brewery-EN.pdf`; `description_ref` = printed page.
      - Viking (32): "Malt character" and "Applications" from
        `VikingMalt_Standard_Portfolio_2023.pdf`; Sprau is not in the 2023 portfolio, so its
        description comes from its hopline page (`raw->'hopline-malts'`, URL as ref).
      - Simpsons (5): its one line in `simpsons-malt-nexthop-product-range-nov25.pdf`.
      - Adjuncts and sugars (7): summarised in English from the hopline adjunct page text
        (`raw->'hopline-adjuncts'`, Hungarian; URL as ref); Honey from *How to Brew* (printed
        page; PDF page − 26).
- [x] **Style names** (R7): each malt's `style_names` as printed (Weyermann's "typically for"
      list, Viking's "Applications" text, Simpsons' hopline "Ajánlott sörtípusok"), with
      `styles_source`. One `[style_names]` table maps every distinct printed name to one
      `ref.beer_style` code (BJCP 2021 or BA 2026) or to `""` (dropped), closest style we use per
      decision H. `check()` raises on a code not in `ref.beer_style` (stack test
      `test_style_codes_exist`).
- [x] Run `python -m loaders.fermentable_facts --propose-min-boil`. Write the draft of
      `docs/work/s2-formulation-rules/report.md`: rows with no stated enzyme activity; the
      proposed long boils; the full style name → code table with dropped names marked; the 18
      `max_pct` values with the drafted basis and where it was found.
- [x] **Stop (needs-input).** Return to the orchestrator with four questions:
      1. Sprau Malt's role. Options: a) adjunct, b) base, c) kilned. Recommend a): hopline calls
         it a malted field bean ("malátázott mezei bab"), max 15 %.
      2. Each proposed `min_boil_min` above 60 (the list from the command): confirm or set 60.
      3. The style name → code table in report.md: approve, or the user's changes.
      4. The basis of each of the 18 `max_pct` values (table in report.md): confirm the drafted
         basis or give the right one (Viking catalogue, *How to Brew* estimate, forum
         consensus, recipe range); a value the user cannot place gets "user decision E,
         2026-10-14". The source stays `user-supplied` for all 18.
      Load nothing and commit nothing before the answers.
- [x] Apply the answers in the TOML (`role` for Sprau; `min_boil_min = 90` only on confirmed
      rows; the mapping as approved; the 18 `max_pct_basis` values). Record them in report.md and in plan Deviations if any
      differs from this plan.
- [x] Before loading, record the 63 untouched `max_pct` values:
      `select md5(string_agg(ingredient_id || ':' || max_pct || ':' || (field_source->>'max_pct'), ',' order by ingredient_id)) from ref.fermentable where max_pct is not null;`
      Run `python -m loaders.fermentable_facts`; run the same query restricted to the 63 ids
      (`and field_source->>'max_pct' <> 'user-supplied'`), expect the same md5.
- [x] Run the loader a second time; this checksum is equal before and after (A6):
      `select md5(string_agg(t::text, '|' order by t::text)) from (select f::text from ref.fermentable f union all select s::text from ref.fermentable_substitute s union all select y::text from ref.fermentable_style y) t;`
- [x] Write stack tests: `test_db_roles` (81 non-null; the R1 table; Sprau as answered),
      `test_db_max_pct` (81/81; the 18 with `field_source.max_pct = 'user-supplied'` and a
      confirmed basis in the TOML, none `"unplaced"`),
      `test_db_enzyme_and_boil` (A3: rows above 60 equal the confirmed list; rows with no
      enzyme activity equal report.md's list), `test_db_substitutes` (A4: Eraclea → Viking
      Pilsner, DRC → Special W, none for Crystal T50, every pair found from both sides through
      the view, and for every malt no substitute that is reachable only through another
      substitute), `test_db_descriptions` (A5: 81 with description and its source, every
      `fermentable_style` row joins a style), `test_load_is_idempotent` (A6: checksum, `load()`,
      checksum, rollback).
- [x] Run `pytest tests/test_fermentable_facts.py`, expect pass. DATABASE.md fermentable row
      (counts measured), PROJECT.md §8 line.
Done when: A1–A6 hold on the live DB and the user's four answers are recorded.
Commit: `Load fermentable facts after user review`

### Task 5: The rule text and its limits, in one place
Why: R9, R10, R11 (A7).
- [x] Create `db/031_formulation_rules.sql` with `app.formulation_limits() returns jsonb`
      (immutable), keys: `max_fermentables` 5, `max_specialty` 3, `max_hop_varieties` 3,
      `crystal_dark_ebc` 60, `crystal_very_dark_ebc` 160, `dark_total_pct` 15,
      `crystal_total_pct` 25, `crystal_dark_pct` 10, `crystal_very_dark_pct` 5,
      `adjunct_sugar_pct` 40, `late_hop_max_min` 15, `mash_min_c` 64, `mash_max_c` 69,
      `min_boil_min` 60, `pct_sum_tolerance` 0.1, and `midpoint_tolerance`
      `{og 0.001, fg 0.002, abv 0.1, ibu 1, srm 1}`.
- [x] Same file: `app.formulation_rules() returns table (rule text, checked boolean, sentence text)`,
      rows `definitions`, `1`–`13`, `pending`. Each sentence is `format()` over the limits
      (`trim_scale` for numbers). Wording to use (numbers come from the limits):
      - definitions: "A share is a percentage of the total fermentable mass, sugars included. A
        fermentable's colour is the midpoint of its ebc range, or its one bound when the range
        is open. Role, max_pct, min_boil_min, fermentability, attenuation_pct, temp_c and
        alcohol_tolerance_pct are ingredient-table fields."
      - 1: "A recipe has at most 5 fermentables, and at most 3 of them have the role kilned,
        crystal or roast; fermentables with the role adjunct or sugar do not count toward the 3."
      - 2: "A recipe uses at most 3 hop varieties."
      - 3: "Fermentables with the role crystal and a colour above 60 EBC, plus fermentables with
        the role roast, are at most 15 % of the grist together."
      - 4: "Fermentables with the role crystal are at most 25 % of the grist together; those
        with a colour above 60 EBC at most 10 %; those with a colour above 160 EBC at most 5 %.
        Those at or below 60 EBC are limited only by rule 6."
      - 5: "Fermentables with the role adjunct or sugar are at most 40 % of the grist together."
      - 6: "Each fermentable is at most its max_pct share of the grist."
      - 7 (checked false): "The colour adjustment changes only the share of the fermentable with
        the darkest colour, and never one with the role crystal. Enforced by the colour solver
        in step 10, not by this check."
      - 8: "A recipe has exactly one bittering addition: a boil addition whose time equals the
        boil time. Every other hop addition is a boil addition of at most 15 min, a whirlpool
        addition or a dry hop."
      - 9: "A target OG, FG, ABV, IBU or SRM that the user did not state is the style's
        midpoint, within 0.001 for OG, 0.002 for FG, 0.1 % for ABV, 1 IBU and 1 SRM; OG and FG
        count as stated when the user stated the ABV. A target is outside the style's range
        only when the user stated it or style guidance is off."
      - 10: "The mash temperature is between 64 and 69 °C, and the FG predicted from the yeast's
        attenuation_pct, each fermentable's fermentability and the mash temperature is inside
        the target FG range: the style's FG range, or the target FG ± 0.002 when the user
        stated the FG or the ABV. The mash temperature maps linearly onto the yeast's
        attenuation_pct range: 64 °C gives the top of the range and 69 °C the bottom. This
        mapping is an uncited assumption."
      - 11: "The planned ABV is at most the yeast's alcohol_tolerance_pct, and the fermentation
        temperature is inside the yeast's temp_c range."
      - 12: "Every fermentable, hop and yeast in the recipe has a purpose that is not empty."
      - 13: "The boil time is at least the largest min_boil_min of the recipe's fermentables,
        and at least 60 min."
      - pending (checked false): "A recipe uses only processes the brewer profile allows.
        Pending: needs the brewer profile (step 0); not checked."
- [x] Apply twice; both functions owned by `postgres`.
- [x] Write stack tests `tests/test_formulation_rules.py`: `test_rules_listed` (definitions,
      1–13, pending; 7 and pending unchecked); `test_no_ingredient_or_style_name` (whole-word,
      case-insensitive match of every `ref.ingredient.name` and `ref.beer_style.name` against
      all sentences; an explicit exemption set holds only words that are rule vocabulary, today
      `crystal` (a role; also a hop name) and `target` (also a hop name), each with a comment);
      `test_no_vague_words` (some, usually, typically, about); `test_text_uses_the_limits`
      (each limit's value, formatted, appears in its rule's sentence; changing a limit in a
      rolled-back `create or replace` changes the sentence).
- [x] Run `pytest tests/test_formulation_rules.py`, expect pass. PROJECT.md: link the file from
      §3's D7 bullet ("rules: `select * from app.formulation_rules()`,
      [`db/031_formulation_rules.sql`](db/031_formulation_rules.sql)"); §8 line.
Done when: A7 holds.
Commit: `Add formulation rule text and limits`

### Task 6: The check: inputs, numbers and the grist rules 1–6
Why: R11, R12, R13, R14, R15 (A8 for rules 1–6, A9, A11, A15).
- [x] Write the contracts. Input (`formulation_check.input`), all top-level properties
      required, `additionalProperties: false`: `style_code` string; `guidance` boolean;
      `stated` object of optional numbers `og fg abv ibu srm`; `targets` object with required
      numbers `og fg abv ibu srm`; `batch` `{volume_l, efficiency_pct, boil_off_l_h, losses_l}`;
      `mash_c`, `boil_min` numbers; `fermentables` array of `{ingredient_id, pct, purpose}`;
      `hops` array of `{ingredient_id, usage: boil|whirlpool|dry_hop, minutes, purpose, g?}`;
      `yeast` `{ingredient_id, ferm_c, purpose}`. Output (`formulation_check.output`):
      `calc_version`; `numbers` `{og, fg, abv, srm, ibu, attenuation_pct, missing[]}` (each
      number nullable); `results` array of `{rule, status: pass|fail|unknown, message,
      failures: [{text, items: [{ingredient_id, name}], value, limit}], missing: [string]}`.
- [x] `tests/test_contracts.py`: add both names to `NAMES`; the `run_id` requirement applies to
      names starting with `step` only; `ABSENT_SLOTS["formulation_check.output"] =
      [("results.status", "enum:unknown"), ("numbers.fg", "null")]`; one good and one bad
      example each.
- [x] Create `db/032_formulation_check.sql` (header like `db/030_maths.sql`; needs 010, 015,
      030, 031):
      - `app.ebc_mid(ebc numrange) returns numeric`: midpoint; one bound when the other is
        open; null for null.
      - `app.mash_attenuation(attenuation numrange, mash_c numeric) returns numeric`:
        top − (mash_c − 64) / 5 × (top − bottom), mash_c clamped to 64–69; comment says
        "uncited assumption, rule 10; cited model on RECIPE-ROADMAP §8 Later".
      - `app.check_recipe_items(recipe jsonb) returns jsonb`: resolves each item's `ref` row
        (name, role, ebc_mid, max_pct, min_boil_min, fermentability, extract, alpha mid; yeast
        attenuation, temp_c, alcohol tolerance) and raises on the bad inputs listed in
        Approach.
      - `app.check_rule_1` … `app.check_rule_6(items jsonb) returns jsonb`, one result object
        each, limits read from `app.formulation_limits()`. Messages name the rule, the items with
        their shares, the measured value and the limit, e.g. "Rule 3: crystal above 60 EBC plus
        roast is 18 % of the grist (Caraaroma 10 %, Carafa Special Type 2 8 %); the limit is
        15 %." Never another ingredient. Missing `max_pct` → `unknown` naming
        `ref.fermentable.max_pct`.
      - `app.check_recipe(recipe jsonb) returns jsonb`: items; numbers (`solve_grist` at the
        target OG, then `og`, `fg` at `mash_attenuation`, `abv`, `grist_mcu` + `srm`, and `ibu`
        via `preboil_volume` and `boil_gravity` when every hop has `g`); results for the rules
        built so far, in rule order.
- [x] Apply twice; functions owned by `postgres`.
- [x] Write stack tests `tests/test_formulation_check.py` (a passing base recipe built in the
      test from ids looked up by name): for each of rules 1–6 one recipe that passes and one that
      fails exactly that rule (and passes rules 1–6 otherwise) (A8); limits at the boundary pass
      (25 % crystal) and just above fail; `test_failure_names_rule_items_value_limit` and
      `test_failure_names_no_other_ingredient` (every ingredient name in any message is in the
      recipe) (A9); `test_numbers_equal_s1` (OG, FG, ABV, SRM, IBU equal direct calls of the
      s1 functions on the same kg, attenuation and volumes) and `test_lactose_raises_fg` (A11);
      `test_input_and_output_match_schemas` (pg_jsonschema) (A11);
      `test_ebc_mid` (Caraamber `[60,80]` → 70 counts as above 60, Carared `[40,60]` → 50 does
      not, `(,8]` → 8) (A15); `test_bad_input_raises` (unknown id, hop id in fermentables,
      percentages summing to 95).
- [x] Run `pytest tests/test_formulation_check.py tests/test_contracts.py`, expect pass.
      PROJECT.md §8 line.
Done when: rules 1–6 return pass, fail and unknown as specified; numbers match s1.
Commit: `Add recipe check with numbers and grist rules`

### Task 7: The check: hop, target, mash, yeast, purpose and boil rules
Why: R10 rules 8–13, R14 (A8 for rules 8–13, A10, A14).
- [x] Add to `db/032_formulation_check.sql`, each a single explicit function taking the
      resolved items and the recipe:
      - rule 8: count boil additions with `minutes = boil_min` (must be 1); every other addition
        is whirlpool, dry_hop, or boil with `minutes ≤ 15`.
      - rule 9: style ranges from `ref.beer_style` by `style_code`; for each of og, fg, abv,
        ibu, srm: if not stated (OG and FG count as stated when `stated.abv` is present), the
        target must be within the tolerance of the range midpoint; a target outside the range
        fails unless stated or `guidance` is false. A style range that is null → `unknown`
        naming `ref.beer_style.<field>`.
      - rule 10: mash_c inside 64–69, and the predicted FG inside the target FG range (style FG
        range, or target FG ± 0.002 when FG or ABV is stated). Yeast without `attenuation_pct`
        → `unknown` naming `ref.yeast.attenuation_pct`; style without FG and FG not stated →
        `unknown` naming `ref.beer_style.fg`.
      - rule 11: planned ABV (`numbers.abv`) ≤ `alcohol_tolerance_pct`; `ferm_c` inside
        `temp_c`. A fail in either part fails; otherwise a missing field (tolerance, or ABV
        missing because attenuation is) makes it `unknown`.
      - rule 12: every fermentable, hop and yeast `purpose` non-empty after trimming.
      - rule 13: `boil_min ≥ max(min_boil_min)` and `≥ 60`; a null `min_boil_min` → `unknown`.
- [x] `app.check_recipe` returns all 12 checked rules (1–6, 8–13) in order.
- [x] Apply twice. Write tests in `tests/test_formulation_check.py`: pass and fail per rule
      8–13 (A8), including rule 9 cases for a stated ABV above the range (b17-like, passes), an
      unstated IBU off the midpoint (fails) and an out-of-range SRM with guidance off (passes);
      `test_rule_10_unknown_without_attenuation` (a yeast with null `attenuation_pct`, e.g.
      Gozdawa W-34/70; result names the field) (A10); `test_mash_mapping` (SafAle US-05
      `[78,82]`: 64 °C → 82, 69 °C → 78, 66.5 °C → 80, and rule 10's sentence contains
      "uncited assumption") (A14); `test_results_cover_checked_rules` (12 results, numbers
      1–6 and 8–13).
- [x] Run `pytest tests/test_formulation_check.py tests/test_formulation_rules.py`, expect pass.
      PROJECT.md §8 line.
Done when: A8, A10 and A14 hold.
Commit: `Add recipe check rules for hops, targets and yeast`

### Task 8: Reference recipes for the 22 test briefs; review stop
Why: R16 (A12).
- [ ] Draft `tests/fixtures/reference_recipes.toml`: one `[[recipe]]` per brief in
      `evals/recipe_briefs.toml`, fields `brief`, `style_code` (the brief's `style`; for b12,
      whose 31B has no vitals in `ref.beer_style`, the first alternative with vitals, 18A, with
      a comment), `guidance`, `stated` (the brief's numbers except `batch_l`), `targets`
      (midpoints, or the stated numbers; OG/FG chosen so `app.abv` gives a stated ABV), `batch`
      (`volume_l` = the brief's `batch_l` or 20; efficiency 72, boil-off 4 L/h, losses 2 L,
      labelled as fixture assumptions), `mash_c`, `boil_min`, `[[recipe.fermentable]]`
      (`producer`, `name`, `pct`, `purpose`), `[[recipe.hop]]` (`name`, `usage`, `minutes`,
      `g`, `purpose`), `[recipe.yeast]` (`producer`, `name`, `ferm_c`, `purpose`). Built only
      from `ref` rows, guided by each brief's `needs`, `wanted`, `excluded` and `inventory`, and
      by the descriptions and typical styles from Task 4. A comment at the top: test data only,
      never in a prompt.
- [ ] Write `tests/test_reference_recipes.py`: every brief has exactly one recipe; names resolve
      to `ref` rows; the input matches the contract; every rule passes, except entries in an
      explicit `ACCEPTED_FAILURES` dict (brief, rule, user's decision, date), empty until the
      user decides otherwise; no file under `shared/prompts/` or `n8n/workflows/` mentions
      `reference_recipes`.
- [ ] Run it and add a section to report.md: each recipe as a short table (grist %, hops,
      yeast, mash, boil, targets, computed numbers) and every rule that does not pass, with its
      message. Also note: under rule 9 as written, hint words ("bitter", "darker") do not move
      a target off the midpoint, so b01's IBU sits at 21A's midpoint.
- [ ] **Stop (needs-input).** Return to the orchestrator: the user reviews the 22 recipes in
      report.md; for each failure, options a) change the recipe, b) change the threshold
      (a change to R10, so it also updates the brief and plan Deviations), c) accept the failure
      for that brief. Commit nothing before the answer.
- [ ] Apply the answers (recipe edits; a threshold change goes into `app.formulation_limits()`
      with its test; accepted failures into `ACCEPTED_FAILURES`), re-run, record the review date
      in report.md.
- [ ] Run `pytest tests/test_reference_recipes.py`, expect pass. PROJECT.md §8 line.
Done when: A12 holds: 22 reviewed recipes, each passing every rule or with the user's decision.
Commit: `Add reviewed reference recipes for 22 briefs`

### Task 9: Project status and full test run
Why: PROJECT.md §10, CLAUDE.md.
- [ ] Run the full suite `pytest` with the stack up and `pytest -m "not stack"`; note both
      counts and the time.
- [ ] PROJECT.md §4 Database row (role, `max_pct`, new columns and tables, rules and check,
      measured counts) and Scripts row (the new loader and test files with counts); §5 malt and
      adjunct rows (descriptions, roles); remove "`fermentable.role` stays empty until P3" where
      it appears in PROJECT.md and DATABASE.md; RECIPE-ROADMAP §8 P3 notes D7 settled. §8 line
      with the measured numbers; "Last updated" date.
- [ ] Re-check A13: `grep` shows RECIPE-ROADMAP §9 D7 decided, §8 Later list with the 3 items,
      the WORKFLOW-ROADMAP S2 link, no D7 in PROJECT.md §7, no `docs/work/s2-corpus/`.
Done when: PROJECT.md describes what is running, with measured numbers.
Commit: `Record s2-formulation-rules status`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Every fermentable's role is R1's (wrong role = wrong rule result) | `test_fermentable_facts.py::test_roles_match_r1`, `::test_db_roles` | 3, 4 |
| The 18 `max_pct` equal decision E; the 63 others untouched | `::test_max_pct_is_decision_e`, `::test_db_max_pct`, md5 step | 3, 4 |
| Substitutes count both ways, never chain | `::test_substitute_pairs`, `::test_db_substitutes` | 3, 4 |
| A long boil is loaded only if proposed and confirmed | `::test_propose_min_boil`, `::test_db_enzyme_and_boil` | 3, 4 |
| Every style code exists | `::test_style_codes_exist`, `::test_db_descriptions` | 4 |
| Load twice gives the same rows | `::test_load_is_idempotent` | 4 |
| Rule text and check share their thresholds; no names, no vague words | `test_formulation_rules.py` | 5 |
| Each rule passes and fails as written, at its boundary | `test_formulation_check.py` per rule | 6, 7 |
| Colour thresholds use the EBC midpoint / open bound | `::test_ebc_mid` | 6 |
| Numbers come from s1 only; lactose stays in FG | `::test_numbers_equal_s1`, `::test_lactose_raises_fg` | 6 |
| Missing data gives `unknown`, never pass or fail | `::test_rule_10_unknown_without_attenuation`, rule 6/9/13 unknown cases | 6, 7 |
| Mash temperature maps 64 → top, 69 → bottom | `::test_mash_mapping` | 7 |
| A failure never names an ingredient outside the recipe | `::test_failure_names_no_other_ingredient` | 6 |
| Input and output match their contracts | `test_contracts.py`, `::test_input_and_output_match_schemas` | 6 |
| The reviewed reference recipes pass | `test_reference_recipes.py` | 8 |

## Approved exceptions

None.

## Deviations
- 2026-10-15 · Plan (draft): the user answered the plan's three questions with the recommended
  options: `max_pct` basis per value with a review stop in Task 4 (no per-value basis given yet);
  rule 10's target FG range as the Approach states; Golden Promise and Maris Otter pair with both
  Pale Ales (27 pairs). Brief R2, R5 and R10 rule 10 clarified to match.
- 2026-10-15 · Task 3: `check(data, rows, sources, allow_unplaced=False)` takes the ref source slugs and
  an `allow_unplaced` switch (tests read the file with it on; `load` never does) — the plan's
  `check(data, rows)` could not both raise on "unplaced" and let Task 3's tests run before the
  user places the bases. `rows` carries each row's EBC range and existing `max_pct` source.
  Enzyme page references (`enzyme_ref`) are PDF pages and stay in the TOML (no column for them).
- 2026-10-15 · Task 4: the user answered the four stop questions with the recommended options:
  Sprau Malt → `adjunct`; the 7 proposed 90-minute boils confirmed; the style name table
  approved as proposed (247 names, 21 dropped); the drafted `max_pct` bases confirmed and the 9
  unplaced ones set to "user decision E, 2026-10-14". Roles are now 81/81 (adjunct 5).
- 2026-10-15 · Task 4: the loader also loads `description`, `description_ref` and
  `ref.fermentable_style`, and `check(..., style_codes=None)` takes the `ref.beer_style` codes to
  check the `[style_names]` table (the plan named the check but not the parameter). `style_names`
  keys are lower case; a printed name is looked up in lower case. Descriptions of the 7 adjuncts
  and sugars cite their source page or URL; Weyermann and Viking `description_ref` are PDF pages.
- 2026-10-15 · Task 7: rule functions 8-13 take `(items, recipe[, numbers])`; rule 9 skips the midpoint test for every target when `guidance` is false (the plan's rule 9 text allowed an out-of-range SRM only for that case) — implementation detail.
