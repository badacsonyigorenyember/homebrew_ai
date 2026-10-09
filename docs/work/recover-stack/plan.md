# Recover the Supabase containers (D6) — implementation plan

Stage: verify
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 1; was Task 1)
Branch: recover-stack

## Approach

`supabase-db`, `supabase-kong` and `supabase-pooler` have been down since 2026-10-08 ~20:48.
Their bind-mounted files were removed in the reset, and Docker created empty root-owned
directories in their place. Each container now fails with "not a directory". Nothing in P1a
can be loaded until the DB is back.

All 12 files are in the archive tag `archive/pre-reset-2026-10-08`. The fix: the user removes
the 10 placeholder directories, we restore the files and the compose definition, then
**`docker start`** the three existing containers. Their mounts already point at these paths,
so nothing is recreated and `supabase-kong` keeps the "don't recreate" rule. The `db-init`
service is removed from the restored compose file, because it applies the old schema list.
This resolves D6: compose and Kong files are back, without `db-init`.

Rules for this work: plain `docker` commands for the containers. Never `docker compose up`,
`down` or `--force-recreate` here. Don't work around `.claude/hooks/guard.sh`; it blocks
writes under `supabase/docker/volumes/db`, so the `rmdir` is the user's.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `docker-compose.yml` | new (from archive), `db-init` removed | Root compose; `include`s the Supabase file |
| `supabase/docker/docker-compose.yml` | new (from archive) | Supabase services (`db`, `kong`, `supavisor`, …) |
| `supabase/docker/volumes/db/{webhooks,jwt,roles,_supabase,logs,pooler,realtime}.sql` | new (from archive) | DB init scripts bind-mounted into `supabase-db` |
| `supabase/docker/volumes/api/{kong.yml,kong-entrypoint.sh}` | new (from archive) | Kong config bind-mounted into `supabase-kong` |
| `supabase/docker/volumes/pooler/pooler.exs` | new (from archive) | Supavisor config bind-mounted into `supabase-pooler` |
| `supabase/docker/volumes/functions/main/index.ts` | new (from archive) | Edge-runtime main service bind-mounted into `supabase-edge-functions` (already un-ignored by `.gitignore`) |
| `docs/OPERATIONS.md` | changed | §1 state of the stack, new trap entry |
| `CLAUDE.md` | changed | "The running stack" no longer says compose fails |
| `PROJECT.md` | changed | §4 Database row, §7 D6 → decided, §8 |

## Tasks

### Task 1: Restore the compose and mount files from the archive
Why: the three containers can't start without their bind-mounted files (D6).
- [x] **Needs the user.** Ask them to remove the 10 empty root-owned placeholder directories.
  The guard hook blocks this for Claude on purpose. `rmdir` refuses non-empty directories, so
  it can't delete data:
  ```bash
  cd "/home/gorenyember/AI Homebrew Assistant/supabase/docker/volumes" && sudo rmdir db/webhooks.sql db/jwt.sql db/roles.sql db/_supabase.sql db/logs.sql db/pooler.sql db/realtime.sql api/kong.yml api/kong-entrypoint.sh pooler/pooler.exs
  ```
  Expected: no output. Report `needs-input` until it is done, and check it with
  `find supabase/docker/volumes -maxdepth 2 -type d -user root` → only
  `supabase/docker/volumes/snippets` (mounted by the running `supabase-studio`; leave it).
  The parent directories `api/` and `pooler/` were also created by Docker as root; the user
  takes them over with `sudo chown gorenyember:gorenyember api pooler` so git can write into them.
- [x] Restore the files:
  `git checkout archive/pre-reset-2026-10-08 -- docker-compose.yml supabase/docker/docker-compose.yml supabase/docker/volumes/db/webhooks.sql supabase/docker/volumes/db/jwt.sql supabase/docker/volumes/db/roles.sql supabase/docker/volumes/db/_supabase.sql supabase/docker/volumes/db/logs.sql supabase/docker/volumes/db/pooler.sql supabase/docker/volumes/db/realtime.sql supabase/docker/volumes/api/kong.yml supabase/docker/volumes/api/kong-entrypoint.sh supabase/docker/volumes/pooler/pooler.exs`
  → `git status` shows the 12 files as new.
- [x] In `docker-compose.yml`, delete the `db-init:` service block and the header comment line
  that describes it. Nothing `depends_on` it (checked 2026-10-09).
- [x] Run `docker compose config -q` → exit 0, no output.
Done when: the 12 files are regular files and compose config validates.
Commit: `Restore compose and Supabase mount files (D6)`

### Task 2: Start the three containers and record D6
Why: the DB must be up for every later P1a item.
- [x] `docker start supabase-db supabase-kong supabase-pooler`. Don't use compose here.
- [x] Restore `supabase/docker/volumes/functions/main/index.ts` from the archive tag and
  `docker restart supabase-edge-functions` (no recreate, no compose).
- [x] Verify:
  - `docker exec supabase-db psql -U postgres -d postgres -Atc "select 1"` → `1`
  - `curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/rest/v1/` → `401` (Kong answers and asks for a key)
  - after about a minute, `docker ps --format '{{.Names}} {{.Status}}' | grep -c Restarting` →
    `0` (auth, storage, realtime and edge-functions recover once the DB is back)
  - `docker compose ps --format '{{.Name}}'` lists `supabase-db`, `supabase-kong` and
    `supabase-pooler` (compose recognises the running containers)
- [x] OPERATIONS.md §1: replace "The files that define them are no longer on disk" and its
  consequences with the current state: the files are back, `docker compose` works, `db-init`
  was removed, and `supabase-kong` can be recreated again from `kong.yml` (date-stamp it).
  Add a trap entry: a bind-mounted file deleted on the host turns into a root-owned empty
  directory on the next container start, and the container then fails with "not a directory".
- [x] CLAUDE.md "The running stack": the compose file is back in the repo; keep the rule to
  read OPERATIONS.md before restarting or recreating anything.
- [x] PROJECT.md: §4 Database row → 🟢 running (with the date); §4 intro text no longer says the
  containers can't be recreated; D6 moves out of §7 with its *why*; §8 entry linking
  `docs/work/recover-stack/`.
- [x] Tell the user to reconnect the `supabase` MCP server with `/mcp` from an interactive
  `claude` terminal.
Done when: all four checks give the expected output.
Commit: `Restart Supabase DB, Kong and pooler; settle D6`

## Critical behaviour and its tests

No code, so no regression tests. The Task 2 checks are what dev-verify re-runs:

| Behaviour | Check | Task |
|---|---|---|
| DB accepts connections as `postgres` | `select 1` → `1` | 2 |
| Kong routes the API | `/rest/v1/` → `401` | 2 |
| Dependent services recover | 0 containers `Restarting` | 2 |
| Compose file matches the running stack | `docker compose config -q` exit 0; `compose ps` lists the 3 | 1, 2 |

## Approved exceptions

## Deviations
- 2026-10-09 · Task 1: the root-owned check accepts `volumes/snippets` in its output, and the user also chowned `volumes/api` and `volumes/pooler` — Docker had created those parents as root too, so git could not write into them; `snippets` is mounted live by `supabase-studio` and is outside this work.
- 2026-10-09 · Task 2: also restored `supabase/docker/volumes/functions/main/index.ts` and restarted `supabase-edge-functions` — it crash-looped ("could not find an appropriate entrypoint") because this 13th bind-mounted file was also removed in the reset, so the 0-Restarting check could not pass; user chose this fix. `.gitignore` already had the `!supabase/docker/volumes/functions/main/` exception, so it needed no change.
- 2026-10-09 · Review fix 1: OPERATIONS.md §1 no longer says all containers run, the trap entry names `searxng`, and PROJECT.md §4 shows SearXNG down — `searxng` is `Exited (127)` from the same deleted-bind-mount trap; user chose to correct the docs only and recover `searxng` as separate work.
