-- Water maths for step 12 (docs/work/m7-process, Task 3): ions of a salt addition, residual
-- alkalinity, the strike and sparge volumes, the sulfate and chloride aim, gypsum and calcium
-- chloride, the alkalinity dose, the malt acidity and the mash pH estimate. Pure maths, no LLM.
-- app.step12_water (Task 4) puts them together. Every function comment names its doc-calc.md
-- section and the book page.
-- Needs db/030_maths.sql (app.preboil_volume, app.ebc_mid), db/049_process_ref.sql
-- (ref.water_profile) and ref.water_salt (db/010).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/050_water.sql
-- Idempotent: safe to re-run.

-- Ions of a salt addition in mg/L. salts is [{ingredient_id, g}], volume_l the water it is stirred
-- into. Returns {ca, mg, na, so4, cl, hco3, oh, co3}, each the sum over the salts of
-- g / volume_l x the mg/L per g/L that ref.water_salt stores. doc-calc.md §1 (Water Table 17, p. 118).
create or replace function app.salt_ions(salts jsonb, volume_l numeric)
returns jsonb
language plpgsql
stable
as $$
declare
    unknown bigint;
begin
    if volume_l is null or volume_l <= 0 then
        raise exception 'salt_ions: volume must be above 0, got %', volume_l;
    end if;
    if salts is null or jsonb_typeof(salts) <> 'array' then
        raise exception 'salt_ions: salts must be an array of {ingredient_id, g}';
    end if;
    if exists (select 1 from jsonb_to_recordset(salts) as x(ingredient_id bigint, g numeric) where x.g is null or x.g < 0) then
        raise exception 'salt_ions: every salt needs a gram amount of 0 or more';
    end if;
    select x.ingredient_id into unknown
    from jsonb_to_recordset(salts) as x(ingredient_id bigint, g numeric)
    where not exists (select 1 from ref.water_salt s where s.ingredient_id = x.ingredient_id) limit 1;
    if found then
        raise exception 'salt_ions: ingredient % is not a water salt', unknown;
    end if;
    return (
        select jsonb_build_object(
            'ca',   coalesce(sum(x.g * coalesce((s.ion_mg_per_l_per_g ->> 'Ca')::numeric, 0)), 0) / volume_l,
            'mg',   coalesce(sum(x.g * coalesce((s.ion_mg_per_l_per_g ->> 'Mg')::numeric, 0)), 0) / volume_l,
            'na',   coalesce(sum(x.g * coalesce((s.ion_mg_per_l_per_g ->> 'Na')::numeric, 0)), 0) / volume_l,
            'so4',  coalesce(sum(x.g * coalesce((s.ion_mg_per_l_per_g ->> 'SO4')::numeric, 0)), 0) / volume_l,
            'cl',   coalesce(sum(x.g * coalesce((s.ion_mg_per_l_per_g ->> 'Cl')::numeric, 0)), 0) / volume_l,
            'hco3', coalesce(sum(x.g * coalesce((s.ion_mg_per_l_per_g ->> 'HCO3')::numeric, 0)), 0) / volume_l,
            'oh',   coalesce(sum(x.g * coalesce((s.ion_mg_per_l_per_g ->> 'OH')::numeric, 0)), 0) / volume_l,
            'co3',  coalesce(sum(x.g * coalesce((s.ion_mg_per_l_per_g ->> 'CO3')::numeric, 0)), 0) / volume_l)
        from jsonb_to_recordset(salts) as x(ingredient_id bigint, g numeric)
        join ref.water_salt s on s.ingredient_id = x.ingredient_id
    );
end
$$;

-- Two waters' ions added together (a source water plus a salt addition). A missing ion counts as 0.
create or replace function app.add_ions(a jsonb, b jsonb)
returns jsonb
language sql
immutable
as $$
    select jsonb_object_agg(k, coalesce((a ->> k)::numeric, 0) + coalesce((b ->> k)::numeric, 0))
    from unnest(array['ca', 'mg', 'na', 'so4', 'cl', 'hco3', 'oh', 'co3']) as k
$$;

-- Kolbach residual alkalinity. Alkalinity as CaCO3 from HCO3, CO3 and OH (ion x 50 / equivalent
-- weight), RA = alkalinity - Ca / 1.4 - Mg / 1.7 (ppm as CaCO3), mEq/L = ppm / 50.
-- doc-calc.md §2; How to Brew ch. 21 p. 342, Water ch. 4 p. 53-54.
create or replace function app.residual_alkalinity(ions jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    alk numeric;
    ra numeric;
begin
    if ions is null or jsonb_typeof(ions) <> 'object' then
        raise exception 'residual_alkalinity: ions must be an object';
    end if;
    alk := coalesce((ions ->> 'hco3')::numeric, 0) * 50 / 61.017
         + coalesce((ions ->> 'co3')::numeric, 0) * 50 / 30.005
         + coalesce((ions ->> 'oh')::numeric, 0) * 50 / 17.007;
    ra := alk - coalesce((ions ->> 'ca')::numeric, 0) / 1.4 - coalesce((ions ->> 'mg')::numeric, 0) / 1.7;
    return jsonb_build_object('alkalinity_ppm', alk, 'ra_ppm', ra, 'ra_meq_l', ra / 50);
end
$$;

-- The mashed grist of step 10: [{ingredient_id, name, kg, role, ebc}] for the fermentables that are
-- not sugar (sugars are not mashed). ebc is the middle of the ingredient's colour range (null: 0).
-- Used by app.water_volumes and, in Task 4, by step 12 for the mash pH.
create or replace function app.mashed_grist(step10 jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    missing bigint;
begin
    if step10 is null or jsonb_typeof(step10 -> 'fermentables') <> 'array' then
        raise exception 'mashed_grist: step 10 has no fermentables';
    end if;
    select (x ->> 'ingredient_id')::bigint into missing
    from jsonb_array_elements(step10 -> 'fermentables') as x
    where not exists (select 1 from ref.fermentable f where f.ingredient_id = (x ->> 'ingredient_id')::bigint) limit 1;
    if found then
        raise exception 'mashed_grist: ingredient % is not a ref fermentable', missing;
    end if;
    return coalesce((
        select jsonb_agg(jsonb_build_object(
                   'ingredient_id', f.ingredient_id, 'name', x.value ->> 'name', 'kg', (x.value ->> 'kg')::numeric,
                   'role', f.role, 'ebc', coalesce(app.ebc_mid(f.ebc), 0)) order by x.ord)
        from jsonb_array_elements(step10 -> 'fermentables') with ordinality as x(value, ord)
        join ref.fermentable f on f.ingredient_id = (x.value ->> 'ingredient_id')::bigint
        where f.role <> 'sugar'
    ), '[]'::jsonb);
end
$$;

-- Strike, sparge and total water. Total = app.preboil_volume + mashed kg x grain absorption;
-- strike = mashed kg x 3 L/kg; sparge = total - strike, and when that is below 0 all the water
-- is strike and sparge is 0. Sugars count in neither. Litres to 2 decimals, so strike + sparge =
-- total exactly. doc-calc.md §8: the ratio is How to Brew ch. 17 p. 262 (2.5-4 L/kg) and its
-- single-infusion example p. 267-269 (3 L/kg); the volumes are the brewer profile's arithmetic.
create or replace function app.water_volumes(profile jsonb, step10 jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    ratio constant numeric := 3;
    grist_kg numeric;
    preboil numeric;
    absorbed numeric;
    total numeric;
    strike numeric;
    sparge numeric;
    because text;
begin
    if profile is null or (profile ->> 'grain_abs_l_kg') is null then
        raise exception 'water_volumes: the profile has no grain_abs_l_kg';
    end if;
    if step10 is null or step10 -> 'batch' is null or (step10 #>> '{boil,boil_min}') is null then
        raise exception 'water_volumes: step 10 has no batch or boil';
    end if;
    select coalesce(sum((x ->> 'kg')::numeric), 0) into grist_kg from jsonb_array_elements(app.mashed_grist(step10)) as x;
    if grist_kg <= 0 then
        raise exception 'water_volumes: the recipe has no mashed grist';
    end if;
    preboil := app.preboil_volume((step10 #>> '{batch,volume_l}')::numeric, (step10 #>> '{boil,boil_min}')::numeric,
                                  (step10 #>> '{batch,boil_off_l_h}')::numeric, (step10 #>> '{batch,losses_l}')::numeric);
    absorbed := round(grist_kg * (profile ->> 'grain_abs_l_kg')::numeric, 2);
    preboil := round(preboil, 2);
    total := preboil + absorbed;
    strike := round(grist_kg * ratio, 2);
    if strike > total then
        because := format('strike water %s L (%s kg x %s L/kg) is more than the total %s L, so all the water is strike and there is no sparge',
                          strike, grist_kg, ratio, total);
        strike := total;
        sparge := 0;
    else
        sparge := total - strike;
        because := format('strike %s L = %s kg x %s L/kg; total %s L = pre-boil %s L + %s L absorbed by the grain; sparge is the rest',
                          strike, grist_kg, ratio, total, preboil, absorbed);
    end if;
    return jsonb_build_object('grist_kg', grist_kg, 'ratio_l_kg', ratio, 'preboil_l', preboil, 'absorbed_l', absorbed,
                              'total_l', total, 'strike_l', strike, 'sparge_l', sparge, 'because', because);
end
$$;

-- The sulfate, chloride and calcium aim inside a Water Table 18/19 row (row_code is a
-- ref.water_profile code). Sulfate and chloride start at the middle of their ranges. Sulfate-side
-- hints (bitter, hoppy, dry, crisp; How to Brew p. 133) move sulfate to 87.5 % and chloride to
-- 12.5 % of their ranges, chloride-side hints (juicy, malty, full, chewy) the reverse; both sides at
-- once leave the middle. Calcium is the row's floor. alkalinity and ra are the row's references,
-- never dosing targets. HTB Table 8.1 / p. 135 caps: sulfate <= 400, chloride <= 150, together <= 500.
-- doc-calc.md §5; the 87.5 / 12.5 positions are RECIPE-ROADMAP §7's.
create or replace function app.water_aim(row_code text, hints text[])
returns jsonb
language plpgsql
stable
as $$
declare
    r ref.water_profile;
    so4_hints constant text[] := array['bitter', 'hoppy', 'dry', 'crisp'];
    cl_hints constant text[] := array['juicy', 'malty', 'full', 'chewy'];
    so4_side boolean;
    cl_side boolean;
    so4_pos numeric := 0.5;
    cl_pos numeric := 0.5;
    so4_aim numeric;
    cl_aim numeric;
    moved text[] := '{}';
    h text;
begin
    select * into r from ref.water_profile where code = row_code;
    if not found then
        raise exception 'water_aim: no water row %', row_code;
    end if;
    so4_side := coalesce(hints && so4_hints, false);
    cl_side := coalesce(hints && cl_hints, false);
    foreach h in array coalesce(hints, '{}') loop
        if h = any (so4_hints) then
            moved := moved || (h || ': sulfate side (How to Brew p. 133)');
        elsif h = any (cl_hints) then
            moved := moved || (h || ': chloride side (How to Brew p. 133)');
        end if;
    end loop;
    if so4_side and cl_side then
        moved := moved || 'sulfate-side and chloride-side hints together: the aims stay at the middle of the ranges'::text;
    elsif so4_side then
        so4_pos := 0.875;
        cl_pos := 0.125;
    elsif cl_side then
        so4_pos := 0.125;
        cl_pos := 0.875;
    end if;
    so4_aim := lower(r.so4) + so4_pos * (upper(r.so4) - lower(r.so4));
    cl_aim := lower(r.cl) + cl_pos * (upper(r.cl) - lower(r.cl));
    -- the rows stay under HTB's caps (a test checks every row at both extremes); this guards a wrong row
    if so4_aim > 400 or cl_aim > 150 or so4_aim + cl_aim > 500 then
        raise exception 'water_aim: row % gives sulfate % and chloride %, above How to Brew''s caps (400, 150, 500 together)',
                        row_code, so4_aim, cl_aim;
    end if;
    return jsonb_build_object(
        'ca', lower(r.ca), 'so4', so4_aim, 'cl', cl_aim,
        'alkalinity', jsonb_build_object('low', lower(r.alkalinity), 'high', upper(r.alkalinity)),
        'ra', jsonb_build_object('low', lower(r.ra), 'high', upper(r.ra)),
        'moved_by', to_jsonb(moved));
end
$$;

-- Notes for every ion of a water that is outside the row's range, as "outside_row: ..." texts.
-- The row's calcium, alkalinity, sulfate, chloride and RA ranges are references: a water outside
-- them is reported and never corrected (doc-calc.md §3, §6; How to Brew p. 363).
create or replace function app.outside_row(ions jsonb, row_code text)
returns text[]
language plpgsql
stable
as $$
declare
    r ref.water_profile;
    ra jsonb := app.residual_alkalinity(ions);
    notes text[] := '{}';
    item record;
begin
    select * into r from ref.water_profile where code = row_code;
    if not found then
        raise exception 'outside_row: no water row %', row_code;
    end if;
    for item in
        select * from (values
            ('calcium', (ions ->> 'ca')::numeric, r.ca, 'mg/L'),
            ('alkalinity', (ra ->> 'alkalinity_ppm')::numeric, r.alkalinity, 'mg/L as CaCO3'),
            ('sulfate', (ions ->> 'so4')::numeric, r.so4, 'mg/L'),
            ('chloride', (ions ->> 'cl')::numeric, r.cl, 'mg/L'),
            ('residual alkalinity', (ra ->> 'ra_ppm')::numeric, r.ra, 'mg/L as CaCO3')
        ) as v(what, val, rng, unit)
    loop
        if not item.rng @> round(item.val, 1) then
            notes := notes || format('outside_row: %s %s %s is %s the row''s %s (a reference, not corrected)',
                                     item.what, round(item.val, 1), item.unit,
                                     case when round(item.val, 1) < lower(item.rng) then 'below' else 'above' end, item.rng);
        end if;
    end loop;
    return notes;
end
$$;

-- Gypsum for sulfate and calcium chloride for chloride, never below 0. source is the source water's
-- ions {ca, mg, na, so4, cl, hco3}; aim is app.water_aim's output. Each salt is (aim - source) /
-- mg/L per g/L from ref.water_salt. When calcium is then below the row's floor both salts rise in
-- proportion until it is reached or sulfate or chloride reaches the row's maximum (or HTB's caps:
-- 400, 150, 500 together); then "calcium below the row" is said. Calcium above the row's maximum is
-- reported, not corrected. The same g/L goes in the strike and the sparge water; each amount is
-- rounded to 0.1 g and the ions are recomputed from the rounded grams. No alkalinity here
-- (app.alkalinity_dose adds it to the strike water). doc-calc.md §6; How to Brew Table 8.1 p. 134,
-- p. 135; Water p. 117.
create or replace function app.salt_additions(source jsonb, aim jsonb, row_code text, strike_l numeric, sparge_l numeric)
returns jsonb
language plpgsql
stable
as $$
declare
    r ref.water_profile;
    gyp_id bigint; gyp_name text; gyp_ca numeric; gyp_so4 numeric;
    cac_id bigint; cac_name text; cac_ca numeric; cac_cl numeric;
    gyp_gl numeric;   -- g/L gypsum
    cac_gl numeric;   -- g/L calcium chloride
    ca_now numeric;
    salt_ca numeric;
    f_need numeric;
    f_max numeric;
    f numeric;
    so4_max numeric;
    cl_max numeric;
    salts jsonb := '[]'::jsonb;
    s_gyp numeric; p_gyp numeric; s_cac numeric; p_cac numeric;
    strike_salts jsonb; sparge_salts jsonb;
    strike_ions jsonb; sparge_ions jsonb;
    notes text[] := '{}';
begin
    select * into r from ref.water_profile where code = row_code;
    if not found then
        raise exception 'salt_additions: no water row %', row_code;
    end if;
    if strike_l is null or strike_l <= 0 or sparge_l is null or sparge_l < 0 then
        raise exception 'salt_additions: strike water must be above 0 and sparge water 0 or more';
    end if;
    select i.id, i.name, (s.ion_mg_per_l_per_g ->> 'Ca')::numeric, (s.ion_mg_per_l_per_g ->> 'SO4')::numeric
      into gyp_id, gyp_name, gyp_ca, gyp_so4
    from ref.water_salt s join ref.ingredient i on i.id = s.ingredient_id where i.name = 'gypsum';
    select i.id, i.name, (s.ion_mg_per_l_per_g ->> 'Ca')::numeric, (s.ion_mg_per_l_per_g ->> 'Cl')::numeric
      into cac_id, cac_name, cac_ca, cac_cl
    from ref.water_salt s join ref.ingredient i on i.id = s.ingredient_id where i.name = 'calcium chloride';

    gyp_gl := greatest(0, ((aim ->> 'so4')::numeric - coalesce((source ->> 'so4')::numeric, 0)) / gyp_so4);
    cac_gl := greatest(0, ((aim ->> 'cl')::numeric - coalesce((source ->> 'cl')::numeric, 0)) / cac_cl);

    ca_now := coalesce((source ->> 'ca')::numeric, 0) + gyp_gl * gyp_ca + cac_gl * cac_ca;
    if ca_now < lower(r.ca) then
        salt_ca := gyp_gl * gyp_ca + cac_gl * cac_ca;
        if salt_ca = 0 then
            notes := notes || format('calcium below the row: %s mg/L against the row''s minimum %s, and no salt is added to raise it',
                                     round(ca_now, 1), lower(r.ca));
        else
            f_need := 1 + (lower(r.ca) - ca_now) / salt_ca;
            so4_max := least(upper(r.so4), 400);
            cl_max := least(upper(r.cl), 150);
            f_max := f_need;
            if gyp_gl > 0 then
                f_max := least(f_max, (so4_max - coalesce((source ->> 'so4')::numeric, 0)) / (gyp_gl * gyp_so4));
            end if;
            if cac_gl > 0 then
                f_max := least(f_max, (cl_max - coalesce((source ->> 'cl')::numeric, 0)) / (cac_gl * cac_cl));
            end if;
            f_max := least(f_max, (500 - coalesce((source ->> 'so4')::numeric, 0) - coalesce((source ->> 'cl')::numeric, 0))
                                  / (gyp_gl * gyp_so4 + cac_gl * cac_cl));
            f := greatest(1, least(f_need, f_max));
            gyp_gl := gyp_gl * f;
            cac_gl := cac_gl * f;
            if f < f_need then
                notes := notes || format('calcium below the row: sulfate or chloride reached its maximum first (calcium %s mg/L against the row''s minimum %s)',
                                         round(coalesce((source ->> 'ca')::numeric, 0) + gyp_gl * gyp_ca + cac_gl * cac_ca, 1), lower(r.ca));
            else
                notes := notes || format('both salts raised by x%s to bring calcium to the row''s minimum %s mg/L', round(f, 3), lower(r.ca));
            end if;
        end if;
    end if;

    -- grams for each water, to 0.1 g; the sparge water gets the same g/L
    s_gyp := round(gyp_gl * strike_l, 1);  p_gyp := round(gyp_gl * sparge_l, 1);
    s_cac := round(cac_gl * strike_l, 1);  p_cac := round(cac_gl * sparge_l, 1);
    if s_gyp + p_gyp > 0 then
        salts := salts || jsonb_build_object('ingredient_id', gyp_id, 'name', gyp_name, 'aims_at', 'sulfate',
                                             'strike_g', s_gyp, 'sparge_g', p_gyp, 'total_g', s_gyp + p_gyp);
    end if;
    if s_cac + p_cac > 0 then
        salts := salts || jsonb_build_object('ingredient_id', cac_id, 'name', cac_name, 'aims_at', 'chloride',
                                             'strike_g', s_cac, 'sparge_g', p_cac, 'total_g', s_cac + p_cac);
    end if;

    strike_salts := jsonb_build_array(jsonb_build_object('ingredient_id', gyp_id, 'g', s_gyp),
                                      jsonb_build_object('ingredient_id', cac_id, 'g', s_cac));
    strike_ions := app.add_ions(source, app.salt_ions(strike_salts, strike_l));
    if sparge_l > 0 then
        sparge_salts := jsonb_build_array(jsonb_build_object('ingredient_id', gyp_id, 'g', p_gyp),
                                          jsonb_build_object('ingredient_id', cac_id, 'g', p_cac));
        sparge_ions := app.add_ions(source, app.salt_ions(sparge_salts, sparge_l));
    else
        sparge_ions := app.add_ions(source, '{}'::jsonb);
    end if;

    notes := notes || app.outside_row(strike_ions, row_code);
    return jsonb_build_object(
        'salts', salts,
        'none_needed', jsonb_array_length(salts) = 0,
        'strike_water', jsonb_build_object('ions', strike_ions) || app.residual_alkalinity(strike_ions),
        'sparge_water', jsonb_build_object('ions', sparge_ions) || app.residual_alkalinity(sparge_ions),
        'notes', to_jsonb(notes));
end
$$;

-- Acidity or alkalinity of a mashed fermentable to mash pH 5.4, in mEq per kg (positive: alkaline,
-- negative: acid), and the buffer. How to Brew Table 21.4 p. 351 (Briess data): the non-roast row
-- nearest in degrees Lovibond (EBC / 1.97, HTB p. 234-235; a tie goes to the row listed first), picked
-- by role: a crystal malt among the five Caramel rows, base, kilned and adjunct among the others; every
-- roast is one class, -42.98 mEq/kg, the mean of the five roast rows. Flaked and unmalted adjuncts
-- count as base malt (Bru'n Water, HTB is silent). Buffer: 40 mEq per pH per kg (HTB p. 342's
-- 200/Rv ppm per 0.1 pH). A sugar is not mashed: 0 and no buffer. doc-calc.md §7.
create or replace function app.malt_acidity(role text, ebc numeric)
returns jsonb
language plpgsql
immutable
as $$
declare
    page constant text := 'How to Brew Table 21.4, p. 351';
    lovibond numeric;
    picked record;
begin
    if role is null or role not in ('base', 'kilned', 'crystal', 'roast', 'adjunct', 'sugar') then
        raise exception 'malt_acidity: unknown role %', role;
    end if;
    if role = 'sugar' then
        return jsonb_build_object('class', 'sugar (not mashed)', 'meq_kg', 0, 'buffer', 0, 'page', page);
    end if;
    if role = 'roast' then
        return jsonb_build_object('class', 'roast (mean of the five roast rows)', 'meq_kg', -42.98, 'buffer', 40, 'page', page);
    end if;
    if ebc is null or ebc < 0 then
        raise exception 'malt_acidity: colour must be 0 or more, got %', ebc;
    end if;
    lovibond := ebc / 1.97;
    select v.name, v.meq into picked
    from (values
        (1,  'Pilsen Malt',        1.5,   9.2), (2,  'Brewers Malt',       1.9,   5.0),
        (3,  'Pale Ale Malt',      2.9,   3.4), (4,  'Red Wheat Malt',     2.8,  11.1),
        (5,  'Goldpils Vienna',    3.5,   7.2), (6,  'Ashburne Mild',      4.4,   2.6),
        (7,  'Bonlander Munich',   12.0,  2.6), (8,  'Aromatic Munich',    16.0,  0.0),
        (9,  'Victory',            28.0, -0.9), (10, 'Caramel 20L',        19.0, -21.3),
        (11, 'Caramel 40L',        40.0, -30.4), (12, 'Special Roast',     40.0, -13.0),
        (13, 'Caramel 60L',        61.0, -43.4), (14, 'Caramel 80L',       80.0, -45.1),
        (15, 'Caramel 120L',       120.0, -60.4), (16, 'Extra Special Malt', 126.0, -67.5)
    ) as v(n, name, lov, meq)
    where (v.name like 'Caramel%') = (role = 'crystal')
    order by abs(v.lov - lovibond), v.n
    limit 1;
    return jsonb_build_object('class', picked.name, 'meq_kg', picked.meq, 'buffer', 40, 'page', page);
end
$$;

-- Mash pH estimate by the zero-sum method: pH = 5.4 + (sum of kg x malt mEq/kg + strike litres x RA
-- in mEq/L) / (40 x grist kg). grist is [{kg, role, ebc, name}] (app.mashed_grist's shape),
-- strike_ions the strike water's ions. colour is the water row's colour (pale, amber, brown/black)
-- and picks HTB's target: pale 5.2-5.4, amber 5.3-5.5, brown/black 5.4-5.6, null (no row) 5.2-5.6.
-- terms lists each addition's mEq and buffer, so sum(meq) / sum(buffer) reproduces ph - 5.4.
-- doc-calc.md §7; How to Brew p. 341-342, 349-351, 365. Unverified against Bru'n Water (§16).
create or replace function app.mash_ph_estimate(grist jsonb, strike_ions jsonb, strike_l numeric, colour text)
returns jsonb
language plpgsql
immutable
as $$
declare
    low numeric;
    high numeric;
    terms jsonb;
    sum_meq numeric;
    sum_buffer numeric;
    ra numeric;
    ph numeric;
begin
    if grist is null or jsonb_typeof(grist) <> 'array' or jsonb_array_length(grist) = 0 then
        raise exception 'mash_ph_estimate: the grist is empty';
    end if;
    if strike_l is null or strike_l <= 0 then
        raise exception 'mash_ph_estimate: strike water must be above 0 L';
    end if;
    case
        when colour is null then low := 5.2; high := 5.6;
        when colour = 'pale' then low := 5.2; high := 5.4;
        when colour = 'amber' then low := 5.3; high := 5.5;
        when colour = 'brown/black' then low := 5.4; high := 5.6;
        else raise exception 'mash_ph_estimate: unknown colour %', colour;
    end case;
    ra := (app.residual_alkalinity(strike_ions) ->> 'ra_meq_l')::numeric;
    select jsonb_agg(t.term order by t.ord) into terms
    from (
        select 0 as ord, jsonb_build_object('what', 'strike water', 'meq', strike_l * ra, 'buffer', 0) as term
        union all
        select g.ord, jsonb_build_object('what', coalesce(g.value ->> 'name', g.value ->> 'role'),
                   'meq', (g.value ->> 'kg')::numeric * (a.acid ->> 'meq_kg')::numeric,
                   'buffer', (g.value ->> 'kg')::numeric * (a.acid ->> 'buffer')::numeric)
        from jsonb_array_elements(grist) with ordinality as g(value, ord)
        cross join lateral (select app.malt_acidity(g.value ->> 'role', (g.value ->> 'ebc')::numeric) as acid) a
    ) t;
    select sum((x ->> 'meq')::numeric), sum((x ->> 'buffer')::numeric) into sum_meq, sum_buffer from jsonb_array_elements(terms) x;
    if sum_buffer <= 0 then
        raise exception 'mash_ph_estimate: the grist has no mashed malt';
    end if;
    ph := round(5.4 + sum_meq / sum_buffer, 3);
    return jsonb_build_object('ph', ph, 'target_low', low, 'target_high', high, 'terms', terms,
        'because', format('pH 5.4 + %s mEq / %s mEq per pH = %s; target %s-%s (How to Brew p. 341, 365)',
                          round(sum_meq, 2), round(sum_buffer, 1), ph, low, high));
end
$$;

-- Alkalinity for the strike water, from the grist and not from the row. Adds baking soda while the
-- strike water's sodium stays at or below 100 mg/L (HTB Table 8.1), slaked lime for the rest, until
-- the mash pH estimate reaches target_low. With sigma = sum of kg x malt mEq/kg, K = 40 x grist kg,
-- V = strike litres and RA0 the strike water's RA in mEq/L:
--   RA to add = ((target_low - 5.4) x K - sigma) / V - RA0      (nothing when it is 0 or less)
-- baking soda by its HCO3 alkalinity, lime by its Kolbach effect (alkalinity - Ca / 3.5), each
-- taken from ref.water_salt. Grams to 0.1 g; soda is rounded down when the sodium cap binds.
-- Chalk is not used (Water p. 117). doc-calc.md §6, §7. ra_needed_meq_l is the RA still to add.
create or replace function app.alkalinity_dose(grist jsonb, strike_ions jsonb, strike_l numeric, target_low numeric)
returns jsonb
language plpgsql
stable
as $$
declare
    k numeric;
    sigma numeric;
    ra0 numeric;
    need numeric;
    soda_id bigint; soda_na numeric; soda_eff numeric;
    lime_id bigint; lime_eff numeric;
    na_room numeric;
    soda_g numeric := 0;
    lime_g numeric := 0;
    rest numeric;
    capped boolean := false;
    salts jsonb := '[]'::jsonb;
    because text;
begin
    if strike_l is null or strike_l <= 0 or target_low is null then
        raise exception 'alkalinity_dose: strike water must be above 0 L and the target given';
    end if;
    select sum((x ->> 'kg')::numeric) * 40,
           sum((x ->> 'kg')::numeric * (app.malt_acidity(x ->> 'role', (x ->> 'ebc')::numeric) ->> 'meq_kg')::numeric)
      into k, sigma from jsonb_array_elements(grist) x;
    if k is null or k <= 0 then
        raise exception 'alkalinity_dose: the grist is empty';
    end if;
    ra0 := (app.residual_alkalinity(strike_ions) ->> 'ra_meq_l')::numeric;
    need := ((target_low - 5.4) * k - sigma) / strike_l - ra0;
    if need <= 0 then
        return jsonb_build_object('ra_needed_meq_l', 0, 'salts', salts,
            'because', format('the mash pH estimate is already at or above %s, so no alkalinity is added', target_low));
    end if;

    select i.id, (s.ion_mg_per_l_per_g ->> 'Na')::numeric,
           (app.residual_alkalinity(app.salt_ions(jsonb_build_array(jsonb_build_object('ingredient_id', i.id, 'g', 1)), 1)) ->> 'ra_meq_l')::numeric
      into soda_id, soda_na, soda_eff
    from ref.water_salt s join ref.ingredient i on i.id = s.ingredient_id where i.name = 'baking soda';
    select i.id,
           (app.residual_alkalinity(app.salt_ions(jsonb_build_array(jsonb_build_object('ingredient_id', i.id, 'g', 1)), 1)) ->> 'ra_meq_l')::numeric
      into lime_id, lime_eff
    from ref.water_salt s join ref.ingredient i on i.id = s.ingredient_id where i.name = 'slaked lime';

    -- baking soda up to the sodium cap, then lime for what is left
    na_room := greatest(0, 100 - coalesce((strike_ions ->> 'na')::numeric, 0));
    if need / soda_eff <= na_room / soda_na then
        soda_g := round(need / soda_eff * strike_l, 1);
    else
        capped := true;
        soda_g := floor(na_room / soda_na * strike_l * 10) / 10;
    end if;
    rest := need - soda_g / strike_l * soda_eff;
    if rest > 0 and capped then
        lime_g := round(rest / lime_eff * strike_l, 1);
    end if;
    if soda_g > 0 then
        salts := salts || jsonb_build_object('ingredient_id', soda_id, 'name', 'baking soda', 'strike_g', soda_g);
    end if;
    if lime_g > 0 then
        salts := salts || jsonb_build_object('ingredient_id', lime_id, 'name', 'slaked lime', 'strike_g', lime_g);
    end if;
    because := format('the grist needs %s mEq/L more residual alkalinity in the %s L of strike water to reach mash pH %s; %s',
                      round(need, 3), strike_l, target_low,
                      case when capped then 'baking soda to the 100 mg/L sodium cap, slaked lime for the rest'
                           else 'baking soda (sodium stays at or below 100 mg/L)' end);
    return jsonb_build_object('ra_needed_meq_l', need, 'salts', salts, 'because', because);
end
$$;


-- A numrange as {low, high} (null for an open end).
create or replace function app.range_json(r numrange)
returns jsonb
language sql
immutable
as $$
    select jsonb_build_object('low', lower(r), 'high', upper(r))
$$;

-- Step 12, water. The salts for the recipe's water: the style's Water Table 18/19 row
-- (ref.beer_style.water_profile of targets.style.code), the aim inside it (sulfate and chloride by the
-- brief's hints), gypsum and calcium chloride in the strike and the sparge water, then alkalinity
-- (baking soda, slaked lime) in the strike water until the mash pH estimate reaches the bottom of the
-- colour target, and the acid line (no acid amount, ever). The volumes are app.water_volumes', the
-- same step 13 outputs. A style with no row gets no salts: the waters are the source water and the pH
-- is still estimated (plan decision Q1). profile is step 0's, targets step 4's, brief step 1's and
-- step10 step 10's output. doc-calc.md §3-§8; How to Brew p. 133-135, 341-342, 349-351, 365.
create or replace function app.step12_water(profile jsonb, targets jsonb, brief jsonb, step10 jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    style_code text := targets -> 'style' ->> 'code';
    row_code text;
    basis text;
    r ref.water_profile;
    source jsonb := profile -> 'water';
    vol jsonb;
    grist jsonb;
    strike_l numeric;
    sparge_l numeric;
    hints text[];
    aim jsonb := null;
    sa jsonb;
    strike_ions jsonb;
    sparge_ions jsonb;
    est jsonb;
    dose jsonb;
    dose_ions jsonb;
    salts jsonb := '[]'::jsonb;
    notes text[] := '{}';
    note text;
    colour text;
    acid jsonb;
    acid_text text;
    values_used jsonb := '[]'::jsonb;
    final_ra jsonb;
    s jsonb;
begin
    if style_code is null then
        raise exception 'step12_water: targets has no style code';
    end if;
    if source is null then
        raise exception 'step12_water: the profile has no water';
    end if;
    select water_profile, water_basis into row_code, basis from ref.beer_style where code = style_code;
    if not found then
        raise exception 'step12_water: no style %', style_code;
    end if;
    vol := app.water_volumes(profile, step10);
    grist := app.mashed_grist(step10);
    strike_l := (vol ->> 'strike_l')::numeric;
    sparge_l := (vol ->> 'sparge_l')::numeric;
    hints := coalesce(array(select jsonb_array_elements_text(coalesce(brief -> 'hints', '[]'::jsonb))), '{}');

    values_used := values_used || jsonb_build_object('what', 'water volumes', 'because', vol ->> 'because',
        'source', 'How to Brew ch. 17 p. 262, 267-269 (3 L/kg); profile grain absorption (doc-calc.md §8)');

    select * into r from ref.water_profile where code = row_code;   -- no row (r all null) when the style has none
    if row_code is null then
        strike_ions := app.add_ions(source, '{}'::jsonb);
        sparge_ions := strike_ions;
        est := app.mash_ph_estimate(grist, strike_ions, strike_l, null);
        values_used := values_used || jsonb_build_object('what', 'salts',
            'because', format('style %s has no water row, so no salts are added and the waters are the source water', style_code),
            'source', 'plan decision Q1');
    else
        colour := r.colour;
        aim := app.water_aim(row_code, hints);
        sa := app.salt_additions(source, aim, row_code, strike_l, sparge_l);
        salts := sa -> 'salts';
        strike_ions := sa -> 'strike_water' -> 'ions';
        sparge_ions := sa -> 'sparge_water' -> 'ions';
        for note in select jsonb_array_elements_text(sa -> 'notes') loop
            if note not like 'outside_row:%' then
                notes := notes || note;
            end if;
        end loop;
        est := app.mash_ph_estimate(grist, strike_ions, strike_l, colour);
        dose := app.alkalinity_dose(grist, strike_ions, strike_l, (est ->> 'target_low')::numeric);
        if jsonb_array_length(dose -> 'salts') > 0 then
            dose_ions := app.salt_ions(
                (select jsonb_agg(jsonb_build_object('ingredient_id', d -> 'ingredient_id', 'g', d -> 'strike_g'))
                 from jsonb_array_elements(dose -> 'salts') d), strike_l);
            strike_ions := app.add_ions(strike_ions, dose_ions);
            for s in select * from jsonb_array_elements(dose -> 'salts') loop
                salts := salts || jsonb_build_object('ingredient_id', s -> 'ingredient_id', 'name', s ->> 'name',
                    'aims_at', 'alkalinity', 'strike_g', s -> 'strike_g', 'sparge_g', 0, 'total_g', s -> 'strike_g');
            end loop;
            est := app.mash_ph_estimate(grist, strike_ions, strike_l, colour);
        end if;
        notes := notes || app.outside_row(strike_ions, row_code);
        values_used := values_used
            || jsonb_build_object('what', 'water row', 'because',
                   format('style %s uses %s (%s)', style_code, row_code, basis), 'source', 'Water ' || r.page || ' (doc-calc.md §4)')
            || jsonb_build_object('what', 'sulfate and chloride aim', 'because',
                   format('sulfate %s and chloride %s mg/L inside the row; %s', round((aim ->> 'so4')::numeric, 1),
                          round((aim ->> 'cl')::numeric, 1),
                          case when jsonb_array_length(aim -> 'moved_by') = 0 then 'no hint moves them from the middle'
                               else (select string_agg(m, '; ') from jsonb_array_elements_text(aim -> 'moved_by') m) end),
                   'source', 'How to Brew p. 133-135 (doc-calc.md §5)')
            || jsonb_build_object('what', 'alkalinity', 'because', dose ->> 'because',
                   'source', 'How to Brew p. 342, 349-351, 363 (doc-calc.md §6, §7)');
    end if;

    final_ra := app.residual_alkalinity(strike_ions);
    acid_text := case
        when (est ->> 'ph')::numeric > (est ->> 'target_high')::numeric then
            format('acid would be needed to bring the mash from %s into %s-%s', round((est ->> 'ph')::numeric, 2),
                   est ->> 'target_low', est ->> 'target_high')
        else
            format('no acid needed: the mash pH estimate %s is not above %s (target %s-%s)', round((est ->> 'ph')::numeric, 2),
                   est ->> 'target_high', est ->> 'target_low', est ->> 'target_high')
    end;
    acid := jsonb_build_object('needed', (est ->> 'ph')::numeric > (est ->> 'target_high')::numeric,
                               'text', acid_text, 'acidify', r.acidify);
    values_used := values_used || jsonb_build_object('what', 'mash pH', 'because', est ->> 'because',
        'source', 'How to Brew p. 341-342, 349-351, 365 (doc-calc.md §7); unverified against Bru''n Water');

    return jsonb_build_object(
        'target', jsonb_build_object(
            'from', case when row_code is null then 'none' else 'style' end,
            'style_code', style_code, 'row', row_code, 'table_no', r.table_no, 'beer_type', r.beer_type,
            'strength', r.strength, 'colour', r.colour, 'bitterness', r.bitterness,
            'ranges', case when row_code is null then null else jsonb_build_object(
                'ca', app.range_json(r.ca), 'alkalinity', app.range_json(r.alkalinity), 'so4', app.range_json(r.so4),
                'cl', app.range_json(r.cl), 'ra', app.range_json(r.ra)) end,
            'acidify', r.acidify, 'page', r.page,
            'aim', case when aim is null then null else aim - 'moved_by' - 'alkalinity' - 'ra' end,
            'basis', basis, 'fallback', coalesce(basis, '') <> 'listed',
            'outside_row', to_jsonb(notes),
            'moved_by', coalesce(aim -> 'moved_by', '[]'::jsonb)),
        'source_water', jsonb_build_object('ions', source) || app.residual_alkalinity(source),
        'volumes', vol,
        'salts', salts,
        'none_needed', jsonb_array_length(salts) = 0,
        'strike_water', jsonb_build_object('ions', strike_ions) || final_ra,
        'sparge_water', jsonb_build_object('ions', sparge_ions) || app.residual_alkalinity(sparge_ions),
        'mash_ph', est - 'terms',
        'acid', acid,
        'values_used', values_used);
end
$$;
