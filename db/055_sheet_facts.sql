-- Step 16 gathers its facts and finds its sources (docs/work/m8-recipe-sheet-chat, Task 4). No LLM.
--   app.sheet_facts(run_id)          the run's saved recipe, its style, step 2, steps 6-10 of the passed try,
--                                    the process (it holds steps 12-15), the choices to explain, and the
--                                    numbers the prose may use
--   app.sheet_allowed_numbers(facts) those numbers, as a list
--   app.sheet_queries(facts)         one retrieval query per topic
--   app.sheet_sources(queries, embeddings, per_query)
--                                    the chunks to cite: How to Brew first (PROJECT.md §6.9)
-- app.sheet_ranges and app.sheet_style are small helpers of the first one.
-- Needs: db/048_save_recipe.sql (app.recipe), db/040_kb_search.sql, db/054_recipe_sheet.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/055_sheet_facts.sql
-- Idempotent: safe to re-run.

-- The five ranges of a style as {og: {low, high}, ...}. A missing range gives nulls.
create or replace function app.sheet_ranges(style_id bigint)
returns jsonb
language sql
stable
as $$
    select jsonb_build_object(
        'og',  jsonb_build_object('low', lower(og),  'high', upper(og)),
        'fg',  jsonb_build_object('low', lower(fg),  'high', upper(fg)),
        'ibu', jsonb_build_object('low', lower(ibu), 'high', upper(ibu)),
        'srm', jsonb_build_object('low', lower(srm), 'high', upper(srm)),
        'abv', jsonb_build_object('low', lower(abv), 'high', upper(abv)))
    from ref.beer_style where id = style_id
$$;

-- A style by code, BJCP before BA, with its name, guide and ranges. Null when the code is unknown.
create or replace function app.sheet_style(code text)
returns jsonb
language sql
stable
as $$
    select jsonb_build_object('id', s.id, 'code', s.code, 'name', s.name, 'guide', s.guide,
                              'ranges', app.sheet_ranges(s.id))
    from ref.beer_style s
    where s.code = sheet_style.code
    order by (s.guide = 'BJCP') desc
    limit 1
$$;

-- The fields of step 6-9 entries that the sheet explains (not their long bookkeeping).
create or replace function app.sheet_entries(entries jsonb)
returns jsonb
language sql
immutable
as $$
    select coalesce(jsonb_agg(jsonb_build_object(
        'ingredient_id', e->'ingredient_id', 'name', e->'name', 'because', e->'because',
        'level', e->'level', 'level_because', e->'level_because', 'inventory', e->'inventory',
        'wanted', e->'wanted')), '[]'::jsonb)
    from jsonb_array_elements(case jsonb_typeof(entries) when 'array' then entries
                                   when 'object' then jsonb_build_array(entries)
                                   else '[]'::jsonb end) e
$$;

create or replace function app.sheet_facts(run_id bigint)
returns jsonb
language plpgsql
stable
as $$
declare
    rec     app.recipe%rowtype;
    st      jsonb;
    t       integer;
    s2      jsonb;
    s6      jsonb;
    s7      jsonb;
    s8      jsonb;
    s9      jsonb;
    s10     jsonb;
    named   jsonb;
    styles  jsonb;
    items   jsonb;
    choices jsonb;
begin
    select r.* into rec from app.recipe r join app.run u on u.recipe_id = r.id where u.id = sheet_facts.run_id;
    if not found then
        raise exception 'sheet_facts: run % has no saved recipe', sheet_facts.run_id;
    end if;
    if rec.process is null then
        raise exception 'sheet_facts: recipe % has no process', rec.id;
    end if;

    -- The try whose step 11 passed: steps 6-10 of that try are the ones the recipe was built from.
    select s.try into t from app.run_step s
    where s.run_id = sheet_facts.run_id and s.step = 11 and (s.output->>'passed')::boolean
    order by s.try limit 1;
    if t is null then
        raise exception 'sheet_facts: run % has no passed step 11', sheet_facts.run_id;
    end if;

    select s.output into s2 from app.run_step s
    where s.run_id = sheet_facts.run_id and s.step = 2 order by s.try limit 1;
    select s.output into s6 from app.run_step s where s.run_id = sheet_facts.run_id and s.step = 6 and s.try = t;
    select s.output into s7 from app.run_step s where s.run_id = sheet_facts.run_id and s.step = 7 and s.try = t;
    select s.output into s8 from app.run_step s where s.run_id = sheet_facts.run_id and s.step = 8 and s.try = t;
    select s.output into s9 from app.run_step s where s.run_id = sheet_facts.run_id and s.step = 9 and s.try = t;
    select s.output into s10 from app.run_step s where s.run_id = sheet_facts.run_id and s.step = 10 and s.try = t;

    select jsonb_build_object('id', b.id, 'code', b.code, 'name', b.name, 'guide', b.guide,
                              'ranges', app.sheet_ranges(b.id),
                              'overall_impression', b.raw->>'overallimpression',
                              'co2_family', b.co2_family,
                              'co2_vol', jsonb_build_object('low', lower(b.co2_vol), 'high', upper(b.co2_vol)))
    into st from ref.beer_style b where b.id = rec.style_id;

    -- The styles step 2 named besides the chosen one: its alternatives and the style of a mismatch.
    select coalesce(jsonb_agg(x), '[]'::jsonb) into styles from (
        select distinct on (x->>'code') x from (
            select app.sheet_style(c) as x
            from jsonb_array_elements_text(coalesce(s2->'alt_styles', '[]'::jsonb)) c
            union all
            select app.sheet_style(split_part(s2->'mismatch'->>'named', ' ', 1))
        ) u where x is not null order by x->>'code') d;
    named := app.sheet_style(split_part(s2->'mismatch'->>'named', ' ', 1));

    select coalesce(jsonb_agg(jsonb_build_object(
               'id', i.id, 'ingredient_id', i.ingredient_id, 'name', i.raw_name, 'usage', i.usage,
               'time_min', i.time_min, 'pct', i.pct, 'amount', i.amount, 'unit', i.unit,
               'kind', case when exists (select 1 from ref.fermentable f where f.ingredient_id = i.ingredient_id) then 'fermentable'
                            when exists (select 1 from ref.hop h where h.ingredient_id = i.ingredient_id) then 'hop'
                            when exists (select 1 from ref.yeast y where y.ingredient_id = i.ingredient_id) then 'yeast'
                            else 'extra' end) order by i.id), '[]'::jsonb)
    into items from app.recipe_item i where i.recipe_id = rec.id;

    -- One choice per style, per distinct ingredient and per process section: each gets a "why" line.
    -- An ingredient's reason and inventory flag come from its entry in step 6, 7, 8 or 9.
    select jsonb_agg(c order by o) into choices from (
        select 0 as o, jsonb_build_object('key', 'style', 'label', st->>'code' || ' ' || (st->>'name'),
                                          'because', s2->'reason') as c
        union all
        select 1 + array_position(array['fermentable', 'hop', 'yeast', 'extra'], i.kind) * 1000 + min(i.id)::integer,
               jsonb_build_object(
                   'key', i.kind || ':' || coalesce(i.ingredient_id::text, i.name),
                   'label', i.name, 'kind', i.kind,
                   'because', e->'because', 'level', e->'level', 'inventory', e->'inventory', 'wanted', e->'wanted')
        from (select x->>'name' as name, x->>'kind' as kind, nullif(x->>'ingredient_id', '')::bigint as ingredient_id,
                     (x->>'id')::bigint as id
              from jsonb_array_elements(items) x) i
        left join lateral (
            select entry as e from jsonb_array_elements(
                case i.kind when 'fermentable' then app.sheet_entries(s7->'fermentables')
                            when 'hop' then app.sheet_entries(s8->'hops')
                            when 'yeast' then app.sheet_entries(s6->'yeast')
                            else app.sheet_entries(s9->'extras') end) entry
            where (entry->>'ingredient_id')::bigint = i.ingredient_id limit 1) en on true
        group by i.kind, i.ingredient_id, i.name, e
        union all
        select 90000 + n, jsonb_build_object('key', k, 'label', l)
        from (values (1, 'water', 'Water'), (2, 'mash', 'Mash'), (3, 'boil', 'Boil'),
                     (4, 'fermentation', 'Fermentation'), (5, 'packaging', 'Packaging')) v(n, k, l)
    ) all_choices;

    return jsonb_build_object(
        'try', t,
        'recipe', jsonb_build_object('id', rec.id, 'status', rec.status, 'batch_l', rec.batch_l,
                                     'efficiency_pct', rec.efficiency_pct, 'og', rec.og, 'fg', rec.fg,
                                     'abv', rec.abv, 'ibu', rec.ibu, 'srm', rec.srm, 'targets', rec.targets,
                                     'calc_version', rec.calc_version),
        'style', st,
        'step2', jsonb_build_object('reason', s2->'reason', 'alt_styles', coalesce(s2->'alt_styles', '[]'::jsonb),
                                    'mismatch', s2->'mismatch', 'named', named, 'styles', styles),
        'items', items,
        'deviations', coalesce((select jsonb_agg(jsonb_build_object(
                                    'subject', d.subject, 'kind', d.kind, 'level', d.level,
                                    'requested_by', d.requested_by, 'note', d.note) order by d.id)
                                from app.recipe_deviation d where d.recipe_id = rec.id), '[]'::jsonb),
        'process', rec.process,
        'step6', jsonb_build_object('yeast', app.sheet_entries(s6->'yeast'),
                                    'absent', coalesce(s6->'absent', '[]'::jsonb),
                                    'unused_inventory', coalesce(s6->'unused_inventory', '[]'::jsonb)),
        'step7', jsonb_build_object('fermentables', app.sheet_entries(s7->'fermentables'),
                                    'absent', coalesce(s7->'absent', '[]'::jsonb),
                                    'unused_inventory', coalesce(s7->'unused_inventory', '[]'::jsonb)),
        'step8', jsonb_build_object('hops', app.sheet_entries(s8->'hops'),
                                    'absent', coalesce(s8->'absent', '[]'::jsonb),
                                    'unused_inventory', coalesce(s8->'unused_inventory', '[]'::jsonb)),
        'step9', jsonb_build_object('extras', app.sheet_entries(s9->'extras'),
                                    'absent', coalesce(s9->'absent', '[]'::jsonb),
                                    'unused_inventory', coalesce(s9->'unused_inventory', '[]'::jsonb)),
        'step10', jsonb_build_object('values_used', coalesce(s10->'values_used', '[]'::jsonb),
                                     'colour_because', s10->'colour'->'because',
                                     'og_used', s10->'og_used', 'rounding', s10->'rounding'),
        'choices', choices)
        || jsonb_build_object('allowed_numbers', to_jsonb(app.sheet_allowed_numbers(
               jsonb_build_object('recipe', jsonb_build_object('id', rec.id) || jsonb_build_object(
                                      'batch_l', rec.batch_l, 'efficiency_pct', rec.efficiency_pct, 'og', rec.og,
                                      'fg', rec.fg, 'abv', rec.abv, 'ibu', rec.ibu, 'srm', rec.srm,
                                      'targets', rec.targets),
                                  'style', st, 'items', items, 'process', rec.process,
                                  'step2', jsonb_build_object('mismatch', s2->'mismatch', 'named', named,
                                                              'styles', styles)))));
end;
$$;

-- The numbers the prose may use (docs/work/m8-recipe-sheet-chat/plan.md, "The check"): every numeric value of
-- the saved recipe (its row, targets and process; item amounts, percentages and times), every range bound of the
-- chosen style and of the styles step 2 named, and the numbers inside ingredient and style names ("S-04").
-- Reads facts' recipe, style, items, process and step2 parts. Distinct, ascending.
create or replace function app.sheet_allowed_numbers(facts jsonb)
returns numeric[]
language sql
immutable
as $$
    select coalesce(array_agg(distinct n order by n), '{}'::numeric[]) from (
        select (v #>> '{}')::numeric as n from (
            select jsonb_path_query((facts->'recipe') - array['id', 'status', 'calc_version']::text[],
                                    'strict $.** ? (@.type() == "number")') v
            union all select jsonb_path_query(facts->'process', 'strict $.** ? (@.type() == "number")')
            union all select jsonb_path_query(facts->'items', 'strict $[*].amount')
            union all select jsonb_path_query(facts->'items', 'strict $[*].pct ? (@.type() == "number")')
            union all select jsonb_path_query(facts->'items', 'strict $[*].time_min ? (@.type() == "number")')
            union all select jsonb_path_query(facts->'style'->'ranges', 'strict $.** ? (@.type() == "number")')
            union all select jsonb_path_query(facts->'style'->'co2_vol', 'strict $.** ? (@.type() == "number")')
            union all select jsonb_path_query(facts->'step2'->'styles', 'strict $[*].ranges.** ? (@.type() == "number")')
            union all select jsonb_path_query(facts->'step2'->'named'->'ranges', 'strict $.** ? (@.type() == "number")')
        ) numbers
        union
        select m[1]::numeric
        from (select facts->'style'->>'name' as t
              union all select x->>'name' from jsonb_array_elements(facts->'items') x
              union all select x->>'name' from jsonb_array_elements(facts->'step2'->'styles') x
              union all select facts->'step2'->'mismatch'->>'named') names,
             regexp_matches(names.t, '([0-9]+(?:\.[0-9]+)?)', 'g') m
    ) all_numbers
$$;

-- One retrieval query per topic, built from names in the facts.
create or replace function app.sheet_queries(facts jsonb)
returns jsonb
language sql
immutable
as $$
    with n as (
        select facts->'style'->>'name' as style,
               (select string_agg(x->>'label', ' ' order by ord) from jsonb_array_elements(facts->'choices') with ordinality c(x, ord)
                where x->>'kind' = 'fermentable') as grist,
               (select string_agg(x->>'label', ' ' order by ord) from jsonb_array_elements(facts->'choices') with ordinality c(x, ord)
                where x->>'kind' = 'hop') as hops,
               (select string_agg(x->>'label', ' ' order by ord) from jsonb_array_elements(facts->'choices') with ordinality c(x, ord)
                where x->>'kind' = 'yeast') as yeast)
    select jsonb_build_array(
        jsonb_build_object('topic', 'style', 'text', style || ' beer style character and history'),
        jsonb_build_object('topic', 'grist', 'text', style || ' ' || coalesce(grist, '') || ' grain bill malt'),
        jsonb_build_object('topic', 'hops', 'text', style || ' ' || coalesce(hops, '') || ' hop bitterness schedule'),
        jsonb_build_object('topic', 'yeast', 'text', style || ' ' || coalesce(yeast, '') || ' yeast pitching rate'),
        jsonb_build_object('topic', 'water', 'text', 'brewing water minerals salts mash pH ' || style),
        jsonb_build_object('topic', 'mash', 'text', 'mash temperature saccharification rest ' || style),
        jsonb_build_object('topic', 'boil', 'text', 'boil time hop additions wort ' || style),
        jsonb_build_object('topic', 'fermentation', 'text', 'fermentation temperature schedule conditioning ' || style),
        jsonb_build_object('topic', 'packaging', 'text', 'priming sugar carbonation bottling CO2 volumes ' || style))
    from n
$$;

-- The chunks to cite. `queries` is the output of app.sheet_queries and `embeddings` the bge-m3 vector of each
-- query's text, in the same order. Per query: app.kb_search top 10, then How to Brew chunks first (by score),
-- then the rest (by score), `per_query` kept. A chunk is kept once, under the first topic that found it.
create or replace function app.sheet_sources(queries jsonb, embeddings jsonb, per_query integer default 3)
returns jsonb
language plpgsql
stable
set search_path = public, extensions
as $$
declare
    i    integer;
    q    jsonb;
    seen bigint[] := '{}';
    kept jsonb := '[]'::jsonb;
    r    record;
begin
    if per_query is null or per_query <= 0 then
        return '[]'::jsonb;
    end if;
    for i in 0 .. jsonb_array_length(queries) - 1 loop
        q := queries->i;
        for r in
            select * from app.kb_search(q->>'text', (embeddings->i)::text::extensions.vector(1024), 10)
            where not (chunk_id = any (seen))
            order by (source_slug = 'palmer-how-to-brew') desc, score desc, chunk_id
            limit per_query
        loop
            seen := seen || r.chunk_id;
            kept := kept || jsonb_build_array(jsonb_build_object(
                'chunk_id', r.chunk_id, 'topic', q->>'topic', 'source_slug', r.source_slug,
                'title', r.source_title, 'url', r.source_url, 'section_path', r.section_path,
                'page', r.page, 'text', r.text));
        end loop;
    end loop;
    return kept;
end;
$$;

-- The user message of the step 16 model call (docs/work/m8-recipe-sheet-chat, Task 5): the facts in labelled
-- sections, then the keys to write a "why" for, then the sources. The numbers are the saved ones, written as
-- they are stored; the model may repeat them and may not make up others. Sources are
-- "[<chunk_id>] <title> - <section>: <text>".
create or replace function app.sheet_prompt(facts jsonb, sources jsonb)
returns text
language plpgsql
immutable
as $$
declare
    st    jsonb := facts->'style';
    rc    jsonb := facts->'recipe';
    pr    jsonb := facts->'process';
    s2    jsonb := facts->'step2';
    out   text;
    c     jsonb;
    x     jsonb;
    extra text;
begin
    out := format(E'STYLE\n%s %s (%s guide)\nOG %s-%s, FG %s-%s, IBU %s-%s, SRM %s-%s, ABV %s-%s\nOverall impression: %s\nWhy this style: %s\n',
        st->>'code', st->>'name', st->>'guide',
        st#>>'{ranges,og,low}', st#>>'{ranges,og,high}', st#>>'{ranges,fg,low}', st#>>'{ranges,fg,high}',
        st#>>'{ranges,ibu,low}', st#>>'{ranges,ibu,high}', st#>>'{ranges,srm,low}', st#>>'{ranges,srm,high}',
        st#>>'{ranges,abv,low}', st#>>'{ranges,abv,high}', st->>'overall_impression', s2->>'reason');
    if s2->'mismatch' is not null and s2->>'mismatch' <> 'null' then
        out := out || format(E'Style mismatch: %s\n', s2->>'mismatch');
    end if;
    if jsonb_array_length(coalesce(s2->'alt_styles', '[]'::jsonb)) > 0 then
        out := out || format(E'Other styles considered: %s\n',
                             (select string_agg(a, ', ') from jsonb_array_elements_text(s2->'alt_styles') a));
    end if;

    out := out || format(E'\nRECIPE\nBatch %s L, efficiency %s %%, OG %s, FG %s, ABV %s %%, IBU %s, SRM %s\n',
        rc->>'batch_l', rc->>'efficiency_pct', rc->>'og', rc->>'fg', rc->>'abv', rc->>'ibu', rc->>'srm');
    for x in select * from jsonb_array_elements(facts->'items') loop
        out := out || format(E'- %s: %s %s%s%s%s\n', x->>'name', x->>'amount', x->>'unit',
                             case when x->>'pct' is not null then ', ' || (x->>'pct') || ' %' else '' end,
                             case when x->>'usage' is not null then ', ' || (x->>'usage') else '' end,
                             case when x->>'time_min' is not null then ', ' || (x->>'time_min') || ' min' else '' end);
    end loop;

    out := out || E'\nKEYS TO WRITE (one "why" for each key, in this order)\n';
    for c in select * from jsonb_array_elements(facts->'choices') loop
        extra := case c->>'key'
            when 'water' then format('target %s (%s, %s); salts: %s; mash pH %s (estimate); %s',
                pr#>>'{water,target,row}', pr#>>'{water,target,from}', pr#>>'{water,target,basis}',
                (select coalesce(string_agg(format('%s %s g', s->>'name', s->>'total_g'), ', '), 'none')
                 from jsonb_array_elements(coalesce(pr#>'{water,salts}', '[]'::jsonb)) s),
                pr#>>'{water,mash_ph,ph}', pr#>>'{water,acid,text}')
            when 'mash' then format('strike %s C, %s',
                pr#>>'{mash,strike_c}',
                (select string_agg(format('%s %s C %s min', s->>'name', s->>'temp_c', s->>'minutes'), '; ')
                 from jsonb_array_elements(coalesce(pr#>'{mash,steps}', '[]'::jsonb)) s))
            when 'boil' then format('%s min. %s', pr#>>'{boil,boil_min}', pr#>>'{boil,because}')
            when 'fermentation' then (select string_agg(format('%s %s C %s days', s->>'phase', s->>'temp_c', s->>'days'), '; ')
                 from jsonb_array_elements(coalesce(pr#>'{fermentation,steps}', '[]'::jsonb)) s)
            when 'packaging' then format('CO2 %s volumes (%s, %s); priming %s g %s',
                pr#>>'{packaging,co2,volumes}', pr#>>'{packaging,co2,family}', pr#>>'{packaging,co2,basis}',
                pr#>>'{packaging,priming,g}', pr#>>'{packaging,priming,sugar}')
            else null end;
        out := out || format(E'- %s | %s%s%s%s%s\n', c->>'key', c->>'label',
            case when c->>'because' is not null and c->>'because' <> 'null' then ' | reason: ' || (c->>'because') else '' end,
            case when c->>'level' is not null and c->>'level' <> 'null' then ' | level in the style: ' || (c->>'level') else '' end,
            case when c->>'inventory' = 'true' then ' | from the brewer''s inventory' else '' end,
            case when extra is not null then ' | facts: ' || extra else '' end);
    end loop;

    out := out || E'\nSOURCES\n';
    if jsonb_array_length(coalesce(sources, '[]'::jsonb)) = 0 then
        out := out || E'(none)\n';
    end if;
    for x in select * from jsonb_array_elements(coalesce(sources, '[]'::jsonb)) loop
        out := out || format(E'[%s] %s - %s: %s\n', x->>'chunk_id', x->>'title', x->>'section_path', x->>'text');
    end loop;
    return out;
end;
$$;
