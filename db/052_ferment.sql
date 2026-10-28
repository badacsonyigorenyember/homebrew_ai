-- Step 14, the fermentation and the pitch (docs/work/m7-process, Task 6): the yeast amount from a
-- pitch rate, the temperature schedule with its gravity triggers, the dry hop and the secondary extras.
-- Everything comes from How to Brew (HTB) first, doc-calc.md §10-§13. No LLM.
-- Needs db/030_maths.sql (app.sg_to_plato) and db/051_mash_boil.sql (applied before it in the series).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/052_ferment.sql
-- Idempotent: safe to re-run.

-- How much of one yeast to pitch. cells = rate x litres x degrees Plato (HTB ch. 7 p. 111); rates for
-- fresh yeast: 0.75 billion cells/L/degP for ales (kveik, brett and untyped yeasts too), 1.5 for lagers,
-- 1.0 for an ale after a souring culture (HTB p. 212). A souring culture (type lacto) is pitched at HTB
-- p. 206: 150 billion cells per 19 L, the middle of 100-200. Dry yeast: 10 billion cells per gram, liquid
-- (and a culture): 100 billion per pack (HTB p. 108); both are HTB's GENERIC figures, not the maker's
-- spec, and the `because` says so. A yeast whose amount cannot be computed gets 1 pack and says so.
-- Returns {rate_m_per_ml_p, plato, cells_billion, amount, unit g|pack, because}; rate_m_per_ml_p is
-- million cells per mL per degP (the same number as billion per L per degP), null for a culture.
create or replace function app.pitch_rate(yeast_id bigint, og numeric, volume_l numeric,
                                          after_souring boolean default false)
returns jsonb
language plpgsql
stable
as $$
declare
    y record;
    plato numeric;
    rate numeric;
    cells numeric;
    amount numeric;
    unit text;
    why text;
begin
    select type, form into y from ref.yeast where ingredient_id = pitch_rate.yeast_id;
    if not found then
        raise exception 'pitch_rate: yeast % is not in ref.yeast', yeast_id;
    end if;
    if og is null or volume_l is null or og <= 1 or volume_l <= 0 or y.form is null or y.form not in ('dry', 'liquid') then
        return jsonb_build_object('rate_m_per_ml_p', null, 'plato', null, 'cells_billion', null, 'amount', 1,
                                  'unit', 'pack', 'because', 'no sourced pitch rate: 1 pack');
    end if;
    plato := app.sg_to_plato(og);

    if y.type = 'lacto' then
        cells := 150 * volume_l / 19;
        why := format('souring culture at 150 billion cells per 19 L, the middle of HTB p. 206''s 100-200 range, for %s L = %s billion cells; '
                      'both that range and the 100 billion cells per pack are HTB''s generic figures, not the maker''s spec, so the %s pack(s) are an estimate',
                      volume_l, round(cells, 1), ceil(cells / 100));
    else
        rate := case when y.type = 'lager' then 1.5 when after_souring then 1.0 else 0.75 end;
        cells := rate * volume_l * plato;
        why := format('%s billion cells/L/degP (HTB ch. 7 p. 111-113%s) x %s L x %s degP = %s billion cells; ',
                      rate, case when after_souring and y.type <> 'lager' then ', raised from 0.75 after souring, p. 212' else '' end,
                      volume_l, round(plato, 1), round(cells, 1))
              || case when y.form = 'dry'
                      then format('dry yeast at 10 billion cells per gram is HTB''s generic figure (p. 108), not the maker''s spec, so the %s g are an estimate', ceil(cells / 10))
                      else format('about 100 billion cells per liquid pack is HTB''s generic figure (p. 108), not the maker''s spec, so the %s pack(s) are an estimate', ceil(cells / 100)) end;
    end if;

    if y.form = 'dry' and y.type is distinct from 'lacto' then
        amount := ceil(cells / 10);
        unit := 'g';
    else
        amount := ceil(cells / 100);
        unit := 'pack';
    end if;
    return jsonb_build_object('rate_m_per_ml_p', rate, 'plato', round(plato, 2), 'cells_billion', round(cells, 1),
                              'amount', greatest(amount, 1), 'unit', unit, 'because', why);
end
$$;

-- The temperature plan, [{phase, yeast_id, temp_c, days, why, source, move_on}] in order. `days` is the
-- minimum; `move_on` says what ends the step (HTB Table 6.2's gravity trigger), null where HTB gives none.
-- main and souring are {ingredient_id} (souring null when no culture). doc-calc.md §11 and §13:
--   main temperature M = ferm_c raised to the yeast's lower bound + 1 C (and kept inside its range);
--   ale (also kveik, brett, untyped): start S = M - 2 (HTB p. 90), 1 day; hold M, 2 days; rest
--     least(M + 3, upper bound), 4 days (Table 6.2: 3-6 C, minimum 4 days);
--   lager: start at M (HTB p. 174), 4 days; diacetyl rest least(M + 8, upper bound), 6 days (Table 6.2);
--   souring culture first: 35 C (inside HTB's 32-46 C and the culture's range), 1.5 days (HTB p. 211);
--   dry_hop (when asked): 14 C or the last fermentation temperature if lower, 3 days contact (HTB p. 72);
--   then ale cold conditioning (M - 8 C, at least 2, a week, HTB p. 95) or lagering (2 C, 14 days, p. 174).
create or replace function app.ferment_schedule(main jsonb, souring jsonb, ferm_c numeric,
                                                dry_hop boolean default false)
returns jsonb
language plpgsql
stable
as $$
declare
    mid bigint := (main ->> 'ingredient_id')::bigint;
    sid bigint := (souring ->> 'ingredient_id')::bigint;
    y record;
    s record;
    m numeric;
    start_c numeric;
    rest_c numeric;
    last_c numeric;
    sour_c numeric;
    steps jsonb := '[]'::jsonb;
    gravity constant text := 'gravity within 2-5 points of FG (HTB p. 93-94, Table 6.2)';
begin
    select type, lower(temp_c) as lo, upper(temp_c) as hi into y from ref.yeast where ingredient_id = mid;
    if not found or y.lo is null then
        raise exception 'ferment_schedule: yeast % has no temperature range in ref.yeast', mid;
    end if;
    if ferm_c is null then
        raise exception 'ferment_schedule: no fermentation temperature';
    end if;
    m := least(y.hi, greatest(ferm_c, y.lo + 1));

    if sid is not null then
        select lower(temp_c) as lo, upper(temp_c) as hi into s from ref.yeast where ingredient_id = sid;
        if found and greatest(s.lo, 32) <= least(s.hi, 46) then
            sour_c := greatest(greatest(s.lo, 32), least(35, least(s.hi, 46)));
            steps := steps || jsonb_build_object('phase', 'souring', 'yeast_id', sid, 'temp_c', sour_c, 'days', 1.5,
                'why', 'sour in the fermenter before the yeast ("bacteria first, yeast second"): Lactobacillus grows at 32-46 C, hops inhibit it, '
                       'so keep the bitterness low (Berliner weisse 5-8 IBU); pre-acidify to pH 4.5-4.8 (amount not computed)',
                'source', 'How to Brew p. 206, 210-211 (doc-calc.md §13)',
                'move_on', 'at least 18 hours (1.5 days planned); move on when the wort has soured to about pH 3.5 (HTB p. 211: 18-36 hours)');
        end if;
    end if;

    if y.type = 'lager' then
        rest_c := least(y.hi, m + 8);
        steps := steps
            || jsonb_build_object('phase', 'ferment', 'yeast_id', mid, 'temp_c', m, 'days', 4,
                'why', 'lager yeast pitched and held at the fermentation temperature (HTB p. 174); high-growth phase of 2-5 days',
                'source', 'How to Brew p. 91, 174, Table 6.2',
                'move_on', 'at least 4 days; move on to the diacetyl rest when ' || gravity)
            || jsonb_build_object('phase', 'rest', 'yeast_id', mid, 'temp_c', rest_c, 'days', 6,
                'why', 'diacetyl rest: raise by 8-10 C (the lowest figure, capped at the yeast''s upper bound) so the yeast cleans up diacetyl and acetaldehyde',
                'source', 'How to Brew p. 93-94, Table 6.2',
                'move_on', 'starts when ' || gravity || '; stay at least 6 days (up to 12), then cool');
        last_c := rest_c;
    else
        start_c := greatest(m - 2, y.lo);
        rest_c := least(y.hi, m + 3);
        steps := steps
            || jsonb_build_object('phase', 'ferment', 'yeast_id', mid, 'temp_c', start_c, 'days', 1,
                'why', 'pitch at or slightly below the fermentation temperature; the first day is mostly adaptation',
                'source', 'How to Brew p. 90-91',
                'move_on', null)
            || jsonb_build_object('phase', 'ferment', 'yeast_id', mid, 'temp_c', m, 'days', 2,
                'why', 'fermentation temperature; high-growth phase of 1-3 days for ales',
                'source', 'How to Brew p. 91, Table 6.2',
                'move_on', 'at least 2 more days (about day 3 of 4); move on to the rest when ' || gravity)
            || jsonb_build_object('phase', 'rest', 'yeast_id', mid, 'temp_c', rest_c, 'days', 4,
                'why', 'maturation rest: raise by 3-6 C (the lowest figure, capped at the yeast''s upper bound) to finish the clean-up',
                'source', 'How to Brew p. 93-94, Table 6.2',
                'move_on', 'starts when ' || gravity || '; stay at least 4 days (up to 8), then cool');
        last_c := rest_c;
    end if;

    if dry_hop then
        steps := steps || jsonb_build_object('phase', 'dry_hop', 'yeast_id', null, 'temp_c', least(14, last_c), 'days', 3,
            'why', 'dry hops after fermentation: 3 days is the low end of HTB''s 3-5 days of contact at 10-21 C (less contact when warmer); remove them after',
            'source', 'How to Brew p. 72; the 14 C point is Janish, Dry Hop Best Practices (MBAA TQ 58(1), 2021)',
            'move_on', null);
    end if;

    if y.type = 'lager' then
        steps := steps || jsonb_build_object('phase', 'lager', 'yeast_id', null, 'temp_c', 2, 'days', 14,
            'why', 'lagering: cool by no more than 6 C a day to about 2 C; 2-4 weeks, 1-2 weeks when priming and bottle conditioning (14 days chosen)',
            'source', 'How to Brew p. 174', 'move_on', null);
    else
        steps := steps || jsonb_build_object('phase', 'crash', 'yeast_id', null, 'temp_c', greatest(2, m - 8), 'days', 7,
            'why', 'cold conditioning: cool slowly (1 C a day) 5-8 C below the fermentation temperature for a week',
            'source', 'How to Brew p. 95', 'move_on', null);
    end if;
    return steps;
end
$$;

-- Step 14. targets is step 4's output (the style, for the text only), step10 step 10's output.
--   steps: app.ferment_schedule of the main yeast and the souring culture;
--   pitch: one line per yeast of step 10, {ingredient_id, name, role, rate_m_per_ml_p, plato, cells_billion,
--          amount, unit, because} (the amounts replace step 10's `1 pack`; the main yeast uses 1.0 after souring);
--   dry_hops: one group when step 10 has dry hops: the day after the last souring/ferment/rest step;
--   secondary: step 10's `secondary` extras that day, `ferment` extras at pitching (day 0), with their
--          contact days from the misc row's time_min (null when there is none);
--   max_temp_c: the highest temperature of the ferment and rest steps, which step 15 reads for the
--          residual CO2 (the souring step is before the yeast has made any CO2, and 35 C is outside Table 10.3).
create or replace function app.step14_ferment(targets jsonb, step10 jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    og numeric := (step10 #>> '{numbers,og}')::numeric;
    vol numeric := (step10 #>> '{batch,volume_l}')::numeric;
    ferm_c numeric := (step10 ->> 'ferm_c')::numeric;
    main_y jsonb := (select y from jsonb_array_elements(step10 -> 'yeasts') y where y ->> 'role' = 'main' limit 1);
    sour_y jsonb := (select y from jsonb_array_elements(step10 -> 'yeasts') y where y ->> 'role' = 'souring' limit 1);
    hops jsonb;
    steps jsonb;
    pitch jsonb;
    dry_hops jsonb := '[]'::jsonb;
    secondary jsonb;
    fermented numeric;
    dry jsonb;
    max_c numeric;
begin
    if main_y is null or og is null or vol is null or ferm_c is null then
        raise exception 'step14_ferment: step 10 has no main yeast, og, batch volume or ferm_c';
    end if;
    select coalesce(jsonb_agg(h order by h ->> 'name'), '[]'::jsonb) into hops
    from jsonb_array_elements(coalesce(step10 -> 'hops', '[]'::jsonb)) h where h ->> 'usage' = 'dry_hop';

    steps := app.ferment_schedule(main_y, sour_y, ferm_c, jsonb_array_length(hops) > 0);

    select coalesce(jsonb_agg(
               jsonb_build_object('ingredient_id', (y ->> 'ingredient_id')::bigint, 'name', y ->> 'name', 'role', y ->> 'role')
               || app.pitch_rate((y ->> 'ingredient_id')::bigint, og, vol, y ->> 'role' = 'main' and sour_y is not null)
               order by case y ->> 'role' when 'souring' then 0 else 1 end, y ->> 'name'), '[]'::jsonb)
      into pitch
    from jsonb_array_elements(step10 -> 'yeasts') y;

    select coalesce(sum((s ->> 'days')::numeric), 0), max((s ->> 'temp_c')::numeric) filter (where s ->> 'phase' in ('ferment', 'rest'))
      into fermented, max_c
    from jsonb_array_elements(steps) s where s ->> 'phase' in ('souring', 'ferment', 'rest');

    if jsonb_array_length(hops) > 0 then
        select s into dry from jsonb_array_elements(steps) s where s ->> 'phase' = 'dry_hop';
        dry_hops := jsonb_build_array(jsonb_build_object(
            'day', fermented, 'temp_c', (dry ->> 'temp_c')::numeric, 'contact_days', (dry ->> 'days')::numeric,
            'hops', (select jsonb_agg(jsonb_build_object('ingredient_id', (h ->> 'ingredient_id')::bigint, 'name', h ->> 'name',
                                                         'g', (h ->> 'g')::numeric) order by h ->> 'name')
                       from jsonb_array_elements(hops) h)));
    end if;

    select coalesce(jsonb_agg(jsonb_build_object(
               'usage', e ->> 'usage',
               'day', case when e ->> 'usage' = 'ferment' then 0 else fermented end,
               'ingredient_id', (e ->> 'ingredient_id')::bigint, 'name', e ->> 'name', 'g', (e ->> 'g')::numeric,
               'contact_days', case when e ->> 'time_min' is null then null else round((e ->> 'time_min')::numeric / 1440, 2) end)
               order by e ->> 'usage' desc, e ->> 'name'), '[]'::jsonb)
      into secondary
    from jsonb_array_elements(coalesce(step10 -> 'extras', '[]'::jsonb)) e where e ->> 'usage' in ('ferment', 'secondary');

    return jsonb_build_object(
        'steps', steps, 'pitch', pitch, 'dry_hops', dry_hops, 'secondary', secondary, 'max_temp_c', max_c,
        'values_used', jsonb_build_array(
            jsonb_build_object('what', 'fermentation plan', 'because',
                format('%s step(s) for %s; each step is a minimum, the next starts on the gravity trigger given with it',
                       jsonb_array_length(steps), coalesce(targets -> 'style' ->> 'code', 'the recipe')),
                'source', 'How to Brew ch. 6 p. 90-95, Table 6.2, p. 174 (doc-calc.md §11)'),
            jsonb_build_object('what', 'pitch amounts', 'because',
                'cells = rate x litres x degP; the cells per gram and per pack are How to Brew''s generic figures, not the makers'' specs (estimates)',
                'source', 'How to Brew ch. 7 p. 108-114, p. 206, 212 (doc-calc.md §10)'),
            jsonb_build_object('what', 'highest fermentation temperature', 'because',
                format('%s C, the highest ferment or rest step: step 15 reads it for the residual CO2', max_c),
                'source', 'How to Brew p. 159 (doc-calc.md §14)')));
end
$$;
