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
