-- Saving a validated recipe (docs/work/m6-compute-validate, Task 6): app.save_recipe writes the
-- app.recipe row, its items and its deviations, and points the run at it, in one transaction
-- (one function, so a failure saves nothing). No LLM.
-- Task 8 of docs/work/m7-process adds app.recipe_process and the `process` argument: the process
-- (steps 12-15) is saved in app.recipe.process and the yeast rows get step 14's amounts.
-- Needs db/045_recipe_deviation_kind.sql (deviation kinds), db/047_validate.sql (step 11 output).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/048_save_recipe.sql
-- Idempotent: safe to re-run.

-- The process to save: {water: step 12, mash: step 13's mash, boil: step 13's boil, fermentation:
-- step 14, packaging: step 15}. The mash temperature and the boil are step 10's (A7): raises when
-- step 13 carries others. Checked against the contract process.output by the caller.
create or replace function app.recipe_process(step10 jsonb, step12 jsonb, step13 jsonb, step14 jsonb, step15 jsonb)
returns jsonb
language plpgsql
immutable
as $$
begin
    if (step13 #>> '{mash,mash_c}')::numeric is distinct from (step10 ->> 'mash_c')::numeric then
        raise exception 'recipe_process: mash % is not step 10''s %', step13 #>> '{mash,mash_c}', step10 ->> 'mash_c';
    end if;
    if (step13 #>> '{boil,boil_min}')::numeric is distinct from (step10 #>> '{boil,boil_min}')::numeric
       or step13 #>> '{boil,because}' is distinct from step10 #>> '{boil,because}' then
        raise exception 'recipe_process: boil % (%) is not step 10''s % (%)',
            step13 #>> '{boil,boil_min}', step13 #>> '{boil,because}',
            step10 #>> '{boil,boil_min}', step10 #>> '{boil,because}';
    end if;
    return jsonb_build_object('water', step12, 'mash', step13 -> 'mash', 'boil', step13 -> 'boil',
                              'fermentation', step14, 'packaging', step15);
end;
$$;

-- step3 is step 3's output ({deviations [{kind, subject, level, requested_by, because}]}), targets
-- step 4's, step10 and step11 the outputs of app.step10_compute and app.step11_validate. Raises
-- unless step 11 passed (R5) and the run has a brief. Returns the recipe id.
-- process is app.recipe_process's output, or null (only the stage D tests call it so): with it,
-- app.recipe.process is set and each yeast row's amount and unit are step 14's pitch for that
-- yeast (a yeast missing from the pitch raises); without it, a yeast row is 1 pack as step 10 says.
drop function if exists app.save_recipe(bigint, jsonb, jsonb, jsonb, jsonb);
create or replace function app.save_recipe(run_id bigint, step3 jsonb, targets jsonb, step10 jsonb, step11 jsonb,
                                           process jsonb default null)
returns bigint
language plpgsql
as $$
declare
    brief bigint;
    style bigint;
    rid bigint;
    x jsonb;
    p jsonb;
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
                            og, fg, abv, ibu, srm, calc_version, process)
    values (brief, style, 'draft',
            (step10 -> 'batch' ->> 'volume_l')::numeric, (step10 -> 'batch' ->> 'efficiency_pct')::numeric,
            targets,
            (step10 -> 'numbers' ->> 'og')::numeric, (step10 -> 'numbers' ->> 'fg')::numeric,
            (step10 -> 'numbers' ->> 'abv')::numeric, (step10 -> 'numbers' ->> 'ibu')::numeric,
            (step10 -> 'numbers' ->> 'srm')::numeric, app.calc_version(), process)
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
        p := x;
        if process is not null then
            select e into p from jsonb_array_elements(process -> 'fermentation' -> 'pitch') e
            where e ->> 'ingredient_id' = x ->> 'ingredient_id' limit 1;
            if p is null then
                raise exception 'save_recipe: yeast % is not in the process pitch', x ->> 'name';
            end if;
        end if;
        insert into app.recipe_item (recipe_id, ingredient_id, raw_name, usage, time_min, pct, amount, unit)
        values (rid, (x ->> 'ingredient_id')::bigint, x ->> 'name', 'ferment', null, null,
                (p ->> 'amount')::numeric, p ->> 'unit');
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
