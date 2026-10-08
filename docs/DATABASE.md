# Database design

> **Status:** design, 2026-10-08. **Nothing is built yet**: the Supabase database is empty
> since the reset. Workflow context: [RECIPE-ROADMAP.md](RECIPE-ROADMAP.md).
> Table and column names are the plan. They become real in `.sql` files applied as `postgres`
> ([OPERATIONS.md](OPERATIONS.md) §4).

---

## TL;DR

- **4 schemas, split by how much you can trust the data**, not just "fact vs user".
- `ref` = curated reference. **Every row has a source + version.** Read-only for the app.
- `corpus` = what brewers actually do (community recipes, quality-weighted). Evidence for ratios, **never cited, never embedded**.
- `kb` = book text for RAG + citations.
- `app` = everything the user experience creates: profile, inventory, briefs, recipes, logs.
- Data only points **inward**: `app` → `ref`, never `ref` → `app`.

---

## 1. The four schemas

```mermaid
flowchart LR
    subgraph REF["🟦 ref: curated reference"]
      direction TB
      r1[source]
      r2[beer_style · style_sensory · style_rule]
      r3[ingredient + fermentable · hop · yeast · misc · water_salt]
      r4[tag · ingredient_tag · usage_effect · hint_knob]
    end
    subgraph CORP["🟨 corpus: observed practice"]
      direction TB
      c1[recipe · recipe_item]
      c2[name_map]
      c3[style_profile]
    end
    subgraph KB["🟩 kb: book knowledge"]
      direction TB
      k1[document · chunk]
    end
    subgraph APP["🟧 app: user experience"]
      direction TB
      a1[brewer_profile · inventory]
      a2[brief · recipe · recipe_item · recipe_deviation]
      a3[run · run_step]
      a4[batch · tasting]
    end
    APP -- "FK + reads" --> REF
    APP -- reads --> CORP
    APP -- reads --> KB
    CORP -- "name_map FK" --> REF
```

| Schema | Holds | Trust | Written by | Cited in a recipe? |
|---|---|---|---|---|
| 🟦 `ref` | styles, sensory envelopes, ingredient specs, tags, knobs | ⭐⭐⭐ authoritative, sourced, reviewed | load scripts + your review | ✅ as data ("BJCP 2021, 21A") |
| 🟨 `corpus` | community recipes + computed per-style stats | ⭐⭐ evidence of practice | one-off load + recompute job | ❌ only as "common practice: 88 % of recipes…" |
| 🟩 `kb` | book chunks + embeddings | ⭐⭐ cited knowledge | ingestion | ✅ with page/section |
| 🟧 `app` | user data, recipes, logs | yours | the pipeline | — |

**Why "curated", not "absolute truth":** BJCP gets revised (2015 → 2021), Weyermann and
Viking report the same malt type differently, and books disagree (IBU formulas). Source +
version per row lets two editions coexist and lets every number be traced.

---

## 2. `ref`: curated reference

```mermaid
erDiagram
    source ||--o{ beer_style : "cites"
    source ||--o{ ingredient : "cites"
    beer_style ||--o{ style_sensory : "envelope"
    beer_style ||--o{ style_rule : "overrides"
    ingredient ||--o| fermentable : "is a"
    ingredient ||--o| hop : "is a"
    ingredient ||--o| yeast : "is a"
    ingredient ||--o| misc : "is a"
    ingredient ||--o{ ingredient_tag : "has"
    tag ||--o{ ingredient_tag : "labels"
    tag ||--o{ tag : "parent"
    tag ||--o{ style_sensory : "allowed character"

    source {
        int id PK
        text title
        text edition
        text licence
        text url
    }
    beer_style {
        int id PK
        text guide "BJCP | BA"
        text code "21A"
        text name
        numrange og
        numrange fg
        numrange ibu
        numrange srm
        numrange abv
        numrange co2_vol
        text_arr characteristic_ingredients
        jsonb raw_text "aroma, flavour, mouthfeel..."
    }
    style_sensory {
        int style_id FK
        text dimension "hop_aroma, roast, sourness..."
        int min_level "0 none .. 7 very high"
        int max_level
        int_arr character_tags
        text quote "source sentence"
        bool reviewed
    }
    style_rule {
        int style_id FK
        int tag_or_ingredient
        text usage "null = any"
        text level "required..changes_style"
        numeric max_pct
        text quote
    }
    ingredient {
        int id PK
        text kind "fermentable|hop|yeast|misc|water_salt"
        text name
        text producer
        int source_id FK
    }
    tag {
        int id PK
        text facet "origin|character|role|family"
        text name
        int parent_id FK
    }
```

| Table | Key columns | Filled from | Rows (source) |
|---|---|---|---|
| `source` | title, edition, licence, url | by hand | ~15 |
| `beer_style` | guide, code, ranges (`numrange`), CO₂ volumes, raw text | `styles.json`, `ba_styles.json` | 116 BJCP + 169 BA |
| `style_sensory` | dimension, min/max level, character tags, quote, `reviewed` | BA: parsed by code · BJCP: LLM extract → **you review** | ~15 per style |
| `style_rule` | selector (tag or ingredient), usage, level, cap | by hand, rare | few |
| `ingredient` | kind, name, producer, source | all below | — |
| `fermentable` | potential (SG), colour (EBC + °L), role, max % | `malts.json` (77) + maltster sheets | 77+ |
| `hop` | alpha/beta range, oils, origin | `hops.json` 72 · `hops.hopslist.json` 268 · Brewtarget 282 (overlap, merge by name) | ~300 |
| `yeast` | producer, product id, attenuation range, temperature range, flocculation, alcohol tolerance | Brewtarget data (296 + 275) | ~500 after dedupe |
| `misc` | type (spice, fruit, fining, …), **no gravity data** | corpus `misc` names, by hand | grows |
| `water_salt` | formula, ions per gram | chemistry constants | ~8 |
| `tag` · `tag_synonym` | facet, name, parent ("citrusy" → citrus) | hops.json `flavour`, malt roles, yeast families | ~150 |
| `ingredient_tag` | ingredient ↔ tag, weight, `auto` or `reviewed` | derived by code from the ingredient's own data ([STYLE-FIT.md](STYLE-FIT.md) §2) | — |
| `usage_effect` | (kind, usage) → which sensory dimensions it drives, carries character or not | by hand, one small global table | ~20 |
| `sensory_dimension` | name, class (core · specialty · transforming), specialty category, intensity cut points | by hand + calibrated on the corpus ([STYLE-FIT.md](STYLE-FIT.md) §4) | ~15 |
| `hint_knob` | hint word → knob + direction + source | by hand, sourced | ~20 |
| `fault` *(later)* | name, descriptors, causes | `beer_faults.json` | 21 |

**Rules for `ref`**
- Every row has `source_id` (and the source has an edition).
- Units are SI (kg, L, °C, SG, EBC). Conversion happens only at display.
- Extras without gravity data (cinnamon, vanilla) are `misc` and **never enter the OG/IBU/SRM
  maths**.

### How a style rule is resolved (pure SQL, no LLM)

```mermaid
flowchart TD
    A["candidate:<br/>Citra · dry hop · 4 g/L<br/>style 15B"] --> B{"explicit style_rule<br/>for it or its tag?"}
    B -- yes --> Z["use that level"]
    B -- no --> C["usage_effect:<br/>dry hop → hop_aroma + character"]
    C --> D{"style_sensory 15B<br/>hop_aroma max = low<br/>character = earthy, floral"}
    D --> E{"dimension<br/>ruled out?"}
    E -- yes --> F["⛔ changes style"]
    E -- no --> G{"character match?<br/>dose ≤ corpus p90?"}
    G -- "mismatch / too much" --> H["⚠️ out of style"]
    G -- "tags match envelope" --> I["👍 typical"]
    G -- "no conflict" --> J["➖ allowed"]
```

✅ *required* comes from the style's characteristic ingredients and is checked at recipe
level ("the recipe has no pale base malt").

---

## 3. `corpus`: observed practice

| Table | Holds | Notes |
|---|---|---|
| `recipe` | one row per recipe: source, style string, batch, OG/FG/IBU/SRM as reported, **gate flags G1–G7, quality weight** | Brewer's Friend (CC0): 35,620 in the archive dump. Gates: [STYLE-PROFILES.md](STYLE-PROFILES.md) §2 |
| `recipe_item` | raw ingredient string, amount, use, time | raw strings kept as they are |
| `name_map` | raw string → `ref.ingredient` or just a role (base / crystal / roast…) + confidence | needed before any stats. Unmapped = honest, never guessed |
| `source_weight` | source → trust weight (corpus 1, books 3, own batches 5…) | config, one row per source |
| `style_profile` | per style: grist % per role (weighted median, IQR), hop split, dosage g/L percentiles, yeast ranking, misc usage, **n and family-blend share** | **computed** by a job, re-runnable |

- ⛔ Never embedded into `kb`. Self-reported, unvalidated data must not look like a citation.
- `style_profile` is the D7 ratio source. It feeds steps 5–9 of the workflow.

---

## 4. `kb`: book knowledge

| Table | Holds |
|---|---|
| `document` | title, author, edition, licence, file path, `source_id` → `ref.source` |
| `chunk` | document, section path, page, text, tokens, `embedding vector(1024)` (bge-m3), `fts tsvector` |

- Hybrid retrieval: HNSW vector index + full-text, fused.
- Only prose is stored here. Tables and formulas found in a book go through the
  **doc → calculation pass** first and land in `ref` or in code ([roadmap](RECIPE-ROADMAP.md) §6).

---

## 5. `app`: user experience

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
    recipe ||--o{ batch : "brewed as"
    batch ||--o{ tasting : "notes"

    brewer_profile {
        int id PK
        numeric batch_l
        numeric efficiency_pct
        numeric boil_off_l_h
        numeric losses_l
        jsonb source_water "Ca, Mg, Na, SO4, Cl, HCO3"
        text units "metric|us"
    }
    inventory {
        int profile_id FK
        int ingredient_id FK "null if not in ref"
        text raw_name
        numeric amount
        text unit
        date best_before
    }
    brief {
        int id PK
        text request_text
        jsonb brief "step 1 output"
        bool guidance_on
    }
    recipe {
        int id PK
        int brief_id FK
        int style_id FK "ref.beer_style"
        jsonb targets
        jsonb computed "OG FG ABV IBU SRM"
        text calc_version
        int parent_id FK
        text status "draft|final|brewed"
    }
    recipe_item {
        int recipe_id FK
        int ingredient_id FK "null for unlisted extras"
        text raw_name
        text usage "mash|boil|whirlpool|dry_hop|..."
        numeric time_min
        numeric pct
        numeric amount
        text unit
    }
    recipe_deviation {
        int recipe_id FK
        text subject
        text level
        text requested_by "user|model"
        text note
    }
    run_step {
        int run_id FK
        int step "0..16"
        jsonb input
        jsonb output
        int ms
        int tokens
        bool ok
    }
```

| Table | Why it exists |
|---|---|
| `brewer_profile` | equipment + water, stored once (step 0) |
| `inventory` | "use what I have" scoring in steps 6–9 |
| `brief` | the parsed request, so a recipe can be regenerated |
| `recipe` + `recipe_item` | the recipe **as rows**, with ratio (`pct`) **and** amount, plus the calc-code version that produced the numbers |
| `recipe_deviation` | the Deviations box: what is out of style, and whether you or the model asked for it |
| `run` + `run_step` | one log row per pipeline step: input, output, time, tokens. Debugging and evals |
| `batch` + `tasting` *(later)* | what was actually brewed and measured, for feedback |

---

## 6. Access rules

| Role | `ref` | `corpus` | `kb` | `app` |
|---|---|---|---|---|
| `postgres` (owner, migrations) | all | all | all | all |
| loader scripts | write | write | write | — |
| pipeline (n8n / service) | read | read | read | **read + write** |
| Supabase MCP (Claude Code) | read | read | read | read |

- All objects are owned by `postgres` and created from `.sql` files in the repo
  ([OPERATIONS.md](OPERATIONS.md) §4), never through MCP.
- `ref` has no foreign keys pointing into `app`.

---

## 7. Build order

| # | Step | Done when |
|---|---|---|
| 1 | `ref.source`, `ref.beer_style` ← both style JSONs | 116 + 169 rows, 5 spot-checked against the PDFs |
| 2 | `ref.ingredient` + kind tables ← malts, hops, Brewtarget yeasts, salts | counts match the sources after dedupe |
| 3 | `tag`, `ingredient_tag`, `usage_effect` | every hop has ≥ 1 character tag |
| 4 | `corpus.*` ← archive dump · `name_map` · `style_profile` job | ≥ 90 % of grist mass mapped to a role for the test styles |
| 5 | `style_sensory` for the test styles (BA parsed, BJCP extracted + reviewed) | the Citra table in the roadmap reproduces from SQL |
| 6 | `app.*` | a test brief → recipe rows + run_step log |
| 7 | `kb.*` | after the doc → calculation pass per book |
