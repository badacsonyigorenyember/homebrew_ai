-- =============================================================================
-- 15_ref.sql  ·  Published reference data (D32)
-- Not my brewing (that is brew.*), not prose (that is kb.*): what a published
-- body asserts. Style guidelines, hop specs, fault tables.
--
-- This schema is what makes deprecation #12 absolute again: nothing from brew.*
-- is ever embedded into kb.*, because the one table that legitimately generated
-- kb chunks -- BJCP styles -- was never brewing data in the first place.
--
-- Runs BEFORE 20_brew.sql: brew.recipes.style_id references ref.styles(id).
-- Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS ref;

-- One row per (guide, year, code). BJCP 2021 and BA 2026 coexist as rows; where
-- they disagree that disagreement is information, surfaced by Layer 4, never
-- resolved by dropping one (phase3 README §5.2).
CREATE TABLE IF NOT EXISTS ref.styles (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  guide       text NOT NULL CHECK (guide IN ('BJCP','BA')),
  guide_year  int  NOT NULL,
  code        text NOT NULL,          -- '15B'  ·  BA codes are not numeric
  name        text NOT NULL,          -- 'Irish Stout'
  category    text,

  -- Vital statistics. NULLABLE ON PURPOSE: 20 of 116 BJCP styles define none
  -- (27A-34C specialty categories), because those vary with the base style.
  og_min numeric(5,3), og_max numeric(5,3),
  fg_min numeric(5,3), fg_max numeric(5,3),
  ibu_min int,         ibu_max int,
  srm_min numeric(4,1), srm_max numeric(4,1),
  abv_min numeric(4,2), abv_max numeric(4,2),

  -- The tripwire for the lookup tool that does not exist yet. A model handed
  -- og_min = null renders "OG 0.000" without hesitating; branch on this instead
  -- of trusting null handling. nlq.lookup_bjcp_style (Phase 3b) must say
  -- "this style defines no vital statistics" explicitly.
  has_vitals boolean GENERATED ALWAYS AS (og_min IS NOT NULL) STORED,

  -- All 11 prose fields from styles.json. The old brew.bjcp_styles imported 6
  -- and dropped style_comparison, which is literally "how does this differ
  -- from X" -- among the most-asked style questions.
  overall_impression text,
  aroma              text,
  appearance         text,
  flavor             text,
  mouthfeel          text,
  comments           text,
  history                    text,
  characteristic_ingredients text,
  style_comparison           text,
  entry_instructions         text,
  commercial_examples text[],
  tags                text[],       -- free FTS fuel: 'session-strength', 'malty'

  UNIQUE (guide, guide_year, code)
);
CREATE INDEX IF NOT EXISTS styles_tags_idx ON ref.styles USING gin (tags);
CREATE INDEX IF NOT EXISTS styles_name_trgm_idx
  ON ref.styles USING gin (name gin_trgm_ops);

COMMENT ON TABLE ref.styles IS
  'Published style guidelines, all sources as rows. Numeric ranges are SQL-only '
  'and NEVER embedded; the narrative cards in kb.chunks are generated from these '
  'rows so the two cannot drift (D32).';

-- NOTE (books 6 and 7): ref.faults and ref.hops land here, not in ad-hoc homes.
-- Deliberately not stubbed -- an empty table with a guessed shape is worse than
-- no table, and both plans run their own probe first.

-- =============================================================================
-- Book 6 — the beer fault list. 21 rows, one per off-flavour.
-- =============================================================================
-- ⛔ THERE IS NO `cause` COLUMN, AND THAT IS DELIBERATE. The source is the BJCP
-- two-column table — Characteristic and Possible Solutions — so the mapping is
-- off-flavour -> remedy, with causes implicit. The corpus doc calls it an
-- "off-flavor -> cause -> remedy mapping"; it is not one. ⛔ Nothing may infer
-- the causes into this table: that is exactly the fabricated-content failure the
-- closed-book design exists to prevent. Causes for the major faults are genuinely
-- covered by Yeast and How to Brew and must come from there, attributed.
CREATE TABLE IF NOT EXISTS ref.faults (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name        text NOT NULL UNIQUE,
  descriptors text[] NOT NULL DEFAULT '{}',
  solutions   text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS faults_name_trgm_idx
  ON ref.faults USING gin (name gin_trgm_ops);

COMMENT ON TABLE ref.faults IS
  'Beer off-flavours: sensory descriptors and remedies, one row per fault. '
  'The narrative cards in kb.chunks are generated from these rows so the two '
  'cannot drift, the same contract as ref.styles (D32). NO cause column — the '
  'source has none and causes must never be inferred.';

-- =============================================================================
-- Book 7 — the hop variety handbook. 72 varieties, one row each.
-- =============================================================================
-- Every numeric spec is a RANGE, and both ends are nullable on purpose:
--   `8-14,5`  -> 8.0 .. 14.5   (the source is European; the comma is a DECIMAL
--                               point, never a thousands or list separator)
--   `<47`     -> NULL .. 47.0  ⛔ an open-ended UPPER bound. The minimum does
--                               not exist and must not be recorded as 0 — the
--                               mirror of BA 2026's `30+` in ref.styles.
CREATE TABLE IF NOT EXISTS ref.hops (
  id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name              text NOT NULL UNIQUE,
  origin            text,
  hop_type          text,
  description       text,
  alpha_min         numeric, alpha_max         numeric,
  beta_min          numeric, beta_max          numeric,
  cohumulone_min    numeric, cohumulone_max    numeric,
  total_oils_min    numeric, total_oils_max    numeric,
  myrcene_min       numeric, myrcene_max       numeric,
  humulene_min      numeric, humulene_max      numeric,
  caryophyllene_min numeric, caryophyllene_max numeric,
  farnesene_min     numeric, farnesene_max     numeric,
  beer_types        text[] NOT NULL DEFAULT '{}',
  flavour           text[] NOT NULL DEFAULT '{}',
  alternatives      text[] NOT NULL DEFAULT '{}',
  created_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT hops_ranges_ordered CHECK (
    (alpha_min         IS NULL OR alpha_max         IS NULL OR alpha_min         <= alpha_max) AND
    (beta_min          IS NULL OR beta_max          IS NULL OR beta_min          <= beta_max) AND
    (cohumulone_min    IS NULL OR cohumulone_max    IS NULL OR cohumulone_min    <= cohumulone_max) AND
    (total_oils_min    IS NULL OR total_oils_max    IS NULL OR total_oils_min    <= total_oils_max) AND
    (myrcene_min       IS NULL OR myrcene_max       IS NULL OR myrcene_min       <= myrcene_max) AND
    (humulene_min      IS NULL OR humulene_max      IS NULL OR humulene_min      <= humulene_max) AND
    (caryophyllene_min IS NULL OR caryophyllene_max IS NULL OR caryophyllene_min <= caryophyllene_max) AND
    (farnesene_min     IS NULL OR farnesene_max     IS NULL OR farnesene_min     <= farnesene_max))
);

CREATE INDEX IF NOT EXISTS hops_name_trgm_idx
  ON ref.hops USING gin (name gin_trgm_ops);

COMMENT ON TABLE ref.hops IS
  'Hop varieties: origin, type, oil and acid ranges, and the handbook prose. '
  'The narrative cards in kb.chunks are generated from these rows so the two '
  'cannot drift, the same contract as ref.styles and ref.faults (D32). A NULL '
  'range end is an open bound from the source, not missing data.';

-- Render one spec range for a card. An open bound must READ as open: "<47" is
-- "up to 47", never "0-47" and never a bare "47" that would be taken as exact.
CREATE OR REPLACE FUNCTION ref.f_range_text(lo numeric, hi numeric, unit text DEFAULT '%')
RETURNS text
LANGUAGE sql IMMUTABLE SET search_path = ref, public AS $fn$
  SELECT CASE
    WHEN lo IS NULL AND hi IS NULL THEN NULL
    WHEN lo IS NULL               THEN 'up to ' || trim_scale(hi) || unit
    WHEN hi IS NULL               THEN trim_scale(lo) || unit || ' or more'
    WHEN lo = hi                  THEN trim_scale(lo) || unit
    ELSE trim_scale(lo) || '-' || trim_scale(hi) || unit
  END
$fn$;

-- ---------------------------------------------------------------------------
-- ref.f_style_bands  ·  the published band a computed recipe is checked against
--
-- cap-formulate-recipe verifies its computed OG/ABV/SRM before accepting a
-- recipe, and the band it checks against has to come from somewhere defensible:
-- a gate that invents a target refuses beers the brewer never asked to have
-- refused. So the only source is what a guide actually publishes about the style
-- the brewer named -- these columns, nothing else.
--
-- The brewer's words are not a style code. `formulate.recipe/parse` returns the
-- style "in the brewer's words" -- "pastry stout", "dry irish stout" -- so match
-- on the HEAD NOUN (the last word; English beer-style names are head-final), then
-- keep only the rows sharing the MOST of the remaining words. "pastry stout"
-- resolves to BA "Dessert Stout or Pastry Beer" alone; a bare "stout" keeps all
-- sixteen and gets the widest band of the set. Ambiguity widens the band, never
-- narrows it, so an uncertain match cannot manufacture a constraint.
--
-- ⛔ A NULL end is an OPEN end, never a zero. has_vitals keeps out the 20 BJCP
-- styles that define no vitals at all, but BA writes "40+" as srm_max NULL and
-- two rows carry no srm_min, and both must read as "no bound on that side".
--
-- ⛔ An srm_max of 40 or more is returned as NO ceiling. Above roughly SRM 30 a
-- beer is opaque and the difference stops being visible -- 29_brew_formulate.sql
-- says the same about Morey past 50. Of the sixteen stout rows here seven name no
-- ceiling and eight name exactly 40: the guides themselves stop distinguishing
-- there. `measured`: 29 runs of the same pastry-stout request landed SRM 35.1-43.3
-- twenty-six times, so a literal 40 would reject five beers that are simply black.
--
-- Returns NULL when the style names nothing. The caller must then let the recipe
-- through rather than guess.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ref.f_style_bands(p_style text)
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ref, public AS $fn$
  WITH w AS (
    SELECT array_remove(regexp_split_to_array(
             regexp_replace(lower(btrim(coalesce(p_style, ''))), '[^a-z0-9]+', ' ', 'g'),
             ' '), '') AS words
  ),
  h AS (SELECT words, words[array_length(words, 1)] AS head FROM w),
  m AS (
    SELECT s.name, s.srm_min, s.srm_max, s.abv_min, s.abv_max,
           (SELECT count(*) FROM unnest(h.words) x
             WHERE length(x) >= 3 AND s.name ILIKE '%' || x || '%') AS hits
    FROM ref.styles s, h
    -- 'beer' is the sentinel `Unpack brief` substitutes when parse named no
    -- style; as a head noun it matches "Fruit Beer", "Spice Beer" and the pastry
    -- row alike, which is not a style, it is a shrug. No style named, no band.
    WHERE h.head IS NOT NULL AND h.head <> 'beer'
      AND s.has_vitals
      AND s.name ILIKE '%' || h.head || '%'
  ),
  best AS (SELECT * FROM m WHERE hits = (SELECT max(hits) FROM m))
  SELECT CASE WHEN count(*) = 0 THEN NULL ELSE jsonb_build_object(
    'styles',  (SELECT jsonb_agg(DISTINCT name) FROM best),
    'srm_min', CASE WHEN bool_or(srm_min IS NULL) THEN NULL ELSE min(srm_min) END,
    'srm_max', CASE WHEN bool_or(srm_max IS NULL) OR max(srm_max) >= 40
                    THEN NULL ELSE max(srm_max) END,
    'abv_min', CASE WHEN bool_or(abv_min IS NULL) THEN NULL ELSE min(abv_min) END,
    'abv_max', CASE WHEN bool_or(abv_max IS NULL) THEN NULL ELSE max(abv_max) END
  ) END
  FROM best
$fn$;

COMMENT ON FUNCTION ref.f_style_bands(text) IS
  'The published SRM and ABV band for a style named in the brewer''s own words, '
  'as the envelope of the ref.styles rows that best match those words. NULL when '
  'nothing matches -- a caller must let the recipe through rather than invent a '
  'band. An open end from the guide stays open, and so does any srm_max of 40+.';

-- SECURITY DEFINER, so mem_writer reads the band without holding SELECT on
-- ref.styles -- the contract 29_brew_formulate.sql already uses for brew.
GRANT USAGE ON SCHEMA ref TO mem_writer;
GRANT EXECUTE ON FUNCTION ref.f_style_bands(text) TO mem_writer;
