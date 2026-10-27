-- Step 11 validating (docs/work/m6-compute-validate, Task 5): the tolerances of the brief and
-- app.step11_validate, which checks a step 10 recipe against the targets, the numbers the user
-- stated, the formulation rules and the style, and says what to retry. No LLM.
-- Needs db/046_compute.sql (step10 output), db/042_choose_table.sql (choose_excluded),
-- db/034_style_level.sql (style_fit_recipe with totals), db/032_formulation_check.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/047_validate.sql
-- Idempotent: safe to re-run.

-- How far a recipe may be from a target or a stated number: user decision "Brewer bar",
-- 2026-10-25, the same for targets and stated numbers; batch size is exact. SRM was 1; user
-- decision 2026-10-26 "50 g + SRM +- 2" widened it to 2, for targets and stated numbers alike,
-- because one 50 g step of a roast malt moves SRM by more than 1 at 20 L. evals/grade.py
-- RECIPE_TOLERANCES must equal this (tests/test_run.py checks it).
create or replace function app.recipe_tolerances()
returns jsonb
language sql
immutable
as $$
    select '{"og": 0.002, "abv": 0.2, "ibu": 2, "srm": 2, "batch_l": 0}'::jsonb
$$;

-- The attenuation (percent) at which a grist, solved for an OG, ends at an FG: app.fg falls as
-- attenuation rises, so it is bisected over [0, 100] (40 halvings) and clamped to that interval.
-- step11_fix uses it to say what attenuation a failed FG or ABV needs (Task 9c).
create or replace function app.attenuation_for_fg(grist jsonb, og numeric, efficiency_pct numeric,
                                                  volume_l numeric, fg numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    solved jsonb := app.solve_grist(og, grist, efficiency_pct, volume_l);
    lo numeric := 0;
    hi numeric := 100;
    mid numeric;
begin
    if app.fg(solved, efficiency_pct, volume_l, 0) <= fg then
        return 0;
    elsif app.fg(solved, efficiency_pct, volume_l, 100) >= fg then
        return 100;
    end if;
    for i in 1..40 loop
        mid := (lo + hi) / 2;
        if app.fg(solved, efficiency_pct, volume_l, mid) > fg then
            lo := mid;
        else
            hi := mid;
        end if;
    end loop;
    return (lo + hi) / 2;
end;
$$;

comment on function app.attenuation_for_fg(jsonb, numeric, numeric, numeric, numeric) is
    'The attenuation at which app.fg of the grist, solved for the OG, equals the FG (bisection, clamped to 0..100).';

-- What the LLM can change after a step 11 failure (Task 9c): one plain sentence, or null when the
-- failure line already says it or no case applies. failure is one step11_validate failure, step10
-- its input, targets step 4's output and stated the brief's stated numbers. Every number in the
-- sentence comes from the failure, step 10's output, ref.fermentable or app.attenuation_for_fg.
-- The shares and the OG are the rounded recipe's (step10.fermentables, step10.numbers.og); where the
-- colour solver's movers stopped is read from step10.colour. A miss that rounding added
-- (step10.rounding.added) has no fix here: its failure line already says it comes from rounding.
create or replace function app.step11_fix(failure jsonb, step10 jsonb, targets jsonb, stated jsonb)
returns text
language plpgsql
stable
as $$
declare
    l jsonb := app.formulation_limits();
    subj text := failure ->> 'subject';
    txt text := failure ->> 'text';
    cgrist jsonb := step10 -> 'colour' -> 'grist';  -- the solver's grist, before rounding: where its movers stopped
    grist jsonb;                                    -- the rounded grist the recipe has, with the solver's facts
    og numeric := coalesce((step10 -> 'numbers' ->> 'og')::numeric, (step10 -> 'og_used' ->> 'value')::numeric);
    eff numeric := (step10 -> 'batch' ->> 'efficiency_pct')::numeric;
    vol numeric := (step10 -> 'batch' ->> 'volume_l')::numeric;
    att numeric := (step10 -> 'numbers' ->> 'attenuation_pct')::numeric;
    yeast_name text := step10 -> 'yeasts' -> 0 ->> 'name';
    mash numeric := (step10 ->> 'mash_c')::numeric;
    got numeric := (failure ->> 'value')::numeric;
    want numeric;
    n numeric;
    fg numeric;
    rng numrange;
    names text;
    sugars text;
    d jsonb;
    d_pct numeric;
    d_max numeric;
    d_role text;
    cap numeric;
    n_base int;
    base jsonb;
begin
    -- the figures below are the rounded recipe's: its shares and its OG (Task 10b)
    select coalesce(jsonb_agg(c || jsonb_build_object('kg', f -> 'kg', 'pct', f -> 'pct') order by fo), cgrist)
      into grist
      from jsonb_array_elements(step10 -> 'fermentables') with ordinality t(f, fo)
      join jsonb_array_elements(cgrist) c on c ->> 'ingredient_id' = f ->> 'ingredient_id';

    -- colour
    if subj in ('srm', 'stated srm') and got is not null then
        want := case when subj = 'srm' then (targets -> 'targets' -> 'srm' ->> 'value')::numeric
                     else (stated ->> 'srm')::numeric end;
        -- rounding caused the miss (the failure's text already says so): changing the picks is not the fix
        if (step10 -> 'rounding' -> 'added') ? 'numbers srm' then
            return null;
        end if;
        select count(*) into n_base from jsonb_array_elements(grist) g where g ->> 'role' = 'base';
        if got > want then
            -- too dark: the instructions below are for a colour the movers could not lower
            if (step10 -> 'colour' ->> 'reached')::boolean is not false then
                return null;
            end if;
            select string_agg(g ->> 'name' || ' ' || trim_scale(round((g ->> 'pct')::numeric, 2)) || ' %', ', '
                              order by ord) into names
              from jsonb_array_elements(grist) with ordinality t(g, ord)
             where g ->> 'role' = 'crystal' and (g ->> 'pct')::numeric > 0;
            if n_base = 0 then
                return 'add a base malt: no other fermentable can take up the colour change.';
            elsif names is not null then
                return format('lower the crystal share (%s): the colour adjustment never moves a crystal.', names);
            end if;
            -- the darkest non-crystal (highest ebc, then larger share) is the only base malt
            select g into d from jsonb_array_elements(grist) g where g ->> 'role' <> 'crystal'
             order by coalesce((g ->> 'ebc')::numeric, 0) desc, (g ->> 'pct')::numeric desc limit 1;
            if n_base = 1 and d ->> 'role' = 'base' then
                return format('use a lighter base malt than %s (%s EBC).', d ->> 'name',
                              trim_scale(round(coalesce((d ->> 'ebc')::numeric, 0), 1)));
            end if;
            select string_agg(g ->> 'name' || ' ' || trim_scale(round((g ->> 'pct')::numeric, 2)) || ' %', ', '
                              order by ord) into names
              from jsonb_array_elements(grist) with ordinality t(g, ord)
             where g ->> 'role' = 'roast' and (g ->> 'pct')::numeric > 0;
            if names is not null then
                return format('lower the roast share (%s): the colour adjustment could not lower it enough.', names);
            end if;
            return null;
        end if;
        -- too light: the mover (the second pass's when there was one) stopped at a limit
        d := coalesce(step10 -> 'colour' -> 'second' -> 'darkest', step10 -> 'colour' -> 'darkest');
        if d is null or d = 'null'::jsonb then
            return null;
        end if;
        d_pct := coalesce((step10 -> 'colour' -> 'second' ->> 'to_pct')::numeric, (step10 -> 'colour' ->> 'to_pct')::numeric);
        select ft.max_pct, ft.role into d_max, d_role from ref.fermentable ft
         where ft.ingredient_id = (d ->> 'ingredient_id')::bigint;
        if d_role = 'base' then
            return null;  -- nothing darker than the base malt moved: no limit was reached
        elsif d_max is not null and d_pct >= d_max - 0.005 then
            return format('%s is at its %s %% limit: add a second dark malt (role roast or kilned).',
                          d ->> 'name', trim_scale(d_max));
        elsif d_role = 'roast' then
            select (l ->> 'dark_total_pct')::numeric - coalesce(sum((g ->> 'pct')::numeric), 0) into cap
              from jsonb_array_elements(cgrist) g
             where (g ->> 'ingredient_id')::bigint <> (d ->> 'ingredient_id')::bigint
               and (g ->> 'role' = 'roast'
                    or (g ->> 'role' = 'crystal' and (g ->> 'ebc')::numeric > (l ->> 'crystal_dark_ebc')::numeric));
            if d_pct >= cap - 0.005 then
                select string_agg(g ->> 'name' || ' ' || trim_scale(round((g ->> 'pct')::numeric, 2)) || ' %', ', '
                                  order by ord) into names
                  from jsonb_array_elements(cgrist) with ordinality t(g, ord)
                 where g ->> 'role' = 'crystal' and (g ->> 'ebc')::numeric > (l ->> 'crystal_dark_ebc')::numeric
                   and (g ->> 'pct')::numeric > 0;
                if names is not null then
                    return format('rule 3 leaves no room for more roast: lower %s to make room.', names);
                end if;
            end if;
        end if;
        return null;
    end if;

    -- rule 10: the predicted FG outside the range
    if subj = 'rule 10' and starts_with(txt, 'Rule 10: the predicted FG') and att is not null
       and step10 -> 'numbers' ->> 'fg' is not null then
        rng := app.rule10_fg_range(step10 -> 'recipe' ->> 'style_code',
                                   (step10 -> 'recipe' -> 'targets' ->> 'fg')::numeric,
                                   step10 -> 'recipe' -> 'stated');
        if rng is null then
            return null;
        end if;
        got := (step10 -> 'numbers' ->> 'fg')::numeric;
        if got < lower(rng) then
            n := app.attenuation_for_fg(grist, og, eff, vol, lower(rng));
            select string_agg(g ->> 'name' || ' ' || trim_scale(round((g ->> 'pct')::numeric, 2)) || ' %', ', '
                              order by ord) into sugars
              from jsonb_array_elements(grist) with ordinality t(g, ord)
             where g ->> 'role' = 'sugar' and (g ->> 'pct')::numeric > 0;
            return format('pick a less attenuative yeast: %s gives %s %% here (mash %s °C) and this grist needs about %s %% for FG %s%s.',
                          yeast_name, trim_scale(round(att, 1)), trim_scale(round(mash, 2)),
                          trim_scale(round(n, 1)), to_char(lower(rng), 'FM0.0000'),
                          case when sugars is null then '' else ', or lower ' || sugars || ', which ferment out' end);
        elsif got > upper(rng) then
            n := app.attenuation_for_fg(grist, og, eff, vol, upper(rng));
            return format('pick a more attenuative yeast: about %s %%.', trim_scale(round(n, 1)));
        end if;
        return null;
    end if;

    -- the ABV after the OG move
    if subj in ('abv', 'stated abv') then
        if att is null then
            return 'pick a yeast with an attenuation figure.';
        end if;
        want := case when subj = 'abv' then (targets -> 'targets' -> 'abv' ->> 'value')::numeric
                     else (stated ->> 'abv')::numeric end;
        begin
            fg := app.fg_for_abv(og, want);
        exception when others then
            return null;
        end;
        n := app.attenuation_for_fg(grist, og, eff, vol, fg);
        return format('pick a yeast attenuating about %s %% (%s gives %s %%).',
                      trim_scale(round(n, 1)), yeast_name, trim_scale(round(att, 1)));
    end if;

    -- rule 11: the ABV above the alcohol tolerance
    if subj = 'rule 11' and starts_with(txt, 'Rule 11: the planned ABV') and got is not null then
        return format('pick a yeast with an alcohol tolerance of at least %s %%.', trim_scale(round(got, 2)));
    end if;

    -- rules 3 and 4: points to take off the items the failure names
    if subj in ('rule 3', 'rule 4') and got is not null and failure ->> 'limit' is not null then
        names := substring(txt from '\((.*)\); the limit');
        if names is not null then
            return format('take at least %s points off %s.',
                          trim_scale(round(got - (failure ->> 'limit')::numeric, 2)), names);
        end if;
    end if;
    return null;
end;
$$;

comment on function app.step11_fix(jsonb, jsonb, jsonb, jsonb) is
    'What the next try can change after a step 11 failure, one sentence with every number computed here; null when none applies.';

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
-- Each feedback line is the failure's text, then ' To fix: <app.step11_fix>' when that gives a
-- sentence (Task 9c), then the ban suffix.
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
    for f in select * from jsonb_array_elements(app.recipe_rule_failures(check_out)) loop
        failures := failures || jsonb_build_object('kind', 'rule', 'subject', 'rule ' || (f ->> 'rule'),
            'value', f -> 'value', 'limit', f -> 'limit', 'text', f ->> 'text', 'ban', null);
    end loop;

    -- style fit: model deviations with guidance off, picks to ban with guidance on
    for ln in select * from jsonb_array_elements(fit -> 'lines') loop
        continue when coalesce(ln ->> 'level', '') not in ('out_of_style', 'changes_style');
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

    -- a failure that rounding to the weighing steps added says so, so the retry knows (Task 10b)
    if jsonb_array_length(coalesce(step10 -> 'rounding' -> 'added', '[]'::jsonb)) > 0 then
        select jsonb_agg(case when (step10 -> 'rounding' -> 'added') ? (case when fl ->> 'kind' = 'numbers'
                                       then 'numbers ' || replace(fl ->> 'subject', 'stated ', '') else fl ->> 'subject' end)
                         then fl || jsonb_build_object('text', (fl ->> 'text')
                                 || case when fl ->> 'text' ~ '[.]$' then '' else '.' end
                                 || ' It comes from rounding to weighing steps: ' || (step10 -> 'rounding' ->> 'because'))
                         else fl end order by ord)
          into failures from jsonb_array_elements(failures) with ordinality t(fl, ord);
    end if;

    -- one ban per ingredient; one feedback line per failure
    select coalesce(jsonb_agg(distinct b), '[]'::jsonb) into bans from jsonb_array_elements(bans) b;
    select coalesce(jsonb_agg(fl ->> 'text'
                              || coalesce(case when fl ->> 'text' ~ '[.]$' then '' else '.' end
                                          || ' To fix: ' || app.step11_fix(fl, step10, targets, stated), '')
                              || case when fl ->> 'ban' is not null then ' (banned for the next try)' else '' end
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
