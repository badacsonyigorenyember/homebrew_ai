# AI Homebrew Assistant

Cleared on 2026-10-08 to rethink the project from scratch.

The previous state is preserved:

- **Repo** — tag `archive/pre-reset-2026-10-08`. Restore a file or the whole tree with
  `git checkout archive/pre-reset-2026-10-08 -- <path>` (or `-- .`).
- **Live databases and n8n** — `~/homebrew-archive-2026-10-08/` (outside git):
  `supabase-postgres.dump` and `n8n-postgres.dump` (`pg_dump -Fc`, restore with
  `pg_restore`), plus per-file `n8n-workflows/` and `n8n-credentials/` exports.
