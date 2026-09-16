-- =============================================================================
-- 73_corpus_search.sql  ·  Finding the right recipes, and what they agree on
--
-- The formulation pipeline asks a question the dimension tables cannot answer:
-- "show me sweet stouts with vanilla and lactose under 7% ABV". That is an
-- arbitrary combination of style x ingredients x parameters, so it cannot be
-- pre-aggregated the way a fixed style page can -- the cells are combinatorial.
-- `measured`: selecting a cohort live costs ~200 ms, so it is computed per call.
--
-- Three pieces:
--   corpus.recipe_search   one GIN-indexed row per recipe: the search index
--   nlq.find_cohort        which recipes match, and WHICH RUNG it settled for
--   nlq.cohort_stats       what that cohort agrees on, as quartiles
--   nlq.ingredient_usage   how one ingredient is used everywhere, style by style
--
-- ⛔ THE RUNG IS PART OF THE ANSWER, NOT DIAGNOSTICS. A search for "vanilla
-- stout" that finds nothing and relaxes to "sweet stout" returns numbers about
-- beers WITHOUT vanilla. Presenting those as vanilla-stout practice is the same
-- fabricated-authority failure as labelling a corpus figure [S..]. Every
-- function here returns what it actually matched, and the caller must say so.
--
-- ⛔ QUARTILES, NOT MEANS, AND NEVER A LONE MEDIAN. Vanilla runs a 10x spread
-- across recipes: a median alone tells the pipeline nothing about whether an
-- amount is specified or to-taste. p25/p50/p75 says which it is.
--
-- Runs AFTER 72_nlq_corpus.sql. Idempotent.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- '2 each' -> (2, 'each');  '0.50 tsp' -> (0.5, 'tsp');  'a pinch' -> (NULL, ...)
-- Misc amounts are free text and the units do not reconcile: vanilla arrives as
-- `each` (beans), `oz`, `tsp` (extract), `g`, `tbsp`, `ml` and `lb`. Those are
-- not the same substance measured differently, so they are NEVER converted into
-- one scale -- they are reported side by side, per unit. A quartile over the
-- mixture would be a number about nothing.
-- ---------------------------------------------------------------------------
-- (corpus.f_parse_amount, a set-returning version of the two scalars below,
--  lived here until the parse moved into STORED generated columns. It had no
--  callers left and is dropped at the end of this file.)

-- Scalar and IMMUTABLE, so the parse can be a
-- STORED generated column instead of a per-row LATERAL call. 141,857 misc rows
-- were being re-parsed on every query that touched them.
CREATE OR REPLACE FUNCTION corpus.f_amount_value(p_raw text) RETURNS numeric
LANGUAGE sql IMMUTABLE SET search_path = corpus, public AS $fn$
  SELECT CASE WHEN m[1] ~ '^[0-9]+(\.[0-9]+)?$' THEN m[1]::numeric END
  FROM regexp_match(btrim(coalesce(p_raw, '')), '^([0-9]+(?:\.[0-9]+)?)\s*(.*)$') AS m
$fn$;

CREATE OR REPLACE FUNCTION corpus.f_amount_unit(p_raw text) RETURNS text
LANGUAGE sql IMMUTABLE SET search_path = corpus, public AS $fn$
  SELECT nullif(lower(btrim(m[2])), '')
  FROM regexp_match(btrim(coalesce(p_raw, '')), '^([0-9]+(?:\.[0-9]+)?)\s*(.*)$') AS m
$fn$;

-- name_key on the FACT tables, matching the dimensions'. Without it every
-- ingredient lookup computes lower(btrim(regexp_replace(...))) per row and can
-- never use an index.
ALTER TABLE corpus.recipe_misc
  ADD COLUMN IF NOT EXISTS name_key text
    GENERATED ALWAYS AS (lower(btrim(regexp_replace(name_raw, '\s+', ' ', 'g')))) STORED,
  ADD COLUMN IF NOT EXISTS amount_value numeric
    GENERATED ALWAYS AS (corpus.f_amount_value(amount_raw)) STORED,
  ADD COLUMN IF NOT EXISTS amount_unit text
    GENERATED ALWAYS AS (corpus.f_amount_unit(amount_raw)) STORED;

ALTER TABLE corpus.recipe_fermentables
  ADD COLUMN IF NOT EXISTS name_key text
    GENERATED ALWAYS AS (lower(btrim(regexp_replace(name_raw, '\s+', ' ', 'g')))) STORED;
ALTER TABLE corpus.recipe_hops
  ADD COLUMN IF NOT EXISTS name_key text
    GENERATED ALWAYS AS (lower(btrim(regexp_replace(name_raw, '\s+', ' ', 'g')))) STORED;

CREATE INDEX IF NOT EXISTS corpus_misc_key_idx ON corpus.recipe_misc (name_key);
CREATE INDEX IF NOT EXISTS corpus_ferm_key_idx ON corpus.recipe_fermentables (name_key);
CREATE INDEX IF NOT EXISTS corpus_hops_key_idx ON corpus.recipe_hops (name_key);

-- ---------------------------------------------------------------------------
-- The search index. One row per recipe; `ingredients` is every ingredient the
-- recipe names, from all four fact tables, as dimension name_keys.
--
-- All four are pooled into ONE array on purpose: lactose is filed as a
-- fermentable in some recipes and a misc in others, so a caller searching only
-- one kind silently loses matches. The brewer asking for "vanilla and lactose"
-- does not know or care which table they landed in.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus.recipe_search (
  recipe_id   bigint PRIMARY KEY REFERENCES corpus.recipes(id) ON DELETE CASCADE,
  style_raw   text,
  style_key   text,
  method      text,
  abv         numeric,
  ibu         numeric,
  og          numeric,
  fg          numeric,
  color_srm   numeric,
  batch_l     numeric,
  ingredients text[] NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS corpus_search_ing_idx   ON corpus.recipe_search USING gin (ingredients);
CREATE INDEX IF NOT EXISTS corpus_search_style_idx ON corpus.recipe_search USING gin (style_key gin_trgm_ops);
CREATE INDEX IF NOT EXISTS corpus_search_abv_idx   ON corpus.recipe_search (abv);

COMMENT ON TABLE corpus.recipe_search IS
  'Search index over corpus.*, not a second copy of it: one GIN-indexed row per '
  'recipe so an arbitrary style + ingredients + parameters cohort is one query. '
  'Rebuilt by corpus.f_rebuild_search(); the fact tables remain authoritative.';

CREATE OR REPLACE FUNCTION corpus.f_rebuild_search()
RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = corpus, public AS $fn$
DECLARE n bigint;
BEGIN
  TRUNCATE corpus.recipe_search;
  INSERT INTO corpus.recipe_search
    (recipe_id, style_raw, style_key, method, abv, ibu, og, fg, color_srm, batch_l, ingredients)
  SELECT r.id, r.style_raw, lower(coalesce(r.style_raw, '')), r.method,
         r.abv, r.ibu, r.og, r.fg, r.color_srm, r.batch_l,
         coalesce((
           SELECT array_agg(DISTINCT k) FROM (
             SELECT lower(btrim(regexp_replace(f.name_raw, '\s+', ' ', 'g'))) AS k
               FROM corpus.recipe_fermentables f WHERE f.recipe_id = r.id
             UNION SELECT lower(btrim(regexp_replace(h.name_raw, '\s+', ' ', 'g')))
               FROM corpus.recipe_hops h WHERE h.recipe_id = r.id
             UNION SELECT lower(btrim(regexp_replace(y.name_raw, '\s+', ' ', 'g')))
               FROM corpus.recipe_yeasts y WHERE y.recipe_id = r.id
             UNION SELECT lower(btrim(regexp_replace(m.name_raw, '\s+', ' ', 'g')))
               FROM corpus.recipe_misc m WHERE m.recipe_id = r.id
           ) u), '{}')
  FROM corpus.recipes r;
  GET DIAGNOSTICS n = ROW_COUNT;
  ANALYZE corpus.recipe_search;
  RETURN n;
END $fn$;

-- ---------------------------------------------------------------------------
-- 'vanilla' -> {vanilla, vanilla bean, vanilla beans, vanilla extract, ...}
--
-- The alias problem, handled at read time instead of waiting for curation. The
-- dimensions are small (16k miscs is the largest), so a substring sweep across
-- all four costs nothing, and it is why a search for "vanilla" does not miss the
-- 451 recipes that wrote "Vanilla Bean".
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.f_resolve_ingredient(p_term text)
RETURNS text[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, public AS $fn$
  SELECT coalesce(array_agg(DISTINCT name_key), '{}')
  FROM (
    SELECT name_key FROM corpus.fermentables WHERE name_key LIKE '%' || lower(btrim(p_term)) || '%'
    UNION ALL SELECT name_key FROM corpus.hops   WHERE name_key LIKE '%' || lower(btrim(p_term)) || '%'
    UNION ALL SELECT name_key FROM corpus.yeasts WHERE name_key LIKE '%' || lower(btrim(p_term)) || '%'
    UNION ALL SELECT name_key FROM corpus.miscs  WHERE name_key LIKE '%' || lower(btrim(p_term)) || '%'
  ) x
  WHERE length(btrim(coalesce(p_term, ''))) >= 2
$fn$;

-- ---------------------------------------------------------------------------
-- nlq.f_cohort_ids  ·  the relaxation ladder
--
-- Five rungs, widest constraint first, stopping at the first that clears
-- p_min_recipes. The rung travels WITH the ids because it changes what the
-- numbers mean:
--   1  style + every ingredient + parameters
--   2  style + every ingredient          (parameters dropped)
--   3  style + the RAREST ingredient     (the defining one is kept: in
--                                         "sweet stout, vanilla, lactose" that
--                                         is vanilla, not lactose)
--   4  style alone                       ⚠️ NO ingredient is present any more
--   5  style broadened to its head noun  ⚠️ a different beer
--
-- ⛔ No dynamic SQL -- 40_nlq.sql's rule for every SECURITY DEFINER function
-- here. The rungs are five static queries, not one assembled string.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.f_cohort_ids(
  p_style       text,
  p_ingredients text[] DEFAULT '{}',
  p_abv_min     numeric DEFAULT NULL,
  p_abv_max     numeric DEFAULT NULL,
  p_ibu_min     numeric DEFAULT NULL,
  p_ibu_max     numeric DEFAULT NULL,
  p_min_recipes int     DEFAULT 30
) RETURNS TABLE (recipe_id bigint, rung int, rung_label text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, nlq, public AS $fn$
  WITH w AS (
    SELECT array_remove(regexp_split_to_array(
             regexp_replace(lower(btrim(coalesce(p_style, ''))), '[^a-z0-9]+', ' ', 'g'),
             ' '), '') AS words
  ),
  h AS (SELECT words, words[array_length(words, 1)] AS head FROM w),
  terms AS (
    SELECT t AS term, nlq.f_resolve_ingredient(t) AS keys
    FROM unnest(coalesce(p_ingredients, '{}'::text[])) t
    WHERE length(btrim(t)) >= 2
  ),
  broad AS (
    SELECT s.recipe_id, s.ingredients, s.abv, s.ibu
    FROM corpus.recipe_search s, h
    WHERE h.head IS NOT NULL AND h.head <> 'beer'
      AND s.style_key LIKE '%' || h.head || '%'
  ),
  narrow AS (
    SELECT b.* FROM broad b, h
    WHERE NOT EXISTS (
      SELECT 1 FROM unnest(h.words) x
      WHERE length(x) >= 3
        AND (SELECT s.style_key FROM corpus.recipe_search s WHERE s.recipe_id = b.recipe_id)
            NOT LIKE '%' || x || '%')
  ),
  -- How selective is each term inside the narrow style set? The rarest one is
  -- the defining ingredient -- in "sweet stout, vanilla, lactose" that is
  -- vanilla -- so it is the one rung 3 keeps.
  term_hits AS (
    SELECT t.term, t.keys,
           (SELECT count(*) FROM narrow n WHERE n.ingredients && t.keys) AS hits
    FROM terms t
  ),
  rarest AS (SELECT term, keys FROM term_hits ORDER BY hits ASC NULLS LAST LIMIT 1),

  r1 AS (SELECT n.recipe_id, 1 AS rung FROM narrow n
         WHERE NOT EXISTS (SELECT 1 FROM terms t WHERE NOT (n.ingredients && t.keys))
           AND (p_abv_min IS NULL OR n.abv >= p_abv_min)
           AND (p_abv_max IS NULL OR n.abv <= p_abv_max)
           AND (p_ibu_min IS NULL OR n.ibu >= p_ibu_min)
           AND (p_ibu_max IS NULL OR n.ibu <= p_ibu_max)),
  r2 AS (SELECT n.recipe_id, 2 FROM narrow n
         WHERE NOT EXISTS (SELECT 1 FROM terms t WHERE NOT (n.ingredients && t.keys))),
  r3 AS (SELECT n.recipe_id, 3 FROM narrow n
         WHERE (SELECT count(*) FROM terms) > 1
           AND n.ingredients && (SELECT keys FROM rarest)),
  r4 AS (SELECT n.recipe_id, 4 FROM narrow n WHERE (SELECT count(*) FROM terms) >= 1),
  r5 AS (SELECT b.recipe_id, 5 FROM broad b),

  all_rungs AS (SELECT * FROM r1 UNION ALL SELECT * FROM r2 UNION ALL SELECT * FROM r3
                UNION ALL SELECT * FROM r4 UNION ALL SELECT * FROM r5),
  -- The tightest rung that still has enough recipes to mean anything.
  pick AS (SELECT min(rung) AS rung FROM (
             SELECT rung, count(*) c FROM all_rungs GROUP BY rung) z
           WHERE z.c >= p_min_recipes)

  SELECT a.recipe_id, a.rung,
         CASE a.rung
           WHEN 1 THEN 'exact: style, every ingredient, and the stated parameters'
           WHEN 2 THEN 'relaxed: ABV/IBU limits dropped; style and every ingredient still match'
           WHEN 3 THEN 'relaxed: kept only "' || (SELECT term FROM rarest) ||
                       '" -- the other requested ingredients are NOT in these recipes'
           WHEN 4 THEN 'relaxed: style only -- NONE of the requested ingredients is in these recipes'
           ELSE        'relaxed: widened to every "' || (SELECT head FROM h) ||
                       '" -- not the style asked for, and no requested ingredient'
         END
  FROM all_rungs a, pick WHERE a.rung = pick.rung
$fn$;

-- ---------------------------------------------------------------------------
-- 1) nlq.find_cohort  ·  what matched, and how honestly
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.find_cohort(
  p_style text, p_ingredients text[] DEFAULT '{}',
  p_abv_min numeric DEFAULT NULL, p_abv_max numeric DEFAULT NULL,
  p_ibu_min numeric DEFAULT NULL, p_ibu_max numeric DEFAULT NULL,
  p_min_recipes int DEFAULT 30
) RETURNS TABLE (
  rung int, rung_label text, n_recipes int,
  og numeric, fg numeric, abv numeric, ibu numeric, color_srm numeric
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, nlq, public AS $fn$
  WITH c AS (SELECT * FROM nlq.f_cohort_ids(p_style, p_ingredients,
                        p_abv_min, p_abv_max, p_ibu_min, p_ibu_max, p_min_recipes)),
  s AS (SELECT r.* FROM corpus.recipe_search r JOIN c ON c.recipe_id = r.recipe_id
        WHERE r.batch_l BETWEEN 5 AND 100)
  SELECT (SELECT min(rung) FROM c), (SELECT min(rung_label) FROM c), count(*)::int,
         round(percentile_cont(0.5) WITHIN GROUP (ORDER BY s.og)  FILTER (WHERE s.og  BETWEEN 1.0 AND 1.2)::numeric, 3),
         round(percentile_cont(0.5) WITHIN GROUP (ORDER BY s.fg)  FILTER (WHERE s.fg  BETWEEN 0.98 AND 1.1)::numeric, 3),
         round(percentile_cont(0.5) WITHIN GROUP (ORDER BY s.abv) FILTER (WHERE s.abv BETWEEN 0 AND 20)::numeric, 1),
         round(percentile_cont(0.5) WITHIN GROUP (ORDER BY s.ibu) FILTER (WHERE s.ibu BETWEEN 0 AND 150)::numeric, 0),
         round(percentile_cont(0.5) WITHIN GROUP (ORDER BY s.color_srm) FILTER (WHERE s.color_srm BETWEEN 0 AND 80)::numeric, 1)
  FROM s HAVING count(*) > 0
$fn$;

-- ---------------------------------------------------------------------------
-- 2) nlq.cohort_stats  ·  what the cohort agrees on, as quartiles
--
-- p25/p50/p75, never a lone median: the spread is what says whether an amount
-- is specified or to-taste. Misc is grouped BY UNIT, because `each` (beans),
-- `tsp` (extract) and `g` are different substances and a quartile across them
-- would be a number about nothing.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.cohort_stats(
  p_style text, p_ingredients text[] DEFAULT '{}',
  p_abv_min numeric DEFAULT NULL, p_abv_max numeric DEFAULT NULL,
  p_ibu_min numeric DEFAULT NULL, p_ibu_max numeric DEFAULT NULL,
  p_min_recipes int DEFAULT 30, p_top int DEFAULT 8
) RETURNS TABLE (
  section text, item text, n_recipes int, pct_of_cohort numeric,
  unit text, p25 numeric, p50 numeric, p75 numeric, typical text
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, nlq, public AS $fn$
  WITH c AS (SELECT recipe_id FROM nlq.f_cohort_ids(p_style, p_ingredients,
                     p_abv_min, p_abv_max, p_ibu_min, p_ibu_max, p_min_recipes)),
  r AS (SELECT s.recipe_id, s.batch_l FROM corpus.recipe_search s JOIN c ON c.recipe_id = s.recipe_id
        WHERE s.batch_l BETWEEN 5 AND 100),
  n AS (SELECT count(*)::numeric total FROM r),

  grain AS (
    SELECT 1 ord, row_number() OVER (ORDER BY count(DISTINCT f.recipe_id) DESC) rn,
           'grain bill'::text sec, f.name_raw it, count(DISTINCT f.recipe_id)::int cnt,
           '% of grist'::text un,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY f.pct_bill)::numeric q1,
           percentile_cont(0.50) WITHIN GROUP (ORDER BY f.pct_bill)::numeric q2,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY f.pct_bill)::numeric q3
    FROM corpus.recipe_fermentables f JOIN r ON r.recipe_id = f.recipe_id
    WHERE f.pct_bill BETWEEN 0 AND 100 GROUP BY f.name_raw),

  hop_r AS (
    SELECT h.name_raw, h.recipe_id, sum(h.amount_g) / max(r.batch_l) gpl
    FROM corpus.recipe_hops h JOIN r ON r.recipe_id = h.recipe_id
    WHERE h.amount_g BETWEEN 0 AND 5000 GROUP BY 1, 2),
  hops AS (
    SELECT 2, row_number() OVER (ORDER BY count(*) DESC), 'hops'::text, x.name_raw, count(*)::int,
           'g/L'::text,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY x.gpl)::numeric,
           percentile_cont(0.50) WITHIN GROUP (ORDER BY x.gpl)::numeric,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY x.gpl)::numeric
    FROM hop_r x GROUP BY x.name_raw),

  yeasts AS (
    SELECT 3, row_number() OVER (ORDER BY count(DISTINCT y.recipe_id) DESC), 'yeast'::text,
           y.name_raw, count(DISTINCT y.recipe_id)::int, '% attenuation'::text,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY y.attenuation_pct)::numeric,
           percentile_cont(0.50) WITHIN GROUP (ORDER BY y.attenuation_pct)::numeric,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY y.attenuation_pct)::numeric
    FROM corpus.recipe_yeasts y JOIN r ON r.recipe_id = y.recipe_id GROUP BY y.name_raw),

  -- One row per (ingredient, unit). Units are never reconciled.
  misc AS (
    SELECT 4, row_number() OVER (ORDER BY count(DISTINCT m.recipe_id) DESC), 'other additions'::text,
           m.name_raw, count(DISTINCT m.recipe_id)::int, m.amount_unit,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY m.amount_value)::numeric,
           percentile_cont(0.50) WITHIN GROUP (ORDER BY m.amount_value)::numeric,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY m.amount_value)::numeric
    FROM corpus.recipe_misc m JOIN r ON r.recipe_id = m.recipe_id
    WHERE m.amount_value IS NOT NULL AND m.amount_unit IS NOT NULL
    GROUP BY m.name_raw, m.amount_unit HAVING count(*) >= 5),

  u AS (SELECT * FROM grain UNION ALL SELECT * FROM hops
        UNION ALL SELECT * FROM yeasts UNION ALL SELECT * FROM misc)
  SELECT u.sec, u.it, u.cnt, round(100.0 * u.cnt / (SELECT total FROM n), 1), u.un,
         round(u.q1, 2), round(u.q2, 2), round(u.q3, 2),
         -- Rendered so a unit cannot be misread, and so a wide spread READS as
         -- wide: ref.f_range_text's contract, applied to a quartile.
         CASE WHEN u.q1 IS NULL THEN 'no usable amount recorded'
              WHEN u.q3 > 0 AND u.q3 / NULLIF(u.q1, 0) >= 3
                THEN 'varies widely: ' || round(u.q2, 2) || ' ' || u.un ||
                     ' typical, but ' || round(u.q1, 2) || '-' || round(u.q3, 2) || ' is common'
              ELSE round(u.q2, 2) || ' ' || u.un ||
                   ' (usual range ' || round(u.q1, 2) || '-' || round(u.q3, 2) || ')'
         END
  FROM u, n
  WHERE u.rn <= CASE WHEN u.ord IN (1, 2) THEN p_top ELSE greatest(p_top / 2, 3) END
  ORDER BY u.ord, u.rn
$fn$;

-- ---------------------------------------------------------------------------
-- 3) nlq.ingredient_usage  ·  how one ingredient is used EVERYWHERE
--
-- The second, independent lookup: when the cohort has no vanilla stouts, this
-- still answers "how is vanilla used", style by style, from the 2,484 recipes
-- that use it anywhere. Deliberately NOT filtered by the cohort -- that is the
-- whole point of asking it separately.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.ingredient_usage(
  p_term text, p_top int DEFAULT 10
) RETURNS TABLE (
  style_raw text, n_recipes int, unit text,
  p25 numeric, p50 numeric, p75 numeric, typical text
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, nlq, public AS $fn$
  -- ⛔ MATERIALIZED IS LOad-BEARING. Inlined (the PG12+ default), the planner
  -- re-evaluates f_resolve_ingredient once PER ROW of recipe_misc -- 141,857
  -- rows x four substring sweeps over 33k dimension rows. `measured`: 69 ms with
  -- the keys resolved once, >60 s without. Same query, same data.
  WITH k AS MATERIALIZED (
    SELECT unnest(nlq.f_resolve_ingredient(p_term)) AS name_key
  ),
  hits AS (
    SELECT m.recipe_id, c.style_raw, m.amount_value AS val, m.amount_unit AS un
    FROM k
    JOIN corpus.recipe_misc m ON m.name_key = k.name_key  -- corpus_misc_key_idx
    JOIN corpus.recipes c ON c.id = m.recipe_id
    WHERE m.amount_value IS NOT NULL
      AND m.amount_unit  IS NOT NULL
      AND c.style_raw    IS NOT NULL
  ),
  agg AS (
    SELECT h.style_raw, h.un, count(DISTINCT h.recipe_id)::int cnt,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY h.val)::numeric q1,
           percentile_cont(0.50) WITHIN GROUP (ORDER BY h.val)::numeric q2,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY h.val)::numeric q3
    FROM hits h GROUP BY 1, 2 HAVING count(DISTINCT h.recipe_id) >= 5
  )
  SELECT a.style_raw, a.cnt, a.un, round(a.q1,2), round(a.q2,2), round(a.q3,2),
         round(a.q2,2) || ' ' || a.un || ' (usual range ' ||
           round(a.q1,2) || '-' || round(a.q3,2) || ')'
  FROM agg a ORDER BY a.cnt DESC LIMIT p_top
$fn$;

-- mem_writer is the credential cap-formulate-recipe runs its SQL on, and its
-- `Style bands` node now fetches the observed cohort beside the published band.
-- Same contract 15_ref.sql already uses for ref.f_style_bands: EXECUTE on the
-- SECURITY DEFINER function, never SELECT on corpus.* underneath it.
--
-- ⚠️ USAGE on a schema plus Postgres's default PUBLIC EXECUTE on functions means
-- mem_writer can reach the other nlq functions too. That is a widening, and it
-- is accepted rather than overlooked: nlq is read-only views and STABLE
-- functions over kb/brew, mem_writer already holds ref and brew, and the role
-- Layer 1 actually constrains is n8n_agent, which is untouched here.
DO $grant$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mem_writer') THEN
    GRANT USAGE ON SCHEMA nlq TO mem_writer;
    GRANT EXECUTE ON FUNCTION nlq.find_cohort(text, text[], numeric, numeric, numeric, numeric, int) TO mem_writer;
    GRANT EXECUTE ON FUNCTION nlq.cohort_stats(text, text[], numeric, numeric, numeric, numeric, int, int) TO mem_writer;
    GRANT EXECUTE ON FUNCTION nlq.f_resolve_ingredient(text) TO mem_writer;
    GRANT EXECUTE ON FUNCTION nlq.f_cohort_ids(text, text[], numeric, numeric, numeric, numeric, int) TO mem_writer;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'agent_ro') THEN
    GRANT EXECUTE ON FUNCTION nlq.f_resolve_ingredient(text) TO agent_ro;
    GRANT EXECUTE ON FUNCTION nlq.f_cohort_ids(text, text[], numeric, numeric, numeric, numeric, int) TO agent_ro;
    GRANT EXECUTE ON FUNCTION nlq.find_cohort(text, text[], numeric, numeric, numeric, numeric, int) TO agent_ro;
    GRANT EXECUTE ON FUNCTION nlq.cohort_stats(text, text[], numeric, numeric, numeric, numeric, int, int) TO agent_ro;
    GRANT EXECUTE ON FUNCTION nlq.ingredient_usage(text, int) TO agent_ro;
  END IF;
END $grant$;

-- Dead since the amount parse became a STORED generated column: the
-- set-returning form had no callers and every query reads recipe_misc's
-- amount_value / amount_unit directly.
DROP FUNCTION IF EXISTS corpus.f_parse_amount(text);
