# Database design

> **Status:** built 2026-10-11 ([`slim-ref`](finished/slim-ref/plan.md)) from the approved
> [DATABASE-REVIEW.md](DATABASE-REVIEW.md). The `.sql` files in [`db/`](../db/) (`010`–`015`)
> are the exact definitions, applied as `postgres` ([OPERATIONS.md](OPERATIONS.md) §4); this
> file explains them. All tables were created up front, empty, **by user decision**
> (2026-10-11), not in the phase that fills them; each table below names the phase that fills
> it. Row counts were measured on the live DB on 2026-10-11. P1a (`ref` load, fill-order steps
> 1–2) is done and spot-checked ([`ref-spotcheck`](finished/ref-spotcheck/plan.md),
> `db/checks/ref_spotcheck.sql`).
> Workflow context: [RECIPE-ROADMAP.md](RECIPE-ROADMAP.md).

---

## TL;DR

- **4 schemas, split by how much you can trust the data**, not just "fact vs user".
- `ref` = curated reference. **Every row has a source + version.** Read-only for the app.
- `corpus` = what brewers actually do (community recipes, quality-weighted). Evidence for ratios, **never cited, never embedded**.
- `kb` = book text for RAG + citations.
- `app` = everything the user experience creates: profile, inventory, briefs, recipes, logs.
- Data only points **inward**: `app` → `ref`, never `ref` → `app`.
- **The column rule:** a typed column exists only if a pipeline step reads it. Everything else
  the source said stays in `raw jsonb`, so a field needed later is a migration plus a loader
  re-run ([review](DATABASE-REVIEW.md) §1).
- **Behaviour lives in code, not tables:** usage effects, hint knobs, sensory cut points and
  source weights are dicts next to their tests (§8, PROJECT.md §6.8).

---

## 1. The four schemas

```mermaid
flowchart LR
    subgraph REF["🟦 ref: curated reference · 19 tables"]
      direction TB
      r1[source]
      r2[beer_style · sensory_dimension · style_sensory · style_character · style_rule]
      r3[ingredient + fermentable · hop · yeast · misc · water_salt]
      r4[tag · tag_synonym · ingredient_tag · ingredient_review · style_ingredient]
    end
    subgraph CORP["🟨 corpus: observed practice · 7 tables"]
      direction TB
      c1[recipe · recipe_item]
      c2[name_map]
      c3[style_profile · style_grist · style_hop_use · style_ingredient]
    end
    subgraph KB["🟩 kb: book knowledge · 1 table"]
      direction TB
      k1[chunk]
    end
    subgraph APP["🟧 app: user experience · 8 tables"]
      direction TB
      a1[brewer_profile · inventory]
      a2[brief · recipe · recipe_item · recipe_deviation]
      a3[run · run_step]
    end
    APP -- "FK + reads" --> REF
    APP -- reads --> CORP
    APP -- reads --> KB
    CORP -- "FK" --> REF
    KB -- "chunk → source" --> REF
```

| Schema | Holds | Trust | Written by | Cited in a recipe? |
|---|---|---|---|---|
| 🟦 `ref` | styles, sensory envelopes, ingredient specs, tags | ⭐⭐⭐ authoritative, sourced, reviewed | load scripts + your review | ✅ as data ("BJCP 2021, 21A") |
| 🟨 `corpus` | community recipes + computed per-style stats | ⭐⭐ evidence of practice | one-off load + recompute job | ❌ only as "common practice: 88 % of recipes…" |
| 🟩 `kb` | book chunks + embeddings | ⭐⭐ cited knowledge | ingestion | ✅ with page/section |
| 🟧 `app` | user data, recipes, logs | yours | the pipeline | — |

35 tables in all (`ref` 19, `corpus` 7, `kb` 1, `app` 8), every one owned by `postgres` (measured 2026-10-15).

**Why "curated", not "absolute truth":** BJCP gets revised (2015 → 2021), Weyermann and
Viking report the same malt type differently, and books disagree (IBU formulas). Source +
version per row lets two editions coexist and lets every number be traced.

---

## 2. `ref`: curated reference

Defined in [`db/010_ref_schema.sql`](../db/010_ref_schema.sql) (sources, styles, ingredients),
[`db/011_ref_sources.sql`](../db/011_ref_sources.sql) (source rows) and
[`db/012_style_fit.sql`](../db/012_style_fit.sql) (style-fit vocabulary).

```mermaid
erDiagram
    source ||--o{ beer_style : "cites"
    source ||--o{ ingredient : "cites"
    ingredient ||--o| fermentable : "is a"
    ingredient ||--o| hop : "is a"
    ingredient ||--o| yeast : "is a"
    ingredient ||--o| misc : "is a"
    ingredient ||--o| water_salt : "is a"
    ingredient ||--o{ ingredient_tag : "has"
    tag ||--o{ ingredient_tag : "labels"
    tag ||--o{ tag_synonym : "spelled as"
    tag ||--o{ tag : "parent"
    beer_style ||--o{ style_sensory : "envelope"
    sensory_dimension ||--o{ style_sensory : "measures"
    style_sensory ||--o{ style_character : "allows"
    tag ||--o{ style_character : "character"
    beer_style ||--o{ style_rule : "exceptions"
    ingredient ||--o{ style_rule : "or"
    tag ||--o{ style_rule : "or"
    beer_style ||--o{ style_ingredient : "characteristic"
    ingredient ||--o{ ingredient_review : "flagged"

    source {
        bigint id PK
        text slug
        text title
        text edition
        text licence
        text url
        text file_path "book file, if any"
    }
    beer_style {
        bigint id PK
        bigint source_id FK
        text guide "BJCP | BA"
        text code "21A; unique with source_id"
        text name
        numrange og
        numrange fg
        numrange ibu
        numrange srm
        numrange abv
        text characteristic_ingredients
        jsonb raw "whole source record"
    }
    ingredient {
        bigint id PK
        text kind "fermentable|hop|yeast|misc|water_salt"
        text name
        text producer
        bigint source_id FK
        jsonb raw
    }
    fermentable {
        bigint ingredient_id PK
        numeric extract_dbfg_pct
        numrange ebc
        numeric max_pct
        text role "base|kilned|crystal|roast|adjunct|sugar"
        text fermentability "full|normal|none"
        jsonb field_source
    }
    hop {
        bigint ingredient_id PK
        text_arr origins
        text purpose "aroma|bittering|dual"
        numrange alpha_pct
        numrange total_oil_ml_100g
        jsonb field_source
    }
    sensory_dimension {
        text name PK "hop_aroma, roast, sourness..."
        text class "core|specialty|transforming"
    }
    style_sensory {
        bigint style_id PK
        text dimension PK
        smallint min_level "0 none .. 7 very high"
        smallint max_level
        text quote "source sentence"
        bool reviewed
    }
    style_character {
        bigint style_id PK
        text dimension PK
        bigint tag_id PK
    }
    style_rule {
        bigint id PK
        bigint style_id FK
        bigint ingredient_id FK "exactly one of"
        bigint tag_id FK "ingredient or tag"
        text usage "null = any"
        text level "required..changes_style"
        numeric max_pct
        text quote
    }
    style_ingredient {
        bigint id PK
        bigint style_id FK
        text role "or ingredient_id or tag_id"
        bool required
        numeric min_pct
        text quote
        bool reviewed
    }
    ingredient_review {
        bigint ingredient_id PK
        text reason
    }
    tag {
        bigint id PK
        text facet "origin|character|family"
        text name
        bigint parent_id FK
    }
```

| Table | Key columns | Filled from | Rows (2026-10-11; style-fit tables 2026-10-15) |
|---|---|---|---|
| `source` | slug, title, edition, licence, url, `file_path` (book file, for `kb`) | by hand, `db/011_ref_sources.sql` | 18 |
| `beer_style` | guide, code (unique per source), ranges (`numrange`), characteristic ingredients, `raw` | `styles.json`, `ba_styles.json` | 285: BJCP 2021 116 + BA 2026 169 |
| `ingredient` | kind, name, producer, source, `raw` | all kind loaders | 297 (81 fermentable, 89 hop, 119 yeast, 8 water_salt; Sterling removed 2026-10-15) |
| `fermentable` | extract (% dbfg, as the sources state it), colour (EBC range), max % of grist, `role`, `fermentability` (`full` / `normal` / `none`), `enzyme_activity` (`none` / `low` / `normal` / `high`), `min_boil_min` (60-120), `description`, `description_ref`, `field_source` | hopline malt pages + Weyermann, Viking, Simpsons catalogues; hopline flake and sugar pages + Palmer, *How to Brew* Tables 18.5 and 24.1 (adjuncts) | 81: 74 malts + 7 adjuncts (4 flakes, brown candi sugar, lactose, honey); 81 with extract, 78 with EBC (the 4 flakes have a sourced colour; Honey, Lactose, Enzyme Malt do not), 81 with `max_pct` (63 from the catalogues, 18 `user-supplied`, decision E); fermentability `normal` 78, `full` 2, `none` 1; `role` 81 (base 20, kilned 13, crystal 27, roast 13, adjunct 5, sugar 3); `enzyme_activity` 51 (none 30, high 12, low 6, normal 3; 30 empty, listed in the s2 report); `min_boil_min` 81 (60, and 90 for 7); `description` 81. Loaded by `loaders/fermentable_facts.py`, which must run after `loaders.malts` and `loaders.adjuncts` (they rewrite `max_pct` and `field_source`) |
| `fermentable_substitute` · view `fermentable_substitutes` | pair of fermentables stored once (smaller id first), source, note; the view lists both directions | `loaders/fermentable_facts.py` (substitution chart, user decisions) | 27 pairs (19 chart, 8 user decisions) |
| `fermentable_style` | malt ↔ style it is typically used for, source | `loaders/fermentable_facts.py` (maltster catalogues, mapped through the approved `[style_names]` table) | 623 rows, 59 malts |
| `hop` | origins, purpose, alpha range, total oil, `field_source` | hopline hop pages; values hopline lacks (4 hops' alpha/oil, Enigma's purpose) from Beer Maverick through the hop loader | 89 (all with alpha and total oil; Sterling removed 2026-10-15) |
| `yeast` | product id, type, form, attenuation range, temperature range, flocculation, alcohol tolerance | hopline dry and liquid yeast pages; attenuation from the makers' catalogues and data sheets (Brewfather for Gozdawa and Brewline) | 119 (dry 81, liquid 38; 93 with attenuation) |
| `water_salt` | formula, ions per gram | computed from IUPAC atomic masses (`loaders/water_salts.py`) | 8 |
| `misc` | `category` (spice, fruit, wood, vanilla, …), **no gravity data** | corpus `misc` names, by hand | empty, P3 |
| `tag` · `tag_synonym` | facet, name, parent ("citrusy" → citrus) · source word → tag | `loaders/style_fit_vocab.toml` through `loaders/tags.py` | 69 tags, 239 synonyms (2026-10-15) |
| `ingredient_tag` | ingredient ↔ tag, `reviewed` (false = derived by code); no weight, match strength comes from the tag tree | derived by code from the ingredient's own data ([STYLE-FIT.md](STYLE-FIT.md) §2) | 806 rows for 289 ingredients: fermentable 234 (81), hop 343 (89), yeast 229 (119); all `reviewed = false`; 38 yeasts in `ingredient_review` instead (2026-10-15) |
| `sensory_dimension` | name, class (core · specialty · transforming) | by hand | 18 (2026-10-15) |
| `style_sensory` | per style and dimension: min/max level, quote, `reviewed` | BJCP and BA prose: LLM extract (D2 model) → **you review** | 189 rows for 24 styles, all reviewed (31B and the BA Specialty Honey Beer have none by the user's choice) (2026-10-15) |
| `style_character` | characters a style allows for a dimension (15B hop_aroma: earthy, floral); FK to its `style_sensory` row and to `tag` | same as `style_sensory` | 237 (2026-10-15) |
| `style_rule` | style, **exactly one of** ingredient or tag (check constraint), usage, level, cap, quote | by hand, rare | empty: the golden set and the reference recipes need no override (2026-10-15) |
| `style_ingredient` | per style: a characteristic ingredient (an ingredient or a tag, or a role), `required`, `min_pct`, the guideline `quote`, `reviewed` | BJCP and BA prose: LLM extract (D2 model) → **you review** (`loaders/style_envelopes.py`) | 116 rows for the 26 s3 styles, all reviewed (2026-10-15) |
| `ingredient_review` | an ingredient the tagger could not tag from its own data, with the `reason`; nothing is guessed | `loaders/tags.py` | 38 (all yeasts) (2026-10-15) |

Dropped from the first design by the review (§4.1): `beer_style.edition` (it is
`source.edition`), `co2_vol` (no source has it; §9), `fermentable.potential_sg` (computed from
extract in code), `fermentable.type` (replaced by `role`), `hop.beta_pct` and `oils_pct` (no step
reads them; beta stays in `raw`), `water_salt.molar_mass` (computed in code).

**Rules for `ref`**
- Every loaded row is sourced: `beer_style` and `ingredient` have `source_id` (and the source
  has an edition); the kind tables are sourced through their `ingredient` row, and fermentables,
  hops and yeasts record each field's source in `field_source`. The style-fit vocabulary (`tag`,
  `tag_synonym`, `sensory_dimension`, …) is hand-made and reviewed; envelopes and rules carry
  their guideline `quote` instead.
- Units are SI (kg, L, °C, SG, EBC). Conversion happens only at display.
- A value no source states stays `NULL`, never 0. Computed values (potential SG, molar mass) are
  not stored.
- Anything with gravity (malts, flakes, sugars, lactose, honey) is a `fermentable` and enters
  OG through its extract. Its `fermentability` says how much of that extract yeast can ferment:
  `full` all of it, `normal` follows the yeast's attenuation (grain malts and flakes; the
  default, needs no source), `none` none of it (lactose stays whole in FG). `full` and `none`
  must be stated by a source and recorded in `field_source`.
  Sugar and honey extracts are Palmer's as-sold PPG ÷ 46 (water included), not dry basis:
  apply no moisture correction to them.
- Extras without gravity data (cinnamon, vanilla) are `misc` and **never enter the OG/IBU/SRM
  maths**.
- Fermentable `role` is derived by code from EBC + name keywords.

### How a style rule is resolved (pure SQL + code, no LLM)

```mermaid
flowchart TD
    A["candidate:<br/>Citra · dry hop · 4 g/L<br/>style 15B"] --> B{"explicit style_rule<br/>for it or its tag?"}
    B -- yes --> Z["use that level"]
    B -- no --> B2{"adjunct or sugar?"}
    B2 -- "named by the style: 👍<br/>not named: ⚠️" --> Z2["use that level"]
    B2 -- no --> C["usage effects (code):<br/>dry hop → hop_aroma + character"]
    C --> D{"style_sensory 15B<br/>hop_aroma max = low<br/>style_character = earthy, floral"}
    D --> E{"dimension<br/>ruled out?"}
    E -- yes --> F["⛔ changes style"]
    E -- no --> G{"character match?<br/>dose ≤ envelope max<br/>(cut points)?"}
    G -- "mismatch / too much" --> H["⚠️ out of style"]
    G -- "tags match envelope" --> I["👍 typical"]
    G -- "no conflict" --> K{"fermentable listed in<br/>fermentable_style?"}
    K -- yes --> I
    K -- no --> J["➖ allowed"]
```

✅ *required* comes from the style's characteristic ingredients and is checked at recipe
level ("the recipe has no pale base malt").

---

## 3. `corpus`: observed practice

Defined in [`db/013_corpus.sql`](../db/013_corpus.sql). All empty: P1b loads the recipes, P3
builds the name map and computes the profiles.

| Table | Holds | Notes |
|---|---|---|
| `recipe` | one row per recipe: source, external id, mapped style, batch, efficiency, boil, OG/FG/IBU/SRM/ABV as reported, views, **`gates jsonb`** (G1–G7 flags), **quality weight**, `raw` | Brewer's Friend (CC0): 35,620 in the archive dump. Unique on (source, external id). Gates: [STYLE-PROFILES.md](STYLE-PROFILES.md) §2 |
| `recipe_item` | kind, raw ingredient string (as written) + its `raw_key`, amount, use, time, reported alpha | raw strings kept as they are; indexed on `recipe_id` and `(kind, raw_key)` |
| `name_map` | (kind, raw key) → `ref.ingredient` or just a role (base / crystal / roast…) + method (exact · rule · reviewed) | needed before any stats. Unmapped = absent, never guessed |
| `style_profile` | per style: `n_recipes` after gates, family-blend share, computed at | **computed** by a job, re-runnable; parent of the three below |
| `style_grist` | per style and role: p25 / p50 / p75 % of grist, share of recipes using it | |
| `style_hop_use` | per style and use: hop mass share, g/L p10 / p50 / p90 | |
| `style_ingredient` | per style: top yeasts, hops, malts, extras with share of recipes, typical use, median dose | |

- ⛔ Never embedded into `kb`. Self-reported, unvalidated data must not look like a citation.
- The style profile tables are the D7 ratio source. They feed steps 5–9 of the workflow.
- Gates set flags and never delete; source weights (corpus 1, books 3, own batches 5…) are in
  code (§8).

---

## 4. `kb`: book knowledge

Defined in [`db/014_kb.sql`](../db/014_kb.sql). Empty until P7.

| Table | Holds |
|---|---|
| `chunk` | `source_id` → `ref.source` (a book is a source row, with `file_path`), section path, page, text, tokens, `embedding vector(1024)` (bge-m3), `fts tsvector` (generated, English) |

- No separate document table: title, edition and licence live in `ref.source`.
- `vector` 0.8.0 is installed in schema `extensions` (owner `supabase_admin`, like the other
  extensions; created by `postgres` as a supautils privileged extension).
- `pg_jsonschema` 0.3.3 is installed in schema `extensions` the same way (created in
  `db/015_app.sql`). Step contracts are checked with `extensions.jsonschema_validation_errors`.
- Hybrid retrieval: HNSW index on `embedding` (cosine) + GIN on `fts`, fused; plus an index on
  `source_id` to delete or re-ingest one book.
- Only prose is stored here. Tables and formulas found in a book go through the
  **doc → calculation pass** first and land in `ref` or in code ([roadmap](RECIPE-ROADMAP.md) §6).

---

## 5. `app`: user experience

Defined in [`db/015_app.sql`](../db/015_app.sql). All empty: P4–P5 fill them, `recipe.process`
in P6.

```mermaid
erDiagram
    brewer_profile ||--o{ inventory : "owns"
    brewer_profile ||--o{ brief : "asks"
    brief ||--o{ recipe : "produces"
    recipe ||--o{ recipe_item : "contains"
    recipe ||--o{ recipe_deviation : "lists"
    recipe ||--o| recipe : "version of"
    brief ||--o{ run : "runs"
    run ||--o{ run_step : "logs"

    brewer_profile {
        bigint id PK
        numeric batch_l
        numeric efficiency_pct
        numeric boil_off_l_h
        numeric losses_l
        numeric grain_abs_l_kg
        numeric ca_mg_l
        numeric mg_mg_l
        numeric na_mg_l
        numeric so4_mg_l
        numeric cl_mg_l
        numeric hco3_mg_l
        text units "metric|us"
    }
    inventory {
        bigint profile_id FK
        bigint ingredient_id FK "null if not in ref"
        text raw_name
        numeric amount
        text unit
    }
    brief {
        bigint id PK
        bigint profile_id FK "null until step 0, M4"
        text request_text
        jsonb brief "step 1 output"
        bool guidance_on
    }
    recipe {
        bigint id PK
        bigint brief_id FK
        bigint parent_id FK
        bigint style_id FK "ref.beer_style"
        text status "draft|final|brewed"
        numeric batch_l "snapshot"
        numeric efficiency_pct "snapshot"
        jsonb targets
        numeric og
        numeric fg
        numeric abv
        numeric ibu
        numeric srm
        text calc_version
        jsonb process "P6"
    }
    recipe_item {
        bigint recipe_id FK
        bigint ingredient_id FK "null for unlisted extras"
        text raw_name
        text usage "mash|boil|whirlpool|dry_hop|..."
        numeric time_min
        numeric pct
        numeric amount
        text unit
    }
    recipe_deviation {
        bigint recipe_id FK
        text subject
        text level "out_of_style|changes_style"
        text requested_by "user|model"
        text note
    }
    run {
        bigint id PK
        bigint brief_id FK "null until step 1"
        bigint recipe_id FK
        text model
        text eval_id "eval brief id"
        timestamptz finished_at
        bool ok
    }
    run_step {
        bigint run_id PK
        smallint step PK "0..16"
        smallint try PK "validate retries"
        jsonb input
        jsonb output
        bool ok
        int ms
        int tokens
        text error "set iff ok = false"
        jsonb llm "LLM steps: model, think, tries, tokens, ms"
    }
```

| Table | Why it exists |
|---|---|
| `brewer_profile` | equipment + water, stored once (step 0); the 6 source-water ions are typed columns |
| `inventory` | "use what I have" scoring in steps 6–9 |
| `brief` | the parsed request, so a recipe can be regenerated; `profile_id` is null until step 0 builds profiles (M4) |
| `recipe` + `recipe_item` | the recipe **as rows**, with ratio (`pct`) **and** amount; typed results `og…srm`; `batch_l` and `efficiency_pct` snapshot the profile used, so editing the profile never changes an old recipe; `calc_version` names the maths that produced the numbers |
| `recipe_deviation` | the Deviations box: what is out of style, and whether you or the model asked for it |
| `run` + `run_step` | one log row per pipeline step and try: input, output, time, tokens. Debugging and evals. A run exists before its brief (step 1 writes it), so `run.brief_id` can be null; `finished_at` / `ok` stay null until the run ends; a failed step always says why (`error` is set exactly when `ok` is false); `llm` holds an LLM step's model, thinking, tries, tokens, time and first-try errors |

Function `app.step1_read_answer(request, content, contract)` (db/020_step1.sql) checks a model's step 1 answer: parses it, drops repeated words, validates it against the contract, and requires every `stated` number to be written in the request.

Function `app.style_pair()` (db/021_style_pairs.sql) lists the 151 decided BA 2026 to BJCP 2021 style pairs (`ba_code`, `bjcp_code`); step 2 returns the BJCP style when the best fit is a paired BA style.

Step 2 signal functions (db/022_step2.sql), each tested alone: `app.style_words`, `app.style_alias`, `app.style_name_score` (name match, 0 to 1), `app.style_number_score` (stated numbers against a style's ranges), `app.brief_words`, `app.style_tags`, `app.style_word_score` (hints and unknown words against tags and text), `app.style_name_covers` (every named word is in the style's name), `app.guide_from_request` and `app.specialty_style`.

Function `app.step2_best_style(brief, request, guide_preference)` (db/022_step2.sql) picks the best-fit style: scores both guides (name, numbers with a tightness bonus, words), returns the BJCP pair of a BA winner unless that pair is a catch-all in `app.bjcp_catch_all()`, applies the specialty and mismatch rules and returns the style, alternatives, scores and reasons.

Later (§9): `batch`, `tasting`, `inventory.best_before`.

---

## 6. Access rules

| Role | `ref` | `corpus` | `kb` | `app` |
|---|---|---|---|---|
| `postgres` (owner, migrations) | all | all | all | all |
| loader scripts | write | write | write | — |
| pipeline (n8n) | read | read | read | **read + write** |
| Supabase MCP (Claude Code) | read | read | read | read |

- All objects are owned by `postgres` and created from `.sql` files in the repo
  ([OPERATIONS.md](OPERATIONS.md) §4), never through MCP.
- `ref` has no foreign keys pointing into `app`.

---

## 7. Fill order

All tables exist (§1). This is the order they get data in.

| # | Step | Tables filled | Done when |
|---|---|---|---|
| 1 | Styles | `ref.source`, `ref.beer_style` ← both style JSONs | ✅ 285 rows (BJCP 116 + BA 169), 18 sources, 0 rows without a source; 10 rows per table spot-checked against the sources, no errors (2026-10-11, `ref-spotcheck`). `co2_vol` was dropped: no source has it; back in P6 |
| 2 | Ingredients | `ref.ingredient` + kind tables ← malts, hops, hopline yeasts, salts | ✅ malts 74, adjuncts 7, hops 89 (Sterling removed by the user 2026-10-15), yeasts 119, salts 8 (297 ingredients), 0 without a source; 10 rows per table spot-checked, no errors (2026-10-11). Adjuncts (2026-10-11): 4 flakes (oats, corn, rice, barley), brown candi sugar and lactose from hopline, honey from Palmer, extract from Palmer Tables 18.5/24.1. Gaps: the malts are grain malts from three maltsters only; no malt extracts, and other hopline adjuncts (rye, wheat, chit flakes, white candi, fructose) are not loaded; 8 hop values were entered by hand from Beer Maverick (`hop.field_source` = `beermaverick`): alpha and oil of Delta, Lotus and Sterling, Mount Hood's oil and Enigma's purpose; all 8 checked against beermaverick.com by the user, all match (2026-10-11) |
| 3 | Style-fit vocabulary | `ref.tag`, `tag_synonym`, `ingredient_tag`, `misc`, `fermentable.role` | ✅ every hop has ≥ 1 character tag: 89 of 89 hops tagged (343 hop tags), 38 yeasts flagged in `ingredient_review` instead of guessed (measured 2026-10-15, `s3-style-fit`); `misc` stays empty (no style needs it) |
| 4 | Corpus (not loaded, D7, 2026-10-14; style fit does not use it) | `corpus.recipe`, `recipe_item` ← archive dump · `name_map` · profile job → `style_profile`, `style_grist`, `style_hop_use`, `style_ingredient` | ≥ 90 % of grist mass mapped to a role for the test styles |
| 5 | Envelopes | `ref.sensory_dimension`, `style_sensory`, `style_character`, `style_ingredient` for the 26 s3 styles (BJCP and BA extracted by the LLM + reviewed); `style_rule` where needed | ✅ 26 styles reviewed (116 `style_ingredient`, 189 `style_sensory`, 237 `style_character` rows); the Citra table reproduces from SQL + code and the 53 golden cases pass (measured 2026-10-15, `s3-style-fit`) |
| 6 | Pipeline | `app.*` | a test brief → recipe rows + run_step log |
| 7 | Books | `kb.chunk` (and `ref.source.file_path`) | after the doc → calculation pass per book |

---

## 8. Behaviour in code, not tables

These say *how the algorithm behaves*, so they live in code next to their tests, where a reader
sees them with the logic that uses them (PROJECT.md §6.8; review §4.3):

| Behaviour | Was planned as | Lives in |
|---|---|---|
| Usage effects (dry hop → hop aroma + character, ~20 entries) | `ref.usage_effect` | `app.usage_effects()` ([STYLE-FIT.md](STYLE-FIT.md) §3) |
| Hint knobs (hint word → knob + direction, ~20 entries, each with its book source) | `ref.hint_knob` | a dict in the targets step ([RECIPE-ROADMAP.md](RECIPE-ROADMAP.md) §7) |
| Sensory intensity cut points (from *How to Brew* and OBC, or set by the user) | columns on `ref.sensory_dimension` | `app.style_fit_cut_points()` ([STYLE-FIT.md](STYLE-FIT.md) §4) |
| Source weights (corpus 1, books 3, own batches 5…) | `corpus.source_weight` | the profile job ([STYLE-PROFILES.md](STYLE-PROFILES.md) §4) |
| Potential SG from extract | `fermentable.potential_sg` | the maths library (tested) |
| Salt molar mass | `water_salt.molar_mass` | `loaders/water_salts.py` (tested), which stores only the result, `water_salt.ion_mg_per_l_per_g` |

---

## 9. Later

Not built; each comes with the feature or source that needs it.

| What | When |
|---|---|
| `ref.fault` (name, descriptors, causes ← BJCP fault list 2012 (24) and the study guide's *Beer Characteristics* (25), `shared/rag-files/sensory/`; `beer_faults.json` was lost) | fault diagnosis (Priority 2) |
| `app.batch` + `tasting` | batch log feature |
| `app.inventory.best_before` | when a step reads it |
| `ref.beer_style.co2_vol` | P6 (step 15), together with a source that states it (e.g. Palmer ch. 11) |
| A style family for BA styles | when a BA style needs a style profile (D1: step 2 can pick a BA style): `category_code` is `NULL` for all 169 BA rows (the source has none), so the thin-style family fallback ([STYLE-PROFILES.md](STYLE-PROFILES.md) §3) would use BA's `category` text (10 origin families, e.g. *British Origin Ale Styles*) |
