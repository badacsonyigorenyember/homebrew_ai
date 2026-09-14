# Homebrewing Assistant

A self-hosted, local-first brewing assistant. It keeps two things rigorously
separate: **knowledge** (what the books say, retrieved with hybrid RAG) and
**truth** (what you actually brewed, queried with SQL). See
[`homebrew_assistant_architecture.md`](homebrew_assistant_architecture.md) for the full design.

Three other documents matter more than this one once the stack is up:

| Document | What it is for |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | operational facts — Postgres access, Kong, the MCP servers, known defects |
| [`plans/phase3/README.md`](plans/phase3/README.md) | the live plan: the corpus, one source at a time, and the contract every per-source plan follows |
| [`plans/phase3/NEXT-PROMPT.md`](plans/phase3/NEXT-PROMPT.md) | what the next session should do, measured against the live stack |

> **Target hardware:** Ryzen 9900X · RX 9070 XT (16 GB VRAM, gfx1201 / RDNA 4) ·
> 32 GB RAM. Profile: **`gpu-amd`** (ROCm) — both Ollama *and* Docling run under it.
> A `cpu` profile exists as a fallback.

---

## Where this actually is — `measured` 2026-09-13

This repository is well past Phase 0. What is live:

| | Measured |
|---|---|
| Corpus | **2,090** chunks across **6** documents, **2,090** embeddings, **0** gaps, all 1024-dim |
| Reference data | `ref.styles` — **116** BJCP 2021 rows |
| n8n workflows | **11**, all exported to `n8n/demo-data/workflows/` — one engine (`wf1-ingest-book`), six launchers, and the four-workflow agent layer |
| The agent | `chat-agent` + `wf-step-retrieve` + `wf-step-llm` + `cap-brainstorm-pairing`, **active**, **22** logged turns in `mem.chat_turns`, **21** runs in `obs.runs` |
| Truth side | `brew.*` schema exists, **0** batches — no entry path yet (architecture §13.2 D25) |

| Phase (architecture §11) | Status |
|---|---|
| 0 — schema and demolition | ✅ complete |
| 1 — one document end to end | ✅ complete |
| 2 — minimal agent | 🟢 built and answering |
| **3a — the corpus** ([`plans/phase3/`](plans/phase3/README.md)) | 🟢 **6 of 11 sources ingested** — books 0a, 0b, 1, 2, 3, 4 |
| 3b — full tool set and NLQ | ⬜ not started |
| 4 — learning layer · 5 — optional | ⬜ not started |

---

## What's in the stack

Container names as they appear in `docker ps`, under the `gpu-amd` profile:

| Container | Compose service | Port | Role |
|---|---|---|---|
| `supabase-db` | `db` | 5432 (via `supabase-pooler`) | App database — `kb` / `ref` / `brew` / `mem` / `nlq` / `obs`, pgvector |
| `supabase-kong` | `kong` | 8000 | Studio UI, REST, and the `/mcp` route |
| `n8n` | `n8n` | 5678 | Orchestration & glue only |
| `aihomebrewassistant-postgres-1` | `postgres` | — | n8n metadata only (never app data) |
| `ollama` | `ollama-gpu-amd` | 11434 | `gemma4:12b` (chat) + `bge-m3` (embed) |
| `docling` | `docling-gpu-amd` | 5001 | PDF → structured doc + `HybridChunker` |
| `static-files` | `static-files` | 8080 | Serves extracted images (`IMAGE_BASE_URL`) |
| — | `db-init` (one-shot) | — | Applies a **hardcoded list** of `db/init/*.sql`, then exits |

Plus the rest of the Supabase stack (`auth`, `rest`, `realtime`, `storage`,
`imgproxy`, `meta`, `studio`, `functions`, `supavisor`).

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
orphan an existing Postgres volume. It also rotates `POSTGRES_PASSWORD`, which
breaks the Supabase MCP read path until the fix in [`CLAUDE.md`](CLAUDE.md) is re-applied.

### 2. Bring up the stack

```bash
docker compose --profile gpu-amd up -d
```

Run it from **this checkout only, never from a worktree** — a worktree has no
`.env`, and the changed project name collides on container names.

First run pulls several GB (Supabase images, `ollama/ollama:rocm`, Docling, and
the models `bge-m3` + `gemma4:12b`). The `db-init` container waits for Postgres,
applies the schema, and exits `0`.

### 3. Verify the embedder — the dimension gate

Everything downstream is dimension-locked to **1024**. Confirm it before trusting
the schema:

```bash
./scripts/verify-embedding.sh
```

Expected: `ollama ps` shows **100% GPU**, and the reported dimension is **1024**.

### 4. Verify the schema and read-only enforcement

`postgres` is **not** a superuser in this stack; use `supabase_admin`:

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c '\dn' -c '\df nlq.*'
```

Expect six app schemas — `kb`, `ref`, `brew`, `mem`, `nlq`, `obs`.

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "SELECT count(*) FROM nlq.search_knowledge('test', array_fill(0::real,ARRAY[1024])::vector);"
```

Returns rows against the live corpus (6 on the defaults) and, on an empty corpus,
**0 rows without an error** — that is the original Phase 0 gate.

The agent role must be denied on the truth tables. It authenticates by password,
so this needs `-h 127.0.0.1`; peer auth over the socket fails with a misleading
`Peer authentication failed` instead of the permission error you are testing for:

```bash
docker exec -e PGPASSWORD="$(grep -E '^AGENT_DB_PASSWORD=' .env | cut -d= -f2-)" supabase-db psql -h 127.0.0.1 -U n8n_agent -d postgres -c 'SELECT * FROM brew.batches;'
```

Expected: `ERROR: permission denied for schema brew` (§8.4 Layer 1) — while the
same role *can* call `nlq.search_knowledge` (§8.4 Layer 2).

`db-init` is idempotent — re-apply the schema any time with:

```bash
docker compose up db-init
```

⚠️ **A new `.sql` file is not picked up automatically.** `db-init` runs a hardcoded
list in `docker-compose.yml`; a file that is not in that list silently never applies.
Schema changes go through `db/init/*.sql` and this mechanism — **not** through
Supabase migrations. See architecture §3.7.

---

## Layout

```
docker-compose.yml          tailored stack (gpu-amd primary)
.env / .env.example         secrets (generate .env; never commit)
CLAUDE.md                   operational facts + behavioural guidelines
scripts/
  gen-env.py                secret + Supabase-JWT generator
  verify-embedding.sh       the 1024-dim GPU gate
  ask.sh                    embed a question, then call nlq.search_knowledge
  hyphen-probe.sh           pre-ingest scan for wrapped numeric ranges (standing rule 7)
  stress/                   tier1_routing.py (agent decision layer, reads the LIVE workflow)
                            tier2_e2e.py + cases.jsonl
db/init/                    idempotent schema, applied by db-init
  00_extensions.sql         vector / pg_trgm / unaccent / pgcrypto + schemas
  10_kb.sql                 knowledge: documents→versions→chunks→embeddings
  15_ref.sql                reference data: ref.styles (BJCP)
  20_brew.sql               truth: recipes/batches/… + brewing math functions
  30_mem.sql                memory: chat_turns, memories, f_save_memory
  40_nlq.sql                agent surface: search_knowledge (RRF) + find_batches
  50_roles.sql              read-only enforcement: agent_ro / n8n_agent / mem_writer
  60_obs.sql                observability: runs, steps, prompt registry, model profiles
n8n/demo-data/workflows/    all 11 workflows, exported — the source of truth, not n8n's DB
chat/chat.html              @n8n/chat streaming UI — deferred, not deleted (D29)
plans/                      phase3/ (live) · agent/ (the agent build) · archive/ · research/
shared/
  rag-files/{pending,processing,processed,failed}/   ingestion state machine (§6.5)
  extracted-images/         served by nginx at :8080
supabase/docker/            the Supabase stack (copied, no runtime data)
backup/                     n8n exports taken before destructive changes
```

---

## Notes & gotchas

- **Operational detail lives in [`CLAUDE.md`](CLAUDE.md)**, not here: Postgres roles, the
  Kong `/mcp` route, the `supabase_read_only_user` password fix, `get_logs` being
  permanently broken, and the current defect list.
- **n8n's database is not a backup.** Every workflow is exported to
  `n8n/demo-data/workflows/`; standing rule 4 says export and commit *before* the first
  run. Reconcile with:
  `comm -3 <(docker exec n8n n8n list:workflow | sed 's/^[^|]*|//' | sort) <(ls n8n/demo-data/workflows/*.json | xargs -n1 basename | sed 's/\.json$//' | sort)`
  — empty output means every live workflow has a tracked export.
- **Archiving a workflow is not deleting it.** The row stays in `workflow_entity`, so
  duplicate names still break anything that queries by name.
- **Model tags.** `gemma4:12b` and `bge-m3` are set in `.env`
  (`OLLAMA_CHAT_MODEL` / `OLLAMA_EMBED_MODEL`). Tags drift — check
  `ollama.com/library` and edit `.env` if a pull 404s. `qwen3:14b` is the documented
  chat fallback (§4.3).
- **ROCm / gfx1201.** If the card isn't auto-detected, uncomment
  `HSA_OVERRIDE_GFX_VERSION` on `ollama-gpu-amd`. Pin a known-good image digest
  rather than `:rocm` once you have one (§13.1 R1).
- **RAM (32 GB).** Never ingest while chatting (§4.5). `mem_limit` hints are
  commented in the compose — tune to your host and enable them (§13.1 R2).
- **Two Postgres instances, on purpose.** n8n metadata ≠ app data (§12 #11).
  App schemas live in `supabase-db`; n8n's own tables live in the alpine `postgres`
  service (`aihomebrewassistant-postgres-1`).
- **The agent only ever touches `nlq`.** Read tools connect as `n8n_agent`
  (read-only, `nlq` only); the learning layer writes as `mem_writer`
  (`EXECUTE mem.f_save_memory` only).
- **Anything destined for `kb.*` goes through `docling-serve`.** A locally converted
  PDF produces chunks whose provenance (`docling_version`, `chunker_config`) cannot be
  reproduced. Architecture §6.1.

---

## Next

[`plans/phase3/NEXT-PROMPT.md`](plans/phase3/NEXT-PROMPT.md) is the current entry point.
Beyond it: close the agent record, then books 5–9, then 3b (full tool set and NLQ).
