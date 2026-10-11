-- kb: book chunks with embeddings for retrieval. A book is a row in ref.source (file_path).
-- From docs/DATABASE-REVIEW.md §5.4. kb.chunk starts empty; P7 fills it.
-- Needs db/010_ref_schema.sql applied first.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/014_kb.sql
-- Idempotent: safe to re-run.

-- vector is a supautils privileged extension, so postgres may create it.
create extension if not exists vector with schema extensions;

create schema if not exists kb;
alter table ref.source add column if not exists file_path text;   -- book file, if any

create table if not exists kb.chunk (
    id           bigint generated always as identity primary key,
    source_id    bigint not null references ref.source (id),
    section_path text   not null,
    page         integer,
    text         text   not null,
    tokens       integer not null,
    embedding    extensions.vector(1024) not null,     -- bge-m3
    fts          tsvector generated always as (to_tsvector('english', text)) stored
);
create index if not exists chunk_source_id_idx on kb.chunk (source_id);
create index if not exists chunk_embedding_idx on kb.chunk using hnsw (embedding extensions.vector_cosine_ops);
create index if not exists chunk_fts_idx       on kb.chunk using gin (fts);
