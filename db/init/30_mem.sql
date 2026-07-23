-- =============================================================================
-- 30_mem.sql  ·  Agent memory schema (architecture §7.6, §9)
-- Chat turns for analytics/eval + durable memories with a SEPARATE vector space.
-- mem.memory_embeddings is NEVER fused with kb.chunk_embeddings (§9.3) — a
-- preference must never outrank a book on a knowledge question.
-- Idempotent.
-- =============================================================================

-- Structured turn log (parallel to n8n's opaque LangChain memory blob) -------
-- tool_calls + chunk_ids are what make tool-selection accuracy and retrieval
-- hit-rate computable from real traffic (§7.6, §10.2).
CREATE TABLE IF NOT EXISTS mem.chat_turns (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id text NOT NULL,
  turn_no int NOT NULL,
  role text NOT NULL CHECK (role IN ('user','assistant')),
  content text NOT NULL,
  tool_calls jsonb,          -- which tools fired, with what params
  chunk_ids bigint[],        -- what was retrieved  -> retrieval eval
  latency_ms int,
  model text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (session_id, turn_no, role)
);

-- Durable memories (§9.2) ----------------------------------------------------
CREATE TABLE IF NOT EXISTS mem.memories (
  id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  kind         text NOT NULL CHECK (kind IN
               ('preference','constraint','batch_lesson','correction','equipment')),
  content      text NOT NULL,
  batch_id     bigint REFERENCES brew.batches(id) ON DELETE SET NULL,
  confidence   numeric(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  status       text NOT NULL DEFAULT 'pending'
               CHECK (status IN ('pending','active','superseded','rejected')),
  supersedes   bigint REFERENCES mem.memories(id),
  source_turn  bigint REFERENCES mem.chat_turns(id),
  content_sha256 char(64) NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  confirmed_at timestamptz,
  UNIQUE (content_sha256, kind)          -- never store the same fact twice
);
CREATE INDEX IF NOT EXISTS memories_kind_status_idx ON mem.memories (kind, status);

-- SEPARATE vector space. Never joined with kb.chunk_embeddings (§9.3) --------
CREATE TABLE IF NOT EXISTS mem.memory_embeddings (
  memory_id bigint PRIMARY KEY REFERENCES mem.memories(id) ON DELETE CASCADE,
  model     text NOT NULL,
  embedding vector(1024) NOT NULL
);
CREATE INDEX IF NOT EXISTS memory_embeddings_hnsw_idx
  ON mem.memory_embeddings USING hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- mem.f_save_memory (§7.3, §9.4) — the ONLY write surface for the learning
-- layer. SECURITY DEFINER so the mem_writer role needs no table grants.
-- Corrections write active immediately and supersede the prior fact; everything
-- else lands per the caller-supplied status (WF5 applies the confidence gate).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION mem.f_save_memory(
  p_kind        text,
  p_content     text,
  p_confidence  numeric,
  p_batch_id    bigint DEFAULT NULL,
  p_source_turn bigint DEFAULT NULL,
  p_status      text   DEFAULT 'pending'
) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = mem, public AS $$
DECLARE
  v_sha    char(64) := encode(digest(lower(trim(p_content)), 'sha256'), 'hex');
  v_status text     := CASE WHEN p_kind = 'correction' THEN 'active' ELSE p_status END;
  v_id     bigint;
BEGIN
  -- A correction supersedes any prior active memory of the same kind/content family.
  IF p_kind = 'correction' THEN
    UPDATE mem.memories SET status = 'superseded'
    WHERE kind = 'correction' AND status = 'active';
  END IF;

  INSERT INTO mem.memories (kind, content, batch_id, confidence, status,
                            source_turn, content_sha256,
                            confirmed_at)
  VALUES (p_kind, p_content, p_batch_id, p_confidence, v_status,
          p_source_turn, v_sha,
          CASE WHEN v_status = 'active' THEN now() END)
  ON CONFLICT (content_sha256, kind) DO UPDATE
     SET confidence = greatest(mem.memories.confidence, EXCLUDED.confidence)
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$;
