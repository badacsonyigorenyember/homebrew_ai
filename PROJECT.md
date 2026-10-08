# AI Homebrew Assistant — Project Description

> **This file is the single source of truth for the project:** why it exists, what it
> is trying to do, how it is built, and how far along it is. If code and this file
> disagree, one of them is wrong. Fix it, and record the fix in the [Progress log](#8-progress-log).
>
> Last updated: **2026-10-08**

---

## 1. Why this project exists

Homebrewing knowledge is scattered across books, style guidelines, supplier data sheets and
forum posts. Good recipe design means pulling all of these together at once: style limits,
grain bill proportions, hop timing, yeast behaviour, water chemistry, process technique, and
what is actually in your cupboard or at your shop.

The assistant will:

1. **Ingest brewing books and references** into one reliable knowledge base, so every answer
   can cite its source.
2. **Design recipes from scratch** using that knowledge: style first, then proportions, then
   ingredients, then scaling.
3. **Grow into a general brewing companion** later (troubleshooting, water, process, batch
   history). Recipe design comes first.

It is self-hosted and local-first: models, data and books stay on the home machine.

---

## 2. Goals

### Priority 1 — Recipe creation ⭐

The assistant builds a complete, brewable recipe from a user brief that can include any of:

- the target **style** (BJCP or Brewers Association)
- **extra ingredients** or flavours wanted (fruit, coffee, vanilla, lactose, spices, wood, …)
- **ingredients the user already has** and **what they can get**
- preferences or constraints on **hops, fermentables, yeast and techniques**
- batch size and equipment or efficiency details

The output covers fermentables, hops (amount, timing, use), yeast, water/mash/boil/fermentation
process, and calculated targets (OG, FG, ABV, IBU, SRM). Every choice should be traceable to
the knowledge base or to a clearly labelled assumption.

### Priority 2 and later — other skills *(rough order, will change)*

- Brewing Q&A with citations ("why is my beer astringent?", "what does a diacetyl rest do?")
- Recipe critique and adjustment ("make this less bitter", "I have no Crystal 60, substitute")
- Water chemistry recommendations for a recipe
- Fault diagnosis from tasting notes
- Batch log: record what was brewed and learn from the results

### Non-goals (for now)

- A polished public UI or multi-user hosting
- Commercial-scale brewing
- Cloud LLMs as a hard dependency

---

## 3. How recipe creation works *(current approach)*

The approach is **proportions first, quantities last**. A recipe is designed as ratios, which
can then be scaled to any batch size.

```
 User brief
     │
     ▼
 1. STYLE        Pick the target style (BJCP / BA) and load its numeric ranges:
                 OG, FG, ABV, IBU, SRM, plus its characteristic ingredients and process.
     │
     ▼
 2. RATIOS       Decide the recipe's shape as proportions, not amounts:
                 grain bill % (base / specialty / adjunct / roast), bitterness ratio
                 (IBU:OG), hop schedule split (bittering / flavour / aroma / dry hop),
                 yeast attenuation band, and process targets.
     │
     ▼
 3. INGREDIENTS  Fill each ratio slot with real ingredients, preferring what the user has,
                 then what they can get, then the textbook choice. Additions that are not in
                 the catalogue (fruit, spices, …) are kept by name and never swapped for a
                 catalogue item.
     │
     ▼
 4. SCALE        Turn the ratios into amounts for the user's batch size, efficiency and
                 equipment, then calculate OG / FG / ABV / IBU / SRM and check them against
                 the style ranges.
     │
     ▼
 Recipe + reasoning + citations
```

Each step has its own input and output contract that code can check, so a failure can be
pinned to one step. Brewing maths (gravity, IBU, colour, scaling) is **deterministic code,
never the LLM**.

---

## 4. Tech stack

The infrastructure below is **still running** from before the 2026-10-08 reset, but its
`docker-compose.yml` and schema were removed from the repo with everything else (see the
archive tag in §9). Each piece is kept unless a decision in §7 replaces it, and will be
re-committed as it is rebuilt. Until then the containers cannot be recreated (D6). How to
operate the stack safely is in [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

| Layer | Choice | Role | Status |
|---|---|---|---|
| Database | **Supabase** (self-hosted Postgres 15) | Knowledge base, reference data (styles, ingredients), recipes | 🟢 running, empty |
| Vector search | **pgvector** (HNSW) + Postgres full-text, fused (hybrid RAG) | Retrieval over book chunks | ⬜ schema not rebuilt |
| Orchestration | **n8n** (with its own Postgres for metadata) | Ingestion and recipe pipelines, agent | 🟢 running, no workflows |
| Document parsing | **Docling Serve** (ROCm) | PDF → structured Markdown + `HybridChunker` | 🟢 running |
| LLM runtime | **Ollama** (ROCm) | Local chat and embedding models | 🟢 running |
| Chat model | `gemma4:12b-it-q8_0` *(also pulled: `qwen3.8:27b`)* | Reasoning, extraction, recipe drafting | ⚠️ to be re-evaluated (§7) |
| Embedding model | `bge-m3` (1024-dim) | Chunk and query embeddings | 🟢 pulled |
| Web search | **SearXNG** + `webarm` service | Lookups for what the books do not cover | 🟢 running, optional |
| Scripts | Python (`.venv`) | One-off extract/load jobs, evals | — |
| Dev tooling | Claude Code: Supabase MCP (read-only, `.mcp.json`), official n8n MCP (local scope) + `n8n-skills` plugin, guard hook (`.claude/hooks/guard.sh`) | Building and inspecting the stack; schema changes go through SQL files applied as `postgres` | 🟢 |
| Eval guidance | Project skills `retrieval-evaluation-metrics`, `rag-evaluation-frameworks` (`.claude/skills/`) | Reference for building the retrieval test set and regression gate (§6.6) | 🟢 installed, not yet used |

**Hardware:** Ryzen 9 9900X · Radeon RX 9070 XT (16 GB VRAM, RDNA 4 / gfx1201) · 32 GB RAM.

---

## 5. Knowledge sources

The source files sit in `shared/rag-files/pending/` and have not been ingested since the reset.

| Source | Type | Feeds | Status |
|---|---|---|---|
| *How to Brew* — John Palmer | PDF book | General process, ingredients, maths | ⬜ |
| *Water* — Palmer & Kaminski | PDF book | Water chemistry | ⬜ |
| *Yeast* — White & Zainasheff | PDF book | Yeast and fermentation | ⬜ |
| Malt data (`malts.json`) | Structured | Fermentable catalogue | ⬜ |
| Stout Style Guide | PDF | Stout styles and recipes | ⬜ |
| BYO pastry stouts | Markdown | Adjunct technique | ⬜ |
| Draught Beer Quality Manual 2019 | PDF | Serving and dispense | ⬜ |
| BJCP 2021 style guidelines | Structured | Style ranges | ⬜ to source |
| Brewers Association style guidelines | Structured | Style ranges | ⬜ to source |
| Hop, yeast-strain and fault data | Structured | Ingredient catalogues | ⬜ to source |

---

## 6. Design principles

Several of these are lessons from the first build (see §9).

1. **Knowledge and truth stay separate.** Book text is *knowledge*, retrieved with RAG and
   cited. Style ranges, ingredient specs and user batches are *structured data*, queried
   exactly. Do not make an LLM read a number that a SQL query can return.
2. **Small LLM steps, each with a checkable contract.** A 12B model drops constraints as they
   pile up. Several narrow calls with validated outputs beat one large prompt.
3. **Leave room to say "absent."** Every output schema needs a legal way to say "not in the
   catalogue", "unknown" or "conflict". A schema with no such slot pushes the model to invent
   something.
4. **The ingredient catalogue is first-class data.** Recipes can only be as good as the
   inventory they choose from. Fermentables, hops, yeasts and adjuncts each need clean,
   complete records.
5. **Keep it simple.** The first build became too complex to reason about. Add a component
   only when a measured need justifies it.
6. **Measure before and after.** Every change to the recipe pipeline is run against a fixed
   set of test briefs, so improvement is shown, not assumed.

---

## 7. Open decisions

| # | Question | Leaning | Status |
|---|---|---|---|
| D1 | Which style system is primary: BJCP, Brewers Association, or both? | BJCP 2021 as primary (the first build resolved styles against BJCP, classifying to the base style); BA as an alternative the user can pick | open |
| D2 | Chat model: keep `gemma4:12b` or move to `qwen3.8:27b` (fits 16 GB at Q4, slower)? | Benchmark both on the recipe test set before deciding | open |
| D3 | Where does the recipe pipeline live: n8n workflows, Postgres functions, or a Python service? | Undecided. The first build used n8n plus SQL and became hard to follow | open |
| D4 | Ingredient catalogue: what schema, and where does the data come from? | — | open |
| D5 | How the user interacts: chat UI, CLI, n8n chat trigger? | — | open |
| D6 | Re-commit the infrastructure definition (`docker-compose.yml`, `kong.yml`) from the archive tag now, or rebuild it piece by piece? Until one happens, no container can be recreated and `supabase-kong` holds its config only in memory | Restore the compose and Kong files soon; leave `db-init` out until the new schema exists | open |

---

## 8. Progress log

Newest first. One entry per meaningful change: what was done, and why if that is not obvious.

### 2026-10-08
- Hardened the Claude Code setup (audit found the project-specific setup lived outside git):
  committed `.mcp.json` with the Supabase MCP **read-only** on purpose (`~/.mcp.json`, which leaked
  into every project under `~`, moved to `~/.mcp.json.bak`); added `.claude/settings.json` with a
  PreToolUse guard hook (blocks volume deletion, writes to the Postgres data dir, printing `.env`;
  20/20 pipe-test cases pass and it fired live) and the `n8n-skills` plugin at project scope
  (disabled at user scope, as is the unused `supabase` plugin); cleared stale allow rules from
  `settings.local.json`. Moved operational lessons from personal memory into
  [`docs/OPERATIONS.md`](docs/OPERATIONS.md) and expanded `CLAUDE.md` (no worktrees, plans in
  `docs/`, DB-change path). Removed 3 stale worktrees, 8 local branches (all contained in the
  archive tag; remote branches untouched) and junk files. Logged D6.
- Installed two evaluation guides from `Goodnight77/rag-skills` (commit `d403637`, MIT) as
  project skills in `.claude/skills/`: `retrieval-evaluation-metrics` and
  `rag-evaluation-frameworks`. The rest of that plugin was reviewed and not adopted: it is safe
  (no hooks, MCP servers or install scripts) but generic, Qdrant-centred, and pushes complexity
  against §6.5. The `allowed-tools: Bash` grant was removed from the imported frontmatter.
- Created this `PROJECT.md` as the single source of truth for the project, with a standing
  rule in `CLAUDE.md` to update it after every implementation.
- Project reset. All tracked files were removed (archived under tag
  `archive/pre-reset-2026-10-08`), and the Supabase and n8n databases were dumped to
  `~/homebrew-archive-2026-10-08/` and wiped. Reasons: the database had become too complicated
  and messy, ingredient tracking needed a rethink, and style selection needed improvement.

---

## 9. History — the first build (before 2026-10-08)

The first attempt went as far as an ingested corpus of about 2.7k chunks from 11 sources, 285
style records, a chat agent with citations, and a recipe pipeline that passed 7 of 9 test
briefs. Its main lessons are kept in §6. The full design docs (`homebrew_assistant_architecture.md`,
`docs/RECIPE-PIPELINE-V2.md`, `plans/`) can be read with:

```bash
git show archive/pre-reset-2026-10-08:<path>
```

Reuse what still applies from there; do not restore wholesale.

---

## 10. Keeping this file current

- **After anything is implemented**, update the status columns (§4, §5), tick or adjust goals,
  and add a dated entry to §8.
- **When a decision is made**, move it from §7 into the relevant section with a one-line *why*,
  and log it in §8.
- **When the approach changes** (§2, §3, §6), edit the text in place so the file always
  describes the current plan, and log what changed and why. Old thinking belongs in git
  history, not here.
- Keep it readable in one sitting. Detailed designs go in separate docs linked from here.
