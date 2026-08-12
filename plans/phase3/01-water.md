# Plan 01 — Water: *A Comprehensive Guide for Brewers*, through the existing engine

**Status:** 🟢 **built, Tier-A and Tier-B verified 2026-08-12 · `$5` still open** ·
**Written:** 2026-08-12
**Prereqs:** book 0a's engine and schema (✅ live) · book 0b's styles model (✅ live) · **the
five prerequisite items in §P below**
**Follows:** [`plans/phase3/README.md`](README.md) §6, the per-source plan contract.

> ## ✅ Built 2026-08-12 — every acceptance number in §5.1 hit exactly
>
> | | State |
> |---|---|
> | `ingest-water` built and run | ✅ version 3, `is_current`, **382 chunks, 0 embedding gaps, 1024 dims** |
> | §5.1's gate table | ✅ **every row hit, exactly** — 440 raw → 382 kept, 58 dropped, median 342, max 513, under-30 **0**, missing page/heading **0/0**. §5.5 carries the measured column |
> | §5.2's drop ledger | ✅ **17 / 34 / 4 / 3**, on the exact predicted page ranges |
> | §0.3's tab normalisation | ✅ **0 tabs** in content, raw_content and heading_path — for all three documents (A5) |
> | §1.6's four repairs | ✅ **all four in the stored text, 0 unrepaired** (A6); `repairs_applied` **8** |
> | ⛔ **§P.1 — the repair *ledger*** | ⛔ **still not wired.** Node 26 lacks `$5`, so `detail->'repairs'` is absent on this run too. ⚠️ **But no re-ingest is needed — §6 A2 explains why, and it is a correction to what that section originally said** |
> | ✅ **Tier B** | ✅ **run 2026-08-12 — all 10 questions.** Q1 and Q3 hit their documented ranks exactly · **all 4 positive controls at rank 1** · ⭐ **Layer 2 fires on nothing** — Water is 36% of the corpus and returns **0 of 6** on a style question. §6 carries the tables |
> | ⬜ Tier C | ⬜ not runnable — no WF4, by design (§6) |
>
> ⚠️ **The ingest ran before §P was finished**, so Tier B is a **post-Water** measurement —
> §P.7's Option A, taken by default. Q1 and Q3 still function as the gate because their
> expected results were documented independently, and **both passed unchanged**. What is
> permanently missing is a before/after on Q2, Q4 and Q5; those are now the baseline for
> books 2–9 rather than a comparison for book 1. §P.7 has the recovery option if you want it.
>
> ⛔ **Still open: `$5`** — the Query Parameters pass it, the SQL ignores it. One line, and it
> matters for book 2, not this one (§6 A2).

> ## ⭐ Reset — undo everything this workflow added
>
> **Run this to start over.** It works on a **partial** run as well as a complete one — a
> workflow that died in the embedding loop has already written a `kb.documents` row, a
> `kb.document_versions` row and some of its chunks, and this removes all of it.
>
> ```sql
> DELETE FROM kb.document_versions
> WHERE file_sha256 = '454701ca174d3327625c671f4b1ff452ab4c9c3e6b3174c66408d305f7145c99';
> ```
>
> As one command:
>
> ```bash
> docker exec supabase-db psql -U postgres -d postgres -c "delete from kb.document_versions where file_sha256='454701ca174d3327625c671f4b1ff452ab4c9c3e6b3174c66408d305f7145c99';"
> ```
>
> | | |
> |---|---|
> | **Keyed on** | the Water PDF's SHA-256 — so it cannot touch another document, whatever else is in the corpus |
> | **Cascades** | `kb.chunks` from the version · `kb.chunk_embeddings` from the chunks · `kb.ingest_log` from the version |
> | **Left behind** | ✅ the `kb.documents` row, deliberately. The next run reuses it through `ON CONFLICT (slug) DO UPDATE`; deleting it gains nothing and risks the FK |
> | ⛔ **Cannot undo** | §0.3's shared-code edit to `Clean + normalise`, and any node rename or export. Those are §7 |
>
> **Verify — expected `679 · 0 · 2` after a reset, `1061 · 0 · 3` after a good run:**
>
> ```bash
> docker exec supabase-db psql -U postgres -d postgres -Atc "select count(*) from kb.chunks; select count(*) from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null; select count(*) from kb.document_versions where is_current;"
> ```
>
> Then re-run `ingest-water`. ⚠️ **The dedup branch is keyed on the same hash**, so the reset
> is what makes a re-run possible at all — without it the second run stops at
> `Already ingested`.

> ⓘ **Contract note.** This plan was written against README §6's original nine-section
> skeleton. **§6 was revised on 2026-08-12** to prerequisites → build → reset → testing →
> evidence. Nothing here is missing, it is ordered differently: **§P** is the prerequisites,
> **§2 and §3** are the build, **the box above and §7** are the reset, **§6** is the testing,
> and **§1** is the evidence. Books 2–9 use the new order natively.
>
> ⭐ **n8n expressions in this plan are written without the leading `=`** — paste them
> straight into the expression editor, which supplies it. The one place a `=` appears is
> §P.1, which quotes an exported JSON file, where it is part of the stored value.

**Target, in one line:** *Water* (Palmer & Kaminski, 273 pages) becomes **382 chunks** in
`kb.chunks` through **`wf1-ingest-book` unchanged except for one whitespace line**, driven by a
new **2-node `ingest-water` launcher** — `profile: book`, `authority: reference`,
`doc_type: book`.

> ## ⭐ The headline, before anything else
>
> **This is the book that tests D30's promise — that a new source is one Set node, not a new
> workflow. The promise holds, but not perfectly, and the exception is named here rather than
> buried in §3.**
>
> | | Verdict |
> |---|---|
> | A new workflow | ⛔ **no** |
> | A new cleaning **profile** | ⛔ **no** — `book` fits, unchanged |
> | The launcher's 13-field mapper | ✅ **yes, and that is the whole intended change** |
> | ⚠️ **One line of *shared* cleaning code** | ⚠️ **yes — a tab→space normalisation.** This is **more than the launcher**, so it is stated loudly per your instruction. It is **not** a profile branch and **not** source-specific; it is 3 lines, and it is **provably a no-op on book 0a** (measured: **0 tab characters** in all 447 *How to Brew* chunks). §0.3 argues it and §0.4 gives the zero-change fallback if you would rather not touch shared code at all |
>
> **The split holds.** A 273-page book from a different publisher, produced by a different
> toolchain, needed **zero** new nodes, **zero** new profiles and **zero** schema changes. What
> it needed was five constants and one whitespace rule that How to Brew never exercised because
> How to Brew never had a tab in it.

---

## §P — Prerequisites: close book 0a and 0b first

**Five items, in this order. The order is forced, and item 3 is why.** Item 3 changes the
corpus, so item 4's baseline cannot be taken before it — a baseline measured against a corpus
that item 3 then replaces is a baseline of something that no longer exists.

⛔ **Do not start §8 until all five are ticked.**

### P.0 · What is already true — verified against the live stack 2026-08-12

Re-measured for this plan rather than carried from the prompt or from
[`00b-styles.md`](00b-styles.md). All values **measured**:

| Check | Command | Result |
|---|---|---|
| `kb.chunks` · gaps · `is_current` · dims | the §6 A4 query | **679** · **0** · **2** · **1024** (one distinct value) |
| `kb.documents` | `select slug, doc_type, authority` | `how-to-brew-palmer` `book` `reference` **447** · `bjcp-2021-beer-styles` `style_guide` `guideline` **232** |
| `ref.styles` | the §6 A0 query | **116** · 96 with vitals · 20 without · 30 entry instructions · 1 null commercial examples · **34** categories |
| `kb.ingest_log` | `select stage, level, detail ? 'repairs'` | **4 rows** — styles `parse|warn` + `promote|info`, book `clean|warn` + `promote|info`. ⛔ **`detail ? 'repairs'` is `false` on all four** |
| n8n workflows | `n8n list:workflow` | **3** — `wf1-ingest-book` `NoNCV2mkQEppWP7O`, `ingest-how-to-brew` `BAe1fP1g7ZUsbIaq`, `ingest-bjcp-styles` `Ejf3ESE3SK1XBqe3` |
| ⚠️ `wf1-ingest-book` node count | tracked JSON, connection graph walked | **27**, of which **26 are wired and 1 is an orphan** — `Clean + normalise1`, no incoming and no outgoing connections. §P.5 |
| ⚠️ `Log ingest summary` parameters | tracked JSON | **four** positional parameters, and the `clean` row's `detail` is `jsonb_build_object('stats', $2, 'drops', $3)` — **no `$5`, no `repairs` key**. §P.1 |
| `kb.documents` CHECK constraints | `pg_constraint` | `doc_type ∈ book, style_guide, article, datasheet, note` · `authority ∈ reference, guideline, practitioner` — **`book`/`reference` are both legal** |
| `nlq.search_knowledge` signature | `pg_proc` | `(p_query_text, p_query_embed, p_limit, p_candidates, p_rrf_k, p_model, p_doc_type)` — unchanged, no edit needed for this source |
| Docling · Ollama | `/health` · `ask.sh` | `{"status":"ok"}` · bge-m3 answering at 1024 dims |
| n8n bind mounts | `docker inspect n8n` | `…/shared → /data/shared` ✅ — the container path in §2 is correct |
| ⚠️ `n8n/demo-data/workflows/` | `ls` | **8 JSONs**, four of which describe workflows that do not exist. §P.5 |

**Two things this re-measurement establishes that the rest of the plan depends on:**

- ⛔ **The repair ledger has never been captured, for either source.** `detail ? 'repairs'` is
  false on all four `kb.ingest_log` rows. *How to Brew*'s 2026-08-12 re-ingest was a real
  Docling run and the evidence was still lost. **Water has 4 repairs of its own** (§1.6), and
  it is the next real ingest — so P.1 is genuinely before, not merely first in a list.
- **The `book` cleaning profile is the only one implemented.** `PROFILES` in
  `Clean + normalise` holds exactly one key; `ba_manual` and `byo_magazine` are comments with a
  deliberate throw behind them. Water uses `book`, so nothing there changes.

---

### P.1 · A5 — wire node 26's `$5`, **before any new ingest**

⭐ **Do this first, and do it before Water's ingest rather than after.** *How to Brew* was
genuinely re-ingested on 2026-08-12 — a real Docling run that reproduced 447 chunks with an
identical 36-drop ledger — and `detail->'repairs'` still came back empty. That chance is gone.
Water is the next real ingest, it carries **4 measured repairs** (§1.6), and if `$5` is still
missing when it runs, the same evidence is lost a second time. The only way back is another
ten-minute re-ingest.

**Node:** `wf1-ingest-book` → `Log ingest summary` (Postgres, `executeQuery`).

**1. Query Parameters must read, positionally — five values, not four:**

```
{{ [ $('Ensure doc + version').first().json.version_id, JSON.stringify($('Clean + normalise').first().json.stats), JSON.stringify($('Clean + normalise').first().json.drops), JSON.stringify($json), JSON.stringify($('Clean + normalise').first().json.repairs) ] }}
```

**2. The `clean` row's `detail` must build as three keys, not two:**

```sql
jsonb_build_object('stats', $2::jsonb, 'drops', $3::jsonb, 'repairs', $5::jsonb)
```

⚠️ **`$4` stays where it is.** It is the promote row's payload and the two rows are inserted by
one statement; renumbering to make `repairs` `$4` would silently swap the promote detail into
the clean row. **The new parameter is appended as `$5` precisely so nothing else moves.**

**The repairs themselves are applied and verified in the chunks either way** — §6 A6 greps the
stored text for them. This is the audit trail only: which substitutions fired, and how often,
recoverable months later without re-reading the PDF.

**Read it back after Water's run with:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select r->>'find' find, r->>'replace' replace, r->>'applied' applied from kb.ingest_log, jsonb_array_elements(detail->'repairs') r where stage='clean' order by 1;"
```

**Expected after Water: 4 rows, every `applied` = 2** — one hit in `text`, one in `raw_text`,
per §1.6.

---

### P.2 · A3 — watch the launcher short-circuit, **live**

⚠️ **This cannot be checked retroactively, and that is the whole reason it is a separate item.**
A dedup short-circuit writes **nothing** — no chunks, no `ingest_log` row, no version. The
database therefore cannot tell you whether `ingest-how-to-brew` has ever been run a second
time. It has to be watched.

**Fingerprint before:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

**Then run `ingest-how-to-brew` and watch the canvas.** It must end at **`Already ingested`**
(the NoOp on the false branch of `Is new file?`) **in seconds, not minutes.** The path is
`Read file for hashing → Crypto → Dedup lookup → Is new file? → Already ingested` — five nodes,
no HTTP, no Docling.

**Fingerprint after — must be byte-identical**, same command.

⛔ **If it instead runs a full Docling conversion, stop.** The dedup branch is broken, and Water
would then **silently duplicate** rather than dedup: `Ensure doc + version` would mint a second
version for the same file and you would end up with two copies of the same book competing in
every retrieval, with no error anywhere. Fix it here, where the symptom is visible, not at
book 1 where it is a corpus with two Waters and no obvious cause.

---

### P.3 · ~~The card-format A/B~~ — ✅ **retired 2026-08-12. D32b closed.**

⛔ **Do not run this.** It required three runs of `ingest-bjcp-styles` (A0 → A → B) with a
decision rule fixed in advance. **README §6's revision drops multi-variant sequences**, and
the question was settled by argument instead:

> **Variant B stays.** A0 discards five prose fields including `stylecomparison`; A busts the
> ~3,000-token context budget by 36% (~4,074 for six cards). B is the only variant that is
> both complete and within budget. [README §5.5](README.md#55) carries the full argument and
> **records what is given up:** nobody knows whether the sensory/context *split* helps
> retrieval or merely fails to hurt it. If style questions later retrieve badly, the split is
> the live suspect — re-testing costs two ~3-minute runs, and node 12's three-branch `CASE`
> is deliberately left in place for exactly that.

**Consequence for this plan:** ✅ **the corpus is already in its final styles state**, so
§P.4's baseline no longer has to wait for anything. The forced ordering that P.7 describes
was a consequence of the A/B; with the A/B gone, only P.4's own damage remains.

### P.4 · The Tier B baseline — ⭐ the actual blocker for book 1

**There is no recorded baseline anywhere, and the corpus has changed twice since book 0a.**
Every later source's keep/roll-back rule compares a prior rank-1 chunk against a new one, and
there is no prior. Five commands:

```bash
./scripts/ask.sh "diacetyl rest temperature and timing for lagers"
```
```bash
./scripts/ask.sh "how mash pH affects conversion and how to adjust it"
```
```bash
./scripts/ask.sh "when to add hops for bittering vs aroma"
```
```bash
./scripts/ask.sh "pitching rate and rehydrating dry yeast"
```
```bash
./scripts/ask.sh "my beer tastes of green apple, what causes acetaldehyde and how do I fix it"
```

**For each, record three things:** the rank-1 chunk's **heading and page**, the **on-target
count out of 6**, and the **rank of the first correct hit**.

⛔ **Two of the five are a correctness check on the corpus itself, not just a baseline.** Both
are **measured** values for these exact 447 *How to Brew* chunks:

| | Question | Must return |
|---|---|---|
| **Q1** | diacetyl rest | `10.4 Yeast Starters and Diacetyl Rests`, **p.98**, at **rank 1** |
| **Q3** | hop timing | `Bittering` / `Flavoring` / `Finishing`, **all p.41**, at **ranks 1–3** |

A miss on either means the chunks are not the same chunks — which compares *content* where the
447 count only compares cardinality. **Q2, Q4 and Q5 have no prior: whatever they return is the
baseline.**

**Write the table into [`00b-styles.md`](00b-styles.md) §6**, labelled `measured` with the date,
and tick the row in [README §9](README.md).

---

### P.5 · Housekeeping — two pieces of tracked drift

⚠️ **`wf1-ingest-book` carries an orphaned `Clean + normalise1` node.** Measured: no incoming
connection, no outgoing connection, and **its code differs from the live `Clean + normalise`**.
It is harmless to execution — n8n never reaches it — and that is exactly what makes it
dangerous: it is a **second, divergent copy of the cleaning profile sitting in tracked JSON**,
which is the drift the schema rules forbid. In six weeks nobody will know which one is real.

**Delete it in the UI and re-export**, so the engine is **26 nodes** as documented:

```bash
docker exec n8n n8n export:workflow --id=NoNCV2mkQEppWP7O --pretty --output=/demo-data/workflows/wf1-ingest-book.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-ingest-book.json
```

⚠️ **`n8n/demo-data/workflows/` holds four JSONs describing workflows that do not exist:**
`wf1-howtobrew.json`, `wf2-digestion.json`, `tool-search-brewing-knowledge.json`,
`tool-find-batches.json`. Clear them.

⛔ **But `wf4-chat-agent.json` is moved to `backup/`, not deleted.** It is one of three
surviving copies of **system prompt v3**, which the WF4 build needs **verbatim**. Say where it
went in the commit message — a file that was moved and not recorded is a file that was lost.

---

### P.6 · Exit — §P is finished when

- [ ] node 26 carries `$5` and the `clean` row's `detail` builds `'repairs', $5::jsonb` (P.1)
- [ ] `ingest-how-to-brew` was **watched** ending at `Already ingested` in seconds; the
      `kb.chunks` fingerprint is identical before and after (P.2)
- [x] ~~the A/B~~ — ✅ **retired; D32b closed by argument** in [README §5.5](README.md) (P.3)
- [ ] the 5 standing questions are recorded as the baseline against the winning corpus; **Q1 and
      Q3 hit their expected ranks** (P.4)
- [ ] `wf1-ingest-book` is **26 nodes**, re-exported and committed; the four stale JSONs are
      gone and `wf4-chat-agent.json` is in `backup/` with the move named in the commit (P.5)

---

### P.7 · ⚠️ Water was ingested before §P finished — what that costs, and the two ways out

**Measured 2026-08-12: `ingest-water` ran and succeeded while §P.1, §P.3 and §P.4 were still
open.** Nothing is broken and nothing needs undoing — the corpus is correct and every Tier-A
gate passed (§5.5). But two of the three open items were *ordering* items, so it is worth being
exact about what was lost and what was not.

| Item | Damaged? |
|---|---|
| **P.1 — the repair ledger** | ⚠️ **partially, and recoverably.** `detail->'repairs'` is absent, but `stats.repairs_applied = 8` **is** recorded and §6 A6 proves all four repairs in the stored text. §6 A2 reconstructs the per-pair breakdown from first principles |
| **P.2 — A3 dedup** | ✅ **not damaged.** Still watchable, and §6 A3 now tests it on Water directly |
| **P.3 — the A/B** | ✅ **moot.** Retired 2026-08-12; D32b closed by argument. It can no longer be damaged by ordering |
| ⛔ **P.4 — the baseline** | ⛔ **this is the real casualty.** A pre-Water baseline cannot be taken after Water. The five standing questions can still be run, but their answers are now a **post-Water** baseline |

**What P.4's loss actually costs, precisely.** Less than it first looks:

- **Q1 and Q3 are undamaged as a gate.** Both have documented expected results from an earlier
  measurement — `10.4 Yeast Starters and Diacetyl Rests` p.98 at rank 1, and
  `Bittering`/`Flavoring`/`Finishing` all p.41 at ranks 1–3. Running them now still answers
  *"did Water displace them?"*, which is the question the keep/roll-back rule cares about.
- **Q2, Q4 and Q5 had no prior anyway** — §P.4 says so explicitly. Whatever they return is the
  baseline; it is simply a baseline taken one book later.
- ⛔ **What is genuinely unrecoverable is one specific measurement:** whether Water changed the
  rank-1 chunk on Q2, Q4 or Q5. §6's Tier B predicted Q2 would change document. **That
  prediction is now untestable as a before/after**, and it should be recorded as untested rather
  than quietly dropped.

#### The two ways forward

⭐ **Simpler than it was, now that §P.3's A/B is retired** — there is no longer a corpus
change that the baseline has to wait behind.

| | Option A — **accept it and move on** | Option B — **reset, baseline, re-run** |
|---|---|---|
| Steps | wire `$5` · take the 5 questions as a **post-Water** baseline · run Tier B's positive controls and the Layer-2 check | wire `$5` · run the **reset** (top of this file) · take the **pre-Water** baseline · re-run `ingest-water` · run Tier B before *and* after |
| Cost | **~10 min**, no ingest | **~20 min**, of which ~8 is a re-ingest you must not chat through |
| Buys | nothing books 2–9 need is lost — they regress against the post-Water baseline, which is the corpus they will actually land in | ⭐ a true before/after for Water · ⭐ the repair ledger captured properly · ⭐ §6's prediction that Q2 changes document gets tested rather than abandoned |
| Risk | Water's own regression evidence stays a gap in the record | ⭐ **none worth the name.** The re-ingest is a *known-answer* run: 382 chunks, ledger 17/34/4/3, `repairs_applied` 8 — all measured. Reproducing it is a second fixture confirmation, the way *How to Brew* reproduced 447 twice |

**Recommendation: Option B**, because the reset makes it cheap and the re-ingest is no longer
a gamble — it is a repeat of a measured result. ⛔ **But Option A is a legitimate choice.**
Say so on the record and books 2–9 lose nothing.

⚠️ **Either way, wire `$5` first** — one line, pure gain, and under Option B it is what makes
the re-ingest worth doing at all.

---

## §0 — The one-line verdict

**The engine, unchanged, with a new 2-node launcher — plus one shared whitespace line that this
book is the first to need.**

*Water* is the closest twin in the corpus to the one book already ingested: single-column
running prose, a digitally-produced PDF, 273 pages against 248, the same publisher family, the
same `book` shape. The probe (§1) confirms it: **440 raw chunks, 0 with a missing page, 0 with a
missing heading, median 346 tokens, exactly 1 chunk over 512 and 4 under 30.** There is nothing
here for a new workflow or a new cleaning profile to do.

### 0.1 Per-node verdict

Walked over all 26 wired nodes of `wf1-ingest-book`. Only two rows are not *correct as-is*.

| Node(s) | Verdict | Why |
|---|---|---|
| 1 `Ingest book input` | ✅ **correct as-is** | 13 fields, all of which Water fills |
| 2 `Read file for hashing`, 3 `Crypto`, 4 `Dedup lookup`, 5 `Is new file?`, 6 `Already ingested` | ✅ correct as-is | file-shaped source, so the dedup path applies unchanged |
| 7 `Read file for upload` | ✅ correct as-is | Crypto consumes the binary it hashes (D13/D20), so the file is read twice by design |
| 8 `Docling submit` | ✅ **correct as-is** | `convert_from_formats` is driven by `source_format`; all ten form fields verified against the live service in §1 — `dlparse_v4`, `table_mode=accurate`, no OCR, `max_tokens=512`, bge-m3 tokenizer |
| 9 `Wait 15s`, 10 `Docling poll`, 11 `Assert task finished`, 12 `Docling fetch result` | ✅ correct as-is | conversion took **127 s measured**; the poll loop covers it comfortably |
| 13 `Clean + normalise` | ⚠️ **one shared line** | tab→space normalisation. §0.3, §3 |
| 14 `Ensure doc + version` … 26 `Log ingest summary` | ✅ correct as-is | ⚠️ node 26 needs **§P.1's `$5`**, which is book 0a's open item, not a Water change |
| **`ingest-water` (new, 2 nodes)** | 🆕 **the intended change** | 13 constants. §2 |

### 0.2 What is *not* built, stated so its absence is a decision

| Not built | Why |
|---|---|
| A new workflow | the engine fits; §1 found nothing that needs different processing |
| A new cleaning **profile** | `book` fits unchanged. `dropHeading`, `dropReferences` and `minTokens: 30` all behave correctly on this file — §3.2 shows each firing on real chunks |
| An `extra_drop_regex` rule | ⭐ **measured: none is needed.** All 196 distinct headings were read; the only appendix-shaped one is `Chemistry Glossary and Primer` (16 chunks) and it is **real content that must be kept**. Water is cleaner here than *How to Brew*, which needed `(Metric Conversions\|Recommended Reading)`. **The field is set to the empty string, which the engine already handles** (`EXTRA ? new RegExp(EXTRA) : null`) |
| A schema change | none. `doc_type: book` and `authority: reference` are both already legal values (measured, §P.0) |
| A retrieval change | ⛔ **explicitly not.** §4's Layer-2 check may *fire*; Layer 3 is the designated fix and is built when it fires, not in advance |

### 0.3 ⚠️ The one thing that is more than the launcher — and the argument for it

**Measured: every one of the 440 chunks' `text` contains tab characters. 75,154 tabs against
73,812 spaces — 50.5% of this book's whitespace is tabs.** 330 of 440 chunks carry a tab
*inside a heading*: `Chemistry\tGlossary\tand\tPrimer`, `Malts\tand\tMalt\tColor`.

**Measured, and it changes the argument: tabs cost zero tokens.** A control probe through the
live Docling service — the same sentence submitted twice, once space-separated and once
tab-separated — returned **38 tokens and 183 characters in both cases**. bge-m3's tokenizer
normalises tab to space. So this is **not** a chunk-capacity problem and **not** a meaningful
embedding problem, and any claim that it was would have been a guess.

What it *is*, precisely:

| Cost | Real? |
|---|---|
| Chunk capacity / truncation | ⛔ **no** — measured zero token cost |
| Embedding quality | ⚠️ marginal — the tokenizer normalises it away |
| ⭐ **Citations** | ✅ **yes.** `heading_path` is what `ask.sh` and the future tool render. A citation reading `Water > Chemistry⇥Glossary⇥and⇥Primer` is the string the user sees |
| ⭐ **What the model reads** | ✅ **yes.** `raw_content` goes into the passage verbatim — ~190 tab characters per chunk, in the one place the answer is actually built from |
| ⭐ **Whether `text_repairs` can be written at all** | ✅ **yes, decisively.** §1.6's fourth repair site is `take⇥35⇥batches`. Without normalisation the find string must embed literal tabs; with it, the pair is ordinary readable text. §3.1 |

**Why it goes in shared code rather than the `book` branch.** It is not a fact about books, it
is a fact about whitespace — `ba_manual` and `byo_magazine` would each need the identical rule,
and three copies of one line is the drift §P.5 is cleaning up. It is placed **above** the
repair loop so that `text_repairs` pairs are always written in ordinary spaces, for every
source, forever.

**Why it is safe:** ⭐ **provably a no-op on the regression fixture.** Measured on the live
corpus — **0 of 447 *How to Brew* chunks contain a tab**, in `content`, in `raw_content` or in
`heading_path`; likewise 0 of 232 style cards. A tab→space replacement over a string with no
tabs returns the same string. So re-ingesting *How to Brew* after this edit must still reproduce
447 chunks with identical `content_sha256` values — and §6 A7 is that test, stated so the claim
is checked rather than asserted.

⛔ **It normalises tabs only — never runs of spaces.** Measured: **73 of 447** *How to Brew*
chunks contain a double space, and 290 contain a newline. A general whitespace collapse would
rewrite the fixture and destroy the one known-answer test the whole phase rests on. **Tabs, and
nothing else.**

### 0.4 The zero-change fallback, if you would rather not touch shared code

The plan runs without §0.3, at three costs, all of them stated rather than hidden:

1. `text_repairs`'s fourth pair becomes `["take\t35\tbatches","take\t3-5\tbatches"]` — literal
   tabs inside the JSON string on the launcher. It works (`JSON.parse` decodes `\t`), and it is
   measured to match exactly 1 site. It is also unreadable and will be mistyped by whoever
   touches it next.
2. Citations and passages carry the tabs.
3. Books 2–9 inherit the same decision, un-taken.

**Recommendation: take §0.3.** It is three lines, it is measured as a no-op on the fixture, and
§6 A7 proves that rather than assuming it. But it is your call, and the plan is complete either
way — §3.1 gives both forms of the repair table.

---

## §1 — The probe, run before the plan was written

⭐ **Standing rule 1.** Everything below was measured on **2026-08-12** by submitting the file
to the **live Docling service** with the engine's exact form fields. No number in this plan is
extrapolated from *How to Brew*.

**File:** `shared/rag-files/pending/john_palmer_colin_kaminski-water_a_comprehensive_g.pdf`
— 11,267,854 bytes.
**Container path:** `/data/shared/rag-files/pending/john_palmer_colin_kaminski-water_a_comprehensive_g.pdf`
(⚠️ n8n does not see the host path; the mount is `…/shared → /data/shared`, verified §P.0).
**SHA-256:** `454701ca174d3327625c671f4b1ff452ab4c9c3e6b3174c66408d305f7145c99` — **measured.**
This is the value `Crypto` must produce and the dedup key `kb.document_versions.file_sha256`
will carry.

**The submission — the engine's ten form fields, byte for byte:**

```bash
curl -s -X POST http://localhost:5001/v1/chunk/hybrid/file/async \
  -F "files=@shared/rag-files/pending/john_palmer_colin_kaminski-water_a_comprehensive_g.pdf" \
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

**`documents[0].status`: `success`. `processing_time`: 127.03 s — measured.**

### 1.1 The headline numbers

| Measure | **Measured** | Reads as |
|---|---|---|
| raw chunk count | **440** | vs *How to Brew*'s 483 raw / 447 kept |
| pages covered | **4 – 273** | the whole book; p1–3 carry no extractable text |
| **chunks per page** | **1.61** | prose, not structured. *How to Brew*: 1.95 |
| median `num_tokens` | **346** | ✅ inside §11's 200–450 band |
| **p25 / p75** | **202 / 469** | ✅ the band holds across the interquartile range, not just at the median |
| max / min | **513 / 6** | |
| count **over 512** | **1** | chunk 213, 513 tokens — one token over. Not truncated |
| count **under 30** | **4** | §1.4 lists all four |
| ⭐ **chunks with no `page_from`** | **0** | ⛔ the must-be-0 gate, hit exactly. Citations are safe |
| chunks with no headings | **0** | measured — `heading_path` is never null |
| distinct headings | **196** | §1.3 |
| chunks containing a table | **54** (12.3%) | `table_mode=accurate` produced **54 markdown pipe tables**, all of them well-formed |
| chunks with captions | **0** | measured — figure captions are not separated out by this backend |
| chars per token | **4.191** | vs **4.379** measured on the live 447. Close enough that §5's size predictions are calibrated, not guessed |

**What this table decides:** the file needs no format-specific handling. A source with 0 missing
pages, 0 missing headings, 1 chunk over the band and 4 under it is a source the `book` profile
was written for.

### 1.2 The front-matter page range — ⭐ `front_matter_max_page = 18`

⛔ **This is a fact about Palmer & Kaminski's PDF, not about books.** *How to Brew* uses **6**;
copying it here would leave the table of contents, the list of figures and the acknowledgments
in the corpus. Every chunk on pages 4–18 was read:

| Chunks | Pages | Heading | What it is | Keep? |
|---|---|---|---|---|
| 0, 1 | 4–6 | `John Palmer and Colin Kaminski` | title page, publisher block, CIP data, dedication | ⛔ drop |
| 2 | 7–8 | `Table of Contents` | TOC | ⛔ drop |
| 3 | 8 | `10 Wastewater Treatment in the Brewery` | ⚠️ **still the TOC** — a TOC line promoted to a heading | ⛔ drop |
| 4, 5 | 9–10 | `List of Key Figures, Tables, Sidebars and Illustrations` | front matter | ⛔ drop |
| 6, 7 | 11–12 | `Acknowledgments` | front matter | ⛔ drop |
| 8–16 | 13–17 | `Foreword` | Palmer's foreword — why the book exists, not how brewing works | ⛔ drop |
| **17** | **19** | **`A Whole Book on Brewing Water`** | ⭐ **chapter 1, first sentence of real content** | ✅ **keep** |

**`front_matter_max_page = 18` — the last page before chapter 1.** The rule is
`pageTo <= FRONT_MAX`, and chunks 8–16 span `page_numbers` 13–17, so `pageTo = 17 ≤ 18` catches
them. Chunk 17 starts at page 19 and survives. **Drops exactly 17 chunks and not one more** —
verified by simulation, §3.2.

⚠️ **Chunk 3 is the argument against a heading-only rule.** Its heading is
`10 Wastewater Treatment in the Brewery`, which looks exactly like a real chapter heading and is
in fact a line of the table of contents. No `dropHeading` pattern can distinguish them. The page
range can, and does. This is why `front_matter_max_page` is a per-book constant rather than a
regex.

### 1.3 Top 20 headings by frequency

⭐ Plan 06's entire design turned on this one table. Tabs are shown as spaces here for
readability; **the raw strings contain literal tabs** — §0.3.

| n | Heading | Verdict |
|---|---|---|
| **34** | `Index` | ⛔ **dropped** — `^Index` matches the profile's `dropHeading` |
| **16** | `Chemistry Glossary and Primer` | ✅ ⭐ **KEPT — and this is the near-miss worth naming.** The profile drops `^Glossary`. This heading begins *"Chemistry"*, so it does **not** match, which is correct: it is 16 chunks of real explanatory chemistry, the reference half of the book |
| 9 | `Foreword` | ⛔ dropped by page (§1.2) |
| **9** | `-J. Palmer` | ⚠️ ✅ **kept — see §1.5** |
| 8 | `A Whole Book on Brewing Water` | ✅ chapter 1 |
| 7 | `Residual Alkalinity and the Mash` | ✅ core content |
| 7 | `A Discussion of Malt Acidity and Alkalinity` | ✅ |
| 7 | `Boiling` | ✅ |
| 7 | `Solution` | ✅ ⚠️ worked-example answers — §1.4 |
| 7 | `Water Charge Balance and Carbonate Species Distribution` | ✅ |
| 6 | `Removing Dissolved Solids-Nanofiltration and Reverse Osmosis` | ✅ |
| 5 | `Groundwater` | ✅ |
| 5 | `Water Hardness, Alkalinity , and Milliequivalents` | ✅ ⚠️ note the stray space before the comma — cosmetic, left alone |
| 5 | `A Note About pH Meters and Automatic Temperature Compensation (ATC)` | ✅ |
| 5 | `Acidification of Mashing and Sparging Water` | ✅ |
| 5 | `The Balance of Milliequivalents` | ✅ |
| 5 | `Table 17.` | ✅ a real data table |
| 5 | `Problem` | ✅ ⚠️ worked-example questions — §1.4 |
| 4 | `Overview of Brewing Water Processing` | ✅ |
| 4 | `Equilibrium Constants` | ✅ |
| **4** | `References` | ⛔ **dropped** — `^references$` on the trimmed heading, the profile's `dropReferences` rule |

**Headings matching the profile's `dropHeading` pattern, exhaustively:** `Index` (34) and
`Acknowledgments` (2). **Nothing else.** ⛔ In particular **no bare `Glossary`, no `Contents`, no
`Copyright`, no `About the Author`** — measured across all 196 distinct headings. The `book`
profile is neither too greedy nor too narrow on this file.

### 1.4 The four chunks under 30 tokens — and the one that is a real loss

The profile drops a chunk under 30 tokens **unless it contains a table**. All four, verbatim:

| idx | p. | tok | Heading | `raw_text` | Verdict |
|---|---|---|---|---|---|
| 274 | 158 | 24 | `Source Water Treatment Technologies for the Brewery` | `Figure 28-Rotary Screen at Sierra Nevada Brewery` | ✅ **correct drop** — an orphaned figure caption |
| 317 | 184–185 | 14 | `Boiler and Boiler Feedwater` | `caustic embrittlement.` | ✅ **correct drop** — a two-word sentence fragment |
| 390 | 231 | 23 | `Problem` | `How do you calculate the amount of acid that is equal to X number of milliequivalents?` | ⚠️ **an accepted loss — see below** |
| 439 | 273 | 6 | `Index` | `standards for, 44` | ✅ **never reaches this rule** — the `Index` heading rule fires first, so it counts once, under `front-matter heading` |

⚠️ **Chunk 390 is a worked example's question, and its answer survives without it.** Measured
context:

| idx | p. | tok | Heading | Content |
|---|---|---|---|---|
| 388 | 230 | 129 | `Problem` | *"Suppose you have built up a water recipe using distilled water and want to change the sulf…"* |
| 389 | 230–231 | 478 | `Solution` | *"First, go to Table 17 in Chapter 7 for the contributed ion concentrations…"* |
| **390** | **231** | **23** | **`Problem`** | ⛔ **dropped** — *"How do you calculate the amount of acid that is equal to X number of milliequivalents?"* |
| 391 | 231 | 169 | `Solution` | ✅ kept — *"There are really two problems here: 1. (the basic question above), and 2. …"* |

**Chunk 391 survives and literally refers to *"the basic question above"*, which is now gone.**

**Decision: accept the loss, do not tune the rule.** ⭐ Standing rule 6 — *a criterion that does
not fit gets argued, not tuned*. Three reasons:

1. **The cost is one chunk in 440.** Chunk 391's own first sentence restates the problem —
   *"How do you make a 1 N solution"* — so the topic is still retrievable, only the framing
   sentence is missing.
2. **Lowering `minTokens` is not free and not local.** `minTokens` lives in the shared `book`
   profile. Dropping it to 20 would change *How to Brew*'s ledger — its own token-floor drop is
   1 chunk — and break the 447-chunk fixture that the entire phase's confidence rests on. **A
   one-chunk gain in Water is not worth invalidating the only test with a known answer.**
3. **The fix, if it is ever wanted, is not a threshold.** It is a merge-forward rule — a short
   `Problem` chunk absorbed into the `Solution` that follows it. That is real work in the
   cleaning node, it belongs to whichever book makes it pay, and Water at 1 site does not.

**Recorded here so that it is a decision.** If book 3 (*Malt*) shows the same pattern at scale,
this paragraph is the precedent to reopen.

### 1.5 The `-J. Palmer` heading — 9 chunks that are correct but badly labelled

⚠️ **Measured: chunks 241–249, pages 137–141, all carrying the single heading `-J.\tPalmer`.**
This is a sidebar signature that Docling promoted to a heading, so nine consecutive chunks of
real content are labelled with the author's initials and nothing else.

**Verdict: keep all nine, change nothing.** This is the *anonymity* problem README §1.2
describes for the pastry-stouts file — a chunk whose embedded heading path says nothing about
its subject — and the fix there was to repair the **source file**, which was a markdown file
under our control. This is page 137 of a printed book.

**Why not repair it in the cleaning node:** it would mean inventing a heading, which is
fabrication in the one layer that is supposed to be faithful. **Why not drop it:** ⛔ it is nine
chunks of Palmer's own commentary, and §4's rule is that nothing is dropped for being
inconvenient.

**What it costs, honestly:** those nine chunks retrieve on their body text alone, with a heading
prefix that contributes nothing. They will under-perform. **It is recorded as a known,
measured weakness rather than repaired**, and §6's Tier B is where it would show up.

### 1.6 ⭐ The hyphen probe — standing rule 7, and the draft was wrong in **both** directions

```bash
./scripts/hyphen-probe.sh shared/rag-files/pending/john_palmer_colin_kaminski-water_a_comprehensive_g.pdf
```

**Output: 5 at-risk sites**, and the script's own draft `text_repairs`:

```json
[["5.66.0,","5.6-6.0,"],["(6570°C)","(65-70°C)"],["35","3-5"],["0.0050.010","0.005-0.010"],["5070%","50-70%"]]
```

⛔ **Every pair was then checked against the actual Docling output, and pasting that draft blind
would have failed the ingest in two different ways.** The counts below are occurrences in the
**live probe result**, `text` and `raw_text` separately — measured:

| # | Draft pair | in `text` | in `raw_text` | Verdict |
|---|---|---|---|---|
| 1 | `["5.66.0,","5.6-6.0,"]` | **0** | **0** | ⛔ **matches nothing → the engine throws.** §1.6a |
| 2 | `["(6570°C)","(65-70°C)"]` | 1 | 1 | ✅ **valid, use it** |
| 3 | `["35","3-5"]` | **79** | **79** | ⛔ **catastrophic false positive.** §1.6b |
| 4 | `["0.0050.010","0.005-0.010"]` | 1 | 1 | ✅ **valid, use it** |
| 5 | `["5070%","50-70%"]` | 1 | 1 | ✅ **valid, use it** |

⭐ **And the README's list of Water's at-risk sites is wrong in both directions.** It names
*"pH `5.6-6.0`, `(65-70°C)`, `0.005-0.010`, `50-70%`"*. The first of those **is not at risk**,
and the site that **is** the most dangerous — `3-5 batches` — is not in the list at all. Fix
that line in [README §9](README.md) when this plan is executed.

#### 1.6a Site 1 — Docling kept the hyphen, so there is nothing to repair

**Measured, chunk 121, pp.76–77**, `raw_text` shown with real whitespace:

```
…have a distilled water or congress mash pH of 5.6-\n6.0,  depending on barley variety…
```

**The hyphen survived; the line break became a newline.** `dlparse_v4` did not join this wrap,
so the number reads correctly and the draft's fused form `5.66.0,` never occurs.

⭐ **This is the point of running the probe against the real service rather than trusting the
script.** `hyphen-probe.sh` uses `pdftotext -layout`, which shows where a wrap *could* fuse;
whether Docling actually fuses it is a different question, and here the two disagree. **The
probe's output is a hypothesis; the Docling result is the measurement.**

⛔ **Including this pair would abort the ingest**, and correctly so — `Clean + normalise`
throws on any repair that matches nothing, because a dead pair means either the source changed
or the pair was mistyped. Both are true here in spirit.

Two further sites read `5.6-6.0` cleanly with no wrap at all (chunk 130 p.82, chunk 156 p.99),
so the value is well represented in the corpus regardless.

#### 1.6b Site 3 — `["35","3-5"]` would have corrupted 79 places

**Measured, chunk 250, pp.141–142** — the fusion is real:

> *"…perfect pairing of recipe and water the first time. Typically, it will take **35** batches
> to dial in any recipe."*

The page says **3–5 batches**. But `"35"` occurs **79 times** in this book's text, and a literal
`replaceAll` would rewrite every one of them. The very first occurrence is the copyright page's
Library of Congress classification:

> `TP583.P35 2013` → `TP583.P3-5 2013`

and it goes on through every `35 ppm`, every `135°F`, every page cross-reference.

⛔ **This is a data-corrupting repair disguised as a data-fixing one, and it would be silent** —
no error, no throw, 79 plausible wrong numbers in a book about numbers. **It is exactly what
standing rule 7's *"the output is a draft — read it before pasting"* is warning about**, and it
is the strongest case for that warning yet found.

**The correct pair anchors on the surrounding words**, which makes it unique — measured, exactly
1 occurrence in `text` and 1 in `raw_text`:

```
["take 35 batches", "take 3-5 batches"]
```

⚠️ **This pair only works if §0.3's tab normalisation runs first.** The bytes on disk are
`take\t35\tbatches` — the words are separated by **tabs**, not spaces. Both forms are given in
§3.1.

#### 1.6c A sweep for sites the probe could have missed

Because sites 1 and 3 showed that `pdftotext` and Docling disagree about line joining, the
Docling output was swept independently for the *surviving* pattern — a digit run, a hyphen,
whitespace, another digit run:

**Result: exactly 1 site — chunk 121, the pH range of §1.6a.** No other wrap survived
un-joined, which means the probe's five sites are the complete set: four were joined (three
harmlessly repairable, one dangerous) and one was not.

#### 1.6d The final `text_repairs` — 4 pairs, every one verified

| # | find | replace | Sites | Where | Label |
|---|---|---|---|---|---|
| 1 | `(6570°C)` | `(65-70°C)` | 1 | chunk 122, p.77 — caramel-malt stewing range | measured |
| 2 | `0.0050.010` | `0.005-0.010` | 1 | chunk 339, pp.196–197 — yeast cell diameter in mm | measured |
| 3 | `5070%` | `50-70%` | 1 | chunk 347, pp.201–202 — methane fraction of biogas | measured |
| 4 | `take 35 batches` | `take 3-5 batches` | 1 | chunk 250, pp.141–142 — batches to dial in a recipe | measured |

**Predicted `applied` count per pair: 2** — the engine counts field-level replacements, so one
site in the PDF scores 2 (once in `text`, once in `raw_text`). **Predicted total
`repairs_applied`: 8.**

⚠️ **Repair 1 is the one worth a second look, because chunk 122 is dense with correct ranges**
— `(3-10% moisture)`, `(120-160°F/50-70°C)`, `(195-220°F/90-105°C)`, `(105-160°C)`, `150-158°F`
— all of which Docling preserved intact. Only `(65-70°C)` fused, because only that one wrapped.
The find string includes the parentheses and the degree sign, so it cannot touch the others.

### 1.7 Three real chunks, verbatim

⭐ *"The only way to see what cleaning actually has to do."* Tabs are written `⇥`.

**(a) A prose chunk carrying repair #1 — chunk 122, page 77, 333 tokens, heading `Malts⇥and⇥Malt⇥Color`:**

> `Highly-kilned⇥ malts⇥ are⇥ base⇥ malts⇥ (or⇥ base⇥ malts⇥ that⇥ have⇥ not⇥ been⇥ fully⇥ cured)⇥ that⇥ have⇥ been kilned⇥to⇥a⇥higher⇥color,⇥such⇥as⇥pale⇥ale,⇥Vienna,⇥Munich,⇥and⇥aromatic⇥malts.⇥The⇥highly⇥kilned⇥malts⇥are heated⇥dry⇥(3-10%⇥moisture)⇥at⇥low⇥temperatures⇥(120-160°F/50-70°C)⇥to⇥retain⇥their⇥diastatic⇥enzymes. … These⇥malts⇥are⇥put⇥into⇥a⇥roaster⇥and⇥stewed⇥at⇥the⇥saccharification⇥range⇥of⇥150-158°F⇥`**`(6570°C)`**`⇥until⇥starch⇥conversion⇥takes⇥place⇥inside⇥the⇥husk.`

Three things this one chunk shows at once: the tab problem (§0.3), the surviving correct ranges,
and the single fused one that repair #1 targets.

**(b) A table chunk — chunk 51, page 46, 350 tokens, heading `Table⇥2-Key⇥Brewing⇥Parameters⇥in⇥Water⇥Quality⇥Report⇥for⇥the⇥Source⇥Water`:**

```
| Nitrite as N Nitrite   | Primary     | <1 MCL (as N) <3 MCL (NO 2 ) <3 brewing | Nitrites are a food preservative and as such are poisonous to yeast cells. |
| Silicate               | Secondary   | <25 SMCL <25 brewing                    | Scale former and damaging in boiler systems and membrane systems.         |
| Sodium                 | Unregulated | 0-50 brewing                            | Beer flavor-less is generally better.                                     |
| Sulfate                | Secondary   | <250 SMCL 0-250 brewing                 | Beer flavor-emphasizes hop character and dryness.                         |
```

⭐ **Two findings.** `table_mode=accurate` and `chunking_use_markdown_tables=true` produce
**well-formed markdown**, cell boundaries intact, ranges like `0-250` unbroken. And
**table chunks contain no tabs at all** — the markdown table generator pads with spaces — so
§0.3's normalisation cannot disturb a single one of the 54 tables. ⚠️ The first data row is
promoted into the header position, so the column names are lost on some tables. Cosmetic, and
not repairable from here without inventing headers; recorded, not fixed.

**(c) The chunk that gets dropped — chunk 390, page 231, 23 tokens, heading `Problem`:**

> `How⇥do⇥you⇥calculate⇥the⇥amount⇥of⇥acid⇥that⇥is⇥equal⇥to⇥X⇥number⇥of⇥milliequivalents?`

§1.4's accepted loss, shown so the decision is made against the actual text.

---

## §2 — What changes, node by node

**Two nodes exist that did not before, and one line changes in one that did.**

### 2.1 🆕 `ingest-water` — the new launcher, 2 nodes

Copied from `ingest-how-to-brew` (2 nodes, verified §P.0). Its own name in the workflow list,
its own Run button, its own tracked JSON.

| # | Node | Settings |
|---|---|---|
| 1 | `When clicking 'Execute workflow'` — Manual Trigger | none |
| 2 | `Call 'wf1-ingest-book'` — Execute Sub-workflow (typeVersion 1.3) | **Source** `Database` · **Workflow** `wf1-ingest-book` (`NoNCV2mkQEppWP7O`) · **Mode** `Run once with all items` · ⛔ **Wait for Sub-Workflow Completion ON** |

⚠️ **Wait-for-completion ON is not optional.** Off, the launcher reports success the moment
Docling is handed the file, and a failed ten-minute ingest looks like a green check.

**Workflow Settings:** Execution Order `v1`, Binary Mode `separate` — matching the other two
launchers.

**Do not activate it.** A manual trigger needs no activation.

### 2.2 ⭐ The mapper — the 13 fields, and where each number came from

Because the engine's Execute Workflow Trigger uses **Define using fields below**, node 2 renders
all 13 fields. **This table is the entire book-specific content of this plan.**

| Field | Value | Source of the value |
|---|---|---|
| `file_path` | `/data/shared/rag-files/pending/john_palmer_colin_kaminski-water_a_comprehensive_g.pdf` | the container path; the host path is invisible to n8n (§P.0) |
| `source_format` | `pdf` | drives `convert_from_formats` on node 8 |
| `slug` | `water-comprehensive-guide` | the slug README §6 already uses in its Tier B example — keep it |
| `title` | `Water: A Comprehensive Guide for Brewers` | the book |
| `doc_type` | `book` | legal value, verified §P.0 |
| `authors` | `John Palmer, Colin Kaminski` | |
| `language` | `en` | |
| `edition_note` | `Brewers Publications, 2013` | ⭐ **measured from the CIP block in chunk 0** — `TP583.P35 2013`. Not guessed |
| `authority` | `reference` | legal value, verified §P.0. It is a reference work, not a competition guideline and not practitioner opinion |
| `profile` | `book` | the only implemented profile, and the correct one (§0.2) |
| ⭐ `front_matter_max_page` | **`18`** | ⛔ **§1.2, measured.** ⚠️ **Not 6.** 6 is a fact about *How to Brew*'s PDF |
| ⭐ `extra_drop_regex` | *(empty string)* | ⛔ **§0.2, measured** — all 196 headings read, nothing needs a source-specific rule. The engine handles empty (`EXTRA ? … : null`) |
| ⭐ `text_repairs` | see §3.1 | ⛔ **§1.6, measured against the Docling output.** Not the probe's draft |

⛔ **Three of these thirteen are per-book constants that must never be copied from another
book:** `front_matter_max_page`, `extra_drop_regex`, `text_repairs`. All three are measured in
§1 for this file specifically. The first is the one most likely to be copied by habit.

### 2.3 ⚠️ `wf1-ingest-book` → `Clean + normalise` — the one shared line

**Node 13.** Three lines inserted, above the repair loop. Complete code in §3.

**Why it goes above the repair loop and not below:** so that `text_repairs` pairs are written in
ordinary spaces — for this source and every source after it. §1.6b's fourth pair is the concrete
case: `take 35 batches` instead of `take\t35\tbatches`.

⚠️ **It normalises `headings` as well as `text` and `raw_text`, in the same pass.** Plan 06 §4's
standing warning — *if `heading_path` is modified, `content` must be rebuilt, or the embedding
still carries the old heading and the repair does nothing* — is **live here, not inert**.
Docling's `text` field already contains the heading prefix, so normalising one without the other
would make `heading_path` and `content` disagree. §3 does both in one loop, before anything
reads either. **Keep it that way.**

### 2.4 What does not change — stated so its absence is a decision

⛔ **Node 26 `Log ingest summary` is not changed by this plan.** It needs `$5`, and that is
**§P.1** — book 0a's open item, closed before Water runs, not as part of Water. If it were
listed here it would look like a Water-specific edit, and the next book would wonder whether it
needed one too.

⛔ **No node in the embedding loop changes.** Batch size 32, `keep_alive: -1`, Retry On Fail ON,
`Insert embeddings` Execute Once OFF, `Promote version` Execute Once ON. **382 chunks → 12
batches predicted** (11 full, one of 30).

---

## §3 — The cleaning profile

**No new profile. `book` is used unchanged.** What follows is the complete `Clean + normalise`
code with §0.3's edit applied, ready to paste, and then the drop rules with the §1 number that
motivates each.

### 3.1 The `text_repairs` value, both forms

**✅ With §0.3's normalisation (recommended)** — paste into the launcher's `text_repairs` field:

```json
[["(6570°C)","(65-70°C)"],["0.0050.010","0.005-0.010"],["5070%","50-70%"],["take 35 batches","take 3-5 batches"]]
```

**⚠️ Without it (§0.4's fallback)** — the fourth pair carries literal tabs:

```json
[["(6570°C)","(65-70°C)"],["0.0050.010","0.005-0.010"],["5070%","50-70%"],["take\t35\tbatches","take\t3-5\tbatches"]]
```

⛔ **Do not use both.** With normalisation in place the tab form matches nothing and the engine
throws — which is the rule working, not a bug.

### 3.2 Every drop rule, with the §1 number that motivates it

Simulated by running the profile's rules over the **measured** 440-chunk probe result.

| Rule | Motivated by | **Predicted effect on Water** |
|---|---|---|
| `!raw` — empty `raw_text` | hygiene | **0 chunks** — measured, none are empty |
| `pageTo <= 18` — front matter | **§1.2**, read chunk by chunk | **17 chunks** — title/CIP 2, TOC 2, list of figures 2, acknowledgments 2, foreword 9 |
| `dropHeading` `^(Contents\|Index\|Glossary\|Acknowledg\|Copyright\|About the Author)` | §1.3, all 196 headings read | **34 chunks** — the whole `Index`, pp.240–273. `Acknowledgments` is caught by the page rule first |
| `extraRe` — source-specific | **§0.2** — none needed | **0 chunks**; the rule is not installed |
| `dropReferences` — `^references$` trimmed | §1.3 — `References` ×4 | **4 chunks** — one per chapter that carries a reference list, pp.75, 96, 125, 156 |
| `tokens < 30 && !hasTable` | §1.4, all four read | **3 chunks** — a figure caption, a sentence fragment, and §1.4's accepted loss |
| `^\s*\d{1,3}\s*$` — page-number-only | hygiene | **0 chunks** — measured |
| 🆕 **tab → space** (§0.3) | §1.7a — 75,154 tabs | **drops nothing.** It is a normalisation, not a rule |
| `text_repairs` | **§1.6d** — 4 verified pairs | **drops nothing**; predicted **8 field-level replacements** |

**Predicted ledger: 58 dropped, 382 kept, of 440 raw.**

⚠️ **The repair loop runs over *every* chunk, including the ones about to be dropped**, so the
counts describe the book rather than the survivors. All four of §1.6d's sites are in kept
chunks, so this makes no difference here — but it is why a repair can never be "lost" to a drop
rule, which matters at book 4.

### 3.3 The complete node — paste-ready

⚠️ **Only the block marked `+++ NEW +++` differs from what is live today.** Everything else is
byte-identical to the current `Clean + normalise`, reproduced in full so the node can be pasted
rather than hand-patched.

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

// +++ NEW: whitespace normalisation, plan 01-water.md §0.3 +++
// Water (Palmer & Kaminski) separates ~50% of its words with TAB rather than
// space: 75,154 tabs against 73,812 spaces, measured over the 440-chunk probe,
// and 330 of 440 chunks carry one INSIDE a heading.
//
// Three things this must get right, and one it must not do:
//   * headings are normalised in the SAME pass as text/raw_text. Docling's
//     `text` already carries the heading prefix, so fixing one without the
//     other makes heading_path and content disagree — plan 06 §4's warning,
//     which is LIVE here rather than inert.
//   * it runs ABOVE the repair loop, so text_repairs pairs are written in
//     ordinary spaces for every source, now and later.
//   * TABS ONLY. A general whitespace collapse would rewrite the How to Brew
//     fixture: 73 of its 447 chunks contain a double space and 290 contain a
//     newline (measured). Tabs do not: 0 of 447 (measured), which is why this
//     line is provably a no-op on book 0a.
// Measured cost of NOT doing it: zero tokens — bge-m3 normalises tab to space
// (control probe: same sentence, 38 tokens either way). The cost is in what a
// citation renders and what the model reads, not in the vector.
const untab = (s) => (typeof s === 'string' ? s.replaceAll('\t', ' ') : s);
for (const c of chunks) {
  c.text     = untab(c.text);
  c.raw_text = untab(c.raw_text);
  if (Array.isArray(c.headings)) c.headings = c.headings.map(untab);
}
// +++ END NEW +++

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
let REPAIRS;
const rawRepairs = p.text_repairs ?? [];
if (Array.isArray(rawRepairs)) {
  REPAIRS = rawRepairs;                    // trigger field typed `array`
} else if (typeof rawRepairs === 'string') {
  try {                                    // trigger field typed `string`
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

⚠️ **`token_count` is Docling's pre-repair count** and is not recomputed after normalisation or
repairs. It cannot be: nothing in this node runs the bge-m3 tokenizer. The error is bounded and
tiny — measured, tabs cost 0 tokens, and the four repairs add 4 hyphens across 382 chunks — but
it is stated rather than assumed, because §5 gates on it.

---

## §4 — Overlap scoping (README §3 Layer 1)

**Water overlaps *How to Brew* chapter 15 topically, and ⛔ nothing is dropped.**

### 4.1 The overlap, measured

| | Measured 2026-08-12 |
|---|---|
| *How to Brew* chapter 15 — *Water*, pp.136–150 | **33 chunks** of the live 447 |
| Its headings | `15.1 Reading a Water Report`, `What Kind of Water Do I Need?`, `Chloride (Cl -1 )`, `Sulfate (SO4 -2 )`, `Water Hardness, Alkalinity, and milliEquivalents`, `Water pH`, `15.2 Balancing the Malts and Minerals`, `Table 15 - Water Profiles From Notable Brewing Cities`, `15.3 Residual Alkalinity and Mash pH`, `Determining Bicarbonate Addition to Raise the Mash pH`, `Determining Calcium Additions to Lower the Mash pH`, `Table 16 - Salts for Water Adjustment`, `15.4 Using Salts for Brewing Water Adjustment` |
| Water chapters covering the same ground | `Residual Alkalinity and the Mash` (7), `Sulfate-to-Chloride Ratio` (2), `Water Hardness, Alkalinity , and Milliequivalents` (5), `Acidification of Mashing and Sparging Water` (5), `Adding Sodium Bicarbonate` (4), `Calculating Residual Alkalinity` (1), and ~40 more |
| Elsewhere in *How to Brew* | 4 more chunks mention water in a heading (extract brewing, ch.4) |

**⛔ Expected overlap chunks dropped: 0.**

### 4.2 Why — and this is the rule, not a preference

README §3.2 category **(a), topical overlap: keep unconditionally.** This is the canonical case
the rule was written for, named in the README by these two exact books:

> *Palmer's water chapter and the Palmer/Kaminski book are the 20-page answer and the 273-page
> answer; which is correct depends on the question.*

**Concretely.** *How to Brew* 15.3 gives residual alkalinity in about a page: here is the
formula, here is roughly what to do. *Water* gives it in `Residual Alkalinity and the Mash` (7
chunks), `Refinement of RA` (4), `Introducing Z Residual Alkalinity` (1) and
`Calculating Residual Alkalinity` (1), with charge balances and equilibrium constants.

- A brewer asking *"do I need to treat my water?"* wants the 20-page answer. Drop Palmer's
  chapter and every water question becomes a chemistry lecture.
- A brewer asking *"why does my mash pH not match the prediction?"* wants the 273-page answer.
- ⭐ **And Palmer is a co-author of both.** These are not two competing sources; they are one
  author writing at two depths, deliberately.

**The asymmetry that makes this a rule:** an ingest-time deletion is irreversible and
untargeted; a query-time filter is reversible and per-question. You can always suppress at query
time what you kept; you can never retrieve what you dropped. At a predicted 1,061 chunks,
neither storage nor precision forces the issue.

⛔ **Nothing in this plan may touch Palmer's 33 chapter-15 chunks.** They are book 0a's corpus,
they are a different document, and §6 A1 checks that *How to Brew* still reads **447 | 447 | 0 |
0** after Water lands.

### 4.3 Representational duplication — category (b) — does not occur

The defect README §3.2 forbids is *the same assertion stored twice in two shapes unless one is
derived from the other*. Water introduces no structured table and no generated card; it is prose
chunks only. **There is nothing here to drift against.** Where the two books state the same
number — a Burton water profile, say — they are two authors' renderings of a published analysis,
which is (a).

### 4.4 ⭐ Layer 2 — the first source at which the check can discriminate

This is the point at which README §3.3's **retrieval share** stops being decorative.

| Corpus | Retrieval-share check |
|---|---|
| 1 document (book 0a) | trivially 6/6 from one document — no signal |
| 2 documents (book 0b) | nearly so; a book question returns book chunks |
| **3 documents (here)** | ⭐ **discriminates for the first time** |

**The check, unchanged:** over the 10 Tier B questions, flag any question where **≥ 3 of 6**
results come from **one document that does not own the question**.

**Run it and record it, even if it fires nothing.** A recorded null result is what makes the
first real firing legible.

**Corpus share — expect it, argue it, do not tune it.**

| | Predicted |
|---|---|
| Water chunks | **382** |
| Corpus after | **1,061** (679 + 382) |
| ⚠️ **Water's share** | **36.0%** — crosses README §3.3's **25%** signal |
| Water's share at the projected ~3,200-chunk corpus | **~12%** |

⚠️ **This is the largest single-document share the corpus will ever have, and it is a fact about
having three documents, not about Water being over-represented.** 382 chunks for 273 pages is
1.40 kept chunks per page against *How to Brew*'s 1.80 — Water is if anything **less** densely
chunked. Standing rule 6: **argue it, do not shrink it.**

⛔ **Corpus share is the cheap proxy; retrieval share is the measurement.** Layer 3 — the
per-document cap in `nlq.search_knowledge` — is built **only when Layer 2 fires**, not when the
proxy crosses. Do not pre-emptively build it here.

---

## §5 — Acceptance numbers, predicted before the run

Computed by running §3's rules over §1's **measured** probe output. Every number labelled.

### 5.1 The gate table

| Check | **Predicted** | Label | Gate |
|---|---|---|---|
| raw chunks from Docling | **440** | measured (§1.1) | ±2 — a different count means a different Docling |
| **kept chunks** | **382** | predicted from measured | **±10% → 344–420** |
| dropped, total | **58** | predicted from measured | see 5.2 |
| median tokens | **342** | predicted | ✅ **200–450** |
| p25 / p75 tokens | **198 / 472** | predicted | informational |
| max tokens | **513** | predicted | ≪ bge-m3's 8,192 window; nothing truncated |
| min tokens | **31** | predicted | |
| **under-30 after cleaning** | **0** | predicted | ⛔ **must be 0** |
| over-512 after cleaning | **1** | predicted | documented miss — one token over, §5.3 |
| **missing `page_from`** | **0** | predicted from measured (0 in the raw probe) | ⛔ **must be 0** |
| **missing `heading_path`** | **0** | predicted from measured | ⛔ **must be 0** |
| **embedding coverage** | **382/382** | predicted | ⛔ **100%**, all 1024 dims |
| `kb.ingest_log` rows | **2** | predicted | ⛔ **must be 2** |
| ⭐ `detail->'repairs'` entries | **4**, each `applied` = **2** | predicted (§1.6d) | ⛔ **must be present** — this is §P.1's payoff |
| `repairs_applied` total | **8** | predicted | ⛔ non-zero |
| `is_current` versions, whole corpus | **3** | predicted | exactly 3 |
| `kb.chunks` total | **1,061** | predicted | |
| ⚠️ **corpus share, Water** | **36.0%** | predicted | ⚠️ **over 25% — recorded and argued (§4.4), not acted on** |
| *How to Brew* untouched | **447 \| 447 \| 0 \| 0** | measured today | ⛔ **must be unchanged** |
| style cards untouched | **232** (or 116 if A0/A won §P.3) | measured today | ⛔ unchanged |
| `file_sha256` | `454701ca…145c99` | measured (§1) | ⛔ must match, or the file is not the one probed |

### 5.2 The predicted drop ledger — all 58

⭐ **This is the number to read on the canvas at §8's stop-and-check**, before a single embedding
is computed.

| Reason | Predicted | From |
|---|---|---|
| `front matter (p1-p18)` | **17** | §1.2 |
| `front-matter heading` | **34** | §1.3 — the `Index`, pp.240–273 |
| `chapter References list` | **4** | §1.3 — pp.75, 96, 125, 156 |
| `under 30 tokens, no table` | **3** | §1.4 |
| `empty raw_text` · `page-number-only` · `source-specific heading` | **0 · 0 · 0** | §3.2 |
| **total** | **58** | |

⚠️ **A drop ledger that does not read 17/34/4/3 means something upstream changed** — most likely
`front_matter_max_page` was left at 6, which would move 17 → 2 and leave the TOC in the corpus.
That is the single most likely mistake in this plan and it is visible in one glance at this
table.

### 5.3 The two documented misses

⭐ Standing rule 6 — argued, not tuned.

**1 chunk over 512 tokens (chunk 213, 513 tokens, p.128, `Historical Waters, Treatments, and Styles`).**
It is **one token** over a limit that Docling itself enforced, and bge-m3's window is 8,192
(measured from `/api/tags`), so nothing is truncated. Lowering `chunking_max_tokens` to force it
under would re-chunk the entire book to fix one chunk by one token. **No action.**

**§1.4's chunk 390 — one worked-example question lost to the token floor.** Argued in full at
§1.4: the fix would be a merge-forward rule in shared code, and a one-chunk gain does not buy
invalidating the 447-chunk fixture. **No action, recorded as a known loss.**

### 5.4 Runtime, so a hung run is recognisable as hung

| Stage | Predicted | Basis |
|---|---|---|
| read + hash + dedup | < 5 s | |
| ⭐ **Docling conversion** | **~2–3 min** | ⭐ **measured: 127 s** in §1's probe, same service, same ten fields |
| poll loop overhead | ≤ 15 s | `Wait 15s` granularity |
| clean + normalise + repairs | < 2 s | |
| insert 382 chunks | < 2 s | one `jsonb_to_recordset` statement |
| **embed** | **12 batches, ~4–7 min** | book 0a measured 447 embeddings in 4–8 min (≈0.6–1.1 s/chunk) |
| promote + assert + log | < 2 s | |
| **total** | **~7–11 min** | predicted |

⛔ **Past 20 minutes something is wrong.** Most likely Ollama cold-loading per batch, which means
`keep_alive: -1` has gone missing from `Ollama embed`.

### 5.5 ⭐ Measured — the run of 2026-08-12

**Every row of §5.1 hit, and every one of them exactly rather than within its gate.**

| Check | Predicted | **Measured** | |
|---|---|---|---|
| raw chunks from Docling | 440 | **440** | ✅ exact |
| **kept chunks** | 382 | **382** | ✅ exact, against a ±10% gate |
| dropped | 58 | **58** | ✅ exact |
| drop ledger by reason | 17 / 34 / 4 / 3 | **17 / 34 / 4 / 3** | ✅ exact, and on the predicted page ranges — front matter pp.4–13, Index pp.240–273, References pp.75–156, token floor pp.158–231 |
| median tokens | 342 | **342** | ✅ exact · ✅ inside the 200–450 band |
| max tokens | 513 | **513** | ✅ |
| min tokens | 31 | **31** | ✅ |
| under-30 after cleaning | 0 | **0** | ✅ gate |
| over-512 after cleaning | 1 | **1** | ✅ documented miss, §5.3 |
| missing `page_from` / `heading_path` | 0 / 0 | **0 / 0** | ✅ gate |
| embedding coverage | 382/382 | **382/382**, 1024 dims | ✅ gate |
| `repairs_applied` | 8 | **8** | ✅ — and A6 confirms all four in the text, **0 unrepaired** |
| tabs in content / raw_content / heading_path | 0 / 0 / 0 | **0 / 0 / 0**, all three documents | ✅ §0.3 worked, and A5 shows it disturbed nothing else |
| `kb.ingest_log` rows | 2 | **2** | ✅ |
| ⛔ `detail->'repairs'` entries | 4 | **absent** | ⛔ §P.1 not wired — see §6 A2's correction |
| `is_current` versions | 3 | **3** | ✅ |
| `kb.chunks` total | 1,061 | **1,061** | ✅ |
| *How to Brew* untouched | 447 \| 447 \| 0 \| 0 | **447 \| 447 \| 0 \| 0** | ✅ |
| style cards untouched | 232 | **232** | ✅ |
| ⚠️ `page_count` | 273 | **239** | ⛔ **the prediction was wrong** — §8 step 6 |

**Two things this table establishes beyond Water itself.**

⭐ **The probe-then-plan discipline works, and this is the strongest evidence for it so far.**
Every acceptance number was computed by simulating §3's rules over the measured probe *before*
the workflow existed, and 18 of 19 landed exactly. Not within tolerance — exactly. The one miss
was not a measurement error but a misreading of what a field means (`page_count` is over kept
chunks, not over the book), which is precisely the class of error a stop-and-check catches
cheaply and a post-hoc review does not.

⭐ **D30's split holds on a real second book.** A 273-page volume from a different publisher went
through the engine with **zero new nodes, zero new profiles, zero schema changes** — one Set
node of constants, plus §0.3's three shared whitespace lines, which A5 confirms changed nothing
for either existing document.

---

## §6 — Test cases ⭐

Three tiers. **All required.** Written so they can be handed to you or to the agent and run
without further explanation.

### Tier A — pipeline (SQL, deterministic)

**A1 · rows by document, embedding coverage, null pages and headings** — plan 06 §7.6's query,
unmodified:

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, count(*) chunks, count(e.chunk_id) embedded, count(*) filter (where c.page_from is null) no_page, count(*) filter (where c.heading_path is null or cardinality(c.heading_path)=0) no_heading, min(c.token_count) min_tok, percentile_disc(0.5) within group (order by c.token_count) median_tok, max(c.token_count) max_tok from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' group by d.slug order by 1;"
```

**Expected three rows:**

| slug | chunks | embedded | no_page | no_heading | median_tok |
|---|---|---|---|---|---|
| `bjcp-2021-beer-styles` | 232 *(or 116)* | same | **all** — by design, §00b | 0 | — |
| `how-to-brew-palmer` | **447** | **447** | **0** | **0** | unchanged |
| ⭐ `water-comprehensive-guide` | **382** | **382** | ⛔ **0** | ⛔ **0** | **342** |

⛔ **The `how-to-brew-palmer` row is as important as the Water row.** It is the check that this
ingest touched nothing of book 0a.

**A2 · the log has 2 rows, with a drop ledger *and* a repair ledger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select stage, level, message, jsonb_array_length(detail->'drops') drops, jsonb_array_length(detail->'repairs') repairs, detail->'stats'->>'repairs_applied' applied from kb.ingest_log where version_id=(select id from kb.document_versions where file_sha256='454701ca174d3327625c671f4b1ff452ab4c9c3e6b3174c66408d305f7145c99') order by id;"
```

**Expected:** a `clean | warn` row with `drops = 58`, ⭐ **`repairs = 4`** and `applied = 8`;
and a `promote | info` row.

**Measured 2026-08-12:** `clean | warn`, `drops` **58**, `applied` **8** — and `repairs`
**null**, because §P.1's `$5` was still not wired when this ran. The `clean` row's `detail`
holds exactly two keys, `stats` and `drops`.

#### ⚠️ Correction — a null `repairs` here does **not** justify a re-ingest

This section originally said *"the evidence is lost for the second time — stop and re-ingest"*.
**That was wrong, and the reason matters beyond this book.** Three facts recover the ledger
without touching the corpus:

1. **`stats.repairs_applied = 8` is recorded** — it rides in `$2`, the stats object, which node
   26 already passes. The *total* was never at risk.
2. ⭐ **The engine throws on any pair with `applied === 0`.** The run succeeded, so **all four
   pairs fired at least once.**
3. **Each site scores 2** — once in `text`, once in `raw_text`.

Four pairs, each even and ≥ 2, summing to 8, has exactly one solution: **2 + 2 + 2 + 2.** The
per-pair ledger is therefore fully determined, not lost.

⭐ **And A6 is the stronger evidence anyway** — it greps the four repaired strings out of the
stored chunks and confirms **0 unrepaired**. A ledger says what the cleaner *believed* it did;
A6 says what is actually in the database.

⛔ **`$5` is still required, and §P.1 still stands** — but for the *next* book, not this one.
The reconstruction above works only because Water has four pairs at one site each. *How to
Brew* has **five** pairs and at least one (`4590`) that could plausibly match more than one
site; there the total does not pin the breakdown and only the ledger would. **Wire it before
book 2.**

**A2b · read the drop ledger by reason — the §5.2 table, from the database:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d->>'reason' reason, count(*) n, min((d->>'page_from')::int) p_from, max((d->>'page_from')::int) p_to from kb.ingest_log, jsonb_array_elements(detail->'drops') d where stage='clean' and version_id=(select id from kb.document_versions where file_sha256='454701ca174d3327625c671f4b1ff452ab4c9c3e6b3174c66408d305f7145c99') group by 1 order by 2 desc;"
```

**Expected exactly:** `front-matter heading` **34** (pp.240–273) · `front matter (p1-p18)` **17**
(pp.4–13) · `chapter References list` **4** · `under 30 tokens, no table` **3**.
**Anything else is a rule firing that this plan did not authorise.**

**A2c · read the repair ledger — §P.1's payoff, and the first time it has ever been read:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select r->>'find' find, r->>'replace' replace, (r->>'applied')::int applied from kb.ingest_log, jsonb_array_elements(detail->'repairs') r where stage='clean' order by 1;"
```

**Expected: 4 rows, every `applied` = 2.**

**A3 · idempotency — run `ingest-water` a second time; it must stop at `Is new file?`:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

Run before and after the second execution. ⛔ **Identical both times, and the run must end at
`Already ingested` in seconds** — unlike `ingest-bjcp-styles`, this workflow *does* have a dedup
short-circuit. §P.2 proves the branch works; this proves it works for Water.

**A4 · corpus totals:**

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select 'chunks', count(*)::text from kb.chunks union all select 'gaps', count(*)::text from kb.chunks c left join kb.chunk_embeddings e on e.chunk_id=c.id and e.model='bge-m3' where e.chunk_id is null union all select 'current', count(*)::text from kb.document_versions where is_current union all select 'dims', (select string_agg(distinct vector_dims(embedding)::text,',') from kb.chunk_embeddings);"
```

**Expected:** `chunks 1061` *(or 945 if A0/A won §P.3)* · `gaps 0` · `current 3` · `dims 1024`.
⛔ **One value for `dims`** — two means a second model got in and every comparison downstream is
garbage.

**A5 · the tab normalisation did what §0.3 says, and nothing more:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select d.slug, count(*) filter (where c.content like '%'||chr(9)||'%') content_tab, count(*) filter (where c.raw_content like '%'||chr(9)||'%') raw_tab, count(*) filter (where array_to_string(c.heading_path,'') like '%'||chr(9)||'%') head_tab from kb.chunks c join kb.document_versions v on v.id=c.version_id and v.is_current join kb.documents d on d.id=v.document_id group by 1 order by 1;"
```

**Expected: 0 in every column, for all three documents.** ⛔ A non-zero `head_tab` with a zero
`content_tab` is the specific failure §2.3 warns about — headings and content normalised out of
step.

**A6 · the four repairs are in the stored text, not just in the ledger:**

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select count(*) filter (where position('(65-70°C)' in raw_content)>0) r1, count(*) filter (where position('0.005-0.010' in raw_content)>0) r2, count(*) filter (where position('50-70% of the total' in raw_content)>0) r3, count(*) filter (where position('take 3-5 batches' in raw_content)>0) r4, count(*) filter (where position('take 35 batches' in raw_content)>0) unrepaired from kb.chunks c join kb.document_versions v on v.id=c.version_id join kb.documents d on d.id=v.document_id where d.slug='water-comprehensive-guide';"
```

⚠️ **`position()` rather than `LIKE`** — repair 3's replacement contains a literal `%`, which
`LIKE` would read as a wildcard and silently match almost anything.

**Expected: `1 | 1 | 1 | 1 | 0`.** ⛔ The last column is the one that matters — a non-zero
`unrepaired` means a repair silently did not fire.

**A7 · ⭐ the shared-code edit is a no-op on the fixture — the test that makes §0.3 safe rather
than merely argued.** *How to Brew*'s 447 chunks were produced **before** the tab normalisation
existed. If §0.3 is genuinely a no-op on that file, re-ingesting it must reproduce byte-identical
content.

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks c join kb.document_versions v on v.id=c.version_id join kb.documents d on d.id=v.document_id where d.slug='how-to-brew-palmer';"
```

⭐ **Recorded 2026-08-12, before any change — measured:**

```
8d0d3f19c18bce3b248d684a8846fdad | 447
```

Then, **only if you choose to
re-ingest** *How to Brew* per §7 (which §P.1 makes attractive anyway, since it would also
capture that book's five repairs in the ledger for the first time), the fingerprint must be
identical.

⛔ **This is optional and it is a real ten-minute ingest, so it is a decision.** The cheap
version — comparing the tab counts in A5 — already shows *How to Brew* has no tabs to normalise.
The expensive version proves it. **Recommendation: do it, once, right after §P.1's `$5` lands
and before Water** — it closes A5 for book 0a and validates §0.3 in the same run.

### Tier B — retrieval (`scripts/ask.sh`, deterministic)

⛔ **The baseline comes from §P.4 and must already exist.** If it does not, stop: there is
nothing to regress against and the keep/roll-back rule below has no left-hand side.

**Run the 5 standing questions once more immediately before the ingest** for a same-session
baseline — a baseline from a different session is a different measurement — and again after.

**The keep/roll-back rule, unchanged and restated:**

| Outcome | Action |
|---|---|
| prior rank-1 chunk still top 3 on all five | **keep**, log the shift |
| falls out of top 6 on **one** | keep, log as a defect |
| falls out of top 6 on **two or more** | ⛔ **roll back** (§7) |

⚠️ **Q2 — *"how mash pH affects conversion and how to adjust it"* — is the one at risk**, and it
is worth predicting before the run so the prediction can be wrong on the record. Water has
~20 chunks squarely on mash pH and residual alkalinity, several of them deeper than Palmer's.
**Predicted: Q2's rank-1 chunk changes document.** ⭐ **That is not a failure.** The rule is
about the prior chunk *falling out of the top 3*, not about it staying at rank 1 — a better
answer arriving is the corpus working. Record which, and record that it was predicted.

**Positive controls — 4, each stating the document and the rank it must reach.** Every target
heading below was verified present in §1's probe.

| Question | Must reach | Expected chunk |
|---|---|---|
| *"what sulfate to chloride ratio suits a hoppy pale ale"* | `water-comprehensive-guide` in the **top 3** | `Sulfate-to-Chloride Ratio`, pp.134–135 (2 chunks, measured) |
| *"how do I calculate residual alkalinity"* | `water-comprehensive-guide` in the **top 3** | `Residual Alkalinity and the Mash` (7) / `Calculating Residual Alkalinity` (1) |
| *"how does reverse osmosis remove dissolved solids from brewing water"* | `water-comprehensive-guide` in the **top 3** | `Removing Dissolved Solids-Nanofiltration and Reverse Osmosis`, 6 chunks |
| *"how do I acidify my sparge water"* | `water-comprehensive-guide` in the **top 3** | `Acidification of Mashing and Sparging Water`, 5 chunks |

⭐ **The second one is deliberately a question *How to Brew* can also answer** (`15.3 Residual
Alkalinity and Mash pH`). A top-6 carrying both books is the correct result and the best
evidence §4's keep-both rule was right. Note which documents appear.

**Layer-2 retrieval share** over the **10** questions — 5 standing + 4 positive controls + one
question Water does not own:

```bash
./scripts/ask.sh "what should an Irish Stout taste like"
```

⛔ **Flag any question where ≥ 3 of 6 results come from one document that does not own it.** The
specific thing to watch: **Water flooding the two style questions or the yeast question.**
Record the result **even if nothing fires** — §4.4.

### ⭐ Tier B — **measured 2026-08-12**, all 10 questions

**Run against the live 1,061-chunk corpus** with `scripts/ask.sh`, unfiltered, 6/40/50
defaults untouched. ⚠️ **This is a post-Water measurement** — §P.7's Option A, taken because
a pre-Water baseline is no longer obtainable. Q1 and Q3 still function as the gate because
their expected results were documented independently.

#### The 5 standing questions

| # | Question | Rank-1 chunk | doc | On-target of 6 | Verdict |
|---|---|---|---|---|---|
| **Q1** | diacetyl rest | ⭐ `10.4 Yeast Starters and Diacetyl Rests` **p.98** | how-to-brew | 4 | ✅ **gate passed — exactly the documented expectation** |
| **Q2** | mash pH | `4.2 Water Chemistry Adjustment for Extract Brewing` p.39 | how-to-brew | 6 | ⚠️ see below |
| **Q3** | hop timing | ⭐ `Bittering` / `Flavoring` / `Finishing` **all p.41, ranks 1–3** | how-to-brew | 6 | ✅ **gate passed — exactly the documented expectation** |
| **Q4** | pitching rate | `Symptom: I added the yeast 2 days ago…` p.205 | how-to-brew | 5 | ✅ baseline set |
| **Q5** | acetaldehyde | `Acetaldehyde` p.212 | how-to-brew | 4 | ✅ baseline set |

⛔ **Neither gate moved.** Q1 and Q3 return byte-for-byte what they returned when the corpus
was 447 chunks — Water's 382 chunks did not displace a single one. **The keep rule is
satisfied: keep.**

⚠️ **Q2 is the interesting one, and it falsifies a prediction this plan made.** §6 predicted
*"Water's chunks are deeper on mash pH, so Q2's rank-1 chunk changes document."* **It did
not.** Palmer holds ranks 1, 2 and 4; Water takes 3, 5 and 6:

| | |
|---|---|
| 1 | how-to-brew p.39 `4.2 Water Chemistry Adjustment for Extract Brewing` |
| 2 | how-to-brew p.140 `Water pH` |
| 3 | **water** p.75 `Refinement of RA` |
| 4 | how-to-brew p.134 `14.6 Manipulating the Starch Conversion Rest` |
| 5 | **water** p.63 `Residual Alkalinity and the Mash` |
| 6 | **water** p.74 `Refinement of RA` |

⭐ **This is §4's keep-both rule working exactly as designed, and it is the best evidence in
the plan for it.** One question, one top-6, carrying Palmer's practical framing *and*
Palmer & Kaminski's derivation — the 20-page answer and the 273-page answer side by side,
for the reader to choose between. Dropping either would have made this answer worse.

⚠️ **The rank-1 chunk is arguably the weakest of the six**, though — an *extract brewing*
section answering a mash-conversion question. Not a defect this plan introduced (it was
Palmer's rank-1 before Water landed too), but recorded as a known soft spot.

#### The 4 positive controls — ⭐ all four at **rank 1**, not merely top 3

| Question | Required | **Measured** | |
|---|---|---|---|
| sulfate-to-chloride ratio for a hoppy pale ale | water, top 3 | **rank 1** — `Sulfate-to-Chloride Ratio` p.134 · **6 of 6** from water | ✅ |
| how do I calculate residual alkalinity | water, top 3 | **rank 1** — `Calculating Residual Alkalinity` p.142 · 5 of 6 | ✅ |
| how does reverse osmosis remove dissolved solids | water, top 3 | **rank 1** — `Removing Dissolved Solids-Nanofiltration and Reverse Osmosis` p.164 · 6 of 6 | ✅ |
| how do I acidify my sparge water | water, top 3 | **rank 1** — `Acidification of Mashing and Sparging Water` p.112 · 6 of 6 | ✅ |

**Water answers what it was ingested to answer.** The coverage gap README §4.1 called *"the
largest genuine coverage gap"* is closed.

#### ⭐ Layer 2 — the retrieval-share check, and it fires on **nothing**

The first corpus at which this check can discriminate (§4.4). Rule: flag any question where
**≥ 3 of 6** come from one document **that does not own the question**.

| # | Question | how-to-brew | water | styles | Owner | Fires? |
|---|---|---|---|---|---|---|
| Q1 | diacetyl rest | **6** | 0 | 0 | how-to-brew | ✅ no |
| Q2 | mash pH | 3 | **3** | 0 | ⚠️ shared — both own it | ✅ no |
| Q3 | hop timing | **6** | 0 | 0 | how-to-brew | ✅ no |
| Q4 | pitching rate | **6** | 0 | 0 | how-to-brew | ✅ no |
| Q5 | acetaldehyde | **6** | 0 | 0 | how-to-brew | ✅ no |
| Q6 | sulfate:chloride | 0 | **6** | 0 | water | ✅ no |
| Q7 | residual alkalinity | 1 | **5** | 0 | water | ✅ no |
| Q8 | reverse osmosis | 0 | **6** | 0 | water | ✅ no |
| Q9 | sparge acidification | 0 | **6** | 0 | water | ✅ no |
| **Q10** | **what should an Irish Stout taste like** | 1 | ⭐ **0** | **5** | styles | ✅ **no** |

⛔ **Layer 2 does not fire. Layer 3 is not built.** README §3.3's rule is that the
per-document cap is the designated fix and is built **only** when Layer 2 fires — not when
the corpus-share proxy crosses.

⭐ **Q10 is the measurement that matters, and it is a null result worth writing down.** Water
is **36.0% of the corpus** and returns **0 of 6** on a style question. The 25% corpus-share
signal crossed; the thing that signal is a *proxy for* did not happen. **§4.4's "argue it,
do not tune it" was the right call, and this is the evidence** — had the plan shrunk Water to
satisfy the proxy, it would have removed content to fix a problem that does not exist.

#### Three defects the run exposed

⚠️ **1 · `-J. Palmer` retrieves, exactly as §1.5 predicted it would.** It appears at **rank 4
on Q6** and **rank 4 on Q9**. The chunks are relevant; the citation would read
`Water > -J. Palmer`, which tells the reader nothing about the subject. **Predicted,
confirmed, still not repaired** — the fix would be inventing a heading, which is fabrication
in the layer that must stay faithful. Recorded as a known cost.

⚠️ **2 · ⭐ Q8 spends 5 of its 6 slots on one heading on one page** — four chunks of
`Removing Dissolved Solids-Nanofiltration and Reverse Osmosis` (all p.164) at ranks 1–4, and
a fifth at rank 6. The answer is correct but the top-6 has almost no diversity.

⛔ **Layer 3 as specified would not fix this**, and that is a genuinely new finding.
README §3.3's cheap fix is `row_number() OVER (PARTITION BY d.id …)` — a cap per
**document**. All five of these chunks are the *same* document, so a per-document cap changes
nothing. **The concentration here is intra-document, per-heading.** If this pattern recurs,
the fix is `PARTITION BY d.id, c.heading_path` or similar, and this paragraph is where it was
first seen. **Do not act on one question** — record it and watch books 2 and 3.

⚠️ **3 · Q2's rank-1 is an extract-brewing section** answering an all-grain mash question.
Pre-existing, not introduced here, but it is the one standing question whose top result looks
weaker than its runners-up.

#### What Tier B does **not** establish

⛔ **There is no before/after for Water**, because §P.4's baseline was never taken and Water
is already in the corpus. Q1 and Q3 substitute for it on the two questions that had
documented expectations; **Q2, Q4 and Q5 have no prior and their numbers above are the
baseline for books 2–9.** §P.7's Option B is the only way to recover the missing half, and it
is a judgement call, not a requirement.

### Tier C — agent

⛔ **Not runnable, and this is a decision rather than a skip.** There is no chat agent and no
search tool: **WF4 and `tool-search-brewing-knowledge` are both unbuilt** (README §1.3 items 6
and 7; verified §P.0 — `nlq` holds exactly two functions and n8n holds three workflows, none of
them an agent). Running an agent test against no agent is impossible, not omitted. **Tier C is
not runnable for any source yet.**

**Tier C for Water runs as part of the WF4 build**, and must include these five:

| Type | Question | Pass condition |
|---|---|---|
| new coverage | *"What sulfate-to-chloride ratio should I target for a hoppy pale ale?"* | answers with numbers from Water, **names the source**, every `[S…]` resolves |
| ⛔ **refusal still holds** | *"How much Citra do I have?"* | *"I don't have a tool for that yet"* — ⛔ **the one hard fail, re-run in every plan** |
| citation integrity | any water question | no `[S…]` the tool did not return |
| ⭐ **conflict / depth surfacing** | *"How do I work out residual alkalinity — is Palmer's chapter enough?"* | ⭐ **both books attributed**, both carrying `authority: reference`. This is §4's keep-both rule made visible: the 20-page answer and the 273-page answer, side by side |
| numeric honesty | *"How many batches does it take to dial in a water recipe?"* | says **3–5**, not 35 — ⭐ **the end-to-end proof that §1.6b's repair reached the model**, not just the database |

**`scripts/stress/tier1_routing.py` is not run for this source.** It measures tool routing
against a system prompt, and there is neither. It runs when WF4 is built, where the knowledge
row must read **30/30** and the total must not fall below **73/84**.

---

## §7 — Rollback, stated before the run

⛔ **Do not run any of this without deciding to.** It is written here so it exists before it is
needed, not so it can be run casually. **Nothing below is executed by this plan.**

**Roll back Water entirely**, if §5's gates fail or Tier B says roll back:

```sql
DELETE FROM kb.document_versions
WHERE file_sha256 = '454701ca174d3327625c671f4b1ff452ab4c9c3e6b3174c66408d305f7145c99';
-- kb.chunks cascade; kb.chunk_embeddings cascade from chunks; kb.ingest_log cascades
```

Confirm with A4: `chunks 1061 - 382 = 679` · `gaps 0` · `current 2`.

**Leave `kb.documents` alone.** The row is a name and a slug; the next attempt reuses it through
`ON CONFLICT (slug) DO UPDATE`. Deleting it gains nothing and risks the FK from
`kb.document_versions`.

**Roll back §0.3's shared-code edit**, if A7 shows it is not the no-op this plan claims:

> Remove the `+++ NEW +++` block from `Clean + normalise`, re-export, and switch the launcher's
> `text_repairs` to §3.1's tab-literal form. **No SQL and no re-ingest of any other source** —
> the edit only affects text produced by a run that happens after it.

**A deliberate re-ingest of *How to Brew*** — needed for A7, and for capturing that book's own
five repairs in the ledger for the first time:

```sql
DELETE FROM kb.document_versions
WHERE file_sha256 = (SELECT file_sha256 FROM kb.document_versions v
                     JOIN kb.documents d ON d.id = v.document_id
                     WHERE d.slug = 'how-to-brew-palmer');
```

⚠️ **Then re-run `ingest-how-to-brew`** — 447 chunks, 36 drops, ~10 minutes. ⛔ **Do not run this
before §P.1's `$5` is wired**, or it is the third time the repair ledger is thrown away.

**What needs no rollback:** the PDF and the workflow JSON in git. Every artefact this plan
produces is reproducible from files on disk.

---

## §8 — Run procedure

⛔ **§P's six boxes must all be ticked first.** In particular the standing-question baseline must
exist, or Tier B has nothing to compare against.

⛔ **Do not chat with the assistant during any step** (standing rule 3) — embedding saturates the
GPU.

0. **Baseline, same session.** Re-run §P.4's five questions and record. A baseline from a
   different session is a different measurement.

1. **Verify the source file is the one that was probed:**
   ```bash
   sha256sum "shared/rag-files/pending/john_palmer_colin_kaminski-water_a_comprehensive_g.pdf"
   ```
   ⛔ Must be `454701ca174d3327625c671f4b1ff452ab4c9c3e6b3174c66408d305f7145c99`. If it is not,
   **stop and re-run §1's probe** — every acceptance number in §5 is computed from that file.

2. **Re-run the hyphen probe and read it** (standing rule 7):
   ```bash
   ./scripts/hyphen-probe.sh shared/rag-files/pending/john_palmer_colin_kaminski-water_a_comprehensive_g.pdf
   ```
   ⛔ **Do not paste its draft array.** It emits 5 pairs; §1.6 rejected two of them, one because
   it matches nothing and one because it would corrupt 79 sites. Use §3.1.

3. **Apply §0.3's edit to `Clean + normalise`** (or take §0.4's fallback and skip to 4). Then
   **export and commit the engine before running anything**:
   ```bash
   docker exec n8n n8n export:workflow --id=NoNCV2mkQEppWP7O --pretty --output=/demo-data/workflows/wf1-ingest-book.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-ingest-book.json
   ```

4. **Build `ingest-water`** — §2.1, mapper per §2.2. ⛔ Check `front_matter_max_page` reads
   **18** before saving. It is the field most likely to be left at another book's value.

5. **Export and commit the launcher before its first run** (standing rule 4 — n8n's database is
   not a backup):
   ```bash
   docker exec n8n n8n export:workflow --id=<WATER_ID> --pretty --output=/demo-data/workflows/ingest-water.json && docker exec n8n chown 1000:1000 /demo-data/workflows/ingest-water.json
   ```

6. ⛔ **Run it — and stop before embedding.** Execute `ingest-water`. When it reaches
   **`Clean + normalise`**, open the node's output and read `stats` and `drops` **before** the
   loop starts. GPU time on wrong chunks is the expensive mistake, and it is entirely avoidable
   here:

   | `stats` field | Must read |
   |---|---|
   | `profile` | `book` |
   | `raw_chunks` | **440** |
   | `kept` | **382** |
   | `dropped` | **58** |
   | `repairs_applied` | ⭐ **8** |
   | `median_tokens` | **342** |
   | `under_30` | ⛔ **0** |
   | `missing_page` / `missing_heading` | ⛔ **0 / 0** |
   | `page_count` | **239** |

   ⚠️ **`page_count` is 239, not 273, and the difference is the point.** The field is
   `max(page_to)` over the **kept** chunks, not the page count of the book — and the `Index`
   (pp.240–273) is dropped. **A `page_count` of 273 here would mean the Index survived.** An
   earlier draft of this plan predicted 273 and was wrong about what the field measures.

   ⭐ **And check the drop ledger reads 17 / 34 / 4 / 3 by reason** (§5.2). A `front matter` count
   of 2 rather than 17 means `front_matter_max_page` is still 6.

   ⚠️ **A thrown `text_repairs matched nothing` here is the engine working correctly** — it means
   a pair in §3.1 no longer matches, which means the Docling output changed. Re-probe before
   editing the pair.

7. **Let it finish** — **~7–11 minutes predicted** (§5.4). Past **20 minutes**, something is
   wrong; check `keep_alive: -1` on `Ollama embed`.

8. **Run Tier A: A1, A2, A2b, A2c, A4, A5, A6** and record every number beside its prediction.
   ⭐ **A2c is the one to read out loud** — it is the first time this project has ever seen its
   own repair ledger.

9. **Run Tier B**: the 5 standing questions, the 4 positive controls, and the Layer-2 question.
   Apply the keep/roll-back rule. **Record the retrieval share even if it fires nothing.**

10. **Run A3** — re-run `ingest-water` and confirm it stops at `Already ingested` in seconds with
    an identical fingerprint.

11. **Re-export and commit** both workflow JSONs with the measured numbers in the message. Paste
    §5's table into this file with a **measured** column beside the predicted one, the way
    [`00b-styles.md`](00b-styles.md) §5.4 does.

12. **Move the PDF out of `pending/`.** Unlike `styles.json` there is no re-run path that reads
    it — the dedup key is in the database. ⚠️ **But A3 must run first**, since it needs the file
    at the launcher's path.

13. **Tick book 1's row in [README §9](README.md)**, and fix README §9's closing line: it names
    five at-risk hyphen sites for Water including one that is not at risk and omits the one that
    is (§1.6).

---

## §9 — What this source does to WF4

**WF4 does not exist** (verified §P.0). So this section is a **specification for the build**, not
an edit to a running workflow — the same shape as [`00b-styles.md`](00b-styles.md) §9. Three
concrete items, with the exact text.

### 9.1 ⭐ The de-enumeration edit — README §7.1 says *"at book 1, once"*, and this is book 1

The archived system prompt v3 names the corpus explicitly:

> *"You answer from that brewer's library — John Palmer's How to Brew and the BJCP 2021 Style
> Guidelines — not from your own memory."*

⛔ **That sentence becomes false the moment Water lands**, and a model told its library is two
books is being told the third does not exist. **It must be built as:**

> *"You answer from that brewer's library — a collection of brewing books, style guidelines and
> practitioner articles — not from your own memory."*

⭐ **Written this way from the first keystroke, every source from book 2 to book 9 costs zero
prompt edits.** Enumerating a growing corpus inside a token-budgeted prompt is a maintenance
liability, and README §6.2 measured that this prompt is already at the length where additions
start costing accuracy.

⚠️ **It is a prompt edit, so the rule applies without exception when WF4 is built:** edit the
tracked JSON, `n8n import:workflow`, **re-activate** (import deactivates), restart n8n, run
`scripts/stress/tier1_routing.py`, and **read the knowledge row first**. v3.1 looked strictly
safer than v3 and scored 20 points worse. Do not eyeball it.

### 9.2 The tool's passage header — `authority` still surfaces, still never ranks

After this source the corpus holds **two `reference` documents and one `guideline`**. ⭐ **This
is the first time `authority` cannot distinguish two sources that disagree**, because *How to
Brew* and *Water* are both `reference` — and they are the pair most likely to differ in depth on
the same question.

**The consequence for the header formatter:** the passage header must carry **`doc_slug` and
`page_from` as well as `authority`**, or the model cannot attribute two `reference` passages
apart. `nlq.search_knowledge` already returns all three (signature verified §P.0), so this is a
formatting requirement, not a schema one. It should let the model write:

> *"Palmer's How to Brew gives residual alkalinity as a single formula (p.143); Palmer and
> Kaminski's Water derives it from the charge balance (pp.98–104)."*

⛔ **`authority` must never enter ranking**, in the tool or in the SQL. Ranking by authority
suppresses the disagreement the design exists to surface, and does it invisibly — you would
never see the passage that lost. It is the rule most likely to be violated later in good faith
(*"Water is the specialist, boost it for water questions"*), and §4.4's Layer-3 cap is the
sanctioned fix if concentration ever becomes a real problem.

### 9.3 What does not change

`numCtx` 12288, top-6, `contextWindowLength` 6, the citation contract, the personal-scope refusal
sentence: **all unchanged.** Corpus size does not enter the context budget — six chunks is six
chunks whether the corpus is 679 or 3,200. Water's median chunk is **342 tokens predicted**,
close to *How to Brew*'s, so six-chunks-in-context is unchanged too.

---

## Exit — book 1 is done when

- [ ] §P's six boxes are all ticked — **including the standing-question baseline**, without which
      Tier B is meaningless
- [ ] `ingest-water` exists, 2 nodes, Wait-for-completion ON, all 13 mapper fields filled,
      `front_matter_max_page = 18`, exported and committed **before** its first run
- [ ] the run's `stats` read **440 raw → 382 kept, 58 dropped, 8 repairs applied**, and the drop
      ledger reads **17 / 34 / 4 / 3** by reason
- [ ] ⭐ `kb.ingest_log` carries **4 repair entries, every `applied` = 2** — the first repair
      ledger this project has ever recorded (A2c)
- [ ] A1 reads **382 | 382 | 0 | 0** for Water and ⛔ **447 | 447 | 0 | 0** for *How to Brew*
- [ ] A5 reads **0 tabs** in content, raw_content and heading_path, for all three documents
- [ ] A6 shows all four repairs in the stored text and ⛔ **0 unrepaired**
- [ ] A3 stops at `Already ingested` in seconds with an identical fingerprint
- [ ] the 5 standing questions pass the keep rule against §8 step 0's baseline; any shift logged,
      including the predicted Q2 change
- [ ] all 4 positive controls reach the top 3 in `water-comprehensive-guide`
- [ ] ⭐ the Layer-2 retrieval share is **recorded for all 10 questions, including the null
      result** — the first corpus at which the check can discriminate
- [ ] corpus share is **recorded at 36.0% and argued, not tuned** (§4.4)
- [ ] both workflow JSONs re-exported and committed with the measured numbers in the message
- [ ] README §9's book 1 row ticked, and its hyphen-site sentence corrected (§1.6)

**What book 1 unblocks:** books 2 and 3 (*Yeast*, *Malt*) are the same shape and should cost
almost nothing — new launcher, new constants, no engine change at all. ⛔ **If either needs more
than its mapper, the parameterisation is broken and that is the finding**, which is exactly why
README §4.1 puts three books of one shape in a row.
