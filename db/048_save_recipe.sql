-- Saving a validated recipe (docs/work/m6-compute-validate, Task 6): app.save_recipe writes the
-- app.recipe row, its items and its deviations, and points the run at it, in one transaction
-- (one function, so a failure saves nothing). No LLM.
-- Needs db/045_recipe_deviation_kind.sql (deviation kinds), db/047_validate.sql (step 11 output).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/048_save_recipe.sql
-- Idempotent: safe to re-run.

-- step3 is step 3's output ({deviations [{kind, subject, level, requested_by, because}]}), targets
-- step 4's, step10 and step11 the outputs of app.step10_compute and app.step11_validate. Raises
-- unless step 11 passed (R5) and the run has a brief. Returns the recipe id.
create or replace function app.save_recipe(run_id bigint, step3 jsonb, targets jsonb, step10 jsonb, step11 jsonb)
returns bigint
language plpgsql
as $$
declare
    brief bigint;
    style bigint;
    rid bigint;
    x jsonb;
begin
    if step11 is null or not coalesce((step11 ->> 'passed')::boolean, false) then
        raise exception 'save_recipe: step 11 did not pass, nothing is saved';
    end if;
    select r.brief_id into brief from app.run r where r.id = run_id;
    if brief is null then
        raise exception 'save_recipe: run % has no brief', run_id;
    end if;
    select s.id into style from ref.beer_style s where s.code = targets -> 'style' ->> 'code';
    if style is null then
        raise exception 'save_recipe: no style %', targets -> 'style' ->> 'code';
    end if;

    insert into app.recipe (brief_id, style_id, status, batch_l, efficiency_pct, targets,
                            og, fg, abv, ibu, srm, calc_version)
    values (brief, style, 'draft',
            (step10 -> 'batch' ->> 'volume_l')::numeric, (step10 -> 'batch' ->> 'efficiency_pct')::numeric,
            targets,
            (step10 -> 'numbers' ->> 'og')::numeric, (step10 -> 'numbers' ->> 'fg')::numeric,
            (step10 -> 'numbers' ->> 'abv')::numeric, (step10 -> 'numbers' ->> 'ibu')::numeric,
            (step10 -> 'numbers' ->> 'srm')::numeric, app.calc_version())
    returning id into rid;

    for x in select * from jsonb_array_elements(step10 -> 'fermentables') loop
        insert into app.recipe_item (recipe_id, ingredient_id, raw_name, usage, time_min, pct, amount, unit)
        values (rid, (x ->> 'ingredient_id')::bigint, x ->> 'name', x ->> 'usage', null,
                (x ->> 'pct')::numeric, (x ->> 'kg')::numeric, 'kg');
    end loop;
    for x in select * from jsonb_array_elements(step10 -> 'hops') loop
        insert into app.recipe_item (recipe_id, ingredient_id, raw_name, usage, time_min, pct, amount, unit)
        values (rid, (x ->> 'ingredient_id')::bigint, x ->> 'name', x ->> 'usage',
                (x ->> 'minutes')::numeric, (x ->> 'share_pct')::numeric, (x ->> 'g')::numeric, 'g');
    end loop;
    for x in select * from jsonb_array_elements(step10 -> 'yeasts') loop
        insert into app.recipe_item (recipe_id, ingredient_id, raw_name, usage, time_min, pct, amount, unit)
        values (rid, (x ->> 'ingredient_id')::bigint, x ->> 'name', 'ferment', null, null,
                (x ->> 'amount')::numeric, x ->> 'unit');
    end loop;
    for x in select * from jsonb_array_elements(step10 -> 'extras') loop
        insert into app.recipe_item (recipe_id, ingredient_id, raw_name, usage, time_min, pct, amount, unit)
        values (rid, (x ->> 'ingredient_id')::bigint, x ->> 'name', x ->> 'usage',
                (x ->> 'time_min')::numeric, null, (x ->> 'g')::numeric, 'g');
    end loop;

    for x in select * from jsonb_array_elements(coalesce(step3 -> 'deviations', '[]'::jsonb)) loop
        insert into app.recipe_deviation (recipe_id, kind, subject, level, requested_by, note)
        values (rid, x ->> 'kind', x ->> 'subject', x ->> 'level', 'user', x ->> 'because');
    end loop;
    for x in select * from jsonb_array_elements(coalesce(step11 -> 'model_deviations', '[]'::jsonb)) loop
        insert into app.recipe_deviation (recipe_id, kind, subject, level, requested_by, note)
        values (rid, 'ingredient', x ->> 'subject', x ->> 'level', 'model', x ->> 'note');
    end loop;

    update app.run set recipe_id = rid where id = run_id;
    return rid;
end;
$$;
