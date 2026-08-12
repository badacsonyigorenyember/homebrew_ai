-- =============================================================================
-- 50_roles.sql  ·  Read-only enforcement, Layer 1 (architecture §8.4)
-- The agent's DB credential gets rights on nlq and NOTHING else. A separate
-- writer credential gets EXECUTE on mem.f_save_memory only.
--
-- ⛔ THIS IS A psql SCRIPT, NOT PORTABLE SQL. Do not paste it into Supabase
--    Studio or any other SQL client: `\gexec` is a psql meta-command and
--    `:'agent_pw'` is a psql client-side variable. Both are syntax errors to
--    the server. Run it with:  docker compose up db-init
--
-- Passwords are injected by the migration runner via psql variables:
--   psql -v agent_pw='...' -v mem_pw='...' -f 50_roles.sql
-- Idempotent (safe to re-run; passwords are refreshed each run).
--
-- Reminder for anyone debugging a "permission denied for schema kb" in n8n:
-- that is this file working. n8n_agent is the READ-ONLY agent login and reaches
-- nlq only. Ingest and any other writer must use the schema-owning credential.
-- =============================================================================

-- 1) Group role: read-only, no login -----------------------------------------
SELECT 'CREATE ROLE agent_ro NOLOGIN'
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'agent_ro')\gexec

-- 2) Lock down the private schemas: the agent must never see kb/brew/ref/mem ---
--    ref is reference data, but it is still reached only through nlq (D32).
REVOKE ALL ON SCHEMA kb, brew, ref, mem FROM PUBLIC;

-- 3) The only surface the agent may touch -------------------------------------
GRANT USAGE  ON SCHEMA nlq TO agent_ro;
GRANT SELECT   ON ALL TABLES    IN SCHEMA nlq TO agent_ro;   -- views only
GRANT EXECUTE  ON ALL FUNCTIONS IN SCHEMA nlq TO agent_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA nlq GRANT SELECT  ON TABLES    TO agent_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA nlq GRANT EXECUTE ON FUNCTIONS TO agent_ro;

-- 4) The login role n8n uses for read tools -----------------------------------
SELECT 'CREATE ROLE n8n_agent LOGIN'
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'n8n_agent')\gexec
ALTER ROLE n8n_agent WITH LOGIN PASSWORD :'agent_pw';
GRANT agent_ro TO n8n_agent;
ALTER ROLE n8n_agent SET default_transaction_read_only = on;  -- even injected DELETE errors
ALTER ROLE n8n_agent SET statement_timeout = '10s';           -- caps a pathological query

-- 5) The learning-layer writer: EXECUTE on mem.f_save_memory ONLY (§8.4) -------
--    Physically cannot read your batches; the read role physically cannot write.
SELECT 'CREATE ROLE mem_writer LOGIN'
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mem_writer')\gexec
ALTER ROLE mem_writer WITH LOGIN PASSWORD :'mem_pw';
GRANT USAGE ON SCHEMA mem TO mem_writer;
GRANT EXECUTE ON FUNCTION
  mem.f_save_memory(text, text, numeric, bigint, bigint, text) TO mem_writer;
ALTER ROLE mem_writer SET statement_timeout = '10s';
