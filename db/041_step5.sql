-- Step 5 (design frame): what step 6 onward may choose from, with no ratio numbers
-- (docs/work/m4-targets-blueprint, R10). The frame holds the formulation rules and limits, one slot
-- per wanted ingredient with the products it resolves to (role and max_pct from the ingredient
-- table), the excluded and inventory words with their products, the ingredient intents of the hints
-- step 4 applied, and the attenuation the targets need. The function that assembles the step 5
-- output is the last function in this file. No LLM.
-- Needs db/031_formulation_rules.sql, db/032_formulation_check.sql (app.mash_attenuation),
-- db/036_ingredient_resolver.sql and db/039_step4.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/041_step5.sql
-- Idempotent: safe to re-run.

-- The products a word names, as [{ingredient_id, kind, name, role, max_pct}] in the resolver's
-- order. role and max_pct come from ref.fermentable; they are null for other kinds or when unset.
create or replace function app.step5_refs(word text)
returns jsonb
language sql
stable
as $$
    select coalesce(jsonb_agg(jsonb_build_object(
               'ingredient_id', r.ingredient_id, 'kind', r.kind, 'name', r.name,
               'role', f.role, 'max_pct', f.max_pct) order by r.ord), '[]'::jsonb)
      from (select x.*, row_number() over () as ord from app.resolve_ingredient(word) x) r
      left join ref.fermentable f on f.ingredient_id = r.ingredient_id
$$;

-- The same for one product the brewer profile names by id.
create or replace function app.step5_refs_of_id(product_id bigint)
returns jsonb
language sql
stable
as $$
    select coalesce(jsonb_agg(jsonb_build_object(
               'ingredient_id', i.id, 'kind', i.kind, 'name', i.name,
               'role', f.role, 'max_pct', f.max_pct)), '[]'::jsonb)
      from ref.ingredient i
      left join ref.fermentable f on f.ingredient_id = i.id
     where i.id = product_id
$$;

-- The attenuation the targets need, from step 4's output.
--   needed_pct   100 x (OG - FG) / (OG - 1) at the target OG and FG.
--   low_pct, high_pct   the same at the ends of rule 10's FG range: the style's FG range, or the
--                target FG +- midpoint_tolerance.fg when the FG or the ABV is stated (a high FG
--                gives the low attenuation).
--   yeast_*_pct  each of those plus mash_slope_pct_per_c x max(0, mash - mash_knee_c): the middle
--                of a yeast's attenuation_pct range that app.mash_attenuation turns back into it
--                at that mash temperature (Troester's curve, db/032).
-- Values are rounded to 2. A null OG or FG gives nulls with from none. Fermentability (lactose,
-- sugar) is rule 10's business in M6 and is not assumed here.
create or replace function app.step5_attenuation(targets jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    l jsonb := app.formulation_limits();
    og numeric := (targets #>> '{targets,og,value}')::numeric;
    fg numeric := (targets #>> '{targets,fg,value}')::numeric;
    mash numeric := (targets #>> '{mash_c,value}')::numeric;
    stated boolean := targets #>> '{targets,fg,from}' = 'stated' or targets #>> '{targets,abv,from}' = 'stated';
    style_fg numrange;
    fg_lo numeric;
    fg_hi numeric;
    tol numeric := (l #>> '{midpoint_tolerance,fg}')::numeric;
    shift numeric;
    needed numeric;
begin
    if og is null or fg is null or mash is null then
        return jsonb_build_object('needed_pct', null, 'low_pct', null, 'high_pct', null, 'mash_c', mash,
            'yeast_middle_pct', null, 'yeast_low_pct', null, 'yeast_high_pct', null, 'from', 'none',
            'because', 'no OG or FG target, so no attenuation is needed');
    end if;
    if not stated then
        select b.fg into style_fg from ref.beer_style b where b.code = targets #>> '{style,code}' order by b.id limit 1;
    end if;
    if stated or style_fg is null or isempty(style_fg) or lower(style_fg) is null or upper(style_fg) is null then
        fg_lo := fg - case when stated then tol else 0 end;
        fg_hi := fg + case when stated then tol else 0 end;
    else
        fg_lo := lower(style_fg);
        fg_hi := upper(style_fg);
    end if;
    shift := (l->>'mash_slope_pct_per_c')::numeric * greatest(0, mash - (l->>'mash_knee_c')::numeric);
    needed := 100 * (og - fg) / (og - 1);
    return jsonb_build_object(
        'needed_pct', round(needed, 2),
        'low_pct', round(100 * (og - fg_hi) / (og - 1), 2),
        'high_pct', round(100 * (og - fg_lo) / (og - 1), 2),
        'mash_c', mash,
        'yeast_middle_pct', round(needed + shift, 2),
        'yeast_low_pct', round(100 * (og - fg_hi) / (og - 1) + shift, 2),
        'yeast_high_pct', round(100 * (og - fg_lo) / (og - 1) + shift, 2),
        'from', 'derived',
        'because', format('100 x (OG %s - FG %s) / (OG - 1); the yeast band adds %s points for the %s °C mash '
                          || '(Troester''s curve, app.mash_attenuation)',
                          trim_scale(og), trim_scale(fg), trim_scale(round(shift, 2)), trim_scale(mash)));
end;
$$;

-- The step 5 output. targets is the step 4 output. Order of work (all of it reads, nothing is
-- chosen):
--   1. style_code, guidance: step 4's.
--   2. rules and limits: app.formulation_rules() and app.formulation_limits(), unchanged.
--   3. slots: one per wanted item, in order, with the products the item resolves to.
--   4. excluded and inventory: the brief's words, then the profile's inventory rows; a word that
--      resolves to nothing says so.
--   5. intents: the knobs step 4 applied that carry an ingredient intent.
--   6. attenuation: app.step5_attenuation.
create or replace function app.step5_frame(brief jsonb, profile jsonb, targets jsonb)
returns jsonb
language plpgsql
stable
as $$
begin
    return jsonb_build_object(
        'style_code', targets #>> '{style,code}',
        'rules', jsonb_build_object('from', 'app.formulation_rules() (db/031)',
            'rows', (select jsonb_agg(jsonb_build_object('rule', r.rule, 'checked', r.checked, 'sentence', r.sentence))
                       from app.formulation_rules() r)),
        'limits', jsonb_build_object('from', 'app.formulation_limits() (db/031)', 'values', app.formulation_limits()),
        'slots', coalesce((
            select jsonb_agg(jsonb_build_object('item', w.value->>'item', 'wanted_role', w.value->>'role',
                       'refs', x.refs,
                       'from', case when x.refs = '[]'::jsonb then 'not in the catalogue' else 'wanted in the request' end)
                       order by w.ord)
              from jsonb_array_elements(coalesce(brief->'wanted', '[]'::jsonb)) with ordinality w(value, ord),
                   lateral (select app.step5_refs(w.value->>'item') as refs) x), '[]'::jsonb),
        'excluded', coalesce((
            select jsonb_agg(jsonb_build_object('word', w.value, 'refs', x.refs,
                       'from', case when x.refs = '[]'::jsonb then 'not in the catalogue' else 'request' end)
                       order by w.ord)
              from jsonb_array_elements_text(coalesce(brief->'excluded', '[]'::jsonb)) with ordinality w(value, ord),
                   lateral (select app.step5_refs(w.value) as refs) x), '[]'::jsonb),
        'inventory', coalesce((
            select jsonb_agg(e.item order by e.grp, e.ord)
              from (select 1 as grp, w.ord, jsonb_build_object('word', w.value, 'refs', x.refs,
                           'from', case when x.refs = '[]'::jsonb then 'not in the catalogue' else 'request' end) as item
                      from jsonb_array_elements_text(coalesce(brief->'inventory', '[]'::jsonb)) with ordinality w(value, ord),
                           lateral (select app.step5_refs(w.value) as refs) x
                    union all
                    select 2, p.ord, jsonb_build_object('word', p.value->>'raw_name',
                           'refs', case when p.value->>'ingredient_id' is null then '[]'::jsonb
                                        else app.step5_refs_of_id((p.value->>'ingredient_id')::bigint) end,
                           'from', 'profile')
                      from jsonb_array_elements(coalesce(profile->'inventory', '[]'::jsonb)) with ordinality p(value, ord)) e),
            '[]'::jsonb),
        'intents', coalesce((
            select jsonb_agg(jsonb_build_object('hints', k.value->>'hints', 'knob', k.value->>'knob',
                       'intent', k.value->>'intent', 'source', k.value->>'source', 'from', 'hint') order by k.ord)
              from jsonb_array_elements(coalesce(targets->'knobs', '[]'::jsonb)) with ordinality k(value, ord)
             where k.value->>'intent' is not null), '[]'::jsonb),
        'attenuation', app.step5_attenuation(targets),
        'guidance', coalesce((brief->>'guidance')::boolean, true));
end;
$$;
