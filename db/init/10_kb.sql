-- =============================================================================
-- 10_kb.sql  ·  Knowledge schema (architecture §3.2)
-- Replaces the flat `documents` table with a 4-table model:
--   kb.documents -> kb.document_versions -> kb.chunks -> kb.chunk_embeddings
-- Standardised on 1024-dim embeddings (bge-m3 native; qwen3-embedding MRL-truncatable).
-- Idempotent.
-- =============================================================================

-- One row per logical source document ---------------------------------------
CREATE TABLE IF NOT EXISTS kb.documents (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  slug         text NOT NULL UNIQUE,             -- 'stout-style-guide'
  title        text NOT NULL,
  doc_type     text NOT NULL
               CHECK (doc_type IN ('book','style_guide','article','datasheet','note')),
  authors      text[],
  language     text NOT NULL DEFAULT 'en',
  edition_note text,
  -- Presentation metadata (D31 Layer 4), populated by the ingest launcher.
  -- NEVER enters ranking: boosting the "reference" source suppresses exactly the
  -- disagreement this corpus exists to surface, and does it invisibly -- you
  -- would never see the passage that lost. Solve §5.6 in presentation.
  authority    text CHECK (authority IN ('reference','guideline','practitioner')),
  created_at   timestamptz NOT NULL DEFAULT now()
);

-- One row per ingested file revision. Idempotency lives here (§3.7) ----------
CREATE TABLE IF NOT EXISTS kb.document_versions (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  document_id     bigint NOT NULL REFERENCES kb.documents(id) ON DELETE CASCADE,
  version         int    NOT NULL,
  source_filename text   NOT NULL,
  file_sha256     char(64) NOT NULL,
  docling_version text,
  chunker_config  jsonb  NOT NULL DEFAULT '{}',  -- {max_tokens, tokenizer, merge_peers}
  page_count      int,
  image_dir       text,                          -- RELATIVE: 'stout-style-guide/'
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  is_current      boolean NOT NULL DEFAULT false, -- invisible while building (§3.7)
  UNIQUE (document_id, version),
  UNIQUE (file_sha256)                           -- same bytes never ingested twice
);
-- exactly one current version per document
CREATE UNIQUE INDEX IF NOT EXISTS document_versions_one_current_idx
  ON kb.document_versions (document_id) WHERE is_current;

CREATE TABLE IF NOT EXISTS kb.chunks (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id     bigint NOT NULL REFERENCES kb.document_versions(id) ON DELETE CASCADE,
  chunk_index    int    NOT NULL,
  content        text   NOT NULL,   -- contextualized: heading path + body (what you EMBED)
  raw_content    text   NOT NULL,   -- body only (what you SHOW)
  heading_path   text[],            -- {'Stout','Irish Stout','Vital Statistics'}
  page_from      int,
  page_to        int,
  token_count    int,
  image_refs     text[],            -- {'image_017.png'} — filenames only
  content_sha256 char(64) NOT NULL,
  fts            tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
  UNIQUE (version_id, chunk_index)
);
COMMENT ON TABLE kb.chunks IS
  'KNOWLEDGE ONLY. Never insert data derived from brew.* — see architecture rule 2.';
CREATE INDEX IF NOT EXISTS chunks_fts_idx        ON kb.chunks USING gin (fts);
CREATE INDEX IF NOT EXISTS chunks_content_sha_idx ON kb.chunks (content_sha256);
CREATE INDEX IF NOT EXISTS chunks_raw_trgm_idx    ON kb.chunks USING gin (raw_content gin_trgm_ops);

-- Keyed by model so you can A/B embedders without re-chunking (§3.2) ---------
CREATE TABLE IF NOT EXISTS kb.chunk_embeddings (
  chunk_id   bigint NOT NULL REFERENCES kb.chunks(id) ON DELETE CASCADE,
  model      text   NOT NULL,          -- 'bge-m3'
  embedding  vector(1024) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chunk_id, model)
);
CREATE INDEX IF NOT EXISTS chunk_embeddings_hnsw_idx
  ON kb.chunk_embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Ingest audit log (§6.3): every drop logged with a reason -------------------
CREATE TABLE IF NOT EXISTS kb.ingest_log (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_id bigint REFERENCES kb.document_versions(id) ON DELETE CASCADE,
  stage      text NOT NULL,
  level      text NOT NULL CHECK (level IN ('info','warn','error')),
  message    text NOT NULL,
  detail     jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Promote a version to current, but only once it is fully embedded (§11.1 D16)
-- The clear and the set must be separate statements: document_versions_one_current_idx
-- is a partial unique index, and a single UPDATE (or a data-modifying CTE) that
-- flips both rows trips it on the transient double-current state.
CREATE OR REPLACE FUNCTION kb.promote_version(p_version_id bigint)
RETURNS TABLE (version_id bigint, is_current boolean, total bigint, missing bigint)
LANGUAGE plpgsql AS $$
DECLARE
  v_doc     bigint;
  v_total   bigint;
  v_missing bigint;
BEGIN
  SELECT v.document_id INTO v_doc
  FROM kb.document_versions v WHERE v.id = p_version_id;
  IF v_doc IS NULL THEN
    RAISE EXCEPTION 'kb.promote_version: no such version %', p_version_id;
  END IF;

  SELECT count(*), count(*) FILTER (WHERE e.chunk_id IS NULL)
    INTO v_total, v_missing
  FROM kb.chunks c
  LEFT JOIN kb.chunk_embeddings e ON e.chunk_id = c.id AND e.model = 'bge-m3'
  WHERE c.version_id = p_version_id;

  IF v_total > 0 AND v_missing = 0 THEN
    UPDATE kb.document_versions v SET is_current = false
    WHERE v.document_id = v_doc AND v.id <> p_version_id AND v.is_current;

    UPDATE kb.document_versions v SET is_current = true
    WHERE v.id = p_version_id AND NOT v.is_current;
  END IF;

  RETURN QUERY
  SELECT v.id, v.is_current, v_total, v_missing
  FROM kb.document_versions v WHERE v.id = p_version_id;
END;
$$;
