# Homebrewing Assistant

A self-hosted, local-first brewing assistant. It keeps two things rigorously
separate: **knowledge** (what the books say, retrieved with hybrid RAG) and
**truth** (what you actually brewed, queried with SQL). See
[`homebrew_assistant_architecture.md`](homebrew_assistant_architecture.md) for the full design.

This repository is **Phase 0** of that architecture: the infrastructure and the
four-schema database foundation. Workflows (ingestion, chat agent, learning,
eval) are built in n8n in later phases.

> **Target hardware:** Ryzen 9900X · RX 9070 XT (16 GB VRAM, gfx1201 / RDNA 4) ·
> 32 GB RAM. Profile: **`gpu-amd`** (ROCm). A `cpu` profile exists as a fallback.

---

## What's in the stack

| Service | Port | Role |
|---|---|---|
| **Supabase Postgres** (`db`) | 5432 (via pooler) | App database — `kb` / `brew` / `mem` / `nlq` schemas, pgvector |
| Supabase Studio / Kong | 8000 | DB UI + API gateway |
| **n8n** | 5678 | Orchestration & glue only |
| n8n metadata Postgres | — | Workflow definitions only (never app data) |
| **Ollama** (ROCm) | 11434 | `gemma4:12b` (chat) + `bge-m3` (embed), both kept resident |
| **Docling Serve** | 5001 | PDF → structured doc + `HybridChunker` |
| **nginx** (`static-files`) | 8080 | Serves extracted images (`IMAGE_BASE_URL`) |
| `db-init` (one-shot) | — | Applies `db/init/*.sql` then exits |

**Deliberately removed** vs. the starter kit it's based on: Qdrant (pgvector
only, §3.6), Open WebUI (D5), `llama3.2` (D4), and the demo workflow / import.

---

## Prerequisites

- Docker Engine + Compose v2
- For `gpu-amd`: ROCm-capable kernel with `/dev/kfd` and `/dev/dri` present, and
  your user in the `video` + `render` groups.

Confirm the GPU group GIDs match the compose file (`docling-gpu-amd.group_add`):

```bash
getent group video render
```

If they differ from `44` (video) / `992` (render), edit them in `docker-compose.yml`.

---

## Setup

### 1. Generate secrets

Mints strong, fresh secrets — including a new Supabase `JWT_SECRET` and matching
signed `ANON_KEY` / `SERVICE_ROLE_KEY` (not the well-known demo keys):

```bash
python3 scripts/gen-env.py > .env
```

Run this **once**, before the first `up`. Re-running mints new secrets and would
orphan an existing Postgres volume.

### 2. Bring up the stack

```bash
docker compose --profile gpu-amd up -d
```

First run pulls several GB (Supabase images, `ollama/ollama:rocm`, Docling, and
the models `bge-m3` + `gemma4:12b`). The `db-init` container waits for Postgres,
applies the schema, and exits `0`.

### 3. Verify the embedder — the dimension gate (do this first, §"Start tomorrow")

Everything downstream is dimension-locked to **1024**. Confirm it before trusting
the schema:

```bash
./scripts/verify-embedding.sh
```

Expected: `ollama ps` shows **100% GPU**, and the reported dimension is **1024**.

### 4. Verify the schema and read-only enforcement (Phase 0 exit criteria)

```bash
# schema applied?
docker compose exec db psql -U postgres -c '\dn' -c '\df nlq.*'

# search_knowledge returns 0 rows on an empty corpus WITHOUT error:
docker compose exec db psql -U postgres -c \
  "SELECT * FROM nlq.search_knowledge('test', array_fill(0::real,ARRAY[1024])::vector);"

# the agent role is denied on truth tables (should ERROR: permission denied):
docker compose exec db psql -U n8n_agent -d postgres -c 'SELECT * FROM brew.batches;'
```

`db-init` is idempotent — re-apply the schema any time with:

```bash
docker compose up db-init
```

---

## Layout

```
docker-compose.yml          tailored stack (gpu-amd primary)
.env / .env.example         secrets (generate .env; never commit)
scripts/
  gen-env.py                secret + Supabase-JWT generator
  verify-embedding.sh       the 1024-dim GPU gate
db/init/                    idempotent schema, applied by db-init
  00_extensions.sql         vector / pg_trgm / unaccent / pgcrypto + schemas
  10_kb.sql                 knowledge: documents→versions→chunks→embeddings
  20_brew.sql               truth: recipes/batches/… + brewing math functions
  30_mem.sql                memory: chat_turns, memories, f_save_memory
  40_nlq.sql                agent surface: search_knowledge (RRF) + find_batches
  50_roles.sql              read-only enforcement: agent_ro / n8n_agent / mem_writer
chat/chat.html              @n8n/chat streaming UI (wire to WF4 in Phase 2)
shared/
  rag-files/{pending,processing,processed,failed}/   ingestion state machine (§6.5)
  extracted-images/         served by nginx at :8080
supabase/docker/            the Supabase stack (copied, no runtime data)
```

---

## Notes & gotchas

- **Model tags.** `gemma4:12b` and `bge-m3` are set in `.env`
  (`OLLAMA_CHAT_MODEL` / `OLLAMA_EMBED_MODEL`). The architecture flags that tags
  drift — check `ollama.com/library` and edit `.env` if a pull 404s. `qwen3:14b`
  is the documented chat fallback (§4.3).
- **ROCm / gfx1201.** If the card isn't auto-detected, uncomment
  `HSA_OVERRIDE_GFX_VERSION` on `ollama-gpu-amd`. Pin a known-good image digest
  rather than `:rocm` once you have one (§13.1 R1).
- **RAM (32 GB).** Never ingest while chatting (§4.5). `mem_limit` hints are
  commented in the compose — tune to your host and enable them (§13.1 R2).
- **Two Postgres instances, on purpose.** n8n metadata ≠ app data (§12 #11).
  App schemas live in the Supabase `db`; n8n's own tables live in the alpine
  `postgres` service.
- **The agent only ever touches `nlq`.** Read tools connect as `n8n_agent`
  (read-only, `nlq` only); the learning layer writes as `mem_writer`
  (`EXECUTE mem.f_save_memory` only). Configure these as n8n credentials in Phase 2.

---

## Next (per the architecture's phased rollout, §11)

- **Phase 1** — WF1 ingest one real book end-to-end (Docling async + `HybridChunker`),
  WF2 for BJCP.
- **Phase 2** — WF4 chat agent, two tools, streaming; point `chat.html` at its webhook.
- **Phase 3** — full `nlq` tool set + eval (WF6).
- **Phase 4** — learning layer (WF5).
