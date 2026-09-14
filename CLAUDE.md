# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

# Project: AI Homebrew Assistant

Operational facts about this stack. Verified 2026-09-13.

## Stack layout

Self-hosted Supabase + n8n via Docker Compose. Kong fronts everything on
`localhost:8000`. Key containers: `supabase-kong`, `supabase-db`, `supabase-studio`,
`supabase-meta`.

Run `docker compose` from the **main checkout only**, never from a worktree — a
worktree has no `.env` and the changed project name causes container name conflicts.

Schemas in use: `brew` (recipes, batches, measurements), `kb` (documents, chunks,
embeddings), `obs` (runs, steps, prompts, profiles), plus stock `auth`/`storage`/`public`.

`kb.chunks` carries a table comment that is a real architectural rule: **knowledge only —
never insert data derived from `brew.*`**.

## Postgres access

**`postgres` is not a superuser here.** Superuser-level DDL (altering reserved roles,
etc.) fails with *"reserved role, only superusers can modify it"*. Use `supabase_admin`:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "<sql>"
```

Editing `supabase/docker/volumes/api/kong.yml` requires **recreating** the container, not
restarting it — it is a single-file bind mount, so `restart` silently keeps the old config.

`db-init` applies a hardcoded list of `.sql` files on every stack start. A **new** `.sql`
must be added to that list, and the catalog should be checked before assuming an object
is missing.

## Supabase MCP server (`localhost:8000/mcp`)

Configured in `.mcp.json` as `supabase-local`, type `http`. Kong routes `/mcp` →
`studio:3000/api/mcp`. Note `/api/mcp` is separately blocked with a 403 by design; only
`/mcp` is the live path.

Studio opens **two** Postgres connections from the same `POSTGRES_PASSWORD`:

- read-write as `supabase_admin` — `execute_sql`, `apply_migration`, `get_advisors`,
  `list_migrations`
- read-only as `supabase_read_only_user` — `list_tables`, `list_extensions`,
  `generate_typescript_types`

Upstream ships the read-only role with **no password**
(`supabase/docker/utils/db-passwd.sh` states it "is not supposed to have a password"), so
the read-path tools fail with `password authentication failed for user
"supabase_read_only_user"`. `generate_typescript_types` surfaces the same fault as a
misleading Kong 502, not an auth error.

Fix — already applied, but `db-passwd.sh` rotates `POSTGRES_PASSWORD` while skipping this
role, so **re-run after every rotation**:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres \
  -c "ALTER USER supabase_read_only_user WITH PASSWORD '$(grep -E '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)'"
```

The password lives in the persisted DB volume and no init script resets it, so ordinary
stack restarts are safe.

`get_logs` is **permanently broken** in this stack (`TypeError: fetch failed`) — there is
no analytics/logflare container. Do not try to fix it with config; it needs that service
added to `docker-compose.yml`.

## n8n

To run a workflow headlessly via the CLI while the n8n server is up, override
`N8N_RUNNERS_BROKER_PORT` — otherwise the broker port clashes with the running server.

The **`n8n-workflows` skill** (`.claude/skills/n8n-workflows/`) holds this repo's node
conventions and the write-back hazards. Its claims are evidence-tagged because the
upstream it derives from is unreliable unmarked — do not restate one as fact without
the tag.

## Docling

`docling-serve` runs as container `docling` on :5001 under the **`gpu-amd`** profile —
verified 2026-09-13 against `docker ps` (`com.docker.compose.service = docling-gpu-amd`).
All three profiles define a Docling service; `gpu-amd` runs the **same base image** as
`cpu` (`ghcr.io/docling-project/docling-serve:main`) with `/dev/kfd` + `/dev/dri` attached
and the `video`/`render` groups added — there is no separate ROCm *image*, which is what
the earlier "no `gpu-amd` variant" note was reaching for. Only `gpu-nvidia` swaps the image
(`docling-serve-cu126`). `wf1-ingest-book` drives it
asynchronously: `POST /v1/chunk/hybrid/file/async` -> `GET /v1/status/poll/{task_id}` ->
`GET /v1/result/{task_id}`.

The `/docling` skill also documents a local CLI and Python SDK path. Use that only for
throwaway inspection of a file. **Anything destined for `kb.*` must go through
docling-serve**, because `kb.document_versions` records `docling_version` and
`chunker_config` as provenance — a locally-converted document produces chunks whose
origin cannot be reproduced. The same applies to the `pdf` skill, which should never
touch the corpus.

## Known outstanding issues

- `public.n8n_chat_histories` (42 rows) has RLS disabled, **0** policies, and `anon` holds
  the full DML set including `DELETE` and `TRUNCATE`. Verified 2026-09-13: an anon-key
  request to `http://localhost:8000/rest/v1/n8n_chat_histories` returns real rows. `kb` is
  **not** exposed (404), so the blast radius is `public` only. Now architecture §13.1 **R6**,
  with the cheapest fix (`REVOKE ALL … FROM anon, authenticated`).
- Four functions have mutable `search_path`: `kb.promote_version`, `brew.f_abv`,
  `brew.f_dry_hop_rate_g_per_l`, `obs.f_prompt_hash`. ⚠️ **None of them is
  `SECURITY DEFINER`** (`prosecdef = false`), so this is not the escalation hole
  architecture §8.4 Layer 2 warns about — all seven `SECURITY DEFINER` functions do set
  `search_path`, verified 2026-09-13. Worth fixing in the owning `db/init` file; not a
  reason to rewrite §8.4.
- `vector`, `pg_trgm`, and `unaccent` are installed in the `public` schema.
- **Untested, and it is two questions, not one:** whether (a) an n8n REST `PUT` or (b) the
  MCP server's SDK `update_workflow` strips the `$input` prefix from Code node `jsCode`.
  They are different write paths and may answer differently. 14 Code nodes rely on `$input`,
  including two on the live retrieval path in `wf-step-retrieve`. Settle both before the
  first programmatic workflow edit — test procedure in
  `.claude/skills/n8n-workflows/reference/api-and-mcp-writeback.md`. The write-path decision
  itself is architecture §13.2 **D39**.
- **Archiving a workflow is not deleting it.** The row stays in `workflow_entity`, so a
  query filtering by `name` still sees it. This is what killed `scripts/stress/tier1_routing.py`
  on 2026-09-13; that script now filters `isArchived`. There is **no `delete:workflow` in the
  n8n CLI** — deletion is the UI or a `DELETE` on `workflow_entity` (all FKs cascade except
  `workflow_published_version`, which restricts).
- `n8n/demo-data/workflows/` must match the live instance 1:1 (standing rule 4). Reconcile
  with the `comm` one-liner in `README.md`; `measured` 2026-09-13: **11 live = 11 tracked**.
