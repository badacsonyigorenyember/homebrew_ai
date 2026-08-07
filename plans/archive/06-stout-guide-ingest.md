# Plan 06 — ingesting `Stout-Style-Guide.pdf`

**Status:** planned, not built. Probe run 2026-08-07 against the live Docling
(`docling-serve 1.19.0`, task `78e2e223`). Every number below is measured from that
probe's 679 chunks, not estimated.

---

## 0. The short answer to "new workflow, or is 01a good enough?"

**Reuse WF1's graph. Do not build a second workflow.** But **01a as written will not
work on this file**, and the reason is not the wiring — it is that three nodes hold
*How to Brew* constants and one node holds *How to Brew* cleaning rules.

| | |
|---|---|
| **Graph shape** (25 nodes, dedup branch, poll loop, embed loop, promote) | ✅ correct as-is, change nothing |
| **Docling call** (§2 of 01a, node 7) | ✅ byte-identical config works — probe confirms it |
| **Node 2 + 6** — hardcoded `how_to_brew_john_palmer.pdf` | ⚠️ must be parameterised |
| **Node 14** `Ensure doc + version` — hardcoded slug/title/authors/filename | ⚠️ must be parameterised |
| **Node 13** `Clean + normalise` — rules tuned to a single-column book | ⛔ **needs real work.** §4 |

So: **one workflow, parameterised, plus a rewritten cleaning node.** The alternative —
duplicating the graph per book — means N copies of a 25-node workflow to fix when a
defect is found. D22 is exactly that story: one bad node hid in one graph for five
days. At a target of ~20 books that approach is untenable.

---

## 1. What the probe found

Submitted with **the exact form fields 01a §2 node 7 already sends** — no changes.
`documents[0].status = success`, **679 chunks in 65 s** (84 pages).

| Metric | *How to Brew* (built) | **Stout guide (probe)** |
|---|---|---|
| pages | 248 | 84 |
| raw chunks | 483 | **679** |
| chunks / page | 1.9 | **8.1** |
| total tokens | 132,333 (kept) | 119,442 (raw) |
| median tokens | 291 | **171** |
| max / over-512 | 524 / 4 | 520 / **1** |
| under-30 | 0 (after cleaning) | **17** |
| chunks with no `page_from` | 0 | **0** ✅ |
| **heading depth** | real hierarchy | **flat — 678 of 679 have exactly one heading** |

**The finding that decides the whole plan:**

| Heading | Count | |
|---|---|---|
| `Step by Step` | 198 | ⛔ |
| `Ingredients` | 195 | ⛔ |
| `Tips for Success:` | 12 | ⛔ |
| recipe names (ALL CAPS, e.g. `ROGUE'S SHAKESPEARE STOUT CLONE`) | 215 | |
| style sections (`AMERICAN STOUT`, `IMPERIAL STOUT`, …) | 26 | |
| **pull-quotes promoted to headings** | 18 | ⛔ |
| masthead / index / other | 14 | ⛔ |

**405 chunks — 60% of the file — are headed `Ingredients` or `Step by Step` and carry
no indication of which recipe they belong to.**

This matters because of §6.2 of the architecture doc: `contextualize()` prepends the
heading path, and `content` (heading + body) is **what gets embedded**. Ingested as-is,
195 chunks would embed as *"Ingredients / 8.8 lbs pale malt, 1.34 lbs flaked oats…"* —
mutually near-identical in vector space, and unfindable by any query naming a beer.
This is not a tuning problem. It is 60% of the document being anonymous.

### 1.1 Why it happens, and why it is fixable

This is a **BYO magazine special issue** — two-column layout, recipe sidebars
interleaved with technique prose. Docling reads it correctly; the magazine simply has
no heading hierarchy to recover. But the recipe blocks are a **perfectly regular
repeating triplet**:

```
idx 79  heading = ROGUE'S SHAKESPEARE STOUT CLONE   (5 gal, all-grain) OG/FG/IBU/SRM/ABV + blurb   92 tok
idx 80  heading = Ingredients                       the grain and hop bill                        182 tok
idx 81  heading = Step by Step                      the procedure                                 288 tok
idx 82  heading = ROGUE'S SHAKESPEARE STOUT CLONE   (5 gal, partial mash) OG/FG/…                  44 tok
```

Every recipe appears twice — an all-grain and an extract/partial-mash variant — which
is why "101 recipes" yields **193 chunks carrying `OG =`/`FG =`/`IBU =`**.

Because the order is regular, the fix is deterministic: **carry the last-seen recipe
name down onto its subsection chunks.** Tested against all 679 real chunks:

> **402 of 406 subsection chunks re-parent cleanly. 4 orphans** (indices 331, 332,
> 334, 335), which fall out under the under-30 rule anyway.

---

## 2. What the probe changes vs. §6.6 of the architecture doc

§6.6 predicted this file was a BJCP-shaped style guide with repeating *style
definitions*, and routed it to **WF2 (structured)** with ~8–12 generated style cards.
**That prediction is wrong, and the file should not go near WF2.**

It is not a style guide in the BJCP sense. It is a magazine: ~7 technique articles by
Jamil Zainasheff and others, plus 101 recipes. There are no numeric style ranges to
parse into `brew.bjcp_styles` — those already live there from WF2, from the actual BJCP
2021 data. Sending this file to WF2 would duplicate style data the corpus already has,
at lower quality.

§6.6's closing rule still holds and in fact *predicts* this outcome — *"if a document
has a regular repeating structure, parse it; only chunk documents that are genuinely
prose."* This file is **both**, so it needs the prose path (WF1) **plus** a structural
repair step for the repeating part. That repair is §4.

**Action:** §6.6 should be corrected once this lands. It is a worked example built on
an assumption about a file nobody had opened.

---

## 3. The workflow changes

### 3.1 Add node 0 — `Book profile` (Set node, right after the trigger)

This is the whole parameterisation. One node, no expressions elsewhere change shape —
they just point here instead of holding literals.

| Field | Value |
|---|---|
| `file_path` | `/data/shared/rag-files/pending/Stout-Style-Guide.pdf` |
| `source_filename` | `Stout-Style-Guide.pdf` |
| `slug` | `byo-stout-style-guide` |
| `title` | `The Best of Brew Your Own: Stout Style Guide` |
| `doc_type` | `article` |
| `authors` | `["Jamil Zainasheff","Terry Foster","Gordon Strong","Michael Tonsmeire","Josh Weikert"]` |
| `edition_note` | `BYO special newsstand issue, 84 pp.` |
| `front_matter_max_page` | `5` |
| `profile` | `byo_magazine` |

**`doc_type = 'article'`, deliberately.** It is honest (a magazine, not a book) and it
buys a lever: `nlq.search_knowledge` still accepts `p_doc_type`, so if §6's risk
materialises you can filter process questions to `doc_type='book'` without re-ingesting.
The tool stopped *passing* that parameter under D26b; the function still supports it.

### 3.2 Change nodes 2 and 6 — `Read PDF for hashing` / `for upload`

File selector becomes `={{ $('Book profile').first().json.file_path }}`.

### 3.3 Change node 14 — `Ensure doc + version`

SQL becomes fully parameterised — no literals:

```sql
WITH d AS (
  INSERT INTO kb.documents (slug, title, doc_type, authors, language, edition_note)
  VALUES ($6, $7, $8, $9::text[], 'en', $10)
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

Query parameters gain `$6`–`$10` from `Book profile`. **Note `$9::text[]`** — pass
authors as a Postgres array literal `{"Jamil Zainasheff","Terry Foster"}`, not JSON.

### 3.4 Everything else is unchanged

Nodes 3, 4, 5, 7–12, 15, 17–25 and the new `Log ingest summary` need **no edits**. They
already reference `$('Ensure doc + version')` and `$('Crypto')` by name and carry no
book constants. That is the payoff for the D14 discipline of threading `version_id` as
a parameter.

---

## 4. The new `Clean + normalise`

> ⚠️ **Superseded in part by §8.1.** The re-parenting design below was the first draft.
> After measuring, **merging each recipe's parts into one chunk is the better option**
> and makes this node *simpler*: a merged chunk starts with its recipe-name heading, so
> the anonymity problem is solved by construction and the re-parenting pass is not
> needed for recipe chunks at all. Read §8.1 before building this. The rules below —
> the drop set, the state tracking, the rebuilt `content` warning — all still apply;
> only the "carry the heading down" step is replaced by "accumulate the parts".

Three changes over 01a §13: different drop rules, a **re-parenting pass**, and a
**rebuilt `content`**. That last one is the easy thing to miss.

> ⚠️ **`content` must be rebuilt, not copied.** 01a sets `content: c.text`, and
> Docling's `text` is *its* heading plus the body. If you change `heading_path` without
> regenerating `content`, the embedding still says "Ingredients" and the whole exercise
> does nothing. `raw_content` stays the body only, so `content_sha256` — computed in
> SQL over `raw_content` — is unaffected and embedding reuse still works.

```js
// ---- Docling result -> cleaned chunks. BYO magazine profile (plan 06 §4) ----
const res = $json;
const doc = (res.documents && res.documents[0]) || null;
if (doc && doc.status && !['success', 'partial_success'].includes(doc.status))
  throw new Error(`Docling documents[0].status = "${doc.status}"`);

const chunks = res.chunks;
if (!Array.isArray(chunks) || chunks.length === 0)
  throw new Error('Docling returned no chunks');

const FRONT_MAX = 5;                       // p6 is the first real chapter opener
const STYLE   = /^(AMERICAN|FOREIGN EXTRA|IMPERIAL|IRISH|OATMEAL|SWEET|SPECIALTY|DRY|MILK|RUSSIAN)\s+STOUT$/i;
const SUBSEC  = new Set(['ingredients', 'step by step', 'tips for success:']);
const PULLQ   = /^['‘“]/;                  // pull-quotes promoted to headings
const JUNK    = /(EDITORIAL|ADVERTISING|SUBSCRIPTION|CONTRIBUTING|PUBLISHER|BOOKKEEPER|WEBSTORE|RECIPE INDEX|TABLE OF|CONTENTS|ART DIRECTOR|DIGITAL EDITOR|TECHNICAL EDITOR|DESIGNER)/i;

const drops = [];
const kept  = [];
let curStyle = null, curRecipe = null;

for (const c of chunks) {
  const pages    = Array.isArray(c.page_numbers) ? c.page_numbers.filter(Number.isFinite) : [];
  const pageFrom = pages.length ? Math.min(...pages) : null;
  const pageTo   = pages.length ? Math.max(...pages) : null;
  const head     = ((c.headings || [])[0] || '').trim();
  const raw      = (c.raw_text ?? '').trim();
  const tokens   = Number.isFinite(c.num_tokens) ? c.num_tokens : null;
  const hasTable = JSON.stringify(c.doc_items ?? []).includes('/tables/');
  const isSub    = SUBSEC.has(head.toLowerCase());

  // --- track section state BEFORE dropping, so a dropped chunk still updates context
  if (STYLE.test(head)) { curStyle = head; curRecipe = null; }
  else if (head && head === head.toUpperCase() && head.length > 8 && !isSub
           && !PULLQ.test(head) && !JUNK.test(head)) { curRecipe = head; }

  const drop = (reason) => drops.push({
    chunk_index: c.chunk_index, reason, page_from: pageFrom,
    heading: head.slice(0, 120), tokens });

  if (!raw)                                        { drop('empty raw_text');        continue; }
  if (pageTo !== null && pageTo <= FRONT_MAX)      { drop('front matter (p1-p5)');  continue; }
  if (JUNK.test(head))                             { drop('masthead/index');        continue; }
  if (PULLQ.test(head))                            { drop('pull-quote heading');    continue; }
  if (tokens !== null && tokens < 30 && !hasTable) { drop('under 30 tokens');       continue; }
  if (/^\s*\d{1,3}\s*$/.test(raw))                 { drop('page-number-only');      continue; }

  // --- re-parent: {STYLE, RECIPE NAME, subsection}, deduped
  const path = [];
  for (const seg of [curStyle, isSub ? curRecipe : null, head]) {
    if (seg && path[path.length - 1] !== seg) path.push(seg);
  }

  kept.push({
    chunk_index:  c.chunk_index,
    content:      path.join(' > ') + '\n' + raw,   // REBUILT — see the warning above
    raw_content:  raw,
    heading_path: path.length ? path : null,
    page_from:    pageFrom,
    page_to:      pageTo,
    token_count:  tokens,
  });
}

if (kept.length === 0) throw new Error('Cleaning removed every chunk - check the rules');

const toks = kept.map(k => k.token_count).filter(Number.isFinite).sort((a, b) => a - b);
const depth = {};
for (const k of kept) { const d = k.heading_path ? k.heading_path.length : 0; depth[d] = (depth[d] || 0) + 1; }

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
    heading_depth:   depth,
    page_count:      Math.max(...kept.map(k => k.page_to ?? 0)),
  },
}}];
```

**`token_count` becomes slightly wrong after re-parenting** — it is Docling's count for
the original `content`, and the new heading path is longer. The drift is ~5–15 tokens on
a 3-segment path. It is metadata, not a constraint, and nothing downstream computes on
it. Left alone deliberately; noting it so it is not "discovered" later.

---

## 5. What the run should produce — acceptance numbers

Simulated by running §4's rules over the probe's real 679 chunks:

| Check | Predicted | Gate |
|---|---|---|
| raw chunks | 679 | — |
| dropped | **54** (36 front matter, 18 pull-quotes) | within ±15 |
| **kept** | **625** | ±10% |
| median tokens | **172** | — |
| under-30 | **0** | must be 0 |
| over-512 | **0** | ≤1% |
| missing heading | **0** | must be 0 |
| missing page | **0** | must be 0 |
| heading depth 3 (fully re-parented) | **402** | ≥390 |
| heading depth 2 | 197 | — |
| heading depth 1 | 26 | — |
| embedding coverage | 625/625 @1024 | must be 100% |
| `kb.ingest_log` rows | **2** | must be 2 — this is D23's first real exercise |

**Runtime estimate:** ~65 s Docling (measured) + 625 ÷ 32 = **20 embedding batches**.
*How to Brew* ran ~2.3 s/batch at median 291 tokens; these are shorter, so budget
**4–7 minutes** end to end. Do not chat with the assistant during the run (§4.5).

### 5.1 Where this fails the standing criterion, and why that is acceptable

Architecture §11's amended rule is *chunk count within ±25% of `body_tokens / 320`, and
median `token_count` between 200 and 450*.

| variant | chunks vs band **280–466** | median vs band **200–450** |
|---|---|---|
| unmerged | 625 — **34% over** | 172 — **below the floor** |
| **merged (§8.1)** | 218 — **22% under** | 491 — **over the ceiling** |

Neither variant satisfies it, and they miss in *opposite* directions — which is itself
the argument that the criterion, not the file, is what does not fit.

**All four misses are the magazine format, not a defect.** That criterion
was calibrated on a single-column 248-page book. A two-column magazine with recipe
sidebars produces 8.1 chunks/page against a book's 1.9. **Do not tune `max_tokens` to
force this into range** — that would re-split *How to Brew* for no reason and change two
variables at once (§10.4).

**Proposal: make the criterion format-aware** rather than weakening it —
`body_tokens / 320` for `doc_type='book'`, and for magazine-format sources record the
number as a baseline without gating on it. Decide this before the run so the result is
not scored against a moving target.

---

## 6. The real risk: corpus balance

This is the thing to watch, and it is bigger than any node in §3.

| | now | unmerged | **merged (§8.1)** |
|---|---|---|---|
| *How to Brew* | 447 | 447 | 447 |
| BJCP style cards | 116 | 116 | 116 |
| **Stout guide** | — | **625** | **218** |
| **total** | 563 | 1,188 | **781** |
| **stout guide's share** | — | **53%** ⛔ | **28%** ✅ |

**Unmerged, the stout guide becomes 53% of the corpus, and ~400 chunks of it — a third
of everything — are recipe ingredient lists and mash procedures.** §8.1's merge is the
mitigation: it cuts recipe *rows* from ~600 to 193 and the share to 28%. The rest of
this section applies either way, but the risk is roughly threefold lower merged.

§11.2 already logged the soft spot in its mild form: on *"what temperature for a single
infusion mash"*, rank 1 was a recipe (`American Pale Ale`, p.180) and the actual
explanation landed at rank 2, because recipe chunks are table-ish and compete well on
FTS for terms like "mash". **This ingest multiplies the recipe population by roughly
100×.** Chunks saying *"Hold the mash at 148 °F (64 °C)"* will be extremely competitive
on exactly the process queries the retrieval gate tests.

That is not a reason to skip the book — 101 stout recipes are genuinely valuable, and
"clone Guinness Foreign Extra" is a question the assistant currently cannot answer at
all. It is a reason to **measure immediately and keep a rollback ready.**

### 6.1 Rollback path — decide before running, not after

One statement, fully cascading:

```sql
-- undo the entire ingest; kb.chunks and kb.chunk_embeddings cascade
DELETE FROM kb.document_versions WHERE id = <version_id>;
```

`kb.documents` row can stay — it is inert without a current version. Nothing else in
the corpus is touched, and *How to Brew*'s fingerprint is unaffected.

### 6.2 The measurement that decides keep-or-roll-back

**Run the five retrieval questions from `plans/02-phase1-retrieval-gate.md` BEFORE the
ingest and save the output.** They were last run 2026-08-02 and the results are in
§11.2, but re-running gives a same-session baseline rather than a five-day-old one.

Then re-run them after. The keep/roll-back rule, stated in advance:

| Outcome | Action |
|---|---|
| The *How to Brew* chunk that ranked 1st still ranks in the top 3 on all five | **Keep.** Log the shift |
| It falls out of the top 6 on **one** question | Keep, log as a defect, revisit in the Phase 3 eval |
| It falls out of the top 6 on **two or more** | **Roll back.** Then re-ingest with `doc_type='article'` filtering, or exclude `Ingredients`/`Step by Step` chunks and keep only recipe headers |

Add one new question the corpus previously could not answer, as the positive control:

> *"What's a good grain bill for a foreign extra stout?"* — must return stout-guide
> recipe chunks, and each must now carry its recipe name in the heading path.

---

## 7. Run procedure

1. **Baseline first.** Run the five gate questions, save output. Record
   `select count(*) from kb.chunks` and the *How to Brew* fingerprint.
2. Build §3.1's `Book profile` node; repoint nodes 2, 6, 14; replace node 13 with §4.
3. **Export the workflow to `n8n/demo-data/workflows/wf1-howtobrew.json` before
   running** — and rename it. `HowToBrew` is now a misnomer for a parameterised
   ingester; `wf1-ingest-book` is honest. (Renaming a workflow does not change its id,
   so nothing else breaks.)
4. **Execute node 7 alone** (`Docling submit`). Expect a `task_id` in under a second.
   The probe proves the config is right, so a failure here means a wiring slip.
5. Full run. Read `Clean + normalise` output and check `stats` against §5 **before
   letting it embed** — if `kept` is far off 625 or `heading_depth[3]` is far off 402,
   stop and fix the rules. Re-embedding 625 chunks is 5 minutes you need not waste.
6. After promotion, verify:

```bash
docker compose exec -T db psql -U postgres -d postgres -c "
select d.slug, count(c.id) chunks,
       count(*) filter (where cardinality(c.heading_path)=3) reparented,
       count(*) filter (where c.heading_path is null) no_heading,
       count(*) filter (where c.page_from is null) no_page,
       count(*) filter (where e.chunk_id is null) missing_embed
from kb.documents d
join kb.document_versions v on v.document_id=d.id and v.is_current
join kb.chunks c on c.version_id=v.id
left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3'
group by 1 order by 1;"
```

7. **Read `kb.ingest_log`** — D23's first real exercise. If it has 2 rows with a
   populated `drops` array, D23 is verified; if it is empty, the node did not fire.
8. Re-run the gate (§6.2) and apply the keep/roll-back rule.
9. Prove idempotency: run again, confirm it stops at `Is new file?` and inserts nothing.
10. Move the PDF to `processed/` by hand (D24 is still unbuilt).

---

## 8. The three open questions — resolved against probe data

All three were measured rather than argued. **Q3's answer reframes the other two**, so
read it first.

### 8.3 → "Does the prose survive?" — it barely exists. ✅ ANSWERED

Composition of the 624 kept chunks, by share of text:

| Content | Chunks | Tokens | Share |
|---|---|---|---|
| recipe subsections (`Ingredients`, `Step by Step`) | 406 | 88,330 | **80.6%** |
| recipe headers (name + OG/FG/IBU/SRM/ABV + blurb) | 193 | 11,190 | **10.2%** |
| technique prose (style-headed) | 24 | 9,746 | 8.9% |
| other prose | 1 | 279 | 0.3% |

> **91% of this file is recipes. The technique prose is 25 chunks, ~10k tokens.**

This is not "a magazine with technique articles plus recipes". It is **a recipe
collection with a thin prose wrapper**. Two consequences worth being blunt about:

- **What you are buying is 101 stout recipes**, not brewing theory. *How to Brew*
  already covers theory better and at 13× the prose volume. Expect this book to answer
  *"give me a foreign extra stout grain bill"* and to add ~nothing to *"what causes
  diacetyl"*.
- The 25 prose chunks are **style-headed and well-formed** (`AMERICAN STOUT`,
  `IMPERIAL STOUT`, …), so they need no repair. Whatever prose exists survives cleanly.

### 8.1 → "Merge the recipe triplet?" — **yes. This reverses §4's first draft.**

Measured by grouping each recipe header with the subsections that follow it:

| | unmerged | **merged** |
|---|---|---|
| stout-guide chunks | 624 | **218** (193 recipes + 25 prose) |
| median tokens | 172 | **491** |
| corpus total | 1,187 | **781** |
| **stout guide's share of corpus** | **53%** | **28%** |

Size distribution of the 193 merged recipes: min 273 · p25 412 · median 491 · p75 588 ·
max 2,016. 57.5% land under 512, 36.3% in 513–768, 5.7% in 769–1024, one outlier.
Shape is regular: **177 of 193 are clean triplets**, 14 have four parts, 2 have more.

Four reasons this is now the recommendation:

1. **It nearly eliminates §6's headline risk.** Recipe *rows* drop from ~600 to 193, so
   the FTS flooding on terms like "mash" drops threefold, and the stout guide stops
   being the majority of the corpus. §6 is the biggest danger in this whole plan and
   merging is the cheapest thing that moves it.
2. **My "don't change two variables" objection was wrong.** Merging *subsumes*
   re-parenting rather than adding to it — a merged chunk begins with its recipe-name
   heading, so the anonymity problem is solved by construction. Merging makes the
   cleaning node **simpler** than §4, not more complex. There is no second variable.
3. **My "worse for *which recipes use flaked oats*" objection was also wrong.** The
   merged chunk still contains the entire ingredient list, so it still matches that
   query — and returns the whole recipe, which is a better answer.
4. **512 was never a storage constraint.** It is the *chunker's* setting; `bge-m3`
   embeds 8,192. Post-processing past it is legitimate.

**One change to §4: cap the merge.** Accumulate parts while the running total stays
under **~900 tokens**, then start a new chunk carrying the same `{STYLE, RECIPE NAME}`
path. That bounds the 2,016-token outlier and the 11 chunks over 768 without touching
the 177 clean triplets. Merged chunk fields: `chunk_index` = the header's (gaps are
already intentional), `page_from`/`page_to` = min/max across parts, `token_count` = sum.

**Cost, stated honestly:** 6 passages × ~490 tokens ≈ 2,900 tokens of retrieved context
per turn, against `numCtx` 12288 and a ~905-token system prompt. Comfortable, but it
roughly doubles retrieval's share of the context budget (§7.5) and should be re-checked
there rather than assumed.

### 8.2 → "A separate `doc_type` for recipes?" — **no, and don't build the lever yet.**

Three findings, the last one decisive:

1. **`doc_type` is the wrong axis.** It is a property of a *document*; this distinction
   is per-*chunk*.
2. **Splitting one file into two `kb.documents` rows is blocked by the schema.**
   `kb.document_versions` carries `UNIQUE (file_sha256)` — two versions cannot share
   file bytes. Working around it by faking a hash would break the dedup guarantee that
   D22's fix depends on. Not a trade worth making.
3. **The information is fully recoverable later, so building it now buys nothing.**
   After merging, a recipe chunk is exactly one whose `heading_path` has two segments
   and whose `content` matches `OG =`. Tagging them later is a single `UPDATE` — **no
   re-chunking and no re-embedding.** That is architecture rule 8 in its literal form:
   the complexity is cheap to add after the measurement and cannot be un-added before it.

**If §6.2's gate fails**, the fix to build is a nullable `kb.chunks.chunk_kind` column
plus an optional `p_chunk_kind` filter on `nlq.search_knowledge` — additive,
non-destructive, ~20 lines, and it composes with the existing `p_doc_type`. Write that
only when a measurement asks for it.

**Still worth raising in the D25 discussion**, but as evidence rather than a question:
this file demonstrates that "recipes from a book" are a third category alongside
`kb` knowledge and `brew` truth, and that the current schema handles them by ignoring
the distinction. That is fine at 193 rows and would not be at 2,000.
