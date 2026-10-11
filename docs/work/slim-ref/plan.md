# Apply the database review (slim `ref`, create all schemas) — implementation plan

Stage: implementing
Source: [`docs/DATABASE-REVIEW.md`](../../DATABASE-REVIEW.md) (committed on `main` in `8b41df1`)
Branch: slim-ref

## Approach

The review's §5 SQL is applied as idempotent files in `db/`, one file per review section, each
applied twice as `postgres` (OPERATIONS.md §4). The SQL is taken **verbatim** from the review;
the only addition is the `create extension` that `kb.chunk` needs.

- **§5.1 goes into `db/010_ref_schema.sql`**, not a new file: its `create table` statements are
  edited to the slim shape (so a reader of 010 sees the real tables, and a fresh database gets
  them directly) and the review's `alter … drop` statements are appended to 010's existing
  "bring tables up to date" section, which is the pattern 010 already uses (`field_source`).
- §5.2 → `db/012_style_fit.sql`, §5.3 → `db/013_corpus.sql`, §5.4 → `db/014_kb.sql`,
  §5.5 → `db/015_app.sql`. All new tables stay empty.
- The three loaders lose the dropped fields in the same task as the column drop (the styles
  loader cannot run against the old key or the new one without its change), then are re-run so
  `field_source` no longer names dropped columns. `potential_sg()` stays in `loaders/malts.py`
  with its test; only the column and field go.
- **User decision (2026-10-11): "Everything in §5"** — all corpus, kb, app and style-fit tables
  are created now, empty, instead of "in the phase that fills them" as the review says. The
  docs record this as a deviation wherever the review text says otherwise.
- Last task rewrites `docs/DATABASE.md` to describe the built design, marks the review applied,
  moves behaviour tables to "in code" in the design docs, updates the two affected work plans,
  and closes D4 in PROJECT.md.

Facts checked on the live DB (read-only, 2026-10-11): `postgres` is not a superuser; `vector`
0.8.0 is **available but not installed**, and is in `supautils.privileged_extensions` with
`supautils.privileged_role = postgres`, so `postgres` may create it. All 8 installed extensions
are owned by `supabase_admin`. Schemas `corpus`, `kb`, `app` do not exist. `ref` has 7 tables
owned by `postgres`, no views and no functions. Constraint `beer_style_guide_edition_code_key`
exists; no duplicate `(source_id, code)` in 285 styles. Rows: `beer_style` 285, `ingredient`
164, `fermentable` 74 (74 with extract, 73 EBC, 62 `max_pct`; `field_source ? 'potential_sg'`
74), `hop` 90 (`field_source ? 'beta_pct'` 87), `yeast` 0, `water_salt` 0, `source` 10.
Database `search_path` is `"$user", public, extensions`. Suite: 33 passed. Source files present
in `shared/rag-files/pending/`.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `db/010_ref_schema.sql` | changed | slim `create table` shapes + review §5.1 drops |
| `db/012_style_fit.sql` | new | review §5.2: `fermentable.role`, `misc`, `tag`, `tag_synonym`, `ingredient_tag`, `sensory_dimension`, `style_sensory`, `style_character`, `style_rule` |
| `db/013_corpus.sql` | new | review §5.3: `corpus` schema, 7 tables |
| `db/014_kb.sql` | new | `vector` extension, review §5.4: `kb` schema, `ref.source.file_path`, `kb.chunk` |
| `db/015_app.sql` | new | review §5.5: `app` schema, 8 tables |
| `loaders/styles.py` | changed | no `edition`; upsert on `(source_id, code)` |
| `loaders/malts.py` | changed | no `potential_sg` field/column; function stays |
| `loaders/hops.py` | changed | no `beta_pct`; `oils_pct` docstring note removed |
| `tests/test_styles.py` | changed | no `edition` asserts |
| `tests/test_malts.py` | changed | no `potential_sg` field / `field_source` key |
| `tests/test_hops.py` | changed | no `beta_pct` field / `field_source` key |
| `docs/DATABASE.md` | changed | rewritten to the built design |
| `docs/DATABASE-REVIEW.md` | changed | status → approved and applied; deviation recorded |
| `docs/STYLE-FIT.md` | changed | usage effects and cut points in code; `sensory_dimension` slim; fermentable role inputs |
| `docs/STYLE-PROFILES.md` | changed | source weights in code |
| `docs/RECIPE-ROADMAP.md` | changed | usage effects and hint knobs in code |
| `docs/work/water-salts/plan.md` | changed | no `molar_mass` column |
| `docs/work/ref-spotcheck/plan.md` | changed | `co2_vol` / `type` notes |
| `PROJECT.md` | changed | §4 rows, §5 malt row, D4 closed, §8 |

Checked and **not** changed: `docs/work/yeast-loader/plan.md` (`ref.yeast` is unchanged),
`docs/work/fill-ref/README.md` (links DATABASE.md §2, §6, §7, which keep their numbers).

## Tasks

All `psql` commands below are run from the repo root. `Q` is shorthand for
`docker exec -i supabase-db psql -U postgres -d postgres -At -c`.

### Task 1: Drop the 7 unused `ref` columns and re-run the loaders
Why: review §4.1 / §4.2 / §5.1 — columns no step reads, always `NULL`, or computed.
- [x] `db/010_ref_schema.sql`, `create table` statements:
  - `ref.beer_style`: remove `edition text not null` and `co2_vol numrange` (and its comment);
    replace `unique (guide, edition, code)` with `unique (source_id, code)`.
  - `ref.fermentable`: remove `potential_sg` and `type` (and its comment).
  - `ref.hop`: remove `beta_pct` and `oils_pct`.
  - `ref.water_salt`: remove `molar_mass`.
- [x] Append to the end of 010, under a comment
  `-- Columns removed by the database review (docs/DATABASE-REVIEW.md §5.1, 2026-10-11)`, the
  review §5.1 SQL verbatim (drop old key, drop/add `beer_style_source_id_code_key`, drop the 7
  columns with `if exists`).
- [x] `loaders/styles.py`: remove `edition` from `Style`, `parse_style(row, guide)` (no edition
  argument), `parse_bjcp` / `parse_ba` call it without one. `load()`: no `edition` in the column
  list, `on conflict (source_id, code) do update`, and drop `source_id = excluded.source_id`
  from the `set` list (it is now part of the key). Docstring: "on (source_id, code)".
  The printed labels ("BJCP 2021: … styles") stay.
- [x] `loaders/malts.py`: remove `potential_sg` from `Fermentable`, from `merge()` (the
  `field_source["potential_sg"]` line, the constructor argument, the docstring sentence) and
  from `load()`'s insert/update. Keep `potential_sg()` and `PPG_OF_PURE_EXTRACT`; add one line
  to its docstring: not stored (the DB keeps only the extract the sources state), kept for the
  maths library.
- [x] `loaders/hops.py`: remove `beta_pct` from `Hop`, from `make_hop()` (the `Béta-sav` parse,
  the `values` entry, the constructor argument; `null_figures` sets `alpha = oil = None`) and
  from `load()`; remove "oils_pct stays NULL." from `load()`'s docstring. `raw` keeps the whole
  page, so beta stays there.
- [x] Tests: `tests/test_styles.py` — drop the `edition` parts of the asserts in
  `test_bjcp_21a` and `test_ba_code_is_slug`. `tests/test_malts.py` — drop every
  `f.potential_sg` assert in `test_catalogue_wins_hopline_fills`, `test_no_extract_stays_null`,
  `test_user_supplied_fills_only_gaps`, and the `"potential_sg"` key from their expected
  `field_source` dicts and from the set in `test_hopline_only`; `test_potential_sg` stays as is.
  `tests/test_hops.py` — drop the `beta_pct` assert and `field_source` key in `test_citra`, and
  `assert hop.beta_pct is None` in `test_pack_sizes_and_null_figures`.
- [x] Run `.venv/bin/python -m pytest -q` → 33 passed (no test added or removed).
- [x] Apply 010 twice:
  `docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/010_ref_schema.sql`
  → no error either time.
- [x] Re-run the loaders, each twice:
  - `.venv/bin/python -m loaders.styles --bjcp shared/rag-files/pending/styles.json --ba shared/rag-files/pending/ba_styles.json`
    → `BJCP 2021: 116 styles`, `BA 2026: 169 styles`
  - `.venv/bin/python -m loaders.malts --hopline shared/rag-files/pending/hopline_malts.json --catalogue shared/rag-files/pending/malt_catalogue.json`
    → `loaded: 74 malts`
  - `R=$(mktemp -d)/report.md; .venv/bin/python -m loaders.hops --hopline shared/rag-files/pending/hopline_hops.json --report "$R" && diff "$R" docs/finished/hop-loader/report.md`
    → `loaded: 90 hops`, no diff
- [x] Check (after the second run):
  - `Q "select count(*), count(distinct (source_id, code)) from ref.beer_style"` → `285|285`
  - `Q "select count(*) from ref.ingredient"` → `164`
  - `Q "select count(*), count(extract_dbfg_pct), count(*) filter (where field_source ? 'potential_sg') from ref.fermentable"` → `74|74|0`
  - `Q "select count(*), count(alpha_pct), count(*) filter (where field_source ? 'beta_pct') from ref.hop"` → `90|87|0`
  - `Q "select table_name, column_name from information_schema.columns where table_schema = 'ref' and (table_name, column_name) in (('beer_style','edition'),('beer_style','co2_vol'),('fermentable','potential_sg'),('fermentable','type'),('hop','beta_pct'),('hop','oils_pct'),('water_salt','molar_mass'))"` → no rows
  - `Q "select conname from pg_constraint where conrelid = 'ref.beer_style'::regclass and contype = 'u'"` → `beer_style_source_id_code_key` only
  - `Q "select i.raw->'hopline-hops'->'200750-cs'->'table'->>'Béta-sav' from ref.ingredient i where i.kind = 'hop' and i.name = 'Citra'"` → `3-4.5 %` as stored today (beta kept in `raw`)
- [x] PROJECT.md §8: dated line for this task with the measured results.
Done when: suite 33 passed, all checks above match, the hop report is unchanged.
Commit: `Drop unused ref columns and re-run loaders`

### Task 2: Create the style-fit vocabulary tables
Why: review §4.3 / §5.2; user decision "Everything in §5" (created now, empty).
- [x] Write `db/012_style_fit.sql`: header comment in 010's style (what it is, needs 010, the
  apply command, idempotent), then review §5.2 verbatim.
- [x] Apply twice with `-v ON_ERROR_STOP=1` → no error.
- [x] Check:
  - `Q "select count(*), count(*) filter (where tableowner = 'postgres') from pg_tables where schemaname = 'ref'"` → `15|15`
  - `Q "select data_type from information_schema.columns where table_schema = 'ref' and table_name = 'fermentable' and column_name = 'role'"` → `text`
  - `Q "select count(*) from pg_indexes where schemaname = 'ref' and indexname = 'ingredient_tag_tag_id_idx'"` → `1`
- [x] Prove the two constraints the review added instead of arrays and two-target columns
  (rolled back, nothing kept). Run with `ON_ERROR_STOP` **off**:
  ```
  begin;
  insert into ref.style_rule (style_id, level, quote)
       select id, 'allowed', 'test' from ref.beer_style limit 1;
  rollback;
  begin;
  insert into ref.tag (facet, name) values ('character', 'slim-ref-test');
  insert into ref.style_character (style_id, dimension, tag_id)
       select b.id, 'hop_aroma', t.id from ref.beer_style b, ref.tag t limit 1;
  rollback;
  ```
  → first insert fails on the `style_rule` check (neither ingredient nor tag), the
  `style_character` insert fails on its foreign key to `ref.style_sensory`. Then
  `Q "select count(*) from ref.tag"` → `0`.
- [x] PROJECT.md §8: dated line.
Done when: 15 `ref` tables owned by `postgres`, both constraints reject bad rows.
Commit: `Add style-fit vocabulary tables`

### Task 3: Create the `corpus` schema
Why: review §5.3; user decision "Everything in §5".
- [x] Write `db/013_corpus.sql`: header comment, then review §5.3 verbatim.
- [x] Apply twice with `-v ON_ERROR_STOP=1` → no error.
- [x] Check:
  - `Q "select nspowner::regrole from pg_namespace where nspname = 'corpus'"` → `postgres`
  - `Q "select count(*), count(*) filter (where tableowner = 'postgres') from pg_tables where schemaname = 'corpus'"` → `7|7`
  - `Q "select indexname from pg_indexes where schemaname = 'corpus' and indexname like '%\_idx' order by 1"` → `recipe_item_kind_raw_key_idx`, `recipe_item_recipe_id_idx`, `recipe_style_id_idx`
- [x] PROJECT.md §8: dated line.
Done when: 7 `corpus` tables owned by `postgres`, three indexes present.
Commit: `Add corpus schema`

### Task 4: Install pgvector and create the `kb` schema
Why: review §4.3 (`kb.document` merged into `ref.source`) / §5.4; user decision.
- [x] Write `db/014_kb.sql`: header comment, then
  `create extension if not exists vector with schema extensions;` (comment: `vector` is a
  supautils privileged extension, so `postgres` may create it), then review §5.4 verbatim.
- [x] Apply twice with `-v ON_ERROR_STOP=1` → no error. **If `create extension` fails with a
  permission error, stop:** report `blocked` with the error. Do not retry as `supabase_admin`
  (OPERATIONS.md §4); the user decides.
- [x] Check:
  - `Q "select extversion, extnamespace::regnamespace, extowner::regrole from pg_extension where extname = 'vector'"`
    → `0.8.0|extensions|…`; record the owner as measured (`supabase_admin`, like the other 8
    extensions, is expected and fine).
  - `Q "select tableowner from pg_tables where schemaname = 'kb' and tablename = 'chunk'"` → `postgres`
  - `Q "select format_type(atttypid, atttypmod) from pg_attribute where attrelid = 'kb.chunk'::regclass and attname = 'embedding'"` → `extensions.vector(1024)` or `vector(1024)`
  - `Q "select indexname, indexdef ~ 'hnsw', indexdef ~ 'gin' from pg_indexes where schemaname = 'kb' order by 1"`
    → `chunk_embedding_idx|t|f`, `chunk_fts_idx|f|t`, `chunk_pkey…`, `chunk_source_id_idx…`
  - `Q "select data_type from information_schema.columns where table_schema = 'ref' and table_name = 'source' and column_name = 'file_path'"` → `text`
- [x] PROJECT.md §8: dated line (with the measured extension owner).
Done when: `vector` 0.8.0 in `extensions`, `kb.chunk` owned by `postgres` with HNSW and GIN.
Commit: `Add kb schema with pgvector`

### Task 5: Create the `app` schema
Why: review §4.3 (typed water ions, typed results, profile snapshot) / §5.5; user decision.
- [x] Write `db/015_app.sql`: header comment, then review §5.5 verbatim.
- [x] Apply twice with `-v ON_ERROR_STOP=1` → no error.
- [x] Check:
  - `Q "select count(*), count(*) filter (where tableowner = 'postgres') from pg_tables where schemaname = 'app'"` → `8|8`
  - `Q "select column_name from information_schema.columns where table_schema = 'app' and table_name = 'recipe' and column_name in ('batch_l','efficiency_pct','og','fg','abv','ibu','srm') order by 1"` → 7 rows
  - `Q "select schemaname, count(*) from pg_tables where schemaname in ('ref','corpus','kb','app') group by 1 order by 1"` → `app|8`, `corpus|7`, `kb|1`, `ref|15` (31 tables, review §6)
- [x] PROJECT.md §8: dated line.
Done when: 8 `app` tables owned by `postgres`; 31 tables across the four schemas.
Commit: `Add app schema`

### Task 6: Describe the applied design in the docs
Why: CLAUDE.md (PROJECT.md is the source of truth; docs describe the current plan); the user
asked for "all the related files and the docs".
- [x] **`docs/DATABASE.md`: rewrite** to describe what is built, keeping the section numbers
  §1–§7 (fill-ref and ref-spotcheck link §2, §6, §7). Remove the "Under review" note and the
  "Nothing is built yet" status. Contents:
  - Status: built 2026-10-11 ([`slim-ref`](work/slim-ref/plan.md)) from the approved
    [DATABASE-REVIEW.md](DATABASE-REVIEW.md); the `.sql` files in `db/` (010–015) are the exact
    definitions, this file explains them. All tables were created up front, empty, **by user
    decision** (2026-10-11), not in the phase that fills them; each table names the phase that
    fills it.
  - TL;DR: the four schemas (as now); the column rule (a typed column only if a pipeline step
    reads it; everything else stays in `raw`; review §1); behaviour lives in code, not tables.
  - §1 the four schemas: diagram and table updated to the built tables (`ref` 15, `corpus` 7,
    `kb` 1, `app` 8); `usage_effect`, `hint_knob`, `document`, `source_weight` gone.
  - §2 `ref`: ER diagram and table per review §5.1/§5.2 and §6 (no `edition`, `co2_vol`,
    `potential_sg`, `type`, `beta_pct`, `oils_pct`, `molar_mass`; `fermentable.role`;
    `style_character` join table; `style_rule` with two nullable FKs; `ingredient_tag` without
    `weight`; `misc` with `category` only; `sensory_dimension` name + class). Row counts as
    measured after Task 1, empty tables marked empty with the phase that fills them. Rules for
    `ref` kept; style-rule flowchart: "usage effects (code)" instead of `usage_effect`.
  - §3 `corpus`: the 7 tables (`style_profile` split into `style_grist`, `style_hop_use`,
    `style_ingredient`; gate flags in `gates jsonb`; no `source_weight`).
  - §4 `kb`: `chunk` → `ref.source` directly (`ref.source.file_path`), bge-m3 1024 dims,
    `vector` 0.8.0 in schema `extensions` (owner as measured in Task 4), HNSW + GIN.
  - §5 `app`: ER diagram per review §5.5 (6 water-ion columns, typed `og…srm`, `batch_l` /
    `efficiency_pct` snapshot, `run_step.try`); `batch`, `tasting`, `inventory.best_before`
    listed as later.
  - §6 access rules: unchanged.
  - §7 build order: now "fill order" — step 1 loaded and step 2 partly (measured counts; yeasts
    and salts not loaded yet), the rest name the tables they fill.
  - New §8 "Behaviour in code, not tables": usage effects, hint knobs, sensory cut points,
    source weights (review §4.3), and §9 "Later": `ref.fault`, `app.batch`, `tasting`,
    `inventory.best_before`, `beer_style.co2_vol` (P6, with a source).
- [x] **`docs/DATABASE-REVIEW.md`**: status block → "approved 2026-10-11, applied 2026-10-11 by
  [`slim-ref`](work/slim-ref/plan.md); DATABASE.md now describes the built design". Edit in
  place the lines that say a table or column is added "in the phase that first fills it"
  (TL;DR rule bullet, §5 intro "Phase tags say when each part gets built", §9 placeholder row)
  so they say the phase tags name the phase that fills each part and everything was created on
  2026-10-11. Add at the bottom:
  `## Deviations` with `- 2026-10-11 · §5: all tables created now, empty, not in the phase
  that fills them — user decision ("Everything in §5"). fermentable.role is therefore an empty
  column until P3.`
- [x] **`docs/STYLE-FIT.md`**: §1 diagram subgraph "one small global table" → "in code"; §3
  heading → "Usage effects (in code, ~20 entries)" with one line saying they are a dict next to
  their tests (PROJECT.md §6.8); §4: cut points live in code; §5: `ref.sensory_dimension` holds
  name and class (no specialty category, no cut points). §2 fermentable row: role inputs
  "colour (EBC) + name keywords" instead of "colour + type" (`fermentable.type` was dropped;
  review §4.1) — see Question 1.
- [x] **`docs/STYLE-PROFILES.md`** §4: "Weights are one config table" → weights are a dict in
  code next to their tests.
- [x] **`docs/RECIPE-ROADMAP.md`**: §5 table "Usage effects" row "Lives in" → code (not
  `ref.usage_effect`); the "hint-knob table" cell → hint-knob dict in code.
- [x] **`docs/work/water-salts/plan.md`**: Rules line → ion values come from `ATOMIC_MASS` only
  (molar mass is computed in code, not stored); Task 2 upsert list without `molar_mass`; add a
  Deviations line `- 2026-10-11 · Task 2: no molar_mass column — dropped by the database
  review (slim-ref)`.
- [x] **`docs/work/ref-spotcheck/plan.md`**: Task 1 doc-update step → "`fermentable.role`
  exists but stays empty until P3; `beer_style.co2_vol` was dropped (no source has it; back in
  P6)" instead of the `type` / `co2_vol` notes; add a Deviations line naming slim-ref.
- [x] **`PROJECT.md`**:
  - §4 Database row: add the slim-ref result (7 columns dropped, loaders re-run with the counts
    from Task 1; `ref` 15 tables, `corpus` 7, `kb` 1, `app` 8, all owned by `postgres`, new
    ones empty) and the closed decision as `*Why this schema (was D4): …*` in one line (each
    typed column is read by a pipeline step, the rest stays in `raw`; behaviour in code;
    tables created up front by user decision).
  - §4 Vector search row: `vector` 0.8.0 in `extensions`, `kb.chunk` with HNSW + GIN created,
    empty (status 🟡).
  - §5 malt row: "74 with potential" → "74 with extract".
  - §7: remove D4 (its data-source part is D7 and D8).
  - §8: dated line for this task; "Last updated" date.
- [x] Run `.venv/bin/python -m pytest -q` → 33 passed.
- [x] `grep -rn -E 'potential_sg|beta_pct|oils_pct|molar_mass|co2_vol|usage_effect|hint_knob|source_weight|kb\.document|character_tags' docs/DATABASE.md docs/STYLE-FIT.md docs/STYLE-PROFILES.md docs/RECIPE-ROADMAP.md docs/work/`
  → only mentions that say the item was dropped or moved to code (and this plan).
Done when: DATABASE.md matches the catalog table and column names; no doc still describes a
dropped column or a behaviour table as current.
Commit: `Describe the applied database design in docs`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Re-loading styles updates rows on the new key, no duplicates | styles loader run twice → `285|285` (rows, distinct `(source_id, code)`) | 1 |
| Malt extract still merged correctly without `potential_sg` | `tests/test_malts.py::test_catalogue_wins_hopline_fills`, `::test_user_supplied_fills_only_gaps`, `::test_hopline_only` | 1 |
| Potential SG maths unchanged (maths library needs it) | `tests/test_malts.py::test_potential_sg` | 1 |
| Hop figures and provenance correct without `beta_pct` | `tests/test_hops.py::test_citra`, `::test_pack_sizes_and_null_figures`; hop report diff empty | 1 |
| `field_source` never names a dropped column | `field_source ? 'potential_sg'` / `? 'beta_pct'` counts = 0 | 1 |
| Dropped fields stay recoverable from `raw` | Citra `raw` still has `Béta-sav` | 1 |
| A style rule targets exactly one of ingredient or tag | rolled-back insert rejected by the `style_rule` check | 2 |
| A style character cannot exist without its envelope row | rolled-back insert rejected by the FK to `style_sensory` | 2 |
| Embeddings match bge-m3 | `kb.chunk.embedding` type is `vector(1024)` | 4 |
| Every new object owned by `postgres` (n8n and later scripts work) | `tableowner = 'postgres'` counts per schema | 2–5 |
| Each SQL file is idempotent | every file applied twice without error | 1–5 |

## Approved exceptions

## Deviations

- 2026-10-11 · Tasks 2–5: all review §5 tables created now, empty, not in the phase that fills
  them — user decision ("Everything in §5"), overriding the review's phase tags.
- 2026-10-11 · Task 6: DATABASE.md §7 marks step 2 partly done, not done — yeasts and salts
  are not loaded yet (measured: `ref.yeast` and `ref.water_salt` 0 rows).
