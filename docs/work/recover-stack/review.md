# Review: recover-stack

Diff: main...recover-stack at d58fcb2  ·  Verdict: ready for testing

Checked: the 12 restored files plus `functions/main/index.ts` are byte-identical to
`archive/pre-reset-2026-10-08` (`kong-entrypoint.sh` keeps mode 100755). The only change to the
root `docker-compose.yml` against the archive is the removed `db-init` block and its header
line; nothing else refers to `db-init` or `db/init`. `docker compose config -q` exits 0 and
`docker compose ps` lists `supabase-db`, `-kong` and `-pooler` (read-only checks, run during
review). No secrets in the diff: `kong.yml`, `roles.sql` and `index.ts` take credentials from
env vars or psql variables. Both deviations are recorded in the plan. Commits are single lines
with no trailers. PROJECT.md §4 row and intro, §7 (D6 removed, *why* kept in §4) and §8 are
updated; CLAUDE.md and OPERATIONS.md match the plan.

| # | Severity | Where | Finding | Why it matters |
|---|---|---|---|---|
| 1 | should-fix | docs/OPERATIONS.md:10 | §1 now says "All containers run under compose project `aihomebrewassistant`", but `searxng` is `Exited (127)` since 2026-10-08 18:48 UTC with the same trap: `searxng/settings.yml` is a root-owned placeholder directory ("not a directory" in `docker inspect`). The file is in the archive tag. The new trap entry (line 43) lists the affected containers without `searxng`. PROJECT.md §4 still shows SearXNG as "🟢 running" (that line is not in this diff). | A stated fact in the edited section is wrong. With compose back, a later `docker compose up -d` would fail on `searxng`, and `webarm` has `depends_on: searxng: service_healthy`. Fixing it is out of this plan's scope; the user decides whether to correct the docs only or to add a task. |
| 2 | note | — | The exited container `homebrew-db-init` from the removed service still exists. | Compose will report it as an orphan on the next `up`; harmless. |
| 3 | note | docs/work/recover-stack/plan.md:60 | Task 1 "Done when" still says "the 12 files"; the 13th file belongs to Task 2 and is covered by the Task 2 deviation. | None. |
