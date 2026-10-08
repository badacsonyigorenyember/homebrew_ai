#!/usr/bin/env bash
# PreToolUse guard. Blocks the few actions that would destroy the running stack's
# data or print secrets into the transcript. Runs in every permission mode,
# including bypass. Exit 2 = block; the stderr message goes back to Claude.
set -uo pipefail

input=$(cat)
tool=$(jq -r '.tool_name // ""' <<<"$input")

deny() {
  echo "Blocked by .claude/hooks/guard.sh: $1. If this is really intended, ask the user to run it themselves." >&2
  exit 2
}

is_secret_file() {
  local base
  base=$(basename -- "$1")
  [[ "$base" == ".env" || "$base" == .env.* ]] && [[ "$base" != ".env.example" ]]
}

case "$tool" in
  Bash)
    cmd=$(jq -r '.tool_input.command // ""' <<<"$input")

    # Database and volume destruction
    if grep -Eq 'docker[ -]compose\b.*\bdown\b.*([[:space:]]-[[:alpha:]]*v[[:alpha:]]*\b|--volumes)' <<<"$cmd"; then
      deny "'docker compose down' with volumes deletes the Supabase and n8n data"
    fi
    if grep -Eq 'docker[[:space:]]+(volume[[:space:]]+(rm|prune)|system[[:space:]]+prune)' <<<"$cmd"; then
      deny "removing or pruning Docker volumes deletes stack data"
    fi
    if grep -Eq 'supabase/docker/volumes/db' <<<"$cmd" && grep -Eq '\b(rm|mv|truncate|shred|chown|chmod)\b' <<<"$cmd"; then
      deny "this touches the Postgres data directory (supabase/docker/volumes/db)"
    fi

    # Printing secrets: a .env file (not .env.example) read by a tool that prints contents
    stripped=${cmd//.env.example/}
    if grep -Eq '(^|[^[:alnum:]_])\.env(\.[[:alnum:]_-]+)?\b' <<<"$stripped"; then
      if grep -Eq '\b(cat|less|more|head|tail|bat|nl|strings|xxd|od|sed|awk|cut|sort)\b' <<<"$stripped"; then
        deny "this would print a .env file into the transcript; use 'grep -c ^VAR= .env' to check that a variable is set"
      fi
      if grep -Eq '\bgrep\b' <<<"$stripped" && ! grep -Eq '\bgrep[[:space:]]+(-[[:alpha:]]*[cqlL][[:alpha:]]*)' <<<"$stripped"; then
        deny "grep would print .env values; use grep -c, -q or -l"
      fi
    fi
    ;;
  Read | Edit | Write | MultiEdit)
    path=$(jq -r '.tool_input.file_path // ""' <<<"$input")
    if is_secret_file "$path"; then
      deny "$path holds secrets"
    fi
    if [[ "$tool" != "Read" && "$path" == */supabase/docker/volumes/db/* ]]; then
      deny "this writes into the Postgres data directory"
    fi
    ;;
esac

exit 0
