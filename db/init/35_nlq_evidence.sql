-- =============================================================================
-- 35_nlq_evidence.sql  ·  The evidence layer (RECIPE-PIPELINE-V2 §3 Stage B/C)
--
-- Three functions the formulation pipeline asks for and nothing here answered:
--
--   nlq.ingredient_practice   C4 · how brewers actually USE one ingredient:
--                                  stage distribution + amount quantiles
--   nlq.find_exemplars        C3 · 2-3 whole corpus recipes, rendered compactly,
--                                  behind a plausibility gate that COUNTS what
--                                  it threw away
--   brew.f_resolve_request    B  · one verdict per term the brewer named:
--                                  catalogued / known_uncatalogued / thin / unknown
--
-- ⛔ THE CORPUS TELLS YOU WHAT IS POPULAR, NEVER WHAT IS GOOD. Every row these
-- functions return is 174,554 self-reported recipes agreeing with each other,
-- which is evidence of habit and nothing else. The caller MUST label it as
-- observed practice -- "what brewers commonly do" -- and never as what a book,
-- a guideline or a maltster asserts. Presenting a corpus figure as authority is
-- the same fabricated-authority failure `70_corpus.sql` refuses to vectorise
-- for, and `73_corpus_search.sql`'s rung discipline exists to prevent.
--
-- ⛔ NOTHING HERE GOES NEAR kb.*. `kb.chunks` is knowledge-only by table
-- comment; these are derived corpus counts, so they stay in SQL and are read at
-- prompt-build time. No embedding, no chunk, no document row.
--
-- ⛔ UNITS ARE NEVER CONVERTED -- 73_corpus_search.sql states the rule at the
-- top of the file and it is repeated here because C4 is where it bites hardest.
-- `measured` 2026-09-16: vanilla arrives as `each` (1,503 additions), `oz`
-- (453), `tsp` (215), `g` (170), `tbsp` (109), `ml` and `lb`. Those are beans,
-- extract and paste -- not one substance measured differently. A quartile over
-- the mixture would be a number about nothing, so every row here is keyed by
-- (stage, UNIT) and the units sit side by side.
--
-- SECURITY DEFINER + explicit `SET search_path` on every function, the hardening
-- 40_nlq.sql requires. No dynamic SQL anywhere.
--
-- ⚠️ THE 35_ IN THE NAME IS NOT ITS POSITION. db-init runs a hardcoded list in
-- docker-compose.yml, not a sorted glob (50_roles.sql runs LAST, after 74), and
-- this file must be appended to the END of that list. It needs
-- nlq.f_resolve_ingredient, nlq.f_cohort_ids, nlq.f_corpus_styles,
-- corpus.recipe_search and recipe_misc's generated amount_value / amount_unit
-- columns -- all of which arrive in 72_nlq_corpus.sql and 73_corpus_search.sql
-- -- plus brew.ingredients from 27_brew_catalogue.sql. Slotted by number it
-- would abort the whole run under ON_ERROR_STOP=1.
--
-- Idempotent: CREATE OR REPLACE throughout.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 'poppy seeds' -> the corpus wrote "Poppy Seed"
--
-- nlq.f_resolve_ingredient does the real work -- 'vanilla' -> 294 raw-string
-- variants including "vanilla bean in rum" -- and it is reused verbatim rather
-- than re-derived. This wrapper adds exactly one thing: a singular retry.
--
-- ⚠️ Why it is needed rather than tidy. `measured` 2026-09-16:
-- f_resolve_ingredient('poppy seeds') returns NOTHING, while
-- f_resolve_ingredient('poppy seed') returns 1 variant -- the substring sweep is
-- LIKE '%term%', so a plural the brewer typed cannot match a singular the
-- corpus wrote. RECIPE-PIPELINE-V2 §1.2 uses "poppy seed" as its worked example
-- of the `thin` verdict; without this, the brewer's own phrasing would have
-- scored `unknown` and been routed to "we have nothing" instead of to the web.
-- The retry only fires when the exact term found nothing, so it can never
-- broaden a term that already matched.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.f_resolve_ingredient_loose(p_term text)
RETURNS text[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = nlq, corpus, public AS $fn$
  SELECT CASE
           WHEN coalesce(array_length(k.exact, 1), 0) > 0 THEN k.exact
           WHEN lower(btrim(coalesce(p_term, ''))) LIKE '%s'
             THEN nlq.f_resolve_ingredient(left(btrim(p_term), -1))
           ELSE k.exact
         END
  FROM (SELECT nlq.f_resolve_ingredient(p_term) AS exact) k
$fn$;

-- ---------------------------------------------------------------------------
-- C4 · nlq.ingredient_practice  ·  how brewers actually use ONE ingredient
--
-- RECIPE-PIPELINE-V2 §3 Stage C4. The pipeline could already ask "what goes in
-- a sweet stout" (nlq.common_practice) and "what does this cohort agree on"
-- (nlq.cohort_stats). What it could not ask is the question that started the
-- whole investigation: the brewer said "vanilla", so WHEN is it added and HOW
-- MUCH. That is a different shape of answer -- a stage distribution, not a
-- cohort quartile -- and it is answered from all 2,484 vanilla recipes rather
-- than from the cohort, for the same reason nlq.ingredient_usage is not cohort
-- filtered: when the cohort has no vanilla stouts, this must still answer.
--
-- One row per (term, stage, unit). `measured` 2026-09-16 for 'vanilla':
--   Secondary each 1058 · 56% · p25 1.00 p50 2.00 p75 3.00
--   Boil      each  162 · 16% · p25 1.00 p50 1.00 p75 2.00
-- which reproduces §3 Stage C4's worked example exactly.
--
-- ⚠️ pct_at_stage IS THE STAGE'S SHARE, AND IT REPEATS ACROSS THE UNIT ROWS.
-- "Secondary 56%" is 1,509 of 2,671 vanilla additions -- a fact about WHEN,
-- which is not divisible by unit without becoming a different, weaker claim
-- ("40% of vanilla additions are Secondary-in-beans"). The brewer's question is
-- when to add it; the unit belongs to the amount, so the amount is where the
-- unit splits. Both numbers are on the row, and n_additions is the honest
-- denominator for the quantiles beside it.
--
-- ⛔ QUARTILES, NEVER A LONE MEDIAN -- 73_corpus_search.sql's rule. Vanilla in
-- grams runs p25 2.00 / p50 5.00 / p75 15.00: the median alone would hide that
-- this is a to-taste ingredient, which is the single most useful thing the
-- spread says.
--
-- ⚠️ THE RESOLVER IS A SUBSTRING SWEEP, AND FOR A SHORT TERM IT OVER-MATCHES.
-- nlq.f_resolve_ingredient is LIKE '%term%', so 'rum' also collects
-- `lactobacillus plantarum`, `graham cracker crumbs`, `coriandrum` and
-- `brumalt`. `measured` 2026-09-16: 27 of 164 rum additions are not rum, and
-- they move the headline from Secondary 72% to Secondary 62%. It is NOT
-- filtered here on purpose -- this function must select the same recipes as
-- nlq.find_cohort and nlq.cohort_stats, which call the same resolver, or the
-- practice block and the cohort block on one sheet would be computed over
-- different populations, which is a subtler and worse fault than an over-broad
-- match. The fix belongs in f_resolve_ingredient itself (a word-boundary
-- regexp beside the LIKE), in 73_corpus_search.sql, where every caller gets it
-- at once. Long terms are unaffected: 'vanilla' over-matches 1 variant of 294.
--
-- A (stage, unit) cell below 5 additions is dropped rather than reported. That
-- is the same floor nlq.cohort_stats and nlq.ingredient_usage already use, and
-- `measured` 2026-09-16 it is where a quartile starts to mean something: of the
-- 11,860 misc terms used by 1-5 recipes, 0.4% produce any cell of 5+.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.ingredient_practice(
  p_term  text,
  p_style text DEFAULT NULL,   -- optional: restrict to one style's recipes
  p_top   int  DEFAULT 6
) RETURNS TABLE (
  term          text,
  stage         text,
  pct_at_stage  numeric,
  unit          text,
  n_additions   int,
  n_recipes     int,
  p25           numeric,
  p50           numeric,
  p75           numeric,
  typical       text
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, nlq, public AS $fn$
  -- ⛔ MATERIALIZED IS LOAD-BEARING, for the reason nlq.ingredient_usage spells
  -- out: inlined, the planner re-evaluates the resolve once PER ROW of
  -- recipe_misc -- 141,857 rows x four substring sweeps over 33k dimension rows.
  WITH k AS MATERIALIZED (
    SELECT unnest(nlq.f_resolve_ingredient_loose(p_term)) AS name_key
  ),
  -- NULL when no style was asked for, which is the common case and must not
  -- filter anything. MATERIALIZED for the same reason as above.
  st AS MATERIALIZED (
    SELECT style_raw FROM nlq.f_corpus_styles(p_style)
    WHERE length(btrim(coalesce(p_style, ''))) >= 2
  ),
  hits AS (
    SELECT m.recipe_id, m.use_raw AS stage, m.amount_unit AS un, m.amount_value AS val
    FROM k
    JOIN corpus.recipe_misc m ON m.name_key = k.name_key   -- corpus_misc_key_idx
    WHERE m.amount_value IS NOT NULL
      AND m.amount_unit  IS NOT NULL
      AND m.use_raw      IS NOT NULL
      AND (length(btrim(coalesce(p_style, ''))) < 2
           OR EXISTS (SELECT 1 FROM corpus.recipes c JOIN st ON st.style_raw = c.style_raw
                      WHERE c.id = m.recipe_id))
  ),
  tot AS (SELECT count(*)::numeric n FROM hits),
  by_stage AS (SELECT stage, count(*)::numeric n FROM hits GROUP BY 1),
  agg AS (
    SELECT h.stage, h.un, count(*)::int adds, count(DISTINCT h.recipe_id)::int recs,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY h.val)::numeric q1,
           percentile_cont(0.50) WITHIN GROUP (ORDER BY h.val)::numeric q2,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY h.val)::numeric q3
    FROM hits h GROUP BY 1, 2 HAVING count(*) >= 5
  )
  SELECT btrim(p_term), a.stage,
         round(100.0 * s.n / nullif((SELECT n FROM tot), 0), 0),
         a.un, a.adds, a.recs,
         round(a.q1, 2), round(a.q2, 2), round(a.q3, 2),
         -- Rendered, for the reason 72_nlq_corpus.sql renders everything: a
         -- 12B model cannot misread a unit that is spelled out, and a wide
         -- spread has to READ as wide or it is taken for a target.
         CASE WHEN a.q3 > 0 AND a.q3 / nullif(a.q1, 0) >= 3
                THEN 'varies widely: ' || round(a.q2, 2) || ' ' || a.un ||
                     ' typical, but ' || round(a.q1, 2) || '-' || round(a.q3, 2) || ' is common'
              ELSE round(a.q2, 2) || ' ' || a.un ||
                   ' (usual range ' || round(a.q1, 2) || '-' || round(a.q3, 2) || ')'
         END
  FROM agg a JOIN by_stage s ON s.stage = a.stage
  ORDER BY a.adds DESC
  LIMIT greatest(p_top, 1)
$fn$;

COMMENT ON FUNCTION nlq.ingredient_practice(text, text, int) IS
  'How brewers actually use one ingredient: stage distribution and amount '
  'quantiles, one row per (stage, unit). Units are NEVER converted -- beans, '
  'oz and tsp sit side by side. Observed practice from self-reported recipes, '
  'NOT published guidance: an answer must attribute it as "what brewers '
  'commonly do", never as what a book or guideline says.';

-- ---------------------------------------------------------------------------
-- C3 · nlq.find_exemplars  ·  2-3 whole recipes the cohort actually contains
--
-- RECIPE-PIPELINE-V2 §3 Stage C3. Quartiles say what a cohort agrees on; they
-- never say what one coherent beer looks like. This returns whole recipes,
-- rendered as one compact block each (~250 tokens: grain bill with
-- percentages, hops with times, yeast, misc with stages), so three fit in 750.
--
-- ⛔ THE PLAUSIBILITY GATE IS THE POINT, NOT A TIDY-UP. The corpus is
-- self-reported and unvalidated. `measured` 2026-09-16, recipe 280784 "Solin
-- Stout" is a genuine 9.34% vanilla-lactose sweet stout -- exactly the beer a
-- cohort search is looking for -- and it records IBU 0.00 alongside 28 g of
-- Columbus and 28 g of Chinook both at "Boil, 0 min". Handed to the model as an
-- exemplar, that is an instruction to brew a stout with no bitterness.
-- Three rules, all of them arithmetic the recipe contradicts on its own terms:
--   1  zero or missing IBU while boil hops are present   <- catches 280784
--   2  OG/FG implying apparent attenuation outside 40-95%
--   3  a grain bill whose percentages do not sum to ~100 (95-105)
--
-- ⭐ THE REJECTION COUNT IS RETURNED, NOT SWALLOWED. "3 of 47 matches were
-- discarded as implausible" tells the brewer how noisy the evidence under this
-- sheet is. Silently dropping them would present a filtered corpus as a clean
-- one, which is the same overclaim as presenting a relaxed rung as an exact
-- match. n_considered / n_rejected / gate_note repeat on every row so any
-- caller that renders one row can still print them.
--
-- ⚠️ ORDERED BY COMPLETENESS, DELIBERATELY NOT BY RATING. corpus.recipes
-- carries `rating` and `views`, and ordering by either would be this file
-- asserting which self-reported recipe is GOOD -- the one thing the corpus
-- cannot tell anyone. Most-fully-specified, then lowest id, is honest and
-- deterministic.
--
-- The cohort, the rung and the rung_label come from nlq.f_cohort_ids
-- unchanged, so an exemplar can never be more specific than the rung it was
-- drawn from -- ⛔ at rung 4 the requested ingredients are NOT in these
-- recipes, and the label says so. The caller must print it.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.find_exemplars(
  p_style       text,
  p_ingredients text[] DEFAULT '{}',
  p_abv_min     numeric DEFAULT NULL,
  p_abv_max     numeric DEFAULT NULL,
  p_ibu_min     numeric DEFAULT NULL,
  p_ibu_max     numeric DEFAULT NULL,
  p_min_recipes int     DEFAULT 30,
  p_limit       int     DEFAULT 3
) RETURNS TABLE (
  recipe_id    bigint,
  rung         int,
  rung_label   text,
  n_considered int,
  n_rejected   int,
  gate_note    text,
  exemplar     text
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, nlq, public AS $fn$
  WITH c AS MATERIALIZED (
    SELECT * FROM nlq.f_cohort_ids(p_style, p_ingredients,
                  p_abv_min, p_abv_max, p_ibu_min, p_ibu_max, p_min_recipes)
  ),
  -- The same 5-100 L sanity filter nlq.find_cohort and nlq.cohort_stats apply.
  -- It selects what is CONSIDERED; it is not one of the three gate rules, so a
  -- 400 L commercial pilot batch is not counted as "discarded as implausible".
  cand AS (
    SELECT s.* FROM corpus.recipe_search s JOIN c ON c.recipe_id = s.recipe_id
    WHERE s.batch_l BETWEEN 5 AND 100
  ),
  -- ⚠️ CORRELATED SUBQUERIES, AND THEY ARE THE FAST SHAPE HERE. The gate has to
  -- see the WHOLE cohort or the rejection count is a lie, and a cohort is
  -- routinely large -- `measured` 2026-09-16, 'American IPA' + citra is 9,340
  -- recipes. Rewritten as grouped joins over corpus.recipe_hops (621k rows) and
  -- recipe_fermentables (675k), the planner hash-joins the whole fact table and
  -- that same call went from 907 ms to 1,014 ms. Per-candidate index lookups on
  -- corpus_hops_recipe_idx / corpus_ferm_recipe_idx win; the shape was measured,
  -- not assumed.
  facts AS (
    SELECT d.recipe_id,
           d.og, d.fg, d.ibu,
           (SELECT count(*) FROM corpus.recipe_hops h
             WHERE h.recipe_id = d.recipe_id AND h.use = 'Boil'
               AND coalesce(h.amount_g, 0) > 0)             AS boil_hops,
           (SELECT sum(f.pct_bill) FROM corpus.recipe_fermentables f
             WHERE f.recipe_id = d.recipe_id)               AS bill_pct,
           (SELECT count(*) FROM corpus.recipe_fermentables f
             WHERE f.recipe_id = d.recipe_id)               AS n_ferm,
           (SELECT count(*) FROM corpus.recipe_hops h
             WHERE h.recipe_id = d.recipe_id)               AS n_hops
    FROM cand d
  ),
  judged AS (
    SELECT f.*,
           -- Rule 1: bitterness the hop schedule contradicts.
           (coalesce(f.ibu, 0) <= 0 AND f.boil_hops > 0)                     AS bad_ibu,
           -- Rule 2: an OG/FG pair no yeast produces. Apparent attenuation
           -- (og - fg) / (og - 1); 40-95% brackets everything real, including
           -- Brettanomyces at the top and a stuck fermentation at the bottom.
           (f.og IS NULL OR f.fg IS NULL OR f.og <= 1.0
            OR (f.og - f.fg) / nullif(f.og - 1.0, 0) NOT BETWEEN 0.40 AND 0.95) AS bad_atten,
           -- Rule 3: a grain bill that is not a whole grain bill.
           (f.n_ferm = 0 OR f.bill_pct IS NULL
            OR f.bill_pct NOT BETWEEN 95 AND 105)                            AS bad_bill
    FROM facts f
  ),
  counts AS (
    SELECT count(*)::int considered,
           count(*) FILTER (WHERE bad_ibu OR bad_atten OR bad_bill)::int rejected
    FROM judged
  ),
  keep AS (
    SELECT j.recipe_id
    FROM judged j
    WHERE NOT (j.bad_ibu OR j.bad_atten OR j.bad_bill)
    -- ⚠️ THE MISC COUNT IS DELIBERATELY NOT IN THE ORDERING.
    -- `measured` 2026-09-16: ranking by total row count promoted three recipes
    -- whose bulk was water chemistry -- "Baking Soda - MASH ONLY 1.38 g",
    -- "CaCl2 - SPARGE ONLY 0.80 g" -- and pushed the vanilla addition, the one
    -- thing the brewer asked about, past the render cap. A meticulous salt
    -- schedule does not make a better exemplar of a recipe.
    ORDER BY (j.n_ferm + j.n_hops) DESC, j.recipe_id
    LIMIT greatest(p_limit, 1)
  )
  SELECT k.recipe_id,
         (SELECT min(rung) FROM c),
         (SELECT min(rung_label) FROM c),
         cnt.considered,
         cnt.rejected,
         cnt.rejected || ' of ' || cnt.considered ||
           ' matching recipes were discarded as implausible (zero IBU with boil hops, ' ||
           'impossible attenuation, or a grain bill that does not sum)' AS gate_note,
         -- The ~250-token render. Caps of 8 / 6 / 6 keep a 30-fermentable
         -- kitchen-sink recipe from eating the whole evidence budget.
         '#' || k.recipe_id || ' "' || coalesce(r.name, 'untitled') || '" · ' ||
         coalesce(r.style_raw, 'style not recorded') || ' · ' ||
         coalesce(r.method, 'method not recorded') || ' · ' ||
         round(r.batch_l, 1) || ' L · OG ' || to_char(r.og, 'FM0.000') ||
         ' FG ' || to_char(r.fg, 'FM0.000') || ' · ' || round(r.abv, 1) || '% ABV · ' ||
         round(r.ibu, 0) || ' IBU · ' || round(r.color_srm, 0) || ' SRM' ||
         coalesce(E'\ngrain: ' || (
            SELECT string_agg(x.t, ' · ' ORDER BY x.rn) FROM (
              SELECT row_number() OVER (ORDER BY f.pct_bill DESC NULLS LAST, f.position) rn,
                     f.name_raw || ' ' || round(f.pct_bill, 1) || '%' t
              FROM corpus.recipe_fermentables f WHERE f.recipe_id = k.recipe_id) x
            WHERE x.rn <= 8), '') ||
         coalesce(E'\nhops: ' || (
            SELECT string_agg(x.t, ' · ' ORDER BY x.rn) FROM (
              SELECT row_number() OVER (ORDER BY h.position) rn,
                     h.name_raw || ' ' || round(h.amount_g, 0) || ' g ' ||
                     coalesce(h.use, 'use not recorded') ||
                     coalesce(' ' || h.time_raw, '') t
              FROM corpus.recipe_hops h WHERE h.recipe_id = k.recipe_id) x
            WHERE x.rn <= 6), '') ||
         coalesce(E'\nyeast: ' || (
            SELECT string_agg(y.name_raw ||
                     coalesce(' (' || round(y.attenuation_pct, 0) || '% att)', ''), ' · ')
            FROM corpus.recipe_yeasts y WHERE y.recipe_id = k.recipe_id), '') ||
         coalesce(E'\nadditions: ' || (
            SELECT string_agg(x.t, ' · ' ORDER BY x.rn) FROM (
              -- Flavourings before water salts, for the same reason: the cap
              -- is 6, and "Vanilla Bean 2 each at secondary" is the row this
              -- whole function exists to show.
              SELECT row_number() OVER (
                       ORDER BY (m.type_raw IN ('Water Agt', 'Fining')), m.position) rn,
                     m.name_raw || ' ' || coalesce(m.amount_raw, 'amount not recorded') ||
                     ' at ' || lower(coalesce(m.use_raw, 'stage not recorded')) t
              FROM corpus.recipe_misc m WHERE m.recipe_id = k.recipe_id) x
            WHERE x.rn <= 6), '')
  FROM keep k
  JOIN corpus.recipes r ON r.id = k.recipe_id
  CROSS JOIN counts cnt
  ORDER BY k.recipe_id
$fn$;

COMMENT ON FUNCTION nlq.find_exemplars(text, text[], numeric, numeric, numeric, numeric, int, int) IS
  'Whole corpus recipes from a cohort, rendered compactly, behind a '
  'plausibility gate (zero IBU with boil hops / impossible attenuation / a '
  'grain bill that does not sum). n_rejected is part of the answer and must be '
  'shown. Observed practice from self-reported recipes, never authority; the '
  'rung_label says what was actually matched and must be printed with it.';

-- ---------------------------------------------------------------------------
-- B · brew.f_resolve_request  ·  one verdict per term the brewer named
--
-- RECIPE-PIPELINE-V2 §3 Stage B. This replaces a yes/no -- "is it in the
-- catalogue" -- that produced a wrong answer and a silent substitution, with a
-- four-way route where every branch has somewhere to go:
--
--   catalogued          a brew.ingredients row exists -> the id goes to D or E
--   known_uncatalogued  not in the catalogue, but >= 20 corpus recipes use it
--                       -> Stage E, with a corpus practice block (C4)
--   thin                in the corpus, below threshold -> Stage E, with a WEB
--                       technique block; the corpus cannot carry it
--   unknown             nothing anywhere -> tell the brewer BEFORE building
--
-- ⭐ THE THRESHOLD, AND THE EVIDENCE FOR IT. N = 20 corpus recipes.
-- `measured` 2026-09-16 over all 16,112 misc terms: the point of the verdict is
-- whether nlq.ingredient_practice can actually produce a practice block, which
-- needs at least one (stage, unit) cell of 5+ additions. The share of terms
-- that clear that bar, by how many recipes use the term:
--     1-5 recipes    0.4%      21-25    95.2%
--     6-10          47.1%      26-30   100.0%
--    11-15          74.2%      31+     100.0%
--    16-20          91.1%
-- 20 is where the curve has flattened: 91% of terms at that count have a usable
-- block, and the next bucket buys 4 points. Below it the answer would be a
-- verdict promising evidence that does not exist. The `thin` band is therefore
-- 1-19 recipes, which is where "poppy seed, n = 1" sits -- §1.2's worked
-- example, and the case that genuinely needs the web arm.
-- ⚠️ Both numbers are judgement calls on a curve, not a law. They are here, in
-- one place, so raising them is one edit and not an archaeology exercise.
--
-- The corpus count is taken from corpus.recipe_search.ingredients, which pools
-- fermentables, hops, yeasts AND miscs into one GIN-indexed array -- so a term
-- filed as a fermentable in some recipes and a misc in others (lactose is the
-- standing example) is counted once, correctly, rather than missed.
--
-- ⛔ A `catalogued` VERDICT IS NOT A CLAIM THAT THE CORPUS AGREES. The two
-- lookups are independent and both are reported: 'Weyermann Pale Ale Malt' is
-- catalogued and has 0 corpus recipes under that exact phrasing, and that is
-- not a contradiction -- it is a datasheet-backed row whose full name no
-- brewer types.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION brew.f_resolve_request(p_terms text[])
RETURNS TABLE (
  term              text,
  verdict           text,
  ingredient_id     bigint,
  ingredient_name   text,
  ingredient_kind   text,
  n_corpus_recipes  int,
  note              text
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = brew, corpus, nlq, public AS $fn$
  WITH t AS (
    SELECT btrim(x) AS term,
           -- Punctuation and ® stripped from BOTH sides, so "CARAFA® Type 1"
           -- and "carafa type 1" are the same string to the matcher.
           lower(btrim(regexp_replace(x, '[^a-zA-Z0-9]+', ' ', 'g'))) AS tn
    FROM unnest(coalesce(p_terms, '{}'::text[])) x
    WHERE length(btrim(coalesce(x, ''))) >= 2
  ),
  ing AS (
    SELECT i.id, i.kind, i.name, i.supplier,
           lower(btrim(regexp_replace(i.name, '[^a-zA-Z0-9]+', ' ', 'g'))) AS nn,
           lower(btrim(regexp_replace(coalesce(i.supplier, '') || ' ' || i.name,
                                      '[^a-zA-Z0-9]+', ' ', 'g'))) AS hay
    FROM brew.ingredients i
  ),
  hit AS (
    SELECT t.term, t.tn, m.id, m.kind, m.name
    FROM t
    LEFT JOIN LATERAL (
      SELECT i.id, i.kind, i.name FROM ing i
      -- Two directions, because the brewer's phrasing can be either longer than
      -- the catalogue name ('Weyermann Pale Ale Malt' -> 'Pale Ale Malt') or
      -- shorter ('lactose' -> 'Lactose (milk sugar)').
      WHERE t.tn LIKE '%' || i.nn || '%' OR i.hay LIKE '%' || t.tn || '%'
      -- Exact first; then the supplier-qualified form the brewer wrote, which
      -- is what separates Weyermann's 'Pale Ale Malt' from Viking's
      -- 'Pale Ale Malt Organic'; then the longest name, as the most specific.
      ORDER BY (i.hay = t.tn) DESC, (t.tn LIKE '%' || i.nn || '%') DESC,
               length(i.nn) DESC, i.id
      LIMIT 1
    ) m ON true
  ),
  corp AS (
    SELECT h.*,
           (SELECT count(*)::int FROM corpus.recipe_search s
             WHERE s.ingredients && nlq.f_resolve_ingredient_loose(h.term)) AS n
    FROM hit h
  )
  SELECT c.term,
         CASE WHEN c.id IS NOT NULL THEN 'catalogued'
              WHEN c.n >= 20        THEN 'known_uncatalogued'
              WHEN c.n >= 1         THEN 'thin'
              ELSE                       'unknown'
         END,
         c.id, c.name, c.kind, c.n,
         CASE WHEN c.id IS NOT NULL THEN
                'in the catalogue with published specs; ' || c.n ||
                ' corpus recipes also name it'
              WHEN c.n >= 20 THEN
                'not in the catalogue, but ' || c.n || ' brewers use it -- build '
                'the addition from observed practice (nlq.ingredient_practice) '
                'and label it as what brewers commonly do, not as guidance'
              WHEN c.n >= 1 THEN
                'only ' || c.n || ' corpus recipe(s) use it -- too thin to '
                'quantify; the technique has to come from the library or the web'
              ELSE
                'not in the catalogue and not in 174,554 corpus recipes -- say so '
                'to the brewer before building anything around it'
         END
  FROM corp c
  ORDER BY c.term
$fn$;

COMMENT ON FUNCTION brew.f_resolve_request(text[]) IS
  'One verdict per requested ingredient: catalogued / known_uncatalogued / '
  'thin / unknown, with the catalogue id where there is one and the corpus '
  'recipe count either way. The corpus half is observed practice, not '
  'authority -- a high count means popular, never good.';

-- ---------------------------------------------------------------------------
-- ⛔ GUARDED, for the reason 72_nlq_corpus.sql spells out: this file runs inside
-- the db-init loop and 50_roles.sql -- which creates agent_ro -- runs AFTER it.
-- On a fresh volume the role does not exist yet and a bare GRANT would abort the
-- whole migration under ON_ERROR_STOP=1.
--
-- mem_writer is the credential cap-formulate-recipe runs its SQL on, so it needs
-- all three: Stage B resolves the brief, C3/C4 build the evidence pack.
-- agent_ro is the chat agent, which gets the two read-only corpus functions.
-- Same contract as everywhere else here: EXECUTE on the SECURITY DEFINER
-- function, never SELECT on corpus.* or brew.* underneath it.
-- ---------------------------------------------------------------------------
DO $grant$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mem_writer') THEN
    GRANT USAGE ON SCHEMA nlq TO mem_writer;
    GRANT EXECUTE ON FUNCTION nlq.f_resolve_ingredient_loose(text) TO mem_writer;
    GRANT EXECUTE ON FUNCTION nlq.ingredient_practice(text, text, int) TO mem_writer;
    GRANT EXECUTE ON FUNCTION nlq.find_exemplars(text, text[], numeric, numeric, numeric, numeric, int, int) TO mem_writer;
    GRANT EXECUTE ON FUNCTION brew.f_resolve_request(text[]) TO mem_writer;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'agent_ro') THEN
    GRANT EXECUTE ON FUNCTION nlq.f_resolve_ingredient_loose(text) TO agent_ro;
    GRANT EXECUTE ON FUNCTION nlq.ingredient_practice(text, text, int) TO agent_ro;
    GRANT EXECUTE ON FUNCTION nlq.find_exemplars(text, text[], numeric, numeric, numeric, numeric, int, int) TO agent_ro;
  END IF;
END $grant$;
