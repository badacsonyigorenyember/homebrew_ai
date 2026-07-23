#!/usr/bin/env bash
# =============================================================================
# verify-embedding.sh — the FIRST build step (architecture "Start tomorrow").
# Everything downstream is dimension-locked, so confirm bge-m3 is (a) on the GPU
# and (b) returns exactly 1024 dimensions BEFORE trusting the kb schema.
# =============================================================================
set -euo pipefail

EMBED_MODEL="${OLLAMA_EMBED_MODEL:-bge-m3}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

echo "== 1. Pull the embedder =="
docker exec ollama ollama pull "$EMBED_MODEL"

echo
echo "== 2. GPU residency (expect 100% GPU, size_vram == model size) =="
docker exec ollama ollama ps

echo
echo "== 3. Embedding dimension (expected: 1024) =="
dim=$(curl -s "$OLLAMA_URL/api/embed" \
  -d "{\"model\":\"$EMBED_MODEL\",\"input\":\"Irish stout mash temperature\",\"keep_alive\":-1}" \
  | python3 -c "import sys,json; print(len(json.load(sys.stdin)['embeddings'][0]))")

echo "reported dimension: $dim"
if [ "$dim" = "1024" ]; then
  echo "OK — schema dimension matches. Proceed to run the kb DDL (db-init)."
else
  echo "MISMATCH — schema is standardised on 1024 (architecture §3.2)."
  echo "Do NOT ingest until the embedder returns 1024 dims."
  exit 1
fi
