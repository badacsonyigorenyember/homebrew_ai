# Plan 03b — WF4 `chat-agent`, node by node

**Status:** ⬜ not started · **Written:** 2026-08-02
**Prereqs:** [`03a`](03a-tool-subworkflows.md) complete — `tool-search-brewing-knowledge`
exists and passes its standalone test
Companion to [`03-wf4-design.md`](03-wf4-design.md), which explains every choice made
here. This file is the clicking.

Architecture: §5 WF4 · §7.5–7.8 · §8.3 `$fromAI`.

---

## 0. The Ollama credential

Same place as the read-only Postgres one ([`03a`](03a-tool-subworkflows.md) §0.1): in
**n8n**, sidebar **Overview → Credentials → Add credential**. Not compose, not
Supabase. Pick the type **Ollama** and name it `Ollama account`.

| Field | Value |
|---|---|
| Base URL | `http://ollama:11434` |

`ollama`, not `localhost` — n8n resolves it on the `demo` Docker network. Test
connection must go green; if it doesn't, `docker exec n8n wget -qO- http://ollama:11434/api/tags`
tells you whether it's DNS or the credential.

---

## 1. Build order

**New workflow, name it exactly `chat-agent`.** Seven nodes: four on the main line,
three hanging beneath the agent as sub-nodes.

| # | Node name | Add-Node search term | Row |
|---|---|---|---|
| 1 | `When chat message received` | *Chat Trigger* | main |
| 2 | `Prep turn` | *Code* | main |
| 3 | `AI Agent` | *AI Agent* | main |
| 4 | `Log turn` | *Postgres* | main |
| 5 | `Ollama Chat Model` | *Ollama Chat Model* | sub-node of 3 |
| 6 | `Postgres Chat Memory` | *Postgres Chat Memory* | sub-node of 3 |
| 7 | `search_brewing_knowledge` | *Call n8n Workflow Tool* | sub-node of 3 |

> ### ⚠️ Node 7's name **is** the tool name. Get this wrong and nothing works.
>
> n8n 2.x derives the name advertised to the model from the node name —
> `nodeNameToToolName(node)`. There is no separate Name field on `toolWorkflow` v2.2.
> If you accept the auto-generated node name, n8n advertises e.g.
> `Call_tool-search-brewing-knowledge_` while your system prompt and description say
> `search_brewing_knowledge`. The model then calls a tool that does not exist.
>
> **The failure is silent and baffling:** no error, no tool execution in the
> execution list, and the agent dies with *"Max iterations (5) reached"*. The
> conversation never advances because the unmatched call is dropped, so every
> iteration re-sends a byte-identical prompt. Confirmed live 2026-08-02 — see §9.
>
> Check it yourself at any time:
>
> ```bash
> docker exec n8n sh -c 'cd /usr/local/lib/node_modules/n8n && node -e "console.log(require(\"n8n-workflow\").nodeNameToToolName({name: process.argv[1]}))" "YOUR NODE NAME HERE"'
> ```
>
> It must print exactly `search_brewing_knowledge`.

`Prep turn` is referenced by name from node 4.

> **⏸ There is no node 8.** The second tool, `find_batches`, is deferred by **D25**
> (architecture §7.3, §13.2). Phase 2 is a one-tool agent.

**Build in two stages** (design doc §4): get 1 → 3 → 5 → 6 → 7 working and
streaming first, then add 2 and 4. If you build all seven and streaming doesn't work,
you won't know which end broke it.

---

## 2. Node 1 — `When chat message received` (Chat Trigger v1.4)

| Field | Value | Why |
|---|---|---|
| **Make Chat Publicly Available** | **ON** | required for the `@n8n/chat` widget in `chat.html` to reach it at all |
| **Mode** | **Embedded Chat** | the hosted-chat mode serves n8n's own page; you want the widget you already wrote |
| **Authentication** | None | single user, localhost |
| Options → **Response Mode** | **Streaming** ⚠️ | defaults to *Last Node*. This is one of the two streaming switches (§7.7) — the one people miss |
| Options → **Allowed Origins (CORS)** | `*` | `chat.html` is served from nginx on `:8080` (or opened as a file), n8n is on `:5678` — different origin either way |

Leave *Available in Chat* off — that's for n8n's internal chat panel, not your widget.

**Copy the Production URL now** (the node panel shows it), shape:
`http://localhost:5678/webhook/<webhook-id>/chat`. §6 needs it.

> ### ⚠️ Active is not enough in n8n 2.x — you must **publish**, and so must the sub-workflow
>
> n8n 2.x separates a workflow's **draft** from its **published version**
> (`workflow_entity.activeVersionId`). Which one runs depends on the execution mode:
>
> ```js
> const useDraftVersion = isManualOrChatExecution(options.executionMode);
> // production  -> getPublishedWorkflowData() -> requires activeVersion
> //                else throws "Workflow is not active and cannot be executed."
> ```
>
> Consequences, both confirmed live 2026-08-02:
>
> - **The tool sub-workflow must be published too.** A production run of WF4 calling an
>   unpublished `tool-search-brewing-knowledge` fails with *"Workflow is not active and
>   cannot be executed."* — an error that names no workflow, so it reads as if WF4 were
>   the problem.
> - **Edits do not take effect in production until you publish again.** You can rename a
>   node, save, and watch production keep running the old version. Publish after every
>   change you want the `chat.html` webhook to see.
>
> Manual runs and the editor's chat pane use the draft, which is why something can work
> in the editor and fail from `chat.html`.
>
> Check what is published:
>
> ```bash
> docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -tAc "select name, active, \"activeVersionId\" is not null as published from workflow_entity order by name;"
> ```

---

## 3. Node 3 — `AI Agent` (v3.1)

Wire node 1 → node 3 for now (node 2 goes in later).

| Field | Value |
|---|---|
| **Prompt Source** | *Define below* |
| **Prompt (User Message)** | `={{ $json.chatInput }}` |
| **Require Specific Output Format** | off |
| **Enable Fallback Model** | off |

Then **Options → Add Option**, four times:

| Option | Value | Why |
|---|---|---|
| **System Message** | the block from design doc §6 — paste verbatim, **as an expression** (field must start with `=`) so `{{ $now.toFormat('yyyy-MM-dd') }}` resolves | §7.8 |
| **Max Iterations** | `5` | caps a tool loop. Default 10 is a 60-second dead UI on local hardware |
| **Return Intermediate Steps** | **true** | this is what puts tool calls in the node output, which is what makes the exit criterion computable in SQL (§04 gate doc §5) |
| **Enable Streaming** | **true** | defaults true in v3.1 — set it explicitly so a later copy-paste can't lose it. The other half of §7.7 |

Why *Define below* rather than the `auto` prompt source: `auto` reads `chatInput` from
the node's immediate input, and in §5 you insert `Prep turn` between the trigger and
the agent. Binding explicitly now means adding that node changes nothing.

---

## 4. Nodes 5–7 — the sub-nodes

### Node 5 — `Ollama Chat Model`

Credential: `Ollama account`. Model: **`gemma4:12b`** (it will be in the dropdown —
verified present, 7.6 GB).

**Options → Add Option**, four times. All four defaults are wrong for this stack —
the full reasoning is design doc §2:

| Option | Value |
|---|---|
| **Context Length (`numCtx`)** | `12288` — default 2048 truncates a single retrieval. ⚠️ **Count the digits.** `122288` is a real typo that has happened here: it is accepted (the model's nominal limit is 262144), loads a ten-times-oversized KV cache, and eats the VRAM budgeted for `bge-m3`. Verify with `docker exec ollama ollama ps` — the `CONTEXT` column must read `12288` |
| **Sampling Temperature** | `0.2` — default 0.7 makes routing non-reproducible |
| **Think** | `false` — thinking tokens are pre-first-token latency |
| **Keep Alive** | `-1m` — ⚠️ default `5m` **overrides** the server's `OLLAMA_KEEP_ALIVE=-1` |

### Node 6 — `Postgres Chat Memory` (v1.4)

| Field | Value |
|---|---|
| Credential | **`Postgres account`** (the superuser one) |
| Session ID | *Connected Chat Trigger Node* → `={{ $json.sessionId }}` |
| Table Name | `n8n_chat_histories` (default) |
| **Context Window Length** | **`6`** (default 5) |

Not the read-only credential: this node **creates and writes** its table. It is app
plumbing outside the agent's tool surface, which is why that's fine (design doc §3).

On first run it creates `public.n8n_chat_histories` in the app database. Expected —
that's the §7.6 decision to keep chat history with the app data, not in n8n's
metadata Postgres.

### Node 7 — `search_brewing_knowledge`

*Call n8n Workflow Tool* (v2.2). **Rename the node to exactly `search_brewing_knowledge`
before anything else** — no quotes, no spaces, no "Call". The node name is the tool
name the model sees (see the warning in §1). n8n will suggest something like
`Call 'tool-search-brewing-knowledge'`; accepting it breaks the agent.

| Field | Value |
|---|---|
| **Description** | the `search_brewing_knowledge` block from design doc §7, verbatim |
| **Source** | Database |
| **Workflow** | `tool-search-brewing-knowledge` |

The **Workflow Inputs** panel now auto-populates with the two fields you declared on
that sub-workflow's trigger. Fill them:

`query` — click *Let the model define this parameter*, then edit to:

```javascript
{{ $fromAI('query',
   'The user question rewritten as a standalone search query about brewing. Keep the brewing terms the user used. Never include the word "my" or a batch number — this searches published books, not the user records. Example: "why does my beer taste like butter" -> "diacetyl cause and prevention".',
   'string') }}
```

> **`doc_type` — removed 2026-08-02.** Do not map it; the field no longer exists on
> the sub-workflow trigger. Every declared input is required, so a `doc_type` the
> model omitted failed the tool with *"Received tool input did not match expected
> schema ✖ Required → at doc_type"*. Unfiltered retrieval handles style questions
> anyway — design doc §7.1.

`top_k` — **do not** let the model define this. Type the literal `6`. It is the §7.5
context budget (6 chunks × ~500 tokens); a model that decides it wants 8 has just
overspent it.

> ### ⏸ Node 8 — `find_batches` — NOT BUILT (D25)
>
> The truth-side tool is deferred pending an architecture discussion. Its full draft,
> including all seven `$fromAI()` descriptions, is parked at
> [`deferred/find-batches-tool-draft.md`](deferred/find-batches-tool-draft.md).
>
> The consequence for this build is deliberate and worth stating: **the agent now has
> no way at all to answer a question about the user's own brewing.** That is the
> condition Phase 2's exit gate tests — it must refuse, not improvise from the books.
> See [`04`](04-phase2-exit-gate.md) §2.

## 5. Stage A checkpoint — before adding nodes 2 and 4

Open the workflow's chat pane in the editor and ask, in order:

| Ask | Expect |
|---|---|
| `what causes diacetyl in beer` | `search_brewing_knowledge` fires; answer cites `[S…]` from *How to Brew*; a `Sources:` block at the end |
| `how long should a secondary fermentation take` | **the tool must fire.** A confident answer with `[S1]` but no tool node in the execution means the *"Using the library — not optional"* block is missing from the system message (design doc §6) |
| `which of my IPAs were bitter` | **no tool fires**; a refusal — *"I don't have a tool for that yet"*. **Not** a book passage dressed up as the user's data |
| `how much Citra do I have` | *"I don't have a tool for that yet."* — **no tool call, no number** |

Then confirm the two things that are easy to get wrong:

```bash
docker exec ollama ollama ps
```

Both models listed, `100% GPU`, `UNTIL = Forever`. If `gemma4:12b` shows a clock,
`Keep Alive` didn't take.

And **watch the text appear.** Progressive word-by-word rendering = streaming works.
One lump after a long pause = one of the two switches is off (§7.7): check the Chat
Trigger's Response Mode first, it's the one that defaults wrong.

**Do not proceed until Stage A is green.** Everything after this is logging.

---

## 6. Stage B — `Prep turn` and `Log turn`

### Node 2 — `Prep turn` (Code)

Insert between the trigger and the agent. Mode: **Run Once for All Items**.

```javascript
const i = $input.first().json;
return [{ json: {
  sessionId:  i.sessionId,
  chatInput:  i.chatInput,
  started_ms: Date.now(),
}}];
```

It exists for `started_ms` — `latency_ms` needs a start stamp and n8n expressions
don't expose the execution start time. It passes `sessionId` and `chatInput` through
untouched, which is what keeps the memory node's `{{ $json.sessionId }}` and the
agent's `{{ $json.chatInput }}` resolving.

### Node 4 — `Log turn` (Postgres)

After the agent. Credential: **`Postgres account`** — `n8n_agent` has no `USAGE` on
`mem` (verified `f`), by design.

Operation: Execute Query.

```sql
WITH nxt AS (
  SELECT COALESCE(MAX(turn_no), 0) + 1 AS n
  FROM mem.chat_turns WHERE session_id = $1
)
INSERT INTO mem.chat_turns
  (session_id, turn_no, role, content, tool_calls, latency_ms, model)
SELECT $1, nxt.n, 'user',      $2, NULL,                  NULL,               NULL       FROM nxt
UNION ALL
SELECT $1, nxt.n, 'assistant', $3, NULLIF($4,'')::jsonb,  NULLIF($5,'')::int, 'gemma4:12b' FROM nxt
RETURNING session_id, turn_no, role;
```

Options → **Query Parameters**:

```
={{ [ $('Prep turn').first().json.sessionId, $('Prep turn').first().json.chatInput, $json.output, JSON.stringify(($json.intermediateSteps ?? []).map(s => ({ tool: s.action?.tool, input: s.action?.toolInput }))), String(Date.now() - $('Prep turn').first().json.started_ms) ] }}
```

Both rows share one `turn_no` — that's what the `UNIQUE (session_id, turn_no, role)`
constraint is shaped for (§7.6): a turn is the user/assistant pair, and the pair is
the unit the eval counts.

`tool_calls` comes from `intermediateSteps`, which only exists because *Return
Intermediate Steps* is on (§3). Without it this column is silently `[]` on every row
and the gate has nothing to measure.

`chunk_ids` stays NULL — design doc §5 explains why, and Phase 3 is where it gets
wired.

### Stage B checkpoint

Re-ask the **same** Stage A question and check two things:

1. **Streaming still works.** If it regressed, `Log turn` is the cause — delete it,
   confirm streaming returns, then re-add it as a fire-and-forget *Execute
   Sub-workflow* branch instead (design doc §4).
2. The rows landed:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select turn_no, role, left(content,60) as content, tool_calls, latency_ms from mem.chat_turns order by id desc limit 4;"
```

You want two rows per question, matching `turn_no`, `tool_calls` naming the tool that
actually fired, and a plausible `latency_ms`.

---

## 7. Wire `chat.html`

Two edits in [`chat/chat.html`](../../chat/chat.html):

```javascript
// was: 'http://localhost:5678/webhook/REPLACE_WITH_WF4_CHAT_WEBHOOK/chat'
const WEBHOOK_URL = 'http://localhost:5678/webhook/<your-webhook-id>/chat';
```

```javascript
loadPreviousSession: false,   // was true
```

**Why turn `loadPreviousSession` off.** It makes the widget replay history on load,
which needs the trigger to answer a `loadPreviousSession` action as well as normal
messages — an extra failure mode you do not want to debug in the same sitting as
streaming. The Postgres memory still works: history persists *within* a session, the
widget just doesn't replay it after a reload. Revisit in Phase 3.

Then activate the workflow and serve the page:

```bash
cp "/home/gorenyember/AI Homebrew Assistant/chat/chat.html" "/home/gorenyember/AI Homebrew Assistant/shared/extracted-images/chat.html"
```

Open <http://localhost:8080/chat.html>. **The workflow must be Active** or the
production webhook returns 404 — the single most common "the chat page is broken".

---

## 8. Export and commit

```bash
docker exec n8n n8n export:workflow --all --separate --output=/tmp/wf
docker cp n8n:/tmp/wf/. "/home/gorenyember/AI Homebrew Assistant/n8n/demo-data/workflows/"
```

Rename WF4's file to `wf4-chat-agent.json`, commit it with the two tool workflows and
the `chat.html` edit. From here on, edit the JSON in the repo and
`n8n import:workflow` — the WF2 rule (§11 Phase 1.1).

---

## 9. If it doesn't work

**First, decode the failed execution — don't guess.** n8n stores execution data in
`flatted` format, so plain SQL or grep gives you noise:

```bash
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -tAc "select data from execution_data where \"executionId\"=<ID>;" > /tmp/e.raw && docker exec -i n8n sh -c 'cat > /tmp/e.raw' < /tmp/e.raw && docker exec n8n sh -c 'cd /usr/local/lib/node_modules/n8n && node -e "const f=require(\"flatted\"),fs=require(\"fs\");const d=f.parse(fs.readFileSync(\"/tmp/e.raw\",\"utf8\").trim());for(const [n,r] of Object.entries(d.resultData.runData)){console.log(\"==\",n);r.forEach(x=>{if(x.error)console.log(\"  ERROR:\",x.error.message);const j=JSON.stringify(x.data||{});if(j.length<1200)console.log(\"  \",j)})}"'
```

Get the execution id from:

```bash
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -tAc "select e.id, w.name, e.status, e.\"startedAt\" from execution_entity e join workflow_entity w on w.id=e.\"workflowId\" order by e.id desc limit 10;"
```

What to read: the **Ollama Chat Model** entries. `text: ""` with a nonzero
`completionTokens` means the model emitted a tool call. If `promptTokens` is
**identical across every iteration**, the tool call was never dispatched and the
conversation never advanced — go straight to the tool-name check in §1.


| Symptom | First thing to check |
|---|---|
| Chat page 404s | workflow not **Active/published**; or the widget URL is the Test URL, not the Production one |
| **"Workflow is not active and cannot be executed."** | the **sub-workflow** isn't published — the message doesn't say which workflow it means. Publish `tool-search-brewing-knowledge`. See §2 |
| A fix works in the editor but not from `chat.html` | you saved but didn't **publish**. Production runs the published version, the editor runs the draft |
| Knowledge answer with `[S1]` but no tool call in the execution | the *"Tool use is mandatory"* section is missing from the system message — design doc §6 |
| **"Received tool input did not match expected schema ✖ Required → at \<field\>"** | the model omitted a field the sub-workflow trigger declares. Every declared field is required — either remove it from the trigger, or supply it as a literal from WF4 rather than `$fromAI`. See `03a` §1 |
| Chat page hangs, no CORS error visible | Chat Trigger *Allowed Origins* not `*` — check the browser console |
| Text arrives in one lump | Chat Trigger Response Mode ≠ Streaming (check this first), then the agent's Enable Streaming |
| First message takes 15 s, later ones 3 s | `ollama ps` — `gemma4:12b` cold. `Keep Alive` is `5m`, not `-1m` |
| Every answer is slow and rambling | `numCtx` still 2048 → the system prompt plus one retrieval is being truncated |
| Model answers batch questions from the books | the system prompt's **law** section is not landing. Strengthen it — this is a hard fail on the gate, not a nuisance |
| Model calls the search tool for a question about the user's beer | same cause. The tool description ends by saying it knows nothing about the user's records; check it survived the paste |
| `Log turn` errors on `mem` permission | it's using the read-only credential. Switch it to `Postgres account` |
| **"Max iterations (5) reached"** with **no tool execution anywhere** | ⚠️ **Almost certainly the node-name/tool-name mismatch — §1.** Rename node 7 to exactly `search_brewing_knowledge`. Confirm the diagnosis before changing anything else: decode the failed execution and look at the Ollama Chat Model runs — identical `promptTokens` on every iteration plus `text: ""` means the model emitted a tool call that the agent could not match. If `promptTokens` *grows* between iterations, it is a different problem |
| Agent hits Max Iterations, and the tool **did** run each time | tool output is confusing it. Fix the shape, not the cap |
| Answers look plausible but cite `[S1] search_brewing_knowledge` as a source | the model is answering with **no tool bound or matched** and inventing a citation. Same root cause — check the tool name first |
