-- Steps 6-9 (choose yeast, fermentables, hops and extras), part 1: the candidate table the LLM
-- picks from and the prompt text that shows it (docs/work/m5-choose-ingredients, Task 3).
-- Code lists every product the LLM may pick, with the fields the brief names and its style level
-- at each usage choice, and marks the wanted and inventory products. The LLM never sees an excluded
-- product, and it picks only ids from the table. No LLM here; the check is db/043, the outputs db/044.
-- Needs db/034_style_level.sql, db/036_ingredient_resolver.sql, db/037_step3.sql (app.level_rank,
-- app.ingredient_choices, app.rate_wanted) and db/041_step5.sql (the frame it reads).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/042_choose_table.sql
-- Idempotent: safe to re-run.

-- Words that name the form of a product, not another product: a product with the word and one
-- without it are siblings (Citra and Citra LUPOMAX), so excluding one excludes the other.
-- Add a row only for a form word of the catalogue, never to fit a brief.
create or replace function app.hop_form_word()
returns table (word text, note text)
language sql
immutable
as $$
    values ('lupomax', 'LUPOMAX pellets: concentrated lupulin of the same variety')
$$;

-- The words of a product name with the form words removed, sorted: the key two siblings share.
create or replace function app.choose_base_words(name text)
returns text[]
language sql
immutable
as $$
    select coalesce(array_agg(w order by w), '{}'::text[])
      from unnest(app.ingredient_words(choose_base_words.name)) w
     where w not in (select f.word from app.hop_form_word() f)
$$;

-- Every product the table must leave out: the products of the frame's excluded words, and their
-- siblings (same kind, same name once the form words are removed). One entry per product:
-- {ingredient_id, name, word, why}. A product excluded in the request keeps that reason even when
-- it is also a sibling.
create or replace function app.choose_excluded(frame jsonb)
returns jsonb
language sql
stable
as $$
    with direct as (
        select (r.value ->> 'ingredient_id')::bigint as id, r.value ->> 'kind' as kind,
               r.value ->> 'name' as name, e.value ->> 'word' as word
          from jsonb_array_elements(coalesce(frame -> 'excluded', '[]'::jsonb)) e,
               jsonb_array_elements(e.value -> 'refs') r
    ),
    listed as (
        select d.id, d.name, d.word, 'excluded in the request' as why, 1 as grp from direct d
        union all
        select i.id, i.name, d.word, 'sibling of ' || d.name, 2
          from direct d
          join ref.ingredient i on i.kind = d.kind and i.id <> d.id
         where cardinality(app.choose_base_words(d.name)) > 0
           and app.choose_base_words(i.name) = app.choose_base_words(d.name)
    ),
    one as (
        select distinct on (l.id) l.* from listed l order by l.id, l.grp, l.name
    )
    select coalesce(jsonb_agg(jsonb_build_object('ingredient_id', o.id, 'name', o.name, 'word', o.word,
                                                 'why', o.why) order by o.name, o.id), '[]'::jsonb)
      from one o
$$;

-- A numrange as {low, high}; null for no range.
create or replace function app.choose_range(r numrange)
returns jsonb
language sql
immutable
as $$
    select case when r is null or isempty(r) then null
                else jsonb_build_object('low', lower(r), 'high', upper(r)) end
$$;

-- The tag names of one facet ('character', 'origin' or 'family') on a product.
create or replace function app.choose_tags(ingredient_id bigint, facet text)
returns text[]
language sql
stable
as $$
    select coalesce(array_agg(t.name order by t.name), '{}'::text[])
      from ref.ingredient_tag it
      join ref.tag t on t.id = it.tag_id
     where it.ingredient_id = choose_tags.ingredient_id and t.facet = choose_tags.facet
$$;

-- The family tags of a yeast and the families above them (a wheat yeast is also belgian and ale),
-- so "belongs to the required family" is a plain membership test.
create or replace function app.choose_yeast_families(ingredient_id bigint)
returns text[]
language sql
stable
as $$
    with recursive up as (
        select t.id, t.parent_id, t.name
          from ref.ingredient_tag it
          join ref.tag t on t.id = it.tag_id
         where it.ingredient_id = choose_yeast_families.ingredient_id and t.facet = 'family'
        union
        select p.id, p.parent_id, p.name from up join ref.tag p on p.id = up.parent_id
    )
    select coalesce(array_agg(distinct up.name order by up.name), '{}'::text[]) from up
$$;

-- The level of one product at every usage choice in a style:
-- [{choice, usage, minutes, level, because}] in the order of app.ingredient_choices, rated with no
-- dose (the level of the full recipe is M6's app.style_fit_recipe). role is the wanted role, if any
-- (a feature hop has no early boil choice). An empty array when there is no style.
create or replace function app.choose_levels(style_code text, ingredient_id bigint, role text)
returns jsonb
language sql
stable
as $$
    select coalesce(jsonb_agg(jsonb_build_object(
               'choice', c.label, 'usage', c.usage, 'minutes', (c.dose ->> 'minutes')::numeric,
               'level', x.res ->> 'level', 'because', x.res ->> 'because') order by c.ord), '[]'::jsonb)
      from app.ingredient_choices(choose_levels.ingredient_id, choose_levels.role) c
     cross join lateral (
         select app.style_level(choose_levels.style_code, choose_levels.ingredient_id, c.usage, c.dose) as res) x
     where choose_levels.style_code is not null
$$;

-- The best level among rated choices (required, typical, allowed, out_of_style, changes_style);
-- null when no choice could be rated.
create or replace function app.choose_best_level(levels jsonb)
returns text
language sql
immutable
as $$
    select l.value ->> 'level'
      from jsonb_array_elements(levels) l
     where l.value ->> 'level' is not null
     order by app.level_rank(l.value ->> 'level')
     limit 1
$$;

-- For a wanted product: the labels of the choices whose level in the wanted style reaches the best
-- level app.rate_wanted found for the word (R4). Null when the word cannot be rated.
create or replace function app.choose_keeps_best(wanted_style text, item text, role text, ingredient_id bigint)
returns jsonb
language plpgsql
stable
as $$
declare
    v_best text;
begin
    if wanted_style is null then
        return null;
    end if;
    v_best := app.rate_wanted(wanted_style, item, role) ->> 'level';
    if v_best is null then
        return null;
    end if;
    return coalesce((
        select jsonb_agg(c.label order by c.ord)
          from app.ingredient_choices(ingredient_id, role) c
         where app.level_rank(app.style_level(wanted_style, ingredient_id, c.usage, c.dose) ->> 'level')
               <= app.level_rank(v_best)), '[]'::jsonb);
end
$$;

-- What a yeast must be in the style used (no ale yeast for a lager, the required family, a souring
-- culture when the style asks for sourness). With guidance off the lager and family rules are off.
--   lager     a BJCP style tagged bottom-fermented, or a BA style whose category names lager
--   families  the yeast family tags the style requires in ref.style_ingredient
--   souring   the style's sourness has min_level 1 or more
create or replace function app.choose_yeast_rules(style_code text, guidance boolean)
returns jsonb
language sql
stable
as $$
    with st as (
        select b.* from ref.beer_style b where b.code = choose_yeast_rules.style_code order by b.id limit 1
    )
    select jsonb_build_object(
        'lager', coalesce(choose_yeast_rules.guidance, true) and exists (
            select 1 from st
             where (st.guide = 'BJCP' and st.raw ->> 'tags' like '%bottom-fermented%')
                or (st.guide = 'BA' and st.category ilike '%lager%')),
        'families', case when coalesce(choose_yeast_rules.guidance, true) then coalesce((
            select jsonb_agg(distinct t.name)
              from st
              join ref.style_ingredient si on si.style_id = st.id and si.required
              join ref.tag t on t.id = si.tag_id and t.facet = 'family'
             where exists (select 1 from ref.ingredient_tag it join ref.yeast y on y.ingredient_id = it.ingredient_id
                            where app.tag_under(it.tag_id, array[t.name]))), '[]'::jsonb)
            else '[]'::jsonb end,
        'souring', exists (
            select 1 from st
              join ref.style_sensory s on s.style_id = st.id
             where s.dimension = 'sourness' and s.min_level >= 1 and s.reviewed))
$$;

-- Why a table row cannot be used in this recipe, or null when it fits (R3): a misc when the recipe
-- has no extras; a level worse than allowed in the style used (guidance on); a yeast that is not a
-- lager yeast or lacks a required family. The reason is the one the brewer reads.
create or replace function app.choose_fit_reason(r jsonb, rules jsonb, guidance boolean, has_misc boolean)
returns text
language plpgsql
stable
as $$
declare
    v_level  text := r ->> 'best_level';
    v_family text;
begin
    if r ->> 'kind' = 'misc' and not has_misc then
        return 'the recipe has no extras';
    end if;
    if guidance and v_level is not null and app.level_rank(v_level) > app.level_rank('allowed') then
        return replace(v_level, '_', ' ') || ': ' || (
            select c.value ->> 'because' from jsonb_array_elements(r -> 'levels') c
             where c.value ->> 'level' = v_level limit 1);
    end if;
    if r ->> 'kind' = 'yeast' then
        if (rules ->> 'lager')::boolean and r ->> 'type' is distinct from 'lager' then
            return 'not a lager yeast, and the style is a lager style';
        end if;
        for v_family in select jsonb_array_elements_text(rules -> 'families') loop
            if not (r -> 'family') ? v_family then
                return 'not in the yeast family ' || v_family || ' that the style requires';
            end if;
        end loop;
    end if;
    return null;
end
$$;

-- The products a word's refs name, as {kind, ids}. Only the four kinds a recipe picks count (a
-- water salt is M7's). kind is that of the first ref that is a table row (else of the first ref);
-- ids are the refs of that kind that are table rows, in the refs' order. kind is null when no ref
-- is of those kinds.
create or replace function app.choose_word_ids(refs jsonb, rows jsonb)
returns jsonb
language sql
stable
as $$
    with ref_of as (
        select r.ord, (r.value ->> 'ingredient_id')::bigint as id, r.value ->> 'kind' as kind
          from jsonb_array_elements(coalesce(refs, '[]'::jsonb)) with ordinality r(value, ord)
         where r.value ->> 'kind' in ('fermentable', 'hop', 'yeast', 'misc')
    ),
    in_table as (
        select f.* from ref_of f
         where exists (select 1 from jsonb_array_elements(rows) t where (t.value ->> 'ingredient_id')::bigint = f.id)
    ),
    pick as (
        select coalesce((select kind from in_table order by ord limit 1),
                        (select kind from ref_of order by ord limit 1)) as kind
    )
    select jsonb_build_object(
        'kind', (select kind from pick),
        'ids', coalesce((select jsonb_agg(i.id order by i.ord) from in_table i, pick p where i.kind = p.kind),
                        '[]'::jsonb))
$$;

-- The candidate table for steps 6-9. brief = step 1's output, style = step 2's output, targets =
-- step 4's output, frame = step 5's output.
--   style_used    step 4's style (targets.style.code): pipeline picks are rated in it
--   wanted_style  step 2's style: a wanted item is rated in it (the style step 3 rated it in)
--   rows          fermentables, hops, yeasts, misc: see below
--   yeast_rules   app.choose_yeast_rules
--   slots, inventory_words, absent, unused_inventory   what the frame asked for and what the table can fill
-- A row: ingredient_id, name, producer, levels (app.choose_levels in the style used), best_level,
-- inventory (the word or null), wanted ({item, role} or null), keeps_best (wanted rows only), and
-- the fields of its kind. With guidance on a product is listed when one choice is required,
-- typical or allowed in the style used, or it is wanted or in the inventory; with guidance off
-- every product is listed. A misc is listed only when wanted or in the inventory. An excluded
-- product (and its siblings) is never listed.
create or replace function app.choose_table(brief jsonb, style jsonb, targets jsonb, frame jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    v_style_used   text := targets #>> '{style,code}';
    v_wanted_style text := style #>> '{style,code}';
    v_rated        boolean;
    v_guidance     boolean;
    v_excluded     jsonb := app.choose_excluded(frame);
    v_excluded_ids bigint[];
    v_rules        jsonb;
    v_band_low     numeric := (frame #>> '{attenuation,yeast_low_pct}')::numeric;
    v_band_high    numeric := (frame #>> '{attenuation,yeast_high_pct}')::numeric;
    v_style_name   text;
    v_char_ingr    text;
    v_rows         jsonb;
    v_has_misc     boolean;
    v_slots        jsonb := '[]'::jsonb;
    v_words        jsonb := '[]'::jsonb;
    v_absent       jsonb := '[]'::jsonb;
    v_unused       jsonb := '[]'::jsonb;
    x              record;
    w              jsonb;
    v_fit          boolean;
    v_reason       text;
begin
    -- a style with no reviewed envelope has no levels (app.style_level says "not rated"), so the
    -- level filtering cannot apply to it: v_guidance is off and the table lists every product. The
    -- yeast rules (lager, families) read style tags, not levels, so they follow the brief's guidance.
    v_rated := exists (select 1 from ref.beer_style b
                         left join ref.style_sensory s on s.style_id = b.id and s.reviewed
                         left join ref.style_ingredient si on si.style_id = b.id and si.reviewed
                        where b.code = v_style_used and (s.style_id is not null or si.style_id is not null));
    v_guidance := coalesce((brief ->> 'guidance')::boolean, true) and v_rated;
    v_rules := app.choose_yeast_rules(v_style_used, coalesce((brief ->> 'guidance')::boolean, true));
    v_excluded_ids := array(select (e.value ->> 'ingredient_id')::bigint from jsonb_array_elements(v_excluded) e);
    select b.name, b.characteristic_ingredients into v_style_name, v_char_ingr
      from ref.beer_style b where b.code = v_style_used order by b.id limit 1;

    -- 1. every candidate row, flat; the four kind lists are cut from it at the end
    with slot_ref as (
        select s.ord, s.value ->> 'item' as item, s.value ->> 'wanted_role' as role,
               (r.value ->> 'ingredient_id')::bigint as id
          from jsonb_array_elements(coalesce(frame -> 'slots', '[]'::jsonb)) with ordinality s(value, ord),
               jsonb_array_elements(s.value -> 'refs') r
    ),
    inv_ref as (
        select n.ord, n.value ->> 'word' as word, (r.value ->> 'ingredient_id')::bigint as id
          from jsonb_array_elements(coalesce(frame -> 'inventory', '[]'::jsonb)) with ordinality n(value, ord),
               jsonb_array_elements(n.value -> 'refs') r
    ),
    cand as (
        select i.id, i.kind, i.name, i.producer, w.item as wanted_item, w.role as wanted_role, v.word as inv_word
          from ref.ingredient i
          left join lateral (select s.item, s.role from slot_ref s where s.id = i.id order by s.ord limit 1) w on true
          left join lateral (select n.word from inv_ref n where n.id = i.id order by n.ord limit 1) v on true
         where i.kind in ('fermentable', 'hop', 'yeast', 'misc')
           and i.id <> all (v_excluded_ids)
           and (i.kind <> 'misc' or w.item is not null or v.word is not null)
    ),
    rated as (
        select c.*, app.choose_levels(v_style_used, c.id, c.wanted_role) as levels
          from cand c
    ),
    listed as (
        select r.*, app.choose_best_level(r.levels) as best_level
          from rated r
    )
    select coalesce(jsonb_agg(
               jsonb_build_object(
                   'ingredient_id', l.id, 'kind', l.kind, 'name', l.name, 'producer', l.producer,
                   'levels', l.levels, 'best_level', l.best_level, 'inventory', l.inv_word,
                   'wanted', case when l.wanted_item is null then null
                                  else jsonb_build_object('item', l.wanted_item, 'role', l.wanted_role) end)
               || case when l.wanted_item is null then '{}'::jsonb
                       else jsonb_build_object('keeps_best',
                                app.choose_keeps_best(v_wanted_style, l.wanted_item, l.wanted_role, l.id)) end
               || case l.kind
                    when 'fermentable' then jsonb_build_object(
                        'role', f.role, 'max_pct', f.max_pct, 'ebc', app.choose_range(f.ebc),
                        'fermentability', f.fermentability, 'description', f.description)
                    when 'hop' then jsonb_build_object(
                        'purpose', h.purpose, 'alpha', app.choose_range(h.alpha_pct), 'origins', to_jsonb(h.origins),
                        'character', to_jsonb(app.choose_tags(l.id, 'character')))
                    when 'yeast' then jsonb_build_object(
                        'type', y.type, 'form', y.form, 'attenuation', app.choose_range(y.attenuation_pct),
                        'temp_c', app.choose_range(y.temp_c), 'flocculation', y.flocculation,
                        'alcohol_tolerance_pct', y.alcohol_tolerance_pct,
                        'family', to_jsonb(app.choose_yeast_families(l.id)),
                        'character', to_jsonb(app.choose_tags(l.id, 'character')),
                        'overlaps_band', case when y.attenuation_pct is null or v_band_low is null then null
                                              else y.attenuation_pct && numrange(v_band_low, v_band_high, '[]') end)
                    else jsonb_build_object(
                        'category', m.category, 'usages', to_jsonb(m.usages), 'time_min', m.time_min,
                        'dose', app.step5_misc(l.id) -> 'dose_g_per_l')
                  end
               order by case l.kind when 'fermentable' then 1 when 'hop' then 2 when 'yeast' then 3 else 4 end,
                        l.name, l.id), '[]'::jsonb)
      into v_rows
      from listed l
      left join ref.fermentable f on f.ingredient_id = l.id
      left join ref.hop h on h.ingredient_id = l.id
      left join ref.yeast y on y.ingredient_id = l.id
      left join ref.misc m on m.ingredient_id = l.id
     where not v_guidance
        or l.wanted_item is not null or l.inv_word is not null
        or l.best_level in ('required', 'typical', 'allowed');

    v_has_misc := exists (select 1 from jsonb_array_elements(v_rows) r
                           where r.value ->> 'kind' = 'misc' and r.value -> 'wanted' <> 'null'::jsonb);

    -- 2. one slot per wanted item the frame lists, with the table rows that can fill it
    for x in select s.value as slot from jsonb_array_elements(coalesce(frame -> 'slots', '[]'::jsonb)) with ordinality s(value, ord)
              order by s.ord loop
        w := app.choose_word_ids(x.slot -> 'refs', v_rows);
        if jsonb_array_length(x.slot -> 'refs') = 0 then
            v_slots := v_slots || jsonb_build_object('item', x.slot ->> 'item', 'role', x.slot ->> 'wanted_role',
                                                     'kind', null, 'ids', '[]'::jsonb);
            v_absent := v_absent || jsonb_build_object('word', x.slot ->> 'item', 'kind', null,
                'reason', 'no product in the catalogue matches "' || (x.slot ->> 'item') || '"');
        elsif w ->> 'kind' is not null then  -- a slot that names only water salts is M7's
            v_slots := v_slots || jsonb_build_object('item', x.slot ->> 'item', 'role', x.slot ->> 'wanted_role',
                                                     'kind', w -> 'kind', 'ids', w -> 'ids');
            if jsonb_array_length(w -> 'ids') = 0 then
                v_absent := v_absent || jsonb_build_object('word', x.slot ->> 'item', 'kind', w -> 'kind',
                    'reason', 'every product that "' || (x.slot ->> 'item') || '" names is excluded');
            end if;
        end if;
    end loop;

    -- 3. the inventory words: the rows they name, and whether one of them fits this recipe
    for x in select n.value as item from jsonb_array_elements(coalesce(frame -> 'inventory', '[]'::jsonb)) with ordinality n(value, ord)
              order by n.ord loop
        w := app.choose_word_ids(x.item -> 'refs', v_rows);
        if jsonb_array_length(x.item -> 'refs') = 0 then
            v_words := v_words || jsonb_build_object('word', x.item ->> 'word', 'kind', null, 'ids', '[]'::jsonb, 'fits', false);
            v_absent := v_absent || jsonb_build_object('word', x.item ->> 'word', 'kind', null,
                'reason', 'no product in the catalogue matches "' || (x.item ->> 'word') || '"');
        elsif w ->> 'kind' is not null then
            -- fits when some product of the word fits; else the first product's reason (by name)
            select coalesce(bool_or(q.reason is null), false), (array_agg(q.reason order by q.name))[1]
              into v_fit, v_reason
              from (select r.value ->> 'name' as name,
                           app.choose_fit_reason(r.value, v_rules, v_guidance, v_has_misc) as reason
                      from jsonb_array_elements(v_rows) r
                     where (r.value ->> 'ingredient_id')::bigint in (select jsonb_array_elements_text(w -> 'ids')::bigint)) q;
            v_words := v_words || jsonb_build_object('word', x.item ->> 'word', 'kind', w -> 'kind',
                                                     'ids', w -> 'ids', 'fits', v_fit);
            if jsonb_array_length(w -> 'ids') = 0 then
                v_absent := v_absent || jsonb_build_object('word', x.item ->> 'word', 'kind', w -> 'kind',
                    'reason', 'every product that "' || (x.item ->> 'word') || '" names is excluded');
            elsif not v_fit then
                v_unused := v_unused || jsonb_build_object('word', x.item ->> 'word', 'reason', v_reason);
            end if;
        end if;
    end loop;

    return jsonb_build_object(
        'style_used', v_style_used, 'style_name', v_style_name, 'characteristic_ingredients', v_char_ingr,
        'wanted_style', v_wanted_style, 'guidance', v_guidance, 'style_rated', v_rated,
        'targets', jsonb_build_object(
            'og', targets #> '{targets,og,value}', 'fg', targets #> '{targets,fg,value}',
            'ibu', targets #> '{targets,ibu,value}', 'srm', targets #> '{targets,srm,value}'),
        'band', jsonb_build_object('yeast_low_pct', v_band_low, 'yeast_high_pct', v_band_high),
        'excluded', v_excluded,
        'fermentables', (select coalesce(jsonb_agg(r.value order by r.ord), '[]'::jsonb)
                           from jsonb_array_elements(v_rows) with ordinality r(value, ord) where r.value ->> 'kind' = 'fermentable'),
        'hops', (select coalesce(jsonb_agg(r.value order by r.ord), '[]'::jsonb)
                   from jsonb_array_elements(v_rows) with ordinality r(value, ord) where r.value ->> 'kind' = 'hop'),
        'yeasts', (select coalesce(jsonb_agg(r.value order by r.ord), '[]'::jsonb)
                     from jsonb_array_elements(v_rows) with ordinality r(value, ord) where r.value ->> 'kind' = 'yeast'),
        'misc', (select coalesce(jsonb_agg(r.value order by r.ord), '[]'::jsonb)
                   from jsonb_array_elements(v_rows) with ordinality r(value, ord) where r.value ->> 'kind' = 'misc'),
        'yeast_rules', v_rules,
        'slots', v_slots, 'inventory_words', v_words, 'absent', v_absent, 'unused_inventory', v_unused);
end
$$;

-- A number from the table as text: 2.50 -> 2.5. Null for null.
create or replace function app.choose_num(v jsonb)
returns text
language sql
immutable
as $$
    select case when v is null or jsonb_typeof(v) = 'null' then null else trim_scale((v #>> '{}')::numeric)::text end
$$;

-- A {low, high} range as text: "3-5", "5" when both ends are equal, "from 60" or "up to 5" when
-- one end is open. Null for null.
create or replace function app.choose_span(v jsonb)
returns text
language sql
immutable
as $$
    select case
        when v is null or jsonb_typeof(v) = 'null' then null
        when app.choose_num(v -> 'low') = app.choose_num(v -> 'high') then app.choose_num(v -> 'low')
        when app.choose_num(v -> 'high') is null then 'from ' || app.choose_num(v -> 'low')
        when app.choose_num(v -> 'low') is null then 'up to ' || app.choose_num(v -> 'high')
        else app.choose_num(v -> 'low') || '-' || app.choose_num(v -> 'high') end
$$;

-- One table row as one line of the prompt: id | name | the fields of its kind | marks | levels.
-- Levels are words ("out of style"), one "choice=level" per usage choice.
create or replace function app.choose_row_line(r jsonb)
returns text
language sql
immutable
as $$
    select array_to_string(array_remove(array[
        r ->> 'ingredient_id',
        (r ->> 'name') || case when coalesce(r ->> 'producer', '') = '' then '' else ' (' || (r ->> 'producer') || ')' end,
        case r ->> 'kind'
            when 'fermentable' then concat_ws(' | ',
                'role ' || (r ->> 'role'),
                'max ' || app.choose_num(r -> 'max_pct') || ' % of the grist',
                'EBC ' || app.choose_span(r -> 'ebc'),
                'fermentability ' || (r ->> 'fermentability'),
                r ->> 'description')
            when 'hop' then concat_ws(' | ',
                'purpose ' || (r ->> 'purpose'),
                'alpha ' || app.choose_span(r -> 'alpha') || ' %',
                'origin ' || nullif((select string_agg(o, ', ') from jsonb_array_elements_text(
                                        case when jsonb_typeof(r -> 'origins') = 'array' then r -> 'origins' else '[]'::jsonb end) o), ''),
                'character ' || nullif((select string_agg(o, ', ') from jsonb_array_elements_text(r -> 'character') o), ''))
            when 'yeast' then concat_ws(' | ',
                'type ' || (r ->> 'type'),
                'form ' || (r ->> 'form'),
                'attenuation ' || coalesce(app.choose_span(r -> 'attenuation') || ' %', 'not stated'),
                'temperature ' || app.choose_span(r -> 'temp_c') || ' °C',
                'flocculation ' || (r ->> 'flocculation'),
                'alcohol tolerance ' || app.choose_num(r -> 'alcohol_tolerance_pct') || ' %',
                'family ' || nullif((select string_agg(o, ', ') from jsonb_array_elements_text(r -> 'family') o), ''),
                'character ' || nullif((select string_agg(o, ', ') from jsonb_array_elements_text(r -> 'character') o), ''),
                case r ->> 'overlaps_band' when 'true' then 'attenuation reaches the band'
                                          when 'false' then 'attenuation misses the band'
                                          else 'no attenuation figure' end)
            else concat_ws(' | ',
                'category ' || (r ->> 'category'),
                'usages ' || (select string_agg(o, ', ') from jsonb_array_elements_text(r -> 'usages') o),
                'time ' || (r ->> 'time_min') || ' min',
                case when r -> 'dose' is null or jsonb_typeof(r -> 'dose') = 'null' then 'no sourced dose'
                     else 'sourced dose ' || app.choose_span(jsonb_build_object(
                              'low', r -> 'dose' -> 'low_g_per_l', 'high', r -> 'dose' -> 'high_g_per_l')) || ' g/L' end)
        end,
        case when r ->> 'inventory' is null then null else 'IN THE INVENTORY as "' || (r ->> 'inventory') || '"' end,
        case when jsonb_typeof(r -> 'wanted') <> 'object' then null
             else 'WANTED as "' || (r -> 'wanted' ->> 'item') || '" (' || (r -> 'wanted' ->> 'role') || ')'
                  || case when jsonb_typeof(r -> 'keeps_best') = 'array'
                          then '; keeps its best level at: ' || coalesce(nullif((select string_agg(k, ', ')
                                    from jsonb_array_elements_text(r -> 'keeps_best') k), ''), 'no choice')
                          else '' end end,
        'levels: ' || coalesce(nullif((
            select string_agg((l.value ->> 'choice') || '=' || coalesce(replace(l.value ->> 'level', '_', ' '), 'not rated'), ', ')
              from jsonb_array_elements(r -> 'levels') l), ''), 'none')
    ], null), ' | ')
$$;

-- The user message of steps 6-9: the request, the style, the targets and the rules in words, then
-- the table, one line per product, grouped by kind. Plain text, no JSON. Every number in it comes
-- from tbl (or the brief), none is computed here.
create or replace function app.choose_prompt(tbl jsonb, brief jsonb)
returns text
language plpgsql
immutable
as $$
declare
    v_rules jsonb := tbl -> 'yeast_rules';
    v_text  text := 'STYLE AND TARGETS';
    v_kind  record;
    v_part  text;
begin
    v_text := v_text || E'\nStyle used for the picks: ' || (tbl ->> 'style_used') || ' ' || coalesce(tbl ->> 'style_name', '')
              || '. Characteristic ingredients: ' || coalesce(rtrim(tbl ->> 'characteristic_ingredients', '. '), 'not stated') || '.';
    v_text := v_text || E'\nStyle the request was rated in (for wanted items): ' || coalesce(tbl ->> 'wanted_style', 'none') || '.';
    v_text := v_text || E'\n' || case when (tbl ->> 'guidance')::boolean
        then 'Style guidance is on: pick levels required, typical or allowed in the style used; prefer typical over allowed.'
        when coalesce((tbl ->> 'style_rated')::boolean, true) then 'Style guidance is off: any level may be picked.'
        else 'The style used has no reviewed ingredient guidance: any level may be picked.' end;
    v_text := v_text || E'\nTargets: OG ' || coalesce(app.choose_num(tbl -> 'targets' -> 'og'), 'none')
              || ', FG ' || coalesce(app.choose_num(tbl -> 'targets' -> 'fg'), 'none')
              || ', IBU ' || coalesce(app.choose_num(tbl -> 'targets' -> 'ibu'), 'none')
              || ', SRM ' || coalesce(app.choose_num(tbl -> 'targets' -> 'srm'), 'none') || '.';
    v_text := v_text || E'\n' || case when tbl -> 'band' ->> 'yeast_low_pct' is null
        then 'Attenuation band: none.'
        else 'Attenuation band for the yeast: ' || app.choose_num(tbl -> 'band' -> 'yeast_low_pct') || '-'
             || app.choose_num(tbl -> 'band' -> 'yeast_high_pct') || ' %. Pick a yeast whose attenuation reaches it.' end;
    if (v_rules ->> 'lager')::boolean then
        v_text := v_text || E'\nThe style is a lager style: the main yeast must be of type lager.';
    end if;
    if jsonb_array_length(v_rules -> 'families') > 0 then
        v_text := v_text || E'\nThe style requires a yeast of the family: '
                  || (select string_agg(f, ', ') from jsonb_array_elements_text(v_rules -> 'families') f) || '.';
    end if;
    if (v_rules ->> 'souring')::boolean then
        v_text := v_text || E'\nThe style is sour: add one souring culture (type lacto) next to the main yeast.';
    end if;

    v_text := v_text || E'\n\nTHE REQUEST';
    v_text := v_text || E'\nWanted: ' || coalesce(nullif((
        select string_agg((w.value ->> 'item') || ' (' || coalesce(w.value ->> 'role', 'background') || ')', ', ' order by w.ord)
          from jsonb_array_elements(coalesce(brief -> 'wanted', '[]'::jsonb)) with ordinality w(value, ord)), ''), 'nothing') || '.';
    select string_agg(e, ', ') into v_part from jsonb_array_elements_text(coalesce(brief -> 'excluded', '[]'::jsonb)) e;
    v_text := v_text || E'\nExcluded: ' || coalesce(v_part || '. Their products are not in the lists below.', 'nothing.');
    v_text := v_text || E'\nInventory: ' || coalesce(nullif((
        select string_agg(e, ', ') from jsonb_array_elements_text(coalesce(brief -> 'inventory', '[]'::jsonb)) e), ''), 'nothing')
        || '. Use every inventory product that fits.';
    v_text := v_text || E'\nSlots to fill (pick one of the listed ids for each):';
    select string_agg(E'\n- ' || (s.value ->> 'item') || ' (' || coalesce(s.value ->> 'role', 'background') || '): '
                      || case when jsonb_array_length(s.value -> 'ids') = 0 then 'no product'
                              else (s.value ->> 'kind') || ' ids '
                                   || (select string_agg(i, ', ') from jsonb_array_elements_text(s.value -> 'ids') i) end,
                      '' order by s.ord)
      into v_part
      from jsonb_array_elements(tbl -> 'slots') with ordinality s(value, ord);
    v_text := v_text || coalesce(v_part, E'\n- none');
    if jsonb_array_length(tbl -> 'absent') > 0 then
        select string_agg(E'\n- ' || (a.value ->> 'word') || ': ' || (a.value ->> 'reason'), '') into v_part
          from jsonb_array_elements(tbl -> 'absent') a;
        v_text := v_text || E'\nNot available, leave them out:' || v_part;
    end if;
    if jsonb_array_length(tbl -> 'unused_inventory') > 0 then
        select string_agg(E'\n- ' || (u.value ->> 'word') || ': ' || (u.value ->> 'reason'), '') into v_part
          from jsonb_array_elements(tbl -> 'unused_inventory') u;
        v_text := v_text || E'\nInventory that does not fit this recipe, do not pick it:' || v_part;
    end if;

    for v_kind in
        select * from (values ('fermentables', 'FERMENTABLES', 1), ('hops', 'HOPS', 2),
                              ('yeasts', 'YEASTS', 3), ('misc', 'EXTRAS', 4)) k(key, heading, ord)
         order by ord
    loop
        select string_agg(E'\n' || app.choose_row_line(r.value), '' order by r.ord) into v_part
          from jsonb_array_elements(tbl -> v_kind.key) with ordinality r(value, ord);
        v_text := v_text || E'\n\n' || v_kind.heading || coalesce(v_part, E'\nnone');
    end loop;

    return v_text;
end
$$;

-- A retry's table (docs/work/m6-compute-validate, Task 7): the table with the products step 11
-- banned taken out. A banned id leaves fermentables, hops, yeasts, misc and the ids of every slot
-- and inventory word, and is added to `excluded` so the existing check refuses it with its why.
-- feedback = null (try 1) returns the table unchanged. feedback.banned = [{ingredient_id, name, why}].
create or replace function app.choose_ban(tbl jsonb, feedback jsonb)
returns jsonb
language plpgsql
immutable
as $$
declare
    v_ids bigint[];
    v_try text;
    v_out jsonb := tbl;
    k     text;
begin
    if feedback is null or jsonb_typeof(feedback) <> 'object' then
        return tbl;
    end if;
    v_ids := array(select (b.value ->> 'ingredient_id')::bigint
                     from jsonb_array_elements(coalesce(feedback -> 'banned', '[]'::jsonb)) b);
    v_try := feedback ->> 'try';
    foreach k in array array['fermentables', 'hops', 'yeasts', 'misc'] loop
        v_out := jsonb_set(v_out, array[k], (
            select coalesce(jsonb_agg(r.value order by r.ord), '[]'::jsonb)
              from jsonb_array_elements(v_out -> k) with ordinality r(value, ord)
             where (r.value ->> 'ingredient_id')::bigint <> all (v_ids)));
    end loop;
    foreach k in array array['slots', 'inventory_words'] loop
        v_out := jsonb_set(v_out, array[k], (
            select coalesce(jsonb_agg(jsonb_set(s.value, '{ids}', (
                       select coalesce(jsonb_agg(i.value order by i.ord), '[]'::jsonb)
                         from jsonb_array_elements(s.value -> 'ids') with ordinality i(value, ord)
                        where (i.value #>> '{}')::bigint <> all (v_ids))) order by s.ord), '[]'::jsonb)
              from jsonb_array_elements(v_out -> k) with ordinality s(value, ord)));
    end loop;
    return jsonb_set(v_out, '{excluded}', coalesce(v_out -> 'excluded', '[]'::jsonb) || (
        select coalesce(jsonb_agg(jsonb_build_object(
                   'ingredient_id', (b.value ->> 'ingredient_id')::bigint, 'name', b.value ->> 'name',
                   'word', b.value ->> 'name',
                   'why', 'failed step 11 on try ' || v_try || ': ' || (b.value ->> 'why')) order by b.ord), '[]'::jsonb)
          from jsonb_array_elements(coalesce(feedback -> 'banned', '[]'::jsonb)) with ordinality b(value, ord)));
end
$$;

-- The block of the prompt that carries step 11's failures to the retry: the lines (rule or number,
-- value, limit), the failed recipe's picks, the banned names. Empty text for no feedback. Every
-- number in it is copied from the feedback.
-- last = {fermentables [{name, pct, usage}], hops [{name, share_pct, usage, minutes}],
--         yeast [{name}], extras [{name, usage, g?}]}.
create or replace function app.choose_feedback_prompt(feedback jsonb)
returns text
language plpgsql
immutable
as $$
declare
    v_text text;
    v_part text;
    v_last jsonb;
begin
    if feedback is null or jsonb_typeof(feedback) <> 'object' then
        return '';
    end if;
    v_last := coalesce(feedback -> 'last', '{}'::jsonb);
    v_text := E'\n\nTRY ' || (feedback ->> 'try') || E'\nTry ' || (feedback ->> 'try')
              || ': the last recipe failed step 11. Fix these and change as little else as you can:';
    select string_agg(E'\n- ' || l.value, '' order by l.ord) into v_part
      from jsonb_array_elements_text(coalesce(feedback -> 'lines', '[]'::jsonb)) with ordinality l(value, ord);
    v_text := v_text || coalesce(v_part, E'\n- none');

    v_text := v_text || E'\nThe last recipe\'s picks:';
    select string_agg(E'\n- fermentable ' || (f.value ->> 'name') || ' ' || coalesce(app.choose_num(f.value -> 'pct'), '?')
                      || ' % (' || coalesce(f.value ->> 'usage', '?') || ')', '' order by f.ord) into v_part
      from jsonb_array_elements(coalesce(v_last -> 'fermentables', '[]'::jsonb)) with ordinality f(value, ord);
    v_text := v_text || coalesce(v_part, '');
    select string_agg(E'\n- hop ' || (h.value ->> 'name') || ' ' || coalesce(app.choose_num(h.value -> 'share_pct'), '?')
                      || ' % (' || coalesce(h.value ->> 'usage', '?')
                      || case when h.value ->> 'minutes' is null then '' else ', ' || (h.value ->> 'minutes') || ' min' end
                      || ')', '' order by h.ord) into v_part
      from jsonb_array_elements(coalesce(v_last -> 'hops', '[]'::jsonb)) with ordinality h(value, ord);
    v_text := v_text || coalesce(v_part, '');
    select string_agg(E'\n- yeast ' || (y.value ->> 'name'), '' order by y.ord) into v_part
      from jsonb_array_elements(coalesce(v_last -> 'yeast', '[]'::jsonb)) with ordinality y(value, ord);
    v_text := v_text || coalesce(v_part, '');
    select string_agg(E'\n- extra ' || (x.value ->> 'name') || ' (' || coalesce(x.value ->> 'usage', '?') || ')',
                      '' order by x.ord) into v_part
      from jsonb_array_elements(coalesce(v_last -> 'extras', '[]'::jsonb)) with ordinality x(value, ord);
    v_text := v_text || coalesce(v_part, '');

    select string_agg(b.value ->> 'name', ', ' order by b.ord) into v_part
      from jsonb_array_elements(coalesce(feedback -> 'banned', '[]'::jsonb)) with ordinality b(value, ord);
    if v_part is not null then
        v_text := v_text || E'\nBanned for this try (not in the lists above any more): ' || v_part || '.';
    end if;
    return v_text;
end
$$;
