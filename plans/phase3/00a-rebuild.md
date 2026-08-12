# Plan 00a — the schema, the ingest engine, and *How to Brew*

**Status:** ✅ **built and verified** — 447 chunks, 0 embedding gaps, reproduced twice ·
**Written:** 2026-08-07
**Prereqs:** D33 executed (✅) · D32 accepted (✅) · D30 settled (✅)
**Blocks:** everything. 0b needs this schema; books 1–9 need this engine.
**Follows:** [`plans/phase3/README.md`](README.md) §6, the per-source plan contract.

> ## ⭐ Reset — undo everything this workflow added
>
> **Run this to start over**, including after a run that died partway — the engine writes a
> `kb.documents` row, a `kb.document_versions` row and its chunks before it ever reaches the
> embedding loop, so a half-finished run leaves state behind.
>
> ```bash
> docker exec supabase-db psql -U postgres -d postgres -c "delete from kb.document_versions where file_sha256='e29d11cf7ed0cefe52c2544a782e94bc6bb53213e5a84dc1b926c6d37960f410';"
> ```
>
> | | |
> |---|---|
> | **Keyed on** | *How to Brew*'s SHA-256 — it cannot touch another document |
> | **Cascades** | `kb.chunks` from the version · `kb.chunk_embeddings` from the chunks · `kb.ingest_log` from the version |
> | **Left behind** | ✅ the `kb.documents` row — reused via `ON CONFLICT (slug) DO UPDATE` |
> | ⛔ **Cannot undo** | schema changes from `db/init/*.sql`, or any edit to the engine's nodes |
>
> **Verify — expected `0` chunks for this slug after the reset:**
>
> ```bash
> docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from kb.chunks c join kb.document_versions v on v.id=c.version_id join kb.documents d on d.id=v.document_id where d.slug='how-to-brew-palmer';"
> ```
>
> ⚠️ **This is also the only way to re-ingest.** The dedup branch is keyed on the same hash,
> so without the reset a second run stops at `Already ingested`. That is deliberate — and it
> is why §1.4's fixture test could not be rehearsed before D33's purge.

> ⓘ **Contract note.** Written against README §6's original nine-section skeleton; **§6 was
> revised 2026-08-12** to prerequisites → build → reset → testing → evidence. Nothing is
> missing, it is ordered differently.
>
> ⭐ **n8n expressions here are written without the leading `=`** — paste them straight into
> the expression editor, which supplies it. Where the plan quotes an **exported JSON file**
> the `=` is part of the stored value and stays.

**Target, in one line:** an empty database and an empty n8n become a five-schema
application database, a 26-node ingest engine, a 2-node launcher, and **447 chunks of
*How to Brew* with zero embedding gaps.**

> **This plan is a test with a known answer.** 447 is not an estimate. This exact PDF, this
> Docling service and these form fields produced 447 chunks at 100% embedding coverage when
> they were measured on 2026-08-01, and that number is the acceptance gate in §5. Hitting it
> proves the engine on a fixture no later book can offer — every other source in the corpus
> is an unknown, and you would be judging the engine and the book at the same time.

Everything below is written as **build this**, not as a change to anything. Nothing is
assumed to exist except an empty Postgres, an empty n8n, Docling, Ollama and the PDF.

---

## §0 — The one-line verdict

**One shared engine, one thin launcher per book (D30), and this plan builds both.**

The nine sources do not need different processing. They need different *constants*, and
three of them need a different cleaning profile. That is a parameter, not a workflow — so
`wf1-ingest-book` is built once, takes its book-specific values through a sub-workflow
input contract, and each source gets a 2-node `ingest-<slug>` launcher with its own name in
the workflow list and its own Run button.

### 0.1 What gets built

| | Thing | Nodes / files | §|
|---|---|---|---|
| 1 | The five-schema database | 6 SQL files + `docker-compose.yml` | §2.1 |
| 2 | `wf1-ingest-book` — the engine | 26 nodes | §2.2 |
| 3 | `ingest-how-to-brew` — the launcher | 2 nodes | §2.4 |
| 4 | The *How to Brew* corpus | 447 chunks | §5, §8 |

### 0.2 The engine at a glance

```
Ingest book input (sub-workflow trigger, 12 fields)
  → hash the file → look it up → new?  ──no──→ stop
                                  └─yes─→ Docling submit → poll until done
  → fetch result → clean + normalise → ensure doc + version → insert chunks
  → reuse identical embeddings → select what still needs one
  → loop in batches of 32: assemble → Ollama embed → zip → insert
  → promote the version → assert it promoted → log the run
```

### 0.3 Five settings that decide whether it works

These are the ones that fail quietly rather than loudly. Each is specified in full where the
node is built; they are collected here because they are worth reading before you start.

| | Setting | Why it matters |
|---|---|---|
| 1 | `Loop Over Items` — **Reset must stay unset** | Reset re-splits the input on every iteration, turning the loop into an infinite one |
| 2 | `Ollama embed` — **Retry On Fail ON** | one transient blip mid-loop otherwise loses all 14 batches and minutes of GPU |
| 3 | `Insert embeddings` — **Execute Once OFF** | ON would insert one chunk per batch and silently drop the other 31 |
| 4 | `Promote version` — **Execute Once ON** | the loop's `done` output carries all 447 items; without this the node runs 447 times |
| 5 | Workflow **Settings → Execution Order `v1`, Binary Mode `separate`** | under v1 a node positioned left of its data source runs first and reads empty input |

---

## §1 — The probe

The contract's rule is that no plan is written from assumptions. This source was measured
against the live Docling service with the exact form fields §2.2 specifies, and every number
in §5 is computed from that measurement.

### 1.1 Measured — *How to Brew*, 248 pages

| Measure | Value | Label |
|---|---|---|
| Pages | 248 | measured |
| Raw chunks from Docling | 483 | **predicted** — see §1.2 |
| Chunks after cleaning | **447** | **measured** |
| Dropped | 36 | derived — inherits 483's uncertainty |
| chunks / page | 1.80 | measured |
| median `num_tokens` | **291** | measured |
| min / max | 30 / 524 | measured |
| over 512 tokens | 4 | measured — all four are markdown tables |
| under 30 tokens | **0** | measured |
| missing `page_from` | **0** | measured |
| missing `heading_path` | **0** | measured |
| embedding coverage | 447/447 @ 1024 dims | measured |
| front-matter page range | p.1–p.6 | measured → `front_matter_max_page = 6` |
| Docling conversion time | 229 s | measured |

**The four over-512 chunks are correct behaviour, not a defect.** `HybridChunker` will not
split a table mid-row, so a table whose serialization exceeds the budget emerges oversized —
splitting it would produce two half-tables, each worse than one long one. The widest is 550
tokens against bge-m3's 8192-token window, so nothing is truncated at embed time. The
criterion to score against is *"≤ 1% of chunks exceed `max_tokens`, every one explained"*:
4/447 = **0.9%**. ✅

### 1.2 Two things this run measures for the first time

**The raw chunk count.** 483 is arithmetic, not observation — it is 447 plus a drop count
that was never written down. `Log ingest summary` (node 26) writes the drop ledger, so §6's
test A2b reads the real number.

**Which rules dropped what.** The ledger records every dropped chunk with a reason, a page
and a heading in one `detail` jsonb. **Read it once** (§8 step 10). Every later book inherits
these rules, and this is the cheapest possible look at what they actually eat.

### 1.3 Measured — line wrapping destroys numeric ranges, in every source

**The mechanism.** Every PDF text extractor joins wrapped lines and drops the trailing
hyphen, because that hyphen is nearly always a word split — `compa-`/`nies` → `companies`.
When the wrap lands inside a numeric range, the same rule corrupts data. Page 41 of *How to
Brew* sets `45-` at the end of one line and `90 minutes` at the start of the next, and every
extractor renders that as:

```
"Bittering hops additions are boiled for 4590 minutes to isomerize the alpha acids"
```

**This is not a broken PDF and not a Docling bug.** Three things were tested and all three
reproduce it, which is what identifies it as the near-universal line-joining convention
rather than a defect in any one component:

| Tried | Page 41 result |
|---|---|
| `pdf_backend=docling_parse` / `dlparse_v4` / `pypdfium2` | `4590` — identical across all three |
| `do_ocr=true, force_ocr=true` | `4590` — the OCR pipeline joins lines the same way |
| `pdftotext` (poppler, an unrelated library) | `4590` |
| **`pdftotext -layout`** | **`45-` ⏎ `90 minutes`** ← the hyphen is there |

⛔ **There is no Docling setting for this.** All 45 options on `/v1/convert/file` were
enumerated; none controls hyphenation or line joining. The only extraction mode that keeps
the information is `-layout`, which is not a chunking mode. So the sites must be found before
ingest and repaired after it, via `text_repairs`.

**The probe** — [`scripts/hyphen-probe.sh`](../../scripts/hyphen-probe.sh) runs `-layout`,
reports every line ending in `digit-` whose successor starts with a digit, and emits a draft
`text_repairs` array. **Measured across all nine sources:**

| PDF | at-risk sites | what they are |
|---|---|---|
| `2026_BA_Beer_Style_Guidelines` | **9** | ⛔ **final-gravity ranges** — `1.006-1.010` → `1.0061.010` |
| `how_to_brew_john_palmer` | **5** | temperatures, boil times, a dollar range |
| `water_a_comprehensive_g` | **5** | pH `5.6-6.0`, `(65-70°C)`, `0.005-0.010`, `50-70%` |
| `hop_varieties` | 1 | `40-50%` |
| `yeast-the-practical-guide` | 1 | ⚠️ false positive — `Total 2,3-` wraps beside a `900 ppb` table cell |
| `malt-a-practical-guide` | 0 | — |
| `Draught-Beer-Quality-Manual-2019` | 0 | — |
| `Stout-Style-Guide` | 0 | — |
| `BeerStyleStudyGuide` | 0 | — |

**Five of nine sources are affected, so this is a standing step in every book's plan, not a
quirk of book 0a.** Two consequences worth carrying forward:

- ⛔ **Book 0b inherits the worst case.** The BA guidelines fuse *final gravity ranges*, and
  those become `ref.styles.fg_min` / `fg_max`. A wrong number there is not a retrieval
  nuisance, it is the truth layer being wrong, against §10.2's correctness = 1.00. Run the
  probe before parsing that file.
- ⚠️ **The probe output is a draft, never a paste.** The Yeast hit is two unrelated table
  cells. Read every line before it goes in a launcher.

**Palmer's five sites**, cross-checked two independent ways — the probe found them from the
PDF, and a scan of the ingested corpus for 4+-digit runs found the same five, in the same
order:

| stored | should be |
|---|---|
| `(95105°F,` | `(95-105°F,` |
| `4590` | `45-90` |
| `6575F.` | `65-75F.` |
| `5560` | `55-60` |
| `$2050` | `$20-50` |

**Damage shapes checked and clear for this book:** fused decimals (`1.0401.050`) 0 — Palmer
writes gravities as `1.040 to 1.050`; word fusions 0 real cases (the 13 regex hits are
`DanStar`, `PrimeTabs`, `mEq/l`); three-digit fusions among mash temperatures 0 — every
`150°F`/`158°F`/`160°F` is genuine.

**The heading-frequency table.** The contract asks for the top 20 headings by frequency,
because plan 06's entire design turned on that one table. It cannot be produced before the
chunks exist, so §8 step 10 records it and pastes it back into this section — after which
*How to Brew* is a fully described fixture rather than a single number.

### 1.4 Preflight — verify all of this before you start

| Check | Required | How |
|---|---|---|
| Schemas `kb` `brew` `ref` `mem` `nlq` | **none exist** | §8 step 0 |
| Roles `n8n_agent` `agent_ro` `mem_writer` | present | `select rolname from pg_roles where rolname in (…)` |
| Extensions `vector` `pg_trgm` `unaccent` `pgcrypto` | present | `select extname from pg_extension` |
| n8n workflows | **0** | `docker exec n8n n8n list:workflow` |
| Docling | healthy | `docker exec n8n wget -qO- http://docling:5001/health` → `{"status":"ok"}` |
| Ollama | `bge-m3` and `gemma4:12b` resident | `docker exec n8n wget -qO- http://ollama:11434/api/tags` |
| The PDF | at `shared/rag-files/pending/how_to_brew_john_palmer.pdf`, 4,630,168 bytes | `ls -l` |
| n8n credential | **`Postgres account`** exists — pick it on every Postgres node | credentials list |

**The file's SHA-256 is `e29d11cf7ed0cefe52c2544a782e94bc6bb53213e5a84dc1b926c6d37960f410`.**
Worth writing down: node 3 computes it and node 15 stores it, so if the Crypto node is ever
misconfigured — wrong hash type, wrong binary property — the value in
`kb.document_versions.file_sha256` simply will not be this string. One glance, and no other
test gives you it.

**Path note.** n8n sees the share at `/data/shared/rag-files/…`, not the host path. Every
file field below uses the container path.

---

## §2 — What gets built, node by node

Three things, in this order: the **schema** (§2.1), the **engine** (§2.2–2.3), the
**launcher** (§2.4). The order is forced — the engine's SQL will not run against a database
with no `kb`.

### 2.1 ✅ The schema — `db/init`

> **✅ Written and validated 2026-08-07.** All six files were applied twice, in order,
> against a throwaway `sqlcheck` database (created and dropped; the real database was not
> touched). Both passes exited 0, so the set is idempotent — which `db-init` requires,
> because it runs on every `docker compose up`. The resulting objects match §6's A0/A0b/A0c
> exactly. **Nothing to write here; §8 steps 0–2 apply it.**

| File | Holds |
|---|---|
| [`00_extensions.sql`](../../db/init/00_extensions.sql) | four extensions, five schemas: `kb` `brew` `ref` `mem` `nlq` |
| [`10_kb.sql`](../../db/init/10_kb.sql) | `documents` → `document_versions` → `chunks` → `chunk_embeddings`, plus `ingest_log` and `kb.promote_version()` |
| [`15_ref.sql`](../../db/init/15_ref.sql) | `ref.styles` — published reference data |
| [`20_brew.sql`](../../db/init/20_brew.sql) | ingredients, inventory, recipes, batches, measurements, sensory notes, brewing math |
| [`30_mem.sql`](../../db/init/30_mem.sql) | `chat_turns`, `memories`, a separate memory vector space, `mem.f_save_memory()` |
| [`40_nlq.sql`](../../db/init/40_nlq.sql) | `nlq.search_knowledge()` and `nlq.find_batches()` — the agent's only surface |
| [`50_roles.sql`](../../db/init/50_roles.sql) | `agent_ro` / `n8n_agent` / `mem_writer`, and the revokes that make `nlq` the only reachable schema |

Four properties of that schema this plan depends on:

**(a) `ref` is a schema of its own, and it is what keeps the `kb`/`brew` boundary absolute.**
`brew` is *"what I actually did"*; `kb` is prose. Published reference data — style
guidelines, hop specs, fault tables — is a third category, and three of the nine sources are
it. `ref.*` → generated cards in `kb` is clean by construction, and `brew.recipes.style_id →
ref.styles(id)` reads correctly: a recipe references a reference table. Cost is one extra
schema; the agent only ever touches `nlq`, so the grant model does not change at all.

**(b) `kb.documents.authority`** is `reference` | `guideline` | `practitioner`, nullable,
populated per source by the launcher. `nlq.search_knowledge` returns it so the tool can write
*"Palmer suggests X; Angry Chair's practice is Y, which is opinion, not reference."*
⛔ **It must never enter ranking.** Ranking by authority suppresses the disagreement the
design exists to surface, and does it invisibly — you would never see the passage that lost.

**(c) `ref.styles.has_vitals`** is a stored generated column, `og_min IS NOT NULL`. 20 of the
116 BJCP styles define no vital statistics because those vary with the base style, and a
model handed `og_min = null` renders **"OG 0.000"** without hesitating. Branch on the column;
do not trust null handling.

**(d) `db-init` runs an explicit file list, in order, and does not glob.** The list lives in
[`docker-compose.yml:171`](../../docker-compose.yml:171). A new `db/init/*.sql` silently
never runs until its name is added there, and `15_ref.sql` must precede `20_brew.sql`
because of the foreign key. Both are already in place.

### 2.2 🔨 The engine — `wf1-ingest-book`, 26 nodes

Build them **in this order** and wire as you go: under execution order v1, a node placed
left of its data source runs before it and reads empty input. Lay everything out left to
right on one row, x increasing by ~224, except the embedding loop body which drops to a
second row.

Every Postgres node uses **Operation `Execute Query`** and the **`Postgres account`**
credential. Every Code node uses mode **`Run Once for All Items`** unless stated.

---

#### 1 · `Ingest book input` — Execute Workflow Trigger (typeVersion 1.2)

**Input source:** `Define using fields below`. Thirteen fields — this is the book profile
contract, and the whole of D30:

| Field | Type | *How to Brew* value | Read by |
|---|---|---|---|
| `file_path` | string | `/data/shared/rag-files/pending/how_to_brew_john_palmer.pdf` | 2, 7 |
| `source_format` | string | `pdf` | 8 |
| `slug` | string | `how-to-brew-palmer` | 15 |
| `title` | string | `How to Brew` | 15 |
| `doc_type` | string | `book` | 15 |
| `authors` | string | `John Palmer` | 15 |
| `language` | string | `en` | 15 |
| `edition_note` | string | `3rd edition, 2006` | 15 |
| `authority` | string | `reference` | 15 |
| `profile` | string | `book` | 14 |
| `front_matter_max_page` | number | `6` | 14 |
| `extra_drop_regex` | string | `(Metric Conversions\|Recommended Reading)` | 14 |
| `text_repairs` | **array** | see below — `[find, replace]` pairs | 14 |

Every downstream node reads these as `$('Ingest book input').first().json.<field>`.

- **`authors` is a `;`-delimited string, not an array.** The mapper's array handling is
  awkward and the SQL splits it in one call. Semicolon rather than comma, because
  "Palmer, John" is a plausible value and a comma split would quietly produce two authors.
- ⭐ **`extra_drop_regex` is what keeps the cleaning profile generic.** *Metric Conversions*
  and *Recommended Reading* are Palmer's appendices E and F — a fact about one book. Left
  inside the profile, every later source would silently inherit a rule about a book it is
  not. Empty string = no extra rule, which is what most launchers pass.
- ⭐ **`text_repairs` puts back the hyphens that line wrapping ate.** §1.3 has the mechanism
  and the evidence: a range split across a line break (`45-` ⏎ `90 minutes`) is joined into
  `4590 minutes` by every extractor, and no Docling option changes it. Generate the list with
  [`scripts/hyphen-probe.sh`](../../scripts/hyphen-probe.sh), **read it**, then paste. For
  *How to Brew* it is five pairs:

  ```json
  [["(95105°F,","(95-105°F,"],["4590","45-90"],["6575F.","65-75F."],["5560","55-60"],["$2050","$20-50"]]
  ```

  Pass `[]` when the probe finds nothing — Malt, Draught, the Stout guide and the Beer Style
  Study Guide all come back clean.

  **This is the one field typed `array` rather than `string`**, which is why the note about
  `authors` does not apply: nothing here needs splitting, the mapper hands the structure
  straight through, and a malformed pair fails loudly in node 14 instead of becoming one
  long string. Node 14 accepts a JSON string too, so a launcher that declares it the other
  way still works.

  **Why per-source data and not a rule in the engine.** The corruption is not recoverable
  from the joined text: `4590` gives no clue where the split belongs, and a generic
  "re-insert a hyphen between digit runs" rule would mangle `1516`, `3000X` and every year in
  the bibliography. Only the pre-ingest `-layout` probe knows, so the knowledge has to travel
  as data.

  **Why a launcher field and not a manual `UPDATE`.** A hand-patched row is lost on the next
  re-ingest and invisible to anyone reading the workflow. As a field it is reproducible,
  versioned with the workflow JSON, and recorded in `ingest_log`.

  ⛔ **OCR does not fix it** — tested with `force_ocr=true`, which still returns `4590`,
  because the OCR pipeline joins wrapped lines the same way. It would also re-read all 248
  pages and move the 447. Repair the five.
- **Why declared fields rather than `Accept all data`.** This engine will be called nine more
  times. Under passthrough a typo'd key becomes `undefined` at the far end of a five-minute
  run — most likely `front_matter_max_page = undefined`, which silently disables front-matter
  dropping. Declared fields make that a visible gap in the launcher's mapper. The cost is
  real: **a fourteenth field later means editing the trigger and every launcher.**

#### 2 · `Read file for hashing` — Read/Write Files from Disk

| Field | Value |
|---|---|
| Operation | `Read File(s) From Disk` |
| File(s) Selector | `{{ $('Ingest book input').first().json.file_path }}` |
| Put Output File in Field | `data` |

An explicit path, never a glob: `*.pdf` currently matches twelve files and would push twelve
items through the poll loop.

#### 3 · `Crypto`

| Field | Value |
|---|---|
| Action | `Hash` |
| Type | `SHA256` |
| Binary File | **ON** |
| Binary Property Name | `data` |
| Property Name | `file_sha256` |
| Encoding | `HEX` |

Set all of Action, Type and Encoding explicitly even though they match the node's defaults.
n8n omits default-valued parameters from the export, so they will disappear from the JSON —
that is expected, and setting them in the UI is still what documents the intent.

#### 4 · `Dedup lookup` — Postgres

```sql
SELECT
  $1::char(64)                AS file_sha256,
  v.id                        AS existing_version_id,
  COALESCE((SELECT count(*) FROM kb.chunks c WHERE c.version_id = v.id), 0) AS existing_chunks
FROM (SELECT 1) dummy
LEFT JOIN kb.document_versions v ON v.file_sha256 = $1::char(64);
```

**Options → Query Parameters:** `{{ [$json.file_sha256] }}`

**The `LEFT JOIN` off a dummy row is the point of this query:** it always returns exactly one
row, with `existing_version_id` NULL for a new file. A bare `SELECT … WHERE` returns zero
rows for the common case, and a Postgres node emitting zero items silently ends the branch —
the workflow would report success having done nothing.

#### 5 · `Is new file?` — If

Condition, **Boolean → is true**:

```
{{ $json.existing_version_id === null }}
```

A boolean expression rather than a typed comparison, so it reads identically regardless of
the If node's UI version.

- **true** → node 7
- **false** → node 6

#### 6 · `Already ingested — stop` — No Operation

Does nothing, and earns its place: it gives the idempotency test (§6 A3) a visible endpoint,
so a second run reads as *"the workflow refused"* rather than *"the workflow did nothing"*.

#### 7 · `Read file for upload` — Read/Write Files from Disk

Same three settings as node 2. Needed because Crypto consumes the binary it hashes, and the
Postgres and If nodes have replaced the item stream regardless.

⚠️ **Type the expression; do not duplicate node 2.** Duplicating produces
`Read file for hashing1`, and a name that describes the wrong job will mislead you at book 4.

#### 8 · `Docling submit` — HTTP Request

| Field | Value |
|---|---|
| Method | `POST` |
| URL | `http://docling:5001/v1/chunk/hybrid/file/async` |
| Send Body | **ON** |
| Body Content Type | `Form-Data (multipart/form-data)` |
| Options → Timeout | `60000` |

**Body Parameters — exactly these ten.** The first is the file, the rest are text:

| # | Parameter Type | Name | Value |
|---|---|---|---|
| 1 | `n8n Binary File` | `files` | Input Data Field Name: `data` |
| 2 | Form Data | `convert_from_formats` | `{{ $('Ingest book input').first().json.source_format }}` |
| 3 | Form Data | `convert_image_export_mode` | `referenced` |
| 4 | Form Data | `convert_do_ocr` | `false` |
| 5 | Form Data | `convert_pdf_backend` | `dlparse_v4` |
| 6 | Form Data | `convert_table_mode` | `accurate` |
| 7 | Form Data | `chunking_tokenizer` | `BAAI/bge-m3` |
| 8 | Form Data | `chunking_max_tokens` | `512` |
| 9 | Form Data | `chunking_include_raw_text` | `true` |
| 10 | Form Data | `chunking_use_markdown_tables` | `true` |

⛔ **Ten fields, not eleven.** In particular **do not add `chunking_merge_peers`** — the 447
was measured without it and it changes how the chunker packs, so adding it could move the
count and you would spend the afternoon blaming the D30 split. Same for
`convert_do_table_structure` and `convert_abort_on_error`: reproduce the fixture on ten
fields first, then decide separately whether any of them is wanted. `to_formats` does not
exist on chunk endpoints at all, and `chunking_use_markdown_images` is deliberately off —
this corpus is text and tables.

⚠️ **This is the node most likely to be wrong, and it fails slowly.** Build it, then click
**Execute step** on this node alone before wiring anything after it. A correct call returns
`{"task_id": "…", "task_status": "pending"}` in well under a second — that ack *is* success.

#### 9 · `Wait 15s` — Wait

| Field | Value |
|---|---|
| Resume | `After Time Interval` |
| Wait Amount | `15` |
| Wait Unit | `Seconds` |

#### 10 · `Docling poll` — HTTP Request

| Field | Value |
|---|---|
| Method | `GET` |
| URL (expression) | `=http://docling:5001/v1/status/poll/{{ $('Docling submit').first().json.task_id }}` |

Referenced by node name, not `$json`: inside the loop `$json` is the previous poll's
response, which has no `task_id`.

#### 11 · `Still running?` — If

Condition, **Boolean → is false**, on:

```
{{ ['pending','started','not_started'].includes($json.task_status) && $runIndex < 160 }}
```

- **true** (the expression is false — polling is over) → node 12
- **false** → back to node 9

`$runIndex` increments each time the node runs, so it *is* the poll counter, and
`< 160` is the max-iteration guard: 160 × 15 s ≈ 40 min against a measured 229 s conversion,
so a healthy run exits after ~16 polls.

#### 12 · `Assert task finished` — Code

```js
const s = $json.task_status;
if (['pending', 'started', 'not_started'].includes(s))
  throw new Error(`Poll guard hit: still "${s}" after 160 polls (~40 min). Docling task is hung.`);
if (s !== 'success')
  throw new Error(`Docling task_status = "${s}"`);
return $input.all();
```

Without this, hitting the guard falls through to fetching the result of an unfinished task
and fails later, somewhere far less obvious.

#### 13 · `Docling fetch result` — HTTP Request

| Field | Value |
|---|---|
| Method | `GET` |
| URL (expression) | `=http://docling:5001/v1/result/{{ $('Docling submit').first().json.task_id }}` |
| Options → Timeout | `120000` |
| Options → Response → Response Format | `JSON` |

#### 14 · `Clean + normalise` — Code

The complete code is §3. It emits **one item holding the whole chunk array**, not 447 items,
so node 16 inserts them in a single query rather than 447 round trips.

#### 15 · `Ensure doc + version` — Postgres

```sql
WITH d AS (
  INSERT INTO kb.documents (slug, title, doc_type, authors, language,
                            edition_note, authority)
  VALUES ($6, $7, $8, string_to_array($9, ';'), $10, $11, $12)
  ON CONFLICT (slug) DO UPDATE SET
    title        = EXCLUDED.title,
    doc_type     = EXCLUDED.doc_type,
    authors      = EXCLUDED.authors,
    edition_note = EXCLUDED.edition_note,
    authority    = EXCLUDED.authority
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
{{ (() => { const p = $('Ingest book input').first().json; return [
  $('Crypto').first().json.file_sha256,
  p.file_path.split('/').pop(),
  'docling-serve 1.19.0',
  JSON.stringify({ endpoint: 'chunk/hybrid/file/async', tokenizer: 'BAAI/bge-m3', max_tokens: 512, use_markdown_tables: true, use_markdown_images: false, table_mode: 'accurate', do_ocr: false, pdf_backend: 'dlparse_v4', profile: p.profile }),
  $json.stats.page_count,
  p.slug, p.title, p.doc_type, p.authors, p.language, p.edition_note, p.authority
]; })() }}
```

Four things worth knowing about this node:

- **`source_filename` is derived from `file_path`**, not passed separately. Two fields that
  must agree are one field — the same rule that forbids storing an assertion twice in the
  schema, applied to a workflow.
- **`ON CONFLICT (slug) DO UPDATE` refreshes five columns.** Without it, correcting a typo in
  `authors` on the launcher would have no effect on a re-ingest, which is a confusing
  half-hour.
- **`chunker_config` records `profile`**, so a stored version says which cleaning branch
  produced it. At book 4 that is the difference between "the manual chunked badly" and "the
  manual went through the wrong profile".
- **`is_current` is `false` here.** Promotion is node 24's job, through the function, which
  refuses unless embedding coverage is complete. Never hand-roll the flip.

The `UNION ALL … LIMIT 1` makes the node return a version id whether it inserted or hit the
`file_sha256` conflict.

#### 16 · `Insert chunks` — Postgres

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
`{{ [ $json.version_id, JSON.stringify($('Clean + normalise').first().json.chunks) ] }}`

`content_sha256` is computed in SQL over `raw_content`. `image_refs` stays NULL.

#### 17 · `Reuse embeddings` — Postgres

```sql
INSERT INTO kb.chunk_embeddings (chunk_id, model, embedding)
SELECT DISTINCT ON (c.id) c.id, 'bge-m3', e.embedding
FROM kb.chunks c
JOIN kb.chunks c2            ON c2.content_sha256 = c.content_sha256 AND c2.id <> c.id
JOIN kb.chunk_embeddings e   ON e.chunk_id = c2.id AND e.model = 'bge-m3'
WHERE c.version_id = $1
ON CONFLICT (chunk_id, model) DO NOTHING;
```

**Query Parameters:** `{{ [$('Ensure doc + version').first().json.version_id] }}`

Near-zero effect on the first book — it is what makes a **re-ingest** cheap. Identical text
keeps its vector instead of paying for 447 embeddings again.

#### 18 · `Select chunks needing embeddings` — Postgres

```sql
SELECT c.id, c.content
FROM kb.chunks c
WHERE c.version_id = $1
  AND NOT EXISTS (SELECT 1 FROM kb.chunk_embeddings e
                  WHERE e.chunk_id = c.id AND e.model = 'bge-m3')
ORDER BY c.chunk_index;
```

**Query Parameters:** `{{ [$('Ensure doc + version').first().json.version_id] }}`

#### 19 · `Loop Over Items` — Split in Batches (typeVersion 3)

| Field | Value |
|---|---|
| Batch Size | `32` |
| Options | *(empty)* |

⛔ **Do not set Reset** — see §0.3. Batch size 32 is a GPU-memory choice, not a throughput
one: bge-m3 embeds a 32-item batch in one forward pass. 447 ÷ 32 = **14 batches**, the last
holding 31.

#### 20 · `Assemble embed input` — Code

```js
const items = $input.all();
return [{ json: {
  ids:    items.map(i => i.json.id),
  inputs: items.map(i => i.json.content),
}}];
```

Collapses the batch's 32 items into one item holding two parallel arrays — one HTTP call per
batch instead of 32. The arrays are positionally aligned and node 22 depends on that
alignment holding, so nothing between here and there may reorder, filter or re-sort items.

Note it embeds `content`, not `raw_content`. `content` is Docling's contextualized text with
the heading path prepended, which is what makes a chunk retrievable out of context.

#### 21 · `Ollama embed` — HTTP Request

| Field | Value |
|---|---|
| Method | `POST` |
| URL | `http://ollama:11434/api/embed` |
| Send Body | **ON** |
| Body Content Type | `JSON` |
| Specify Body | `Using JSON` |
| JSON | `{{ { "model": "bge-m3", "input": $json.inputs, "keep_alive": -1 } }}` |
| Options → Timeout | `120000` |
| **Settings → Retry On Fail** | **ON** |

Three things that are easy to get subtly wrong:

- **`/api/embed`, not `/api/embeddings`.** The singular endpoint takes `prompt` (one string)
  and returns `embedding`. This one takes `input` (an array) and returns `embeddings` (an
  array of arrays). Hit the wrong one and node 22 throws on `emb.length`.
- **`keep_alive: -1`** pins the model in VRAM. Without it Ollama unloads after 5 minutes idle
  and every batch pays a cold load. It also means bge-m3 stays resident afterwards.
- **The JSON body is an expression producing an object**, not a string of JSON. The leading
  `=` matters; the outer `{{ }}` returns a real object.

#### 22 · `Zip ids + embeddings` — Code

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

- **`'[' + emb[i].join(',') + ']'` — a string, deliberately.** pgvector's text input format
  is `[0.1,0.2,…]`. Handing the Postgres node a raw JS array makes the driver serialise it as
  a Postgres *array* (`{0.1,0.2,…}`), which `::vector` rejects. This is the single
  non-obvious line in the loop.
- **The 1024 check is a schema tripwire.** `kb.chunk_embeddings.embedding` is `vector(1024)`.
  A different model would return a different width and every insert would fail one row at a
  time; this fails once, loudly, on the first batch.
- ⚠️ **`$('Assemble embed input')` is a reference by name.** If a node named
  `Assemble embed input1` ever exists, this expression keeps pointing at the original and
  silently zips the wrong ids onto the vectors. Confirm the name has no numeric suffix.

#### 23 · `Insert embeddings` — Postgres

```sql
INSERT INTO kb.chunk_embeddings (chunk_id, model, embedding)
VALUES ($1, 'bge-m3', $2::vector)
ON CONFLICT (chunk_id, model) DO UPDATE
  SET embedding = EXCLUDED.embedding, created_at = now()
RETURNING chunk_id, (xmax = 0) AS inserted;
```

**Query Parameters:** `{{ [$json.chunk_id, $json.embedding] }}`

- **Runs once per input item** — 32 queries per batch, 447 in total, measured at 8–14 ms per
  batch, so the round trips are free next to the GPU time. **Execute Once must stay OFF.**
- **`(xmax = 0) AS inserted`** distinguishes a fresh insert (`true`) from an overwrite
  (`false`). On this run every row should be `true`; mostly `false` means node 17 already
  filled them and node 18 should have returned nothing.

#### 24 · `Promote version` — Postgres

```sql
SELECT * FROM kb.promote_version($1);
```

**Query Parameters:** `{{ [$('Ensure doc + version').first().json.version_id] }}`
**Settings → Execute Once: ON** — the loop's `done` output carries all 447 items.

Never hand-roll the `is_current` flip. The function refuses to promote unless
`total > 0 AND missing = 0`, which is the coverage gate.

#### 25 · `Assert promoted` — Code

```js
const r = $json;
if (r.missing > 0)  throw new Error(`${r.missing} of ${r.total} chunks have no embedding — not promoted`);
if (!r.is_current)  throw new Error(`Version ${r.version_id} did not become current`);
return [{ json: r }];
```

`promote_version` returns quietly without promoting when coverage is incomplete. This turns
that silence into a failed execution.

#### 26 · `Log ingest summary` — Postgres

```sql
INSERT INTO kb.ingest_log (version_id, stage, level, message, detail)
VALUES
  ($1::bigint, 'clean',
   CASE WHEN ($2::jsonb->>'dropped')::int > 0 THEN 'warn' ELSE 'info' END,
   format('cleaning kept %s of %s chunks, %s dropped, %s text repairs',
          $2::jsonb->>'kept', $2::jsonb->>'raw_chunks', $2::jsonb->>'dropped',
          $2::jsonb->>'repairs_applied'),
   jsonb_build_object('stats', $2::jsonb, 'drops', $3::jsonb, 'repairs', $5::jsonb)),
  ($1::bigint, 'promote',
   CASE WHEN ($4::jsonb->>'missing')::int > 0 THEN 'error' ELSE 'info' END,
   format('version %s promoted: %s chunks, %s missing embeddings',
          $4::jsonb->>'version_id', $4::jsonb->>'total', $4::jsonb->>'missing'),
   $4::jsonb)
RETURNING id, stage, level, message;
```

**Query Parameters:**

```
{{ [ $('Ensure doc + version').first().json.version_id, JSON.stringify($('Clean + normalise').first().json.stats), JSON.stringify($('Clean + normalise').first().json.drops), JSON.stringify($json), JSON.stringify($('Clean + normalise').first().json.repairs) ] }}
```

Five parameters, positional — `$5` is the repair ledger, so which substitutions fired and
how often is recoverable months later without re-reading the PDF.

**Two rows per run, and both matter.** The whole drop list lands in one `detail` jsonb,
queryable later — it is how you tell *"cleaning worked"* from *"cleaning ate the book"*.

It writes 2 rows rather than 894 because node 25 is a Code node in `Run Once for All Items`
mode, which collapses the loop's 447 `done` items to one before this node sees them.

### 2.3 Wiring

Straight line 1 → 26, with three exceptions.

**Dedup branch (node 5):**

```
Is new file?  [true]  → Read file for upload
Is new file?  [false] → Already ingested — stop
```

**Poll loop (node 11):**

```
Docling submit → Wait 15s → Docling poll → Still running?
Still running? [true]  → Assert task finished
Still running? [false] → Wait 15s          ← the loop
```

**Embedding loop (node 19)** — two outputs:

```
Select chunks needing embeddings → Loop Over Items
Loop Over Items [done, output 0] → Promote version → Assert promoted → Log ingest summary
Loop Over Items [loop, output 1] → Assemble embed input → Ollama embed
                                 → Zip ids + embeddings → Insert embeddings
Insert embeddings → Loop Over Items         ← closes the loop
```

Place nodes 20–23 on a row ~430 px below node 19 and keep all four to the **right** of it —
under execution order v1 a node positioned left of the loop node runs before it and reads
empty input.

**Workflow Settings:** Execution Order `v1`, Binary Mode `separate`.

### 2.4 The launcher — `ingest-how-to-brew`, 2 nodes

| # | Node | Settings |
|---|---|---|
| 1 | `When clicking 'Execute workflow'` — Manual Trigger | none |
| 2 | `Run ingest engine` — Execute Sub-workflow | Source `Database`, Workflow = `wf1-ingest-book`, Mode `Run once with all items`, **Wait for completion ON**, then fill the 13 mapper fields from §2.2's table |

The mapper *is* the book profile: its values land in the launcher's tracked JSON, so the
whole of what makes this book different from Water is one readable node in one small file.

**Wait for completion ON is not optional.** Off, the launcher reports success the moment
Docling is handed the file, and a failed ingest looks like a green check.

Do **not** activate either workflow — a manual trigger needs no activation.

---

## §3 — The cleaning profile

Node 14, `Clean + normalise`, mode `Run Once for All Items`. Complete and ready to paste.

⚠️ **The standing warning every plan repeats:** if `heading_path` is modified, `content` must
be rebuilt, or the embedding still carries the old heading and the repair does nothing.
**This profile modifies no heading path**, so the warning is inert here. It stops being inert
at book 4.

```js
// ---- Docling result -> cleaned chunks ----
const p       = $('Ingest book input').first().json;
const PROFILE = p.profile;
const FRONT_MAX = Number(p.front_matter_max_page);

if (!Number.isFinite(FRONT_MAX))
  throw new Error(`front_matter_max_page is not a number: ${p.front_matter_max_page}`);

const res = $json;

// task_status "success" means the task ran, not that it worked.
const doc = (res.documents && res.documents[0]) || null;
if (doc && doc.status && !['success', 'partial_success'].includes(doc.status))
  throw new Error(`Docling documents[0].status = "${doc.status}"`);

const chunks = res.chunks;
if (!Array.isArray(chunks) || chunks.length === 0)
  throw new Error('Docling returned no chunks');

// ---- profile registry. A new source format is a branch here, not a workflow ----
const PROFILES = {
  book: {
    dropHeading: /^(Contents|Index|Glossary|Acknowledg|Copyright|About the Author)/i,
    dropReferences: true,
    minTokens: 30,
  },
  // ba_manual    -> book 4 (Draught manual, two-column).
  // byo_magazine -> book 9 (stout guide). See archive/06-stout-guide-ingest.md §3.
  // Deliberately absent until then: a profile that silently behaves like `book`
  // is worse than a thrown error.
};

const cfg = PROFILES[PROFILE];
if (!cfg) throw new Error(`Unknown cleaning profile "${PROFILE}" — implement it in this node before running`);

// Per-source extras: appendix titles and the like. Empty string = no rule.
const EXTRA = (p.extra_drop_regex || '').trim();
const extraRe = EXTRA ? new RegExp(EXTRA, 'i') : null;

// ---- source text repairs: put back the hyphens that line wrapping ate ----
// A range split across a line break ("45-" / "90 minutes") is joined by every PDF
// extractor into "4590 minutes". Not recoverable here, so the pairs come from
// scripts/hyphen-probe.sh as launcher data (§1.3).
// Literal find/replace, applied to BOTH `text` (embedded) and `raw_text` (read by
// the model) before anything else looks at them. Runs over every chunk including
// the ones about to be dropped, so the counts describe the book, not the survivors.
// `applied` counts field-level replacements, so a single site in the PDF scores 2 —
// once in `text`, once in `raw_text`. What matters is that it is never 0.
// Accepts both trigger field types: `array` hands us a real JS array, `string`
// hands us JSON text. Taking both means a launcher cannot break the engine by
// picking the other one.
let REPAIRS;
const rawRepairs = p.text_repairs ?? [];
if (Array.isArray(rawRepairs)) {
  REPAIRS = rawRepairs;
} else if (typeof rawRepairs === 'string') {
  try {
    REPAIRS = JSON.parse(rawRepairs.trim() || '[]');
  } catch (e) {
    throw new Error(`text_repairs is not valid JSON: ${e.message}`);
  }
} else {
  throw new Error(`text_repairs must be an array or a JSON string, got ${typeof rawRepairs}`);
}
if (!Array.isArray(REPAIRS)) throw new Error('text_repairs must resolve to an array');

const repairCounts = REPAIRS.map(([find, repl]) => {
  if (typeof find !== 'string' || typeof repl !== 'string' || !find)
    throw new Error(`text_repairs entries must be ["find","replace"] string pairs, got ${JSON.stringify([find, repl])}`);
  let n = 0;
  for (const c of chunks) {
    for (const field of ['text', 'raw_text']) {
      const before = c[field];
      if (typeof before !== 'string' || !before.includes(find)) continue;
      // function replacer: disables $-substitution in the replacement string
      c[field] = before.replaceAll(find, () => repl);
      n += before.split(find).length - 1;
    }
  }
  return { find, replace: repl, applied: n };
});

// A repair that matches nothing is a lie about the source, not a harmless no-op:
// either the text changed under us (Docling upgrade) or the pair was mistyped.
const dead = repairCounts.filter(r => r.applied === 0);
if (dead.length)
  throw new Error(`text_repairs matched nothing: ${dead.map(r => JSON.stringify(r.find)).join(', ')} — re-probe the source before re-running`);

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

  if (!raw)                                                { drop('empty raw_text');                 continue; }
  if (pageTo !== null && pageTo <= FRONT_MAX)              { drop(`front matter (p1-p${FRONT_MAX})`); continue; }
  if (heads.some(h => cfg.dropHeading.test(h)))            { drop('front-matter heading');            continue; }
  if (extraRe && extraRe.test(headStr))                    { drop('source-specific heading');         continue; }
  if (cfg.dropReferences &&
      heads.some(h => /^references$/i.test(h.trim())))     { drop('chapter References list');         continue; }
  if (tokens !== null && tokens < cfg.minTokens && !hasTable) { drop(`under ${cfg.minTokens} tokens, no table`); continue; }
  if (/^\s*\d{1,3}\s*$/.test(raw))                         { drop('page-number-only');                continue; }

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
  repairs: repairCounts,
  stats: {
    profile:         PROFILE,
    raw_chunks:      chunks.length,
    repairs_applied: repairCounts.reduce((s, r) => s + r.applied, 0),
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

Each rule, what motivates it, and **what it actually removed** — the ledger from A2b, not a
prediction:

| Rule | Motivated by | Dropped |
|---|---|---|
| `pageTo <= FRONT_MAX` (6) | §1.1 front-matter range p.1–p.6 | **18** |
| `^references$` | citation lists are pure noise in a top-6 | **16** |
| `extra_drop_regex` | Palmer's appendices E and F | **1** ⚠️ see below |
| `< 30 tokens && !hasTable` | §1.1's `under_30 = 0`, which §5 makes a hard gate | **1** |
| `dropHeading` | Contents/Index/Glossary carry no answerable content and rank well on FTS | **0** — verified inert: this PDF has no contents, index or glossary to drop |
| page-number-only | leftover running heads | **0** |
| `text_repairs` | the line-break hyphen loss measured in §1.3 | *repairs, never drops — the count is unaffected* |

Total 36, so 483 → 447. `text_repairs` runs before every drop rule and changes no chunk's
existence, only its bytes, so it cannot move the fixture.

⚠️ **`extra_drop_regex` under-fires on this book, and knowingly.** It matched one chunk, on
p.245, where `heading_path[1]` is literally `Appendix F - Recommended Reading`. Everywhere
else in that appendix Docling makes the individual book title the *top* heading rather than a
child of the appendix — `Designing Great Beers - Ray Daniels`,
`The Real Beer Page - www.realbeer.com/library/` — so the joined path never contains the
words the regex looks for. **23 chunks past page 240 are bibliography and URL lists that are
still in the corpus.** Left as-is deliberately: widening the rule would break the exact-447
gate, and that is a scoping decision, recorded in §4, not a silent tweak here.

**Three behaviours the fixture depends on:**

1. **`chunk_index` keeps Docling's numbering**, so it has gaps after drops. The unique
   constraint is `(version_id, chunk_index)` and needs no contiguity — the gaps are
   provenance.
2. **One item out, holding the whole array** — not 447 items.
3. **Tables are exempt from the token floor.** A 12-token table row is a real answer; a
   12-token prose fragment is a running head.

---

## §4 — Overlap scoping

**This source overlaps nothing: it is the first document in the corpus.**

Present because its absence should be a decision rather than an omission. Two things it does
establish for later:

- ⚠️ **It is the overlap *target* for books 1, 2 and 3.** Palmer's ch.15 (water), ch.6
  (yeast) and ch.12 (malt) are the shallow half of each of those pairs. The policy is keep
  both, unconditionally — the 20-page answer and the 273-page answer are different answers,
  and which is correct depends on the question. **Nothing in Water's plan may drop a Palmer
  chunk.**
- `authority = 'reference'` is set here, so book 8's `practitioner` has something to contrast
  against when the passage header starts surfacing it.

**Expected overlap chunks dropped: 0.**

### 4.1 Known scoping debt — Palmer's Appendix F

**Measured:** 23 chunks past page 240 are Appendix F's recommended-reading list and Appendix
E's conversion tables — book titles, publishers, years, and `www.` URLs. §3 explains why
`extra_drop_regex` misses them: Docling promotes each book title to the top of the heading
path, so the appendix name is nowhere in the string the rule tests.

**Why they are still there.** Removing them means either widening the rule (breaks the
exact-447 gate) or a page-range drop (a second book-specific mechanism for one appendix).
Neither is worth doing blind.

**What decides it.** These chunks are almost pure proper nouns, so they are an FTS risk, not
a vector one — they will surface for *"what does Ray Daniels say about…"* and rank on the
name alone. The Layer-2 retrieval-share measurement over books 1–3 is what should settle it:
if any of the 23 ever enters a top-6, drop them then, re-measure, and move the gate from 447
to whatever the run produces. **Until that evidence exists, changing nothing is the correct
action** — this is exactly the "argue a failing criterion rather than tune it" rule applied
to a criterion that has not failed yet.

---

## §5 — Acceptance numbers

Predicted by running §3's rules over §1.1's measured probe.

| Check | Predicted | Gate |
|---|---|---|
| raw chunks from Docling | 483 | informational — this run measures it |
| **kept chunks** | **447** | ⛔ **exactly 447.** ±2 = investigate and record the reason here; ±10 or worse = **stop, the engine is not reproducing the fixture** |
| dropped | 36 | must equal `raw − kept` |
| median `token_count` | 291 | 200–450 |
| max `token_count` | 524 | — |
| over 512 | 4 | ≤ 1%, each explainable as an unsplittable table |
| **under 30** | **0** | ⛔ **must be 0** |
| **missing `page_from`** | **0** | ⛔ **must be 0** |
| **missing `heading_path`** | **0** | ⛔ **must be 0** |
| embedding coverage | 447/447 | ⛔ **100%**, all at 1024 dims |
| `is_current` versions | 1 | exactly 1 |
| `kb.ingest_log` rows | **2** | ⛔ must be 2 — one `clean`, one `promote` |
| `kb.documents.authority` | `reference` | not null |
| corpus share after | **100%** | the 25% rule is meaningless at n=1 — see below |
| `file_sha256` | `e29d11cf…60f410` | must match §1.3 exactly |

**Why 447 is an exact gate and the contract's ±10% band does not apply.** That band exists
for sources whose output nobody has seen. This file, this service and these ten form fields
have been measured together, so a drift of 45 chunks means the cleaning code or
`Docling submit` is not what §2.2 and §3 specify — most likely an extra Docling form field.
That is a defect to find now, not a tolerance to accept.

**Corpus share is 100%, and that is fine.** The 25% threshold is about competition inside a
top-6, and there is nothing to compete with. It becomes meaningful at book 1 (447/937 ≈ 48%)
and lands near 14% at book 9. Recorded here only so the series is continuous.

**Runtime: 8–14 minutes**, so a hung run is recognisable as hung:

| Stage | Expected |
|---|---|
| hash + dedup | < 2 s |
| Docling submit → poll exits | ~229 s (~16 polls at 15 s) |
| clean + insert 447 chunks | < 5 s |
| **embed, 14 batches of 32** | **4–8 min** — the bulk |
| promote + log | < 1 s |

Past **20 minutes** something is wrong. Past **40** the poll guard fires by design and node
12 throws with a readable message.

---

## §6 — Test cases

### Tier A — pipeline (SQL, deterministic)

**A0 · the schema landed.** Run before n8n is touched:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select n.nspname, count(c.oid) from pg_namespace n left join pg_class c on c.relnamespace=n.oid and c.relkind='r' where n.nspname in ('kb','brew','mem','nlq','ref') group by 1 order by 1;"
```

Expected: `brew|7` · `kb|5` · `mem|3` · `nlq|0` · `ref|1`.

**A0b · the style foreign key points into `ref`:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select conname, pg_get_constraintdef(oid) from pg_constraint where conrelid='brew.recipes'::regclass and contype='f';"
```

Expected to include `FOREIGN KEY (style_id) REFERENCES ref.styles(id)`.

**A0c · `search_knowledge` returns `authority`:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select pg_get_function_result(oid) from pg_proc where proname='search_knowledge';" | tr ',' '\n' | grep -c authority
```

Expected: `1`.

**A1 · rows, coverage, nulls:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, count(*) chunks, count(e.chunk_id) embedded, count(*) filter (where c.page_from is null) no_page, count(*) filter (where c.heading_path is null or cardinality(c.heading_path)=0) no_heading, min(c.token_count) min_tok, percentile_disc(0.5) within group (order by c.token_count) median, max(c.token_count) max_tok from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' group by d.slug;"
```

Expected: `how-to-brew-palmer | 447 | 447 | 0 | 0 | 30 | 291 | 524`.

**A2 · the ingest log has 2 rows and a populated drop ledger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select stage, level, message, jsonb_array_length(detail->'drops') drops from kb.ingest_log order by id;"
```

Expected: `clean | warn | cleaning kept 447 of 483 chunks, 36 dropped | 36` and
`promote | info | version N promoted: 447 chunks, 0 missing embeddings | (null)`.

**A2b · which rules did the dropping:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d->>'reason' reason, count(*) from kb.ingest_log, jsonb_array_elements(detail->'drops') d where stage='clean' group by 1 order by 2 desc;"
```

No expected values — this is the first measurement. **Read it once.** A reason with a
suspiciously large count is a rule over-matching, and every later book inherits these rules.

**A3 · idempotency.** Run the launcher a second time. It must finish in **seconds, not
minutes** — that is the real signal — and end at `Already ingested — stop`.

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

Run before and after: **both values identical.** A run that takes four minutes went to
Docling, and the dedup branch is broken regardless of what the counts say.

⭐ **If the corpus is already ingested, the launcher's *first* run is this test.** Nothing
about A3 requires a second ingest — it requires a matching `file_sha256`, which already
exists. So building the launcher (§2.4) and proving idempotency are one action. That is
also the honest way round: a launcher whose very first run must short-circuit exercises the
dedup branch before any book depends on it.

**A4 · corpus totals:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 'chunks', count(*)::text from kb.chunks union all select 'gaps', count(*)::text from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null union all select 'current', count(*)::text from kb.document_versions where is_current union all select 'dims', (select distinct vector_dims(embedding)::text from kb.chunk_embeddings);"
```

Expected: `chunks 447 · gaps 0 · current 1 · dims 1024`. **One row for `dims`** — two means a
second model got in and every comparison downstream is garbage.

**A5 · the repairs fired, and nothing else is fused.** Two halves. First, the ledger:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select r->>'find', r->>'applied' from kb.ingest_log, jsonb_array_elements(detail->'repairs') r where stage='clean';"
```

Expected: five rows, **every `applied` ≥ 1**. The cleaning node throws on a zero, so a
completed run cannot fail this — it is here because a *silently removed* repair would not
throw, and this makes that visible.

**A5b · the pre-ingest probe. ⚠️ This one is mandatory for every source, book 1 onward** —
five of the nine sources are affected (§1.3), so skipping it is not a judgement call:

```bash
./scripts/hyphen-probe.sh shared/rag-files/pending/<book>.pdf
```

It prints every at-risk site with its context and a draft `text_repairs` array. **Read the
sites, delete the false positives, then fill the launcher field.** A table column that wraps
next to a number looks identical to a split range and the probe cannot tell them apart.

**A5c · the post-ingest backstop**, which catches anything the probe's pattern missed:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select c.page_from, m[1] from kb.chunks c, lateral regexp_matches(c.raw_content, '([^0-9.,][0-9]{4,}[^0-9.,])', 'g') m order by 1;"
```

Every hit must be a **year, a quantity, or a citation** — read them, do not count them. For
*How to Brew* after the repairs this is **measured at 20 occurrences**, all legitimate:
`1902`, `1516`, `1842`, `1984`, `1994` ×2, `1995`, `1996` ×2, `1997`, `1998`, `1950'`,
`1860'`, `1500s`, `1800s` ×3, `1000` years, `3000X`, `1370-`. **Any hit that reads as two
numbers shoved together is an unrepaired split** — add it to `text_repairs` and re-run
per §7.

Note the two do not overlap perfectly, which is why both exist: A5b sees splits the digit
scan misses (`5-`/`10` fuses to `510`, only three digits), and A5c sees anything whose line
break the probe's regex did not match.

### Tier B — retrieval (`scripts/ask.sh`, deterministic)

⚠️ **There is no before-baseline to take, and this is the only source where that is true.**
The corpus is empty until this run, so the standing questions cannot be run first. This run
*creates* the baseline that books 1–9 are measured against.

**The 5 standing questions:**

```bash
./scripts/ask.sh "diacetyl rest temperature and timing for lagers"
./scripts/ask.sh "how mash pH affects conversion and how to adjust it"
./scripts/ask.sh "when to add hops for bittering vs aroma"
./scripts/ask.sh "pitching rate and rehydrating dry yeast"
./scripts/ask.sh "my beer tastes of green apple, what causes acetaldehyde and how do I fix it"
```

Each is answerable from a known chapter, so a miss is a **chunking defect, not a corpus
gap** — that is the whole design of the set.

| # | Answerable from | Expected result |
|---|---|---|
| 1 | Ch 10 — Brewing Lager Beer | **4/6 on-target, first hit rank 1** — `10.4 Yeast Starters and Diacetyl Rests`, p.98 |
| 2 | Ch 15 — Understanding the Mash pH | to be recorded |
| 3 | Ch 5 — Hops | **6/6, rank 1** — `Bittering` / `Flavoring` / `Finishing`, all p.41 |
| 4 | Ch 6 — Yeast | to be recorded |
| 5 | Ch 21 — Is My Beer Ruined? | to be recorded |

⛔ **Q1 and Q3 are the real gate of this plan, stronger than 447 itself.** Their expected
results are measured values for these same 447 chunks. **Q1 must put a diacetyl-rest chunk at
rank 1; Q3 must put the three hop-timing chunks at ranks 1–3.** If either misses, the chunks
are not the same chunks — and that compares *content*, where the count only compares
cardinality.

**Pass for the set as a whole:** every question has a genuinely useful chunk at rank 1 or 2,
and ≥ 3 of 6 on-target. Rank matters more than count — the agent gets all six, but a 12B
model weights the top of the list heavily.

| # | on-target /6 | rank of first correct hit | verdict |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

**The control question** — must return process text, not recipe scaffolding:

```bash
./scripts/ask.sh "what temperature for a single infusion mash"
```

Expected shape: no style cards, and `16.1 Single Temperature Infusion` (p.149) in the top 2,
with recipe chunks around it. This is the corpus's known soft spot — recipe chunks are mostly
markdown table scaffolding and compete well on FTS for "mash" and "single". Note what you
see; do not act on it.

**Positive controls (≥ 3).** Every hit must be `how-to-brew-palmer`, the only document:

| Question | Must reach |
|---|---|
| *"how long should I boil wort and why"* | top 3 |
| *"what causes a stuck fermentation"* | top 3 |
| *"how do I calculate strike water temperature"* | top 3 |

**Retrieval share:** trivially 6/6 from one document on all 10 questions, and **not a
signal** — there is one document. Recorded so the series is continuous; the metric becomes
real at book 2.

### Tier C — agent

⛔ **Not runnable in this plan, and that is a decision rather than a skip.** There is no chat
agent yet — WF4 is scheduled after book 0b, together with the tool it depends on. Running an
agent test against no agent is impossible, not omitted.

**Tier C for this source runs as part of the WF4 build**, and must include the refusal check
verbatim, because it is the one hard fail:

> *"How much Citra do I have?"* → *"I don't have a tool for that yet"*

**`scripts/stress/tier1_routing.py` is not run here** — it measures tool routing against a
system prompt, and there is neither. It runs when WF4 is built, where the knowledge row must
read 30/30 and the total must not fall below 73/84.

---

## §7 — Rollback

**The ingest**, if §5 fails:

```sql
DELETE FROM kb.document_versions WHERE id = <version_id>;  -- chunks + embeddings cascade
```

`kb.ingest_log` cascades too, so a re-run gives a clean ledger. The launcher can then be run
again directly: the dedup branch keys on `file_sha256`, and deleting the version removes the
row it matched.

**The schema**, if D32 turns out wrong:

```sql
DROP SCHEMA ref CASCADE;   -- takes brew.recipes.style_id's FK with it
```

then restore the `db/init` files from git and re-run `docker compose up db-init`.
**Cost: zero data.** `ref.styles` is empty until book 0b and `brew.recipes` is empty — the
whole point of doing D32 now is that this paragraph is boring.

**What needs no rollback:** the PDF, `styles.json`, and the workflow JSON in git. Every
artefact this plan produces is reproducible from files on disk.

---

## §8 — Run procedure

0. ⛔ **Start from a verified zero.** Nothing in this plan may be applied by hand — the
   database must only ever be built by `db-init` from the tracked files.
   ```bash
   docker exec supabase-db psql -U postgres -d postgres -c "DROP SCHEMA IF EXISTS kb, brew, mem, nlq, ref CASCADE;"
   ```
   Two seconds, and it is the *whole* reset this project needs: roles and extensions are
   cluster- and database-level, survive it, and `50_roles.sql` re-grants everything.

   **Do not reach for anything bigger.** Dropping the `postgres` database is not available —
   Supabase's own `auth`, `storage`, `realtime`, `vault` and `graphql` schemas live in it.
   `docker compose down -v` destroys the three n8n credentials and ~9 GB of Ollama models,
   and does not even clear the app database, whose data directory is a bind mount at
   `supabase/docker/volumes/db/data`. Worst of both.

   Verify before continuing — expect `0`:
   ```bash
   docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from pg_namespace where nspname in ('kb','brew','mem','nlq','ref');"
   ```
1. ✅ **The `db/init` files and the compose file list** — §2.1. **Written and validated
   2026-08-07.** Commit them before running anything: a migration that has run but is not
   committed is the worst possible state to debug from.
2. **Apply the schema:**
   ```bash
   docker compose up db-init
   ```
   Run from the main checkout, never a worktree. Expect `Schema migrations complete.` and
   **six `>>` lines including `15_ref.sql`**. Five means the compose list is wrong.
3. **Run A0, A0b, A0c** (§6). Three commands, all before n8n is touched. A schema defect
   found now is a two-minute fix; found after the ingest it is a re-ingest.
4. **Build the engine** — §2.2, in node order, wiring per §2.3. At node 8, click **Execute
   step** on that node alone and confirm the `task_id` ack before wiring anything after it.
5. **Run the hyphen probe** (§6 A5b) — `./scripts/hyphen-probe.sh` on the PDF. Read the
   sites, drop the false positives, keep the draft array. For this book it should return the
   five in §1.3; if it returns something else, the file on disk is not the one measured.
6. **Build the launcher** — §2.4, filling all 13 mapper fields. `text_repairs` is typed
   `array`; paste step 5's output as the array literal, brackets and quotes included.
7. **Export both and commit**, before the run:
   ```bash
   docker exec n8n n8n export:workflow --id=<ENGINE_ID> --pretty --output=/demo-data/workflows/wf1-ingest-book.json && docker exec n8n n8n export:workflow --id=<LAUNCHER_ID> --pretty --output=/demo-data/workflows/ingest-how-to-brew.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-ingest-book.json /demo-data/workflows/ingest-how-to-brew.json
   ```
   ⚠️ **`n8n/demo-data/workflows/` still holds five JSON files describing workflows that do
   not exist.** Clear them in the same commit — but **move `wf4-chat-agent.json` into
   `backup/` rather than deleting it**: it is one of the three surviving copies of system
   prompt v3, which the WF4 build needs verbatim. Say where it went in the commit message.
8. ⛔ **Stop before embedding.** Run the launcher. When execution reaches
   `Clean + normalise`, open its output and read `stats` **before** the loop finishes:

   | Field | Must read |
   |---|---|
   | `kept` | **447** |
   | `under_30` | 0 |
   | `missing_page` / `missing_heading` | 0 / 0 |
   | `profile` | `book` |

   If `kept` is not 447, **stop the execution now.** Embedding 447 wrong chunks costs
   8 minutes of GPU and then a rollback. Node 14 is where this gets fixed.
9. **Let it finish.** 8–14 minutes (§5). **Do not chat with the assistant during the run** —
   embedding saturates the GPU.
10. **Run A1–A4**, read the drop ledger (A2b), and record the heading table:
   ```bash
   docker exec supabase-db psql -U postgres -d postgres -c "select array_to_string(heading_path,' > ') heading, count(*) from kb.chunks group by 1 order by 2 desc limit 20;"
   ```
   **Paste both into §1**, labelled `measured`. That is what turns *How to Brew* into a fully
   described fixture rather than a single number.
11. **Run Tier B** and fill the five-row table. Q1 and Q3 are the gate; Q2, Q4 and Q5 become
    the baseline.
12. **Idempotency (A3)** — run the launcher again, confirm seconds and an unchanged
    fingerprint.
13. **Move the file:**
    ```bash
    mv "shared/rag-files/pending/how_to_brew_john_palmer.pdf" shared/rag-files/processed/
    ```
    After §6, not before — A3 reads from `pending/`. `file_sha256` stays authoritative for
    dedup either way.
14. **Re-export both workflows and commit** with the measured numbers in the message. Tick
    0a's row in [README §9](README.md).

---

## §9 — What this source does to WF4

**Nothing, because there is no WF4 yet.** Recorded as a decision, and two things this plan
hands forward so they are not rediscovered:

**1. The system prompt is written de-enumerated from the first keystroke.** The prompt is
transcribed verbatim from [`archive/phase2/03-wf4-design.md`](../archive/phase2/03-wf4-design.md) §6
with exactly one substitution — this sentence, which must read:

> *"You answer from that brewer's library — a collection of brewing books, style guidelines
> and practitioner articles — not from your own memory."*

A prompt that names its sources is false the moment a tenth one lands, and enumerating a
growing corpus inside a token-budgeted prompt is a maintenance liability. Written this way
once, every later source costs **zero** prompt edits.

⚠️ Prompt text is the one thing that must never be eyeballed: edit the tracked JSON,
`n8n import:workflow`, **re-activate** (import deactivates), restart n8n, then run
`scripts/stress/tier1_routing.py` and **read the knowledge row first**.

**2. `nlq.search_knowledge` returns an `authority` column** that nothing reads yet. When
`tool-search-brewing-knowledge` is built, its passage-header formatter should surface it —
*"Palmer suggests X; Angry Chair's practice is Y, which is opinion"*. ⛔ **It must never
enter ranking**, in the tool or in the SQL.

Everything else the agent design specifies is unaffected by corpus size: `numCtx` 12288,
top-6, `contextWindowLength` 6, the citation contract, the personal-scope refusal sentence.
Six chunks is six chunks whether the corpus is 447 or 3,100.

---

## Exit — 0a is done when

- [ ] Five schemas exist; `ref.styles` present and empty; style FK points into `ref` (A0/A0b)
- [ ] `kb.documents.authority` exists and `search_knowledge` returns it (A0c)
- [ ] **447 chunks, 0 embedding gaps, 1024 dims, 1 `is_current` version** (A1/A4)
- [ ] `under_30` / `missing_page` / `missing_heading` all 0 (A1)
- [ ] `kb.ingest_log` has 2 rows; the drop ledger is recorded in §1 (A2/A2b)
- [ ] the hyphen probe was run and its sites reviewed (A5b); all 5 `text_repairs` show
      `applied ≥ 1` (A5); A5c's 4+-digit hits are all legitimate years or quantities
- [ ] re-running the launcher inserts nothing, in seconds (A3)
- [ ] Q1 and Q3 hit their expected ranks; Q2, Q4, Q5 recorded as the baseline
- [ ] `wf1-ingest-book.json` and `ingest-how-to-brew.json` committed; stale JSON cleared
- [ ] the heading-frequency table and the drop ledger pasted into §1

**Then 0b is unblocked** — `ref.styles` is waiting for 116 rows, and the card-format A/B has
a corpus to compete against.
