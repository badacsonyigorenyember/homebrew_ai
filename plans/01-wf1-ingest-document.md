# Plan 01 — WF1 `ingest-document`, first book: *How to Brew*

**Status:** §3 probe done ✅ · §4.1 shape decided ✅ · **Next:** §4 build WF1 · **Blocks:** Phase 1 exit, everything after it
**Written:** 2026-07-27 · **Probed:** 2026-08-01 · **Prereqs:** all met (Phase 0 ✅, Phase 1.1 ✅)

Self-contained handoff. A fresh session should work from this file plus
`homebrew_assistant_architecture.md` §5–6 and §11, without re-deriving anything below.

---

## 0. Where we are

- Phase 0 closed, including the live-login test of `n8n_agent`.
- Phase 1.1 closed — WF2's defect ledger (D13–D16) fixed, merged to `main` and
  pushed (`977151a`).
- WF2 is the only workflow in n8n, tracked at `n8n/demo-data/workflows/wf2-digestion.json`
  — **edit the file, then import.** Do not edit in the browser editor.
- `kb.chunks` holds 116 BJCP style cards. A correct corpus fingerprints as
  `md5(string_agg(content_sha256, ',' ORDER BY chunk_index))` = `48a8990d2ba3c4a8ca44f35345c75b39`
- **WF1 is the next step.** The book is chosen and staged.
- **§3 probe ran 2026-08-01: 483 chunks, 229 s, both §2 blockers cleared.** A second
  probe settled image handling: **Option A — images are not ingested, `image_refs`
  stays NULL.** No open questions. **§4 is ready to build.**
- **WF1 is manually triggered, one book per execution — never scheduled (§4.1,
  decided 2026-08-01).** The nightly trigger and the chat-recency guard are struck.

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
| Body text | 78,201 words = **139,859 bge-m3 tokens** (measured 2026-08-01) | Drives the chunk estimate below |
| Density | mean 314 words/page (median 314 — very even) | |
| Embedded images | **177** (Docling parses 182) | **Not ingested — §3 Option A.** Text and tables only |
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

### Two blockers — both CLEARED by the §3 probe (2026-08-01)

- [x] **`raw_text`** — populated on **all 483 chunks**, 0 null / 0 empty. The earlier
      `null` came from the markdown-only probe, not from the flag. Map `raw_text`
      straight into `raw_content`. **No heading-strip fallback needed.**
- [x] **`page_numbers`** — populated on **all 483 chunks**, spanning pages 1–248 with
      every page represented. `page_from`/`page_to` map cleanly.

### Endpoint shape — corrections found while probing

- Prefer **`POST /v1/chunk/hybrid/file/async`** (multipart) over `…/source/async`.
  It takes the PDF as a file part — no base64 step, no ~30 MB JSON body.
- Multipart options are **flat, prefixed form fields**, not nested objects:
  `convert_pdf_backend`, `chunking_tokenizer`, … (see the §3 command).
- **`to_formats` does not exist on the chunk endpoints** — it is a `/v1/convert`
  parameter only. Sending it on a chunk call is dead config.
- `chunking_image_placeholder` defaults to `![IMAGE]`, gated by
  `chunking_use_markdown_images` (default `false`). It is a **static string, not a
  template** — both stay at their defaults per §3 Option A.

### One decision §6 never makes

`use_markdown_tables` defaults to `false`. §6 calls the corpus table-dense and
`table_mode: accurate` "non-negotiable", then never says how tables should be
*serialized* into chunk text. Recommend `true` for this book — hop and water
tables are high-value and a markdown grid embeds better than flattened triplets.

---

## 3. Step 1 — Probe before building anything ✅ DONE 2026-08-01

Do **not** build the workflow first. One curl against the real book answers the two
blockers and calibrates every number below. Expect several minutes: 248 pages,
177 images, `table_mode: accurate`.

This is the exact command that produced the numbers below:

```bash
curl -s -X POST http://localhost:5001/v1/chunk/hybrid/file/async \
  -F 'files=@shared/rag-files/pending/how_to_brew_john_palmer.pdf' \
  -F 'convert_from_formats=pdf' \
  -F 'convert_image_export_mode=referenced' \
  -F 'convert_do_ocr=false' \
  -F 'convert_pdf_backend=dlparse_v4' \
  -F 'convert_table_mode=accurate' \
  -F 'convert_do_table_structure=true' \
  -F 'convert_abort_on_error=false' \
  -F 'chunking_tokenizer=BAAI/bge-m3' \
  -F 'chunking_max_tokens=512' \
  -F 'chunking_merge_peers=true' \
  -F 'chunking_include_raw_text=true' \
  -F 'chunking_use_markdown_tables=true'
```

**`chunking_use_markdown_images` is deliberately absent** (defaults to `false`) —
§3 Option A. This is the exact config WF1 must send.

It returns `{"task_id": …, "task_status": "pending"}` **immediately — that ack is
success, not an error.** Then poll `GET /v1/status/poll/{task_id}` until
`task_status` leaves `pending`/`started`, and fetch `GET /v1/result/{task_id}`.

⚠️ `task_status: "success"` means *the task ran*, not that it worked. Always also
check `documents[0].status` and `len(chunks)` — a bad payload yields
`success` + `chunks: []` + `documents[0].status: "failure"` in under a millisecond.

`do_ocr: false` — the text layer is clean and OCR on a digital PDF is slower *and
worse* (§6.1). If tables come out mangled, that is a `table_mode` problem, not OCR.

**Recorded from the probe:**

- [x] total chunk count → **483**
- [x] `page_numbers` populated? → **✅ all 483**, pages 1–248, every page present
- [x] `raw_text` populated? → **✅ all 483**, 0 null / 0 empty
- [x] token distribution → min 15 · p25 169 · **median 283** · p75 422 · max 524 ·
      mean 290 · **4 over 512** · 3 under 30 · **total 139,859**
- [x] where the 177 images landed → **nowhere. See the finding below.**
- [x] wall-clock → **229 s** (~3.8 min) → poll guard in §4

Also confirmed: `headings[]` non-empty on all 483; 68 chunks carry a table and all
68 render as pipe-markdown, so `use_markdown_tables=true` does what §2 wanted;
contextualization overhead is only ~25 chars (~7 tokens) median.

### ⚠️ Finding — images, and why `image_refs` cannot work as §4 describes

**Probe 1 (`use_markdown_images` default `false`):** across all 483 chunks
`doc_items` holds **only** `texts` (1251) and `tables` (81) — **zero picture refs** —
and `metadata.has_image` is `false` everywhere. The chunker drops pictures entirely.
Docling *does* parse them: a control convert of pp. 20–30 returned 5 `#/pictures/N`
items with real `image.uri` filenames. This also explains why only 3 chunks fall
under 30 tokens instead of §5's expected handful — figure-only pages yielded no chunks.

**Probe 2 (`chunking_use_markdown_images=true`), 488 chunks / 145 s:** pictures now
reach the chunks — **182 picture refs** in `doc_items` (indices 0–181, all distinct),
**134 chunks** with `metadata.has_image`. But:

> **`chunking_image_placeholder` is a static string, not a template.** Every one of
> the 134 chunks carries the literal text `![IMAGE]` — **0 markdown refs with a path.**

So §4's mapping — *"filenames parsed from `![…](…)`"* — **cannot be implemented from
chunk text at any configuration.** Image identity exists only as `doc_items` entries
`#/pictures/N`, resolvable to `image_%06d_<sha256>.png` via `pictures[N].image.uri`
in the converted document (needs `include_converted_doc=true` or a second convert).

Costs of enabling it: +5 chunks, under-30 count rises **3 → 8**, and the new tiny
chunks are pure junk — `'![IMAGE]'` (5 tokens, p1), `'7.2 The "Hot Break"\n![IMAGE]'`
(12 tokens). The placeholder also lands in **`raw_text`**, so it pollutes
`raw_content` and changes `content_sha256`.

**⚠️ Unverified:** whether the referenced PNG bytes are persisted anywhere reachable.
With `target_type=inbody` the `uri` may be a name only — storing filenames could
create dangling refs. Verify before choosing Option B.

### ✅ DECIDED 2026-08-01 — Option A: images are not ingested

**Leave `chunking_use_markdown_images` at its default `false`.** Consequences, which
are now settled and must not be re-litigated during the §4 build:

- `kb.chunks.image_refs` is **NULL for this book.** WF1 does not populate it.
- §5's two image rules are **struck** — there is nothing for them to act on.
- The §3 probe-1 numbers (**483 chunks**, 3 under-30) are the operative ones
  everywhere in this plan. Probe 2's 488 / 8 are recorded for contrast only.
- `raw_content` and `content_sha256` stay free of `![IMAGE]` pollution.

**Rationale:** the placeholder is contentless. It cannot be resolved to a filename
from chunk text, so it adds nothing retrievable while corrupting the hash and
manufacturing 5 junk chunks. Option B — populating `image_refs` from `doc_items`
`#/pictures/N` plus a converted-doc pass to resolve `image_%06d_<sha>.png` — remains
technically available if figure references are ever wanted, but it also requires
first verifying the PNG bytes are persisted at all, which was never established.

---

## 4. Step 2 — Build WF1

Carry these forward from WF2. Each was learned the hard way (§11.1 D14/D15/D21):

- **Strictly linear.** No parallel branches — n8n v1 orders by node position, not
  data dependency.
- **Crypto consumes the binary it hashes.** Read the file twice: hash → re-read → parse.
- **Thread `version_id` as `$1`.** Never re-derive with `ORDER BY version DESC`.
- **Promote via `kb.promote_version($1)`**, never a hand-rolled `is_current` flip.

```
Manual Trigger                                               [§4.1 — run by hand]
  └─ Read/Write Files      pending/<one-book>.pdf   ← pinned path, NOT a glob
  └─ Crypto                action=hash, type=SHA256, encoding=hex   ← pin all three
  └─ Postgres              dedup: SELECT by file_sha256
  └─ IF                    already ingested → move to processed/, stop
  └─ Re-read file          (Crypto ate the binary)
  └─ HTTP POST             /v1/chunk/hybrid/file/async       [config from §3]
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
→ Measured 229 s; 229 × 2 = 458 s = 31 iterations, so **the floor governs: use 160.**

### 4.1 ✅ DECIDED 2026-08-01 — manual trigger, one book per execution

**WF1 is not scheduled.** It is a manually-triggered workflow, run by hand once per
book. Corpus growth is deliberate and staged (§9), not continuous, so there is
nothing for a nightly job to pick up. Settled — do not re-add automation during the
build:

- **`manualTrigger`, not `scheduleTrigger`.** WF2 already carries the exact node
  block to copy. The workflow is never activated; test and run it headless with
  `n8n execute --id=` (§10), so no trigger fires on its own.
- **The `mem.chat_turns` recency guard is deleted, not disabled.** It existed only
  because a nightly job could fire mid-conversation and contend for the GPU (§8).
  Choosing when to run *is* that mitigation — just don't chat during the ~4 minutes.
- **`fileSelector` is a pinned single path**, exactly as WF2 pins `styles.json`.
  A `pending/*.pdf` glob currently matches **two** files and would fan out into two
  items through the async poll loop, where Wait → poll → IF-loop-back has no coherent
  meaning with several tasks in flight. **One book per execution.** Re-point the path
  and run again for the next book.

**What survives the simplification, and why** — these look redundant for a one-shot
run and are not:

| Kept | Reason |
|---|---|
| Dedup on `file_sha256` + IF branch | Two nodes. §9 guarantees re-runs (Stout guide, then Phase 3's 3–5 books). Without it one accidental double-execute silently doubles the corpus and degrades every later retrieval. Also a literal §7 exit criterion |
| Poll loop + 160 guard | Unavoidable — 229 s per conversion regardless of trigger |
| `pending/` → `processed/` move | *More* useful when driven by hand: the folder is the record of which books are in |

**Scope for the first run: `how_to_brew_john_palmer.pdf` alone.** `Stout-Style-Guide.pdf`
is also staged in `pending/` but has never been profiled or probed, and §9 fixes
Phase 1 at *How to Brew* only so the §7 gate stays attributable. Ingest it on a
second run, after the gate passes.

### 4.2 Click-by-click build guide

**`plans/01a-wf1-build-guide.md`** expands the diagram above into 27 nodes with exact
field values, the full SQL, both Code nodes, the wiring, and the verification queries.
Follow it beside the n8n editor. This section stays the design; that file is the build.

### Field mapping — Docling → `kb.chunks`

| Column | Source | Note |
|---|---|---|
| `content` | `text` | already contextualized (adds ~7 tokens) |
| `raw_content` | `raw_text` | ✅ never null on this book — map straight through, no fallback |
| `heading_path` | `headings[]` | ✅ non-empty on all 483 |
| `page_from` / `page_to` | `min/max(page_numbers)` | ✅ populated on all 483 |
| `token_count` | `num_tokens` | **log-only, do not assert ≤ 512** — see below |
| `content_sha256` | `encode(sha256(convert_to(raw_content,'UTF8')),'hex')` | in SQL, same as WF2 |
| `image_refs` | — | **NULL — do not populate.** §3 Option A. Markdown parsing is impossible (static `![IMAGE]`, no filename); images are not ingested for this book |

**Why `token_count` is log-only:** the chunker packs against `max_tokens` on the
*raw* text, then `contextualize()` prepends the heading path afterwards. A chunk
packed to ~514 emerges at 521. That is how the 4 over-512 chunks (max 524) arose —
it is arithmetic, not a defect, and no config value prevents it. **No truncation
risk either way: bge-m3's window is 8192 tokens.**

---

## 5. Cleaning rules, tuned to this book

§6.3 generic rules, with this book's specifics. Log every drop to `kb.ingest_log`
with a reason — the log is how you tell "cleaning worked" from "cleaning ate the book".

Dry-run counts below are **measured against the 483 probe chunks**, not estimated.

| Rule | This book | Measured effect |
|---|---|---|
| Front matter | drop `p1` (title/ISBN) and `p2–p6` (TOC) | **18 chunks** |
| Heading regex `^(Contents\|Index\|Glossary\|Acknowledg\|Copyright\|About the Author)` | matches the p2 block | 1, folded into the above |
| Appendices E, F | drop `Metric Conversions`, `Recommended Reading` | **1 chunk** |
| Per-chapter `References` | drop by heading path | **16 chunks** (2,028 tokens) — estimate was ~15 ✅ |
| `token_count < 30` and no table | 15 pages are figure-only | **3** |
| ~~Image-only chunks~~ | ~~177 images — some chunks will be pure figure~~ | **STRUCK — §3 Option A.** Pictures are not ingested; no such chunks exist |
| Repeated line >60% of pages | **no-op — this book has no running heads** | 0 |
| Page-number-only lines | only 6 in the book | 0–6 |

**Total: 35 unique drops → 448 chunks retained.**

---

## 6. Expected numbers — RESOLVED by the probe

**Actual: 483 chunks, mean 290 tokens, median 283.**

The prediction was directionally right and quantitatively wrong, in an instructive
way. The original guess of 300–400 chunks rested on **105,000 body tokens**, derived
from 78,201 words at ~1.34 tokens/word. **The real figure is 139,859** — bge-m3 runs
~1.79 tokens/word on this text, and markdown table serialization adds more. The
formula was fine; its input was 25% low.

Scoring the amended criterion with the **measured** token count:

> chunk count within ±25% of `body_tokens / 320`, **and** median `token_count`
> between 200 and 450, **and** zero chunks over 512.

| Clause | Target | Actual | |
|---|---|---|---|
| count ±25% of `139,859 / 320 = 437` | 328–546 | **483** | ✅ |
| median `token_count` 200–450 | 200–450 | **283** | ✅ |
| zero chunks over 512 | 0 | **4** (max 524) | ❌ — but see below |

**The third clause is unachievable as written and must be amended.**
`contextualize()` prepends the heading path *after* the chunker has already packed
to `max_tokens`, so any chunk packed near 512 necessarily exceeds it. Restate it
against the pre-contextualization text:

> …**and** zero chunks whose **`raw_text`** exceeds 512 tokens.

For reference, the original heuristic (±20% of `page_count × 2.5` = 496–744) misses
**low by 2.6%** — far closer than the "expect 300–400" prediction. It is still the
wrong criterion for the reason given, but it was not badly calibrated.

**`merge_peers` verdict: working.** The defect signal was ~170 tokens/chunk. Actual
is 290. No chunking changes needed.

---

## 7. The retrieval gate — the real exit

Mechanical criteria first:

- [ ] zero chunks under 30 tokens *(3 in the raw probe; §5 cleaning drops them)*
- [ ] every chunk has a non-empty `heading_path` **and** a `page_from`
      *(pre-verified on all 483 probe chunks — should be free)*
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
| Docling conversion is slow (248 pp, 177 images, accurate tables) | **Measured: 229 s.** Async only; poll guard 160 (§4) |
| GPU contention with chat | Never ingest while chatting. **Handled by §4.1** — the run is manual, so don't start one mid-conversation. No guard node |
| `bge-m3` tokenizer download | Loaded fine on the probe — but it is a HuggingFace fetch; confirm the container has network or a cache |
| 177 images inflate the payload | Moot — images are not ingested (§3 Option A). Keep `image_export_mode: referenced` anyway so nothing base64 can leak into chunk text |
| Book is copyrighted | Local, personal corpus. Do not redistribute chunks or expose the corpus publicly |

---

## 9. When to add more books

**Never add books between recording a baseline and comparing against it.**

Each book is one manual execution of WF1 — re-point `fileSelector` and run again
(§4.1). This is why the dedup branch stays in the workflow.

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

- [ ] Correct §6.2 of the architecture doc with the verified endpoint shape and defaults (§2),
      including the multipart endpoint, the flat `convert_*`/`chunking_*` form fields,
      and the fact that `to_formats` does not exist on chunk endpoints.
- [ ] Amend the Phase 1 chunk-count exit criterion to the token-based form (§6),
      **with the over-512 clause scored against `raw_text`** — the probe showed the
      original wording cannot be satisfied while `contextualize()` is on.
- [x] ~~Choose §3 Option A or B for images.~~ **Decided 2026-08-01: Option A.**
- [ ] §6.4 of the architecture doc assumes chunk text carries parseable image refs.
      It does not, at any config — correct it alongside §6.2, and note that this
      corpus ingests text and tables only.
- [ ] Prove D15 empirically — truncate `brew.bjcp_styles`, run the *old* graph,
      confirm it generates 0 cards. Recoverable; the fingerprint in §0 verifies the rebuild.
