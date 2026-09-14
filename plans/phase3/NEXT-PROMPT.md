# Prompt for the next session

Paste everything below the line into a fresh Claude Code session started in
`/home/gorenyember/AI Homebrew Assistant`.

**Rewritten 2026-09-13.** Every number in this file was measured against the live stack on
that date, three and a half weeks after the last work happened (2026-08-20). ⚠️ **The stack
had just been started when these were taken** — re-verify anyway. This file has been wrong
before, twice, both times because events overtook it.

> ## ⭐ What happened since the last rewrite — and why this file was stale again
>
> The previous version of this file said it *"should now be rewritten as the book 4 closing
> session"*. That is **not** what happened. On **2026-08-20** the entire agent layer —
> phases **4.5, 4.6 and 4.7** of [`../agent/00-orchestrator-architecture.md`](../agent/00-orchestrator-architecture.md)
> §8 — was built, and it **works**. Book 4's closing was skipped again.
>
> ⛔ **None of it is in git, and no record file was written**, so
> [`README.md`](README.md) §9 and [`../agent/01-n8n-build.md`](../agent/01-n8n-build.md)
> both still say *"⬜ not started"* about a thing that has served 22 chat turns.
>
> | ⭐ `measured` 2026-09-13 | |
> |---|---|
> | The four workflows | ✅ **built, active, and exactly the build sheet's counts** — `wf-step-retrieve` **6** · `chat-agent` **8** · `wf-step-llm` **8** · `cap-brainstorm-pairing` **15** = ⭐ **37 nodes**, matching [`../agent/02-build-sheet.md`](../agent/02-build-sheet.md) *Final counts* node for node |
> | The exports on disk | ✅ **current, not drifted** — all four JSONs carry the live ids and node counts. ⛔ **All four are untracked** |
> | `obs` schema | ✅ live — 4 tables, **3** prompts, **4** profiles, **21** runs, **36** steps |
> | `mem.chat_turns` | ✅ **22 rows**, real cited answers (`Liberty [S2] and Willamette [S2]…`) |
> | ⭐ **D38's hard refusal** | ✅ **fires correctly in production** — *"The library does not cover Nelson Sauvin"* |
> | ⭐ **The latency baseline 4.5 asked for** | ⭐ **it already exists and nobody recorded it** — see the table in step 3 |
> | Corpus | **2,090** chunks · **6** documents · 0 embedding gaps · `ref.styles` **116** — unchanged since book 4 |
>
> ⭐ **Two corrections to what an earlier reading of this repo claimed.** Both were wrong in
> *direction*, which is the kind of wrong that sends a session off building the opposite of
> what is needed:
>
> | Claimed | ⭐ `measured` |
> |---|---|
> | *"`tool-search-brewing-knowledge` was never exported — standing rule 4 broken again"* | ⛔ **Wrong.** It is a **3-node inactive stub**, superseded by the build sheet's *"retrieval is ONE workflow serving two callers"* merge. ⭐ **Nothing references it** (`nodes::text like '%bjxNuz5KaGnK371c%'` returns zero rows). It should be **deleted, not exported** |
> | *"there are two `chat-agent` workflows"* | ✅ True, and ⛔ **worse than hygiene** — see the blocker below |

---

> ## ✅ ⭐ The blocker, found **and closed**, 2026-09-13: the 4.5 gate runs again
>
> `scripts/stress/tier1_routing.py` reads the deployed config out of the n8n database with
> `select nodes from workflow_entity where name='chat-agent'`. ⭐ **Two workflows carry that
> name**, so the query returns **two rows**, and:
>
> ```
> json.loads FAILS -> JSONDecodeError: Extra data: line 2 column 1 (char 6748)
> ```
>
> ⛔ **The harness every phase re-runs is dead until the duplicate is deleted.** That moves
> *"delete the dead workflows"* out of housekeeping and into **step 1**, because steps 3 and
> onward depend on it.
>
> ✅ ⭐ **Closed the same day — see step 2.** The duplicate had been *archived*, not deleted,
> and an archived workflow keeps its row, so the query still returned two. The row is now
> deleted **and** the harness filters `isArchived` and names the fault instead of dying in
> `json.loads`. `measured`: `load_deployed_config()` returns the live config again —
> `gemma4:12b`, a 5,467-character system prompt.
>
> ⚠️ **And note what the harness does when it works**: it tests the **live** workflow, not a
> copy. That is the property that makes it worth unblocking rather than working around.

---

## The job, in one screen

**Close the agent build. Do not start anything new.** Six things, in this order — the order
is load-bearing twice (step 1 protects work that exists only in a container; step 2 unblocks
step 3).

| # | Step | Verify | Est. |
|---|---|---|---|
| 1 | ✅ **DONE** — everything in §1 is committed | `measured` 2026-09-13: `git ls-files` carries `db/init/60_obs.sql`, `plans/agent/*`, `CLAUDE.md` and all 11 workflow JSONs; `docker-compose.yml` is clean and registers `60_obs.sql` | — |
| 2 | ✅ ⭐ **DONE 2026-09-13** — three dead workflows deleted, `ingest-draught` exported | `measured`: `n8n list:workflow` shows **11**, one `chat-agent`, one `ingest-malt`, 11 live = 11 tracked exports | — |
| 3 | **Run the gates 4.5/4.6/4.7 shipped without** | `tier1` knowledge **30/30**, total **≥73/84**; the 12-case grounding eval; the latency baseline recorded | ~90 min |
| 4 | **Write the record** — `plans/agent/03-record.md` | README §9 row 4.5 ticked; `01-n8n-build.md` §0 no longer says *not started* | ~45 min |
| 5 | **Fix the three logging defects** | `chunk_ids` and `latency_ms` populate on a fresh turn | ~45 min |
| 6 | ⚠️ **Decide, do not build**: the four open questions in *Decisions wanted* | answers written into the record | — |

⛔ **Explicitly NOT in this session:** book 5, the epigraph/PUA text pass, `ref.ingredients`,
`recipe.create`, multi-model, `web.lookup`, OpenWebUI. Reasons in *What comes after*.

---

## 1. ✅ Commit what exists — **DONE 2026-09-13**

⛔ **Everything below lived only in a container and an untracked file.** A `docker volume rm`,
a bad `db-init` edit, or an n8n upgrade loses 37 nodes, the `obs` schema and three plan files.
**This was the highest-value 15 minutes in the whole session.**

✅ ⭐ **`measured` 2026-09-13 — every row of the table below is now tracked**, and
`docker-compose.yml` is committed with the `60_obs.sql` line at
[`docker-compose.yml:176`](../../docker-compose.yml). The table is kept as the record of what
was at risk, not as work outstanding.

```bash
cd "/home/gorenyember/AI Homebrew Assistant" && git status --short
```

`measured` 2026-09-13 — what **was** outstanding, all of it now committed:

| File | What it is |
|---|---|
| `db/init/60_obs.sql` | ⭐ **untracked** — 275 lines, 4 tables, the `SECURITY DEFINER` functions `mem_writer` calls |
| `docker-compose.yml` | modified — the one line that registers `60_obs.sql` with `db-init`. ⛔ **Without it the schema silently never re-applies** |
| `n8n/demo-data/workflows/{chat-agent,wf-step-llm,wf-step-retrieve,cap-brainstorm-pairing}.json` | ⭐ **untracked** — the whole agent layer |
| `plans/agent/` | ⭐ **untracked** — the architecture, the build plan, the 1,144-line build sheet |
| `CLAUDE.md` | untracked |

⚠️ **`supabase/docker/volumes/snippets/Untitled query 515.sql` is also modified** — that is
Supabase Studio scratch, not work. Leave it or commit it separately; do not fold it into the
agent commit.

**Suggested split** — three commits, so the record reads correctly later:

1. `db/init/60_obs.sql` + `docker-compose.yml` — the observability schema and its registration
2. the four workflow JSONs — the agent layer as built
3. `plans/agent/` + `CLAUDE.md` — the plans it was built from

⭐ **Standing rule 4 says export-and-commit *before* the first run.** That property is already
lost for these four workflows — they ran on 2026-08-20 and 21 `obs.runs` rows prove it.
⛔ **Record that as broken in the record file. Do not quietly tick it.** It was kept at book 3,
broken at book 4, and broken again here; three books of evidence that the rule does not survive
a session that ends without a commit.

**Verify:** `git status --short` shows nothing from the table above.

## 2. ✅ Delete the four dead workflows — ⭐ **DONE 2026-09-13**, and the blocker was not what it looked like

⛔ **There is no `delete:workflow` in the n8n CLI** (`export`/`import`/`list`/`publish`/
`unpublish`/`execute`/`audit` is the whole surface — re-checked against the running
container). The UI is one way; ⭐ **the other is a `DELETE` on `workflow_entity`**, which is
what was used: all 17 FKs pointing at that table are `ON DELETE CASCADE` except two
`SET NULL` and one `RESTRICT` on `workflow_published_version`, and none of the three had a
published version or a single execution row.

> ### ⛔ ⭐ The finding: **archiving is not deleting, and it does not unblock the harness**
>
> Before this session, two of the four had been **archived** — `chat-agent`
> `ztLTT3xiKT8eCSfh` and `tool-search-brewing-knowledge` `bjxNuz5KaGnK371c` both carried
> `isArchived = true`. ⭐ **An archived workflow keeps its row**, so
> `select nodes from workflow_entity where name='chat-agent'` still returned **2** and
> `tier1_routing.py` still died on `json.loads`. Archiving hides a workflow from the UI, the
> API and the MCP server, which is exactly what makes it look like the job is done.
>
> ⭐ **Two fixes, not one.** The rows are deleted, **and**
> [`scripts/stress/tier1_routing.py`](../../scripts/stress/tier1_routing.py) now filters
> `and "isArchived" = false` and exits with a named error — *"N live workflows are named
> 'chat-agent'"* — instead of a `JSONDecodeError`. The harness was one line away from
> diagnosing itself and cost a session to diagnose by hand.

`measured` 2026-09-13 — the live list before the deletions, 14 workflows:

| id | name | nodes | active | Verdict |
|---|---|---|---|---|
| `h2lN0E6u0J5x0MSC` | `chat-agent` | **8** | ✅ | ⭐ **KEEP** — this is the one that runs |
| `ztLTT3xiKT8eCSfh` | `chat-agent` | 5 | ✗ | ✅ ⭐ **DELETED** — the imported Phase-2 backup, superseded, **0 executions**. It had been *archived*, which is why it still broke `tier1_routing.py` |
| `bjxNuz5KaGnK371c` | `tool-search-brewing-knowledge` | 3 | ✗ | ✅ ⭐ **DELETED** — an abandoned stub of the 6-node spec, superseded by the `wf-step-retrieve` merge. `measured`: referenced by **0** workflows, **0** executions |
| `ingestMalt00001A` | `ingest-malt` | 2 | ✗ | ✅ ⭐ **DELETED** — never ran, **0 executions**; three books old. `hpW9P0n7fxXY9KdF` is the one `ingest-malt.json` tracks |
| `7woo7XABKVdazwZO` | `ingest-draught` | 2 | ✗ | ✅ ⭐ **RENAMED and EXPORTED** — the rename had already happened; `n8n/demo-data/workflows/ingest-draught.json` now exists, so ⭐ **11 live workflows = 11 tracked exports** and standing rule 4 is green for the first time since book 3 |

✅ **The tool bindings survived the deletions** — both point at the merged workflows, not at
the stub. Re-run this after any workflow deletion:

```bash
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -tAc "select nodes from workflow_entity where name='chat-agent' and active=true;" | python3 -c "import sys,json;[print(n['name'],'->',n['parameters'].get('workflowId',{}).get('cachedResultName')) for n in json.load(sys.stdin) if n['type'].endswith('toolWorkflow')]"
```

Expect exactly: `search_brewing_knowledge -> wf-step-retrieve` and
`brainstorm_pairing -> cap-brainstorm-pairing`.

**Verify:** the `json.loads` failure is gone —

```bash
docker exec aihomebrewassistant-postgres-1 psql -U root -d n8n -tAc "select count(*) from workflow_entity where name='chat-agent';"
```

must print **1**. Then export and commit `ingest-draught.json`.

## 3. Run the gates the build shipped without

Three phases were built and **none of their verification columns were run**.
[`../agent/00-orchestrator-architecture.md`](../agent/00-orchestrator-architecture.md) §8 sets
them; they are reproduced here so this session does not have to interpret them.

### 3.1 — 4.5's gate: `tier1_routing.py`

```bash
cd "/home/gorenyember/AI Homebrew Assistant/scripts/stress" && ./tier1_routing.py -n 10 --json /tmp/tier1-2026-09-13.json
```

| Pass condition | Source |
|---|---|
| knowledge row **30/30** | §8 phase 4.5 |
| total **≥ 73/84** | §8 phase 4.5 |
| ⭐ the **two-tool** selection number | §8 phase 4.7 — *"this is the number Phase 2 could never measure"*. There are now two tools bound; this is the first run that can measure it |

⚠️ **The harness declares a single-parameter tool** (`{"query": string}`) while
`brainstorm_pairing` takes a question. ⭐ **Read `load_deployed_config()` before trusting the
score** — if it only builds one tool definition from the live workflow, the two-tool number is
**not** what came out, and the harness needs a small change before the claim can be made. ⛔ **Do
not report a two-tool number the harness did not actually produce.**

### 3.2 — 4.7's gate: the 12-case grounding eval

§8: *"⛔ **0 ungrounded candidates survive step 4** · every cited claim resolves to a real
chunk."* ⛔ **The eval set does not exist yet — write it.** Twelve questions, and the set must
contain both directions:

- anchors the corpus **covers** (Cascade, diacetyl, water chemistry, a BJCP style) → expect
  grounded candidates with `[S…]` that resolve to real `kb.chunks` ids
- anchors it **does not** (Nelson Sauvin, Sabro, a modern kveik trade name) → expect D38's
  refusal in ~10 s with **no** LLM `propose` call

⭐ **One thing the live data already says, and it is a gap in the eval:**

```
obs.runs.spent  →  {"grounded": 2..4, "suggested": 0}   on every ok run
```

⛔ **`suggested` has been 0 on all nine successful runs.** The labelled-suggestion path —
*"Not from your library"* — has **never fired in production**. ⚠️ **Either the eval includes a
case that provokes it, or the record states plainly that the path is untested.** Do not leave
it implied.

### 3.3 — the latency baseline: ⭐ it already exists

4.5's gate says *"record the latency baseline"*. It is sitting in `obs` and nobody has written
it down. `measured` 2026-09-13:

| `obs.runs.status` | n | avg | min | max |
|---|---|---|---|---|
| `ok` | 9 | **126.4 s** | 74.0 s | 168.3 s |
| ⭐ `refused` | 4 | ⭐ **10.7 s** | 9.3 s | 14.5 s |
| ⚠️ `failed` | 8 | 1,397 s | 35 s | 3,849 s |

| `obs.steps.step_id` | n | avg latency |
|---|---|---|
| `parse` | 15 | 8.3 s |
| `propose` | 9 | **61.6 s** |
| `compose` | 9 | **55.3 s** |
| `smoke` | 3 | 14.8 s |

⭐ **This is the measured confirmation of D38's *"the cheap failure"* claim — a refusal costs
10.7 s against a 126 s answer, ~12×.** The decision was taken on the argument; ⭐ **the numbers
are now available to score it.** Put this table in the record.

⚠️ **The eight `failed` rows are debugging residue**, with finish times up to 64 minutes because
`f_finish_run` was called long after the run died. Harmless, but they poison any future average
— ⭐ **either mark them or note them in the record so the next reader does not average across
them.**

⭐ **And note what A1 says about these numbers.** §9 A1 calls silence during a multi-minute run
*"the main risk"*. A 126 s answer with no progress narration **is** that risk, now measured.
Progress narration is a build requirement that has not been built.

## 4. Write the record

⛔ **This repo's failure mode is not bad work — it is unrecorded work.** Book 4 ran without a
plan; the agent layer was built without a record; both times the status board went stale and the
next session had to rediscover the truth from the database. **Do not end this session the same
way.**

Create **`plans/agent/03-record.md`**, following §6's shape as closely as a non-ingest phase
allows — the six-section skeleton in [`README.md`](README.md) §6 exists for books, so adapt:

| Section | Content |
|---|---|
| §0 verdict | what was built, in one screen: 4 workflows, 37 nodes, `obs`, the tool bindings |
| §1 what was already true | the 2026-09-13 measured tables from this file |
| §2 the build | ⭐ **what the build sheet got wrong or learned** — the runtime rules at the end of [`02-build-sheet.md`](../agent/02-build-sheet.md) were clearly written *from* failures (the `}}` delimiter, the `bigint`→`::int` cast, the blank-model default, sub-workflows needing ACTIVE). **Say which were discovered during the build**; that is the transferable part |
| §3 reset | how to undo: `drop schema obs cascade`, delete the four workflows, revert the compose line |
| §4 testing | step 3's results, scored ✅/⚠️/⛔ |
| §5 evidence | the latency tables, the 21 runs, the 22 turns |

Then update, in the same commit:

- [`README.md`](README.md) §9 — row **4.5**, currently all `⬜`. ⭐ **Tier C becomes runnable for
  books 0a–4 retroactively**, which is the line every book plan so far ends on
- [`../agent/01-n8n-build.md`](../agent/01-n8n-build.md) header — *"Status: ⬜ not started"* is
  false
- [`../agent/00-orchestrator-architecture.md`](../agent/00-orchestrator-architecture.md) §8 —
  tick 4.5, 4.6, 4.7 with their measured verify columns

## 5. Fix the three logging defects

All three are in `chat-agent`, all three are cheap, and ⭐ **one of them is a regex that cannot
match the format its own comment says it parses.**

### 5.1 ⛔ `chunk_ids` is empty on all 22 turns — and a better regex will not fix it

`measured`: `count(*) filter (where array_length(chunk_ids,1)>0)` = **0 of 22**.

`Prep turn` recovers ids with `/"chunk_id"\s*:\s*(\d+)/g` over the tool observation. But
`wf-step-retrieve` in `mode: text` — which is what the tool node sends — returns:

```
[S1] Yeast · Chapter 3 > Pitching Rates · p.88
<text>
```

⛔ **No `chunk_id` appears anywhere in the model-facing string, by design.** The merge note in
the build sheet is explicit that handing the model JSON rows would *"roughly double the
retrieval token budget and bury the `[S…]` labels"*. So the ids are genuinely not recoverable
from what `Prep turn` can see.

⚠️ **This is a design choice, not a bug fix — bring it back as a decision, do not pick
silently.** Three options:

| Option | Cost | ⭐ Verdict |
|---|---|---|
| Emit an `[S1] → chunk_id` map in the tool's text | tokens; visible to the model; pollutes the context the citation contract depends on | ⛔ cheapest to write, worst to live with |
| Add a second non-model key to the tool output | ⛔ the `toolWorkflow` node hands the whole last item to the model — an extra key **is** model-visible. Does not work | ⛔ rejected on the mechanism |
| ⭐ **`wf-step-retrieve` logs its own retrieval to `obs`**, keyed by session; `Log turn` joins | one Postgres node in a workflow that already has a `mem_writer` credential pattern | ⭐ **recommended** — it puts the trace in the schema built to hold traces, and it captures retrievals from **capabilities** too, which `Prep turn` can never see |

### 5.2 `latency_ms` is null on all 22 turns

Not a passing bug — ⭐ **the column is simply absent from `Log turn`'s INSERT column list**, and
`Prep turn` never computes it. Add a `t0` at the trigger and the column to the insert. ⚠️ **Keep
`Continue On Fail: ON`** — a logging failure must never cost the user an answer.

### 5.3 ⚠️ Raw channel tokens reached stored content

`mem.chat_turns` id **13** stores `thought\n<channel|>Liberty [S2] and Willamette [S2]…` — the
model's harmony framing leaked into `content` on one turn out of eleven. ⚠️ **One in eleven, so
it is intermittent, which makes it worth a strip rather than a shrug**; a stored answer that
begins with `thought<channel|>` is what a future `mem` reader will treat as the assistant's
words. Strip in `Prep turn`, and ⛔ **do not strip in the model's output path** — that would hide
it rather than fix it.

**Verify all three:** send one chat message, then

```bash
docker exec supabase-db psql -U postgres -d postgres -c "select id, role, coalesce(array_length(chunk_ids,1),0) nchunks, latency_ms, left(content,40) from mem.chat_turns order by id desc limit 2;"
```

## 6. Decisions wanted — answer these, build none of them

| | Question | ⭐ Recommendation |
|---|---|---|
| **a** | `chunk_ids` — which of §5.1's three options? | ⭐ **the `obs` trace row.** It is the only one that also captures capability retrievals |
| **b** | ⛔ **The epigraph + PUA text pass changes stored text — do three books get re-ingested?** | ⭐ **Yes, and it is the next session.** Water, Malt and Draught carry the defects; *Draught*'s 21 PUA sites are in `heading_path`, which **is** the citation the user sees. ⚠️ Cost is three engine runs (~3 min each) plus a Tier B re-baseline |
| **c** | **D31 — the overlap policy** | ⛔ **needed before book 5**, and book 5 is the first source with a real scoping choice. Not needed this session |
| **d** | **D37 — OpenWebUI** | ⭐ **stays at 5.0.** ⛔ Probe the SSE transport before it enters a plan; and if adopted, **the Ollama connection must not be configured in it at all** or it bypasses WF4, the tools and the citations while appearing to work |

---

## What comes after — the shape of the next three sessions

⛔ **One variable per session** (standing rule 2). The order below is not preference; each one
would corrupt the next's measurement if reordered.

| Session | Work | ⭐ Why here |
|---|---|---|
| **This one** | close 4.5–4.7: commit, delete, gate, record, logging | ⭐ **nothing is measured until the gates run, and nothing is safe until it is committed** |
| **Next** | ⭐ **the shared-code text pass** — the epigraph-heading fix + a **per-font PUA decode map** (data, not a `+17` offset), then re-ingest Water, Malt, Draught, then re-baseline Tier B | ⭐ **It must land while no ingest is running and before book 5** — it changes stored text, so doing it after book 5 means re-ingesting four books instead of three. ⛔ Also fix `scripts/hyphen-probe.sh`'s `[-‐–—]$` false negative while in `scripts/` — **three books old**, and the `Log ingest summary` row-id message while in the engine |
| **Then** | **book 4's Tier A + Tier B**, the only book with neither | ⚠️ Run it **after** the text pass, or it measures a corpus that is about to change |
| **Then** | **book 5** — BA 2026 + BJCP Study Guide | ⛔ blocked on **D31** |

⭐ **And the retroactive prize nobody has collected:** every book plan from 0a to 4 ends on the
line *"Tier C — not runnable, no WF4"*. ⛔ **WF4 exists now.** Tier C is runnable for all five
books, and that backlog is the cheapest evidence in the project — the questions are already
written in each plan's §4.

---

## Standing rules that apply to this session

| | |
|---|---|
| **1** | ⭐ **Probe before planning.** Every number in this file was measured 2026-09-13; measure again rather than quoting it |
| **2** | **One variable at a time.** Do not fix the text defects *and* close the agent record in one session |
| **3** | ⛔ **Do not run an ingest without asking.** Nothing here ingests — if that changes, stop and ask first |
| **4** | ⛔ **Export and commit before the first run.** Already broken for these four workflows; record it broken rather than ticking it |
| **5** | ⛔ **Never edit a workflow in the browser and leave it there.** Edit tracked JSON → `n8n import:workflow` → re-activate. ⚠️ The two UI-only actions in step 2 are deletions, which is the one thing the CLI cannot do |
| **6** | **Argue, do not delete.** A metric that fires on nothing gets a recorded argument, not a quiet removal |

**The export command, for step 1 and step 2:**

```bash
docker exec n8n n8n export:workflow --all --separate --output=/tmp/wf && docker cp n8n:/tmp/wf/. "/home/gorenyember/AI Homebrew Assistant/n8n/demo-data/workflows/"
```

---

## Read before starting

- [`../agent/00-orchestrator-architecture.md`](../agent/00-orchestrator-architecture.md) — §8
  sequencing (the verify columns this session owes), §10 **D38** (the refusal decision, taken
  live), §9 **A1** (silence during a long run — now measured at 126 s)
- [`../agent/02-build-sheet.md`](../agent/02-build-sheet.md) — the *Rules that apply everywhere*
  block at the end is the build's hard-won knowledge; §2.4–2.6 is what step 5 edits
- [`README.md`](README.md) — **§6** the plan contract, **§9** the status board this session
  updates, **§4.2** why 4.5 is the seam
- `scripts/stress/tier1_routing.py` — ⛔ read `load_deployed_config()` before trusting any score
