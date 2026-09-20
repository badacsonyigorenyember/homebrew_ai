-- =============================================================================
-- 78_trend.sql  ·  Style-level brewing practice
--
-- ⛔ THE CENTRAL RULE: MARGINAL FREQUENCY IS NOT JOINT COMPOSITION.
-- `measured` 2026-09-19 on American IPA: 713 distinct hop varieties, top-12
-- presence rates summing to 230%, median recipe using 3. The nine commonest malt
-- types' median grist percentages sum to 190%; a grist must sum to 100%.
--
-- So four kinds of fact live in four tables and are NEVER mixed:
--   shape        how many          style_profile
--   composition  role shares       style_grist_template   (<=100, undershoot expected)
--   choice+amount conditional      style_fermentable, style_hop
--   affinity     lift              style_hop_pair
--
-- The generator MUST read shape first, as a budget, before opening any
-- popularity list (TREND-SCHEMA.md 7). That is what makes 20 hops unreachable.
--
-- Runs AFTER 77_bf_corpus.sql. Idempotent.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS trend;
REVOKE ALL ON SCHEMA trend FROM PUBLIC;

-- D9: rebuilds write a NEW snapshot. Nothing mutates in place, so a finalised
-- patch stays finalised and two patches can be diffed.
CREATE TABLE IF NOT EXISTS trend.snapshot (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  built_at      timestamptz NOT NULL DEFAULT now(),
  corpus_filter text NOT NULL,
  n_recipes     int  NOT NULL,
  is_current    boolean NOT NULL DEFAULT false,
  notes         text
);
CREATE UNIQUE INDEX IF NOT EXISTS trend_snapshot_one_current
  ON trend.snapshot (is_current) WHERE is_current;

CREATE TABLE IF NOT EXISTS trend.style_profile (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  n_recipes    int NOT NULL,
  ferm_count_p25 numeric(4,1), ferm_count_p50 numeric(4,1), ferm_count_p75 numeric(4,1),
  hop_variety_count_p25 numeric(4,1),
  hop_variety_count_p50 numeric(4,1),   -- the 20-hop guard
  hop_variety_count_p75 numeric(4,1),
  hop_addition_count_p50 numeric(4,1),
  og_p50 numeric(6,4), fg_p50 numeric(6,4), abv_p50 numeric(5,2),
  ibu_p50 numeric(6,2), srm_p50 numeric(6,2),
  PRIMARY KEY (snapshot_id, ref_style_id)
);

CREATE TABLE IF NOT EXISTS trend.style_grist_template (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  role         text   NOT NULL,
  slots_p25 numeric(4,1), slots_p50 numeric(4,1), slots_p75 numeric(4,1),
  role_pct_p25 numeric(5,2), role_pct_p50 numeric(5,2), role_pct_p75 numeric(5,2),
  n_with int NOT NULL,
  PRIMARY KEY (snapshot_id, ref_style_id, role)
);

CREATE TABLE IF NOT EXISTS trend.style_fermentable (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  ferm_type    text   NOT NULL REFERENCES corpus.fermentable_types(type_key),
  role         text   NOT NULL,
  n_with        int NOT NULL,
  presence_rate numeric(5,4) NOT NULL,
  pct_of_grist_p25 numeric(5,2),
  pct_of_grist_p50 numeric(5,2),
  pct_of_grist_p75 numeric(5,2),
  PRIMARY KEY (snapshot_id, ref_style_id, ferm_type)
);

CREATE TABLE IF NOT EXISTS trend.style_hop (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  ref_hop_id   bigint NOT NULL REFERENCES ref.hops(id),
  n_with        int NOT NULL,
  presence_rate numeric(5,4) NOT NULL,
  share_of_hop_mass_p25 numeric(5,2),
  share_of_hop_mass_p50 numeric(5,2),
  share_of_hop_mass_p75 numeric(5,2),
  timing_min_p50 numeric(7,1),
  PRIMARY KEY (snapshot_id, ref_style_id, ref_hop_id)
);

-- ⛔ support >= 30 IS A CONSTRAINT, NOT A CONVENTION. A row below the gate
-- cannot exist (TREND-SCHEMA.md 1.4).
CREATE TABLE IF NOT EXISTS trend.style_hop_pair (
  snapshot_id  bigint NOT NULL REFERENCES trend.snapshot(id) ON DELETE CASCADE,
  ref_style_id bigint NOT NULL REFERENCES ref.styles(id),
  hop_a_id     bigint NOT NULL REFERENCES ref.hops(id),
  hop_b_id     bigint NOT NULL REFERENCES ref.hops(id),
  support    int NOT NULL,
  lift       numeric(8,3) NOT NULL,
  confidence numeric(5,4),
  PRIMARY KEY (snapshot_id, ref_style_id, hop_a_id, hop_b_id),
  CONSTRAINT hop_pair_ordered   CHECK (hop_a_id < hop_b_id),
  CONSTRAINT hop_pair_supported CHECK (support >= 30)
);

COMMENT ON TABLE trend.style_hop_pair IS
  'Hop affinity as LIFT, not co-occurrence. `measured` 2026-09-19 on American '
  'IPA: Cascade+Mosaic co-occurs MORE often than Ahtanum+Chinook (147 vs 62) yet '
  'lift 0.49 says brewers avoid it. Raw counts cannot express that.';

-- ---------------------------------------------------------------------------
-- Rebuild. Writes a new snapshot and flips is_current at the end.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trend.f_rebuild(p_min_n int DEFAULT 30)
RETURNS TABLE (snapshot bigint, styles bigint, ferms bigint, hops bigint, pairs bigint)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = trend, corpus, ref, public AS $fn$
DECLARE v_snap bigint;
BEGIN
  INSERT INTO trend.snapshot (corpus_filter, n_recipes, notes)
  SELECT 'views>500 script-clean', count(*), 'trend.f_rebuild'
  FROM corpus.bf_recipes
  RETURNING id INTO v_snap;

  -- shape
  INSERT INTO trend.style_profile
  SELECT v_snap, r.ref_style_id, count(*),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY c.nf),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY c.nf),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY c.nf),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY c.nh),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY c.nh),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY c.nh),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY c.na),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.og)  FILTER (WHERE r.og BETWEEN 1.0 AND 1.2),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.fg)  FILTER (WHERE r.fg BETWEEN 0.98 AND 1.1),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.abv) FILTER (WHERE r.abv BETWEEN 0 AND 20),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.ibu) FILTER (WHERE r.ibu BETWEEN 0 AND 150),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY r.color_srm) FILTER (WHERE r.color_srm BETWEEN 0 AND 80)
  FROM corpus.bf_recipes r
  JOIN LATERAL (
    SELECT (SELECT count(*) FROM corpus.bf_fermentables f WHERE f.recipe_id=r.id) AS nf,
           (SELECT count(DISTINCT h.ref_hop_id) FROM corpus.bf_hops h WHERE h.recipe_id=r.id) AS nh,
           (SELECT count(*) FROM corpus.bf_hops h WHERE h.recipe_id=r.id) AS na
  ) c ON true
  WHERE r.ref_style_id IS NOT NULL
  GROUP BY r.ref_style_id HAVING count(*) >= p_min_n;

  -- composition: unconditional over the style's recipes, absent role = 0.
  -- RULING 11: a per-role median taken only over the recipes that HAVE that
  -- role is a choice+amount figure (that's style_fermentable's job), not
  -- composition. base and extract are near-disjoint populations (all-grain vs
  -- extract brewing) whose conditional medians summed past 200% for American
  -- Light Lager. Composition must be computed over every recipe in the style,
  -- with roles the recipe doesn't use contributing 0 — that is what makes the
  -- six role shares describe one grist instead of six different subsets.
  -- n_with still counts only recipes that actually contain the role, so it
  -- keeps distinguishing a rare role from a common one; only the percentile
  -- population (denominator) is zero-filled.
  --
  -- RULING 12: this is unconditional by design, and unconditional means a
  -- role held by fewer than half a style's recipes has median 0 and drops
  -- out of the sum — medians do not add the way means would. That undershoot
  -- is expected, not a bug: a role a minority of brewers use genuinely is
  -- not part of the style's typical grist, and the conditional figure for
  -- when it IS used already lives in style_fermentable (presence_rate +
  -- pct_of_grist_p50) — mixing that back in here would re-open the exact
  -- conflation Ruling 11 closed. `measured` 2026-09-20 on this rebuild, 73
  -- styles: 0 exceeding 100, min 78.50 / median 92.40 / max 99.35. No
  -- consumer needs the stored sum to reach 100 — the generator (TREND-
  -- SCHEMA.md §7 step 3) normalises the drawn shares to exactly 100% itself.
  INSERT INTO trend.style_grist_template
  SELECT v_snap, z.ref_style_id, z.role,
    percentile_cont(0.25) WITHIN GROUP (ORDER BY z.slots),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY z.slots),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY z.slots),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY z.pct),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY z.pct),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY z.pct),
    count(*) FILTER (WHERE z.has_role)
  FROM (
    SELECT rc.ref_style_id, rl.role, rc.id,
           coalesce(x.slots, 0) AS slots, coalesce(x.pct, 0) AS pct,
           (x.id IS NOT NULL) AS has_role
    FROM (
      SELECT DISTINCT r.ref_style_id, r.id
      FROM corpus.bf_recipes r
      JOIN corpus.bf_fermentables f ON f.recipe_id = r.id
      JOIN corpus.fermentable_types t ON t.type_key = f.ferm_type
      WHERE r.ref_style_id IS NOT NULL
    ) rc
    CROSS JOIN (SELECT DISTINCT role FROM corpus.fermentable_types) rl
    LEFT JOIN (
      SELECT r.ref_style_id, t.role, r.id,
             count(DISTINCT f.ferm_type) AS slots, sum(f.pct_of_grist) AS pct
      FROM corpus.bf_recipes r
      JOIN corpus.bf_fermentables f ON f.recipe_id = r.id
      JOIN corpus.fermentable_types t ON t.type_key = f.ferm_type
      WHERE r.ref_style_id IS NOT NULL
      GROUP BY r.ref_style_id, t.role, r.id
    ) x ON x.ref_style_id = rc.ref_style_id AND x.id = rc.id AND x.role = rl.role
  ) z
  GROUP BY z.ref_style_id, z.role HAVING count(*) FILTER (WHERE z.has_role) >= p_min_n;

  -- choice + amount, conditional on presence
  -- ⚠ presence_rate divides by the RECIPE count for the style, which is why
  -- sn is a separate join and not a window: a window over the grouped rows
  -- would count (style, type, recipe) combinations instead.
  INSERT INTO trend.style_fermentable
  SELECT v_snap, x.ref_style_id, x.ferm_type, x.role, count(*),
    round(count(*)::numeric / max(sn.n), 4),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY x.pct),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY x.pct),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY x.pct)
  FROM (
    SELECT r.ref_style_id, f.ferm_type, t.role, sum(f.pct_of_grist) AS pct
    FROM corpus.bf_recipes r
    JOIN corpus.bf_fermentables f ON f.recipe_id = r.id
    JOIN corpus.fermentable_types t ON t.type_key = f.ferm_type
    WHERE r.ref_style_id IS NOT NULL
    GROUP BY r.ref_style_id, f.ferm_type, t.role, r.id
  ) x
  JOIN (SELECT ref_style_id, count(*) n FROM corpus.bf_recipes
        WHERE ref_style_id IS NOT NULL GROUP BY 1) sn
    ON sn.ref_style_id = x.ref_style_id
  GROUP BY x.ref_style_id, x.ferm_type, x.role HAVING count(*) >= p_min_n;

  INSERT INTO trend.style_hop
  SELECT v_snap, x.ref_style_id, x.ref_hop_id, count(*),
    round(count(*)::numeric / max(sn.n), 4),
    percentile_cont(0.25) WITHIN GROUP (ORDER BY x.share),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY x.share),
    percentile_cont(0.75) WITHIN GROUP (ORDER BY x.share),
    percentile_cont(0.50) WITHIN GROUP (ORDER BY x.tmin)
  FROM (
    SELECT r.ref_style_id, h.ref_hop_id,
           100.0 * sum(h.amount_g)
             / nullif(sum(sum(h.amount_g)) OVER (PARTITION BY r.id), 0) AS share,
           avg(h.timing_min) AS tmin
    FROM corpus.bf_recipes r
    JOIN corpus.bf_hops h ON h.recipe_id = r.id
    WHERE r.ref_style_id IS NOT NULL AND h.ref_hop_id IS NOT NULL
    GROUP BY r.ref_style_id, h.ref_hop_id, r.id
  ) x
  JOIN (SELECT ref_style_id, count(*) n FROM corpus.bf_recipes
        WHERE ref_style_id IS NOT NULL GROUP BY 1) sn
    ON sn.ref_style_id = x.ref_style_id
  GROUP BY x.ref_style_id, x.ref_hop_id HAVING count(*) >= p_min_n;

  -- affinity: lift = P(A and B) / (P(A) * P(B))
  INSERT INTO trend.style_hop_pair
  SELECT v_snap, p.ref_style_id, p.a, p.b, p.support,
         round((p.support::numeric * s.n) / (ha.n_with * hb.n_with), 3),
         round(p.support::numeric / ha.n_with, 4)
  FROM (
    SELECT r.ref_style_id, ha.ref_hop_id AS a, hb.ref_hop_id AS b, count(DISTINCT r.id) AS support
    FROM corpus.bf_recipes r
    JOIN corpus.bf_hops ha ON ha.recipe_id = r.id AND ha.ref_hop_id IS NOT NULL
    JOIN corpus.bf_hops hb ON hb.recipe_id = r.id AND hb.ref_hop_id > ha.ref_hop_id
    WHERE r.ref_style_id IS NOT NULL
    GROUP BY r.ref_style_id, ha.ref_hop_id, hb.ref_hop_id
    HAVING count(DISTINCT r.id) >= 30
  ) p
  JOIN (SELECT ref_style_id, count(*) n FROM corpus.bf_recipes
        WHERE ref_style_id IS NOT NULL GROUP BY 1) s ON s.ref_style_id = p.ref_style_id
  JOIN trend.style_hop ha ON ha.snapshot_id=v_snap AND ha.ref_style_id=p.ref_style_id AND ha.ref_hop_id=p.a
  JOIN trend.style_hop hb ON hb.snapshot_id=v_snap AND hb.ref_style_id=p.ref_style_id AND hb.ref_hop_id=p.b;

  UPDATE trend.snapshot SET is_current = false WHERE is_current;
  UPDATE trend.snapshot SET is_current = true  WHERE id = v_snap;

  RETURN QUERY SELECT v_snap,
    (SELECT count(*) FROM trend.style_profile      WHERE snapshot_id=v_snap),
    (SELECT count(*) FROM trend.style_fermentable  WHERE snapshot_id=v_snap),
    (SELECT count(*) FROM trend.style_hop          WHERE snapshot_id=v_snap),
    (SELECT count(*) FROM trend.style_hop_pair     WHERE snapshot_id=v_snap);
END
$fn$;

-- Schema-level REVOKE above does not reach function-level grants, so Postgres's
-- default PUBLIC EXECUTE on a new function survives it unless revoked here too.
REVOKE ALL ON FUNCTION trend.f_rebuild(int) FROM PUBLIC;

-- Reads go through views pinned to is_current, so callers never name a snapshot.
CREATE OR REPLACE VIEW trend.v_style_profile AS
  SELECT p.* FROM trend.style_profile p
  JOIN trend.snapshot s ON s.id = p.snapshot_id AND s.is_current;
CREATE OR REPLACE VIEW trend.v_style_grist_template AS
  SELECT g.* FROM trend.style_grist_template g
  JOIN trend.snapshot s ON s.id = g.snapshot_id AND s.is_current;
CREATE OR REPLACE VIEW trend.v_style_fermentable AS
  SELECT f.* FROM trend.style_fermentable f
  JOIN trend.snapshot s ON s.id = f.snapshot_id AND s.is_current;
CREATE OR REPLACE VIEW trend.v_style_hop AS
  SELECT h.* FROM trend.style_hop h
  JOIN trend.snapshot s ON s.id = h.snapshot_id AND s.is_current;
CREATE OR REPLACE VIEW trend.v_style_hop_pair AS
  SELECT p.* FROM trend.style_hop_pair p
  JOIN trend.snapshot s ON s.id = p.snapshot_id AND s.is_current;
