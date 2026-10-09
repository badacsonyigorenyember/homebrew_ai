# Operations notes

How the running stack behaves and the traps already hit. Linked from `CLAUDE.md` and
`PROJECT.md` §4. Facts are marked with the date they were last checked.

## 1. State of the stack after the reset

*Checked 2026-10-09.*

- All containers run under compose project `aihomebrewassistant`, with working directory
  this repo's root. Every one has restart policy `unless-stopped`, so they come back after a
  reboot.
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
  (2026-10-08). Fix: stop the container, remove the placeholder directory (root-owned, so the
  user runs `sudo rmdir`), restore the file, `docker start` again.
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

## 6. Ollama (ROCm)

- On every start Ollama logs `dropping ROCm device … gfx1036 … set HSA_OVERRIDE_GFX_VERSION`.
  That is the Raphael **iGPU** being correctly dropped. The RX 9070 XT is picked up on the same
  boot. **Do not set `HSA_OVERRIDE_GFX_VERSION`.** It would break the working discrete GPU.
  Check `docker logs ollama | grep "inference compute"` for `compute=gfx1201`, and
  `docker exec ollama ollama ps` for `100% GPU`.
- Models pulled *(checked 2026-10-08)*: `gemma4:12b-it-q8_0`, `gemma4:12b`, `qwen3.8:27b`, plus
  the embedding model `bge-m3`.

## 7. Claude Code guardrails

`.claude/hooks/guard.sh` runs before every Bash, Read, Edit and Write call, in every
permission mode. It blocks:

- `docker compose down -v` / `--volumes`, `docker volume rm|prune`, `docker system prune`
- `rm`/`mv`/`chmod`/… on `supabase/docker/volumes/db`, and any file write inside it
- printing a `.env` file (`cat`, `head`, `grep` without `-c`/`-q`/`-l`, the Read tool, …).
  `.env.example` is allowed. To check that a variable is set: `grep -c '^VAR=' .env`.

It matches on the command text, so an `echo` that merely mentions a blocked command is blocked
too. If a blocked action is really needed, the user runs it.
