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
    v_warm_above_c numeric;
    v_lower_bound  text := (select string_agg(n, ', ') from jsonb_array_elements_text(coalesce(v_dose -> 'srm_lower_bound', '[]'::jsonb)) n);
    v_oil_range    numrange;
    v_ebc_range    numrange;
    v_misc         ref.misc%rowtype;
    v_dim          text;
    v_dose_range   numrange;
    v_g            numeric;
    v_word         text;
    v_cut          text;
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
            or ing.kind = 'yeast' and v_usage = 'ferment'
            or ing.kind = 'misc') then
        raise exception 'usage % is not valid for a % (ingredient %)', v_usage, ing.kind, v_ingredient;
    end if;
    if ing.kind = 'misc' then
        select * into v_misc from ref.misc m where m.ingredient_id = ing.id;
        if not found or not (v_usage = any (v_misc.usages)) then
            raise exception 'usage % is not a usage of % (ingredient %)', v_usage, ing.name, v_ingredient;
        end if;
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

    -- a process aid adds no flavour: allowed in any style, before the envelope is looked at
    if ing.kind = 'misc' and v_misc.purpose = 'process' then
        return jsonb_build_object('level', 'allowed',
            'because', 'no flavour effect: ' || ing.name || ' is a process aid (' || v_misc.category
                       || ') and adds no sensation to ' || v_style_label || '.');
    end if;

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

    -- 1b. a flavour misc (docs/work/s9-misc-extras): one added-character dimension chosen by its
    -- category, scored by the dose against the entry's own sourced dose; its tags are never read
    if ing.kind = 'misc' then
        select ue.dimension into v_dim from app.usage_effects() ue
            where ue.kind = 'misc' and ue.applies_to = v_misc.category;
        if v_dim is null then
            return jsonb_build_object('level', null,
                'because', 'no added-character dimension for category ' || v_misc.category
                           || ', so ' || ing.name || ' is not rated against ' || v_style_label || '.');
        end if;
        select * into sens from ref.style_sensory s
            where s.style_id = st.id and s.dimension = v_dim and s.reviewed;
        if not found then
            return jsonb_build_object('level', 'out_of_style',
                'because', 'specialty ' || v_dim || ' on ' || v_style_label || '.');
        end if;
        v_dose_range := v_misc.dose_g_per_l;
        v_what := v_dim || ' from ' || ing.name;
        if v_dose_range is null then
            v_notes := array[v_what || ': no sourced dose, intensity not checked.'];
        elsif not (v_dose ? 'g_per_l') then
            v_notes := array[v_what || ': dose not given, intensity not checked.'];
        else
            v_g := (v_dose ->> 'g_per_l')::numeric;
            if v_g < (v_cuts -> 'misc_dose' -> 'subtle_below' ->> 'ratio')::numeric * lower(v_dose_range) then
                v_word := 'subtle';
                v_cut := 'M1: below ' || (v_cuts -> 'misc_dose' -> 'subtle_below' ->> 'ratio') || ' x the lower sourced dose, '
                         || split_part(v_cuts -> 'misc_dose' -> 'subtle_below' ->> 'basis', ' (', 1);
            elsif v_g > (v_cuts -> 'misc_dose' -> 'aggressive_above' ->> 'ratio')::numeric * upper(v_dose_range) then
                v_word := 'aggressive';
                v_cut := 'M2: above ' || (v_cuts -> 'misc_dose' -> 'aggressive_above' ->> 'ratio') || ' x the upper sourced dose, '
                         || split_part(v_cuts -> 'misc_dose' -> 'aggressive_above' ->> 'basis', ' (', 1);
            else
                v_word := 'noticeable';
            end if;
            v_lvl := (v_cuts -> 'misc_dose' -> 'levels' ->> v_word)::int;
            v_what := v_what || ': ' || to_char(v_g, 'FM990.0#') || ' g/L is ' || v_word || ' ('
                      || app.level_word(v_lvl) || ') against the sourced '
                      || to_char(lower(v_dose_range), 'FM990.0#') || '-' || to_char(upper(v_dose_range), 'FM990.0#') || ' g/L'
                      || case when v_cut is not null then ' (' || v_cut || ')' else '' end;
            if v_lvl > sens.max_level then
                return jsonb_build_object('level', 'out_of_style',
                    'because', 'too much: ' || v_what || '; ' || v_style_label || ' allows up to '
                               || app.level_word(sens.max_level::int) || ' ' || v_dim || ': ''' || sens.quote || '''.');
            end if;
            v_notes := array[v_what || '.'];
        end if;
        if sens.min_level >= 1 then
            return jsonb_build_object('level', 'typical',
                'because', array_to_string(v_notes, ' ') || ' ' || v_style_label || ' asks for ' || v_dim || ': '''
                           || sens.quote || '''.');
        end if;
        return jsonb_build_object('level', 'allowed',
            'because', array_to_string(v_notes, ' ') || ' ' || v_style_label || ' allows ' || v_dim || ' but does not ask for it: '''
                       || sens.quote || '''.');
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
                v_notes := v_notes || (case e.dimension
                    when 'colour' then 'colour: the recipe SRM is not given (a fermentable has no colour), colour check skipped.'
                    else 'bitterness: the recipe IBU is not given, bitterness check skipped.' end);
            elsif v_value > upper(v_range) then
                v_levels := v_levels || 'out_of_style'::text;
                v_notes := v_notes || ('too much ' || e.dimension || ': '
                    || case when v_lower_bound is not null and e.dimension = 'colour' then 'at least ' else '' end
                    || case e.dimension when 'bitterness' then round(v_value)::text else round(v_value, 1)::text end
                    || ' ' || v_what
                    || case when v_lower_bound is not null and e.dimension = 'colour'
                            then ' (lower bound, no colour for ' || v_lower_bound || ')' else '' end
                    || ' is above ' || v_style_label || '''s ' || lower(v_range) || '-' || upper(v_range) || '.');
            elsif v_lower_bound is not null and e.dimension = 'colour' then
                v_notes := v_notes || ('colour: at least ' || round(v_value, 1) || ' SRM (lower bound, no colour for '
                    || v_lower_bound || ') is not above ' || v_style_label || '''s '
                    || lower(v_range) || '-' || upper(v_range) || '; the rest is unknown.');
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
                select h.total_oil_ml_100g into v_oil_range from ref.hop h where h.ingredient_id = ing.id;
                if v_oil_range is not null then
                    v_value := app.oil_dose((v_dose ->> 'g_per_l')::numeric, v_oil_range);
                end if;
            end if;
            v_what := trim(to_char(v_value, 'FM990.0000')) || ' mL/L oil';
        elsif e.dimension = 'roast' then
            v_scale := 'roast_index';
            if v_dose ? 'roast_index' then
                v_value := (v_dose ->> 'roast_index')::numeric;
            elsif v_dose ? 'pct' then
                select f.ebc into v_ebc_range from ref.fermentable f where f.ingredient_id = ing.id;
                if v_ebc_range is not null then
                    v_value := app.roast_index((v_dose ->> 'pct')::numeric, v_ebc_range);
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
                v_warm_above_c := (v_cuts -> 'esters' -> 'warm_step' ->> 'above_c')::numeric;
            else
                if exists (select 1 from jsonb_array_elements_text(v_cuts -> 'phenols' -> 'phenolic_tags' -> 'tags') w
                           where w = any (v_tags)) then
                    v_value := (v_cuts -> 'phenols' -> 'phenolic_character' ->> 'level')::numeric;
                else
                    v_value := 0;
                end if;
                v_warm := (v_cuts -> 'phenols' -> 'warm_step' ->> 'step')::int;
                v_warm_above_c := (v_cuts -> 'phenols' -> 'warm_step' ->> 'above_c')::numeric;
            end if;
            if v_ferm_c is null then
                v_notes := v_notes || 'fermentation temperature not given, warm step skipped.'::text;
            elsif v_ferm_c > v_warm_above_c then
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

        if v_lvl is null and v_scale is not null then
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
                -- said once, and only for an ingredient flagged in ref.ingredient_review
                if v_char_tags is null and v_review
                   and not ('no character tags (needs review).' = any (v_notes)) then
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

-- Whole recipe (Task 9): every line through app.style_level with the recipe's totals, the
-- required characteristic ingredients, and the min check on the recipe's late-hop oil dose and
-- roast index (one-level tolerance, user 2026-10-15). recipe is the app.check_recipe input.
-- extras (optional) is [{ingredient_id, usage, g}] (g optional): misc lines, each rated with
-- g / batch volume as its dose and added to lines as kind 'misc'.
-- Output: {style_code, lines[{kind, ingredient_id, name, usage, level, because}],
--          required[{requirement, met, because}], too_little[{dimension, level, min, because}]}
drop function if exists app.style_fit_recipe(jsonb);
create or replace function app.style_fit_recipe(recipe jsonb, extras jsonb default '[]')
returns jsonb
language plpgsql
stable
as $$
declare
    items       jsonb := app.check_recipe_items(recipe);
    numbers     jsonb := app.check_recipe(recipe) -> 'numbers';
    v_style     text := recipe ->> 'style_code';
    st          ref.beer_style%rowtype;
    v_label     text;
    v_volume    numeric := (recipe -> 'batch' ->> 'volume_l')::numeric;
    v_tol       int := (app.style_fit_cut_points() -> 'min_tolerance' ->> 'levels')::int;
    v_srm       numeric := (numbers ->> 'srm')::numeric;
    v_ibu       numeric := (numbers ->> 'ibu')::numeric;
    v_oil       numeric := 0;
    v_roast     numeric := 0;
    v_oil_miss  int := 0;
    v_lines     jsonb := '[]'::jsonb;
    v_required  jsonb := '[]'::jsonb;
    v_little    jsonb := '[]'::jsonb;
    x           jsonb;
    v_dose      jsonb;
    v_usage     text;
    v_late      boolean;
    v_range     numrange;
    v_ebc       numrange;
    v_res       jsonb;
    r           record;
    s           record;
    v_met       boolean;
    v_what      text;
    v_pct       numeric;
    v_lvl       int;
    v_total     numeric;
    v_no_colour jsonb := '[]'::jsonb;
    v_grist     jsonb;
begin
    select * into st from ref.beer_style b where b.code = v_style;
    v_label := coalesce(st.name, st.code) || ' (' || st.code || ')';

    -- colour lower bound: app.check_recipe leaves srm null when a fermentable has no colour. Here
    -- those fermentables count as 0 EBC (they can only add colour), so the SRM is a lower bound,
    -- and the lines say which fermentables had no colour. check_recipe itself is unchanged.
    if v_srm is null and numbers -> 'missing' ? 'ref.fermentable.ebc' then
        select coalesce(jsonb_agg(f ->> 'name'), '[]'::jsonb) into v_no_colour
            from jsonb_array_elements(items -> 'fermentables') f where f ->> 'ebc_mid' is null;
        select jsonb_agg(jsonb_build_object(
                   'pct', f -> 'pct', 'extract_pct', f -> 'extract_pct', 'mashed', f -> 'mashed',
                   'fermentability', f -> 'fermentability', 'ebc', coalesce((f ->> 'ebc_mid')::numeric, 0)))
            into v_grist from jsonb_array_elements(items -> 'fermentables') f;
        v_srm := app.srm(app.grist_mcu(
            app.solve_grist((recipe -> 'targets' ->> 'og')::numeric, v_grist,
                            (recipe -> 'batch' ->> 'efficiency_pct')::numeric, v_volume),
            v_volume));
    end if;

    -- recipe totals: late-hop oil dose (mL/L) and roast index
    for x in select * from jsonb_array_elements(items -> 'hops') loop
        if x ->> 'usage' in ('whirlpool', 'dry_hop')
           or x ->> 'usage' = 'boil' and (x ->> 'minutes')::numeric < 30 then
            select h.total_oil_ml_100g into v_range from ref.hop h
                where h.ingredient_id = (x ->> 'ingredient_id')::bigint;
            if v_range is null or x ->> 'g' is null then
                v_oil_miss := v_oil_miss + 1;
            else
                v_oil := v_oil + app.oil_dose((x ->> 'g')::numeric / v_volume, v_range);
            end if;
        end if;
    end loop;
    for x in select * from jsonb_array_elements(items -> 'fermentables') loop
        if x ->> 'role' = 'roast' and x ->> 'ebc_mid' is not null then
            v_roast := v_roast + (x ->> 'pct')::numeric * (x ->> 'ebc_mid')::numeric;
        end if;
    end loop;

    -- every line through style_level
    for x in select * from jsonb_array_elements(items -> 'fermentables') loop
        v_usage := case when (x ->> 'mashed')::boolean then 'mash' else 'boil' end;
        v_dose := jsonb_build_object('pct', x -> 'pct', 'ibu', v_ibu, 'srm', v_srm, 'srm_lower_bound', v_no_colour);
        if x ->> 'role' = 'roast' then
            v_dose := v_dose || jsonb_build_object('roast_index', v_roast);
        end if;
        v_res := app.style_level(v_style, (x ->> 'ingredient_id')::bigint, v_usage, v_dose);
        v_lines := v_lines || jsonb_build_object('kind', 'fermentable', 'ingredient_id', x -> 'ingredient_id',
            'name', x -> 'name', 'usage', v_usage, 'level', v_res -> 'level', 'because', v_res -> 'because');
    end loop;
    for x in select * from jsonb_array_elements(items -> 'hops') loop
        v_usage := x ->> 'usage';
        v_late := v_usage in ('whirlpool', 'dry_hop') or v_usage = 'boil' and (x ->> 'minutes')::numeric < 30;
        v_dose := jsonb_build_object('ibu', v_ibu, 'srm', v_srm, 'srm_lower_bound', v_no_colour);
        if v_usage = 'boil' then
            v_dose := v_dose || jsonb_build_object('minutes', x -> 'minutes');
        end if;
        if x ->> 'g' is not null then
            v_dose := v_dose || jsonb_build_object('g_per_l', (x ->> 'g')::numeric / v_volume);
        end if;
        if v_late and v_oil_miss = 0 then
            v_dose := v_dose || jsonb_build_object('oil_ml_per_l', v_oil);
        end if;
        v_res := app.style_level(v_style, (x ->> 'ingredient_id')::bigint, v_usage, v_dose);
        v_lines := v_lines || jsonb_build_object('kind', 'hop', 'ingredient_id', x -> 'ingredient_id',
            'name', x -> 'name', 'usage', v_usage, 'level', v_res -> 'level', 'because', v_res -> 'because');
    end loop;
    x := items -> 'yeast';
    v_res := app.style_level(v_style, (x ->> 'ingredient_id')::bigint, 'ferment',
        jsonb_build_object('ferm_c', x -> 'ferm_c', 'ibu', v_ibu, 'srm', v_srm, 'srm_lower_bound', v_no_colour));
    v_lines := v_lines || jsonb_build_object('kind', 'yeast', 'ingredient_id', x -> 'ingredient_id',
        'name', x -> 'name', 'usage', 'ferment', 'level', v_res -> 'level', 'because', v_res -> 'because');

    -- extras: misc lines, rated at their own dose
    for x in select * from jsonb_array_elements(coalesce(extras, '[]'::jsonb)) loop
        v_dose := '{}'::jsonb;
        if x ->> 'g' is not null then
            v_dose := jsonb_build_object('g_per_l', (x ->> 'g')::numeric / v_volume);
        end if;
        v_res := app.style_level(v_style, (x ->> 'ingredient_id')::bigint, x ->> 'usage', v_dose);
        v_lines := v_lines || jsonb_build_object('kind', 'misc', 'ingredient_id', x -> 'ingredient_id',
            'name', (select i.name from ref.ingredient i where i.id = (x ->> 'ingredient_id')::bigint),
            'usage', x ->> 'usage', 'level', v_res -> 'level', 'because', v_res -> 'because');
    end loop;

    -- required characteristic ingredients
    for r in
        select si.*, i.name as ing_name, t.name as tag_name
        from ref.style_ingredient si
        left join ref.ingredient i on i.id = si.ingredient_id
        left join ref.tag t on t.id = si.tag_id
        where si.style_id = st.id and si.required and si.reviewed
        order by si.id
    loop
        if r.role is not null then
            v_what := 'a ' || r.role || ' fermentable'
                || case when r.min_pct is not null then ' of at least ' || r.min_pct || '% of the grist' else '' end;
            select coalesce(sum((f ->> 'pct')::numeric), 0) into v_pct
                from jsonb_array_elements(items -> 'fermentables') f where f ->> 'role' = r.role;
            v_met := v_pct > 0 and v_pct >= coalesce(r.min_pct, 0);
            v_required := v_required || jsonb_build_object('requirement', v_what, 'met', v_met,
                'because', 'the recipe has ' || v_pct || '% ' || r.role
                           || ' for ' || v_label || ': ''' || r.quote || '''');
        elsif r.ingredient_id is not null then
            v_what := r.ing_name;
            v_met := exists (select 1 from jsonb_array_elements(items -> 'fermentables') f
                             where (f ->> 'ingredient_id')::bigint = r.ingredient_id)
                  or exists (select 1 from jsonb_array_elements(items -> 'hops') h
                             where (h ->> 'ingredient_id')::bigint = r.ingredient_id)
                  or (items -> 'yeast' ->> 'ingredient_id')::bigint = r.ingredient_id;
            v_required := v_required || jsonb_build_object('requirement', v_what, 'met', v_met,
                'because', case when v_met then v_what || ' is in the recipe' else v_what || ' is not in the recipe' end
                           || ' for ' || v_label || ': ''' || r.quote || '''');
        else
            v_what := 'an ingredient tagged ' || r.tag_name;
            v_met := exists (
                select 1 from ref.ingredient_tag it
                where it.tag_id = r.tag_id
                  and (it.ingredient_id in (select (f ->> 'ingredient_id')::bigint from jsonb_array_elements(items -> 'fermentables') f)
                       or it.ingredient_id in (select (h ->> 'ingredient_id')::bigint from jsonb_array_elements(items -> 'hops') h)
                       or it.ingredient_id = (items -> 'yeast' ->> 'ingredient_id')::bigint));
            v_required := v_required || jsonb_build_object('requirement', v_what, 'met', v_met,
                'because', case when v_met then 'the recipe has ' || v_what else 'the recipe has no ' || v_what end
                           || ' for ' || v_label || ': ''' || r.quote || '''');
        end if;
    end loop;

    -- min check on the recipe totals (hops and roast)
    for s in
        select * from ref.style_sensory ss
        where ss.style_id = st.id and ss.reviewed and ss.dimension in ('hop_flavour', 'hop_aroma', 'roast')
        order by ss.dimension
    loop
        if s.dimension = 'roast' then
            v_lvl := app.intensity_level('roast_index', v_roast);
            v_total := v_roast;
        else
            if v_oil_miss > 0 or v_volume is null then
                continue;
            end if;
            v_lvl := app.intensity_level('oil_ml_per_l', v_oil);
            v_total := v_oil;
        end if;
        if v_lvl < s.min_level - v_tol then
            v_little := v_little || jsonb_build_object('dimension', s.dimension, 'level', v_lvl, 'min', s.min_level,
                'because', 'too little ' || replace(s.dimension, '_', ' ') || ': the recipe total is '
                    || app.level_word(v_lvl) || ', ' || v_label || ' wants at least ' || app.level_word(s.min_level::int)
                    || ': ''' || s.quote || '''.');
        end if;
    end loop;

    return jsonb_build_object('style_code', v_style, 'lines', v_lines, 'required', v_required,
                              'too_little', v_little);
end
$$;
