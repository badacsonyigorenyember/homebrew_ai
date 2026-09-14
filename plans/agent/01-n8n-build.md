# Plan 01 — building the agent architecture in n8n, node by node

**Written:** 2026-08-19 · **Status:** ✅ ⭐ **built 2026-08-20, gated and recorded 2026-09-14** — see [`03-record.md`](03-record.md) · **Covers:** phases **4.5, 4.6 and 4.7** of
[`00-orchestrator-architecture.md`](00-orchestrator-architecture.md) §8 — the chat agent, the step
engine, and the first capability.

**Out of scope, deliberately:** `ref.ingredients` and the math functions (4.8), `recipe.create`
(4.9), multi-model (4.10), web (4.11), OpenWebUI (5.0, deferred by your decision).

---

## §0 — The verdict, in one screen

**Six artifacts get built, in this order. Three of them already have complete specs you are
reusing rather than rewriting.**

| # | Artifact | Kind | Source |
|---|---|---|---|
| 1 | `db/init/60_obs.sql` | schema | ⭐ new — §2.1. ⛔ **and one line in `docker-compose.yml`** |
| 2 | `tool-search-brewing-knowledge` | n8n sub-workflow | ✅ **already fully specified** — [`../archive/phase2/03a-tool-subworkflows.md`](../archive/phase2/03a-tool-subworkflows.md) §1, six nodes, D26b-corrected. **Build it verbatim** |
| 3 | `chat-agent` (WF4) | n8n workflow | 🟡 **five nodes exist** in `backup/wf4-chat-agent-systemprompt-v3.json`. Import, then make the three changes in §2.4 |
| 4 | `wf-step-llm` | n8n sub-workflow | ⭐ new — §2.5. **The engine. Everything later depends on it** |
| 5 | `cap-brainstorm-pairing` | n8n sub-workflow | ⭐ new — §2.6 |
| 6 | the tool binding on WF4 | node | §2.7 |

⭐ **The single most important structural rule in this plan:** `wf-step-llm` is the **engine** and
capabilities are **launchers**, exactly as `wf1-ingest-book` is the engine and `ingest-malt` is a
launcher. ⛔ **If building capability #2 requires editing `wf-step-llm`, stop — the engine is
wrong.** That test is what made books 2, 3 and 4 cost zero new nodes.

**On models, answered in full in §5:** ⛔ **stay on `gemma4:12b` for the agent, and do not change
it in this plan.** The bigger models belong in the **creative slot at 4.10**, as a scored A/B —
and one of the two you named is a much better fit than the other for reasons that are not about
size.

---

## §1 — Prerequisites

### 1.1 What is already true — measured 2026-08-19

| Check | Command | Result |
|---|---|---|
| Corpus is retrievable | `select count(*) from kb.chunks` | **2,090**, 0 embedding gaps |
| `nlq.search_knowledge` | `pg_proc` | ✅ exists, `SECURITY DEFINER` |
| Read-only role | `50_roles.sql` | ✅ `n8n_agent` — `nlq` USAGE only, `default_transaction_read_only=on`, `statement_timeout=10s` |
| Write role | `50_roles.sql` | ✅ `mem_writer` — USAGE on `mem`, EXECUTE on one function, `statement_timeout=10s` |
| Ollama | `/api/tags` | `gemma4:12b` 7.6 GB · `bge-m3` 1.2 GB. Ollama **0.30.6** |
| ⭐ VRAM | `/sys/class/drm/card1/device/mem_info_vram_total` | ⭐ **16,304 MB total, 1,312 MB already in use by the desktop** → ⛔ **~14.9 GB usable** |
| n8n | `n8n --version` | **2.23.4** |
| ⛔ Conversational surface | `n8n list:workflow` | ⛔ **8 workflows, all ingest. No agent, no tool** |
| ⛔ `obs` schema | `information_schema.tables` | ⛔ **does not exist** |

### 1.2 What must be done first

1. ⛔ **The read-only Postgres credential in n8n.** [`03a`](../archive/phase2/03a-tool-subworkflows.md) §0.1 specifies it: host `db`, user `n8n_agent`, password `AGENT_DB_PASSWORD` from `.env`. ⭐ **Verify it with 03a §0.2's 30-second sanity check before building anything** — a wrong credential here surfaces as a retrieval bug three nodes later.
2. ⭐ **A second Postgres credential for `mem_writer`.** New requirement in this plan: `n8n_agent` **cannot write to `obs`** and must not be given the ability. §2.1 grants `mem_writer` EXECUTE on three `SECURITY DEFINER` functions and nothing else.
3. ⛔ **Run compose from the main checkout, never a worktree.** No `.env` there, and the project name changes.

⚠️ **`supabase-pooler` is in a restart loop.** Nothing here uses it. Reported, not fixed.

---

## §2 — The build

### 2.1 `db/init/60_obs.sql` — and the line that makes it actually run

⛔ **The trap, first.** `db-init` does **not** glob. Its command carries an explicit file list with
its own comment saying so:

> *"this list is the execution order and it does NOT glob. A new `db/init/*.sql` file silently
> never runs until its name is added here."*

⭐ **So this is a two-file change.** Add `60_obs.sql`, **and** add it to the loop in
`docker-compose.yml` (after `40_nlq.sql`, before the separate `50_roles.sql` call):

```
        for f in /db-init/00_extensions.sql /db-init/10_kb.sql /db-init/15_ref.sql \
                 /db-init/20_brew.sql /db-init/30_mem.sql /db-init/40_nlq.sql \
                 /db-init/60_obs.sql; do
```

⛔ **Forgetting this produces the worst failure mode in the plan:** everything appears to apply,
`db-init` exits 0, and the first workflow run fails on a missing table.

**The schema.** Tables are as specified in [`00`](00-orchestrator-architecture.md) §3.6. What is
new here is the **function surface**, because it is what keeps the write boundary intact.

```sql
-- =============================================================================
-- 60_obs.sql · Observability, prompt registry and model profiles.
-- Writes reach this schema ONLY through the three SECURITY DEFINER functions
-- below, granted to mem_writer. n8n_agent gets nothing here — it stays read-only
-- on nlq, and the §3.4 guarantee depends on that staying true.
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
  model_loaded  boolean,
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
-- the same pattern 50_roles.sql already uses for mem.f_save_memory.
-- ---------------------------------------------------------------------------

-- One call returns everything wf-step-llm needs: the profile AND the active
-- prompt. Two round trips would let the pair drift between them.
CREATE OR REPLACE FUNCTION obs.f_step_config(p_profile text, p_prompt_name text)
RETURNS TABLE (model text, options jsonb, body text, sha256 char(64))
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = obs, public AS $$
  SELECT pf.model, pf.options, pr.body, pr.sha256
  FROM obs.profiles pf
  LEFT JOIN obs.prompts pr ON pr.name = p_prompt_name AND pr.active
  WHERE pf.name = p_profile
$$;

CREATE OR REPLACE FUNCTION obs.f_start_run(
  p_session_id text, p_turn_no int, p_capability text, p_budget jsonb)
RETURNS bigint
LANGUAGE sql SECURITY DEFINER SET search_path = obs, public AS $$
  INSERT INTO obs.runs (session_id, turn_no, capability, budget)
  VALUES (p_session_id, p_turn_no, p_capability, coalesce(p_budget,'{}'::jsonb))
  RETURNING id
$$;

CREATE OR REPLACE FUNCTION obs.f_log_step(
  p_run_id bigint, p_seq int, p_step_id text, p_kind text,
  p_profile text, p_model text, p_model_loaded boolean, p_prompt_sha256 char(64),
  p_input jsonb, p_output jsonb, p_verdict text,
  p_tokens_in int, p_tokens_out int, p_latency_ms int)
RETURNS bigint
LANGUAGE sql SECURITY DEFINER SET search_path = obs, public AS $$
  INSERT INTO obs.steps (run_id, seq, step_id, kind, profile, model, model_loaded,
                         prompt_sha256, input, output, verdict,
                         tokens_in, tokens_out, latency_ms)
  VALUES (p_run_id, p_seq, p_step_id, p_kind, p_profile, p_model, p_model_loaded,
          p_prompt_sha256, p_input, p_output, p_verdict,
          p_tokens_in, p_tokens_out, p_latency_ms)
  RETURNING id
$$;

CREATE OR REPLACE FUNCTION obs.f_finish_run(
  p_run_id bigint, p_status text, p_spent jsonb)
RETURNS void
LANGUAGE sql SECURITY DEFINER SET search_path = obs, public AS $$
  UPDATE obs.runs
     SET status = p_status, spent = p_spent, finished_at = now()
   WHERE id = p_run_id
$$;

-- ---------------------------------------------------------------------------
-- Grants. mem_writer gets EXECUTE on four functions and NOTHING else.
-- ⛔ n8n_agent is deliberately absent from this file.
-- ---------------------------------------------------------------------------
GRANT USAGE ON SCHEMA obs TO mem_writer;
GRANT EXECUTE ON FUNCTION obs.f_step_config(text, text)          TO mem_writer;
GRANT EXECUTE ON FUNCTION obs.f_start_run(text, int, text, jsonb) TO mem_writer;
GRANT EXECUTE ON FUNCTION obs.f_log_step(
  bigint, int, text, text, text, text, boolean, char, jsonb, jsonb, text, int, int, int)
  TO mem_writer;
GRANT EXECUTE ON FUNCTION obs.f_finish_run(bigint, text, jsonb)   TO mem_writer;
```

⭐ **Why `f_step_config` returns the profile and the prompt in one call:** two separate queries
would let the model and the prompt drift apart between them, and the pair is what
`obs.steps.prompt_sha256` is meant to pin. One call, one snapshot.

### 2.2 Seeding profiles and prompts

⛔ **Prompts are loaded by a migration, never pasted into a node.** That is the whole point of
§3.6 — and the reason `tier1_routing.py` currently has to regex the deployed prompt out of the
n8n database's workflow JSON.

```sql
-- Profiles for 4.5–4.9. ⛔ ALL gemma4:12b. §5 explains why nothing bigger yet.
INSERT INTO obs.profiles (name, model, options, notes) VALUES
  ('extract',  'gemma4:12b',
     '{"temperature":0,   "num_ctx":8192,  "keep_alive":"5m"}', 'text->struct, t=0'),
  ('creative', 'gemma4:12b',
     '{"temperature":0.85,"top_p":0.95,"num_ctx":12288,"keep_alive":"5m"}', 'draft, brainstorm'),
  ('critique', 'gemma4:12b',
     '{"temperature":0,   "num_ctx":12288,"keep_alive":"5m"}', 'revise against violations'),
  ('compose',  'gemma4:12b',
     '{"temperature":0.3, "num_ctx":12288,"keep_alive":"5m"}', 'the prose the user reads')
ON CONFLICT (name) DO UPDATE
  SET model = EXCLUDED.model, options = EXCLUDED.options, notes = EXCLUDED.notes;

-- A prompt is inserted with its own hash computed in SQL — never typed by hand.
INSERT INTO obs.prompts (name, version, body, sha256, active, notes)
SELECT 'brainstorm.pairing/propose', 1, $prompt$
...prompt body here...
$prompt$, encode(digest($prompt$
...the identical body...
$prompt$, 'sha256'), 'hex'), true, 'initial'
ON CONFLICT (name, version) DO NOTHING;
```

⚠️ **The doubled body above is a real hazard** — two copies that must stay identical. ⭐ **Better:
insert with a NULL hash and let a trigger compute it.** Add to `60_obs.sql`:

```sql
CREATE OR REPLACE FUNCTION obs.f_prompt_hash() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.sha256 := encode(digest(NEW.body, 'sha256'), 'hex');
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS prompts_hash_trg ON obs.prompts;
CREATE TRIGGER prompts_hash_trg BEFORE INSERT OR UPDATE OF body ON obs.prompts
  FOR EACH ROW EXECUTE FUNCTION obs.f_prompt_hash();
```

⭐ **Then a prompt insert carries the body once and the hash is never wrong.** `pgcrypto` is
required — check `00_extensions.sql` and add `CREATE EXTENSION IF NOT EXISTS pgcrypto;` if absent.

### 2.3 `tool-search-brewing-knowledge` — build 03a verbatim

⛔ **Do not redesign this.** [`03a`](../archive/phase2/03a-tool-subworkflows.md) §1 is a complete
six-node spec that was built, run and measured in Phase 2, and it already carries the D26b
correction (two trigger fields, not three).

| Node | Type | Purpose |
|---|---|---|
| 1 | Execute Workflow Trigger v1.2 | fields `query` (String), `top_k` (Number). ⛔ **Two fields. Every declared field is required** |
| 2 | Code — `Normalise input` | reject empty query, discard hallucinated `doc_type`, cap `top_k` at 8 |
| 3 | HTTP Request — `Embed query` | Ollama `/api/embed`, `bge-m3` |
| 4 | Code — `Build vector` | assert 1024 dims |
| 5 | Postgres — `Search knowledge` | `nlq.search_knowledge($1,$2,$3,40,50,'bge-m3',NULLIF($4,''))`. ⛔ **Do not tune 40/50** — they are what Phase 1 was scored against |
| 6 | Code — `Shape for model` | `[S…]` markers with title · heading path · page |

⭐ **One amendment for this plan:** node 6 must return `chunk_id` alongside the shaped text.
`mem.chat_turns.chunk_ids` and `brainstorm.pairing`'s grounding step (§2.6 step 4) both need it,
and it is the column §10's retrieval-hit-rate metric is computed from.

### 2.4 `chat-agent` (WF4) — import the backup, then three changes

`backup/wf4-chat-agent-systemprompt-v3.json` holds a working five-node graph:

```
When chat message received (chatTrigger v1.4, responseMode: streaming)
  └─main→ AI Agent (agent v3.1)
              ├─ai_languageModel← Ollama Chat Model (lmChatOllama)
              ├─ai_memory←        Postgres Chat Memory (memoryPostgresChat v1.4)
              └─ai_tool←          search_brewing_knowledge (toolWorkflow v2.2)
```

⛔ **Import it, do not rebuild it** — and ⛔ **do not edit it in the browser.** Edit the tracked
JSON, `n8n import:workflow`, re-activate (import deactivates), restart n8n.

**Change 1 — de-enumerate the system prompt.** The v3 prompt says *"John Palmer's How to Brew and
the BJCP 2021 Style Guidelines"*. There are **six documents** now. Replace with the §7.1 wording:

> *"You answer from that brewer's library — a collection of brewing books, style guidelines and
> practitioner articles — not from your own memory."*

⛔ **This appears once. Nothing else in the prompt changes in this plan** — standing rule 2, and
§7.1 records that v3.1 looked strictly safer than v3 and scored **20 points worse**.

**Change 2 — `mem.chat_turns` logging.** ⛔ **Built inside WF4, not after it.** Every turn logged
before the logging exists is a turn that cannot be scored, which is why it has been deferred
since Phase 2.

- On the **AI Agent** node, enable **Return Intermediate Steps** — this is where `tool_calls` and
  the retrieved `chunk_id`s come from.
- `AI Agent` →main→ **Code `Prep turn`** → **Postgres `Log turn`** (credential: `mem_writer`).

```javascript
// Prep turn — pull tool calls and chunk ids out of the agent's intermediate steps.
const a = $input.first().json;
const steps = a.intermediateSteps ?? [];
const toolCalls = steps.map(s => ({
  tool:  s.action?.tool,
  input: s.action?.toolInput,
}));
const chunkIds = steps.flatMap(s => {
  const o = s.observation;
  const rows = typeof o === 'string' ? safeParse(o) : o;
  return Array.isArray(rows) ? rows.map(r => r.chunk_id).filter(Boolean) : [];
});
function safeParse(s) { try { return JSON.parse(s); } catch { return null; } }

return [{ json: {
  session_id: $('When chat message received').first().json.sessionId,
  content:    a.output ?? '',
  tool_calls: JSON.stringify(toolCalls),
  chunk_ids:  chunkIds,
  model:      'gemma4:12b',
}}];
```

⚠️ ⛔ **Probe this before trusting it — two unknowns, both cheap to settle and both capable of
wasting an afternoon:**

1. **Does a node downstream of the AI Agent break streaming?** §7.7 says only the Agent streams
   and *"no node between the Agent and the user"*. A logging node is *after* the streamed output
   rather than between — ⭐ **but that is an argument, not a measurement.** Send one chat message
   with the logging node wired and confirm tokens still arrive incrementally.
2. **Does `Return Intermediate Steps` coexist with streaming?** Same test, same run: check that
   `intermediateSteps` is populated when `responseMode: streaming` is set.

⛔ **If either fails, log from inside the tool sub-workflow instead** — it knows its own chunk ids
and runs off the response path entirely. Note which one you used; it changes what `tool_calls`
can record.

**Change 3 — pin the model options.** On `Ollama Chat Model`, set `num_ctx: 12288` and
`temperature: 0.2` explicitly. ⚠️ **A default that changes under you is a variable you did not
know you moved** — the same class of defect as D13/D20's Crypto node.

### 2.5 `wf-step-llm` — the engine

⭐ **The most important artifact in this plan.** One Execute Workflow node per LLM step for every
capability, forever. Build it once, correctly.

**Trigger fields** — six, all required (D26b), all supplied by a *workflow* rather than a model,
so "required" costs nothing here:

| Field | Type | Example |
|---|---|---|
| `run_id` | Number | `41` |
| `seq` | Number | `3` |
| `step_id` | String | `propose` |
| `profile` | String | `creative` |
| `prompt_name` | String | `brainstorm.pairing/propose` |
| `vars_json` | String | `{"anchor":"Nelson Sauvin","passages":"[S1] …"}` |
| `schema_json` | String | `''` for free prose, or a JSON Schema |

| # | Node | Type | Why it exists |
|---|---|---|---|
| 1 | `When Executed by Another Workflow` | Execute Workflow Trigger v1.2 | the contract |
| 2 | `Load config` | Postgres (`mem_writer`) | `SELECT * FROM obs.f_step_config($1,$2)` with `[profile, prompt_name]`. ⭐ **One call: model, options, prompt body and hash together, so they cannot drift** |
| 3 | `Render prompt` | Code | substitute `{{var}}` from `vars_json` into the body; ⛔ **throw on an unresolved placeholder** rather than sending `{{anchor}}` to the model |
| 4 | `Check residency` | HTTP Request | `GET http://ollama:11434/api/ps`. ⭐ Feeds `model_loaded` — without it the first profile change reads as a step regression rather than a load (§3.3) |
| 5 | `Call Ollama` | HTTP Request | `POST /api/chat`. ⛔ **Timeout 600000 ms** — the default will kill a long generation, and killing it is the *one* thing your latency tolerance does not permit. **Retry On Fail: 2, 5 s apart** |
| 6 | `Validate output` | Code | if `schema_json` is non-empty, parse and assert required keys; throw with the offending payload in the message |
| 7 | `Log step` | Postgres (`mem_writer`) | `obs.f_log_step(...)` |
| 8 | `Return` | Code | `{ output, prompt_sha256, latency_ms, tokens_in, tokens_out }` |

⛔ **Linear chain, no branches** (D15 — n8n v1 orders parallel branches by *node position*, not
data dependency, and that defect cost this project a re-ingest).

**Node 3 — `Render prompt`:**

```javascript
const cfg  = $('Load config').first().json;
const inp  = $('When Executed by Another Workflow').first().json;

if (!cfg.model)  throw new Error(`No obs.profiles row for profile '${inp.profile}'`);
if (!cfg.body)   throw new Error(`No ACTIVE obs.prompts row named '${inp.prompt_name}'`);

const vars = JSON.parse(inp.vars_json || '{}');
let body = cfg.body.replace(/\{\{(\w+)\}\}/g, (m, k) => {
  if (!(k in vars)) throw new Error(`Prompt '${inp.prompt_name}' needs {{${k}}}, not supplied`);
  return String(vars[k]);
});

const schema = (inp.schema_json || '').trim();

return [{ json: {
  model:    cfg.model,
  options:  cfg.options,
  messages: [{ role: 'user', content: body }],
  format:   schema ? JSON.parse(schema) : undefined,   // Ollama structured output
  stream:   false,
  sha256:   cfg.sha256,
  started:  Date.now(),
}}];
```

⭐ **`format` is Ollama's structured-output parameter** and it does the schema enforcement in the
sampler rather than in a retry loop. ⚠️ **Confirm it behaves on 0.30.6 with `gemma4:12b` before
relying on it** — if it does not, node 6 becomes a retry loop and the step budget absorbs it.

**Node 5 — `Call Ollama`, body:**

```
{{ { model: $json.model, messages: $json.messages, options: $json.options,
     format: $json.format, stream: false } }}
```

⚠️ **Written without a leading `=`**, per the phase 3 contract §6 note.

### 2.6 `cap-brainstorm-pairing` — capability #1

⭐ **Chosen first because it needs nothing built.** No math, no `ref.ingredients`, no validator —
it runs against the corpus exactly as it stands today.

**Trigger field** — ⭐ **one**, and it is one the model will fill every single time (the D26b rule):

| Field | Type |
|---|---|
| `question` | String |

| # | Node | Type | Detail |
|---|---|---|---|
| 1 | `When Executed by Another Workflow` | trigger v1.2 | `question` |
| 2 | `Start run` | Postgres (`mem_writer`) | `SELECT obs.f_start_run($1,NULL,'brainstorm.pairing',$2)` → `run_id` |
| 3 | `Step 1 · parse` | Execute Workflow → `wf-step-llm` | profile `extract`, schema `{anchor_ingredient, style_context, direction}` |
| 4 | `Unpack parse` | Code | ⛔ **thread `run_id` forward as a parameter** (D14 — never re-derive it) |
| 5 | `Step 2a · retrieve anchor` | Execute Workflow → `tool-search-brewing-knowledge` | `query` = the anchor ingredient |
| 6 | `Step 2b · retrieve technique` | Execute Workflow → same tool | `query` = the style context. ⛔ **Sequential, not parallel** (D15) |
| 7 | `Build pack` | Code | merge both result sets, keep a `chunk_id → text` map for step 4 |
| 8 | `Step 3 · propose` | Execute Workflow → `wf-step-llm` | profile `creative` **t=0.9** — ⭐ the highest temperature in the system, and the safest place for it: this step states no numbers and writes nothing. Schema: `[{candidate, why, cites:[chunk_id]}]` |
| 9 | `Step 4 · ground` | Code | ⛔ **the whole point of this capability** — see below |
| 10 | `Step 5 · compose` | Execute Workflow → `wf-step-llm` | profile `compose` t=0.3 |
| 11 | `Finish run` | Postgres (`mem_writer`) | `obs.f_finish_run($1,'ok',$2)` |
| 12 | `Return` | Code | text back to the agent |

**Node 9 — `Step 4 · ground`:**

```javascript
// Every candidate must attach to a chunk that was actually retrieved.
// A cite the model invented is not evidence, and dropping it silently would be
// worse than either keeping or labelling it — so: labelled, never silent.
const pack  = $('Build pack').first().json;
const valid = new Set(pack.chunks.map(c => String(c.chunk_id)));
const cands = $input.first().json.output.candidates ?? [];

const grounded = [], suggested = [];
for (const c of cands) {
  const hits = (c.cites ?? []).map(String).filter(id => valid.has(id));
  (hits.length ? grounded : suggested).push({ ...c, cites: hits });
}

if (!grounded.length && !suggested.length) {
  throw new Error('propose returned no candidates');
}
return [{ json: { grounded, suggested, run_id: pack.run_id } }];
```

⭐ **Grounded candidates are cited; ungrounded ones become a labelled *"my own suggestion, not
from your library"* line.** ⛔ **Never silently mixed** — that is the difference between
brainstorming and confident invention, and it is the property the 12-case eval scores.

### 2.7 Binding the capability to WF4

Add a second **Call n8n Workflow Tool** node on the agent's `ai_tool` input:

| Field | Value |
|---|---|
| **Node name** | ⛔ **`brainstorm_pairing`** — D26a: the tool name the model sees is the **node** name. A mismatch with the system prompt makes every call unmatchable and the agent dies at max iterations with no tool execution |
| Workflow | `cap-brainstorm-pairing` |
| Description | *"Use when the user asks what ingredients would work together, what to do with an ingredient they have, or wants ideas rather than a specific fact. Not for questions with one correct answer."* |
| `question` | `{{ $fromAI('question', 'the user question, verbatim') }}` |

⭐ **The description is written as a *question shape*, and it names what the tool is NOT for.**
With two tools the boundary between them is the thing the model gets wrong, and §7.1 of the
architecture doc is explicit that in about half of "the model won't call my tool" cases the
description is the bug.

---

## §3 — Reset

```bash
docker exec -i supabase-db psql -U postgres -d postgres -c "DROP SCHEMA IF EXISTS obs CASCADE;"
```

```bash
docker exec n8n n8n delete:workflow --id=<id>
```

⚠️ Reverting `60_obs.sql` also means removing its line from the `docker-compose.yml` loop, or the
next `docker compose up db-init` recreates the schema.

⛔ **`mem.chat_turns` rows are not reset** — they are evidence. Delete by `session_id` if a test
run needs excluding.

---

## §4 — Tests

| Phase | Gate | ⛔ Hard failure |
|---|---|---|
| **4.5** | `tier1_routing.py`: knowledge row **30/30**, total **≥ 73/84** · the Tier C backlog for books 0a–4 · streaming visibly incremental · `mem.chat_turns` gains a row per turn with non-empty `chunk_ids` | any knowledge question answered with **no tool call** · any question about the user's own brewing answered with **an invented number** |
| **4.6** | a WF4 turn produces `obs.runs` + `obs.steps` rows joinable to `mem.chat_turns` · `prompt_sha256` matches `obs.prompts` · ⭐ **`tier1` re-run is unchanged** — nothing user-facing moved | a score that moves. It means something user-facing *did* move |
| **4.7** | 12-case eval · ⛔ **0 ungrounded candidates presented as cited** · every `[S…]` resolves to a real `chunk_id` · ⭐ **`tier1` re-run with two tools — the two-tool selection number Phase 2 could never measure** | a cite that does not resolve · the agent calling `brainstorm_pairing` for a factual question |

⭐ **Record the latency baseline at 4.5** — median and p90 time-to-first-token, median total. Every
budget in §3.7 of plan 00 and every claim about model swapping in §5 below is unmeasured until it
exists.

---

## §5 — ⭐ Which model, and what about the big ones

### 5.1 The constraint, measured

⭐ **16,304 MB total, 1,312 MB already consumed by the desktop → ~14.9 GB usable.** That number,
not 16, is what every model must fit in.

| Model | Size | Fits? |
|---|---|---|
| `gemma4:12b` (q4) | **7.6 GB** | ✅ **comfortably** — 7.6 + `bge-m3` 1.2 + ~2 KV ≈ **10.8 of 14.9** |
| `gemma4:12b-it-q8` | 13 GB | ⚠️ alone only. ⛔ evicts `bge-m3` |
| `gemma4:26b-a4b-it-qat` | 16 GB | ⛔ **does not fit.** 16 > 14.9 *before any KV cache* |
| `gemma4:26b` / `qwen3.8:27b` (q4) | **18 GB** | ⛔ ~3–4 GB to system RAM |
| `gemma4:31b-it-qat` / `31b` | 19–20 GB | ⛔ ~5–6 GB to system RAM |

RAM is not the blocker — **21 GB available**, so any of these can offload. Disk is not the blocker
— **528 GB free**. ⭐ **The blocker is VRAM, and it binds at 14.9 GB.**

### 5.2 ⭐ The detail that decides it: `26b-a4b` is not a dense 26B

⭐ **`gemma4:26b`'s full tag is `26b-a4b-it-q4`.** The `a4b` is the standard convention for a
**Mixture-of-Experts** model — ~26 B total parameters, **~4 B active per token**. `qwen3.8:27b`
carries no such marker and is presumably **dense**. They are the same 18 GB on disk and behave
completely differently:

| | `gemma4:26b` (MoE, ~4B active) | `qwen3.8:27b` (dense 27B) |
|---|---|---|
| Memory needed | all 26 B resident | all 27 B resident |
| Compute per token | ⭐ **like a 4 B model — fast** | like a 27 B model — slow |
| Cost of 3–4 GB CPU offload | ⭐ **moderate**; low per-token compute hides some of the transfer, though expert routing across PCIe is variable | ⛔ **severe** — every token touches offloaded weights |
| Likely strength | broad knowledge recall | ⭐ **deep, coherent long-form reasoning** |

⚠️ ⛔ **Verify the architecture before believing this paragraph** — `ollama show gemma4:26b` after
pulling, and read the parameter count. The `a4b` convention is strong evidence, not a measurement.

### 5.3 The recommendation

**⛔ For the agent / router slot: stay on `gemma4:12b`, and do not change it in this plan.** Four
reasons, in order:

1. ⛔ **It is the only baseline you have.** `tier1_routing.py`, the 73/84 target, prompt v3, the
   28 cases — all defined against `gemma4:12b`. Changing the model *and* building the agent in one
   run breaks standing rule 2 and leaves you unable to attribute either result.
2. ⛔ **Tool calling is the one hard requirement in this slot**, and it is the capability most
   damaged by heavy quantization and by MoE expert routing. It is also the failure that is
   *silent* — a model that routes slightly worse produces confident wrong answers, not errors.
3. ⭐ **Anything over ~13 GB cannot co-reside with `bge-m3`.** The router calls retrieval on most
   turns, so a 18 GB router means **an embedder reload on every single search**. That is an
   architectural objection, not a speed one, and your latency tolerance does not dissolve it.
4. It is called on **every turn**, where the others are called rarely.

**⭐ For the creative slot at 4.10: yes, and this is exactly what that slot exists for.** The
creative profile has **no tool-calling requirement** — it is a plain generation step — so it can be
chosen purely on prose quality and brewing sense. Pull both and A/B them:

```bash
docker exec ollama ollama pull gemma4:26b
```

```bash
docker exec ollama ollama pull qwen3.8:27b
```

⭐ **Pull them now even though 4.10 is four phases away** — 18 GB each, and a download is a bad
thing to discover in the middle of an eval.

**My prediction, written down so it can be scored** (this project's method, applied to itself):

| | Prediction |
|---|---|
| `gemma4:26b` vs `gemma4:12b` on brainstorm quality | ⚠️ **genuinely uncertain, and I would not bet either way.** 4 B active params is *less* compute per token than the 12 B dense. More knowledge, less reasoning depth. ⛔ **The one thing I am confident of is that "26 > 12" is not a reason** |
| `qwen3.8:27b` vs `gemma4:12b` on brainstorm quality | **better prose and better reasoning, meaningfully slower.** The most likely winner on quality alone |
| Speed order | `gemma4:12b` ≫ `gemma4:26b` > `qwen3.8:27b` |
| Which I would deploy if the evals tie | ⭐ **`gemma4:12b`** — a tie means the bigger model bought a swap cost and a second model to evaluate for nothing |

**⛔ Do not add a small `extract` model yet.** Run `extract` on `gemma4:12b` at `temperature 0`
through 4.9. Adding a third family before there is an eval to score it against is a variable with
no measurement attached.

### 5.4 How to run the A/B at 4.10, so the result means something

1. ⛔ **One model per run** (standing rule 2). Change `obs.profiles.model` for `creative` **only**.
   Touch no prompt, no schema, no other profile.
2. Re-run the **4.7 brainstorm eval** and, once it exists, the **4.9 recipe eval**. ⛔ **Do not
   re-run `tier1`** — the router did not change, so a different score would be noise.
3. ⭐ **Read `obs.steps.model_loaded` before reading `latency_ms`.** A cold step includes an 18 GB
   load. Comparing a cold big model against a warm small one measures your keep-alive setting, not
   the models.
4. ⭐ **Score prose quality by hand, on the same questions, blind to which model produced which.**
   There is no deterministic metric for "is this a good brewing idea", and an LLM judge sharing
   weights with the judged is the anti-pattern §10.2 already names.
5. Keep the winner **only if it moves a gated metric**. A change that does not move a number is
   maintenance bought for nothing (§11 Phase 5's rule).

---

## §6 — Handover

**What this plan does not answer, and where it goes:**

- ⛔ **The two streaming probes in §2.4** — a downstream node, and `Return Intermediate Steps`.
  Both are settled by one chat message at 4.5, and both change what `mem.chat_turns` can record.
- ⛔ **Whether Ollama's `format` parameter behaves on 0.30.6 with `gemma4:12b`** (§2.5 node 5). If
  not, node 6 becomes a retry loop and every step budget absorbs the extra call.
- **The retrieval confidence floor** for §6 of plan 00 — set from 4.5's measured score
  distribution, not invented.
- **`ref.ingredients` and the three math functions** — 4.8, and they gate `recipe.create`.

⛔ **Standing rule 4 applies to every artifact here:** export each workflow to
`n8n/demo-data/workflows/` and commit it **before** its first run. It was broken at books 1, 2 and
4, kept only at book 3, and the answer side starts with five new workflows at once.
