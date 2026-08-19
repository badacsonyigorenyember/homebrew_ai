# Phase 3 — the corpus, rebuilt one source at a time

**Status:** 🟢 **0a, 0b, 1 and 2 built and Tier-B verified · the agent scheduled at book 4.5
(§4.2) ·** ⭐ **book 3 (Malt) built, run and Tier-A/Tier-B verified — 340 chunks** ·
**Written:** 2026-08-07 · **§6 contract revised 2026-08-12 · agent timing set 2026-08-12 ·
book 2's record closed 2026-08-19 · ⭐ book 3 run and closed 2026-08-19**
**Prereqs:** none for 0a. Books 0b–9 need 0a's schema and engine, both of which now exist.

> ## 🟢 Where the corpus actually stands — measured 2026-08-19
>
> | | Measured |
> |---|---|
> | `kb.chunks` | ⭐ **1,864** — *How to Brew* **447** (24.0%) · **Yeast 463** (24.8%) · **Water 382** (20.5%) · ⭐ **Malt 340** (18.2%) · BJCP style cards **232** (12.4%) |
> | ⭐ **corpus share** | ⭐ **no document is above 25%** — for the first time since book 0b |
> | embedding gaps · dims · `is_current` versions | **0** · **1024** (one value) · ⭐ **5** |
> | `page_count` per book | Yeast **305** · How to Brew **248** · Water **239** · ⭐ **Malt 262** |
> | `ref.styles` | **116** BJCP 2021 rows · 96 with vitals · 20 without · 30 entry instructions |
> | n8n workflows | ⚠️ **7** — `wf1-ingest-book`, `ingest-how-to-brew`, `ingest-bjcp-styles`, `ingest-water`, `ingest-yeast`, and ⛔ ⭐ **two named `ingest-malt`** (`hpW9P0n7fxXY9KdF`, which ran; `ingestMalt00001A`, which never did). ⛔ **None is an agent or a tool** — Tier C still not runnable |
>
> ⭐ **Probe-then-plan has now been tested three times and it is still getting *more* accurate.**
> Book 1: **18 of 19** acceptance numbers exact. ⭐ **Book 2: 21 of 21** — 526 raw → 463 kept,
> drop ledger 27/21/15 by reason, median 313, `page_count` 305, `repairs_applied` 87, corpus
> total 1,524, every one of them derived from a §5 probe before the run. That is the strongest
> evidence yet for §6's probe-then-plan rule, and for D30's engine split: two books from two
> other publishers needed **zero** new nodes, **zero** new profiles and **zero** schema
> changes, and book 2 needed **zero shared-code edits** as well.
>
> ⭐ **Book 3: 30 of 30** — 458 raw → **340 kept**, drop ledger **62 / 29 / 12 / 8 / 7**, median
> **339**, p25/p75 **160 / 482**, min/max **44 / 517**, `page_count` **262**, `repairs_applied`
> **4**, corpus **1,864**, and A7's residue counts **5 / 7 / 1 / 262**. ⛔ **Not one needed a
> tolerance and not one prediction in the plan was falsified.** ⭐ **The runtime estimate held
> too — `predicted` ~3 min, `measured` 3 min 02 s** — which is the first time that number has
> been right, because it was derived from book 2's execution record instead of inherited as
> prose.
>
> ⚠️ **Where the accuracy stops, stated so it is not over-read.** Book 2's two wrong
> predictions were both *outside* the gate table and both were arithmetic rather than
> pipeline: a `text_repairs` check that counted **sites** and asserted **rows**, and a glyph
> residue counted on the wrong field. **A number derived from the probe by simulation held
> every time; a number written by hand next to one did not.**
>
> ⭐ **New since the last revision — book 2's record is closed and book 3 is planned and armed:**
>
> | | |
> |---|---|
> | ⭐ ✅ **Book 3 built, run and closed** | [`03-malt.md`](03-malt.md) — probed 2026-08-19 (**458 raw, 160.85 s**), ingested the same day (**3 min 02 s**, executions 248/249), **340 chunks**. ⭐ **Thirty predicted numbers, thirty exact.** Tier B **keep** — all five prior rank-1 chunks still at **rank 1**, Q1–Q5 **byte-identical** to the post-Yeast baseline, all **5** controls at rank 1. ⭐ **Mapper-only: zero new nodes, zero new profiles, zero schema changes, zero shared-code edits** — the third book in a row |
> | ⭐ ⛔ **The epigraph-heading defect retrieved — it is no longer cosmetic** | Water's `-J. Palmer` was recorded as a known cost. `measured` at book 3: `-Bill Simpson` reaches **rank 3 on Q8** and **rank 6 on Q6**, `-William Littell Tizard…` **rank 4 on Q10**. ⭐ **Three documents, and for the first time it retrieves on questions the source *owns*** — a correct Mallett passage cited to the author of the chapter's epigraph. ⛔ **Fix it at book 4**, which is already editing the cleaning node |
> | ⭐ ✅ **Ownership declared before the run — Layer 2's last unmeasured term** | [`02-yeast.md`](02-yeast.md) §4.2b complained that five of book 2's ten questions were resolved by adjudicating ownership **after** seeing the results. Book 3 declared all **11** in the plan. `measured`: ⭐ **zero post-hoc adjudications were needed.** The rule is now a measurement rather than a judgement |
> | ⚠️ **Layer 2 fires on nothing, a third time — and the corpus-share proxy is 0 for 3** | books 1 and 2 **crossed** 25% and took 0 of 6 on the style question; ⭐ **book 3 does not cross it, takes 0 of 6 anyway, and puts the whole corpus back under the line.** ⛔ **Corpus share has predicted retrieval share three times and been wrong three times.** Argued, not deleted (standing rule 6) — the case it was written for is still ahead at book 5 |
> | ⭐ ✅ **Standing rule 4 kept, for the first time** | `ingest-malt.json` was exported from n8n and **committed before any execution of it existed** (`a9bcefb`). Broken at book 1, broken again at book 2 — ⭐ **book 3 is the first book where the launcher was in git before it was in a run** |
> | ⭐ ⛔ **`hyphen-probe.sh` has a false-negative bug, found at book 3** | [`03-malt.md`](03-malt.md) §5.6 — Docling normalises en dashes to ASCII **after** joining a wrap, so an en-dashed numeric range that wraps is **invisible** to the script and **fused** by Docling. `measured`: the probe returned `0 at-risk site(s)` while two real fusions sit in kept text — `212220°F` (p.256) and `5565°F` (p.259). ⛔ **The first of three books where the draft failed *silently*.** Fix is one character class, `[-‐–—]$`; handed to book 4 |
> | ⭐ ⛔ **The glyph decoder is closed by measurement** | [`02-yeast.md`](02-yeast.md) §0.3 set the test: *"if a second Brewers Publications title ships the same broken display font, build it."* `measured` at book 3 — **it does not.** *Malt* is Brewers Publications 2014 and has **0** glyph runs in 458 chunks. **The `+17` offset was a property of one PDF's font subset, as argued** |
> | ⭐ ✅ **Book 1's untab edit is confirmed *necessary*, not merely safe** | book 2 proved it a provable no-op (0 tabs). ⭐ Book 3 proves it load-bearing: *Malt* carries **147,910** tabs — **twice Water's, and more tabs than spaces** — with **296 of 458** chunks carrying one **inside a heading**. Without it, 296 citations would render `-Bill\tSimpson` |
> | ⭐ ⛔ **Merge-forward is decided against, and book 2 named the wrong fix** | [`02-yeast.md`](02-yeast.md) §4.4 said *"if Malt shows it again, build merge-forward."* `measured`: Malt's token floor takes **7**, and **0** are severed prerequisites — all 7 are **sentence tails** sharing the preceding chunk's heading, which merge-forward would not fix and merge-**backward** would. ⭐ **Two problems were being counted as one.** [`03-malt.md`](03-malt.md) §0.2 |
> | ⭐ ✅ **Book 2 built, run and closed** | [`02-yeast.md`](02-yeast.md) — ingested 2026-08-12, record closed 2026-08-19. **526 raw → 463 kept**, and ⭐ **every one of §4.0's twenty-one predicted numbers hit exactly** — the drop ledger by reason (27/21/15), median 313, `page_count` 305, `repairs_applied` 87, corpus total 1,524. Book 1 landed 18 of 19; **book 2 landed all of them.** ⭐ **Mapper-only: zero new nodes, zero new profiles, zero schema changes and — unlike book 1 — zero shared-code edits.** §4's *"should be near-free"* prediction holds a second time |
> | ⭐ ✅ **The repair ledger records, per pair** | `kb.ingest_log`'s `clean` row carries `repairs` `54 / 17 / 10 / 6`, matching [`02-yeast.md`](02-yeast.md) §2.4 pair for pair. **`$5` is passed *and stored*.** The asymmetry is what makes it a real test — a total could not have produced those four numbers. ⚠️ **One observation on one book**; book 3 re-reads it rather than assuming it |
> | ✅ **Tier B at four documents — Layer 2 fires on nothing, again** | **keep**: all five prior rank-1 chunks still top 3, **all four positive controls at rank 1**, Q2 and Q3 byte-identical to the post-Water baseline. ⭐ **Yeast is 30.4% of the corpus and returns 0 of 6 on the style question** — the second document to cross the 25% proxy without touching a question it does not own |
> | ⭐ **The agent has a date: book 4.5** | §4.2 — `tool-search-brewing-knowledge` + WF4 + `mem.chat_turns` logging, built **after book 4 and before book 5**, which is where cross-source disagreement first exists. ⛔ **This is what closes the *"Tier C — not runnable"* line that every plan so far ends on** |
>
> ⛔ **Three things book 2 did *not* close, all of them hygiene and all of them repeats:**
>
> | Open | Why it still matters |
> |---|---|
> | ⛔ **A3 — the dedup short-circuit — has still never been observed on a book launcher since book 0a** | it writes nothing, so it cannot be checked after the fact. `measured`: `ingest-yeast` has exactly **one** execution. ⚠️ Book 1's attempt (executions 244/245) was launched **86 s before the first run committed**, so it ran the full path instead — and finished with status **`success`** having promoted nothing. **Run A3 as the last step of book 3's session** |
> | ✅ ⭐ **Standing rule 4 — CLOSED at book 3** | broken at book 1, broken again at book 2. ⭐ **`ingest-malt.json` was exported and committed before its first run**, which is the property the rule exists for and the first time it has held |
> | ⛔ **The orphaned `Clean + normalise1` node is still live — and now we know why it keeps surviving** | `measured` 2026-08-19: `wf1-ingest-book` is **27 nodes** in both the live workflow and the tracked JSON, still unconnected, still **without** the untab fix. ⭐ **Book 3 established the cause: there is no n8n CLI command that edits a node** — only `export`/`import`/`list`/`publish`/`execute`/`audit` — and importing over the engine is a second variable in a run. ⛔ **It is a UI action and it has to be done by hand.** [`03-malt.md`](03-malt.md) §1.2 |
>
> ✅ **Closed since the last revision:** D32b (the card format — variant B, by argument,
> §5.5) and the A/B protocol itself, which §6's revision retires.

**This is the only live plan.** Everything before it is in
[`plans/archive/`](../archive/README.md), indexed by what is still true.

> ## 🔴 D33 — full reset, executed 2026-08-07
>
> **Decision (yours, 2026-08-07): purge the database and the workflows, and rebuild from
> zero against a schema designed for the whole corpus rather than for two documents.**
>
> This was **executed, not planned.** State as of now:
>
> | | Before | After |
> |---|---|---|
> | `kb` · `brew` · `mem` · `nlq` schemas | 563 chunks, 563 embeddings, 116 styles | ⛔ **dropped** |
> | `public.n8n_chat_histories` | chat memory | ⛔ dropped |
> | n8n workflows | 5 (`HowToBrew`, `Digestion`, `chat-agent`, 2 tools) | ⛔ **0** |
> | n8n credentials | 3 | ✅ **kept** — `Postgres account`, `n8n_agent`, `Ollama account` |
> | DB roles `n8n_agent` / `agent_ro` / `mem_writer` | exist | ✅ kept (cluster-level; `50_roles.sql` re-grants) |
> | Extensions `vector` / `pg_trgm` / `unaccent` | installed | ✅ kept |
> | Ollama models `gemma4:12b` / `bge-m3` | resident | ✅ untouched |
>
> **Backup before purge:** all 5 live workflows exported to
> `backup/n8n-workflows-20260807-085702/`. Node counts verified identical to the tracked
> JSON in `n8n/demo-data/workflows/` (25 / 18 / 5 / 6 / 1). **System prompt v3 confirmed
> present in three independent places** — the backup, the tracked JSON, and
> [`archive/phase2/03-wf4-design.md`](../archive/phase2/03-wf4-design.md) §6 — before
> anything was deleted.
>
> ✅ **Resolved by book 0a.** The `db/init` files were rewritten for D32 first, then applied.
> All five schemas — `kb` `ref` `brew` `mem` `nlq` — now exist, and `db-init` is safe to
> re-run. The warning this paragraph used to carry (*"do not re-run db-init, it would
> recreate the old schema"*) no longer applies.
>
> **Why this was the right moment.** Everything in that database was reproducible from
> files on disk — `how_to_brew_john_palmer.pdf` and `styles.json` — and `brew`, `mem` and
> `chat_turns` were all empty. There was nothing to lose and a schema anomaly to fix
> (§5.4). It gets strictly more expensive after every book.
>
> **What it settles:** D32 loses its only counter-argument. The case for keeping
> `brew.bjcp_styles` was incumbency — existing rows, an existing FK. Both are gone, so the
> question reduces to *"what would you design fresh?"*, and that is `ref`.
> **D32 is therefore taken as accepted.**

> ⚠️ **Naming collision.** Architecture §11 has a *"Phase 3 — Full tool set and NLQ"*.
> This is **not** that. **Recommendation:** split §11 into **3a — corpus (this folder)**
> and **3b — tools and NLQ**, and do 3a first. Adding tools to a thin corpus measures the
> tools; adding books to a one-tool agent measures retrieval; doing both at once measures
> nothing. That is §10.3's "one variable" rule at phase granularity.

§6 is the **contract**: when you ask for *"the detailed plan for Water"*, §6 is what
gets followed.

---

## 1. Where things stand

| Change | Effect |
|---|---|
| **Everything purged** (D33), then **books 0a and 0b rebuilt it** | 🟢 five schemas live; `wf1-ingest-book` + `ingest-how-to-brew` + `ingest-bjcp-styles` built and committed; **679 chunks** — *How to Brew* 447 and 232 style cards. §1.3 tracks what is back and what is still outstanding |
| *Radical Brewing* removed from `pending/` | ✅ closed. The file was a 3-page ad, not a book. **It must also come out of the corpus doc's ingredient/process table** — the coverage map is what the agent's refusal behaviour depends on, so a book listed but not ingested is worse than one that was never listed |
| `byo_pastry_stouts.md` added | ✅ reviewed, reformatted, and now **book 8** |
| `Beer_faults.pdf` transcribed to `beer_faults.json` | ✅ **book 6**, and much easier than the first draft claimed. §2 |

### 1.3 The rebuild inventory — what must exist again, and from what

Nothing here is lost work; all of it is reproducible. Listed so that "rebuild from zero"
is a checklist rather than a feeling.

| # | Thing | Rebuilt from | Where it lands |
|---|---|---|---|
| 1 | ✅ `ref` · `kb` · `brew` · `mem` · `nlq` schemas | `db/init/*.sql`, **edited for D32 first** | **done** — all five live; `15_ref.sql` added to the compose file list |
| 2 | ✅ **`wf1-ingest-book`** — the engine, **26 nodes** ⚠️ **live: 27** | rebuilt per [`00a-rebuild.md`](00a-rebuild.md) §2.2, minus every book constant (D30) | **done** — 13-field input contract. ⚠️ the 27th is the orphaned `Clean + normalise1`; §9 |
| 3 | ✅ `ingest-how-to-brew` launcher (2 nodes) | new — [`00b-styles.md`](00b-styles.md) §P.1 | **done 2026-08-12**, id `BAe1fP1g7ZUsbIaq`, exported and committed. D30's per-book pattern now exists for books 1–9 to copy |
| 4 | ✅ *How to Brew* corpus | the PDF, through #2 | **done — 447 chunks**, 0 embedding gaps, §1.4. Re-ingested 2026-08-12 after a `kb` truncate and **reproduced 447 with the identical 36-drop ledger** — the fixture has now held twice, through two independent builds |
| 5 | ✅ **`ref.styles`** import + card generator | `styles.json`, all 11 prose fields | **done 2026-08-12** — `ingest-bjcp-styles`, 22 nodes, id `Ejf3ESE3SK1XBqe3`. 116 rows, 232 cards (variant B). ⛔ **the card-format A/B did not run** — see [`00b-styles.md`](00b-styles.md) §5.4 |
| 5b | ⭐ **Per-book launchers** — `ingest-water`, `ingest-yeast`, ⭐ **`ingest-malt`** | D30's 2-node pattern, copied per book | ✅ **`ingest-malt` done and run 2026-08-19**, id `hpW9P0n7fxXY9KdF`, exported and committed ⭐ **before its first run**. ⚠️ a second, unused workflow of the same name exists — [`03-malt.md`](03-malt.md) §2.1a |
| 6 | `tool-search-brewing-knowledge` | `backup/…/QNAqwfeQyHLxtjZr.json` — 6 nodes, was working | ⭐ **book 4.5** — §4.2 |
| 7 | **WF4 `chat-agent`** | `backup/…/ztLTT3xiKT8eCSfh.json` + [`archive/phase2/03b`](../archive/phase2/03b-wf4-build-guide.md). **System prompt v3 verbatim from [`archive/phase2/03-wf4-design.md`](../archive/phase2/03-wf4-design.md) §6**, with §7.1's de-enumeration edit | ⭐ **book 4.5** — §4.2 |
| 8 | `Prep turn` / `Log turn` → `mem.chat_turns` | never built; carried from the archive as an open item | ⛔ **inside #7's build, not after it** — §4.2 |
| ⏸ | `tool-find-batches` | 1-node stub, parked by D25 | **do not rebuild** |

**Rebuilding WF4 is not a regression.** It was 5 nodes, it is fully documented, and the
rebuild is where the two things the old one lacked — turn logging (#8) and the
de-enumerated system prompt (§7.1) — get built in rather than retrofitted.

### 1.4 *How to Brew* is now a regression fixture, and that is the point

The single best consequence of the purge. Its previous ingest was measured: **447 chunks,
100% embedding coverage at 1024 dims.** Re-running it through the rebuilt engine is
therefore a **test with a known answer**:

> **If book 0a does not reproduce ~447 chunks with 0 embedding gaps, the D30 engine split
> is wrong — and you know it before touching a new book.**

✅ **Result, measured 2026-08-07: 447 chunks, 0 embedding gaps, 1024 dims, 1 `is_current`
version — exact, not approximate.** The D30 split holds: a rebuilt 26-node engine carrying
no book constants reproduced a fixture produced by a workflow full of them. The drop ledger
also matches at 36 (front matter 18, References 16, source-specific 1, token floor 1).

The original plan proved the engine on Water, where there is no prior to compare against.
This is strictly better, and it is why *How to Brew* is re-ingested first rather than
treated as something merely lost.

⚠️ **This could not have been rehearsed before the purge.** Dedup on `file_sha256` would
have stopped the re-run at `Is new file?`. The order genuinely has to be purge → build →
verify, and the worst case is an empty corpus until the engine works.

### 1.1 Correction: the fault list extracts perfectly

The first draft of this plan called `Beer_faults.pdf` *"the hardest single extraction in
the set"*. **That was wrong, and the fix is one flag.** Plain `pdftotext` interleaves the
two columns into unusable order; `pdftotext -layout` reproduces the table exactly —
21 faults, each with its descriptors and its remedy list, no ambiguity anywhere.

So the answer to *"is it really not understandable?"* is **no — it is completely
readable**, and **you should not hand-type it.** A hand-transcription of 21 rows of
dense remedy text is twenty minutes and a real chance of a typo in exactly the kind of
content where a typo is invisible. It has been generated instead:

**`shared/rag-files/pending/beer_faults.json`** — 21 faults, validated as parseable, every
row populated. Schema per row: `name`, `descriptors[]`, `solutions`.

Two things to know about it:

- **Markdown would have been the wrong target.** This is structured data headed for a
  `faults` table (§4 book 6), and JSON is what the existing structured path already
  consumes (`styles.json`, D17). A markdown table would just have to be re-parsed.
- ⚠️ **There is no `cause` column, because the source has none.** The BJCP table is
  exactly two columns — *Characteristic* and *Possible Solutions*. The corpus doc
  describes this source as an *"off-flavor → cause → remedy mapping"*; it is really
  off-flavor → remedy, with causes implicit. **Do not let anything infer the causes** —
  that is precisely the fabricated-numbers failure the closed-book design exists to
  prevent. Causes for the major faults are genuinely covered by *Yeast* and *How to Brew*,
  which is where they should come from, attributed.

**Your job now:** spot-check the JSON against the PDF. Five minutes, and it is the only
verification step that a generated transcription needs.

### 1.2 `byo_pastry_stouts.md` — reviewed

**The content is correct and complete.** All three contributors, all their numbers intact
(30–31 °P, 152–154 °F, WLP066, OYL-052, 158 °F / pH 5.4, 10–14% ABV, Chico). Nothing was
added, removed, or rewritten. Two things were fixed, both about how it will chunk:

| Fixed | Why it mattered |
|---|---|
| **Heading hierarchy.** Was `#` → `###` with the middle level missing, and each pro's ~900-token section was one flat block. Now `#` → `##` per pro → `###` per topic (*Base recipe and gravity*, *Adjunct additions*, *Yeast selection*, …) | `HybridChunker` builds `heading_path` from headings and **embeds the heading path with the body**. Flat sections would have produced chunks embedded as *"Ben Romano, Angry Chair Brewing / …"* with no indication they were about yeast or barrels. This is the same anonymity failure that dominated the stout guide probe — cheaper to prevent in a source file you control than to repair in a cleaning node |
| **Provenance line + trailing whitespace** | Citations need a source; and the article is **practitioner opinion**, not reference text, which requirement §5.6 says must be distinguishable. The italic line under the title states both |

The topic sub-headings are groupings of the article's own paragraphs — no sentence was
moved between sections and no wording changed. If you would rather the file stay
byte-faithful to the original, say so and the grouping moves into the cleaning profile
instead; it costs a slightly more complex node and gains nothing else.

---

## 2. Answers to the five rules you set

| # | Your rule | Recommendation | State |
|---|---|---|---|
| 1 | Research crossovers / overlapping data | **Don't deduplicate. Scope at ingest, measure retrieval share, hold a per-document cap in reserve.** Full reasoning §3 | proposed as **D31** |
| 2 | Decide the order | **Styles model → Water → Yeast → Malt → Draught → BA 2026 + Study Guide → faults → hops → pastry stouts → stout guide.** §4 | ✅ set |
| 3 | A detailed plan per book | **One plan per source at `plans/phase3/<NN>-<slug>.md`**, produced on request, following §6 | ✅ contract written |
| 4 | Each plan: step-by-step build, why each node, small test cases | §6 — nine fixed sections, three tiers of tests, probe-before-plan | ✅ contract written |
| 5 | One workflow per book | **✅ accepted your call: one shared engine.** §2.1 | ✅ settled — **D30** |

### 2.1 D30, settled: one engine, one thin launcher per book

You were right to question it and right to drop it. **The books do not need different
processing — they need different *constants*, and one of them needs a different cleaning
profile.** That is a parameter, not a workflow.

The shape:

```mermaid
flowchart LR
  subgraph L["ingest-water (2 nodes — yours to run)"]
    MT["Manual Trigger"] --> BP["Book profile (Set)<br/>file_path · slug · title · authors<br/>doc_type · profile · front_matter_max_page"]
  end
  BP ==> ENG["wf1-ingest-book (the engine, 25 nodes)<br/>hash → dedup → Docling → clean →<br/>chunks → embed → promote"]
  ENG -.-> P1["profile: book"]
  ENG -.-> P2["profile: ba_manual"]
  ENG -.-> P3["profile: byo_magazine"]
```

`HowToBrew` is renamed **`wf1-ingest-book`**, gains an Execute Workflow Trigger, and loses
every book constant. Each source gets `ingest-<slug>` — its own name in the workflow list,
its own Run button, its own tracked JSON — and is **two nodes**, which is what makes a
per-book plan readable rather than a 25-node re-run.

**Where "slightly different processing" actually lives:** the `profile` field on the
launcher selects a branch in the cleaning node. Three profiles cover all nine sources
(`book`, `ba_manual`, `byo_magazine`). Adding a fourth is ~20 lines in one place, not a
new graph.

**The three structured sources (faults, hops, styles) do not use the engine at all** —
they parse rather than chunk, per architecture §6.6, and are genuinely their own
workflows. No reconciliation needed there.

---

## 3. Crossovers and overlapping data

**The question:** *How to Brew* has a water chapter; *Water* is 273 pages on it. Three
sources define Irish Stout. Four describe diacetyl. Detect, deduplicate, or rank?

### 3.1 The overlaps, named

| Overlap | Sources | Kind | Severity |
|---|---|---|---|
| **Style definitions** | BJCP 2021 cards *(in corpus)* × BJCP Study Guide × BA 2026 × stout guide | **near-duplicate text**, tight embedding cluster | ⛔ **high** — §5 |
| Off-flavours | fault list × How to Brew × Yeast × Draught manual | same topic, different depth | ⚠️ medium |
| Water chemistry | How to Brew ch.15 × Water | same topic, wildly different depth | ⚠️ medium |
| Malt / yeast basics | How to Brew × Malt × Yeast | same | ⚠️ medium |
| Stout brewing | stout guide × pastry stouts | complementary — recipes vs. practitioner method | ✅ low |
| Hop specs | hop handbook (table) × How to Brew (prose) | complementary | ✅ low |

**Almost none of this is textual duplication.** Four books on diacetyl share concepts and
vocabulary, not strings. That single observation decides the policy.

### 3.2 The principle

Two different things get called "overlap", and separating them gives one rule that
resolves both D31 and D32:

| | | Verdict |
|---|---|---|
| **(a) Topical overlap** | four books explain diacetyl, in different words, at different depths, by different authors | ✅ **keep, unconditionally** |
| **(b) Representational duplication** | the *same assertion* stored twice in two shapes — a style's OG range as a numeric column *and* as prose in a card | ⛔ **defect — unless one is generated from the other** |

> **Never drop distinct explanation. Never store the same assertion twice unless one side
> is derived from the other.**

**Why (a) is not negotiable.** It is corroboration and disagreement, not redundancy, and
it is most of what the corpus is worth. Palmer's water chapter and the Palmer/Kaminski
book are the 20-page answer and the 273-page answer; which is correct depends on the
question. Drop the shallow one and every water question becomes a chemistry lecture; drop
the deep one and the assistant cannot go deep.

The asymmetry that makes this a rule rather than a preference: **an ingest-time deletion is
irreversible and untargeted; a query-time filter is reversible and per-question.** You can
always suppress at query time what you kept. You can never retrieve what you dropped. So
the default is keep-and-fix-retrieval unless storage or precision forces otherwise — and
at ~3,100 chunks neither does.

**Why (b) is a defect.** The same fact in two places drifts. The existing style-card design
already dodges this: the card is an `INSERT … SELECT` from the numeric row, so the two
*cannot* disagree. Derived duplication is fine; parallel duplication is a bug.

Layers 0 and 1 below are this one principle applied to (a) and (b) respectively — they are
not in tension.

### 3.3 The policy — four layers, cheapest first

**Layer 0 — never deduplicate across sources.** `file_sha256` and `content_sha256`
already catch byte- and chunk-identical content, and across two different books they will
essentially never fire, correctly. An *embedding-similarity* near-dup pass would delete
exactly what requirement §5.5 demands — *"where sources disagree, present both rather than
averaging them."* You cannot present both positions if ingest deleted one. The
[conflicting-evidence literature](https://arxiv.org/abs/2504.13079) draws the same line:
conflict from **ambiguity** should surface as multiple valid answers; only conflict from
**noise or misinformation** should be filtered. This corpus is entirely the former.

**Layer 1 — prevent overlap at ingest, by scoping.** The real lever, and it costs nothing
at query time. Where a source is structured and already represented, do not add a second
prose representation of the same rows — that is (b), and it is a defect. §5 is this layer
applied to the worst case in the corpus.

**Layer 2 — measure concentration, not duplicates.** Two numbers per source:

| Metric | Signal to act |
|---|---|
| **corpus share** — `count(chunks)` / total, per document | any document > **25%** |
| **retrieval share** — over the 10 probe questions, how many of top-6 come from one document | **≥ 3 of 6** from one document on a question it does not own |

Retrieval share is the one that matters; corpus share is the cheap proxy plan 06 uses.

**Layer 3 — only if Layer 2 fires: a per-document cap in the fusion.** MMR is the textbook
answer and the wrong first move — it needs candidate vectors carried into the fusion stage
and a tuning constant you have no evidence to set. The cheap 80% is
`row_number() OVER (PARTITION BY d.id ORDER BY f.score DESC)` inside
`nlq.search_knowledge`, keeping at most 3 of 6 per document. ~5 lines, additive, no
re-embedding, no new parameter the model can get wrong. §10.4's discipline, applied to a
new row.

**Layer 4 — authority is metadata, never a ranking boost.** Add
`kb.documents.authority` (`reference` | `guideline` | `practitioner`), nullable, and
surface it in the tool's passage header so the model can write *"Palmer suggests X;
Mallett frames it as Y"* — or *"Angry Chair's practice is X, which is opinion, not
reference."* **Do not rank on it.** Ranking by authority suppresses the disagreement the
design exists to surface, and does it invisibly: you would never see the passage that
lost. Requirement §5.6 is a *presentation* requirement; solve it in presentation.

> **D31 (proposed).** No cross-source deduplication. Overlap is controlled at ingest by
> scoping (Layer 1) and measured by retrieval share (Layer 2). The per-document cap
> (Layer 3) is the designated fix and is built **only** when Layer 2 fires.
> `kb.documents.authority` is presentation metadata and never enters ranking (Layer 4).
>
> **Decide by book 5, not book 1** — corrected 2026-08-07. Layers 0–2 change no schema and
> cost nothing; Layer 3 is deferred by construction. Books 1–4 (Water, Yeast, Malt,
> Draught) each own their topic and present no scoping choice, so there is nothing for
> D31 to gate until the style sources arrive.
>
> ✅ The one piece with an earlier deadline is **done**: `kb.documents.authority` was added
> at book 0a and *How to Brew* carries `reference`. `nlq.search_knowledge` already returns
> the column — added while it had zero callers, because `CREATE OR REPLACE` cannot change a
> function's return type later. Populate it per source from here on.
>
> **The line worth your attention is one sentence: authority never enters ranking.** It is
> the rule most likely to be violated later in good faith — *"Palmer is the reference, boost
> him"* — and doing so suppresses the disagreement the design exists to surface, invisibly.
> You would never see the passage that lost.

### 3.4 Deferred: `process_stage` and `style_scope`

Both are asked for by the corpus doc, both are genuinely useful, and both are deferred for
one reason: they need an LLM classification pass over every chunk and **nothing queries
them** — `nlq.search_knowledge` has no parameter for either. They are also cheap to add
later: a nullable column and an `UPDATE`, no re-chunking, no re-embedding.

**Build them when:** an answer needs several process stages and retrieval keeps returning
three chunks about the mash. That is measurable. Wait for it.

---

## 4. The order

> **The principle: earn the right to change the pipeline.** Group 1 changes nothing but a
> Set node, three times, and produces the evidence that decides everything after it.

| # | Source | Path | New capability exercised | Est. |
|---|---|---|---|---|
| **0a** | ✅ **Rebuild** — `db/init` with `ref` → engine → *How to Brew* | new schema + `wf1-ingest-book` | the D30 split, tested against a **known answer: 447 chunks** — ✅ **reproduced exactly**. §1.4 | ~4 h |
| **0b** | 🟡 **Styles model** — `ref.styles` + widened `styles.json` import | new WF — ✅ built, [`00b`](00b-styles.md) | one styles model ✅ **116 rows, 232 cards**; the card-format A/B (§5.5) ⛔ **not run** | ~3 h |
| **1** | **Water** — Palmer & Kaminski, 273 p | engine, `profile: book` | the D30 split itself, on the easiest possible file | ~90 min |
| **2** | **Yeast** — White & Zainasheff, 325 p | engine, `profile: book` | nothing — should be near-free | ~40 min |
| **3** | ✅ **Malt** — Mallett, 335 p | engine, `profile: book` | ⛔ ⭐ **the stated capability is falsified.** `measured` 2026-08-19: Malt is **5.9%** table chunks (27 of 458) against *Yeast*'s **8.0%** — the **least** table-dense book of the three. ⭐ **What it actually exercised is the untab path at double Water's scale** (147,910 tabs, **0** surviving) and the first source where **all three** `book`-profile rules fire. [`03-malt.md`](03-malt.md) §0 | ⭐ **run in 3 min 02 s** |
| **4** | **Draught Beer Quality Manual**, 124 p | engine, **new** `profile: ba_manual` | two-column layout; first new cleaning profile | ~90 min |
| ⭐ **4.5** | **The agent** — `tool-search-brewing-knowledge` + **WF4 `chat-agent`** + `mem.chat_turns` logging | ⛔ **not a source.** §1.3 items 6, 7, 8 | ⭐ **Tier C becomes runnable**, for the first time in the phase. The de-enumeration prompt edit (§7.1) and its `tier1_routing.py` re-run land here, where no ingest is happening. §4.2 | ~4 h |
| **5** | **BA 2026** + **BJCP Study Guide** | new WF rows + engine | extra sources into the model book 0 built. §5 | ~3 h |
| **6** | **Beer Fault List** — `beer_faults.json`, 21 rows | **new WF** | the structured path, on already-clean data | ~2 h |
| **7** | **Hop Variety Handbook**, 44 p | **new WF** | `hops` table; extraction from repeating PDF spec cards | ~3 h |
| **8** | **BYO Pastry Stouts** — markdown, ~2,300 words | engine, `profile: book` | **first non-PDF input** — does the engine take `.md`? | ~45 min |
| **9** | **Stout Style Guide**, 84 p | engine, `profile: byo_magazine` | [archived plan 06](../archive/06-stout-guide-ingest.md), already written and probed | ~2 h |

### 4.1 Why this order

**The styles model first — revised 2026-08-07, and this reverses the first draft.** It was
book 5; it is now book 0, for one reason that outweighs the rest: **the 116 style cards are
already in `kb.chunks`, competing in every retrieval, and the standing regression questions
hit them.** Reworking styles at book 5 would invalidate the baseline books 1–4 were measured
against, splitting the sequence into "before styles" and "after styles" — the exact
moving-target failure this plan warns about everywhere else. Doing it first costs **one
clean re-baseline at the start** instead.

Three supporting reasons: it is the cheapest it will ever be (116 rows, **no consumer** —
`lookup_bjcp_style` is unbuilt); it is a different workflow from the engine, so it does not
delay the D30 split; and it is the only piece of *already-built* work that is actually
wrong, which is what the reset was for.

It also splits cleanly: the schema plus the BJCP 2021 re-import is book 0 (~2 h), and
BA 2026 + the Study Guide land at book 5 as additional rows into a model that already
exists (~3 h) — instead of one five-hour job.

**Water first, because it is the easiest hard thing.** Closest twin to the one book
already ingested — single-column prose, calibre-produced, 273 pages against 248 — so the
D30 split is proved on a file where a failure means *the split is wrong*, not *the file is
weird*. It is also the largest genuine coverage gap: water chemistry is listed as a
strength and the corpus has one Palmer chapter of it.

**Yeast and Malt next, because they should cost almost nothing.** If they don't, the
parameterisation is broken and you want to learn that on book 3 of 9, not book 8. Three
books of one shape is also the smallest sample that shows whether the engine generalises —
one proves nothing, two is a coincidence.

⭐ **`measured` 2026-08-19 — the sample is complete and the prediction held.** Books 1, 2 and 3
are from **three different publishers and two different production toolchains**, and all three
landed with **zero new nodes, zero new profiles and zero schema changes**. Only book 1 needed a
shared-code edit (the untab block), and ⭐ **book 3 is what proved that edit was necessary rather
than merely safe** — 147,910 tabs, 296 of them inside headings, none surviving. **The D30 split
is no longer a coincidence.**

**Draught fourth: a format change on a topically disjoint file.** The first new cleaning
profile since the stout guide, and the manual is the only source covering dispense — so if
the profile mangles something, no existing answer degrades. Format risk and overlap risk
are separated deliberately.

**BA 2026 and the Study Guide fifth, into a model that already exists.** They are the two
sources with real scoping decisions, so they wait for D31 and for the retrieval-share
evidence from four clean books. Splitting them from book 0 also keeps them apart from each
other in the right way: BA 2026 is structured rows, the Study Guide is prose scoped to
rationale — different paths, and running them back to back would change two variables.

**Faults before hops.** The fault list's source data is now clean JSON, so it exercises the
structured path — parse → assert → upsert → generate cards → embed — with the extraction
problem already solved. The hop handbook does the same path *plus* a real extraction from
44 pages of PDF spec cards. Do the easy half first.

**Pastry stouts eighth, right before the stout guide.** It is the first non-PDF input, so
it is a variable of its own and belongs alone; and it is the same topic as book 9, so the
two should be evaluated together. It is also 45 minutes.

**Stout guide last — and this is the change plan 06 wants.** Plan 06 §6 calls corpus
balance *"the thing to watch, and it is bigger than any node in §3"*: 218 merged chunks
against today's 563 is **28%** of the corpus, with a rollback rule already drafted for it.
Against ~2,900 it is **~7%**. Same file, same chunks, a third of the risk — bought purely
by running it ninth. Plan 06 needs no rewrite, only a note that its percentages assume it
runs first.

### 4.2 ⭐ Book 4.5 — where the agent gets built, and why not earlier

**Decided 2026-08-12, while planning book 2.** The question was *"when do we build a working
agent that can fetch the books, check whether it can find a proper answer, and merge several
sources into one response?"* — and the answer is a **seam**, not a source: **after book 4,
before book 5.**

⛔ **Every per-source plan so far ends with the same line: *"Tier C — not runnable, no WF4."***
Books 0a, 0b, 1 and 2 all carry it. That is not a skip, it is a debt, and it compounds: each
source lands with pipeline and retrieval evidence and **no end-to-end evidence at all**.

**Four reasons the seam is at 4.5 and not somewhere else:**

| | |
|---|---|
| ⭐ **Book 5 is where disagreement first exists** | BA 2026 and BJCP 2021 state different numbers about the same styles. Merging and attributing two conflicting sources is exactly what Layer 4 exists for, and the agent should be **live and measured as book 5 lands** rather than retrofitted onto a corpus that already contains the conflict. Build at 4.5 and book 5 is the agent's first real test |
| **Books 1–4 are one group by construction** | §4.1: same shape, no scoping choice, and **D31 does not gate until book 5**. The boundary after book 4 is the only place in the sequence where nothing is mid-flight |
| ⛔ **The prompt edit needs a run with no ingest in it** | WF4 carries §7.1's de-enumeration edit and therefore a `tier1_routing.py` re-run. **Standing rule 2 forbids moving the prompt and the corpus in the same run.** 4.5 is the only free slot |
| **The Tier C backlog clears in one sitting** | each plan already specifies its own five Tier C questions, so books 0a–4 are ~20 questions against an existing spec — not a new design job |

⛔ **Why not now, after book 2.** Three overlapping documents on two axes is not enough to
measure *merging*. You would be testing the agent, not the corpus, and you would have to test
it again at book 5 anyway. **Why not at book 8 or 9**, when practitioner sources finally make
`authority` discriminate: nine sources would then be ingested with no end-to-end check, and the
first failure would have eight candidate causes.

**Two consequences that are part of the decision, not additions to it:**

1. ⛔ **`mem.chat_turns` logging (§1.3 item 8) is built *inside* WF4, not after it.**
   `chunk_ids` per turn is the prerequisite for the retrieval-hit-rate metric, and **every turn
   logged before the logging exists is a turn that cannot be scored.** It has been carried as an
   open item since phase 2 precisely because it kept being deferred to "after".
2. **The test suite splits in two, and only the first half is written at 4.5.** At 4.5: the
   per-source Tier C questions already specified in plans 00a–04, plus the hard refusal check.
   ⭐ **At book 5: the merge/conflict eval** — *"where two sources disagree, are both
   attributed?"* — because that is the first point at which the cases can be written from **real
   disagreements** instead of invented ones. §10.1's full eval baseline still waits for source 9,
   per §8; that ordering does not change.

⚠️ **4.5 is a build, so it obeys the same rules as a source:** export and commit before running
(standing rule 4), one variable per run (rule 2), and ⛔ **read `tier1_routing.py`'s knowledge
row before believing the prompt is fine** — v3.1 looked strictly safer than v3 and scored 20
points worse (§7.1).

### 4.3 Projected corpus

Extrapolated from the one measured book (248 p → 447 chunks) and plan 06's probe:

| | chunks | running total |
|---|---|---|
| **0a+0b — measured 2026-08-12** — How to Brew **447** + BJCP cards **232** (variant B) | **679** | **679** |
| **1 — measured 2026-08-12** — Water | **382** *(projected ~490)* | **1,061** |
| ⭐ **2 — measured 2026-08-19** — Yeast | **463** *(predicted 463; projected ~590)* | **1,524** |
| ⭐ **3 — measured 2026-08-19** — Malt | ⛔ **340** *(predicted 340; projected ~600)* | ⭐ **1,864** |
| **4** Draught manual | ~250 | ~2,114 |
| **5** BA 2026 cards + Study Guide prose | ~100 · ~130 | ~2,344 |
| **6–7** faults · hops | ~21 · ~110 | ~2,475 |
| **8** pastry stouts | ~12 | ~2,487 |
| **9** stout guide | 218 | ⭐ **~2,705** |

⭐ **The first three rows are no longer projections, and both books came in *under* the
extrapolation** — Water by 22%, Yeast by 22%. The reason is the same in both cases and worth
carrying to book 3: the projection scaled *How to Brew*'s 1.80 kept chunks per page, and both
later books sit near **1.40**. Page counts are a poor proxy for chunk counts across
publishers — *Yeast* is 325 pages on a 3.5″ × 5.19″ trim.

⭐ **`measured` 2026-08-19: Yeast landed at exactly the 463 its plan predicted.**

⛔ **And book 3's probe has now corrected the projection by 260 chunks.** [`03-malt.md`](03-malt.md)
§5.1: *Malt* yields **458 raw → 340 kept `predicted`**, against this table's **~600**. The band
the last revision called honest — *"~470–600"* — was still **too high**, and the reason is
measurable rather than a trend: ⭐ **118 of Malt's 458 raw chunks are dropped, 62 of them the
Index alone.** *Malt* has the largest back matter in the phase and the lowest kept-chunks-per-page
of any book — **1.02**, against Yeast 1.42, Water 1.40 and *How to Brew* 1.80.

⭐ **The end state therefore moves from ~2,965 to ~2,705**, and every downstream row above is
shifted by the same −260. ⚠️ **Books 4–9 are still naive projections** and each will move when
its own probe runs; the correction is recorded here rather than absorbed silently.

**⭐ `predicted` ~2,700 chunks, not ~2,950 and not ~3,200.** Architecture §3.6 sized pgvector
for 40–60k and called 500k comfortable, so **do not let corpus growth become an infrastructure
conversation.** The
thing that degrades is top-6 competition — §3 — and it degrades silently (R5).

---

## 5. ⭐ The styles rework — your BJCP question, answered

You said you think the BJCP guidelines should be added again, rethought, maybe elsewhere
in the DB and in another format. **Agreed, and now is the cheapest moment it will ever
be.** Here is the case and the proposal.

### 5.1 What is wrong with the current shape

Today (D17): `styles.json` → 116 rows in **`brew.bjcp_styles`** + 116 generated style
cards in `kb.chunks`. Three problems, in increasing order of importance:

1. **It is in the wrong schema.** `brew` is *"truth — what I actually did"* (§3.1). BJCP is
   *"what a reference says"*, which is knowledge. Architecture §3.5 admits the case is
   awkward and put the numeric side in `brew` anyway. With two more style sources arriving,
   that compromise stops being harmless.
2. **The name encodes one source.** `brew.bjcp_styles` cannot hold BA 2026 without either
   lying about its name or fighting `ON CONFLICT (guide_year, code)`. Two guides, two
   numbering systems, overlapping style names.
3. ⛔ **Three sources will produce three prose descriptions of Irish Stout.** They will
   cluster tightly in embedding space, and a top-6 that returns three of them has spent
   half its budget saying the same thing three ways. This is the highest-probability
   retrieval defect in the whole plan, and Layer 1 is the only place to stop it cheaply.

**And the cost of changing it is near zero right now**, which is the decisive fact:
**nothing reads the numeric table.** `lookup_bjcp_style` is Phase 3b, unbuilt. 116 rows,
no consumer. Re-import is a JSON parse, not a Docling run — minutes, not hours. This gets
strictly more expensive every week it waits.

### 5.2 The three representations, kept straight

Being precise about which representation is which is what makes the overlap disappear:

| | Form | Retrieval | Answers |
|---|---|---|---|
| **Numeric ranges** | real columns, one row per `(guide, guide_year, code)` | **SQL only — never embedded** | *"is my 1.048 in range for 15B?"* — a `BETWEEN`, not a retrieval gamble |
| **Narrative** | one **or two** cards per `(guide, style)` — §5.5's A/B — **generated from the row** | embedded | *"what's the difference between a porter and a stout?"* |
| **Causation prose** | ordinary chunks — the Study Guide's *why* | embedded | *"why does an Irish Stout read roasty rather than burnt?"* |

The overlap rules fall straight out of §3.2's principle:

- **Numeric + card coexist** because the card is *derived* — they cannot drift. Derived
  duplication is fine.
- **Two guides coexist** because they are different assertions by different bodies. Where
  BJCP 15B and BA's Irish-Style Dry Stout disagree on numbers, **that disagreement is
  information** — surface both, attributed. Layer 4, not a deduplication problem.
- ⛔ **Two cards for one style that say the same thing** is the actual defect — and the
  Study Guide's vital-statistics tables restating BJCP numbers as prose is the same defect
  in different clothes. Both get dropped.

  ⚠️ **This is not what §5.5's variant B does, and the distinction is the whole principle.**
  A sensory card and a context card carry **disjoint fields** — no sentence appears in
  both. That is one assertion split across two chunks, which is fine. Two cards would only
  be a defect if they *restated* each other. Splitting ≠ duplicating.
- The Study Guide is therefore the **one style source that goes through the prose engine**,
  not the structured path. Its rationale is genuinely unique content; nothing else in the
  corpus has it.

### 5.3 The proposal

**One styles model, all sources as rows.**

| Change | Detail |
|---|---|
| **Move and rename** | `brew.bjcp_styles` → **`ref.styles`**, keyed `(guide, guide_year, code)`. `guide` ∈ `BJCP`, `BA`. Numeric ranges stay real columns and stay **nullable** — see §5.4 finding 2 |
| **Widen the row** | the current table imports **6 of the 11 prose fields** in `styles.json`. Add `history`, `characteristic_ingredients`, `style_comparison`, `entry_instructions`, `tags[]` — see §5.4 finding 3 |
| **Cards per style** | ⚖️ **decided by measurement, not argument — §5.5.** Whatever wins, they are regenerated by the same `INSERT … SELECT`, so the row and the card still cannot drift (§3.5's actual good idea, preserved) |
| **The dedup rule** | ⛔ **never two cards for the same style within a guide**, and cross-guide cards must differ in heading path so they are distinguishable in a citation. *"BJCP 2021 15B Irish Stout"* and *"BA 2026 Irish-Style Dry Stout"* are different claims by different bodies and both are legitimate — that is Layer 4, not Layer 0 |
| **BJCP Study Guide** | scoped to **rationale prose only** — *why* a style tastes as it does. Its vital-statistics tables are dropped as duplicates of the cards. This is the source's genuine unique value and nothing else in the corpus has it |
| **Repoint the FK** | `brew.recipes.style_id` → `ref.styles(id)`. See §5.4 finding 1 |

**Rollback is the whole point of doing it now:** the current 116 rows and 116 cards are
reproducible from `styles.json` by re-running the import. There is nothing to lose.

⚠️ **One implementation note not to forget:** `n8n_agent` holds rights on `nlq` and nothing
else (§8.4). `ref.styles` is therefore unreachable by the agent until an `nlq` view or
function exposes it — same as every other table, but easy to overlook when
`lookup_bjcp_style` lands in Phase 3b.

### 5.4 Three findings from the live data and schema

Measured 2026-08-07 against `db/init/20_brew.sql`, `styles.json` (116 styles) and the
tracked `wf2-digestion.json`. Each one moved the design.

**Finding 1 — it is not consumer-free. There is an FK.**
`brew.recipes.style_id` references `brew.bjcp_styles(id)`
([`db/init/20_brew.sql:56`](../../db/init/20_brew.sql)). The table is empty, but the
dependency is structural, and it is why the target is **`ref.styles` and not `kb.styles`**:
a `brew → kb` foreign key points the wrong way across the boundary the design protects.

**Why a `ref` schema rather than either.** There is a standing anomaly today —
deprecation #12 forbids embedding anything from `brew.*` into `kb.*`, and §3.5's card
generator does exactly that as a deliberate carve-out, because `brew.bjcp_styles` is the
one table in `brew` that is not *"what I actually did"*. **Published reference data is a
third category, and three of the nine sources are it: styles, hops (book 7), faults
(book 6).**

```sql
CREATE SCHEMA ref;   -- published reference data: not my brewing, not prose
```

| Gain |
|---|
| Deprecation #12 becomes **absolute again** — nothing from `brew` ever reaches `kb`, no carve-out |
| `ref.*` → generated cards in `kb` is clean by construction |
| `brew.recipes.style_id → ref.styles(id)` reads correctly: a recipe references a reference table |
| **Hops and faults get a home before books 6 and 7 each invent one ad hoc** |

Cost: a fifth schema. Real but small — the agent only ever touches `nlq`, so the grant
model does not change at all. Conceptual cost, structural gain.

**Finding 2 — 20 of the 116 styles have no vital statistics.**
Every specialty category (`27A`–`34C`: Historical Beer, Alternative Fermentables,
Wood-Aged, Specialty IPA…) ships with no OG/FG/IBU/SRM/ABV, because those vary with the
base style. The columns are nullable and that is correct.

✅ **The card generator already handles this** — `CASE WHEN s.og_min IS NOT NULL` omits the
vitals line entirely. Nothing to fix there.

⚠️ **The lookup path does not exist yet, and this is where it will break.** A model handed
`og_min = null` will render **"OG 0.000"** without hesitation. Add a generated column and
branch on it rather than trusting null handling:

```sql
has_vitals boolean GENERATED ALWAYS AS (og_min IS NOT NULL) STORED
```

`lookup_bjcp_style` (Phase 3b) must say *"this style defines no vital statistics"*
explicitly. Recorded here because that is the plan that will be written months from now.

**Finding 3 — the import throws away five prose fields.**
`styles.json` carries 11 prose fields; the table has columns for 6. Discarded today:
`history`, `characteristicingredients`, `stylecomparison`, `entryinstructions`, `tags`.

`stylecomparison` is literally *"how does this differ from X"* — among the most-asked style
questions — and it is dropped at import. `tags`
(`session-strength, dark-color, britishisles, brown-ale-family, malty`) is free FTS fuel.

### 5.5 ⚖️ The card format — ✅ **settled 2026-08-12: variant B, by argument. D32b closed.**

> ⭐ **This section is kept as the record of why, not as a protocol to run.** It was written
> as a three-run A/B with the decision rule fixed in advance. **That A/B is retired** — §6's
> revision drops multi-variant sequences — so the question is settled here, on the evidence
> that already exists, and the runner-up is written down.
>
> **The decision: variant B — all 11 prose fields, split into a sensory card and a context
> card. 232 cards. It is what is deployed.**
>
> **Why B, without running A0 and A.** The measured card sizes below decide it:
>
> | Variant | Median tokens | Six cards in context | Verdict |
> |---|---|---|---|
> | **A0** — 6 prose fields | ~471 predicted | ~2,826 | ⛔ **discards five prose fields**, including `stylecomparison` — literally *"how does this differ from X"*, among the most-asked style questions (§5.4 finding 3). Losing content to save context is the wrong trade when a split saves the same context and loses nothing |
> | **A** — all 11 fields, one card | ~679 predicted | **~4,074** ⚠️ | ⛔ **busts the ~3,000-token budget by 36%**. This is not a retrieval preference, it is an arithmetic failure: six A cards do not fit |
> | ✅ **B** — all 11 fields, two cards | ~350 predicted | ~2,100 | ✅ **carries everything A carries, at half the width.** The only variant that is both complete and within budget |
>
> **The argument is not "B retrieves better" — that was the bet the A/B would have tested,
> and it is now untested and recorded as such.** The argument is narrower and does not need a
> run: **A0 is incomplete and A does not fit.** B is the only option that is neither, and the
> §5.2 rule that makes it safe — a sensory card and a context card carry **disjoint** fields,
> so no sentence appears in both — is a property of the design, not of a measurement.
>
> ⚠️ **What is genuinely given up, stated so it is not rediscovered as a surprise:** nobody
> knows whether splitting *helps* retrieval or merely fails to hurt it. If style questions
> later retrieve badly, **the sensory/context split is a live suspect** and this paragraph is
> the note that says so. Re-testing it costs two ~3-minute runs of `ingest-bjcp-styles` with
> the `variant` field changed — the workflow still supports A0 and A, and §2 node 12's
> three-branch `CASE` is deliberately left in place for exactly that.
>
> **Everything below is the original protocol, retained as the reasoning record.**

#### The original protocol — retired, retained for the reasoning

**Decided 2026-08-07 (your call): build each variant, measure it, keep the winner.** The
argument for splitting the card is a retrieval bet, not a correctness fix, and this plan's
own rule is that bets get measured. What follows is the protocol, written **before** the
run so the decision rule cannot be chosen after seeing the numbers.

**Card sizes, measured over all 116 styles:**

| Variant | Fields | Median tokens | Max | 6 cards in context |
|---|---|---|---|---|
| **A0** — status quo, deployed | 6 prose fields, 1 card | ~460 | ~925 | ~2,760 |
| **A** — widened | all 11 fields, 1 card | **~667** | ~1,260 | **~4,000** ⚠️ over the ~3,000 budget |
| **B** — widened + split | all 11 fields, **2 cards** | **~330** | ~630 | ~1,980 |

- **sensory card** — overall impression, aroma, appearance, flavor, mouthfeel
- **context card** — history, style comparison, characteristic ingredients, commercial
  examples, entry instructions, tags

**Three runs, not two — because A0 → A → B isolates one variable each.** Testing A against
B alone confounds *"do the extra fields help"* with *"does splitting help"*, and §10.3's
rule is one variable per run.

| Run | Variable under test |
|---|---|
| A0 → A | **do the five missing prose fields help?** |
| A → B | **does splitting the card help?** |

#### How to run it — sequentially, in place

⚠️ **The two variants cannot coexist in the corpus.** `kb.document_versions` carries
`UNIQUE (file_sha256)`, and both variants are generated from the same `styles.json`, so
they hash identically. This is the same constraint plan 06 §8.2 hit.

**That is fine, because `ingest-bjcp-styles` is built to be re-run in place** — see
[`00b-styles.md`](00b-styles.md) §2, nodes 10 and 11. `Ensure KB doc + version` uses
`ON CONFLICT (file_sha256) DO UPDATE … RETURNING id`, so a re-run **reuses the same
`version_id`** and records the variant in `chunker_config`; `Demote + clear old cards`
demotes the version and deletes its chunks (embeddings cascade) before regeneration. So the
loop is:

1. set the `variant` field on the `Card variant` node — `A0`, then `A`, then `B`
2. re-run the workflow — cards are cleared and regenerated, embeddings follow
3. run the probe set, record
4. repeat

⚠️ **The variant is a launcher field, not an edit to the card SQL.** Hand-editing a 60-line
`INSERT … SELECT` three times makes the thing under test also the thing being modified three
times, and the export then records only the last paste. As a field it lands in
`kb.document_versions.chunker_config`, so *"which variant produced these cards"* stays
answerable from SQL.

Each cycle is **~2–5 minutes measured-adjacent** (variant B ran in that band on 2026-08-12):
a JSON parse and 116–232 embeddings, no Docling. **No rollback SQL is needed** — the next run
overwrites.

#### The probe set — 8 questions, 4 of each kind

The set has to *discriminate*. Sensory questions should be indifferent to the split;
context questions are where B should win if it wins at all.

| | Sensory | Context / comparison |
|---|---|---|
| 1 | what should an Irish Stout taste like | what is the difference between a porter and a stout |
| 2 | what aroma is expected in a Dark Mild | where did Dark Mild come from |
| 3 | how should a Doppelbock look and feel in the mouth | what commercial examples are there for Irish Stout |
| 4 | what mouthfeel is right for an Oatmeal Stout | which ingredients are characteristic of a Munich Helles |

Run each with `scripts/ask.sh`; record **hit@1** and **hit@3** — does the correct style's
card come back, and at what rank. Plus the **5 standing regression questions** from
[`02-phase1-retrieval-gate.md`](../archive/02-phase1-retrieval-gate.md), because a card
change alters what every book question competes against.

#### The decision rule, fixed in advance

| Comparison | Keep the new variant if |
|---|---|
| **A0 → A** | context questions improve on hit@3 **and** sensory questions do not regress. If the extra fields help nothing, stay at A0 and the split question is moot |
| **A → B** | context hit@1 improves by **≥ 2 of 4** with no sensory regression — **or** it holds parity, in which case **B wins the tie** |
| **either** | ⛔ any of the 5 standing questions drops its rank-1 chunk out of the top 3 → reject, regardless of the style scores |

**Why B wins ties:** at ~330 tokens against ~667 it returns the same answer for half the
context budget. Parity on quality plus half the cost is a win, and it is the one place in
this comparison where the tiebreak is not a judgement call.

**Record all three results in the book 0 plan**, including the losers. A measured negative
is the thing that stops the question being reopened in three months.

> **D32 (proposed) — the styles model.** A new **`ref` schema** holds published reference
> data. `brew.bjcp_styles` moves to **`ref.styles`**, keyed by guide and widened to all 11
> prose fields; `brew.recipes.style_id` repoints to it. All style sources — BJCP 2021,
> BA 2026, any future guide — become rows in it. Cards are generated from the rows so the
> two cannot drift. **Hops (book 7) and faults (book 6) go to `ref.*` too.** The BJCP Study
> Guide is ingested as prose scoped to rationale only. Supersedes the `brew`-side placement
> in architecture §3.5, closes the style half of D31's Layer 1, and removes deprecation
> #12's standing carve-out.
>
> ⚖️ **The card format is explicitly NOT decided here.** One card or two is settled by the
> A/B in §5.5 — three runs, decision rule fixed in advance, all three results recorded
> including the losers.
>
> **Decide now; execute as book 0** — revised 2026-08-07. It was scheduled at book 5. The
> deciding argument is the baseline: the 116 cards are already competing in every
> retrieval, so reworking them mid-sequence invalidates what books 1–4 were measured
> against. See §4.1.
>
> This is a schema change to a live table, and it is the **only decision that gates the
> start of the phase.** D31 does not.

---

## 6. ⭐ The contract for every per-source detailed plan

**This is the section that matters most.** Every plan lives at
`plans/phase3/<NN>-<slug>.md`, follows this skeleton in this order, and is not finished
until every section has content.

> ### How the work is actually divided — revised 2026-08-12
>
> This replaces the nine-section contract that governed plans 00a, 00b and 01. Those plans
> were written for a reader who would be talked through a build step by step and stopped
> mid-run to check things. **That is not how the work happens.**
>
> | Who | Does what |
> |---|---|
> | **The plan** | states the prerequisites, specifies the build completely, gives a **reset command**, and lists the tests |
> | **You** | build the whole workflow, then run it. If something breaks, you say so |
>
> **Four consequences, and they are the whole revision:**
>
> 1. ⛔ **No stop-and-check-before-embedding steps.** A build is built and run. If the
>    numbers come back wrong, the reset command (§3) makes starting over cheap, which is a
>    better safety net than a checkpoint that interrupts every run to catch a rare one.
> 2. ⛔ **No A/B or multi-variant sequences.** A plan proposes one design and measures it.
>    Where two designs were genuinely arguable — the styles card format, §5.5 — the question
>    is settled by argument on the record and the runner-up written down, not by three runs.
>    **D32b is closed on this basis.**
> 3. ⭐ **Every plan carries a reset command** — §3, new and required.
> 4. ⭐ **n8n expressions are written without the leading `=`.** §3.1.

---

### §0 — The verdict, in one screen
Engine or new workflow, and why. If it is the engine, a per-node table of *correct as-is /
parameterise / needs real work*, and ⛔ **an explicit sentence if anything outside the
launcher changes** — that is the signal that the D30 split is not holding.
[Archived plan 06 §0](../archive/06-stout-guide-ingest.md) and
[`01-water.md`](01-water.md) §0 are the models.

### §1 — Prerequisites
What must be true before the build starts, verified against the **live stack** rather than
carried from a previous plan. Two parts:

- **What is already true** — a table of checks actually run, with the command and the
  result. Plans have been wrong before, including in ways that cost a re-ingest.
- **What must be done first** — open items from earlier books that this one depends on, in
  the order they must happen, with the reason any ordering is forced.

⛔ **If nothing is outstanding, the section says so in one line.** Present, so its emptiness
is a decision rather than an omission.

### §2 — The build
**Complete enough to build from, without coming back to ask.**

- **New workflow:** the full node list, in build order, with settings, SQL and code inline,
  and a wiring diagram. [`00b-styles.md`](00b-styles.md) §2 is the model.
- **Existing workflow:** the exact parameterisation — which node, which field, which value,
  and **where each value came from**. [`01-water.md`](01-water.md) §2.2 is the model: a
  13-row mapper table where every row names its source of truth.

**Every node gets a "why this node exists" line when it is not self-evident.** Not
*"Crypto node — hashes the file"*, but *"Crypto computes the SHA-256 dedup key; the Read
node runs twice because Crypto consumes the binary it hashes (D13/D20)"*. If a node's
purpose is obvious from its name, **say nothing** — padding hides the three nodes that
genuinely need explaining.

**Include, where they apply:**

- **The cleaning profile or parser**, complete and paste-ready, with every drop rule naming
  the §5 number that motivates it.
  ⚠️ Every plan repeats plan 06 §4's warning: **if `heading_path` is modified, `content`
  must be rebuilt**, or the embedding still carries the old heading and the repair does
  nothing.
- **Overlap scoping** (§3 Layer 1) — what this source duplicates that is already in the
  corpus, and the rule that keeps or drops it, with an expected **overlap chunks dropped**
  count. One line if it overlaps nothing.
- **What this source does to WF4** — the concrete edits, with exact text. Never *"update the
  system prompt"*, always the sentence written out. One line if nothing changes.

#### §3.1 — n8n expressions: no leading `=`

⭐ **Write every expression as `{{ … }}`, never `={{ … }}`.**

The `=` is an artefact of n8n's **JSON export format**, where it marks a field as an
expression rather than a literal. In the **UI**, that role is played by the expression
editor itself — so a pasted `=` becomes a literal `=` inside the expression and the field
silently evaluates to something wrong.

```
✅  {{ $('Ingest book input').first().json.file_path }}
⛔  ={{ $('Ingest book input').first().json.file_path }}
```

⚠️ **The exception is when the plan quotes an exported JSON file**, where the `=` is part of
the stored value and must stay. Say which one you are looking at.

### §3 — ⭐ Reset: undo everything this workflow added
**New and required.** One copy-pasteable command that returns the database to exactly the
state before this source's workflow first ran — so a run that dies halfway, or finishes with
wrong numbers, can simply be started over.

**It has to work on a *partial* run, not just a complete one.** That is the whole point: a
workflow that failed at the embedding loop has already written a `kb.documents` row, a
`kb.document_versions` row and some or all of its chunks. A reset that only handles the
clean case is a reset that is useless exactly when it is needed.

**For an engine-path source**, keyed on the file hash so it cannot touch another document:

```sql
DELETE FROM kb.document_versions WHERE file_sha256 = '<sha256 of the source file>';
-- kb.chunks cascade from the version; kb.chunk_embeddings cascade from chunks;
-- kb.ingest_log cascades. Nothing else in the corpus is touched.
```

**For a structured source**, the same plus its rows and generated cards, **cards first** —
`ref.*` has no FK from `kb.chunks`, so deleting the rows first leaves orphaned cards, which
is precisely the drift the design exists to prevent.

**Every plan's §3 states, explicitly:**

| | |
|---|---|
| the **exact literal** the command is keyed on | the file's SHA-256, or the guide and year |
| what **cascades** and what does not | so nothing is deleted twice or missed |
| the **verify-after** query and its expected output | a reset you cannot confirm is not a reset |
| whether `kb.documents` is left behind | ✅ normally yes — `ON CONFLICT (slug) DO UPDATE` reuses it on the next run, and deleting it gains nothing |
| anything the reset **cannot** undo | a shared-code edit, a renamed node, an exported JSON |

⛔ **The plan never runs this.** It is written so it exists before it is needed, and it is
triggered by you.

### §4 — Testing
**Two tiers, both required, written so they can be handed over and run without further
explanation.** Copy-pasteable `docker exec` blocks with the expected output stated.

**Tier A — pipeline (SQL, deterministic).** At minimum:

1. rows by document + embedding coverage + null pages/headings — plan 06 §7.6's query,
   unmodified; it is already the right one. ⛔ **Including a row for every *existing*
   document**, which is the check that this ingest touched nothing else
2. `kb.ingest_log` has 2 rows, with a populated `drops` array and a populated `repairs`
   array
3. the drop ledger **by reason**, against the predicted counts
4. **idempotency** — run again, stops at `Is new file?`, inserts 0
5. `count(*)` before vs after matches the predicted number

**Tier B — retrieval (`scripts/ask.sh`, deterministic).**

- **≥ 3 positive controls** — questions this source newly makes answerable, each stating the
  expected document slug and the rank it must reach. *"What sulfate-to-chloride ratio suits
  a hoppy pale ale?"* → `water-comprehensive-guide` in the top 3.
- **the 5 standing regression questions** from
  [`02-phase1-retrieval-gate.md`](../archive/02-phase1-retrieval-gate.md), run **before**
  the ingest for a same-session baseline and again after. Keep/roll-back rule, unchanged
  and restated in every plan:

  | Outcome | Action |
  |---|---|
  | prior rank-1 chunk still top 3 on all five | **keep**, log the shift |
  | falls out of top 6 on **one** | keep, log as a defect |
  | falls out of top 6 on **two or more** | ⛔ **reset** (§3) |

- the §3 Layer-2 **retrieval share** check over those 10 questions. **Record it even when it
  fires nothing** — a recorded null is what makes the first real firing legible.

**Tier C — agent (ask the assistant, judged).** ⚠️ **Not runnable until WF4 exists**, and
every plan says so explicitly rather than omitting the tier. When it is runnable, 3–5
questions through the n8n chat panel:

| Type | Pass condition |
|---|---|
| new coverage | answers, names the new source, `[S…]` markers all resolve |
| **refusal still holds** | *"How much Citra do I have?"* → *"I don't have a tool for that yet"*. **Every plan re-runs this** — it is the one hard fail |
| citation integrity | no `[S…]` the tool did not return |
| conflict surfacing | where the new source disagrees with an existing one, both are attributed (Layer 4) |

Each plan states whether `scripts/stress/tier1_routing.py` needs re-running — see §7.

**Predicted numbers, with a gate column**, computed by running §2's rules over §5's real
probe output — because a test with no expected value is not a test:

| Check | Predicted | Gate |
|---|---|---|
| kept chunks | *n* | ±10% |
| median tokens | *n* | 200–450, or a documented miss and why |
| under-30 | 0 | **must be 0** |
| missing page / heading | 0 | **must be 0** |
| embedding coverage | *n*/*n* | **100%** |
| `kb.ingest_log` rows | 2 | must be 2 |
| corpus share after | *x*% | < 25%, or argued |

Plus a **runtime estimate, so a hung run is recognisable as hung** — and a threshold past
which it is definitely hung, with the most likely cause.

### §5 — Evidence: what was measured before the plan was written
⭐ **Standing rule 1, and the section the rest of the plan is derived from.** No plan is
written from assumptions. Submit the file to the **live** Docling service with the engine's
exact form fields and measure first:

| Measure | What it decides |
|---|---|
| raw chunk count, chunks/page | sizing; prose vs. structured |
| median / max / p25 / p75 `num_tokens` | whether §11's chunk-size band is met |
| count under 30, count over 512 | drop rules; whether merging is needed |
| chunks with no `page_from` | **must be 0** — citations break without it |
| **top 20 headings by frequency** | plan 06's entire design turned on this one table |
| front-matter page range | the `front_matter_max_page` constant |
| **the hyphen probe, checked against the Docling output** | `text_repairs` — standing rule 7 |
| 3 real chunks, verbatim | the only way to see what cleaning actually has to do |

For a structured source the equivalent is: row count, per-field coverage, and any row that
fails validation.

**The probe output goes in the plan, as tables.** It is what makes every predicted number in
§4 a derivation rather than a guess — and [`01-water.md`](01-water.md) §5.5 is the evidence
that this works: 18 of 19 acceptance numbers landed **exactly**, not within tolerance.

---

### Standing rules

1. **Measure, then plan.** No plan without §5. Plan 06's design turned on one
   heading-frequency table nobody would have guessed.
2. **One source per execution, one variable per run.** Never ingest two before re-running
   Tier B. §10.3's most-ignored rule.
3. **Never ingest while chatting.** §4.5 — embedding saturates the GPU.
4. ⛔ **Export the workflow JSON and commit it** before the run. n8n's DB is not a backup —
   and this rule has been broken once already, at book 1, where a shared-code edit and an
   entire launcher existed only in n8n's database.
5. **Every number is labelled `predicted` or `measured`.** One without a label is a defect
   in the plan.
6. **A criterion that does not fit gets argued, not tuned.** Plan 06 §5.1 is the
   precedent: the stout guide misses the chunk-size band in *both* directions, and the
   right answer was a format-aware criterion, not a changed `max_tokens`.
7. ⚠️ **Run [`scripts/hyphen-probe.sh`](../../scripts/hyphen-probe.sh) on every PDF before
   ingesting it, and put the result in `text_repairs`.** Every extractor joins wrapped lines
   and drops the trailing hyphen, so a numeric range split across a line break silently
   fuses — `45-`/`90 minutes` becomes `4590 minutes`. No Docling option changes this and OCR
   does not help; both were tested ([`00a-rebuild.md`](00a-rebuild.md) §1.3).
   ⛔ **The script's output is a hypothesis, not the answer — check every pair against the
   real Docling result before pasting.** Book 1 is the precedent and it failed in both
   directions: one drafted pair matched **nothing** (which aborts the ingest, by design),
   and another, `["35","3-5"]`, matched **79** places and would have silently rewritten the
   copyright page's `TP583.P35 2013`. Meanwhile the site the README had recorded as at-risk
   turned out not to be, because Docling and `pdftotext` disagree about which wraps they
   join. See [`01-water.md`](01-water.md) §5.6.
8. ⭐ **Every plan carries a reset command (§3), and it must work on a partial run.**
   Replaces the stop-and-check-before-embedding step that plans 00a–01 used.

## 7. What this phase does to WF4

The archived agent design still holds, with **one coupling this phase breaks nine times.**

### 7.1 The coupling

The deployed system prompt names the corpus explicitly:

> *"You answer from that brewer's library — John Palmer's How to Brew and the BJCP 2021
> Style Guidelines — not from your own memory."*

Every source landed makes that sentence false, and a model told its library is two books is
being told the other seven do not exist. It appears **once** in
`n8n/demo-data/workflows/wf4-chat-agent.json`. The live tool description is already generic
(*"books and the BJCP 2021 style guidelines"*) and needs only its trailing clause revisited.

**The fix is to stop enumerating** — one sentence, written this way:

> *"You answer from that brewer's library — a collection of brewing books, style guidelines
> and practitioner articles — not from your own memory."*

⚠️ **Corrected 2026-08-12: this is no longer an *edit at book 1*, it is how WF4 is built at
book 4.5.** The original wording assumed WF4 would exist by book 1. It does not — §1.3 items 6
and 7 are unbuilt, §4.2 schedules them — so books 1–4 land against **no prompt at all**, and
the de-enumerated sentence goes in **from the first keystroke** rather than replacing an
enumerated one. [`01-water.md`](01-water.md) §9.1 already specifies it that way, and books 2–4
inherit it at **zero** cost, which was the whole point of not enumerating.

Enumerating a growing corpus inside a token-budgeted prompt is a maintenance liability, and
§6.2 measured that this prompt is already at the length where additions start costing accuracy.

⚠️ **It is still a prompt, so the rule applies without exception when 4.5 is built:** edit the
tracked JSON, `n8n import:workflow`, **re-activate** (import deactivates), restart n8n, run
`scripts/stress/tier1_routing.py`, and **read the knowledge row first** — it must be **30/30**
and the total must not fall below v3's **73/84**. v3.1 looked strictly safer than v3 and scored
20 points worse. Do not eyeball it.

**After book 4.5, re-run tier 1 only when** the prompt or a tool description changed, or a
Tier C test failed. Adding a source without a prompt change cannot move routing — different
variable — and 9 runs of an 84-call harness to detect nothing is a bad trade.

### 7.2 What does not change

`numCtx` 12288, top-6, `contextWindowLength` 6, the citation contract, the personal-scope
refusal sentence: **all unchanged.** Corpus size does not enter the context budget — six
chunks is six chunks whether the corpus is 563 or 3,100.

---

## 8. Corpus-level gates — run once, after source 9

Per-source gates catch per-source damage. These catch drift that only shows in aggregate,
and they are why the §10 eval baseline waits until the corpus is complete.

- [ ] All sources present in `kb.documents` with `is_current` versions, **0 embedding gaps**
- [ ] No single document > **25%** of `kb.chunks`
- [ ] The 5 standing questions still return their original rank-1 chunk in the top 3,
      measured against the 2026-08-07 baseline — not against the last source's
- [ ] Retrieval share: no probe question returns ≥ 3 of 6 from one document it doesn't own
- [ ] `tier1_routing.py` — **knowledge row 30/30**, total not below v3's 73/84
- [ ] **`mem.chat_turns` logging built** (`Prep turn` / `Log turn`) — ⭐ **scheduled: inside
      book 4.5's WF4 build, §4.2.** `chunk_ids` is a prerequisite for the retrieval-hit-rate
      metric, and every turn logged before the logging exists is a turn that cannot be scored,
      which is why it is no longer allowed to be "after"
- [ ] The coverage map in `homebrew_assistant_architecture.md` and corpus doc §3 matches
      what is actually ingested, **with the Radical Brewing row removed**
- [ ] **Only then** build the §10.1 eval set and record the §10.4 baseline

---

## 9. Status board

| # | Source | Plan | Probed | Built | Tier A | Tier B | Tier C |
|---|---|---|---|---|---|---|---|
| 0a | Rebuild + How to Brew | ✅ [00a](00a-rebuild.md) | ✅ 447, re-measured | ✅ **engine + launcher, both committed** | 🟡 **A3 watchable, `$5` left** | ✅ **Q1 and Q3 hit their documented ranks** | ⬜ n/a — no WF4 |
| 0b | Styles model | ✅ [00b](00b-styles.md) | ✅ re-measured 2026-08-12 | ✅ **22 nodes, committed** | ✅ **A0–A5b pass** | ✅ **covered by book 1's run** — Q10 returns 5 of 6 style cards | ⬜ n/a — no WF4 |
| **1** | **Water** | ✅ [01](01-water.md) | ✅ **440 raw, measured 2026-08-12** | ✅ **built and run — 382 chunks, 0 gaps** | ✅ **all pass; 18 of 19 predictions exact** | ✅ **10 questions; Layer 2 fires on nothing** | ⬜ n/a — no WF4 |
| **2** | **Yeast** | ✅ [02](02-yeast.md) | ✅ **526 raw, measured 2026-08-12** | ✅ **built and run — 463 chunks, 0 gaps** | ⭐ ✅ **A1–A7 recorded; 21 of 21 predicted numbers exact.** ⚠️ two predictions missed (A5 units, A6 over-count) · ⛔ **A3 not observed** | ✅ **10 questions; keep — 4 controls at rank 1; Layer 2 fires on nothing** | ⬜ n/a — no WF4 |
| **3** | **Malt** | ✅ [03](03-malt.md) | ✅ **458 raw, measured 2026-08-19** | ✅ **built and run — 340 chunks, 0 gaps.** ⭐ **committed *before* the run — standing rule 4 kept for the first time.** ⚠️ a duplicate launcher exists | ⭐ ✅ **A1–A7 recorded; 30 of 30 predicted numbers exact, none falsified.** ⛔ **A3 not observed** | ✅ **11 questions; keep — 5 controls at rank 1; Layer 2 fires on nothing.** ⛔ **the epigraph defect retrieved on 3** | ⬜ n/a — no WF4 |
| 4 | Draught manual | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ n/a — no WF4 |
| ⭐ **4.5** | **The agent** — search tool + WF4 + turn logging | ⬜ **§4.2 sets the timing; the build guide is [`archive/phase2/03b`](../archive/phase2/03b-wf4-build-guide.md)** | n/a | ⬜ | n/a | ⭐ **re-baseline after** | ⭐ **unblocks Tier C for 0a–4, retroactively** |
| 5 | BA 2026 + Study Guide | ⬜ **needs D31** | ⬜ | ⬜ | ⬜ | ⬜ | ⭐ **the merge/conflict eval lands here** |
| 6 | Beer faults | ⬜ | ✅ source JSON generated | ⬜ | ⬜ | ⬜ | ⬜ |
| 7 | Hop handbook | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 8 | Pastry stouts | ⬜ | ✅ file reviewed | ⬜ | ⬜ | ⬜ | ⬜ |
| 9 | Stout guide | ✅ [plan 06](../archive/06-stout-guide-ingest.md) | ✅ 679 chunks | ⬜ | ⬜ | ⬜ | ⬜ |

**Decisions wanted before planning starts**

| | | Status |
|---|---|---|
| **D30** | engine + per-book launcher, §2.1 | ✅ **settled** — your call |
| **D33** | full reset, §D33 above | ✅ **settled and executed** 2026-08-07 |
| **D32** | the styles model — `ref` schema, §5.3 | ✅ **accepted** — D33 removed its only counter-argument |
| **D32b** | one card or two, §5.5 | ✅ **closed 2026-08-12 — variant B, by argument.** A0 discards five prose fields; A busts the context budget by 36%. B is the only complete variant that fits. ⚠️ Whether the *split* helps retrieval is untested and recorded as such — §5.5 names it as the live suspect if style questions retrieve badly |
| **D31** | overlap policy, §3.3 | ⬜ **open — decide by book 5.** Books 1–4 each own their topic and present no scoping choice. `kb.documents.authority` ✅ shipped at book 0a, as planned |

**Nothing is blocked by a decision.** D31 is the only open one and it is not needed until
book 5.

**Where things actually stand, 2026-08-19 — ⭐ books 0a, 0b, 1, 2 and 3 are built and all five
are Tier-B verified. What is left is hygiene, one item has finally stopped repeating, and one
has stopped being cosmetic:**

| | What | Status |
|---|---|---|
| ✅ **Tier B, all five books** | the 5 standing questions from [`02-phase1-retrieval-gate.md`](../archive/02-phase1-retrieval-gate.md), the per-book positive controls, and the Layer-2 retrieval-share check | ✅ **run at 1,061 (2026-08-12), 1,524 and ⭐ 1,864 chunks (2026-08-19).** All three runs: **keep**, every positive control at rank 1, **Layer 2 fires on nothing**. ⭐ **At book 3 the five standing top-6s were byte-identical to the post-Yeast baseline** — 340 new chunks displaced nothing. ⚠️ Still a **post-Water** baseline — Q2, Q4 and Q5 have no pre-Water prior and never will |
| ✅ **A5 — the repair ledger** | node 26's `$5` | ✅ **done and proven.** Yeast's `clean` row carries four per-pair counts — `54 / 17 / 10 / 6`. ⭐ **Re-read from the live database 2026-08-19 rather than assumed** ([`03-malt.md`](03-malt.md) §1.1) — still stored, still per pair. ⚠️ **Book 3 cannot strengthen it**: Malt has two repair pairs and both read `applied = 2`, and a symmetric ledger cannot distinguish *stored* from *reconstructed*. Said in the plan instead of ticked |
| ✅ ⭐ **Standing rule 4 — broken at book 1, broken again at book 2, KEPT at book 3** | book 1: the untab edit and the `ingest-water` launcher · book 2: the whole `ingest-yeast` launcher · ⭐ **book 3: `ingest-malt.json`** | ⭐ ✅ **closed.** `ingest-malt.json` was exported out of n8n and committed in `a9bcefb` **before any execution of that workflow existed**. Books 1 and 2 recovered the artefact after the fact; book 3 is the first to preserve the property the rule is for |
| ⛔ **A3 — the dedup short-circuit** | run the launcher a second time; it must end at `Already ingested` in seconds | ⛔ **still never observed on a book launcher since book 0a.** ⚠️ Book 1's attempt (n8n executions 244/245) was launched **86 s before the first run committed**, so dedup found nothing and it ran the full path — finishing with status **`success`** having promoted nothing. **That is the engine's real behaviour on a duplicate concurrent run, and it is now on the record** |
| ⛔ **Housekeeping — the orphan, and ⭐ now we know why it survives** | the orphaned `Clean + normalise1` node | ⛔ **still live** — `measured` 2026-08-19, `wf1-ingest-book` is **27 nodes** in both the live workflow and the tracked JSON, still without the untab fix. ⭐ **Book 3 established the cause rather than just re-flagging it: no n8n CLI command edits a node** (`export`/`import`/`list`/`publish`/`unpublish`/`execute`/`audit` are the whole surface), and importing over the engine is a second variable in a run. ⛔ **It is a UI action and has to be done by hand** — which is why three sessions in a row have deferred it |
| ⛔ ⭐ **The epigraph-heading defect — now RETRIEVING, on three documents** | a chapter's epigraph byline becomes the `heading_path` of the chapter's opening prose | Water's `-J. Palmer` was a recorded cost. ⭐ `measured` at book 3: `-Bill Simpson` at **rank 3 on Q8** and **rank 6 on Q6**, `-William Littell Tizard…` at **rank 4 on Q10** — ⛔ **on questions Malt owns**, so the citation a user receives names the wrong person. ⛔ **No longer cosmetic. Fix at book 4**, which is already editing the cleaning node; repairing `heading_path` requires rebuilding `content` (plan 06 §4) |
| ⭐ ⛔ **A duplicate workflow, created at book 3** | **two** workflows are named `ingest-malt` | `hpW9P0n7fxXY9KdF` ran (executions 248/249) and is what `ingest-malt.json` tracks; `ingestMalt00001A` never ran. All 13 mapper fields were diffed and are identical. ⛔ **The unused one needs deleting and there is no `delete:workflow` in the n8n CLI** — same UI-only constraint as the orphaned node. ⚠️ **Worse than the orphan**: the next person to click Run has a 50% chance of picking the wrong artefact |
| ⭐ ⛔ **A `scripts/` defect, found at book 3** | `hyphen-probe.sh` returns a **false negative** on en-dashed numeric ranges | Docling normalises `–` to `-` **after** joining the wrap; the script matches an ASCII `-` on the `pdftotext` output, where the character is still an en dash. `measured`: `0 at-risk site(s)` reported while `212220°F` and `5565°F` sit in kept text. ⛔ **The first silent failure of the draft in three books.** Fix: `[-‐–—]$`. **Book 4 is a two-column PDF and should fix it there** — [`03-malt.md`](03-malt.md) §5.6 |
| ⚠️ **A cosmetic engine defect, found at book 2** | `Log ingest summary`'s promote message reads *"version 5 promoted"* while `kb.document_versions.version` is **1** | it interpolates the **row id**, not the version number, and has done since book 0a. Nothing reads the string. ⛔ **Not fixed at book 3** — deleting an orphaned node is not "touching the engine", and book 3's verdict is mapper-only. ⭐ **Handed to book 4**, whose verdict is already *not* mapper-only |

⚠️ **A3 cannot be checked retroactively** — a dedup short-circuit writes nothing to the
database, so it must be watched live: run the launcher, confirm it ends at
`Already ingested` in seconds with an unchanged `kb.chunks` fingerprint. ⭐ **Run it as the
*last* step of the ingest session**, after the log rows exist — book 1's attempt failed only
because it was launched too early.

⭐ **Book 3 is built and its record is closed.** [`03-malt.md`](03-malt.md) — the engine
unchanged, an `ingest-malt` launcher, `profile: book`, **340 chunks measured** from a
**458-chunk** probe. ⭐ **All five questions [`02-yeast.md`](02-yeast.md) handed over are
answered:** the glyph decoder is closed (Malt has **0** glyph runs, so the `+17` offset was a
property of one font subset); merge-forward is decided against and **tested** (7 token-floor
drops, **0** severed prerequisites, and a procedure-shaped control returns 6 of 6 at rank 1);
the pair-concentration metric is adopted and recorded for all 11 questions; ownership is
declared before the run and needed **zero** adjudications; and the compound-question warning
was applied rather than ignored.

⭐ **Standing rule 7 came out a third way here.** Book 1's draft had false positives, book 2's
matched nothing — ⛔ **book 3's was empty and *wrong*.** `hyphen-probe.sh` reported
`0 at-risk site(s)` while Docling fused two temperature ranges in kept text, because Docling
normalises en dashes to ASCII **after** joining the wrap. The final `text_repairs` is two pairs
the script never saw. See [`03-malt.md`](03-malt.md) §2.4, §5.6.

**Book 2 is built and its record is closed.** [`02-yeast.md`](02-yeast.md) — the engine
unchanged, an `ingest-yeast` launcher, `profile: book`, **463 chunks measured**. ⭐ **The
mapper carried the whole book**: a broken `ToUnicode` map in *Yeast*'s display font makes
`dropHeading` and `dropReferences` match **0 of 262** headings, so all 27 front- and
back-matter drops ride on `extra_drop_regex`, and four `text_repairs` pairs decode chemistry
(`α-amylase`, `β-amylase`) rather than hyphens. ⭐ **Standing rule 7 came out the other way
here:** the hyphen probe drafted **one** pair, `["2,3900","2,3-900"]`, and it matches **nothing**
in the Docling output — pasting it would have aborted the ingest, correctly. The final
`text_repairs` contains **no hyphen pair at all**. See [`02-yeast.md`](02-yeast.md) §2.4, §5.6.

**Book 1 is built.** [`01-water.md`](01-water.md) — the engine with an `ingest-water`
launcher, `profile: book`, **382 chunks measured**. ⭐ **Standing rule 7's warning earned its
⛔ there:** the hyphen probe drafted 5 pairs for this file and **two were wrong** — one
matched nothing (which aborts the ingest, correctly) and `["35","3-5"]` matched **79**
places. The final set is **4 pairs**, and the site the earlier draft of this README called
at-risk — pH `5.6-6.0` — **is not**, because Docling kept that hyphen where `pdftotext`
predicted a fusion. See [`01-water.md`](01-water.md) §5.6.
