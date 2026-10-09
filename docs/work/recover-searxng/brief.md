# Recover the SearXNG container

Status: approved
Slug: recover-searxng · Branch: recover-searxng

## Why
`searxng` has been `Exited (127)` since 2026-10-08 18:48 UTC. The reset removed its bind-mounted
`searxng/settings.yml`, and Docker put an empty root-owned directory in its place, so the
container can't start. This is the same trap `recover-stack` fixed for the Supabase containers.
While it is down, `docker compose up -d` fails on `searxng`, and `webarm` (which `depends_on` a
healthy `searxng`) can't be started through compose. Web search is optional in PROJECT.md §4,
so this blocks nothing in P1a. Do it when web lookups or a compose start are needed.

## Goal
`searxng` runs again from its archived settings and answers JSON searches. Its settings can't
silently disappear again, and its real secret never lands in git.

## Scope
In: the `searxng` container, `searxng/settings.yml`, and the docs that describe its state
(OPERATIONS.md §1 and §3 trap entry, PROJECT.md §4 Web search row).
Out:
- `webarm`: it is running and healthy and stays untouched. Its source (`services/webarm`) is not
  in the repo, and testing web lookups end to end through it is separate work.
- The orphaned `homebrew-db-init` container and the root-owned `supabase/docker/volumes/snippets`.
- Changes to the SearXNG settings themselves (engines, limiter, formats): restore, don't redesign.
- Recreating `searxng` or anything else through compose.

## Requirements
R1. `searxng` runs and is healthy. It is the existing container started again, not a new one.
R2. SearXNG answers searches with `format=json` (n8n and `webarm` need JSON).
R3. `searxng/settings.yml` has the archived settings (`archive/pre-reset-2026-10-08`), apart from
    the secret that the image's entrypoint writes into it at start.
R4. The real `SEARXNG_SECRET` value is in no commit.
R5. A secret-free template of the settings (for example `searxng/settings.example.yml`) is
    tracked in git, and the live `searxng/settings.yml` is copied from it and git-ignored. So
    deleting the live file doesn't lose the settings, and the secret can't be committed by
    accident (user's decision, 2026-10-09).
R6. The docs describe the new state: OPERATIONS.md §1 no longer lists `searxng` as down, the §3
    trap entry says it was recovered, and the PROJECT.md §4 Web search row is 🟢.

## Constraints
- Plain `docker` commands for the container. No `docker compose up`, `down` or
  `--force-recreate` (CLAUDE.md, OPERATIONS.md). Read OPERATIONS.md before touching containers.
- The entrypoint rewrites the `ultrasecretkey` placeholder in `settings.yml` in place from
  `SEARXNG_SECRET`, which is why the mount is read-write (comment in `docker-compose.yml`). So
  after the first start, the working-tree file holds the real secret.
- `searxng/` and `searxng/settings.yml` are owned by root (checked 2026-10-09). Removing the
  placeholder and taking ownership is the user's step, run in their own terminal (`sudo` doesn't
  work in Claude Code's shell). Don't work around `.claude/hooks/guard.sh`.
- Never print `.env` or the secret value; check it by length or by match count only.
- Readable over optimal (PROJECT.md §6.8).

## Assumptions
- The container `d8d71fa1d3aa` still exists, and its bind mount points at
  `searxng/settings.yml` in this checkout (checked 2026-10-09). `docker start` will reuse it.
- `SEARXNG_SECRET` is set in `.env` and in the container's environment *(unverified)*.
- The archived `settings.yml` holds only the `ultrasecretkey` placeholder, not a real secret
  (checked 2026-10-09: 38 lines, 1 match for `ultrasecretkey`).
- The `searxng/searxng:latest` image already pulled still accepts the archived settings
  *(unverified)*.
- SearXNG can reach the internet for the search check *(unverified)*.

## Acceptance criteria
A1. `docker ps` shows `searxng` as `Up … (healthy)`, and `docker inspect searxng --format
    '{{.Id}}'` still starts with `d8d71fa1d3aa` (R1).
A2. `curl -s -o /dev/null -w '%{http_code}' 'http://localhost:8081/search?q=hops&format=json'` →
    `200`, and the body is JSON with a non-empty `results` list (R2).
A3. `settings.yml` differs from the archived file only on the `secret_key` line (R3).
A4. `git log -p --all -S "<secret>"` finds nothing, run without printing the value (R4).
A5. The template is tracked and identical to the archived `settings.yml`; `git check-ignore
    searxng/settings.yml` prints the path; `git status` doesn't list `settings.yml` (R5).
A6. OPERATIONS.md §1 and §3 and the PROJECT.md §4 Web search row say `searxng` is running, and
    `docker ps` shows 0 containers `Restarting` and `webarm` still healthy (R6).

## Open questions
None. Settled 2026-10-09: tracked template + git-ignored live file (R5), chosen over
ignore-only (settings lost again if the archive tag goes) and tracking the live file (secret
could be committed).

## Deviations
