-- =============================================================================
-- 40_nlq.sql  ·  The agent's ONLY surface (architecture §3.4, §8.2)
-- Every function is SECURITY DEFINER with typed, nullable parameters. No dynamic
-- SQL, no free-form input reaching the planner (§8.4 Layer 3). The n8n_agent role
-- gets USAGE on nlq + EXECUTE here and nothing else (grants in 50_roles.sql).
--
-- Functions are owned by the migration superuser and run with its rights, so the
-- agent reads knowledge/truth without ever holding a grant on kb/brew/mem. The
-- explicit `SET search_path` on each is the required SECURITY DEFINER hardening.
-- Idempotent.
-- =============================================================================

-- Hybrid retrieval over the book/PDF corpus: FTS + vector, fused with RRF (§3.4).
-- Over-fetch p_candidates from each arm, fuse, return p_limit.
--
-- The DROP is required, not defensive: CREATE OR REPLACE cannot change a
-- function's return type, and this one gained `authority` (D31 Layer 4). It
-- matches on argument types only, so it re-runs harmlessly on every db-init and
-- makes any future column addition here survivable. 50_roles.sql runs after this
-- file and re-grants EXECUTE, so the drop costs the agent nothing.
DROP FUNCTION IF EXISTS nlq.search_knowledge(text, vector, int, int, int, text, text);

CREATE OR REPLACE FUNCTION nlq.search_knowledge(
  p_query_text  text,
  p_query_embed vector(1024),
  p_limit       int  DEFAULT 6,
  p_candidates  int  DEFAULT 40,
  p_rrf_k       int  DEFAULT 50,
  p_model       text DEFAULT 'bge-m3',
  p_doc_type    text DEFAULT NULL
) RETURNS TABLE (
  chunk_id bigint, doc_slug text, doc_title text, heading_path text[],
  page_from int, page_to int, raw_content text, image_refs text[],
  -- authority is for the passage header the model reads ("Palmer suggests X;
  -- Angry Chair's practice is Y, which is opinion"). It is NOT a ranking input
  -- and must never become one (D31 Layer 4).
  image_dir text, authority text, score real
) LANGUAGE sql STABLE SECURITY DEFINER SET search_path = kb, public AS $$
WITH kw AS (
  SELECT c.id, row_number() OVER (
           ORDER BY ts_rank_cd(c.fts, websearch_to_tsquery('english', p_query_text)) DESC) AS rk
  FROM kb.chunks c
  JOIN kb.document_versions v ON v.id = c.version_id AND v.is_current
  JOIN kb.documents d ON d.id = v.document_id
  WHERE c.fts @@ websearch_to_tsquery('english', p_query_text)
    AND (p_doc_type IS NULL OR d.doc_type = p_doc_type)
  LIMIT p_candidates
),
vec AS (
  SELECT c.id, row_number() OVER (ORDER BY e.embedding <=> p_query_embed) AS rk
  FROM kb.chunk_embeddings e
  JOIN kb.chunks c ON c.id = e.chunk_id
  JOIN kb.document_versions v ON v.id = c.version_id AND v.is_current
  JOIN kb.documents d ON d.id = v.document_id
  WHERE e.model = p_model
    AND (p_doc_type IS NULL OR d.doc_type = p_doc_type)
  ORDER BY e.embedding <=> p_query_embed
  LIMIT p_candidates
),
fused AS (
  SELECT COALESCE(kw.id, vec.id) AS id,
         COALESCE(1.0/(p_rrf_k + kw.rk), 0) + COALESCE(1.0/(p_rrf_k + vec.rk), 0) AS score
  FROM kw FULL OUTER JOIN vec ON kw.id = vec.id
)
SELECT c.id, d.slug, d.title, c.heading_path, c.page_from, c.page_to,
       c.raw_content, c.image_refs, v.image_dir, d.authority, f.score::real
FROM fused f
JOIN kb.chunks c ON c.id = f.id
JOIN kb.document_versions v ON v.id = c.version_id
JOIN kb.documents d ON d.id = v.document_id
ORDER BY f.score DESC
LIMIT p_limit;
$$;

-- Truth query: filter the user's own batches (§8.2). SQL only, never retrieval.
-- Note LIMIT LEAST(p_limit, 50): the model cannot blow the context budget.
CREATE OR REPLACE FUNCTION nlq.find_batches(
  p_style_name          text    DEFAULT NULL,
  p_style_code          text    DEFAULT NULL,
  p_descriptor          text    DEFAULT NULL,
  p_brewed_after        date    DEFAULT NULL,
  p_brewed_before       date    DEFAULT NULL,
  p_min_abv             numeric DEFAULT NULL,
  p_max_abv             numeric DEFAULT NULL,
  p_min_dry_hop_rate    numeric DEFAULT NULL,
  p_max_dry_hop_rate    numeric DEFAULT NULL,
  p_limit               int     DEFAULT 20
) RETURNS TABLE (
  batch_no text, recipe_name text, style_code text, style_name text,
  brewed_on date, og numeric, fg numeric, abv numeric,
  dry_hop_rate_g_per_l numeric, descriptors text[], avg_score numeric
-- search_path includes ref because style names now come from ref.styles (D32).
) LANGUAGE sql STABLE SECURITY DEFINER SET search_path = brew, ref, public AS $$
  SELECT b.batch_no, r.name, s.code, s.name, b.brewed_on, b.og, b.fg,
         brew.f_abv(b.og, b.fg),
         brew.f_dry_hop_rate_g_per_l(b.id),
         (SELECT array_agg(DISTINCT d) FROM brew.sensory_notes sn,
                 unnest(sn.descriptors) d WHERE sn.batch_id = b.id),
         (SELECT round(avg(sn.score),1) FROM brew.sensory_notes sn WHERE sn.batch_id = b.id)
  FROM brew.batches b
  LEFT JOIN brew.recipes r ON r.id = b.recipe_id
  LEFT JOIN ref.styles s ON s.id = r.style_id
  WHERE (p_style_name IS NULL OR s.name ILIKE '%'||p_style_name||'%')
    AND (p_style_code IS NULL OR s.code = upper(p_style_code))
    AND (p_brewed_after  IS NULL OR b.brewed_on >= p_brewed_after)
    AND (p_brewed_before IS NULL OR b.brewed_on <= p_brewed_before)
    AND (p_min_abv IS NULL OR brew.f_abv(b.og,b.fg) >= p_min_abv)
    AND (p_max_abv IS NULL OR brew.f_abv(b.og,b.fg) <= p_max_abv)
    AND (p_min_dry_hop_rate IS NULL
         OR brew.f_dry_hop_rate_g_per_l(b.id) >= p_min_dry_hop_rate)
    AND (p_max_dry_hop_rate IS NULL
         OR brew.f_dry_hop_rate_g_per_l(b.id) <= p_max_dry_hop_rate)
    AND (p_descriptor IS NULL OR EXISTS (
          SELECT 1 FROM brew.sensory_notes sn
          WHERE sn.batch_id = b.id
            AND (sn.descriptors @> ARRAY[lower(p_descriptor)]
                 OR sn.fts @@ plainto_tsquery('english', p_descriptor))))
  ORDER BY b.brewed_on DESC
  LIMIT LEAST(p_limit, 50);
$$;

-- NOTE (Phase 3, §7.3/§8.2): remaining tools live here as SECURITY DEFINER
-- functions/views — nlq.get_inventory, nlq.get_batch_detail, nlq.compare_batches,
-- nlq.get_recipe, nlq.lookup_bjcp_style, plus nlq.search_lessons over
-- mem.memory_embeddings (kept separate from search_knowledge, §9.3).
