-- =============================================================================
-- 70_corpus.sql  ·  Observed community practice
--
-- The third category. Not `brew` ("what I actually did"), not `ref` ("what a
-- published body asserts"): what a large population of homebrewers actually
-- put in a fermenter, as reported by themselves.
--
-- Source: 179,455 recipes scraped from brewersfriend.com before July 2020,
-- published to Kaggle as angeredsquid/brewers-friend-beer-recipes under CC0.
-- Loaded once by scripts/ingest/corpus_load.py -- NOT by this file, which only
-- creates the (empty) tables and re-runs harmlessly on every stack start.
--
-- ⛔ NEVER VECTORISED. These rows are unvalidated, self-reported, and carry no
-- publisher. Embedding them into kb.* would hand the retrieval layer 179,455
-- documents that look like knowledge and are not -- the exact fabricated-
-- authority failure the closed-book design exists to prevent. The `kb.chunks`
-- knowledge-only rule covers brew.*; it covers this schema for the same reason.
--
-- ⛔ NO FOREIGN KEY TO brew.ingredients, AND THAT IS THE POINT. These recipes
-- name 8,243 distinct fermentable strings and 6,660 hop strings against a
-- 150-row catalogue. Resolving them by creating brew.ingredients rows would
-- mean inventing a potential_ppg per row, which 27_brew_catalogue.sql forbids
-- in as many words. Raw strings are stored raw and resolved later, if ever, by
-- a mapping table that does not exist yet. An unresolved string is honest; a
-- fabricated spec is not.
--
-- Runs AFTER 20_brew.sql (shares nothing with it, but keeps the numbering
-- meaningful). Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS corpus;

-- Layer 1 (architecture §8.4): the agent reaches nlq and nothing else. This
-- schema is private for the same reason kb/brew/ref/mem are. 50_roles.sql runs
-- last and names `corpus` in its REVOKE; this line makes the file standalone.
REVOKE ALL ON SCHEMA corpus FROM PUBLIC;

-- ---------------------------------------------------------------------------
-- One row per scraped recipe.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus.recipes (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source      text NOT NULL,            -- 'brewersfriend'
  source_ref  text NOT NULL,            -- the site-relative recipe URL

  name        text,
  -- The style the USER picked from a dropdown, kept as text. Deliberately not
  -- a FK to ref.styles: the strings are the site's own list, they drift from
  -- BJCP, and a failed join would silently drop recipes rather than report a
  -- mismatch. Reconciling the two is a separate, honest piece of work.
  style_raw   text,
  method      text,                     -- All Grain · BIAB · Extract · Partial Mash

  batch_l     numeric(8,2),
  og          numeric(6,4),
  fg          numeric(6,4),
  abv         numeric(6,2),
  ibu         numeric(7,2),
  -- Brewer's Friend reports colour in SRM.
  color_srm   numeric(7,2),
  -- The source writes -1 for "not recorded"; that is stored as NULL. Present on
  -- only 40,245 of 179,455 recipes, so branch on NULL rather than averaging it.
  mash_ph     numeric(4,2),

  rating      numeric(4,2),
  num_ratings int,
  views       bigint,

  UNIQUE (source, source_ref)
);

COMMENT ON TABLE corpus.recipes IS
  'Self-reported homebrew recipes scraped from a public recipe site (CC0). '
  'Observed practice, not truth (brew.*) and not published reference (ref.*). '
  'NEVER embedded into kb.* -- unvalidated and unattributed.';

CREATE INDEX IF NOT EXISTS corpus_recipes_style_idx  ON corpus.recipes (style_raw);
CREATE INDEX IF NOT EXISTS corpus_recipes_method_idx ON corpus.recipes (method);

-- ---------------------------------------------------------------------------
-- Grain bill. 675,287 rows. Source tuple: [kg, name, PPG, °L, % of bill].
--
-- ⚠️ The Kaggle data card annotates the fourth element as "°L Degree Lintner".
-- It is NOT: it is degrees LOVIBOND (colour). "Caramel / Crystal 60L" carries
-- 60.0 and "Pale 2-Row" carries 1.8 -- those are colours. 2-row's diastatic
-- power is ~140 °Lintner. The uploader's comment is simply wrong; the column
-- is named for what the number is.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus.recipe_fermentables (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  recipe_id      bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position       int NOT NULL,
  name_raw       text NOT NULL,
  amount_kg      numeric(10,4),
  potential_ppg  numeric(6,2),
  color_lovibond numeric(8,2),
  pct_bill       numeric(6,2)
);
CREATE INDEX IF NOT EXISTS corpus_ferm_recipe_idx ON corpus.recipe_fermentables (recipe_id);
CREATE INDEX IF NOT EXISTS corpus_ferm_name_idx   ON corpus.recipe_fermentables (name_raw);

COMMENT ON COLUMN corpus.recipe_fermentables.color_lovibond IS
  'Degrees Lovibond. The source data card mislabels this field as Lintner.';

-- ---------------------------------------------------------------------------
-- Hop schedule. 621,055 rows.
-- Source tuple: [g, name, form, %AA, use, time, IBU contributed, % of hops].
--
-- `use` arrives with the temperature glued on -- 'Whirlpool at 170 °F',
-- 'Dry Hop at 20 °C' -- so it is split: use_raw keeps the string, `use` the
-- verb that groups, use_temp_c the temperature normalised to Celsius.
-- `time` mixes units ('60 min', '7 days'): storing dry-hop days as minutes
-- would make them sort alongside boil times, so value and unit stay separate.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus.recipe_hops (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  recipe_id    bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position     int NOT NULL,
  name_raw     text NOT NULL,
  amount_g     numeric(10,3),
  form         text,             -- Pellet · Leaf/Whole · Lupulin Pellet · Fresh · Plug · Extract
  alpha_pct    numeric(6,2),
  use_raw      text,
  use          text,             -- Boil · Dry Hop · Whirlpool · Aroma · First Wort · Mash
  use_temp_c   numeric(5,1),
  -- numeric(14,2), not (8,2): the corpus is self-reported and unvalidated, and
  -- it contains a 14,515,200-day dry hop. Columns are sized to hold what the
  -- source actually says. Clamping outliers here would falsify the record --
  -- filtering them is the query's job, not the loader's. Other observed
  -- extremes: 500,000 g of one hop, 4,768 IBU, 140% attenuation, 4,200 °L.
  time_value   numeric(14,2),
  time_unit    text,             -- min · hr · days
  time_raw     text,
  ibu_contrib  numeric(7,2),
  pct_amount   numeric(6,2)
);
CREATE INDEX IF NOT EXISTS corpus_hops_recipe_idx ON corpus.recipe_hops (recipe_id);
CREATE INDEX IF NOT EXISTS corpus_hops_name_idx   ON corpus.recipe_hops (name_raw);
CREATE INDEX IF NOT EXISTS corpus_hops_use_idx    ON corpus.recipe_hops (use);

-- ---------------------------------------------------------------------------
-- Yeast. One row per recipe that names one (162,980 of 179,455); the remaining
-- 16,475 carry an empty array and get no row.
-- Source tuple: [name, attenuation, flocculation, temp_low_F, temp_high_F, starter].
--
-- ⚠️ These specs are the recipe SITE's strain database, denormalised onto every
-- recipe -- 68% of strains carry an attenuation identical in every recipe using
-- them. That makes them a usable strain LIST and cross-check. It does not make
-- them citable: there is no source_doc, so they must not be promoted into a
-- ref.* table, which would require the maltster/lab datasheet contract that
-- ref.malts and ref.hops hold.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus.recipe_yeasts (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  recipe_id       bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  name_raw        text NOT NULL,
  attenuation_pct numeric(5,2),
  flocculation    text,
  temp_min_f      numeric(5,1),
  temp_max_f      numeric(5,1),
  starter         boolean
);
CREATE INDEX IF NOT EXISTS corpus_yeast_recipe_idx ON corpus.recipe_yeasts (recipe_id);
CREATE INDEX IF NOT EXISTS corpus_yeast_name_idx   ON corpus.recipe_yeasts (name_raw);

-- ---------------------------------------------------------------------------
-- Everything else: water agents, finings, spices, flavourings. 145,691 rows.
-- Source tuple: [amount, name, type, use, time] -- all free text, including the
-- amount ('4 g', '0.50 tsp', '1 each'). It is kept as written: parsing 'tsp'
-- into a mass would require a density this data does not carry.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus.recipe_misc (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  recipe_id  bigint NOT NULL REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  position   int NOT NULL,
  name_raw   text NOT NULL,
  amount_raw text,
  type_raw   text,             -- Water Agt · Fining · Flavor · Spice · Herb · Other
  use_raw    text,             -- Boil · Mash · Secondary · Primary · Sparge · Kegging · Bottling
  time_raw   text
);
CREATE INDEX IF NOT EXISTS corpus_misc_recipe_idx ON corpus.recipe_misc (recipe_id);
CREATE INDEX IF NOT EXISTS corpus_misc_name_idx   ON corpus.recipe_misc (name_raw);
CREATE INDEX IF NOT EXISTS corpus_misc_type_idx   ON corpus.recipe_misc (type_raw);
