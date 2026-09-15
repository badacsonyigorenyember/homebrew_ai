-- =============================================================================
-- 28_brew_derived_sugars.sql  ·  Sugars whose figure is DERIVED, not cited
--
-- ⛔ Read this before adding anything here.
--
-- Every other row in brew.ingredients traces to a published datasheet: malts to
-- ref.malts (maltster spec sheets), hops to ref.hops (Hop Variety Handbook). The
-- rows in THIS file do not, and the file is separate so that can never be
-- mistaken. Maltsters do not publish specs for lactose -- it is a dairy
-- commodity, not a malt product -- and the homebrew aggregators that do quote a
-- figure disagree with each other (41, 35-46, and one worked example implying
-- 30 on the same page).
--
-- So the figure is derived instead, transparently:
--
--   The PPG scale is defined by sucrose = 46.21 PPG. Lactose and sucrose are
--   both disaccharides of molecular weight 342.3, so anhydrous lactose sits at
--   essentially the same value. Brewing lactose is sold as the MONOHYDRATE
--   (C12H22O11.H2O, MW 360.3), so ~5.0% of its mass is water of crystallisation:
--
--       46.21 * (342.3 / 360.3) = 43.9 PPG
--
-- attrs.provenance says 'derived' so any consumer can tell this apart from a
-- citation, and attrs.derivation carries the arithmetic so it can be rechecked.
--
-- ⛔ Maltodextrin is deliberately NOT here. Its gravity contribution is a
-- function of DE (dextrose equivalent), which varies by product -- DE 4 and
-- DE 18 are different ingredients. There is no single correct number, so it
-- must be entered from the product actually bought.
--
-- Runs AFTER 27_brew_catalogue.sql. Idempotent.
-- =============================================================================

INSERT INTO brew.ingredients (kind, name, supplier, potential_ppg, color_lovibond, attrs)
SELECT 'adjunct', 'Lactose (milk sugar)', NULL, 43.9, 1.0,
       jsonb_build_object(
         'provenance',  'derived',
         'derivation',  '46.21 PPG (sucrose, scale definition) * 342.3/360.3 '
                        '(anhydrous/monohydrate MW) = 43.9',
         'assumes',     'lactose monohydrate, food grade, ~100% purity',
         'fermentable', false,
         'apparent_attenuation_pct', 0,
         'note',        'Unfermentable by brewers yeast: contributes to OG and '
                        'stays in FG. Not from the library -- no ingested source '
                        'states a gravity figure for lactose.')
WHERE NOT EXISTS (SELECT 1 FROM brew.ingredients
                  WHERE kind = 'adjunct' AND name = 'Lactose (milk sugar)');
