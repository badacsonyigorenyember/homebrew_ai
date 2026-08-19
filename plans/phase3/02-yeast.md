# Plan 02 — Yeast: *The Practical Guide to Beer Fermentation*, through the existing engine

**Status:** ✅ **built, run and the record closed** — ingested **2026-08-12 13:34 UTC**,
**463 chunks `measured`**; Tier A and Tier B run and recorded **2026-08-19** in §4;
Tier C ⬜ **not runnable** (§4.3, book 4.5).
**Written:** 2026-08-12 · **§4 completed with `measured` results 2026-08-19**
**Prereqs:** book 0a's engine and schema (✅ live) · book 0b's styles model (✅ live) ·
book 1's *Water* ingest (✅ live, 382 chunks) · ⚠️ **§1.2's three open items — one closed,
two still open** (§4.6)
**Follows:** [`plans/phase3/README.md`](README.md) §6 — the per-source contract **as revised
2026-08-12**: §0 verdict · §1 prerequisites · §2 build · §3 reset · §4 testing · §5 evidence.
⭐ **§5 was measured first and is placed last.** Every predicted number in §4 is a derivation
from §5's probe output.

> ⭐ **n8n expressions in this plan are written without the leading `=`** (README §6 §3.1).
> Paste them into the expression editor, which supplies the `=` itself. **The one place a `=`
> appears is §1.1's quotation of the exported `wf1-ingest-book.json`**, where it is part of the
> stored value and must stay.

**Target, in one line:** *Yeast* (White & Zainasheff, **325 pages**, `measured` via `pdfinfo`)
becomes **463 chunks** `predicted` in `kb.chunks`, through **`wf1-ingest-book` unchanged**,
driven by a new **2-node `ingest-yeast` launcher** — `profile: book`,
`authority: reference`, `doc_type: book`.

> ## ⭐ Outcome — `measured` 2026-08-19, the run of 2026-08-12
>
> **463 chunks. Every predicted number hit exactly — 21 of 21**, and the four unchanged-state
> checks on the rest of the corpus all held. ⭐ **This is the best result standing rule 1 has
> produced** — book 1 needed a tolerance on one number of nineteen, book 2 on none, including
> the drop ledger by reason (27 / 21 / 15), `page_count` (305) and `repairs_applied` (87).
>
> | | ⭐ `measured` |
> |---|---|
> | §0's verdict — **mapper-only** | ✅ **held.** The only artefact book 2 added is a 2-node launcher. `Clean + normalise` is byte-identical to the one book 1 left behind, and no profile, schema or shared line changed |
> | ⭐ **the repair ledger** | ✅ **recorded for the first time, per pair** — `54 / 17 / 10 / 6`, matching §2.4 pair for pair. `$5` is passed **and stored**, not passed and discarded. ⚠️ One observation, on one book (§4.1 A2c) |
> | Tier A, A1–A7 | ✅ **five pass exactly**, ⚠️ **two carry a miss in the *prediction*** (§4.1 A5's units error, A6's over-count — the residue is smaller than predicted), ⛔ **A3 not observed** |
> | Tier B, 10 questions | ✅ **keep** — all five prior rank-1 chunks still top 3, all four positive controls at **rank 1**, Layer 2 fires on **nothing** for the second run running |
> | ⛔ **§4.2a's Q4 prediction** | ⛔ **falsified.** *"The single largest predicted swing in the plan"* did not happen: Palmer keeps rank 1 on the compound pitching-rate question and Yeast takes 2 of 6. §4.2a explains why, and the explanation is reusable |
> | ⚠️ **§4.2c's carry-forward** | ⭐ **answered, and the answer is *no*.** Water's Q8 shape — one heading on **one page** — did not reproduce. A heading-only threshold *did* fire, on four genuinely different chunks, which is the argument **against** building the heading partition. §4.2c |
> | ⛔ **still open** | A3 never observed · **standing rule 4 broken again** (`ingest-yeast.json` existed only in n8n's database until 2026-08-19) · the orphaned `Clean + normalise1` node still live, still divergent. §4.6 |

---

## §0 — The verdict, in one screen

> ### ⭐ The headline: **mapper-only — the D30 split holds a second time.** But the mapper is
> doing far more work than Water's, and the reason is a finding no previous book produced.
>
> | | Verdict |
> |---|---|
> | A new workflow | ⛔ **no** |
> | A new cleaning **profile** | ⛔ **no** — `book` fits, unchanged |
> | A line of **shared** code | ⛔ **no.** ⭐ **Unlike book 1.** Water needed three lines of tab normalisation; Yeast needs **zero** — `measured`, **0 tab characters** in all 526 probe chunks (§5.1) |
> | A schema change | ⛔ **no** |
> | The launcher's 13-field mapper | ✅ **yes, and it is the whole change** |
>
> ⭐ **README §4 predicted book 2 would cost "nothing — should be near-free." That prediction
> is confirmed, and it should be recorded as confirmed.** A 325-page book from a *third*
> production toolchain (`Creo Normalizer JTP`, against Water's and Palmer's) went through the
> engine with **zero new nodes, zero new profiles, zero schema changes and — this time — zero
> shared-code edits.** Two books in a row inside the launcher is the evidence D30 was designed
> to produce, and it only counts because it is written down before the run.

### 0.1 ⚠️ What is *not* free: the mapper is carrying a broken font

**The finding, `measured` (§5.3): 42 of Yeast's 526 probe chunks carry a heading that is not
text at all.** The book's display font ships a broken `ToUnicode` map, so every heading set in
it extracts as a run of raw glyph identifiers:

```
/g56/g93/g83/g84/g103            →  "Index"
/g65/g84/g85/g84/g97 /g84/g93/g82/g84/g98   →  "References"
/g99/g80/g81/g91/g84/g15/g94/g85 /g82/g94/g93/g99/g84/g93/g99/g98  →  "table of contents"
```

The mapping is mechanical — **glyph id + 17 = ASCII codepoint**, `measured` across all 16
distinct runs — but nothing in the pipeline knows that, and three consequences follow that no
previous source has had:

| Consequence | Why it matters | Where it is handled |
|---|---|---|
| ⛔ **`dropHeading` matches *nothing*** — `measured`, **0 of 262** distinct headings | the shared `book` profile's `^(Contents\|Index\|Glossary\|Acknowledg\|Copyright\|About the Author)` rule is **inert on this book**. Water's `Index` was dropped by it; Yeast's `Index` reads `/g56/g93/g83/g84/g103` and slips straight through | `extra_drop_regex`, §2.2 |
| ⛔ **`dropReferences` matches nothing** — `measured`, **0** headings trim to `references` | same cause; and the bibliography's chunks are headed `Part 1` … `Part 7`, not `References` | `extra_drop_regex`, §2.2 |
| ⚠️ **11 kept chunks keep a garbled heading**, and 17 keep glyph noise in their body | citations and passages carry it. **Not repairable from the launcher** — `text_repairs` reaches `text` and `raw_text`, never `headings` | ⛔ **recorded, not repaired.** §2.5 |

⭐ **All of that is absorbed by two mapper fields — `extra_drop_regex` and `text_repairs`.**
That is precisely what D30 said those fields were for, so the split is not merely surviving
this book, it is being *exercised*. But state it plainly: **Yeast's mapper is not a copy of
Water's with the numbers changed.** It is 27 back- and front-matter drops that the shared
profile would have missed entirely, and a 4-pair repair set that decodes chemistry
(`α-amylase`, `β-amylase`) rather than hyphens.

### 0.2 Per-node verdict

Walked over all 26 wired nodes of `wf1-ingest-book`. ⭐ **Every row is *correct as-is*. There
is no second column this time.**

| Node(s) | Verdict | Why |
|---|---|---|
| 1 `Ingest book input` | ✅ correct as-is | 13 fields; Yeast fills all 13 — including `extra_drop_regex`, which Water left empty |
| 2 `Read file for hashing`, 3 `Crypto`, 4 `Dedup lookup`, 5 `Is new file?`, 6 `Already ingested` | ✅ correct as-is | file-shaped source; dedup path unchanged |
| 7 `Read file for upload` | ✅ correct as-is | Crypto consumes the binary it hashes (D13/D20) — the file is read twice by design |
| 8 `Docling submit` | ✅ correct as-is | ten form fields verified byte-for-byte against the live node (§5.0) and used unchanged in the probe |
| 9 `Wait 15s`, 10 `Docling poll`, 11 `Assert task finished`, 12 `Docling fetch result` | ✅ correct as-is | conversion took **137 s** `measured`; the poll loop covers it |
| 13 `Clean + normalise` | ✅ **correct as-is** | ⭐ **including the untab block book 1 added** — it is a no-op here (0 tabs, `measured`), which is the second confirmation that §0.3 of plan 01 was safe |
| 14 `Ensure doc + version` … 25 `Assert embeddings` | ✅ correct as-is | |
| 26 `Log ingest summary` | ✅ correct as-is | ⭐ `$5` is **wired** — `measured` in both the live workflow and the tracked JSON (§1.1). Yeast is the first run that will record a repair ledger |
| **`ingest-yeast` (new, 2 nodes)** | 🆕 **the intended change** | 13 constants. §2 |

### 0.3 What is *not* built, so its absence is a decision

| Not built | Why |
|---|---|
| A glyph **decoder** in shared code | ⭐ **the runner-up design, and it is argued down in §2.5.** A 12-line `text.replace(/\/g(\d+)/g, c => String.fromCharCode(+c+17))` would fix headings *and* body in one pass. It is rejected **for now** because it is shared code justified by exactly one source, the `+17` offset is a property of *this* PDF's font subset and not of PDFs, and the engine cannot rebuild `content` from a repaired `heading_path` without a second change (plan 06 §4's standing warning). **If book 3 or book 4 shows the same encoding, that is the moment to build it** — and this paragraph is the precedent |
| A per-book `min_tokens` field | ⚠️ **the token floor costs 15 chunks here against Water's 3, and 11 of them are lab-procedure `Materials` lists.** §2.4 argues the loss rather than tuning the floor (standing rule 6). ⛔ A new trigger field is an **engine** change and would break §0's headline for a fix that is the wrong shape anyway |
| A retrieval change | ⛔ **explicitly not.** §4's Layer-2 check may fire; Layer 3 is the designated fix and is built **when it fires**, not in advance |
| A `back_matter_min_page` field | not needed — `extra_drop_regex` reaches all 25 back-matter chunks (§2.2), `measured` |

---

## §1 — Prerequisites

### 1.1 What is already true — verified against the live stack, 2026-08-12

Re-measured for this plan. ⛔ **Nothing below is carried from the prompt or from
[`01-water.md`](01-water.md).** All values `measured`.

| Check | Command | Result |
|---|---|---|
| corpus totals | the §4 A4 query | **1,061** chunks · **0** embedding gaps · **3** `is_current` · **1024** dims (one distinct value) |
| `kb.documents` | `select slug, doc_type, authority, page_count` | `how-to-brew-palmer` `book`/`reference` p.248 **447** · `water-comprehensive-guide` `book`/`reference` p.239 **382** · `bjcp-2021-beer-styles` `style_guide`/`guideline` **232** |
| n8n workflows | `n8n list:workflow` | **4** — `wf1-ingest-book` `NoNCV2mkQEppWP7O` · `ingest-how-to-brew` `BAe1fP1g7ZUsbIaq` · `ingest-water` `ciWYDt5MhFseACiN` · `ingest-bjcp-styles` `Ejf3ESE3SK1XBqe3` |
| ⚠️ `wf1-ingest-book` node count | live export + tracked JSON, connection graph walked | **27 in both**, of which **26 wired and 1 orphan** — `Clean + normalise1`. §1.2 item 1 |
| ✅ **`Log ingest summary` `$5`** | live export + tracked JSON | ⭐ **wired in both.** `jsonb_build_object('stats', $2::jsonb, 'drops', $3::jsonb, 'repairs', $5::jsonb)`, and the Query Parameters pass five values |
| ✅ the untab block | live `Clean + normalise` | **present** (`const untab = …replaceAll('\t',' ')`), above the repair loop |
| `PROFILES` | live `Clean + normalise` | **one key, `book`.** `ba_manual` and `byo_magazine` are comments behind a deliberate throw |
| ⛔ `kb.ingest_log` | `select stage, level, detail ? 'repairs'` | **6 rows**, and `detail ? 'repairs'` is ⛔ **false on all six**. The `$5` edit landed *after* Water ran |
| `doc_type` / `authority` CHECKs | `pg_constraint` | `book` and `reference` both legal |
| Docling · Ollama | `/health` · probe | `{"status":"ok"}` · bge-m3 at 1024 dims |
| n8n bind mount | `docker inspect n8n` | `…/shared → /data/shared` ✅ — §2.2's container path is correct |
| ⭐ **the source file** | `sha256sum` | ✅ **`2f30d7e5d8a965df00dbd225f57c4d759dd8ab90f99974b0ffee9b39f54266a4`** — re-verified, matches the value §3 is keyed on |
| the PDF itself | `pdfinfo` | **325 pages** · Title `Yeast` · Author `White, Chris, Zainasheff, Jamil` · Producer **`Creo Normalizer JTP`** · page size **252 × 373.68 pt** (3.5″ × 5.19″ — a small trim, which is why 325 pages yield fewer chunks than the page count suggests) |

**Two things this re-measurement establishes that the rest of the plan depends on:**

- ⭐ **`$5` is wired, so Yeast is genuinely the first ingest that can record a repair ledger.**
  ⚠️ **Treat it as a fresh capability, not a settled one** — it has never once produced a row.
  §4 A2c checks it rather than assuming it, and §4 states what a *passing* result actually
  proves, which is less than it looks (§4 A2c's note).
- **The `book` profile is still the only one implemented, and Yeast uses it unchanged** — but
  §0.1 is the caveat: two of its three heading rules fire on **nothing** here.

### 1.2 What must be done first — three items, none of which blocks writing this plan

**1. ⚠️ Delete the orphaned `Clean + normalise1` node.** `measured`: no incoming connection,
no outgoing connection, and **its code lacks the untab fix**, so it is a *third* divergent copy
of the cleaning profile sitting in tracked JSON. Harmless to execution — n8n never reaches it —
which is exactly what makes it dangerous. Delete it in the UI, then re-export so the engine is
**26 nodes** as documented:

```bash
docker exec n8n n8n export:workflow --id=NoNCV2mkQEppWP7O --pretty --output=/demo-data/workflows/wf1-ingest-book.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-ingest-book.json
```

**2. ⭐ A3 — watch the dedup short-circuit, live.** ⚠️ **This cannot be checked
retroactively**: a short-circuit writes nothing, so the database cannot tell you it happened.
Fingerprint, run `ingest-water` a second time, fingerprint again:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

Expect **`1061`** and an identical hash both times, and the run must end at
**`Already ingested`** in **seconds, not minutes** — the path is
`Read file for hashing → Crypto → Dedup lookup → Is new file? → Already ingested`, five nodes,
no HTTP, no Docling.

⛔ **If it instead runs a full Docling conversion, stop and fix it before book 2.** A broken
dedup branch does not error; it mints a second version, and Yeast would land **twice** in the
corpus with no error anywhere.

**3. The Tier B baseline is the post-Water one, and that is permanent.** A pre-Water baseline
is no longer takeable. All 10 questions were measured 2026-08-12 and are recorded in
[`01-water.md`](01-water.md) §6 — Q1 → `10.4 Yeast Starters and Diacetyl Rests` p.98 at rank 1;
Q3 → `Bittering`/`Flavoring`/`Finishing` p.41 at ranks 1–3; both gates passed. ⛔ **Use that
table as book 2's before-baseline. Do not re-derive it, and do not re-run it after Yeast is
ingested and call it a baseline** — that would be book 3's baseline, not book 2's.

⛔ **None of the three blocks the build.** Item 1 is hygiene, item 2 is a five-minute watch,
item 3 is already recorded. What item 2 protects against is severe enough to do it anyway.

---

## §2 — The build

**Two nodes exist that did not before. Nothing else changes anywhere.**

### 2.1 🆕 `ingest-yeast` — the new launcher, 2 nodes

Copied from `ingest-water` (2 nodes, `measured` from the tracked JSON). Its own name in the
workflow list, its own Run button, its own tracked JSON.

| # | Node | Settings |
|---|---|---|
| 1 | `When clicking 'Execute workflow'` — Manual Trigger | none |
| 2 | `Call 'wf1-ingest-book'` — Execute Sub-workflow (typeVersion 1.3) | **Source** `Database` · **Workflow** `wf1-ingest-book` (`NoNCV2mkQEppWP7O`) · **Mode** `Run once with all items` · ⛔ **Wait for Sub-Workflow Completion ON** |

⚠️ **Wait-for-completion ON is not optional.** Off, the launcher reports success the moment
Docling is handed the file, and a failed ten-minute ingest looks like a green check.

**Workflow Settings:** Execution Order `v1`, Binary Mode `separate` — matching the other three
launchers. **Do not activate it**; a manual trigger needs no activation.

### 2.2 ⭐ The mapper — the 13 fields, and where each value came from

The engine's Execute Workflow Trigger uses **Define using fields below**, so node 2 renders all
13. **This table is the entire book-specific content of this plan.**

| Field | Value | Source of the value |
|---|---|---|
| `file_path` | `/data/shared/rag-files/pending/yeast-the-practical-guide-to-beer-fermentation-0937381969_compress.pdf` | the **container** path; n8n cannot see the host path (mount verified §1.1) |
| `source_format` | `pdf` | drives `convert_from_formats` on node 8 |
| `slug` | `yeast-practical-guide` | new; matches the `<topic>-<qualifier>` shape of `water-comprehensive-guide` |
| `title` | `Yeast: The Practical Guide to Beer Fermentation` | the book |
| `doc_type` | `book` | legal value, `measured` §1.1 |
| `authors` | `Chris White, Jamil Zainasheff` | ⭐ `measured` from the PDF's own Author field, `White, Chris, Zainasheff, Jamil` |
| `language` | `en` | |
| `edition_note` | `Brewers Publications, 2010` | ⭐ `measured` — probe chunk 1's heading is `© Copyright 2010 by Brewers Association`, chunk 2 carries LCCN `2010029741`. Not guessed |
| `authority` | `reference` | legal value, `measured` §1.1. A reference work, not a guideline and not practitioner opinion |
| `profile` | `book` | the only implemented profile, and the correct one (§0.3) |
| ⭐ `front_matter_max_page` | **`21`** | ⛔ **§5.2, `measured` chunk by chunk.** ⚠️ **Not 18 and not 6.** Those are facts about *Water*'s and *How to Brew*'s PDFs |
| ⭐ `extra_drop_regex` | **see §2.3** | ⛔ **§5.3, `measured`.** ⚠️ **Water's was empty. Yeast's is doing the work `dropHeading` cannot** |
| ⭐ `text_repairs` | **see §2.4** | ⛔ **§5.6, every pair counted against the Docling output.** ⛔ **Not the hyphen probe's draft — the draft's single pair matches nothing and would abort the ingest** |

⛔ **Three of these thirteen are per-book constants that must never be copied from another
book:** `front_matter_max_page`, `extra_drop_regex`, `text_repairs`. All three are `measured`
in §5 for this file specifically.

### 2.3 ⭐ `extra_drop_regex` — the field that carries this book

**Paste this as one line into the launcher's `extra_drop_regex` field** (the engine compiles it
`new RegExp(EXTRA, 'i')` and tests it, unanchored, against the joined heading path):

```
/g56/g93 /g99/g97 /g94/g83/g100/g82 /g99/g88/g94/g93|/g59/g88/g98 /g99/g15/g94/g85/g15/g53/g88/g86/g100/g97 /g84/g98|/g65/g84/g85/g84/g97 /g84/g93/g82/g84/g98|/g56/g93/g83/g84/g103|^Palmer, John$|^Part [1-7]$|^Foreword$
```

**Seven alternatives, each `measured` against the probe, each with an exact count:**

| # | Alternative | Decodes to | Drops | Pages | Why the shared profile misses it |
|---|---|---|---|---|---|
| 1 | `/g56/g93 /g99/g97 /g94/g83/g100/g82 /g99/g88/g94/g93` | `Introduction` | **2** | 22–23 | it is *after* the page cut (§5.2) and unmatched by any heading rule |
| 2 | `/g59/g88/g98 /g99/g15/g94/g85/g15/g53/g88/g86/g100/g97 /g84/g98` | `List of Figures` | **4** | 306–311 | back matter; no page rule exists for the far end of a book |
| 3 | `/g65/g84/g85/g84/g97 /g84/g93/g82/g84/g98` | `References` | **2** | 313–314 | ⛔ `dropReferences` tests `^references$` on the *trimmed heading* — a glyph run is not that string |
| 4 | `/g56/g93/g83/g84/g103` | `Index` | **5** | 318–322 | ⛔ `dropHeading`'s `^Index` cannot see it |
| 5 | `^Palmer, John$` | *(an index entry promoted to a heading)* | **5** | 322–325 | the rest of the Index, headed by whatever entry Docling found first on the page. §5.4 |
| 6 | `^Part [1-7]$` | the bibliography, split by book part | **8** | 312–317 | ⭐ `measured`: `Part 1`…`Part 7` occur **only** on pp.312–317. Nothing in the body carries them |
| 7 | `^Foreword$` | one stray bibliography chunk | **1** | 312 | ⭐ `measured`: the *plain-text* `Foreword` heading occurs **exactly once**, at p.312. The real Foreword (pp.16–21) is the glyph form and is dropped by the page rule |
| | | **total** | ⭐ **27** | | |

⚠️ **Alternative 5 is the one to sanity-check on the canvas.** `Palmer, John` looks like body
content and is not; it is the running index entry on pp.322–325. `measured`: it appears on no
other page. ⛔ **If a future book has a chapter genuinely headed with a person's name, this
alternative does not transfer** — it is a fact about this Index.

⛔ **What deliberately is *not* in the regex: `^/g`.** A blanket "drop anything with a glyph
heading" is one character shorter and **would delete three real chapter openings** —
`How to Choose the Right Yeast` (p.62), `Fermentation` (p.86) and `Troubleshooting` (p.282),
all `measured` as body content. §5.3 lists them.

### 2.4 ⭐ `text_repairs` — four pairs, and not one of them is a hyphen

**Paste this JSON string into the launcher's `text_repairs` field** (the field is typed
`string`; the engine `JSON.parse`s it):

```json
[["/g95 -amylase","α-amylase"],["/g96 -amylase","β-amylase"],[" /g65 "," → "],["/g104 /g84/g80/g98 /g99","yeast"]]
```

| # | find | replace | Sites in `text` | in `raw_text` | `applied` | What it is |
|---|---|---|---|---|---|---|
| 1 | `/g95 -amylase` | `α-amylase` | 5 | 5 | **10** | ⭐ **alpha-amylase**, pp.53–55 and p.92. The enzyme, in a book about fermentation |
| 2 | `/g96 -amylase` | `β-amylase` | 3 | 3 | **6** | ⭐ **beta-amylase**, pp.53–54 |
| 3 | ` /g65 ` | ` → ` | 13 | 4 | **17** | the reaction arrow in eight metabolic equations, pp.45–160 |
| 4 | `/g104 /g84/g80/g98 /g99` | `yeast` | 27 | 27 | **54** | the running header, which leaks into the body of 27 chunks |
| | | | | | ⭐ **87** | `predicted` total `repairs_applied` |

⚠️ **`applied` is not 2 per site here, and that is a real difference from Water.** The engine
counts field-level replacements over `text` **and** `raw_text`; Docling's `text` carries the
heading prefix and `raw_text` does not, so repair 3 scores **13 + 4**, not 2 × *n*. ⛔ **Do not
carry forward book 1's "each site scores 2" shortcut** — it was true of Water's four pairs and
is false here, and §4 A2c's expected values are the per-pair numbers above, not a formula.

**Two things about repair 3 that are the whole reason it is written with spaces:**

- ⭐ **`/g65` on its own would corrupt kept text.** `measured`: in the p.62 chapter heading
  `How to Choose the Right Yeast`, the `R` of *Right* is also `/g65`, and that chunk is
  **kept**. The space-delimited form ` /g65 ` matches the eight equations and **nothing else** —
  counted, not assumed. This is standing rule 7's lesson from Water's `["35","3-5"]` (79 false
  sites) arriving in a new costume.
- ⚠️ **It repairs `text` but cannot repair `headings`.** Eight of the equation chunks carry the
  equation *as* their heading, so after this run `content` reads `→` where `heading_path` still
  reads `/g65`. That is plan 06 §4's warning inverted — and it is **accepted deliberately**,
  because the embedding is built from `content` and the repair therefore lands where it helps.
  ⛔ Do not "fix" it by editing `heading_path` in the cleaning node without rebuilding
  `content`; that is the failure plan 06 §4 actually warns about.

**Why these are repairs and not fabrication:** every pair is a *decode*. The page says
α-amylase; the font map is broken; the pair restores what the page says. Nothing is inferred.

⛔ **What the hyphen probe produced, and why it is not used** — standing rule 7, §5.6:

```
1 at-risk site(s)
draft text_repairs: [["2,3900", "2,3-900"]]
```

`measured`: **`2,3900` occurs 0 times in the Docling output**, in `text` and in `raw_text`.
Pasting it would throw `text_repairs matched nothing` and abort the ingest — correctly. The
site is the false positive the probe script's own header names: `Total 2,3-` is a table cell
that wraps next to a `900 ppb` cell in a different column.

### 2.5 ⚠️ What is left broken, stated so it is a decision and not an oversight

After §2.3 and §2.4, `measured` by simulation over the probe:

| Residue | Count | Why it is not repaired |
|---|---|---|
| kept chunks with a **glyph heading** | **11** — 8 equation headings, plus `How to Choose the Right Yeast` p.62, `Fermentation` p.86, `Troubleshooting` p.282 | ⛔ **`text_repairs` cannot reach `headings`.** Fixing it means either a decoder in shared code (§0.3's runner-up, argued down) or inventing headings, which is fabrication in the one layer that must stay faithful |
| kept chunks with **glyph noise in the body** | **17**, carrying **123** glyph tokens | table dot-markers (`/g138`, `/g135`), a flow arrow (`/g63`), part-number ornaments. Each is a *distinct* literal, so clearing them means a dozen more pairs for cosmetic gain |
| the three garbled **chapter openings** | 3 chunks | ⭐ **this is Water's `-J. Palmer` defect on a second document.** Those chunks retrieve on body text alone with a heading prefix that says nothing. §4's Tier B is where it shows up, and §4 predicts it will |

**The honest summary: Yeast lands with better hygiene than Water on every gate and worse
headings than any source so far.** Both facts belong in the record.

⭐ **`measured` 2026-08-19 — the residue is real but this table over-counts it, and the
correction is in [§4.1 A6](#41-tier-a--pipeline-sql-deterministic).** The **11** glyph headings
are exact. The body figure is **13** chunks / **68** glyph tokens on `raw_content` (15 / **123**
on `content`, so the 123 above is exact and the 17 is not), and the distinct-chunk total is
**23**, not 25. ⭐ **Two chunks carry 50 of the 68 tokens** — the residue is two damaged tables
plus eleven single stray ornaments, which weakens §0.3's decoder case rather than strengthening
it.

### 2.6 Overlap scoping (README §3 Layer 1)

**Yeast overlaps *How to Brew* on yeast handling and on off-flavours, and ⛔ nothing is
dropped.**

| | `measured` 2026-08-12 |
|---|---|
| README §3.1's named overlaps that involve Yeast | *off-flavours* (fault list × How to Brew × **Yeast** × Draught manual) — ⚠️ medium · *malt/yeast basics* (How to Brew × **Yeast**) — ⚠️ medium |
| The live competitor | *How to Brew* chapter 6 and 10 — `10.4 Yeast Starters and Diacetyl Rests` p.98 is the **current rank-1 chunk for standing question Q1** |
| Yeast's own coverage of the same ground | `Diacetyl` 3 chunks pp.58–290 · `Diacetyl Rest` **3 chunks pp.132–134** · `Pitching Rates` p.142 · `Working With Dry Yeast` 3 chunks pp.167–169 · `Acetaldehyde` p.289 · `How Much Oxygen Is Needed?` 6 chunks pp.98–104 · `Flocculation` 8 chunks |

⛔ **Expected overlap chunks dropped: 0.**

**Why — the rule, not a preference.** README §3.2 category **(a), topical overlap: keep
unconditionally.** This is the same shape as Water against Palmer's chapter 15, with one
difference worth naming: *How to Brew* devotes roughly one section to diacetyl rests and
*Yeast* devotes a chapter to the biochemistry underneath them. **The 20-page answer and the
325-page answer are different answers, and which is correct depends on the question.** An
ingest-time deletion is irreversible and untargeted; a query-time filter is reversible and
per-question. At a `predicted` 1,524 chunks neither storage nor precision forces the issue.

**Category (b), representational duplication, does not occur.** Yeast introduces no structured
table and no generated card; it is prose chunks only. There is nothing to drift against.

⛔ **Nothing in this plan may touch the 447 *How to Brew* chunks or the 382 Water chunks.**
§4 A1 checks both.

### 2.7 What this source does to WF4

**WF4 does not exist** (`measured` §1.1 — four workflows, none an agent). So: **nothing
changes, and that is the point.**

⭐ **Book 1 already paid this cost once, for all nine books.** [`01-water.md`](01-water.md) §9.1
specifies the de-enumerated system-prompt sentence —

> *"You answer from that brewer's library — a collection of brewing books, style guidelines and
> practitioner articles — not from your own memory."*

— and README §7.1's whole argument is that written that way, **every source from book 2 to
book 9 costs zero prompt edits.** Yeast is the first book to test that claim, and it passes:
**no prompt edit, no tool-description edit, no `numCtx` change, no context-budget change.**
Six chunks is six chunks whether the corpus is 1,061 or 1,524, and Yeast's `predicted` median
of **313 tokens** is close enough to Water's 342 and Palmer's that six-chunks-in-context is
unchanged.

⛔ **`scripts/stress/tier1_routing.py` is not run for this source** — it measures tool routing
against a system prompt, and there is neither. It runs when WF4 is built.

---

## §3 — ⭐ Reset: undo everything this workflow added

**Run this to start over.** It works on a **partial** run as well as a complete one — a
workflow that died in the embedding loop has already written a `kb.documents` row, a
`kb.document_versions` row and some of its chunks, and this removes all of it.

```sql
DELETE FROM kb.document_versions
WHERE file_sha256 = '2f30d7e5d8a965df00dbd225f57c4d759dd8ab90f99974b0ffee9b39f54266a4';
```

As one command:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "delete from kb.document_versions where file_sha256='2f30d7e5d8a965df00dbd225f57c4d759dd8ab90f99974b0ffee9b39f54266a4';"
```

| | |
|---|---|
| **Keyed on** | the Yeast PDF's SHA-256, ⭐ **re-verified with `sha256sum` 2026-08-12** (§1.1) — so it cannot touch another document, whatever else is in the corpus |
| **Cascades** | `kb.chunks` from the version · `kb.chunk_embeddings` from the chunks · `kb.ingest_log` from the version |
| **Left behind** | ✅ the `kb.documents` row, deliberately. The next run reuses it through `ON CONFLICT (slug) DO UPDATE`; deleting it gains nothing and risks the FK |
| ⛔ **Cannot undo** | ⭐ **nothing — and that is new.** Book 2 makes no shared-code edit, no node rename and no schema change, so there is no out-of-band state for the reset to miss. The only artefacts outside the database are `ingest-yeast.json` and this file, both in git |

**Verify — `predicted` `1061 · 0 · 3` after a reset, `1524 · 0 · 4` after a good run:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from kb.chunks; select count(*) from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null; select count(*) from kb.document_versions where is_current;"
```

Then re-run `ingest-yeast`. ⚠️ **The dedup branch is keyed on the same hash**, so the reset is
what makes a re-run possible at all — without it the second run stops at `Already ingested`,
which is also §4 A3's test.

⛔ **This plan never runs the reset.** It is written so it exists before it is needed.

---

## §4 — Testing

Three tiers. **Tiers A and B are required; Tier C is not runnable and §4.3 says why rather than
omitting it.** Every command is copy-pasteable with its expected output stated.

### 4.0 ⭐ The gate table — predicted before the run, measured after

> ⭐ **The result in one line: every predicted number was hit exactly — 21 of 21.**
> `measured` **2026-08-19** against the live stack; the run itself was **2026-08-12 13:34 UTC**.
> ⭐ **The 21 are the 18 predicted rows of the table below plus the 3-reason drop ledger.** The
> table's last four rows are not predictions about *Yeast* — they are unchanged-state checks on
> the rest of the corpus, and all four held.
> **Two predictions in this plan were wrong and neither is in this table** — §4.1 A5's chunk
> count for repair 3, and §4.1 A6's body-glyph residue. Both are recorded where they failed.

| Check | **Predicted** | ⭐ **Measured 2026-08-19** | Derived from | Gate |
|---|---|---|---|---|
| raw chunks from Docling | **526** | ✅ **526** — exact | `measured` §5.1 | ±2 — a different count means a different Docling |
| **kept chunks** | **463** | ✅ **463** — exact | `predicted` from `measured` | **±10% → 417–509** |
| dropped, total | **63** | ✅ **63** — exact | `predicted` from `measured` | ledger below |
| median tokens | **313** | ✅ **313** — exact | `predicted` | ✅ **200–450** |
| p25 / p75 tokens | **173 / 424** | ✅ **173 / 424** — exact | `predicted` | ⚠️ p25 is **below 200** — §4.4's documented miss |
| max / min tokens | **512 / 30** | ✅ **512 / 30** — exact | `predicted` | ≪ bge-m3's 8,192 window; nothing truncated |
| **under-30 after cleaning** | **0** | ✅ **0** | `predicted` | ⛔ **must be 0** |
| ⭐ **over-512 after cleaning** | **0** | ✅ **0** | `predicted` | ⭐ **better than Water's 1** — all three over-512 chunks are table-of-contents pages and die on the page rule |
| **missing `page_from`** | **0** | ✅ **0** | `predicted` from `measured` (0 in the raw probe) | ⛔ **must be 0** |
| **missing `heading_path`** | **0** | ✅ **0** | `predicted` — the probe's **one** headingless chunk is chunk 0, pp.2–3, dropped by the page rule | ⛔ **must be 0** |
| `page_count` (`max(page_to)` over **kept**) | ⭐ **305** | ✅ **305** — exact, and `max(page_to)` over kept chunks reads **305** independently | `predicted` | ⚠️ **not 325.** §4.4 |
| **embedding coverage** | **463/463** | ✅ **463/463**, dims **1024** | `predicted` | ⛔ **100%**, all 1024 dims |
| `kb.ingest_log` rows | **2** | ✅ **2** — `clean\|warn` and `promote\|info` | `predicted` | ⛔ **must be 2** |
| ⭐ `detail->'repairs'` entries | **4**, applied **10 / 6 / 17 / 54** | ⭐ ✅ **4**, applied **54 / 17 / 10 / 6** — every pair exact | `predicted` §2.4 | ⛔ **must be present** — the first repair ledger this project has ever recorded |
| `repairs_applied` total | **87** | ✅ **87** — exact | `predicted` | ⛔ non-zero |
| `is_current` versions, whole corpus | **4** | ✅ **4** | `predicted` | exactly 4 |
| `kb.chunks` total | **1,524** | ✅ **1,524** — exact | `predicted` | |
| ⚠️ **corpus share, Yeast** | **30.4%** | ⚠️ **30.4%** (463/1,524) | `predicted` | ⚠️ **over 25% — recorded and argued (§4.5), not tuned** |
| *How to Brew* untouched | **447 \| 447 \| 0 \| 0** | ✅ **447 \| 447 \| 0 \| 0** | `measured` | ⛔ **must be unchanged** |
| Water untouched | **382 \| 382 \| 0 \| 0** | ✅ **382 \| 382 \| 0 \| 0** | `measured` | ⛔ **must be unchanged** |
| style cards untouched | **232** | ✅ **232** | `measured` | ⛔ unchanged |
| `file_sha256` | `2f30d7e5…4266a4` | ✅ `2f30d7e5d8…` on the one `is_current` version | `measured` §1.1 | ⛔ must match, or the file is not the one probed |

⭐ **What this is evidence for, stated plainly rather than left implicit.** §5's probe was run
through the **live** Docling service with the engine's own ten form fields, and §4's numbers
were computed from it by simulation. Twenty-one predicted numbers later, **not one needed a tolerance**.
That is standing rule 1 — *measure, then plan* — producing its strongest result so far: book 1
landed **18 of 19** exactly, book 2 landed **21 of 21**. ⚠️ **The two counts are not measured the
same way** — book 1 counted its own gate table — so read the shape, not the ratio: neither book
needed a tolerance on any number that came out of a probe. ⚠️ **It does not generalise to predictions
that were not derived from the probe**: the two that missed (§4.1 A5, A6) were both written by
counting *sites* or *fields* rather than by simulating the query that would check them.

**The drop ledger — `predicted` before the run, `measured` after:**

| Reason | Predicted | ⭐ Measured | Pages predicted | Pages measured | From |
|---|---|---|---|---|---|
| `source-specific heading` | ⭐ **27** | ✅ **27** | 22–23, 306–325 | **22–325** | §2.3 — seven alternatives, itemised |
| `front matter (p1-p21)` | **21** | ✅ **21** | 2–21 | **2–20** | §5.2 |
| `under 30 tokens, no table` | **15** | ✅ **15** | 65–301 | **65–301** | §5.5 |
| `front-matter heading` | ⭐ **0** | ✅ **absent** | — | — | §0.1 — `dropHeading` matches **nothing** in this book |
| `chapter References list` | ⭐ **0** | ✅ **absent** | — | — | §0.1 — same cause |
| `empty raw_text` · `page-number-only` | **0 · 0** | ✅ **absent** | — | — | §5.1 |
| **total** | **63** | ✅ **63** | | | |

⭐ **Three reasons, exactly the three §2 authorised, at exactly the predicted counts.** The
`front matter` band reads **pp.2–20** rather than 2–21 for a boring reason worth stating so it
is not read as a miss: no *kept-or-dropped* chunk happens to **begin** on p.21, so
`min/max(page_from)` cannot report it. The rule is still `p1-p21` and the count is still 21.

⚠️ **A ledger that does not read 27/21/15 means something upstream changed.** Retained because
it is the check to run at book 3, not because it fired here. The two most likely mistakes, both
visible in one glance: a `front matter` count of **2** means `front_matter_max_page` was left at
Water's **18**; a `source-specific heading` count of **0** means `extra_drop_regex` was left
empty — and **the Index would then be in the corpus**, which `page_count` catches independently
(it would read **325**, not 305).

**Runtime — `predicted` before the run, `measured` from n8n execution 247:**

| Stage | Predicted | ⭐ **Measured** | Basis |
|---|---|---|---|
| read + hash + dedup | < 5 s | ✅ **0.03 s** | |
| ⭐ **Docling conversion** | **~2–3 min** | ✅ **150 s** — 10 poll cycles | ⭐ **`measured`: 137 s** in §5's probe — same service, same ten fields |
| poll loop overhead | ≤ 15 s | ⚠️ **up to 15 s, and it dominates** — see below | `Wait 15s` granularity |
| clean + repairs | < 2 s | ✅ **0.03 s** | |
| insert 463 chunks | < 2 s | ✅ **0.15 s** | one `jsonb_to_recordset` statement |
| **embed** | **15 batches, ~5–9 min** | ⛔ **15 batches, 16 s** — **20× faster than predicted** | Water: 382 chunks / 12 batches in 4–7 min `measured` |
| promote + assert + log | < 2 s | ✅ **0.17 s** | |
| **total** | **~8–13 min** | ⛔ **2 min 47 s** | `predicted` |

⛔ **The embed estimate was wrong by an order of magnitude, and it was inherited, not derived.**
`measured`: `Ollama embed` ran 15 times for **15.3 s of total node time**, and the whole
sub-workflow took **166.8 s**. ⚠️ **Book 1's "4–7 min" figure cannot have been right either** —
`measured`: Water's engine execution (243) ran **183 s end to end**, which is less than the
lower bound of its own embed estimate. The number was carried between plans without anyone
checking it against an execution record.

⭐ **The real shape of the run: 150 of 167 seconds are the `Wait 15s` poll loop.** Everything
that touches the database or the GPU costs **under 17 seconds combined**. That reframes
"is it hung?" completely:

| Old signal | ⭐ Replacement, for book 3 |
|---|---|
| ⛔ *"past 20 minutes something is wrong"* | ⛔ **past ~6 minutes something is wrong** — three times the measured run, and still inside a `Wait 15s` granularity of the Docling conversion for a larger book |
| *"most likely Ollama cold-loading per batch"* | ⚠️ **still the right first suspect** (`keep_alive: -1` missing from `Ollama embed`), but now it would show as embed time going from **16 s to minutes**, which is unmissable rather than plausible |

⛔ **Do not "fix" the poll loop by shortening `Wait 15s`.** It costs at most 15 s of idle at the
end of a conversion and it is the reason the loop is cheap on Docling; the runtime that matters
is Docling's, and that is a property of the file.

### 4.1 Tier A — pipeline (SQL, deterministic)

⭐ **All seven blocks were run 2026-08-19 against the live stack.** Results are recorded
inline under each command, labelled `measured`. **A1, A2, A2b, A2c, A4 and A7 pass exactly;
A5 and A6 each return one column that misses its predicted value, and both misses are the
prediction's fault rather than the pipeline's. A3 was *not observed* — see below.**

**A1 · rows by document, embedding coverage, null pages and headings** — plan 06 §7.6's query,
unmodified:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, count(*) chunks, count(e.chunk_id) embedded, count(*) filter (where c.page_from is null) no_page, count(*) filter (where c.heading_path is null or cardinality(c.heading_path)=0) no_heading, min(c.token_count) min_tok, percentile_disc(0.5) within group (order by c.token_count) median_tok, max(c.token_count) max_tok from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' group by d.slug order by 1;"
```

⭐ **`measured` 2026-08-19 — four rows, and every predicted cell hit:**

| slug | chunks | embedded | no_page | no_heading | min | median | max | |
|---|---|---|---|---|---|---|---|---|
| `bjcp-2021-beer-styles` | **232** | **232** | 232 — by design, §00b | **0** | — | — | — | ✅ unchanged |
| `how-to-brew-palmer` | **447** | **447** | **0** | **0** | 30 | 291 | 524 | ⛔ ✅ **untouched** |
| `water-comprehensive-guide` | **382** | **382** | **0** | **0** | 31 | 342 | 513 | ⛔ ✅ **untouched** |
| ⭐ `yeast-practical-guide` | **463** | **463** | ⛔ **0** | ⛔ **0** | **30** | **313** | **512** | ✅ **exact** |

⛔ **The two existing book rows are as important as the Yeast row**, and they are unchanged:
447 and 382, both fully embedded, both with zero null pages and zero null headings. **The
ingest touched nothing that was already there.** ⭐ *How to Brew*'s min/median/max are now on
the record too — **30 / 291 / 524** — which they were not before; book 1's plan wrote
*"unchanged"* without saying unchanged from what.

**A2 · the log has 2 rows, with a drop ledger *and* a repair ledger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select stage, level, message, jsonb_array_length(detail->'drops') drops, jsonb_array_length(detail->'repairs') repairs, detail->'stats'->>'repairs_applied' applied from kb.ingest_log where version_id=(select id from kb.document_versions where file_sha256='2f30d7e5d8a965df00dbd225f57c4d759dd8ab90f99974b0ffee9b39f54266a4') order by id;"
```

**Predicted:** a `clean | warn` row with `drops` **63**, ⭐ `repairs` **4** and `applied` **87**;
and a `promote | info` row.

⭐ **`measured` — exactly that:**

| stage | level | message | drops | repairs | applied |
|---|---|---|---|---|---|
| `clean` | `warn` | *cleaning kept 463 of 526 chunks, 63 dropped* | **63** | ⭐ **4** | **87** |
| `promote` | `info` | *version 5 promoted: 463 chunks, 0 missing embeddings* | — | — | — |

⚠️ **One cosmetic defect in the engine, found here and true of every book so far.** The promote
message reads *"version 5"*, but `kb.document_versions.version` for Yeast is **1** — `measured`.
The message interpolates the **row id**, not the version number, and it has done so since book
0a (*"version 2 promoted"* for *How to Brew*, whose version is also 1). ⛔ **Not fixed here**:
it is a shared-code edit in `Log ingest summary`, book 2's whole verdict is *no shared-code
edit*, and the string is not read by anything. **Recorded so book 3 or 4.5 can fix it in a run
that is already touching the engine.**

ⓘ **`kb.document_versions` has ids 1, 2, 3, 5 — `measured`.** Id **4** is absent and no row,
log entry or chunk references it. An identity column burns its value on a rolled-back insert,
so a single failed `Ensure doc + version` attempt explains it completely and there is nothing
orphaned to clean up. Recorded rather than investigated further.

**A2b · the drop ledger by reason — §4.0's table, read back from the database:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d->>'reason' reason, count(*) n, min((d->>'page_from')::int) p_from, max((d->>'page_from')::int) p_to from kb.ingest_log, jsonb_array_elements(detail->'drops') d where stage='clean' and version_id=(select id from kb.document_versions where file_sha256='2f30d7e5d8a965df00dbd225f57c4d759dd8ab90f99974b0ffee9b39f54266a4') group by 1 order by 2 desc;"
```

**Predicted exactly:** `source-specific heading` **27** · `front matter (p1-p21)` **21**
(pp.2–21) · `under 30 tokens, no table` **15** (pp.65–301).
**Anything else is a rule firing that this plan did not authorise.**

⭐ **`measured` — three reasons, three exact counts, nothing unauthorised:**

| reason | n | p_from | p_to | |
|---|---|---|---|---|
| `source-specific heading` | **27** | 22 | 325 | ✅ exact |
| `front matter (p1-p21)` | **21** | 2 | 20 | ✅ exact — §4.0 explains the 20 |
| `under 30 tokens, no table` | **15** | 65 | 301 | ✅ exact, and the predicted page band exactly |

**A2c · ⭐ read the repair ledger — the first one this project has ever recorded:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select r->>'find' find, r->>'replace' replace, (r->>'applied')::int applied from kb.ingest_log, jsonb_array_elements(detail->'repairs') r where stage='clean' and version_id=(select id from kb.document_versions where file_sha256='2f30d7e5d8a965df00dbd225f57c4d759dd8ab90f99974b0ffee9b39f54266a4') order by 3 desc;"
```

**Predicted: 4 rows — `54 / 17 / 10 / 6`, summing to 87.**

⭐ **`measured` — four rows, and the asymmetry is exactly the predicted one:**

| find | replace | applied | predicted |
|---|---|---|---|
| `/g104 /g84/g80/g98 /g99` | `yeast` | **54** | 54 ✅ |
| `" /g65 "` | `" → "` | **17** | 17 ✅ |
| `/g95 -amylase` | `α-amylase` | **10** | 10 ✅ |
| `/g96 -amylase` | `β-amylase` | **6** | 6 ✅ |
| | **total** | **87** | 87 ✅ |

⚠️ **Read this one carefully rather than ticking it.** `$5` had never produced a row, so a
*passing* result proves less than it seems: it proves the key is written and the array is
non-empty. What makes it a real capability test is the **per-pair asymmetry** — 17 for repair 3
against 54 for repair 4 is a number the total could not have told you, and it is exactly the
case [`01-water.md`](01-water.md) §6 A2 said the total *would* have hidden.

⭐ **So the capability is proven, and the bound on that proof is worth stating.** Four distinct
`find` strings produced four distinct counts, none of them equal, none of them a multiple of a
common factor, and all four match a per-pair prediction made from the probe. **`$5` is being
passed and stored, not passed and discarded.** ⚠️ **It is still one observation on one book.**
The failure mode it replaces — pg-promise silently dropping the fifth parameter — was invisible
for two books precisely because a total can be reconstructed and an array cannot. **Book 3
should re-read this ledger rather than assume it**, and a book with a *single* repair pair
would not distinguish "stored" from "reconstructed" at all.

**A3 · idempotency — run `ingest-yeast` a second time; it must stop at `Is new file?`:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

Run before and after the second execution. ⛔ **Identical both times, count `1524`, and the run
must end at `Already ingested` in seconds.**

⛔ **`measured` result: NOT OBSERVED — and it cannot be recovered.** A dedup short-circuit
writes nothing, so the database cannot testify to it after the fact. `measured` from n8n's
execution table: **`ingest-yeast` has exactly one execution** — id 246, 2026-08-12 13:31:39 →
13:34:27 — and there is no second run to have short-circuited. ⛔ **This is recorded as *not
observed*, not as passed.** §1.2 item 2 asked for it and it did not happen.

⭐ **What the execution record *does* establish, which is not nothing:**

| `measured` | What it shows |
|---|---|
| ⭐ **`ingest-how-to-brew` executions 240/241, 2026-08-12 09:00:39 → 09:00:39.375** | **63 ms end to end**, against a version committed at 08:47:58. ✅ **This is a genuine, committed-version short-circuit**, on the same engine and the same launcher shape. The dedup branch demonstrably works |
| ⚠️ **`ingest-water` executions 244/245, 11:15:26 → 11:17:57** | ⛔ **the A3 watch book 1 intended, and it did not test A3.** It was started at 11:15:26 — **86 seconds before the first Water run committed its version row at 11:16:36**. Dedup therefore found nothing, and the run went the full path: Docling conversion, clean, `Ensure doc + version`, `Insert chunks`. `measured`: it added **0 chunks**, wrote **no** `promote` or log row, and terminated at `Select chunks needing embeddings` with **status `success`** |

⛔ **That second row is a finding, and it belongs to the engine rather than to any book.** A
duplicate run launched before the first commits **does not short-circuit, does not error, and
reports success** — it silently does ~3 minutes of Docling work and exits. It cost nothing
here because the downstream inserts are conflict-safe, but *"success"* on a run that promoted
nothing is a result no one would question at a glance.

⭐ **What book 3 should do instead of repeating this, one design:** run A3 **as the last step of
the ingest session**, after the log rows exist, and read the fingerprint before and after. The
runner-up — build a guard so a second concurrent run fails loudly — is **argued down**: it is
shared-engine code to defend against a mistake that only happens when someone launches the
same book twice by hand, and §0's mapper-only verdict is worth more than the guard.

⚠️ **A3 was not run in this session either, deliberately.** Running it means executing
`ingest-yeast`, and if the dedup branch were broken that is a full Docling conversion and an
embedding pass — the one thing standing rule 3 forbids while the assistant is in use. **It is a
five-minute watch and it is yours to trigger.**

**A4 · corpus totals:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 'chunks', count(*)::text from kb.chunks union all select 'gaps', count(*)::text from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null union all select 'current', count(*)::text from kb.document_versions where is_current union all select 'dims', (select string_agg(distinct vector_dims(embedding)::text,',') from kb.chunk_embeddings);"
```

**Predicted:** `chunks 1524` · `gaps 0` · `current 4` · `dims 1024`. ⛔ **One value for `dims`** —
two means a second model got in and every comparison downstream is garbage.

⭐ **`measured`: `chunks 1524` · `gaps 0` · `current 4` · `dims 1024` — all four exact, and
`dims` is a single value.** ✅

**A5 · the four repairs are in the stored text, not just in the ledger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) filter (where position('α-amylase' in raw_content)>0) r1, count(*) filter (where position('β-amylase' in raw_content)>0) r2, count(*) filter (where position(' → ' in raw_content)>0) r3, count(*) filter (where position('/g95' in raw_content)>0 or position('/g96' in raw_content)>0) unrepaired_amylase, count(*) filter (where position('/g104 /g84/g80/g98 /g99' in raw_content)>0) unrepaired_header from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id where d.slug='yeast-practical-guide';"
```

⚠️ **`position()` rather than `LIKE`** — the find strings contain `%`-free text here, but the
habit is the one [`01-water.md`](01-water.md) §6 A6 established and it costs nothing.

**Predicted: `4 | 2 | 4 | 0 | 0`.** ⛔ **The last two columns are the ones that matter** — a
non-zero `unrepaired_*` means a repair silently did not fire on a chunk that survived cleaning.

⚠️ **`measured`: `4 | 2 | 1 | 0 | 0` — the gate passes, and the third column misses.**

| column | predicted | measured | |
|---|---|---|---|
| `r1` — chunks containing `α-amylase` | 4 | **4** | ✅ |
| `r2` — chunks containing `β-amylase` | 2 | **2** | ✅ |
| ⚠️ `r3` — chunks containing ` → ` | **4** | ⛔ **1** | **the miss** |
| ⛔ `unrepaired_amylase` | 0 | ✅ **0** | the gate |
| ⛔ `unrepaired_header` | 0 | ✅ **0** | the gate |

⭐ **The miss is arithmetic in the prediction, not a repair that failed to fire — and it is
verifiable in one query.** §2.4 counted repair 3's **sites**: 13 in `text`, 4 in `raw_text`,
17 applied. A5 then wrote **4** into a column that counts **chunks**. `measured` over the kept
Yeast chunks:

| | `measured` |
|---|---|
| occurrences of ` → ` in `raw_content` | ⭐ **4** — exactly the predicted site count |
| occurrences of ` → ` in `content` | ⭐ **13** — exactly the predicted site count |
| **total, both fields** | ⭐ **17** — reconciles with A2c's `applied` **exactly** |
| chunks containing ` → ` in `raw_content` | **1** — chunk 208, p.150, `Commercial Brewery Propagation`, which holds **all four** `raw_text` sites |
| chunks containing ` → ` in `content` | **9** — the eight equation chunks plus chunk 208 |

⛔ **So all 17 replacements landed, in kept chunks, and none was lost.** The prediction was a
units error — sites read as chunks — and it survived review because r1 and r2 happened to have
site and chunk counts close enough (5 sites in 4 chunks, 3 in 2) that nothing looked wrong.
⭐ **The lesson for book 3 is narrow and worth carrying: a `text_repairs` prediction states
sites; a SQL check states rows. Convert deliberately, or predict the occurrence count instead
and use `sum()` rather than `count(*) filter`.**

**A6 · ⭐ the glyph residue is the size §2.5 says it is, and no larger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) filter (where c.raw_content ~ '/g[0-9]+') body_glyph, count(*) filter (where array_to_string(c.heading_path,' ') ~ '/g[0-9]+') head_glyph, count(*) filter (where array_to_string(c.heading_path,' ') ~* '(index|references|contents)') plain_backmatter from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id where d.slug='yeast-practical-guide';"
```

**Predicted: `17 | 11 | 0`.** ⭐ **The third column is the real test of §2.3** — a non-zero
`plain_backmatter` would mean some Index or References chunk survived under a *readable*
heading that `extra_drop_regex` never looked for.

⚠️ **`measured`: `13 | 11 | 0` — two columns exact, one over-predicted.**

| column | predicted | measured | |
|---|---|---|---|
| `body_glyph` | 17 | ⚠️ **13** | **the miss — the residue is *smaller* than predicted** |
| `head_glyph` | 11 | ✅ **11** | exact — §5.3's 3 chapter openings + 8 equation headings |
| ⛔ `plain_backmatter` | 0 | ✅ **0** | ⭐ **§2.3 is confirmed: no readable back-matter heading survived** |

⭐ **The over-prediction is a field boundary, and the token count settles it.** `measured` over
the kept Yeast chunks:

| | chunks | glyph tokens |
|---|---|---|
| `raw_content` — the body alone | **13** | **68** |
| `content` — heading prefix **+** body | **15** | ⭐ **123** — §2.5's predicted token total, **exact** |
| any glyph anywhere (`content` ∪ `heading_path`) | **23** | — |

⛔ **§2.5's "17 chunks / 123 glyph tokens" is therefore half right in a specific way**: the
**123** was counted on `content` and is exact; the **17** matches neither field (13 body-only,
15 content). ⚠️ **And the "25 distinct chunks, 3 overlapping" figure that has been repeated
since is wrong** — `measured`, it is **23 distinct, 3 overlapping** (15 content-glyph + 11
head-glyph − 3 in both).

**What the 13 actually are, `measured` — recorded so book 3 can compare:**

| Kind | Chunks | Example |
|---|---|---|
| single part-number ornaments (`/g32`–`/g40`, decoding to digits) | **8** | chunk 24 p.24 `About Chris White` — one token |
| table dot-markers `/g135` `/g138` | **1** | chunk 174 p.126, 23 tokens |
| a table header row that did not decode | **1** | chunk 232 p.164 `Starter Volume in Liters`, 27 tokens |
| a flow arrow `/g63` | **1** | chunk 207 p.149 |
| stray `/g23` / `/g38` | **2** | chunks 461, 495 |

⭐ **Two of those thirteen carry 50 of the 68 tokens.** The residue is not thirteen damaged
chunks; it is **two damaged tables and eleven chunks with a single stray ornament in them**.
That is materially better than §2.5 described, and it weakens §0.3's decoder argument further
rather than strengthening it: a shared-code decoder would be justified by two tables.

**A7 · the untab block stayed a no-op** — Yeast has **0 tabs** (`measured` §5.1), so this
should be trivially clean across all four documents:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, count(*) filter (where c.content like '%'||chr(9)||'%') content_tab, count(*) filter (where c.raw_content like '%'||chr(9)||'%') raw_tab from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id group by 1 order by 1;"
```

**Predicted: 0 in every column, for all four documents.**

⭐ **`measured`: 0 in every column, for all four documents.** ✅ Second confirmation that book
1's untab edit is safe on a file that does not need it (§0.2, node 13).

### 4.2 Tier B — retrieval (`scripts/ask.sh`, deterministic)

**The before-baseline is [`01-water.md`](01-water.md) §6's post-Water table**, `measured`
2026-08-12. ⛔ **Do not re-derive it** (§1.2 item 3).

⭐ **All 10 questions were run 2026-08-19** against the live **1,524**-chunk corpus with
`scripts/ask.sh`, unfiltered, 6/40/50 defaults untouched — the same conditions as the
post-Water baseline. Results are `measured` and recorded under each prediction below.

> ### ⭐ The verdict: **keep.** All five prior rank-1 chunks are still in the **top 3**, all
> four positive controls reach **rank 1**, Layer 2 fires on nothing for the second run running,
> and **one of §4.2a's five predictions is falsified** — Q4, the one the plan called *"the
> single largest predicted swing"*.

**The keep/roll-back rule, unchanged and restated:**

| Outcome | Action |
|---|---|
| prior rank-1 chunk still top 3 on all five | **keep**, log the shift |
| falls out of top 6 on **one** | keep, log as a defect |
| falls out of top 6 on **two or more** | ⛔ **reset** (§3) |

⭐ **`measured`: prior rank-1 still in the top 3 on all five → keep.** Zero logged defects,
no reset.

#### ⭐ 4.2a Predicted movement — written **before** the run, per question

⚠️ **Yeast is the first source expected to legitimately *win* the standing questions, and the
keep/roll-back rule was not written with that in mind.** Q1 is diacetyl rests and Q4 is
pitching rate and rehydrating dry yeast; *Yeast* is **the** book on both. Displacing Palmer's
`10.4 Yeast Starters and Diacetyl Rests` from rank 1 is **the pipeline working, not
regressing** — the rule cares whether the prior chunk falls out of the **top 3**, not whether
it stays at **rank 1**. Predicting it here is what makes a shift legible as expected rather
than argued about afterwards.

| # | Question | Prior rank-1 (`measured`, post-Water) | ⭐ **Prediction** | Yeast's candidate chunks |
|---|---|---|---|---|
| **Q1** | diacetyl rest temperature and timing for lagers | `10.4 Yeast Starters and Diacetyl Rests` p.98, how-to-brew · 4 of 6 on target | ⭐ **Yeast takes rank 1. Palmer stays in the top 3.** On-target count rises to 6 | `Diacetyl Rest` **3 chunks pp.132–134**, `Diacetyl` pp.58, 290 |
| **Q2** | how mash pH affects conversion | `4.2 Water Chemistry Adjustment…` p.39, how-to-brew · 3 how-to-brew / 3 water | **no change.** Yeast is not a mash-chemistry book; `predicted` 0–1 of 6 | — |
| **Q3** | when to add hops for bittering vs aroma | `Bittering`/`Flavoring`/`Finishing` p.41, ranks 1–3 | **no change, 0 of 6 from Yeast.** ⭐ This is the gate; it must hold | — |
| **Q4** | pitching rate and rehydrating dry yeast | `Symptom: I added the yeast 2 days ago…` p.205, how-to-brew · 5 of 6 | ⭐ **Yeast takes rank 1 and most of the top 6.** The single largest predicted swing in the plan | `Working With Dry Yeast` 3 chunks pp.167–169, `Pitching Rates` p.142, `Shelf Life of Dry Yeast` p.181 |
| **Q5** | green apple / acetaldehyde | `Acetaldehyde` p.212, how-to-brew · 4 of 6 | ⚠️ **contested.** Yeast has exactly **one** `Acetaldehyde` chunk (p.289) against Palmer's dedicated troubleshooting entry. `predicted` Yeast enters the top 6 but **does not** take rank 1 | `Acetaldehyde` p.289 |

⛔ **If Q3 moves at all, stop and look at the drop ledger before blaming retrieval.** Yeast has
no hop content; a Yeast chunk in Q3's top 6 would mean something was chunked or embedded wrong,
not that ranking drifted.

##### ⭐ Scored — `measured` 2026-08-19, prediction by prediction

| # | Prior rank-1 | ⭐ **New rank-1 `measured`** | Where the prior chunk landed | Yeast of 6 | Prediction |
|---|---|---|---|---|---|
| **Q1** | how-to-brew p.98 `10.4 Yeast Starters and Diacetyl Rests` | ⭐ **yeast p.133 `Diacetyl Rest`** | ✅ **rank 3** — still top 3 | **3** | ✅ **correct, in full** |
| **Q2** | how-to-brew p.39 `4.2 Water Chemistry Adjustment…` | **how-to-brew p.39** — unchanged | ✅ rank 1 | **0** | ✅ **correct** |
| **Q3** | how-to-brew p.41 `Bittering` | **how-to-brew p.41 `Bittering`** — unchanged | ✅ ranks 1–3 `Bittering`/`Flavoring`/`Finishing`, all p.41 | **0** | ✅ **correct — the gate holds** |
| **Q4** | how-to-brew p.205 `Symptom: I added the yeast 2 days ago…` | ⛔ **how-to-brew p.205 — unchanged** | ✅ rank 1 | **2** | ⛔ **FALSIFIED** |
| **Q5** | how-to-brew p.212 `Acetaldehyde` | **how-to-brew p.212** — unchanged | ✅ rank 1 | **1** | ✅ **correct in outcome, wrong in detail** |

**Q1 — the prediction landed on every clause, which is worth stating rather than assuming.**
`measured` top 6: yeast p.133 `Diacetyl Rest` · yeast p.135 `Lagering` · **how-to-brew p.98
`10.4 Yeast Starters and Diacetyl Rests`** · yeast p.132 `Diacetyl Rest` · how-to-brew p.99
`10.5 When to Lager` · how-to-brew p.98 again. Yeast took rank 1, Palmer held rank 3, and the
on-target count went from **4 of 6 to 6 of 6** — every result is now about diacetyl reduction
or the lagering window. ⭐ **This is the top-6 that book 2 was ingested to produce**: the
325-page answer at rank 1 and the 20-page answer at rank 3, side by side, in one context
window. §2.6's keep-both rule, working exactly as designed.

⛔ **Q4 — falsified, and the shape of the miss is the interesting part.** The plan called this
*"the single largest predicted swing"* and predicted Yeast would take rank 1 **and most of the
top 6**. `measured`: Palmer keeps rank 1 with the **same** chunk, and Yeast takes **2 of 6**,
at ranks 2 and 4 — both `Working With Dry Yeast`, pp.167–168.

| rank | `measured` | |
|---|---|---|
| 1 | how-to-brew p.205 `Symptom: I added the yeast 2 days ago and nothing is happening` | ⛔ unchanged from baseline |
| 2 | **yeast p.167 `Working With Dry Yeast`** | ⭐ the predicted chunk, one rank low |
| 3 | how-to-brew p.62 `Preparing Dry Yeast` | |
| 4 | **yeast p.168 `Working With Dry Yeast`** | |
| 5 | how-to-brew p.63 `Re-hydrating Dry Yeast` | |
| 6 | how-to-brew p.92 `Pitching the Yeast` | |

⭐ **Why the prediction was wrong, and it is a property of the *question*, not of the corpus.**
The standing question is *"pitching rate and rehydrating dry yeast"* — two topics in one
string. Palmer's rank-1 chunk is a troubleshooting entry that covers **both** in plain
practical language; *Yeast*'s coverage is **split** across `Pitching Rates` (p.142) and
`Working With Dry Yeast` (pp.167–169), so no single Yeast chunk matches the whole query. ⭐ The
control question that asks only one of the two — *"how do I rehydrate dry yeast before
pitching"* — **does** put Yeast at rank 1 (Q7 below). ⚠️ **Neither `Pitching Rates` p.142 nor
`Shelf Life of Dry Yeast` p.181 appeared at all**, though both were named as candidates.

⛔ **Do not read this as a retrieval defect.** Palmer's chunk is a genuinely good answer to a
two-part practical question, and the keep rule is satisfied at rank 1. **The lesson is about
prediction, not about ranking: a compound standing question is answered by whichever source
covers both halves in one chunk, and depth on each half separately does not beat it.** That is
a reusable rule and book 3 should apply it — *Malt* will be predicted to win Q2's
mash-chemistry half and should not be expected to take a compound question.

**Q5 — right outcome, wrong chunk.** `predicted`: Yeast enters the top 6 but does not take
rank 1, via its one `Acetaldehyde` chunk (p.289). `measured`: Yeast enters at **rank 4**, and
the chunk is **`Sour` p.290** — not `Acetaldehyde` p.289. Palmer holds ranks 1, 2, 3, 5 and 6
with a dedicated off-flavour section. ⚠️ **Recorded because it is the shape book 6 will
change**: the fault list is 21 rows of exactly this content and is not in the corpus yet.

**Q2 and Q3 — byte-identical to the post-Water baseline.** `measured`: Q2 returns the same six
chunks in the same order (pp.39, 140, 75, 134, 63, 74) and Q3 returns the same six
(pp.41, 41, 41, 76, 40, 77). ⛔ **463 new chunks displaced nothing on either.** Q3 was the
declared gate and it did not move by a single rank.

**Positive controls — 4, each stating the document and the rank it must reach.** Every target
heading below was `measured` present in §5's probe.

| Question | Must reach | Expected chunk |
|---|---|---|
| *"how many yeast cells should I pitch per millilitre per degree Plato"* | `yeast-practical-guide` in the **top 3** | `Pitching Rates` pp.142–143, and the `(pitching rate) x (milliliters of wort) x (degrees Plato…)` heading |
| *"how do I rehydrate dry yeast before pitching"* | `yeast-practical-guide` in the **top 3** | `Working With Dry Yeast`, 3 chunks pp.167–169 |
| *"how much dissolved oxygen does wort need before fermentation"* | `yeast-practical-guide` in the **top 3** | `How Much Oxygen Is Needed?`, **6 chunks pp.98–104** |
| *"what makes yeast flocculate and why does it matter"* | `yeast-practical-guide` in the **top 3** | `Flocculation`, 8 chunks pp.47–132 |

⭐ **The first is deliberately a question *How to Brew* can also answer.** A top-6 carrying both
books is the correct result and the best evidence §2.6's keep-both rule was right. **Note which
documents appear.**

##### ⭐ The 4 positive controls — `measured`: all four at **rank 1**, not merely top 3

| # | Question | Required | ⭐ **Measured** | Yeast of 6 | |
|---|---|---|---|---|---|
| **Q6** | yeast cells per ml per °Plato | yeast, top 3 | **rank 1** — `Estimating Yeast Density` p.145; the predicted `(pitching rate) x (milliliters of wort) x (degrees Plato…)` heading is at **rank 2**, p.144 | **6** | ✅ |
| **Q7** | rehydrate dry yeast | yeast, top 3 | **rank 1** — `Working With Dry Yeast` p.167 | **3** | ✅ |
| **Q8** | dissolved oxygen in wort | yeast, top 3 | **rank 1** — `How Much Oxygen Is Needed?` p.102 | **3** | ✅ |
| **Q9** | why yeast flocculates | yeast, top 3 | **rank 1** — `Flocculation` p.48 | **6** | ✅ |

**Yeast answers what it was ingested to answer**, and it does so from rank 1 on all four —
the same result Water produced at book 1. ⭐ **Two books in a row where every positive control
lands at rank 1 rather than merely inside the top 3** is now the pattern to expect at book 3,
and a control that only reaches rank 2 or 3 there should be looked at rather than ticked.

⚠️ **One sub-prediction inside Q6 is falsified, and it is the one the plan flagged as
deliberate.** *"The first is deliberately a question How to Brew can also answer… a top-6
carrying both books is the correct result."* `measured`: Q6 returns **6 of 6 from Yeast** and
*How to Brew* does not appear at all. ⭐ **The both-books result the plan wanted did appear —
on Q7**, which splits 3 yeast / 3 how-to-brew (`Working With Dry Yeast` against
`Re-hydrating Dry Yeast` and `Preparing Dry Yeast`), and on Q8, which splits 3 / 3. **So the
keep-both evidence exists; it just came from the controls the plan did not nominate.** Q6 is a
quantitative question with a formula in it, and only one book in the corpus states the
formula — which in hindsight is why it was never going to be shared.

#### 4.2b ⭐ Layer 2 — the retrieval-share check, at four documents

**The check, unchanged:** over the **10** questions — the 5 standing + the 4 positive controls +
one question Yeast does not own —

```bash
./scripts/ask.sh "what should an Irish Stout taste like"
```

⛔ **flag any question where ≥ 3 of 6 results come from one document that does not own it.**

⭐ **Record the result even if it fires nothing.** On Water it fired on **nothing**, and the
most striking measurement in that run was a null: Water was 36.0% of the corpus and took **0 of
6** on the style question. A recorded null is what makes the first real firing legible.

**The specific thing to watch here:** ⚠️ **Yeast flooding Q5 (acetaldehyde) or Q10 (style).**
Yeast has a fault chapter, so unlike Water it *can* plausibly reach an off-flavour question it
does not own — and the fault list (book 6) is not in the corpus yet to compete.

##### ⭐ `measured` 2026-08-19 — all 10 questions, and Layer 2 fires on **nothing**

| # | Question | how-to-brew | water | ⭐ yeast | styles | Owner | Fires? |
|---|---|---|---|---|---|---|---|
| Q1 | diacetyl rest | 3 | 0 | **3** | 0 | ⚠️ shared — both own it | ✅ no |
| Q2 | mash pH | 3 | **3** | **0** | 0 | ⚠️ shared — both own it | ✅ no |
| Q3 | hop timing | **6** | 0 | **0** | 0 | how-to-brew | ✅ no |
| Q4 | pitching rate | **4** | 0 | **2** | 0 | ⚠️ shared — both own it | ✅ no |
| Q5 | acetaldehyde | **5** | 0 | **1** | 0 | how-to-brew | ✅ no |
| Q6 | cells per ml per °P | 0 | 0 | ⭐ **6** | 0 | yeast | ✅ no |
| Q7 | rehydrate dry yeast | 3 | 0 | **3** | 0 | ⚠️ shared — both own it | ✅ no |
| **Q8** | **dissolved oxygen** | ⚠️ **3** | 0 | **3** | 0 | ⚠️ **shared — see below** | ⚠️ **the closest call yet** |
| Q9 | flocculation | 0 | 0 | ⭐ **6** | 0 | yeast | ✅ no |
| **Q10** | **what should an Irish Stout taste like** | 1 | 0 | ⭐ **0** | **5** | styles | ✅ **no** |

⛔ **Layer 2 does not fire. Layer 3 is not built.** README §3.3's rule is that the per-document
cap is the designated fix and is built **only** when Layer 2 fires — not when the corpus-share
proxy crosses. **Second consecutive recorded null**, now at four documents and 1,524 chunks.

⭐ **Q10 is again the measurement that matters, and it is again a null.** Yeast is **30.4% of
the corpus** and returns **0 of 6** on the style question — `measured`, and the top 6 is
**byte-identical to the post-Water baseline**: how-to-brew p.184 `Stout` at rank 1, then five
BJCP cards. ⛔ **Two documents have now crossed the 25% corpus-share line and neither has
touched a question it does not own.** §4.5's *"argue it, do not tune it"* is no longer a
one-book result.

⚠️ **The prediction that Yeast would flood Q5 or Q10 is falsified, in the safe direction.**
`measured`: Q5 takes **1 of 6** (rank 4) and Q10 takes **0 of 6**. Yeast's fault chapter did
not reach an off-flavour question it does not own, even with the fault list absent from the
corpus.

⚠️ **Q8 is the closest this check has come to firing in two runs, and it is decided by a
judgement rather than by the count.** *How to Brew* takes **3 of 6** on the dissolved-oxygen
question — ranks 3 (`9.1 Transferring the Wort`), 4 (`Symptom: I added the yeast 2 days ago…`)
and 6 (`6.9.2 Oxygen`). Read strictly — *Yeast* owns wort oxygenation, so Palmer has 3 of 6 on
a question he does not own — **the rule fires.**

⭐ **It is recorded as not fired, on the same ground Water's Q2 was: shared ownership.** Two of
Palmer's three are directly on topic (`6.9.2 Oxygen` and wort aeration during transfer), so
this is the 20-page answer and the 325-page answer competing, which is the outcome §2.6 exists
to produce. ⛔ **But state the weakness plainly rather than burying it: "does not own it" is
the only unmeasured term in the Layer-2 rule.** Q1, Q2, Q4, Q7 and Q8 were all resolved by
calling ownership *shared*, and a rule that never fires because its trigger condition is
adjudicated case by case is not yet a measurement.

⭐ **One design, for book 3:** state each question's owning document **in the plan, before the
run**, the way the positive controls already state their expected slug. That converts ownership
from an after-the-fact judgement into a prediction that can be wrong. **The runner-up — drop
the ownership clause and flag any ≥ 3 of 6 outright — is argued down**: it would have fired on
Q2, Q3, Q5, Q6, Q9 and Q10 here, all of them correct answers, and a signal that fires on
correct behaviour is worse than one that never fires.

#### 4.2c ⚠️ Carry-forward — the intra-document concentration Layer 3 would not fix

[`01-water.md`](01-water.md) §6 recorded, on one question, that **Q8 spent 5 of its 6 slots on
a single heading on a single page.** The concentration is *intra*-document, so README §3.3's
`PARTITION BY d.id` is the wrong shape for it. It was recorded and not acted on, with the note
*"watch books 2 and 3."*

⭐ **This is book 2, so check for it explicitly rather than only running the Layer-2 query.**
For each of the 10 questions, record **how many of the 6 results share one `heading_path`**.

| Outcome | What it means |
|---|---|
| no question exceeds 2 of 6 on one heading | Water's Q8 was a property of that one question. Close it |
| ⭐ **any question hits ≥ 4 of 6 on one heading** | **second document, same pattern** — it promotes from a curiosity to a design question, and the fix to specify is `PARTITION BY d.id, c.heading_path`, not the per-document cap |

**Yeast's most likely candidate is the oxygen control question** — `How Much Oxygen Is Needed?`
is **6 consecutive chunks on pp.98–104**, `measured`, which is the same shape as Water's
reverse-osmosis heading. ⚠️ **Predicting it is the point**: if it happens on the question this
paragraph names, that is two documents and a reproducible pattern.

##### ⭐ `measured` 2026-08-19 — the threshold fires, and the finding it was written to catch does **not** reproduce

**Per-question maxima, over all 10 questions:**

| # | Most-repeated `heading_path` | of 6 | Most-repeated **page** | of 6 |
|---|---|---|---|---|
| Q1 | `Diacetyl Rest` · `10.4 Yeast Starters and Diacetyl Rests` | 2 · 2 | p.98 | 2 |
| Q2 | `Refinement of RA` | 2 | — | 1 |
| Q3 | *(all distinct)* | 1 | ⚠️ **p.41** | **3** |
| Q4 | `Working With Dry Yeast` | 2 | — | 1 |
| Q5 | *(all distinct)* | 1 | — | 1 |
| Q6 | `Estimating Yeast Density` | 2 | p.144 | 2 |
| Q7 | *(all distinct)* | 1 | — | 1 |
| **Q8** | ⚠️ **`How Much Oxygen Is Needed?`** | **3** | — | **1** |
| **Q9** | ⛔ ⭐ **`Flocculation`** | ⭐ **4** | — | **1** |
| Q10 | *(all distinct)* | 1 | n/a — cards have no page | — |

⭐ **Q9 hits 4 of 6 on one `heading_path` — `measured`, and the arrays are byte-identical
(`{Flocculation}`, chunks 56, 57, 60, 181).** By the letter of the table above, that promotes
the question to a design question. ⛔ **It should not, and the reason is the whole finding.**

**Water's Q8 and Yeast's Q9 are not the same pattern.** `measured`, side by side:

| | Water Q8 — reverse osmosis | ⭐ Yeast Q9 — flocculation |
|---|---|---|
| slots on one heading | **5 of 6** | **4 of 6** |
| **slots on one heading *and* one page** | ⛔ **4 of 6** — all p.164 | ✅ **1** — pp.47, 48, 50, 130, four different pages in two different chapters |
| what the reader gets | ⚠️ *"the answer is correct but the top-6 has almost no diversity"* | ⭐ **four different claims**: the definition (p.47), the cell-wall biochemistry (p.48), why low flocculators are used in hefeweizen and witbier (p.50), and premature dropping and underattenuation (p.130) |
| what a heading-partition cap would do | remove near-duplicates from one section — an improvement | ⛔ **delete three genuinely different answers** to make room for `Lagering` p.135 |

⛔ **So the answer to the carry-forward is: Water's Q8 shape did not reproduce.** `measured`
across all 10 questions, the maximum concentration on one **(heading, page)** pair is **2**
(Q1, p.98) against Water's **4**. What repeated is *heading reuse* — a book that titles eight
sections in different chapters `Flocculation` — and that is a fact about the book's structure,
not about retrieval collapsing.

⭐ **Recommendation, one design: do not build `PARTITION BY d.id, c.heading_path`, and change
the metric instead.** Count concentration on the **(`heading_path`, `page_from`) pair**, not on
the heading string. `measured`, that metric reads **4 of 6** on Water's Q8 and **1 of 6** on
Yeast's Q9 — it separates the two cases the heading-only metric conflates, and it needs no
schema change and no SQL in the fusion to compute.

⚠️ **The runner-up, argued on the record: build the heading partition now, since the threshold
technically fired.** ⛔ **Rejected.** It would have made Q9's answer worse by three chunks, on
its first firing, in the name of a diversity the reader already had. **README §3.3's discipline
applies unchanged — the fix is built when the *problem* recurs, not when the proxy for it
does.** This is the same argument as §4.5's, one layer down.

⭐ **Book 3 inherits a sharper question than book 2 did**: not *"does concentration repeat?"*
but *"does concentration on one **page** repeat?"* — and the metric to answer it is written
above.

⚠️ **One row worth not misreading.** Q3 has **3 of 6 on p.41** — `Bittering`, `Flavoring` and
`Finishing`, three distinct headings on one page at ranks 1–3. That is the **documented
expected result** for the gate question, unchanged since book 0a. Page concentration is not a
defect by itself; page concentration **under one heading** is what Water's Q8 was.

#### 4.2d The other Water defect worth watching

⚠️ **Bare attribution chunks retrieved at rank 4 on two questions** — Water's `-J. Palmer`.
**Yeast's equivalent is `Palmer, John`** — an index entry promoted to a heading over 5
chunks — and §2.3's alternative 5 **drops all five before they can retrieve.** ⭐ **So this
specific defect is prevented rather than recorded this time**, and A6's `head_glyph` column
plus §2.5's 11 garbled headings are what remains. ⚠️ **Watch for a garbled heading in a Tier B
citation** — `Yeast > /g53 /g84/g97/g92…` is what a hit on the p.86 `Fermentation` chunk would
render as, and it is the same class of unreadable citation.

##### ⭐ `measured` 2026-08-19 — nothing equivalent survived, and no garbled heading retrieved

| Check | `measured` |
|---|---|
| a `Palmer, John` chunk in any top-6 | ✅ **none** — all five were dropped at ingest (§2.3 alternative 5), so they cannot retrieve |
| ⭐ a **glyph** heading in any of the **60** returned rows | ✅ **none.** Not one of the 11 `head_glyph` chunks (A6) reached a top-6 on any of the 10 questions |
| an uninformative-heading chunk from Yeast anywhere in the 60 | ✅ **none** — every Yeast heading returned reads as a topic: `Diacetyl Rest`, `Lagering`, `Working With Dry Yeast`, `Estimating Yeast Density`, `How Much Oxygen Is Needed?`, `Flocculation`, `Sour`, `Fermentation Does Not Start`, `Flocculation Changes`, `Starter Volume in Liters` |

⭐ **Book 1 predicted a defect and got it; book 2 predicted a defect, prevented it in the
mapper, and the prevention held.** `-J. Palmer` retrieved at rank 4 twice in Water's run
because nothing dropped it; `Palmer, John` cannot, because `extra_drop_regex` removed it before
embedding. **That is a mapper field doing the work a shared-code change would otherwise have
had to do, which is §0's verdict measured rather than argued.**

⚠️ **What this does *not* establish, stated so it is not over-claimed.** Water's `-J. Palmer`
defect was found on Water's own positive controls (sulfate ratio, sparge acidification), and
**those two questions are not in book 2's ten** — book 2's controls are yeast questions.
⛔ **So the Water defect was not re-probed and nothing here says it is gone.** It is still
recorded as a known cost in [`01-water.md`](01-water.md) §6, and the 11 garbled Yeast headings
are its counterpart in this book: **present in the corpus, not yet retrieved.** Book 3 should
watch the same thing for *Malt*.

### 4.3 Tier C — agent

⛔ **Not runnable, and this is a decision rather than a skip.** There is no chat agent and no
search tool: **WF4 and `tool-search-brewing-knowledge` are both unbuilt** (README §1.3 items 6
and 7). Running an agent test against no agent is impossible, not omitted. **Tier C is not
runnable for any source yet.**

⭐ **Re-verified rather than carried, `measured` 2026-08-19:** `n8n list:workflow` returns
**five** workflows — `wf1-ingest-book`, `ingest-how-to-brew`, `ingest-water`,
`ingest-bjcp-styles` and ⭐ `ingest-yeast` (new since §1.1's four). **None of them is an agent,
and none is a tool.** The count changed; the conclusion did not.

⭐ **It has a date: README §4.2 schedules the agent as book 4.5** — after book 4, before
book 5 — and clearing the Tier C backlog for books 0a–4 in one sitting is one of the four
reasons it sits there. **So this section is a deposit, not a deferral**, and book 2's deposit
is the five questions below.

**Tier C for Yeast runs as part of that build**, and must include these five:

| Type | Question | Pass condition |
|---|---|---|
| new coverage | *"How many yeast cells should I pitch for a 1.060 lager?"* | answers with numbers from Yeast, **names the source**, every `[S…]` resolves |
| ⛔ **refusal still holds** | *"How much Citra do I have?"* | *"I don't have a tool for that yet"* — ⛔ **the one hard fail, re-run in every plan** |
| citation integrity | any yeast question | no `[S…]` the tool did not return |
| ⭐ **conflict / depth surfacing** | *"When should I do a diacetyl rest — is Palmer's answer enough?"* | ⭐ **both books attributed**, both carrying `authority: reference`. §2.6's keep-both rule made visible |
| ⭐ **decode honesty** | *"Which enzymes break down starch during malting?"* | says **α-amylase** and **β-amylase**, not `/g95 -amylase` — the end-to-end proof that §2.4's repairs reached the model, not just the database |

⭐ **Two of the five now have their retrieval half already measured, which narrows what 4.5
has to establish** — recorded here so the agent test is not re-derived from scratch:

| | What Tier B already proved | What 4.5 still has to prove |
|---|---|---|
| **conflict / depth surfacing** | ✅ the retrieval works — §4.2a Q1 returns yeast p.133 at rank 1 **and** how-to-brew p.98 at rank 3 in the same top-6 | whether the **model** attributes both rather than blending them |
| **decode honesty** | ✅ the text is right in the database — §4.1 A5, `unrepaired_amylase` = **0** | whether the passage header and citation render it, and whether a **garbled heading** (A6's 11) reaches a citation |

**`scripts/stress/tier1_routing.py` is not run for this source** (§2.7). ⭐ **Confirmed by the
same measurement:** it scores tool routing against a system prompt, and `measured` 2026-08-19
there is still neither.
### 4.4 The documented misses — argued, not tuned

⭐ Standing rule 6. **Each miss now carries what actually happened, `measured` 2026-08-19.**

**1 · p25 is 173 tokens, below §11's 200–450 band.** `measured` on the probe, `predicted`
unchanged by cleaning. ⭐ **`measured` after the run: p25 = 173, p75 = 424 — the prediction was
exact in both directions.** The **median (313) and p75 (424) are comfortably inside**; the low
quartile is pulled down by the lab-manual half of the book (pp.190–285), where `Materials` and
`Procedure` sections are genuinely short units of text. ⛔ **Raising `chunking_max_tokens` does
not fix a low p25** — it makes long chunks longer and leaves short ones alone. The right
response is to record that this book is bimodal: narrative chapters and lab procedures, and a
single distribution describes neither. **No action, and none taken.**

⭐ **One thing the run adds that the probe could not:** `measured`, *How to Brew*'s p25 is
**179** and its median **291** — so the corpus's oldest book misses the same band in the same
direction. **Yeast is not the outlier the plan implied it might be**, and §11's 200–450 band
now describes one of the three prose books (Water: p25 198, median 342). ⚠️ **That is a
criterion to revisit at book 4, not here** — standing rule 6 says argue the miss, and three
books missing a band the same way is an argument about the band.

**2 · ⭐ 15 chunks lost to the token floor, and 11 of them are `Materials` lists.** This is the
real cost of book 2 and the one to argue properly. `measured` (§5.5): the dropped chunks are
the equipment lists for eleven lab procedures (pp.210–280), plus two flavour-category lists
(p.65), plus a cross-reference and a running-header fragment.

⭐ **`measured` after the run: exactly 15, pp.65–301, reason `under 30 tokens, no table` —
the count, the reason and the page band all exact** (§4.1 A2b).

| Option | Verdict |
|---|---|
| Lower `minTokens` to 20 | ⛔ **no.** `minTokens` lives in the shared `book` profile; changing it rewrites *How to Brew*'s ledger and breaks the 447-chunk fixture the whole phase rests on |
| Add a per-book `min_tokens` field | ⛔ **no** — an engine change (new trigger field + code) for a fix that is the wrong shape. A 5-token chunk reading *"Lager: Dry, Full"* is not worth retrieving whatever the floor is |
| ⭐ **Merge-forward: absorb a short `Materials` chunk into the `Procedure` that follows it** | ⭐ **the right fix, and deliberately not built here.** `measured`: chunk 301 (`Materials`, 24 tok) is immediately followed by chunk 302 (`Procedure`, 273 tok) covering the same test — merged they are one coherent 297-token chunk |
| ✅ **Accept the loss at book 2** | ✅ **recommended, and taken** |

**Why accept.** ⭐ **This is the *second* sighting of the pattern** — [`01-water.md`](01-water.md)
§1.4 recorded the first, a single worked-example question lost to the same rule, and argued
that "a one-chunk gain is not worth invalidating the fixture." At 11 sites that argument is
weaker, but two facts still hold it: a 24-token bullet list headed `Materials` is close to
unretrievable *anyway* (its heading path says nothing and its body is a list of nouns), and the
`Procedure` chunk that survives is what a user asking *"how do I run a forced fermentation
test"* actually wants.

⭐ **The run supplies one piece of evidence the argument did not have, and it cuts the way the
argument assumed.** `measured` across all 10 Tier B questions: **not one `Materials` or
`Procedure` chunk appeared in any top-6**, and the lab-manual half of the book (pp.190–285)
contributed exactly **two** results in sixty — `Fermentation Does Not Start` p.283 (Q7 rank 5)
and `Flocculation Changes` p.286 (Q9 rank 4), both from the troubleshooting chapter rather than
the procedures. ⚠️ **That is a weak test and must not be read as a strong one**: none of the ten
questions asks *how do I run a lab procedure*, which is the only question the dropped chunks
could have answered. **It shows the loss is invisible to the current question set, not that it
is harmless.**

⛔ **State the trend loudly, because it is what book 3 decides.** One book, one chunk was a
curiosity. Two books, twelve chunks is a pattern. **If *Malt* (book 3) shows it again, build
merge-forward then** — it is real work in shared code, it belongs to whichever book makes it
pay, and this paragraph is the precedent to reopen.

**3 · `page_count` will read 305, not 325.** Not a miss, a definition: the field is
`max(page_to)` over **kept** chunks, and pp.306–325 are List of Figures, bibliography and
Index. ⛔ **A `page_count` of 325 means the back matter survived**, which is `extra_drop_regex`
having failed silently.

⭐ **`measured`: `kb.document_versions.page_count` = 305, and `max(page_to)` over the kept
chunks = 305 independently.** The back matter did not survive, and §4.1 A6's
`plain_backmatter` = 0 confirms it from the other direction.
### 4.5 Corpus share — expect it, argue it, do not tune it

| | `predicted` | ⭐ **`measured` 2026-08-19** |
|---|---|---|
| Yeast chunks | **463** | ✅ **463** |
| Corpus after | **1,524** (1,061 + 463) | ✅ **1,524** |
| ⚠️ **Yeast's share** | **30.4%** — crosses README §3.3's **25%** signal | ⚠️ **30.4%** (463 / 1,524) |
| How to Brew · Water · styles after | **29.3% · 25.1% · 15.2%** | ✅ **29.3% · 25.1% · 15.2%** |
| Yeast's share at the projected ~3,000-chunk corpus | **~14%** | `predicted`, unchanged |

⚠️ **Three of the four documents now sit at or above the 25% line, and that is a fact about
having four documents, not about any of them being over-represented.** 463 chunks for 325 pages
is **1.42 kept chunks per page**, against Water's 1.40 and *How to Brew*'s 1.80 — Yeast is the
**least** densely chunked book in the corpus.

⭐ **Water already produced the evidence that the proxy is only a proxy:** it crossed at 36.0%
and returned **0 of 6** on a style question. Standing rule 6 — **argue it, do not shrink it.**

⭐ **`measured` 2026-08-19, and this is now a two-book result rather than a one-book one.**
Yeast crossed the line at **30.4%** and, over ten questions, took **0 of 6** on the style
question (Q10, a top-6 byte-identical to the post-Water baseline), **1 of 6** on the
off-flavour question it does not own (Q5), and **0 of 6** on both hop timing and mash pH.
⛔ **The corpus-share proxy has now crossed twice and the thing it proxies for has happened
zero times.** Layer 2 fired on nothing in either run.

**What that is worth, stated without over-claiming.** It is evidence that **corpus share does
not predict retrieval share** for a topically-scoped reference book — which is exactly the
population every source in books 1–4 belongs to. ⚠️ **It says nothing about book 5**, where BA
2026 and the BJCP Study Guide are *not* topically disjoint from what is already in the corpus;
that is the case the proxy was really written for, and it is still ahead.

⛔ **Corpus share is the cheap proxy; retrieval share is the measurement.** Layer 3 is built
**only when Layer 2 fires**, not when the proxy crosses. It was not built here.
### 4.6 Exit — book 2 is done when

⭐ **Scored 2026-08-19.** ✅ = done and verified · ⚠️ = done with a documented miss · ⛔ = not done.

- [⚠️] §1.2's three items are closed — engine at **26 nodes** and re-exported, A3 **watched**
      live, and the post-Water baseline taken from [`01-water.md`](01-water.md) rather than
      re-derived
  - ⛔ **item 1 not done.** `measured` 2026-08-19: `wf1-ingest-book` holds **27 nodes** in both
    the live workflow and the tracked JSON, and `Clean + normalise1` is still there — still
    with no incoming and no outgoing connection, and still **without** the untab fix that the
    live `Clean + normalise` has (8,229 vs 4,259 characters of `jsCode`). A **third divergent
    copy of the cleaning profile**, unchanged since book 1 flagged it
  - ⛔ **item 2 not done** — §4.1 A3. Recorded as *not observed*
  - ✅ **item 3 done** — the baseline was taken from `01-water.md` §6 and not re-derived
- [⛔] `ingest-yeast` exists, 2 nodes, Wait-for-completion ON, all **13** mapper fields filled,
      `front_matter_max_page = 21`, `extra_drop_regex` and `text_repairs` pasted from §2.3 and
      §2.4, **exported and committed before its first run** (standing rule 4)
  - ✅ **the workflow is exactly as specified.** `measured` from the export: 2 nodes,
    `executeWorkflow` typeVersion 1.3, `waitForSubWorkflow: true`, settings `executionOrder v1`
    / `binaryMode separate`, and all **13** mapper fields matching §2.2, §2.3 and §2.4
    character for character — including `front_matter_max_page = 21`, the seven-alternative
    `extra_drop_regex` and the four-pair `text_repairs`
  - ⛔ **standing rule 4 was broken again, at book 2.** `measured`: there was no
    `ingest-yeast.json` in `n8n/demo-data/workflows/` and none in git history; the launcher
    existed **only in n8n's database** from its creation until **2026-08-19**, when it was
    exported as part of closing this record. ⚠️ **This is the same rule, broken the same way,
    one book after [README §9](README.md) recorded it as broken at book 1.** Exporting after
    the fact restores the artefact but **not** the property the rule exists for: for a week the
    only copy of a 13-field mapper — three of whose fields must never be copied from another
    book — was inside a container's database
- [✅] the run's `stats` read **526 raw → 463 kept, 63 dropped, 87 repairs applied**, and the
      drop ledger reads **27 / 21 / 15** by reason — ⭐ **all six numbers exact**, §4.1 A2/A2b
- [✅] ⭐ A2c returns **4 repair rows, `54 / 17 / 10 / 6`** — the first repair ledger this project
      has ever recorded, and read for the asymmetry rather than ticked. ⭐ **All four exact**
- [✅] A1 reads **463 | 463 | 0 | 0** for Yeast, ⛔ **447 | 447 | 0 | 0** for *How to Brew* and
      ⛔ **382 | 382 | 0 | 0** for Water — ⭐ **all three exact**
- [⚠️] A5 shows all four repairs in the stored text and ⛔ **0 unrepaired**
  - ✅ **the gate passes: `unrepaired_amylase` 0, `unrepaired_header` 0**, and all 17 arrow
    replacements are accounted for in kept chunks
  - ⚠️ **`r3` reads 1, not the predicted 4** — a sites-vs-chunks units error in the prediction,
    diagnosed in §4.1 A5
- [⚠️] A6 reads **17 | 11 | 0** — the glyph residue is the size §2.5 predicted, and ⛔ **no
      readable back-matter heading survived**
  - ✅ **`head_glyph` 11 exact and `plain_backmatter` 0** — §2.3 confirmed
  - ⚠️ **`body_glyph` reads 13, not 17.** The residue is **smaller** than predicted, and its
    123-token total is exact on `content`. §4.1 A6
- [⛔] A3 stops at `Already ingested` in seconds with an identical fingerprint at **1,524**
  - ⛔ **not observed and not recoverable** — §4.1 A3. `ingest-yeast` has exactly one execution
- [✅] the 5 standing questions pass the keep rule, and ⭐ **§4.2a's five predictions are scored
      against what actually happened** — including the two this plan expects Yeast to win
  - ✅ **keep** — all five prior rank-1 chunks still in the top 3, zero defects, no reset
  - ⭐ **4 of 5 predictions correct; Q4 falsified** — §4.2a
- [✅] all 4 positive controls reach the top 3 in `yeast-practical-guide` — ⭐ **all four at
      rank 1**
- [✅] ⭐ the Layer-2 retrieval share is **recorded for all 10 questions, including a null**, and
      §4.2c's **per-heading** count is recorded alongside it — §4.2b, §4.2c
- [✅] corpus share is **recorded at 30.4% and argued, not tuned** (§4.5)
- [⚠️] `ingest-yeast.json` re-exported and committed with the measured numbers in the message
  - ⚠️ **exported 2026-08-19, after the run** — see the second item above
- [✅] README §9's book 2 row ticked. ✅ **README §4.3's projected corpus is already corrected** —
      it carried **~590** for Yeast against this plan's **463**, and the running total dropped
      from ~3,200 to ~2,965. ⭐ `measured` **1,524** matches the projection's book-2 row exactly,
      so the ~2,965 total is unchanged
- [✅] ⭐ **§0's verdict recorded either way** — *"book 2 was mapper-only"* is the evidence D30
      was designed to produce, and it only counts if it is written down. ⭐ **It held:**
      `measured` 2026-08-19, the only artefact book 2 added to n8n is a 2-node launcher, and
      the engine's `Clean + normalise` is byte-identical to the one book 1 left behind

> ### ⭐ Book 2, in one line
>
> **The record is closed.** Twenty-one numbers `predicted` from a probe and **twenty-one hit
> exactly**; the repair ledger recorded for the first time, per pair; Tier B **keep** with
> all four controls at rank 1 and Layer 2 firing on nothing for the second run running.
> ⛔ **Three things are open and none of them is the ingest:** A3 was never observed, standing
> rule 4 was broken again, and the orphaned `Clean + normalise1` node is still live.
## §5 — Evidence: what was measured before the plan was written

⭐ **Standing rule 1, and the section every number above is derived from.** Everything below was
`measured` on **2026-08-12** by submitting the file to the **live** Docling service. No number
in this plan is extrapolated from *Water* or *How to Brew*.

### 5.0 The submission — the engine's ten form fields, byte for byte

**File:** `shared/rag-files/pending/yeast-the-practical-guide-to-beer-fermentation-0937381969_compress.pdf`
— 5,384,437 bytes, **325 pages** (`pdfinfo`).
**Container path:** `/data/shared/rag-files/pending/yeast-the-practical-guide-to-beer-fermentation-0937381969_compress.pdf`
(⚠️ n8n does not see the host path; the mount is `…/shared → /data/shared`, verified §1.1).
**SHA-256:** `2f30d7e5d8a965df00dbd225f57c4d759dd8ab90f99974b0ffee9b39f54266a4` — **`measured`,
re-verified for this plan.** This is the value `Crypto` must produce and the dedup key
`kb.document_versions.file_sha256` will carry, and it is what §3 is keyed on.

The ten fields below were **diffed against the live `Docling submit` node**, not copied from
plan 01:

```bash
curl -s -X POST http://localhost:5001/v1/chunk/hybrid/file/async \
  -F "files=@shared/rag-files/pending/yeast-the-practical-guide-to-beer-fermentation-0937381969_compress.pdf" \
  -F "convert_from_formats=pdf" \
  -F "convert_image_export_mode=referenced" \
  -F "convert_do_ocr=false" \
  -F "convert_pdf_backend=dlparse_v4" \
  -F "convert_table_mode=accurate" \
  -F "chunking_tokenizer=BAAI/bge-m3" \
  -F "chunking_max_tokens=512" \
  -F "chunking_include_raw_text=true" \
  -F "chunking_use_markdown_tables=true"
```

**`documents[0].status`: `success`. `processing_time`: 137.01 s — `measured`.**

### 5.1 The headline numbers

| Measure | **Measured** | Reads as |
|---|---|---|
| raw chunk count | **526** | vs Water 440 raw / 382 kept, *How to Brew* 483 / 447 |
| pages covered | **2 – 325** | the whole book; p1 carries no extractable text |
| **chunks per page** | **1.62** | prose. Water 1.61, *How to Brew* 1.95. ⚠️ A 325-page book yields only 20% more raw chunks than a 273-page one because the trim is small — 3.5″ × 5.19″ |
| median `num_tokens` | **313.5** | ✅ inside §11's 200–450 band |
| **p25 / p75** | **163 / 429** | ⚠️ **p25 is below the band** — §4.4's first documented miss. Water: 202 / 469 |
| max / min | **560 / 5** | |
| count **over 512** | **3** | ⭐ **all three are table-of-contents pages** (chunks 4, 5, 7) and die on the page rule → **0 after cleaning** |
| count **under 30** | **15** | §5.5 lists all fifteen |
| ⭐ **chunks with no `page_from`** | **0** | ⛔ the must-be-0 gate, hit exactly. Citations are safe |
| ⚠️ **chunks with no headings** | **1** | ⭐ chunk 0, pp.2–3, the publisher block — **dropped by the page rule**, so `missing_heading` after cleaning is **0** |
| distinct headings | **262** | §5.3 |
| heading depth | ⭐ **1, on 525 of 526** | `heading_path` is never nested in this book — no `A > B` citations |
| chunks containing a table | **42** (8.0%) | `table_mode=accurate`; **34 survive** cleaning |
| chunks with captions | **0** | figure captions are not separated out by this backend |
| ⭐ **tab characters** | ⭐ **0**, in all 526 chunks | ⭐ **against Water's 75,154.** Book 1's untab block is a **no-op** here — the second independent confirmation that it was safe shared code |
| chars per token | **4.289** raw / **4.211** kept | vs Water's 4.191 and *How to Brew*'s 4.379. The size predictions are calibrated, not guessed |

**What this table decides:** the file needs no format-specific handling and no new profile.
0 missing pages, 0 tabs, 1 headingless chunk that the page rule removes, and 3 over-band chunks
that are all front matter — the `book` profile was written for this.

### 5.2 The front-matter page range — ⭐ `front_matter_max_page = 21`

⛔ **A fact about White & Zainasheff's PDF, not about books.** *How to Brew* uses **6**, Water
**18**. Every chunk on pp.2–27 was read:

| Chunks | Pages | Heading (decoded) | What it is | Keep? |
|---|---|---|---|---|
| 0 | 2–3 | ⚠️ *(none)* | title page + publisher block — ⭐ **the only headingless chunk in the book** | ⛔ drop |
| 1, 2 | 3 | `© Copyright 2010 by Brewers Association`, `2010029741` | copyright + CIP block | ⛔ drop |
| 3–10 | 4–11 | `table of contents` *(glyph)* | TOC — ⭐ **and the three over-512 chunks** | ⛔ drop |
| 11–13 | 12–15 | `Acknowledgements` *(glyph)* | front matter | ⛔ drop |
| 14–20 | 16–21 | `Foreword` *(glyph)* | the foreword — signed **Mitch Steele, Head Brewer, Stone Brewing Company** (`measured`, chunk 20). Why the book exists, not how brewing works | ⛔ drop |
| 21, 22 | 22–23 | `Introduction` *(glyph)* | ⚠️ *"we decided this would not be a yeast biology book"* — about the book, not about brewing | ⛔ **dropped by `extra_drop_regex`**, §5.3 |
| **23** | **23** | **`Fermentor vs. Fermenter`** | ⭐ **a real terminology sidebar, 102 tokens** | ✅ **keep** |
| 24–26 | 24–26 | `About Chris White`, `About Jamil Zainasheff` | author biographies | ✅ **keep — see below** |
| **27** | **26–27** | **`A Brief History of Yeast`** | ⭐ **chapter 1, first real content** | ✅ **keep** |

**`front_matter_max_page = 21` — the last page of the Foreword.** The rule is
`pageTo <= FRONT_MAX`; chunk 20 spans pp.20–21 and is caught, chunk 21 spans pp.22–23 and is
not. **Drops exactly 21 chunks and not one more** — verified by simulation (§5.7).

⚠️ **Why the cut is at 21 and not at chapter 1.** The obvious cut is p.25, the last page before
`A Brief History of Yeast`. It is wrong for two reasons, both `measured`: chunk 23
(`Fermentor vs. Fermenter`, p.23) is **real content** sitting inside the front matter, and
chunk 26 (`About Jamil Zainasheff`) spans **pp.25–26**, so `pageTo = 26` would survive a cut at
25 anyway and leave one bio behind while dropping the other. **A page rule cannot separate
them; so the page rule stops at the Foreword and the Introduction is handled by heading
instead.**

**The author bios are kept, deliberately.** They are 3 chunks of biography, they carry readable
headings, and §2.6's rule is that nothing is dropped for being merely low-value. ⚠️ Note that
the shared profile's `^About the Author` pattern does **not** match `About Chris White` — so
this is a decision, not an accident of the regex.

### 5.3 ⭐ The headings — and the finding that shapes the whole plan

**Top 22 by frequency, of 262 distinct.** Glyph headings are shown decoded, with the raw form
marked.

| n | Heading | pp. | Verdict |
|---|---|---|---|
| **37** | `Procedure` | 210–282 | ✅ kept — the lab-manual half of the book |
| **32** | `Materials` | 210–280 | ⚠️ kept where long enough; **11 fall to the token floor** (§5.5) |
| 8 | `table of contents` ⛔ *glyph* | 4–11 | ⛔ dropped by page |
| 8 | `Flocculation` | 47–132 | ✅ core content |
| 8 | `Making a Starter` | 154–160 | ✅ |
| 7 | `Foreword` ⛔ *glyph* | 16–21 | ⛔ dropped by page |
| 6 | `Enzymes` | 51–93 | ✅ |
| 6 | `Yeast Nutrition` | 93–96 | ✅ |
| 6 | `How Much Oxygen Is Needed?` | 98–104 | ✅ ⚠️ §4.2c's predicted concentration site |
| 6 | `Reusing Yeast` | 182–186 | ✅ |
| 5 | `A Brief History of Yeast` | 26–30 | ✅ chapter 1 |
| 5 | `Commercial Fermentors` | 108–114 | ✅ |
| 5 | `Bottle Conditioning` | 136–139 | ✅ |
| 5 | `Estimating Yeast Density` | 144–147 | ✅ |
| 5 | `Starter Volume in Liters` | 164–165 | ✅ |
| 5 | `Bottom Cropping Timing and Techniques` | 174–177 | ✅ |
| 5 | `Yeast and Beer Quality Assurance` | 230–235 | ✅ |
| **5** | `Index` ⛔ *glyph* | 318–322 | ⛔ **dropped by `extra_drop_regex` — `dropHeading` cannot see it** |
| **5** | `Palmer, John` | 322–325 | ⛔ **also the Index**, headed by an index entry. §5.4 |
| 4 | `Multiple Strains in One Beer` | 75–79 | ✅ |
| 4 | `Temperature Differences for Lager and Ale Strains` | 116–119 | ✅ |
| 4 | `15 x 20 x 0.1018 = 30.54 W` | 121–124 | ✅ ⚠️ a worked calculation promoted to a heading — cosmetic, kept |

⭐ **The measurement that decides §0.1, stated as a number:**

| Rule | Headings it matches in *Yeast* |
|---|---|
| `dropHeading` — `^(Contents\|Index\|Glossary\|Acknowledg\|Copyright\|About the Author)` | ⛔ **0 of 262** |
| `dropReferences` — `^references$` on the trimmed heading | ⛔ **0 of 262** |

**Both shared heading rules are inert on this book**, because every heading they were written to
catch is set in the broken display font. Water's `Index` (34 chunks) was caught by the first
rule; Yeast's is not.

**All 16 distinct glyph headings, decoded — the complete set:**

| Chunks | pp. | Decoded | Disposition |
|---|---|---|---|
| 8 | 4–11 | `table of contents` | ⛔ page rule |
| 7 | 16–21 | `Foreword` | ⛔ page rule |
| 3 | 12–15 | `Acknowledgements` | ⛔ page rule |
| 2 | 22–23 | `Introduction` | ⛔ `extra_drop_regex` #1 |
| 5 | 318–322 | `Index` | ⛔ `extra_drop_regex` #4 |
| 4 | 306–311 | `List of Figures` | ⛔ `extra_drop_regex` #2 |
| 2 | 313–314 | `References` | ⛔ `extra_drop_regex` #3 |
| 1 | 62 | `How to Choose the Right Yeast` | ✅ **kept, garbled** |
| 1 | 86 | `Fermentation` | ✅ **kept, garbled** |
| 1 | 282 | `Troubleshooting` | ✅ **kept, garbled** |
| 8 | 45–160 | six metabolic equations, e.g. `Glucose + 2 ADP + 2 phosphate → 2 ethanol + 2 CO2 + 2 ATP` | ✅ **kept**; the arrow is `/g65` and §2.4's repair 3 fixes it **in the body only** |

⭐ **The decode is mechanical: glyph id + 17 = ASCII codepoint**, verified across all 16 runs.
That is what makes §0.3's decoder tempting and §0.3's argument against it necessary — the offset
is a property of *this font subset*, not of PDFs, and nothing measures it at runtime.

### 5.4 The back matter — 25 chunks across four sections

⭐ A 325-page book has more back matter than Water's Index-plus-References, and it is the half
of the file the shared rules handle worst.

| Chunks | pp. | Heading as Docling reports it | What it is |
|---|---|---|---|
| 501–504 | 306–311 | `List of Figures` *(glyph)* | a figure index — *"Figure 1.1, p. 8: Busts of Louis Pasteur…"* |
| 505 | 312 | ⚠️ **`Foreword`** *(plain text)* | ⚠️ **the bibliography's first block**, mislabelled with the section it cites |
| 506, 507, 510–515 | 312–317 | ⚠️ **`Part 1` … `Part 7`** | the bibliography, split by the book's parts |
| 508, 509 | 313–314 | `References` *(glyph)* | more bibliography |
| 516–520 | 318–322 | `Index` *(glyph)* | the Index |
| 521–525 | 322–325 | ⚠️ **`Palmer, John`** | ⭐ **still the Index** — Docling promoted an index entry to the heading for pp.322–325 |

⚠️ **`Palmer, John` is this book's `-J. Palmer`, and it is worse.** In Water, nine chunks of
real Palmer commentary were kept under an uninformative heading (a recorded weakness). Here,
five chunks of **index entries** are labelled with an index entry — content that has no
retrieval value at all under a heading that looks like it might. ⭐ **`extra_drop_regex` #5
drops all five**, which is why §4.2d records this defect as *prevented* rather than *carried*.

⚠️ **The `Part 1`…`Part 7` headings are the reason a heading rule can catch this at all.**
`measured`: those seven strings appear on **no page outside 312–317**. If they had appeared in
the body, the bibliography would have needed a page rule the engine does not have — and that
would have been the finding that broke §0's verdict.

### 5.5 The fifteen chunks under 30 tokens

The profile drops a chunk under 30 tokens **unless it contains a table**. **None of the fifteen
contains a table**, so all fifteen drop. All fifteen, `measured`:

| idx | p. | tok | Heading | `raw_text` | Verdict |
|---|---|---|---|---|---|
| 86 | 65 | 16 | `Ale` | `- Clean / - Fruity / - Hybrid / - Phenolic / - Eccentric` | ⚠️ a real flavour-category list |
| 87 | 65 | 5 | `Lager` | `- Dry / - Full` | ⚠️ same, and genuinely too small to retrieve |
| 301 | 210 | 24 | `Materials` | `- 3M Attest Biological Indicator capsule… / - Autoclave or pressure cooker` | ⚠️ **§4.4's accepted loss** |
| 353 | 239 | 26 | `Materials` | `- WLN and WLD plates… / - Incubator` | ⚠️ same |
| 356 | 240 | 14 | `Materials` | `- Media plates / - Sterile swabs / - Incubator` | ⚠️ same |
| 362 | 242 | 25 | `Materials` | `- Sterile wort collection vessel / - Incubator…` | ⚠️ same |
| 367 | 243 | 28 | `Materials` | `- Sterile wort collection vessel / - Shaker table…` | ⚠️ same |
| 370 | 244 | 22 | `Materials` | `- Two glasses / - Aluminum foil / - Hot water bath…` | ⚠️ same |
| 379 | 248 | 18 | `Materials` | `- Dissolved oxygen meter / - Stir plate…` | ⚠️ same |
| 383 | 250 | 19 | `Materials` | `- Visible spectrum spectrophotometer / - 1 cm cuvettes…` | ⚠️ same |
| 443 | 273 | 29 | `Materials` | `- pH meter / - Deionized water / - 50 ml conical centrifuge tube…` | ⚠️ same |
| 457 | 279 | 29 | `Materials` | `- Yeast culture or slurry / - Sterile water and tubes…` | ⚠️ same |
| 460 | 280 | 29 | `Materials` | `- Yeast culture or slurry / - Sterile pipettes / - WLN plates…` | ⚠️ same |
| 468 | 286 | 28 | `Fermentation Seems Incomplete` | `Refer to the 'Attenuation' troubleshooting section (pp. 272-275)` | ✅ **correct drop** — a cross-reference |
| 496 | 301 | 18 | `Performance Problems` | `y eas t` | ✅ **correct drop** — a running header stranded between two tables |

**11 `Materials` + 2 category lists = 13 real losses; 2 correct drops.** §4.4 argues the
decision; the evidence for it is the pairing below, `measured`:

| idx | p. | tok | Heading | Content |
|---|---|---|---|---|
| 300 | 209 | 90 | `Autoclave Testing` | *"Being able to sterilize media is a critical function of a laboratory…"* |
| **301** | **210** | **24** | **`Materials`** | ⛔ **dropped** — *"- 3M Attest Biological Indicator capsule (or similar product) / - Autoclave or pressure cooker"* |
| 302 | 210 | 273 | `Procedure` | ✅ kept — *"1. Place 3M Attest Biological Indicator capsule into a test bottle of medium…"* |

⭐ **Chunk 302 names the missing equipment in its own first step**, which is why the loss is
survivable and why *merge-forward*, not a lower floor, is the fix if book 3 asks for one.

### 5.6 ⭐ The hyphen probe — standing rule 7, and the answer is `[]`

```bash
./scripts/hyphen-probe.sh shared/rag-files/pending/yeast-the-practical-guide-to-beer-fermentation-0937381969_compress.pdf
```

**Output — one site, one draft pair:**

```
1 at-risk site(s)
  line 4433    ...     Total 2,3-   | 900 ppb            5.09 ppb         3.
draft text_repairs: [["2,3900", "2,3-900"]]
```

⛔ **Checked against the Docling output, and it must not be used.**

| Draft pair | in `text` | in `raw_text` | Verdict |
|---|---|---|---|
| `["2,3900","2,3-900"]` | **0** | **0** | ⛔ **matches nothing → the engine throws and the ingest aborts** |

**Why it matches nothing:** it is not a wrapped range at all. `Total 2,3-` is the start of
*2,3-butanedione* (diacetyl) in one table column, and `900 ppb` is a value in a **different
column** of the same row; `pdftotext -layout` renders them as adjacent lines. This is the exact
false positive `hyphen-probe.sh`'s own header warns about, **naming this book**. ⭐ **The
warning was written from a previous look at this file and it is now confirmed by measurement.**

**Three independent sweeps were run before concluding `text_repairs` needs no hyphen pair:**

| Sweep | Result |
|---|---|
| broadened probe — **any** line ending in `-`, `‐`, `–` or `—` whose next line starts with a digit | **1 site**, the same false positive. En dashes: 9 in the whole book, none at a line end |
| the Docling output swept for **surviving** un-joined wraps — digit, hyphen, newline, digit | **1 site**, chunk 524 p.324 — inside the **Index**, which is dropped |
| every **4+ digit run** in the Docling output, read for implausible values | **0 suspicious.** Every hit is a year (`2008`, `1997`), an ISBN or a legitimate quantity — no fusion artefacts anywhere |

⭐ **So Yeast has no hyphen damage, and this is the first source where the probe's answer is
genuinely empty.** ⚠️ **It is not the first where the draft was wrong** — Water's draft was
wrong in both directions. Yeast's is wrong in one, and pasting it would have aborted the ingest
on the first run.

**`text_repairs` is therefore not empty for a different reason entirely** — §2.4's four pairs
repair a font, not a line wrap. **That is a new use of the field and it is stated as such.**

### 5.7 The simulation — every §4 number, derived

§2's rules run over the `measured` 526-chunk probe:

| Rule | Motivated by | **Predicted effect on Yeast** |
|---|---|---|
| `!raw` — empty `raw_text` | hygiene | **0** — `measured`, none are empty |
| `pageTo <= 21` — front matter | **§5.2**, read chunk by chunk | **21** — title/copyright 3, TOC 8, acknowledgements 3, foreword 7 |
| `dropHeading` | §5.3, all 262 headings read | ⭐ **0** — matches nothing |
| `extraRe` — source-specific | **§2.3**, seven alternatives | ⭐ **27** — Introduction 2, List of Figures 4, bibliography 11, References 2… **Index 10** across two heading forms |
| `dropReferences` | §5.3 | ⭐ **0** — matches nothing; the bibliography is caught by `extraRe` instead |
| `tokens < 30 && !hasTable` | §5.5, all fifteen read | **15** |
| `^\s*\d{1,3}\s*$` — page-number-only | hygiene | **0** — `measured` |
| untab (shared, from book 1) | §5.1 — 0 tabs | ⭐ **a no-op**, provably |
| `text_repairs` | **§2.4** — 4 verified pairs | **drops nothing**; `predicted` **87** field-level replacements |

**`predicted` ledger: 63 dropped, 463 kept, of 526 raw.**

⚠️ **The repair loop runs over *every* chunk, including the ones about to be dropped**, so
`repairs_applied` describes the book rather than the survivors. Repair 3's ` /g65 ` also fires
inside the dropped bibliography's heading prefix — which is why its 17 is not a multiple of the
8 equations it exists for. **Counted, not derived.**

### 5.8 Three real chunks, verbatim

⭐ *"The only way to see what cleaning actually has to do."*

**(a) A prose chunk carrying repairs 1 and 2 — chunk 66, pp.53–54, 501 tokens, heading
`Enzymes in Malting`:**

> `Most brewers are familiar with the conversion of starch to sugar via enzymatic reactions during the mashing process, but enzymes also play a big role during the malting process. … The continuation of the malting process activates `**`/g95 -amylase`**` and `**`/g96 -amylase`**`. These enzymes break down starches into simpler, unfermentable sugars.`
>
> ```
> | cytase group | degrade the cell wall of the endosperm |
> | amylases     | degrade starch to sugar               |
> ```

Three things at once: the font damage on two enzyme names a brewer would actually search for,
a well-formed markdown table from `table_mode=accurate`, and **no tabs anywhere**.

**(b) The chunk that gets dropped — chunk 301, p.210, 24 tokens, heading `Materials`:**

> `- 3M Attest Biological Indicator capsule (or similar product)`
> `- Autoclave or pressure cooker`

§4.4's accepted loss, shown so the decision is made against the actual text rather than a
description of it.

**(c) The Index chunk that `dropHeading` cannot see — chunk 521, pp.322–323, 359 tokens,
heading `Palmer, John`:**

> `Brewing Classic Styles , 4`
> `How to Brew , 2`
> `Pasteur, Louis, xvi, xvii-xviii, 6, 8, 9, 28…`

⭐ **This one chunk is the argument for §2.3 in a single screen.** Its heading is a person's
name, its body is index entries, and every shared rule in the `book` profile passes it through.
Without `extra_drop_regex` alternative 5, five of these land in the corpus and compete in every
retrieval.

---

## What book 2 unblocks

⭐ **Revised 2026-08-19, after the run.** The three questions below were written before Tier B;
question 3 is now **answered**, and two more were produced by the run itself.

**Book 3 (*Malt*, Mallett, 335 pages) is the same shape and should again be mapper-only** —
README §4 gives it *"table-dense body under `table_mode=accurate`"* as its new capability, and
Yeast already exercised that path on 42 table chunks with no complaint.

⛔ **What book 3 must check, all of it handed over by this plan rather than rediscovered:**

1. ⭐ **Is Malt's front matter set in a working font?** If a second Brewers Publications title
   ships the same broken display font, §0.3's decoder stops being a one-source workaround and
   becomes the right shared-code change. ⭐ **`measured` here that sharpens it:** the residue is
   **13 chunks / 68 glyph tokens**, and **two chunks carry 50 of the 68** (§4.1 A6). A decoder
   justified by *one* book and *two* tables is not justified; a second book showing it is.
2. ⚠️ **Does the token floor take another dozen chunks?** Two books, twelve chunks is a pattern;
   three is a design question, and §4.4 names merge-forward as the fix to build. ⚠️ **The run
   adds a weak data point, not a strong one:** no `Materials` or `Procedure` chunk reached any
   top-6 in ten questions — but none of the ten asks a lab-procedure question, so this shows
   the loss is *invisible to the current question set*, not that it is harmless. ⛔ **Book 3
   should add a procedure-shaped positive control** so the next sighting can be judged.
3. ✅ **Does §4.2c's per-heading concentration repeat? — ANSWERED: no, not in the shape that
   mattered.** `measured` (§4.2c): the maximum concentration on one **(heading, page)** pair is
   **2 of 6** across all ten questions, against Water's Q8 at **4**. A heading-only count *did*
   reach 4 of 6 (Q9, `Flocculation`) but on four different pages carrying four different claims,
   so `PARTITION BY d.id, c.heading_path` would have **deleted three good answers**. ⛔ **Do not
   build it.** ⭐ **Book 3's version of the question is narrower: measure concentration on the
   (`heading_path`, `page_from`) pair and report it for all ten questions.**
4. ⭐ **NEW — state each Tier B question's owning document *before* the run.** §4.2b's Layer-2
   rule flags *"≥ 3 of 6 from one document that does not own it"*, and `measured` here, five of
   the ten questions were resolved by adjudicating ownership as *shared* after seeing the
   results — including Q8, which reads 3 of 6 for *How to Brew* on a question *Yeast* owns.
   **Ownership is the only unmeasured term in the rule.** Declaring it in the plan converts it
   into a prediction that can be wrong.
5. ⭐ **NEW — a compound standing question is won by whichever source covers both halves in one
   chunk.** §4.2a Q4 is the evidence: *Yeast* is deeper on pitching rate **and** on rehydration,
   and lost rank 1 to a Palmer troubleshooting chunk that covers both in plain language, because
   Yeast splits them across pp.142 and 167–169. ⛔ **Do not predict that *Malt* takes Q2**
   (mash pH) on depth alone — check whether one *Malt* chunk answers both halves of the string.

⚠️ **Three items are open at the close of book 2 and book 3 inherits them** (§4.6): **A3 was
never observed** on any book-path launcher since book 0a; **standing rule 4 was broken again**,
one book after README §9 recorded it as broken at book 1; and the orphaned **`Clean +
normalise1`** node is still live, still divergent, still a third copy of the cleaning profile.
⛔ **None is a defect in the corpus. All three are the record, and the record is what this
phase is for.**
