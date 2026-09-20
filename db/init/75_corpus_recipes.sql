-- ---------------------------------------------------------------------------
-- 75_corpus_recipes.sql  ·  corpus.* — Brewfather BeerJSON recipes
--
-- Eight tables holding BeerJSON 2.06 recipe exports in full: one parent plus
-- seven child tables for the repeating groups. Loaded by
-- scripts/ingest/recipes_load.py. Idempotent.
--
-- ⛔ EVERY QUANTITY IS STORED AS value + unit, VERBATIM, AND NOTHING IS EVER
-- CONVERTED. The units are not uniform and cannot be assumed away -- `measured`
-- 2026-09-19 across the 10 exports in recipes/:
--   hop timing.duration       min (43) and day (12)
--   culture amount            pkg (8), unit (1), ml (1)
--   miscellaneous amount      g (21), each (7), ml (6), unit (1)
-- A reader that wants one unit converts at read time, where the choice is
-- visible. Water ion columns are the one exception: they are named _ppm and the
-- loader REFUSES a row carrying any other unit rather than converting it.
--
-- ⚠ NO FILENAME, NO RAW JSON, NO FORMAT METADATA. Only what the recipe states.
-- The consequence is that there is no natural key: `name` is not unique enough
-- ('Sierra Nevada Pale Ale' and 'Sierra Nevada pale ale' are two different
-- exports differing only in case), so identity is the surrogate `id` alone and
-- re-running the loader appends rather than upserting. Clear the tables first
-- if you mean to replace -- the loader carries that statement, commented out.
--
-- ⚠ `style_guide` IS NOT ALL BJCP. 8 rows say BJCP 2015, 1 says BJCP 2021 and
-- 1 says Norbrygg 2017 (whose style name is Norwegian). Stored as written, so
-- a join to ref.styles must filter on the guide it actually wants.
--
-- `position` preserves the order the addition appeared in the export, which is
-- the brewer's own ordering and is not recoverable from the values.
-- ---------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS corpus;
REVOKE ALL ON SCHEMA corpus FROM PUBLIC;

CREATE TABLE IF NOT EXISTS corpus.recipes (
  id                          bigserial PRIMARY KEY,
  name                        text NOT NULL,
  type                        text,
  author                      text,
  notes                       text,
  carbonation                 numeric,

  batch_size_value            numeric,
  batch_size_unit             text,
  efficiency_brewhouse_value  numeric,
  efficiency_brewhouse_unit   text,
  boil_time_value             numeric,
  boil_time_unit              text,
  pre_boil_size_value         numeric,
  pre_boil_size_unit          text,

  original_gravity_value      numeric,
  original_gravity_unit       text,
  final_gravity_value         numeric,
  final_gravity_unit          text,
  alcohol_by_volume_value     numeric,
  alcohol_by_volume_unit      text,
  apparent_attenuation_value  numeric,
  apparent_attenuation_unit   text,
  color_estimate_value        numeric,
  color_estimate_unit         text,
  ibu_estimate_method         text,

  style_name                  text,
  style_category              text,
  style_category_number       int,
  style_letter                text,
  style_guide                 text,
  style_type                  text,

  mash_name                   text,
  mash_grain_temperature_value numeric,
  mash_grain_temperature_unit  text,
  fermentation_name           text,

  loaded_at                   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corpus.recipe_fermentables (
  id                      bigserial PRIMARY KEY,
  recipe_id               bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position                int NOT NULL,
  name                    text NOT NULL,
  type                    text,
  grain_group             text,
  producer                text,
  origin                  text,
  amount_value            numeric,
  amount_unit             text,
  color_value             numeric,
  color_unit              text,
  yield_fine_grind_value  numeric,
  yield_fine_grind_unit   text,
  yield_potential_value   numeric,
  yield_potential_unit    text,
  timing_use              text,
  UNIQUE (recipe_id, position)
);

CREATE TABLE IF NOT EXISTS corpus.recipe_hops (
  id                      bigserial PRIMARY KEY,
  recipe_id               bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position                int NOT NULL,
  name                    text NOT NULL,
  origin                  text,
  form                    text,
  year                    text,
  alpha_acid_value        numeric,
  alpha_acid_unit         text,
  amount_value            numeric,
  amount_unit             text,
  timing_use              text,
  timing_duration_value   numeric,
  timing_duration_unit    text,
  UNIQUE (recipe_id, position)
);

CREATE TABLE IF NOT EXISTS corpus.recipe_cultures (
  id                      bigserial PRIMARY KEY,
  recipe_id               bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position                int NOT NULL,
  name                    text NOT NULL,
  type                    text,
  form                    text,
  producer                text,
  product_id              text,
  amount_value            numeric,
  amount_unit             text,
  attenuation_value       numeric,
  attenuation_unit        text,
  cell_count_billions     int,
  timing_use              text,
  UNIQUE (recipe_id, position)
);

CREATE TABLE IF NOT EXISTS corpus.recipe_miscs (
  id                      bigserial PRIMARY KEY,
  recipe_id               bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position                int NOT NULL,
  name                    text NOT NULL,
  type                    text,
  amount_value            numeric,
  amount_unit             text,
  timing_use              text,
  timing_duration_value   numeric,
  timing_duration_unit    text,
  UNIQUE (recipe_id, position)
);

-- ⚠ Ion columns are named _ppm and hold the number as written. The loader
-- refuses any water addition whose ions are not in ppm; it does not convert.
CREATE TABLE IF NOT EXISTS corpus.recipe_waters (
  id                      bigserial PRIMARY KEY,
  recipe_id               bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position                int NOT NULL,
  name                    text NOT NULL,
  amount_value            numeric,
  amount_unit             text,
  calcium_ppm             numeric,
  bicarbonate_ppm         numeric,
  sulfate_ppm             numeric,
  chloride_ppm            numeric,
  sodium_ppm              numeric,
  magnesium_ppm           numeric,
  UNIQUE (recipe_id, position)
);

CREATE TABLE IF NOT EXISTS corpus.recipe_mash_steps (
  id                      bigserial PRIMARY KEY,
  recipe_id               bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position                int NOT NULL,
  name                    text,
  type                    text,
  step_temperature_value  numeric,
  step_temperature_unit   text,
  step_time_value         numeric,
  step_time_unit          text,
  ramp_time_value         numeric,
  ramp_time_unit          text,
  UNIQUE (recipe_id, position)
);

CREATE TABLE IF NOT EXISTS corpus.recipe_fermentation_steps (
  id                       bigserial PRIMARY KEY,
  recipe_id                bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position                 int NOT NULL,
  name                     text,
  description              text,
  start_temperature_value  numeric,
  start_temperature_unit   text,
  step_time_value          numeric,
  step_time_unit           text,
  UNIQUE (recipe_id, position)
);

COMMENT ON TABLE corpus.recipes IS
  'Brewfather BeerJSON 2.06 recipe exports, one row per recipe, with the '
  'repeating groups in corpus.recipe_*. Quantities are stored as value + unit '
  'exactly as exported and are never converted. No filename, raw JSON or '
  'format metadata is kept, so there is no natural key -- identity is id.';
COMMENT ON COLUMN corpus.recipes.style_guide IS
  'As written by the exporter: BJCP 2015, BJCP 2021 and Norbrygg 2017 all '
  'occur. Filter on it before joining ref.styles.';
COMMENT ON COLUMN corpus.recipes.apparent_attenuation_value IS
  '⚠ A FRACTION, NOT A PERCENT, despite apparent_attenuation_unit saying "%". '
  '`measured` 2026-09-19: Brewfather exports 0.722 for 72.2%% attenuation while '
  'writing efficiency_brewhouse as 71 and alcohol_by_volume as 4.99 in the same '
  'recipe. The exporter is inconsistent; the value is stored exactly as written '
  'and is NOT corrected here. Multiply by 100 to compare against '
  'efficiency_brewhouse_value.';
