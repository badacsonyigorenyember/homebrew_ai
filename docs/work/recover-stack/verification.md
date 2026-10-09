# Verification: recover-stack

Overall: ✅ all 10 checks pass (no code, so no regression tests; the plan's critical checks are C1–C5)

Run 2026-10-09 on branch `recover-stack` at `ca934f3`, read-only: no container was started,
stopped, restarted or recreated.

## Part 1: Where to look

**Start here:** `docker ps --format '{{.Names}} {{.Status}}'`. `supabase-db`, `supabase-kong`
and `supabase-pooler` show `Up … (healthy)`, and nothing shows `Restarting`. `searxng` is
`Exited (127)`: that is known and is separate work (OPERATIONS.md §1).

**Services (running stack).** The three Supabase containers that had been down since
2026-10-08 ~20:48 were brought back with `docker start`, not recreated. Their bind-mounted files
had been deleted in the reset, and Docker had replaced them with empty root-owned directories,
so each failed with "not a directory". With the files back, `auth`, `storage`, `realtime` and
`edge-functions` recovered as well. `supabase-edge-functions` was restarted once after its
`functions/main/index.ts` was restored (recorded deviation).

**Files and config.**
- `docker-compose.yml` (root) and `supabase/docker/docker-compose.yml` are back from the archive
  tag. The only change against the archive is the removed `db-init` service and its header line
  (86 lines removed, 0 added).
- 11 bind-mounted files restored byte-identical to the archive: 7 `volumes/db/*.sql`,
  `volumes/api/kong.yml` + `kong-entrypoint.sh`, `volumes/pooler/pooler.exs` and
  `volumes/functions/main/index.ts`.
- Docs: `docs/OPERATIONS.md` §1 (current stack state, `searxng` down) and §3 (new trap: a
  deleted bind-mounted file turns into a root-owned directory). `CLAUDE.md` "The running stack"
  no longer says compose fails. `PROJECT.md` §4 Database row, D6 moved out of §7 with its *why*,
  §8 entry.

## Part 2: Spot checks

### ✅ C1 · DB accepts connections as `postgres`

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 1"
```

| Expected | Actual | Result |
|---|---|---|
| 1 | 1 | ✅ pass |

### ✅ C2 · Kong routes the API and asks for a key

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/rest/v1/
```

| Expected | Actual | Result |
|---|---|---|
| 401 | 401 | ✅ pass |

### ✅ C3 · No container is crash-looping

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep -c Restarting
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C4 · Compose file validates

```bash
docker compose config -q; echo "exit=$?"
```

| Expected | Actual | Result |
|---|---|---|
| exit=0, no other output | exit=0 | ✅ pass |

### ✅ C5 · Compose recognises the three running containers

```bash
docker compose ps --format '{{.Name}}' | grep -E '^supabase-(db|kong|pooler)$' | sort
```

| Expected | Actual | Result |
|---|---|---|
| supabase-db, supabase-kong, supabase-pooler | supabase-db, supabase-kong, supabase-pooler | ✅ pass |

### ✅ C6 · All 13 restored paths are regular files, not placeholder directories

```bash
stat -c %F docker-compose.yml supabase/docker/docker-compose.yml supabase/docker/volumes/db/{webhooks,jwt,roles,_supabase,logs,pooler,realtime}.sql supabase/docker/volumes/api/kong.yml supabase/docker/volumes/api/kong-entrypoint.sh supabase/docker/volumes/pooler/pooler.exs supabase/docker/volumes/functions/main/index.ts | sort | uniq -c
```

| Expected | Actual | Result |
|---|---|---|
| 13 regular file | 13 regular file | ✅ pass |

### ✅ C7 · The 12 Supabase files match the archive tag exactly

```bash
git diff --name-only archive/pre-reset-2026-10-08 HEAD -- supabase/docker/docker-compose.yml supabase/docker/volumes/db/{webhooks,jwt,roles,_supabase,logs,pooler,realtime}.sql supabase/docker/volumes/api/kong.yml supabase/docker/volumes/api/kong-entrypoint.sh supabase/docker/volumes/pooler/pooler.exs supabase/docker/volumes/functions/main/index.ts | wc -l
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C8 · Root compose differs from the archive only by removals (`db-init`)

```bash
git diff archive/pre-reset-2026-10-08 HEAD -- docker-compose.yml | grep -c '^+[^+]'; grep -c db-init docker-compose.yml
```

| Expected | Actual | Result |
|---|---|---|
| 0 added lines; 0 mentions of `db-init` | 0; 0 | ✅ pass |

### ✅ C9 · No root-owned placeholder directories left, except accepted `snippets`

```bash
find supabase/docker/volumes -maxdepth 2 -type d -user root
```

| Expected | Actual | Result |
|---|---|---|
| supabase/docker/volumes/snippets | supabase/docker/volumes/snippets | ✅ pass |

### ✅ C10 · Core Supabase services are healthy

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep -E '^(supabase-(db|kong|pooler|auth|rest|storage|edge-functions)|realtime-dev\.supabase-realtime) ' | grep -c '(healthy)'
```

| Expected | Actual | Result |
|---|---|---|
| 8 | 8 | ✅ pass |

## Part 3: Regression tests

No code changed, so the plan names no regression tests ("Critical behaviour and its tests":
the Task 2 checks are what verify re-runs). Those are C1 (DB), C2 (Kong), C3 (0 Restarting),
C4 + C5 (compose matches the stack), all ✅ above. No test suite was run.
