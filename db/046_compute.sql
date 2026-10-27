-- Step 10 computing (docs/work/m6-compute-validate, Tasks 3-4): the colour solver (rule 7),
-- the boil time and the amounts and numbers of a recipe. Task 3 adds app.solve_colour; Task 4
-- adds app.step10_boil, app.step10_abv and app.step10_compute. s1's functions do all the maths,
-- no LLM.
-- Task 9b (second colour pass, rule 3 and 5 caps, mash move) changes solve_colour and step10_compute.
-- Task 10b (rounding to weighing steps) adds app.weighing_steps, app.recipe_rule_failures,
-- app.step10_grist_failures, app.step10_round_grist, app.step10_round_hops, app.step10_set_amounts
-- and rounds the amounts in step10_compute.
-- Needs db/030_maths.sql (grist_mcu, srm, solve_grist), db/032_formulation_check.sql,
-- db/037_step3.sql (ingredient_choices).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/046_compute.sql
-- Idempotent: safe to re-run.

-- Colour adjustment (rule 7). When the SRM of the proposed grist is more than 1 from the target,
-- the darkest fermentable that is not a crystal malt changes its share (the mover), and the base
-- malt with the largest share (the absorber) takes up the difference, so every other share stays
-- as proposed. The mover's upper limit is its max_pct and, for a roast, the room left under
-- rule 3's dark total, for an adjunct or sugar the room left under rule 5's total. When that
-- first pass stops at a limit and SRM is still more than 1 away, one second pass runs on the
-- result with the fermentable that stopped it held fixed (`fixed`): the next-darkest non-crystal
-- moves (the mover hit its limit), or the next-largest base malt takes up the change (the
-- absorber hit its limit). Never more than two passes; a crystal never moves (Task 9b of
-- m6-compute-validate, user decision 2026-10-26 "Mash + colour reach").
-- Grist items {ingredient_id, name, role, pct, extract_pct, mashed, ebc, max_pct}; a null ebc
-- counts as 0. fixed: ingredient ids that neither move nor take up the change. Returns {grist
-- (pct changed, kg from app.solve_grist), adjusted, reached (SRM within 1 of the target), srm,
-- darkest, absorber, from_pct, to_pct (the first pass), second (null, or the second pass's
-- {darkest, absorber, from_pct, to_pct, because}), because}.
--
-- Closed form. With the shares p_i (percent), e_i = extract_i/100 x 384 x eff_i/100 (eff is the
-- efficiency for mashed items, 100 otherwise) and ebc_i, app.solve_grist gives
-- kg_i = p_i x K / sum(p e) with K = (OG - 1) x 1000 x volume, so
-- MCU = c x N / D, c = (OG - 1) x 1000 x 3.785411784 / (1.97 x 0.45359237),
-- N = sum(p ebc), D = sum(p e): the volume cancels, and both N and D are linear in the mover's
-- share x, because the absorber's share is S - x (S = their shares together) and nothing else
-- moves. Setting c N(x) = m D(x), with m the MCU of the target SRM (app.srm inverted), gives
-- x = x0 + (m D0 - c N0) / (c dN - m dD), dN and dD the change of N and D per point moved from
-- the absorber to the mover. x is then clamped so that the mover stays in (0, its upper limit]
-- and the absorber in (0, its max_pct]; if SRM is still more than 1 away, reached is false.
drop function if exists app.solve_colour(numeric, jsonb, numeric, numeric, numeric);
create or replace function app.solve_colour(target_srm numeric, grist jsonb, target_og numeric,
                                            efficiency_pct numeric, volume_l numeric,
                                            fixed bigint[] default '{}')
returns jsonb
language plpgsql
immutable
as $$
declare
    -- the colour solver aims within 1 SRM, tighter than step 11's +- 2 (app.recipe_tolerances, widened
    -- 2026-10-26 for the rounding), so the rounding to 50 g steps has the rest of the 2 to use
    tolerance constant numeric := 1;
    least constant numeric := 0.01;   -- the smallest share a fermentable may be left with, in percent
    l jsonb := app.formulation_limits();
    items jsonb;
    solved jsonb;
    srm_before numeric;
    srm_after numeric;
    d jsonb;
    a jsonb;
    d_idx int;
    a_idx int;
    x0 numeric;
    s numeric;
    x numeric;
    x_raw numeric;
    lo numeric;
    hi numeric;
    cap numeric;
    d_hi numeric;
    a_lo numeric;
    stopped text;       -- null, 'mover' or 'absorber': who the clamp stopped
    c numeric;
    m numeric;
    n0 numeric := 0;
    d0 numeric := 0;
    dn numeric;
    dd numeric;
    denom numeric;
    e_d numeric;
    e_a numeric;
    why text;
    base_because text;
    reached boolean;
    result jsonb;
    second jsonb;
begin
    if jsonb_typeof(grist) is distinct from 'array' or jsonb_array_length(grist) = 0 then
        raise exception 'solve_colour: grist must be a non-empty JSON array, got %', grist;
    end if;
    if target_srm is null or target_srm <= 0 then
        raise exception 'solve_colour: target SRM must be above 0, got %', target_srm;
    end if;

    -- null ebc counts as 0
    select jsonb_agg(g || jsonb_build_object('ebc', coalesce((g->>'ebc')::numeric, 0)) order by ord)
      into items from jsonb_array_elements(grist) with ordinality t(g, ord);
    solved := app.solve_grist(target_og, items, efficiency_pct, volume_l);
    srm_before := app.srm(app.grist_mcu(solved, volume_l));

    -- the darkest non-crystal that is not fixed: highest ebc, then larger share, then lower id
    select (ord - 1)::int into d_idx
      from jsonb_array_elements(items) with ordinality t(g, ord)
     where g->>'role' <> 'crystal' and not (g->>'ingredient_id')::bigint = any(fixed)
     order by (g->>'ebc')::numeric desc, (g->>'pct')::numeric desc, (g->>'ingredient_id')::bigint
     limit 1;
    if d_idx is not null then
        d := items -> d_idx;
        -- the absorber: the base malt with the largest share other than the mover, not fixed
        select (ord - 1)::int into a_idx
          from jsonb_array_elements(items) with ordinality t(g, ord)
         where g->>'role' = 'base' and (ord - 1)::int <> d_idx
           and not (g->>'ingredient_id')::bigint = any(fixed)
         order by (g->>'pct')::numeric desc, (g->>'ingredient_id')::bigint
         limit 1;
        if a_idx is not null then
            a := items -> a_idx;
        end if;
    end if;

    if abs(srm_before - target_srm) <= tolerance then
        why := format('SRM %s is within %s of the target %s, so the shares stay as proposed',
                      round(srm_before, 1), tolerance, target_srm);
    elsif d is null and cardinality(fixed) > 0 then
        why := 'no other fermentable that is not a crystal malt can take the colour change';
    elsif d is null then
        why := 'every fermentable is a crystal malt, so no share can take the colour change';
    elsif a is null then
        why := format('%s is the darkest fermentable and no other base malt can take up the change',
                      d->>'name');
    elsif (d->>'ebc')::numeric <= (a->>'ebc')::numeric then
        why := format('%s is not darker than %s, so moving shares between them cannot change the colour as needed',
                      d->>'name', a->>'name');
    end if;

    if why is not null then
        return jsonb_build_object(
            'grist', solved, 'adjusted', false,
            'reached', abs(srm_before - target_srm) <= tolerance, 'srm', srm_before,
            'darkest', case when d is null then null
                       else jsonb_build_object('ingredient_id', d->'ingredient_id', 'name', d->'name') end,
            'absorber', case when a is null then null
                        else jsonb_build_object('ingredient_id', a->'ingredient_id', 'name', a->'name') end,
            'from_pct', d->'pct', 'to_pct', d->'pct', 'second', null, 'because', why);
    end if;

    x0 := (d->>'pct')::numeric;
    s := x0 + (a->>'pct')::numeric;
    c := (target_og - 1) * 1000 * 3.785411784 / (1.97 * 0.45359237);
    m := power(target_srm / 1.49, 1 / 0.69);
    e_d := (d->>'extract_pct')::numeric / 100 * 384
           * case when (d->>'mashed')::boolean then efficiency_pct else 100 end / 100;
    e_a := (a->>'extract_pct')::numeric / 100 * 384
           * case when (a->>'mashed')::boolean then efficiency_pct else 100 end / 100;
    select sum((g->>'pct')::numeric * (g->>'ebc')::numeric),
           sum((g->>'pct')::numeric * (g->>'extract_pct')::numeric / 100 * 384
               * case when (g->>'mashed')::boolean then efficiency_pct else 100 end / 100)
      into n0, d0 from jsonb_array_elements(items) g;
    dn := (d->>'ebc')::numeric - (a->>'ebc')::numeric;
    dd := e_d - e_a;
    denom := c * dn - m * dd;
    if denom = 0 then
        x_raw := x0;
    else
        x_raw := x0 + (m * d0 - c * n0) / denom;
    end if;

    -- the mover's upper limit: its max_pct, and the room left under rule 3 (a roast) or rule 5
    -- (an adjunct or sugar) next to the other shares counted there
    d_hi := coalesce((d->>'max_pct')::numeric, 100);
    if d->>'role' = 'roast' then
        select (l->>'dark_total_pct')::numeric - coalesce(sum((g->>'pct')::numeric), 0) into cap
          from jsonb_array_elements(items) with ordinality t(g, ord)
         where (ord - 1)::int <> d_idx
           and (g->>'role' = 'roast'
                or (g->>'role' = 'crystal' and (g->>'ebc')::numeric > (l->>'crystal_dark_ebc')::numeric));
        d_hi := least(d_hi, greatest(cap, x0));  -- a grist already over the total is not made to shrink
    elsif d->>'role' in ('adjunct', 'sugar') then
        select (l->>'adjunct_sugar_pct')::numeric - coalesce(sum((g->>'pct')::numeric), 0) into cap
          from jsonb_array_elements(items) with ordinality t(g, ord)
         where (ord - 1)::int <> d_idx and g->>'role' in ('adjunct', 'sugar');
        d_hi := least(d_hi, greatest(cap, x0));
    end if;
    a_lo := s - coalesce((a->>'max_pct')::numeric, 100);
    lo := greatest(least, a_lo);
    hi := least(s - least, d_hi);
    if lo > hi then
        x := x0;  -- no room to move inside both limits
    else
        x := least(greatest(x_raw, lo), hi);
        if x_raw < lo then
            stopped := case when least >= a_lo then 'mover' else 'absorber' end;
        elsif x_raw > hi then
            stopped := case when d_hi <= s - least then 'mover' else 'absorber' end;
        end if;
    end if;

    items := jsonb_set(items, array[d_idx::text, 'pct'], to_jsonb(x));
    items := jsonb_set(items, array[a_idx::text, 'pct'], to_jsonb(s - x));
    solved := app.solve_grist(target_og, items, efficiency_pct, volume_l);
    srm_after := app.srm(app.grist_mcu(solved, volume_l));
    reached := abs(srm_after - target_srm) <= tolerance;
    base_because := format('%s %s %% to %s %%, %s %s %% to %s %%: SRM %s to %s (target %s)',
            d->>'name', round(x0, 2), round(x, 2), a->>'name',
            round((a->>'pct')::numeric, 2), round(s - x, 2),
            round(srm_before, 1), round(srm_after, 1), target_srm);

    result := jsonb_build_object(
        'grist', solved, 'adjusted', x <> x0, 'reached', reached, 'srm', srm_after,
        'darkest', jsonb_build_object('ingredient_id', d->'ingredient_id', 'name', d->'name'),
        'absorber', jsonb_build_object('ingredient_id', a->'ingredient_id', 'name', a->'name'),
        'from_pct', x0, 'to_pct', x, 'second', null,
        'because', base_because || case when reached then ''
                 else ', still more than ' || tolerance || ' away because of the share limits' end);

    -- the second pass: the fermentable that stopped the move is held fixed
    if not reached and stopped is not null and cardinality(fixed) = 0 then
        second := app.solve_colour(target_srm, items, target_og, efficiency_pct, volume_l,
            array[case stopped when 'mover' then (d->>'ingredient_id')::bigint
                               else (a->>'ingredient_id')::bigint end]);
        if (second->>'adjusted')::boolean then
            result := result || jsonb_build_object(
                'grist', second->'grist', 'adjusted', true, 'reached', second->'reached', 'srm', second->'srm',
                'second', jsonb_build_object('darkest', second->'darkest', 'absorber', second->'absorber',
                                             'from_pct', second->'from_pct', 'to_pct', second->'to_pct',
                                             'because', second->>'because'),
                'because', base_because || '; then ' || (second->>'because'));
        end if;
    end if;
    return result;
end;
$$;

comment on function app.solve_colour(numeric, jsonb, numeric, numeric, numeric, bigint[]) is
    'Rule 7 colour adjustment: the darkest non-crystal fermentable changes its share and the largest base malt takes up the difference (closed form, see the file header); at most one second pass when a limit stops the first.';

-- The boil time: the largest of the floor (rule 13's min_boil_min, 60), the largest min_boil_min
-- of the grist and the longest boil addition of the hops. hops is step 8's hops array (usage,
-- minutes, name). Returns {boil_min, because}; the because names what decided it.
create or replace function app.step10_boil(grist_ids bigint[], hops jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    floor_min numeric := (app.formulation_limits()->>'min_boil_min')::numeric;
    grist_min numeric;
    grist_name text;
    hop_min numeric;
    hop_name text;
    boil numeric;
    why text;
begin
    select ft.min_boil_min, i.name into grist_min, grist_name
      from ref.fermentable ft join ref.ingredient i on i.id = ft.ingredient_id
     where ft.ingredient_id = any(grist_ids) and ft.min_boil_min is not null
     order by ft.min_boil_min desc, i.name limit 1;
    select (h->>'minutes')::numeric, h->>'name' into hop_min, hop_name
      from jsonb_array_elements(hops) h where h->>'usage' = 'boil'
     order by (h->>'minutes')::numeric desc, (h->>'share_pct')::numeric desc, (h->>'ingredient_id')::bigint
     limit 1;
    boil := greatest(floor_min, coalesce(grist_min, 0), coalesce(hop_min, 0));
    why := case
        when hop_min is not null and hop_min = boil and hop_min > greatest(floor_min, coalesce(grist_min, 0))
            then format('%s min: the longest boil addition (%s) is %s min, longer than the %s min the grist needs',
                        trim_scale(boil), hop_name, trim_scale(hop_min),
                        trim_scale(greatest(floor_min, coalesce(grist_min, 0))))
        when grist_min is not null and grist_min = boil and grist_min > floor_min
            then format('%s min: %s needs at least %s min (rule 13)', trim_scale(boil), grist_name, trim_scale(grist_min))
        else format('%s min: the minimum boil time (rule 13)', trim_scale(boil)) end;
    return jsonb_build_object('boil_min', boil, 'because', why);
end;
$$;

-- ABV of a grist at an OG: the shares are solved for that OG, then FG at the attenuation and
-- app.abv. Step 10 bisects the OG move on it.
create or replace function app.step10_abv(og numeric, grist jsonb, efficiency_pct numeric,
                                          volume_l numeric, attenuation_pct numeric)
returns numeric
language sql
immutable
as $$
    select app.abv(og, app.fg(s, efficiency_pct, volume_l, attenuation_pct))
      from (select app.solve_grist(og, grist, efficiency_pct, volume_l) as s) q
$$;

-- The OG move of step 10: when the ABV at the target OG misses the ABV target by more than 0.2,
-- the OG moves inside target +- 0.002 to the ABV target (bisection; ABV rises with OG at fixed
-- shares). Returns {value, because}. A yeast with no attenuation figure (attenuation null) gives
-- no ABV and no move. Step 10 calls it again when the mash move has changed the attenuation.
create or replace function app.step10_og_move(target_og numeric, target_abv numeric, grist jsonb,
                                              efficiency_pct numeric, volume_l numeric,
                                              attenuation_pct numeric, yeast_name text)
returns jsonb
language plpgsql
immutable
as $$
declare
    og_move constant numeric := 0.002;   -- OG tolerance (user decision 2026-10-25, "Brewer bar")
    abv_tol constant numeric := 0.2;     -- ABV tolerance, the same decision
    og_final numeric;
    og_lo numeric; og_hi numeric; og_mid numeric;
    abv_at_target numeric;
begin
    if attenuation_pct is null then
        return jsonb_build_object('value', target_og, 'because',
            format('%s has no attenuation figure, so no ABV can be computed and the OG stays', yeast_name));
    end if;
    abv_at_target := app.step10_abv(target_og, grist, efficiency_pct, volume_l, attenuation_pct);
    if abs(abv_at_target - target_abv) <= abv_tol then
        return jsonb_build_object('value', target_og, 'because',
            format('ABV %s at OG %s is within %s of the target %s, so the OG stays',
                   round(abv_at_target, 2), trim_scale(target_og), abv_tol, trim_scale(target_abv)));
    end if;
    og_lo := target_og - og_move;
    og_hi := target_og + og_move;
    if target_abv <= app.step10_abv(og_lo, grist, efficiency_pct, volume_l, attenuation_pct) then
        og_final := og_lo;
    elsif target_abv >= app.step10_abv(og_hi, grist, efficiency_pct, volume_l, attenuation_pct) then
        og_final := og_hi;
    else
        for i in 1..40 loop
            og_mid := (og_lo + og_hi) / 2;
            if app.step10_abv(og_mid, grist, efficiency_pct, volume_l, attenuation_pct) < target_abv then
                og_lo := og_mid;
            else
                og_hi := og_mid;
            end if;
        end loop;
        og_final := (og_lo + og_hi) / 2;
    end if;
    return jsonb_build_object('value', og_final, 'because',
        format('ABV %s at OG %s misses the target %s by more than %s; OG moved to %s (at most %s) to give ABV %s',
               round(abv_at_target, 2), trim_scale(target_og), trim_scale(target_abv), abv_tol,
               round(og_final, 4), og_move,
               round(app.step10_abv(og_final, grist, efficiency_pct, volume_l, attenuation_pct), 2)));
end;
$$;

-- The weighing steps (Task 10b of m6-compute-validate; user decisions 2026-10-26: "malts, I want 50g
-- rounding", "Malts + flaked grains (Rec.)", "1 g (Rec.)", and "50 g + SRM +- 2"): every malt and
-- flaked grain, roast malts included, 50 g; a fermentable with role sugar (sugars, syrups, honey,
-- lactose) 1 g; hops and extras 1 g. The floor is one step, never 0.
create or replace function app.weighing_steps()
returns jsonb
language sql
immutable
as $$
    select '{"malt_kg": 0.05, "sugar_kg": 0.001, "hop_g": 1, "extra_g": 1}'::jsonb
$$;

comment on function app.weighing_steps() is
    'The step each amount is rounded to by step 10: malts and flaked grains 50 g, sugars 1 g, hops and extras 1 g; the floor is one step.';

-- The failures of an app.check_recipe output as [{rule, text, value, limit}], without rule 9's OG
-- and ABV target lines: step 10 moves the OG on purpose and step 11 checks the OG and ABV against
-- their targets at +- 0.002 and +- 0.2 by the numbers check (Task 5).
create or replace function app.recipe_rule_failures(check_out jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    r jsonb;
    f jsonb;
    found jsonb := '[]'::jsonb;
begin
    for r in select * from jsonb_array_elements(check_out -> 'results') loop
        continue when r ->> 'status' <> 'fail';
        for f in select * from jsonb_array_elements(r -> 'failures') loop
            continue when (r ->> 'rule')::int = 9
                      and (starts_with(f ->> 'text', 'Rule 9: the OG target ')
                           or starts_with(f ->> 'text', 'Rule 9: the ABV target '));
            found := found || jsonb_build_object('rule', (r ->> 'rule')::int, 'text', f ->> 'text',
                                                'value', f -> 'value', 'limit', f -> 'limit');
        end loop;
    end loop;
    return found;
end;
$$;

comment on function app.recipe_rule_failures(jsonb) is
    'The rule failures of an app.check_recipe output as [{rule, text, value, limit}], without rule 9''s OG and ABV target lines.';

-- A recipe object (the formulation_check.input step 11 checks) with new amounts: targets.og, the
-- fermentables'' pct (in the order of the grist) and the hops'' g (in the order of the hops).
create or replace function app.step10_set_amounts(recipe jsonb, og numeric, grist jsonb, hops jsonb)
returns jsonb
language sql
immutable
as $$
    select jsonb_set(jsonb_set(jsonb_set(recipe, '{targets,og}', to_jsonb(og)),
        '{fermentables}', (select jsonb_agg(f || jsonb_build_object('pct', g -> 'pct') order by ord)
                             from jsonb_array_elements(recipe -> 'fermentables') with ordinality t(f, ord)
                             join jsonb_array_elements(grist) with ordinality u(g, ord2) on ord = ord2)),
        '{hops}', coalesce((select jsonb_agg(h || jsonb_build_object('g', x -> 'g') order by ord)
                              from jsonb_array_elements(recipe -> 'hops') with ordinality t(h, ord)
                              join jsonb_array_elements(hops) with ordinality u(x, ord2) on ord = ord2), '[]'::jsonb))
$$;

-- The failures of one grist, as {key: text}: OG, ABV and SRM outside app.recipe_tolerances() of
-- step 4's targets or of the stated numbers (key "numbers og" ...), and the failed rules of
-- app.check_recipe on the recipe with this grist (key "rule 4" ...). grist items {kg, ...} as
-- step10_round_grist takes them; pct and targets.og follow the kg. Used for the exact grist and for
-- every rounded one, so the two are judged the same way.
create or replace function app.step10_grist_failures(grist jsonb, recipe jsonb, targets jsonb, stated jsonb,
                                                     efficiency_pct numeric, volume_l numeric,
                                                     attenuation_pct numeric)
returns jsonb
language plpgsql
stable
as $$
declare
    tol jsonb := app.recipe_tolerances();
    total numeric;
    shaped jsonb;
    og numeric; fg numeric; abv numeric; srm numeric;
    found jsonb := '{}'::jsonb;
    k text;
    got numeric; want numeric; wanted_stated numeric;
    f jsonb;
begin
    select sum((g ->> 'kg')::numeric) into total from jsonb_array_elements(grist) g;
    select jsonb_agg(g || jsonb_build_object('pct', (g ->> 'kg')::numeric / total * 100) order by ord)
      into shaped from jsonb_array_elements(grist) with ordinality t(g, ord);
    og := app.og(shaped, efficiency_pct, volume_l);
    if attenuation_pct is not null then
        fg := app.fg(shaped, efficiency_pct, volume_l, attenuation_pct);
        abv := app.abv(og, fg);
    end if;
    srm := app.srm(app.grist_mcu(shaped, volume_l));
    foreach k in array array['og', 'abv', 'srm'] loop
        got := case k when 'og' then og when 'abv' then abv else srm end;
        want := (targets ->> k)::numeric;
        wanted_stated := (stated ->> k)::numeric;
        if got is null
           or (want is not null and abs(got - want) > (tol ->> k)::numeric + 1e-9)
           or (wanted_stated is not null and abs(got - wanted_stated) > (tol ->> k)::numeric + 1e-9) then
            found := found || jsonb_build_object('numbers ' || k,
                case when got is null then upper(k) || ' cannot be computed'
                     else format('%s %s against %s (limit +- %s)', upper(k),
                                 trim_scale(round(got, case when k = 'og' then 4 else 2 end)),
                                 trim_scale(round(coalesce(wanted_stated, want), case when k = 'og' then 4 else 2 end)),
                                 trim_scale((tol ->> k)::numeric)) end);
        end if;
    end loop;
    for f in select * from jsonb_array_elements(
                 app.recipe_rule_failures(app.check_recipe(app.step10_set_amounts(recipe, og, shaped, recipe -> 'hops')))) loop
        if not found ? ('rule ' || (f ->> 'rule')) then
            found := found || jsonb_build_object('rule ' || (f ->> 'rule'), f ->> 'text');
        end if;
    end loop;
    return found;
end;
$$;

-- Round a solved grist to the weighing steps (Task 10b). grist: step 10's solved grist (kg, role,
-- extract_pct, mashed, fermentability, ebc, ...); recipe: the formulation_check.input object built
-- from the exact amounts; targets: {og, abv, srm} of step 4 as numbers; stated: the numbers the user
-- stated. Each fermentable goes down or up to its step (at least one step; one candidate when kg is
-- on a step): at most 2^n grists, ordered by the sum of |rounded - exact| kg (ties: the order the
-- combinations are listed in, the first fermentable changing fastest). The first whose failures
-- (app.step10_grist_failures) are all among the exact grist's wins. None: the nearest step for every
-- fermentable. Returns {grist (kg rounded, pct recomputed), reached, added (keys the chosen grist
-- adds, empty when reached), off_nearest (names not at their nearest step), because}.
create or replace function app.step10_round_grist(grist jsonb, recipe jsonb, targets jsonb, stated jsonb,
                                                  efficiency_pct numeric, volume_l numeric,
                                                  attenuation_pct numeric)
returns jsonb
language plpgsql
stable
as $$
declare
    steps jsonb := app.weighing_steps();
    n int := jsonb_array_length(grist);
    exact jsonb;
    nearest jsonb;
    chosen jsonb := null;
    combo record;
    cand jsonb;
    fails jsonb;
    nearest_fails jsonb;
    added text[];
    off text[];
    reached boolean;
    why text;
    total numeric;
begin
    exact := app.step10_grist_failures(grist, recipe, targets, stated, efficiency_pct, volume_l, attenuation_pct);
    -- the nearest step for every fermentable, at least one step
    select jsonb_agg(g || jsonb_build_object('kg', greatest(round((g ->> 'kg')::numeric / st) * st, st)) order by ord)
      into nearest
      from jsonb_array_elements(grist) with ordinality t(g, ord),
           lateral (select (case when g ->> 'role' = 'sugar' then steps ->> 'sugar_kg'
                                 else steps ->> 'malt_kg' end)::numeric st) s;
    -- every combination of down and up: digit 0 = down, 1 = up; the first fermentable is the fastest digit
    for combo in
        with recursive items as (
            select ord, (g ->> 'kg')::numeric kg,
                   (case when g ->> 'role' = 'sugar' then steps ->> 'sugar_kg' else steps ->> 'malt_kg' end)::numeric st
              from jsonb_array_elements(grist) with ordinality t(g, ord)),
        cands as (
            select ord, 0 digit, greatest(floor(kg / st) * st, st) kg_r, kg from items
            union all
            select ord, 1, greatest(ceil(kg / st) * st, st), kg from items
             where greatest(ceil(kg / st) * st, st) <> greatest(floor(kg / st) * st, st)),
        walk(ord, kgs, idx, dist) as (
            select c.ord, array[c.kg_r], c.digit::bigint, abs(c.kg_r - c.kg) from cands c where c.ord = 1
            union all
            select c.ord, w.kgs || c.kg_r, w.idx + c.digit::bigint * (1::bigint << (c.ord - 1)::int),
                   w.dist + abs(c.kg_r - c.kg)
              from walk w join cands c on c.ord = w.ord + 1)
        select kgs, dist, idx from walk where ord = n order by dist, idx
    loop
        select jsonb_agg(g || jsonb_build_object('kg', combo.kgs[ord::int]) order by ord)
          into cand from jsonb_array_elements(grist) with ordinality t(g, ord);
        fails := app.step10_grist_failures(cand, recipe, targets, stated, efficiency_pct, volume_l, attenuation_pct);
        if not exists (select 1 from jsonb_object_keys(fails) k where not exact ? k) then
            chosen := cand;
            exit;
        end if;
    end loop;
    reached := chosen is not null;
    if not reached then
        chosen := nearest;
        nearest_fails := app.step10_grist_failures(nearest, recipe, targets, stated, efficiency_pct, volume_l, attenuation_pct);
        select array_agg(k order by k) into added from jsonb_each_text(nearest_fails) e(k, v) where not exact ? k;
        select string_agg(case when starts_with(k, 'rule') then k else k || ' (' || v || ')' end, '; ' order by k) into why
          from jsonb_each_text(nearest_fails) e(k, v) where not exact ? k;
    end if;
    select array_agg(g ->> 'name' order by ord) into off
      from jsonb_array_elements(chosen) with ordinality a(g, ord)
      join jsonb_array_elements(nearest) with ordinality b(h, ord2) on ord = ord2
     where (g ->> 'kg')::numeric <> (h ->> 'kg')::numeric;
    select sum((g ->> 'kg')::numeric) into total from jsonb_array_elements(chosen) g;
    select jsonb_agg(g || jsonb_build_object('pct', (g ->> 'kg')::numeric / total * 100) order by ord)
      into chosen from jsonb_array_elements(chosen) with ordinality t(g, ord);
    return jsonb_build_object(
        'grist', chosen, 'reached', reached,
        'added', to_jsonb(coalesce(added, '{}'::text[])),
        'off_nearest', to_jsonb(coalesce(off, '{}'::text[])),
        'because', format('Malts and flaked grains are weighed in %s g steps, sugars in %s g steps', 
                          trim_scale((steps ->> 'malt_kg')::numeric * 1000), trim_scale((steps ->> 'sugar_kg')::numeric * 1000))
            || case when reached and cardinality(coalesce(off, '{}'::text[])) > 0
                    then '; ' || array_to_string(off, ', ') || ' is rounded away from the nearest step to keep the numbers and rules the exact amounts met'
                    when reached then ''
                    else ', and no grist on those steps avoids what the exact amounts did not have: ' || why end
            || '.');
end;
$$;

comment on function app.step10_round_grist(jsonb, jsonb, jsonb, jsonb, numeric, numeric, numeric) is
    'Rounds a solved grist to the weighing steps, down or up per fermentable, taking the closest grist that adds no failure the exact amounts did not have.';

-- Round solved hops to the nearest gram, at least 1 g (Task 10b). When that alone moves IBU outside
-- the tolerance of the target or a stated IBU and the exact grams did not, the bittering addition (the
-- longest boil addition) takes the other of its floor and ceiling. share_pct is recomputed from the
-- rounded grams. Returns {hops, ibu, because}.
create or replace function app.step10_round_hops(hops jsonb, target_ibu numeric, stated jsonb,
                                                 boil_sg numeric, volume_l numeric)
returns jsonb
language plpgsql
immutable
as $$
declare
    tol numeric := (app.recipe_tolerances() ->> 'ibu')::numeric;
    stated_ibu numeric := (stated ->> 'ibu')::numeric;
    exact_ibu numeric := app.ibu(hops, boil_sg, volume_l);
    rounded jsonb;
    ibu numeric;
    bitter bigint;
    g numeric;
    other numeric;
    because text := 'Hops are weighed to the gram, at least 1 g';
    miss boolean;
begin
    select coalesce(jsonb_agg(h || jsonb_build_object('g', greatest(round((h ->> 'g')::numeric), 1)) order by ord), '[]'::jsonb)
      into rounded from jsonb_array_elements(hops) with ordinality t(h, ord);
    ibu := app.ibu(rounded, boil_sg, volume_l);
    miss := abs(ibu - target_ibu) > tol + 1e-9 or (stated_ibu is not null and abs(ibu - stated_ibu) > tol + 1e-9);
    if miss
       and abs(exact_ibu - target_ibu) <= tol + 1e-9
       and (stated_ibu is null or abs(exact_ibu - stated_ibu) <= tol + 1e-9) then
        select ord into bitter from jsonb_array_elements(rounded) with ordinality t(h, ord)
         where h ->> 'usage' = 'boil'
         order by (h ->> 'minutes')::numeric desc, (h ->> 'share_pct')::numeric desc, (h ->> 'ingredient_id')::bigint
         limit 1;
        if bitter is not null then
            select (h ->> 'g')::numeric into g from jsonb_array_elements(hops) with ordinality t(h, ord) where ord = bitter;
            other := case when round(g) >= g then greatest(floor(g), 1) else ceil(g) end;
            select jsonb_agg(case when ord = bitter then h || jsonb_build_object('g', other) else h end order by ord)
              into rounded from jsonb_array_elements(rounded) with ordinality t(h, ord);
            ibu := app.ibu(rounded, boil_sg, volume_l);
            because := because || format('; the bittering hop went to %s g, the other side of its gram, because the nearest gram moved IBU out of the limit', other);
        end if;
    end if;
    select jsonb_agg(h || jsonb_build_object('share_pct', (h ->> 'g')::numeric / nullif(total, 0) * 100) order by ord)
      into rounded
      from jsonb_array_elements(rounded) with ordinality t(h, ord),
           lateral (select sum((x ->> 'g')::numeric) total from jsonb_array_elements(rounded) x) s;
    return jsonb_build_object('hops', coalesce(rounded, '[]'::jsonb), 'ibu', ibu, 'because', because || '.');
end;
$$;

comment on function app.step10_round_hops(jsonb, numeric, jsonb, numeric, numeric) is
    'Rounds solved hops to the gram (at least 1 g); the bittering addition takes the other side of its gram when the rounding alone pushes IBU out of tolerance.';

-- Step 10: amounts and numbers of the recipe from steps 6-9, step 4's targets and step 0's
-- profile. No LLM; s1's functions only (docs/work/m6-compute-validate/plan.md Task 4). In order:
--   1. batch, efficiency, boil-off and losses; every target must be present
--   2. boil time (app.step10_boil); the longest boil addition is set to it, so it is the
--      bittering addition of rule 8
--   3. colour adjustment (app.solve_colour) at the target OG
--   4. OG move: when the ABV at the target OG misses the ABV target by more than 0.2, the OG moves
--      inside target +- 0.002 to the ABV target (bisection; ABV rises with OG at fixed shares)
--   4b. mash move: when the FG predicted at the OG used is below rule 10's range (app.rule10_fg_range)
--      and the mash is not a brewer's hint, the mash is raised inside (68.3, 69] C towards step 4's FG
--      target (bisection; 69 C when even that leaves FG below it); a moved mash gives a new
--      attenuation, so the OG move (app.step10_og_move) is made again
--   5. grist kg (app.solve_grist), hop grams (app.solve_hops at the boil gravity), misc grams
--      (dose g/L x batch, to the gram), one pack for each yeast
--   6. rounding to the weighing steps (Task 10b): the grist by app.step10_round_grist, then the hops
--      solved again at the rounded OG's boil gravity and rounded by app.step10_round_hops
--   7. OG, FG at the mash-adjusted attenuation, ABV, IBU, SRM, from the rounded amounts. A yeast with no attenuation figure
--      gives null FG and ABV (and no OG move); step 11 fails that. A fermentable with no colour counts
--      as 0 EBC and is named in numbers.srm_lower_bound (as app.style_fit_recipe does).
-- recipe is the formulation_check.input object step 11 checks; its targets.og is the OG used, so
-- app.check_recipe recomputes exactly these numbers.
create or replace function app.step10_compute(profile jsonb, targets jsonb, step6 jsonb, step7 jsonb,
                                              step8 jsonb, step9 jsonb, brief jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    volume numeric := (targets->'batch_l'->>'value')::numeric;
    eff numeric := (profile->>'efficiency_pct')::numeric;
    boil_off numeric := (profile->>'boil_off_l_h')::numeric;
    losses numeric := (profile->>'losses_l')::numeric;
    mash_c numeric := (targets->'mash_c'->>'value')::numeric;
    style_code text := targets->'style'->>'code';
    k text;
    t_og numeric; t_fg numeric; t_abv numeric; t_ibu numeric; t_srm numeric;
    yeast_id bigint := (step6->'yeast'->>'ingredient_id')::bigint;
    yeast_name text := step6->'yeast'->>'name';
    yeast_range numrange;
    attenuation numeric;
    ferm_c numeric;
    ferm_from_range boolean := false;
    items jsonb;
    hops jsonb;
    hop_ord bigint;
    boil_j jsonb;
    boil numeric;
    col jsonb;
    og_final numeric;
    og_j jsonb;
    og_note text;
    mash_note text;
    mash_from numeric;
    fg_range numrange;
    fg_pred numeric;
    knee numeric := (app.formulation_limits()->>'mash_knee_c')::numeric;
    mash_max numeric := (app.formulation_limits()->>'mash_max_c')::numeric;
    mash_lo numeric; mash_hi numeric; mash_mid numeric;
    solved jsonb;
    solved_hops jsonb;
    solver jsonb;
    preboil numeric;
    boil_sg numeric;
    extras jsonb := '[]'::jsonb;
    e jsonb;
    dose numeric;
    n_fg numeric; n_abv numeric; n_ibu numeric; n_srm numeric;
    no_colour jsonb;
    yeasts jsonb;
    recipe jsonb;
    rounded jsonb;
    rounded_hops jsonb;
    og_r numeric;
    values_used jsonb;
    stated jsonb := coalesce(brief->'stated', '{}'::jsonb) - 'batch_l';
begin
    -- 1. inputs
    foreach k in array array['og', 'fg', 'abv', 'ibu', 'srm'] loop
        if targets->'targets'->k->>'value' is null then
            raise exception 'step 10: step 4 gave no % target', upper(k);
        end if;
    end loop;
    if style_code is null then
        raise exception 'step 10: step 4 gave no style';
    end if;
    t_og := (targets->'targets'->'og'->>'value')::numeric;
    t_fg := (targets->'targets'->'fg'->>'value')::numeric;
    t_abv := (targets->'targets'->'abv'->>'value')::numeric;
    t_ibu := (targets->'targets'->'ibu'->>'value')::numeric;
    t_srm := (targets->'targets'->'srm'->>'value')::numeric;

    select ye.attenuation_pct into yeast_range from ref.yeast ye where ye.ingredient_id = yeast_id;
    attenuation := app.mash_attenuation(yeast_range, mash_c);  -- null when the yeast has no figure
    select (c.dose->>'ferm_c')::numeric into ferm_c
      from app.ingredient_choices(yeast_id, null) c where c.label = step6->'yeast'->>'choice';
    if ferm_c is null and step6->'yeast'->>'choice' is null then
        -- step 6 may pick a yeast with no choice: the middle of its temperature range stands in
        ferm_c := (coalesce((step6->'yeast'->'temp_c'->>'low')::numeric, (step6->'yeast'->'temp_c'->>'high')::numeric)
                   + coalesce((step6->'yeast'->'temp_c'->>'high')::numeric, (step6->'yeast'->'temp_c'->>'low')::numeric)) / 2;
        if ferm_c is null then
            raise exception 'step 10: the yeast % has no fermentation temperature', yeast_name;
        end if;
        ferm_from_range := true;
    elsif ferm_c is null then
        raise exception 'step 10: the choice "%" of % is not a fermentation temperature',
            step6->'yeast'->>'choice', yeast_name;
    end if;

    -- the grist, with the facts of the ref row (as check_recipe_items reads them)
    select jsonb_agg(jsonb_build_object(
               'ingredient_id', (f->>'ingredient_id')::bigint, 'name', f->>'name', 'role', ft.role,
               'pct', (f->>'pct')::numeric, 'extract_pct', ft.extract_dbfg_pct,
               'mashed', ft.role is distinct from 'sugar', 'ebc', app.ebc_mid(ft.ebc),
               'max_pct', ft.max_pct, 'fermentability', ft.fermentability,
               'usage', f->>'usage', 'purpose', f->>'purpose') order by ord)
      into items
      from jsonb_array_elements(step7->'fermentables') with ordinality t(f, ord)
      join ref.fermentable ft on ft.ingredient_id = (f->>'ingredient_id')::bigint;
    if items is null or jsonb_array_length(items) <> jsonb_array_length(step7->'fermentables') then
        raise exception 'step 10: a step 7 fermentable is not in ref.fermentable';
    end if;
    if exists (select 1 from jsonb_array_elements(items) x where x->>'extract_pct' is null) then
        raise exception 'step 10: a fermentable has no extract_dbfg_pct';
    end if;
    select coalesce(jsonb_agg(x->>'name' order by ord), '[]'::jsonb) into no_colour
      from jsonb_array_elements(items) with ordinality t(x, ord) where x->>'ebc' is null;

    -- 2. boil time; the longest boil addition becomes the bittering addition
    boil_j := app.step10_boil(array(select (x->>'ingredient_id')::bigint from jsonb_array_elements(items) x),
                              step8->'hops');
    boil := (boil_j->>'boil_min')::numeric;
    select ord into hop_ord
      from jsonb_array_elements(step8->'hops') with ordinality t(h, ord)
     where h->>'usage' = 'boil'
     order by (h->>'minutes')::numeric desc, (h->>'share_pct')::numeric desc, (h->>'ingredient_id')::bigint
     limit 1;
    select coalesce(jsonb_agg(case when ord = hop_ord then h || jsonb_build_object('minutes', boil) else h end
                              order by ord), '[]'::jsonb)
      into hops from jsonb_array_elements(step8->'hops') with ordinality t(h, ord);
    if exists (select 1 from jsonb_array_elements(hops) h where h->>'alpha_pct' is null) then
        raise exception 'step 10: no alpha acid for %',
            (select h->>'name' from jsonb_array_elements(hops) h where h->>'alpha_pct' is null limit 1);
    end if;

    -- 3. colour
    col := app.solve_colour(t_srm, items, t_og, eff, volume);
    items := col->'grist';

    -- 4. OG move (for the mash used)
    og_j := app.step10_og_move(t_og, t_abv, items, eff, volume, attenuation, yeast_name);
    og_final := (og_j->>'value')::numeric;
    og_note := og_j->>'because';

    -- 4b. mash move: Troester's curve lowers the attenuation only above the knee, so a predicted
    -- FG (at the OG used) below rule 10's range is raised by a hotter mash, never by a cooler one;
    -- a moved mash changes the attenuation, so the OG move is made again
    mash_from := mash_c;
    if attenuation is null then
        mash_note := format('%s C stays: %s has no attenuation figure, so no FG is predicted', trim_scale(mash_c), yeast_name);
    else
        fg_range := app.rule10_fg_range(style_code, t_fg, stated);
        fg_pred := app.fg(app.solve_grist(og_final, items, eff, volume), eff, volume, attenuation);
        if fg_range is null then
            mash_note := format('%s C stays: the style has no FG range to check the predicted FG against', trim_scale(mash_c));
        elsif targets->'mash_c'->>'from' = 'hint' then
            mash_note := format('%s C stays: the brief hints at this mash temperature (predicted FG %s, range %s to %s)',
                                trim_scale(mash_c), to_char(fg_pred, 'FM0.0000'),
                                to_char(lower(fg_range), 'FM0.0000'), to_char(upper(fg_range), 'FM0.0000'));
        elsif fg_pred >= lower(fg_range) and fg_pred <= upper(fg_range) then
            mash_note := format('%s C stays: the predicted FG %s is inside the range %s to %s',
                                trim_scale(mash_c), to_char(fg_pred, 'FM0.0000'),
                                to_char(lower(fg_range), 'FM0.0000'), to_char(upper(fg_range), 'FM0.0000'));
        elsif fg_pred > upper(fg_range) then
            mash_note := format('%s C stays: the predicted FG %s is above the range %s to %s, and a lower mash does not help (the attenuation curve is flat below %s C)',
                                trim_scale(mash_c), to_char(fg_pred, 'FM0.0000'),
                                to_char(lower(fg_range), 'FM0.0000'), to_char(upper(fg_range), 'FM0.0000'), trim_scale(knee));
        else
            -- below the range: FG rises with the mash, so bisect [knee, max] for the FG target
            if app.fg(app.solve_grist(og_final, items, eff, volume), eff, volume,
                      app.mash_attenuation(yeast_range, mash_max)) < t_fg then
                mash_c := mash_max;
            else
                mash_lo := knee;
                mash_hi := mash_max;
                for i in 1..40 loop
                    mash_mid := (mash_lo + mash_hi) / 2;
                    if app.fg(app.solve_grist(og_final, items, eff, volume), eff, volume,
                              app.mash_attenuation(yeast_range, mash_mid)) < t_fg then
                        mash_lo := mash_mid;
                    else
                        mash_hi := mash_mid;
                    end if;
                end loop;
                mash_c := (mash_lo + mash_hi) / 2;
            end if;
            attenuation := app.mash_attenuation(yeast_range, mash_c);
            mash_note := format('mash raised from %s C to %s C%s: the predicted FG %s at %s C was below the range %s to %s',
                trim_scale(mash_from), trim_scale(round(mash_c, 2)),
                case when mash_c = mash_max then format(' (the mash limit; the FG target %s is still not reached)',
                                                        to_char(t_fg, 'FM0.0000'))
                     else '' end,
                to_char(fg_pred, 'FM0.0000'), trim_scale(mash_from),
                to_char(lower(fg_range), 'FM0.0000'), to_char(upper(fg_range), 'FM0.0000'));
        end if;
    end if;
    if mash_c <> mash_from then
        og_j := app.step10_og_move(t_og, t_abv, items, eff, volume, attenuation, yeast_name);
        og_final := (og_j->>'value')::numeric;
        og_note := og_j->>'because';
        mash_note := mash_note || format(', and is %s now',
            to_char(app.fg(app.solve_grist(og_final, items, eff, volume), eff, volume, attenuation), 'FM0.0000'));
    end if;

    -- 5. amounts
    solved := app.solve_grist(og_final, items, eff, volume);
    preboil := app.preboil_volume(volume, boil, boil_off, losses);
    boil_sg := app.boil_gravity(og_final, volume + losses, preboil);
    select coalesce(jsonb_agg(jsonb_build_object(
               'ingredient_id', h->'ingredient_id', 'name', h->'name', 'purpose', h->'purpose',
               'usage', h->'usage', 'minutes', h->'minutes', 'share_pct', h->'share_pct',
               'alpha_pct', h->'alpha_pct') order by ord), '[]'::jsonb)
      into solver from jsonb_array_elements(hops) with ordinality t(h, ord);
    solved_hops := app.solve_hops(t_ibu, solver, boil_sg, volume);

    for e in select * from jsonb_array_elements(step9->'extras') loop
        dose := (e->>'dose_g_per_l')::numeric;
        if dose is null then
            raise exception 'step 10: no dose for %', e->>'name';
        end if;
        extras := extras || jsonb_build_object(
            'ingredient_id', (e->>'ingredient_id')::bigint, 'name', e->>'name', 'usage', e->>'usage',
            'time_min', e->'time_min', 'dose_g_per_l', dose, 'purpose', e->>'purpose',
            'g', greatest(round(dose * volume), (app.weighing_steps()->>'extra_g')::numeric));
    end loop;

    yeasts := jsonb_build_array(jsonb_build_object(
        'ingredient_id', yeast_id, 'name', yeast_name, 'role', 'main', 'amount', 1, 'unit', 'pack',
        'purpose', step6->'yeast'->>'purpose'));
    if jsonb_typeof(step6->'souring') = 'object' then
        yeasts := yeasts || jsonb_build_object(
            'ingredient_id', (step6->'souring'->>'ingredient_id')::bigint, 'name', step6->'souring'->>'name',
            'role', 'souring', 'amount', 1, 'unit', 'pack', 'purpose', step6->'souring'->>'purpose');
    end if;

    recipe := jsonb_build_object(
        'style_code', style_code, 'guidance', (targets->>'guidance')::boolean, 'stated', stated,
        'hints', coalesce(brief->'hints', '[]'::jsonb),
        'targets', jsonb_build_object('og', og_final, 'fg', t_fg, 'abv', t_abv, 'ibu', t_ibu, 'srm', t_srm),
        'batch', jsonb_build_object('volume_l', volume, 'efficiency_pct', eff, 'boil_off_l_h', boil_off,
                                    'losses_l', losses),
        'mash_c', mash_c, 'boil_min', boil,
        'fermentables', (select jsonb_agg(jsonb_build_object('ingredient_id', x->'ingredient_id',
                             'pct', x->'pct', 'purpose', x->'purpose') order by ord)
                           from jsonb_array_elements(solved) with ordinality t(x, ord)),
        'hops', (select coalesce(jsonb_agg(jsonb_build_object('ingredient_id', x->'ingredient_id',
                             'usage', x->'usage', 'minutes', x->'minutes', 'purpose', x->'purpose',
                             'g', x->'g') order by ord), '[]'::jsonb)
                   from jsonb_array_elements(solved_hops) with ordinality t(x, ord)),
        'yeast', jsonb_build_object('ingredient_id', yeast_id, 'ferm_c', ferm_c,
                                    'purpose', step6->'yeast'->>'purpose'));
    if jsonb_array_length(extras) > 0 then
        recipe := recipe || jsonb_build_object('extras', (
            select jsonb_agg(jsonb_build_object('ingredient_id', x->'ingredient_id', 'usage', x->'usage',
                             'g', x->'g', 'purpose', x->'purpose') order by ord)
              from jsonb_array_elements(extras) with ordinality t(x, ord)));
    end if;

    -- 6. rounding to the weighing steps (Task 10b): the grist first, then the hops at the rounded
    -- OG's boil gravity; the recipe object and the numbers follow the rounded amounts
    rounded := app.step10_round_grist(solved, recipe, jsonb_build_object('og', t_og, 'abv', t_abv, 'srm', t_srm),
                                      stated, eff, volume, attenuation);
    solved := rounded->'grist';
    og_r := app.og(solved, eff, volume);
    boil_sg := app.boil_gravity(og_r, volume + losses, preboil);
    solved_hops := app.solve_hops(t_ibu, solver, boil_sg, volume);
    rounded_hops := app.step10_round_hops(solved_hops, t_ibu, stated, boil_sg, volume);
    solved_hops := rounded_hops->'hops';
    recipe := app.step10_set_amounts(recipe, og_r, solved, solved_hops);

    -- 7. numbers, from the rounded amounts
    if attenuation is not null then
        n_fg := app.fg(solved, eff, volume, attenuation);
        n_abv := app.abv(og_r, n_fg);
    end if;
    n_ibu := (rounded_hops->>'ibu')::numeric;
    n_srm := app.srm(app.grist_mcu(solved, volume));

    values_used := jsonb_build_array(
        jsonb_build_object('what', 'colour', 'because',
            'each fermentable counts at the middle of its EBC range: ' || (
                select string_agg(x->>'name' || ' ' || coalesce(trim_scale(round((x->>'ebc')::numeric, 1))::text,
                                                                'no colour, counted as 0'), ', ' order by ord)
                  from jsonb_array_elements(items) with ordinality t(x, ord))),
        jsonb_build_object('what', 'alpha', 'because',
            'each hop counts at the middle of its alpha acid range: ' || (
                select coalesce(string_agg(x->>'name' || ' ' || trim_scale(round((x->>'alpha_pct')::numeric, 1)) || ' %',
                                           ', ' order by ord), 'no hops')
                  from jsonb_array_elements(hops) with ordinality t(x, ord))),
        jsonb_build_object('what', 'attenuation', 'because',
            case when attenuation is null
                then yeast_name || ' has no attenuation figure, so FG and ABV are not computed'
                else format('%s attenuates %s %%: the middle of its range %s at a mash of %s C (app.mash_attenuation)',
                            yeast_name, trim_scale(round(attenuation, 1)), yeast_range, trim_scale(round(mash_c, 2))) end),
        jsonb_build_object('what', 'ferm_c', 'because',
            case when ferm_from_range
                then format('%s C, the middle of the temperature range of %s: step 6 gave no choice', trim_scale(ferm_c), yeast_name)
                else format('%s C, the temperature of the chosen "%s"', trim_scale(ferm_c), step6->'yeast'->>'choice') end),
        jsonb_build_object('what', 'boil', 'because', boil_j->>'because'),
        jsonb_build_object('what', 'mash', 'because', mash_note),
        jsonb_build_object('what', 'yeast amount', 'because',
            '1 pack of each yeast: a placeholder until the pitch rate is set (M7)'));

    return jsonb_build_object(
        'batch', jsonb_build_object('volume_l', volume, 'efficiency_pct', eff, 'boil_off_l_h', boil_off,
                                    'losses_l', losses),
        'boil', boil_j, 'mash_c', mash_c, 'ferm_c', ferm_c,
        'og_used', jsonb_build_object('value', og_final, 'moved', og_final <> t_og, 'because', og_note),
        'colour', col,
        'fermentables', (select jsonb_agg(jsonb_build_object('ingredient_id', x->'ingredient_id',
                             'name', x->'name', 'usage', x->'usage', 'pct', x->'pct', 'kg', x->'kg',
                             'purpose', x->'purpose') order by ord)
                           from jsonb_array_elements(solved) with ordinality t(x, ord)),
        'hops', (select coalesce(jsonb_agg(jsonb_build_object('ingredient_id', x->'ingredient_id',
                             'name', x->'name', 'usage', x->'usage', 'minutes', x->'minutes',
                             'share_pct', x->'share_pct', 'alpha_pct', x->'alpha_pct', 'g', x->'g',
                             'purpose', x->'purpose') order by ord), '[]'::jsonb)
                   from jsonb_array_elements(solved_hops) with ordinality t(x, ord)),
        'yeasts', yeasts,
        'extras', (select coalesce(jsonb_agg(x || jsonb_build_object(
                             'usage', case when x->>'usage' = 'packaging' then 'package' else x->>'usage' end)
                             order by ord), '[]'::jsonb)
                     from jsonb_array_elements(extras) with ordinality t(x, ord)),
        'numbers', jsonb_build_object('og', og_r, 'fg', n_fg, 'abv', n_abv,
                                      'ibu', n_ibu, 'srm', n_srm, 'attenuation_pct', attenuation,
                                      'srm_lower_bound', no_colour),
        'values_used', values_used,
        'rounding', jsonb_build_object('steps', app.weighing_steps(), 'reached', rounded->'reached',
                                       'added', rounded->'added', 'off_nearest', rounded->'off_nearest',
                                       'because', (rounded->>'because') || ' ' || (rounded_hops->>'because')),
        'recipe', recipe);
end;
$$;

comment on function app.step10_compute(jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb) is
    'Step 10: amounts and numbers of a recipe from steps 6-9, with s1''s functions only; builds the formulation_check.input object step 11 checks.';
