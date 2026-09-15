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

CREATE TABLE IF NOT EXISTS ref.malts (
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
  ON ref.malts USING gin (name gin_trgm_ops);

COMMENT ON TABLE ref.malts IS
  'Malt specifications as published by the maltster. Both the source units '
  '(extract % dry basis fine grind, colour EBC) and the brewing-calculator '
  'units (PPG, degrees Lovibond) are stored: the first so a figure can be '
  'audited against the datasheet, the second so the recipe compute step never '
  'does unit conversion of its own. source_doc names the datasheet.';
