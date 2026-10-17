-- Formulation check (docs/work/s2-formulation-rules): resolves a proposed recipe against the ref
-- tables, computes its numbers with s1's functions only, and checks the formulation rules. One
-- function per rule, written out in plain SQL; there is no rule table. Every threshold comes from
-- app.formulation_limits() and the rule text from app.formulation_rules() (db/031).
-- Built task by task; later tasks append to this file. Bad input raises, it never becomes a pass.
-- Needs db/010_ref_schema.sql, db/015_app.sql, db/030_maths.sql, db/031_formulation_rules.sql,
-- db/039_step4.sql (rule 9 calls app.step4_numbers).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/032_formulation_check.sql
-- Idempotent: safe to re-run.

-- Midpoint of a numeric range; one bound when the other is open; null when there is no range.
-- Used for a fermentable's colour (ebc) and for a hop's alpha acid.
create or replace function app.ebc_mid(ebc numrange)
returns numeric
language sql
immutable
as $$
    select case
        when ebc is null or isempty(ebc) then null
        when lower(ebc) is null then upper(ebc)
        when upper(ebc) is null then lower(ebc)
        else (lower(ebc) + upper(ebc)) / 2
    end
$$;

-- Attenuation at a mash temperature, after Troester's curve of the limit of attenuation against
-- mash temperature (Troester 2009, "Effects of mash parameters on attenuation and efficiency",
-- braukaiser.com, CC BY-NC 3.0, Figure 10 and the appendix temperature series; constants and
-- derivation in docs/work/s5-mash-attenuation/doc-calc.md). The middle of the yeast's range is
-- its attenuation at the reference temperature; the curve's difference is added for any other
-- mash temperature. Up to the knee (68.3 C) the attenuation is the middle of the yeast's range;
-- above it, it is 4.15 points lower per degree, never outside the yeast's range. mash_c is
-- clamped to the mash limits (rule 10).
create or replace function app.mash_attenuation(attenuation numrange, mash_c numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    l jsonb := app.formulation_limits();
    low_c numeric := (l->>'mash_min_c')::numeric;
    high_c numeric := (l->>'mash_max_c')::numeric;
    ref_c numeric := (l->>'mash_ref_c')::numeric;
    knee_c numeric := (l->>'mash_knee_c')::numeric;
    slope numeric := (l->>'mash_slope_pct_per_c')::numeric;
    top numeric := upper(attenuation);
    bottom numeric := lower(attenuation);
    middle numeric;
    clamped numeric;
    result numeric;
begin
    if attenuation is null or top is null or bottom is null or mash_c is null then
        return null;
    end if;
    clamped := greatest(low_c, least(high_c, mash_c));
    middle := (top + bottom) / 2;
    result := middle - slope * (greatest(clamped, knee_c) - greatest(ref_c, knee_c));
    return greatest(bottom, least(top, result));
end;
$$;

-- "Caraaroma 10 %, Carafa Special Type 2 8 %" from an array of resolved fermentable items.
create or replace function app.share_list(items jsonb)
returns text
language sql
immutable
as $$
    select coalesce(string_agg(x->>'name' || ' ' || trim_scale(round((x->>'pct')::numeric, 1))::text
                               || ' %', ', '), 'none')
    from jsonb_array_elements(items) x
$$;

-- One failure of a rule: its sentence, the items involved (id and name only), the measured value
-- and the limit.
create or replace function app.rule_failure(message text, items jsonb, value numeric, lim numeric)
returns jsonb
language sql
immutable
as $$
    select jsonb_build_object(
        'text', message,
        'items', coalesce((select jsonb_agg(jsonb_build_object(
                     'ingredient_id', (x->>'ingredient_id')::bigint, 'name', x->>'name'))
                 from jsonb_array_elements(items) x), '[]'::jsonb),
        'value', value,
        'limit', lim)
$$;

-- The result object of one rule. fail when there is any failure; otherwise unknown when a needed
-- field is missing; otherwise pass. The message is the failures' sentences, the missing fields,
-- or the pass message.
create or replace function app.rule_result(rule int, failures jsonb, missing jsonb, pass_message text)
returns jsonb
language sql
immutable
as $$
    select jsonb_build_object(
        'rule', rule,
        'status', case when jsonb_array_length(failures) > 0 then 'fail'
                       when jsonb_array_length(missing) > 0 then 'unknown'
                       else 'pass' end,
        'message', case
            when jsonb_array_length(failures) > 0
                then (select string_agg(f->>'text', ' ') from jsonb_array_elements(failures) f)
            when jsonb_array_length(missing) > 0
                then format('Rule %s: not checked, missing %s.', rule,
                            (select string_agg(m #>> '{}', ', ') from jsonb_array_elements(missing) m))
            else pass_message end,
        'failures', failures,
        'missing', missing)
$$;

-- Resolves the ids of a recipe against the ref tables and returns
-- {style_code, fermentables[], hops[], yeast}. Raises on an unknown style code, an id that is not
-- of the right kind, a duplicate fermentable, or percentages more than pct_sum_tolerance from 100.
-- A fermentable counts as mashed unless its role is sugar (brief assumption).
create or replace function app.check_recipe_items(recipe jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    l jsonb := app.formulation_limits();
    r jsonb;
    ferm jsonb := '[]'::jsonb;
    hops jsonb := '[]'::jsonb;
    yeast jsonb;
    seen bigint[] := '{}';
    pct_sum numeric := 0;
    ing_id bigint;
    f record;
    h record;
    y record;
begin
    if not exists (select 1 from ref.beer_style where code = recipe->>'style_code') then
        raise exception 'check_recipe: style code % is not in ref.beer_style', recipe->>'style_code';
    end if;

    for r in select * from jsonb_array_elements(recipe->'fermentables') loop
        ing_id := (r->>'ingredient_id')::bigint;
        if ing_id = any(seen) then
            raise exception 'check_recipe: fermentable % appears twice', ing_id;
        end if;
        seen := seen || ing_id;
        select i.name, ft.role, app.ebc_mid(ft.ebc) as ebc_mid, ft.max_pct, ft.min_boil_min,
               ft.fermentability, ft.extract_dbfg_pct
          into f
          from ref.ingredient i join ref.fermentable ft on ft.ingredient_id = i.id
         where i.id = ing_id;
        if not found then
            raise exception 'check_recipe: ingredient % is not a fermentable', ing_id;
        end if;
        if f.extract_dbfg_pct is null then
            raise exception 'check_recipe: % has no extract_dbfg_pct', f.name;
        end if;
        pct_sum := pct_sum + (r->>'pct')::numeric;
        ferm := ferm || jsonb_build_object(
            'ingredient_id', ing_id, 'name', f.name, 'pct', (r->>'pct')::numeric,
            'purpose', r->>'purpose', 'role', f.role, 'ebc_mid', f.ebc_mid,
            'max_pct', f.max_pct, 'min_boil_min', f.min_boil_min,
            'fermentability', f.fermentability, 'extract_pct', f.extract_dbfg_pct,
            'mashed', f.role is distinct from 'sugar');
    end loop;
    if abs(pct_sum - 100) > (l->>'pct_sum_tolerance')::numeric then
        raise exception 'check_recipe: fermentable percentages add up to %, not 100', pct_sum;
    end if;

    for r in select * from jsonb_array_elements(recipe->'hops') loop
        ing_id := (r->>'ingredient_id')::bigint;
        select i.name, app.ebc_mid(hp.alpha_pct) as alpha_mid
          into h
          from ref.ingredient i join ref.hop hp on hp.ingredient_id = i.id
         where i.id = ing_id;
        if not found then
            raise exception 'check_recipe: ingredient % is not a hop', ing_id;
        end if;
        hops := hops || jsonb_build_object(
            'ingredient_id', ing_id, 'name', h.name, 'usage', r->>'usage',
            'minutes', (r->>'minutes')::numeric, 'purpose', r->>'purpose',
            'g', (r->>'g')::numeric, 'alpha_pct', h.alpha_mid);
    end loop;

    ing_id := (recipe->'yeast'->>'ingredient_id')::bigint;
    select i.name, ye.attenuation_pct, ye.temp_c, ye.alcohol_tolerance_pct
      into y
      from ref.ingredient i join ref.yeast ye on ye.ingredient_id = i.id
     where i.id = ing_id;
    if not found then
        raise exception 'check_recipe: ingredient % is not a yeast', ing_id;
    end if;
    yeast := jsonb_build_object(
        'ingredient_id', ing_id, 'name', y.name, 'ferm_c', (recipe->'yeast'->>'ferm_c')::numeric,
        'purpose', recipe->'yeast'->>'purpose',
        'attenuation_pct', y.attenuation_pct::text, 'temp_c', y.temp_c::text,
        'alcohol_tolerance_pct', y.alcohol_tolerance_pct);

    return jsonb_build_object('style_code', recipe->>'style_code', 'fermentables', ferm,
                              'hops', hops, 'yeast', yeast);
end;
$$;

-- Rule 1: at most max_fermentables fermentables, at most max_specialty of them kilned, crystal
-- or roast. Adjunct and sugar do not count toward the second limit.
create or replace function app.check_rule_1(items jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    l jsonb := app.formulation_limits();
    ferm jsonb := items->'fermentables';
    total int := jsonb_array_length(ferm);
    spec jsonb := (select coalesce(jsonb_agg(x), '[]'::jsonb) from jsonb_array_elements(ferm) x
                    where x->>'role' in ('kilned', 'crystal', 'roast'));
    n_spec int := jsonb_array_length(spec);
    failures jsonb := '[]'::jsonb;
begin
    if total > (l->>'max_fermentables')::int then
        failures := failures || app.rule_failure(
            format('Rule 1: the recipe has %s fermentables (%s); the limit is %s.',
                   total, app.share_list(ferm), l->>'max_fermentables'),
            ferm, total, (l->>'max_fermentables')::numeric);
    end if;
    if n_spec > (l->>'max_specialty')::int then
        failures := failures || app.rule_failure(
            format('Rule 1: %s fermentables have the role kilned, crystal or roast (%s); the limit is %s.',
                   n_spec, app.share_list(spec), l->>'max_specialty'),
            spec, n_spec, (l->>'max_specialty')::numeric);
    end if;
    return app.rule_result(1, failures, '[]'::jsonb,
        format('Rule 1: %s fermentables, %s of them kilned, crystal or roast; the limits are %s and %s.',
               total, n_spec, l->>'max_fermentables', l->>'max_specialty'));
end;
$$;

-- Rule 2: at most max_hop_varieties distinct hops.
create or replace function app.check_rule_2(items jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    l jsonb := app.formulation_limits();
    hops jsonb := items->'hops';
    n int := (select count(distinct x->>'ingredient_id') from jsonb_array_elements(hops) x);
    failures jsonb := '[]'::jsonb;
begin
    if n > (l->>'max_hop_varieties')::int then
        failures := failures || app.rule_failure(
            format('Rule 2: the recipe uses %s hop varieties (%s); the limit is %s.', n,
                   (select string_agg(distinct x->>'name', ', ') from jsonb_array_elements(hops) x),
                   l->>'max_hop_varieties'),
            hops, n, (l->>'max_hop_varieties')::numeric);
    end if;
    return app.rule_result(2, failures, '[]'::jsonb,
        format('Rule 2: %s hop varieties; the limit is %s.', n, l->>'max_hop_varieties'));
end;
$$;

-- Rule 3: crystal above crystal_dark_ebc plus roast, together at most dark_total_pct.
-- A crystal malt with no colour cannot be placed: the rule is unknown unless it already fails.
create or replace function app.check_rule_3(items jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    l jsonb := app.formulation_limits();
    ferm jsonb := items->'fermentables';
    dark jsonb := (select coalesce(jsonb_agg(x), '[]'::jsonb) from jsonb_array_elements(ferm) x
                    where x->>'role' = 'roast'
                       or (x->>'role' = 'crystal'
                           and (x->>'ebc_mid')::numeric > (l->>'crystal_dark_ebc')::numeric));
    total numeric := (select coalesce(sum((x->>'pct')::numeric), 0) from jsonb_array_elements(dark) x);
    lim numeric := (l->>'dark_total_pct')::numeric;
    failures jsonb := '[]'::jsonb;
    missing jsonb := '[]'::jsonb;
begin
    if exists (select 1 from jsonb_array_elements(ferm) x
                where x->>'role' = 'crystal' and x->>'ebc_mid' is null) then
        missing := '["ref.fermentable.ebc"]'::jsonb;
    end if;
    if total > lim then
        failures := failures || app.rule_failure(
            format('Rule 3: crystal above %s EBC plus roast is %s %% of the grist (%s); the limit is %s %%.',
                   l->>'crystal_dark_ebc', trim_scale(round(total, 1)), app.share_list(dark), l->>'dark_total_pct'),
            dark, total, lim);
    end if;
    return app.rule_result(3, failures, missing,
        format('Rule 3: crystal above %s EBC plus roast is %s %% of the grist; the limit is %s %%.',
               l->>'crystal_dark_ebc', trim_scale(round(total, 1)), l->>'dark_total_pct'));
end;
$$;

-- Rule 4: crystal at most crystal_total_pct together; those above crystal_dark_ebc at most
-- crystal_dark_pct; those above crystal_very_dark_ebc at most crystal_very_dark_pct.
-- Crystal at or below crystal_dark_ebc is limited only by rule 6.
create or replace function app.check_rule_4(items jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    l jsonb := app.formulation_limits();
    ferm jsonb := items->'fermentables';
    crystal jsonb := (select coalesce(jsonb_agg(x), '[]'::jsonb) from jsonb_array_elements(ferm) x
                       where x->>'role' = 'crystal');
    dark jsonb := (select coalesce(jsonb_agg(x), '[]'::jsonb) from jsonb_array_elements(crystal) x
                    where (x->>'ebc_mid')::numeric > (l->>'crystal_dark_ebc')::numeric);
    very_dark jsonb := (select coalesce(jsonb_agg(x), '[]'::jsonb) from jsonb_array_elements(crystal) x
                         where (x->>'ebc_mid')::numeric > (l->>'crystal_very_dark_ebc')::numeric);
    t_all numeric := (select coalesce(sum((x->>'pct')::numeric), 0) from jsonb_array_elements(crystal) x);
    t_dark numeric := (select coalesce(sum((x->>'pct')::numeric), 0) from jsonb_array_elements(dark) x);
    t_very numeric := (select coalesce(sum((x->>'pct')::numeric), 0) from jsonb_array_elements(very_dark) x);
    failures jsonb := '[]'::jsonb;
    missing jsonb := '[]'::jsonb;
begin
    if exists (select 1 from jsonb_array_elements(crystal) x where x->>'ebc_mid' is null) then
        missing := '["ref.fermentable.ebc"]'::jsonb;
    end if;
    if t_all > (l->>'crystal_total_pct')::numeric then
        failures := failures || app.rule_failure(
            format('Rule 4: crystal is %s %% of the grist (%s); the limit is %s %%.',
                   trim_scale(round(t_all, 1)), app.share_list(crystal), l->>'crystal_total_pct'),
            crystal, t_all, (l->>'crystal_total_pct')::numeric);
    end if;
    if t_dark > (l->>'crystal_dark_pct')::numeric then
        failures := failures || app.rule_failure(
            format('Rule 4: crystal above %s EBC is %s %% of the grist (%s); the limit is %s %%.',
                   l->>'crystal_dark_ebc', trim_scale(round(t_dark, 1)), app.share_list(dark),
                   l->>'crystal_dark_pct'),
            dark, t_dark, (l->>'crystal_dark_pct')::numeric);
    end if;
    if t_very > (l->>'crystal_very_dark_pct')::numeric then
        failures := failures || app.rule_failure(
            format('Rule 4: crystal above %s EBC is %s %% of the grist (%s); the limit is %s %%.',
                   l->>'crystal_very_dark_ebc', trim_scale(round(t_very, 1)), app.share_list(very_dark),
                   l->>'crystal_very_dark_pct'),
            very_dark, t_very, (l->>'crystal_very_dark_pct')::numeric);
    end if;
    return app.rule_result(4, failures, missing,
        format('Rule 4: crystal is %s %% of the grist, %s %% above %s EBC, %s %% above %s EBC; the limits are %s, %s and %s %%.',
               trim_scale(round(t_all, 1)), trim_scale(round(t_dark, 1)), l->>'crystal_dark_ebc',
               trim_scale(round(t_very, 1)), l->>'crystal_very_dark_ebc',
               l->>'crystal_total_pct', l->>'crystal_dark_pct', l->>'crystal_very_dark_pct'));
end;
$$;

-- Rule 5: adjunct plus sugar at most adjunct_sugar_pct together.
create or replace function app.check_rule_5(items jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    l jsonb := app.formulation_limits();
    extra jsonb := (select coalesce(jsonb_agg(x), '[]'::jsonb)
                      from jsonb_array_elements(items->'fermentables') x
                     where x->>'role' in ('adjunct', 'sugar'));
    total numeric := (select coalesce(sum((x->>'pct')::numeric), 0) from jsonb_array_elements(extra) x);
    lim numeric := (l->>'adjunct_sugar_pct')::numeric;
    failures jsonb := '[]'::jsonb;
begin
    if total > lim then
        failures := failures || app.rule_failure(
            format('Rule 5: adjunct and sugar are %s %% of the grist (%s); the limit is %s %%.',
                   trim_scale(round(total, 1)), app.share_list(extra), l->>'adjunct_sugar_pct'),
            extra, total, lim);
    end if;
    return app.rule_result(5, failures, '[]'::jsonb,
        format('Rule 5: adjunct and sugar are %s %% of the grist; the limit is %s %%.',
               trim_scale(round(total, 1)), l->>'adjunct_sugar_pct'));
end;
$$;

-- Rule 6: each fermentable at most its own max_pct. A fermentable with no max_pct is unknown.
create or replace function app.check_rule_6(items jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    x jsonb;
    failures jsonb := '[]'::jsonb;
    missing jsonb := '[]'::jsonb;
begin
    for x in select * from jsonb_array_elements(items->'fermentables') loop
        if x->>'max_pct' is null then
            missing := '["ref.fermentable.max_pct"]'::jsonb;
        elsif (x->>'pct')::numeric > (x->>'max_pct')::numeric then
            failures := failures || app.rule_failure(
                format('Rule 6: %s is %s %% of the grist; its max_pct is %s %%.', x->>'name',
                       trim_scale(round((x->>'pct')::numeric, 1)), trim_scale((x->>'max_pct')::numeric)),
                jsonb_build_array(x), (x->>'pct')::numeric, (x->>'max_pct')::numeric);
        end if;
    end loop;
    return app.rule_result(6, failures, missing,
        'Rule 6: every fermentable is within its max_pct.');
end;
$$;

-- Rule 8: exactly one bittering addition (a boil addition whose time equals the boil time); every
-- other addition is a boil addition of at most late_hop_max_min, a whirlpool or a dry hop.
create or replace function app.check_rule_8(items jsonb, recipe jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    l jsonb := app.formulation_limits();
    boil numeric := (recipe->>'boil_min')::numeric;
    late numeric := (l->>'late_hop_max_min')::numeric;
    hops jsonb := items->'hops';
    bitter jsonb := (select coalesce(jsonb_agg(x), '[]'::jsonb) from jsonb_array_elements(hops) x
                      where x->>'usage' = 'boil' and (x->>'minutes')::numeric = boil);
    other jsonb := (select coalesce(jsonb_agg(x), '[]'::jsonb) from jsonb_array_elements(hops) x
                     where x->>'usage' = 'boil' and (x->>'minutes')::numeric <> boil
                       and ((x->>'minutes')::numeric > late or (x->>'minutes')::numeric > boil));
    n_bitter int := jsonb_array_length(bitter);
    x jsonb;
    failures jsonb := '[]'::jsonb;
begin
    if n_bitter <> 1 then
        failures := failures || app.rule_failure(
            format('Rule 8: the recipe has %s bittering additions (boil additions of %s min)%s; it needs exactly 1.',
                   n_bitter, trim_scale(boil),
                   case when n_bitter = 0 then '' else ' (' || (select string_agg(h->>'name', ', ')
                        from jsonb_array_elements(bitter) h) || ')' end),
            bitter, n_bitter, 1);
    end if;
    for x in select * from jsonb_array_elements(other) loop
        failures := failures || app.rule_failure(
            format('Rule 8: %s is a boil addition of %s min; besides the bittering addition a boil addition is at most %s min.',
                   x->>'name', trim_scale((x->>'minutes')::numeric), l->>'late_hop_max_min'),
            jsonb_build_array(x), (x->>'minutes')::numeric, late);
    end loop;
    return app.rule_result(8, failures, '[]'::jsonb,
        format('Rule 8: one bittering addition at %s min; every other addition is at most %s min, a whirlpool or a dry hop.',
               trim_scale(boil), l->>'late_hop_max_min'));
end;
$$;

-- Rule 9: with guidance on, a target the user did not state is where step 4 puts it
-- (app.step4_numbers, db/039): the style's midpoint, moved by the request's hints, with OG moved
-- inside its range as far as the ABV range needs; within midpoint_tolerance. OG and FG count as
-- stated when the ABV is stated. The ABV target is not compared with a midpoint: it must be
-- app.abv of the OG and FG targets, within midpoint_tolerance.abv. A stated target, or any
-- target with guidance off, may sit anywhere.
create or replace function app.check_rule_9(items jsonb, recipe jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    l jsonb := app.formulation_limits();
    stated jsonb := coalesce(recipe->'stated', '{}'::jsonb);
    guidance boolean := coalesce((recipe->>'guidance')::boolean, true);
    expected jsonb;
    k text;
    target numeric;
    want numeric;
    tol numeric;
    computed_abv numeric;
    failures jsonb := '[]'::jsonb;
    missing jsonb := '[]'::jsonb;
begin
    if guidance then
        expected := app.step4_numbers(items->>'style_code', stated, coalesce(recipe->'hints', '[]'::jsonb));
        foreach k in array array['og', 'fg', 'ibu', 'srm'] loop
            continue when stated ? k or (k in ('og', 'fg') and stated ? 'abv');
            want := (expected->k->>'value')::numeric;
            if want is null then
                missing := missing || to_jsonb('ref.beer_style.' || k);
                continue;
            end if;
            target := (recipe->'targets'->>k)::numeric;
            tol := (l->'midpoint_tolerance'->>k)::numeric;
            if abs(target - want) > tol then
                failures := failures || app.rule_failure(
                    format('Rule 9: the %s target %s was not stated and is not %s (%s), within %s.',
                           upper(k), trim_scale(target), trim_scale(want), expected->k->>'because', trim_scale(tol)),
                    '[]'::jsonb, target, want);
            end if;
        end loop;
        if not stated ? 'abv' then
            computed_abv := app.abv((recipe->'targets'->>'og')::numeric, (recipe->'targets'->>'fg')::numeric);
            target := (recipe->'targets'->>'abv')::numeric;
            tol := (l->'midpoint_tolerance'->>'abv')::numeric;
            if abs(target - computed_abv) > tol then
                failures := failures || app.rule_failure(
                    format('Rule 9: the ABV target %s is not app.abv of the OG and FG targets (%s), within %s.',
                           trim_scale(target), trim_scale(round(computed_abv, 2)), trim_scale(tol)),
                    '[]'::jsonb, target, round(computed_abv, 2));
            end if;
        end if;
    end if;
    return app.rule_result(9, failures, missing,
        'Rule 9: every target the user did not state is where step 4 puts it.');
end;
$$;

-- Rule 10: mash temperature inside mash_min_c..mash_max_c, and the predicted FG (numbers.fg, from
-- the mash-adjusted attenuation) inside the target FG range: the style's FG range, or the target
-- FG +- midpoint_tolerance.fg when the user stated the FG or the ABV.
create or replace function app.check_rule_10(items jsonb, recipe jsonb, numbers jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    l jsonb := app.formulation_limits();
    stated jsonb := coalesce(recipe->'stated', '{}'::jsonb);
    mash numeric := (recipe->>'mash_c')::numeric;
    pred numeric := (numbers->>'fg')::numeric;
    lo numeric;
    hi numeric;
    style_fg numrange;
    failures jsonb := '[]'::jsonb;
    missing jsonb := '[]'::jsonb;
begin
    if mash < (l->>'mash_min_c')::numeric or mash > (l->>'mash_max_c')::numeric then
        failures := failures || app.rule_failure(
            format('Rule 10: the mash temperature is %s °C; it must be between %s and %s °C.',
                   trim_scale(mash), l->>'mash_min_c', l->>'mash_max_c'),
            '[]'::jsonb, mash,
            case when mash < (l->>'mash_min_c')::numeric then (l->>'mash_min_c')::numeric
                 else (l->>'mash_max_c')::numeric end);
    end if;
    if stated ? 'fg' or stated ? 'abv' then
        lo := (recipe->'targets'->>'fg')::numeric - (l->'midpoint_tolerance'->>'fg')::numeric;
        hi := (recipe->'targets'->>'fg')::numeric + (l->'midpoint_tolerance'->>'fg')::numeric;
    else
        select fg into style_fg from ref.beer_style where code = items->>'style_code';
        if style_fg is null then
            missing := missing || '"ref.beer_style.fg"'::jsonb;
        else
            lo := lower(style_fg);
            hi := upper(style_fg);
        end if;
    end if;
    if pred is null then
        missing := missing || '"ref.yeast.attenuation_pct"'::jsonb;
    elsif lo is not null and (pred < lo or pred > hi) then
        failures := failures || app.rule_failure(
            format('Rule 10: the predicted FG %s (mash %s °C) is outside the target FG range %s to %s.',
                   to_char(pred, 'FM0.0000'), trim_scale(mash), to_char(lo, 'FM0.0000'), to_char(hi, 'FM0.0000')),
            '[]'::jsonb, pred, case when pred < lo then lo else hi end);
    end if;
    return app.rule_result(10, failures, missing,
        format('Rule 10: mash %s °C and predicted FG %s are within the limits.',
               trim_scale(mash), coalesce(to_char(pred, 'FM0.0000'), 'unknown')));
end;
$$;

-- Rule 11: planned ABV at most the yeast's alcohol_tolerance_pct; ferm_c inside the yeast's temp_c.
create or replace function app.check_rule_11(items jsonb, numbers jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    y jsonb := items->'yeast';
    abv numeric := (numbers->>'abv')::numeric;
    tolerance numeric := (y->>'alcohol_tolerance_pct')::numeric;
    temp numrange := (y->>'temp_c')::numrange;
    ferm_c numeric := (y->>'ferm_c')::numeric;
    failures jsonb := '[]'::jsonb;
    missing jsonb := '[]'::jsonb;
begin
    if tolerance is null then
        missing := missing || '"ref.yeast.alcohol_tolerance_pct"'::jsonb;
    elsif abv is null then
        missing := missing || '"ref.yeast.attenuation_pct"'::jsonb;
    elsif abv > tolerance then
        failures := failures || app.rule_failure(
            format('Rule 11: the planned ABV %s %% is above the alcohol tolerance of %s, %s %%.',
                   trim_scale(round(abv, 2)), y->>'name', trim_scale(tolerance)),
            jsonb_build_array(y), abv, tolerance);
    end if;
    if temp is null then
        missing := missing || '"ref.yeast.temp_c"'::jsonb;
    elsif not temp @> ferm_c then
        failures := failures || app.rule_failure(
            format('Rule 11: the fermentation temperature %s °C is outside the range %s to %s °C of %s.',
                   trim_scale(ferm_c), trim_scale(lower(temp)), trim_scale(upper(temp)), y->>'name'),
            jsonb_build_array(y), ferm_c, case when ferm_c < lower(temp) then lower(temp) else upper(temp) end);
    end if;
    return app.rule_result(11, failures, missing,
        'Rule 11: the planned ABV and the fermentation temperature suit the yeast.');
end;
$$;

-- Rule 12: every fermentable, hop and yeast has a purpose that is not empty after trimming.
create or replace function app.check_rule_12(items jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    x jsonb;
    failures jsonb := '[]'::jsonb;
begin
    for x in select * from jsonb_array_elements(
                 (items->'fermentables') || (items->'hops') || jsonb_build_array(items->'yeast')) loop
        if btrim(coalesce(x->>'purpose', '')) = '' then
            failures := failures || app.rule_failure(
                format('Rule 12: %s has no purpose.', x->>'name'), jsonb_build_array(x), null, null);
        end if;
    end loop;
    return app.rule_result(12, failures, '[]'::jsonb,
        'Rule 12: every fermentable, hop and yeast has a purpose.');
end;
$$;

-- Rule 13: boil_min at least the largest min_boil_min of the fermentables, and at least min_boil_min
-- from the limits. A fermentable with no min_boil_min is unknown.
create or replace function app.check_rule_13(items jsonb, recipe jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    l jsonb := app.formulation_limits();
    boil numeric := (recipe->>'boil_min')::numeric;
    floor_min numeric := (l->>'min_boil_min')::numeric;
    longest jsonb := (select x from jsonb_array_elements(items->'fermentables') x
                       where x->>'min_boil_min' is not null
                       order by (x->>'min_boil_min')::numeric desc limit 1);
    failures jsonb := '[]'::jsonb;
    missing jsonb := '[]'::jsonb;
begin
    if boil < floor_min then
        failures := failures || app.rule_failure(
            format('Rule 13: the boil time is %s min; the minimum is %s min.', trim_scale(boil), l->>'min_boil_min'),
            '[]'::jsonb, boil, floor_min);
    end if;
    if longest is not null and boil < (longest->>'min_boil_min')::numeric then
        failures := failures || app.rule_failure(
            format('Rule 13: the boil time is %s min; %s needs at least %s min.', trim_scale(boil),
                   longest->>'name', longest->>'min_boil_min'),
            jsonb_build_array(longest), boil, (longest->>'min_boil_min')::numeric);
    end if;
    if exists (select 1 from jsonb_array_elements(items->'fermentables') x where x->>'min_boil_min' is null) then
        missing := '["ref.fermentable.min_boil_min"]'::jsonb;
    end if;
    return app.rule_result(13, failures, missing,
        format('Rule 13: the boil time of %s min covers every fermentable.', trim_scale(boil)));
end;
$$;

-- The check. recipe is the input contract (shared/contracts/formulation_check.input.schema.json);
-- the result is the output contract. Numbers come from s1's functions only: the grist is solved
-- at the target OG, then OG, FG (at the mash-adjusted attenuation), ABV, SRM and IBU follow.
-- SRM is null when a fermentable has no colour; IBU is null unless every hop has grams and alpha;
-- FG and ABV are null when the yeast has no attenuation. The missing fields are named.
create or replace function app.check_recipe(recipe jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    items jsonb := app.check_recipe_items(recipe);
    batch jsonb := recipe->'batch';
    volume numeric := (batch->>'volume_l')::numeric;
    efficiency numeric := (batch->>'efficiency_pct')::numeric;
    losses numeric := (batch->>'losses_l')::numeric;
    grist jsonb;
    solved jsonb;
    yeast_att numrange := (items->'yeast'->>'attenuation_pct')::numrange;
    attenuation numeric := app.mash_attenuation(yeast_att, (recipe->>'mash_c')::numeric);
    n_og numeric;
    n_fg numeric;
    n_abv numeric;
    n_srm numeric;
    n_ibu numeric;
    preboil numeric;
    boil_sg numeric;
    missing jsonb := '[]'::jsonb;
    numbers jsonb;
    results jsonb;
begin
    grist := (select jsonb_agg(jsonb_build_object(
                  'pct', x->'pct', 'extract_pct', x->'extract_pct', 'mashed', x->'mashed',
                  'fermentability', x->'fermentability', 'ebc', x->'ebc_mid'))
                from jsonb_array_elements(items->'fermentables') x);
    solved := app.solve_grist((recipe->'targets'->>'og')::numeric, grist, efficiency, volume);
    n_og := app.og(solved, efficiency, volume);

    if attenuation is null then
        missing := missing || '"ref.yeast.attenuation_pct"'::jsonb;
    else
        n_fg := app.fg(solved, efficiency, volume, attenuation);
        n_abv := app.abv(n_og, n_fg);
    end if;

    if exists (select 1 from jsonb_array_elements(solved) x where x->>'ebc' is null) then
        missing := missing || '"ref.fermentable.ebc"'::jsonb;
    else
        n_srm := app.srm(app.grist_mcu(solved, volume));
    end if;

    if jsonb_array_length(items->'hops') = 0
       or exists (select 1 from jsonb_array_elements(items->'hops') x where x->>'g' is null) then
        missing := missing || '"hops.g"'::jsonb;
    elsif exists (select 1 from jsonb_array_elements(items->'hops') x where x->>'alpha_pct' is null) then
        missing := missing || '"ref.hop.alpha_pct"'::jsonb;
    else
        preboil := app.preboil_volume(volume, (recipe->>'boil_min')::numeric,
                                      (batch->>'boil_off_l_h')::numeric, losses);
        boil_sg := app.boil_gravity(n_og, volume + losses, preboil);
        n_ibu := app.ibu((select jsonb_agg(jsonb_build_object(
                              'g', x->'g', 'alpha_pct', x->'alpha_pct',
                              'minutes', x->'minutes', 'usage', x->'usage'))
                            from jsonb_array_elements(items->'hops') x), boil_sg, volume);
    end if;

    numbers := jsonb_build_object('og', n_og, 'fg', n_fg, 'abv', n_abv, 'srm', n_srm,
                                  'ibu', n_ibu, 'attenuation_pct', attenuation, 'missing', missing);
    results := jsonb_build_array(
        app.check_rule_1(items), app.check_rule_2(items), app.check_rule_3(items),
        app.check_rule_4(items), app.check_rule_5(items), app.check_rule_6(items),
        app.check_rule_8(items, recipe), app.check_rule_9(items, recipe),
        app.check_rule_10(items, recipe, numbers), app.check_rule_11(items, numbers),
        app.check_rule_12(items), app.check_rule_13(items, recipe));

    return jsonb_build_object(
        'calc_version', app.calc_version(),
        'numbers', numbers,
        'results', results);
end;
$$;
