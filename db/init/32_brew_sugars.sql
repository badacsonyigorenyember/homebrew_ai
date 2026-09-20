-- =============================================================================
-- 32_brew_sugars.sql  ·  Sugars, syrups and flaked cereals
--
-- ⛔⛔ THIS FILE IS NOT LIKE 31_brew_misc.sql AND MUST BE READ DIFFERENTLY.
--
-- Everything in 31_ is 'misc' or 'water_agent', which brew.f_compute_recipe
-- never looks at, so a wrong row there is inert. Everything in THIS file is
-- 'adjunct' or 'fermentable', which f_compute_recipe reads on every single
-- call. A wrong potential_ppg here does not fail -- it silently shifts the OG,
-- FG and ABV of every recipe that uses the row, and nothing downstream can tell.
--
-- So the standard from 27_brew_catalogue.sql applies at full strength: no
-- figure is invented. Each row is one of three things, named in
-- attrs.provenance, exactly as 28_brew_derived_sugars.sql did for lactose:
--
--   'published'           a real source states it, and the source is named
--   'derived'             arithmetic from a stated constant, shown in full
--   'corpus_selfreported' the modal figure across corpus.fermentables, with n
--
-- and where a derivation and the corpus DISAGREE, both are recorded and the
-- disagreement is stated. It is never averaged away.
--
-- ---------------------------------------------------------------------------
-- THE CONSTANT EVERYTHING IS DERIVED FROM
--
-- 28_brew_derived_sugars.sql establishes it: the PPG scale is DEFINED by
-- sucrose = 46.21 PPG, i.e. one pound of sucrose in one US gallon gives
-- SG 1.04621. Any dry sugar that is chemically the same kind of thing and is
-- sold at less than 100% sugar solids scales by its solids fraction:
--
--     PPG = 46.21 * (mass fraction that is actually sugar solids)
--
-- That single line is the whole derivation method used below. It is the same
-- line 28_ used to get lactose from sucrose, and it is stated per row.
--
-- ---------------------------------------------------------------------------
-- ⛔ WHY THE FLAKED CEREALS ARE 'fermentable' AND NOT 'adjunct'
--
-- docs/RECIPE-PIPELINE-V2.md §5 Phase 2 item 9 lists "flaked adjuncts" for this
-- file, which reads as kind='adjunct'. Entering them that way would be an
-- arithmetic error, so they are entered as 'fermentable' instead. The reason is
-- in 29_brew_formulate.sql, in f_compute_recipe:
--
--     v_eff := CASE WHEN r.kind = 'adjunct' THEN 1.0 ELSE p_efficiency END;
--     -- "Sugars dissolve completely; only mashed grain is subject to
--     --  brewhouse efficiency."
--
-- 'adjunct' in this schema does not mean "not barley malt". It means "dissolves
-- completely, therefore 100% efficient". Dextrose and honey are that. Flaked
-- oats are not: they are gelatinised whole grain that has to be MASHED, and
-- their extract is subject to brewhouse efficiency like any malt. At the
-- default 0.72 efficiency, filing them as 'adjunct' would overstate their
-- gravity contribution by 1/0.72 = 39% -- about 4 gravity points for 1 kg of
-- flaked oats in a 20 L batch, silently, on every such recipe.
--
-- ⚠ The cost of the correct choice, stated so it is not a surprise:
-- brew.f_catalogue derives its `role` from colour for fermentables, so flaked
-- oats at 2.2 °L land in the 'base' bucket alongside pale malt. That is a
-- PROMPT-side classification question (it belongs with Phase 2 item 10, the
-- SECTIONS array in `Build propose pack`), not an arithmetic one, and it does
-- not touch the invariance this step is verified on. attrs.grain_class =
-- 'flaked' is recorded on each row so that work has something to filter on;
-- nothing in this file acts on it.
--
-- ---------------------------------------------------------------------------
-- ⛔ WHAT IS DELIBERATELY ABSENT
--
-- - Lactose. Already in the catalogue from 28_brew_derived_sugars.sql. Not
--   duplicated, and not re-derived.
-- - Maltodextrin. 28_ excluded it because its contribution is a function of DE
--   and DE 4 and DE 18 are different ingredients. That still holds.
-- - Belgian candi SYRUP (D-45/D-90/D-180). The corpus has it at 32 PPG, cleanly
--   separated from the dry rocks, but syrup is sold by brand-specific colour
--   grade and the colour is the whole reason to buy it. Adding four more rows
--   whose only real difference is a colour nobody here has verified is not
--   worth the risk; the dry sugar covers the gravity case.
-- - Fruit purees. They are in 31_ as 'misc' with an explicit note that this
--   UNDER-states OG, because no puree datasheet is in the library.
--
-- ---------------------------------------------------------------------------
-- IDEMPOTENCY
--
-- Same as 27_/28_/31_: NOT EXISTS on (kind, name), not ON CONFLICT. supplier is
-- NULL on every row and Postgres treats NULLs as distinct in the
-- UNIQUE (kind, name, supplier) index, so ON CONFLICT would not dedupe these.
--
-- Runs AFTER 28_brew_derived_sugars.sql. Idempotent.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Sugars and syrups -- kind 'adjunct' (dissolves completely, 100% efficiency)
-- -----------------------------------------------------------------------------
INSERT INTO brew.ingredients (kind, name, supplier, potential_ppg, color_lovibond, attrs)
SELECT v.kind, v.name, NULL, v.ppg, v.color, v.attrs
FROM (VALUES

  ('adjunct', 'Sucrose (table sugar)', 46.2::numeric, 0.0::numeric,
   jsonb_build_object(
     'provenance', 'published',
     'source', 'the definition of the PPG scale itself: sucrose = 46.21 PPG. '
               'This is the constant 28_brew_derived_sugars.sql derives lactose '
               'from; it is not a measurement of a product.',
     'exact_value', 46.21,
     'rounding', 'brew.ingredients.potential_ppg is numeric(5,1), so 46.21 is '
                 'stored as 46.2. The unrounded constant is in exact_value.',
     'fermentable', true,
     'apparent_attenuation_pct', 100,
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Cane Sugar', 'recipes', 6088,
        'ppg_mode', 46.00, 'ppg_min', 33.00, 'ppg_max', 46.00,
        'agrees', true),
     'note', 'Fully fermentable. Corroborated rather than sourced by the corpus: '
             '6,088 recipes put it at 46.0, which is the scale constant rounded.')),

  ('adjunct', 'Dextrose (corn sugar)', 42.0::numeric, 0.0::numeric,
   jsonb_build_object(
     'provenance', 'derived',
     'derivation', '46.21 PPG (sucrose, scale definition) * 180.16/198.17 '
                   '(anhydrous glucose / glucose monohydrate formula mass) '
                   '= 42.0',
     'assumes', 'dextrose MONOHYDRATE (C6H12O6·H2O), which is what brewing '
                'dextrose is sold as, at ~100% purity. Anhydrous dextrose would '
                'be 46.2, the same as sucrose.',
     'fermentable', true,
     'apparent_attenuation_pct', 100,
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Corn Sugar - Dextrose', 'recipes', 7576,
        'ppg_mode', 46.00, 'ppg_min', 42.00, 'ppg_max', 46.00,
        'agrees', false),
     'conflict', '⚠ 7,576 corpus recipes take the MODE at 46.0, not 42.0 -- but '
                 'their own minimum is exactly 42.0. 46 is the anhydrous figure '
                 'and is what you get by copying sucrose; 42 is the monohydrate '
                 'that is actually in the bag. The derivation is used, following '
                 '28_, which likewise preferred derived arithmetic over an '
                 'aggregate that disagreed with itself. The spread is 4.2 PPG '
                 'and is recorded rather than averaged.')),

  ('adjunct', 'Honey', 38.1::numeric, NULL::numeric,
   jsonb_build_object(
     'provenance', 'derived',
     'derivation', '46.21 PPG (sucrose, scale definition) * 0.824 (sugar solids '
                   'mass fraction of honey) = 38.1',
     'assumes', 'honey at 17.1% moisture with 82.4% of its mass as fermentable '
                'simple sugars (fructose, glucose, maltose). At the Codex 20% '
                'moisture MAXIMUM the same arithmetic gives 37.0, so the '
                'derivation is worth about ±1 PPG on grade alone.',
     'fermentable', true,
     'apparent_attenuation_pct', 100,
     'color_note', 'color_lovibond is deliberately NULL, not 0. Honey colour '
                   'runs from water-white to near-black by floral source and '
                   'there is no single honest figure; NULL contributes nothing '
                   'to MCU, which is the honest "unknown" rather than a guess. '
                   'Enter it from the honey actually bought if colour matters.',
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Honey', 'recipes', 5180,
        'ppg_mode', 42.00, 'ppg_min', 0.00, 'ppg_max', 42.30,
        'agrees', false),
     'conflict', '⚠ 5,180 corpus recipes take the mode at 42.0. 42/46.21 = 0.909 '
                 'implies 9% moisture, which no honey has -- it is dextrose''s '
                 'number reused. The derivation is used. Difference 3.9 PPG.')),

  ('adjunct', 'Maple syrup', 30.5::numeric, NULL::numeric,
   jsonb_build_object(
     'provenance', 'derived',
     'derivation', '46.21 PPG (sucrose, scale definition) * 0.660 (sugar solids '
                   'mass fraction) = 30.5',
     'assumes', 'Grade A maple syrup at the 66.0 °Brix legal minimum density, '
                'its solids treated as sucrose, which they predominantly are.',
     'fermentable', true,
     'apparent_attenuation_pct', 100,
     'color_note', 'color_lovibond is NULL. Maple grade runs Golden Delicate to '
                   'Very Dark and the colours differ by an order of magnitude; '
                   'the corpus mode of 35 °L has a minimum of 0, i.e. it is '
                   'noise. NULL contributes nothing to MCU.',
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Maple Syrup', 'recipes', 593,
        'ppg_mode', 30.00, 'ppg_min', 29.80, 'ppg_max', 30.00,
        'agrees', true),
     'note', 'The one row where derivation and corpus agree tightly: 30.5 '
             'derived against a corpus range of 29.8-30.0 over 593 recipes. '
             'That agreement is the best evidence in this file that the '
             '46.21 × solids-fraction method is sound.')),

  ('adjunct', 'Belgian candi sugar — clear/blond', 38.0::numeric, 0.0::numeric,
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Belgian Candi Sugar - Clear/Blond (0L)', 'recipes', 1424,
        'ppg_mode', 38.00, 'ppg_min', 12.50, 'ppg_max', 50.00,
        'color_mode', 0.00, 'color_min', 0.00, 'color_max', 0.00),
     'fermentable', true,
     'apparent_attenuation_pct', 100,
     'conflict', '⚠ UNRESOLVED, and load-bearing. Dry candi rock is essentially '
                 'sucrose, so the 46.21 × solids derivation used everywhere else '
                 'in this file would give ~46.2, not 38.0. 38.0/46.21 = 0.822, '
                 'i.e. the corpus figure implies ~82% solids, which fits a SOFT '
                 'or syrup-wetted candi sugar rather than a dry rock. Neither '
                 'reading can be confirmed from anything in this library, so the '
                 'corpus figure is used because (a) it is what 1,424 real '
                 'recipes and the brewing software they came from assume, and '
                 '(b) it is the LOWER of the two, so the failure direction is an '
                 'under-stated OG rather than an over-stated one. Uncertainty on '
                 'this row is ±8 PPG -- larger than any other row here.',
     'note', 'Colour 0 is a real reported zero (corpus min = max = 0), not a '
             'missing value. Light and dark candi differ in COLOUR, not in PPG: '
             'all three corpus grades sit at exactly 38.0.')),

  ('adjunct', 'Belgian candi sugar — amber/brown', 38.0::numeric, 60.0::numeric,
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Belgian Candi Sugar - Amber/Brown (60L)', 'recipes', 580,
        'ppg_mode', 38.00, 'ppg_min', 38.00, 'ppg_max', 38.00,
        'color_mode', 60.00, 'color_min', 60.00, 'color_max', 60.00),
     'fermentable', true,
     'apparent_attenuation_pct', 100,
     'conflict', 'Same ±8 PPG question as the clear grade -- see that row.',
     'note', 'ppg_min = ppg_max = 38.00 and color_min = color_max = 60.00 across '
             '580 recipes: this is a catalogue constant carried by brewing '
             'software, not 580 independent measurements. Weigh it as one '
             'source with wide adoption, not as 580.')),

  ('adjunct', 'Belgian candi sugar — dark', 38.0::numeric, 275.0::numeric,
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Belgian Candi Sugar - Dark (275L)', 'recipes', 468,
        'ppg_mode', 38.00, 'ppg_min', 38.00, 'ppg_max', 38.00,
        'color_mode', 275.00, 'color_min', 275.00, 'color_max', 275.00),
     'fermentable', true,
     'apparent_attenuation_pct', 100,
     'conflict', 'Same ±8 PPG question as the clear grade -- see that row.',
     'note', '⚠ 275 °L is a large colour figure and it DOES enter SRM through '
             'MCU. It is a catalogue constant (min = max across 468 recipes), '
             'not a measurement, and the real product varies. 200 g in a 20 L '
             'batch contributes about 5.7 MCU on its own.')),

  ('adjunct', 'Rice hulls', 0.0::numeric, 0.0::numeric,
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Rice Hulls', 'recipes', 4312,
        'ppg_mode', 0.00, 'ppg_min', 0.00, 'ppg_max', 0.10,
        'color_mode', 0.00, 'color_min', 0.00, 'color_max', 0.01),
     'fermentable', false,
     'apparent_attenuation_pct', 0,
     'purpose', 'lauter aid — a filter bed that keeps a high-oat or high-wheat '
                'mash from setting. Not an ingredient of the beer.',
     'note', '⭐ 0.0 is a MEASURED ZERO, not a missing figure, and the '
             'difference matters: NULL would mean "nobody knows", 0.0 means '
             '"known to contribute nothing". Rice hulls are indigestible husk '
             'with no extract, and 4,312 corpus recipes agree at exactly 0.00 '
             '(max 0.10). Being an adjunct at 0.0 PPG it is arithmetically inert '
             'whatever the efficiency, so it is the one row in this file that '
             'cannot be wrong.'))

) AS v(kind, name, ppg, color, attrs)
WHERE NOT EXISTS (SELECT 1 FROM brew.ingredients i
                  WHERE i.kind = v.kind AND i.name = v.name);

-- -----------------------------------------------------------------------------
-- Flaked cereals -- kind 'fermentable' (MASHED, therefore subject to efficiency)
--
-- See the header for why these are not 'adjunct'. Figures are the mode across
-- corpus.fermentables, which is how 71_corpus_dims.sql computes that column
-- (mode() WITHIN GROUP (ORDER BY f.potential_ppg)). ppg_min is 0.00 on several
-- of these because some source recipes carry a blank yield; the MODE is
-- unaffected by those and the raw extremes are recorded anyway rather than
-- quietly trimmed.
--
-- These are corpus_selfreported and NOT published: no maltster datasheet for a
-- flaked cereal is in ref.fermentables (checked 2026-09-16 -- ref.fermentables has exactly one
-- row matching /flake|oat|maize|rice|corn/, Viking "Oat Malt", which is malted
-- oats and a different ingredient). If a flaked-cereal datasheet is ever
-- ingested, these rows should be superseded by ref.* rows through 27_'s path.
-- -----------------------------------------------------------------------------
INSERT INTO brew.ingredients (kind, name, supplier, potential_ppg, color_lovibond, attrs)
SELECT v.kind, v.name, NULL, v.ppg, v.color, v.attrs
FROM (VALUES

  ('fermentable', 'Flaked oats', 33.0::numeric, 2.2::numeric,
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'grain_class', 'flaked',
     'mashed', true,
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Flaked Oats', 'recipes', 23308, 'additions', 23338,
        'ppg_mode', 33.00, 'ppg_min', 0.00, 'ppg_max', 39.10,
        'color_mode', 2.20, 'color_min', 0.00, 'color_max', 60.00),
     'note', 'The most-used flaked cereal in the corpus by a wide margin. '
             'ppg_max 39.1 and color_max 60.0 are outliers from mis-entered '
             'source recipes; the mode is what is stored.')),

  ('fermentable', 'Flaked wheat', 34.0::numeric, 2.0::numeric,
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'grain_class', 'flaked',
     'mashed', true,
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Flaked Wheat', 'recipes', 8988, 'additions', 8995,
        'ppg_mode', 34.00, 'ppg_min', 0.00, 'ppg_max', 34.00,
        'color_mode', 2.00, 'color_min', 1.50, 'color_max', 2.00),
     'note', 'Tight spread: ppg_max equals the mode and colour runs 1.5-2.0 '
             'across 8,988 recipes.')),

  ('fermentable', 'Flaked maize', 40.0::numeric, 0.5::numeric,
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'grain_class', 'flaked',
     'mashed', true,
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Flaked Corn', 'recipes', 4456, 'additions', 4467,
        'ppg_mode', 40.00, 'ppg_min', 0.00, 'ppg_max', 40.00,
        'color_mode', 0.50, 'color_min', 0.00, 'color_max', 1.30),
     'note', 'Entered under the British name; the corpus row is "Flaked Corn". '
             'Highest yield of the flaked cereals -- nearly pure gelatinised '
             'starch with the germ removed.')),

  ('fermentable', 'Flaked barley', 32.0::numeric, 2.2::numeric,
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'grain_class', 'flaked',
     'mashed', true,
     'corpus', jsonb_build_object(
        'source', 'corpus.fermentables (mode across per-recipe entries), '
                  '174,554 public recipes, measured 2026-09-16',
        'name', 'Flaked Barley', 'recipes', 5923, 'additions', 5927,
        'ppg_mode', 32.00, 'ppg_min', 0.00, 'ppg_max', 34.00,
        'color_mode', 2.20, 'color_min', 0.00, 'color_max', 3.00),
     'note', 'Unmalted, so it carries no enzyme of its own and needs a base '
             'malt to convert it. Lowest yield of the four.'))

) AS v(kind, name, ppg, color, attrs)
WHERE NOT EXISTS (SELECT 1 FROM brew.ingredients i
                  WHERE i.kind = v.kind AND i.name = v.name);
