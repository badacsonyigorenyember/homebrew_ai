-- =============================================================================
-- 76_fermentable_types.sql  ·  The malt-type taxonomy, and the bridge to
-- purchasable product rows.
--
-- WHY TYPE AND NOT PRODUCT: ref.fermentables' maltster rows are Weyermann (44)
-- and Viking (33) against an American homebrew corpus. `measured` 2026-09-19,
-- product-level resolution reaches 21.5% of corpus rows; type-level reaches
-- 98.7% (TREND-SCHEMA.md 1.6, 1.7). Type is also what a trend actually wants --
-- "pilsner malt at 80% of grist" is useful, "Weyermann Barke Pilsner at 80%"
-- is not.
--
-- ⛔ substitute_basis EXISTS SO A COLOUR-DERIVED GUESS NEVER READS AS A
-- PUBLISHED EQUIVALENCE. Flavour equivalence is asserted nowhere: colour and
-- ppg are measured, flavour is not. A 'sourced' row needs a citation in
-- substitute_note; a cell stays NULL rather than carrying an uncited claim.
--
-- Runs AFTER 26_ref_fermentables.sql. Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS corpus;
REVOKE ALL ON SCHEMA corpus FROM PUBLIC;

CREATE TABLE IF NOT EXISTS corpus.fermentable_types (
  type_key         text PRIMARY KEY,
  role             text NOT NULL
                   CHECK (role IN ('base','character','colour','adjunct','sugar','extract')),
  lov_min          numeric(6,1),
  lov_max          numeric(6,1),
  typical_pct_min  numeric(5,2),
  typical_pct_max  numeric(5,2),
  substitute_id    bigint REFERENCES ref.fermentables(id) ON DELETE SET NULL,
  substitute_basis text CHECK (substitute_basis IN ('exact','colour_ppg','sourced','manual')),
  substitute_note  text
);

COMMENT ON TABLE corpus.fermentable_types IS
  'The 22-type vocabulary the corpus loader classifies into, each with a '
  'purchasable stand-in from ref.fermentables. role is exhaustive and mutually '
  'exclusive, which is what lets trend.style_grist_template sum to 100%.';

INSERT INTO corpus.fermentable_types
  (type_key, role, lov_min, lov_max, typical_pct_min, typical_pct_max) VALUES
  ('base_pilsner',      'base',        0,    3,  40, 100),
  ('base_pale',         'base',        0,    5,  40, 100),
  ('vienna',            'base',        3,    6,   0,  80),
  ('munich',            'base',        5,   20,   0,  80),
  ('wheat',             'base',        0,    8,   0,  70),
  ('rye',               'base',        0,    8,   0,  40),
  ('oats',              'adjunct',     0,   12,   0,  30),
  ('adjunct_starch',    'adjunct',     0,    5,   0,  40),
  ('dextrine',          'character',   0,    5,   0,  15),
  ('crystal_light',     'character',   5,   25,   0,  25),
  ('crystal_medium',    'character',  25,   70,   0,  20),
  ('crystal_dark',      'character',  70,  120,   0,  15),
  ('crystal_extra_dark','character', 120,  300,   0,  10),
  ('kilned_specialty',  'character',  10,  100,   0,  20),
  ('chocolate',         'colour',    200,  400,   0,  15),
  ('black',             'colour',    400,  600,   0,  10),
  ('roast_barley',      'colour',    300,  550,   0,  15),
  ('smoked',            'character',   0,   10,   0,  50),
  ('acidulated',        'character',   1,    5,   0,   5),
  ('sugar',             'sugar',       0,  300,   0,  20),
  ('sugar_lactose',     'sugar',       0,    2,   0,  10),
  ('extract',           'extract',     2,   30,   0, 100)
ON CONFLICT (type_key) DO NOTHING;

-- ---------------------------------------------------------------------------
-- The substitution map. Matched on name, so it survives identity churn in
-- ref.fermentables. Only rows still unmapped are touched -- a 'manual' bridge
-- is human work and is never overwritten.
-- ---------------------------------------------------------------------------
UPDATE corpus.fermentable_types t
SET substitute_id = f.id, substitute_basis = m.basis, substitute_note = m.note
FROM (VALUES
  ('base_pilsner',      'Pilsner Malt',                  'Weyermann','exact',     NULL),
  ('base_pale',         'Pale Ale Malt',                 'Weyermann','colour_ppg','stands in for American 2-row and Maris Otter'),
  ('vienna',            'Vienna Malt',                   'Weyermann','exact',     NULL),
  ('munich',            'Munich Malt Type 1',            'Weyermann','exact',     NULL),
  ('wheat',             'Wheat Malt pale',               'Weyermann','exact',     NULL),
  ('rye',               'Rye Malt pale',                 'Weyermann','exact',     NULL),
  ('dextrine',          'CARAFOAM®',                     'Weyermann','exact',     NULL),
  ('crystal_light',     'CARAHELL®',                     'Weyermann','colour_ppg','9.9 L, band 5-25'),
  ('crystal_medium',    'CARAAMBER®',                    'Weyermann','colour_ppg','26.9 L, band 25-70'),
  ('crystal_dark',      'CARABOHEMIAN®',                 'Weyermann','colour_ppg','74.0 L, band 70-120'),
  ('crystal_extra_dark','CARAAROMA®',                    'Weyermann','colour_ppg','151.2 L, band 120+'),
  ('chocolate',         'Chocolate Light Malt',          'Viking Malt','colour_ppg','150.5 L'),
  ('black',             'Black Malt',                    'Viking Malt','colour_ppg','525.2 L'),
  ('roast_barley',      'Roasted Barley',                'Viking Malt','exact',     NULL),
  ('kilned_specialty',  'Melanoidin Malt',               'Weyermann','colour_ppg','26.9 L; covers biscuit/victory/amber/aromatic'),
  ('smoked',            'Beech Smoked Barley Malt',      'Weyermann','exact',     NULL),
  ('oats',              'Flaked Oats',                    NULL,      'exact',     NULL),
  ('acidulated',        'Acidulated Malt',                NULL,      'exact',     NULL),
  ('adjunct_starch',    'Flaked Barley',                  NULL,      'colour_ppg','the commonest unmalted adjunct; corn/wheat/rice differ in colour only'),
  ('sugar',             'Corn Sugar - Dextrose',          NULL,      'colour_ppg','commonest sugar by usage'),
  ('sugar_lactose',     'Lactose (Milk Sugar)',           NULL,      'exact',     NULL),
  ('extract',           'Dry Malt Extract - Light',       NULL,      'colour_ppg','DME is flat 42 across grades')
) AS m(type_key, fname, fmaltster, basis, note)
JOIN ref.fermentables f
  ON f.name = m.fname
 AND f.maltster IS NOT DISTINCT FROM m.fmaltster
WHERE t.type_key = m.type_key
  AND (t.substitute_basis IS NULL OR t.substitute_basis <> 'manual');
