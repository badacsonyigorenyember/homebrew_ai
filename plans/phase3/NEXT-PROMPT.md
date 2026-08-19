# Prompt for the next session

Paste everything below the line into a fresh Claude Code session started in
`/home/gorenyember/AI Homebrew Assistant`.

Written 2026-08-19, after **book 2's record was closed**. Every number below was measured
against the live stack on that date. **Re-verify rather than trusting it** — this file has been
wrong before.

> ⭐ **What changed since the last prompt:** book 2's record is closed. `02-yeast.md` §4 carries
> a measured column beside every prediction, all seven Tier A blocks, all ten Tier B questions
> and a scored exit checklist; README §9's book 2 row is ticked. **The corpus is at 1,524 chunks
> across four documents and nothing is mid-flight.**
>
> ⭐ **This prompt is the whole of book 3 — probe, plan, build, ingest, close the record.** It
> is not a planning-only session like the last two. The one gate is the run itself: standing
> rule 3 forbids ingesting while I am chatting, so **stop and ask before executing the
> launcher**, and do everything on both sides of that without stopping.

> ## ⭐ Progress marker — book 3 is RUN and SCORED, updated 2026-08-19
>
> ⛔ **Do not restart from the top if you are resuming.** What is finished:
>
> | Step | Status |
> |---|---|
> | 1 · probe first | ✅ **done** — live Docling, the ten form fields, **458 raw chunks, 160.85 s**. Hyphen probe plus three broadened sweeps. [`03-malt.md`](03-malt.md) §5 |
> | 2 · write `03-malt.md` | ✅ **done** — six sections, §5 measured first and placed last, all five handover questions answered in their own sections |
> | 3 · delete the orphaned `Clean + normalise1` | ⭐ ✅ **DONE 2026-08-19 10:58:46 UTC, in the UI**, five minutes before the run. **26 nodes** live and tracked; `Clean + normalise` byte-identical at 8,229 chars. Flagged at book 1, flagged at book 2, closed at book 3 |
> | 4 · build and export `ingest-malt` | ✅ **done** — exported and committed **before** the first run. ⭐ **Standing rule 4 kept for the first time in the phase** |
> | 5 · the ingest | ✅ **run 2026-08-19 11:03:53 → 11:06:55 UTC** (executions 248/249, **3 min 02 s**) — ⚠️ **triggered from the UI, not by the assistant** |
> | 6 · A3 last | ⛔ **NOT OBSERVED.** ⭐ The `promote` row exists, so the obstacle books 1 and 2 hit is gone and the check is one click. Recorded as *not observed*, never as passed |
> | 7 · close the record | ✅ **done** — §4.0 has a measured column, Tier A A1–A7 and all 11 Tier B questions are recorded inline, §4.6 is scored ✅/⚠️/⛔, README §9 and §4.3 updated |
>
> ⭐ **Result: 340 chunks, 30 of 30 predicted numbers exact, none falsified.** Tier B **keep** —
> all five prior rank-1 chunks still at **rank 1**, Q1–Q5 byte-identical to the post-Yeast
> baseline, all 5 controls at rank 1, Layer 2 fires on nothing. `kb.chunks` = **1,864**.
>
> ⛔ **Two things are open:** **A3** (one click — the `promote` row exists, so the race that
> broke book 1's attempt cannot happen) · ⭐ a **duplicate `ingest-malt` workflow**
> (`ingestMalt00001A`, never ran — the tracked JSON is the one that did; deleting it is a UI
> action, same constraint that kept the orphan alive for three books).
>
> ⚠️ **This file is now stale as an instruction set.** Rewriting it for **book 4 — the Draught
> Beer Quality Manual, 124 p**, the first source needing a new `ba_manual` cleaning profile, is
> the remaining task. [`03-malt.md`](03-malt.md)'s *"What book 3 hands to book 4"* section is
> the source material: nine numbered items, including the epigraph-heading fix, the
> `hyphen-probe.sh` bug and the chunk-size band.

---

Read `@plans/phase3/README.md` (the contract — **§6** is the six-section skeleton every plan
follows, **§4** is the order and why, **§9** is the status board) and
`@plans/phase3/02-yeast.md` (the most recent completed book, and the model for both halves of
this job — its §5 probe, its §4.0 gate table with a measured column beside every prediction,
its §4.1/§4.2 recorded results, and its closing *"What book 2 unblocks"* section, which is
**addressed to this session**).

**The job:** get ***Malt: A Practical Guide from Field to Brewhouse*** (John Mallett, 335 p)
into `kb.chunks` and close its record — write `plans/phase3/03-malt.md`, build the
`ingest-malt` launcher, run it, run Tiers A and B, and tick README §9.

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
  again at book 2, still there. ⭐ **Deleting it is in scope this time** — see step 3.
- ⭐ **`$5` works.** Yeast's `kb.ingest_log` `clean` row carries a four-entry `repairs` array
  with per-pair counts `54 / 17 / 10 / 6`. **Treat it as proven-once, not settled** — read the
  ledger back rather than assuming it.
- ⛔ **A3 — the dedup short-circuit — has never been observed on a book launcher since book 0a.**
  It writes nothing, so it cannot be checked after the fact. ⭐ **Book 3 is where that ends** —
  see step 6.

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

## What to actually do — in this order

### 1. Probe first (§5), before writing a word of the plan

Standing rule 1. Submit the file to the **live** Docling service with the engine's exact ten
form fields (`02-yeast.md` §5.0 records them byte for byte). Measure: raw chunk count,
chunks/page, median / max / p25 / p75 tokens, count under 30 and over 512, chunks with no
`page_from`, **top 20 headings by frequency**, the front-matter page range, table-chunk count,
and 3 real chunks verbatim.

⚠️ **A Docling probe is not an ingest** — it converts, it does not embed and does not write to
`kb`. Run it without asking.

Also run [`scripts/hyphen-probe.sh`](../../scripts/hyphen-probe.sh) — standing rule 7 — and
⛔ **check every drafted pair against the real Docling output before pasting it.** Both previous
books' drafts were wrong: Water's `["35","3-5"]` matched **79** places, and Yeast's single draft
matched **nothing**, which aborts the ingest by design.

### 2. Write `plans/phase3/03-malt.md`

README §6's six sections: **§0 verdict · §1 prerequisites · §2 build · §3 reset · §4 testing ·
§5 evidence.** ⭐ **§5 is measured first and placed last** — every predicted number in §4 must be
a derivation from it, and §4.0's gate table must exist **before** the run so it can be scored
after.

**Five questions `02-yeast.md`'s closing section hands over, each answered in its own section:**

- **Is Malt's front matter set in a working font?** If a second book shows the glyph problem,
  the shared-code decoder stops being a one-source workaround. (§0/§5)
- **Does the token floor take another dozen chunks?** Water lost 1, Yeast lost 15 (11 of them
  `Materials` lists). ⭐ **This is Malt's to decide** — three books is a design question, and
  `02-yeast.md` §4.4 names **merge-forward** as the fix to build. Argue it either way, but
  **decide**, and if the answer is *build it*, that is a shared-code change and §0's verdict
  says so out loud. (§2/§4.4)
- ⭐ **Add a procedure-shaped positive control** to Tier B, so the next token-floor sighting can
  be judged. Yeast's ten questions never asked one, which is why its evidence was weak.
- ⭐ **State each Tier B question's owning document *before* the run.** Layer 2's rule is
  *"≥ 3 of 6 from one document that does not own it"*, and five of Yeast's ten were resolved by
  adjudicating ownership after seeing the results. Declaring it up front makes it a prediction
  that can be wrong. (§4.2)
- ⭐ **Measure concentration on the (`heading_path`, `page_from`) pair, not on the heading
  string.** `measured`: heading-only reads 4 of 6 on Yeast's flocculation question and would
  have deleted three good answers; the pair metric reads **1** there and **4** on Water's Q8,
  which is the case that actually mattered. ⛔ **Do not build `PARTITION BY d.id,
  c.heading_path`.** (§4.2)

**Three more things §4 must carry:**

- **README §4 gives Malt its new capability: *"table-dense body under `table_mode=accurate`"*.**
  Measure how many chunks are tables and say whether it changes anything, rather than repeating
  the phrase.
- ⭐ **A runtime estimate built from the measured one, not the inherited one.** Yeast's whole run
  was **2 min 47 s** — 150 s of it the `Wait 15s` Docling poll loop, **16 s** the embedding of
  463 chunks. The *"~5–9 min to embed"* figure carried from book 1 was wrong by an order of
  magnitude, and *"past 20 minutes"* is far too loose a hung-run signal. **~6 minutes is the
  honest threshold.**
- **Corpus share.** Malt at ~500 chunks would be ~25% of ~2,024. ⭐ **Two documents have now
  crossed the 25% proxy and neither touched a question it does not own.** Argue it, do not tune
  it (standing rule 6).

**§3 is a reset command keyed on the SHA-256 above**, and it must work on a **partial** run.

### 3. Clear the engine's one piece of drift, *before* the build

⭐ **In scope this time, because book 3 is the last cheap moment.** Delete the orphaned
`Clean + normalise1` node so `wf1-ingest-book` is **26 nodes**, then re-export:

```bash
docker exec n8n n8n export:workflow --id=NoNCV2mkQEppWP7O --pretty --output=/demo-data/workflows/wf1-ingest-book.json && docker exec n8n chown 1000:1000 /demo-data/workflows/wf1-ingest-book.json
```

⚠️ **Deleting a node is a UI action**, so if it cannot be done from the CLI, say so and hand it
over rather than editing the tracked JSON and importing — an import deactivates workflows and
that is a second variable in a run that should have one.

⛔ **This does not touch `Clean + normalise` itself.** The live cleaning profile stays
byte-identical unless step 2 decided to build merge-forward, which is a separate, declared
change.

### 4. Build `ingest-malt` — 2 nodes, and export it **before** it runs

Copy `ingest-yeast` (`UvDB7iJdXH262CNl`) and change the 13 mapper fields. ⛔ **Three of the
thirteen must never be copied from another book** — `front_matter_max_page`, `extra_drop_regex`
and `text_repairs` — all three come from §5's probe of *this* file.

⛔ **Wait for Sub-Workflow Completion ON.** Off, the launcher reports success the moment Docling
is handed the file, and a failed ten-minute ingest looks like a green check.

**Then, standing rule 4, before the first run:**

```bash
docker exec n8n n8n export:workflow --id=<new-id> --pretty --output=/demo-data/workflows/ingest-malt.json && docker exec n8n chown 1000:1000 /demo-data/workflows/ingest-malt.json
```

⛔ **Commit it.** This rule was broken at book 1 and again at book 2, where `ingest-yeast.json`
existed only inside n8n's database for a week. **Third time is a pattern, not an accident** —
put the export in the build, not after it.

### 5. ⛔ Stop here and ask before running the ingest

Standing rule 3: **embedding saturates the GPU and must not happen while I am chatting.** Report
the predicted numbers from §4.0, confirm the launcher is exported and committed, and **wait for
me to say go.**

When I do, the run is yours to trigger and to watch. Either the Run button in the UI, or
headless:

```bash
docker exec -e N8N_RUNNERS_BROKER_PORT=5699 -e N8N_RUNNERS_BROKER_LISTEN_ADDRESS=127.0.0.1 n8n n8n execute --id=<new-id>
```

⚠️ **Expect ~3–5 minutes**, most of it the Docling poll loop. Past ~6 minutes, suspect
`keep_alive: -1` missing from `Ollama embed`; §3's reset makes starting over cheap.

### 6. ⭐ Run A3 **last**, in the same session

Fingerprint, run the launcher a **second** time, fingerprint again:

```bash
docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
```

⛔ **It must end at `Already ingested` in seconds**, with an identical hash both times. ⭐ **This
is the point of doing it last:** book 1's attempt failed only because it was launched **86 s
before the first run committed its version row**, so dedup found nothing, it ran the full path,
and it finished with status **`success`** having promoted nothing. Wait for the `promote` log
row to exist, then run it.

⛔ **A3 cannot be checked retroactively.** If it does not get run, record it as *not observed*,
not as passed.

### 7. Close the record, the way book 2's was closed

- **§4.0 gains a measured column** beside every prediction. Where a prediction was exact, say
  so; where it was not, **the gap is the finding**, and say which side the error was on —
  book 2's two misses were both arithmetic in the plan, not defects in the pipeline.
- **Tier A A1–A7 recorded inline**, each result under its command. ⛔ **A1 must include a row
  for every existing document** — that is the check that this ingest touched nothing else:
  `447 | 447 | 0 | 0`, `382 | 382 | 0 | 0`, `463 | 463 | 0 | 0`, `232`.
- **Tier B, 10 questions**, against the **post-Yeast** baseline in `02-yeast.md` §4.2 —
  ⛔ **not the post-Water one in `01-water.md`.** The keep/roll-back rule binds: out of top 6 on
  one question is a logged defect, on two or more is a reset (§3).
- **Layer 2 recorded for all 10 even when it fires nothing** — a recorded null is what makes the
  first real firing legible. It has now fired on nothing twice.
- **§4.6's exit checklist scored honestly**, ✅/⚠️/⛔ per line.
- **README §9's book 3 row ticked** — Plan, Probed, Built, Tier A, Tier B; Tier C stays
  `⬜ n/a — no WF4`. Update README §4.3's projected-corpus table with the measured total.
- ⛔ **Do not edit §5 after the run.** It is the pre-run evidence and its value is that it was
  written before the outcome was known. New measurements go in §4, labelled `measured`.

## Standing rules that matter here

- **Rule 1, measure then plan.** No §5, no plan. Books 1 and 2 landed **18 of 19** and
  **21 of 21** acceptance numbers because every one was derived from a probe.
- **Rule 5.** Every number labelled `predicted` or `measured`. An unlabelled number is a defect
  in the plan. ⭐ **Book 2's two wrong predictions were both numbers written *by hand* next to
  probe-derived ones** — a check that counted *sites* and asserted *rows*, and a residue counted
  on the wrong field. **Simulate the query you intend to run.**
- **Rule 4.** ⛔ Export and commit the launcher JSON **before** the first run — step 4.
- **Rule 3.** ⛔ Never ingest while I am chatting — step 5.
- **Rule 2.** One source per execution, one variable per run. ⚠️ If step 2 decides to build
  merge-forward, that is a **second** variable landing with a new book; say so explicitly and
  argue whether it should wait for book 4.
- **Rule 6.** A criterion that does not fit gets **argued, not tuned**.
- **§3.1, expressions.** Write every n8n expression as `{{ … }}`, **never** `={{ … }}`. The `=`
  belongs to the JSON export format; pasted into the UI's expression editor it becomes a literal
  and the field silently evaluates wrong. The exception is when quoting an exported JSON file —
  say which one.

## How to work

Verify claims against the live stack rather than trusting this prompt or the plan documents —
both have been wrong before, including in ways that cost a re-ingest. `docker compose` runs
from this checkout only, never a worktree. ⚠️ **A Docling probe is not an ingest** and is fine;
`ask.sh` embeds one short query per call and is fine; **the ingest itself waits for step 5.**
Do not run destructive SQL — §3's reset is mine to trigger.

**What I do on my end:** if something breaks, I will tell you. Don't write
stop-and-check-before-embedding steps inside the plan, and don't propose A/B or multi-variant
runs — propose one design, argue the runner-up on the record.

## After this session

Book 4 — the **Draught Beer Quality Manual**, 124 p — which is the first source needing a
**new cleaning profile** (`ba_manual`, two-column layout) and therefore the first since book 0a
whose verdict is *not* mapper-only. Then ⭐ **book 4.5, the agent**: WF4 +
`tool-search-brewing-knowledge` + `mem.chat_turns` logging, which is what finally makes **Tier C
runnable for books 0a–4 retroactively**. README §4.2 has the reasoning and the four reasons the
seam sits there.

⚠️ **One cosmetic engine defect is still open** and belongs to whichever session next touches
shared code: `Log ingest summary`'s promote message interpolates the version **row id**
(*"version 5 promoted"*) instead of the version number (**1**). Nothing reads it; wrong since
book 0a.

⛔ **Rewrite this file before that session.** A stale NEXT-PROMPT is how book 1 ended up
re-deriving things that were already measured.
