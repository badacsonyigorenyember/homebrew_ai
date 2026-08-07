# Phase 2 — minimal agent, one tool

**Status:** ⬜ not started · **Written:** 2026-08-02
**Prereqs:** Phase 1 corpus in place (563 chunks, 0 embedding gaps) ✅
**Blocks:** Phase 3 (full tool set + NLQ + eval baseline)

Architecture reference: §5 WF4 · §7 chat & retrieval · §8.2–8.4 safe tool interface ·
§11 Phase 2. This folder is the *how*; the architecture doc stays the *what and why*.

> **⏸ Rescoped 2026-08-02 — D25.** This phase was *"minimal agent, two tools"*.
> `find_batches` and the whole truth-side surface are **deferred pending an
> architecture discussion** (architecture §7.3, §13.2). Nothing was torn down —
> `nlq.find_batches`, the `brew` schema and the `n8n_agent` grants all stay. The
> drafted work is parked in [`deferred/`](deferred/).
>
> The blocking question isn't the tool's shape, it's that **nothing populates
> `brew.batches`**: no WF3, no UI, no entry path. A query tool over a table nobody can
> fill isn't a feature.

**Goal:** get the agent, streaming, memory and the knowledge/truth **law** working
before adding a second tool. A knowledge question must call
`search_brewing_knowledge`; a question about the user's own beer — for which there is
now no tool at all — must produce *"I don't have a tool for that"* rather than an
invented number or a book passage dressed up as their record.

That refusal is a **harder** test than the two-tool routing test it replaces. A system
that fabricates batch data when it has no batch tool would have fabricated it with one
too.

---

## Files, in build order

| # | File | What it is | Est. |
|---|---|---|---|
| 0 | this file | preflight, order, decisions at a glance | — |
| 1 | [`03-wf4-design.md`](03-wf4-design.md) | decisions: model settings, credentials, node graph, streaming constraint, the full system prompt v1 | read first |
| 2 | [`03a-tool-subworkflows.md`](03a-tool-subworkflows.md) | click-by-click: `tool-search-brewing-knowledge` | ~50 min |
| 3 | [`03b-wf4-build-guide.md`](03b-wf4-build-guide.md) | click-by-click: WF4 itself + `chat.html` wiring | ~60 min |
| 4 | [`05-stress-testing.md`](05-stress-testing.md) | the automated harness — routing, refusal, citation integrity, adversarial, flakiness. **Run this while iterating** | ~30 min setup |
| 5 | [`04-phase2-exit-gate.md`](04-phase2-exit-gate.md) | the 20-question behaviour test, scoring sheet, latency baseline. **Run once, at the end** | ~60 min |
| ⏸ | [`deferred/`](deferred/) | the `find_batches` draft and the batch-seeding template — **parked by D25, do not build** | — |

No seeding step any more: `brew.batches` stays empty by design, and that emptiness is
the condition the gate tests.

---

## 0. Preflight — verified live 2026-08-02

Everything in this table was checked against the running stack, not assumed.

| Check | Value | |
|---|---|---|
| n8n version | **2.23.4** (streaming needs ≥ 1.106.3) | ✅ |
| `gemma4:12b` pulled | 7.6 GB, present in `ollama list` | ✅ |
| `bge-m3` resident | `ollama ps` → 664 MB, **100% GPU**, `Forever` | ✅ |
| `db:5432` reachable from the n8n container | yes | ✅ |
| `n8n_agent` can `EXECUTE nlq.search_knowledge` | `t` | ✅ |
| `n8n_agent` can `EXECUTE nlq.find_batches` | `t` | ✅ |
| `n8n_agent` has `USAGE` on `mem` | **`f`** — turn logging needs the other credential (§3 of the design doc) | ⚠️ |
| `kb.chunks` | 563 (116 style cards + 447 book) | ✅ |
| `brew.batches` | **0 rows** — stays that way by design (D25) | ✅ |
| `mem.chat_turns` | exists, 0 rows | ✅ |
| n8n credentials that exist | **only `Postgres account`** — you will create two more | ⚠️ |
| Workflows in n8n | `Digestion`, `HowToBrew` | ✅ |
| The demo Basic LLM Chain workflow | already gone (§11 "delete it now" is done) | ✅ |
| n8n reachable on the host | `localhost:5678` | ✅ |

Re-run the preflight yourself before you start:

```bash
docker exec ollama ollama list && docker exec ollama ollama ps && docker exec n8n n8n --version
```

---

## 1. Two standing warnings

**Never run WF1 while chatting.** Architecture §4.5: embedding saturates the GPU and
chat latency goes to double digits. Worse in your case — **D22 is still in WF1's
graph** (§11.2), so a stray WF1 run also deletes the book corpus out from under the
chat agent. Phase 2 does not need WF1; leave it alone.

**VRAM.** `gemma4:12b` (~7.6 GB) + KV cache at `num_ctx 12288` (~1.5 GB) + `bge-m3`
(~0.7 GB resident) ≈ 10 GB of your 16 GB. It fits, but only because
`OLLAMA_MAX_LOADED_MODELS=2`. Do not add a third model in this phase.

---

## 2. Decisions at a glance

Full reasoning in [`03-wf4-design.md`](03-wf4-design.md); this is the summary you'll
want while clicking.

| Thing | Setting |
|---|---|
| Chat model | `gemma4:12b`, `numCtx` **12288**, `temperature` **0.2**, `think` **off**, `keepAlive` **`-1m`** |
| Agent node | `@n8n/n8n-nodes-langchain.agent` **v3.1**, `enableStreaming` **on**, `maxIterations` **5** |
| Trigger | Chat Trigger **v1.4**, mode **Embedded Chat**, Public **on**, Response Mode **Streaming** |
| Memory | Postgres Chat Memory **v1.4**, `contextWindowLength` **6**, table `n8n_chat_histories` |
| Tools | exactly **one** — `search_brewing_knowledge`, a `Call n8n Workflow Tool` (v2.2) → sub-workflow |
| Tool DB credential | **new** `Postgres — n8n_agent (read-only)` |
| Truth-side tools | ⏸ **deferred — D25** |
| Memory + logging DB credential | existing **`Postgres account`** (superuser) |
| Ollama credential | **new** `Ollama account` → `http://ollama:11434` |
| Turn logging | one Postgres node **after** the agent, writing both rows to `mem.chat_turns` |
| WF5 (learning) | **not in this phase** — Phase 4 |
| Preference injection | **not in this phase** — `mem.memories` is empty |
| `chunk_ids` in `mem.chat_turns` | left NULL in Phase 2; wired in Phase 3 with WF6 |

---

## 3. Exit criteria (from §11, scored in `04-phase2-exit-gate.md`)

- [ ] Streaming visibly works in `chat.html` — tokens appear progressively, not in one lump
- [ ] 12/12 knowledge questions call `search_brewing_knowledge` (≥10/12 with a description fix is a pass — see §6 of the gate doc)
- [ ] **8/8 questions about the user's own brewing are refused** — no invented number, date, gravity or batch number, and no book passage presented as their record. **Any leak here is a hard fail regardless of the rest**
- [ ] *"How much Citra do I have?"* → *"I don't have a tool for that"*, **not** an invented number
- [ ] Every tool-using answer carries a `Sources:` block
- [ ] Baseline latency recorded: median and p90 time-to-first-token, median total
- [ ] The sub-workflow and WF4 exported to `n8n/demo-data/workflows/` **and committed** — n8n's DB is not a backup (the lesson from plan 02 §7.1)
