# Prompt for the next session

Paste everything below the line into a fresh Claude Code session started in
`/home/gorenyember/AI Homebrew Assistant`.

Written 2026-08-19, after **book 2's record was closed**. Every number below was measured
against the live stack on that date. **Re-verify rather than trusting it** — this file has been
wrong before.

> ⭐ **What changed since the last prompt:** book 2's record is closed. `02-yeast.md` §4 now
> carries a measured column beside every prediction, all seven Tier A blocks, all ten Tier B
> questions, and a scored exit checklist; README §9's book 2 row is ticked. **The corpus is at
> 1,524 chunks across four documents and nothing is mid-flight.** This prompt is the **book 3
> (Malt) plan** — a plan, not a run.

---

Read `@plans/phase3/README.md` (the contract — **§6** is the six-section skeleton every plan
follows, **§4** is the order and why, **§9** is the status board) and
`@plans/phase3/02-yeast.md` (the most recent completed book, and the model for what a finished
plan looks like — its §5 probe, its §4.0 gate table with a measured column beside every
prediction, and its closing *"What book 2 unblocks"* section, which is **addressed to this
plan**).

**One thing:** write **`plans/phase3/03-malt.md`** — the book 3 plan for *Malt: A Practical
Guide from Field to Brewhouse* (John Mallett), under §6's six-section contract.

⛔ **Do not ingest.** The plan ends at *"here is the launcher, here are the predicted numbers,
here is the reset command."* Running it is mine.

## What is already true — verify, don't assume

Measured 2026-08-19 against the live stack.

- **`kb.chunks` holds 1,524 rows**, four documents, **0 embedding gaps**, `is_current` = 4,
  `dims` = 1024 (one value):

  | slug | authority | page_count | chunks | share | min/median/max tok |
  |---|---|---|---|---|---|
  | `yeast-practical-guide` | `reference` | 305 | **463** | 30.4% | 30 / 313 / 512 |
  | `how-to-brew-palmer` | `reference` | 248 | 447 | 29.3% | 30 / 291 / 524 |
  | `water-comprehensive-guide` | `reference` | 239 | 382 | 25.1% | 31 / 342 / 513 |
  | `bjcp-2021-beer-styles` | `guideline` | — | 232 | 15.2% | — |

- **n8n holds five workflows** — `wf1-ingest-book` (`NoNCV2mkQEppWP7O`), `ingest-how-to-brew`,
  `ingest-water`, `ingest-bjcp-styles`, `ingest-yeast` (`UvDB7iJdXH262CNl`). ⛔ **None is an
  agent and none is a tool**, so Tier C is still not runnable — README §4.2 schedules that at
  **book 4.5**. Say so explicitly in §4's Tier C section rather than omitting it.
- ⚠️ **`wf1-ingest-book` is 27 nodes, not 26** — in the live workflow *and* in the tracked JSON.
  The 27th is the orphaned **`Clean + normalise1`**: no incoming connection, no outgoing
  connection, and its `jsCode` is 4,259 characters against the live node's 8,229 — it **lacks
  the untab fix**. A third divergent copy of the cleaning profile, flagged at book 1, flagged
  again at book 2, still there.
- ⭐ **`$5` works.** Yeast's `kb.ingest_log` `clean` row carries a four-entry `repairs` array
  with per-pair counts `54 / 17 / 10 / 6`. **Treat it as proven-once, not settled** — book 3
  reads the ledger back rather than assuming it.
- ⛔ **A3 — the dedup short-circuit — has never been observed on a book launcher since book 0a.**
  It writes nothing, so it cannot be checked after the fact.

### The source file, measured 2026-08-19

`shared/rag-files/pending/malt-a-practical-guide-from-field-to-brewhouse-978-1-938469-12-1-1-938469-12-7-978-1-938469-16-9.pdf`

| | `measured` |
|---|---|
| SHA-256 | `c85d388f8ff828313d2d364625072530d7e4b00c8b0a0235903af22a76169579` — §3's reset command is keyed on this |
| pages · title · author | **335** · *Malt: A Practical Guide from Field to Brewhouse* · **John Mallett** |
| ⭐ producer | **calibre 3.32.0** — ⭐ **the same toolchain as *Water***, not Yeast's `Creo Normalizer JTP` |
| page size | **612 × 792 pt (letter)** — a full-size trim, unlike Yeast's 3.5″ × 5.19″ |

⭐ **That producer line is a real prediction to make and then check.** Yeast's whole mapper
existed because a `Creo`-produced PDF shipped a broken `ToUnicode` map. *Malt* is calibre, like
*Water*, whose `extra_drop_regex` was **empty**. **Predict in §0 whether Malt needs one, then
let §5's probe falsify it.** Do not assume either way — `02-yeast.md` §0.3's decoder question
turns on exactly this.

## What to actually do

Write `03-malt.md` following README §6: **§0 verdict · §1 prerequisites · §2 build · §3 reset ·
§4 testing · §5 evidence.** ⭐ **§5 is measured first and placed last** — every predicted number
in §4 must be a derivation from it.

1. **Run the probe (§5) before writing anything else** — standing rule 1. Submit the file to the
   **live** Docling service with the engine's exact ten form fields (`02-yeast.md` §5.0 records
   them byte for byte). Measure: raw chunk count, chunks/page, median / max / p25 / p75 tokens,
   count under 30 and over 512, chunks with no `page_from`, **top 20 headings by frequency**, the
   front-matter page range, and 3 real chunks verbatim.
2. **Run [`scripts/hyphen-probe.sh`](../../scripts/hyphen-probe.sh)** — standing rule 7 — and
   ⛔ **check every drafted pair against the real Docling output before pasting it.** Both
   previous books' drafts were wrong: Water's `["35","3-5"]` matched **79** places, and Yeast's
   single draft matched **nothing**, which aborts the ingest by design.
3. **README §4 gives Malt a new capability to exercise: *"table-dense body under
   `table_mode=accurate`"*.** Measure how many chunks are tables and say whether that changes
   anything, rather than repeating the phrase.
4. **Answer the five questions `02-yeast.md`'s closing section hands over**, each in the section
   where it belongs:
   - **Is Malt's front matter set in a working font?** If a second book shows the glyph problem,
     the shared-code decoder stops being a one-source workaround. (§0/§5)
   - **Does the token floor take another dozen chunks?** Water lost 1, Yeast lost 15 (11 of them
     `Materials` lists). ⭐ **This is Malt's to decide** — three books is a design question, and
     `02-yeast.md` §4.4 names **merge-forward** as the fix to build. Argue it either way, but
     decide. (§2/§4.4)
   - ⭐ **Add a procedure-shaped positive control**, so the next token-floor sighting can be
     judged. Yeast's ten questions never asked one, which is why its evidence was weak.
   - ⭐ **State each Tier B question's owning document *before* the run.** Layer 2's rule is
     *"≥ 3 of 6 from one document that does not own it"*, and five of Yeast's ten were resolved
     by adjudicating ownership after seeing the results. Declaring it up front makes it a
     prediction that can be wrong. (§4.2)
   - ⭐ **Measure concentration on the (`heading_path`, `page_from`) pair, not on the heading
     string.** `measured`: heading-only reads 4 of 6 on Yeast's flocculation question and would
     have deleted three good answers; the pair metric reads **1** there and **4** on Water's Q8,
     which is the case that actually mattered. ⛔ **Do not build `PARTITION BY d.id,
     c.heading_path`.** (§4.2)
5. **§3 is a reset command keyed on the SHA-256 above**, and it must work on a **partial** run.
6. **§4 carries a gate table with a `Gate` column and a runtime estimate.** ⭐ **Use the measured
   runtime, not the inherited one:** Yeast's whole run was **2 min 47 s** — 150 s of it the
   `Wait 15s` Docling poll loop, **16 s** the embedding of 463 chunks. The *"~5–9 min to embed"*
   figure carried from book 1 was wrong by an order of magnitude, and *"past 20 minutes"* is far
   too loose a hung-run signal. **~6 minutes is the honest threshold.**
7. **Corpus share:** Malt at ~500 chunks would be ~25% of ~2,024. ⭐ **Two documents have now
   crossed the 25% proxy and neither touched a question it does not own.** Argue it in §4, do
   not tune it (standing rule 6).
8. ⛔ **Do not tick README §9's book 3 row beyond `Plan ✅` and `Probed ✅`.** Built, Tier A and
   Tier B are the run's to claim, not the plan's.

## Standing rules that matter here

- **Rule 1, measure then plan.** No §5, no plan. Plan 06's design turned on one
  heading-frequency table nobody would have guessed, and books 1 and 2 landed **18 of 19** and
  **21 of 21** acceptance numbers because every one was derived from a probe.
- **Rule 5.** Every number labelled `predicted` or `measured`. An unlabelled number is a defect
  in the plan. ⭐ **Book 2's two wrong predictions were both numbers written *by hand* next to
  probe-derived ones** — a check that counted *sites* and asserted *rows*, and a residue counted
  on the wrong field. Simulate the query you intend to run.
- **Rule 4.** ⛔ **Export and commit the launcher JSON *before* the first run.** Broken at book
  1 and again at book 2, where `ingest-yeast.json` existed only inside n8n's database for a
  week. Write the export command into §2 so it is part of the build, not an afterthought.
- **Rule 6.** A criterion that does not fit gets **argued, not tuned**.
- **Rule 2.** One source per execution, one variable per run.
- **§3.1, expressions.** Write every n8n expression as `{{ … }}`, **never** `={{ … }}`. The `=`
  belongs to the JSON export format; pasted into the UI's expression editor it becomes a literal
  and the field silently evaluates wrong. The exception is when quoting an exported JSON file —
  say which one.

## How to work

Verify claims against the live stack rather than trusting this prompt or the plan documents —
both have been wrong before, including in ways that cost a re-ingest. `docker compose` runs
from this checkout only, never a worktree. **Do not ingest or embed anything while I am chatting
with the assistant** — embedding saturates the GPU. ⚠️ A **Docling probe** is not an ingest and
is fine; `ask.sh` embeds one short query per call and is fine. Do not run destructive SQL.
Export and commit every workflow JSON **before** running it, not after.

**What I do on my end:** if something breaks, I will tell you. Don't write
stop-and-check-before-embedding steps, and don't propose A/B or multi-variant runs — propose
one design, argue the runner-up on the record.

## After this session

The run itself, then the book 3 record closed the way book 2's was: a measured column beside
every prediction, Tier A recorded inline, Tier B against the **post-Yeast** baseline in
`02-yeast.md` §4.2 (not the post-Water one), and README §9 ticked.

⚠️ **Three items are open and belong to whichever session touches the engine next** — most
likely book 4 or book 4.5, since book 3 should again be mapper-only:

1. **A3, live** — run the launcher a second time as the **last** step of the ingest session,
   after the log rows exist. Book 1's attempt failed only because it was launched 86 s too early.
2. **Delete the orphaned `Clean + normalise1` node** and re-export, so the engine is 26 nodes.
3. **`Log ingest summary`'s promote message** interpolates the version **row id** (*"version 5
   promoted"*) instead of the version number (**1**). Cosmetic, nothing reads it, wrong since
   book 0a.

⛔ **Rewrite this file before that session.** A stale NEXT-PROMPT is how book 1 ended up
re-deriving things that were already measured.
