# Record 06 — books 8 and 9, and the RAG closeout

**Run:** 2026-09-14 · **Plan:** [`06-corpus-completion-and-rag-closeout.md`](06-corpus-completion-and-rag-closeout.md)
· follows [`README.md`](README.md) §6's six-section skeleton.

⭐ **The corpus is complete: 11 of 11 sources, 12 documents, 2,678 chunks, 0 embedding gaps.**

---

## §0 — The verdict

| | |
|---|---|
| **Book 8** — BYO Pastry Stouts | ✅ **launcher only, engine unchanged.** 15 chunks. Fourth consecutive mapper-only source, and the first non-PDF input |
| **Book 9** — BYO Stout Style Guide | ✅ **launcher + the `byo_magazine` cleaning profile**, the first change to shared engine code since book 4. 229 chunks |
| **RAG closeout** | ✅ three defects fixed — a false eval control, a false prompt example, and a silent doc_type trap |

⛔ **The D30 split held for book 8 and was deliberately broken for book 9**, which is what
`Clean + normalise`'s own placeholder comment specified. Nothing outside `Clean + normalise`
changed in the engine.

---

## §1 — Prerequisites: what was true before the run

Every row re-measured on the day, per standing rule 1.

| Check | `measured` 2026-09-14 |
|---|---|
| Stack | ✅ 16 containers, `gpu-amd` profile, all healthy |
| Corpus before | ✅ **2,434** chunks · 2,434 embeddings · **0** gaps · 1 dim · **10** documents |
| Reference tables | ✅ `ref.styles` 285 · `ref.hops` 72 · `ref.faults` 21 |
| Workflows before | ✅ **15 live = 15 tracked** |
| Both sources present | ✅ `byo_pastry_stouts.md` 8,633 B · `Stout-Style-Guide.pdf` 9,735,054 B |

**What had to be done first**, both completed:

1. ⛔ **Standing rule 4 was already broken.** `ingest-draught.json` — book 4's launcher, which
   had already run — was untracked. Committed before anything else ran.
2. `.claude/worktrees/` was gitignored rather than committed; they are git worktrees, not
   project content. The `n8n-workflows` skill that CLAUDE.md references **is** now tracked.

---

## §2 — The build

### 2.1 Book 8 — `ingest-pastry-stouts`

Two nodes, no Code nodes, modelled byte-for-byte on `ingest-draught.json` with the 13-entry
`workflowInputs.schema` copied verbatim. Mapper values and where each came from:

| Field | Value | Source of truth |
|---|---|---|
| `file_path` | `/data/…/byo_pastry_stouts.md` | `docker exec n8n ls` |
| ⭐ `source_format` | `md` | the probe — Docling `InputFormat` accepts it |
| `slug` / `title` | `byo-pastry-stouts` / `Pastry Stouts: Tips from the Pros` | the file's H1 |
| ⭐ `doc_type` | `article` | first `article` in the corpus |
| `authors` | `Ben Romano;Brian Eckert;Michael Lalli` | the three `##` headings |
| ⭐ `authority` | `practitioner` | the file's own subtitle says so |
| `profile` | `book` | simulated over the 15 real chunks — 0 drops |
| ⭐ `front_matter_max_page` | `0` | markdown has no pages; the field must be finite |
| `text_repairs` | `[]` | **measured 0 tabs**, and markdown does not wrap |

### 2.2 Book 9 — the `byo_magazine` profile

Added to `wf1-ingest-book` › `Clean + normalise` as **registry keys**, so `book` and `ba_manual`
are untouched. Two capabilities the other profiles do not have:

- **`reparent: true`** — a pre-pass over **all** chunks *before* any drop, so a dropped masthead
  chunk still updates the running `{style, recipe}` context. Carries the last-seen recipe name
  down onto its `Ingredients` / `Step by Step` children.
- **`mergeCap: 900`** — accumulates each recipe's parts into one chunk under a 900-token cap.

⛔ **`content` is rebuilt, not copied.** Docling's `text` is its own heading plus the body;
changing `heading_path` without regenerating `content` would leave the embedding still saying
"Ingredients" and the whole exercise would do nothing. `raw_content` stays body-only, so
`content_sha256` is unaffected.

⚠️ **`dropHeading` is deliberately NOT anchored with `^`** — masthead credits appear mid-heading
(`CONTRIBUTING WRITERS`). It is also used in the recipe-name detector, so anchoring it would let
masthead credits become `curRecipe` and poison every path after them.

---

## §3 — Reset

```bash
# book 8
docker exec supabase-db psql -U supabase_admin -d postgres -c \
  "delete from kb.documents where slug = 'byo-pastry-stouts';"
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -c \
  "delete from workflow_entity where name = 'ingest-pastry-stouts';"

# book 9
docker exec supabase-db psql -U supabase_admin -d postgres -c \
  "delete from kb.documents where slug = 'byo-stout-style-guide';"
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -c \
  "delete from workflow_entity where name = 'ingest-stout-guide';"

# the engine edit resets separately
git checkout n8n/demo-data/workflows/wf1-ingest-book.json
docker exec n8n n8n import:workflow --input=/demo-data/workflows/wf1-ingest-book.json
```

⛔ **Archiving is not deleting** — the row stays in `workflow_entity`.

---

## §4 — Testing

### Tier A — book 8: 15 of 15 predictions exact

| Check | Predicted | Actual | |
|---|---|---|---|
| raw chunks | 15 | **15** | ✅ |
| dropped / kept | 0 / 15 | **0 / 15** | ✅ |
| median tokens | 163 | **163** | ✅ |
| min / max tokens | 48 / 363 | **48 / 363** | ✅ |
| over-512 / under-30 | 0 / 0 | **0 / 0** | ✅ |
| missing heading | 0 | **0** | ✅ |
| ⭐ missing page | 15 | **15** | ✅ |
| `page_count` | 0 | **0** | ✅ |
| heading depth | 14@3, 1@1 | **14@3, 1@1** | ✅ |
| `repairs_applied` | 0 | **0** | ✅ |
| embedding coverage | 15/15 @1024 | **15/15 @1024** | ✅ |
| `kb.ingest_log` rows | 2 | **2** | ✅ |
| corpus total after | 2,449 | **2,449** | ✅ |

### Tier A — book 9

⭐ **The fresh probe returned 679 raw chunks — exactly the archived 2026-08-07 figure**, so the
archive's predictions carried. Docling Serve 1.19.0 both times.

| Check | Predicted | Actual | |
|---|---|---|---|
| raw chunks | 679 ±20 | **679** | ✅ exact |
| dropped | 54 | **54** = 36 front matter + 18 pull-quotes | ✅ exact |
| pre-merge kept | 625 | **625** | ✅ |
| ⭐ post-merge kept | **229** (re-derived) | **229** | ✅ |
| median / max tokens | 454 / ≤900 | **479 avg / 896 max** | ✅ cap holds |
| under-30 | 0 | **0** | ✅ |
| missing heading / page | 0 / 0 | **0 / 0** | ✅ |
| heading depth ≥2 | ≥190 | **203** | ✅ |
| embedding coverage | 229/229 | **229/229 @1024** | ✅ |
| `kb.ingest_log` rows | 2 | **2** | ✅ |
| corpus total after | **2,678** (re-derived) | **2,678** | ✅ |

**Idempotency** — both launchers re-run: 4 executions all `success`, corpus unchanged at 2,678.

### Tier B — retrieval: **KEEP**

A **same-session** pre-book-9 baseline was captured, per the archive's requirement.

- **5 of 7 standing questions byte-identical.** `what causes diacetyl` unchanged — 229 new
  chunks displaced nothing.
- On the two that moved, **every prior rank-1 chunk is still rank 1**; book 9 enters at ranks
  3–5 with relevant recipes.
- **Positive controls:** *"give me a foreign extra stout grain bill"* → all six hits are stout
  guide chunks headed by a **recipe name**. *"which stout recipes use flaked oats"* → named
  recipes at 1, 3, 6. *"coconut and cinnamon adjuncts"* → book 8 holds ranks 1–3.

### Tier C — agent, end to end

⭐ **Runnable, and run.** *"Give me a foreign extra stout grain bill."* through the live chat
webhook returned four named recipes with metric grain bills, cited `[S1] [S3] [S4] [S6]`.
**All 6 recorded `chunk_ids` resolve to real `kb.chunks` rows; 0 unresolved**, and the cited
pages match the Sources block exactly.

---

## §5 — Evidence, and what the numbers changed

### 5.1 ⭐ The merge did the one thing it exists for

405 of 679 raw chunks are headed a bare `Ingredients`, `Step by Step` or `Tips for Success:`
with no recipe name — mutually near-identical vectors, unfindable by any query naming a beer.

**After the ingest: 0 stored chunks are headed by a bare subsection.** 26 chunks sit at heading
depth 1 (style prose), 197 at depth 2 (merged recipes), 6 at depth 3 (parts that overflowed the
cap), across **105 distinct recipes**.

### 5.2 Three corrections to plan 06 §3, each evidence-backed

| | Plan said | Measured | Why |
|---|---|---|---|
| `doc_type` | `book` | ⭐ **`article`** | Archive §3.1 chose `article` *deliberately*, to preserve the `p_doc_type='book'` filter lever and §6.2's rollback remedy. Plan 06 changed it citing archive §2 — but §2 argues only that the file must not go to WF2, never that it is a book. `nlq.search_knowledge`'s `p_doc_type` parameter is live, so the lever is real |
| `authors` | `Jamil Zainasheff` | ⭐ **the 7 CONTRIBUTING WRITERS** | Read from the masthead: Glenn BurnSilver, Terry Foster, Christian Lavender, Josh Weikert, Michael Tonsmeire, Forrest Whitesides, Gordon Strong. ⛔ **Jamil Zainasheff is not among them** — he appears only in recipe names like `JAMIL'S AMERICAN STOUT`, which is very likely how both plans came to guess him |
| corpus total | **2,667**, gated "exact" | ⭐ **2,678** | The archive's 218 post-merge figure predates the 900-token cap and was never re-simulated; ~11 recipes split under it. 2,449 + 229 = 2,678 |

### 5.3 ⭐ The method that keeps working

**A number derived from the probe by simulation has now held for every source in this repo.**
For both books the *actual patched node's JavaScript* was run over the *real probe output* in a
harness before n8n was touched. Book 8: 15 of 15 exact. Book 9: 229 predicted, 229 delivered.

### 5.4 §3.8's own verification SQL is wrong

The plan's `merged_ok` check is `content like '%Ingredients%' and content like '%Step by Step%'`.
⛔ **It returns 0 on a correct ingest** — the merge strips those subsection headings by design,
and Docling's `raw_text` never contained them. Use instead: 0 chunks whose `heading_path[1]` is a
subsection, and `merged_from`(625) > `kept`(229).

### 5.5 D31's corpus-share proxy, for the fourth time

Unmerged, book 9 would have been 20.3% of the corpus; merged it is **8.6%**. Both pass the 25%
gate, so corpus balance no longer chooses between them — the merge is justified on the
**anonymity** argument alone. ⚠️ D31's proxy has now failed to predict retrieval share four
times. Standing rule 6: argue, do not delete. This is the argument.

### 5.6 Final corpus

| doc_type | docs | chunks |
|---|---|---|
| `book` | 5 | 1,858 |
| `style_guide` | 3 | 483 |
| `article` | 2 | 244 |
| `datasheet` | 2 | 93 |
| **total** | **12** | **2,678** |

Largest document: `yeast-practical-guide` at **17.3%** — under the 25% gate.

---

## §6 — The closeout, and what it found

### C1 — ⭐ the `$input` question is SETTLED

Probed on a throwaway workflow, verified against `workflow_entity.nodes` directly rather than
the tool's own read-back.

| Path | Verdict |
|---|---|
| MCP `create_workflow_from_code` | ✅ **`$input` survives** |
| MCP `update_workflow` — `setNodeParameter`, `updateNodeParameters`, `setNodePosition` | ✅ **survives all three** |
| REST `PUT` | ⚠️ **still untested** — the only API key has `aud: mcp-server-api`, not `public-api`. The paths are independent, so the MCP result does not transfer |

⛔ **The reference doc's `availableInMCP` claim was wrong in both directions.** Actual: **9 of
15** true, and **`chat-agent` and `wf-step-retrieve` — the live retrieval path — are `false`**,
so they must be written through tracked JSON + `n8n import:workflow`. `wf1-ingest-book` **is**
true, so the engine edit was MCP-eligible. Discovery is ungated (`search_workflows` returns all
workflows); read-detail and write are gated.

### C2 — the eval's negative controls were false

Book 7 put **Nelson Sauvin** (`kb` 2, `ref.hops` 1) and **Sabro** (`kb` 2, `ref.hops` 2) into the
library, so `U01` and `U02` were asserting the corpus lacks something it knows. Replaced with
**Talus** and **Cryo Pop**, verified 0 across `kb.chunks`, `ref.hops`, `ref.styles` *and*
`ref.faults`, re-checked **after** book 9 landed.

⛔ **The actual defect was a hardcoded claim about corpus contents with no way to recheck it.**
The comment is now the command that generates the counts.

⭐ **`S03` added** to provoke the labelled-suggestion path deliberately. Sabro is the right
anchor *because* it is now covered: `ref.hops` knows the variety so the capability runs, but the
library holds no pairing guidance for it. The anchor changed category rather than being discarded.

### C3 — the prompt taught the model something false

⛔ **The `brainstorm_pairing` worked example was "What hops go with Nelson Sauvin"** — a
**covered** ingredient held up as the archetype of an *uncovered* one, in both the system prompt
and the tool-node description. **This is the thing that would have made the pipeline look correct
while being wrong.** Both now use `Talus`.

The prompt never said what the library holds, so every refusal was a guess about scope. Added a
`## What the library contains` section built by querying `kb.documents` — all 12 rows.
⚠️ The plan's suggested "nothing published after 2026" line was **dropped deliberately**: the
sources span 2016 to 2026, so a single cut-off would be a false statement.

⚠️ **Defect 4 (the system prompt is not in `obs.prompts`) is NOT built.** The plan says decide,
do not build as a side effect. **Left as-is, with the reason recorded:** it is tracked in git so
it is versioned, but it is not hashed and `obs.runs` cannot say which prompt produced an answer.
Moving it to `obs.prompts` costs one Postgres node on the hot path. **That is a decision for its
own session.**

### C4 — a trap, and 39 empty description fields

`Normalise input`'s `allowed` list held `['book','style_guide']` while its own comment listed
four legal values, so scoping to `article` or `datasheet` silently became a whole-corpus search.
Fixed.

⛔ **But the plan understates it: `doc_type` cannot be scoped to at all.** It appears **zero**
times in `wf-step-retrieve.json` and `chat-agent.json` — the `executeWorkflowTrigger` declares
only `query`, `top_k`, `mode`, `session_id`, and no caller maps it. The fix removes a trap; it
changes no behaviour. **Wiring `doc_type` through is a second variable and was not done.**

All 39 nodes across the four agent workflows had `notes: null` and all four workflow
`description`s were null. Descriptions added to all four, notes to the five nodes named by the
plan. `Build vector` is flagged as borderline and **left blank rather than padded**, per
README §6's second half.

### C5 — ⭐ measured, and the measurement settled it

Both `propose`-prompt issues were "measure, then decide". **The measurement was taken, and it
says: change nothing.**

Plan 06 C5.1 asked whether `ref.hops`'s 72 varieties now let the grounded path answer hop
questions that used to fall to the suggestion path. `measured` 2026-09-14 from `obs.runs.spent`
over the closeout runs:

| run | `spent` |
|---|---|
| 32 | `{"grounded": 2, "suggested": 0}` |
| 33 | `{"grounded": 5, "suggested": 0}` |
| 35 | `{"grounded": 4, "suggested": 0}` |

⭐ **`suggested` is 0 everywhere, and `grounded` dominates.** Before this plan it was
`{"grounded": 0, "suggested": 1}`. ✅ **That is the corpus improving, exactly as C5.1 predicted,
so the `propose` prompt needs no change** — and C5.2 falls with it. ⛔ **No prompt edited on
the way past.** `obs.prompts` still holds 3 active rows and `obs.profiles` 4 profiles.

⚠️ **Consequence for Step C2's `S03`, stated honestly: it did not do what it was added to do.**
`S03` was written to provoke the labelled-suggestion path deliberately. It did not fire —
because Sabro is in `ref.hops`, so the capability *grounds* it rather than suggesting. **The
labelled-suggestion path is now hard to provoke at all**, which is the corpus being good rather
than a defect. Anyone wanting to test that path needs an anchor that is *partially* covered —
named in the corpus but with no pairing guidance — and the corpus may no longer contain one.

### ⭐ The gates, final

| Gate | Result |
|---|---|
| **Grounding eval** | ✅ **PASS 10 · WARN 3 · FAIL 0 · ERROR 0** of 13. ⭐ **All four `uncovered` cases refuse**, including on the *new* anchors — the coverage gate logs `reason: "anchor_not_in_corpus"` for Talus, Cryo Pop, kveik and Phantasm |
| **Tier 2 end-to-end** | ✅ ⛔ **`cited_unbacked` = 0** — *"no fabricated citations found"* across 20 executions. The four refusals show `tool: yes, psg 0, cites []`: the tool ran, returned nothing, and the model cited nothing |
| **Context budget** | ✅ 6 passages × 479 median ≈ **2,874** + a 7,308-char system prompt, against `numCtx` **12288** — comfortable |

⚠️ **The 3 WARNs are pre-existing and not caused by this plan.** They are the `suggested` cases
recording no `chunk_ids` on the chat turn, because the capability returns composed text rather
than retrieval rows, so `obs.f_session_chunk_ids` has nothing to join. Noted, not fixed.

⭐ **Refusal latency — the plan's "~10 s" claim holds, but only at the right layer.** `obs.runs`
measures the capability at **12.0 s** (9.9–12.9). The eval measures the whole chat round-trip at
**29.6–36.8 s**. Both are correct; they measure different things. ⛔ **Do not compare one to the
other** — that is how the 1,397 s `failed` average got into the record in the first place.

### C6 — latency, and a correction to the plan's SQL

⛔ **The plan's suggested `update obs.runs set notes = …` cannot run — `obs.runs` has no `notes`
column.** Columns are `id, session_id, turn_no, capability, status, budget, spent, started_at,
finished_at`. **`status` is already the marker**; the exclusion rule is
`where status <> 'failed'`, recorded here instead of adding a column.

| status | runs | avg | |
|---|---|---|---|
| `ok` | 11 | **126.4 s** | |
| `refused` | 9 | **10.1 s** | ⭐ |
| `failed` | 8 | 1,397 s | ⛔ debug residue — exclude from every average |

⭐ **Refusal is ~12.5× cheaper than an answer — the measured confirmation of D38's "cheap
failure" claim.**

---

## §7 — Operational notes for the next editor

0. ⛔⛔ **The one that cost real time: re-publishing does not restore `chat-agent`'s webhook.**
   After importing the four agent workflows and re-publishing them, the DB said `active = t`
   but the running n8n had dropped the route — every POST to the chat webhook returned
   `404 "… is not registered"` in ~2 ms. **`docker restart n8n` fixes it.**

   ⛔ **This silently invalidated a whole eval run.** `grounding_eval.py` reported
   *"NO REFUSAL — answered an anchor the corpus lacks"* on all four `uncovered` cases. The
   agent had never been asked: the requests 404'd, no `mem.chat_turns` row was written, and
   `check()` — which read only the database — could not tell "never asked" from "answered
   wrongly". **A refusal regression and a transport failure scored identically.**

   ⭐ **Fixed in the script, not just noted.** `check()` now returns a distinct `ERROR`
   verdict when `res["ok"]` is false, the summary prints the webhook probe command, and the
   exit code is non-zero for `ERROR` as well as `FAIL`. ⚠️ The tell was in the output all
   along and is worth remembering: **four consecutive failures at exactly `0.0s`.** A real
   refusal takes ~10 s.

1. ⛔ **`n8n import:workflow` DEACTIVATES an active workflow.** All four agent workflows had to
   be re-published afterwards. Check `active` before and after every import.
2. ⚠️ `update:workflow --active=true` still works but is **deprecated** in favour of
   `publish:workflow --id=…`.
3. ⛔ **`n8n execute --id=…` fails for these launchers** with *"Workflow is not active and cannot
   be executed"* — this n8n gates `executeWorkflow` on a **published** version, and
   `wf1-ingest-book` has none. Use MCP `execute_workflow` with `executionMode: "manual"`, which
   is what the UI does. This is why books 0a–7 ran from the UI.
4. `hyphen-probe.sh`'s character class is **fixed** — it now matches en dash, em dash and
   non-breaking hyphen, the false negative found at book 3 and left unfixed at book 4.
