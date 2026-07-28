# Plan 01 — WF1 `ingest-document`, first book: *How to Brew*

**Status:** not started · **Blocks:** Phase 1 exit, everything after it
**Written:** 2026-07-27 · **Prereqs:** all met (Phase 0 ✅, Phase 1.1 ✅)

Self-contained handoff. A fresh session should work from this file plus
`homebrew_assistant_architecture.md` §5–6 and §11, without re-deriving anything below.

---

## 0. Where we are

- Phase 0 closed, including the live-login test of `n8n_agent`.
- Phase 1.1 closed — WF2's defect ledger (D13–D16) fixed, committed on branch
  `phase-1.1-wf2-defect-ledger` (2 commits, **not pushed, not merged to `main`**).
- WF2 is the only workflow in n8n, tracked at `n8n/demo-data/workflows/wf2-digestion.json`
  — **edit the file, then import.** Do not edit in the browser editor.
- `kb.chunks` holds 116 BJCP style cards. A correct corpus fingerprints as
  `md5(string_agg(content_sha256, ',' ORDER BY chunk_index))` = `48a8990d2ba3c4a8ca44f35345c75b39`
- **WF1 is the next step.** The book is chosen and staged. Nothing blocks the build.

---

## 1. The book — profile

`shared/rag-files/pending/how_to_brew_john_palmer.pdf` *(already copied here from
the starter-kit stack; that stack is a separate checkout — see memory)*

```
sha256  e29d11cf7ed0cefe52c2544a782e94bc6bb53213e5a84dc1b926c6d37960f410
```

| Property | Value | Why it matters |
|---|---|---|
| Title / author | *How to Brew*, John Palmer, 3rd ed. (2006) | |
| Pages | 248, A4 | |
| Producer | Acrobat Distiller 7.0, from Word | **Digital-native, not a scan** |
| Fonts | TrueType, WinAnsi, tagged PDF | Real text layer |
| Text quality | 0 replacement chars, 72.8% alpha | Extraction is clean |
| Body text | 78,201 words ≈ **105,000 tokens** | Drives the chunk estimate below |
| Density | mean 314 words/page (median 314 — very even) | |
| Embedded images | **177** | §6.4 image handling is real work here, not theoretical |
| Running heads/footers | **none** | Most common repeated line occurs 2×, not 150× |
| Page-number-only lines | 6 in the whole book | Negligible |

### Why this is the right first book

Meets all three criteria from the original plan: digital-native (no OCR noise to
confound the chunking gate), process-heavy rather than a recipe collection, and
well-structured. It is also the single most-cited homebrewing text, so retrieval
quality here is directly meaningful.

### Structure

```
p1        title / ISBN                      → DROP
p2–p6     Contents (bulleted TOC)           → DROP
p7–p8     Introduction                      → keep
p9+       Section 1  Extract brewing         Ch 1–11
          Section 2  Extract + specialty grain
          Section 3  All-grain               Ch 12–18
          Section 4  Recipes & solutions     Ch 19–21
p219–248  Appendices A–F
```

Chapters 1–21. Appendices: A Hydrometers (p219) · B Brewing Metallurgy (p221) ·
C Chillers (p226) · D Building a Mash/Lauter Tun (p229) · E Metric Conversions
(p241) · F Recommended Reading (p245).

**Keep A–D** (real process content). **Drop E and F** — a conversion table and a
reading list retrieve as junk against process questions.

Per-chapter `References` lists appear at chapter ends (p32, 37, 55, 71, 79, 87,
103, 110, …). Decide once: they are citation noise with no process content.
Recommend dropping via a heading-path rule.

---

## 2. ⚠️ Verified environment facts

Checked live 2026-07-27. **The architecture doc §6 has NOT been corrected — trust
this section over §6.2.**

| Fact | Value |
|---|---|
| Docling | `docling-serve 1.19.0`, `http://docling:5001` (host `localhost:5001`) |
| Chunk endpoint | `POST /v1/chunk/hybrid/source/async` — **separate from `/v1/convert`**, converts *and* chunks in one call |
| Poll / result | `GET /v1/status/poll/{task_id}` · `GET /v1/result/{task_id}` |
| Ollama | `bge-m3:latest` (1024-dim), `gemma4:12b` · `POST http://ollama:11434/api/embed` |
| Response shape | `{chunks:[{chunk_index, text, raw_text, num_tokens, headings[], page_numbers[], doc_items[], metadata{}}]}` |
| `contextualize()` | ✅ confirmed — `text` arrives with the heading path prepended |

### Where §6.2 is wrong

| Setting | API default | §6 says | Action |
|---|---|---|---|
| `tokenizer` | `sentence-transformers/all-MiniLM-L6-v2` | `BAAI/bge-m3` | **Must set explicitly.** The default *is* the silent-truncation bug §6.2 warns about |
| `repeat_table_headers` | **not in this API** | `true` | Omit — sending it may 422 |
| `image_export_mode` | `embedded` | `referenced` | Set explicitly or base64 lands in chunk text |
| `pdf_backend` / `ocr_engine` | `docling_parse` / `auto` | `dlparse_v4` / `easyocr` | Verify accepted before relying on them |

### Two blockers to resolve first

- [ ] **`raw_text` returned `null`** on a probe with `include_raw_text: true`, but
      `kb.chunks.raw_content` is `NOT NULL`. Either the flag misbehaves or
      `raw_content` must be derived in the cleaning node. **Resolve before writing
      the insert node.** Fallback: strip the heading prefix from `text`.
- [ ] **`page_numbers` was empty** on the markdown probe. Expected for markdown,
      but `page_from` is a Phase 1 exit requirement. **Confirm it populates on this
      PDF before building the mapping** — this is the first thing to test in §3.

### One decision §6 never makes

`use_markdown_tables` defaults to `false`. §6 calls the corpus table-dense and
`table_mode: accurate` "non-negotiable", then never says how tables should be
*serialized* into chunk text. Recommend `true` for this book — hop and water
tables are high-value and a markdown grid embeds better than flattened triplets.

---

## 3. Step 1 — Probe before building anything

Do **not** build the workflow first. One curl against the real book answers the two
blockers and calibrates every number below. Expect several minutes: 248 pages,
177 images, `table_mode: accurate`.

```bash
curl -s -X POST http://localhost:5001/v1/chunk/hybrid/source/async \
  -H 'Content-Type: application/json' -d '{
  "sources": [{"kind": "file", "base64_string": "<...>", "filename": "how_to_brew_john_palmer.pdf"}],
  "convert_options": {
    "from_formats": ["pdf"], "to_formats": ["md", "json"],
    "image_export_mode": "referenced",
    "do_ocr": false,
    "pdf_backend": "dlparse_v4", "table_mode": "accurate", "do_table_structure": true,
    "abort_on_error": false
  },
  "chunking_options": {
    "chunker": "hybrid", "tokenizer": "BAAI/bge-m3", "max_tokens": 512,
    "merge_peers": true, "include_raw_text": true, "use_markdown_tables": true
  }
}'
```

`do_ocr: false` — the text layer is clean and OCR on a digital PDF is slower *and
worse* (§6.1). If tables come out mangled, that is a `table_mode` problem, not OCR.

**Record from the probe:**

- [ ] total chunk count
- [ ] `page_numbers` populated? ← **exit-criterion blocker**
- [ ] `raw_text` populated? ← **NOT NULL blocker**
- [ ] token distribution: min / median / max, and count over 512
- [ ] where the 177 images landed and what the refs look like
- [ ] wall-clock conversion time → sets the poll guard in §4

---

## 4. Step 2 — Build WF1

Carry these forward from WF2. Each was learned the hard way (§11.1 D14/D15/D21):

- **Strictly linear.** No parallel branches — n8n v1 orders by node position, not
  data dependency.
- **Crypto consumes the binary it hashes.** Read the file twice: hash → re-read → parse.
- **Thread `version_id` as `$1`.** Never re-derive with `ORDER BY version DESC`.
- **Promote via `kb.promote_version($1)`**, never a hand-rolled `is_current` flip.

```
Schedule Trigger (nightly)
  └─ Guard: skip if mem.chat_turns activity < 5 min ago        [§5, D12]
  └─ Read/Write Files      pending/*.pdf
  └─ Crypto                action=hash, type=SHA256, encoding=hex   ← pin all three
  └─ Postgres              dedup: SELECT by file_sha256
  └─ IF                    already ingested → move to processed/, stop
  └─ Re-read file          (Crypto ate the binary)
  └─ HTTP POST             /v1/chunk/hybrid/source/async     [config from §3]
  └─ Wait 15s ─┐
  └─ HTTP GET  /v1/status/poll/{task_id}
  └─ IF pending └─ loop back    ← MAX-ITERATION GUARD, see below
  └─ HTTP GET  /v1/result/{task_id}
  └─ Code      normalise + clean   [§5 of this plan]
  └─ Postgres  INSERT kb.document_versions (is_current=false)
  └─ Postgres  INSERT kb.chunks (batched)
  └─ Postgres  embedding reuse: skip chunks whose content_sha256 already has a vector
  └─ Loop Over Items (batch 32)          ≈ 11 batches at ~350 chunks
       └─ HTTP POST ollama /api/embed
       └─ Code      zip ids + embeddings, assert 1024 dims
       └─ Postgres  INSERT kb.chunk_embeddings
  └─ (done) Postgres  SELECT * FROM kb.promote_version($1)
  └─ Move file → processed/   (failed/ on error)
```

**Poll guard:** set max iterations from the probe's wall-clock time × 2, floor 160
(= 40 min at 15 s). A hung Docling task must not loop forever.

### Field mapping — Docling → `kb.chunks`

| Column | Source | Note |
|---|---|---|
| `content` | `text` | already contextualized |
| `raw_content` | `raw_text` | **NOT NULL** — fallback: strip heading prefix from `text` |
| `heading_path` | `headings[]` | |
| `page_from` / `page_to` | `min/max(page_numbers)` | **verify populated — §2 blocker** |
| `token_count` | `num_tokens` | assert ≤ 512, log violations, do not truncate silently |
| `content_sha256` | `encode(sha256(convert_to(raw_content,'UTF8')),'hex')` | in SQL, same as WF2 |
| `image_refs` | filenames parsed from `![…](…)` | replace ref with `[[IMG:file.png]]` — **never store a URL** (§6.4) |

---

## 5. Cleaning rules, tuned to this book

§6.3 generic rules, with this book's specifics. Log every drop to `kb.ingest_log`
with a reason — the log is how you tell "cleaning worked" from "cleaning ate the book".

| Rule | This book | Expected effect |
|---|---|---|
| Front matter | drop `p1` (title/ISBN) and `p2–p6` (TOC) | ~6 pages |
| Heading regex `^(Contents\|Index\|Glossary\|Acknowledg\|Copyright\|About the Author)` | matches the p2 block | folded into the above |
| Appendices E, F | drop `Metric Conversions`, `Recommended Reading` | ~8 pages |
| Per-chapter `References` | drop by heading path | ~15 short chunks |
| `token_count < 30` and no table | 15 pages are figure-only | expect a handful |
| Image-only chunks | 177 images — some chunks will be pure figure | roll ref into preceding chunk |
| Repeated line >60% of pages | **no-op — this book has no running heads** | 0 |
| Page-number-only lines | only 6 in the book | 0–6 |

---

## 6. Expected numbers — and a criterion that will fail

105,000 body tokens. HybridChunker at `max_tokens: 512` with `merge_peers: true`
averages roughly 300 tokens/chunk in practice, so:

```
105,000 / ~300  ≈  300–400 chunks
```

**The Phase 1 exit criterion "chunk count within ±20% of `page_count × 2.5`" gives
496–744 for this book. Expect to miss it, low.**

That heuristic implies ~170 tokens/chunk, which contradicts a 512-token chunker on
a 314-words/page book. **The heuristic is wrong for this book — do not "fix"
chunking to satisfy it.** Amend the criterion to a token-based one and record why:

> chunk count within ±25% of `body_tokens / 320`, **and** median `token_count`
> between 200 and 450, **and** zero chunks over 512.

If the real count lands near 620, that means chunks average 170 tokens — that is
the actual defect signal, and it would mean `merge_peers` is not working.

---

## 7. The retrieval gate — the real exit

Mechanical criteria first:

- [ ] zero chunks under 30 tokens
- [ ] every chunk has a non-empty `heading_path` **and** a `page_from`
- [ ] embedding coverage 100% at 1024 dims
- [ ] **re-running WF1 on the same file inserts nothing**
- [ ] exactly one `is_current` version

Then the gate that actually matters. Call `nlq.search_knowledge` by hand for these
five, read the **top 6 chunks** each, and ask: *would I have picked these myself?*
Each is answerable from a known chapter, so a miss is a chunking defect, not a
corpus gap:

| # | Question | Should retrieve from |
|---|---|---|
| 1 | diacetyl rest temperature and timing for lagers | Ch 10 — Brewing Lager Beer |
| 2 | how mash pH affects conversion and how to adjust it | Ch 15 — Understanding the Mash pH |
| 3 | when to add hops for bittering vs aroma | Ch 5 — Hops |
| 4 | pitching rate and rehydrating dry yeast | Ch 6 — Yeast |
| 5 | my beer tastes of green apple / acetaldehyde — cause and fix | Ch 21 — Is My Beer Ruined? |

Also worth running: *"what temperature for a single infusion mash"* (Ch 16) — it
should return process text, **not** BJCP style cards. That directly tests whether
the new corpus displaced the D19 failure mode.

**If the top 6 are wrong, fix chunking now.** Every later phase inherits these chunks.

Then delete the n8n heading-splitter Code node (§12 #7).

---

## 8. Known risks

| Risk | Mitigation |
|---|---|
| Docling conversion is slow (248 pp, 177 images, accurate tables) | Async only. Time the §3 probe before setting the poll guard |
| GPU contention with chat | Never ingest while chatting (§5). Nightly + recency guard |
| `bge-m3` tokenizer download | Loaded fine on the probe — but it is a HuggingFace fetch; confirm the container has network or a cache |
| 177 images inflate the payload | `image_export_mode: referenced`, not `embedded` |
| Book is copyrighted | Local, personal corpus. Do not redistribute chunks or expose the corpus publicly |

---

## 9. When to add more books

**Never add books between recording a baseline and comparing against it.**

| When | Corpus | Why |
|---|---|---|
| Phase 1 (now) | *How to Brew* only | Chunking gate |
| Phase 3, *before* the baseline | 3–5 books | Enough for the 60-question eval to mean something |
| After the Phase 3 baseline | the rest | A regression is now attributable |

---

## 10. Commands

Run compose from this checkout only, never a worktree.

```bash
docker exec n8n n8n export:workflow --id=<ID> --pretty --output=/demo-data/workflows/<f>.json
docker exec n8n chown 1000:1000 /demo-data/workflows/<f>.json
docker exec n8n n8n import:workflow --input=/demo-data/workflows/<f>.json
```

Headless run — the broker-port override is required while the server is up:

```bash
docker exec -e N8N_RUNNERS_BROKER_PORT=5699 -e N8N_RUNNERS_BROKER_LISTEN_ADDRESS=127.0.0.1 n8n n8n execute --id=<ID>
```

Corpus health:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 'chunks', count(*)::text from kb.chunks union all select 'gaps', count(*)::text from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null union all select 'current', count(*)::text from kb.document_versions where is_current;"
```

Token distribution after ingest:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) chunks, min(token_count), percentile_disc(0.5) within group (order by token_count) median, max(token_count), count(*) filter (where token_count > 512) over_512, count(*) filter (where token_count < 30) under_30 from kb.chunks c join kb.document_versions v on v.id=c.version_id where v.source_filename like 'how_to_brew%';"
```

---

## 11. Deferred

- [ ] Correct §6.2 of the architecture doc with the verified endpoint shape and defaults (§2).
- [ ] Amend the Phase 1 chunk-count exit criterion to the token-based form (§6).
- [ ] Merge/push `phase-1.1-wf2-defect-ledger` (2 commits, local only).
- [ ] Prove D15 empirically — truncate `brew.bjcp_styles`, run the *old* graph,
      confirm it generates 0 cards. Recoverable; the fingerprint in §0 verifies the rebuild.
