# Programmatic write-back: REST API and MCP

Read this **before** the first programmatic edit to any workflow in
`n8n/demo-data/workflows/`.

> ✅ **UPDATED 2026-09-14 — the headline question is settled and two claims below
> were WRONG.** The `$input` hazard does **not** reproduce on the MCP path
> (§"The `$input` question"), and the `availableInMCP` list was wrong in both
> directions (§"Two write paths"). Both corrected in place, `measured`, with the
> evidence. The REST `PUT` path remains genuinely untested.

---

## Two write paths, two auth schemes

| Path | Endpoint | Auth | Notes |
|---|---|---|---|
| Public REST API | `http://localhost:5678/api/v1/…` | `X-N8N-API-KEY` header | ✅ enabled (returns 401, not 404). No key in `.env` — mint one in the n8n UI under Settings → n8n API |
| Official MCP server | `http://localhost:5678/mcp-server/http` | `Authorization: Bearer <JWT>` | Token lives in `~/.claude.json`. Gated per workflow by `settings.availableInMCP` |

⛔ **CORRECTED 2026-09-14 — this was wrong in both directions.** `measured`
against `workflow_entity.settings`: **9 of 15** were true, and **two of the three
named above were false**.

| `availableInMCP: true` (9) | unset / false (6) |
|---|---|
| `cap-brainstorm-pairing`, `ingest-bjcp-styles`, `ingest-draught`, `ingest-how-to-brew`, `ingest-malt`, `ingest-water`, `ingest-yeast`, `wf-step-llm`, **`wf1-ingest-book`** | ⛔ **`chat-agent`**, ⛔ **`wf-step-retrieve`**, `ingest-ba-styles`, `ingest-beer-faults`, `ingest-hop-varieties`, `ingest-study-guide` |

⛔ **`chat-agent` and `wf-step-retrieve` — the live retrieval path — are NOT
reachable over MCP.** Edit them via tracked JSON + `n8n import:workflow`.

⚠️ **The gate is per-tool, not global.** `search_workflows` returns **every**
workflow regardless of the flag, each reporting a full scope set
(`workflow:update`, `workflow:delete`) and `canExecute: true`. Those scopes are
misleading — the flag is enforced separately at `get_workflow_details` and
`update_workflow`, which return *"Workflow is not available in MCP."* Discovery is
ungated; read-detail and write are gated. Workflows MCP creates get `true`
automatically.

Check it directly rather than trusting this table:

```bash
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -c \
  "select name, settings->>'availableInMCP' from workflow_entity order by name;"
```

The MCP server's authoring model is the **TypeScript Workflow SDK**
(`create_workflow_from_code`), not raw node JSON. Start from `get_sdk_reference`
and `get_suggested_nodes` rather than hand-writing nodes.

---

## The `$input` question — settle it before editing

Upstream claims a REST `PUT` silently strips the `$input` prefix from Code node
`jsCode`, turning `$input.first().json` into `.first().json` — a syntax error
that only surfaces at run time.

> ## ✅ SETTLED 2026-09-14 — MCP path: `$input` SURVIVES
>
> Probed on a throwaway `ZZ-scratch-input-probe`, verified by reading
> `workflow_entity.nodes` **directly** rather than trusting the tool's own
> read-back (which could normalise).
>
> | Path under test | Stored value |
> |---|---|
> | `create_workflow_from_code` | ✅ `const x = $input.first().json;` — byte-identical |
> | `update_workflow` · `setNodePosition` (Code node untouched) | ✅ intact |
> | `update_workflow` · `setNodeParameter` `/jsCode` | ✅ 2/2 `$input` intact |
> | `update_workflow` · `updateNodeParameters` `replace: true` | ✅ intact |
>
> A grep for a bare `.first()` / `.all()` found none in any case. **Upstream's
> stripping claim does not reproduce on the MCP/SDK path.** The
> "newlines double-escape" hazard also did not fire — `\n` stored correctly.
>
> ⚠️ **The REST `PUT` path is STILL UNTESTED.** There is no public-API key: the
> one row in `user_api_keys` is labelled "MCP Server API Key" and its JWT carries
> `aud: mcp-server-api`, not `public-api`, so it returns
> `401 {"message":"unauthorized"}` as `X-N8N-API-KEY`. **The two paths are
> independent — this result does not transfer to REST.**
>
> ⚠️ Caveat: the probe was a 2-node hand-built workflow. It exercised the
> serialization round-trip the claim is about, but not a large workflow with
> credentials and expressions.

**Historical context for the question:** 14 Code nodes here use `$input`.
⚠️ Note the original wording named *"`Normalise input` and `Return rows` in
`wf-step-retrieve`"* — `measured` 2026-09-14, only `Normalise input` uses
`$input`; `Return rows` does not.

Upstream's track record is mixed — its `specifyBody: 'json'` claim is
demonstrably false here — so verify rather than assume. Safe round-trip test,
touching nothing that exists:

```bash
# 1. create a throwaway workflow containing the pattern under test
#    (needs an API key from Settings -> n8n API)
curl -s -X POST http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY" -H 'Content-Type: application/json' \
  -d '{"name":"ZZ-scratch-input-probe","nodes":[{"parameters":{"jsCode":"const x = $input.first().json; return [{json:x}];"},"type":"n8n-nodes-base.code","typeVersion":2,"position":[0,0],"id":"probe","name":"Probe"}],"connections":{},"settings":{"executionOrder":"v1"}}'
```

Then `GET /api/v1/workflows/<new-id>` and check whether `$input` survived; `PUT`
the same body back and re-read to cover the update path too.

⛔ **Delete the scratch workflow with a `DELETE` on `workflow_entity`, not an
archive** — archiving leaves the row and has already cost this repo a session.
Verify the workflow count returns to its prior value and that `shared_workflow`
has no orphans.

---

## PUT body: only five fields are accepted

`name`, `nodes`, `connections`, `settings`, `staticData`.

Rejected or ignored: `active`, `id`, `createdAt`, `updatedAt`, `versionId`,
`tags`, `pinData`, `triggerCount`. Activation is a separate endpoint
(`POST /api/v1/workflows/:id/activate`).

The safe shape is read → mutate → strip → write:

```javascript
const wf = await get(`/api/v1/workflows/${id}`);
// ...mutate wf.nodes / wf.connections...
await put(`/api/v1/workflows/${id}`, {
  name: wf.name, nodes: wf.nodes, connections: wf.connections,
  settings: wf.settings ?? {}, staticData: wf.staticData ?? null,
});
```

## Other write-back hazards

- **Credentials are not inherited.** A Postgres node written via the API needs
  `node.credentials = { postgres: { id, name } }` set explicitly, or it runs
  unauthenticated. All 23 Postgres nodes here carry credentials today.
- **Webhook registration breaks after PUT.** `/activate` does not reliably fix
  it; sometimes only a UI toggle does. Not currently an issue — this repo has no
  webhook nodes, it uses `chatTrigger` and `manualTrigger`.
- **IF `conditions` must stay an object**, `{options, conditions, combinator}`.
  A bare array is accepted on write and breaks at run time.
- **Postgres `insert` keeps two lists in sync** — a column in `columns.value`
  with no matching `columns.schema[]` entry is hidden and may not be written.
  Not used here (everything is `executeQuery`), but relevant if that changes.
- **Newlines double-escape.** A literal `\n` in a JS string becomes a real
  newline in the stored expression and breaks it; write `\\n`.
- **`.replace()` with `$` in the replacement** treats `$` as a backreference.
  When patching `jsCode`, use `str.split(old).join(new)`.

## Killing a stuck execution

`DELETE /api/v1/executions/:id` — this both stops and removes it.
`POST /api/v1/executions/:id/stop` 404s on most versions.
