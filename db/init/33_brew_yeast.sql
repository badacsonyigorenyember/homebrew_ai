-- =============================================================================
-- 33_brew_yeast.sql  ·  The yeast catalogue, seeded from self-reported corpus data
--
-- ⛔ READ THIS BEFORE TRUSTING A NUMBER IN THIS FILE.
--
-- ⛔⛔ WIRING: THE NUMBER IN THE FILENAME IS NOT THE EXECUTION ORDER.
-- docker-compose.yml's db-init loop is a hardcoded list, not a glob, and it is
-- the execution order. This file SELECTs from corpus.yeasts, which is created by
-- 71_corpus_dims.sql. It must therefore be listed AFTER /db-init/71_corpus_dims.sql
-- -- i.e. at the END of the list -- even though it sorts as "33". Placed in
-- numeric order it will fail on a fresh database with "relation corpus.yeasts
-- does not exist", and because the loop runs with ON_ERROR_STOP=1 that halts
-- db-init and silently skips every later file (the exact failure 27_brew_catalogue.sql
-- documents). It is named 33_ because it belongs to the brew catalogue by subject.
--
-- =============================================================================
-- 0. This is a RECOMMENDATION ACTED ON, not a decision the user made
-- =============================================================================
-- docs/RECIPE-PIPELINE-V2.md §7 Q1 ("Yeast provenance") is an OPEN question. The
-- user has not answered it. The plan's own recommendation is option (a) -- seed
-- from corpus.yeasts with attrs.provenance = 'corpus_selfreported', following
-- 28_brew_derived_sugars.sql's honesty pattern -- with (c) as the later upgrade.
-- This file implements (a) on that recommendation alone.
--
-- What would change if the user picks differently:
--
--   (b) hand-enter ~40 strains from manufacturer datasheets
--       -> This file's SELECT is replaced by a VALUES list of ~40 rows, each
--          carrying attrs.source_doc = the lab's datasheet + revision date, and
--          attrs.provenance = 'datasheet'. The catalogue shrinks from ~120 to
--          ~40: lager and Brett coverage gets thinner, and the corpus ranking
--          (which strains brewers actually use) is lost. Nothing downstream
--          breaks -- the column contract is identical.
--
--   (c) ingest a yeast datasheet PDF through docling and derive from ref.*
--       -> A ref.yeasts table is created first (it does not exist today --
--          71_corpus_dims.sql says so explicitly and says why). This file then
--          becomes a sibling of 27_brew_catalogue.sql: SELECT ... FROM ref.yeasts,
--          attrs.ref_yeast_id + attrs.source_doc, provenance = 'ref'. The rows
--          seeded here are then REPLACED, not merged: a corpus figure and a
--          datasheet figure for the same strain must not coexist under one name.
--          The upgrade is a delete-where-provenance='corpus_selfreported' plus
--          the new insert, which is why the tag below is load-bearing.
--
-- =============================================================================
-- 1. Why this does not break 27_brew_catalogue.sql's rule
-- =============================================================================
-- 27_brew_catalogue.sql forbids INVENTING a spec. It does not forbid recording
-- one whose origin is stated. Every row here carries
-- attrs.provenance = 'corpus_selfreported' plus the exact corpus string and the
-- recipe count it was measured over, so no consumer can mistake it for the
-- maltster/handbook contract that ref.fermentables and ref.hops hold. This is the same
-- move 28_brew_derived_sugars.sql makes for lactose: the number is not a
-- citation, and the row says so in a machine-readable field.
--
-- ⛔ The corpus tells you what is POPULAR. It never tells you what is GOOD.
-- n_recipes is a usage count from a recipe-sharing site, nothing more.
--
-- =============================================================================
-- 2. Attenuation: kept. Range: DISCARDED.
-- =============================================================================
-- corpus.yeasts.attenuation_pct is the MODE of the figure across every recipe
-- using the strain. 71_corpus_dims.sql explains why that is usable: the specs
-- are the recipe site's own strain database denormalised onto every recipe, so
-- the mode is that database's single value, not a crowd average. Spot-checked
-- against manufacturer datasheets (RECIPE-PIPELINE-V2 §1.2, re-verified here):
-- US-05 81, S-04 75, WLP002 66.5, W-34/70 83 -- all correct.
--
-- corpus.yeasts.attenuation_min / attenuation_max are the min and max across
-- recipes, i.e. what users TYPED after editing the field. Measured here: US-05's
-- own span is 0.00 to 127.00 (the figure RECIPE-PIPELINE-V2 §4 quotes), and
-- across the whole table the columns span 0.00 to 140.00. That is not a spec
-- range, it is a typo range, and it is discarded. It is NOT copied into
-- brew.ingredients.attenuation_min / attenuation_max merely because the column
-- names line up.
--
-- What IS written to attenuation_min / attenuation_max: the single mode figure,
-- in BOTH columns, deliberately equal. Reading min = max = 81.0 is the honest
-- statement "this is a point estimate, not a range" -- while keeping the one
-- number a consumer actually needs (f_compute_recipe's p_attenuation) in the
-- typed column that exists for it, rather than only in jsonb. Under (b) or (c)
-- these two columns become a genuine published range and stop being equal.
--
-- =============================================================================
-- 3. Temperature: the unit repair rule, and why it is safe
-- =============================================================================
-- corpus.recipe_yeasts names its columns temp_min_f / temp_max_f, but the values
-- are a mix of Fahrenheit and Celsius -- US-05 is recorded as 12.0-25.0 "F",
-- which is plainly 12-25 °C. The rule applied here is ONE test, on the maximum:
--
--     temp_max_f <= 45  ->  the pair is already °C, use as written
--     temp_max_f >  45  ->  the pair is °F, convert (v - 32) * 5/9
--
-- Why 45 does not mangle a genuinely-Fahrenheit row. No brewing yeast has a
-- maximum fermentation temperature below 46 °F (7.8 °C); the coldest true
-- Fahrenheit row in the table is The Yeast Bay "Hessian Pils" at 45-48 °F, whose
-- MAX is 48 and which the rule therefore leaves in °F correctly. On the Celsius
-- side the largest max is 45 °C (Escarpment Labs Lactobacillus Blend, a souring
-- culture pitched warm). The values 46 and 47 never occur as a maximum at all --
-- the data's own distribution leaves a gap exactly where the rule cuts.
--
-- Cross-checked against an independent test: measured over all 1,745 rows, ZERO
-- rows are called Fahrenheit by this rule while carrying a minimum <= 30, and
-- zero rows are called Celsius while carrying a Fahrenheit-shaped minimum that
-- the max rule did not already catch. The two tests never disagree in the
-- direction that would corrupt a real lager row.
--
-- 65 of the 1,745 rows survive neither test: 35 have a minimum ABOVE the maximum
-- after repair (e.g. "65.0 to 8.0" -- a Fahrenheit minimum beside a Celsius
-- maximum) and 30 more record min = max, which is not a range. Those are not
-- repaired, they are DROPPED: attrs carries no temperature at all for them, and
-- temp_source records why. None of them is popular enough to be selected below
-- (0 of the 120 rows loaded lost its temperature), but the guard is in the query
-- so it stays true if the corpus is reloaded.
--
-- =============================================================================
-- 4. How the ~120 strains were picked -- reproducible, not hand-typed
-- =============================================================================
-- The whole selection is the query below; nothing is hand-listed. In order:
--
--   Quality gate  lab IS NOT NULL (drops the "- Wyeast Bohemian 2124" style
--                 orphan strings), name not starting with a dash, and
--                 attenuation between 50 and 95 (outside that band the figure
--                 is a typo, not a strain).
--
--   Family        derived from the name, with ONE physical arm. Order matters:
--                 sour/Brett -> wheat -> lager-by-name -> lager-by-temperature
--                 -> Belgian/saison -> ale. The temperature arm promotes a
--                 strain whose repaired maximum is <= 16 °C: no ale yeast
--                 attenuates there, and it is what correctly files Imperial's
--                 L-series -- L17 Harvest and L13 Global are the two it rescues
--                 here -- as lagers when their names carry no style word. It
--                 acts only on coherent
--                 temperatures and only where no name token already matched.
--                 ⚠️ It can mis-tag a deliberately cold-fermented ale -- Siebel
--                 "German Kölsch BRY 401" at 13-15 °C would be promoted -- but
--                 that strain is far below the selection cut (4 recipes).
--
--   Quota         top N per family by n_recipes. The quotas exist because a
--                 flat "top 120 by usage" list is overwhelmingly American ale
--                 strains, and §2 of the plan is explicit that "any style" is
--                 blocked on LAGERS and BELGIANS specifically. Coverage is the
--                 point of the quota, not tidiness.
--
-- ⚠️ Near-duplicate corpus strings are NOT merged. "Fermentis - Safbrew - Abbaye
-- Yeast" and "... Abbaye Yeast BE-256" are the same product and both land here.
-- The obvious fix -- collapse a name that is a prefix of a longer one from the
-- same lab -- is WRONG and was rejected on evidence: it also collapses Omega
-- "West Coast Ale I" into "West Coast Ale II/III/IV" and The Yeast Bay "Saison
-- Blend" into "Saison Blend II", which are different organisms. One duplicated
-- pair is a smaller error than four wrong merges.
--
-- =============================================================================
-- 5. Contract with brew.f_compute_recipe -- it cannot be affected
-- =============================================================================
-- f_compute_recipe (29_brew_formulate.sql) reads exactly two kinds:
-- WHERE i.kind IN ('fermentable','adjunct') for gravity and colour, and
-- WHERE i.kind = 'hop' for bitterness. kind = 'yeast' matches neither, and the
-- rows here set potential_ppg, color_lovibond and alpha_acid_pct to NULL
-- regardless. Adding them cannot move any existing recipe's OG/FG/IBU/SRM.
-- Attenuation still reaches the arithmetic the way it always has -- as
-- f_compute_recipe's p_attenuation argument, chosen by the caller -- which is
-- why this file changes what the caller can KNOW without changing what the
-- function DOES.
--
-- ⚠️ brew.f_catalogue does not return attenuation in any column. Yeast rows
-- surface there as name + supplier with the spec columns NULL. Extending it is
-- a change to 29_brew_formulate.sql and deliberately out of scope for this file.
--
-- Runs AFTER 27/28 and after 71_corpus_dims.sql has populated corpus.yeasts.
-- If the corpus is not loaded this file inserts nothing and does not fail.
-- Idempotent: brew.ingredients is UNIQUE (kind, name, supplier) and supplier is
-- never NULL here, so ON CONFLICT DO NOTHING is a real no-op on re-run.
-- =============================================================================

INSERT INTO brew.ingredients
  (kind, name, supplier, attenuation_min, attenuation_max, attrs)
SELECT
  'yeast',
  s.display_name,
  s.lab,
  s.attenuation_pct,          -- deliberately equal: a point, not a range
  s.attenuation_pct,
  jsonb_build_object(
    'provenance',       'corpus_selfreported',
    'provenance_note',  'Self-reported by homebrewers on a recipe-sharing site, '
                        'not a manufacturer datasheet. corpus.yeasts.attenuation_pct '
                        'is the mode across every recipe using the strain; the site '
                        'denormalises its own strain database onto each recipe, so '
                        'the mode is that database value. No source_doc exists, so '
                        'this must never be promoted into ref.* (71_corpus_dims.sql). '
                        'Open decision: RECIPE-PIPELINE-V2 §7 Q1 option (a).',
    'source_table',     'corpus.yeasts',
    'corpus_name_raw',  s.name_raw,
    'n_recipes',        s.n_recipes,
    'popularity_note',  'n_recipes counts how often brewers used this strain. '
                        'It is popularity, never quality or suitability.',
    'attenuation_pct',  s.attenuation_pct,
    'attenuation_range_discarded',
                        'corpus.yeasts.attenuation_min/max span 0.00-127.00 across '
                        'the table -- user-typed values, not a spec range. Discarded. '
                        'attenuation_min = attenuation_max here marks a point estimate.',
    'flocculation',     s.flocculation,
    'temp_c_min',       s.temp_c_min,
    'temp_c_max',       s.temp_c_max,
    'temp_source',      CASE
                          WHEN s.temp_c_min IS NULL THEN
                            'dropped: corpus min/max incoherent or absent after unit repair'
                          WHEN s.recorded_unit = 'C' THEN
                            'corpus values were already Celsius despite the _f column name'
                          ELSE
                            'converted from Fahrenheit, (v-32)*5/9'
                        END,
    'style_family',     s.family,
    'style_family_note','Derived from the strain name (plus a <=16 C fermentation-'
                        'maximum test for unnamed lagers) purely to guarantee style '
                        'coverage in this catalogue. It is a selection tag, not a '
                        'specification of what the strain may brew.')
FROM (
  SELECT DISTINCT ON (c.lab, c.display_name)
         c.*
  FROM (
   SELECT q.*
   FROM (
    SELECT r.*,
           row_number() OVER (PARTITION BY r.family
                              ORDER BY r.n_recipes DESC, r.name_raw) AS rn
    FROM (
      SELECT g.name_raw,
             g.lab,
             g.n_recipes,
             g.attenuation_pct,
             g.flocculation,
             g.recorded_unit,
             -- Incoherent pairs (a Fahrenheit minimum beside a Celsius maximum)
             -- are dropped rather than guessed at.
             CASE WHEN g.t_min_c < g.t_max_c THEN g.t_min_c END AS temp_c_min,
             CASE WHEN g.t_min_c < g.t_max_c THEN g.t_max_c END AS temp_c_max,
             -- The lab already prefixes the corpus string; supplier carries it,
             -- so the stored name does not repeat it.
             CASE WHEN g.name_raw LIKE g.lab || ' - %'
                  THEN btrim(substr(g.name_raw, length(g.lab) + 4))
                  ELSE g.name_raw END AS display_name,
             CASE
               WHEN g.name_key ~ '(brett|lacto|pedio|sour|lambic|roeselare|wild|funk|souring)'
                 THEN 'sour'
               WHEN g.name_key ~ '(weizen|wheat|hefe|weiss|wit |witbier|blanche)'
                 THEN 'wheat'
               WHEN g.name_key ~ '(lager|pils|bock|oktoberfest|marzen|märzen|helles|budvar|budejovice|urquell|steam|california common|vienna)'
                 THEN 'lager'
               WHEN g.t_min_c < g.t_max_c AND g.t_max_c <= 16
                 THEN 'lager'
               WHEN g.name_key ~ '(belgian|saison|abbey|abbaye|trappist|dubbel|tripel|ardennes|farmhouse|garde|monastery)'
                 THEN 'belgian'
               ELSE 'ale'
             END AS family
      FROM (
        SELECT y.name_raw, y.name_key, y.lab, y.n_recipes,
               y.attenuation_pct, y.flocculation,
               CASE WHEN y.temp_max_f <= 45 THEN 'C' ELSE 'F' END AS recorded_unit,
               CASE WHEN y.temp_max_f <= 45 THEN y.temp_min_f
                    ELSE round((y.temp_min_f - 32) * 5 / 9.0, 1) END AS t_min_c,
               CASE WHEN y.temp_max_f <= 45 THEN y.temp_max_f
                    ELSE round((y.temp_max_f - 32) * 5 / 9.0, 1) END AS t_max_c
        FROM corpus.yeasts y
        WHERE y.lab IS NOT NULL
          AND y.name_raw !~ '^\s*-'
          AND y.attenuation_pct BETWEEN 50 AND 95
      ) g
    ) r
   ) q
   WHERE q.rn <= CASE q.family
                   WHEN 'ale'     THEN 52
                   WHEN 'lager'   THEN 24
                   WHEN 'belgian' THEN 22
                   WHEN 'wheat'   THEN 12
                   ELSE 10                      -- sour / Brett
                 END
  ) c
  ORDER BY c.lab, c.display_name, c.n_recipes DESC
) s
ON CONFLICT (kind, name, supplier) DO NOTHING;
