-- =============================================================================
-- 26_ref_malts.sql  ·  Published malt specifications (D32, same contract as
-- ref.hops and ref.styles)
--
-- What a maltster asserts about its own product, not what this brewer measured.
-- Exists because recipe formulation needs extract potential as a NUMBER, and the
-- prose in kb.* ("Malt: A Practical Guide") never states one per product.
--
-- Sources (both ingested through docling-serve, see shared/rag-files/pending):
--   Weyermann   -- per-product PRODUCT SPECIFICATION sheets, crop-dated.
--   Viking Malt -- Craft Portfolio 2020.
--
-- Source units are the maltster's, converted once on ingest and both kept:
--   potential_ppg  = extract_dbfg_pct / 100 * 46.21   (sucrose = 46.21 PPG)
--   color_lovibond -- Weyermann PUBLISHES Lovibond alongside EBC, so its rows use
--                     the published midpoint and no conversion happens at all.
--                     Viking publishes EBC only, so those rows are converted:
--                       ((ebc_mid / 1.97) + 0.76) / 1.3546
--                     (EBC = 1.97*SRM, SRM = 1.3546*L - 0.76, both ASBC)
-- The published columns stay so a conversion can always be re-derived and
-- audited against the datasheet; the derived ones stay so the compute step
-- never does unit maths of its own.
--
-- Runs AFTER 15_ref.sql (needs the ref schema and pg_trgm). Idempotent.
-- =============================================================================

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

CREATE TABLE IF NOT EXISTS ref.fermentables (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  maltster         text NOT NULL,
  name             text NOT NULL,
  category         text,

  -- As published.
  moisture_max_pct numeric(5,2),
  extract_dbfg_pct numeric(5,2),
  colour_ebc_min   numeric(7,2),
  colour_ebc_max   numeric(7,2),

  -- Derived on ingest. NULL where the datasheet states no figure -- a malt with
  -- no published colour (flaked adjuncts) is not a malt with zero colour.
  potential_ppg    numeric(5,1),
  color_lovibond   numeric(6,1),

  source_doc       text NOT NULL,   -- the datasheet these rows were read from
  created_at       timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT malts_maltster_name_key UNIQUE (maltster, name),
  CONSTRAINT malts_colour_ordered CHECK (
    colour_ebc_min IS NULL OR colour_ebc_max IS NULL
    OR colour_ebc_min <= colour_ebc_max)
);

CREATE INDEX IF NOT EXISTS malts_name_trgm_idx
  ON ref.fermentables USING gin (name gin_trgm_ops);

COMMENT ON TABLE ref.fermentables IS
  'Malt specifications as published by the maltster. Both the source units '
  '(extract % dry basis fine grind, colour EBC) and the brewing-calculator '
  'units (PPG, degrees Lovibond) are stored: the first so a figure can be '
  'audited against the datasheet, the second so the recipe compute step never '
  'does unit conversion of its own. source_doc names the datasheet.';

-- ---------------------------------------------------------------------------
-- Commodity fermentables need shapes the maltster rows never did.
-- ---------------------------------------------------------------------------
ALTER TABLE ref.fermentables ALTER COLUMN maltster DROP NOT NULL;
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS potential_ppg_min numeric(5,1);
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS potential_ppg_max numeric(5,1);
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS fermentability_pct numeric(5,2);
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS spec_source text;
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS spec_note   text;

-- source_doc is declared NOT NULL on the CREATE TABLE above, but this
-- environment's live table drifted from that CREATE TABLE (it predates this
-- file and never actually gained the column). Add it back, nullable, so the
-- 77 pre-existing rows are not blocked, and so the commodity INSERT below can
-- supply a citation on both a fresh cluster and this drifted one.
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS source_doc text;

-- category and moisture_max_pct are also declared on the CREATE TABLE above
-- and are also missing from this drifted live table. 27_brew_catalogue.sql
-- reads m.category and fails with "column m.category does not exist" under
-- db-init's ON_ERROR_STOP=1 until it exists; moisture_max_pct is not read by
-- any consumer today but is reconciled alongside it for the same reason --
-- it is part of the same published-columns shape this table's own CREATE
-- TABLE declares. No values are backfilled for the 77 pre-existing rows;
-- these ALTERs only make the columns exist again.
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS category text;
ALTER TABLE ref.fermentables ADD COLUMN IF NOT EXISTS moisture_max_pct numeric(5,2);

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
   fermentability_pct, spec_source, spec_note, source_doc)
VALUES
  (NULL,'Flaked Oats',                     33,33,   2,   NULL,'brewersfriend','Brewfather 36.8 / 1.0 L','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Flaked Barley',                   32,32,   2,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Flaked Wheat',                    34,34,   2,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Flaked Corn',                     40,40,   1,   NULL,'brewersfriend','Flaked Maize is a separate, near-unused row at 37','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Flaked Rye',                      36,36,   3,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Acidulated Malt',                 27,27,   3,   NULL,'brewersfriend','user_reference gave 33-35 / 1.7-3.0','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Oat Malt',                        28,28,   2,   NULL,'brewersfriend','malted, NOT flaked -- 33 vs 28 is the distinction','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Rice',                          35.5,35.5, 1,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Flaked Rice',                     40,40,   1,   NULL,'brewersfriend','Brewfather 32 (1.032 sg) / 2 EBC','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Cane Sugar',                      46,46,   0,   97.5,'brewersfriend','fermentability_pct is user_reference: 95-100','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Corn Sugar - Dextrose',           42,42,   1,  100,  'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Brown Sugar',                     45,45,  15,   97.5,'brewersfriend','fermentability_pct is user_reference: 95-100','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Belgian Candi Sugar - Clear/Blond',38,38,  0,   95,  'brewersfriend','sugar is 38, SYRUP is 32 -- a real catalogue split','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Belgian Candi Sugar - Amber/Brown',38,38, 60,   95,  'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Belgian Candi Sugar - Dark',      38,38, 275,   95,  'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Belgian Candi Syrup - D-90',      32,32,  90,   95,  'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Lactose (Milk Sugar)',            41,41,   1,    0,  'brewersfriend','Brewfather 35. 0% fermentable -- points land on FG','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Honey',                           35,35,   2,   92.5,'brewersfriend','fermentability_pct is user_reference: 90-95','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Rice Syrup Solids',               37,37,   1,  100,  'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Brown Rice Syrup - Gluten Free',  44,44,   2,  100,  'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Dry Malt Extract - Pilsen',       42,42,   2,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Dry Malt Extract - Extra Light',  42,42,   3,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Dry Malt Extract - Light',        42,42,   4,   NULL,'brewersfriend','DME is flat 42 across grades; COLOUR carries the grade','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Dry Malt Extract - Munich',       42,42,   8,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Dry Malt Extract - Amber',        42,42,  10,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Dry Malt Extract - Dark',         44,44,  30,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Dry Malt Extract - Wheat',        42,42,   3,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Liquid Malt Extract - Pilsen',    35,35,   2,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Liquid Malt Extract - Extra Light',37,37,  3,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Liquid Malt Extract - Light',     35,35,   4,   NULL,'brewersfriend','LME is flat 35; 37 only for Extra Light','https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Liquid Malt Extract - Munich',    35,35,   8,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Liquid Malt Extract - Amber',     35,35,  10,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Liquid Malt Extract - Dark',      35,35,  30,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'),
  (NULL,'Liquid Malt Extract - Wheat',     35,35,   3,   NULL,'brewersfriend',NULL,'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)')
ON CONFLICT DO NOTHING;

-- Backfill for rows already inserted before source_doc existed on a drifted
-- live table (ON CONFLICT DO NOTHING above does not touch pre-existing rows).
-- Idempotent: only ever touches commodity rows that still have no citation.
UPDATE ref.fermentables SET source_doc = 'https://www.brewersfriend.com/fermentables/ (read 2026-09-20)'
WHERE maltster IS NULL AND source_doc IS NULL;

-- The 77 maltster rows predate spec_source and are all datasheet-derived.
UPDATE ref.fermentables SET spec_source = 'maltster'
WHERE maltster IS NOT NULL AND spec_source IS NULL;
