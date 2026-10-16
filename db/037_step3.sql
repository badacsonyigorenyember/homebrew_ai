-- Step 3 (the deviation report): rules (docs/work/m3-deviations).
-- Each function finds one kind of deviation. The function that assembles the step 3 output is the
-- last function in this file. No LLM is involved.
-- Needs db/010_ref_schema.sql, db/015_app.sql, db/022_step2.sql, db/034_style_level.sql and
-- db/036_ingredient_resolver.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/037_step3.sql
-- Idempotent: safe to re-run.

-- RECIPE-ROADMAP §7, "Hints -> knobs", as it stands (starter table):
--   bitter          IBU -> top 25 % of range · BU:GU up
--   hoppy / juicy   late + dry hop share up (not IBU)
--   dry / crisp     mash 64-65 C · high-attenuation yeast · sugar <= 10 %
--   full / chewy    mash 68-69 C · oats or dextrin malt · lower-attenuation yeast
--   malty           Munich / Vienna share up · BU:GU down
--   darker          SRM up via crystal / roast
--   stronger / session   OG up / OG down
-- One row per hint and knob. direction: +1 pushes the knob up, -1 down. Hints with the same
-- side are synonyms and never conflict. "sugar <= 10 %" is a cap, not a direction, so it is left
-- out. Two sides conflict when they push one knob in opposite directions.
create or replace function app.hint_knob()
returns table (hint text, side text, knob text, direction int)
language sql
immutable
as $$
    values
        ('bitter',   'bitter',      'ibu',             1),
        ('bitter',   'bitter',      'bu_gu',           1),
        ('hoppy',    'hoppy/juicy', 'late_hop_share',  1),
        ('juicy',    'hoppy/juicy', 'late_hop_share',  1),
        ('dry',      'dry/crisp',   'mash_temp',      -1),
        ('dry',      'dry/crisp',   'attenuation',     1),
        ('crisp',    'dry/crisp',   'mash_temp',      -1),
        ('crisp',    'dry/crisp',   'attenuation',     1),
        ('full',     'full/chewy',  'mash_temp',       1),
        ('full',     'full/chewy',  'attenuation',    -1),
        ('chewy',    'full/chewy',  'mash_temp',       1),
        ('chewy',    'full/chewy',  'attenuation',    -1),
        ('malty',    'malty',       'munich_share',    1),
        ('malty',    'malty',       'bu_gu',          -1),
        ('darker',   'darker',      'srm',             1),
        ('stronger', 'stronger',    'og',              1),
        ('session',  'session',     'og',             -1)
$$;

-- Conflicts: wishes in the request that pull one knob in opposite directions. One deviation per
-- pair of sides, naming the brief's own hints of each side ("dry vs full, chewy").
create or replace function app.step3_conflicts(hints jsonb)
returns jsonb
language sql
stable
as $$
    with knob_label(knob, label) as (
        values ('ibu', 'IBU'), ('bu_gu', 'BU:GU'), ('late_hop_share', 'late hop share'),
               ('mash_temp', 'mash temperature'), ('attenuation', 'attenuation'),
               ('munich_share', 'Munich share'), ('srm', 'SRM'), ('og', 'OG')
    ),
    -- table rows of the hints the brief gave
    present as (
        select h.hint, h.side, h.knob, h.direction, h.ord
          from app.hint_knob() with ordinality as h(hint, side, knob, direction, ord)
         where exists (select 1 from jsonb_array_elements_text(coalesce(hints, '[]'::jsonb)) x
                        where lower(trim(x)) = h.hint)
    ),
    -- one row per side: its hints and what it does to its knobs, in table order
    sides as (
        select s.side, s.first_ord, s.hint_list, s.n_hints,
               (select string_agg(case k.direction when 1 then 'raise' else 'lower' end
                                  || case when s.n_hints = 1 then 's ' else ' ' end || l.label,
                                  ' and ' order by k.ord)
                  from (select distinct on (p.knob) p.knob, p.direction, p.ord
                          from present p where p.side = s.side order by p.knob, p.ord) k
                  join knob_label l on l.knob = k.knob) as effect
          from (select side, min(ord) as first_ord,
                       (select string_agg(hint, ', ' order by o) from
                            (select p2.hint, min(p2.ord) as o from present p2
                              where p2.side = p.side group by p2.hint) z) as hint_list,
                       count(distinct hint) as n_hints
                  from present p group by side) s
    )
    select coalesce(jsonb_agg(jsonb_build_object(
               'kind', 'conflict',
               'subject', a.hint_list || ' vs ' || b.hint_list,
               'from', 'the request''s own hints (RECIPE-ROADMAP §7)',
               'level', null,
               'requested_by', 'user',
               'because', a.hint_list || ' ' || a.effect || '; ' || b.hint_list || ' ' || b.effect
           ) order by a.first_ord, b.first_ord), '[]'::jsonb)
      from sides a
      join sides b on a.first_ord < b.first_ord
     where exists (select 1 from present pa join present pb on pa.knob = pb.knob
                    where pa.side = a.side and pb.side = b.side
                      and pa.direction = -pb.direction)
$$;

-- Numbers: a stated abv, og, ibu or srm outside the chosen style's range (bounds inclusive, an
-- open end works). batch_l is never compared. A style with no range for a number gives none.
create or replace function app.step3_numbers(stated jsonb, style_code text)
returns jsonb
language sql
stable
as $$
    with q as (
        select s.code, s.name, k.label, k.ord, (stated ->> k.key)::numeric as val,
               case k.key when 'abv' then s.abv when 'og' then s.og
                          when 'ibu' then s.ibu else s.srm end as r
          from ref.beer_style s
         cross join (values ('abv', 'ABV', 1), ('og', 'OG', 2), ('ibu', 'IBU', 3), ('srm', 'SRM', 4))
                    as k(key, label, ord)
         where s.code = style_code
           and jsonb_typeof(stated -> k.key) = 'number'
    ),
    -- the range as text: "22–40", or "40+" when it has no upper end
    outside as (
        select q.*,
               case when lower_inf(r) then '≤' || trim_scale(upper(r))
                    when upper_inf(r) then trim_scale(lower(r)) || '+'
                    else trim_scale(lower(r)) || '–' || trim_scale(upper(r)) end as range_text,
               case when not upper_inf(r) and val > upper(r) then 'above' else 'below' end as dir
          from q
         where r is not null and not isempty(r) and not (lower_inf(r) and upper_inf(r))
           and not r @> val
    )
    select coalesce(jsonb_agg(jsonb_build_object(
               'kind', 'number',
               'subject', label || ' ' || trim_scale(val),
               'from', code || ' ' || label || ' ' || range_text,
               'level', null,
               'requested_by', 'user',
               'because', label || ' ' || trim_scale(val) || ' is ' || dir || ' ' || name
                          || ' (' || code || ')''s ' || label || ' range ' || range_text
           ) order by ord), '[]'::jsonb)
      from outside
$$;

-- Mismatch: step 2's mismatch object (a style named, but the stated numbers fit another style)
-- becomes one deviation. The subject adds the stated numbers whose label appears in the range.
create or replace function app.step3_mismatch(stated jsonb, mismatch jsonb)
returns jsonb
language sql
stable
as $$
    select case when mismatch is null or jsonb_typeof(mismatch) <> 'object' then '[]'::jsonb
    else jsonb_build_array(jsonb_build_object(
        'kind', 'mismatch',
        'subject', (mismatch ->> 'named') || coalesce(' with ' || v.stated_text, ''),
        'from', (mismatch ->> 'named') || ' ' || (mismatch ->> 'range'),
        'level', null,
        'requested_by', 'user',
        'because', 'you named ' || (mismatch ->> 'named') || ', but '
                   || coalesce(v.stated_text, 'the request') || ' is outside its ' || (mismatch ->> 'range') || '; '
                   || (mismatch ->> 'chosen') || ' fits better and was chosen'))
    end
    from (select string_agg(k.label || ' ' || trim_scale((stated ->> k.key)::numeric), ', '
                            order by k.ord) as stated_text
            from (values ('abv', 'ABV', 1), ('og', 'OG', 2), ('ibu', 'IBU', 3), ('srm', 'SRM', 4))
                 as k(key, label, ord)
           where jsonb_typeof(stated -> k.key) = 'number'
             and (mismatch ->> 'range') ~ ('\m' || k.label || '\M')) v
$$;
