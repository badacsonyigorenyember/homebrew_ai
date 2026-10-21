-- Steps 6-9 (choose yeast, fermentables, hops and extras), part 2: the check of the LLM's proposal
-- (docs/work/m5-choose-ingredients, Task 4). The LLM picks ids from the candidate table
-- (db/042); this file checks the picks against that table (R1-R7) and returns errors that start
-- with "step 6: " ... "step 9: ", so a failure says which step it belongs to. It also holds the
-- misc dose rule, which code (never the LLM) applies in the step 9 output.
-- Needs db/042_choose_table.sql, db/015_app.sql (pg_jsonschema in schema extensions).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/043_choose_check.sql
-- Idempotent: safe to re-run.

-- The dose of a misc in g/L, from its sourced range and the wanted role (R7, user decision
-- 2026-10-18): a one-point range is used as it is, `feature` takes the high end, `background` (and
-- no role) the low end. No sourced range gives g_per_l null. Returns {g_per_l, because}.
create or replace function app.misc_dose(product_id bigint, role text)
returns jsonb
language sql
stable
as $$
    select case
        when m.dose_g_per_l is null or isempty(m.dose_g_per_l) then
            jsonb_build_object('g_per_l', null, 'because', 'no sourced dose')
        when lower(m.dose_g_per_l) = upper(m.dose_g_per_l) then
            jsonb_build_object('g_per_l', lower(m.dose_g_per_l), 'because', 'one sourced dose')
        when misc_dose.role = 'feature' then
            jsonb_build_object('g_per_l', upper(m.dose_g_per_l), 'because', 'feature: high end of the sourced range')
        else
            jsonb_build_object('g_per_l', lower(m.dose_g_per_l),
                               'because', coalesce(misc_dose.role, 'no role given') || ': low end of the sourced range')
        end
      from ref.misc m
     where m.ingredient_id = misc_dose.product_id
$$;

-- One row of the candidate table by product id, whatever its kind; null when the id is not a row.
create or replace function app.choose_row(tbl jsonb, id bigint)
returns jsonb
language sql
immutable
as $$
    select r.value
      from jsonb_array_elements(coalesce(tbl -> 'fermentables', '[]'::jsonb) || coalesce(tbl -> 'hops', '[]'::jsonb)
                                || coalesce(tbl -> 'yeasts', '[]'::jsonb) || coalesce(tbl -> 'misc', '[]'::jsonb)) r
     where (r.value ->> 'ingredient_id')::bigint = choose_row.id
     limit 1
$$;

-- "id name, id name" for the table rows with these ids, for an error the model can act on.
create or replace function app.choose_names(tbl jsonb, ids jsonb)
returns text
language sql
immutable
as $$
    select string_agg(i.value || ' ' || (app.choose_row(tbl, i.value::bigint) ->> 'name'), ', ' order by i.ord)
      from jsonb_array_elements_text(ids) with ordinality i(value, ord)
$$;

-- The rules every step shares, for the picks of one kind (R1-R4, R6, R3). picks is
-- [{ingredient_id, choice}]; choice is the label of the table's usage choice the pick sits at
-- ("mash", "boil 30 min", "dry hop", "secondary"), null for a yeast (rated at its best choice).
--   R1  the id is a row of this kind in the table
--   R2  an excluded product (or a sibling) gets its own message
--   R4  with guidance on: a pipeline pick is required, typical or allowed at its choice; a wanted
--       pick sits at a choice that keeps the best level step 3 gave the word
--   R3  every fitting inventory word of this kind has a product picked (yeast: step 6 does it)
--   R6, R7  every slot of this kind has one of its products picked
create or replace function app.choose_pick_errors(step int, kind text, tbl jsonb, picks jsonb)
returns text[]
language plpgsql
stable
as $$
declare
    pre        text := 'step ' || step || ': ';
    v_guidance boolean := coalesce((tbl ->> 'guidance')::boolean, true);
    errs       text[] := '{}';
    v_ids      bigint[] := '{}';
    p          jsonb;
    r          jsonb;
    e          jsonb;
    x          jsonb;
    v_id       bigint;
    v_choice   text;
    v_level    jsonb;
    v_ok       jsonb;
begin
    for p in select value from jsonb_array_elements(picks) loop
        v_id := (p ->> 'ingredient_id')::bigint;
        v_choice := p ->> 'choice';
        r := app.choose_row(tbl, v_id);
        if r is null then
            select ex.value into e from jsonb_array_elements(coalesce(tbl -> 'excluded', '[]'::jsonb)) ex
             where (ex.value ->> 'ingredient_id')::bigint = v_id limit 1;
            if e is not null then
                errs := errs || (pre || (e ->> 'name') || ' (id ' || v_id || ') is excluded: ' || (e ->> 'why')
                                 || ' (' || coalesce(e ->> 'word', '') || '); pick another product');
            else
                errs := errs || (pre || 'id ' || v_id || ' is not in the candidate table');
            end if;
            continue;
        end if;
        if r ->> 'kind' <> kind then
            errs := errs || (pre || (r ->> 'name') || ' (id ' || v_id || ') is a ' || (r ->> 'kind')
                             || ', not a ' || kind);
            continue;
        end if;
        v_ids := v_ids || v_id;
        if not v_guidance then
            continue;
        end if;

        if jsonb_typeof(r -> 'wanted') = 'object' then
            -- wanted: the choice must keep the best level (rated in the style the request was rated in)
            if jsonb_typeof(r -> 'keeps_best') = 'array' then
                if kind = 'yeast' then
                    if jsonb_array_length(r -> 'keeps_best') = 0 then
                        errs := errs || (pre || (r ->> 'name') || ' is wanted as "' || (r #>> '{wanted,item}')
                                         || '" but no choice of it keeps the best level in ' || (tbl ->> 'wanted_style'));
                    end if;
                elsif v_choice is not null and not (r -> 'keeps_best') ? v_choice then
                    errs := errs || (pre || (r ->> 'name') || ' is wanted as "' || (r #>> '{wanted,item}')
                                     || '", and ' || v_choice || ' does not keep its best level in '
                                     || (tbl ->> 'wanted_style') || '; use one of: '
                                     || (select string_agg(k.value, ', ') from jsonb_array_elements_text(r -> 'keeps_best') k));
                end if;
            end if;
        else
            -- pipeline pick: required, typical or allowed in the style used
            if kind = 'yeast' then
                v_level := jsonb_build_object('level', r -> 'best_level', 'because',
                    (select l.value ->> 'because' from jsonb_array_elements(r -> 'levels') l
                      where l.value ->> 'level' = r ->> 'best_level' limit 1));
            else
                select l.value into v_level from jsonb_array_elements(r -> 'levels') l
                 where l.value ->> 'choice' = v_choice limit 1;
            end if;
            if v_level ->> 'level' is not null and app.level_rank(v_level ->> 'level') > app.level_rank('allowed') then
                errs := errs || (pre || (r ->> 'name') || coalesce(' at ' || v_choice, '') || ' is '
                                 || replace(v_level ->> 'level', '_', ' ') || ' in ' || (tbl ->> 'style_used')
                                 || ': ' || (v_level ->> 'because'));
            end if;
        end if;
    end loop;

    -- R3: a fitting inventory word needs one of its products (a yeast is the step 6 rule)
    if kind <> 'yeast' then
        for x in select w.value from jsonb_array_elements(coalesce(tbl -> 'inventory_words', '[]'::jsonb)) w
                  where w.value ->> 'kind' = kind and (w.value ->> 'fits')::boolean
                    and jsonb_array_length(w.value -> 'ids') > 0 loop
            if not exists (select 1 from jsonb_array_elements_text(x -> 'ids') i where i.value::bigint = any (v_ids)) then
                errs := errs || (pre || 'the inventory "' || (x ->> 'word') || '" fits this recipe and must be used; pick one of: '
                                 || app.choose_names(tbl, x -> 'ids'));
            end if;
        end loop;
    end if;

    -- R6, R7: every slot of this kind needs one of its products
    for x in select s.value from jsonb_array_elements(coalesce(tbl -> 'slots', '[]'::jsonb)) s
              where s.value ->> 'kind' = kind and jsonb_array_length(s.value -> 'ids') > 0 loop
        if not exists (select 1 from jsonb_array_elements_text(x -> 'ids') i where i.value::bigint = any (v_ids)) then
            errs := errs || (pre || 'the wanted "' || (x ->> 'item') || '" has no pick; pick one of: '
                             || app.choose_names(tbl, x -> 'ids'));
        end if;
    end loop;
    return errs;
end
$$;

-- Step 6: the yeast. yeast = {main {ingredient_id, purpose}, souring {..} or null}.
--   the main yeast is a brewing yeast (type ale, lager or kveik: not a lacto culture, a blend or a brett); a lager style gets a lager yeast; every family the style
--   requires is on the main yeast; its attenuation reaches step 5's yeast band when a usable yeast
--   does (a yeast the brewer wants or has is not refused for it: the step 6 output reports it);
--   a sour style gets a souring culture (type lacto), any other style none unless wanted or in stock.
--   Of the inventory yeasts that fit one is enough (a recipe has one main yeast); a fitting lacto
--   culture in stock is used as the souring culture.
create or replace function app.step6_errors(tbl jsonb, yeast jsonb)
returns text[]
language plpgsql
stable
as $$
declare
    pre     text := 'step 6: ';
    rules   jsonb := coalesce(tbl -> 'yeast_rules', '{}'::jsonb);
    main_id bigint := (yeast #>> '{main,ingredient_id}')::bigint;
    sour_id bigint := (yeast #>> '{souring,ingredient_id}')::bigint;
    picks   jsonb := jsonb_build_array(jsonb_build_object('ingredient_id', main_id, 'choice', null));
    errs    text[];
    m       jsonb;
    s       jsonb;
    fam     text;
    x       jsonb;
    v_ids   bigint[];
    v_cands boolean;
begin
    if sour_id is not null then
        picks := picks || jsonb_build_object('ingredient_id', sour_id, 'choice', null);
    end if;
    errs := app.choose_pick_errors(6, 'yeast', tbl, picks);
    m := app.choose_row(tbl, main_id);
    s := case when sour_id is null then null else app.choose_row(tbl, sour_id) end;

    if m is not null and m ->> 'kind' = 'yeast' then
        if m ->> 'type' = 'lacto' then
            errs := errs || (pre || (m ->> 'name') || ' is a lacto culture; it goes in souring, and the main yeast is a brewing yeast');
        elsif m ->> 'type' is null or m ->> 'type' not in ('ale', 'lager', 'kveik') then
            errs := errs || (pre || (m ->> 'name') || ' is not a brewing yeast (type ' || coalesce(m ->> 'type', 'none')
                             || '); the main yeast is an ale, lager or kveik yeast');
        end if;
        if (rules ->> 'lager')::boolean and m ->> 'type' is distinct from 'lager' then
            errs := errs || (pre || (m ->> 'name') || ' is not a lager yeast, and ' || (tbl ->> 'style_used') || ' is a lager style');
        end if;
        for fam in select jsonb_array_elements_text(coalesce(rules -> 'families', '[]'::jsonb)) loop
            if not (m -> 'family') ? fam then
                errs := errs || (pre || (m ->> 'name') || ' is not in the yeast family ' || fam
                                 || ', which ' || (tbl ->> 'style_used') || ' requires');
            end if;
        end loop;
        -- R5: the attenuation reaches the band, when some usable yeast does
        if (m -> 'overlaps_band') = 'false'::jsonb
           and m ->> 'inventory' is null and jsonb_typeof(m -> 'wanted') <> 'object'
           and exists (
                select 1 from jsonb_array_elements(tbl -> 'yeasts') y
                 where y.value -> 'overlaps_band' = 'true'::jsonb and y.value ->> 'type' <> 'lacto'
                   and (not (rules ->> 'lager')::boolean or y.value ->> 'type' = 'lager')
                   and not exists (select 1 from jsonb_array_elements_text(coalesce(rules -> 'families', '[]'::jsonb)) f
                                    where not (y.value -> 'family') ? f.value)) then
            errs := errs || (pre || (m ->> 'name') || ' attenuates ' || app.choose_span(m -> 'attenuation')
                             || ' %, which does not reach the band ' || app.choose_num(tbl #> '{band,yeast_low_pct}') || '-'
                             || app.choose_num(tbl #> '{band,yeast_high_pct}') || ' %; pick a yeast that does');
        end if;
    end if;

    -- the souring culture
    if (rules ->> 'souring')::boolean then
        if sour_id is null then
            errs := errs || (pre || 'the style is sour: add a souring culture (type lacto) in souring');
        end if;
    elsif s is not null and s ->> 'kind' = 'yeast' and s ->> 'inventory' is null and jsonb_typeof(s -> 'wanted') <> 'object' then
        errs := errs || (pre || (s ->> 'name') || ' is a souring culture, but the style is not sour and none was asked for; use null');
    end if;
    if s is not null and s ->> 'kind' = 'yeast' and s ->> 'type' is distinct from 'lacto' then
        errs := errs || (pre || (s ->> 'name') || ' is not a lacto culture, so it cannot be the souring culture');
    end if;

    -- R3: the inventory yeasts. Lacto-only words must be used; of the other words one is enough.
    v_ids := array_remove(array[main_id, sour_id], null);
    v_cands := false;
    for x in select w.value from jsonb_array_elements(coalesce(tbl -> 'inventory_words', '[]'::jsonb)) w
              where w.value ->> 'kind' = 'yeast' and (w.value ->> 'fits')::boolean
                and jsonb_array_length(w.value -> 'ids') > 0 loop
        if not exists (select 1 from jsonb_array_elements_text(x -> 'ids') i
                        where app.choose_row(tbl, i.value::bigint) ->> 'type' is distinct from 'lacto') then
            if not exists (select 1 from jsonb_array_elements_text(x -> 'ids') i where i.value::bigint = any (v_ids)) then
                errs := errs || (pre || 'the inventory "' || (x ->> 'word') || '" fits this recipe and must be used as the souring culture; pick one of: '
                                 || app.choose_names(tbl, x -> 'ids'));
            end if;
        else
            v_cands := true;
        end if;
    end loop;
    if v_cands and not exists (
            select 1 from jsonb_array_elements(tbl -> 'inventory_words') w
             where w.value ->> 'kind' = 'yeast' and (w.value ->> 'fits')::boolean
               and exists (select 1 from jsonb_array_elements_text(w.value -> 'ids') i
                            where i.value::bigint = main_id
                              and app.choose_row(tbl, i.value::bigint) ->> 'type' is distinct from 'lacto')) then
        errs := errs || (pre || 'the inventory has a yeast that fits this recipe and the main yeast must be one of them: '
                         || (select string_agg(app.choose_names(tbl, w.value -> 'ids'), '; ')
                               from jsonb_array_elements(tbl -> 'inventory_words') w
                              where w.value ->> 'kind' = 'yeast' and (w.value ->> 'fits')::boolean
                                and jsonb_array_length(w.value -> 'ids') > 0));
    end if;
    return errs;
end
$$;

-- Step 7: the fermentables. Each product once, the shares add up to 100, each at most its max_pct.
create or replace function app.step7_errors(tbl jsonb, fermentables jsonb)
returns text[]
language plpgsql
stable
as $$
declare
    pre   text := 'step 7: ';
    errs  text[];
    f     jsonb;
    r     jsonb;
    v_sum numeric;
begin
    errs := app.choose_pick_errors(7, 'fermentable', tbl,
        (select coalesce(jsonb_agg(jsonb_build_object('ingredient_id', f.value -> 'ingredient_id', 'choice', f.value -> 'usage')), '[]'::jsonb)
           from jsonb_array_elements(fermentables) f));
    for f in select value from jsonb_array_elements(fermentables) loop
        r := app.choose_row(tbl, (f ->> 'ingredient_id')::bigint);
        if r is not null and r ->> 'kind' = 'fermentable' and jsonb_typeof(r -> 'max_pct') = 'number'
           and (f ->> 'pct')::numeric > (r ->> 'max_pct')::numeric then
            errs := errs || (pre || (r ->> 'name') || ' is ' || app.choose_num(f -> 'pct') || ' % of the grist, above its maximum of '
                             || app.choose_num(r -> 'max_pct') || ' %');
        end if;
    end loop;
    for f in select (d.id)::text::jsonb from (
                 select (x.value ->> 'ingredient_id') as id from jsonb_array_elements(fermentables) x
                  group by 1 having count(*) > 1) d loop
        errs := errs || (pre || 'id ' || f || ' is picked more than once; use one entry');
    end loop;
    select coalesce(sum((x.value ->> 'pct')::numeric), 0) into v_sum from jsonb_array_elements(fermentables) x;
    if abs(v_sum - 100) > 0.1 then
        errs := errs || (pre || 'the fermentable shares add up to ' || app.choose_num(to_jsonb(v_sum)) || ', not 100');
    end if;
    return errs;
end
$$;

-- Step 8: the hops. Each addition sits at a choice of its product (a boil addition at the choice
-- whose minutes band holds its minutes), the shares add up to 100, and a recipe with an IBU target
-- has a boil addition (app.solve_hops needs one). Minutes: boil 0-90, whirlpool 0-60, dry hop 0
-- (contact time is M7's).
create or replace function app.step8_errors(tbl jsonb, hops jsonb)
returns text[]
language plpgsql
stable
as $$
declare
    pre     text := 'step 8: ';
    errs    text[];
    picks   jsonb := '[]'::jsonb;
    h       jsonb;
    r       jsonb;
    v_label text;
    v_min   numeric;
    v_sum   numeric;
    v_ibu   numeric := (tbl #>> '{targets,ibu}')::numeric;
begin
    for h in select value from jsonb_array_elements(hops) loop
        r := app.choose_row(tbl, (h ->> 'ingredient_id')::bigint);
        v_min := (h ->> 'minutes')::numeric;
        v_label := null;
        if r is not null and r ->> 'kind' = 'hop' then
            v_label := case h ->> 'usage'
                when 'whirlpool' then 'whirlpool'
                when 'dry_hop' then 'dry hop'
                else (select l.value ->> 'choice' from jsonb_array_elements(r -> 'levels') l
                       where l.value ->> 'usage' = 'boil' and (l.value ->> 'minutes')::numeric <= v_min
                       order by (l.value ->> 'minutes')::numeric desc limit 1) end;
            if not exists (select 1 from jsonb_array_elements(r -> 'levels') l where l.value ->> 'choice' = v_label) then
                errs := errs || (pre || (r ->> 'name') || ' has no ' || replace(h ->> 'usage', '_', ' ')
                                 || ' choice' || case when h ->> 'usage' = 'boil' then ' for ' || app.choose_num(h -> 'minutes') || ' min' else '' end
                                 || ' (a feature hop is not boiled early)');
                v_label := null;
            end if;
        end if;
        picks := picks || jsonb_build_object('ingredient_id', h -> 'ingredient_id', 'choice', v_label);

        if h ->> 'usage' = 'boil' and v_min > 90 then
            errs := errs || (pre || 'a boil addition of ' || app.choose_num(h -> 'minutes') || ' min is longer than 90 min');
        elsif h ->> 'usage' = 'whirlpool' and v_min > 60 then
            errs := errs || (pre || 'a whirlpool addition of ' || app.choose_num(h -> 'minutes') || ' min is longer than 60 min');
        elsif h ->> 'usage' = 'dry_hop' and v_min <> 0 then
            errs := errs || (pre || 'a dry hop addition has minutes 0 (contact time is set later)');
        end if;
    end loop;
    errs := app.choose_pick_errors(8, 'hop', tbl, picks) || errs;

    select coalesce(sum((x.value ->> 'share_pct')::numeric), 0) into v_sum from jsonb_array_elements(hops) x;
    if (jsonb_array_length(hops) > 0 or coalesce(v_ibu, 0) > 0) and abs(v_sum - 100) > 0.1 then
        errs := errs || (pre || 'the hop shares add up to ' || app.choose_num(to_jsonb(v_sum)) || ', not 100');
    end if;
    if coalesce(v_ibu, 0) > 0 and not exists (select 1 from jsonb_array_elements(hops) x where x.value ->> 'usage' = 'boil') then
        errs := errs || (pre || 'the recipe needs ' || app.choose_num(to_jsonb(v_ibu)) || ' IBU, so at least one hop is a boil addition');
    end if;
    return errs;
end
$$;

-- Step 9: the extras. A usage from the product's row, each product once, one extra per wanted misc.
-- The model gives no dose; the contract refuses the field and code sets it from app.misc_dose.
create or replace function app.step9_errors(tbl jsonb, extras jsonb)
returns text[]
language plpgsql
stable
as $$
declare
    pre  text := 'step 9: ';
    errs text[];
    x    jsonb;
    r    jsonb;
    s    jsonb;
    n    int;
begin
    errs := app.choose_pick_errors(9, 'misc', tbl,
        (select coalesce(jsonb_agg(jsonb_build_object('ingredient_id', e.value -> 'ingredient_id', 'choice', e.value -> 'usage')), '[]'::jsonb)
           from jsonb_array_elements(extras) e));
    for x in select value from jsonb_array_elements(extras) loop
        r := app.choose_row(tbl, (x ->> 'ingredient_id')::bigint);
        if r is not null and r ->> 'kind' = 'misc' and not (r -> 'usages') ? (x ->> 'usage') then
            errs := errs || (pre || (r ->> 'name') || ' cannot be used as "' || (x ->> 'usage') || '"; its usages are: '
                             || (select string_agg(u.value, ', ') from jsonb_array_elements_text(r -> 'usages') u));
        end if;
    end loop;
    for x in select (d.id)::text::jsonb from (
                 select (e.value ->> 'ingredient_id') as id from jsonb_array_elements(extras) e
                  group by 1 having count(*) > 1) d loop
        errs := errs || (pre || 'id ' || x || ' is picked more than once; use one entry');
    end loop;
    for s in select sl.value from jsonb_array_elements(coalesce(tbl -> 'slots', '[]'::jsonb)) sl
              where sl.value ->> 'kind' = 'misc' and jsonb_array_length(sl.value -> 'ids') > 0 loop
        select count(*) into n from jsonb_array_elements(extras) e
         where (e.value ->> 'ingredient_id')::bigint in (select i.value::bigint from jsonb_array_elements_text(s -> 'ids') i);
        if n > 1 then
            errs := errs || (pre || 'the wanted "' || (s ->> 'item') || '" has ' || n || ' picks; use one');
        end if;
    end loop;
    return errs;
end
$$;

-- All four lists in step order.
create or replace function app.choose_check(tbl jsonb, proposal jsonb)
returns text[]
language sql
stable
as $$
    select app.step6_errors(tbl, proposal -> 'yeast')
        || app.step7_errors(tbl, proposal -> 'fermentables')
        || app.step8_errors(tbl, proposal -> 'hops')
        || app.step9_errors(tbl, proposal -> 'extras')
$$;

-- Reads the model's answer for steps 6-9, as app.step1_read_answer does for step 1: the text must
-- be JSON, match the contract (errors start "contract: "), then pass app.choose_check.
create or replace function app.choose_read_answer(content text, contract json, tbl jsonb)
returns table (proposal jsonb, errors text[])
language plpgsql
stable
as $$
declare
    answer   jsonb;
    problems text[];
begin
    begin
        answer := content::jsonb;
    exception when others then
        return query select null::jsonb, array['answer is not JSON: ' || sqlerrm];
        return;
    end;
    problems := array(select 'contract: ' || e
                        from unnest(coalesce(extensions.jsonschema_validation_errors(contract, answer::json), '{}')) e);
    if cardinality(problems) = 0 then
        problems := app.choose_check(tbl, answer);
    end if;
    return query select answer, problems;
end
$$;
