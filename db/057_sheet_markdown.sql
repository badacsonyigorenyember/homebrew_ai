-- Code writes the recipe sheet in Markdown (docs/work/m8-recipe-sheet-chat, Task 6). No LLM, no maths: every
-- quantity is a saved value (the facts of app.sheet_facts) shown at its display precision; the model's answer
-- (app.sheet_read_answer) only supplies the prose, placed next to the item or section it explains.
--   app.sheet_markdown(facts, sources, answer)   the whole sheet, calling one helper per section in R2's order:
--       sheet_sec_style, _results, _items (fermentables, hops, yeast, extras), _worked, _water, _mash, _boil,
--       _ferment, _packaging, _deviations, _absent, _notes, _sources
-- Display precision: gravity 3 decimals; ABV, %, deg C and L 1 decimal (pH 2, CO2 volumes 2); kg 2 decimals;
-- g and minutes whole, except water salts (1 decimal, they are small amounts).
-- Citations are numbered in order of first use on the sheet (style, items, water ... packaging, then the notes)
-- and listed at the end: a book chunk "<title>, PDF p. <page> - <section>", an article "<title> - <section> - <url>".
-- Needs: db/055_sheet_facts.sql (the shape of the facts).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/057_sheet_markdown.sql
-- Idempotent: safe to re-run.

-- A number at a fixed number of decimals; a null places picks 0 for a whole number and 1 otherwise; null gives a dash.
create or replace function app.sheet_num(x numeric, places integer)
returns text
language sql
immutable
as $$
    select case when x is null then '–'
                else to_char(round(x, p), 'FM999999990' || case when p > 0 then '.' || repeat('0', p) else '' end) end
    from (select coalesce(places, case when x = round(x) then 0 else 1 end) as p) q
$$;

-- A number without trailing zeros (days, odd units).
create or replace function app.sheet_trim(x numeric)
returns text
language sql
immutable
as $$ select case when x is null then '–' else trim_scale(x)::text end $$;

-- "<amount> <unit>": kg 2 decimals (under 0.1 kg as whole grams, so a tiny amount is not "0.00 kg"),
-- g whole, any other unit as stored.
create or replace function app.sheet_amount(amount numeric, unit text)
returns text
language sql
immutable
as $$
    select case when unit = 'kg' and abs(amount) < 0.1 then app.sheet_num(amount * 1000, 0) || ' g'
                else case unit when 'kg' then app.sheet_num(amount, 2) when 'g' then app.sheet_num(amount, 0)
                              else app.sheet_trim(amount) end || ' ' || coalesce(unit, '') end
$$;

-- "low–high" at `places` decimals (null places: whole when whole).
create or replace function app.sheet_range(r jsonb, places integer)
returns text
language sql
immutable
as $$
    select case when r is null or r->'low' is null or r->>'low' is null then '–'
                else app.sheet_num((r->>'low')::numeric, places) || '–' || app.sheet_num((r->>'high')::numeric, places) end
$$;

-- The chunk ids the sheet cites, in order of first use on the sheet.
create or replace function app.sheet_cite_order(facts jsonb, answer jsonb)
returns bigint[]
language sql
immutable
as $$
    select coalesce(array_agg(id order by pos), '{}'::bigint[]) from (
        select id, min(pos) as pos from (
            select c.v::bigint as id, coalesce(ch.ord, 999) * 1000 + c.ord as pos
            from jsonb_array_elements(coalesce(answer->'why', '[]'::jsonb)) w
            cross join lateral jsonb_array_elements_text(w.value->'cite') with ordinality c(v, ord)
            left join lateral (select t.ord from jsonb_array_elements(facts->'choices') with ordinality t(x, ord)
                               where t.x->>'key' = w.value->>'key' limit 1) ch on true
            union all
            select c.v::bigint, 1000000 + n.ord * 1000 + c.ord
            from jsonb_array_elements(coalesce(answer->'notes', '[]'::jsonb)) with ordinality n(value, ord)
            cross join lateral jsonb_array_elements_text(n.value->'cite') with ordinality c(v, ord)
        ) u group by id) g
$$;

-- " [1, 2]" for a cite list (the sheet's numbers, ascending), or nothing.
create or replace function app.sheet_cites(cite jsonb, ids bigint[])
returns text
language sql
immutable
as $$
    select coalesce(' [' || string_agg(n::text, ', ' order by n) || ']', '')
    from (select array_position(ids, c::bigint) as n from jsonb_array_elements_text(coalesce(cite, '[]'::jsonb)) c) x
    where n is not null
$$;

-- The "why" line of one choice key, as a sub-bullet, or nothing.
create or replace function app.sheet_why(answer jsonb, key text, ids bigint[], indent text default '')
returns text
language sql
immutable
as $$
    select coalesce((select indent || '- Why: ' || (w.value->>'text') || app.sheet_cites(w.value->'cite', ids) || E'\n'
                     from jsonb_array_elements(coalesce(answer->'why', '[]'::jsonb)) w
                     where w.value->>'key' = key limit 1), '')
$$;

-- The choice of the facts with this key (label, inventory word), or null.
create or replace function app.sheet_choice(facts jsonb, key text)
returns jsonb
language sql
immutable
as $$ select x from jsonb_array_elements(facts->'choices') x where x->>'key' = key limit 1 $$;

-- 1. Style: the pick and why, the alternatives or the mismatch, the description.
create or replace function app.sheet_sec_style(facts jsonb, answer jsonb, ids bigint[])
returns text
language plpgsql
immutable
as $$
declare
    st  jsonb := facts->'style';
    s2  jsonb := facts->'step2';
    out text;
    alt text;
begin
    out := format(E'## Style\n\n**%s %s** (%s guide)\n\n%s\n\n- Why this style: %s\n%s',
        st->>'code', st->>'name', st->>'guide', answer->>'style_description', s2->>'reason',
        app.sheet_why(answer, 'style', ids, '  '));
    select string_agg(coalesce(c.value || ' ' || (s.x->>'name'), c.value), ', ' order by c.ord) into alt
    from jsonb_array_elements_text(coalesce(s2->'alt_styles', '[]'::jsonb)) with ordinality c(value, ord)
    left join lateral (select x from jsonb_array_elements(coalesce(s2->'styles', '[]'::jsonb)) x
                       where x->>'code' = c.value limit 1) s on true;
    if alt is not null then
        out := out || format(E'- Other styles considered: %s\n', alt);
    end if;
    if jsonb_typeof(s2->'mismatch') = 'object' then
        out := out || format(E'- Mismatch: you named %s (its range is %s); %s fits better and was chosen.\n',
            s2->'mismatch'->>'named', s2->'mismatch'->>'range', s2->'mismatch'->>'chosen');
    end if;
    return out || E'\n';
end;
$$;

-- 2. Targets and results against the style's ranges.
create or replace function app.sheet_sec_results(facts jsonb)
returns text
language plpgsql
immutable
as $$
declare
    rc  jsonb := facts->'recipe';
    tg  jsonb := rc->'targets';
    rg  jsonb := facts->'style'->'ranges';
    out text := E'## Targets and results\n\n| Quantity | Target | Result | Style range |\n|---|---|---|---|\n';
    r   record;
    tv  text;
begin
    for r in select * from (values
            (1, 'Batch (L)',      'batch_l', 1, rc->'batch_l',        null::jsonb),
            (2, 'Efficiency (%)', null,      1, rc->'efficiency_pct', null),
            (3, 'OG',             'og',      3, rc->'og',             rg->'og'),
            (4, 'FG',             'fg',      3, rc->'fg',             rg->'fg'),
            (5, 'ABV (%)',        'abv',     1, rc->'abv',            rg->'abv'),
            (6, 'IBU',            'ibu',     1, rc->'ibu',            rg->'ibu'),
            (7, 'SRM',            'srm',     1, rc->'srm',            rg->'srm')) t(n, label, key, places, result, range)
            order by n loop
        -- batch_l is a target of its own; the others sit under targets.targets
        tv := case when r.key is null then '–'
                   when r.key = 'batch_l' then format('%s (%s)', app.sheet_num((tg#>>'{batch_l,value}')::numeric, r.places), tg#>>'{batch_l,from}')
                   when tg#>('{targets,' || r.key || ',value}')::text[] is null then '–'
                   else format('%s (%s)', app.sheet_num((tg#>>('{targets,' || r.key || ',value}')::text[])::numeric, r.places),
                               tg#>>('{targets,' || r.key || ',from}')::text[]) end;
        out := out || format(E'| %s | %s | %s | %s |\n', r.label, tv, app.sheet_num((r.result #>> '{}')::numeric, r.places),
            case when r.range is null then '–'
                 else app.sheet_range(r.range, case when r.key in ('og', 'fg') then 3 when r.key = 'abv' then 1 else null end) end);
    end loop;
    return out || E'\n';
end;
$$;

-- 3-6. Fermentables, hops, yeast, extras: one line per saved item, its "why" under the first line of each choice.
-- kind is the heading's kind: fermentable, hop, yeast or extra. Yeast gets its pitch line (step 14), extras "none".
create or replace function app.sheet_sec_items(facts jsonb, answer jsonb, ids bigint[], kind text)
returns text
language plpgsql
immutable
as $$
declare
    heading text := case kind when 'fermentable' then 'Fermentables' when 'hop' then 'Hops'
                              when 'yeast' then 'Yeast' else 'Extras' end;
    out     text := format(E'## %s\n\n', heading);
    seen    text[] := '{}';
    it      jsonb;
    key     text;
    inv     text;
    line    text;
    p       jsonb;
    n       integer := 0;
begin
    for it in select x from jsonb_array_elements(facts->'items') x where x->>'kind' = kind
              order by (x->>'id')::bigint loop
        n := n + 1;
        key := kind || ':' || coalesce(it->>'ingredient_id', it->>'name');
        inv := app.sheet_choice(facts, key)->>'inventory';
        line := case kind
            when 'fermentable' then format('%s %s, %s %%', app.sheet_amount((it->>'amount')::numeric, it->>'unit'),
                                           it->>'name', app.sheet_num((it->>'pct')::numeric, 1))
            when 'yeast' then format('%s %s', app.sheet_amount((it->>'amount')::numeric, it->>'unit'), it->>'name')
            else format('%s %s, %s%s', app.sheet_amount((it->>'amount')::numeric, it->>'unit'), it->>'name',
                        replace(coalesce(it->>'usage', ''), '_', ' '),
                        case when it->>'time_min' is null then '' else ' ' || app.sheet_num((it->>'time_min')::numeric, 0) || ' min' end)
            end;
        out := out || '- ' || line
            || case when inv is not null then format(' — from your inventory ("%s")', inv) else '' end || E'\n';
        if kind = 'yeast' then
            select x into p from jsonb_array_elements(coalesce(facts->'process'->'fermentation'->'pitch', '[]'::jsonb)) x
            where x->>'ingredient_id' = it->>'ingredient_id' limit 1;
            if p is not null then
                out := out || format(E'  - Pitch: %s%s\n', p->>'because',
                                     case when p->>'because' ilike '%estimate%' then '' else ' (estimate)' end);
            end if;
        end if;
        if not key = any (seen) then
            seen := seen || key;
            out := out || app.sheet_why(answer, key, ids, '  ');
        end if;
    end loop;
    if n = 0 then
        out := out || E'- none\n';
    end if;
    return out || E'\n';
end;
$$;

-- 7. How the amounts were worked out: step 10's values used (without the yeast placeholder, step 14 replaces
-- it), the colour and gravity moves, the rounding, then the pitch lines.
create or replace function app.sheet_sec_worked(facts jsonb)
returns text
language plpgsql
immutable
as $$
declare
    s10 jsonb := facts->'step10';
    out text := E'## How the amounts were worked out\n\n';
    v   jsonb;
begin
    for v in select x from jsonb_array_elements(coalesce(s10->'values_used', '[]'::jsonb)) x
             where x->>'what' <> 'yeast amount' loop
        out := out || format(E'- %s: %s\n',
            case v->>'what' when 'ferm_c' then 'Fermentation temperature'
                 else upper(left(v->>'what', 1)) || substr(replace(v->>'what', '_', ' '), 2) end, v->>'because');
    end loop;
    if s10->>'colour_because' is not null then
        out := out || format(E'- Colour moves: %s\n', s10->>'colour_because');
    end if;
    if s10->'og_used'->>'because' is not null then
        out := out || format(E'- Gravity: %s\n', s10->'og_used'->>'because');
    end if;
    if s10->'rounding'->>'because' is not null then
        out := out || format(E'- Rounding: %s\n', s10->'rounding'->>'because');
    end if;
    for v in select x from jsonb_array_elements(coalesce(facts->'process'->'fermentation'->'pitch', '[]'::jsonb)) x loop
        out := out || format(E'- Yeast amount (%s): %s%s\n', v->>'name', v->>'because',
                             case when v->>'because' ilike '%estimate%' then '' else ' (estimate)' end);
    end loop;
    return out || E'\n';
end;
$$;

-- 8. Water: the row and its basis, the salts, the mash pH estimate, the acid line.
create or replace function app.sheet_sec_water(facts jsonb, answer jsonb, ids bigint[])
returns text
language plpgsql
immutable
as $$
declare
    w   jsonb := facts->'process'->'water';
    t   jsonb := w->'target';
    out text := E'## Water\n\n' || app.sheet_why(answer, 'water', ids);
    s   jsonb;
    n   integer := 0;
begin
    out := out || format(E'- Target: row %s, from %s, basis %s (%s)%s\n', t->>'row', t->>'from', t->>'basis', t->>'page',
                         case when (t->>'fallback')::boolean then ', fallback row' else '' end);
    out := out || format(E'- Aim (mg/L): calcium %s, sulfate %s, chloride %s\n', app.sheet_num((t#>>'{aim,ca}')::numeric, 0),
                         app.sheet_num((t#>>'{aim,so4}')::numeric, 0), app.sheet_num((t#>>'{aim,cl}')::numeric, 0));
    out := out || E'- Salts:\n';
    for s in select x from jsonb_array_elements(coalesce(w->'salts', '[]'::jsonb)) x loop
        n := n + 1;
        out := out || format(E'  - %s %s g (strike %s g, sparge %s g)\n', s->>'name', app.sheet_num((s->>'total_g')::numeric, 1),
                             app.sheet_num((s->>'strike_g')::numeric, 1), app.sheet_num((s->>'sparge_g')::numeric, 1));
    end loop;
    if n = 0 then
        out := out || E'  - none\n';
    end if;
    out := out || format(E'- Mash pH: %s (estimate, unverified against Bru''n Water); target %s–%s\n',
                         app.sheet_num((w#>>'{mash_ph,ph}')::numeric, 2), app.sheet_num((w#>>'{mash_ph,target_low}')::numeric, 1),
                         app.sheet_num((w#>>'{mash_ph,target_high}')::numeric, 1));
    out := out || format(E'- Acid: %s\n', w#>>'{acid,text}');
    for s in select to_jsonb(x) from jsonb_array_elements_text(coalesce(t->'outside_row', '[]'::jsonb)) x loop
        out := out || format(E'- Note: %s\n', s #>> '{}');
    end loop;
    return out || E'\n';
end;
$$;

-- 9. Mash: strike water and temperature, the steps, the sparge.
create or replace function app.sheet_sec_mash(facts jsonb, answer jsonb, ids bigint[])
returns text
language plpgsql
immutable
as $$
declare
    m   jsonb := facts->'process'->'mash';
    v   jsonb := m->'volumes';
    out text := E'## Mash\n\n' || app.sheet_why(answer, 'mash', ids);
    s   jsonb;
begin
    out := out || format(E'- Strike water: %s L at %s °C (grain at %s °C, %s L/kg)\n', app.sheet_num((v->>'strike_l')::numeric, 1),
                         app.sheet_num((m->>'strike_c')::numeric, 1), app.sheet_num((m->>'grain_c')::numeric, 1),
                         app.sheet_num((v->>'ratio_l_kg')::numeric, 1));
    out := out || E'- Steps:\n';
    for s in select x from jsonb_array_elements(coalesce(m->'steps', '[]'::jsonb)) x loop
        out := out || format(E'  - %s: %s °C for %s min\n', s->>'name', app.sheet_num((s->>'temp_c')::numeric, 1),
                             app.sheet_num((s->>'minutes')::numeric, 0));
    end loop;
    out := out || format(E'- Sparge water: %s L (pre-boil volume %s L)\n', app.sheet_num((v->>'sparge_l')::numeric, 1),
                         app.sheet_num((v->>'preboil_l')::numeric, 1));
    for s in select x from jsonb_array_elements(coalesce(m->'additions', '[]'::jsonb)) x loop
        out := out || format(E'- Added to the mash: %s g %s\n', app.sheet_num((s->>'g')::numeric, 0), s->>'name');
    end loop;
    return out || E'\n';
end;
$$;

-- 10. Boil: the time and the additions in order, then the whirlpool.
create or replace function app.sheet_sec_boil(facts jsonb, answer jsonb, ids bigint[])
returns text
language plpgsql
immutable
as $$
declare
    b   jsonb := facts->'process'->'boil';
    out text := E'## Boil\n\n' || app.sheet_why(answer, 'boil', ids);
    a   jsonb;
begin
    out := out || format(E'- Boil time: %s min\n', app.sheet_num((b->>'boil_min')::numeric, 0));
    if b->>'because' is not null then
        out := out || format(E'- Because: %s\n', b->>'because');
    end if;
    for a in select x from jsonb_array_elements(coalesce(b->'additions', '[]'::jsonb)) x loop
        out := out || format(E'- %s g %s, boil %s min\n', app.sheet_num((a->>'g')::numeric, 0), a->>'name',
                             app.sheet_num((a->>'at_min')::numeric, 0));
    end loop;
    for a in select x from jsonb_array_elements(coalesce(b->'whirlpool', '[]'::jsonb)) x loop
        out := out || format(E'- %s g %s, whirlpool%s\n', app.sheet_num((a->>'g')::numeric, 0), a->>'name',
                             case when a->>'minutes' is null then '' else ' ' || app.sheet_num((a->>'minutes')::numeric, 0) || ' min' end);
    end loop;
    return out || E'\n';
end;
$$;

-- 11. Fermentation: the steps with days and when to move on, dry hops, secondary additions.
create or replace function app.sheet_sec_ferment(facts jsonb, answer jsonb, ids bigint[])
returns text
language plpgsql
immutable
as $$
declare
    f   jsonb := facts->'process'->'fermentation';
    out text := E'## Fermentation\n\n' || app.sheet_why(answer, 'fermentation', ids);
    s   jsonb;
begin
    out := out || E'- Steps:\n';
    for s in select x from jsonb_array_elements(coalesce(f->'steps', '[]'::jsonb)) x loop
        out := out || format(E'  - %s: %s °C for %s %s%s\n', s->>'phase', app.sheet_num((s->>'temp_c')::numeric, 1),
                             app.sheet_trim((s->>'days')::numeric), case when (s->>'days')::numeric = 1 then 'day' else 'days' end,
                             case when s->>'move_on' is null then '' else '; move on: ' || (s->>'move_on') end);
    end loop;
    for s in select x from jsonb_array_elements(coalesce(f->'dry_hops', '[]'::jsonb)) x loop
        out := out || format(E'- Dry hops on day %s at %s °C, %s days of contact: %s\n', app.sheet_trim((s->>'day')::numeric),
                             app.sheet_num((s->>'temp_c')::numeric, 1), app.sheet_trim((s->>'contact_days')::numeric),
                             (select string_agg(format('%s g %s', app.sheet_num((h->>'g')::numeric, 0), h->>'name'), ', ')
                              from jsonb_array_elements(s->'hops') h));
    end loop;
    for s in select x from jsonb_array_elements(coalesce(f->'secondary', '[]'::jsonb)) x loop
        out := out || format(E'- %s on day %s: %s g %s%s\n', replace(s->>'usage', '_', ' '), app.sheet_trim((s->>'day')::numeric),
                             app.sheet_num((s->>'g')::numeric, 0), s->>'name',
                             case when s->>'contact_days' is null then '' else ', ' || app.sheet_trim((s->>'contact_days')::numeric) || ' days of contact' end);
    end loop;
    return out || E'\n';
end;
$$;

-- 12. Packaging: CO2 volumes with their family, basis and origin, the priming sugar, packaging extras.
create or replace function app.sheet_sec_packaging(facts jsonb, answer jsonb, ids bigint[])
returns text
language plpgsql
immutable
as $$
declare
    p   jsonb := facts->'process'->'packaging';
    c   jsonb := p->'co2';
    out text := E'## Packaging\n\n' || app.sheet_why(answer, 'packaging', ids);
    e   jsonb;
begin
    out := out || format(E'- CO₂: %s volumes; family %s, from %s, basis %s; range %s–%s\n',
        app.sheet_num((c->>'volumes')::numeric, 2), c->>'family', c->>'from', c->>'basis',
        app.sheet_num((c#>>'{range,0}')::numeric, 1), app.sheet_num((c#>>'{range,1}')::numeric, 1));
    out := out || format(E'- Priming: %s g %s for %s L, beer at %s °C (%s g/L)\n', app.sheet_num((p#>>'{priming,g}')::numeric, 0),
        p#>>'{priming,sugar}', app.sheet_num((p#>>'{priming,volume_l}')::numeric, 1),
        app.sheet_num((p#>>'{priming,temp_c}')::numeric, 1), app.sheet_num((p#>>'{priming,g_per_l}')::numeric, 1));
    for e in select x from jsonb_array_elements(coalesce(p->'extras', '[]'::jsonb)) x loop
        out := out || format(E'- Packaging extra: %s g %s\n', app.sheet_num((e->>'g')::numeric, 0), e->>'name');
    end loop;
    return out || E'\n';
end;
$$;

-- 13. The deviations box: what is outside the style or the brewer's numbers, and who asked for it.
create or replace function app.sheet_sec_deviations(facts jsonb)
returns text
language plpgsql
immutable
as $$
declare
    out text := E'## Deviations\n\n';
    d   jsonb;
    n   integer := 0;
begin
    for d in select x from jsonb_array_elements(coalesce(facts->'deviations', '[]'::jsonb)) x loop
        if n = 0 then
            out := out || E'| Subject | Kind | Level | Who | Note |\n|---|---|---|---|---|\n';
        end if;
        n := n + 1;
        out := out || format(E'| %s | %s | %s | %s | %s |\n', replace(d->>'subject', '|', '/'), d->>'kind',
            coalesce(replace(d->>'level', '_', ' '), ''),
            case d->>'requested_by' when 'user' then 'you asked' else 'the pipeline chose' end,
            replace(coalesce(d->>'note', ''), '|', '/'));
    end loop;
    if n = 0 then
        out := out || E'No deviations.\n';
    end if;
    return out || E'\n';
end;
$$;

-- 14. Absent and unused items (steps 6-9) with what to do about each.
create or replace function app.sheet_sec_absent(facts jsonb)
returns text
language plpgsql
immutable
as $$
declare
    out  text := E'## Absent and unused items\n\n';
    seen text[] := '{}';
    x    jsonb;
    n    integer := 0;
begin
    for x in select e from (
                 select jsonb_array_elements(coalesce(facts->s->'absent', '[]'::jsonb)) as e, s
                 from (values ('step6'), ('step7'), ('step8'), ('step9')) v(s) order by s) a loop
        if x->>'word' = any (seen) then continue; end if;
        seen := seen || (x->>'word');
        n := n + 1;
        out := out || case
            when x->>'reason' like 'no product in the catalogue%' then
                format(E'- "%s": not in the catalogue. To use it, add it through `shared/ingredients/` and ask again, or brew without it.\n', x->>'word')
            when x->>'reason' like 'every product%excluded' then
                format(E'- "%s": every product it names is excluded. To use it, drop the exclusion.\n', x->>'word')
            else format(E'- "%s": %s.\n', x->>'word', x->>'reason') end;
    end loop;
    for x in select e from (
                 select jsonb_array_elements(coalesce(facts->s->'unused_inventory', '[]'::jsonb)) as e, s
                 from (values ('step6'), ('step7'), ('step8'), ('step9')) v(s) order by s) a loop
        if x->>'word' = any (seen) then continue; end if;
        seen := seen || (x->>'word');
        n := n + 1;
        out := out || format(E'- "%s" (in your inventory, not used): %s; you can keep it for another brew.\n', x->>'word', x->>'reason');
    end loop;
    if n = 0 then
        out := out || E'None.\n';
    end if;
    return out || E'\n';
end;
$$;

-- 15. Notes from the model, with their citations.
create or replace function app.sheet_sec_notes(answer jsonb, ids bigint[])
returns text
language plpgsql
immutable
as $$
declare
    out text := E'## Notes\n\n';
    n   jsonb;
    c   integer := 0;
begin
    for n in select x from jsonb_array_elements(coalesce(answer->'notes', '[]'::jsonb)) x loop
        c := c + 1;
        out := out || format(E'- %s%s\n', n->>'text', app.sheet_cites(n->'cite', ids));
    end loop;
    if c = 0 then
        out := out || E'None.\n';
    end if;
    return out || E'\n';
end;
$$;

-- 16. The sources the sheet cites, numbered in order of first use.
create or replace function app.sheet_sec_sources(sources jsonb, ids bigint[])
returns text
language plpgsql
immutable
as $$
declare
    out text := E'## Sources\n\n';
    i   integer;
    s   jsonb;
begin
    if cardinality(ids) = 0 then
        return out || E'None cited.\n';
    end if;
    for i in 1 .. cardinality(ids) loop
        select x into s from jsonb_array_elements(coalesce(sources, '[]'::jsonb)) x
        where (x->>'chunk_id')::bigint = ids[i] limit 1;
        out := out || format(E'%s. %s\n', i, case
            when s is null then 'chunk ' || ids[i]
            when s->>'page' is not null then
                (s->>'title') || ', PDF p. ' || (s->>'page') || coalesce(' — ' || nullif(s->>'section_path', ''), '')
                    || coalesce(' — ' || (s->>'url'), '')
            else (s->>'title') || coalesce(' — ' || nullif(s->>'section_path', ''), '') || coalesce(' — ' || (s->>'url'), '')
            end);
    end loop;
    return out;
end;
$$;

-- The whole sheet, in the order of the brief's R2.
create or replace function app.sheet_markdown(facts jsonb, sources jsonb, answer jsonb)
returns text
language plpgsql
immutable
as $$
declare
    ids bigint[] := app.sheet_cite_order(facts, answer);
begin
    return format(E'# Recipe sheet: %s %s, %s L\n\n', facts#>>'{style,code}', facts#>>'{style,name}',
                  app.sheet_num((facts#>>'{recipe,batch_l}')::numeric, 1))
        || app.sheet_sec_style(facts, answer, ids)
        || app.sheet_sec_results(facts)
        || app.sheet_sec_items(facts, answer, ids, 'fermentable')
        || app.sheet_sec_items(facts, answer, ids, 'hop')
        || app.sheet_sec_items(facts, answer, ids, 'yeast')
        || app.sheet_sec_items(facts, answer, ids, 'extra')
        || app.sheet_sec_worked(facts)
        || app.sheet_sec_water(facts, answer, ids)
        || app.sheet_sec_mash(facts, answer, ids)
        || app.sheet_sec_boil(facts, answer, ids)
        || app.sheet_sec_ferment(facts, answer, ids)
        || app.sheet_sec_packaging(facts, answer, ids)
        || app.sheet_sec_deviations(facts)
        || app.sheet_sec_absent(facts)
        || app.sheet_sec_notes(answer, ids)
        || app.sheet_sec_sources(sources, ids);
end;
$$;
