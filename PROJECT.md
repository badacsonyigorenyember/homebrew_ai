# AI Homebrew Assistant — Project Description

> **This file is the single source of truth for the project:** why it exists, what it
> is trying to do, how it is built, and how far along it is. If code and this file
> disagree, one of them is wrong. Fix it, and record the fix in the [Progress log](#8-progress-log).
>
> Last updated: **2026-10-09**

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

Agreed 2026-10-08. Full design, diagrams and worked examples:
[`docs/RECIPE-ROADMAP.md`](docs/RECIPE-ROADMAP.md). Database: [`docs/DATABASE.md`](docs/DATABASE.md).

The approach is **proportions first, quantities last**, and **compute first**: the LLM reads the
request (step 1) and writes the recipe sheet (step 16). Everything in between is SQL or
deterministic code, with an LLM tie-break only when scores tie.

```
 A UNDERSTAND   0 brewer profile (stored) · 1 brief · 2 best-fit style · 3 deviation report
 B DESIGN       4 targets (style range + hint knobs + user's numbers) · 5 blueprint (ratios)
 C CHOOSE       6 yeast · 7 fermentables · 8 hops · 9 extras   (scored by code)
 D COMPUTE      10 calculate amounts, OG/FG/ABV/IBU/SRM · 11 validate, retry max 3×
 E PROCESS      12 water · 13 mash + boil · 14 ferment + condition · 15 package
 F DELIVER      16 write + save (reasons, deviations, citations)
```

- **The style is guidance, not law.** A best-fit style is always picked. Guidance is on by
  default: the pipeline's own choices stay in style, and anything the user asks for
  (ingredients or numbers) is accepted and listed as a deviation, never blocked.
- **Style rules are graded on 5 levels** (required · typical · allowed · out of style · changes
  style). They are not written per ingredient: a deterministic function compares the style's
  sensory envelope with the ingredient's automatically derived tags, its usage and its dose, so
  new ingredients need no rules ([`docs/STYLE-FIT.md`](docs/STYLE-FIT.md)).
- **Ratios** come from per-style statistics computed over community recipes (D7).
- Each step has an input/output contract that code can check, so a failure can be pinned to
  one step.

---

## 4. Tech stack

The infrastructure below is **still running** from before the 2026-10-08 reset, but its
`docker-compose.yml` and schema were removed from the repo with everything else (see the
archive tag in §9). Each piece is kept unless a decision in §7 replaces it, and will be
re-committed as it is rebuilt. Until then the containers cannot be recreated (D6). How to
operate the stack safely is in [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

| Layer | Choice | Role | Status |
|---|---|---|---|
| Database | **Supabase** (self-hosted Postgres 15) | Knowledge base, reference data (styles, ingredients), recipes | 🔴 down since 2026-10-08 ~20:48: `supabase-db`, `-kong`, `-pooler` can't start because their mounted files were removed in the reset (recovery = [`recover-stack`](docs/work/recover-stack/plan.md)) |
| Vector search | **pgvector** (HNSW) + Postgres full-text, fused (hybrid RAG) | Retrieval over book chunks | ⬜ schema not rebuilt |
| Orchestration | **n8n** (with its own Postgres for metadata) | Ingestion and recipe pipelines, agent | 🟢 running, no workflows |
| Document parsing | **Docling Serve** (ROCm) | PDF → structured Markdown + `HybridChunker` | 🟢 running |
| LLM runtime | **Ollama** (ROCm) | Local chat and embedding models | 🟢 running |
| Chat model | `gemma4:12b-it-q8_0` *(also pulled: `qwen3.8:27b`)* | Reasoning, extraction, recipe drafting | ⚠️ to be re-evaluated (§7) |
| Embedding model | `bge-m3` (1024-dim) | Chunk and query embeddings | 🟢 pulled |
| Web search | **SearXNG** + `webarm` service | Lookups for what the books do not cover | 🟢 running, optional |
| Scripts | Python (`.venv`) | One-off extract/load jobs, evals | — |
| Dev tooling | Claude Code: Supabase MCP (read-only, `.mcp.json`), official n8n MCP (local scope) + `n8n-skills` plugin, guard hook (`.claude/hooks/guard.sh`) | Building and inspecting the stack; schema changes go through SQL files applied as `postgres` | 🟢 |
| Delivery workflow | Project skills `dev-flow` (orchestrator) + `dev-brief`, `dev-plan`, `dev-implement`, `dev-review`, `dev-verify`, `dev-ship` (`.claude/skills/`) | Brief → plan → build → review → verify → merge, one subagent per step, work in `docs/work/<slug>/` | 🟢 installed, not yet used |
| Eval guidance | Project skills `retrieval-evaluation-metrics`, `rag-evaluation-frameworks` (`.claude/skills/`) | Reference for building the retrieval test set and regression gate (§6.6) | 🟢 installed, not yet used |

**Hardware:** Ryzen 9 9900X · Radeon RX 9070 XT (16 GB VRAM, RDNA 4 / gfx1201) · 32 GB RAM.

---

## 5. Knowledge sources

Not ingested since the reset. On 2026-10-08 the source files were removed from `shared/rag-files/pending/` on purpose, to be re-added as each loader needs them. Only `how_to_brew.pdf` is there now (checked 2026-10-09).

| Source | Type | Feeds | Status |
|---|---|---|---|
| *How to Brew* — John Palmer | PDF book | General process, ingredients, maths | ⬜ |
| *Water* — Palmer & Kaminski | PDF book | Water chemistry | ⬜ |
| *Yeast* — White & Zainasheff | PDF book | Yeast and fermentation | ⬜ |
| Malt data (`malts.json`) | Structured | Fermentable catalogue | ⬜ |
| Stout Style Guide | PDF | Stout styles and recipes | ⬜ |
| BYO pastry stouts | Markdown | Adjunct technique | ⬜ |
| Draught Beer Quality Manual 2019 | PDF | Serving and dispense | ⬜ |
| BJCP 2021 style guidelines (`styles.json`) | Structured | Styles, 116 rows | ⬜ |
| Brewers Association style guidelines (`ba_styles.json`) | Structured | Styles, 169 rows | ⬜ |
| Hop data (`hops.json`, `hops.hopslist.json`), fault data (`beer_faults.json`) | Structured | Hop catalogue (72 + 268), faults (21) | ⬜ |
| Brewer's Friend recipes (Kaggle, CC0) | Structured, 179,455 recipes | Per-style ratios (D7) | ⬜ 35,620 (views > 500) in the archive dump, measured 2026-10-08 |
| Brewtarget default data (GPL-3) | Structured, BeerJSON | Yeast (296 + 275 entries), hops (282) (D8) | ⬜ downloaded before the reset (`DefaultContent003/004`), to be re-added |
| AHA recipe-design crash course · Oregon Brew Crew recipe formulation · BJCP exam study guide | Free web / PDF | Design method, rules of thumb, output checklist | ⬜ candidate, not downloaded |

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
7. **Compute first.** Anything that can be SQL or deterministic code must be: it is faster,
   cheaper and testable. The LLM is only for free text in and prose out. Every new source gets
   a *doc → calculation* pass first: its tables, formulas and rules of thumb become data or
   code, and only the remaining prose goes to RAG.

---

## 7. Open decisions

| # | Question | Leaning | Status |
|---|---|---|---|
| D1 | Which style system is primary: BJCP, Brewers Association, or both? | BJCP 2021 as primary (the first build resolved styles against BJCP, classifying to the base style); BA as an alternative the user can pick | open |
| D2 | Chat model: keep `gemma4:12b` or move to `qwen3.8:27b` (fits 16 GB at Q4, slower)? | Benchmark both on the recipe test set before deciding | open |
| D3 | Where does the recipe pipeline live: n8n workflows, Postgres functions, or a Python service? | Undecided. The first build used n8n plus SQL and became hard to follow | open |
| D4 | Ingredient catalogue: what schema, and where does the data come from? | Schema designed in [`docs/DATABASE.md`](docs/DATABASE.md) §2 (one `ref.ingredient` table + one table per kind, tags, source per row). Data sources: D7, D8 | open |
| D5 | How the user interacts: chat UI, CLI, n8n chat trigger? | — | open |
| D6 | Re-commit the infrastructure definition (`docker-compose.yml`, `kong.yml`) from the archive tag now, or rebuild it piece by piece? Until one happens, no container can be recreated and `supabase-kong` holds its config only in memory | Restore the compose and Kong files soon; leave `db-init` out until the new schema exists | open |
| D7 | Where do the recipe ratios (grist %, hop split) come from? | Brewer's Friend corpus through automatic quality gates (no hand curation) → `corpus.style_profile`, thin styles shrunk toward their family, specialty styles use the base style, extra sources weighted (books, DIY Dog, own batches) ([`docs/STYLE-PROFILES.md`](docs/STYLE-PROFILES.md)) | open |
| D8 | Yeast data source | Brewtarget default data: 571 entries with attenuation and temperature ranges, GPL-3 (fine for a private install) | open |
| D9 | Who approves the extracted style sensory envelopes before they enter `ref`? | LLM extracts BJCP prose, code parses BA fields, the user reviews | open |

---

## 8. Progress log

Newest first. One entry per meaningful change: what was done, and why if that is not obvious.

### 2026-10-09
- Split the P1a plan into 8 dev-flow work items, each with its own `docs/work/<slug>/plan.md`
  (`Stage: draft`, awaiting approval) and branch: `recover-stack`, `ref-schema`, `style-loader`,
  `malt-loader`, `hop-loader`, `yeast-loader`, `water-salts`, `ref-spotcheck`. The index (order,
  source files, global constraints, review focus) is
  [`docs/work/fill-ref/README.md`](docs/work/fill-ref/README.md), and the original plan was
  removed. Changes found while curating: `recover-stack` uses `docker start` on the existing
  containers (no recreate, so the Kong rule holds); `read_beerjson` moved to the shared helpers so
  the yeast loader doesn't depend on the hop loader; the hop source precedence is a question at
  plan approval; `pytest` is not installed yet (checked).
- Added the delivery-workflow skills: `dev-flow` orchestrates `dev-brief` → `dev-plan` →
  `dev-implement` (one subagent per task) → `dev-review` → `dev-verify` → `dev-ship`, with user
  approval gates on the brief, the plan and shipping. Each piece of work gets
  `docs/work/<slug>/` and branch `<slug>`; one-line commits, `--no-ff` merge to `main`. Not yet
  run on real work.
- Wrote the P1a plan (now split, see above; original at `b84e914:docs/superpowers/plans/2026-10-09-fill-ref.md`):
  recover the stack (D6), then load `ref` (styles, malts, hops, yeasts, water salts) with tested
  Python loaders, plus the order of the phases after it. Found while planning: the Supabase DB,
  Kong and pooler have been down since 2026-10-08 ~20:48, because their bind-mounted files
  (removed in the reset) became empty root-owned directories on restart; all of them are in the
  archive tag. Measured source shapes from the 2026-10-08 copies (counts in the plan). Nothing
  built yet.

### 2026-10-08
- Measured the archived Brewer's Friend corpus (read from the dump, nothing restored): 35,620
  recipes (views > 500 of 179,455), 34,052 mapped to a BJCP 2021 style; 84 of 116 styles have
  ≥ 50 recipes, 19 have 20–49, 9 have 1–19, 4 have none (28D, 29D, 30D, 34A). Junk left: 0
  non-Latin names, 219 OG outside 1.020–1.150, 90 ABV-inconsistent, 3,287 (9 %) grist % not
  summing to 100 ± 2. Wrote [`docs/STYLE-PROFILES.md`](docs/STYLE-PROFILES.md) (quality gates
  instead of hand curation, robust statistics, family shrinkage for thin styles, weighted extra
  sources) and [`docs/STYLE-FIT.md`](docs/STYLE-FIT.md) (deterministic 5-level algorithm with
  automatic ingredient tagging, so new ingredients need no rules). Updated the roadmap,
  `DATABASE.md` (`sensory_dimension`, `source_weight`, gate flags) and D7.
- Agreed the recipe-creation approach after reviewing the roadmap point by point: brief before
  style; style as guidance (best-fit style always picked, user overrides accepted and listed);
  yeast → fermentables → hops → extras; added brewer profile, water, mash + boil, fermentation,
  packaging and a validate loop (16 steps in 6 stages, §3); new principle 7 *compute first*
  (§6). Rewrote [`docs/RECIPE-ROADMAP.md`](docs/RECIPE-ROADMAP.md): style rules organised as
  sensory envelope + ingredient tags + usage effects + dose (worked "Citra in a stout" example
  from BJCP 15B/20B text), a doc → calculation table, and web research on free ratio sources
  (Brewer's Friend CC0 corpus, Beer Analytics, DIY Dog, AHA, Oregon Brew Crew, BJCP study guide,
  Brewtarget yeast data). Wrote [`docs/DATABASE.md`](docs/DATABASE.md): `ref` / `corpus` / `kb` /
  `app` schemas split by trust, ER diagrams, access rules, build order. Design only, nothing
  built. Updated D4, D7–D9 and corrected §5 (the BJCP and BA style JSONs are already in
  `pending/`).
- Wrote [`docs/RECIPE-ROADMAP.md`](docs/RECIPE-ROADMAP.md): a review of the proposed recipe-creation
  flow, an improved 10-step flow (brief → style → conflict check → targets → blueprint → pick →
  calculate → validate → process → write), a 5-level style-rule scale, a hint→knob table, a
  database split by trust (`ref` / `kb` / `corpus` / `app`) and a phased roadmap (P0–P9). It is a
  **proposal**: §3 is unchanged until the user approves it. Added D7–D9.
- Added a scope rule to `CLAUDE.md`: implement only what is asked, no unrequested suggestions or
  follow-up fixes, so sessions can close.
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
