# CLAUDE.md

## Scope: do what was asked, then stop

- Implement exactly what the user asked for, and nothing else. No extra fixes, refactors,
  cleanups or "while I was here" changes.
- Don't end a task with suggestions, follow-up ideas, "next steps" or lists of issues you found.
  Report what was done and stop, so the conversation can close.
- Don't go looking for problems after the task is done. Improvement reviews happen only when the
  user asks for one.
- Exception: if you notice something that would lose data, expose a secret, or stop the requested
  change from working, say so in one sentence. Don't fix it unless asked.

## PROJECT.md is the single source of truth

[`PROJECT.md`](PROJECT.md) holds the project's purpose, goals, recipe approach, tech stack,
open decisions and progress log. Read it at the start of any non-trivial task.

**Update it in the same change as the work, every time something is implemented, decided, or
abandoned**, following its §10 "Keeping this file current":

- update the status columns, and add a dated entry (newest first) to §8 Progress log
- a decision that gets made moves out of §7 Open decisions, keeping a one-line *why*
- edit goals or approach text in place, so the file describes the current plan rather than
  its history
- do not change goals, priorities or the recipe approach (§2, §3, §6) without the user's
  agreement; suggest the change instead

Facts in PROJECT.md should be measured (row counts, test results, what is actually running),
not hoped for. Mark anything unverified as such.

## Working rules

- **Readable over optimal** ([PROJECT.md](PROJECT.md) §6.8). Write code and workflows a reader
  can follow from the file alone; no config-table-driven or generic machinery unless a measured
  need requires it.
- **No git worktrees.** Work in this checkout and use a plain branch when isolation is
  needed. This overrides superpowers' `using-git-worktrees` step and the isolation default in
  `subagent-driven-development`. A worktree has no `.env`, and compose run from one starts a
  second, broken stack (see [`docs/OPERATIONS.md`](docs/OPERATIONS.md) §3).
- **Design docs and plans go in `docs/`**, including the specs and plans superpowers writes.
  Link each one from PROJECT.md, so PROJECT.md stays the single entry point.
- **The pre-reset build is reference material, not a starting point.** Read it with
  `git show archive/pre-reset-2026-10-08:<path>`, and take only what still applies.
- **Brewing maths is deterministic, tested code.** Never ask the LLM to compute gravity, IBU,
  colour or scaling, and never write a skill as a substitute for that code.

## The running stack

- The compose definition (`docker-compose.yml`, `supabase/docker/`) is back in the repo, without
  the old `db-init` service. Read [`docs/OPERATIONS.md`](docs/OPERATIONS.md) before restarting,
  recreating or reconfiguring anything.
- **Database changes:** write them as `.sql` files in the repo and apply them with `psql` as
  `postgres` (the command is in OPERATIONS.md §4). The Supabase MCP server is **read-only on
  purpose**, for inspection only. Objects created through MCP or as `supabase_admin` end up
  with the wrong owner and break n8n and later scripts.
- Query the catalog before treating a DB object as missing. Don't trust a written status.

## Claude Code setup

- MCP: `supabase` (read-only) is in [`.mcp.json`](.mcp.json). `n8n-mcp` is in local scope,
  because it carries a token (re-add command in OPERATIONS.md §5).
- [`.claude/hooks/guard.sh`](.claude/hooks/guard.sh) blocks deleting Docker volumes, writes to
  the Postgres data directory, and printing `.env` files. Don't work around it. If a blocked
  action is really needed, ask the user to run it.
- Project skills: `retrieval-evaluation-metrics` and `rag-evaluation-frameworks` (PROJECT.md §6.6).
- Delivery workflow: `dev-flow` runs brief → plan → implement → review → verify → ship with one
  subagent per step; each step is also its own skill (`dev-brief`, `dev-plan`, `dev-implement`,
  `dev-review`, `dev-verify`, `dev-ship`). Work lives in `docs/work/<slug>/`. Shared rules:
  [`.claude/skills/dev-flow/conventions.md`](.claude/skills/dev-flow/conventions.md).
- Operational traps (compose, Kong, roles, n8n CLI, the Ollama iGPU warning) are in
  [`docs/OPERATIONS.md`](docs/OPERATIONS.md). Add new ones there, not to personal memory, so
  they are versioned with the repo.
