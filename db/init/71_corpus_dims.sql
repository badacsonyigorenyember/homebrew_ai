-- =============================================================================
-- 71_corpus_dims.sql  ·  What an ingredient IS, separated from what a recipe DID
--
-- 70_corpus.sql stores events: 658,090 fermentable additions, 605,406 hop
-- additions. Asking "what is Gypsum?" against those tables returns 15,279 rows
-- because it is the wrong question for a fact table. These four tables answer
-- it: one row per distinct ingredient string, no amounts, no timings.
--
-- ⛔ WHY THE ADDITIONS ARE NOT COLLAPSED INTO THE RECIPE ROW. A map keyed on
-- ingredient name has one slot per key, and `measured`: 102,411 of 158,287
-- recipes (65%) name the same hop more than once, up to 41 times in one recipe
-- -- boil, whirlpool, and two separate dry hops are the same string at
-- different times. Keying on the name discards the schedule for two-thirds of
-- the corpus. Fermentables repeat in only 0.5% of recipes, so the intuition
-- holds for a grain bill and fails for a hop schedule. The one-row-per-recipe
-- READ is real and wanted; it is served by corpus.v_recipe below, which costs
-- nothing because a view stores nothing.
--
-- The join key is name_raw itself, not a surrogate id: it is already unique per
-- dimension and already indexed on both sides, so the dimensions can be rebuilt
-- without renumbering anything or touching 1.4M fact rows.
--
-- ⚠️ A DIMENSION IS NOT AN ALIAS RESOLUTION. Gypsum has 58 distinct spellings
-- and lands as 58 rows, not one -- better than 15,279, still not one. name_key
-- folds case and whitespace automatically, which merges 14,940 of those 15,279
-- rows; the rest ("Gypsum (Calcium Sulfate)" vs "Calcium Sulphate (Gypsum)")
-- need judgment and are a curation job, not a schema job.
--
-- Populated by corpus.f_rebuild_dims(), which corpus_load.py calls. This file
-- only creates empty structures and re-runs harmlessly. Runs AFTER 70_corpus.sql.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Dimensions. Observed statistics only: these describe what the corpus SAYS
-- about an ingredient, never what a publisher asserts. ref_* is the bridge to
-- the sourced specs in ref.*, and stays NULL until someone maps it by hand.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus.fermentables (
  name_raw       text PRIMARY KEY,
  name_key       text GENERATED ALWAYS AS
                   (lower(btrim(regexp_replace(name_raw, '\s+', ' ', 'g')))) STORED,
  -- "American - Pale 2-Row" -> origin "American", base "Pale 2-Row". The site's
  -- picklist is vendor-prefixed; a NULL origin means the string had no prefix.
  origin_raw     text,
  base_name      text,
  n_recipes      int NOT NULL DEFAULT 0,
  n_additions    int NOT NULL DEFAULT 0,
  -- Mode, not mean: these come from a picklist, so the common value is the
  -- site's own figure and the spread is users overriding it.
  potential_ppg  numeric(6,2),
  ppg_min        numeric(6,2),
  ppg_max        numeric(6,2),
  color_lovibond numeric(8,2),
  color_min      numeric(8,2),
  color_max      numeric(8,2),
  ref_malt_id    bigint REFERENCES ref.malts(id)
);
CREATE INDEX IF NOT EXISTS corpus_dim_ferm_key_idx ON corpus.fermentables (name_key);

CREATE TABLE IF NOT EXISTS corpus.hops (
  name_raw    text PRIMARY KEY,
  name_key    text GENERATED ALWAYS AS
                (lower(btrim(regexp_replace(name_raw, '\s+', ' ', 'g')))) STORED,
  n_recipes   int NOT NULL DEFAULT 0,
  n_additions int NOT NULL DEFAULT 0,
  alpha_pct   numeric(6,2),
  alpha_min   numeric(6,2),
  alpha_max   numeric(6,2),
  forms       text[] NOT NULL DEFAULT '{}',   -- Pellet, Leaf/Whole, Lupulin Pellet, ...
  uses        text[] NOT NULL DEFAULT '{}',   -- Boil, Dry Hop, Whirlpool, ...
  ref_hop_id  bigint REFERENCES ref.hops(id)
);
CREATE INDEX IF NOT EXISTS corpus_dim_hops_key_idx ON corpus.hops (name_key);

-- No ref_yeast_id: ref.yeasts does not exist. And these specs must never create
-- it -- they are the recipe site's strain database denormalised onto every
-- recipe, with no source_doc, so they fail the provenance contract ref.malts
-- and ref.hops hold. Usable as a strain list and a cross-check; not citable.
CREATE TABLE IF NOT EXISTS corpus.yeasts (
  name_raw        text PRIMARY KEY,
  name_key        text GENERATED ALWAYS AS
                    (lower(btrim(regexp_replace(name_raw, '\s+', ' ', 'g')))) STORED,
  lab             text,        -- leading segment of "Fermentis - Safale - ... US-05"
  n_recipes       int NOT NULL DEFAULT 0,
  attenuation_pct numeric(5,2),
  attenuation_min numeric(5,2),
  attenuation_max numeric(5,2),
  flocculation    text,
  temp_min_f      numeric(5,1),
  temp_max_f      numeric(5,1)
);
CREATE INDEX IF NOT EXISTS corpus_dim_yeast_key_idx ON corpus.yeasts (name_key);
CREATE INDEX IF NOT EXISTS corpus_dim_yeast_lab_idx ON corpus.yeasts (lab);

CREATE TABLE IF NOT EXISTS corpus.miscs (
  name_raw    text PRIMARY KEY,
  name_key    text GENERATED ALWAYS AS
                (lower(btrim(regexp_replace(name_raw, '\s+', ' ', 'g')))) STORED,
  -- The dominant classification. `types` keeps every one observed, because the
  -- same substance is filed three ways: Gypsum appears as Water Agt, Other and
  -- Fining. Collapsing that to one value would hide a real disagreement.
  type_raw    text,
  types       text[] NOT NULL DEFAULT '{}',
  uses        text[] NOT NULL DEFAULT '{}',
  n_recipes   int NOT NULL DEFAULT 0,
  n_additions int NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS corpus_dim_misc_key_idx  ON corpus.miscs (name_key);
CREATE INDEX IF NOT EXISTS corpus_dim_misc_type_idx ON corpus.miscs (type_raw);

COMMENT ON TABLE corpus.fermentables IS
  'One row per distinct fermentable string in the corpus. Observed statistics, '
  'not published specs -- ref.malts is the sourced side, reached via ref_malt_id.';
COMMENT ON TABLE corpus.miscs IS
  'One row per distinct misc/water-agent/fining string. `types` keeps every '
  'classification observed: the corpus files the same substance several ways.';
COMMENT ON TABLE corpus.yeasts IS
  'One row per distinct yeast string. Specs are the recipe site''s own strain '
  'database, carry no source_doc, and must NOT be promoted into a ref.* table.';

-- ---------------------------------------------------------------------------
-- corpus.f_rebuild_dims()  ·  derive every dimension from the fact tables
--
-- Owns the fact-table foreign keys too, and that is deliberate: the constraint
-- cannot exist while the dimensions are empty and the facts are not, which is
-- exactly the state corpus_load.py passes through. Dropping it, filling the
-- dimensions, and re-adding it is the only ordering that holds at every point.
-- Upsert rather than truncate, so a rebuild never orphans a fact row.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION corpus.f_rebuild_dims()
RETURNS TABLE (dimension text, rows bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = corpus, ref, public AS $fn$
BEGIN
  ALTER TABLE corpus.recipe_fermentables DROP CONSTRAINT IF EXISTS recipe_fermentables_name_fk;
  ALTER TABLE corpus.recipe_hops         DROP CONSTRAINT IF EXISTS recipe_hops_name_fk;
  ALTER TABLE corpus.recipe_yeasts       DROP CONSTRAINT IF EXISTS recipe_yeasts_name_fk;
  ALTER TABLE corpus.recipe_misc         DROP CONSTRAINT IF EXISTS recipe_misc_name_fk;

  INSERT INTO corpus.fermentables AS d
    (name_raw, origin_raw, base_name, n_recipes, n_additions,
     potential_ppg, ppg_min, ppg_max, color_lovibond, color_min, color_max)
  SELECT f.name_raw,
         CASE WHEN f.name_raw LIKE '% - %' THEN btrim(split_part(f.name_raw, ' - ', 1)) END,
         CASE WHEN f.name_raw LIKE '% - %'
              THEN btrim(substr(f.name_raw, position(' - ' in f.name_raw) + 3))
              ELSE f.name_raw END,
         count(DISTINCT f.recipe_id), count(*),
         mode() WITHIN GROUP (ORDER BY f.potential_ppg),
         min(f.potential_ppg), max(f.potential_ppg),
         mode() WITHIN GROUP (ORDER BY f.color_lovibond),
         min(f.color_lovibond), max(f.color_lovibond)
  FROM corpus.recipe_fermentables f GROUP BY f.name_raw
  ON CONFLICT (name_raw) DO UPDATE SET
    origin_raw = EXCLUDED.origin_raw, base_name = EXCLUDED.base_name,
    n_recipes = EXCLUDED.n_recipes, n_additions = EXCLUDED.n_additions,
    potential_ppg = EXCLUDED.potential_ppg, ppg_min = EXCLUDED.ppg_min,
    ppg_max = EXCLUDED.ppg_max, color_lovibond = EXCLUDED.color_lovibond,
    color_min = EXCLUDED.color_min, color_max = EXCLUDED.color_max;

  INSERT INTO corpus.hops AS d
    (name_raw, n_recipes, n_additions, alpha_pct, alpha_min, alpha_max, forms, uses)
  SELECT h.name_raw, count(DISTINCT h.recipe_id), count(*),
         mode() WITHIN GROUP (ORDER BY h.alpha_pct), min(h.alpha_pct), max(h.alpha_pct),
         coalesce(array_agg(DISTINCT h.form) FILTER (WHERE h.form IS NOT NULL), '{}'),
         coalesce(array_agg(DISTINCT h.use)  FILTER (WHERE h.use  IS NOT NULL), '{}')
  FROM corpus.recipe_hops h GROUP BY h.name_raw
  ON CONFLICT (name_raw) DO UPDATE SET
    n_recipes = EXCLUDED.n_recipes, n_additions = EXCLUDED.n_additions,
    alpha_pct = EXCLUDED.alpha_pct, alpha_min = EXCLUDED.alpha_min,
    alpha_max = EXCLUDED.alpha_max, forms = EXCLUDED.forms, uses = EXCLUDED.uses;

  INSERT INTO corpus.yeasts AS d
    (name_raw, lab, n_recipes, attenuation_pct, attenuation_min, attenuation_max,
     flocculation, temp_min_f, temp_max_f)
  SELECT y.name_raw,
         CASE WHEN y.name_raw LIKE '% - %' THEN btrim(split_part(y.name_raw, ' - ', 1)) END,
         count(DISTINCT y.recipe_id),
         mode() WITHIN GROUP (ORDER BY y.attenuation_pct),
         min(y.attenuation_pct), max(y.attenuation_pct),
         mode() WITHIN GROUP (ORDER BY y.flocculation),
         mode() WITHIN GROUP (ORDER BY y.temp_min_f),
         mode() WITHIN GROUP (ORDER BY y.temp_max_f)
  FROM corpus.recipe_yeasts y GROUP BY y.name_raw
  ON CONFLICT (name_raw) DO UPDATE SET
    lab = EXCLUDED.lab, n_recipes = EXCLUDED.n_recipes,
    attenuation_pct = EXCLUDED.attenuation_pct,
    attenuation_min = EXCLUDED.attenuation_min, attenuation_max = EXCLUDED.attenuation_max,
    flocculation = EXCLUDED.flocculation,
    temp_min_f = EXCLUDED.temp_min_f, temp_max_f = EXCLUDED.temp_max_f;

  INSERT INTO corpus.miscs AS d (name_raw, type_raw, types, uses, n_recipes, n_additions)
  SELECT m.name_raw,
         mode() WITHIN GROUP (ORDER BY m.type_raw),
         coalesce(array_agg(DISTINCT m.type_raw) FILTER (WHERE m.type_raw IS NOT NULL), '{}'),
         coalesce(array_agg(DISTINCT m.use_raw)  FILTER (WHERE m.use_raw  IS NOT NULL), '{}'),
         count(DISTINCT m.recipe_id), count(*)
  FROM corpus.recipe_misc m GROUP BY m.name_raw
  ON CONFLICT (name_raw) DO UPDATE SET
    type_raw = EXCLUDED.type_raw, types = EXCLUDED.types, uses = EXCLUDED.uses,
    n_recipes = EXCLUDED.n_recipes, n_additions = EXCLUDED.n_additions;

  ALTER TABLE corpus.recipe_fermentables ADD CONSTRAINT recipe_fermentables_name_fk
    FOREIGN KEY (name_raw) REFERENCES corpus.fermentables(name_raw);
  ALTER TABLE corpus.recipe_hops ADD CONSTRAINT recipe_hops_name_fk
    FOREIGN KEY (name_raw) REFERENCES corpus.hops(name_raw);
  ALTER TABLE corpus.recipe_yeasts ADD CONSTRAINT recipe_yeasts_name_fk
    FOREIGN KEY (name_raw) REFERENCES corpus.yeasts(name_raw);
  ALTER TABLE corpus.recipe_misc ADD CONSTRAINT recipe_misc_name_fk
    FOREIGN KEY (name_raw) REFERENCES corpus.miscs(name_raw);

  RETURN QUERY
    SELECT 'fermentables', count(*) FROM corpus.fermentables
    UNION ALL SELECT 'hops',   count(*) FROM corpus.hops
    UNION ALL SELECT 'yeasts', count(*) FROM corpus.yeasts
    UNION ALL SELECT 'miscs',  count(*) FROM corpus.miscs;
END $fn$;

-- ---------------------------------------------------------------------------
-- corpus.v_recipe  ·  one row per recipe, the whole beer, start to end
--
-- The one-row read, without paying for it in storage. Additions keep their own
-- order and their own timings, so a hop named four times stays four entries.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW corpus.v_recipe AS
SELECT r.id, r.source, r.source_ref, r.name, r.style_raw, r.method,
       r.batch_l, r.og, r.fg, r.abv, r.ibu, r.color_srm, r.mash_ph,
       (SELECT jsonb_agg(jsonb_build_object(
                 'name', f.name_raw, 'kg', f.amount_kg, 'ppg', f.potential_ppg,
                 'lovibond', f.color_lovibond, 'pct_bill', f.pct_bill)
               ORDER BY f.position)
          FROM corpus.recipe_fermentables f WHERE f.recipe_id = r.id) AS fermentables,
       (SELECT jsonb_agg(jsonb_build_object(
                 'name', h.name_raw, 'g', h.amount_g, 'form', h.form,
                 'alpha_pct', h.alpha_pct, 'use', h.use, 'temp_c', h.use_temp_c,
                 'time', h.time_value, 'unit', h.time_unit, 'ibu', h.ibu_contrib)
               ORDER BY h.position)
          FROM corpus.recipe_hops h WHERE h.recipe_id = r.id) AS hops,
       (SELECT jsonb_build_object(
                 'name', y.name_raw, 'attenuation_pct', y.attenuation_pct,
                 'flocculation', y.flocculation, 'temp_min_f', y.temp_min_f,
                 'temp_max_f', y.temp_max_f, 'starter', y.starter)
          FROM corpus.recipe_yeasts y WHERE y.recipe_id = r.id LIMIT 1) AS yeast,
       (SELECT jsonb_agg(jsonb_build_object(
                 'name', m.name_raw, 'amount', m.amount_raw, 'type', m.type_raw,
                 'use', m.use_raw, 'time', m.time_raw)
               ORDER BY m.position)
          FROM corpus.recipe_misc m WHERE m.recipe_id = r.id) AS misc
FROM corpus.recipes r;

COMMENT ON VIEW corpus.v_recipe IS
  'One row per recipe with the complete build as jsonb. The read-side answer to '
  '"a whole recipe in one place"; the fact tables stay normalised so a hop named '
  'at boil, whirlpool and two dry hops keeps four distinct additions.';
