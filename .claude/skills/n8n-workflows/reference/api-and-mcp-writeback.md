# Programmatic write-back: REST API and MCP

Read this **before** the first programmatic edit to any workflow in
`n8n/demo-data/workflows/`. Everything here is currently hypothetical for this
repo — all ten workflows were authored in the UI, so none of these hazards has
fired yet.

---

## Two write paths, two auth schemes

| Path | Endpoint | Auth | Notes |
|---|---|---|---|
| Public REST API | `http://localhost:5678/api/v1/…` | `X-N8N-API-KEY` header | ✅ enabled (returns 401, not 404). No key in `.env` — mint one in the n8n UI under Settings → n8n API |
| Official MCP server | `http://localhost:5678/mcp-server/http` | `Authorization: Bearer <JWT>` | Token lives in `~/.claude.json`. Gated per workflow by `settings.availableInMCP` |

Only `cap-brainstorm-pairing`, `chat-agent`, and `wf-step-retrieve` have
`availableInMCP: true`. The other seven checked-in workflows cannot be read or
written over MCP until that toggle is flipped on the workflow card.

The MCP server's authoring model is the **TypeScript Workflow SDK**
(`create_workflow_from_code`), not raw node JSON. Start from `get_sdk_reference`
and `get_suggested_nodes` rather than hand-writing nodes.

---

## The `$input` question — settle it before editing

Upstream claims a REST `PUT` silently strips the `$input` prefix from Code node
`jsCode`, turning `$input.first().json` into `.first().json` — a syntax error
that only surfaces at run time.

**This is untested on this instance, and it matters:** 14 Code nodes here use
`$input`, including `Normalise input` and `Return rows` in `wf-step-retrieve`,
which is on the live retrieval path.

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
the same body back and re-read to cover the update path too. Delete the scratch
workflow afterwards. If `$input` is stripped, migrate the 14 sites to `$json` and
`$('Node Name')` **before** any real edit; if it survives, record that here and
stop worrying about it.

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
