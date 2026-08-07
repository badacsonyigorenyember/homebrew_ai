# Archive — plans 01 through 06 and Phase 2

**Archived:** 2026-08-07 · **Reason:** deliberate reset. The only live plan is
[`plans/phase3/`](../phase3/README.md).

> **Archived ≠ wrong ≠ deleted.** Most of what is in here was *measured*, and measured
> facts do not expire because a plan was reorganised. This file is the index that says
> which is which, so nothing has to be re-derived by reading five documents.

**The rule for using this folder:** never build from a file in here. Read it for
evidence — a probe number, a measured failure, a piece of SQL that is known to work —
and carry that evidence into a Phase 3 plan. If you find yourself following an archived
file step by step, stop; that step belongs in a live plan.

---

## 1. What is in here

| File | What it was | Status |
|---|---|---|
| [`01-wf1-ingest-document.md`](01-wf1-ingest-document.md) | WF1 design — the ingest pipeline's *what and why* | 🟡 **superseded in shape, correct in substance.** The pipeline it describes is built and working. Phase 3 §2 splits it into an engine + per-book launcher (D30), which changes the workflow's boundaries, not its stages |
| [`01a-wf1-build-guide.md`](01a-wf1-build-guide.md) | click-by-click WF1 build, 25 nodes, full SQL | ✅ **still the reference for the engine's internals.** The node-level SQL, the poll-loop guard, the embed batching and the D13/D14/D15/D16 fixes are all still exactly what runs. Phase 3 per-book plans cite it rather than repeat it |
| [`02-phase1-retrieval-gate.md`](02-phase1-retrieval-gate.md) | the 5 standing retrieval questions + the gate procedure | ✅ **fully live.** Phase 3 §5 Tier B makes these questions the regression baseline for **every** book. Do not change them — a moving baseline measures nothing |
| [`06-stout-guide-ingest.md`](06-stout-guide-ingest.md) | the stout guide plan, built on a real 679-chunk probe | ✅ **fully live, one correction.** It is the model every Phase 3 per-book plan follows, and it is still the plan for book 9. Its §6 corpus-share percentages assume it runs *first*; running it last drops its share from 28% to ~7%. See Phase 3 §4.1 |
| [`phase2/`](phase2/) | the agent: design, build guides, stress harness, exit gate | 🟡 **built and running; the plans are archived, the workflow is not.** See §2 |
| [`phase2/deferred/`](phase2/deferred/) | the `find_batches` draft, parked by D25 | ⏸ unchanged — still the reference for when the truth side is designed |

---

## 2. ⚠️ Phase 2 is archived but WF4 is live

This is the one thing in this folder that can bite. **The agent is running right now**,
answering questions, with a system prompt whose only human-readable copy lives in
[`phase2/03-wf4-design.md`](phase2/03-wf4-design.md) §6.

The 2026-08-02 hardening was measured and then lost — only its scores survived — and it
had to be rewritten and re-measured from scratch on 2026-08-07. That is the exact
failure this note exists to prevent a second time.

| Artefact | Where the truth lives |
|---|---|
| **System prompt v3 (deployed)** | `n8n/demo-data/workflows/wf4-chat-agent.json` is authoritative; [`phase2/03-wf4-design.md`](phase2/03-wf4-design.md) §6 is the readable copy and the only record of *why* |
| What v3 bought and cost, measured | [`phase2/03-wf4-design.md`](phase2/03-wf4-design.md) §6.2 — including why v3.1 scored 20 points worse while looking safer |
| Stress harness | `scripts/stress/` — **live code, not archived.** [`phase2/05-stress-testing.md`](phase2/05-stress-testing.md) documents it |
| Model settings, credentials, streaming constraint | [`phase2/03-wf4-design.md`](phase2/03-wf4-design.md) §2–§4 — unchanged and still correct |
| The Phase 2 exit gate | [`phase2/04-phase2-exit-gate.md`](phase2/04-phase2-exit-gate.md) — **never run.** See §3 |

**Standing rule, carried forward from §6 of the design doc:** never change the system
prompt without pasting the new text into a live plan and re-running
`scripts/stress/tier1_routing.py`. Archiving the folder does not archive that rule —
Phase 3 §7 restates it.

---

## 3. Open items that did not close, and where they went

Archiving must not be a way to lose an unfinished thing. These were open on
2026-08-07 and are still open:

| Item | State | Carried to |
|---|---|---|
| **Phase 2 exit gate never run** | 🔴 the agent works but was never formally scored against its own criteria | Phase 3 §6 — folded into the corpus-level gate, run once, after the corpus is complete rather than against a two-book corpus |
| `mem.chat_turns` logging (`Prep turn` / `Log turn`) | 🟡 not built. `chunk_ids` and `tool_calls` therefore unavailable | Phase 3 §6 — it is a prerequisite for the §10.2 retrieval-hit-rate metric, so it must exist before the eval baseline |
| **D25 — truth-side tool surface** | ⏸ deferred by decision, not by neglect. `nlq.find_batches`, the `brew` schema and the `n8n_agent` grants all still exist and are untouched | still open; nothing in Phase 3 depends on it |
| `X02` / `X03` adversarial cases at 0/3 | 🔴 over-refusal on legitimate brewing questions framed as instructions | Phase 3 §7 — re-check whenever the prompt is touched |
| `M04` (the bare word *"hops"*) regressed 3/3 → 0/3 in v3 | 🟡 a known, accepted trade for closing the prompt leak | as above |
| Deprecation #2 — the OpenAI vector-search snippet file | 🟡 table dropped, file still tracked | housekeeping, not blocking |

---

## 4. What was measured and is still true

Facts, not plans. These survive the reset and should not be re-measured:

- *How to Brew*: 248 pages → **447 chunks**, 100% embedding coverage at 1024 dims
- BJCP 2021: **116 styles** in `brew.bjcp_styles` + **116 style cards** in `kb.chunks`,
  verified aligned and idempotent (D17)
- Stout guide probe: **679 raw chunks in 65 s**; 60% of the file headed `Ingredients` or
  `Step by Step` with no recipe name; merging the recipe triplets yields **218 chunks**
- WF1 idempotency proved: a second run stops at `Is new file?` and inserts nothing
- `kb.promote_version()` refuses to promote a version with missing embeddings (D16)
- The Crypto node is typeVersion 2 and its digests were always genuine SHA-256 (D20)
- System prompt v3: **73–74/84** on the 84-call tier-1 harness; knowledge row **30/30**
- `n8n_agent` holds `EXECUTE` on `nlq.*`, is denied `mem` and `kb` at schema level,
  and reports `default_transaction_read_only=on` (D18)

Everything above is also recorded in `homebrew_assistant_architecture.md` §11.1–11.4,
which is **not archived** and remains the project's single source of truth.
