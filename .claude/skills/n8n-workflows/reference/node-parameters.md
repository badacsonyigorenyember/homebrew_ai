# Node parameter forms

Only the nodes this repo actually uses. Condensed from
[WASD-Team/n8n-claude-skill](https://github.com/WASD-Team/n8n-claude-skill),
with this repo's conventions marked ✅.

---

## Postgres — `n8n-nodes-base.postgres`

| typeVersion | Behaviour | Use for |
|---|---|---|
| 2.3 | Stores `{{ }}` as-is | `executeQuery` (most conservative) |
| 2.5 | Stores `{{ }}` correctly | `executeQuery` (upstream's preference) |
| 2.6 | Rewrites `{{ }}` → `={{ }}` in `query` on save | `select`/`insert`/`update`, **and `executeQuery` provided `query` holds no `{{ }}`** |

✅ **This repo: 23 nodes, all 2.6 / `executeQuery`, all parameterised.** Values go
through `options.queryReplacement` as `$1/$2`; no `query` field contains `{{ }}`.
The 2.6 rewrite therefore has nothing to act on. Follow the same form:

```json
{
  "operation": "executeQuery",
  "query": "SELECT * FROM nlq.search_knowledge($1, $2::vector, $3, $4)",
  "options": {
    "queryReplacement": "={{ [$json.query, $json.embedding, $json.top_k, $json.doc_type] }}"
  }
}
```

- `query` is **template substitution** — `={{ }}` there is invalid SQL.
- `queryReplacement` is **JS evaluation** — `={{ }}` is required there.
- Parameterising is also the fix for SQL injection; interpolating a user-supplied
  value into `query` is the textbook hole.
- An `INSERT` with no `RETURNING` emits no items. As a sub-workflow terminal that
  fails the parent with *"No item to return was found"*. Add `RETURNING true AS ok`.

Quirks worth knowing: `{{ null }}` renders as the string `"null"` — wrap with
`NULLIF(NULLIF($1, ''), 'null')` if a null can reach SQL. Inside a Code node,
JS template literals and n8n's `{{ }}` collide; build SQL with concatenation.

## HTTP Request — `n8n-nodes-base.httpRequest` v4.4

✅ **This repo uses `specifyBody: 'json'` + `jsonBody` for POST and it works** —
`Ollama embed` (×3), `Call Ollama`, `Embed query`. Upstream calls this broken and
prescribes a `contentType: "raw"` workaround; that is false on this n8n version.
Do not change these nodes.

`Docling submit` uses `contentType: "multipart-form-data"` for the file upload.

Keep HTTP calls in HTTP Request nodes, not in Code nodes — a Code node doing raw
`https.request()` is invisible in the execution view and skips retry handling.

## Code — `n8n-nodes-base.code` v2

Code nodes are for **transformation**, not side effects. See
`api-and-mcp-writeback.md` before introducing or editing `$input` usage.

## Execute Workflow — `n8n-nodes-base.executeWorkflow` v1.3

✅ All nine callers here are v1.3 with `mode: 'list'`, which is the correct form.

```json
{
  "workflowId": { "__rl": true, "value": "cCt9O4NyNPyegHBq", "mode": "list",
                  "cachedResultName": "wf-step-retrieve" },
  "workflowInputs": {
    "mappingMode": "defineBelow",
    "value": { "query": "={{ $json.query }}", "top_k": "={{ $json.top_k }}" },
    "schema": [
      { "id": "query", "displayName": "query", "type": "string",
        "required": false, "defaultMatch": false, "display": true,
        "canBeUsedToMatch": true, "removed": false }
    ],
    "attemptToConvertTypes": false,
    "convertFieldsToString": false
  },
  "options": {}
}
```

- Never `mode: 'id'` — with v1.1 it makes `$('Node')` silently return null.
- `convertFieldsToString: false`, or `null` becomes the string `"null"`.
- Fire-and-forget is `options.waitForSubWorkflow: false`; its output must be a
  dead end, never wired into Merge or a shared downstream.
- A sub-workflow does **not** need `active: true` to be callable.

## Execute Workflow Trigger — `n8n-nodes-base.executeWorkflowTrigger`

✅ **v1.2 here**, not the v1.1 upstream documents. Declares what the child expects:

```json
{ "workflowInputs": { "values": [
    { "name": "query",  "type": "string" },
    { "name": "top_k",  "type": "number" },
    { "name": "mode",   "type": "string" } ] } }
```

Types: `string`, `number`, `boolean`, `object`, `array`. **Both sides must
declare their fields** — parent `value` + `schema`, child `values`. If either is
empty, data passes as empty with no error.

Note the default fan-out mode changed across versions: `once` (all items in one
call) was the v1.2 default, `each` (one call per item) the v1.3 default.

## Split In Batches — `n8n-nodes-base.splitInBatches` v3

The loop node behind both embedding loops. Remember the "fires once per item"
rule: everything downstream of the loop body runs per batch.

## IF — `n8n-nodes-base.if` v2.2 / v2.3

`conditions` must be the object form `{options, conditions, combinator}`. A bare
array is accepted on write but breaks the UI and runtime.

## Set — `n8n-nodes-base.set` v3.4 · Wait — v1.1 · NoOp / Crypto / Read-Write File

Used in single spots here; no known traps beyond the item-count rule.
