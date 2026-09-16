-- =============================================================================
-- 72_nlq_corpus.sql  ·  The corpus, reshaped for a 12B model (architecture §8.4)
--
-- corpus.* is revoked from PUBLIC and stays that way. This file is the ONLY
-- surface through which the agent reaches it, and it is deliberately narrow.
--
-- ⛔ NOT A VECTOR PATH. Nothing here embeds anything. The corpus is
-- self-reported and unattributed, so it must never enter kb.chunks; what it can
-- honestly answer is "how often" and "how much", which is a SQL question. The
-- retrieval tool keeps answering "what does the library say"; this answers
-- "what do brewers actually do", and the two must not be confused in an answer.
--
-- ⛔ NO MIN/MAX COLUMNS ARE EXPOSED, AND THAT IS THE WHOLE POINT. corpus.hops
-- records Cascade at alpha 0.00-88.40 because users type into a free field. A
-- model handed that row answers "Cascade is 0 to 88.4% alpha" without
-- hesitating -- the same failure ref.styles.has_vitals exists to prevent. Only
-- the mode and the median leave this file, and quantities leave as RENDERED
-- TEXT ('11.5% of grist', '2.3 g/L at dry hop') so a unit cannot be misread,
-- the same reason ref.f_range_text renders instead of returning numbers.
--
-- Runs AFTER 71_corpus_dims.sql. Idempotent.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Which corpus style strings does the brewer's phrase mean?
--
-- Same problem ref.f_style_bands solves for the guides, same shape of answer:
-- match the HEAD NOUN (English beer-style names are head-final), then keep the
-- rows sharing the most of the remaining words. 'hazy ipa' lands on the New
-- England row; a bare 'stout' keeps every stout and the answer widens.
-- 'beer' alone is a shrug, not a style, and matches nothing.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.f_corpus_styles(p_style text)
RETURNS TABLE (style_raw text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, public AS $fn$
  WITH w AS (
    SELECT array_remove(regexp_split_to_array(
             regexp_replace(lower(btrim(coalesce(p_style, ''))), '[^a-z0-9]+', ' ', 'g'),
             ' '), '') AS words
  ),
  h AS (SELECT words, words[array_length(words, 1)] AS head FROM w),
  m AS (
    SELECT DISTINCT c.style_raw,
           (SELECT count(*) FROM unnest(h.words) x
             WHERE length(x) >= 3 AND c.style_raw ILIKE '%' || x || '%') AS hits
    FROM corpus.recipes c, h
    WHERE h.head IS NOT NULL AND h.head <> 'beer'
      AND c.style_raw IS NOT NULL
      AND c.style_raw ILIKE '%' || h.head || '%'
  )
  SELECT style_raw FROM m WHERE hits = (SELECT max(hits) FROM m)
$fn$;

-- ---------------------------------------------------------------------------
-- nlq.common_practice(style)  ·  what brewers actually put in this beer
--
-- One flat table, one call. `section` groups it, `item` names the thing, and
-- `typical` is already a phrase -- a small model reads a short table far more
-- reliably than it reads nested JSON, and cannot invent a unit that is spelled
-- out for it.
--
-- Outliers are filtered here rather than by the caller: batch sizes outside
-- 5-100 L and percentages outside 0-100 are data-entry noise, and a median
-- taken over them is not a median of anything.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION nlq.common_practice(
  p_style text,
  p_top   int DEFAULT 8
) RETURNS TABLE (
  section        text,
  item           text,
  pct_of_recipes numeric,
  typical        text
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = corpus, nlq, public AS $fn$
  WITH s AS (SELECT style_raw FROM nlq.f_corpus_styles(p_style)),
  r AS (
    SELECT c.id, c.og, c.fg, c.abv, c.ibu, c.color_srm, c.batch_l
    FROM corpus.recipes c JOIN s ON s.style_raw = c.style_raw
    WHERE c.batch_l BETWEEN 5 AND 100
  ),
  n AS (SELECT count(*)::numeric AS total FROM r),

  overview AS (
    SELECT 0 AS ord, 0 AS rn, 'overview'::text AS section,
           'recipes in corpus'::text AS item, NULL::numeric AS pct,
           to_char((SELECT total FROM n), 'FM999,999') || ' matching recipes' AS typical
    WHERE (SELECT total FROM n) > 0
    UNION ALL
    SELECT 0, 1, 'overview', label, NULL::numeric, val FROM (
      SELECT 'typical OG'::text AS label,
             to_char(percentile_cont(0.5) WITHIN GROUP (ORDER BY og), 'FM0.000') AS val
        FROM r WHERE og BETWEEN 1.0 AND 1.2
      UNION ALL SELECT 'typical FG',
             to_char(percentile_cont(0.5) WITHIN GROUP (ORDER BY fg), 'FM0.000')
        FROM r WHERE fg BETWEEN 0.98 AND 1.1
      UNION ALL SELECT 'typical ABV',
             to_char(percentile_cont(0.5) WITHIN GROUP (ORDER BY abv), 'FM990.0') || '%'
        FROM r WHERE abv BETWEEN 0 AND 20
      UNION ALL SELECT 'typical IBU',
             to_char(percentile_cont(0.5) WITHIN GROUP (ORDER BY ibu), 'FM990')
        FROM r WHERE ibu BETWEEN 0 AND 150
      UNION ALL SELECT 'typical SRM',
             to_char(percentile_cont(0.5) WITHIN GROUP (ORDER BY color_srm), 'FM990.0')
        FROM r WHERE color_srm BETWEEN 0 AND 80
    ) m WHERE m.val IS NOT NULL
  ),

  grain AS (
    SELECT 1 AS ord,
           row_number() OVER (ORDER BY count(DISTINCT f.recipe_id) DESC) AS rn,
           'grain bill'::text AS section, f.name_raw AS item,
           round(100.0 * count(DISTINCT f.recipe_id) / (SELECT total FROM n), 1) AS pct,
           to_char(percentile_cont(0.5) WITHIN GROUP (ORDER BY f.pct_bill), 'FM990.0')
             || '% of grist' AS typical
    FROM corpus.recipe_fermentables f JOIN r ON r.id = f.recipe_id
    WHERE f.pct_bill BETWEEN 0 AND 100
    GROUP BY f.name_raw
  ),

  -- Hops are summed per recipe first: the same variety appears at boil,
  -- whirlpool and dry hop, and a rate must count the beer once, not the
  -- additions. The dominant use is reported beside it so 'Citra, 2.3 g/L,
  -- usually dry hop' reads as one fact.
  hop_rate AS (
    SELECT h.name_raw, h.recipe_id, sum(h.amount_g) / max(r.batch_l) AS g_per_l
    FROM corpus.recipe_hops h JOIN r ON r.id = h.recipe_id
    WHERE h.amount_g BETWEEN 0 AND 5000
    GROUP BY h.name_raw, h.recipe_id
  ),
  hop_use AS (
    SELECT DISTINCT ON (h.name_raw) h.name_raw, h.use
    FROM corpus.recipe_hops h JOIN r ON r.id = h.recipe_id
    WHERE h.use IS NOT NULL
    GROUP BY h.name_raw, h.use
    ORDER BY h.name_raw, count(*) DESC
  ),
  hops AS (
    SELECT 2 AS ord,
           row_number() OVER (ORDER BY count(*) DESC) AS rn,
           'hops'::text AS section, x.name_raw AS item,
           round(100.0 * count(*) / (SELECT total FROM n), 1) AS pct,
           to_char(percentile_cont(0.5) WITHIN GROUP (ORDER BY x.g_per_l), 'FM990.00')
             || ' g/L, usually ' || lower(coalesce(u.use, 'boil')) AS typical
    FROM hop_rate x LEFT JOIN hop_use u ON u.name_raw = x.name_raw
    GROUP BY x.name_raw, u.use
  ),

  yeasts AS (
    SELECT 3 AS ord,
           row_number() OVER (ORDER BY count(DISTINCT y.recipe_id) DESC) AS rn,
           'yeast'::text AS section, y.name_raw AS item,
           round(100.0 * count(DISTINCT y.recipe_id) / (SELECT total FROM n), 1) AS pct,
           coalesce(to_char(mode() WITHIN GROUP (ORDER BY y.attenuation_pct), 'FM990')
                      || '% apparent attenuation', 'no attenuation recorded') AS typical
    FROM corpus.recipe_yeasts y JOIN r ON r.id = y.recipe_id
    GROUP BY y.name_raw
  ),

  -- Water salts and finings, which is where the corpus is most useful and the
  -- library most silent: no book says how often people actually add gypsum.
  miscs AS (
    SELECT 4 AS ord,
           row_number() OVER (ORDER BY count(DISTINCT m.recipe_id) DESC) AS rn,
           'other additions'::text AS section, m.name_raw AS item,
           round(100.0 * count(DISTINCT m.recipe_id) / (SELECT total FROM n), 1) AS pct,
           coalesce(mode() WITHIN GROUP (ORDER BY m.type_raw), 'other')
             || ', at ' || lower(coalesce(mode() WITHIN GROUP (ORDER BY m.use_raw), 'boil')) AS typical
    FROM corpus.recipe_misc m JOIN r ON r.id = m.recipe_id
    GROUP BY m.name_raw
  ),

  all_rows AS (
    SELECT * FROM overview
    UNION ALL SELECT * FROM grain   WHERE rn <= p_top
    UNION ALL SELECT * FROM hops    WHERE rn <= p_top
    UNION ALL SELECT * FROM yeasts  WHERE rn <= greatest(p_top / 2, 3)
    UNION ALL SELECT * FROM miscs   WHERE rn <= greatest(p_top / 2, 3)
  )
  -- Below ~30 recipes the percentages stop meaning anything, so nothing is
  -- returned at all. An empty result the tool can report as "the corpus has
  -- nothing for that style" is honest; a 2-recipe median dressed as practice
  -- is not.
  SELECT section, item, pct, typical
  FROM all_rows, n
  WHERE n.total >= 30
  ORDER BY ord, rn, pct DESC NULLS FIRST
$fn$;

COMMENT ON FUNCTION nlq.common_practice(text, int) IS
  'What brewers actually brew for a named style, from 174k self-reported recipes. '
  'Observed practice, NOT published guidance -- an answer must attribute it as '
  '"what brewers commonly do", never as what a book or guideline says. Returns '
  'nothing below 30 matching recipes rather than a meaningless median.';

-- ⛔ GUARDED, because this file runs inside the db-init LOOP and 50_roles.sql --
-- which creates agent_ro -- runs AFTER it. On a fresh volume the role does not
-- exist yet, and a bare GRANT would abort the whole migration under
-- ON_ERROR_STOP=1. 50_roles.sql re-grants these anyway via its blanket
-- `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA nlq`, so the guard costs nothing and
-- keeps the file correct when applied on its own.
DO $grant$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'agent_ro') THEN
    GRANT EXECUTE ON FUNCTION nlq.f_corpus_styles(text)      TO agent_ro;
    GRANT EXECUTE ON FUNCTION nlq.common_practice(text, int) TO agent_ro;
  END IF;
END $grant$;
