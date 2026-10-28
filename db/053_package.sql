-- Step 15, carbonation and priming sugar (docs/work/m7-process, Task 7): the CO2 volumes from the style's
-- family (ref.beer_style.co2_vol, db/049_process_ref.sql), the table sugar to prime with, and step 10's
-- packaging extras. How to Brew (HTB) ch. 10 p. 155-161, doc-calc.md §14. No LLM.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/053_package.sql
-- Idempotent: safe to re-run.

-- HTB Table 10.3 (p. 161): for a beer temperature in whole degrees C, 5-30, the gas volume constant
-- (litres per mol of CO2) and the CO2 already dissolved in the beer, in volumes. The temperature is the
-- highest the beer reached after fermentation (p. 158). A fractional temperature takes the nearest row.
create or replace function app.residual_co2(temp_c numeric)
returns jsonb
language plpgsql
immutable
as $$
declare
    t integer := round(temp_c);
    r record;
begin
    select * into r from (values
        (5, 23.1, 1.32), (6, 23.2, 1.27), (7, 23.3, 1.23), (8, 23.4, 1.19), (9, 23.5, 1.16), (10, 23.5, 1.12),
        (11, 23.6, 1.08), (12, 23.7, 1.05), (13, 23.8, 1.02), (14, 23.9, 0.99), (15, 24.0, 0.96), (16, 24.0, 0.93),
        (17, 24.1, 0.90), (18, 24.2, 0.87), (19, 24.3, 0.84), (20, 24.4, 0.82), (21, 24.5, 0.80), (22, 24.5, 0.77),
        (23, 24.6, 0.75), (24, 24.7, 0.73), (25, 24.8, 0.72), (26, 24.9, 0.70), (27, 25.0, 0.68), (28, 25.0, 0.67),
        (29, 25.1, 0.65), (30, 25.2, 0.64)) as t10_3(c, gas, resid)
     where c = t;
    if not found then
        raise exception 'residual_co2: % C is outside HTB Table 10.3 (5 to 30 C)', temp_c;
    end if;
    return jsonb_build_object('temp_c', r.c, 'gas_l_mol', r.gas, 'residual_vol', r.resid);
end
$$;

-- Table sugar (sucrose, 342.3 g/mol, 4 mol CO2 per mol, as HTB p. 156-157) to raise litres of
-- beer from its residual CO2 to co2_vol volumes: (target - residual) x litres x 342.3 / 4 / gas volume.
-- Not rounded here.
create or replace function app.priming_sugar_g(co2_vol numeric, temp_c numeric, volume_l numeric)
returns numeric
language sql
immutable
as $$
    select greatest(co2_vol - (r ->> 'residual_vol')::numeric, 0) * volume_l * (342.3 / 4) / (r ->> 'gas_l_mol')::numeric
    from (select app.residual_co2(temp_c) r) x
$$;

-- Step 15. co2: the middle of the style's family range (from 'style', with the family and its basis label),
-- or 2.5 volumes when the style has none (HTB p. 155, from 'default'). priming: grams of table sugar for
-- step 10's batch volume at step 14's max_temp_c, to the gram. extras: step 10's packaging extras.
create or replace function app.step15_package(targets jsonb, step10 jsonb, step14 jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    style_code text := targets -> 'style' ->> 'code';
    litres numeric := (step10 #>> '{batch,volume_l}')::numeric;
    temp numeric := (step14 ->> 'max_temp_c')::numeric;
    b record;
    vol numeric;
    co2 jsonb;
    res jsonb;
    sugar numeric;
begin
    if style_code is null or litres is null or temp is null then
        raise exception 'step15_package: targets have no style code, or step 10 no batch volume, or step 14 no max_temp_c';
    end if;
    select co2_family, co2_vol, co2_basis into b from ref.beer_style where code = style_code;
    if not found then
        raise exception 'step15_package: no style %', style_code;
    end if;
    if b.co2_vol is null then
        vol := 2.5;
        co2 := jsonb_build_object('volumes', vol, 'basis', null, 'range', null, 'family', null, 'from', 'default',
            'source', 'How to Brew p. 155: medium carbonation, about 2.5 volumes, suits most ales and lagers (doc-calc.md §14)');
    else
        vol := round((lower(b.co2_vol) + upper(b.co2_vol)) / 2, 2);
        co2 := jsonb_build_object('volumes', vol, 'basis', b.co2_basis,
            'range', jsonb_build_array(lower(b.co2_vol), upper(b.co2_vol)), 'family', b.co2_family, 'from', 'style',
            'source', format('How to Brew p. 159: the middle of the %s family''s %s-%s volumes (doc-calc.md §14)',
                            b.co2_family, lower(b.co2_vol), upper(b.co2_vol)));
    end if;
    res := app.residual_co2(temp);
    sugar := app.priming_sugar_g(vol, temp, litres);

    return jsonb_build_object(
        'co2', co2,
        'priming', jsonb_build_object(
            'sugar', 'table sugar (sucrose)', 'g', round(sugar), 'g_per_l', round(sugar / litres, 2),
            'temp_c', (res ->> 'temp_c')::numeric, 'residual_vol', (res ->> 'residual_vol')::numeric, 'volume_l', litres,
            'source', 'How to Brew p. 156-161, Table 10.3: (target - residual CO2) x litres x 85.575 / gas volume, residual and gas volume at the highest temperature after fermentation (doc-calc.md §14)'),
        'extras', (select coalesce(jsonb_agg(jsonb_build_object('ingredient_id', (e ->> 'ingredient_id')::bigint, 'name', e ->> 'name',
                                                                 'g', (e ->> 'g')::numeric) order by e ->> 'name'), '[]'::jsonb)
                     from jsonb_array_elements(coalesce(step10 -> 'extras', '[]'::jsonb)) e where e ->> 'usage' = 'package'));
end
$$;
