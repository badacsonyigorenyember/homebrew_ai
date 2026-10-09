# Fill `ref` (phase P1, first half): index

This folder is an **index, not a work item**. It has no `plan.md`, so don't run `/dev-flow`
on `fill-ref` itself. Run it on one of the work items below. Each one has its own folder,
branch and `plan.md` (`Stage: draft`, waiting for your approval).

**Goal of the whole set:** bring the database back up, then load the curated reference data
(styles, malts, hops, yeasts, water salts) into a new `ref` schema. Every row is sourced and
in SI units, and every loader can be re-run.

**Spec:** [`docs/DATABASE.md`](../../DATABASE.md) §2, §6, §7 steps 1–2 ·
[`docs/RECIPE-ROADMAP.md`](../../RECIPE-ROADMAP.md) §8 (P1) ·
[`docs/STYLE-FIT.md`](../../STYLE-FIT.md) §2 (what tagging will need later, so `raw` keeps it).

Split on 2026-10-09 from `docs/superpowers/plans/2026-10-09-fill-ref.md`, which was written
before the dev-flow skills existed. Its content now lives in the plans below. The original is
in git history (`git show b84e914:docs/superpowers/plans/2026-10-09-fill-ref.md`).

## Work items, in order

Run them one at a time. Each starts from `main` after the one before it has shipped. They all
edit PROJECT.md, so parallel branches would conflict.

| # | Slug (folder + branch) | Was task | What it delivers | Depends on | Needs from you |
|---|---|---|---|---|---|
| 1 | [`recover-stack`](../../finished/recover-stack/plan.md) | 1 | `supabase-db`, `-kong`, `-pooler` running again; compose file back in the repo (D6) | — | One `sudo rmdir` command |
| 2 | [`ref-schema`](../../finished/ref-schema/plan.md) | 2, 3 | `loaders/` package with shared helpers, `ref` schema, 8 source rows, DB helpers | 1 | — |
| 3 | [`style-loader`](../../finished/style-loader/plan.md) | 4 | 116 BJCP 2021 + 169 BA 2026 styles in `ref.beer_style` | 2 | Re-add `styles.json`, `ba_styles.json` |
| 4 | [`malt-loader`](../../finished/malt-loader/plan.md) | 5 | The 74 Weyermann, Viking and Simpsons malts hopline.hu sells, figures from the maltster catalogues, in `ref.fermentable` | 2 | The 3 maltster PDFs (in `~/Downloads`) |
| 5 | [`hop-loader`](../hop-loader/plan.md) | 6 | 3 hop sources merged into `ref.hop`, near-duplicate report | 2 | Re-add 3 hop files; confirm source precedence |
| 6 | [`yeast-loader`](../yeast-loader/plan.md) | 7 | Brewtarget yeasts, deduped, in `ref.yeast` | 2 | Re-add 2 Brewtarget files |
| 7 | [`water-salts`](../water-salts/plan.md) | 8 | 8 brewing salts with computed ion contributions | 2 | — |
| 8 | [`ref-spotcheck`](../ref-spotcheck/plan.md) | 9 | Spot-check pack run, measured counts recorded in PROJECT.md and DATABASE.md | 3–7 | Spot-check 10 rows per table |

Items 3–7 only need item 2, so their order can change. Item 7 needs no source files, so it
can go first if the files aren't back yet.

## Where this sits: the order of work after P1a

Each step gets its own work item(s) when it is reached.

| # | Work | Why now / why later | Needs from you |
|---|---|---|---|
| 1 | **Recover the stack** (`recover-stack`, resolves D6) | Nothing can be loaded until the DB is back. | Run one `sudo` command |
| 2 | **P0 test briefs**: 20 briefs | Can run alongside P1a. Briefs decide which styles get envelopes first (P3). | You write or approve them |
| 3 | **P1a: fill `ref`** (`ref-schema` … `ref-spotcheck`) | Everything downstream picks from it. | Re-add the source files (table below) |
| 4 | **P2: maths library**, starting with the doc → calc pass on *How to Brew* | Gravity, IBU, SRM and ABV are needed before any recipe step. `how_to_brew.pdf` is already in `pending/`. | — |
| 5 | **P1b: `corpus`** ← archive dump, `name_map`, `style_profile` | Ratios (D7). Mapping names to `ref` needs `ref` filled first. | Settle D7 |
| 6 | **P3: tags, usage effects, envelopes** | Needs `ref` + `corpus`. | Review envelopes (D9) |
| 7 | **P4–P5: the recipe workflow** (steps 0–11) | **Not yet.** It needs 3–6, and D3 (n8n vs SQL vs Python service) must be decided first. | Decide D3 |
| 8 | **P7: books → `kb`**, *How to Brew* → *Water* → *Yeast* | After each book's doc → calc pass, so only prose is embedded. *Water* feeds P6 (step 12), *Yeast* feeds steps 6 and 14. | Re-add the PDFs |

## Source files the loaders read

You removed them on purpose (2026-10-08). Every loader takes its file paths as arguments, so put
them wherever you like. The plans use `shared/rag-files/pending/`. The shapes below were
measured on the 2026-10-08 copies. If a re-added file has a different shape, the parser tests
catch it.

| File | Work item | Shape (measured) |
|---|---|---|
| `styles.json` | `style-loader` | list of 116, all values strings, 20 styles with no vitals (27A–34C) |
| `ba_styles.json` | `style-loader` | list of 169, numbers as floats; 25 with no OG; 12 with `srmmin` but no `srmmax` |
| `hopline_malts.json` (fetched), `malt_catalogue.json` (hand-built from the Weyermann Crop 2026, Viking 2023 and Simpsons Nov 2025 PDFs) | `malt-loader` | hopline: 82 products, 74 loaded (re-scoped 2026-10-09; `malts.json` no longer used) |
| `hops.json` | `hop-loader` | list of 72, `flavour` list, origins like `USA`, `SVN`, `BE/DE` |
| `hops.hopslist.json` | `hop-loader` | list of 268, same fields as `hops.json`, 22 with no origin |
| `DefaultContent003-Ingredients-Hops-Yeasts.json` | `hop-loader`, `yeast-loader` | Brewtarget BeerJSON: `//` comment header, then `beerjson.hop_varieties` (282) and `beerjson.cultures` (296) |
| `DefaultContent004-MoreYeasts.json` | `yeast-loader` | Brewtarget BeerJSON: `beerjson.cultures` (275) |

Not loaded in P1a: `beer_faults.json` (later), BJCP/BA PDFs (P3), books (P7).

## Global constraints (every work item)

- Every `ref` row has a `source_id` pointing at `ref.source`, and every source has an edition or version.
- Units are SI: °C, L, kg, SG, EBC. °F and ppg are converted on load. Conversion back happens only at display.
- Unknown stays `NULL`. Nothing is guessed. Every original record is kept whole in a `raw jsonb` column.
- Schema objects are created only by `.sql` files in `db/`, applied as `postgres`:
  `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/<file>.sql`. Never through MCP, never as `supabase_admin`.
- Loaders connect as `postgres.<POOLER_TENANT_ID>` to `localhost:${POSTGRES_PORT}` (the pooler), reading only `POSTGRES_DB`, `POSTGRES_PASSWORD`, `POOLER_TENANT_ID` and `POSTGRES_PORT` from the root `.env`. Never print `.env`.
- Every loader is idempotent: running it twice leaves the same row counts.
- Source data files are never committed.
- Nothing calls an LLM.

## Review focus (across the set)

1. **Open-ended ranges:** a BA style with `srmmin = 5` and no `srmmax` must load as `[5,)`, not `NULL`, `[5,0]` or `[5,5]` (`ref-schema` `to_range`, `style-loader` test).
2. **Specialty styles with no vitals** (20 BJCP, 25 BA) must still load, with `NULL` ranges, not zeros (`style-loader` test).
3. **Same name, different hop:** `Saaz` and `Saaz (US)` must stay two hops. Prefix and similar-name pairs go to a review report and are never merged automatically (`hop-loader` tests).
4. **Re-running a loader** must not duplicate ingredients or styles (load-twice step in every loader).
5. **Yeasts:** 71 of 571 entries have no `product_id`, and 72 `(producer, product_id)` pairs repeat across the two files. Dedupe must merge only true repeats, and the 4 entries already in °C must not be converted again (`yeast-loader` tests).

## What changed from the original plan

- **One branch per work item** (the slug) instead of one `p1-ref` branch, and commits follow
  [`conventions.md`](../../../.claude/skills/dev-flow/conventions.md) (one line, no trailer).
  PROJECT.md updates follow the conventions too.
- **`recover-stack` starts the three existing containers with `docker start`** instead of
  `docker compose up -d --no-deps db kong supavisor`. Their bind mounts already point at the
  restored paths (checked with `docker inspect`), so nothing is recreated. This keeps the
  CLAUDE.md rule "do not recreate `supabase-kong`", so the plan needs no rule exception. It also
  updates CLAUDE.md "The running stack", which would otherwise still say compose fails.
- **`read_beerjson` moved from the hop loader to `loaders/common.py`** (`ref-schema`), with its
  test. The yeast loader no longer depends on the hop loader. Test totals are unchanged (28).
- **Each loader is split into two tasks**, parse (pure, tested) and load (DB, load twice), so
  each commit can be reviewed on its own.
- **The hop near-duplicate report is committed** as `docs/work/hop-loader/report.md`. The
  original put it in a PR description, but dev-flow merges locally without PRs.
- **The hop source precedence is a question at plan approval**, not at review.

## Facts checked on 2026-10-09 while splitting

- `supabase-db`, `supabase-kong` and `supabase-pooler` are `Exited (127)`. Each one's error is
  "not a directory" on a bind-mounted file. The 10 placeholder paths are root-owned empty
  directories, re-created 2026-10-09 15:55. `supabase-auth`, `-storage`, `-realtime` and
  `-edge-functions` are restarting.
- The containers belong to compose project `aihomebrewassistant`, config
  `<repo>/docker-compose.yml`, services `db`, `kong`, `supavisor`. All 12 files to restore are in
  `archive/pre-reset-2026-10-08`.
- `shared/rag-files/pending/` holds only `how_to_brew.pdf`.
- `.venv`: Python 3.12.3, `psycopg` 3.3.6 installed, `pytest` **not** installed.
- The root `.env` defines all four variables the loaders read.
