-- =============================================================================
-- 20_brew.sql  ·  Truth schema (architecture §3.3)
-- What I actually did: ingredients, inventory, recipes, batches, measurements,
-- sensory notes, BJCP styles. SQL-only surface — NEVER vectorised into kb.*.
-- Brewing math lives here as deterministic Postgres functions (§3.3), never the LLM.
-- Idempotent.
-- =============================================================================

CREATE TABLE IF NOT EXISTS brew.ingredients (
  id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  kind      text NOT NULL CHECK (kind IN ('fermentable','hop','yeast','water_agent','adjunct','misc')),
  name      text NOT NULL,
  supplier  text,
  alpha_acid_pct  numeric(5,2),   -- hops
  color_lovibond  numeric(6,2),   -- fermentables
  potential_ppg   numeric(5,1),
  attenuation_min numeric(4,1),   -- yeast
  attenuation_max numeric(4,1),
  attrs     jsonb NOT NULL DEFAULT '{}',   -- everything else, kind-specific
  UNIQUE (kind, name, supplier)
);

CREATE TABLE IF NOT EXISTS brew.inventory (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ingredient_id bigint NOT NULL REFERENCES brew.ingredients(id),
  lot_code      text,
  qty           numeric(10,3) NOT NULL,
  unit          text NOT NULL CHECK (unit IN ('g','kg','ml','l','pkg','ea')),
  acquired_on   date,
  best_before   date,
  location      text,
  notes         text
);

CREATE TABLE IF NOT EXISTS brew.bjcp_styles (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  guide_year int NOT NULL,
  code       text NOT NULL,          -- '15B'
  name       text NOT NULL,          -- 'Irish Stout'
  category   text,
  og_min numeric(5,3), og_max numeric(5,3),
  fg_min numeric(5,3), fg_max numeric(5,3),
  ibu_min int, ibu_max int,
  srm_min numeric(4,1), srm_max numeric(4,1),
  abv_min numeric(4,2), abv_max numeric(4,2),
  overall_impression text, aroma text, appearance text,
  flavor text, mouthfeel text, comments text,
  commercial_examples text[],
  UNIQUE (guide_year, code)
);

CREATE TABLE IF NOT EXISTS brew.recipes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL, version int NOT NULL DEFAULT 1,
  parent_recipe_id bigint REFERENCES brew.recipes(id),
  style_id bigint REFERENCES brew.bjcp_styles(id),
  batch_size_l numeric(6,2) NOT NULL,
  target_og numeric(5,3), target_fg numeric(5,3),
  target_ibu int, target_srm numeric(4,1),
  mash_profile jsonb, water_profile jsonb, notes text,
  UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS brew.recipe_items (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  recipe_id bigint NOT NULL REFERENCES brew.recipes(id) ON DELETE CASCADE,
  ingredient_id bigint NOT NULL REFERENCES brew.ingredients(id),
  stage text NOT NULL CHECK (stage IN ('mash','boil','whirlpool','dryhop','fermenter','packaging')),
  qty numeric(10,3) NOT NULL, unit text NOT NULL,
  timing_min int,          -- boil time remaining, or days for dry hop
  notes text
);

CREATE TABLE IF NOT EXISTS brew.batches (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  recipe_id bigint REFERENCES brew.recipes(id),
  batch_no text NOT NULL UNIQUE,
  brewed_on date NOT NULL, packaged_on date,
  volume_l numeric(6,2),
  og numeric(5,3), fg numeric(5,3),
  status text NOT NULL DEFAULT 'planned'
         CHECK (status IN ('planned','fermenting','conditioning','packaged','archived')),
  notes text
);

CREATE TABLE IF NOT EXISTS brew.measurements (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id bigint NOT NULL REFERENCES brew.batches(id) ON DELETE CASCADE,
  taken_at timestamptz NOT NULL,
  kind text NOT NULL CHECK (kind IN ('gravity','temp_c','ph','pressure','do_ppb','volume_l')),
  value numeric(10,4) NOT NULL,
  device text, notes text
);

CREATE TABLE IF NOT EXISTS brew.sensory_notes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id bigint NOT NULL REFERENCES brew.batches(id) ON DELETE CASCADE,
  tasted_at date NOT NULL,
  days_since_packaging int,
  aroma text, appearance text, flavor text, mouthfeel text, overall text,
  score numeric(3,1),
  descriptors text[],       -- {'bitter','resinous','dank'} — the NLQ filter surface
  fts tsvector GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(aroma,'')||' '||coalesce(flavor,'')||' '||
      coalesce(mouthfeel,'')||' '||coalesce(overall,''))) STORED
);
CREATE INDEX IF NOT EXISTS sensory_notes_fts_idx  ON brew.sensory_notes USING gin (fts);
CREATE INDEX IF NOT EXISTS sensory_notes_desc_idx ON brew.sensory_notes USING gin (descriptors);

-- ---------------------------------------------------------------------------
-- Brewing math as Postgres functions (§3.3). Deterministic, unit-testable,
-- composable into nlq views. NEVER computed by the LLM.
-- ---------------------------------------------------------------------------

-- ABV from OG/FG (standard formula used across the design)
CREATE OR REPLACE FUNCTION brew.f_abv(og numeric, fg numeric) RETURNS numeric
  LANGUAGE sql IMMUTABLE AS
$$ SELECT round(((76.08 * (og - fg) / (1.775 - og)) * (fg / 0.794))::numeric, 2) $$;

-- Dry-hop rate in grams per litre for a batch (sums 'dryhop' stage additions)
CREATE OR REPLACE FUNCTION brew.f_dry_hop_rate_g_per_l(p_batch_id bigint) RETURNS numeric
  LANGUAGE sql STABLE AS $$
  SELECT round(
    sum(CASE ri.unit WHEN 'kg' THEN ri.qty*1000 ELSE ri.qty END)
      / NULLIF(max(b.volume_l), 0), 2)
  FROM brew.batches b
  JOIN brew.recipe_items ri ON ri.recipe_id = b.recipe_id AND ri.stage = 'dryhop'
  WHERE b.id = p_batch_id
$$;

-- NOTE (Phase 3): add f_ibu_tinseth, f_srm_morey, f_gravity_temp_correct here,
-- the same way — deterministic SQL functions consumed by nlq views (§3.3).
-- Deliberately not stubbed: an inexact math function silently poisons the eval
-- baseline (architecture §10.2, truth-query correctness = 1.00, no tolerance).
