#!/usr/bin/env bash
# =============================================================================
# ask.sh — embed a question with bge-m3, then call nlq.search_knowledge.
#
# nlq.search_knowledge takes p_query_embed vector(1024), so a question cannot be
# typed straight into psql: it has to go through Ollama first and come back as a
# pgvector literal. That two-step is the whole reason this script exists.
#
# Usage:  ./scripts/ask.sh "<question>" [doc_type]
#   doc_type is optional: 'book' | 'style_guide'. Omit to search the whole corpus.
#
# Used by plans/02-phase1-retrieval-gate.md §4 — the Phase 1 retrieval gate.
# The 6/40/50 parameters are the architecture §3.4 defaults (p_limit,
# p_candidates, p_rrf_k). Do not tune them while running the gate: the gate
# measures the corpus, not the retrieval function.
# =============================================================================
set -euo pipefail

Q="${1:?usage: ask.sh \"<question>\" [doc_type]}"
DT="${2:-}"

# jq -Rn --arg builds the JSON string rather than interpolating it — questions
# contain apostrophes and quotes, and naive interpolation yields a confusing 400.
EMB=$(curl -s http://localhost:11434/api/embed \
        -d "{\"model\":\"bge-m3\",\"input\":$(jq -Rn --arg q "$Q" '$q'),\"keep_alive\":-1}" \
      | jq -c '.embeddings[0]')

[ "$(echo "$EMB" | jq 'length')" = "1024" ] || {
  echo "ask.sh: expected a 1024-dim embedding — is bge-m3 loaded?" >&2; exit 1; }

DTSQL=$([ -n "$DT" ] && echo "'$DT'" || echo NULL)
QESC=$(echo "$Q" | sed "s/'/''/g")

echo "=============================================================="
echo "Q: $Q"
echo "=============================================================="

# Printed twice on purpose: judge from the ranked table (is the *heading* right?),
# confirm from the snippets. Reading six 400-char blocks cold loses the thread.
docker exec -i supabase-db psql -U postgres -d postgres -X -q <<SQL
\pset format aligned
\pset border 2
SELECT row_number() OVER () AS n, doc_slug, page_from AS pg,
       round(score::numeric,4) AS score,
       left(array_to_string(heading_path,' > '), 55) AS heading
FROM nlq.search_knowledge('$QESC', '$EMB'::vector, 6, 40, 50, 'bge-m3', $DTSQL);
\pset format unaligned
\pset tuples_only on
SELECT E'\n--- ' || row_number() OVER () || '. [' || doc_slug || ' p.' ||
       COALESCE(page_from::text,'?') || '] ' || array_to_string(heading_path,' > ') ||
       E'\n' || left(regexp_replace(raw_content, '[[:space:]]+', ' ', 'g'), 420)
FROM nlq.search_knowledge('$QESC', '$EMB'::vector, 6, 40, 50, 'bge-m3', $DTSQL);
SQL
