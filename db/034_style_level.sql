-- Style fit, part 2 (docs/work/s3-style-fit, Task 8): app.style_level, the 5-level decision of
-- docs/STYLE-FIT.md §5, with a "because" for every verdict. Reads only ref data and the
-- helpers of db/033 (no corpus, A7).
-- Needs db/012_style_fit.sql, db/033_style_fit_effects.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/034_style_level.sql
-- Idempotent: safe to re-run.

-- The BJCP intensity words for the 0-7 scale.
create or replace function app.level_word(level int)
returns text
language sql
immutable
as $$
    select (array['none', 'very low', 'low', 'medium-low', 'medium', 'medium-high', 'high',
                  'very high'])[level + 1]
$$;

-- True when a tag is one of the named tags or sits anywhere below one of them in the tree.
create or replace function app.tag_under(tag_id bigint, roots text[])
returns boolean
language sql
stable
as $$
    with recursive up as (
        select t.id, t.parent_id, t.name from ref.tag t where t.id = tag_under.tag_id
        union all
        select p.id, p.parent_id, p.name from up join ref.tag p on p.id = up.parent_id
    )
    select exists (select 1 from up where up.name = any (tag_under.roots))
$$;

-- STYLE-FIT.md §5 "character match = the best pair": over the ingredient's character tags and
-- the style's characters for one dimension, 1.0 for the same tag, 0.5 when one is the other's
-- parent, else 0; the highest pair wins. Null when either side has no tags. For a yeast, esters
-- look only at its ester tags (under fruity or estery) and phenols only at its phenolic tags
-- (the cut points' phenolic_tags), so a banana yeast is not judged on its phenols.
create or replace function app.tag_match(ingredient_id bigint, style_id bigint, dimension text)
returns numeric
language sql
stable
as $$
    with ing as (
        select t.id, t.name, t.parent_id
        from ref.ingredient_tag it
        join ref.tag t on t.id = it.tag_id
        where it.ingredient_id = tag_match.ingredient_id and t.facet = 'character'
    ),
    ing_used as (
        select i.* from ing i
        where case tag_match.dimension
                  when 'esters' then app.tag_under(i.id, array['fruity', 'estery'])
                  when 'phenols' then i.name in (
                      select jsonb_array_elements_text(
                          app.style_fit_cut_points() -> 'phenols' -> 'phenolic_tags' -> 'tags'))
                  else true
              end
    ),
    sty as (
        select t.id, t.parent_id
        from ref.style_character sc
        join ref.tag t on t.id = sc.tag_id
        where sc.style_id = tag_match.style_id and sc.dimension = tag_match.dimension
    )
    select case
        when not exists (select 1 from ing_used) or not exists (select 1 from sty) then null
        else coalesce((select max(case when i.id = s.id then 1.0
                                       when i.parent_id = s.id or s.parent_id = i.id then 0.5
                                       else 0 end)
                       from ing_used i cross join sty s), 0)
    end
$$;

create or replace function app.style_level(style_code text, ingredient_id bigint, usage text,
                                           dose jsonb default '{}')
returns jsonb
language plpgsql
stable
as $$
declare
    v_style_code   text := style_level.style_code;
    v_ingredient   bigint := style_level.ingredient_id;
    v_usage        text := style_level.usage;
    v_dose         jsonb := coalesce(style_level.dose, '{}'::jsonb);
    st             ref.beer_style%rowtype;
    ing            ref.ingredient%rowtype;
    v_role         text;
    v_tags         text[];
    v_char_tags    text;
    v_review       boolean;
    v_cuts         jsonb := app.style_fit_cut_points();
    v_minutes      numeric := (v_dose ->> 'minutes')::numeric;
    v_ferm_c       numeric := (v_dose ->> 'ferm_c')::numeric;
    v_style_label  text;
    v_levels       text[] := '{}';
    v_notes        text[] := '{}';
    v_level        text;
    v_rule         record;
    v_row          record;
    v_hit          record;
    e              record;
    sens           ref.style_sensory%rowtype;
    v_class        text;
    v_value        numeric;
    v_what         text;
    v_scale        text;
    v_lvl          int;
    v_tol          int := (v_cuts -> 'min_tolerance' ->> 'levels')::int;
    v_match        numeric;
    v_style_chars  text;
    v_warm         int;
    v_range        numrange;
    v_dose_key     numeric;
    v_oil          numrange;
begin
    select * into st from ref.beer_style b where b.code = v_style_code;
    if not found then
        raise exception 'unknown style code: %', v_style_code;
    end if;
    select * into ing from ref.ingredient i where i.id = v_ingredient;
    if not found then
        raise exception 'unknown ingredient id: %', v_ingredient;
    end if;
    if not (ing.kind = 'hop' and v_usage in ('boil', 'whirlpool', 'dry_hop')
            or ing.kind = 'fermentable' and v_usage in ('mash', 'boil')
            or ing.kind = 'yeast' and v_usage = 'ferment') then
        raise exception 'usage % is not valid for a % (ingredient %)', v_usage, ing.kind, v_ingredient;
    end if;
    if ing.kind = 'hop' and v_usage = 'boil' and v_minutes is null then
        raise exception 'a hop boil needs dose.minutes';
    end if;

    v_style_label := coalesce(st.name, st.code) || ' (' || st.code || ')';
    select f.role into v_role from ref.fermentable f where f.ingredient_id = ing.id;
    select coalesce(array_agg(t.name), '{}') into v_tags
        from ref.ingredient_tag it join ref.tag t on t.id = it.tag_id
        where it.ingredient_id = ing.id;
    select string_agg(t.name, ', ' order by t.name) into v_char_tags
        from ref.ingredient_tag it join ref.tag t on t.id = it.tag_id
        where it.ingredient_id = ing.id and t.facet = 'character';
    v_review := exists (select 1 from ref.ingredient_review r where r.ingredient_id = ing.id);

    -- 0. rated at all?
    if not exists (select 1 from ref.style_sensory s where s.style_id = st.id and s.reviewed)
       and not exists (select 1 from ref.style_ingredient si where si.style_id = st.id and si.reviewed) then
        return jsonb_build_object('level', null,
                                  'because', 'not rated: ' || v_style_label || ' has no reviewed envelope');
    end if;

    -- 1. explicit override: the ingredient first, else one of its tags
    select r.level, r.quote into v_rule
    from ref.style_rule r
    left join ref.tag t on t.id = r.tag_id
    where r.style_id = st.id
      and (r.usage is null or r.usage = v_usage)
      and (r.ingredient_id = ing.id or t.name = any (v_tags))
    order by (r.ingredient_id is not null) desc,
             array_position(array['changes_style', 'out_of_style', 'required', 'typical', 'allowed'], r.level)
    limit 1;
    if found then
        return jsonb_build_object('level', v_rule.level,
            'because', 'rule for ' || v_style_label || ': ''' || v_rule.quote || '''');
    end if;

    -- 2. adjunct or sugar: named in the characteristic ingredients, or not usual
    if ing.kind = 'fermentable' and v_role in ('adjunct', 'sugar') then
        select si.quote into v_row
        from ref.style_ingredient si
        where si.style_id = st.id and si.reviewed
          and (si.ingredient_id = ing.id or si.role = v_role)
        order by (si.ingredient_id is not null) desc
        limit 1;
        if found then
            return jsonb_build_object('level', 'typical',
                'because', 'named in ' || v_style_label || '''s characteristic ingredients: ''' || v_row.quote || '''');
        end if;
        return jsonb_build_object('level', 'out_of_style',
            'because', 'not a usual ingredient of ' || v_style_label);
    end if;

    -- 3. every sensation this use drives
    for e in
        select ue.* from app.usage_effects() ue
        where (ue.kind = ing.kind or ue.kind = 'any')
          and (ue.applies_to = ing.kind or ue.applies_to = v_role or ue.applies_to = any (v_tags))
          and (ue.usage is null or ue.usage = v_usage)
          and (ue.min_minutes is null
               or v_minutes between ue.min_minutes and coalesce(ue.max_minutes, 1000000))
    loop
        -- colour and bitterness: the recipe's SRM / IBU against the style's range
        if e.dimension in ('bitterness', 'colour') then
            v_range := case e.dimension when 'bitterness' then st.ibu else st.srm end;
            v_value := (v_dose ->> case e.dimension when 'bitterness' then 'ibu' else 'srm' end)::numeric;
            v_what  := case e.dimension when 'bitterness' then 'IBU' else 'SRM' end;
            if v_range is null or upper(v_range) is null then
                v_notes := v_notes || (e.dimension || ': ' || v_style_label || ' has no range, check skipped.');
            elsif v_value is null then
                v_notes := v_notes || (e.dimension || ': dose not given, dose check skipped.');
            elsif v_value > upper(v_range) then
                v_levels := v_levels || 'out_of_style'::text;
                v_notes := v_notes || ('too much ' || e.dimension || ': ' || v_value || ' ' || v_what
                    || ' is above ' || v_style_label || '''s ' || lower(v_range) || '-' || upper(v_range) || '.');
            end if;
            continue;
        end if;

        select * into sens from ref.style_sensory s
            where s.style_id = st.id and s.dimension = e.dimension and s.reviewed;
        if not found then
            select d.class into v_class from ref.sensory_dimension d where d.name = e.dimension;
            if v_class = 'transforming' then
                v_levels := v_levels || 'changes_style'::text;
                v_notes := v_notes || (e.dimension || ' is transforming and ' || v_style_label || ' is silent on it.');
            elsif v_class = 'specialty' then
                v_levels := v_levels || 'out_of_style'::text;
                v_notes := v_notes || ('specialty ' || e.dimension || ' on ' || v_style_label || '.');
            end if;
            continue;
        end if;

        -- intensity of the dose on this dimension (null = cannot be computed)
        v_value := null; v_lvl := null; v_scale := null;
        if e.dimension in ('hop_flavour', 'hop_aroma') then
            v_scale := 'oil_ml_per_l';
            if v_dose ? 'oil_ml_per_l' then
                v_value := (v_dose ->> 'oil_ml_per_l')::numeric;
            elsif v_dose ? 'g_per_l' then
                select h.total_oil_ml_100g into v_oil from ref.hop h where h.ingredient_id = ing.id;
                if v_oil is not null then
                    v_value := app.oil_dose((v_dose ->> 'g_per_l')::numeric, v_oil);
                end if;
            end if;
            v_what := trim(to_char(v_value, 'FM990.0000')) || ' mL/L oil';
        elsif e.dimension = 'roast' then
            v_scale := 'roast_index';
            if v_dose ? 'roast_index' then
                v_value := (v_dose ->> 'roast_index')::numeric;
            elsif v_dose ? 'pct' then
                select f.ebc into v_oil from ref.fermentable f where f.ingredient_id = ing.id;
                if v_oil is not null then
                    v_value := app.roast_index((v_dose ->> 'pct')::numeric, v_oil);
                end if;
            end if;
            v_what := 'roast index ' || round(v_value);
        elsif e.dimension in ('esters', 'phenols') then
            -- base level from the yeast's tags, +warm step above the cut-point temperature
            if e.dimension = 'esters' then
                if 'lager' = any (v_tags) then
                    v_value := (v_cuts -> 'esters' -> 'lager_family' ->> 'level')::numeric;
                elsif exists (
                        select 1 from ref.ingredient_tag it join ref.tag t on t.id = it.tag_id
                        where it.ingredient_id = ing.id and t.facet = 'character'
                          and app.tag_under(t.id, array['fruity', 'estery'])) then
                    v_value := (v_cuts -> 'esters' -> 'ester_character' ->> 'level')::numeric;
                else
                    v_value := (v_cuts -> 'esters' -> 'no_ester_character' ->> 'level')::numeric;
                end if;
                v_warm := (v_cuts -> 'esters' -> 'warm_step' ->> 'step')::int;
                v_dose_key := (v_cuts -> 'esters' -> 'warm_step' ->> 'above_c')::numeric;
            else
                if exists (select 1 from jsonb_array_elements_text(v_cuts -> 'phenols' -> 'phenolic_tags' -> 'tags') w
                           where w = any (v_tags)) then
                    v_value := (v_cuts -> 'phenols' -> 'phenolic_character' ->> 'level')::numeric;
                else
                    v_value := 0;
                end if;
                v_warm := (v_cuts -> 'phenols' -> 'warm_step' ->> 'step')::int;
                v_dose_key := (v_cuts -> 'phenols' -> 'warm_step' ->> 'above_c')::numeric;
            end if;
            if v_ferm_c is null then
                v_notes := v_notes || 'fermentation temperature not given, warm step skipped.'::text;
            elsif v_ferm_c > v_dose_key then
                v_value := v_value + v_warm;
            end if;
            v_lvl := least(v_value, 7)::int;
            v_what := e.dimension;
        else
            -- present / absent dimensions (sourness, brett funk, smoke, spice ...)
            v_lvl := 1;
            v_what := replace(e.dimension, '_', ' ');
        end if;
        if v_scale is not null and v_value is not null then
            v_lvl := app.intensity_level(v_scale, v_value);
        end if;

        if v_lvl is null and e.dimension not in ('caramel') and v_scale is not null then
            v_notes := v_notes || (e.dimension || ': dose not given, dose check skipped.');
        elsif v_lvl is not null then
            if v_lvl > sens.max_level then
                v_levels := v_levels || 'out_of_style'::text;
                v_notes := v_notes || ('too much: ' || v_what || ' is ' || app.level_word(v_lvl) || ', '
                    || v_style_label || ' allows up to ' || app.level_word(sens.max_level::int)
                    || ': ''' || sens.quote || '''.');
            elsif e.kind = 'yeast' and e.dimension in ('esters', 'phenols')
                  and v_lvl < sens.min_level - v_tol then
                if v_review then
                    v_notes := v_notes || ('needs review: min check skipped for ' || e.dimension || '.');
                else
                    v_levels := v_levels || 'out_of_style'::text;
                    v_notes := v_notes || ('too little: ' || v_what || ' is ' || app.level_word(v_lvl) || ', '
                        || v_style_label || ' wants at least ' || app.level_word(sens.min_level::int)
                        || ': ''' || sens.quote || '''.');
                end if;
            end if;
        end if;

        -- character
        if e.carries_character then
            v_match := app.tag_match(ing.id, st.id, e.dimension);
            if v_match is null then
                if v_char_tags is null then
                    v_notes := v_notes || 'no character tags (needs review).'::text;
                end if;
            else
                select string_agg(t.name, ', ' order by t.name) into v_style_chars
                    from ref.style_character sc join ref.tag t on t.id = sc.tag_id
                    where sc.style_id = st.id and sc.dimension = e.dimension;
                if v_match >= (v_cuts -> 'character_match' ->> 'typical')::numeric then
                    v_levels := v_levels || 'typical'::text;
                    v_notes := v_notes || (e.dimension || ' character matches (' || v_char_tags || ' vs ' || v_style_chars || ').');
                elsif v_match >= (v_cuts -> 'character_match' ->> 'allowed')::numeric then
                    v_levels := v_levels || 'allowed'::text;
                    v_notes := v_notes || (e.dimension || ' character partly matches (' || v_char_tags || ' vs ' || v_style_chars || ').');
                else
                    v_levels := v_levels || 'out_of_style'::text;
                    v_notes := v_notes || ('wrong character: ' || v_char_tags || ' vs ' || v_style_chars
                        || ': ''' || sens.quote || '''.');
                end if;
            end if;
        end if;
    end loop;

    -- 4. combine
    v_level := case
        when 'changes_style' = any (v_levels) then 'changes_style'
        when 'out_of_style' = any (v_levels) then 'out_of_style'
        when 'typical' = any (v_levels) then 'typical'
        else 'allowed' end;

    -- 5. a fermentable the maltster lists for this style
    if v_level = 'allowed' and ing.kind = 'fermentable' then
        select s.title into v_hit
        from ref.fermentable_style fs join ref.source s on s.id = fs.source_id
        where fs.ingredient_id = ing.id and fs.style_id = st.id
        limit 1;
        if found then
            v_level := 'typical';
            v_notes := v_notes || ('listed for ' || v_style_label || ' in ' || coalesce(v_hit.title, 'a source') || '.');
        end if;
    end if;

    if cardinality(v_notes) = 0 then
        v_notes := array['no sensation of ' || v_style_label || ' conflicts with this use.'];
    end if;
    return jsonb_build_object('level', v_level, 'because', array_to_string(v_notes, ' '));
end
$$;
