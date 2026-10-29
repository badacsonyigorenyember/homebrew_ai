-- Step 13, mash steps, volumes and boil schedule (docs/work/m7-process, Task 5): the neutral mash
-- rests, the strike water temperature, and the boil and whirlpool schedule. Nothing here is decided
-- again: the mash temperature and the boil are step 10's (brief R3, A7). No LLM.
-- Needs db/050_water.sql (app.water_volumes, app.mashed_grist).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/051_mash_boil.sql
-- Idempotent: safe to re-run.

-- The mash steps in order, [{name, temp_c, minutes, why, source}]: the neutral rests whose trigger
-- holds, the saccharification rest at mash_c, the mash-out. Every rest sits below the starch range, so
-- rule 10's FG model (the temperature of mash_c) is unchanged. grist is app.mashed_grist's output.
-- doc-calc.md §9, all figures How to Brew's:
--   ferulic acid rest 40 C / 30 min for Weissbier, Dunkles Weissbier and Weizenbock (10A-10C; ch. 17 p. 264);
--   beta-glucan rest 45 C / 20 min when adjuncts are above 20 % of the grist by mass (ch. 16 p. 244);
--   a weizen that also triggers the beta-glucan rest keeps the one ferulic rest;
--   saccharification rest 60 min (Table 17.1 p. 263); mash-out 77 C (ch. 16 p. 252), 10 min unsourced.
create or replace function app.mash_rests(style_code text, grist jsonb, mash_c numeric)
returns jsonb
language plpgsql
immutable
as $$
declare
    total_kg numeric;
    adjunct_kg numeric;
    steps jsonb := '[]'::jsonb;
begin
    if mash_c is null then
        raise exception 'mash_rests: no mash temperature';
    end if;
    if grist is null or jsonb_typeof(grist) <> 'array' then
        raise exception 'mash_rests: grist must be an array';
    end if;
    select coalesce(sum((x ->> 'kg')::numeric), 0),
           coalesce(sum((x ->> 'kg')::numeric) filter (where x ->> 'role' = 'adjunct'), 0)
      into total_kg, adjunct_kg
    from jsonb_array_elements(grist) as x;

    if style_code in ('10A', '10B', '10C') then
        steps := steps || jsonb_build_object('name', 'ferulic acid rest', 'temp_c', 40, 'minutes', 30,
            'why', format('%s is a German wheat beer: a rest at 40 C builds ferulic acid, the clove character', style_code),
            'source', 'How to Brew ch. 17 p. 264, Table 17.2 p. 265');
    elsif total_kg > 0 and adjunct_kg / total_kg > 0.20 then
        steps := steps || jsonb_build_object('name', 'beta-glucan rest', 'temp_c', 45, 'minutes', 20,
            'why', format('adjuncts (flaked or unmalted grain) are %s %% of the grist, above 20 %%: a rest at 45 C breaks down beta-glucans',
                          round(adjunct_kg / total_kg * 100, 1)),
            'source', 'How to Brew ch. 16 p. 244, Table 16.2 p. 249');
    end if;
    steps := steps || jsonb_build_object('name', 'saccharification rest', 'temp_c', mash_c, 'minutes', 60,
        'why', format('step 10''s mash temperature %s C, which sets the fermentability', mash_c),
        'source', 'How to Brew Table 17.1 p. 263 (30-60 min); the temperature is step 10''s');
    steps := steps || jsonb_build_object('name', 'mash-out', 'temp_c', 77, 'minutes', 10,
        'why', 'raise the mash to 77 C before lautering',
        'source', 'How to Brew ch. 16 p. 252 (77 C); the 10 minutes are unsourced');
    return steps;
end
$$;

-- The strike water temperature of a single infusion, How to Brew ch. 17 p. 268, Dry Grain Infusion
-- Calculations: Tw = (S / R)(T2 - T1) + T2 with S = 0.4 (grain heat capacity relative to water) and
-- R = Rv x 0.985 kg/L (Table 17.3 p. 266-267). ratio_l_kg is Rv in L/kg, grain_c T1, target_c T2.
-- The mash tun is taken as pre-heated and without heat loss, as in the book. Rounded to 0.1 C.
-- doc-calc.md §8 (the book's example gives 73.2 C).
create or replace function app.strike_temp(ratio_l_kg numeric, grain_c numeric, target_c numeric)
returns numeric
language plpgsql
immutable
as $$
begin
    if ratio_l_kg is null or ratio_l_kg <= 0 then
        raise exception 'strike_temp: the water-to-grist ratio must be above 0, got %', ratio_l_kg;
    end if;
    if grain_c is null or target_c is null then
        raise exception 'strike_temp: grain and target temperatures are needed';
    end if;
    return round(0.4 / (0.985 * ratio_l_kg) * (target_c - grain_c) + target_c, 1);
end
$$;

-- Step 13. profile is step 0's, targets step 4's (the style code), step10 step 10's output.
--   mash: {mash_c, steps, volumes (app.water_volumes, the same step 12 doses for), strike_c, grain_c,
--          additions}: mash_c is step 10's; strike_c is the strike temperature for the first mash
--          step; grain_c is 21 C (How to Brew p. 268: grain at room temperature); additions are the
--          extras step 10 puts in the mash.
--   boil: {boil_min, because, additions, whirlpool}: boil_min and because are step 10's boil as is;
--          additions are the boil hops and boil extras by minute, largest first (a hop's `minutes` and
--          an extra's time_min are minutes before the end of the boil; an extra with no time goes in at
--          the start of the boil); whirlpool are the whirlpool hops and extras by their minutes.
-- Dry hops and fermentation extras belong to step 14, packaging extras to step 15.
create or replace function app.step13_mash_boil(profile jsonb, targets jsonb, step10 jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    grain_c constant numeric := 21;
    style_code text := targets -> 'style' ->> 'code';
    mash_c numeric := (step10 ->> 'mash_c')::numeric;
    boil_min numeric := (step10 #>> '{boil,boil_min}')::numeric;
    vol jsonb;
    steps jsonb;
    strike_c numeric;
    additions jsonb;
    whirlpool jsonb;
    mash_extras jsonb;
begin
    if style_code is null then
        raise exception 'step13_mash_boil: targets has no style code';
    end if;
    if mash_c is null or boil_min is null then
        raise exception 'step13_mash_boil: step 10 has no mash_c or boil';
    end if;
    vol := app.water_volumes(profile, step10);
    steps := app.mash_rests(style_code, app.mashed_grist(step10), mash_c);
    strike_c := app.strike_temp((vol ->> 'ratio_l_kg')::numeric, grain_c, (steps -> 0 ->> 'temp_c')::numeric);

    select coalesce(jsonb_agg(jsonb_build_object('at_min', at_min, 'kind', kind, 'ingredient_id', ingredient_id,
                                                  'name', name, 'usage', 'boil', 'g', g)
                              order by at_min desc, kind desc, name), '[]'::jsonb)
      into additions
    from (
        select (h ->> 'minutes')::numeric as at_min, 'hop' as kind, (h ->> 'ingredient_id')::bigint as ingredient_id,
               h ->> 'name' as name, (h ->> 'g')::numeric as g
        from jsonb_array_elements(coalesce(step10 -> 'hops', '[]'::jsonb)) h
        where h ->> 'usage' = 'boil'
        union all
        select coalesce((e ->> 'time_min')::numeric, boil_min), 'extra', (e ->> 'ingredient_id')::bigint,
               e ->> 'name', (e ->> 'g')::numeric
        from jsonb_array_elements(coalesce(step10 -> 'extras', '[]'::jsonb)) e
        where e ->> 'usage' = 'boil'
    ) t;

    select coalesce(jsonb_agg(jsonb_build_object('minutes', minutes, 'kind', kind, 'ingredient_id', ingredient_id,
                                                  'name', name, 'usage', 'whirlpool', 'g', g)
                              order by minutes desc nulls last, kind desc, name), '[]'::jsonb)
      into whirlpool
    from (
        select (h ->> 'minutes')::numeric as minutes, 'hop' as kind, (h ->> 'ingredient_id')::bigint as ingredient_id,
               h ->> 'name' as name, (h ->> 'g')::numeric as g
        from jsonb_array_elements(coalesce(step10 -> 'hops', '[]'::jsonb)) h
        where h ->> 'usage' = 'whirlpool'
        union all
        select (e ->> 'time_min')::numeric, 'extra', (e ->> 'ingredient_id')::bigint, e ->> 'name', (e ->> 'g')::numeric
        from jsonb_array_elements(coalesce(step10 -> 'extras', '[]'::jsonb)) e
        where e ->> 'usage' = 'whirlpool'
    ) t;

    select coalesce(jsonb_agg(jsonb_build_object('ingredient_id', (e ->> 'ingredient_id')::bigint, 'name', e ->> 'name',
                                                  'usage', 'mash', 'time_min', e -> 'time_min', 'g', (e ->> 'g')::numeric)
                              order by e ->> 'name'), '[]'::jsonb)
      into mash_extras
    from jsonb_array_elements(coalesce(step10 -> 'extras', '[]'::jsonb)) e
    where e ->> 'usage' = 'mash';

    return jsonb_build_object(
        'mash', jsonb_build_object('mash_c', mash_c, 'steps', steps, 'volumes', vol, 'strike_c', strike_c,
                                   'grain_c', grain_c, 'additions', mash_extras),
        'boil', jsonb_build_object('boil_min', boil_min, 'because', step10 #>> '{boil,because}',
                                   'additions', additions, 'whirlpool', whirlpool),
        'values_used', jsonb_build_array(
            jsonb_build_object('what', 'mash temperature and boil', 'because',
                format('copied from step 10: mash %s C, boil %s min', mash_c, boil_min),
                'source', 'step 10 (brief R3, A7)'),
            jsonb_build_object('what', 'mash steps', 'because',
                format('%s step(s): %s', jsonb_array_length(steps),
                       (select string_agg(s ->> 'name' || ' ' || (s ->> 'temp_c') || ' C', ', ') from jsonb_array_elements(steps) s)),
                'source', 'How to Brew ch. 16 p. 244, 252, ch. 17 p. 263-265 (doc-calc.md §9)'),
            jsonb_build_object('what', 'strike water temperature', 'because',
                format('%s C for %s L/kg, grain at %s C, first step at %s C', strike_c, vol ->> 'ratio_l_kg', grain_c, steps -> 0 ->> 'temp_c'),
                'source', 'How to Brew ch. 17 p. 267-269 (doc-calc.md §8)')));
end
$$;
