# Plan 01a — WF1 build guide, node by node

Companion to `01-wf1-ingest-document.md`. That file decides *what* and *why*; this
one is the click-by-click *how*. Read §4.1 there first — this guide assumes the
manual-trigger, one-book-per-execution shape.

**Target:** ingest `how_to_brew_john_palmer.pdf` → 448 chunks in `kb.chunks`, all
embedded, one `is_current` version.

---

## 0. Before you open n8n

Verified live 2026-08-01 — all four hold right now:

| Check | Status |
|---|---|
| `docker exec n8n wget -qO- http://docling:5001/health` | `{"status":"ok"}` |
| `docker exec n8n wget -qO- http://ollama:11434/api/tags` | `bge-m3:latest` present |
| PDF visible to n8n at `/data/shared/rag-files/pending/how_to_brew_john_palmer.pdf` | ✅ |
| `NODES_EXCLUDE=[]` — Execute Command is available | ✅ |

**Path note.** n8n sees the share at `/data/shared/rag-files/…`, not the host path.
Every file field below uses the container path.

**Credential.** Every Postgres node uses the existing **`Postgres account`**
(`fDjeFLjBj3r9berH`). Pick it from the dropdown — do not create a second one.

---

## 1. Build order

27 nodes, of which 3 are optional. Build them **in this order** and wire as you go —
n8n v1 executes by node position, so a node placed left of its data source will run
before it and read empty input.

Lay everything out **left to right on one row**, x increasing by ~224, except the
embedding loop body which drops to a second row (§3).

| # | Node | Type (search this in Add Node) |
|---|---|---|
| 1 | When clicking 'Execute workflow' | Manual Trigger |
| 2 | Read PDF for hashing | Read/Write Files from Disk |
| 3 | Crypto | Crypto |
| 4 | Dedup lookup | Postgres |
| 5 | Is new file? | If |
| — | Already ingested — stop | No Operation |
| 6 | Read PDF for upload | Read/Write Files from Disk |
| 7 | Docling submit | HTTP Request |
| 8 | Wait 15s | Wait |
| 9 | Docling poll | HTTP Request |
| 10 | Still running? | If |
| 11 | Assert task finished | Code |
| 12 | Docling fetch result | HTTP Request |
| 13 | Clean + normalise | Code |
| 14 | Ensure doc + version | Postgres |
| 15 | Insert chunks | Postgres |
| 16 | Log ingest summary *(optional)* | Postgres |
| 17 | Reuse embeddings | Postgres |
| 18 | Select chunks needing embeddings | Postgres |
| 19 | Loop Over Items | Loop Over Items (Split in Batches) |
| 20 | Assemble embed input | Code |
| 21 | Ollama embed | HTTP Request |
| 22 | Zip ids + embeddings | Code |
| 23 | Insert embeddings | Postgres |
| 24 | Promote version | Postgres |
| 25 | Assert promoted *(optional)* | Code |
| 26 | Move to processed *(optional)* | Execute Command |

Nodes 19–23 come **verbatim from WF2**, but node 19 already exists in `Book` — paste
only **20–23** from `Digestion` and delete the `Replace Me` placeholder. See §19–23 for
the exact procedure and the two connections the paste will not carry over.

---

## 2. Node settings

### 1 · When clicking 'Execute workflow' — Manual Trigger
No parameters. This is the whole of §4.1: no schedule, no recency guard.

### 2 · Read PDF for hashing — Read/Write Files from Disk

| Field | Value |
|---|---|
| Operation | `Read File(s) From Disk` |
| File(s) Selector | `/data/shared/rag-files/pending/how_to_brew_john_palmer.pdf` |
| Put Output File in Field | `data` (default) |

**A pinned path, not `*.pdf`.** A glob currently matches two PDFs and would push two
items through the poll loop (§4.1).

### 3 · Crypto

| Field | Value |
|---|---|
| Action | `Hash` |
| Type | `SHA256` |
| Binary File | **ON** |
| Binary Property Name | `data` |
| Property Name | `file_sha256` |
| Encoding | `HEX` |

Pin all three of Action/Type/Encoding explicitly — this is D14/D15.

### 4 · Dedup lookup — Postgres

Operation `Execute Query`. Credential `Postgres account`.

```sql
SELECT
  $1::char(64)                AS file_sha256,
  v.id                        AS existing_version_id,
  COALESCE((SELECT count(*) FROM kb.chunks c WHERE c.version_id = v.id), 0) AS existing_chunks
FROM (SELECT 1) dummy
LEFT JOIN kb.document_versions v ON v.file_sha256 = $1::char(64);
```

**Options → Query Parameters:**
```
={{ [$json.file_sha256] }}
```

The `LEFT JOIN` off a dummy row is deliberate: it **always returns exactly one row**,
with `existing_version_id` NULL for a new file. A bare `SELECT … WHERE` would return
zero rows for the common case, and a Postgres node emitting zero items silently ends
the branch — the workflow would look like it "succeeded" having done nothing.

### 5 · Is new file? — If

Condition — **Boolean → is true**:

| Side | Value |
|---|---|
| Left | `={{ $json.existing_version_id === null }}` |
| Operator | Boolean → is true |

A boolean expression rather than a typed number comparison, because it reads
identically regardless of the If node's UI version.

- **true** → node 6 (new file, ingest it)
- **false** → `Already ingested — stop` (No Operation)

### 6 · Read PDF for upload — Read/Write Files from Disk
Identical settings to node 2. Needed because Crypto consumes the binary it hashes,
and the Postgres/If nodes have replaced the item stream regardless.

### 7 · Docling submit — HTTP Request

| Field | Value |
|---|---|
| Method | `POST` |
| URL | `http://docling:5001/v1/chunk/hybrid/file/async` |
| Send Body | **ON** |
| Body Content Type | `Form-Data (multipart/form-data)` |
| Options → Timeout | `60000` |

**Body Parameters** — add 12 entries. The first is the file, the rest are text:

| # | Parameter Type | Name | Value |
|---|---|---|---|
| 1 | `n8n Binary File` | `files` | Input Data Field Name: `data` |
| 2 | Form Data | `convert_from_formats` | `pdf` |
| 3 | Form Data | `convert_image_export_mode` | `referenced` |
| 4 | Form Data | `convert_do_ocr` | `false` |
| 5 | Form Data | `convert_pdf_backend` | `dlparse_v4` |
| 6 | Form Data | `convert_table_mode` | `accurate` |
| 7 | Form Data | `convert_do_table_structure` | `true` |
| 8 | Form Data | `convert_abort_on_error` | `false` |
| 9 | Form Data | `chunking_tokenizer` | `BAAI/bge-m3` |
| 10 | Form Data | `chunking_max_tokens` | `512` |
| 11 | Form Data | `chunking_merge_peers` | `true` |
| 12 | Form Data | `chunking_include_raw_text` | `true` |
| 13 | Form Data | `chunking_use_markdown_tables` | `true` |

**This is the node most likely to be wrong, and it fails slowly.** Build it, then
click **Execute step** on this node alone before wiring anything after it. A correct
call returns `{"task_id": "...", "task_status": "pending"}` in well under a second —
that ack *is* success (§3).

Do **not** add `chunking_use_markdown_images` (§3 Option A) and do **not** add
`to_formats` — it does not exist on chunk endpoints (§2).

### 8 · Wait 15s — Wait

| Field | Value |
|---|---|
| Resume | `After Time Interval` |
| Wait Amount | `15` |
| Wait Unit | `Seconds` |

### 9 · Docling poll — HTTP Request

| Field | Value |
|---|---|
| Method | `GET` |
| URL (expression) | `=http://docling:5001/v1/status/poll/{{ $('Docling submit').first().json.task_id }}` |

Referenced by node name, not `$json` — inside the loop `$json` is the previous poll's
response, which has no `task_id`.

### 10 · Still running? — If

Condition — **Boolean → is true**:

```
={{ ['pending','started','not_started'].includes($json.task_status) && $runIndex < 160 }}
```

- **true** → back to node 8 (`Wait 15s`) — this is the loop
- **false** → node 11

`$runIndex` increments each time this node runs, so it *is* the poll counter. This is
the **max-iteration guard** from §4: 160 × 15 s ≈ 40 min. Measured conversion is
229 s, so a healthy run exits after ~16 polls.

### 11 · Assert task finished — Code

Mode `Run Once for All Items`.

```js
const s = $json.task_status;
if (['pending', 'started', 'not_started'].includes(s))
  throw new Error(`Poll guard hit: still "${s}" after 160 polls (~40 min). Docling task is hung.`);
if (s !== 'success')
  throw new Error(`Docling task_status = "${s}"`);
return $input.all();
```

Without this, hitting the guard would fall through to fetching the result of an
unfinished task and fail later, somewhere less obvious.

### 12 · Docling fetch result — HTTP Request

| Field | Value |
|---|---|
| Method | `GET` |
| URL (expression) | `=http://docling:5001/v1/result/{{ $('Docling submit').first().json.task_id }}` |
| Options → Timeout | `120000` |
| Options → Response → Response Format | `JSON` |

### 13 · Clean + normalise — Code

Mode `Run Once for All Items`. Implements the §5 rules and the §4 field mapping.

```js
// ---- Docling result -> cleaned chunks. Rules from plan 01 §5 ----
const res = $json;

// §3: task_status "success" means the task ran, not that it worked.
const doc = (res.documents && res.documents[0]) || null;
if (doc && doc.status && !['success', 'partial_success'].includes(doc.status))
  throw new Error(`Docling documents[0].status = "${doc.status}"`);

const chunks = res.chunks;
if (!Array.isArray(chunks) || chunks.length === 0)
  throw new Error('Docling returned no chunks');

const DROP_HEADING = /^(Contents|Index|Glossary|Acknowledg|Copyright|About the Author)/i;
const APPENDIX_EF  = /(Metric Conversions|Recommended Reading)/i;

const drops = [];
const kept  = [];

for (const c of chunks) {
  const pages    = Array.isArray(c.page_numbers) ? c.page_numbers.filter(Number.isFinite) : [];
  const pageFrom = pages.length ? Math.min(...pages) : null;
  const pageTo   = pages.length ? Math.max(...pages) : null;
  const heads    = Array.isArray(c.headings) ? c.headings : [];
  const headStr  = heads.join(' > ');
  const raw      = (c.raw_text ?? '').trim();
  const tokens   = Number.isFinite(c.num_tokens) ? c.num_tokens : null;
  // shape-agnostic: doc_items entries may be strings or objects
  const hasTable = JSON.stringify(c.doc_items ?? []).includes('/tables/');

  const drop = (reason) => {
    drops.push({ chunk_index: c.chunk_index, reason, page_from: pageFrom,
                 heading: headStr.slice(0, 120), tokens });
  };

  if (!raw)                                          { drop('empty raw_text');            continue; }
  if (pageTo !== null && pageTo <= 6)                { drop('front matter (p1-p6)');      continue; }
  if (heads.some(h => DROP_HEADING.test(h)))         { drop('front-matter heading');      continue; }
  if (APPENDIX_EF.test(headStr))                     { drop('appendix E/F');              continue; }
  if (heads.some(h => /^references$/i.test(h.trim()))) { drop('chapter References list'); continue; }
  if (tokens !== null && tokens < 30 && !hasTable)   { drop('under 30 tokens, no table'); continue; }
  if (/^\s*\d{1,3}\s*$/.test(raw))                   { drop('page-number-only');          continue; }

  kept.push({
    chunk_index:  c.chunk_index,
    content:      c.text,
    raw_content:  raw,
    heading_path: heads.length ? heads : null,
    page_from:    pageFrom,
    page_to:      pageTo,
    token_count:  tokens,
  });
}

if (kept.length === 0) throw new Error('Cleaning removed every chunk - check the rules');

const toks = kept.map(k => k.token_count).filter(Number.isFinite).sort((a, b) => a - b);

return [{ json: {
  chunks: kept,
  drops,
  stats: {
    raw_chunks:      chunks.length,
    kept:            kept.length,
    dropped:         drops.length,
    median_tokens:   toks.length ? toks[Math.floor(toks.length / 2)] : null,
    max_tokens:      toks.length ? toks[toks.length - 1] : null,
    over_512:        toks.filter(t => t > 512).length,
    under_30:        toks.filter(t => t < 30).length,
    missing_heading: kept.filter(k => !k.heading_path).length,
    missing_page:    kept.filter(k => k.page_from === null).length,
    page_count:      Math.max(...kept.map(k => k.page_to ?? 0)),
  },
}}];
```

It emits **one item** holding the whole array, not one item per chunk — node 15
inserts all of them in a single query rather than 448 round trips.

**Expected on this book: `raw_chunks` 483, `dropped` 35, `kept` 448.** Open the
output panel and read `stats` before continuing. If `dropped` is wildly off, a rule
is over-matching — fix it here, not downstream.

**`chunk_index` keeps Docling's original numbering**, so it has gaps after drops.
That is intentional (provenance); the unique constraint is on `(version_id,
chunk_index)` and needs no contiguity.

**One shape to confirm on first run:** `doc_items` entries could be strings or
objects. `JSON.stringify(...).includes('/tables/')` works either way, but check
`stats.under_30` looks sane (expect 0 after the drop rule) in case table detection
misfired.

### 14 · Ensure doc + version — Postgres

```sql
WITH d AS (
  INSERT INTO kb.documents (slug, title, doc_type, authors, language, edition_note)
  VALUES ('how-to-brew-palmer', 'How to Brew', 'book',
          ARRAY['John Palmer'], 'en', '3rd edition, 2006')
  ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title
  RETURNING id
),
ins AS (
  INSERT INTO kb.document_versions
    (document_id, version, source_filename, file_sha256,
     docling_version, chunker_config, page_count, is_current)
  SELECT d.id,
         COALESCE((SELECT max(v.version) FROM kb.document_versions v
                   WHERE v.document_id = d.id), 0) + 1,
         $2, $1, $3, $4::jsonb, $5::int, false
  FROM d
  ON CONFLICT (file_sha256) DO NOTHING
  RETURNING id
)
SELECT id AS version_id FROM ins
UNION ALL
SELECT id FROM kb.document_versions WHERE file_sha256 = $1
LIMIT 1;
```

**Query Parameters:**
```
={{ [ $('Crypto').first().json.file_sha256, 'how_to_brew_john_palmer.pdf', 'docling-serve 1.19.0', JSON.stringify({ endpoint: 'chunk/hybrid/file/async', tokenizer: 'BAAI/bge-m3', max_tokens: 512, merge_peers: true, use_markdown_tables: true, use_markdown_images: false, table_mode: 'accurate', do_ocr: false, pdf_backend: 'dlparse_v4' }), $json.stats.page_count ] }}
```

`is_current` is **false** here — promotion is node 24's job, via the function.
The `UNION ALL … LIMIT 1` makes the node return the version id whether it inserted
or hit the `file_sha256` conflict.

### 15 · Insert chunks — Postgres

```sql
INSERT INTO kb.chunks
  (version_id, chunk_index, content, raw_content, heading_path,
   page_from, page_to, token_count, content_sha256)
SELECT $1::bigint,
       x.chunk_index,
       x.content,
       x.raw_content,
       CASE WHEN x.heading_path IS NULL THEN NULL
            ELSE ARRAY(SELECT jsonb_array_elements_text(x.heading_path)) END,
       x.page_from, x.page_to, x.token_count,
       encode(sha256(convert_to(x.raw_content, 'UTF8')), 'hex')
FROM jsonb_to_recordset($2::jsonb) AS x(
  chunk_index  int,
  content      text,
  raw_content  text,
  heading_path jsonb,
  page_from    int,
  page_to      int,
  token_count  int
)
ON CONFLICT (version_id, chunk_index) DO UPDATE SET
  content        = EXCLUDED.content,
  raw_content    = EXCLUDED.raw_content,
  heading_path   = EXCLUDED.heading_path,
  page_from      = EXCLUDED.page_from,
  page_to        = EXCLUDED.page_to,
  token_count    = EXCLUDED.token_count,
  content_sha256 = EXCLUDED.content_sha256;
```

**Query Parameters:**
```
={{ [ $json.version_id, JSON.stringify($('Clean + normalise').first().json.chunks) ] }}
```

`content_sha256` is computed **in SQL over `raw_content`**, matching WF2 and §4's
field mapping. `image_refs` is never mentioned — it stays NULL (§3 Option A).

### 16 · Log ingest summary — Postgres *(optional)*

```sql
INSERT INTO kb.ingest_log (version_id, stage, level, message, detail)
VALUES ($1::bigint, 'clean', 'info', $2, $3::jsonb);
```

**Query Parameters:**
```
={{ [ $('Ensure doc + version').first().json.version_id, 'Kept ' + $('Clean + normalise').first().json.stats.kept + ' of ' + $('Clean + normalise').first().json.stats.raw_chunks + ' chunks', JSON.stringify({ stats: $('Clean + normalise').first().json.stats, drops: $('Clean + normalise').first().json.drops }) ] }}
```

This is what §5 means by "log every drop with a reason" — the whole drop list lands
in one `detail` jsonb, queryable later. Skip it and you lose the ability to tell
"cleaning worked" from "cleaning ate the book".

### 17 · Reuse embeddings — Postgres

```sql
INSERT INTO kb.chunk_embeddings (chunk_id, model, embedding)
SELECT DISTINCT ON (c.id) c.id, 'bge-m3', e.embedding
FROM kb.chunks c
JOIN kb.chunks c2            ON c2.content_sha256 = c.content_sha256 AND c2.id <> c.id
JOIN kb.chunk_embeddings e   ON e.chunk_id = c2.id AND e.model = 'bge-m3'
WHERE c.version_id = $1
ON CONFLICT (chunk_id, model) DO NOTHING;
```

**Query Parameters:** `={{ [$('Ensure doc + version').first().json.version_id] }}`

Near-zero effect on the first book. It is what makes a **re-ingest** cheap: identical
text keeps its vector instead of paying for 448 embeddings again.

### 18 · Select chunks needing embeddings — Postgres

WF2's query unchanged:

```sql
SELECT c.id, c.content
FROM kb.chunks c
WHERE c.version_id = $1
  AND NOT EXISTS (SELECT 1 FROM kb.chunk_embeddings e
                  WHERE e.chunk_id = c.id AND e.model = 'bge-m3')
ORDER BY c.chunk_index;
```

**Query Parameters:** `={{ [$('Ensure doc + version').first().json.version_id] }}`

### 19–23 · The embedding loop — copy from WF2

Verified against `Digestion` execution 65 (a clean 116-chunk run) on 2026-08-01. Every
parameter below is the live value, not a paraphrase.

#### Where you actually are

The `Book` workflow already contains node 19 with Batch Size `32`, and n8n's default
**`Replace Me`** (NoOp) sitting on the `loop` output. So this is not a five-node paste:

- **19 already exists** — open it and confirm Batch Size `32`, Options empty. Do not
  re-paste it; a second Loop Over Items would break the `$('…')` references in 22.
- **Paste 20–23 only** from `Digestion`, then **delete `Replace Me`**.
- Delete it *after* wiring, not before — deleting a node in n8n auto-heals the
  connection around it, so removing it first leaves `Loop Over Items[loop]` wired
  straight back to itself.

Current DB state: version **36**, **447 chunks**, **0 embeddings**, `is_current = false`.
447, not the 448 the plan predicted — one extra chunk was dropped by the cleaning
rules. Not worth chasing unless retrieval is poor. 447 ÷ 32 = **14 batches**, the last
holding 31 items.

#### 19 · Loop Over Items — Split in Batches (`splitInBatches`, typeVersion 3)

| Field | Value |
|---|---|
| Batch Size | `32` |
| Options | *(none — leave empty)* |

**Do not set `Reset`.** It re-splits the input on every iteration, which turns the loop
into an infinite one. It is the single most common way this node is broken.

Batch size 32 is a GPU-memory choice, not a throughput one — bge-m3 embeds a 32-item
batch in one forward pass. Measured on WF2: **~2.3 s per batch** for style cards. Book
chunks run longer (median 283 tokens), so budget **4–8 minutes** for all 14 batches.

#### 20 · Assemble embed input — Code (typeVersion 2)

Mode `Run Once for All Items`.

```js
const items = $input.all();
return [{ json: {
  ids:    items.map(i => i.json.id),
  inputs: items.map(i => i.json.content),
}}];
```

Collapses the batch's 32 items into **one** item holding two parallel arrays. That is
the whole point: one HTTP call per batch instead of 32. The arrays are positionally
aligned, and node 22 depends on that alignment holding — nothing between here and
there may reorder, filter, or re-sort items.

Note it embeds `content`, not `raw_content`. `content` is Docling's contextualized text
(heading path prepended), which is what makes a chunk retrievable out of context.

#### 21 · Ollama embed — HTTP Request (typeVersion 4.4)

| Field | Value |
|---|---|
| Method | `POST` |
| URL | `http://ollama:11434/api/embed` |
| Send Body | **ON** |
| Body Content Type | `JSON` |
| Specify Body | `Using JSON` |
| JSON | `={{ { "model": "bge-m3", "input": $json.inputs, "keep_alive": -1 } }}` |
| Options → Timeout | `120000` |
| **Settings → Retry On Fail** | **ON** |

Four things that are easy to get subtly wrong:

- **`/api/embed`, not `/api/embeddings`.** The older singular endpoint takes `prompt`
  (one string) and returns `embedding`. This one takes `input` (an array) and returns
  `embeddings` (an array of arrays). Hit the wrong one and node 22 throws on
  `emb.length`.
- **`keep_alive: -1`** pins the model in VRAM indefinitely. Without it Ollama unloads
  after 5 minutes idle and every batch pays a cold-load. It also means bge-m3 stays
  resident afterwards — expected, and why §4 says not to chat with the assistant
  during the run.
- **The JSON body is an expression producing an object**, not a string of JSON. The
  leading `=` matters; the outer `{{ }}` returns a real object.
- **Retry On Fail is set in WF2** and the guide's old summary omitted it. Keep it. The
  defaults (3 tries, 1 s apart) cover a transient Ollama hiccup mid-run; without it one
  blip loses the whole loop.

#### 22 · Zip ids + embeddings — Code (typeVersion 2)

Mode `Run Once for All Items`.

```js
const src = $('Assemble embed input').first().json;
const emb = $json.embeddings;
if (!Array.isArray(emb) || emb.length !== src.ids.length)
  throw new Error(`Embedding count ${emb?.length} != inputs ${src.ids.length}`);
if (emb[0].length !== 1024)
  throw new Error(`Expected 1024 dims, got ${emb[0].length} — schema mismatch`);
return src.ids.map((id, i) => ({
  json: { chunk_id: id, embedding: '[' + emb[i].join(',') + ']' },
}));
```

Fans one item back out to 32, re-pairing each vector with its chunk id by index.

- **`'[' + emb[i].join(',') + ']'` — a string, deliberately.** pgvector's text input
  format is `[0.1,0.2,…]`. Handing the n8n Postgres node a raw JS array makes the pg
  driver serialise it as a Postgres *array* (`{0.1,0.2,…}`), which `::vector` rejects.
  This is the single non-obvious line in the loop.
- **The 1024 check is a schema tripwire.** `kb.chunk_embeddings.embedding` is
  `vector(1024)`. A different Ollama model (or a quantised bge-m3 variant) would return
  a different width and every insert would fail one row at a time; this fails once,
  loudly, on the first batch.
- **`$('Assemble embed input')` is a node reference by name.** If you paste 20–23 into
  a workflow that already has those names, n8n renames the pasted copies to
  `Assemble embed input1` — and this expression keeps pointing at the *original*,
  silently zipping the wrong ids onto the vectors. After pasting, confirm the node is
  named exactly `Assemble embed input` with no numeric suffix.
- `.first()` is correct because 20 emits exactly one item per batch.

#### 23 · Insert embeddings — Postgres (typeVersion 2.6)

Operation `Execute Query`. Credential `Postgres account` (`fDjeFLjBj3r9berH`).

```sql
INSERT INTO kb.chunk_embeddings (chunk_id, model, embedding)
VALUES ($1, 'bge-m3', $2::vector)
ON CONFLICT (chunk_id, model) DO UPDATE
  SET embedding = EXCLUDED.embedding, created_at = now()
RETURNING chunk_id, (xmax = 0) AS inserted;
```

**Options → Query Parameters:**
```
={{ [$json.chunk_id, $json.embedding] }}
```

- **This node runs once per input item** — 32 queries per batch, 447 for the book.
  Measured at 8–14 ms per batch total in WF2, so the round trips are free next to the
  GPU time. Leave `Execute Once` **off**; turning it on would insert one chunk per
  batch and silently drop 31.
- **`(xmax = 0) AS inserted`** distinguishes a fresh insert (`true`) from an update of
  an existing row (`false`). On a first run every row should be `true`. A run that
  comes back mostly `false` means node 17 `Reuse embeddings` already filled them and
  node 18 should have returned nothing — worth a look.
- `DO UPDATE` rather than `DO NOTHING` so a re-embed with a changed model actually
  overwrites.

#### Wiring these five

```
Select chunks needing embeddings → Loop Over Items
Loop Over Items  [done, output 0] → Promote version        ← node 24
Loop Over Items  [loop, output 1] → Assemble embed input
Assemble embed input → Ollama embed → Zip ids + embeddings → Insert embeddings
Insert embeddings → Loop Over Items                        ← closes the loop
```

Two things the copy-paste will *not* bring across, because their source nodes were not
part of the selection: `Select chunks needing embeddings → Loop Over Items` (already
wired in `Book`) and the `done` output. Wire the `done` output by hand.

**The `done` output carries every item that was fed back into the loop.** Measured in
WF2: the four loop passes returned 32+32+32+20 items, and the `done` branch emitted all
**116** at once — so `promote_version($1)` executed **116 times**. For the book that is
**447 executions** of node 24. The function is idempotent so the result is correct
either way, but if you would rather it ran once, set **Settings → Execute Once = ON**
on node 24. WF2 does not, which is why the guide never mentioned it.

Place 20–23 on a row ~430 px below node 19 (WF2 uses y `208` → `400`), each ~224 px
apart, and keep all four to the **right** of `Loop Over Items` — under execution order
v1 a node positioned left of the loop node will run before it and read empty input.

### 24 · Promote version — Postgres

```sql
SELECT * FROM kb.promote_version($1);
```

**Query Parameters:** `={{ [$('Ensure doc + version').first().json.version_id] }}`

Never hand-roll the `is_current` flip. The function refuses to promote unless
`total > 0 AND missing = 0`, which is the coverage gate.

### 25 · Assert promoted — Code *(optional)*

```js
const r = $json;
if (r.missing > 0)  throw new Error(`${r.missing} of ${r.total} chunks have no embedding — not promoted`);
if (!r.is_current)  throw new Error(`Version ${r.version_id} did not become current`);
return [{ json: r }];
```

`promote_version` returns quietly without promoting when coverage is incomplete. This
turns that silence into a failed execution.

### 26 · Move to processed — Execute Command *(optional)*

```
mv /data/shared/rag-files/pending/how_to_brew_john_palmer.pdf /data/shared/rag-files/processed/
```

Runs inside the n8n container, where that path exists. Safe to skip on the first run
and move the file by hand once the §7 gate passes — arguably better, since a failed
gate means you want the file back in `pending/` anyway.

---

## 3. Wiring

Straight line 1 → 26, with three exceptions:

**Dedup branch (node 5):**
- `Is new file?` **true** → `Read PDF for upload`
- `Is new file?` **false** → `Already ingested — stop`

**Poll loop (node 10):**
- `Still running?` **true** → back to `Wait 15s`
- `Still running?` **false** → `Assert task finished`

**Embedding loop (node 19)** — the Loop Over Items node has two outputs, and this
topology is copied from WF2:
- output **`done`** (index 0) → `Promote version`
- output **`loop`** (index 1) → `Assemble embed input`
- `Insert embeddings` → back to `Loop Over Items`

Place 20–23 on a lower row so the loop is visually obvious and, more importantly, so
none of them sits left of `Loop Over Items`.

**Settings → check both:** `Execution Order` = `v1`, `Binary Mode` = `separate`
(WF2 uses exactly these).

---

## 4. First run

Do **not** activate the workflow — a manual trigger needs no activation.

1. **Test node 7 alone first.** Click `Docling submit` → Execute step. Expect a
   `task_id` in under a second. If it 422s, the multipart body is wrong; fix it here
   before spending 4 minutes on a full run.
2. Click **Execute workflow**. Expect **~4–5 minutes**, nearly all of it in the poll
   loop. Do not chat with the assistant meanwhile — that is the GPU contention
   mitigation now that the recency guard is gone (§4.1).
3. Read `Clean + normalise` output: `stats.kept` should be **448**.

Then export immediately — the file is the source of truth, not the browser:

```bash
docker exec n8n n8n export:workflow --id=<ID> --pretty --output=/demo-data/workflows/wf1-ingest.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-ingest.json
```

---

## 5. Verify

Corpus health — expect `chunks` 564 (116 BJCP + 448), `gaps` 0, `current` 2:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 'chunks', count(*)::text from kb.chunks union all select 'gaps', count(*)::text from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null union all select 'current', count(*)::text from kb.document_versions where is_current;"
```

Token distribution for this book — expect median ~283, `under_30` 0:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) chunks, min(token_count), percentile_disc(0.5) within group (order by token_count) median, max(token_count), count(*) filter (where token_count > 512) over_512, count(*) filter (where token_count < 30) under_30 from kb.chunks c join kb.document_versions v on v.id=c.version_id where v.source_filename like 'how_to_brew%';"
```

`over_512` will be about **4** — expected, not a defect (§4, contextualization
arithmetic).

Metadata completeness — both must be 0:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) filter (where heading_path is null or cardinality(heading_path)=0) no_heading, count(*) filter (where page_from is null) no_page from kb.chunks c join kb.document_versions v on v.id=c.version_id where v.source_filename like 'how_to_brew%';"
```

**Idempotency — the §7 criterion.** Move the PDF back to `pending/` if node 26 moved
it, then run the workflow again. It must stop at `Already ingested — stop` and insert
nothing. Re-run the corpus health query and confirm the counts are unchanged.

Then the real gate: the five retrieval questions in §7 of plan 01. **If the top 6 are
wrong, fix chunking now** — every later phase inherits these chunks.
