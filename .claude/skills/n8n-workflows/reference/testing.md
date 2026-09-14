# Testing workflow changes

Condensed from [WASD-Team/n8n-claude-skill](https://github.com/WASD-Team/n8n-claude-skill)
and narrowed to this stack, which is batch ingest plus a chat path — not the
high-volume webhook traffic upstream assumes.

---

## Replay, don't wait

After changing transformation logic, replay a known input immediately rather
than waiting for live data. Ramp, never jump:

```
1. fix          2. replay ONE known-good input      3. diff against expected
4. replay 10–20 5. replay the rest                  6. regression -> back to 1
```

## Where inputs come from here

- **Execution history.** `GET /api/v1/executions?workflowId=<id>&limit=500`, then
  `?includeData=true` per execution for the full input. Upstream's rate-limit
  spacing advice is aimed at Google Sheets and Telegram and does not apply — the
  only external calls here are local Ollama and Docling.
- **The corpus itself.** Ingest is idempotent by `file_sha256`
  (`kb.document_versions` has a unique constraint on it), so re-running an
  ingest launcher against an already-ingested PDF exercises the dedup path
  rather than duplicating rows. That makes ingest workflows unusually safe to
  replay.
- **`obs.runs` / `obs.steps`.** The observability schema already records step
  inputs and outputs for the conversational path — that is the natural fixture
  source for `wf-step-llm` and `cap-brainstorm-pairing` replays, and it is what
  the Phase 3 eval workflow is meant to consume.

## Don't measure a stale execution

The classic trap: you save a fix, open "the latest execution", and it is traffic
that landed milliseconds before your write. Compare an execution's `startedAt`
against the workflow's `updatedAt`, or match on an identifier you injected, so
you know which code produced the output.

## What to check after touching a workflow here

- **Item counts.** A change in how many items a node emits silently changes how
  many times every downstream node fires. Check the loop bodies in
  `wf1-ingest-book` and `ingest-bjcp-styles`.
- **The promotion gate.** `kb.promote_version` only flips `is_current` once every
  chunk has an embedding; a partial ingest leaves the version invisible rather
  than half-live. Assert on `promote_version`'s returned `missing` count, which
  `wf1-ingest-book` already does in `Assert promoted`.
- **`kb.ingest_log`.** Every drop is supposed to be logged with a reason. A silent
  run with no log rows is itself a failure signal.
- **Sub-workflow contracts.** If you add a field on one side of an
  `executeWorkflow`/`executeWorkflowTrigger` pair and not the other, it passes as
  empty with no error. Change both sides in the same edit.

## Cleaning up

`DELETE /api/v1/executions/:id` stops and removes a stuck execution. For DB
state, re-ingest is idempotent; to genuinely start over on one document, delete
the `kb.document_versions` row and let the cascade take its chunks and
embeddings with it.
