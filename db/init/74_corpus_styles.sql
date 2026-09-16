-- =============================================================================
-- 74_corpus_styles.sql  ·  The style dimension, and the bridge to ref.styles
--
-- The asymmetry 73 left behind: four ingredient dimensions and none for style,
-- so `style_raw` sat as bare text on 174,554 rows and every cohort query did a
-- LIKE scan instead of an indexed join.
--
-- It also carries the join this whole schema was built to make possible. The
-- corpus says what brewers DID; ref.styles says what a guide PERMITS. Until
-- something links them, a formulated recipe can be checked against one or the
-- other but never both, and the interesting cases are exactly where they
-- disagree.
--
-- ⛔ THE BRIDGE IS ONLY AUTO-FILLED WHERE THE NAMES MATCH EXACTLY (101 of 181,
-- normalised for case and punctuation). The other 80 are left NULL on purpose.
-- Many are obvious to a human -- "Dry Stout" is BJCP 2021's "Irish Stout",
-- "Bohemian Pilsener" is "Czech Premium Pale Lager", "Dortmunder Export" is
-- "German Helles Exportbier" -- and precisely because they are renames across
-- guide editions, guessing them in SQL would be this schema inventing a mapping
-- and presenting it as sourced. Some are not beer styles at all (Dry Mead,
-- Common Cider, Common Perry, Apple Wine, Braggot) and some are not styles
-- (`--`, `Clone Beer`). corpus.v_styles_unbridged lists what is left.
--
-- Runs AFTER 73_corpus_search.sql (needs corpus.recipe_search). Idempotent.
-- =============================================================================

CREATE TABLE IF NOT EXISTS corpus.styles (
  style_raw    text PRIMARY KEY,
  style_key    text GENERATED ALWAYS AS
                 (lower(btrim(regexp_replace(style_raw, '[^a-zA-Z0-9]+', ' ', 'g')))) STORED,
  n_recipes    int NOT NULL DEFAULT 0,

  -- Observed vitals, cached. These are a pure GROUP BY over corpus.recipe_search
  -- and were being recomputed on every nlq.common_practice call -- the slowest
  -- path in the surface at 1082 ms. Denormalised deliberately: this workload is
  -- read-only and read-heavy, so a stale-able cache rebuilt in one pass beats
  -- recomputing a median over 12,891 stouts per question.
  og           numeric(6,4),
  fg           numeric(6,4),
  abv          numeric(6,2),
  ibu          numeric(7,2),
  color_srm    numeric(7,2),

  -- The bridge. NULL means "nobody has established this link", which is a
  -- different and more useful statement than a wrong link.
  ref_style_id bigint REFERENCES ref.styles(id) ON DELETE SET NULL,
  match_method text CHECK (match_method IN ('exact', 'manual')),

  CONSTRAINT styles_bridge_method CHECK (
    (ref_style_id IS NULL AND match_method IS NULL) OR
    (ref_style_id IS NOT NULL AND match_method IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS corpus_styles_ref_idx ON corpus.styles (ref_style_id);

-- ⚠️ NO INDEX ON style_key. The column stays -- it is the documented fold and
-- costs nothing over 181 rows -- but nothing reads it: f_rebuild_styles matches
-- on unaccent(style_raw) because unaccent() is STABLE and cannot live in a
-- generated column, and f_cohort_ids uses recipe_search.style_key, a different
-- table. An index on a column no query names can never be chosen.
DROP INDEX IF EXISTS corpus.corpus_styles_key_idx;
DROP INDEX IF EXISTS corpus.corpus_styles_trgm_idx;

COMMENT ON TABLE corpus.styles IS
  'One row per distinct style string in the corpus (181), with its observed '
  'vitals cached and a nullable bridge to the published guideline in ref.styles. '
  'A NULL ref_style_id means no link has been established -- never that the '
  'style has no guideline.';
COMMENT ON COLUMN corpus.styles.match_method IS
  'How the bridge was made: ''exact'' is an automatic normalised name match, '
  '''manual'' is a human decision. f_rebuild_styles never overwrites ''manual''.';

-- ---------------------------------------------------------------------------
-- Rebuild. Upsert, never truncate: a manual bridge is human work and survives
-- every rebuild. Only rows that are unlinked, or linked by the automatic rule,
-- have their bridge recomputed.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION corpus.f_rebuild_styles()
RETURNS TABLE (styles bigint, bridged bigint, manual bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = corpus, ref, public AS $fn$
BEGIN
  INSERT INTO corpus.styles (style_raw, n_recipes, og, fg, abv, ibu, color_srm)
  SELECT s.style_raw, count(*)::int,
         percentile_cont(0.5) WITHIN GROUP (ORDER BY s.og)  FILTER (WHERE s.og  BETWEEN 1.0 AND 1.2   AND s.batch_l BETWEEN 5 AND 100),
         percentile_cont(0.5) WITHIN GROUP (ORDER BY s.fg)  FILTER (WHERE s.fg  BETWEEN 0.98 AND 1.1  AND s.batch_l BETWEEN 5 AND 100),
         percentile_cont(0.5) WITHIN GROUP (ORDER BY s.abv) FILTER (WHERE s.abv BETWEEN 0 AND 20      AND s.batch_l BETWEEN 5 AND 100),
         percentile_cont(0.5) WITHIN GROUP (ORDER BY s.ibu) FILTER (WHERE s.ibu BETWEEN 0 AND 150     AND s.batch_l BETWEEN 5 AND 100),
         percentile_cont(0.5) WITHIN GROUP (ORDER BY s.color_srm) FILTER (WHERE s.color_srm BETWEEN 0 AND 80 AND s.batch_l BETWEEN 5 AND 100)
  FROM corpus.recipe_search s
  -- Every style that appears gets a row, so corpus.recipes can carry a real FK
  -- to this table. The batch-size filter applies to the VITALS only (via the
  -- FILTER clauses above plus this one), never to whether the style exists:
  -- a style whose every recipe is an odd batch size is still a style.
  WHERE s.style_raw IS NOT NULL
  GROUP BY s.style_raw
  ON CONFLICT (style_raw) DO UPDATE SET
    n_recipes = EXCLUDED.n_recipes, og = EXCLUDED.og, fg = EXCLUDED.fg,
    abv = EXCLUDED.abv, ibu = EXCLUDED.ibu, color_srm = EXCLUDED.color_srm;

  -- Automatic bridge: identical names once case and punctuation are stripped.
  -- BJCP is preferred over BA when both match, because the corpus's own style
  -- list is BJCP-derived. Nothing fuzzier than equality is attempted.
  UPDATE corpus.styles c
     SET ref_style_id = m.id, match_method = 'exact'
    FROM (
      -- ⚠️ unaccent, or "Kölsch" folds to "k lsch" and never meets BJCP's
      -- "Kolsch". The corpus is a German/Belgian-style-heavy homebrew site, so
      -- the accented names are not a rare edge: Kölsch alone is 1,957 recipes.
      -- It lives here and not in style_key because unaccent() is STABLE, and a
      -- generated column needs IMMUTABLE.
      SELECT DISTINCT ON (k)
             lower(btrim(regexp_replace(public.unaccent(r.name), '[^a-zA-Z0-9]+', ' ', 'g'))) AS k,
             r.id
      FROM ref.styles r
      ORDER BY k, (r.guide = 'BJCP') DESC, r.guide_year DESC, r.id
    ) m
   WHERE m.k = lower(btrim(regexp_replace(public.unaccent(c.style_raw), '[^a-zA-Z0-9]+', ' ', 'g')))
     AND c.match_method IS DISTINCT FROM 'manual';

  -- Added here rather than in the DDL: the constraint cannot exist while this
  -- table is empty and corpus.recipes is not, which is the state a fresh load
  -- passes through. Same contract f_rebuild_dims holds for the ingredient FKs.
  ALTER TABLE corpus.recipes DROP CONSTRAINT IF EXISTS recipes_style_fk;
  ALTER TABLE corpus.recipes ADD CONSTRAINT recipes_style_fk
    FOREIGN KEY (style_raw) REFERENCES corpus.styles(style_raw);

  RETURN QUERY SELECT count(*), count(ref_style_id), count(*) FILTER (WHERE match_method = 'manual')
               FROM corpus.styles;
END $fn$;

-- What a human still has to decide. Ordered by how much it would buy.
CREATE OR REPLACE VIEW corpus.v_styles_unbridged AS
SELECT style_raw, n_recipes, abv, ibu, color_srm
FROM corpus.styles WHERE ref_style_id IS NULL
ORDER BY n_recipes DESC;

COMMENT ON VIEW corpus.v_styles_unbridged IS
  'Corpus styles with no link to a published guideline, commonest first. Link '
  'one with: UPDATE corpus.styles SET ref_style_id = <ref.styles.id>, '
  'match_method = ''manual'' WHERE style_raw = ''...''; rebuilds preserve it.';
