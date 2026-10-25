-- Step 11 validating (docs/work/m6-compute-validate, Task 5): the tolerances of the brief and
-- app.step11_validate, which checks a step 10 recipe against the targets, the numbers the user
-- stated, the formulation rules and the style, and says what to retry. No LLM.
-- Needs db/046_compute.sql (step10 output), db/042_choose_table.sql (choose_excluded),
-- db/034_style_level.sql (style_fit_recipe with totals), db/032_formulation_check.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/047_validate.sql
-- Idempotent: safe to re-run.

-- How far a recipe may be from a target or a stated number: user decision "Brewer bar",
-- 2026-10-25, the same for targets and stated numbers; batch size is exact. evals/grade.py
-- RECIPE_TOLERANCES must equal this (tests/test_run.py checks it).
create or replace function app.recipe_tolerances()
returns jsonb
language sql
immutable
as $$
    select '{"og": 0.002, "abv": 0.2, "ibu": 2, "srm": 1, "batch_l": 0}'::jsonb
$$;

-- Step 11. step10 is app.step10_compute's output, brief step 1's output, targets step 4's output,
-- frame step 5's output and picks every step 6-9 pick [{ingredient_id, name, self_picked}]
-- (self_picked: the pipeline chose it, no `wanted` and no `inventory` behind it).
-- Failures are {kind, subject, value, limit, text, ban}:
--   numbers  OG, ABV, IBU, SRM against step 4's targets; the stated og, abv, ibu, srm and
--            batch_l against the computed ones (a stated number that is also the target is
--            reported once); a number that cannot be computed fails.
--   rule     every failed check_recipe rule, one failure per rule failure, except the OG line of
--            rule 9: step 10 moves OG on purpose (inside OG +- 0.002, towards the ABV target) and
--            this function checks the OG against the target itself (user decision 2026-10-25).
--            The ABV line of rule 9 (the ABV target against app.abv of the OG and FG targets)
--            is skipped for the same reason: the moved OG breaks it, and ABV is checked against
--            its target here.
--   pick     with guidance on, a self-picked line out_of_style or changes_style (rated without the
--            recipe totals, so the user's own IBU or the colour before the adjustment ban
--            nothing); an excluded product; an item without an ingredient id. Only self-picks get
--            a ban: the brewer's wanted and inventory picks stay.
-- With guidance off a self-picked out_of_style or changes_style line is a model deviation
-- (saved with the recipe) instead of a failure.
create or replace function app.step11_validate(step10 jsonb, brief jsonb, targets jsonb, frame jsonb, picks jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    tol jsonb := app.recipe_tolerances();
    recipe jsonb := step10 -> 'recipe';
    numbers jsonb := step10 -> 'numbers';
    stated jsonb := coalesce(brief -> 'stated', '{}'::jsonb);
    guidance boolean := coalesce((targets ->> 'guidance')::boolean, true);
    check_out jsonb := app.check_recipe(recipe);
    fit jsonb := app.style_fit_recipe(recipe, null, false);
    excluded jsonb := app.choose_excluded(frame);
    failures jsonb := '[]'::jsonb;
    bans jsonb := '[]'::jsonb;
    target_rows jsonb := '[]'::jsonb;
    stated_rows jsonb := '[]'::jsonb;
    model_dev jsonb := '[]'::jsonb;
    feedback jsonb := '[]'::jsonb;
    failed_keys text[] := '{}';
    k text;
    want numeric;
    got numeric;
    lim numeric;
    met boolean;
    txt text;
    digits int;
    r jsonb;
    f jsonb;
    x jsonb;
    ln jsonb;
    ban_id bigint;
    ban_why text;
    own boolean;
    reason text;
begin
    -- numbers against the targets
    foreach k in array array['og', 'abv', 'ibu', 'srm'] loop
        want := (targets -> 'targets' -> k ->> 'value')::numeric;
        got := (numbers ->> k)::numeric;
        lim := (tol ->> k)::numeric;
        digits := case when k = 'og' then 4 else 2 end;
        met := got is not null and want is not null and abs(got - want) <= lim + 1e-9;
        target_rows := target_rows || jsonb_build_object('key', k, 'target', want, 'value', got,
                                                         'tolerance', lim, 'met', met);
        if not met then
            if got is null then
                txt := format('Step 11: the %s cannot be computed%s.', upper(k),
                              case when numbers ->> 'attenuation_pct' is null and k = 'abv'
                                   then ': the yeast has no attenuation figure' else '' end);
            else
                txt := format('Step 11: the %s is %s and the target is %s (limit +- %s).', upper(k),
                              trim_scale(round(got, digits)), trim_scale(round(want, digits)), trim_scale(lim));
                if k = 'srm' and (step10 -> 'colour' ->> 'reached')::boolean is false then
                    txt := txt || ' The colour adjustment could not reach it: ' || (step10 -> 'colour' ->> 'because');
                end if;
            end if;
            failures := failures || jsonb_build_object('kind', 'numbers', 'subject', k, 'value', got,
                                                       'limit', lim, 'text', txt, 'ban', null);
            failed_keys := failed_keys || k;
        end if;
    end loop;
    target_rows := target_rows || jsonb_build_object('key', 'batch_l',
        'target', (targets -> 'batch_l' ->> 'value')::numeric, 'value', (step10 -> 'batch' ->> 'volume_l')::numeric,
        'tolerance', (tol ->> 'batch_l')::numeric,
        'met', abs((targets -> 'batch_l' ->> 'value')::numeric - (step10 -> 'batch' ->> 'volume_l')::numeric)
                   <= (tol ->> 'batch_l')::numeric);
    if not (target_rows -> 4 ->> 'met')::boolean then
        failures := failures || jsonb_build_object('kind', 'numbers', 'subject', 'batch_l',
            'value', (step10 -> 'batch' ->> 'volume_l')::numeric, 'limit', 0,
            'text', format('Step 11: the batch is %s L and the target is %s L.', step10 -> 'batch' ->> 'volume_l',
                           targets -> 'batch_l' ->> 'value'), 'ban', null);
    end if;

    -- the numbers the user stated
    foreach k in array array['og', 'abv', 'ibu', 'srm', 'batch_l'] loop
        continue when not stated ? k;
        want := (stated ->> k)::numeric;
        got := case when k = 'batch_l' then (step10 -> 'batch' ->> 'volume_l')::numeric
                    else (numbers ->> k)::numeric end;
        lim := (tol ->> k)::numeric;
        digits := case when k = 'og' then 4 else 2 end;
        met := got is not null and abs(got - want) <= lim + 1e-9;
        stated_rows := stated_rows || jsonb_build_object('key', k, 'stated', want, 'value', got,
                                                         'tolerance', lim, 'met', met);
        if not met and not k = any(failed_keys) and k <> 'batch_l' then
            failures := failures || jsonb_build_object('kind', 'numbers', 'subject', 'stated ' || k,
                'value', got, 'limit', lim, 'ban', null,
                'text', case when got is null then format('Step 11: the %s you stated cannot be checked: it cannot be computed.', upper(k))
                    else format('Step 11: the stated %s %s is not met: the recipe gives %s (limit +- %s).', upper(k),
                                trim_scale(round(want, digits)), trim_scale(round(got, digits)), trim_scale(lim)) end);
        elsif not met and k = 'batch_l' then
            failures := failures || jsonb_build_object('kind', 'numbers', 'subject', 'stated batch_l',
                'value', got, 'limit', 0, 'ban', null,
                'text', format('Step 11: the stated batch %s L is not the recipe''s %s L.', trim_scale(want), trim_scale(got)));
        end if;
    end loop;

    -- formulation rules
    for r in select * from jsonb_array_elements(check_out -> 'results') loop
        continue when r ->> 'status' <> 'fail';
        for f in select * from jsonb_array_elements(r -> 'failures') loop
            continue when (r ->> 'rule')::int = 9
                      and (starts_with(f ->> 'text', 'Rule 9: the OG target ')
                           or starts_with(f ->> 'text', 'Rule 9: the ABV target '));
            failures := failures || jsonb_build_object('kind', 'rule', 'subject', 'rule ' || (r ->> 'rule'),
                'value', f -> 'value', 'limit', f -> 'limit', 'text', f ->> 'text', 'ban', null);
        end loop;
    end loop;

    -- style fit: model deviations with guidance off, picks to ban with guidance on
    for ln in select * from jsonb_array_elements(fit -> 'lines') loop
        continue when ln ->> 'level' not in ('out_of_style', 'changes_style');
        select coalesce(bool_or((p ->> 'self_picked')::boolean), false) into own
          from jsonb_array_elements(picks) p
         where (p ->> 'ingredient_id')::bigint = (ln ->> 'ingredient_id')::bigint;
        continue when not own;
        if guidance then
            failures := failures || jsonb_build_object('kind', 'pick', 'subject', ln ->> 'name',
                'value', null, 'limit', null, 'ban', ln -> 'ingredient_id',
                'text', format('Step 11: %s (%s) is %s for the style: %s', ln ->> 'name', ln ->> 'usage',
                               replace(ln ->> 'level', '_', ' '), ln ->> 'because'));
            bans := bans || jsonb_build_object('ingredient_id', ln -> 'ingredient_id', 'name', ln ->> 'name',
                'why', replace(ln ->> 'level', '_', ' ') || ': ' || (ln ->> 'because'));
        else
            model_dev := model_dev || jsonb_build_object('subject', ln ->> 'name', 'level', ln ->> 'level',
                                                         'note', ln ->> 'because');
        end if;
    end loop;

    -- excluded products and items with no ref id
    for x in
        select e from (
            select jsonb_array_elements(recipe -> 'fermentables') e
            union all select jsonb_array_elements(recipe -> 'hops')
            union all select jsonb_array_elements(coalesce(recipe -> 'extras', '[]'::jsonb))
            union all select jsonb_array_elements(step10 -> 'yeasts')) s
    loop
        if x ->> 'ingredient_id' is null then
            failures := failures || jsonb_build_object('kind', 'pick', 'subject', 'unknown item',
                'value', null, 'limit', null, 'ban', null,
                'text', 'Step 11: an item has no ingredient from the reference data.');
            continue;
        end if;
        select e ->> 'why', (e ->> 'name') into ban_why, reason
          from jsonb_array_elements(excluded) e
         where (e ->> 'ingredient_id')::bigint = (x ->> 'ingredient_id')::bigint;
        continue when ban_why is null;
        select coalesce(bool_or((p ->> 'self_picked')::boolean), false) into own
          from jsonb_array_elements(picks) p
         where (p ->> 'ingredient_id')::bigint = (x ->> 'ingredient_id')::bigint;
        failures := failures || jsonb_build_object('kind', 'pick', 'subject', reason, 'value', null, 'limit', null,
            'ban', case when own then x -> 'ingredient_id' else null end,
            'text', format('Step 11: %s is excluded (%s).', reason, ban_why));
        if own then
            bans := bans || jsonb_build_object('ingredient_id', x -> 'ingredient_id', 'name', reason, 'why', ban_why);
        end if;
    end loop;

    -- one ban per ingredient; one feedback line per failure
    select coalesce(jsonb_agg(distinct b), '[]'::jsonb) into bans from jsonb_array_elements(bans) b;
    select coalesce(jsonb_agg(fl ->> 'text' || case when fl ->> 'ban' is not null then ' (banned for the next try)' else '' end
                              order by ord), '[]'::jsonb)
      into feedback from jsonb_array_elements(failures) with ordinality t(fl, ord);

    return jsonb_build_object(
        'passed', jsonb_array_length(failures) = 0, 'failures', failures, 'banned', bans, 'feedback', feedback,
        'check', check_out, 'style_fit', fit, 'targets', target_rows, 'stated', stated_rows,
        'model_deviations', model_dev);
end;
$$;

comment on function app.step11_validate(jsonb, jsonb, jsonb, jsonb, jsonb) is
    'Step 11: checks a step 10 recipe against targets, stated numbers, the formulation rules and the style; says which picks to ban for the next try.';
