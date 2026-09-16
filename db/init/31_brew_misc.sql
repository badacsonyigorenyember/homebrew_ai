-- =============================================================================
-- 31_brew_misc.sql  ·  Flavourings, spices, oak, fruit, and water salts
--
-- ⛔ Read 27_brew_catalogue.sql and 28_brew_derived_sugars.sql first. The rule
-- they set is binding here: a spec is never invented. Every row below carries
-- attrs.provenance saying which of three things it is --
--
--   'published'           a real source says this, and the source is named
--   'derived'             arithmetic from a stated constant, shown in full so
--                         it can be rechecked (the 28_ pattern)
--   'corpus_selfreported' what brewers in corpus.* actually did, with the n
--
-- ---------------------------------------------------------------------------
-- WHY THIS FILE IS SAFE TO ADD, and how that was checked
--
-- brew.f_compute_recipe reads exactly two kinds for gravity and colour and one
-- for bitterness. From 29_brew_formulate.sql, its only two ingredient loops are:
--
--     WHERE i.kind IN ('fermentable','adjunct')     -- gravity + MCU/SRM
--     WHERE i.kind = 'hop'                          -- Tinseth IBU
--
-- Verified against the live catalogue rather than the file, 2026-09-16:
--
--     select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
--     where n.nspname='brew' and p.proname='f_compute_recipe'
--       and pg_get_functiondef(p.oid) ~ 'kind IN \(''fermentable'',''adjunct''\)';
--     -- 1
--
-- Nothing in this file is 'fermentable', 'adjunct' or 'hop'. Every row is
-- 'misc' or 'water_agent', so every row is ARITHMETICALLY INERT: adding them
-- cannot move OG, FG, ABV, IBU or SRM by any amount, and f_compute_recipe
-- returns a byte-identical result with and without them. That invariance is
-- the stated verification for this step and it is proved by construction, not
-- by hoping the numbers happen to match.
--
-- The consequence, which is the whole point: a vanilla bean gets NO
-- potential_ppg. There is no honest one. It appears on the recipe sheet as a
-- line with a stage, an amount and a citation, and never as a term in the
-- gravity equation.
--
-- ---------------------------------------------------------------------------
-- UNITS
--
-- brew.ingredients has no unit column -- brew.f_save_recipe writes every
-- recipe_item in grams. That is right for hops and malt and wrong for a vanilla
-- bean, which is counted. attrs.unit records the unit the ingredient is
-- ACTUALLY measured in, and attrs.corpus.median is the corpus median in that
-- unit. Nothing here converts; consumers read attrs.unit and render it.
--
-- ---------------------------------------------------------------------------
-- IDEMPOTENCY
--
-- brew.ingredients has UNIQUE (kind, name, supplier), but supplier is NULL on
-- every row here and Postgres treats NULLs as distinct in a unique index, so
-- ON CONFLICT would NOT dedupe these. 27_ and 28_ both use NOT EXISTS for the
-- same reason; this file does too. db-init applies its whole list on every
-- stack start, so re-running must insert nothing.
--
-- Runs AFTER 27_brew_catalogue.sql. Idempotent.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Flavourings and spices -- kind 'misc'
--
-- Every figure here is corpus_selfreported: corpus.recipe_misc holds 141,857
-- additions across 174,554 public recipes, each with the brewer's own stage
-- (use_raw) and amount. Measured 2026-09-16. This is evidence of PRACTICE, not
-- authority -- §2 of docs/RECIPE-PIPELINE-V2.md is explicit that the corpus says
-- what is popular and never what is good -- so attrs.corpus carries the n so a
-- reader can weigh it. Name variants were folded case-insensitively (e.g.
-- 'Vanilla Bean', 'vanilla beans', 'Vanilla' -> one group); attrs.corpus.n_names
-- is not recorded because the fold is in this file's history, not the data.
--
-- ⛔ Coffee is TWO ingredients and they are entered separately on purpose.
-- Whole/ground beans are a solid dosed by mass and steeped in the beer; cold
-- brew is a liquid extract dosed by volume that also ADDS volume to the batch.
-- The corpus separates them too, and their stage distributions differ: beans
-- are 44% Secondary and 26% Boil, cold brew is 41% Secondary and 36% at
-- bottling/kegging -- i.e. beans go in the beer, cold brew mostly goes in at
-- packaging. Folding them into one row would lose both the unit and the stage.
--
-- ⛔ Bitter and sweet orange peel are likewise separate. They are different
-- species (Citrus aurantium vs sinensis), the corpus records them separately,
-- and the median doses differ by half (14 g vs 20.5 g).
--
-- ⛔ Lactose is NOT here. It is already in the catalogue as an 'adjunct' with a
-- derived potential_ppg -- see 28_brew_derived_sugars.sql. It belongs there
-- because it DOES enter the gravity equation; nothing in this file does.
-- -----------------------------------------------------------------------------
INSERT INTO brew.ingredients (kind, name, supplier, potential_ppg, color_lovibond, attrs)
SELECT v.kind, v.name, NULL, NULL, NULL, v.attrs
FROM (VALUES

  ('misc', 'Vanilla bean',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'each',
     'category', 'flavour',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 1538, 'additions', 1585,
        'top_uses', 'Secondary 1018 · Boil 209 · Primary 191 · Kegging 67',
        'median', 2, 'p25', 1, 'p75', 2.5, 'median_unit', 'each', 'median_n', 1194),
     'note', 'Counted, never weighed. No honest potential_ppg exists for a '
             'vanilla bean and none is given: it is a line on the sheet with a '
             'stage and a citation, not a term in the gravity equation.')),

  ('misc', 'Cacao nibs',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'g',
     'category', 'flavour',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 1075, 'additions', 1156,
        'top_uses', 'Secondary 677 · Boil 263 · Primary 131 · Mash 39',
        'median', 113, 'median_unit', 'g',
        'median_basis', '4 oz median where dosed in oz (n=801) = 113 g; '
                        '100 g median where dosed in g (n=298)'),
     'note', 'Cocoa nibs and cacao nibs are the same thing under two spellings; '
             'the corpus figures above fold both. Cocoa POWDER is a different '
             'ingredient and is deliberately not entered.')),

  ('misc', 'Coffee beans (whole or ground)',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'g',
     'category', 'flavour',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 562, 'additions', 603,
        'top_uses', 'Secondary 266 · Boil 156 · Primary 83 · Kegging 27',
        'median', 50, 'p25', 17.9, 'p75', 100, 'median_unit', 'g', 'median_n', 191),
     'note', 'A solid steeped in the beer. Distinct from Cold brew coffee, '
             'which is a liquid dosed by volume -- see that row.')),

  ('misc', 'Cold brew coffee',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'ml',
     'category', 'flavour',
     'adds_volume', true,
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 274, 'additions', 282,
        'top_uses', 'Secondary 117 · Bottling 61 · Kegging 39 · Primary 31',
        'median', 500, 'p25', 200, 'p75', 500, 'median_unit', 'ml', 'median_n', 25),
     'note', 'A liquid extract. It ADDS volume to the batch, which dilutes the '
             'packaged gravity -- adds_volume flags that; nothing in this repo '
             'acts on it yet. Dosed mostly at packaging, unlike whole beans.')),

  ('misc', 'Cinnamon stick',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'each',
     'category', 'spice',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 1622, 'additions', 1740,
        'top_uses', 'Boil 1168 · Secondary 298 · Primary 103 · Whirlpool 51',
        'median', 2, 'p25', 1, 'p75', 3, 'median_unit', 'each', 'median_n', 717),
     'note', 'Corpus figures fold sticks and ground cinnamon, which are dosed '
             'in different units (717 additions in "each", 474 in tsp, 224 in '
             'g). The "each" figure is the one quoted; ground is not entered '
             'as a separate row because the corpus does not separate it '
             'cleanly enough to stand on its own.')),

  ('misc', 'Star anise',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'each',
     'category', 'spice',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 151, 'additions', 153,
        'top_uses', 'Boil 122 · Secondary 13 · Primary 7 · Mash 6',
        'median', 2, 'p25', 1, 'p75', 3, 'median_unit', 'each', 'median_n', 72),
     'note', 'Counted as whole pods. n=151 recipes is thin next to coriander; '
             'the figure is reported with its n so it can be weighed.')),

  ('misc', 'Coriander seed',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'g',
     'category', 'spice',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 3031, 'additions', 3115,
        'top_uses', 'Boil 2774 · Mash 138 · Whirlpool 66 · Secondary 61',
        'median', 14, 'p25', 7, 'p75', 21.3, 'median_unit', 'g', 'median_n', 1366),
     'note', 'Overwhelmingly a late boil addition (89%). Corpus figures fold '
             'whole seed, crushed and ground.')),

  ('misc', 'Bitter orange peel',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'g',
     'category', 'spice',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 645, 'additions', 663,
        'top_uses', 'Boil 601 · Mash 22 · Whirlpool 12 · Secondary 9',
        'median', 14, 'p25', 8, 'p75', 28, 'median_unit', 'g', 'median_n', 178),
     'note', 'Citrus aurantium. Kept separate from sweet peel: different '
             'species, and the corpus median dose is a third lower.')),

  ('misc', 'Sweet orange peel',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'g',
     'category', 'flavour',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 791, 'additions', 815,
        'top_uses', 'Boil 694 · Secondary 33 · Whirlpool 30 · Primary 25',
        'median', 20.5, 'p25', 13.8, 'p75', 50, 'median_unit', 'g', 'median_n', 176),
     'note', 'Citrus sinensis. See Bitter orange peel for why the two are '
             'separate rows.')),

  ('misc', 'Oak cubes',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'g',
     'category', 'wood',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 258, 'additions', 261,
        'top_uses', 'Secondary 209 · Primary 32 · Kegging 10 · Other 4',
        'median', 57, 'median_unit', 'g',
        'median_basis', '2 oz median where dosed in oz (n=197) = 57 g; '
                        '40 g median where dosed in g (n=33)'),
     'note', 'Toast level and oak species are NOT recorded: the corpus does not '
             'carry them reliably and they change the result more than the mass '
             'does. Enter them from the product actually bought. Oak CHIPS are '
             'a separate, more common form (474 recipes) and are deliberately '
             'not added here -- they extract faster and are not interchangeable '
             'by mass.')),

  ('misc', 'Oak spirals',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'each',
     'category', 'wood',
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 44, 'additions', 44,
        'top_uses', 'Secondary 32 · Primary 4 · Mash 4 · Kegging 3',
        'median', 1, 'p25', 1, 'p75', 2, 'median_unit', 'each', 'median_n', 36),
     'note', '⚠ n=44 recipes. That is thin, and it is stated rather than '
             'smoothed over. A spiral is sold sized for a 5 gal batch, which is '
             'why the median is 1 and why it is counted, not weighed.')),

  ('misc', 'Raspberry puree',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'kg',
     'category', 'fruit',
     'adds_volume', true,
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 63, 'additions', 67,
        'top_uses', 'Secondary 41 · Primary 14 · Boil 7 · Bottling 3',
        'median', 1.36, 'median_unit', 'kg',
        'median_basis', '3 lb median where dosed in lb (n=34) = 1.36 kg'),
     'note', '⚠ Fruit puree DOES carry fermentable sugar and so does move OG in '
             'reality -- roughly 10% sugar by mass for raspberry. It is entered '
             'as misc anyway because no published figure for a specific '
             'commercial puree is in this library, and a guessed potential_ppg '
             'in an adjunct row would silently corrupt every recipe using it. '
             'The consequence is that OG is UNDER-stated for fruit beers, which '
             'is stated here rather than hidden. Fix by ingesting a puree '
             'datasheet and moving the row to 32_, not by inventing a number.')),

  ('misc', 'Mango puree',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'kg',
     'category', 'fruit',
     'adds_volume', true,
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 78, 'additions', 81,
        'top_uses', 'Secondary 42 · Primary 17 · Boil 16 · Mash 3',
        'median', 1.81, 'median_unit', 'kg',
        'median_basis', '4 lb median where dosed in lb (n=17) = 1.81 kg'),
     'note', 'See Raspberry puree for why fruit is misc and what that costs.')),

  ('misc', 'Apricot puree',
   jsonb_build_object(
     'provenance', 'corpus_selfreported',
     'unit', 'kg',
     'category', 'fruit',
     'adds_volume', true,
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 56, 'additions', 57,
        'top_uses', 'Secondary 42 · Primary 12 · Other 1 · Boil 1',
        'median', 1.36, 'median_unit', 'kg',
        'median_basis', '3 lb median where dosed in lb (n=40) = 1.36 kg'),
     'note', 'See Raspberry puree for why fruit is misc and what that costs.'))

) AS v(kind, name, attrs)
WHERE NOT EXISTS (SELECT 1 FROM brew.ingredients i
                  WHERE i.kind = v.kind AND i.name = v.name);

-- -----------------------------------------------------------------------------
-- Water salts -- kind 'water_agent'
--
-- These rows carry a chemical formula and an ION CONTRIBUTION, not a gravity
-- figure, because that is the only number about a brewing salt that is ever
-- used. The unit throughout is ppm (mg/L) contributed per GRAM PER US GALLON,
-- which is the unit the ingested source states its own figures in.
--
-- ⭐ The derivation is validated against the library before being trusted.
-- kb document 3, "Water: A Comprehensive Guide for Brewers" (Palmer &
-- Kaminski), p.144, chunk 913, states for calcium sulfate:
--
--     "1 gram per gallon adds 61.5 ppm of calcium and 147 ppm of sulfate"
--
-- Gypsum is therefore 'published' and cites that page. Every other salt is
-- 'derived' by this arithmetic:
--
--     ppm per g/gal  =  1000 * (ion formula mass / salt formula mass) / 3.78541
--
-- Applying it to gypsum, CaSO4·2H2O, formula mass 172.17:
--     Ca : 1000 * (40.08/172.17) / 3.78541 = 61.5 ppm   ← matches the book
--     SO4: 1000 * (96.06/172.17) / 3.78541 = 147.4 ppm  ← matches the book
--
-- The method reproduces the one published figure this library actually contains,
-- to the digit. That is why the other five are derived and not guessed. They
-- are still labelled 'derived', because reproducing one case is evidence, not a
-- citation, and attrs.derivation carries the arithmetic for each.
--
-- ⛔ The book's Table 17 ("Ion Contributions by Salt Additions") is referenced in
-- chunks 894 and 895 but its CELLS did not survive docling's table extraction --
-- only the caption did. So the table cannot be cited for the other five salts
-- even though it contains them. That is a library gap, recorded here rather than
-- papered over by pretending the numbers came from it.
-- -----------------------------------------------------------------------------
INSERT INTO brew.ingredients (kind, name, supplier, potential_ppg, color_lovibond, attrs)
SELECT v.kind, v.name, NULL, NULL, NULL, v.attrs
FROM (VALUES

  ('water_agent', 'Gypsum (calcium sulfate)',
   jsonb_build_object(
     'provenance', 'published',
     'source', 'kb document 3, Water: A Comprehensive Guide for Brewers '
               '(Palmer & Kaminski), p.144 (kb.chunks id 913)',
     'formula', 'CaSO4·2H2O',
     'formula_mass', 172.17,
     'unit', 'g',
     'ion_ppm_per_g_per_gal', jsonb_build_object('Ca', 61.5, 'SO4', 147.0),
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 14547, 'additions', 15240,
        'top_uses', 'Mash 13595 · Boil 927 · Sparge 540 · Other 159',
        'median', 4, 'p25', 2.2, 'p75', 7.1, 'median_unit', 'g', 'median_n', 12430),
     'note', 'The commonest way to add sulfate (same source, p.133). Hard to '
             'dissolve: saturation is about 1.9-2.1 g/L (p.135).')),

  ('water_agent', 'Calcium chloride (dihydrate)',
   jsonb_build_object(
     'provenance', 'derived',
     'derivation', '1000 * (40.08/147.01) / 3.78541 = 72.0 ppm Ca ; '
                   '1000 * (70.90/147.01) / 3.78541 = 127.4 ppm Cl',
     'derivation_method', 'validated against the published gypsum figure -- see '
                          'the header of 31_brew_misc.sql',
     'formula', 'CaCl2·2H2O',
     'formula_mass', 147.01,
     'unit', 'g',
     'ion_ppm_per_g_per_gal', jsonb_build_object('Ca', 72.0, 'Cl', 127.4),
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 12247, 'additions', 12897,
        'top_uses', 'Mash 11879 · Sparge 542 · Boil 354 · Other 106',
        'median', 4, 'p25', 2, 'p75', 6, 'median_unit', 'g', 'median_n', 11248),
     'assumes', 'the DIHYDRATE at full purity. ⚠ kb doc 3 p.135 warns that '
                'calcium chloride is deliquescent and that commercial food-grade '
                'product is often only 75-80% CaCl2·2H2O, so a real addition may '
                'contribute up to a quarter less than these figures.')),

  ('water_agent', 'Chalk (calcium carbonate)',
   jsonb_build_object(
     'provenance', 'derived',
     'derivation', '1000 * (40.08/100.09) / 3.78541 = 105.8 ppm Ca ; '
                   '1000 * (60.01/100.09) / 3.78541 = 158.4 ppm CO3',
     'derivation_method', 'validated against the published gypsum figure -- see '
                          'the header of 31_brew_misc.sql',
     'formula', 'CaCO3',
     'formula_mass', 100.09,
     'unit', 'g',
     'ion_ppm_per_g_per_gal', jsonb_build_object('Ca', 105.8, 'CO3', 158.4),
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 1479, 'additions', 1522,
        'top_uses', 'Mash 1427 · Boil 49 · Sparge 32 · Other 12',
        'median', 4.5, 'p25', 2, 'p75', 9, 'median_unit', 'g', 'median_n', 1397),
     'note', '⛔ These ion figures are NOMINAL and are mostly not achieved. kb '
             'doc 3 p.136 (kb.chunks id 895): chalk is practically insoluble, '
             'about 0.05 g/L, dissolving it in the mash precipitates hydroxyl '
             'apatite almost immediately, and "experiments have shown that it is '
             'largely ineffective". p.102 (chunk 825) adds that added chalk '
             '"never dissolves and is therefore never part of the system". The '
             'row exists because 1,479 corpus recipes use it, not because it '
             'works.')),

  ('water_agent', 'Epsom salt (magnesium sulfate)',
   jsonb_build_object(
     'provenance', 'derived',
     'derivation', '1000 * (24.31/246.47) / 3.78541 = 26.1 ppm Mg ; '
                   '1000 * (96.06/246.47) / 3.78541 = 103.0 ppm SO4',
     'derivation_method', 'validated against the published gypsum figure -- see '
                          'the header of 31_brew_misc.sql',
     'formula', 'MgSO4·7H2O',
     'formula_mass', 246.47,
     'unit', 'g',
     'ion_ppm_per_g_per_gal', jsonb_build_object('Mg', 26.1, 'SO4', 103.0),
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 4738, 'additions', 5013,
        'top_uses', 'Mash 4633 · Sparge 256 · Boil 73 · Other 30',
        'median', 2, 'p25', 1, 'p75', 4, 'median_unit', 'g', 'median_n', 4674),
     'note', 'Adds sulfate as well as magnesium (kb doc 3 p.133). The same page '
             'cites the EBC Manual of Good Practice that magnesium above roughly '
             '86 ppm turns sour and bitter, and that some sources hold 40 ppm as '
             'the ceiling.')),

  ('water_agent', 'Table salt (sodium chloride)',
   jsonb_build_object(
     'provenance', 'derived',
     'derivation', '1000 * (22.99/58.44) / 3.78541 = 103.9 ppm Na ; '
                   '1000 * (35.45/58.44) / 3.78541 = 160.3 ppm Cl',
     'derivation_method', 'validated against the published gypsum figure -- see '
                          'the header of 31_brew_misc.sql',
     'formula', 'NaCl',
     'formula_mass', 58.44,
     'unit', 'g',
     'ion_ppm_per_g_per_gal', jsonb_build_object('Na', 103.9, 'Cl', 160.3),
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 2835, 'additions', 2937,
        'top_uses', 'Mash 2638 · Boil 166 · Sparge 95 · Other 18',
        'median', 1.25, 'p25', 1, 'p75', 3, 'median_unit', 'g', 'median_n', 2699),
     'assumes', 'non-iodised salt. Iodised salt carries iodate, which is not '
                'wanted in beer; the corpus does not distinguish them.')),

  ('water_agent', 'Baking soda (sodium bicarbonate)',
   jsonb_build_object(
     'provenance', 'derived',
     'derivation', '1000 * (22.99/84.01) / 3.78541 = 72.3 ppm Na ; '
                   '1000 * (61.02/84.01) / 3.78541 = 191.9 ppm HCO3',
     'derivation_method', 'validated against the published gypsum figure -- see '
                          'the header of 31_brew_misc.sql',
     'formula', 'NaHCO3',
     'formula_mass', 84.01,
     'unit', 'g',
     'ion_ppm_per_g_per_gal', jsonb_build_object('Na', 72.3, 'HCO3', 191.9),
     'corpus', jsonb_build_object(
        'source', 'corpus.recipe_misc, 174,554 public recipes, measured 2026-09-16',
        'recipes', 2168, 'additions', 2235,
        'top_uses', 'Mash 2109 · Sparge 81 · Boil 33 · Other 7',
        'median', 2.5, 'p25', 1.2, 'p75', 4.5, 'median_unit', 'g', 'median_n', 2029),
     'note', '⚠ The HCO3 figure is a mass balance, not an alkalinity. kb doc 3 '
             'p.136 (kb.chunks id 895) is explicit that bicarbonate dissociates '
             'according to pH, so the alkalinity actually contributed depends on '
             'the water pH and the target pH and cannot be read off this row.'))

) AS v(kind, name, attrs)
WHERE NOT EXISTS (SELECT 1 FROM brew.ingredients i
                  WHERE i.kind = v.kind AND i.name = v.name);
