-- Remove the Sterling hop from ref (s3-style-fit, user decision 2026-10-15): "It is from Saaz, and
-- not really available on hopline as well, so I won´t encounter with it."
-- loaders.hop_products.EXCLUDED keeps loaders.hops from loading it again.
-- Deleting the ingredient row cascades to ref.hop, ref.ingredient_tag and ref.ingredient_review
-- (checked 2026-10-15: one row each; no ref.style_rule, ref.style_ingredient, corpus.* or app.*
-- row references it).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/035_drop_sterling.sql
-- Idempotent: safe to re-run.

delete from ref.ingredient
where kind = 'hop' and producer_key = '' and name_key = 'sterling';
