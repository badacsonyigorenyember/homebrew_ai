# Execution model

Why a workflow does something the canvas does not explain. Condensed from
[WASD-Team/n8n-claude-skill](https://github.com/WASD-Team/n8n-claude-skill).
Unless marked ✅, these are upstream claims not yet tested on this instance.

---

## Fan-out is depth-first, not parallel

When a node feeds several children from one output port, n8n fires the **topmost**
child (smallest Y on the canvas) and runs that branch to its terminal node, then
starts the next sibling down.

- A branch **can** read an earlier sibling's output: `$('END_A').first().json`.
- A branch **cannot** read a later sibling's — it returns `null`.
- **Merge is the only node that waits** for all its inputs.

Consequence: never let branch ordering carry a dependency. If step B needs what
step A wrote, wire B from A's output, not from a shared parent with A above it.

## Every downstream node fires once per incoming item

N items in means every downstream node runs N times — including IF nodes, Set
nodes, and side-effect nodes. This is the usual cause of duplicate SQL writes.

Three fixes, in order of preference:
1. **Aggregate upstream** so the branch starts from one item.
2. **Re-root** the "run once" branch at an earlier single-item source.
3. **Guard** with a second IF condition: `{{ $itemIndex }}` equals `0`.

Relevant here: `wf1-ingest-book` and `ingest-bjcp-styles` both drive
`splitInBatches` loops into Postgres inserts, so item counts are load-bearing.

## Merge semantics

- **Append** (default): 2 items + 3 items → 5 items out; downstream fires 5 times.
- **Combine** with `mergeByPosition` or `mergeByFields` joins across inputs.
- **The stall trap:** an async fire-and-forget branch emits nothing, so a Merge
  waiting on it waits forever. Async branches must be dead ends.

## Item pairing breaks after a synchronous Execute Workflow

Downstream of a sync `executeWorkflow`, `.item.json` silently returns `null`.
Use `.first().json`.

✅ Consistent with this repo: every step in `cap-brainstorm-pairing` reads
`$input.first()` after its `executeWorkflow` call.

## Expression cheat sheet

| Expression | Meaning | Use for |
|---|---|---|
| `$json.field` | Current item | Per-item transforms |
| `$('Node').first().json` | First item of a named node | Config and single-value lookups |
| `$('Node').all()` | All items of a named node | Collect / reduce |
| `$('Node').item.json` | Paired upstream item | Avoid — breaks after Execute Workflow |
| `$input.first()` / `$input.all()` | This Code node's own input | ⚠️ may not survive an API write-back — see `api-and-mcp-writeback.md` |
| `$itemIndex` | 0-based item index | "Run once" guards |
| `$runIndex` | 0-based run index | Retry / backoff loops |

## Settings

`settings.executionOrder` is `"v1"` on all ten workflows here ✅ — keep it. This
is per-workflow and unrelated to instance-level queue mode.

## Workers

Each running execution holds a worker; a synchronous sub-workflow holds an extra
one while the child runs. Suspended `Wait` nodes hold theirs indefinitely. On
self-hosted n8n the ceiling is `N8N_CONCURRENCY_PRODUCTION_LIMIT`.

`wf1-ingest-book` has a `Wait 15s` node inside its Docling poll loop — bounded and
fine, but it is the one place here where executions accumulate.
