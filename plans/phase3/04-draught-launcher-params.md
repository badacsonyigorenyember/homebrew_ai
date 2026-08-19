# Book 4 — `wf1-ingest-book` input parameters: *Draught Beer Quality Manual* (4th ed., 2019)

**Scope:** the 13 launcher inputs, what must exist before the run, and a short set of
runnable checks with their expected values. Everything under "measured" was read off the
file or the live stack on 2026-08-19; everything under "expected" is a prediction to score
the run against.

> ## ⭐ Outcome — run 2026-08-19, `measured`
>
> **226 chunks, 0 embedding gaps, version 7 current.** Every parameter below went in unchanged
> and the run needed one thing this file called for: the **`ba_manual` profile**, which did not
> exist and which `Clean + normalise` refused to guess at (*"Unknown cleaning profile"* — the
> deliberate throw). It was added in `774e9c2` and imported into the live workflow.
>
> | Check from the *Tests* section | Predicted here | ⭐ `measured` |
> |---|---|---|
> | chunks | 150–350 (README: ~250) | ✅ **226** |
> | `first_page` ≥ 13 · `last_page` ≤ 124 | ✅ | ✅ **13 / 124** |
> | embedding gaps | 0 | ✅ **0** |
> | dims | 1024, one distinct value | ✅ **1\|1024** |
> | versions · current | `6\|6` | ✅ **6\|6** |
> | glossary / index chunks | 0 | ✅ **0** |
> | `repairs_applied` | 0 (`text_repairs` is `[]`) | ✅ **0** |
> | tabs in stored text | ~0 | ✅ **0** |
> | `ingest_log` | `clean` + `promote` | ✅ both — `clean` is **warn** (46 dropped, which is normal), `promote` **info** |
>
> **Drop ledger:** 272 raw → 226 kept — **25** front-matter heading · **17** front matter
> (p1–p12) · **4** under-30-tokens. ⭐ **The 25 are `ba_manual`'s own rule**: on `profile: book`
> the glossary and index would have been ingested whole.
> **Token shape:** median **232** · p25 **136** · min/max **40 / 542** · **6** over 512 ·
> **0** under 30 · **0** missing heading · **0** missing page.
>
> ⛔ **Two things this run leaves open, stated so they are not mistaken for done:**
>
> 1. ⭐ **A new defect, found afterwards: 29 Private Use Area codepoints**, 21 of them inside
>    `heading_path`. `U+F6BA` is this PDF's display-font hyphen and nothing renders it, so the
>    corpus stores `DIRECTDRAW`, `LONGDRAW`, `OFFFLAVORS`, `SINGLEUSE`, `AIRCOOLED`. The body
>    text of the same chunks spells them correctly. See [`README.md`](README.md)'s book 4
>    section — **this reopens the glyph decoder book 3 closed.**
> 2. ⛔ **Tier A and Tier B have not been run**, and this file is not a §6 plan: there was no
>    predicted chunk count to score, so **standing rule 1 was not exercised on book 4.**
>
> ⚠️ The launcher in n8n is named **`ingest-drought`** — misspelled — and is **not exported to
> git**, which breaks standing rule 4 one book after it was first kept.

## Source facts (measured)

| | Value |
|---|---|
| Host path | `shared/rag-files/pending/Draught-Beer-Quality-Manual-2019.pdf` |
| Path inside n8n | `/data/shared/rag-files/pending/Draught-Beer-Quality-Manual-2019.pdf` |
| `sha256` | `bbf6e63a34f893f229d3627aef63b4b66c5a658b84213dca1d23f051523e3956` |
| Pages · size | 124 · 6,306,893 bytes · 594 × 774 pt |
| Producer | Adobe PDF Library 15.0 (InDesign 15.1) — **not** calibre, **not** Creo |
| Tabs in extracted text | **4** (Water: 75,154 · Malt: 147,910) — the untab block is a near no-op here |
| Hyphen-wrap probe, broadened to `[-‐–—]$` | **0 at-risk sites** → `text_repairs` must be `[]` |
| Front matter | PDF p1–p12 (cover, copyright, TOC p5–p7, Preface p9–p10, Acknowledgments p11–p12). Introduction starts **p13** |
| Back matter | Glossary p111–p114, Index p115–p122 — headed `DRAUGHT BEER GLOSSARY` / `INDEX` |
| Body layout | two-column throughout; Appendices A–D (p99–p110) are real content, keep them |

---

## Prerequisites

1. ✅ **DONE in `774e9c2`.** ~~The `ba_manual` cleaning profile does not exist yet.~~ It now
   exists in both the tracked JSON and the live workflow; the text below is kept because it is
   what the error meant and what the fix was.
   **The `ba_manual` cleaning profile does not exist yet.** `Clean + normalise` in
   `wf1-ingest-book` carries `PROFILES = { book: … }` and a deliberate throw:
   `Unknown cleaning profile "ba_manual" — implement it in this node before running`.
   The run fails at node 13 until a `ba_manual` key is added. Minimum viable shape,
   matching the source's back matter:

   ```js
   ba_manual: {
     dropHeading: /^(Contents|Table of Contents|Index(?![a-z])|Draught Beer Glossary|Glossary|Acknowledg|Copyright|Preface)/i,
     dropReferences: false,
     minTokens: 30,
   },
   ```

   `Index(?![a-z])` rather than `Index`: the copyright page credits *"Indexing: Doug Easton"*,
   which the naive form matched. `dropReferences: false` because this manual carries no
   per-chapter References lists, and no appendix rule because Appendices A–D are content.

   If you would rather not touch the node yet, `profile: "book"` runs unchanged — but its
   `dropHeading` is anchored and will **not** match `DRAUGHT BEER GLOSSARY`, so the glossary
   and index survive unless `extra_drop_regex` catches them (see the parameter table).

2. **A launcher workflow.** `wf1-ingest-book` starts from an `executeWorkflowTrigger`, so it
   cannot be run on its own — it needs a 2-node caller (Manual Trigger → Execute Sub-workflow
   → `NoNCV2mkQEppWP7O`) with the 13 fields below mapped as constants. Copy
   `n8n/demo-data/workflows/ingest-malt.json`, rename to `ingest-draught`, replace the 13
   values, and **export it to git before the run**. Check no second workflow of that name
   exists first (`docker exec n8n n8n list:workflow`) — book 3 left two `ingest-malt`.

3. **Stack up**: `docling`, `ollama` (bge-m3 loaded, 1024 dims) and `supabase-db` running,
   compose brought up from this checkout, not a worktree.

4. **The file must not already be ingested** — dedup is on `file_sha256`; it currently
   returns 0 rows, so this is a fresh ingest and the `Is new file?` branch goes to Docling.

---

## The 13 input parameters

| Field | Value | Why |
|---|---|---|
| `file_path` | `/data/shared/rag-files/pending/Draught-Beer-Quality-Manual-2019.pdf` | container path, not host path |
| `source_format` | `pdf` | |
| `slug` | `draught-beer-quality-manual` | new slug; unique key of `kb.documents` |
| `title` | `Draught Beer Quality Manual` | |
| `doc_type` | `book` | legal under the CHECK constraint (`book` / `style_guide`) |
| `authors` | `Brewers Association Technical Committee` | split on `;` into a text[]; single author here |
| `language` | `en` | |
| `edition_note` | `Brewers Publications, 4th edition, 2019` | |
| `authority` | `reference` | same tier as Water/Yeast/Malt — a published, edited manual |
| `profile` | `ba_manual` | requires prerequisite 1. Use `book` only if you deliberately skip it |
| `front_matter_max_page` | `12` | measured: Introduction starts on PDF p13. Drops cover, copyright, TOC, preface, acknowledgments |
| `extra_drop_regex` | `Draught Beer Glossary\|^Index` | tested case-insensitively against the joined heading path. Redundant if `ba_manual` already lists the glossary; harmless if it matches nothing |
| `text_repairs` | `[]` | the broadened probe found **0** sites. A pair that matches nothing throws — do not invent one |

`text_repairs` is accepted as a JSON string or an array; `[]` as a literal string is fine.

---

## Tests

### Before the run

```bash
sha256sum "shared/rag-files/pending/Draught-Beer-Quality-Manual-2019.pdf"
```
Expected: `bbf6e63a34f893f229d3627aef63b4b66c5a658b84213dca1d23f051523e3956`

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from kb.document_versions where file_sha256='bbf6e63a34f893f229d3627aef63b4b66c5a658b84213dca1d23f051523e3956';"
```
Expected: `0` (not yet ingested — a `1` means the run will short-circuit to `Already ingested`)

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from kb.chunks;"
```
Expected: `1864` — the pre-run baseline every after-check is measured against

```bash
curl -s http://localhost:5001/health; echo; curl -s http://localhost:11434/api/embed -d '{"model":"bge-m3","input":"draught line cleaning"}' | python3 -c "import sys,json;print(len(json.load(sys.stdin)['embeddings'][0]))"
```
Expected: `{"status":"ok"}` and `1024`

```bash
docker exec n8n n8n export:workflow --id=NoNCV2mkQEppWP7O --output=/tmp/wf1.json >/dev/null && docker exec n8n grep -c "ba_manual:" /tmp/wf1.json
```
Expected: `1` — the profile is implemented. `0` means the run throws at `Clean + normalise`

### After the run

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, v.version, v.is_current, v.page_count, count(c.id) as chunks, min(c.page_from) as first_page, max(c.page_to) as last_page from kb.documents d join kb.document_versions v on v.document_id=d.id left join kb.chunks c on c.version_id=v.id where d.slug='draught-beer-quality-manual' group by 1,2,3,4;"
```
Expected: one row · `is_current = t` · `chunks` in the **150–350** band (README's estimate is ~250) ·
`first_page >= 13` (front matter gone) · `last_page <= 124`

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from kb.chunks c join kb.document_versions v on v.id=c.version_id join kb.documents d on d.id=v.document_id left join kb.chunk_embeddings e on e.chunk_id=c.id where d.slug='draught-beer-quality-manual' and e.chunk_id is null;"
```
Expected: `0` — no chunk without an embedding (the same condition `Assert promoted` enforces)

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(distinct vector_dims(embedding)), min(vector_dims(embedding)) from kb.chunk_embeddings;"
```
Expected: `1|1024`

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select stage, level, message from kb.ingest_log order by id desc limit 2;"
```
Expected: two rows, `promote` and `clean`, both `level = info`. A `warn` on `clean` only
reports that chunks were dropped (normal); `error` on `promote` means missing embeddings

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select r->>'find' as find, r->>'applied' as applied from kb.ingest_log, jsonb_array_elements(detail->'repairs') r where stage='clean' order by id desc;"
```
Expected: **no new rows for this document** — `text_repairs` is `[]`

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from kb.chunks c join kb.document_versions v on v.id=c.version_id join kb.documents d on d.id=v.document_id where d.slug='draught-beer-quality-manual' and (c.heading_path::text ilike '%glossary%' or c.heading_path::text ilike '%index%');"
```
Expected: `0` — the back matter was dropped

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*), sum(case when is_current then 1 else 0 end) from kb.document_versions;"
```
Expected: `6|6` — six versions, all current (baseline is `5|5`), nothing else demoted

```bash
./scripts/ask.sh "How often should draught beer lines be cleaned?"
```
Expected: at least 3 of the 6 hits from `draught-beer-quality-manual`, top hit in the
Chapter 7 cleaning material (printed p61–p79 → PDF p73–p91), and the four earlier books
still returning sensible hits on their own topics
