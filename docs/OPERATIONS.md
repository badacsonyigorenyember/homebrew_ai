# Operations notes

How the running stack behaves and the traps already hit. Linked from `CLAUDE.md` and
`PROJECT.md` §4. Facts are marked with the date they were last checked.

## 1. State of the stack after the reset

*Checked 2026-10-09, re-checked 2026-10-11 (`searxng` still `Exited (127)`, every other
service up).*

- The containers belong to compose project `aihomebrewassistant`, with working directory
  this repo's root. Every one has restart policy `unless-stopped`, so they come back after a
  reboot.
- **`searxng` is down**: `Exited (127)` since 2026-10-08 18:48 UTC. Its bind-mounted
  `searxng/settings.yml` was removed in the reset and is now a root-owned placeholder directory,
  so the container fails with "not a directory" (the trap in §3). The file is in the archive tag.
  Recovering it is separate work. Until then a `docker compose up -d` fails on `searxng`, and
  `webarm` (which `depends_on` a healthy `searxng`) can't be started through compose.
- **The compose definition is back in the repo** (2026-10-09, `recover-stack`):
  `docker-compose.yml`, `supabase/docker/docker-compose.yml`, the bind-mounted Supabase files
  (`volumes/db/*.sql`, `volumes/api/kong.yml` + `kong-entrypoint.sh`, `volumes/pooler/pooler.exs`)
  and the edge-functions entrypoint `volumes/functions/main/index.ts`, all restored from the
  archive tag. `docker compose config -q` passes and `docker compose ps` sees the running
  containers.
- The **`db-init` service was removed** from the restored compose file, because it applied the
  old schema list. The old `db/init/*.sql` schema files were not restored.
- `supabase-kong` can be recreated again: its config comes from `volumes/api/kong.yml` in the
  repo. Recreating still follows the rules in §3 (main checkout only, `--no-deps`).

## 2. Machine-level constraints

- **This stack and `~/AI/self-hosted-ai-starter-kit` cannot run at the same time.** This
  project was rebuilt from that starter kit and keeps its hardcoded container names
  (`supabase-db`, `n8n`, `ollama`, …) and host ports (5432, 8000, 5678, 8080, 5001, 11434).
  Stop one before starting the other.
- Hardware: Ryzen 9 9900X, Radeon RX 9070 XT (gfx1201, 16 GB), 32 GB RAM.

## 3. Compose rules

- **Run compose only from the main checkout**, never from `.claude/worktrees/*`. Compose takes
  the project name from the directory, and a worktree has no `.env` (it is gitignored). The
  result is a second stack with blank secrets, which then dies on container-name conflicts and
  leaves a stray `<dir>_default` network behind. Remove that with `docker network rm` once
  `docker network inspect` shows no containers.
- **Single-file bind mounts need a recreate, not a restart.** Editors save via
  write-temp-then-rename, which gives the file a new inode. The container keeps reading the
  old one. After editing `kong.yml`, run `docker compose up -d --no-deps --force-recreate kong`,
  then confirm inside the container (`docker exec supabase-kong grep … /home/kong/temp.yml`).
- **A bind-mounted file deleted on the host becomes an empty root-owned directory.** On the
  next container start Docker creates the missing source path as a directory, and the container
  fails with "not a directory" (or, for a mounted code directory, can't find its entrypoint).
  This took down `supabase-db`, `-kong`, `-pooler` and `-edge-functions` after the reset
  (2026-10-08), and `searxng` (`searxng/settings.yml`, still down, see §1). Fix: stop the
  container, remove the placeholder directory (root-owned, so the user runs `sudo rmdir`),
  restore the file, `docker start` again.
- The old `db-init` service ran a **hardcoded** file list, not a glob. A new `.sql` file
  never ran until it was added to that list, and the list order was the execution order. If
  `db-init` comes back, keep that in mind or make it glob.

## 4. Database (self-hosted Supabase)

- **Roles.** `postgres` is *not* a superuser here. `supabase_admin` is. *(Checked 2026-10-08.)*
- **Supabase MCP is read-only on purpose.** `.mcp.json` points at
  `http://localhost:8000/mcp?read_only=true` (Studio's MCP endpoint, routed through Kong).
  Queries run as `supabase_read_only_user`. Use it for inspection only.
- **Schema changes go through SQL files in the repo, applied as `postgres`:**

  ```bash
  docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql
  ```

  Why not MCP or `-U supabase_admin`: objects created that way are **owned by
  `supabase_admin`**. n8n's Postgres credential (connecting as `postgres`) then gets
  `permission denied`, and any later script run as `postgres` fails with
  `must be owner of …`. If a mis-owned object turns up, fix that object only
  (`ALTER … OWNER TO postgres`). Never mass-reassign owners: `SECURITY DEFINER` functions run
  as their owner, so changing the owner changes what they can do.
- **The read-only role needs a password.** Upstream ships `supabase_read_only_user` without
  one, which breaks the MCP read tools (`list_tables`, `list_extensions`, …) with
  `password authentication failed`. The fix lives in the DB volume and survives restarts, but
  **re-run it after any `POSTGRES_PASSWORD` rotation** (`db-passwd.sh` skips this role):

  ```bash
  docker exec supabase-db psql -U supabase_admin -d postgres \
    -c "ALTER USER supabase_read_only_user WITH PASSWORD '<POSTGRES_PASSWORD>'"
  ```

  *Working as of 2026-10-08.*
- MCP `get_logs` is permanently broken (`fetch failed`). There is no analytics/logflare
  container in this stack.
- **Check the catalog before believing a status.** Before treating a DB object as missing,
  query `pg_proc`, `pg_roles`, `pg_indexes` or `information_schema`. Written notes have been
  wrong about this before.

## 5. n8n

- The MCP server is **n8n's official one** (`http://localhost:5678/mcp-server/http`, Workflow
  SDK, TypeScript authoring). It is configured in local scope (`~/.claude.json`), because its
  bearer token must not be committed. To re-add it on another machine:
  `claude mcp add --transport http n8n-mcp http://localhost:5678/mcp-server/http --header "Authorization: Bearer <token>"`.
- The **`n8n-skills@n8n-io`** plugin (the official skill pack, enabled in
  `.claude/settings.json`) matches that server. The community `n8n-mcp-skills` pack targets a
  different server and was removed on 2026-09-13. Don't reinstall it.
- **Running a workflow headlessly while the server is up** needs a different task-broker
  port, or the CLI fails with "port 5679 is already in use":

  ```bash
  docker exec -e N8N_RUNNERS_BROKER_PORT=5699 -e N8N_RUNNERS_BROKER_LISTEN_ADDRESS=127.0.0.1 n8n n8n execute --id=<id>
  ```

  Files exported from the container are root-owned: `docker exec n8n chown 1000:1000 <path>`.
- **The pipeline webhook** is `POST http://localhost:5678/webhook/recipe-pipeline` with body
  `{"request": "...", "brief_id": "b01", "model": "...", "think": false, "guide": "any", "temperature": 0, "seed": 42}` (`brief_id`, `model`, `think`, `guide`, `temperature` and `seed` optional; `temperature` and `seed` go to step 1's Ollama call, defaults 0 and 42; `guide` is `any`, `bjcp` or `ba`: when it is not sent, a guide named in the request text restricts the pick, else `any`; a bad value fails at step 2; defaults `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K` and `false`). It
  answers after the run ends with `{run_id, ok, failed_step?, error?}`; the record is in
  `app.run` and `app.run_step`. No auth for now (revisit with the chat trigger, M8). The four
  workflows must be **published**. Publish a sub-workflow after editing it too: an Execute Workflow
  node runs the **published** version of the workflow it calls, not the draft (measured 2026-10-12: the
  pipeline's draft was published first, and its call to the still-published old `Step 1` ran the old
  nodes). Run `python -m evals.workflows` after every workflow change, then commit the files.
- **The MCP cannot set `onError`** (`addNode` accepts the field and drops it). To add a node with
  an error output to a published workflow, edit its JSON in `n8n/workflows/`, copy it to
  `shared/`, run `docker exec -e N8N_RUNNERS_BROKER_PORT=5699 -e N8N_RUNNERS_BROKER_LISTEN_ADDRESS=127.0.0.1 n8n n8n import:workflow --input=/data/shared/<file>`
  (it keeps the id and deactivates the workflow), publish through the MCP and delete the copy.
- **A null sub-workflow input arrives as missing.** Read it with `?? null` inside the sub-workflow
  (step 2's `guide_preference`).
- **Running a workflow from the editor.** Each workflow has a `Test data` sticky note with
  ready-to-paste JSON: pin it on `POST recipe-pipeline` (`Recipe pipeline`) or on `When Executed
  by Another Workflow` (`Step 1 · read request`, `Step 2 · best-fit style`, `Check contract`), then click *Execute workflow*.
  A pipeline run writes a real run log tagged `editor-b01`; open the step 1 sub-execution from the
  `Step 1 · read request` node. Remove editor runs with
  `docker exec supabase-db psql -U postgres -d postgres -c "delete from app.run where eval_id like 'editor-%'"`
  (steps cascade). Webhook calls ignore pins (`test_webhook_ignores_pin`). Pins are not exported,
  so no re-export after pinning, but an edited note is a workflow change and needs one. Keep
  `brief_id` starting with `editor-` when changing the sample.
- **Step 1 calls Ollama** with an HTTP Request node: `POST http://ollama:11434/api/chat` (n8n and
  Ollama share the compose network), body `{model, think, stream: false, format: <step 1 output
  contract>, options: {temperature: <input, default 0>, seed: <input, default 42>, num_ctx: 8192, num_predict: 4096}, messages}`,
  timeout 30 min. The system prompt is `shared/prompts/step1.system.md`, read by the workflow from
  `/data/shared`. The n8n `Ollama Chat Model` node is not used (no `seed`, no JSON schema, no token
  counts). `num_ctx` must equal `evals/benchmark.py` `NUM_CTX` (`test_num_ctx_matches_benchmark`).
- **The `Postgres account` credential** connects as `postgres` to database `postgres` on
  `supabase-db:5432` (measured 2026-10-12 with `select current_user, current_database()`), so
  the `app` tables and `extensions.jsonschema_validation_errors` are reachable. The password was
  entered in the n8n UI by the user.
- **Exporting workflows into the repo:** `python -m evals.workflows` writes
  `n8n/workflows/<name>.json`. It runs `n8n export:workflow --all --output=/data/shared/.n8n-export.json`
  (stdout has log lines, so the file route is used), reads `shared/.n8n-export.json` and removes
  it. Archived workflows are skipped. With no workflows n8n exits 1 with "No workflows found"; the tool treats that as empty.
  `n8n/` is root-owned (docker-created); `n8n/workflows/` was created with a one-off
  `docker run --user 0 --entrypoint mkdir/chown -v $PWD/n8n:/w n8nio/n8n:latest`.

## 6. Ollama (ROCm)

- On every start Ollama logs `dropping ROCm device … gfx1036 … set HSA_OVERRIDE_GFX_VERSION`.
  That is the Raphael **iGPU** being correctly dropped. The RX 9070 XT is picked up on the same
  boot. **Do not set `HSA_OVERRIDE_GFX_VERSION`.** It would break the working discrete GPU.
  Check `docker logs ollama | grep "inference compute"` for `compute=gfx1201`, and
  `docker exec ollama ollama ps` for `100% GPU`.
- Models pulled *(checked 2026-10-13)*: `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K` (the chat
  default, D2), `gemma4:31b-it-qat`, `gemma4:26b-a4b-it-qat`, `gemma4:12b-it-q8_0`, `gemma4:12b`,
  `qwen3.8:27b` (also listed as `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q4_K_M`, same model ID), plus the
  embedding model `bge-m3`. The Q6_K model runs 36%/64% CPU/GPU on the 16 GB GPU.

## 7. Claude Code guardrails

`.claude/hooks/guard.sh` runs before every Bash, Read, Edit and Write call, in every
permission mode. It blocks:

- `docker compose down -v` / `--volumes`, `docker volume rm|prune`, `docker system prune`
- `rm`/`mv`/`chmod`/… on `supabase/docker/volumes/db`, and any file write inside it
- printing a `.env` file (`cat`, `head`, `grep` without `-c`/`-q`/`-l`, the Read tool, …).
  `.env.example` is allowed. To check that a variable is set: `grep -c '^VAR=' .env`.

It matches on the command text, so an `echo` that merely mentions a blocked command is blocked
too. If a blocked action is really needed, the user runs it.
