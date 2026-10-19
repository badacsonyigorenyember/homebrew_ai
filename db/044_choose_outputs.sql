-- Steps 6-9 (choose yeast, fermentables, hops and extras), part 3: the step outputs
-- (docs/work/m5-choose-ingredients, Task 6). A proposal that passed app.choose_check (db/043) is
-- turned into the four step outputs. Every pick is read only from its row of the candidate table
-- (db/042) by id: the LLM supplies ids, usages, percentages, hop minutes, shares and a purpose,
-- and code adds the facts (level, inventory, wanted, slot, EBC, alpha, ...) and, for extras, the
-- dose from app.misc_dose. An id that is not a row of the right kind raises, so no invented
-- product can reach an output (R1).
-- Needs db/043_choose_check.sql, db/042_choose_table.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/044_choose_outputs.sql
-- Idempotent: safe to re-run.

-- The fields every pick carries (R9): the row's name and producer, its level at the chosen usage
-- (a yeast at its best ferment choice, which names the temperature), the inventory word, the wanted
-- item and slot it fills, the LLM's purpose, and one sentence that joins the purpose and the facts.
-- p is the LLM's pick {ingredient_id, purpose, ...}; choice is the label of the table choice it sits
-- at (null for a yeast).
create or replace function app.choose_pick(step int, kind text, tbl jsonb, p jsonb, choice text)
returns jsonb
language plpgsql
stable
as $$
declare
    v_id    bigint := (p ->> 'ingredient_id')::bigint;
    r       jsonb := app.choose_row(tbl, v_id);
    l       jsonb;
    v_slot  text;
    v_text  text;
begin
    if r is null then
        raise exception 'step %: id % is not in the candidate table', step, v_id;
    elsif r ->> 'kind' <> kind then
        raise exception 'step %: id % is a %, not a %', step, v_id, r ->> 'kind', kind;
    end if;
    if kind = 'yeast' then
        select x.value into l from jsonb_array_elements(r -> 'levels') x
         where x.value ->> 'level' = r ->> 'best_level' limit 1;
    else
        select x.value into l from jsonb_array_elements(r -> 'levels') x
         where x.value ->> 'choice' = choice limit 1;
    end if;
    select s.value ->> 'item' into v_slot
      from jsonb_array_elements(coalesce(tbl -> 'slots', '[]'::jsonb)) s
     where s.value -> 'ids' @> to_jsonb(v_id) limit 1;
    v_text := (r ->> 'name') || ': ' || (p ->> 'purpose')
        || coalesce(' (' || replace(l ->> 'level', '_', ' ') || ' at ' || (l ->> 'choice') || ' in ' || (tbl ->> 'style_used') || ')', '')
        || coalesce('; from your inventory ("' || (r ->> 'inventory') || '")', '')
        || case when jsonb_typeof(r -> 'wanted') = 'object' then '; you asked for "' || (r #>> '{wanted,item}') || '"' else '' end;
    return jsonb_build_object(
        'ingredient_id', v_id, 'name', r ->> 'name', 'producer', nullif(r ->> 'producer', ''),
        'choice', l ->> 'choice', 'level', l ->> 'level', 'level_because', l ->> 'because',
        'inventory', r ->> 'inventory',
        'wanted', case when jsonb_typeof(r -> 'wanted') = 'object' then r -> 'wanted' else null end,
        'slot', v_slot, 'purpose', p ->> 'purpose', 'because', v_text);
end
$$;

-- The table's absent entries for one kind; the entries with no kind (a word no product matches)
-- go with step 9's.
create or replace function app.choose_absent(tbl jsonb, kind text)
returns jsonb
language sql
immutable
as $$
    select coalesce(jsonb_agg(a.value order by a.ord), '[]'::jsonb)
      from jsonb_array_elements(coalesce(tbl -> 'absent', '[]'::jsonb)) with ordinality a(value, ord)
     where a.value ->> 'kind' = choose_absent.kind
        or (choose_absent.kind = 'misc' and jsonb_typeof(a.value -> 'kind') = 'null')
$$;

-- The inventory words of one kind that no pick uses, with why: the words the table already judged
-- not to fit, and (yeast only) fitting words left over because a recipe has one main yeast.
create or replace function app.choose_unused(tbl jsonb, kind text, picked bigint[])
returns jsonb
language sql
stable
as $$
    select coalesce(jsonb_agg(u.value), '[]'::jsonb) from (
        select jsonb_build_object('word', x.value ->> 'word', 'reason', x.value ->> 'reason') as value
          from jsonb_array_elements(coalesce(tbl -> 'unused_inventory', '[]'::jsonb)) x
         where exists (select 1 from jsonb_array_elements(tbl -> 'inventory_words') w
                        where w.value ->> 'word' = x.value ->> 'word' and w.value ->> 'kind' = choose_unused.kind)
        union all
        select jsonb_build_object('word', w.value ->> 'word',
                                  'reason', 'a recipe has one main yeast, and another inventory yeast was used')
          from jsonb_array_elements(coalesce(tbl -> 'inventory_words', '[]'::jsonb)) w
         where choose_unused.kind = 'yeast' and w.value ->> 'kind' = 'yeast' and (w.value ->> 'fits')::boolean
           and not exists (select 1 from jsonb_array_elements_text(w.value -> 'ids') i where i.value::bigint = any (picked))
    ) u
$$;

-- The facts of a yeast row that step 6 reports.
create or replace function app.choose_yeast_facts(tbl jsonb, p jsonb)
returns jsonb
language sql
stable
as $$
    select app.choose_pick(6, 'yeast', tbl, p, null)
        || jsonb_build_object('type', r ->> 'type', 'form', r ->> 'form', 'attenuation', r -> 'attenuation',
                              'temp_c', r -> 'temp_c', 'flocculation', r ->> 'flocculation', 'family', r -> 'family')
      from (select app.choose_row(tbl, (p ->> 'ingredient_id')::bigint) as r) q
$$;

-- Step 6: the main yeast, the souring culture (or null), how the yeast's attenuation sits against
-- step 5's yeast band, the inventory yeasts not used, and the absent yeast words.
create or replace function app.step6_output(tbl jsonb, yeast jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    m       jsonb := app.choose_yeast_facts(tbl, yeast -> 'main');
    s       jsonb := case when jsonb_typeof(yeast -> 'souring') = 'object' then app.choose_yeast_facts(tbl, yeast -> 'souring') else null end;
    r       jsonb := app.choose_row(tbl, (yeast #>> '{main,ingredient_id}')::bigint);
    v_over  jsonb := r -> 'overlaps_band';
    v_band  jsonb := jsonb_build_object('low_pct', tbl #> '{band,yeast_low_pct}', 'high_pct', tbl #> '{band,yeast_high_pct}');
    v_why   text;
begin
    v_why := case
        when jsonb_typeof(r -> 'attenuation') = 'null' then 'no attenuation figure; not assumed'
        when jsonb_typeof(v_over) = 'null' then 'no yeast band for this recipe; not assumed'
        when v_over = 'true'::jsonb then (r ->> 'name') || ' attenuates ' || app.choose_span(r -> 'attenuation')
             || ' %, which reaches the band ' || app.choose_num(v_band -> 'low_pct') || '-' || app.choose_num(v_band -> 'high_pct') || ' %'
        else (r ->> 'name') || ' attenuates ' || app.choose_span(r -> 'attenuation')
             || ' %, which does not reach the band ' || app.choose_num(v_band -> 'low_pct') || '-' || app.choose_num(v_band -> 'high_pct')
             || ' %' end;
    return jsonb_build_object(
        'yeast', m, 'souring', s,
        'attenuation', jsonb_build_object('band', v_band, 'yeast', r -> 'attenuation', 'overlaps', v_over, 'because', v_why),
        'unused_inventory', app.choose_unused(tbl, 'yeast',
            array_remove(array[(m ->> 'ingredient_id')::bigint, (s ->> 'ingredient_id')::bigint], null)),
        'absent', app.choose_absent(tbl, 'yeast'));
end
$$;

-- Step 7: the fermentables with their share, role, maximum, EBC and fermentability.
create or replace function app.step7_output(tbl jsonb, fermentables jsonb)
returns jsonb
language sql
stable
as $$
    select jsonb_build_object(
        'fermentables', coalesce(jsonb_agg(
            app.choose_pick(7, 'fermentable', tbl, f.value, f.value ->> 'usage')
            || jsonb_build_object('usage', f.value ->> 'usage', 'pct', f.value -> 'pct', 'role', r.value ->> 'role',
                                  'max_pct', r.value -> 'max_pct', 'ebc', r.value -> 'ebc',
                                  'fermentability', r.value ->> 'fermentability')
            order by f.ord), '[]'::jsonb),
        'unused_inventory', app.choose_unused(tbl, 'fermentable',
            coalesce(array_agg((f.value ->> 'ingredient_id')::bigint), '{}')),
        'absent', app.choose_absent(tbl, 'fermentable'))
      from jsonb_array_elements(fermentables) with ordinality f(value, ord)
      left join lateral (select app.choose_row(tbl, (f.value ->> 'ingredient_id')::bigint) as value) r on true
$$;

-- The table choice label of a hop addition: whirlpool and dry hop have one each, a boil addition
-- takes the choice with the largest minutes not above its own (as app.step8_errors does).
create or replace function app.choose_hop_choice(r jsonb, usage text, minutes numeric)
returns text
language sql
immutable
as $$
    select case usage
        when 'whirlpool' then 'whirlpool'
        when 'dry_hop' then 'dry hop'
        else (select l.value ->> 'choice' from jsonb_array_elements(r -> 'levels') l
               where l.value ->> 'usage' = 'boil' and (l.value ->> 'minutes')::numeric <= minutes
               order by (l.value ->> 'minutes')::numeric desc limit 1) end
$$;

-- Step 8: the hops with usage, minutes, share and alpha (the middle of the row's range). `solver`
-- holds exactly what app.solve_hops takes: share_pct, alpha_pct, minutes, usage.
create or replace function app.step8_output(tbl jsonb, hops jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    v_hops   jsonb := '[]'::jsonb;
    v_solver jsonb := '[]'::jsonb;
    h        jsonb;
    r        jsonb;
    v_alpha  numeric;
    v_ids    bigint[] := '{}';
begin
    for h in select value from jsonb_array_elements(hops) loop
        r := app.choose_row(tbl, (h ->> 'ingredient_id')::bigint);
        if r is null or r ->> 'kind' <> 'hop' then
            perform app.choose_pick(8, 'hop', tbl, h, null);  -- raises the right message
        end if;
        v_alpha := case when jsonb_typeof(r -> 'alpha') = 'object'
                        then ((r #>> '{alpha,low}')::numeric + (r #>> '{alpha,high}')::numeric) / 2 end;
        v_hops := v_hops || (app.choose_pick(8, 'hop', tbl, h,
                                app.choose_hop_choice(r, h ->> 'usage', (h ->> 'minutes')::numeric))
            || jsonb_build_object('usage', h ->> 'usage', 'minutes', h -> 'minutes', 'share_pct', h -> 'share_pct',
                                  'alpha', r -> 'alpha', 'alpha_pct', v_alpha, 'origins', r -> 'origins',
                                  'character', r -> 'character'));
        v_solver := v_solver || jsonb_build_object('share_pct', h -> 'share_pct', 'alpha_pct', v_alpha,
                                                    'minutes', h -> 'minutes', 'usage', h ->> 'usage');
        v_ids := v_ids || (h ->> 'ingredient_id')::bigint;
    end loop;
    return jsonb_build_object('hops', v_hops, 'solver', v_solver, 'ibu_target', tbl #> '{targets,ibu}',
        'unused_inventory', app.choose_unused(tbl, 'hop', v_ids), 'absent', app.choose_absent(tbl, 'hop'));
end
$$;

-- Step 9: the extras. The dose is set here from the wanted role (app.misc_dose), never by the LLM.
create or replace function app.step9_output(tbl jsonb, extras jsonb)
returns jsonb
language sql
stable
as $$
    select jsonb_build_object(
        'extras', coalesce(jsonb_agg(
            app.choose_pick(9, 'misc', tbl, e.value, e.value ->> 'usage')
            || jsonb_build_object('usage', e.value ->> 'usage', 'category', r.value ->> 'category',
                                  'time_min', r.value -> 'time_min',
                                  'dose_g_per_l', d.value -> 'g_per_l', 'dose_because', d.value ->> 'because')
            order by e.ord), '[]'::jsonb),
        'unused_inventory', app.choose_unused(tbl, 'misc',
            coalesce(array_agg((e.value ->> 'ingredient_id')::bigint), '{}')),
        'absent', app.choose_absent(tbl, 'misc'))
      from jsonb_array_elements(extras) with ordinality e(value, ord)
      left join lateral (select app.choose_row(tbl, (e.value ->> 'ingredient_id')::bigint) as value) r on true
      left join lateral (select app.misc_dose((e.value ->> 'ingredient_id')::bigint,
                                              r.value #>> '{wanted,role}') as value) d on true
$$;

-- All four outputs of a proposal that passed app.choose_check.
create or replace function app.choose_outputs(tbl jsonb, proposal jsonb)
returns jsonb
language sql
stable
as $$
    select jsonb_build_object(
        'step6', app.step6_output(tbl, proposal -> 'yeast'),
        'step7', app.step7_output(tbl, proposal -> 'fermentables'),
        'step8', app.step8_output(tbl, proposal -> 'hops'),
        'step9', app.step9_output(tbl, proposal -> 'extras'))
$$;
