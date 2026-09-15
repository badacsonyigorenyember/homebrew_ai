-- =============================================================================
-- 60_obs.sql  ·  Observability, prompt registry and model profiles
--                (plans/agent/00-orchestrator-architecture.md §3.6)
--
-- Writes reach this schema ONLY through the SECURITY DEFINER functions below,
-- granted to mem_writer. n8n_agent gets nothing here — it stays read-only on
-- nlq, and the §3.4 deterministic-fetch guarantee depends on that staying true.
--
-- Prompts live in obs.prompts, not in n8n node parameters: the deployed prompt
-- is a queryable row with a hash, so a scored regression has a diffable cause.
-- Requires pgcrypto (00_extensions.sql) for digest().
-- Idempotent.
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS obs;

CREATE TABLE IF NOT EXISTS obs.prompts (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name       text NOT NULL,                 -- 'brainstorm.pairing/propose'
  version    int  NOT NULL,
  body       text NOT NULL,
  sha256     char(64) NOT NULL,
  active     boolean NOT NULL DEFAULT false,
  notes      text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (name, version)
);
CREATE UNIQUE INDEX IF NOT EXISTS prompts_one_active_idx
  ON obs.prompts (name) WHERE active;

-- The hash is computed, never typed. A hand-written hash is a hash that is wrong.
CREATE OR REPLACE FUNCTION obs.f_prompt_hash() RETURNS trigger
LANGUAGE plpgsql AS $fn$
BEGIN
  NEW.sha256 := encode(digest(NEW.body, 'sha256'), 'hex');
  RETURN NEW;
END $fn$;

DROP TRIGGER IF EXISTS prompts_hash_trg ON obs.prompts;
CREATE TRIGGER prompts_hash_trg
  BEFORE INSERT OR UPDATE OF body ON obs.prompts
  FOR EACH ROW EXECUTE FUNCTION obs.f_prompt_hash();

CREATE TABLE IF NOT EXISTS obs.profiles (
  name    text PRIMARY KEY,                 -- 'creative'
  model   text NOT NULL,
  options jsonb NOT NULL DEFAULT '{}',      -- temperature, top_p, num_ctx, keep_alive
  notes   text
);

CREATE TABLE IF NOT EXISTS obs.runs (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id  text NOT NULL,
  turn_no     int,
  capability  text NOT NULL,
  status      text NOT NULL DEFAULT 'running'
              CHECK (status IN ('running','ok','budget_exceeded','failed','refused')),
  budget      jsonb NOT NULL DEFAULT '{}',
  spent       jsonb,
  started_at  timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz
);

CREATE TABLE IF NOT EXISTS obs.steps (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id        bigint NOT NULL REFERENCES obs.runs(id) ON DELETE CASCADE,
  seq           int NOT NULL,
  step_id       text NOT NULL,
  kind          text NOT NULL CHECK (kind IN ('llm','sql','code','http')),
  profile       text,
  model         text,
  model_loaded  boolean,                    -- was this step's model already resident?
  prompt_sha256 char(64),
  input         jsonb,
  output        jsonb,
  verdict       text,
  tokens_in     int,
  tokens_out    int,
  latency_ms    int,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (run_id, seq)
);
CREATE INDEX IF NOT EXISTS steps_run_idx ON obs.steps (run_id, seq);

-- ---------------------------------------------------------------------------
-- The only write path. SECURITY DEFINER so mem_writer needs no table grants —
-- the same pattern 40_nlq.sql already uses for the agent's read surface.
-- ---------------------------------------------------------------------------

-- One call returns the profile AND the active prompt: two round trips would let
-- the pair drift, and the pair is what obs.steps.prompt_sha256 pins.
CREATE OR REPLACE FUNCTION obs.f_step_config(p_profile text, p_prompt_name text)
RETURNS TABLE (model text, options jsonb, body text, sha256 char(64))
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = obs, public AS $fn$
  SELECT pf.model, pf.options, pr.body, pr.sha256
  FROM obs.profiles pf
  LEFT JOIN obs.prompts pr ON pr.name = p_prompt_name AND pr.active
  WHERE pf.name = p_profile
$fn$;

CREATE OR REPLACE FUNCTION obs.f_start_run(
  p_session_id text, p_turn_no int, p_capability text, p_budget jsonb)
RETURNS bigint
LANGUAGE sql SECURITY DEFINER SET search_path = obs, public AS $fn$
  INSERT INTO obs.runs (session_id, turn_no, capability, budget)
  VALUES (p_session_id, p_turn_no, p_capability, coalesce(p_budget, '{}'::jsonb))
  RETURNING id
$fn$;

CREATE OR REPLACE FUNCTION obs.f_log_step(
  p_run_id bigint, p_seq int, p_step_id text, p_kind text,
  p_profile text, p_model text, p_model_loaded boolean, p_prompt_sha256 char(64),
  p_input jsonb, p_output jsonb, p_verdict text,
  p_tokens_in int, p_tokens_out int, p_latency_ms int)
RETURNS bigint
LANGUAGE sql SECURITY DEFINER SET search_path = obs, public AS $fn$
  INSERT INTO obs.steps (run_id, seq, step_id, kind, profile, model, model_loaded,
                         prompt_sha256, input, output, verdict,
                         tokens_in, tokens_out, latency_ms)
  VALUES (p_run_id, p_seq, p_step_id, p_kind, p_profile, p_model, p_model_loaded,
          p_prompt_sha256, p_input, p_output, p_verdict,
          p_tokens_in, p_tokens_out, p_latency_ms)
  ON CONFLICT (run_id, seq) DO NOTHING
  RETURNING id
$fn$;

CREATE OR REPLACE FUNCTION obs.f_finish_run(
  p_run_id bigint, p_status text, p_spent jsonb)
RETURNS void
LANGUAGE sql SECURITY DEFINER SET search_path = obs, public AS $fn$
  UPDATE obs.runs
     SET status = p_status, spent = p_spent, finished_at = now()
   WHERE id = p_run_id
$fn$;

-- ---------------------------------------------------------------------------
-- Grants. mem_writer gets EXECUTE on four functions and NOTHING else.
-- PUBLIC is revoked first: a function EXECUTE-able by every role would hand the
-- read-only n8n_agent a write path into obs, which is exactly what §3.4 forbids.
-- ---------------------------------------------------------------------------
REVOKE ALL ON FUNCTION obs.f_step_config(text, text)            FROM PUBLIC;
REVOKE ALL ON FUNCTION obs.f_start_run(text, int, text, jsonb)  FROM PUBLIC;
REVOKE ALL ON FUNCTION obs.f_log_step(
  bigint, int, text, text, text, text, boolean, char, jsonb, jsonb, text, int, int, int)
  FROM PUBLIC;
REVOKE ALL ON FUNCTION obs.f_finish_run(bigint, text, jsonb)    FROM PUBLIC;

GRANT USAGE ON SCHEMA obs TO mem_writer;
GRANT EXECUTE ON FUNCTION obs.f_step_config(text, text)           TO mem_writer;
GRANT EXECUTE ON FUNCTION obs.f_start_run(text, int, text, jsonb) TO mem_writer;
GRANT EXECUTE ON FUNCTION obs.f_log_step(
  bigint, int, text, text, text, text, boolean, char, jsonb, jsonb, text, int, int, int)
  TO mem_writer;
GRANT EXECUTE ON FUNCTION obs.f_finish_run(bigint, text, jsonb)   TO mem_writer;

-- mem.chat_turns is not function-gated, and WF4's `Log turn` node writes it
-- directly under mem_writer. 50_roles.sql grants mem_writer USAGE on mem but no
-- table privileges, so without this the turn log fails on every turn.
GRANT SELECT, INSERT ON mem.chat_turns TO mem_writer;

-- =============================================================================
-- Seed: model profiles. All gemma4:12b through 4.9 (plan 01 §5.3) — one model
-- per run is standing rule 2, and the creative slot only splits off at 4.10.
-- =============================================================================
INSERT INTO obs.profiles (name, model, options, notes) VALUES
  ('extract',  'gemma4:12b',
     '{"temperature":0,   "num_ctx":8192,  "keep_alive":"30m"}', 'text->struct, t=0'),
  ('creative', 'gemma4:12b',
     '{"temperature":0.85,"top_p":0.95,"num_ctx":12288,"keep_alive":"30m"}', 'draft, brainstorm'),
  ('critique', 'gemma4:12b',
     '{"temperature":0,   "num_ctx":12288,"keep_alive":"30m"}', 'revise against violations'),
  ('compose',  'gemma4:12b',
     '{"temperature":0.3, "num_ctx":12288,"keep_alive":"30m"}', 'the prose the user reads')
ON CONFLICT (name) DO UPDATE
  SET model = EXCLUDED.model, options = EXCLUDED.options, notes = EXCLUDED.notes;

-- =============================================================================
-- Seed: prompts for brainstorm.pairing. The body appears once — the trigger
-- computes the hash. ON CONFLICT DO NOTHING so a hand-edited row survives a
-- restart; bump `version` and flip `active` to deploy a new one.
-- =============================================================================
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('brainstorm.pairing/parse', 1, $body$
Extract structured search terms from a brewing question. Output JSON only, no prose.

Question:
{{question}}

Fields:
- anchor_ingredient: the single ingredient, hop, malt, yeast or adjunct the question centres
  on. If no ingredient is named, use the clearest brewing subject instead.
- style_context: the beer style or beer type mentioned, or "" if none is mentioned.
- direction: one of "pairing", "substitution", "usage", "general".

Do not add fields. Do not explain.
$body$, true, 'v1 initial'),

('brainstorm.pairing/propose', 1, $body$
You are an experienced brewer helping a peer think out loud. Suggest options; do not
write a recipe and do not state any number as fact.

The question asked:
{{question}}

Anchor: {{anchor}}
Style context: {{style_context}}

Passages from the brewer's library:
{{passages}}

Propose up to 6 candidates that directly answer the question asked.

⛔ Every candidate must be the SAME KIND OF THING the question asks for. If the question
asks which hops, every candidate must be a named hop variety. If it asks which malts,
every candidate must be a named malt. A technique, a piece of equipment or a general
principle is NOT an answer to "which hops" — leave it out.

⛔ Do not pad. Returning one candidate that answers the question is correct. Returning
an empty list is correct when the passages contain no answer of the right kind. Never
add a candidate merely to reach a count, and never substitute adjacent advice for an
answer you do not have.

For each candidate:
- candidate: the ingredient, technique or pairing, named plainly.
- why: at most 40 words. Say what it does, not that it is popular.
- cites: an array of the passage labels ("S1", "S2", ...) that support the claim in
  "why". Use the label exactly as it appears in square brackets above. Never write a
  chunk_id here, and never write a label that does not appear above.

If you believe in a candidate that nothing above supports, still return it with cites: [].
An honest empty list is correct; an invented label is not.

Output JSON only.
$body$, true, 'v1 initial'),

('brainstorm.pairing/compose', 1, $body$
Write the answer for the brewer.

Their question:
{{question}}

Supported by their library — cite each of these with its label:
{{grounded}}

Your own suggestions, NOT supported by their library:
{{suggested}}

Source list — the ONLY document titles you may print:
{{sources}}

Rules:
- Lead with the answer. No preamble, no "great question".
- ⛔ Write ONLY from the two lists above. You may rephrase them; you may not add to
  them. Every candidate you mention must appear in one of the lists verbatim in
  substance. Adding an ingredient, technique or tip of your own is a failure, even a
  correct one.
- ⛔ Answer only what was asked. Do not append adjacent advice, background, caveats
  or "you might also consider" material. If the question asks which hops, do not
  discuss equipment, process or malt unless the listed candidates are about those.
- Mark every claim from a supported candidate with its [S..] label inline.
- Put unsupported suggestions under a final section headed exactly:
  "Not from your library — my own suggestions:"
  Never mix them with cited claims.
- ⛔ If the unsupported list reads "none", that section MUST NOT appear at all. Do not
  create it, and do not populate it from your own knowledge.
- ⛔ If the supported list also reads "none", write exactly one sentence saying the
  brewer's library does not cover this, and stop. Add nothing else.
- End with a Sources block, copied verbatim from the source list above, keeping
  only the lines whose label you actually cited. Never invent a document title
  and never print a placeholder such as <document>. If you cited nothing, omit
  the Sources block entirely.
- English. Metric: litres, °C, g/L. Gravity to three decimals. IBU whole numbers.
- Quote ranges as the source states them. Never average a range.
- Direct and technical. This brewer is experienced.
$body$, true, 'v1 initial')
ON CONFLICT (name, version) DO NOTHING;

-- =============================================================================
-- v2 — the web arm (§3.4.1). `propose` may now be handed [W..] passages that came
-- from the web rather than the library, and `compose` gets them as their own
-- bucket so it cannot present them as library-backed.
--
-- Why a bucket and not just a label: compose's v1 contract is "Supported by their
-- library — cite each of these", and putting a web passage in that list makes
-- every downstream sentence a lie about provenance. The separation is the point.
-- =============================================================================
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('brainstorm.pairing/propose', 2, $body$
You are an experienced brewer helping a peer think out loud. Suggest options; do not
write a recipe and do not state any number as fact.

The question asked:
{{question}}

Anchor: {{anchor}}
Style context: {{style_context}}

Passages from the brewer's library:
{{passages}}

⚠️ Some passages may be marked "(from the WEB, not the library)" and labelled [W1],
[W2], ... The brewer's library does not contain them. Cite them exactly as you cite
library passages — they are real evidence you were shown — but never describe them as
coming from the brewer's books.

Propose up to 6 candidates that directly answer the question asked.

⛔ Every candidate must be the SAME KIND OF THING the question asks for. If the question
asks which hops, every candidate must be a named hop variety. If it asks which malts,
every candidate must be a named malt. A technique, a piece of equipment or a general
principle is NOT an answer to "which hops" — leave it out.

⛔ Do not pad. Returning one candidate that answers the question is correct. Returning
an empty list is correct when the passages contain no answer of the right kind. Never
add a candidate merely to reach a count, and never substitute adjacent advice for an
answer you do not have.

For each candidate:
- candidate: the ingredient, technique or pairing, named plainly.
- why: at most 40 words. Say what it does, not that it is popular.
- cites: an array of the passage labels ("S1", "W1", ...) that support the claim in
  "why". Use the label exactly as it appears in square brackets above. Never write a
  chunk_id here, and never write a label that does not appear above.

If you believe in a candidate that nothing above supports, still return it with cites: [].
An honest empty list is correct; an invented label is not.

Output JSON only.
$body$, false, 'v2 — [W..] web passages are citable'),

('brainstorm.pairing/compose', 2, $body$
Write the answer for the brewer.

Their question:
{{question}}

Supported by their library — cite each of these with its label:
{{grounded}}

Found on the web, NOT in their library — cite each of these with its [W..] label:
{{web}}

Your own suggestions, supported by neither:
{{suggested}}

Source list — the ONLY document titles and URLs you may print:
{{sources}}

Rules:
- Lead with the answer. No preamble, no "great question".
- ⛔ Write ONLY from the three lists above. You may rephrase them; you may not add to
  them. Every candidate you mention must appear in one of the lists verbatim in
  substance. Adding an ingredient, technique or tip of your own is a failure, even a
  correct one.
- ⛔ Answer only what was asked. Do not append adjacent advice, background, caveats
  or "you might also consider" material. If the question asks which hops, do not
  discuss equipment, process or malt unless the listed candidates are about those.
- Mark every claim from a supported candidate with its [S..] label inline.
- ⛔ Web candidates are marked with [W..] labels. Keep those labels exactly — never
  renumber a [W..] as an [S..] — and say in plain words that this part came from the
  web and is not in the brewer's library. Put them under a section headed exactly:
  "From the web — not in your library:"
- ⛔ If the web list reads "none", that section MUST NOT appear at all.
- Put unsupported suggestions under a final section headed exactly:
  "Not from your library — my own suggestions:"
  Never mix them with cited claims.
- ⛔ If the unsupported list reads "none", that section MUST NOT appear at all. Do not
  create it, and do not populate it from your own knowledge.
- ⛔ If all three lists read "none", write exactly one sentence saying the brewer's
  library does not cover this, and stop. Add nothing else.
- End with a Sources block, copied verbatim from the source list above, keeping
  only the lines whose label you actually cited. Never invent a document title
  and never print a placeholder such as <document>. If you cited nothing, omit
  the Sources block entirely.
- English. Metric: litres, °C, g/L. Gravity to three decimals. IBU whole numbers.
- Quote ranges as the source states them. Never average a range.
- Direct and technical. This brewer is experienced.
$body$, false, 'v2 — web bucket, [W..] never renumbered as [S..]')
ON CONFLICT (name, version) DO NOTHING;

-- ⛔ Two statements, not one: prompts_one_active_idx is a partial unique index on
-- (name) WHERE active, and a single UPDATE flipping both rows trips it on the
-- transient double-active state -- the same trap kb.promote_version documents.
UPDATE obs.prompts SET active = false
 WHERE name IN ('brainstorm.pairing/propose', 'brainstorm.pairing/compose')
   AND version <> 2 AND active;
UPDATE obs.prompts SET active = true
 WHERE name IN ('brainstorm.pairing/propose', 'brainstorm.pairing/compose')
   AND version = 2 AND NOT active;


-- =============================================================================
-- Retrieval trace — the fix for the empty mem.chat_turns.chunk_ids column.
-- `Prep turn` cannot recover the ids: the tool hands the model mode 'text', and
-- that string carries no chunk_id by design — putting them there would roughly
-- double the retrieval token budget and bury the [S..] labels the citation
-- contract depends on. So the retriever records its own trace instead, keyed by
-- session, and `Log turn` joins it. This also captures retrievals made inside a
-- capability, which `Prep turn` can never see.
-- =============================================================================
CREATE TABLE IF NOT EXISTS obs.retrievals (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id text,
  query      text NOT NULL,
  chunk_ids  bigint[] NOT NULL DEFAULT '{}',
  top_k      int,
  mode       text,
  -- Words in the question that the corpus vocabulary has never seen, after the
  -- typo/locale and off-domain guards in nlq.corpus_vocabulary_gap. Logged, and
  -- for now ONLY logged: it is the evidence that decides whether a web-search
  -- fallback is worth building, and the thresholds that produced it were fitted
  -- to 15 hand-picked terms. `query` is stored beside it, so any future threshold
  -- can be replayed over this table offline.
  gap_terms  text[] NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

-- The table predates gap_terms in every already-running volume, and this file is
-- re-applied rather than migrated.
ALTER TABLE obs.retrievals
  ADD COLUMN IF NOT EXISTS gap_terms text[] NOT NULL DEFAULT '{}';

-- `Log turn` reads the newest trace for a session, so this is the access path.
CREATE INDEX IF NOT EXISTS retrievals_session_created_idx
  ON obs.retrievals (session_id, created_at DESC);

-- p_gap_terms is trailing and defaulted so the argument stays optional, but the
-- 5-arg form MUST go: leaving it behind would make every 5-argument call
-- ambiguous against the defaulted 6-arg one. Same reasoning as the two DROPs in
-- front of nlq.search_knowledge.
DROP FUNCTION IF EXISTS obs.f_log_retrieval(text, text, bigint[], int, text);

CREATE OR REPLACE FUNCTION obs.f_log_retrieval(
  p_session_id text, p_query text, p_chunk_ids bigint[], p_top_k int, p_mode text,
  p_gap_terms text[] DEFAULT '{}')
RETURNS bigint
LANGUAGE sql SECURITY DEFINER SET search_path = obs, public AS $fn$
  INSERT INTO obs.retrievals (session_id, query, chunk_ids, top_k, mode, gap_terms)
  VALUES (nullif(p_session_id, ''), p_query,
          coalesce(p_chunk_ids, '{}'::bigint[]), p_top_k, p_mode,
          coalesce(p_gap_terms, '{}'::text[]))
  RETURNING id
$fn$;

REVOKE ALL ON FUNCTION obs.f_log_retrieval(text, text, bigint[], int, text, text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION obs.f_log_retrieval(text, text, bigint[], int, text, text[]) TO mem_writer;

-- `Log turn` runs as mem_writer, which holds no table privileges anywhere in obs.
-- Same SECURITY DEFINER pattern as the rest of this file: the join it needs is a
-- function, not a grant. p_since bounds the lookup to the turn that is being
-- logged, so a later turn never inherits an earlier turn's chunk_ids.
CREATE OR REPLACE FUNCTION obs.f_session_chunk_ids(
  p_session_id text, p_since timestamptz)
RETURNS bigint[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = obs, public AS $fn$
  SELECT coalesce(
    (SELECT r.chunk_ids
       FROM obs.retrievals r
      WHERE r.session_id = p_session_id
        AND r.created_at >= p_since
      ORDER BY r.created_at DESC
      LIMIT 1),
    '{}'::bigint[])
$fn$;

REVOKE ALL ON FUNCTION obs.f_session_chunk_ids(text, timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION obs.f_session_chunk_ids(text, timestamptz) TO mem_writer;
