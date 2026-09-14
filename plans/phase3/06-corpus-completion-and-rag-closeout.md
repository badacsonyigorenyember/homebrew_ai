# Plan 06 — finish the corpus (books 8 + 9) and close out the RAG pipeline

**Written:** 2026-09-14 · **Every number below was measured against the live stack that
day**, not carried from an earlier plan. Commands are included so each one can be re-run.
**Standing rule 1 applies to this plan too: re-measure before trusting it.**

**Scope:** the last two of the eleven sources ([`README.md`](README.md) §4.1 rows 8 and 9),
plus the prompt/description/eval work that makes the pipeline *correct* rather than merely
*running*.

---

## §0 — Read this first

### 0.1 ✅ The MCP question, answered up front

> **You asked: can the required workflows be added to n8n over MCP? — ✅ Yes, and for the two
> new launchers it is the *safe* path, not just an available one.**

| Evidence | `measured` 2026-09-14 |
|---|---|
| MCP server reachable | ✅ `search_workflows` returned **15** workflows |
| Create permission | ✅ every workflow row carries `workflow:create`, `workflow:update`, `workflow:delete` in `scopes` |
| Credentials visible | ✅ **4** — `Postgres account` `fDjeFLjBj3r9berH`, `n8n_agent` `6vilCQCI30RUdvfd`, `Ollama account` `mvKFL1A3chsbllnL`, `Postgres — mem_writer` `memWriterCred001` |
| ⭐ **The `$input` write-back hazard does not apply to the launchers** | ✅ **all five existing book launchers contain ZERO Code nodes and ZERO `$input` sites** (`ingest-water`, `ingest-yeast`, `ingest-malt`, `ingest-draught`, `ingest-how-to-brew` — each is exactly 2 nodes: `manualTrigger` + `executeWorkflow`) |

⛔ **But there is one place MCP must NOT be used until a probe settles it.** The book 9 work
edits `wf1-ingest-book`'s `Clean + normalise` node. That workflow carries **2 `$input` sites**
(`Assert task finished`, `Assemble embed input`), and
[`.claude/skills/n8n-workflows/reference/api-and-mcp-writeback.md`](../../.claude/skills/n8n-workflows/reference/api-and-mcp-writeback.md)
records the open question — untested on this instance — of whether a programmatic write strips
the `$input` prefix and silently produces `.first().json`, a syntax error that only surfaces at
run time.

**So the rule for this plan is:**

| Target | Path | Why |
|---|---|---|
| ⭐ **`ingest-pastry-stouts`, `ingest-stout-guide`** (new, 2 nodes, no Code) | ✅ **MCP `create_workflow_from_code`** | nothing to strip |
| ⛔ **`wf1-ingest-book`** (engine, 5 Code nodes, 2 with `$input`) | ⛔ **not over MCP until Step C1's probe passes.** Until then: n8n UI, or edit the tracked JSON and `n8n import:workflow` | a stripped `$input` breaks the engine for **all ten** ingested documents' re-runs |
| ⚠️ **`chat-agent`, `wf-step-retrieve`** (prompt/description edits, Code nodes present) | ⚠️ same gate as the engine | `wf-step-retrieve` is the **live retrieval path** |

**Step C1 runs that probe first, and it is cheap (~10 min).** If `$input` survives, every
remaining edit in this plan may go over MCP and the reference doc gets its answer recorded. If
it does not, the fallback is the CLI import path the repo already uses (standing rule 5).

### 0.2 What is left, in one screen

**Nine of eleven sources are in. Two remain, and neither is blocked by a decision.**

| # | Source | State `measured` 2026-09-14 | What it needs |
|---|---|---|---|
| **8** | **BYO Pastry Stouts** — `byo_pastry_stouts.md`, 1,488 words | ⬜ not ingested | ⭐ **a 2-node launcher and nothing else.** §2 — probed today, engine unchanged |
| **9** | **Stout Style Guide** — `Stout-Style-Guide.pdf`, 84 p | ⬜ not ingested | ⛔ **a launcher AND the `byo_magazine` cleaning profile**, which is deliberately absent from the engine. §3 |
| — | **RAG correctness** | ⚠️ running, but three defects found today | §4 — prompts, descriptions, and a **broken eval** |

⛔ **The single most important finding in this plan is not about books at all.** See §0.3.

### 0.3 ⛔ The grounding eval's negative controls are now false

[`scripts/stress/grounding_eval.py`](../../scripts/stress/grounding_eval.py) proves D38 — the
hard refusal — using three anchors the corpus was supposed *not* to cover. **Book 7 (hops) put
two of them into the library on 2026-09-14.**

```bash
# measured 2026-09-14 — the line at grounding_eval.py:37 claims "Nelson Sauvin 0 · Sabro 0"
docker exec supabase-db psql -U supabase_admin -d postgres -tAc \
"select 'kb', count(*) from kb.chunks where raw_content ilike '%Nelson Sauvin%'
 union all select 'ref.hops', count(*) from ref.hops where name ilike '%Nelson Sauvin%';"
```

| Eval case | Anchor | `measured` 2026-09-14 | Verdict |
|---|---|---|---|
| `U01` | Nelson Sauvin | ⛔ **`kb.chunks` 2 · `ref.hops` 1** | ⛔ **no longer uncovered** |
| `U02` | Sabro | ⛔ **`kb.chunks` 2 · `ref.hops` 2** (`Sabro`, `Sabro Cryo`) | ⛔ **no longer uncovered** |
| `U03` | kveik | ✅ `kb.chunks` **0** · `ref` **0** | ✅ still valid |

⚠️ **And the same two names are baked into the `chat-agent` system prompt** as the worked
example for `brainstorm_pairing` (*"What hops go with Nelson Sauvin"*). That example now
instructs the model to treat a **covered** ingredient as the archetype of an *uncovered* one.

⭐ **This is the thing that would quietly make the pipeline look correct while being wrong**,
and it is why §4 is not optional polish. Fixed in Step C3 and Step C5.

### 0.4 The order, and why it is forced

| Session | Step | Est. | Why it must be here |
|---|---|---|---|
| **A** | §1 preflight + §2 **book 8** | ~60 min | smallest source, zero engine change — it proves the launcher-over-MCP path on something cheap to reset |
| **B** | §3 **book 9** | ~3 h | ⛔ needs the engine edit, so it must follow Step C1's `$input` probe *or* use the UI path |
| **C** | §4 **RAG closeout** | ~2.5 h | ⛔ **must be last.** The eval anchors and the corpus-share numbers both change when books 8 and 9 land; re-baselining before the corpus is final measures a corpus that is about to change |

⛔ **Do not reorder B before A.** Book 8 is the only remaining source that touches nothing
shared; if the launcher-over-MCP path has a flaw, it is discovered on 15 chunks rather than
inside a 26-node engine edit.

⚠️ **Step C1 (the `$input` probe) is listed in session C but may be run at any time, and
session B needs its answer.** Run it at the start of session B if session C is far off.

---

## §1 — Prerequisites and the measured baseline

### 1.1 What is already true — every row is a command that was run

```bash
cd "/home/gorenyember/AI Homebrew Assistant"
docker ps --format '{{.Names}}\t{{.Status}}' | sort
```

| Check | Command | `measured` 2026-09-14 |
|---|---|---|
| Stack up | `docker ps` | ✅ **16 containers**, `gpu-amd` profile — `supabase-db`, `supabase-kong`, `n8n`, `ollama`, `docling`, `static-files` all healthy |
| Corpus | SQL below | ✅ **2,434 chunks · 2,434 embeddings · 0 gaps · 1 distinct dim (1024) · 10 documents** |
| Reference tables | SQL below | ✅ `ref.styles` **285** (116 BJCP + 169 BA) · `ref.hops` **72** · `ref.faults` **21** |
| Workflows | SQL below | ✅ **15 live**, 0 archived, **15 tracked JSON** — standing rule 4 green |
| Agent | SQL below | ✅ `mem.chat_turns` **54** · `obs.runs` **28** (11 `ok`, 9 `refused`, 8 `failed`) · `obs.retrievals` **23** |
| Prompts | SQL below | ✅ `obs.prompts` **3** active · `obs.profiles` **4** (`extract`/`creative`/`critique`/`compose`, all `gemma4:12b`) |
| Models | `curl …/api/tags` | ✅ `gemma4:12b` 7.6 GB · `bge-m3:latest` 1.2 GB |
| Docling | `curl …/openapi.json` | ✅ **Docling Serve 1.19.0**, `docling` 2.95.0 — ⭐ **the same version archived plan 06's probe ran on**, so its 679-chunk baseline is still comparable |
| ⭐ Retrieval works | `./scripts/ask.sh` | ✅ *"what causes diacetyl in stout"* → 6 rows, rank 1 *How to Brew* p.56, and ⭐ **`Beer Fault List › Diacetyl` at rank 5** — book 6's cards are live in retrieval |
| Both sources present | `docker exec n8n ls …` | ✅ `byo_pastry_stouts.md` (8,633 B) and `Stout-Style-Guide.pdf` (9,735,054 B) are both in the n8n container at `/data/shared/rag-files/pending/` |

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select (select count(*) from kb.chunks) chunks,
       (select count(*) from kb.chunk_embeddings) embs,
       (select count(*) from kb.chunks c
          left join kb.chunk_embeddings e on e.chunk_id=c.id where e.chunk_id is null) gaps,
       (select count(distinct vector_dims(embedding)) from kb.chunk_embeddings) dims,
       (select count(*) from kb.documents) docs,
       (select count(*) from ref.styles) styles, (select count(*) from ref.hops) hops,
       (select count(*) from ref.faults) faults;"

docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -c \
  "select name, active, \"isArchived\", json_array_length(nodes) n from workflow_entity order by name;"
```

The ten ingested documents, for reference:

| id | slug | doc_type | chunks |
|---|---|---|---|
| 1 | `bjcp-2021-beer-styles` | style_guide | 232 |
| 2 | `how-to-brew-palmer` | book | 447 |
| 3 | `water-comprehensive-guide` | book | 382 |
| 5 | `yeast-practical-guide` | book | **463** ← largest, 19.0% |
| 6 | `malt-practical-guide` | book | 340 |
| 7 | `draught-beer-quality-manual` | book | 226 |
| 40 | `ba-2026-beer-styles` | style_guide | 169 |
| 44 | `bjcp-style-study-guide` | style_guide | 82 |
| 46 | `beer-fault-list` | datasheet | 21 |
| 88 | `hop-variety-handbook` | datasheet | 72 |

### 1.2 What must be done first

⛔ **Two items, both small, both ordering-forced.**

1. **Commit the working tree before anything runs.** `git status --short` currently shows
   `M CLAUDE.md`, `M README.md`, `M homebrew_assistant_architecture.md`,
   `M plans/phase3/NEXT-PROMPT.md`, and **untracked** `.claude/`,
   `backup/n8n-deleted-20260913/`, `n8n/demo-data/workflows/ingest-draught.json`,
   `plans/research/`. ⛔ **`ingest-draught.json` untracked is standing rule 4 broken** — it is
   the book 4 launcher and it has already run.
2. ⭐ **Standing rule 4 for this plan: export and commit each new launcher BEFORE its first
   run.** Books 3, 5, 6 and 7 kept this. Keep it here.

⛔ **No schema change is required by either book.** `db/init/` is unchanged and
`docker-compose.yml`'s hardcoded `db-init` file list needs no new entry. Stated explicitly so
its absence is a decision, not an omission.

---

## §2 — Book 8: BYO Pastry Stouts

### §2.0 — The verdict

⭐ **Engine, unchanged. A 2-node launcher and nothing else.** This is the fourth
consecutive mapper-only source.

⭐ **And the open question the README has carried since 2026-08-07 — *"first non-PDF input —
does the engine take `.md`?"* — is ✅ ANSWERED YES, measured today, before the plan was
written.**

```bash
# the probe that answered it — submitted with the EXACT form fields the engine's
# `Docling submit` node already sends, changing only convert_from_formats
curl -s -X POST http://localhost:5001/v1/chunk/hybrid/file/async \
  -F "files=@shared/rag-files/pending/byo_pastry_stouts.md" \
  -F "convert_from_formats=md" -F "convert_image_export_mode=referenced" \
  -F "convert_do_ocr=false" -F "convert_pdf_backend=dlparse_v4" \
  -F "convert_table_mode=accurate" -F "chunking_tokenizer=BAAI/bge-m3" \
  -F "chunking_max_tokens=512" -F "chunking_include_raw_text=true" \
  -F "chunking_use_markdown_tables=true"
```

`measured` 2026-09-14, task `95adf6a9-22a1-457c-aed5-59ef651046d9`: `task_status: success`,
`documents[0].status: success`, **15 chunks**. Docling's `InputFormat` enum accepts
`md` alongside `pdf`, `docx`, `pptx`, `html`, `csv`, `xlsx` and others — so `source_format`
being a launcher parameter was the right design and it needed no change to exercise.

| Engine node | Verdict |
|---|---|
| all 26 nodes | ✅ **correct as-is, change nothing** |
| `Clean + normalise` | ✅ ⭐ **`profile: book` works unmodified** — simulated over the 15 real probe chunks, **0 drops** |

⛔ **Nothing outside the launcher changes.** The D30 split holds.

### §2.1 — ⛔ The one thing that is genuinely new: no page numbers

⚠️ **Markdown has no pages, so Docling returns no `page_numbers`, so every chunk stores
`page_from = NULL`.** `measured`: **15 of 15**. Three consequences, all checked:

| Consequence | Status |
|---|---|
| `front_matter_max_page` never fires | ✅ **safe by construction** — the rule is guarded `if (pageTo !== null && …)`. ⚠️ The field must still be a **finite number** or `Clean + normalise` throws at line 5. **Set it to `0`**, which is the honest value |
| `stats.page_count` = `Math.max(...kept.map(k => k.page_to ?? 0))` | ⚠️ **stores `0`, not `NULL`** — cosmetic, and it is the first document where `page_count` is not a page count. Note it in the record; do not "fix" it |
| Citations render without a page | ✅ **already handled** — `wf-step-retrieve`'s `Return rows` builds the label as `` `[S1] ${doc_title} · ${heading}${x.page ? ` · p.${x.page}` : ''}` ``. A null page yields `[S1] Pastry Stouts: Tips from the Pros · Ben Romano… > Yeast selection` with no dangling `p.` |

⭐ **That last row is worth stating plainly: the citation path was already null-safe, and this
book is the first source to prove it.**

### §2.2 — The build: the launcher mapper table

**Create `ingest-pastry-stouts`, modelled byte-for-byte on
[`ingest-draught.json`](../../n8n/demo-data/workflows/ingest-draught.json).**

Two nodes: `manualTrigger` → `executeWorkflow` targeting **`NoNCV2mkQEppWP7O`**
(`wf1-ingest-book`), `mappingMode: defineBelow`.

⛔ **Copy the `workflowInputs.schema` array verbatim from `ingest-draught.json`.** It is the
13-entry array n8n derives from the engine's `executeWorkflowTrigger`; a launcher written
without it can save cleanly and pass nothing at run time.

| # | Field | Value | Where the value came from |
|---|---|---|---|
| 1 | `file_path` | `/data/shared/rag-files/pending/byo_pastry_stouts.md` | ✅ `docker exec n8n ls` — confirmed present, 8,633 B |
| 2 | ⭐ `source_format` | `md` | ⭐ **the probe** — Docling `InputFormat` accepts it; `documents[0].status: success` |
| 3 | `slug` | `byo-pastry-stouts` | kebab-case convention of the other nine rows |
| 4 | `title` | `Pastry Stouts: Tips from the Pros` | the file's H1, line 1 |
| 5 | ⭐ `doc_type` | `article` | ⭐ **the first `article` in the corpus.** `kb.documents_doc_type_check` allows `book\|style_guide\|article\|datasheet\|note`. It is a magazine column, not a book — see §2.5 |
| 6 | `authors` | `Ben Romano;Brian Eckert;Michael Lalli` | the three `##` headings. ⚠️ **semicolon-separated** — `Ensure doc + version` does `string_to_array($9, ';')` |
| 7 | `language` | `en` | — |
| 8 | `edition_note` | `Brew Your Own — "Tips from the Pros"` | the file's italic subtitle, line 3 |
| 9 | ⭐ `authority` | `practitioner` | ⭐ **the first `practitioner` row.** `kb.documents_authority_check` allows `reference\|guideline\|practitioner`. The subtitle says *"Practitioner opinion, not reference text"* |
| 10 | `profile` | `book` | ✅ simulated over the 15 real chunks — 0 drops, no rule misfires |
| 11 | ⭐ `front_matter_max_page` | `0` | ⭐ **§2.1** — must be finite; the rule cannot fire on null pages |
| 12 | `extra_drop_regex` | *(empty string)* | no back matter, no masthead — the file is 71 lines of pure body |
| 13 | `text_repairs` | `[]` | ✅ `measured`: **0 tabs** in the source and no line-wrapped ranges — markdown does not wrap. ⛔ **A repair that matches nothing throws** (`text_repairs matched nothing: … — re-probe the source before re-running`), so an empty array is required, not merely allowed |

### §2.3 — Reset command

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c \
  "delete from kb.documents where slug = 'byo-pastry-stouts';"
```

`kb.document_versions`, `kb.chunks`, `kb.chunk_embeddings` and `kb.ingest_log` all cascade.
Then delete the launcher (⛔ **archiving is not deleting** — see [`CLAUDE.md`](../../CLAUDE.md)):

```bash
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -c \
  "delete from workflow_entity where name = 'ingest-pastry-stouts';"
```

### §2.4 — Acceptance numbers

⭐ **These are not estimates. They are simulated by running the live `book` profile's rules
over the probe's 15 real chunks.** Twelve predictions; score every one.

| Check | Predicted | Gate |
|---|---|---|
| raw chunks from Docling | **15** | exact |
| dropped | **0** | exact |
| **kept** | **15** | exact |
| median tokens | **163** | ±10 |
| min / max tokens | **48 / 363** | exact |
| over-512 | **0** | must be 0 |
| under-30 | **0** | must be 0 |
| missing heading | **0** | must be 0 |
| ⭐ missing page | ⭐ **15** | ⭐ **must be 15** — §2.1; the one metric that is *supposed* to be maximal |
| `stats.page_count` | **0** | exact |
| heading depth | **14 at depth 3, 1 at depth 1** | exact |
| `repairs_applied` | **0** | exact |
| embedding coverage | 15/15 @ 1024 | must be 100% |
| `kb.ingest_log` rows | **2** (`clean` + `promote`) | must be 2 |
| corpus total after | **2,449** | exact |

**Runtime:** Docling returned in under one poll interval. Total run **well under 1 minute** —
1 embedding batch. ⚠️ Do not chat with the assistant during the run.

### §2.5 — Verify the data actually landed

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select d.slug, d.doc_type, d.authority, d.authors, v.version, v.is_current, v.page_count,
       count(c.id) chunks, count(e.chunk_id) embs,
       count(*) filter (where c.page_from is null) no_page,
       count(*) filter (where c.heading_path is null) no_head
from kb.documents d
join kb.document_versions v on v.document_id = d.id
left join kb.chunks c on c.version_id = v.id
left join kb.chunk_embeddings e on e.chunk_id = c.id
where d.slug = 'byo-pastry-stouts'
group by 1,2,3,4,5,6,7;"
```

Expect: `article` · `practitioner` · 3 authors · version 1 · `is_current = t` · `page_count 0`
· **chunks 15 · embs 15 · no_page 15 · no_head 0**.

```bash
# Tier B — does it retrieve on what it owns, and only on that?
./scripts/ask.sh "how do I add coconut and cinnamon adjuncts to a pastry stout"
./scripts/ask.sh "what causes diacetyl"          # control: must NOT be displaced
```

| Question | Expect |
|---|---|
| the adjunct question | ⭐ **`Pastry Stouts` chunks in the top 3** — this is the only source in the corpus that covers cold-side adjunct dosing |
| `what causes diacetyl` | ⛔ **byte-identical to the pre-book-8 top 6** — 15 chunks must displace nothing |

---

## §3 — Book 9: the Stout Style Guide

### §3.0 — The verdict

⛔ **Engine + launcher, and this is the first source since book 4 that changes shared code.**
`Clean + normalise` carries an explicit placeholder:

```js
// byo_magazine -> book 9 (stout guide). See archive/06-stout-guide-ingest.md §3.
// Deliberately absent until then: a profile that silently behaves like `book`
// is worse than a thrown error.
```

⭐ **That comment is the whole design brief, and the engine will throw
`Unknown cleaning profile "byo_magazine" — implement it in this node before running` until it
is honoured.** Good: the failure is loud.

[`../archive/06-stout-guide-ingest.md`](../archive/06-stout-guide-ingest.md) is a **542-line
plan that is already written and already probed** (2026-08-07, docling-serve **1.19.0** — ⭐ the
same version running today). ⛔ **Read it before building.** This section does not restate it;
it records what has changed underneath it in the five weeks since, and there is one change that
alters the argument.

### §3.1 — ⭐ What changed under the archived plan: its headline risk is gone

Archived §6 — *"the real risk: corpus balance"* — was the plan's biggest objection, and §8.1
recommended merging **primarily** to defuse it. **At 563 chunks that argument was decisive. At
2,449 it is moot.**

| | archived plan's context | ⭐ `measured` 2026-09-14 |
|---|---|---|
| corpus before book 9 | 563 | ⭐ **2,449** (after book 8) |
| stout guide **unmerged** (625) share | ⛔ **53%** | ⭐ **20.3%** — *under* the 25% threshold |
| stout guide **merged** (218) share | 28% | ⭐ **8.2%** |
| largest document after | stout guide | `yeast-practical-guide` at **17.4%** |

⭐ **Both variants now pass the corpus-share gate, so corpus balance no longer chooses between
them.** ⛔ **Merge anyway** — and say why, because the reason has changed:

> **Merging is now recommended on the anonymity argument alone**, which is archived §8.1's
> reason 2 and was always the stronger one. 405 chunks headed `Ingredients` or `Step by Step`
> with no recipe name embed as mutually near-identical vectors and are unfindable by any query
> naming a beer. A merged chunk **begins with its recipe-name heading**, so the problem is
> solved by construction and the cleaning node gets *simpler*, not more complex.

⚠️ **Record this in the book 9 record: D31's corpus-share proxy has now failed to predict
retrieval share four times** (books 1, 2, 3, and here it no longer even fires). Standing rule 6
— argue, do not delete. This is the argument.

### §3.2 — Re-probe before building (standing rule 1)

⛔ **Do not build from the archived numbers.** They are five weeks old. Re-run the probe and
diff against 679:

```bash
curl -s -X POST http://localhost:5001/v1/chunk/hybrid/file/async \
  -F "files=@shared/rag-files/pending/Stout-Style-Guide.pdf" \
  -F "convert_from_formats=pdf" -F "convert_image_export_mode=referenced" \
  -F "convert_do_ocr=false" -F "convert_pdf_backend=dlparse_v4" \
  -F "convert_table_mode=accurate" -F "chunking_tokenizer=BAAI/bge-m3" \
  -F "chunking_max_tokens=512" -F "chunking_include_raw_text=true" \
  -F "chunking_use_markdown_tables=true"
# then poll /v1/status/poll/<task_id> until success, and GET /v1/result/<task_id>
```

⭐ **Save the result JSON and simulate §3.3's rules over it in Python before touching n8n.**
That is how book 8's twelve predictions were produced, and how books 2, 3, 5, 6 and 7 hit
theirs exactly. **A number derived from the probe by simulation has held every time in this
repo; a number written by hand next to one has not.**

| Gate | Action |
|---|---|
| raw chunks **679 ± 20** | ✅ proceed; the archived §5/§8.1 predictions carry |
| raw chunks outside that | ⛔ **stop.** Docling's chunking changed. Re-derive every number in §3.5 from the new probe before building |

⚠️ **Also re-run the hyphen probe, and use the corrected character class** — `scripts/hyphen-probe.sh`
still carries the `[-‐–—]$` false negative found at book 3 and not fixed at book 4. Run the
broadened pattern by hand, or fix the script first (it is one character class).

### §3.3 — The build, part 1: the `byo_magazine` profile

⛔ **This edits `wf1-ingest-book`'s `Clean + normalise` — shared code used by all six
engine-ingested documents.** Follow §0.1's routing rule: **UI or `n8n import:workflow`, unless
Step C1's probe has passed.**

The node already has a profile registry. `byo_magazine` needs **two capabilities the registry
does not have**: state tracking across chunks, and a merge pass. Add them as registry keys so
the existing two profiles are untouched.

**(a) Add to the `PROFILES` object**, replacing the placeholder comment:

```js
  // byo_magazine -> book 9, the BYO Stout Style Guide (two-column magazine).
  // Two capabilities `book` and `ba_manual` do not need:
  //   * reparent  — 405 of 679 chunks are headed `Ingredients` / `Step by Step`
  //                 with no recipe name. Carry the last-seen {STYLE, RECIPE} down.
  //   * mergeCap  — accumulate each recipe's parts into ONE chunk, capped at 900
  //                 tokens. archive/06 §8.1: this SUBSUMES reparenting for recipe
  //                 chunks, so the node gets simpler, not more complex.
  byo_magazine: {
    dropHeading: /(EDITORIAL|ADVERTISING|SUBSCRIPTION|CONTRIBUTING|PUBLISHER|BOOKKEEPER|WEBSTORE|RECIPE INDEX|TABLE OF|CONTENTS|ART DIRECTOR|DIGITAL EDITOR|TECHNICAL EDITOR|DESIGNER)/i,
    dropReferences: false,
    minTokens: 30,
    reparent: true,
    mergeCap: 900,
  },
```

⚠️ **Note this `dropHeading` is deliberately NOT anchored with `^`**, unlike the other two
profiles — masthead credits appear mid-heading. That is a real difference; do not "tidy" it.

**(b) Insert the re-parent pre-pass** immediately after `const cfg = PROFILES[PROFILE];` and its
throw, and **before** the repair loop:

```js
// ---- byo_magazine: re-parent pass (archive/06 §4) -------------------------
// Runs over ALL chunks BEFORE any drop, so a dropped masthead chunk still
// updates the running {style, recipe} context for the chunks after it.
if (cfg.reparent) {
  const STYLE  = /^(AMERICAN|FOREIGN EXTRA|IMPERIAL|IRISH|OATMEAL|SWEET|SPECIALTY|DRY|MILK|RUSSIAN)\s+STOUT$/i;
  const SUBSEC = new Set(['ingredients', 'step by step', 'tips for success:']);
  const PULLQ  = /^['‘“]/;            // pull-quotes promoted to headings
  let curStyle = null, curRecipe = null;
  for (const c of chunks) {
    const head  = ((c.headings || [])[0] || '').trim();
    const isSub = SUBSEC.has(head.toLowerCase());
    if (STYLE.test(head)) { curStyle = head; curRecipe = null; }
    else if (head && head === head.toUpperCase() && head.length > 8 && !isSub
             && !PULLQ.test(head) && !cfg.dropHeading.test(head)) { curRecipe = head; }
    const path = [];
    for (const seg of [curStyle, isSub ? curRecipe : null, head]) {
      if (seg && path[path.length - 1] !== seg) path.push(seg);
    }
    c.__path  = path;
    c.__isSub = isSub;
    c.__pullq = PULLQ.test(head);
  }
}
```

**(c) In the main loop**, add one drop rule and change two `kept.push` fields:

```js
  if (cfg.reparent && c.__pullq)                           { drop('pull-quote heading');   continue; }
```

```js
  const path = cfg.reparent ? c.__path : heads;
  kept.push({
    chunk_index:  c.chunk_index,
    // ⛔ REBUILT, not copied. archive/06 §4: Docling's `text` is ITS heading plus
    // the body. Changing heading_path without regenerating `content` leaves the
    // embedding still saying "Ingredients" and the whole exercise does nothing.
    content:      cfg.reparent ? (path.join(' > ') + '\n' + raw) : c.text,
    raw_content:  raw,
    heading_path: path.length ? path : null,
    page_from:    pageFrom,
    page_to:      pageTo,
    token_count:  tokens,
    __isSub:      cfg.reparent ? c.__isSub : false,
  });
```

**(d) Add the merge pass** after `if (kept.length === 0) throw …` and **before** the `toks`
line:

```js
// ---- byo_magazine: merge each recipe's parts into one chunk (archive/06 §8.1) ----
// A subsection merges into the chunk above it only when they share the same
// {STYLE, RECIPE} prefix and the running total stays under the cap. That bounds
// the 2,016-token outlier without touching the 177 clean triplets.
let finalChunks = kept;
if (cfg.mergeCap) {
  finalChunks = [];
  const key = (k) => JSON.stringify((k.heading_path || []).slice(0, 2));
  for (const k of kept) {
    const prev = finalChunks[finalChunks.length - 1];
    const canMerge = k.__isSub && prev && key(prev) === key(k) &&
      (prev.token_count ?? 0) + (k.token_count ?? 0) <= cfg.mergeCap;
    if (!canMerge) { finalChunks.push({ ...k }); continue; }
    prev.raw_content = prev.raw_content + '\n' + k.raw_content;
    prev.page_from   = Math.min(prev.page_from ?? k.page_from, k.page_from ?? prev.page_from);
    prev.page_to     = Math.max(prev.page_to   ?? k.page_to,   k.page_to   ?? prev.page_to);
    prev.token_count = (prev.token_count ?? 0) + (k.token_count ?? 0);
    prev.content     = (prev.heading_path || []).join(' > ') + '\n' + prev.raw_content;
  }
}
for (const f of finalChunks) delete f.__isSub;
```

**(e) Point the stats and the return at `finalChunks`**, not `kept`:

```js
const toks = finalChunks.map(k => k.token_count).filter(Number.isFinite).sort((a, b) => a - b);
```
…and in the returned object use `chunks: finalChunks`, `kept: finalChunks.length`, and
`dropped: drops.length` (unchanged — drops are counted pre-merge, which is correct: they
describe the *source*).

⚠️ **Add `merged_from: kept.length` to `stats`.** Without it `kept` and `raw_chunks - dropped`
disagree by ~400 and the `kb.ingest_log` message reads as a defect.

### §3.4 — Four consequences to state before the run, not discover after

| | Consequence | Verdict |
|---|---|---|
| 1 | ⛔ **Merging changes `raw_content`, and `content_sha256 = sha256(raw_content)`** (computed in SQL by `Insert chunks`). So merged chunks get **new hashes** and the `Reuse embeddings` node will reuse **nothing** for this document | ✅ **correct and expected** on a first ingest. ⛔ But it means re-running book 9 after a merge-rule change re-embeds all 218 |
| 2 | `token_count` drifts — it is Docling's per-part count, summed, against a longer heading path | ✅ metadata only; nothing downstream computes on it. ⚠️ Left alone **deliberately** (archived §4) |
| 3 | `chunk_index` gains gaps where subsections were absorbed | ✅ harmless — `UNIQUE (version_id, chunk_index)` does not require density |
| 4 | ⭐ **Retrieval context cost roughly doubles** — 6 passages × ~490 tokens ≈ **2,900 tokens/turn** against `numCtx` 12288 and a ~5,500-char system prompt | ⚠️ **comfortable, but re-check it in Step C6 rather than assuming it.** Archived §8.1 asks for exactly this |

### §3.5 — Acceptance numbers

⛔ **Re-derive these from §3.2's fresh probe.** The archived figures, for comparison:

| Check | archived prediction (merged) | Gate |
|---|---|---|
| raw chunks | 679 | ±20 vs. the fresh probe |
| dropped | ~54 (36 front matter, 18 pull-quotes) | ±15 |
| pre-merge kept | ~625 | ±10% |
| ⭐ **post-merge kept** | ⭐ **218** (193 recipes + 25 prose) | ±15 |
| median tokens | **491** | 400–600 |
| max tokens | ≤ **900** | ⛔ **must be ≤ 900** — this is the cap doing its job |
| under-30 | 0 | must be 0 |
| missing heading | 0 | must be 0 |
| missing page | 0 | must be 0 |
| heading depth ≥2 | ≥ 190 | ⛔ the anonymity fix; **if this is low the re-parent pass did not fire** |
| embedding coverage | 218/218 @1024 | must be 100% |
| `kb.ingest_log` rows | 2 | must be 2 |
| **corpus total after** | **2,667** | exact |

⚠️ **Archived §5.1 stands: this file fails architecture §11's chunk-count criterion in both
variants, in opposite directions, and that is the criterion not fitting a magazine — not a
defect.** ⛔ **Do not tune `chunking_max_tokens` to force it into range**; that would re-split
*How to Brew* and change two variables at once.

### §3.6 — The launcher mapper table

| # | Field | Value |
|---|---|---|
| 1 | `file_path` | `/data/shared/rag-files/pending/Stout-Style-Guide.pdf` |
| 2 | `source_format` | `pdf` |
| 3 | `slug` | `byo-stout-style-guide` |
| 4 | `title` | `Stout Style Guide` |
| 5 | `doc_type` | `book` — ⚠️ **not `style_guide`.** Archived §2: *"it is not a style guide in the BJCP sense"*; the real style ranges already live in `ref.styles` from books 0b and 5 |
| 6 | `authors` | `Jamil Zainasheff` *(confirm against the masthead in the fresh probe)* |
| 7 | `language` | `en` |
| 8 | `edition_note` | `Brew Your Own special issue` |
| 9 | `authority` | `practitioner` |
| 10 | `profile` | ⭐ `byo_magazine` |
| 11 | `front_matter_max_page` | `5` — archived §4: p6 is the first real chapter opener |
| 12 | `extra_drop_regex` | *(empty — the profile's own `dropHeading` covers the masthead)* |
| 13 | `text_repairs` | ⛔ **from §3.2's corrected hyphen probe.** `[]` only if it genuinely returns 0 sites |

### §3.7 — Reset command

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c \
  "delete from kb.documents where slug = 'byo-stout-style-guide';"
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -c \
  "delete from workflow_entity where name = 'ingest-stout-guide';"
```

⚠️ **The engine edit resets separately** — `git checkout n8n/demo-data/workflows/wf1-ingest-book.json`
then `n8n import:workflow`. ⛔ **Export and commit the engine edit before the first run**; it is
shared code and this is the step where standing rule 4 has been broken three times.

### §3.8 — Verify

```bash
docker exec supabase-db psql -U supabase_admin -d postgres -c "
select count(*) chunks, count(e.chunk_id) embs,
       round(avg(c.token_count)) avg_tok, max(c.token_count) max_tok,
       count(*) filter (where array_length(c.heading_path,1) >= 2) deep,
       count(*) filter (where c.content like '%Ingredients%' and c.content like '%Step by Step%') merged_ok,
       count(*) filter (where c.page_from is null) no_page
from kb.chunks c
join kb.document_versions v on v.id = c.version_id
join kb.documents d on d.id = v.document_id
left join kb.chunk_embeddings e on e.chunk_id = c.id
where d.slug = 'byo-stout-style-guide';"
```

⛔ **`max_tok` must be ≤ 900. `deep` must be ≥ 190. `no_page` must be 0.**

⭐ **The retrieval test that actually proves the merge worked** — the anonymity problem was
that no query naming a beer could find a recipe:

```bash
./scripts/ask.sh "give me a foreign extra stout grain bill"
./scripts/ask.sh "which stout recipes use flaked oats"
./scripts/ask.sh "what causes diacetyl"     # control — must not be displaced
```

Expect the first two to return chunks whose `heading_path` names a **recipe**, not
`Ingredients`. ⛔ **If a returned heading is bare `Ingredients`, the re-parent pass did not run
and the ingest must be reset.**

---

## §4 — Session C: close out the RAG pipeline

⛔ **Run this after both books land.** Every number here moves when the corpus does.

### Step C1 — ⭐ Settle the `$input` question (do this first; it gates §3 too)

**~10 min, touches nothing that exists.** The procedure is already written in
[`api-and-mcp-writeback.md`](../../.claude/skills/n8n-workflows/reference/api-and-mcp-writeback.md).
Create a throwaway workflow containing `$input.first().json` **via MCP
`create_workflow_from_code`**, read it back, then `update_workflow` it and read again.

| Outcome | Action |
|---|---|
| ✅ `$input` survives both create and update | ⭐ **record it in the reference doc as verified**, delete the scratch workflow, and use MCP for every remaining edit in this plan |
| ⛔ `$input` is stripped | ⛔ **record it**, and route the engine, `chat-agent` and `wf-step-retrieve` edits through the tracked JSON + `n8n import:workflow` path. ⚠️ **Do not migrate the 14 `$input` sites to `$json` as a workaround** — that is a second variable and the repo has 14 working sites |

⛔ **Delete the scratch workflow with a `DELETE` on `workflow_entity`, not an archive.**
Archiving leaves the row and has already cost this repo a session.

### Step C2 — Repair the grounding eval's negative controls

⛔ **§0.3. Two of three anchors are now covered.** `grounding_eval.py:37` carries a comment
asserting counts that are false.

⭐ **Verified-clean replacements**, `measured` 2026-09-14 across `kb.chunks`, `ref.hops`,
`ref.styles` and `ref.faults` — and re-checked against book 8's source, which mentions none of
them:

| Candidate | kb | ref |
|---|---|---|
| `kveik` *(keep — `U03`)* | 0 | 0 |
| ⭐ `Phantasm` | 0 | 0 |
| ⭐ `Talus` | 0 | 0 |
| ⭐ `Cryo Pop` | 0 | 0 |
| `thiolized` | 0 | 0 |
| `Voss` / `Lutra` | 0 | 0 |
| `hard seltzer` | 0 | 0 |

⛔ **Re-run this check AFTER book 9 lands** — 101 stout recipes may mention a hop the corpus did
not have:

```bash
for t in kveik Phantasm Talus "Cryo Pop" thiolized Voss Lutra "hard seltzer"; do
  printf "%-14s %s\n" "$t" "$(docker exec supabase-db psql -U supabase_admin -d postgres -tAc \
    "select count(*) from kb.chunks where raw_content ilike '%$t%' or array_to_string(heading_path,' ') ilike '%$t%';")"
done
```

Then rewrite `U01`/`U02` with two anchors that still score **0**, and ⭐ **replace the stale
comment with the command that generated the counts**, so the next reader re-measures instead of
trusting prose. ⛔ **That is the actual defect here — a hardcoded claim about corpus contents
with no way to recheck it.**

⭐ **Add a fourth case.** Archived `NEXT-PROMPT` recorded that the labelled-suggestion path had
never fired. ✅ **It has now** — `measured`: `obs.runs.spent` shows `{"grounded": 0,
"suggested": 1}` on **2** runs. Add a case that provokes it deliberately so it is *tested*
rather than merely observed.

### Step C3 — Fix the `chat-agent` system prompt

The prompt is **5,467 characters** and structurally good — instruction precedence, mandatory
tool use, the D38 refusal contract, citations, metric units, voice. ⛔ **Four defects, in
severity order:**

| | Defect | Fix |
|---|---|---|
| **1** ⛔ | The `brainstorm_pairing` worked example is **"What hops go with Nelson Sauvin"** — ⭐ now a **covered** ingredient (§0.3). The prompt teaches the model that a hop in `ref.hops` is the archetype of something the library lacks | Replace with an anchor verified uncovered in Step C2. ⚠️ **Do the same in the `brainstorm_pairing` tool-node description**, which repeats it |
| **2** ⛔ | The prompt **never says what is in the library**, so every refusal is a guess about scope rather than a judgement about coverage | Add a short inventory paragraph — see below |
| **3** ⚠️ | `search_brewing_knowledge`'s description says *"books, style guidelines and practitioner articles"*. ⭐ **`practitioner articles` only becomes true when book 8 lands**, and it still omits the two `datasheet` sources (72 hop varieties, 21 faults) that retrieval demonstrably returns | Update after both books land |
| **4** ⚠️ | ⛔ **The system prompt is not in `obs.prompts`.** The three capability prompts are versioned, SHA-256 hashed by `obs.f_prompt_hash`, and have a one-active constraint. **The prompt that governs every turn is a string in a workflow JSON** | See below — decide, do not silently build |

**For defect 2**, add after the tool descriptions:

```
## What the library contains
Eleven sources: general brewing technique; dedicated volumes on water, yeast and malt;
draught dispense and beer quality; BJCP 2021 and Brewers Association 2026 style
guidelines plus a BJCP study guide; a beer fault reference; a hop variety reference
covering 72 varieties; and practitioner articles.

It does NOT contain: this brewer's own batches, recipes or inventory; equipment
manuals; supplier catalogues; or anything published after 2026.
```

⛔ **Rewrite that list from `kb.documents` after both books land — do not paste it as written
here.** A prompt that describes the wrong corpus is worse than one that describes none.

**For defect 4**, the choice:

| Option | Verdict |
|---|---|
| Leave it in the workflow JSON | ⚠️ **status quo.** It is tracked in git, so it is not *unversioned* — but it is not hashed, not diffable against a run, and `obs.runs` cannot say which prompt produced an answer |
| ⭐ Insert it into `obs.prompts` as `chat.agent/system` v1 and have `chat-agent` read it | ⭐ **recommended**, and the mechanism already exists — `wf-step-llm` does exactly this via `obs.f_step_config`. ⚠️ **Costs one Postgres node on the hot path** |
| Copy it into `obs.prompts` for the record, keep the workflow as the source of truth | ⛔ **rejected** — two copies, one authoritative, guaranteed to drift |

⛔ **Decide this; do not build it as a side effect of the prompt edit.** One variable at a time.

### Step C4 — Node and workflow descriptions

⭐ **You asked specifically about node descriptions. `measured` 2026-09-14: they are empty.**

| Object | State |
|---|---|
| ⛔ **All 9 `chat-agent` nodes** | `notes` is **null** on every one — including `Prep turn` and `Log turn`, the two whose purpose is not evident from the name |
| ⛔ **Workflow-level `description`** | **null** on `chat-agent`, `wf-step-retrieve`, `wf-step-llm`, `cap-brainstorm-pairing`, and the seven older ingest workflows |
| ✅ **Books 5, 6, 7 launchers** | ⭐ **have real descriptions** — e.g. *"Book 6: load the BJCP beer fault list into ref.faults as rows, then generate one card per fault…"*. **This is the standard; the rest should match it** |

⚠️ **Two reasons this is not cosmetic.** A workflow `description` is what `search_workflows`
returns, so it is how *you* will find these over MCP in six months. And
[`README.md`](README.md) §6 already requires *"every node gets a 'why this node exists' line
when it is not self-evident"* — the plans honour it, the workflows do not.

⛔ **Follow §6's rule, including its second half: if a node's purpose is obvious from its name,
say nothing.** Padding hides the nodes that need explaining. Priority order:

1. Workflow `description` on all 4 agent workflows (via MCP `setWorkflowMetadata`, gated on C1)
2. `notes` on `Prep turn`, `Log turn`, `Mark t0` in `chat-agent`
3. `notes` on `Normalise input` and `Return rows` in `wf-step-retrieve` — ⭐ **both carry
   load-bearing comments in their code that belong on the canvas**, especially
   `Normalise input`'s *"`mode` MUST be carried through"*
4. Workflow `description` on the 7 older ingest launchers

⭐ **One real bug to fix while in `Normalise input`:**

```js
const allowed = ['book', 'style_guide'];
```

⛔ **`article` and `datasheet` are missing**, so a caller scoping to either gets silently
downgraded to a whole-corpus search. After book 8 the corpus has **all four** types. ✅ It is
fail-open, so nothing is broken today — but it means the hop and fault cards, and book 8's
article, **cannot be scoped to**. Fix to `['book', 'style_guide', 'article', 'datasheet']`.
⚠️ Code node on the live retrieval path — C1's gate applies.

### Step C5 — The other model prompts

✅ **`obs.prompts` holds 3 active rows, all for `cap-brainstorm-pairing`** — `parse` (474 B),
`propose` (1,507 B), `compose` (1,846 B) — and `obs.profiles` holds 4 decode profiles
(`extract` t=0, `creative` t=0.85, `critique` t=0, `compose` t=0.3), all `gemma4:12b`.
⭐ **The mechanism is sound. Two content issues:**

| | Issue | Fix |
|---|---|---|
| **1** ⚠️ | `propose` says *"If the question asks which hops, every candidate must be a named hop variety."* ⭐ **With `ref.hops` now holding 72 varieties, the grounded path can answer hop questions from the library that previously fell to the suggestion path** | ⛔ **Do not edit the prompt first.** Re-run the pairing capability on hop questions and read `obs.runs.spent`. If `grounded` now dominates where `suggested` used to fire, that is the corpus improving and the prompt needs no change |
| **2** ⚠️ | Nothing tells `propose` that the library now contains a **structured hop reference**, so it cannot prefer a `ref.hops` card over a passing mention in prose | ⚠️ **Measure before writing.** Only add a line if C5.1's measurement shows it choosing badly |

⛔ **Both are "measure, then decide" — not edits to make on the way past.**

### Step C6 — Re-baseline and run the gates

**In this order:**

| | Gate | Command | Pass |
|---|---|---|---|
| 1 | ⭐ **Tier B, full corpus** | `./scripts/ask.sh` on the 5 standing questions + each book's positive controls | **keep** — every prior rank-1 chunk still in the top 3; every positive control at rank 1 |
| 2 | **Tier A, books 8 and 9** | §2.5 and §3.8 | every predicted number scored ✅/⚠️/⛔ |
| 3 | **Tier 1 routing** | `cd scripts/stress && ./tier1_routing.py -n 10 --json /tmp/tier1-final.json` | knowledge **30/30**; total **≥ 75/84** (the post-prompt-fix figure, not the 73 in the architecture doc) |
| 4 | ⭐ **Grounding eval** | `./grounding_eval.py` — **after** Step C2's repair | ⛔ **0 ungrounded candidates survive; every `[S…]` resolves to a real `kb.chunks` id**; the refusal cases refuse in ~10 s with no `propose` call |
| 5 | **Tier 2 end-to-end** | `./tier2_e2e.py --score-only -n 20` | ⛔ **`cited_unbacked` = 0.** Archived note: this is *"the one failure that reads exactly like a correct answer"* |
| 6 | ⭐ **Context budget** | §3.4 row 4 | 6 passages × median tokens + system prompt **< 12288** (`numCtx`) |

⚠️ **Before averaging any latency, exclude the 8 `failed` runs.** `measured` 2026-09-14:
`ok` **11 runs, avg 126.4 s**; `refused` **9 runs, avg 10.1 s**; `failed` **8 runs, avg
1,397 s** — debugging residue where `f_finish_run` was called long after the run died. ⛔ **Mark
them or they poison every future average.**

```sql
-- suggested: a one-line marker so the next reader cannot average across them
update obs.runs set notes = coalesce(notes,'') || ' [debug residue 2026-08-20]'
where status = 'failed';
```

⭐ **The refusal-vs-answer ratio is the measured confirmation of D38's "cheap failure" claim:
10.1 s against 126.4 s, ~12.5×.** Put it in the record.

### Step C7 — Write the record and update the status board

⛔ **This repo's failure mode is unrecorded work, not bad work.** Three books have now gone
stale on the board this way.

Create **`plans/phase3/06-record.md`** following [`README.md`](README.md) §6's six-section
skeleton, then update in the same commit:

- [`README.md`](README.md) — the *"Where this actually is"* table still reads **2,090 chunks /
  6 documents / 11 workflows**, which was true at book 4. ⭐ `measured` today, **before** this
  plan's work: **2,434 / 10 / 15**. ⛔ **It is three books stale right now.**
- [`plans/phase3/README.md`](README.md) §4.1 — rows **8** and **9**
- The §1228 status board — rows 8 and 9, and ⭐ **the Tier C column**, which reads
  *"⬜ n/a — no WF4"* on books 0a–4 and plain `⬜` on books 5–7. **WF4 exists.** Tier C is
  runnable for **all** of them and the questions are already written in each plan's §4. ⭐ **That
  is the cheapest evidence left in the project.**
- [`plans/phase3/NEXT-PROMPT.md`](NEXT-PROMPT.md) — ⛔ **it is stale in a way that will mislead.**
  It was rewritten 2026-09-13 as a "close the agent build" prompt and books 5, 6 and 7 happened
  after it. It still says the corpus is 2,090 across 6 documents and that book 5 is blocked on
  D31; D31 was ratified 2026-09-14. **Rewrite or delete it.**
- [`../../CLAUDE.md`](../../CLAUDE.md) — record C1's `$input` answer, which closes a
  *"settle both before the first programmatic workflow edit"* item

---

## §5 — Definition of done

⛔ **All eleven of these, or the pipeline is not finished.**

| # | Criterion | Command |
|---|---|---|
| 1 | **11 of 11 sources ingested** | `select count(*) from kb.documents;` → **12 rows** (10 now + books 8 and 9) |
| 2 | **Corpus ≈ 2,667 chunks, 0 embedding gaps, 1 distinct dim** | §1.1's SQL |
| 3 | **No document above 25% of the corpus** | largest should be `yeast-practical-guide` at ~17.4% |
| 4 | **17 live workflows = 17 tracked JSON** | the `comm` one-liner in [`README.md`](../../README.md) |
| 5 | ⭐ **Standing rule 4 kept for both books** | `git log` shows each launcher committed **before** its first execution row |
| 6 | **Tier A scored for both books** | every predicted number in §2.4 and §3.5 marked ✅/⚠️/⛔ |
| 7 | **Tier B: keep** | no prior rank-1 chunk displaced below rank 3 |
| 8 | ⛔ **Grounding eval passes with VALID negative controls** | Step C2 — and the anchors re-verified *after* book 9 |
| 9 | ⛔ **`cited_unbacked` = 0** | `tier2_e2e.py --score-only -n 20` |
| 10 | **Descriptions present** | all 4 agent workflows have a `description`; `Prep turn`, `Log turn`, `Mark t0`, `Normalise input`, `Return rows` have `notes` |
| 11 | ⭐ **A real question answered end to end, cited, from a newly ingested book** | ask the assistant for a foreign extra stout grain bill; the answer cites the stout guide and every `[S…]` resolves |

### ⚠️ What this plan deliberately does NOT do

Stated so their absence is a decision:

- ⛔ **The epigraph-heading + PUA text pass.** Water, Malt and Draught carry the defects, and
  *Draught*'s 21 PUA sites are in `heading_path` — the citation the user sees. ⚠️ **It changes
  stored text and forces a re-ingest of three books plus a Tier B re-baseline.** It is a
  session of its own, and it should be the **next** one.
- ⛔ **Book 4's Tier A and Tier B**, still never run. Run it **after** the text pass, or it
  measures a corpus that is about to change.
- ⛔ **`brew.*` data entry** (architecture §13.2 D25) — `brew` has 0 batches and no entry path.
  The assistant correctly says *"I don't have a tool for that yet."*
- ⛔ **R6** — `public.n8n_chat_histories` has RLS disabled and `anon` holds full DML.
  ⚠️ **Unrelated to the corpus, but it is a live security hole**; the cheapest fix is
  `REVOKE ALL … FROM anon, authenticated`. Do it in its own commit.
- ⛔ **`get_logs`** is permanently broken — no analytics container. Do not try to fix it here.
