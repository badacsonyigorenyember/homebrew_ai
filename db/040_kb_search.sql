-- app.kb_search: hybrid retrieval over kb.chunk. The nearest chunks by cosine distance (HNSW)
-- and the best full-text matches (GIN) are fused by reciprocal rank.
-- Needs db/014_kb.sql applied first.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/040_kb_search.sql
-- Idempotent: safe to re-run.
--
-- The caller embeds the question first (bge-m3, 1024 dims) and passes text and vector.
-- score = 1/(rrf_k + vec_rank) + 1/(rrf_k + fts_rank); an arm that did not find the chunk adds 0.

-- The drop is needed because the return type changed (s7: source_url added); create or replace
-- cannot change it.
drop function if exists app.kb_search(text, extensions.vector, integer, integer, integer);

create function app.kb_search(
    query_text      text,
    query_embedding extensions.vector(1024),
    k               integer default 5,
    candidates      integer default 40,
    rrf_k           integer default 60)
returns table (chunk_id bigint, source_slug text, source_title text, source_url text, section_path text,
               page integer, text text, score double precision, vec_rank integer, fts_rank integer)
language sql stable
set search_path = public, extensions
as $$
    with
    -- Vector arm: the nearest chunks. The inner order by ... limit is what the HNSW index serves.
    vec as (
        select id, row_number() over (order by distance, id)::integer as rank
        from (select id, embedding <=> query_embedding as distance
              from kb.chunk
              order by embedding <=> query_embedding
              limit candidates) nearest
    ),
    -- The question as an OR query: a chunk matching any query word counts
    -- (a whole question ANDed matches almost nothing).
    words as (
        select replace(plainto_tsquery('english', query_text)::text, ' & ', ' | ')::tsquery as q
    ),
    -- Full-text arm: the best matches for any query word.
    fts as (
        select id, row_number() over (order by score desc, id)::integer as rank
        from (select c.id, ts_rank_cd(c.fts, words.q) as score
              from kb.chunk c, words
              where c.fts @@ words.q
              order by score desc, c.id
              limit candidates) matched
    ),
    -- Fuse the two rankings.
    fused as (
        select coalesce(vec.id, fts.id) as id,
               vec.rank as vec_rank,
               fts.rank as fts_rank,
               (coalesce(1.0 / (rrf_k + vec.rank), 0)
                + coalesce(1.0 / (rrf_k + fts.rank), 0))::double precision as score
        from vec full outer join fts on fts.id = vec.id
    )
    select c.id, s.slug, s.title, s.url, c.section_path, c.page, c.text,
           fused.score, fused.vec_rank, fused.fts_rank
    from fused
    join kb.chunk c on c.id = fused.id
    join ref.source s on s.id = c.source_id
    order by fused.score desc, c.id
    limit k
$$;
