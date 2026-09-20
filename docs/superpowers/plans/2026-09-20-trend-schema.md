# Trend Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use `- [ ]` for tracking.

**Goal:** Build `trend.*` — per-style brewing practice aggregated from a filtered brewersfriend corpus — plus the `ref.fermentables` and taxonomy layers it needs.

**Spec:** `docs/TREND-SCHEMA.md`. Read §1 before starting; every threshold here comes from a measurement there.

**Stack:** Postgres 15 (self-hosted Supabase), Python 3 stdlib only, `psql` via `docker exec`.

## Global Constraints

- **`postgres` is not a superuser.** Every psql call uses `-U supabase_admin`.
- **`db-init` does not glob.** A new `db/init/*.sql` silently never runs until its name is added to the list in `docker-compose.yml`.
- **Every `.sql` here is idempotent** — it re-runs on every stack start.
- **Run `docker compose` from the main checkout only**, never a worktree.
- **No invented specs.** `27_brew_catalogue.sql` forbids fabricating `potential_ppg`. Every number comes from the spec's §3.2, sourced from the live brewersfriend catalogue.
- **Never vectorise corpus rows** into `kb.*`.
- **There is no pytest in this repo.** Verification is a SQL assertion run through `psql`, in the style of `docs/TESTING.md`. Each task states the assertion, the command, and the expected output.

## File Structure

| File | Responsibility |
|---|---|
| `db/init/26_ref_fermentables.sql` | renamed from `26_ref_malts.sql`; `ref.fermentables` + commodity rows |
| `db/init/27_brew_catalogue.sql` | **modify line 27** — consumer of the renamed table |
| `db/init/76_fermentable_types.sql` | `corpus.fermentable_types` taxonomy + substitution map |
| `db/init/77_bf_corpus.sql` | `corpus.bf_*` tables |
| `db/init/78_trend.sql` | `trend.*` tables + `trend.f_rebuild()` |
| `db/init/79_drop_dead_nlq.sql` | drops the three broken functions (D12) |
| `scripts/ingest/bf_load.py` | filter, classify, resolve, COPY |
| `docker-compose.yml` | db-init file list |

## Out of scope

**Spec §7 (how the generator reads the trend tables) is deliberately not a task
here.** It specifies the read order that makes 20 hops unreachable — budget
first, popularity list second — but its consumer is `cap-formulate-recipe`, which
D12 says is being reworked. This plan delivers the tables and the rebuild; wiring
the generator belongs to that rework and needs its own plan.

Spec §3.7 (the Brewfather migration) is likewise deferred by D11.

---

## Task 1: `ref.fermentables`

Renames `ref.malts`, adds the columns the commodity rows need, loads them.

**Files:**
- Rename: `db/init/26_ref_malts.sql` → `db/init/26_ref_fermentables.sql`
- Modify: `db/init/27_brew_catalogue.sql:27`
- Modify: `docker-compose.yml` (db-init list)

- [ ] **Step 1: Write the assertion and watch it fail**

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select count(*) filter (where name='Flaked Oats' and potential_ppg_min=33 and color_lovibond=2) as oats,
       count(*) filter (where name='Lactose (Milk Sugar)' and potential_ppg_min=41 and fermentability_pct=0) as lactose,
       count(*) as total
from ref.fermentables;"
```

Expected now: `ERROR: relation "ref.fermentables" does not exist`

- [ ] **Step 2: Rename the file, keep git history**

```bash
cd "/home/gorenyember/AI Homebrew Assistant"
git mv db/init/26_ref_malts.sql db/init/26_ref_fermentables.sql
```

- [ ] **Step 3: Put the rename + columns at the top of that file**

Insert immediately after the header comment block, **before** `CREATE TABLE IF NOT EXISTS ref.malts`:

```sql
-- ---------------------------------------------------------------------------
-- RENAME (D10). ref.malts became ref.fermentables when it gained sugars,
-- extracts and flaked adjuncts -- none of which are malts. Guarded so a fresh
-- database (no ref.malts) and an existing one (no ref.fermentables) both work.
-- ---------------------------------------------------------------------------
DO $rename$
BEGIN
  IF to_regclass('ref.malts') IS NOT NULL
     AND to_regclass('ref.fermentables') IS NULL THEN
    ALTER TABLE ref.malts RENAME TO fermentables;
  END IF;
END
$rename$;
```

Then change the three `ref.malts` occurrences in this file to `ref.fermentables`
(the `CREATE TABLE IF NOT EXISTS`, the trgm index, the `COMMENT ON TABLE`), and
append:

```sql
-- ---------------------------------------------------------------------------
-- Commodity fermentables need shapes the maltster rows never did.
-- ---------------------------------------------------------------------------
ALTER TABLE ref.fermentables ALTER COLUMN maltster DROP NOT NULL;
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS potential_ppg_min numeric(5,1);
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS potential_ppg_max numeric(5,1);
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS fermentability_pct numeric(5,2);
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS spec_source text;
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS spec_note   text;

DO $ck$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fermentables_spec_source') THEN
    ALTER TABLE ref.fermentables ADD CONSTRAINT fermentables_spec_source
      CHECK (spec_source IS NULL OR spec_source IN
             ('brewersfriend','brewfather','maltster','user_reference','corpus_default','manual'));
  END IF;
END
$ck$;

COMMENT ON COLUMN ref.fermentables.spec_source IS
  'Which publisher the numbers came from. D11: brewersfriend is the source of '
  'record, Brewfather is the deferred migration target (TREND-SCHEMA.md 3.7). '
  'A colour-derived guess must never read as a published spec.';
COMMENT ON COLUMN ref.fermentables.fermentability_pct IS
  'Percent of extract the yeast can reach. Lactose is 0. brewersfriend does not '
  'publish this, so these values stay user_reference even where ppg does not. '
  '29_brew_formulate.sql:88 reads the boolean form from brew.ingredients.attrs.';

-- ---------------------------------------------------------------------------
-- Commodity rows. Read from https://www.brewersfriend.com/fermentables/ on
-- 2026-09-20 (TREND-SCHEMA.md 3.2). maltster is NULL: these are categories, not
-- products. ON CONFLICT DO NOTHING -- re-runs on every stack start.
-- ⚠ The UNIQUE is (maltster, name) and NULL never equals NULL, so the conflict
-- target is the partial index below, not the constraint.
-- ---------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS fermentables_generic_name_idx
  ON ref.fermentables (name) WHERE maltster IS NULL;

INSERT INTO ref.fermentables
  (maltster, name, potential_ppg_min, potential_ppg_max, color_lovibond,
   fermentability_pct, spec_source, spec_note)
VALUES
  (NULL,'Flaked Oats',                     33,33,   2,   NULL,'brewersfriend','Brewfather 36.8 / 1.0 L'),
  (NULL,'Flaked Barley',                   32,32,   2,   NULL,'brewersfriend',NULL),
  (NULL,'Flaked Wheat',                    34,34,   2,   NULL,'brewersfriend',NULL),
  (NULL,'Flaked Corn',                     40,40,   1,   NULL,'brewersfriend','Flaked Maize is a separate, near-unused row at 37'),
  (NULL,'Flaked Rye',                      36,36,   3,   NULL,'brewersfriend',NULL),
  (NULL,'Acidulated Malt',                 27,27,   3,   NULL,'brewersfriend','user_reference gave 33-35 / 1.7-3.0'),
  (NULL,'Oat Malt',                        28,28,   2,   NULL,'brewersfriend','malted, NOT flaked -- 33 vs 28 is the distinction'),
  (NULL,'Rice',                          35.5,35.5, 1,   NULL,'brewersfriend',NULL),
  (NULL,'Flaked Rice',                     40,40,   1,   NULL,'brewersfriend','Brewfather 32 (1.032 sg) / 2 EBC'),
  (NULL,'Cane Sugar',                      46,46,   0,   97.5,'brewersfriend','fermentability_pct is user_reference: 95-100'),
  (NULL,'Corn Sugar - Dextrose',           42,42,   1,  100,  'brewersfriend',NULL),
  (NULL,'Brown Sugar',                     45,45,  15,   97.5,'brewersfriend','fermentability_pct is user_reference: 95-100'),
  (NULL,'Belgian Candi Sugar - Clear/Blond',38,38,  0,   95,  'brewersfriend','sugar is 38, SYRUP is 32 -- a real catalogue split'),
  (NULL,'Belgian Candi Sugar - Amber/Brown',38,38, 60,   95,  'brewersfriend',NULL),
  (NULL,'Belgian Candi Sugar - Dark',      38,38, 275,   95,  'brewersfriend',NULL),
  (NULL,'Belgian Candi Syrup - D-90',      32,32,  90,   95,  'brewersfriend',NULL),
  (NULL,'Lactose (Milk Sugar)',            41,41,   1,    0,  'brewersfriend','Brewfather 35. 0% fermentable -- points land on FG'),
  (NULL,'Honey',                           35,35,   2,   92.5,'brewersfriend','fermentability_pct is user_reference: 90-95'),
  (NULL,'Rice Syrup Solids',               37,37,   1,  100,  'brewersfriend',NULL),
  (NULL,'Brown Rice Syrup - Gluten Free',  44,44,   2,  100,  'brewersfriend',NULL),
  (NULL,'Dry Malt Extract - Pilsen',       42,42,   2,   NULL,'brewersfriend',NULL),
  (NULL,'Dry Malt Extract - Extra Light',  42,42,   3,   NULL,'brewersfriend',NULL),
  (NULL,'Dry Malt Extract - Light',        42,42,   4,   NULL,'brewersfriend','DME is flat 42 across grades; COLOUR carries the grade'),
  (NULL,'Dry Malt Extract - Munich',       42,42,   8,   NULL,'brewersfriend',NULL),
  (NULL,'Dry Malt Extract - Amber',        42,42,  10,   NULL,'brewersfriend',NULL),
  (NULL,'Dry Malt Extract - Dark',         44,44,  30,   NULL,'brewersfriend',NULL),
  (NULL,'Dry Malt Extract - Wheat',        42,42,   3,   NULL,'brewersfriend',NULL),
  (NULL,'Liquid Malt Extract - Pilsen',    35,35,   2,   NULL,'brewersfriend',NULL),
  (NULL,'Liquid Malt Extract - Extra Light',37,37,  3,   NULL,'brewersfriend',NULL),
  (NULL,'Liquid Malt Extract - Light',     35,35,   4,   NULL,'brewersfriend','LME is flat 35; 37 only for Extra Light'),
  (NULL,'Liquid Malt Extract - Munich',    35,35,   8,   NULL,'brewersfriend',NULL),
  (NULL,'Liquid Malt Extract - Amber',     35,35,  10,   NULL,'brewersfriend',NULL),
  (NULL,'Liquid Malt Extract - Dark',      35,35,  30,   NULL,'brewersfriend',NULL),
  (NULL,'Liquid Malt Extract - Wheat',     35,35,   3,   NULL,'brewersfriend',NULL)
ON CONFLICT DO NOTHING;

-- The 77 maltster rows predate spec_source and are all datasheet-derived.
UPDATE ref.fermentables SET spec_source = 'maltster'
WHERE maltster IS NOT NULL AND spec_source IS NULL;
```

- [ ] **Step 4: Fix the one consumer**

`db/init/27_brew_catalogue.sql:27` reads `FROM ref.malts m`. Change to:

```sql
FROM ref.fermentables m
```

⚠ Check the surrounding `SELECT` still refers only to columns that exist — the rename changed no columns, so it should. Do not otherwise touch that file.

- [ ] **Step 5: Update stale comments naming the renamed table**

These name a table that no longer exists, so they are now wrong. Change `ref.malts` → `ref.fermentables` in comments only:
- `db/init/28_brew_derived_sugars.sql:7`
- `db/init/32_brew_sugars.sql:288`
- `db/init/33_brew_yeast.sql:52`

Leave `70_corpus.sql` and `71_corpus_dims.sql` alone — both are out of the db-init list.

- [ ] **Step 6: Point db-init at the renamed file**

In `docker-compose.yml`, in the `for f in ...` list, change `26_ref_malts.sql` to `26_ref_fermentables.sql`.

- [ ] **Step 7: Apply and verify**

```bash
cd "/home/gorenyember/AI Homebrew Assistant"
docker exec -i supabase-db psql -U supabase_admin -d postgres -v ON_ERROR_STOP=1 \
  -f /dev/stdin < db/init/26_ref_fermentables.sql
```

Then re-run the Step 1 assertion. Expected: `oats=1  lactose=1  total=111` (77 maltster + 34 commodity).

Also confirm nothing still points at the old name:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "select to_regclass('ref.malts') as old, to_regclass('ref.fermentables') as new;"
```
Expected: `old = NULL`, `new = ref.fermentables`.

- [ ] **Step 8: Commit**

```bash
git add db/init/26_ref_fermentables.sql db/init/27_brew_catalogue.sql \
        db/init/28_brew_derived_sugars.sql db/init/32_brew_sugars.sql \
        db/init/33_brew_yeast.sql docker-compose.yml
git commit -m "Rename ref.malts to ref.fermentables and load the commodity rows"
```

---

## Task 2: `corpus.fermentable_types`

The 22-type taxonomy, each type carrying a purchasable substitute from Task 1's table.

**Files:** Create `db/init/76_fermentable_types.sql`; modify `docker-compose.yml`

**Interfaces — Produces:** `corpus.fermentable_types.type_key`, referenced as a FK by Tasks 3 and 5, and written by Task 4's classifier. The 22 `type_key` values below are the exact vocabulary; Task 4 must emit these strings and nothing else.

- [ ] **Step 1: Write the assertion and watch it fail**

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select count(*) as types,
       count(substitute_id) as with_substitute,
       count(*) filter (where substitute_basis is null) as unsourced
from corpus.fermentable_types;"
```
Expected now: `ERROR: relation "corpus.fermentable_types" does not exist`

- [ ] **Step 2: Create the file**

```sql
-- =============================================================================
-- 76_fermentable_types.sql  ·  The malt-type taxonomy, and the bridge to
-- purchasable product rows.
--
-- WHY TYPE AND NOT PRODUCT: ref.fermentables' maltster rows are Weyermann (44)
-- and Viking (33) against an American homebrew corpus. `measured` 2026-09-19,
-- product-level resolution reaches 21.5% of corpus rows; type-level reaches
-- 98.7% (TREND-SCHEMA.md 1.6, 1.7). Type is also what a trend actually wants --
-- "pilsner malt at 80% of grist" is useful, "Weyermann Barke Pilsner at 80%"
-- is not.
--
-- ⛔ substitute_basis EXISTS SO A COLOUR-DERIVED GUESS NEVER READS AS A
-- PUBLISHED EQUIVALENCE. Flavour equivalence is asserted nowhere: colour and
-- ppg are measured, flavour is not. A 'sourced' row needs a citation in
-- substitute_note; a cell stays NULL rather than carrying an uncited claim.
--
-- Runs AFTER 26_ref_fermentables.sql. Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS corpus;
REVOKE ALL ON SCHEMA corpus FROM PUBLIC;

CREATE TABLE IF NOT EXISTS corpus.fermentable_types (
  type_key         text PRIMARY KEY,
  role             text NOT NULL
                   CHECK (role IN ('base','character','colour','adjunct','sugar','extract')),
  lov_min          numeric(6,1),
  lov_max          numeric(6,1),
  typical_pct_min  numeric(5,2),
  typical_pct_max  numeric(5,2),
  substitute_id    bigint REFERENCES ref.fermentables(id) ON DELETE SET NULL,
  substitute_basis text CHECK (substitute_basis IN ('exact','colour_ppg','sourced','manual')),
  substitute_note  text
);

COMMENT ON TABLE corpus.fermentable_types IS
  'The 22-type vocabulary the corpus loader classifies into, each with a '
  'purchasable stand-in from ref.fermentables. role is exhaustive and mutually '
  'exclusive, which is what lets trend.style_grist_template sum to 100%.';

INSERT INTO corpus.fermentable_types
  (type_key, role, lov_min, lov_max, typical_pct_min, typical_pct_max) VALUES
  ('base_pilsner',      'base',        0,    3,  40, 100),
  ('base_pale',         'base',        0,    5,  40, 100),
  ('vienna',            'base',        3,    6,   0,  80),
  ('munich',            'base',        5,   20,   0,  80),
  ('wheat',             'base',        0,    8,   0,  70),
  ('rye',               'base',        0,    8,   0,  40),
  ('oats',              'adjunct',     0,   12,   0,  30),
  ('adjunct_starch',    'adjunct',     0,    5,   0,  40),
  ('dextrine',          'character',   0,    5,   0,  15),
  ('crystal_light',     'character',   5,   25,   0,  25),
  ('crystal_medium',    'character',  25,   70,   0,  20),
  ('crystal_dark',      'character',  70,  120,   0,  15),
  ('crystal_extra_dark','character', 120,  300,   0,  10),
  ('kilned_specialty',  'character',  10,  100,   0,  20),
  ('chocolate',         'colour',    200,  400,   0,  15),
  ('black',             'colour',    400,  600,   0,  10),
  ('roast_barley',      'colour',    300,  550,   0,  15),
  ('smoked',            'character',   0,   10,   0,  50),
  ('acidulated',        'character',   1,    5,   0,   5),
  ('sugar',             'sugar',       0,  300,   0,  20),
  ('sugar_lactose',     'sugar',       0,    2,   0,  10),
  ('extract',           'extract',     2,   30,   0, 100)
ON CONFLICT (type_key) DO NOTHING;

-- ---------------------------------------------------------------------------
-- The substitution map. Matched on name, so it survives identity churn in
-- ref.fermentables. Only rows still unmapped are touched -- a 'manual' bridge
-- is human work and is never overwritten.
-- ---------------------------------------------------------------------------
UPDATE corpus.fermentable_types t
SET substitute_id = f.id, substitute_basis = m.basis, substitute_note = m.note
FROM (VALUES
  ('base_pilsner',      'Pilsner Malt',                  'Weyermann','exact',     NULL),
  ('base_pale',         'Pale Ale Malt',                 'Weyermann','colour_ppg','stands in for American 2-row and Maris Otter'),
  ('vienna',            'Vienna Malt',                   'Weyermann','exact',     NULL),
  ('munich',            'Munich Malt Type 1',            'Weyermann','exact',     NULL),
  ('wheat',             'Wheat Malt pale',               'Weyermann','exact',     NULL),
  ('rye',               'Rye Malt pale',                 'Weyermann','exact',     NULL),
  ('dextrine',          'CARAFOAM®',                     'Weyermann','exact',     NULL),
  ('crystal_light',     'CARAHELL®',                     'Weyermann','colour_ppg','9.9 L, band 5-25'),
  ('crystal_medium',    'CARAAMBER®',                    'Weyermann','colour_ppg','26.9 L, band 25-70'),
  ('crystal_dark',      'CARABOHEMIAN®',                 'Weyermann','colour_ppg','74.0 L, band 70-120'),
  ('crystal_extra_dark','CARAAROMA®',                    'Weyermann','colour_ppg','151.2 L, band 120+'),
  ('chocolate',         'Chocolate Light Malt',          'Viking Malt','colour_ppg','150.5 L'),
  ('black',             'Black Malt',                    'Viking Malt','colour_ppg','525.2 L'),
  ('roast_barley',      'Roasted Barley',                'Viking Malt','exact',     NULL),
  ('kilned_specialty',  'Melanoidin Malt',               'Weyermann','colour_ppg','26.9 L; covers biscuit/victory/amber/aromatic'),
  ('smoked',            'Beech Smoked Barley Malt',      'Weyermann','exact',     NULL),
  ('oats',              'Flaked Oats',                    NULL,      'exact',     NULL),
  ('acidulated',        'Acidulated Malt',                NULL,      'exact',     NULL),
  ('adjunct_starch',    'Flaked Barley',                  NULL,      'colour_ppg','the commonest unmalted adjunct; corn/wheat/rice differ in colour only'),
  ('sugar',             'Corn Sugar - Dextrose',          NULL,      'colour_ppg','commonest sugar by usage'),
  ('sugar_lactose',     'Lactose (Milk Sugar)',           NULL,      'exact',     NULL),
  ('extract',           'Dry Malt Extract - Light',       NULL,      'colour_ppg','DME is flat 42 across grades')
) AS m(type_key, fname, fmaltster, basis, note)
JOIN ref.fermentables f
  ON f.name = m.fname
 AND f.maltster IS NOT DISTINCT FROM m.fmaltster
WHERE t.type_key = m.type_key
  AND (t.substitute_basis IS NULL OR t.substitute_basis <> 'manual');
```

- [ ] **Step 3: Add to db-init**

In `docker-compose.yml`, append `/db-init/76_fermentable_types.sql` to the `for f in ...` list, after `/db-init/75_corpus_recipes.sql`.

- [ ] **Step 4: Apply and verify**

```bash
docker exec -i supabase-db psql -U supabase_admin -d postgres -v ON_ERROR_STOP=1 \
  -f /dev/stdin < db/init/76_fermentable_types.sql
```

Re-run the Step 1 assertion. Expected: `types=22  with_substitute=22  unsourced=0`.

⚠ If `with_substitute < 22`, a name in the VALUES list does not match `ref.fermentables`. Find which:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c \
  "select type_key from corpus.fermentable_types where substitute_id is null;"
```

- [ ] **Step 5: Commit**

```bash
git add db/init/76_fermentable_types.sql docker-compose.yml
git commit -m "Add the fermentable-type taxonomy and its substitution map"
```

---

## Task 3: `corpus.bf_*` tables

**Files:** Create `db/init/77_bf_corpus.sql`; modify `docker-compose.yml`

**Interfaces — Produces:** the five tables Task 4 COPYs into. Column order in `bf_recipes` is the COPY column list Task 4 must match exactly.

- [ ] **Step 1: Write the assertion and watch it fail**

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select table_name from information_schema.tables
where table_schema='corpus' and table_name like 'bf_%' order by 1;"
```
Expected now: `(0 rows)`

- [ ] **Step 2: Create the file**

```sql
-- =============================================================================
-- 77_bf_corpus.sql  ·  The filtered brewersfriend corpus
--
-- Source: angeredsquid/brewers-friend-beer-recipes (Kaggle, CC0), 179,455
-- recipes scraped from brewersfriend.com before July 2020. Loaded by
-- scripts/ingest/bf_load.py -- NOT by this file, which creates empty tables and
-- re-runs harmlessly on every stack start.
--
-- FILTERED, not complete (D1/D2, TREND-SCHEMA.md 1.3): views > 500 leaves 36,271
-- recipes and 114 styles reaching n>=50, against 55 styles at views>1000.
-- Script-block language filter only -- a strict ASCII filter would drop Kölsch,
-- Crème Brûlée and Jalapeño to clean 45 CJK rows.
--
-- ⛔ NEVER VECTORISED. These rows are unvalidated, self-reported and carry no
-- publisher. Embedding them into kb.* would hand retrieval 36,000 documents that
-- look like knowledge and are not.
--
-- ⛔ THE PREFIX IS bf_ BECAUSE corpus.recipes IS ALREADY TAKEN by the Brewfather
-- BeerJSON tables in 75_corpus_recipes.sql. Two unrelated corpora, one schema.
--
-- ⚠ RAW STRINGS ARE KEPT ON EVERY CHILD ROW. An unresolved string is honest; a
-- fabricated resolution is not.
--
-- Runs AFTER 76_fermentable_types.sql. Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS corpus;
REVOKE ALL ON SCHEMA corpus FROM PUBLIC;

CREATE TABLE IF NOT EXISTS corpus.bf_recipes (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_ref   text NOT NULL UNIQUE,      -- the site-relative recipe URL
  name         text NOT NULL,
  style_raw    text,
  ref_style_id bigint REFERENCES ref.styles(id) ON DELETE SET NULL,
  method       text,
  views        int NOT NULL,
  batch_l      numeric(8,2),
  og           numeric(6,4),
  fg           numeric(6,4),
  abv          numeric(6,2),
  ibu          numeric(7,2),
  color_srm    numeric(7,2)
);
CREATE INDEX IF NOT EXISTS bf_recipes_style_idx ON corpus.bf_recipes (ref_style_id);

CREATE TABLE IF NOT EXISTS corpus.bf_fermentables (
  recipe_id    bigint NOT NULL REFERENCES corpus.bf_recipes(id) ON DELETE CASCADE,
  position     int    NOT NULL,
  raw_name     text   NOT NULL,
  ferm_type    text   REFERENCES corpus.fermentable_types(type_key),
  pct_of_grist numeric(6,3),
  stated_ppg   numeric(6,2),   -- what the recipe itself claimed
  stated_lov   numeric(7,2),
  PRIMARY KEY (recipe_id, position)
);
CREATE INDEX IF NOT EXISTS bf_ferm_type_idx ON corpus.bf_fermentables (ferm_type);

CREATE TABLE IF NOT EXISTS corpus.bf_hops (
  recipe_id   bigint NOT NULL REFERENCES corpus.bf_recipes(id) ON DELETE CASCADE,
  position    int    NOT NULL,
  raw_name    text   NOT NULL,
  ref_hop_id  bigint REFERENCES ref.hops(id) ON DELETE SET NULL,
  amount_g    numeric(9,3),
  use_stage   text,           -- Boil | Dry Hop | Whirlpool | Aroma | First Wort | Mash
  timing_min  numeric(7,1),
  PRIMARY KEY (recipe_id, position)
);
CREATE INDEX IF NOT EXISTS bf_hops_ref_idx ON corpus.bf_hops (ref_hop_id);

CREATE TABLE IF NOT EXISTS corpus.bf_miscs (
  recipe_id  bigint NOT NULL REFERENCES corpus.bf_recipes(id) ON DELETE CASCADE,
  position   int    NOT NULL,
  raw_name   text   NOT NULL,
  amount_raw text,             -- '2 oz', '1 tsp' -- units are not uniform, never converted
  misc_type  text,
  use_stage  text,
  PRIMARY KEY (recipe_id, position)
);

CREATE TABLE IF NOT EXISTS corpus.bf_yeasts (
  recipe_id bigint NOT NULL REFERENCES corpus.bf_recipes(id) ON DELETE CASCADE,
  position  int    NOT NULL,
  raw_name  text   NOT NULL,
  PRIMARY KEY (recipe_id, position)
);

COMMENT ON TABLE corpus.bf_recipes IS
  'Filtered brewersfriend corpus: views>500, script-clean. Substrate for trend.* '
  'and nothing else -- never retrieved, never shown, never embedded.';
COMMENT ON COLUMN corpus.bf_fermentables.ferm_type IS
  'NULL means the classifier did not recognise the string. `measured` 2026-09-19 '
  'that is 1.3% of rows, mostly fruit. NULL is honest; a guess is not.';
```

- [ ] **Step 3: Add to db-init, apply, verify**

Append `/db-init/77_bf_corpus.sql` to the `for f in ...` list in `docker-compose.yml`, then:

```bash
docker exec -i supabase-db psql -U supabase_admin -d postgres -v ON_ERROR_STOP=1 \
  -f /dev/stdin < db/init/77_bf_corpus.sql
```

Re-run the Step 1 assertion. Expected 5 rows: `bf_fermentables, bf_hops, bf_miscs, bf_recipes, bf_yeasts`.

- [ ] **Step 4: Commit**

```bash
git add db/init/77_bf_corpus.sql docker-compose.yml
git commit -m "Add the filtered brewersfriend corpus tables"
```

---

## Task 4: `scripts/ingest/bf_load.py`

Filters, classifies, resolves, loads. Modelled on `scripts/ingest/corpus_load.py` — read it first for the `psql()` and COPY pattern.

**Files:** Create `scripts/ingest/bf_load.py`

**Interfaces — Consumes:** `corpus.fermentable_types.type_key` (Task 2) and the five tables from Task 3. `classify()` must emit only the 22 type_key strings or `None`.

**Input:** `recipes_full.txt`, one JSON object per line as `"N": {...}`. Located at `/home/gorenyember/Downloads/brewers-friend-beer-recipes/recipes_full.txt`; it is gitignored and must never enter the repo.

- [ ] **Step 1: Write the assertion and watch it fail**

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select (select count(*) from corpus.bf_recipes)     as recipes,
       (select count(*) from corpus.bf_fermentables) as ferms,
       (select round(100.0*count(ferm_type)/count(*),1) from corpus.bf_fermentables) as pct_classified,
       (select round(100.0*count(ref_hop_id)/count(*),1) from corpus.bf_hops) as pct_hops_resolved;"
```
Expected now: `recipes=0` and NULL percentages.

- [ ] **Step 2: Write the loader**

```python
#!/usr/bin/env python3
"""Load the filtered Brewer's Friend corpus into corpus.bf_* (77_bf_corpus.sql).

One-shot. The DDL runs on every stack start; this does not. Re-running is safe:
it truncates first.

    python3 scripts/ingest/bf_load.py <recipes_full.txt>

Filters (TREND-SCHEMA.md D1/D2):
  views > 500          36,271 of 179,455 recipes; 114 styles reach n>=50
  script-block clean   drops CJK/Hangul/Cyrillic/Hebrew/Arabic/Thai names only.
                       NOT an ASCII filter -- that would drop Kolsch and Jalapeno.

Source: angeredsquid/brewers-friend-beer-recipes (Kaggle, CC0).
"""
import csv, json, re, subprocess, sys, tempfile, unicodedata

MIN_VIEWS = 500

# Script blocks that mean "not readable here". Latin-with-diacritics is KEPT.
_SCRIPTS = ((0x3040, 0x30FF), (0x4E00, 0x9FFF), (0xAC00, 0xD7AF),
            (0x0400, 0x04FF), (0x0590, 0x05FF), (0x0600, 0x06FF), (0x0E00, 0x0E7F))

_PREFIX = re.compile(
    r"^(american|united kingdom|german|belgian|french|canadian|australian|"
    r"new zealand|czech|danish|dutch|finnish|irish|polish|swedish|norwegian|"
    r"austrian|italian|spanish|mexican|japanese|chilean|us|uk)\s+-\s+")


def foreign_script(s):
    return any(lo <= ord(c) <= hi for c in s for lo, hi in _SCRIPTS)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def classify(name, lov):
    """Corpus fermentable string -> corpus.fermentable_types.type_key, or None.

    Reads only values the recipe already carries. `measured` 2026-09-19: 98.7%
    of rows classify. The 1.3% that do not are mostly fruit, which belongs in
    misc rather than the grist.
    """
    n = _PREFIX.sub("", name.lower()).strip()
    L = num(lov)
    h = lambda *w: any(k in n for k in w)

    if h("lactose"):                                            return "sugar_lactose"
    if h("dextrose", "corn sugar", "sucrose", "table sugar", "cane sugar",
          "candi", "honey", "molasses", "maple", "treacle", "invert",
          "turbinado", "demerara", "brown sugar", "agave"):      return "sugar"
    if h("extract") and h("dry malt", "dme", "liquid malt", "lme", "malt extract"):
        return "extract"
    if h("acidulated", "acid malt", "sauermalz"):                return "acidulated"
    if h("carapils", "dextrine", "carafoam"):                    return "dextrine"
    if h("smoked", "rauch", "peated", "mesquite"):               return "smoked"
    if h("roasted barley", "roast barley"):                      return "roast_barley"
    if h("de-bittered black", "debittered black"):               return "black"
    if h("black patent", "blackprinz", "black malt", "carafa",
          "midnight wheat", "black barley"):                     return "black"
    if h("chocolate"):                                           return "chocolate"
    if h("special b"):                                           return "crystal_extra_dark"
    if h("crystal", "caramel", "cara"):
        if L is None:                                            return "crystal_medium"
        if L <= 25:                                              return "crystal_light"
        if L <= 70:                                              return "crystal_medium"
        if L <= 120:                                             return "crystal_dark"
        return "crystal_extra_dark"
    if h("coffee malt", "abbey", "red x"):                       return "kilned_specialty"
    if re.fullmatch(r"(brown|amber)", n):                        return "kilned_specialty"
    if h("biscuit", "victory", "amber malt", "brown malt", "melanoidin",
          "aromatic", "special roast", "honey malt"):            return "kilned_specialty"
    if h("munich"):                                              return "munich"
    if h("vienna"):                                              return "vienna"
    if h("oat", "golden naked"):                                 return "oats"
    if h("rye"):                                                 return "rye"
    if h("flaked corn", "maize", "corn", "grits", "polenta", "rice",
          "flaked barley", "torrified", "unmalted", "spelt", "buckwheat",
          "sorghum", "quinoa", "millet"):                        return "adjunct_starch"
    if h("wheat"):                                               return "wheat"
    if h("pilsner", "pilsen", "lager malt") or re.fullmatch(r"lager", n):
        return "base_pilsner"
    if h("maris otter", "golden promise", "pale ale", "2-row", "2 row",
          "six-row", "6-row", "pale malt", "optic", "halcyon", "mild malt"):
        return "base_pale"
    if L is not None and L <= 4 and h("malt", "pale"):            return "base_pale"
    return None


def norm_hop(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def psql(sql, stdin=None):
    """supabase_admin, not postgres -- postgres is not a superuser in this stack."""
    p = subprocess.run(
        ["docker", "exec", "-i", "supabase-db", "psql", "-U", "supabase_admin",
         "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-c", sql],
        stdin=stdin, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"psql failed:\n{p.stderr}")
    return p.stdout.strip()


def hop_index():
    """name -> ref.hops.id, including the alternatives[] column.

    `measured` 2026-09-19: exact 64.0% of rows, alternatives a further 20.4%.
    """
    idx = {}
    rows = psql("SELECT id, name, array_to_string(alternatives,'|') "
                "FROM ref.hops ORDER BY id")
    for line in rows.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        hid, name, alts = parts[0], parts[1], parts[2:]
        idx.setdefault(norm_hop(name), hid)
        for a in alts:
            if a:
                idx.setdefault(norm_hop(a), hid)
    return idx


def style_index():
    """normalised BJCP style name -> ref.styles.id (guide='BJCP')."""
    idx = {}
    for line in psql("SELECT id, name FROM ref.styles WHERE guide='BJCP'").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 2 and parts[0].isdigit():
            idx[norm_hop(parts[1])] = parts[0]
    return idx


def main(path):
    hops, styles = hop_index(), style_index()
    tmp = {k: tempfile.NamedTemporaryFile("w+", newline="", suffix=f".{k}.csv")
           for k in ("r", "f", "h", "m", "y")}
    w = {k: csv.writer(v) for k, v in tmp.items()}
    rid = 0
    kept = skipped_views = skipped_script = 0

    for i, line in enumerate(open(path, encoding="utf-8", errors="replace")):
        s = line.strip()
        if i == 0:
            s = s[1:]
        if s.endswith(","):
            s = s[:-1]
        mt = re.match(r'^"\d+":\s*(\{.*)$', s)
        if not mt:
            continue
        body = mt.group(1)
        if body.endswith("}}"):
            body = body[:-1]
        try:
            r = json.loads(body)
        except ValueError:
            continue

        if (r.get("views") or 0) <= MIN_VIEWS:
            skipped_views += 1
            continue
        name = r.get("name") or ""
        if foreign_script(name):
            skipped_script += 1
            continue
        url = r.get("url")
        if not url:
            continue

        rid += 1
        kept += 1
        style_raw = (r.get("style") or "").strip() or None
        w["r"].writerow([
            rid, url, name, style_raw,
            styles.get(norm_hop(style_raw)) if style_raw else None,
            r.get("method"), int(r.get("views") or 0),
            num(r.get("batch")), num(r.get("og")), num(r.get("fg")),
            num(r.get("abv")), num(r.get("ibu")), num(r.get("color"))])

        for pos, x in enumerate(r.get("fermentables") or []):
            if isinstance(x, list) and len(x) >= 5:
                w["f"].writerow([rid, pos, x[1], classify(str(x[1]), x[3]),
                                 num(x[4]), num(x[2]), num(x[3])])
        for pos, x in enumerate(r.get("hops") or []):
            if isinstance(x, list) and len(x) >= 2:
                t = str(x[5]) if len(x) > 5 else ""
                mm = re.match(r"\s*([\d.]+)", t)
                w["h"].writerow([rid, pos, x[1], hops.get(norm_hop(str(x[1]))),
                                 num(x[0]), (x[4] if len(x) > 4 else None),
                                 float(mm.group(1)) if mm else None])
        for pos, x in enumerate(r.get("other") or []):
            if isinstance(x, list) and len(x) > 1:
                w["m"].writerow([rid, pos, x[1], x[0],
                                 (x[2] if len(x) > 2 else None),
                                 (x[3] if len(x) > 3 else None)])
        for pos, x in enumerate(r.get("yeast") or []):
            if isinstance(x, list) and x:
                w["y"].writerow([rid, pos, x[0]])

    print(f"kept {kept:,}  skipped: views<={MIN_VIEWS} {skipped_views:,}, "
          f"foreign script {skipped_script:,}", file=sys.stderr)
    for f in tmp.values():
        f.flush()
    return tmp


def load(tmp):
    psql("TRUNCATE corpus.bf_recipes CASCADE")
    psql("ALTER TABLE corpus.bf_recipes ALTER COLUMN id DROP IDENTITY IF EXISTS")
    cols = ("id, source_ref, name, style_raw, ref_style_id, method, views, "
            "batch_l, og, fg, abv, ibu, color_srm")
    order = [("r", f"corpus.bf_recipes ({cols})"),
             ("f", "corpus.bf_fermentables"),
             ("h", "corpus.bf_hops"),
             ("m", "corpus.bf_miscs"),
             ("y", "corpus.bf_yeasts")]
    for key, target in order:
        tmp[key].seek(0)
        with open(tmp[key].name) as fh:
            psql(f"COPY {target} FROM STDIN WITH (FORMAT csv)", stdin=fh)
    psql("ALTER TABLE corpus.bf_recipes ALTER COLUMN id "
         "ADD GENERATED ALWAYS AS IDENTITY")
    psql("SELECT setval(pg_get_serial_sequence('corpus.bf_recipes','id'), "
         "coalesce(max(id),1)) FROM corpus.bf_recipes")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    load(main(sys.argv[1]))
    print("\n" + psql(
        "SELECT 'recipes', count(*) FROM corpus.bf_recipes "
        "UNION ALL SELECT 'fermentables', count(*) FROM corpus.bf_fermentables "
        "UNION ALL SELECT 'hops', count(*) FROM corpus.bf_hops "
        "UNION ALL SELECT 'miscs', count(*) FROM corpus.bf_miscs "
        "UNION ALL SELECT 'yeasts', count(*) FROM corpus.bf_yeasts;"))
```

- [ ] **Step 3: Run it**

```bash
cd "/home/gorenyember/AI Homebrew Assistant"
python3 scripts/ingest/bf_load.py \
  /home/gorenyember/Downloads/brewers-friend-beer-recipes/recipes_full.txt
```

Expected on stderr: `kept 36,271` (±50 — `url` is required and a few rows lack it).

- [ ] **Step 4: Verify against the spec's baselines**

Re-run the Step 1 assertion. Expected:
- `recipes` ≈ 36,271
- `ferms` ≈ 146,343
- `pct_classified` **≥ 98.0** (spec §1.7 baseline: 98.7)
- `pct_hops_resolved` **≥ 92.0** (spec §1.6 baseline: 92.5)

⚠ If `pct_classified` is below 98, the classifier regressed. Find the gap:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select raw_name, count(*) from corpus.bf_fermentables
where ferm_type is null group by 1 order by 2 desc limit 20;"
```
Fruit names (Cherry, Mango, Raspberry) are expected and correct. Malt names are not.

- [ ] **Step 5: Commit**

```bash
git add scripts/ingest/bf_load.py
git commit -m "Add the filtered corpus loader"
```

---

## Task 5: `trend.*`

The four kinds of fact, plus the rebuild that fills them.

**Files:** Create `db/init/78_trend.sql`; modify `docker-compose.yml`

- [ ] **Step 1: Write the assertion and watch it fail**

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "select * from trend.f_rebuild();"
```
Expected now: `ERROR: schema "trend" does not exist`

- [ ] **Step 2: Create the file**

```sql
-- =============================================================================
-- 78_trend.sql  ·  Style-level brewing practice
--
-- ⛔ THE CENTRAL RULE: MARGINAL FREQUENCY IS NOT JOINT COMPOSITION.
-- `measured` 2026-09-19 on American IPA: 713 distinct hop varieties, top-12
-- presence rates summing to 230%, median recipe using 3. The nine commonest malt
-- types' median grist percentages sum to 190%; a grist must sum to 100%.
--
-- So four kinds of fact live in four tables and are NEVER mixed:
--   shape        how many          style_profile
--   composition  role shares       style_grist_template   (sums to 100)
--   choice+amount conditional      style_fermentable, style_hop
--   affinity     lift              style_hop_pair
--
-- The generator MUST read shape first, as a budget, before opening any
-- popularity list (TREND-SCHEMA.md 7). That is what makes 20 hops unreachable.
--
-- Runs AFTER 77_bf_corpus.sql. Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS trend;
REVOKE ALL ON SCHEMA trend FROM PUBLIC;

-- D9: rebuilds write a NEW snapshot. Nothing mutates in place, so a finalised
-- patch stays finalised and two patches can be diffed.
CREATE TABLE IF NOT EXISTS trend.snapshot (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  built_at      timestamptz NOT NULL DEFAULT now(),
  corpus_filter text NOT NULL,
  n_recipes     int  NOT NULL,
  is_current    boolean NOT NULL DEFAULT false,
  notes         text
);
CREATE UNIQUE INDEX IF NOT EXISTS trend_snapshot_one_current
  ON trend.snapshot (is_current) WHERE is_current;

CREATE TABLE IF NOT EXISTS trend.style_profile (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  n_recipes    int NOT NULL,
  ferm_count_p25 numeric(4,1), ferm_count_p50 numeric(4,1), ferm_count_p75 numeric(4,1),
  hop_variety_count_p25 numeric(4,1),
  hop_variety_count_p50 numeric(4,1),   -- the 20-hop guard
  hop_variety_count_p75 numeric(4,1),
  hop_addition_count_p50 numeric(4,1),
  og_p50 numeric(6,4), fg_p50 numeric(6,4), abv_p50 numeric(5,2),
  ibu_p50 numeric(6,2), srm_p50 numeric(6,2),
  PRIMARY KEY (snapshot_id, ref_style_id)
);

CREATE TABLE IF NOT EXISTS trend.style_grist_template (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  role         text   NOT NULL,
  slots_p25 numeric(4,1), slots_p50 numeric(4,1), slots_p75 numeric(4,1),
  role_pct_p25 numeric(5,2), role_pct_p50 numeric(5,2), role_pct_p75 numeric(5,2),
  n_with int NOT NULL,
  PRIMARY KEY (snapshot_id, ref_style_id, role)
);

CREATE TABLE IF NOT EXISTS trend.style_fermentable (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  ferm_type    text   NOT NULL REFERENCES corpus.fermentable_types(type_key),
  role         text   NOT NULL,
  n_with        int NOT NULL,
  presence_rate numeric(5,4) NOT NULL,
  pct_of_grist_p25 numeric(5,2),
  pct_of_grist_p50 numeric(5,2),
  pct_of_grist_p75 numeric(5,2),
  PRIMARY KEY (snapshot_id, ref_style_id, ferm_type)
);

CREATE TABLE IF NOT EXISTS trend.style_hop (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  ref_hop_id   bigint NOT NULL REFERENCES ref.hops(id),
  n_with        int NOT NULL,
  presence_rate numeric(5,4) NOT NULL,
  share_of_hop_mass_p25 numeric(5,2),
  share_of_hop_mass_p50 numeric(5,2),
  share_of_hop_mass_p75 numeric(5,2),
  timing_min_p50 numeric(7,1),
  PRIMARY KEY (snapshot_id, ref_style_id, ref_hop_id)
);

-- ⛔ support >= 30 IS A CONSTRAINT, NOT A CONVENTION. A row below the gate
-- cannot exist (TREND-SCHEMA.md 1.4).
CREATE TABLE IF NOT EXISTS trend.style_hop_pair (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  hop_a_id     bigint NOT NULL REFERENCES ref.hops(id),
  hop_b_id     bigint NOT NULL REFERENCES ref.hops(id),
  support    int NOT NULL,
  lift       numeric(8,3) NOT NULL,
  confidence numeric(5,4),
  PRIMARY KEY (snapshot_id, ref_style_id, hop_a_id, hop_b_id),
  CONSTRAINT hop_pair_ordered   CHECK (hop_a_id < hop_b_id),
  CONSTRAINT hop_pair_supported CHECK (support >= 30)
);

COMMENT ON TABLE trend.style_hop_pair IS
  'Hop affinity as LIFT, not co-occurrence. `measured` 2026-09-19 on American '
  'IPA: Cascade+Mosaic co-occurs MORE often than Ahtanum+Chinook (147 vs 62) yet '
  'lift 0.49 says brewers avoid it. Raw counts cannot express that.';

-- ---------------------------------------------------------------------------
-- Rebuild. Writes a new snapshot and flips is_current at the end.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trend.f_rebuild(p_min_n int DEFAULT 30)
RETURNS TABLE (snapshot bigint, styles bigint, ferms bigint, hops bigint, pairs bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = trend, corpus, ref, public AS $fn$
DECLARE v_snap bigint;
BEGIN
  INSERT INTO trend.snapshot (corpus_filter, n_recipes, notes)
  SELECT 'views>500 script-clean', count(*), 'trend.f_rebuild'
  FROM corpus.bf_recipes
  RETURNING id INTO v_snap;

  -- shape
  INSERT INTO trend.style_profile
  SELECT v_snap, r.ref_style_id, count(*),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY c.nf),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY c.nf),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY c.nf),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY c.nh),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY c.nh),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY c.nh),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY c.na),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.og)  FILTER (WHERE r.og BETWEEN 1.0 AND 1.2),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.fg)  FILTER (WHERE r.fg BETWEEN 0.98 AND 1.1),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.abv) FILTER (WHERE r.abv BETWEEN 0 AND 20),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.ibu) FILTER (WHERE r.ibu BETWEEN 0 AND 150),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.color_srm) FILTER (WHERE r.color_srm BETWEEN 0 AND 80)
  FROM corpus.bf_recipes r
  JOIN LATERAL (
    SELECT (SELECT count(*) FROM corpus.bf_fermentables f WHERE f.recipe_id=r.id) AS nf,
           (SELECT count(DISTINCT h.ref_hop_id) FROM corpus.bf_hops h WHERE h.recipe_id=r.id) AS nh,
           (SELECT count(*) FROM corpus.bf_hops h WHERE h.recipe_id=r.id) AS na
  ) c ON true
  WHERE r.ref_style_id IS NOT NULL
  GROUP BY r.ref_style_id HAVING count(*) >= p_min_n;

  -- composition: roles are exhaustive, so role_pct sums to ~100 by construction
  INSERT INTO trend.style_grist_template
  SELECT v_snap, x.ref_style_id, x.role,
    percentile_cont(0.25) WITHIN GROUP (ORDER BY x.slots),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY x.slots),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY x.slots),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY x.pct),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY x.pct),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY x.pct),
    count(*)
  FROM (
    SELECT r.ref_style_id, t.role, r.id,
           count(DISTINCT f.ferm_type) AS slots, sum(f.pct_of_grist) AS pct
    FROM corpus.bf_recipes r
    JOIN corpus.bf_fermentables f ON f.recipe_id = r.id
    JOIN corpus.fermentable_types t ON t.type_key = f.ferm_type
    WHERE r.ref_style_id IS NOT NULL
    GROUP BY r.ref_style_id, t.role, r.id
  ) x
  GROUP BY x.ref_style_id, x.role HAVING count(*) >= p_min_n;

  -- choice + amount, conditional on presence
  -- ⚠ presence_rate divides by the RECIPE count for the style, which is why
  -- sn is a separate join and not a window: a window over the grouped rows
  -- would count (style, type, recipe) combinations instead.
  INSERT INTO trend.style_fermentable
  SELECT v_snap, x.ref_style_id, x.ferm_type, x.role, count(*),
    round(count(*)::numeric / max(sn.n), 4),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY x.pct),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY x.pct),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY x.pct)
  FROM (
    SELECT r.ref_style_id, f.ferm_type, t.role, sum(f.pct_of_grist) AS pct
    FROM corpus.bf_recipes r
    JOIN corpus.bf_fermentables f ON f.recipe_id = r.id
    JOIN corpus.fermentable_types t ON t.type_key = f.ferm_type
    WHERE r.ref_style_id IS NOT NULL
    GROUP BY r.ref_style_id, f.ferm_type, t.role, r.id
  ) x
  JOIN (SELECT ref_style_id, count(*) n FROM corpus.bf_recipes
        WHERE ref_style_id IS NOT NULL GROUP BY 1) sn
    ON sn.ref_style_id = x.ref_style_id
  GROUP BY x.ref_style_id, x.ferm_type, x.role HAVING count(*) >= p_min_n;

  INSERT INTO trend.style_hop
  SELECT v_snap, x.ref_style_id, x.ref_hop_id, count(*),
    round(count(*)::numeric / max(sn.n), 4),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY x.share),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY x.share),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY x.share),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY x.tmin)
  FROM (
    SELECT r.ref_style_id, h.ref_hop_id,
           100.0 * sum(h.amount_g)
             / nullif(sum(sum(h.amount_g)) OVER (PARTITION BY r.id), 0) AS share,
           avg(h.timing_min) AS tmin
    FROM corpus.bf_recipes r
    JOIN corpus.bf_hops h ON h.recipe_id = r.id
    WHERE r.ref_style_id IS NOT NULL AND h.ref_hop_id IS NOT NULL
    GROUP BY r.ref_style_id, h.ref_hop_id, r.id
  ) x
  JOIN (SELECT ref_style_id, count(*) n FROM corpus.bf_recipes
        WHERE ref_style_id IS NOT NULL GROUP BY 1) sn
    ON sn.ref_style_id = x.ref_style_id
  GROUP BY x.ref_style_id, x.ref_hop_id HAVING count(*) >= p_min_n;

  -- affinity: lift = P(A and B) / (P(A) * P(B))
  INSERT INTO trend.style_hop_pair
  SELECT v_snap, p.ref_style_id, p.a, p.b, p.support,
         round((p.support::numeric * s.n) / (ha.n_with * hb.n_with), 3),
         round(p.support::numeric / ha.n_with, 4)
  FROM (
    SELECT r.ref_style_id, ha.ref_hop_id AS a, hb.ref_hop_id AS b, count(DISTINCT r.id) AS support
    FROM corpus.bf_recipes r
    JOIN corpus.bf_hops ha ON ha.recipe_id = r.id AND ha.ref_hop_id IS NOT NULL
    JOIN corpus.bf_hops hb ON hb.recipe_id = r.id AND hb.ref_hop_id > ha.ref_hop_id
    WHERE r.ref_style_id IS NOT NULL
    GROUP BY r.ref_style_id, ha.ref_hop_id, hb.ref_hop_id
    HAVING count(DISTINCT r.id) >= 30
  ) p
  JOIN (SELECT ref_style_id, count(*) n FROM corpus.bf_recipes
        WHERE ref_style_id IS NOT NULL GROUP BY 1) s ON s.ref_style_id = p.ref_style_id
  JOIN trend.style_hop ha ON ha.snapshot_id=v_snap AND ha.ref_style_id=p.ref_style_id AND ha.ref_hop_id=p.a
  JOIN trend.style_hop hb ON hb.snapshot_id=v_snap AND hb.ref_style_id=p.ref_style_id AND hb.ref_hop_id=p.b;

  UPDATE trend.snapshot SET is_current = false WHERE is_current;
  UPDATE trend.snapshot SET is_current = true  WHERE id = v_snap;

  RETURN QUERY SELECT v_snap,
    (SELECT count(*) FROM trend.style_profile      WHERE snapshot_id=v_snap),
    (SELECT count(*) FROM trend.style_fermentable  WHERE snapshot_id=v_snap),
    (SELECT count(*) FROM trend.style_hop          WHERE snapshot_id=v_snap),
    (SELECT count(*) FROM trend.style_hop_pair     WHERE snapshot_id=v_snap);
END
$fn$;

-- Reads go through views pinned to is_current, so callers never name a snapshot.
CREATE OR REPLACE VIEW trend.v_style_profile AS
  SELECT p.* FROM trend.style_profile p
  JOIN trend.snapshot s ON s.id = p.snapshot_id AND s.is_current;
CREATE OR REPLACE VIEW trend.v_style_grist_template AS
  SELECT g.* FROM trend.style_grist_template g
  JOIN trend.snapshot s ON s.id = g.snapshot_id AND s.is_current;
CREATE OR REPLACE VIEW trend.v_style_fermentable AS
  SELECT f.* FROM trend.style_fermentable f
  JOIN trend.snapshot s ON s.id = f.snapshot_id AND s.is_current;
CREATE OR REPLACE VIEW trend.v_style_hop AS
  SELECT h.* FROM trend.style_hop h
  JOIN trend.snapshot s ON s.id = h.snapshot_id AND s.is_current;
CREATE OR REPLACE VIEW trend.v_style_hop_pair AS
  SELECT p.* FROM trend.style_hop_pair p
  JOIN trend.snapshot s ON s.id = p.snapshot_id AND s.is_current;
```

⚠ The pair insert reads `n_with` from `trend.style_hop`, so it must run **after**
that insert in the same function body — it does. Do not reorder them.

- [ ] **Step 3: Add to db-init, apply, rebuild**

Append `/db-init/78_trend.sql` to the `for f in ...` list, then:

```bash
docker exec -i supabase-db psql -U supabase_admin -d postgres -v ON_ERROR_STOP=1 \
  -f /dev/stdin < db/init/78_trend.sql
docker exec supabase-db psql -U supabase_admin -d postgres -c "select * from trend.f_rebuild();"
```

- [ ] **Step 4: Verify the spec's success criteria**

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select 'roles sum to 100' as check,
       count(*) filter (where total not between 95 and 105) as failures
from (select ref_style_id, sum(role_pct_p50) total
      from trend.v_style_grist_template group by 1) x
union all
select 'hop budget <= 6',
       count(*) from trend.v_style_profile where hop_variety_count_p50 > 6
union all
select 'no pair below gate',
       count(*) from trend.v_style_hop_pair where support < 30;"
```

Expected: **all three `failures = 0`** (spec §10 criteria 5, 6, 7).

Then confirm the finding the schema exists to preserve:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select h1.name || ' + ' || h2.name as pair, p.support, p.lift
from trend.v_style_hop_pair p
join ref.hops h1 on h1.id=p.hop_a_id join ref.hops h2 on h2.id=p.hop_b_id
join ref.styles s on s.id=p.ref_style_id
where s.name like '%American IPA%'
order by p.lift desc limit 5;"
```
Expected: Amarillo+Simcoe near 1.7×; a Cascade+Mosaic row exists with lift below 1.

- [ ] **Step 5: Commit**

```bash
git add db/init/78_trend.sql docker-compose.yml
git commit -m "Add the trend schema and its rebuild"
```

---

## Task 6: Drop the dead `nlq` functions

Per D12 they are replaced, not repointed. They fail today and nothing may depend on a failing function.

**Files:** Create `db/init/79_drop_dead_nlq.sql`; modify `docker-compose.yml`

- [ ] **Step 1: Confirm they are still broken**

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "select nlq.common_practice('stout');"
```
Expected: `ERROR: column c.style_raw does not exist`

- [ ] **Step 2: Create the file**

```sql
-- =============================================================================
-- 79_drop_dead_nlq.sql  ·  Remove the functions trend.* replaces (D12)
--
-- nlq.common_practice, nlq.ingredient_practice and nlq.f_corpus_styles read
-- corpus.recipe_misc and corpus.recipe_yeasts (dropped with the old corpus) and
-- a corpus.recipes since reshaped to BeerJSON. They raise at every call.
--
-- ⚠ THEY ARE REFERENCED BY SEVEN NODES ACROSS THREE WORKFLOWS -- wf-step-practice,
-- cap-formulate-recipe (Step 3 propose and Step 3b re-propose) and chat-agent.
-- D12: the pipeline is being reworked and owes them no compatibility. Those
-- workflows must move to trend.v_* as part of that rework; this file only stops
-- a broken function from looking available.
--
-- Idempotent.
-- =============================================================================

DROP FUNCTION IF EXISTS nlq.common_practice(text);
DROP FUNCTION IF EXISTS nlq.ingredient_practice(text, text);
DROP FUNCTION IF EXISTS nlq.f_corpus_styles(text);
```

⚠ Argument types must match what exists. Confirm before writing the DROPs:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select p.proname || '(' || pg_get_function_arguments(p.oid) || ')'
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='nlq' and p.proname in
  ('common_practice','ingredient_practice','f_corpus_styles');"
```

Adjust the signatures above to match, then run.

- [ ] **Step 3: Add to db-init, apply, verify**

Append `/db-init/79_drop_dead_nlq.sql` to the `for f in ...` list, then:

```bash
docker exec -i supabase-db psql -U supabase_admin -d postgres -v ON_ERROR_STOP=1 \
  -f /dev/stdin < db/init/79_drop_dead_nlq.sql
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select count(*) as should_be_zero from pg_proc p
join pg_namespace n on n.oid=p.pronamespace
where n.nspname='nlq' and p.proname in
  ('common_practice','ingredient_practice','f_corpus_styles');"
```
Expected: `should_be_zero = 0`

- [ ] **Step 4: Full-stack check**

The real test is that db-init replays cleanly from scratch:

```bash
cd "/home/gorenyember/AI Homebrew Assistant"
docker compose up -d db-init
docker compose logs --tail=40 db-init
```
Expected: every `>> /db-init/...` line, no `ERROR`. ⚠ Run from the main checkout, never a worktree.

- [ ] **Step 5: Commit**

```bash
git add db/init/79_drop_dead_nlq.sql docker-compose.yml
git commit -m "Drop the nlq functions trend.* replaces"
```
