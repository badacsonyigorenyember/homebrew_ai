---
name: n8n-workflows
description: >
  Working knowledge of this project's n8n layer — node parameter forms,
  execution-model semantics, sub-workflow contracts, and the hazards that only
  appear when a workflow is written back programmatically. Use when building,
  editing, debugging, or reviewing anything under n8n/demo-data/workflows/, when
  driving the n8n MCP server, or when an execution behaves in a way the canvas
  does not explain.
---

# n8n Workflows — this stack

Adapted from [WASD-Team/n8n-claude-skill](https://github.com/WASD-Team/n8n-claude-skill)
(no licence declared upstream; content here is rewritten and cut down to what
this repo actually uses). **Every claim below is tagged with its evidence.**
Upstream contains at least one assertion this repo empirically disproves, so
treat untagged upstream material as a hypothesis, not a fact.

| Tag | Meaning |
|---|---|
| ✅ **verified here** | Checked against `n8n/demo-data/workflows/*.json` on 2026-09-13 |
| ⚠️ **unverified** | Upstream claim, plausible, not yet tested on this instance |
| ❌ **false here** | Upstream claim this repo contradicts |

---

## What this repo actually runs

Node inventory across the ten checked-in workflows (✅ verified here):

```
 23  n8n-nodes-base.postgres              v2.6   (all executeQuery)
 23  n8n-nodes-base.code                  v2
  9  n8n-nodes-base.executeWorkflow       v1.3
  8  n8n-nodes-base.httpRequest           v4.4
  5  n8n-nodes-base.manualTrigger         v1
  4  n8n-nodes-base.readWriteFile         v1.1
  4  n8n-nodes-base.executeWorkflowTrigger v1.2
  2  n8n-nodes-base.crypto                v2
  2  n8n-nodes-base.splitInBatches        v3
  2  @n8n/n8n-nodes-langchain.toolWorkflow v2.2
  3  n8n-nodes-base.if                    v2.2 / v2.3
  1  n8n-nodes-base.set                   v3.4
  1  n8n-nodes-base.extractFromFile       v1.1
  1  @n8n/n8n-nodes-langchain.chatTrigger v1.4
  1  @n8n/n8n-nodes-langchain.agent       v3.1
  1  @n8n/n8n-nodes-langchain.lmChatOllama v1
  1  @n8n/n8n-nodes-langchain.memoryPostgresChat v1.4
  1  n8n-nodes-base.wait                  v1.1
  1  n8n-nodes-base.noOp                  v1
```

Every workflow carries `settings: {"executionOrder": "v1", "binaryMode": "separate"}`.
Ignore upstream guidance about Telegram, Slack, Google Sheets/Drive, Switch,
Merge, Webhook — none are used here.

---

## The three rules that matter most here

### 1. Postgres: parameterise, never interpolate ✅ verified here

All 23 Postgres nodes are `executeQuery` on typeVersion **2.6**, and all 23 pass
values through `options.queryReplacement` as `$1/$2` positional parameters. Not
one has `{{ }}` inside the `query` field.

```json
{
  "operation": "executeQuery",
  "query": "SELECT * FROM nlq.search_knowledge($1, $2::vector, $3, $4)",
  "options": { "queryReplacement": "={{ [$json.query, $json.embedding, $json.top_k, $json.doc_type] }}" }
}
```

**Keep it that way.** Upstream flags 2.6 + `executeQuery` as an anti-pattern
because 2.6 rewrites `{{ }}` → `={{ }}` in `query` on save, which then fails as
invalid SQL. That rewrite has nothing to act on here, which is why 2.6 is safe
in this repo and why no typeVersion migration is needed. The moment someone adds
a `{{ }}` to a `query` field, the hazard becomes live — so don't.

Corollaries:
- `={{ }}` is valid in `queryReplacement` (JS evaluation) and invalid in `query`
  (template substitution). The two fields do not work the same way.
- An `INSERT` as a sub-workflow's terminal node returns no items, and the parent
  fails with *"No item to return was found"*. Add `RETURNING true AS ok`.
  ✅ verified here — `wf1-ingest-book` ends on `Log ingest summary`, not an insert.

### 2. Execution is depth-first, and every node fires once per item ⚠️ unverified

Fan-out is sequential, topmost child first (smallest Y). A branch can read an
*earlier* sibling's output via `$('Node').first().json`; it cannot read a later
one. Only Merge waits.

Separately: if a node emits N items, every downstream node runs N times. This is
the usual cause of duplicate SQL writes. Guard with `$itemIndex === 0`, aggregate
upstream, or re-root the branch at a single-item source.

Relevant here because `ingest-bjcp-styles` and `wf1-ingest-book` both drive
`splitInBatches` loops into Postgres inserts.

### 3. `$input` may not survive an API write-back ⚠️ unverified — 14 sites at risk

Upstream claims the REST API strips the `$input` prefix on `PUT`, leaving
`.first().json` — a syntax error. Not yet tested on this instance, but the blast
radius is known (✅ verified here):

```
cap-brainstorm-pairing  Unpack parse, Build pack, Step 4 · ground,
                        Not in library, Wrap answer
chat-agent              Prep turn
ingest-bjcp-styles      Parse + validate styles, Assemble embed input
wf-step-llm             Render prompt, Validate output
wf-step-retrieve        Normalise input, Return rows
wf1-ingest-book         Assert task finished, Assemble embed input
```

These are fine today because every workflow here was authored in the UI. They
become a risk the first time anything saves a workflow through the REST API —
**which includes the n8n MCP server**. See
[`reference/api-and-mcp-writeback.md`](reference/api-and-mcp-writeback.md) for a
cheap round-trip test to settle this before the first programmatic edit.

---

## Corrections to upstream

### `specifyBody: 'json'` on POST is **not** broken here ❌ false here

Upstream calls it an anti-pattern that silently sends an empty body, and
prescribes a `contentType: "raw"` workaround. This repo has five POST nodes using
`specifyBody: 'json'` — `Ollama embed` (×3), `Call Ollama`, `Embed query` — and
the corpus is ingested and retrieval returns rows, so the bodies demonstrably
arrive. Do not "fix" these.

### `executeWorkflowTrigger` is v1.2 here, not v1.1 or v1.3 ✅ verified here

Upstream documents v1.1. All four sub-workflow triggers here are **v1.2**, and
all nine callers are `executeWorkflow` **v1.3** with `mode: 'list'` — already
matching upstream's rule. Worth knowing: `mode: 'once'` (all items in one call)
was the v1.2 default and `mode: 'each'` is the v1.3 default, so a trigger/caller
version mismatch changes fan-out semantics silently.

---

## Sub-workflow contract used here

`cap-brainstorm-pairing` composes `wf-step-llm` and `wf-step-retrieve` over five
steps; the four `ingest-*` launchers call `wf1-ingest-book`. The contract:

- Both sides must declare fields. The parent needs `workflowInputs.value` **and**
  `workflowInputs.schema[]`; the trigger needs `workflowInputs.values[]`. If
  either is empty, data passes as empty — silently.
- `convertFieldsToString: false` on both sides, or `null` arrives as `"null"`.
- After a synchronous `executeWorkflow`, item pairing breaks: use
  `.first().json`, never `.item.json`. ⚠️ unverified here, but consistent with
  `cap-brainstorm-pairing` using `$input.first()` after every step call.
- `active: false` does not prevent a workflow being called — it only disables its
  own triggers. Handy for utility sub-workflows.
- MCP visibility is a *separate* per-workflow gate: `settings.availableInMCP`.
  Only `cap-brainstorm-pairing`(live), `chat-agent`, and `wf-step-retrieve` have
  it on; the other nine cannot be read or edited over MCP.

---

## Reference files

Load on demand — do not read all of these up front.

| File | Read when |
|---|---|
| [`reference/execution-model.md`](reference/execution-model.md) | An execution produces duplicate writes, stalls, or nulls |
| [`reference/node-parameters.md`](reference/node-parameters.md) | Hand-editing workflow JSON for a node used in this repo |
| [`reference/api-and-mcp-writeback.md`](reference/api-and-mcp-writeback.md) | Before the first programmatic workflow edit |
| [`reference/testing.md`](reference/testing.md) | Changing a workflow that has already run against real data |
