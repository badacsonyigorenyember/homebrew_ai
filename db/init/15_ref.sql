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
-- Hop varieties, scraped from brewersfriend.com by scripts/ingest/hops_extract.py.
-- =============================================================================
-- ⛔ REPLACED THE HOP VARIETY HANDBOOK SHAPE ON 2026-09-22. The 21 handbook
-- columns -- origin, hop_type, and the eight min/max oil and acid ranges with
-- their hops_ranges_ordered CHECK -- were dropped, because the brewersfriend
-- index carries none of them. What the source does carry is one alpha figure
-- per variety, not a range, so alpha_acid_pct is a single NOT NULL number and
-- there is no open-bound convention left to honour.
--
-- beer_styles is the "Most used in" table off each variety's detail page, kept
-- as a jsonb ARRAY of {beer_style, usage_pct, popularity} and filtered to the
-- styles above 10% of that hop's recipes. The DEFAULT is '{}' -- an empty jsonb
-- OBJECT, not an array -- so a row inserted without it does not read as "no
-- styles" in the same shape the loader writes.
CREATE TABLE IF NOT EXISTS ref.hops (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name           text NOT NULL UNIQUE,
  description    text,
  alpha_acid_pct numeric NOT NULL,
  substitutes    text[] DEFAULT '{}',
  beer_styles    jsonb NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS hops_name_trgm_idx
  ON ref.hops USING gin (name gin_trgm_ops);

COMMENT ON TABLE ref.hops IS
  'Hop varieties from brewersfriend.com, loaded by scripts/ingest/hops_extract.py. '
  'One alpha figure per variety, not a range -- the source publishes a single '
  'number. ⚠️ The kb.chunks hop cards are NO LONGER generated from these rows: '
  'they came from the Hop Variety Handbook, whose columns this table dropped on '
  '2026-09-22, so the D32 no-drift contract that ref.styles and ref.faults still '
  'keep does not hold here.';

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
    SELECT s.name, s.srm_min, s.srm_max, s.abv_min, s.abv_max, s.ibu_min, s.ibu_max,
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
    'abv_max', CASE WHEN bool_or(abv_max IS NULL) THEN NULL ELSE max(abv_max) END,
    -- IBU, unlike SRM, has no open-ended-guide problem: every row that has
    -- vitals states both ends. The envelope rule is the same -- an ambiguous
    -- style widens the band, it never narrows it.
    'ibu_min', CASE WHEN bool_or(ibu_min IS NULL) THEN NULL ELSE min(ibu_min) END,
    'ibu_max', CASE WHEN bool_or(ibu_max IS NULL) THEN NULL ELSE max(ibu_max) END
  ) END
  FROM best
$fn$;

COMMENT ON FUNCTION ref.f_style_bands(text) IS
  'The published SRM, ABV and IBU band for a style named in the brewer''s own words, '
  'as the envelope of the ref.styles rows that best match those words. NULL when '
  'nothing matches -- a caller must let the recipe through rather than invent a '
  'band. An open end from the guide stays open, and so does any srm_max of 40+.';

-- SECURITY DEFINER, so mem_writer reads the band without holding SELECT on
-- ref.styles -- the contract 29_brew_formulate.sql already uses for brew.
GRANT USAGE ON SCHEMA ref TO mem_writer;
GRANT EXECUTE ON FUNCTION ref.f_style_bands(text) TO mem_writer;
