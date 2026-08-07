# Plan 03a — the tool sub-workflow, node by node

**Status:** ⬜ not started · **Written:** 2026-08-02 · **Rescoped 2026-08-02 (D25)**
**Prereqs:** [`03-wf4-design.md`](03-wf4-design.md) read · preflight in
[`README.md`](README.md) §0 green
**Build this first.** WF4's tool node selects a sub-workflow from a dropdown — it has
to exist before you can point at it.

Architecture: §5 "Tool sub-workflows" · §8.2 safe tool interface · §8.3 `$fromAI` ·
§8.4 read-only enforcement.

> **⏸ One tool, not two — D25.** This file originally built
> `tool-search-brewing-knowledge` *and* `tool-find-batches`. The truth-side surface is
> deferred pending an architecture discussion (architecture §7.3, §13.2). The
> `find_batches` draft is parked intact at
> [`deferred/find-batches-tool-draft.md`](deferred/find-batches-tool-draft.md) — **do
> not build it.**

---

## 0. Do this once, before you start

### 0.1 Create the read-only Postgres credential

**This is an n8n credential — nothing to add to `docker-compose.yml`, and nothing to
create in Supabase.** Three things share the word "credential" here; only the third is
work:

| Layer | Where it lives | Status |
|---|---|---|
| The `n8n_agent` **Postgres role** | inside Supabase Postgres, created by `db/init/50_roles.sql`, which `db-init` runs on every stack start | ✅ already exists — verified 2026-08-02 |
| The **password** | `AGENT_DB_PASSWORD` in `.env` → `db-init` → `psql -v agent_pw` | ✅ already set |
| The **n8n credential** | n8n's own database — its stored copy of host/user/password | ⬜ **you create this** |

Confirm layer 1 from the Supabase side if you want to see it there — Studio →
**Database → Roles**, or:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "\du n8n_agent"
```

Expect `Cannot login: no` to be absent and the attributes to include
`default_transaction_read_only=on`, `statement_timeout=10s`.

**Now the one thing to build.** In n8n (<http://localhost:5678>) → sidebar
**Overview → Credentials → Add credential**, or the *Create new credential* entry in
any Postgres node's credential dropdown.

⚠️ **Choose the type `Postgres`.** n8n also ships a **`Supabase`** credential type —
that one talks to the PostgREST API and is the wrong thing here. You want the same
type as the existing `Postgres account`, with a different user.

Name it exactly **`Postgres — n8n_agent (read-only)`**.

| Field | Value |
|---|---|
| Host | `db` |
| Database | `postgres` |
| User | `n8n_agent` |
| Password | the value of `AGENT_DB_PASSWORD` in `.env` |
| Maximum Number of Connections | `100` (default) |
| **Ignore SSL Issues** | **OFF** ⚠️ see below |
| **SSL** | **Disable** |
| Port | `5432` |
| SSH Tunnel | off |

⚠️ **The SSL pair is the one thing that will fail.** Symptom:
*"The server does not support SSL connections"*.

Supabase Postgres here runs with `ssl = off` — it only accepts connections from
inside the Docker network (`host all all 172.16.0.0/12 scram-sha-256` in
`pg_hba.conf`), so there is no TLS to negotiate. Verify with
`docker exec supabase-db psql -U postgres -d postgres -tAc "show ssl;"` → `off`.

n8n resolves the two fields like this:

```js
if (credentials.allowUnauthorizedCerts === true) {
    dbConfig.ssl = { rejectUnauthorized: false };          // SSL ON
} else {
    dbConfig.ssl = !['disable', undefined].includes(credentials.ssl);
}
```

So **"Ignore SSL Issues" turns SSL on**, despite reading like the opposite — and
while it is on, the SSL dropdown is *hidden*, so you cannot set it to Disable. Turn
the toggle **off first**, then pick **Disable** in the dropdown that reappears.
Anything other than `Disable` (`Allow`, `Require`) fails the same way.

Get the password without echoing the whole file:

```bash
grep -E '^AGENT_DB_PASSWORD=' "/home/gorenyember/AI Homebrew Assistant/.env" | cut -d= -f2-
```

Hit **Test connection** — it must go green. `db:5432` was verified reachable from the
n8n container on 2026-08-02.

This credential is read-only *at the server*: `default_transaction_read_only=on` and
`statement_timeout=10s` are set on the role itself (§8.4), so you get them for free
here and cannot forget them. That is the entire point of not reusing
`Postgres account`.

### 0.2 A sanity check worth 30 seconds

```bash
cd "/home/gorenyember/AI Homebrew Assistant" && PW=$(grep -E '^AGENT_DB_PASSWORD=' .env | cut -d= -f2-) && docker exec -e PGPASSWORD="$PW" supabase-db psql -U n8n_agent -h localhost -d postgres -tAc "select current_user, count(*) from nlq.find_batches();"
```

Expect `n8n_agent|0` — `brew.batches` is empty and stays empty (D25). This query is
not testing the batch data; it is testing that the role can log in and reach `nlq` at
all. If it errors, fix it here — debugging a grant through three layers of n8n is
miserable.

---

## 1. The tool — `tool-search-brewing-knowledge`

**New workflow, name it exactly `tool-search-brewing-knowledge`.** Six nodes, one
straight line, left to right.

| # | Node name | Add-Node search term |
|---|---|---|
| 1 | `When Executed by Another Workflow` | *Execute Workflow Trigger* |
| 2 | `Normalise input` | *Code* |
| 3 | `Embed query` | *HTTP Request* |
| 4 | `Build vector` | *Code* |
| 5 | `Search knowledge` | *Postgres* |
| 6 | `Shape for model` | *Code* |

Keep those names exactly — nodes 4 and 6 reference node 2 by name.

### Node 1 — `When Executed by Another Workflow`

Execute Workflow Trigger, typeVersion 1.2.

- **Input data mode:** *Define using fields below* (`inputSource: workflowInputs`)
- Add **two** fields:

| Name | Type |
|---|---|
| `query` | String |
| `top_k` | Number |

This schema is what lets WF4's tool node auto-populate its parameter list (§5). If you
skip it and use *Accept all data*, you get a free-text blob and `$fromAI` has nothing
to bind to.

> ### ⚠️ Two fields, not three — `doc_type` was removed 2026-08-02
>
> **Every field declared here is required.** There is no optional flag on
> `workflowInputs` in trigger v1.2, so a field the model omits fails the tool with
> *"Received tool input did not match expected schema ✖ Required → at doc_type"*.
>
> `doc_type` was deleted rather than forced, because unfiltered retrieval already
> handles style questions — *"BJCP specs for Irish Stout"* returns six style cards,
> *"IBU of Altbier"* puts `7B Altbier` at rank 1. It was failure surface buying
> nothing (design doc §7.1).
>
> `top_k` stays declared but WF4 passes the literal `6`, so the model never fills it
> and it never fails validation. **The rule to carry forward: any field here that the
> model fills must be one it will fill every single time.**
>
> The node code below is unchanged — `Normalise input` already defaults a missing
> `doc_type` to `''`, and the SQL `NULLIF` turns that into "search the whole corpus".

### Node 2 — `Normalise input` (Code)

Mode: **Run Once for All Items**.

```javascript
const i = $input.first().json;

const query = String(i.query ?? '').trim();
if (!query) throw new Error('search_brewing_knowledge called with an empty query');

// kb.documents.doc_type CHECK allows book|style_guide|article|datasheet|note.
// Only two exist in the corpus today; anything else means the model guessed, so
// drop it to '' (= search everything) rather than returning zero rows.
const allowed = ['book', 'style_guide'];
const dt = String(i.doc_type ?? '').trim().toLowerCase();

const k = Number(i.top_k);

return [{ json: {
  query,
  doc_type: allowed.includes(dt) ? dt : '',
  top_k: Number.isFinite(k) && k > 0 ? Math.min(Math.round(k), 8) : 6,
}}];
```

Three jobs, all defensive: reject an empty query loudly, silently discard a
hallucinated `doc_type`, and cap `top_k` at 8 so the model cannot blow the §7.5
context budget by asking for 50 chunks.

### Node 3 — `Embed query` (HTTP Request)

Identical in shape to WF1's `Ollama embed` node — reuse the pattern, it's proven.

| Field | Value |
|---|---|
| Method | `POST` |
| URL | `http://ollama:11434/api/embed` |
| Send Body | on |
| Body Content Type | JSON |
| Specify Body | Using JSON |
| JSON | `={{ { "model": "bge-m3", "input": $json.query, "keep_alive": -1 } }}` |
| Options → Timeout | `120000` |

No credential. `keep_alive: -1` keeps `bge-m3` pinned — the same trap as the chat
model's `keepAlive` (design doc §2), on the other model.

### Node 4 — `Build vector` (Code)

```javascript
const src = $('Normalise input').first().json;
const emb = $json.embeddings?.[0];

if (!Array.isArray(emb) || emb.length !== 1024) {
  throw new Error(`Expected a 1024-dim embedding, got ${emb?.length} — is bge-m3 loaded?`);
}

// pgvector literal, cast with $2::vector downstream. Same trick as WF1's
// "Zip ids + embeddings": an array parameter would arrive as a Postgres array.
return [{ json: { ...src, embedding: '[' + emb.join(',') + ']' } }];
```

The dimension check is not paranoia — a silent dimension mismatch is exactly how a
corpus and a query end up in two different vector spaces, and the symptom is
"retrieval got worse", not an error.

### Node 5 — `Search knowledge` (Postgres)

- **Credential:** `Postgres — n8n_agent (read-only)` ← the whole point
- **Operation:** Execute Query
- **Settings tab → Always Output Data: ON** ⚠️ without this, a zero-row result emits
  zero items, node 6 never runs, and the tool returns nothing at all to the agent —
  which the model interprets as a broken tool rather than "no results"

Query:

```sql
SELECT chunk_id, doc_title, heading_path, page_from, raw_content
FROM nlq.search_knowledge(
  $1::text,
  $2::vector,
  $3::int,                      -- p_limit
  40,                           -- p_candidates  (§3.4 default)
  50,                           -- p_rrf_k       (§3.4 default)
  'bge-m3',
  NULLIF($4::text, '')          -- p_doc_type; '' means the whole corpus
);
```

Options → **Query Parameters**:

```
={{ [$json.query, $json.embedding, $json.top_k, $json.doc_type] }}
```

**Do not tune 40 / 50 here.** They are the §3.4 defaults the Phase 1 gate was scored
against. Changing them makes every Phase 1 measurement incomparable, and §11 Phase 5
is where retrieval parameters get tuned — with an eval to justify it.

### Node 6 — `Shape for model` (Code)

Mode: **Run Once for All Items**. This produces the compact `[S…]` block from §7.5.

```javascript
const rows = $input.all().map(i => i.json).filter(r => r.chunk_id != null);
const q = $('Normalise input').first().json.query;

if (!rows.length) {
  return [{ json: { response: `No passages in the library matched "${q}".` } }];
}

const body = rows.map((r, n) => {
  const head = Array.isArray(r.heading_path) ? r.heading_path.join(' > ') : '';
  const page = r.page_from ? ` · p.${r.page_from}` : '';
  const text = String(r.raw_content).replace(/\s+/g, ' ').trim();
  return `[S${n + 1}] ${r.doc_title} · ${head}${page}\n${text}`;
}).join('\n\n');

return [{ json: {
  response: `${rows.length} passages from the library for "${q}":\n\n${body}`,
}}];
```

Two things this is doing deliberately:

- **One item, one key.** A `Call n8n Workflow Tool` node hands the sub-workflow's last
  output to the model. One item with a single `response` string gives clean text;
  six items gives the model a JSON array to wade through.
- **`[S1]…[S6]` labels are assigned here**, not by the model. The system prompt tells
  the model to reuse the labels the tool gives it — that's the only mechanism you have
  for citation integrity once streaming rules out post-processing (§7.7).

### Test it standalone

**Execute Workflow** with pinned input:

```json
{ "query": "what temperature and how long for a diacetyl rest", "doc_type": "", "top_k": 6 }
```

Expect six `[S…]` blocks, and — from the §11.2 gate — ranks 1 and 3 should be
`10.4 Yeast Starters and Diacetyl Rests`, p.98. If you get that, the tool is wired
correctly end to end: embed → RRF → shape.

Then try `{"query": "Irish Stout", "doc_type": "style_guide", "top_k": 3}` to confirm
the `doc_type` filter reaches the function.

---

## 3. Export before moving on

n8n's database is not a backup. Plan 02 §7.1 learned this the hard way with WF1.

```bash
docker exec n8n n8n export:workflow --all --separate --output=/tmp/wf
docker cp n8n:/tmp/wf/. "/home/gorenyember/AI Homebrew Assistant/n8n/demo-data/workflows/"
```

Rename the new file to `tool-search-brewing-knowledge.json`, then commit. Edit them in the repo and
`n8n import:workflow` — not in the editor — the same rule WF2 follows (§11 Phase 1.1).

---

## 4. Reference — what WF4 will bind to these

Not built here, but this is the contract [`03b`](03b-wf4-build-guide.md) §4 fills in,
so keep it in view while you name the input fields:

| Sub-workflow field | `$fromAI` name in WF4 |
|---|---|
| `query` | `query` |
| `doc_type` | `doc_type` |
| `top_k` | fixed at `6` — not model-defined |

⚠️ `$fromAI()` only works in tools attached to an AI Agent (§8.3). It will not
evaluate inside this sub-workflow — everything here reads plain `$json`.
