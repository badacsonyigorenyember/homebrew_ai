-- =============================================================================
-- 03c-seed-batches.template.sql  ·  Phase 2, §11: "seed 3–5 real batches by hand"
--
-- ⚠️  THIS IS A TEMPLATE, NOT A SEED FILE. Every value below is a placeholder.
--
-- brew.* is the TRUTH schema (architecture §3.3). Its whole contract is that
-- every number in it is a number you actually measured. Inventing plausible
-- batches to "have something to test with" poisons that contract silently:
-- the Phase 3 eval (§10.2, truth correctness = 1.00, no tolerance) would then be
-- scored against fiction, and you would never find out from the inside.
--
-- So: open this file, replace every <<PLACEHOLDER>> with a real record from your
-- own brewing, delete the batch blocks you don't need, delete the guard below,
-- and only then run it.
--
-- Run:
--   docker exec -i supabase-db psql -U postgres -d postgres \
--     < "plans/phase2/03c-seed-batches.template.sql"
--
-- Three to five batches is enough. You need enough variety that the §04 gate can
-- tell "routed correctly" from "routed correctly and found nothing":
--   · at least two different styles
--   · at least two with dry hop additions (that's what exercises
--     brew.f_dry_hop_rate_g_per_l, the §8.5 trace)
--   · at least two with sensory notes carrying descriptors
--   · a spread of brew dates, so date filters have something to bite on
-- =============================================================================

\set ON_ERROR_STOP on
BEGIN;

-- --- GUARD: delete this block once you have filled in real data --------------
DO $guard$ BEGIN
  RAISE EXCEPTION
    'Template not filled in. Replace the <<PLACEHOLDER>> values with real batch data, then delete this guard block.';
END $guard$;
-- ----------------------------------------------------------------------------


-- =============================================================================
-- 1. INGREDIENTS
-- Only the ones you actually reference below. Hops need alpha_acid_pct if you
-- want it recorded; the dry-hop rate math only needs qty and unit.
--
-- NOTE on `supplier`: the UNIQUE key is (kind, name, supplier), and Postgres
-- treats NULLs as distinct — a NULL supplier makes ON CONFLICT a no-op and you
-- will accumulate duplicate ingredients on every re-run. Use a real string
-- ('unknown' is fine), never NULL.
-- =============================================================================

INSERT INTO brew.ingredients (kind, name, supplier, alpha_acid_pct, color_lovibond, attenuation_min, attenuation_max)
VALUES
  ('hop',         '<<HOP NAME>>',         '<<SUPPLIER>>', <<ALPHA_PCT>>, NULL, NULL, NULL),
  ('fermentable', '<<MALT NAME>>',        '<<SUPPLIER>>', NULL, <<LOVIBOND>>, NULL, NULL),
  ('yeast',       '<<YEAST STRAIN>>',     '<<SUPPLIER>>', NULL, NULL, <<ATTEN_MIN>>, <<ATTEN_MAX>>)
ON CONFLICT (kind, name, supplier) DO NOTHING;


-- =============================================================================
-- 2. BATCH BLOCK — copy this whole block once per batch (3–5 times)
-- Replace every <<...>>. Keep the recipe name/version consistent between the
-- recipe, the recipe items and the batch.
-- =============================================================================

-- 2a. Recipe -----------------------------------------------------------------
-- style_id resolves from the BJCP 2021 table you already loaded in Phase 1
-- (116 styles). Use the code: '21A' American IPA, '15B' Irish Stout, etc.
INSERT INTO brew.recipes
  (name, version, style_id, batch_size_l, target_og, target_fg, target_ibu, notes)
VALUES (
  '<<RECIPE NAME>>',
  <<RECIPE VERSION, e.g. 1>>,
  (SELECT id FROM brew.bjcp_styles WHERE guide_year = 2021 AND code = '<<BJCP CODE>>'),
  <<BATCH SIZE L>>,
  <<TARGET OG, e.g. 1.062>>,
  <<TARGET FG, e.g. 1.012>>,
  <<TARGET IBU>>,
  <<'notes' or NULL>>
)
ON CONFLICT (name, version) DO NOTHING;

-- 2b. Dry hop additions ------------------------------------------------------
-- This is what brew.f_dry_hop_rate_g_per_l sums (stage = 'dryhop'), divided by
-- brew.batches.volume_l. Skip this block for a batch with no dry hop.
--
-- ⚠️ brew.recipe_items has NO unique constraint. The NOT EXISTS guard is what
-- stops a second run from doubling your dry hop rate — a wrong number that
-- looks entirely plausible. Do not remove it.
INSERT INTO brew.recipe_items (recipe_id, ingredient_id, stage, qty, unit, timing_min)
SELECT r.id, i.id, 'dryhop', <<GRAMS>>, 'g', <<DAYS IN CONTACT>>
FROM brew.recipes r
JOIN brew.ingredients i ON i.kind = 'hop' AND i.name = '<<HOP NAME>>' AND i.supplier = '<<SUPPLIER>>'
WHERE r.name = '<<RECIPE NAME>>' AND r.version = <<RECIPE VERSION>>
  AND NOT EXISTS (
    SELECT 1 FROM brew.recipe_items x
    WHERE x.recipe_id = r.id AND x.ingredient_id = i.id AND x.stage = 'dryhop'
  );

-- 2c. The batch --------------------------------------------------------------
-- og/fg are the MEASURED values, not the targets. brew.f_abv derives ABV from
-- them, and nlq.find_batches returns that — the model never does this arithmetic
-- (§3.3). volume_l is the packaged volume; it is the denominator of the dry hop
-- rate, so an approximation here makes that number wrong.
INSERT INTO brew.batches
  (recipe_id, batch_no, brewed_on, packaged_on, volume_l, og, fg, status, notes)
VALUES (
  (SELECT id FROM brew.recipes WHERE name = '<<RECIPE NAME>>' AND version = <<RECIPE VERSION>>),
  '<<BATCH NO, e.g. IPA-024>>',
  '<<BREWED ON, YYYY-MM-DD>>',
  <<'YYYY-MM-DD' packaged, or NULL>>,
  <<VOLUME L>>,
  <<MEASURED OG>>,
  <<MEASURED FG>>,
  '<<planned|fermenting|conditioning|packaged|archived>>',
  <<'notes' or NULL>>
)
ON CONFLICT (batch_no) DO NOTHING;

-- 2d. Sensory notes ----------------------------------------------------------
-- `descriptors` is the array nlq.find_batches filters on (p_descriptor) — keep
-- them lowercase single adjectives. The free-text fields feed the FTS index,
-- which is the fallback when a descriptor isn't in the array.
--
-- ⚠️ No unique constraint here either — hence the NOT EXISTS guard.
INSERT INTO brew.sensory_notes
  (batch_id, tasted_at, days_since_packaging, aroma, appearance, flavor, mouthfeel, overall, score, descriptors)
SELECT b.id,
       '<<TASTED ON, YYYY-MM-DD>>',
       <<DAYS SINCE PACKAGING or NULL>>,
       <<'aroma' or NULL>>,
       <<'appearance' or NULL>>,
       <<'flavor' or NULL>>,
       <<'mouthfeel' or NULL>>,
       <<'overall' or NULL>>,
       <<SCORE 0-10, e.g. 7.5>>,
       ARRAY[<<'bitter','resinous','dank'>>]::text[]
FROM brew.batches b
WHERE b.batch_no = '<<BATCH NO>>'
  AND NOT EXISTS (
    SELECT 1 FROM brew.sensory_notes s
    WHERE s.batch_id = b.id AND s.tasted_at = '<<TASTED ON, YYYY-MM-DD>>'
  );

-- 2e. Measurements — OPTIONAL in Phase 2 -------------------------------------
-- No Phase 2 tool reads brew.measurements; get_batch_detail (Phase 3) does.
-- Add them if you have the logs, skip them if you don't.
-- INSERT INTO brew.measurements (batch_id, taken_at, kind, value, device, notes)
-- SELECT b.id, '<<YYYY-MM-DD HH:MM+02>>', '<<gravity|temp_c|ph|pressure|do_ppb|volume_l>>',
--        <<VALUE>>, <<'device' or NULL>>, <<'notes' or NULL>>
-- FROM brew.batches b WHERE b.batch_no = '<<BATCH NO>>';

-- =============================================================================
-- END OF BATCH BLOCK — copy 2a–2e again for the next batch
-- =============================================================================


COMMIT;


-- =============================================================================
-- 3. VERIFY — run this after the commit. Re-run it after a second execution of
--    the file: every number must be identical, or a guard above was removed.
-- =============================================================================

\echo '--- what the agent will see through nlq.find_batches ---'
SELECT batch_no, recipe_name, style_code, brewed_on, og, fg, abv,
       dry_hop_rate_g_per_l, descriptors, avg_score
FROM nlq.find_batches();

\echo '--- sanity: ABV plausible, dry hop rate plausible ---'
SELECT batch_no,
       abv                   AS abv_pct,
       dry_hop_rate_g_per_l  AS dh_g_per_l,
       CASE WHEN abv BETWEEN 0 AND 15 THEN 'ok' ELSE 'CHECK OG/FG' END        AS abv_check,
       CASE WHEN dry_hop_rate_g_per_l IS NULL
                 OR dry_hop_rate_g_per_l BETWEEN 0 AND 25 THEN 'ok'
            ELSE 'CHECK volume_l / recipe_items — probably double-inserted' END AS dh_check
FROM nlq.find_batches();

\echo '--- duplicate guard: these must all be 0 ---'
SELECT
  (SELECT count(*) FROM (SELECT recipe_id, ingredient_id, stage FROM brew.recipe_items
                         GROUP BY 1,2,3 HAVING count(*) > 1) d) AS dup_recipe_items,
  (SELECT count(*) FROM (SELECT batch_id, tasted_at FROM brew.sensory_notes
                         GROUP BY 1,2 HAVING count(*) > 1) d)   AS dup_sensory_notes;
