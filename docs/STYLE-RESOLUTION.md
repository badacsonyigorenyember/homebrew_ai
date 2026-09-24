# Style resolution (S2)

How a brief's `style.value` becomes `brief.style.ref_id`: SQL ranks BJCP styles,
code accepts a clear winner, and an LLM picks between the close ones.
Worked out 2026-09-24. `ref.styles` is **BJCP 2021 only** (116 rows): the BA rows
were removed the same day, and the table's CHECK now refuses them
(`db/init/15_ref.sql`).

```
brief.style.value + brief.sensory + brief.targets.abv
        │
        ▼
 1. SQL shortlist  ── top 5 BJCP styles, scored
        │
        ▼
 2. Gate (code) ──── clear winner ──────────────► brief.style.ref_id
        │   └─────── no family match ───────────► ask the brewer (E1)
        ▼
 3. LLM picks ONE  ── formulate.recipe/resolve_style
        │
        ▼
 4. Check (code) ─────────────────────────────► brief.style.ref_id
```

## 1. SQL shortlist

Inputs are the brief's own slots:

| Input | From | Required |
|---|---|---|
| `family` | `brief.style.value`, the base family only (`stout`, `ipa`) | yes |
| `sensory` | `brief.sensory` (`aroma`, `flavour`, `appearance`, `mouthfeel` arrays) | no |
| `abv` | `brief.targets.abv` | no |

What it scores:

- **Family** filters on the style name or its `*-family` tag, punctuation
  stripped because the tags are inconsistent (`bock-family` vs `bockfamily`).
  If the family matches nothing, all 116 styles are ranked and
  `family_match = false`.
- **Sensory words** are searched in the matching BJCP field plus
  `overall_impression` and `tags`. A tag hit counts 1: tags are curated and never
  negated. A prose hit counts by how rare the word is in the family (0..1),
  because coffee, chocolate, black and full hit all eight stouts and decide
  nothing. ⚠️ Prose matching cannot see negation: "sweet" hits every stout
  through "low sweetness".
- **ABV** scores 1 inside the style's band, falling to 0 one band-width outside
  it, and is weighted x2 over the sensory score. Score range is 0–3.
- **Specialty styles** (29A–34C) rank last: a beer is filed under its base style.

For n8n, change the three `params` values to `$1::text`, `$2::jsonb`,
`$3::numeric` and pass `brief.style.value`, `JSON.stringify(brief.sensory)`,
`brief.targets.abv`.

```sql
WITH params AS (
  SELECT 'stout'::text AS family,                                   -- brief.style.value
         '{"aroma":["chocolate","coffee"],"flavour":["sweet"],"mouthfeel":["full","creamy"]}'::jsonb
                        AS sensory,                                 -- brief.sensory
         11::numeric    AS abv                                      -- brief.targets.abv, or NULL
),
fam AS (
  SELECT regexp_replace(lower(coalesce(family, '')), '[^a-z0-9]+', '', 'g') AS f FROM params
),
hit AS (   -- family match on name or *-family tag
  SELECT s.id FROM ref.styles s, fam
  WHERE s.guide = 'BJCP' AND fam.f <> ''
    AND (regexp_replace(lower(s.name), '[^a-z0-9]+', '', 'g') LIKE '%' || fam.f || '%'
         OR EXISTS (SELECT 1 FROM unnest(s.tags) t
                    WHERE regexp_replace(t, '-?family$|[^a-z0-9]+', '', 'g') = fam.f))
),
pool AS (  -- the family, or all BJCP styles if the family matched nothing
  SELECT s.*, EXISTS (SELECT 1 FROM hit) AS family_match
  FROM ref.styles s
  WHERE s.guide = 'BJCP'
    AND (s.id IN (SELECT id FROM hit) OR NOT EXISTS (SELECT 1 FROM hit))
),
words AS (
  SELECT DISTINCT e.key AS field, lower(btrim(w)) AS word
  FROM params, jsonb_each(coalesce(sensory, '{}')) e, jsonb_array_elements_text(e.value) w
  WHERE e.key IN ('aroma', 'flavour', 'appearance', 'mouthfeel') AND btrim(w) <> ''
),
hits AS (  -- word found in its own field, overall_impression or tags
  SELECT p.id, w.field, w.word,
         to_tsvector('english', array_to_string(p.tags, ' '))
           @@ plainto_tsquery('english', w.word) AS in_tags
  FROM pool p JOIN words w
    ON to_tsvector('english', concat_ws(' ',
         CASE w.field WHEN 'aroma'      THEN p.aroma
                      WHEN 'flavour'    THEN p.flavor
                      WHEN 'appearance' THEN p.appearance
                      ELSE p.mouthfeel END,
         p.overall_impression, array_to_string(p.tags, ' ')))
       @@ plainto_tsquery('english', w.word)
),
rarity AS ( -- 1 when one style matches the word, 0 when all do
  SELECT field, word,
         ln((SELECT count(*) FROM pool)::numeric / count(*))
           / nullif(ln((SELECT count(*) FROM pool)::numeric), 0) AS r
  FROM hits GROUP BY field, word
),
weighted AS ( -- a tag hit counts in full: tags are curated and never negated
  SELECT h.id, h.field, h.word,
         CASE WHEN h.in_tags THEN 1 ELSE coalesce(r.r, 0) END AS weight
  FROM hits h JOIN rarity r USING (field, word)
),
sens AS (
  SELECT id, sum(weight) AS raw, jsonb_object_agg(field, words) AS matched
  FROM (SELECT id, field, sum(weight) AS weight, jsonb_agg(word ORDER BY word) AS words
        FROM weighted GROUP BY id, field) x
  GROUP BY id
),
scored AS (
  SELECT p.*, sens.matched, params.abv AS target_abv,
         coalesce(sens.raw / nullif(max(sens.raw) OVER (), 0), 0) AS sensory_score,
         CASE WHEN params.abv IS NULL OR NOT p.has_vitals THEN NULL
              WHEN params.abv BETWEEN p.abv_min AND p.abv_max THEN 1
              ELSE greatest(0, 1 - greatest(p.abv_min - params.abv, params.abv - p.abv_max)
                                   / greatest(p.abv_max - p.abv_min, 1))
         END AS abv_score,
         (p.tags && ARRAY['specialty-beer', 'specialtybeer']) AS is_specialty
  FROM pool p CROSS JOIN params LEFT JOIN sens ON sens.id = p.id
)
SELECT id                                             AS ref_style_id,
       code || '. ' || name                           AS label,
       round(2 * coalesce(abv_score, 0) + sensory_score, 2) AS score,
       family_match,
       ref.f_range_text(abv_min, abv_max)             AS abv_range,
       CASE WHEN abv_score IS NULL THEN NULL
            WHEN target_abv < abv_min THEN 'below by ' || trim_scale(abv_min - target_abv)
            WHEN target_abv > abv_max THEN 'above by ' || trim_scale(target_abv - abv_max)
            ELSE 'in range' END                       AS abv_fit,
       coalesce(matched, '{}')                        AS matched,
       overall_impression
FROM scored
ORDER BY is_specialty, 2 * coalesce(abv_score, 0) + sensory_score DESC, code
LIMIT 5;
```

`measured` 2026-09-24 against the live table:

| Input | Top result |
|---|---|
| stout + pastry words + ABV 11 | 20C Imperial Stout 2.11, next 1.00 |
| stout + pastry words, no ABV | 15C / 16A / 16C within 0.05 of each other |
| stout + dry, roasty, bitter, light + 4.2 | 15B Irish Stout 3.00 |
| IPA + tropical, hazy, smooth + 6.5 | 21C Hazy IPA 3.00 |

Without an ABV the sensory words give a sensible top 3, not an answer. Keep
adjuncts (vanilla, lactose) out of `brief.sensory`: BJCP happens to mention
vanilla under 15C, which is enough to put it first.

## 2. Gate

| Case | Test on the rows | Action |
|---|---|---|
| No family match | row 1 `family_match = false` | Don't pick; `brief.style.value` is wrong. Ask the brewer (E1). |
| Clear winner | row 1 `abv_fit = 'in range'` **and** `score₁ − score₂ ≥ 0.5` | Take row 1, no LLM call. |
| Anything else | | Send the rows to the LLM. |

## 3. LLM pick

Prompt: `formulate.recipe/resolve_style` v1, stored in `obs.prompts` and seeded
from `db/init/62_obs_recipe_prompts.sql`. Run it through `wf-step-llm` with a
temperature-0 profile (`extract` or `critique`, never `creative`).

`vars_json` (`Style candidates` is the Postgres node running the query above):

```
{{ JSON.stringify({
  question:   $json.question,
  family:     $json.brief.style.value,
  target_abv: $json.brief.targets.abv ?? "not given",
  sensory:    JSON.stringify($json.brief.sensory),
  candidates: $('Style candidates').all().map(({ json: c }) =>
    `- id ${c.ref_style_id} | ${c.label} | score ${c.score} | ABV ${c.abv_range ?? "not defined"} (${c.abv_fit ?? "no target"})\n` +
    `  matched: ${JSON.stringify(c.matched)}\n` +
    `  description: ${c.overall_impression}`
  ).join("\n")
}) }}
```

`schema_json`: the allowed ids and labels are built from the same rows, so the
model can only answer with one of them:

```
{{ JSON.stringify({
  type: "object",
  additionalProperties: false,
  required: ["ref_style_id", "style_name", "abv_basis", "reason"],
  properties: {
    ref_style_id: { enum: $('Style candidates').all().map(i => i.json.ref_style_id) },
    style_name:   { enum: $('Style candidates').all().map(i => i.json.label) },
    abv_basis:    { type: "string", enum: ["given", "inferred", "none"] },
    reason:       { type: "string" }
  }
}) }}
```

⚠️ Ollama enforces `enum` in `format`. `measured` 2026-09-24 on
`gemma4:12b-it-q8_0`: asked for id 999 against `[74, 106, null]`, it returned
106. So the enum guarantees a **valid** id, not a **right** one: under pressure
the model silently substitutes a legal value.

## 4. Check

- `style_name` must be the label of `ref_style_id`. The two enums are
  independent, so a mismatched pair is possible. On a mismatch, trust the id.
- Write `output.ref_style_id` to `brief.style.ref_id`. Record `abv_basis` and
  `reason` in the trace: an `abv_basis` of `"none"` means the pick rests on
  descriptions alone.
- The validator's ABV band check still applies to the finished recipe.
