-- app.recipe_deviation keeps every kind of step 3 deviation (docs/work/m6-compute-validate, Task 1).
-- Step 3 gives four kinds: ingredient (with a level), number, mismatch and conflict (no level).
-- The table had only ingredient rows (level not null); `kind` is added and `level` may be null
-- for the other three. An ingredient deviation has a level, the others have none.
-- Needs db/015_app.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/045_recipe_deviation_kind.sql
-- Idempotent: safe to re-run. The table had 0 rows when this was written, so no backfill.

alter table app.recipe_deviation add column if not exists kind text;
alter table app.recipe_deviation alter column kind set not null;

alter table app.recipe_deviation drop constraint if exists recipe_deviation_kind_check;
alter table app.recipe_deviation add constraint recipe_deviation_kind_check
    check (kind in ('ingredient', 'number', 'mismatch', 'conflict'));

alter table app.recipe_deviation alter column level drop not null;

alter table app.recipe_deviation drop constraint if exists recipe_deviation_level_kind_check;
alter table app.recipe_deviation add constraint recipe_deviation_level_kind_check
    check ((kind = 'ingredient') = (level is not null));
