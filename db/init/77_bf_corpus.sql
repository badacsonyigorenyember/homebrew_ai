-- =============================================================================
-- 77_bf_corpus.sql  ·  The filtered brewersfriend corpus
--
-- Source: angeredsquid/brewers-friend-beer-recipes (Kaggle, CC0), 179,455
-- recipes scraped from brewersfriend.com before July 2020. Loaded by
-- scripts/ingest/bf_load.py -- NOT by this file, which creates empty tables and
-- re-runs harmlessly on every stack start.
--
-- FILTERED, not complete (D1/D2, TREND-SCHEMA.md 1.3): views > 500 leaves 36,271
-- recipes and 114 styles reaching n>=50, against 55 styles at views>1000. That
-- 36,271 is the views>500 count alone; net of the script filter and the
-- duplicate-url dedup in bf_load.py, the loaded corpus is 35,620 recipes.
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
COMMENT ON COLUMN corpus.bf_hops.timing_min IS
  'The source''s own number, unconverted -- its UNIT depends on use_stage: '
  'minutes for Boil/Whirlpool/Aroma/First Wort/Mash, but DAYS for Dry Hop '
  '("5 days" -> 5). trend.f_rebuild() therefore excludes Dry Hop rows from the '
  'style_hop timing aggregate; averaging both units together produced a '
  'meaningless figure (Citra in American IPA read 8.0).';
