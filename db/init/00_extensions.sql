-- =============================================================================
-- 00_extensions.sql  ·  Homebrewing Assistant foundation
-- Architecture §3. Four schemas as a security boundary, not decoration.
-- Runs against the SUPABASE Postgres (the app database), NOT the n8n metadata DB.
-- Idempotent: safe to re-run.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector: HNSW + <=> cosine distance
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- fuzzy fallback (gin_trgm_ops)
CREATE EXTENSION IF NOT EXISTS unaccent;  -- accent-insensitive matching
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- digest() for content_sha256 helpers

CREATE SCHEMA IF NOT EXISTS kb;    -- knowledge : what the books say
CREATE SCHEMA IF NOT EXISTS brew;  -- truth     : what I actually did
CREATE SCHEMA IF NOT EXISTS mem;   -- memory    : what I've learned about you
CREATE SCHEMA IF NOT EXISTS nlq;   -- the ONLY surface the agent may touch
