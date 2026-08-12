# Prompt for the next session

Paste everything below the line into a fresh Claude Code session started in
`/home/gorenyember/AI Homebrew Assistant`.

Written 2026-08-12, after book 1 (Water) landed. Every number below was measured against the
live stack on that date. **Re-verify rather than trusting it** — this file has been wrong
before.

---

Read `@plans/phase3/README.md` (the contract — note §6 was rewritten on 2026-08-12 and the
skeleton is now six sections, not nine) and `@plans/phase3/01-water.md` (the worked example
written under the new contract; its §2.2 mapper table and §5 evidence tables are the models
to copy).

**One thing:** write me the detailed plan for **book 2 — Yeast** at `plans/phase3/02-yeast.md`.

Follow README §6's skeleton exactly, in order: **§0 verdict · §1 prerequisites · §2 build ·
§3 reset · §4 testing · §5 evidence**. §5 is written *first* and placed *last* — standing
rule 1 is measure-then-plan, and every predicted number in §4 has to be a derivation from
§5's probe output rather than a guess.

Four standing rules matter most here:

- **Rule 1, measure then plan.** §5 is a **real Docling probe** against the live service with
  the engine's exact ten form fields. Raw chunk count, chunks/page, median/max/p25/p75
  tokens, count under 30, count over 512, chunks with no `page_from`, chunks with no
  headings, **the top 20 headings by frequency**, the front-matter page range, and three real
  chunks verbatim.
- **Rule 7, the hyphen probe.** Run `./scripts/hyphen-probe.sh` on the Yeast PDF, then
  **check every candidate site against the Docling output**, not against `pdftotext`. Water
  proved both failure directions: one candidate (`5.6-6.0`) was never fused at all — Docling
  kept the hyphen where `pdftotext` predicted loss, and **a pair that matches nothing throws
  and aborts the ingest**. Another (a bare `35` → `3-5`) matched **79 sites** including a
  library code on the copyright page, and would have silently written 79 wrong numbers.
  Anchor every pair in enough surrounding words to be unique, and count the matches before
  writing it down.
- **Rule 5.** Every number labelled `predicted` or `measured`. No unlabelled numbers.
- **§3.1, expressions.** Write every n8n expression as `{{ … }}`, **never** `={{ … }}`. The
  `=` belongs to the JSON export format; pasted into the UI's expression editor it becomes a
  literal and the field silently evaluates wrong. The exception is when you are quoting an
  exported JSON file — say which one you are looking at.

## What is already true — verify, don't assume

Measured 2026-08-12.

- **`kb.chunks` holds 1,061 rows**, three documents, **0 embedding gaps**:

  | slug | authority | doc_type | page_count | chunks |
  |---|---|---|---|---|
  | `how-to-brew-palmer` | `reference` | `book` | 248 | 447 |
  | `water-comprehensive-guide` | `reference` | `book` | 239 | 382 |
  | `bjcp-2021-beer-styles` | `guideline` | `style_guide` | — | 232 |

  ⚠️ `page_count` is `max(page_to)` over **kept** chunks, not the PDF's page count — Water is
  a 273-page book showing 239 because the Index is dropped. Yeast is 325 pages; a
  `page_count` of 325 would mean its back matter survived.

- **Four n8n workflows exist**, all exported and committed, all matching the live database:

  | Workflow | id | Nodes |
  |---|---|---|
  | `wf1-ingest-book` — the engine | `NoNCV2mkQEppWP7O` | 26 live + **1 orphan, see §1** |
  | `ingest-how-to-brew` | `BAe1fP1g7ZUsbIaq` | 2 |
  | `ingest-water` | `ciWYDt5MhFseACiN` | 2 |
  | `ingest-bjcp-styles` | `Ejf3ESE3SK1XBqe3` | 22 |

- **The repair ledger works.** `Log ingest summary` now reads `$5` — the `clean` row builds
  `jsonb_build_object('stats', $2::jsonb, 'drops', $3::jsonb, 'repairs', $5::jsonb)`. The
  parameter had been passed and silently discarded by pg-promise for two books. **Yeast is the
  first ingest whose repair ledger will actually be recorded** — check it in Tier A rather
  than assuming, and treat it as a fresh capability, not a settled one.
- **The engine untabs before it repairs.** `Clean + normalise` normalises `\t` → space in
  `text`, `raw_text` and every heading, *above* the repair loop. This was Water's one shared
  edit: 440/440 of its chunks were tab-delimited (50.5% of all whitespace) where How to Brew
  had zero tabs in 447 chunks. **Measure Yeast's tab density in §5** — if it is another
  tabbed file the code already handles it, and if it is not, that is worth one line saying so.
  Consequence for you: `text_repairs` pairs are matched against *untabbed* text, so write them
  with ordinary spaces even when the bytes on disk have tabs.
- Postgres nodes use the **`Postgres account`** credential. `n8n_agent` is the read-only agent
  role and **cannot see `kb`** — never pick it on a write node.
- There is **still no WF4 and no search tool**, so Tier C is not runnable. That is a decision,
  not a skip, and §4 must say so explicitly rather than omitting the tier.

## What must be done first

Only three things, and none of them blocks the plan being *written*.

1. ⚠️ **`wf1-ingest-book` still carries an orphaned `Clean + normalise1` node** — no
   connections, and its code **lacks the untab fix**, so it is now a third divergent copy of
   the cleaning profile sitting in tracked JSON. Harmless to execution, exactly the drift the
   schema rules forbid. Delete it in the UI and re-export so the engine is 26 nodes as
   documented.
2. **A3 — watch the dedup short-circuit live.** ⚠️ **This cannot be checked retroactively**: a
   short-circuit writes nothing, so the database cannot tell you it happened. Run
   `ingest-water` a second time; it must end at `Already ingested — stop` in **seconds, not
   minutes**, with an identical fingerprint:

   ```bash
   docker exec supabase-db psql -U postgres -d postgres -Atc "select md5(string_agg(content_sha256, ',' order by chunk_index)), count(*) from kb.chunks;"
   ```

   Expect `1061`. If it instead runs a full Docling conversion, the dedup branch is broken and
   **Yeast would duplicate rather than dedup** — stop and fix it before book 2.
3. **The Tier B baseline is post-Water, and that is now permanent.** A pre-Water baseline is
   no longer takeable. All 10 questions were measured on 2026-08-12 and are recorded in
   `01-water.md`; both gates passed (Q1 → `10.4 Yeast Starters and Diacetyl Rests` p.98 at
   rank 1; Q3 → `Bittering`/`Flavoring`/`Finishing` p.41 at ranks 1–3). Use that table as
   book 2's before-baseline; do not re-derive it, and do not re-run it after Yeast is ingested
   and call it a baseline.

## What book 2 is, and is not

**Is:** *Yeast — The Practical Guide to Beer Fermentation* (White & Zainasheff, **325 pages**,
`measured` via `pdfinfo`), through the existing engine with a new **2-node `ingest-yeast`
launcher**, `profile: book`, `authority: reference`, `doc_type: book`.

- Container path: `/data/shared/rag-files/pending/yeast-the-practical-guide-to-beer-fermentation-0937381969_compress.pdf`
  — n8n does not see the host path.
- Host SHA-256, `measured` 2026-08-12:
  `2f30d7e5d8a965df00dbd225f57c4d759dd8ab90f99974b0ffee9b39f54266a4`. This is the literal §3's
  reset command is keyed on. **Re-verify it** with `sha256sum` before writing it into the plan.

**Is not:** a new workflow, a new cleaning profile, or a schema change.

⭐ **README §4 predicts book 2 costs "nothing — should be near-free."** That prediction is the
point of running it. Water needed the 13-field mapper *plus* three lines of shared code, and
that was argued loudly. **If Yeast needs anything outside the launcher's mapper, say so in §0
in the strongest terms**, because two books in a row exceeding "one Set node" means the D30
split does not hold — and you want to learn that on book 3 of 9, not book 8. Equally: if it
genuinely is mapper-only, say *that* plainly. A near-free book is the evidence D30 was
designed to produce, and it only counts if it is recorded.

## The things most likely to go wrong

- ⭐ **Yeast is the first source expected to legitimately win the standing questions**, and the
  keep/roll-back rule was not written with that in mind. Q1 is diacetyl rests and Q4 is
  pitching rate and rehydrating dry yeast — Yeast is *the* book on both, and displacing
  Palmer's `10.4 Yeast Starters and Diacetyl Rests` from rank 1 would be the pipeline working,
  not regressing. **Predict in §4, before the run, which of the five standing questions you
  expect to move and to what** — so that a shift is legible as expected rather than argued
  about afterwards. The rule itself is unchanged and still binds: out of top 6 on one is a
  logged defect, on two or more is a reset.
- **Overlap is medium on two axes**, per README §3.2: *off-flavours* (fault list × How to Brew
  × Yeast × Draught manual) and *malt/yeast basics* (How to Brew × Yeast). Layer 1 keeps
  topical overlap **unconditionally** — the 20-page answer and the 325-page answer are
  different answers, and which is correct depends on the question. §2's overlap block should
  state **expected overlap chunks dropped: 0** and say why.
- **Layer 2 gets its first real test at four documents.** On Water it fired on **nothing** —
  the most striking measurement being that Water is 36.0% of the corpus yet took **0 of 6
  slots** on the style question. Run the check over all 10 questions and **record it even when
  it fires nothing**; a recorded null is what makes the first real firing legible. Remember
  Layer 3 is built **only** when Layer 2 fires, not when the corpus-share proxy does.
- **Corpus share will cross 25% and that is expected.** Yeast at a predicted ~590 chunks
  against a ~1,651 total is `predicted` ~36%. Argue it rather than tuning it (standing rule 6).
- ⚠️ **Carry forward one finding from Water that Layer 3 would not fix.** Q8 spent **5 of 6
  slots on a single heading on a single page**. The concentration is *intra*-document, so
  Layer 3's `PARTITION BY d.id` is the wrong shape for it. Recorded, not acted on. If Yeast
  reproduces the pattern on a second document, that promotes it from a curiosity to a design
  question — so check for it rather than only running the Layer-2 query.
- **The other Water defect worth watching:** bare attribution chunks (`-J. Palmer`) retrieved
  at rank 4 on two questions. If Yeast has an equivalent — pull quotes, sidebar bylines,
  "Chris White" attributions — a token floor may not catch them, and §2's drop rules should.
- **`front_matter_max_page` and `extra_drop_regex` are per-book constants** and must come from
  §5's probe, not from another book. Palmer's How to Brew is `6`; Water is **`18`**, because
  Water's chunk 3 is a *table-of-contents line* promoted to a heading — which no regex can
  distinguish from a real chapter heading, and which is the whole argument for a page rule
  over a heading rule. Find Yeast's own number the same way.
- **Back matter is the other end of the same problem.** Water dropped 34 chunks of Index and 4
  of References. A 325-page book almost certainly has both plus an appendix — identify them in
  §5 by heading, and predict the drop counts by page range so §4 can check them.

## How to work

Verify claims against the live stack rather than trusting this prompt or the plan documents —
both have been wrong before, including in ways that cost a re-ingest. `docker compose` runs
from this checkout only, never a worktree. **Do not ingest or embed anything while I am
chatting with the assistant** — embedding saturates the GPU; a Docling *probe* is fine, a full
ingest is not. Do not run destructive SQL; write it in §3 and let me trigger it. Export and
commit every workflow JSON **before** running it, not after.

**What I do on my end:** build the whole workflow from §2, then run it. If something breaks, I
will tell you. Don't write stop-and-check-before-embedding steps, and don't propose A/B or
multi-variant runs — propose one design, argue the runner-up on the record, and make §3's
reset command good enough that starting over is cheap.
