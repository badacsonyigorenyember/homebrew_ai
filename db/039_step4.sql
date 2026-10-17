-- Step 4 (targets): where OG, FG, ABV, IBU and SRM go (docs/work/m4-targets-blueprint).
-- app.step4_numbers is the one place that says so; rule 9 (db/032) calls it too, so the check and
-- step 4 cannot disagree. A later function in this file assembles the step 4 output. No LLM.
-- Needs db/030_maths.sql (app.abv), db/031_formulation_rules.sql and db/037_step3.sql
-- (app.hint_knob).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/039_step4.sql
-- Idempotent: safe to re-run.

-- A point inside a range: lower + fraction x (upper - lower). Null for a null or empty range;
-- the one bound when the other end is open.
create or replace function app.range_position(r numrange, fraction numeric)
returns numeric
language sql
immutable
as $$
    select case
        when r is null or isempty(r) then null
        when lower(r) is null then upper(r)
        when upper(r) is null then lower(r)
        else lower(r) + fraction * (upper(r) - lower(r))
    end
$$;

-- The OG that gives the ABV at the FG: the inverse of s1's app.abv (no new formula), found by
-- bisection because app.abv rises with OG. Raises when the ABV cannot be reached.
create or replace function app.og_for_abv(abv numeric, fg numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    lo numeric := fg;
    hi numeric := 1.200;
    mid numeric;
begin
    if abv < app.abv(lo, fg) or abv > app.abv(hi, fg) then
        raise exception 'og_for_abv: ABV % cannot be reached at FG % with an OG up to 1.200', abv, fg;
    end if;
    for i in 1..40 loop
        mid := (lo + hi) / 2;
        if app.abv(mid, fg) < abv then lo := mid; else hi := mid; end if;
    end loop;
    return (lo + hi) / 2;
end;
$$;

-- The FG that gives the ABV at the OG: the same bisection, with app.abv falling as FG rises.
create or replace function app.fg_for_abv(og numeric, abv numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    lo numeric := 1.000;
    hi numeric := og;
    mid numeric;
begin
    if abv > app.abv(og, lo) or abv < app.abv(og, hi) then
        raise exception 'fg_for_abv: ABV % cannot be reached at OG % with an FG between 1.000 and the OG', abv, og;
    end if;
    for i in 1..40 loop
        mid := (lo + hi) / 2;
        if app.abv(og, mid) > abv then lo := mid; else hi := mid; end if;
    end loop;
    return (lo + hi) / 2;
end;
$$;

-- The hint knobs the brief's hints move, minus every knob they pull both ways (R7: opposite
-- hints leave the knob at its default). One row per knob and direction; hints are the brief's
-- hints for it, comma-separated in table order.
create or replace function app.hint_moves(hint_list jsonb)
returns table (knob text, direction int, hints text, "position" numeric, mash_c numeric,
               intent text, source text)
language sql
stable
as $$
    with present as (
        select h.hint, h.knob, h.direction, h."position", h.mash_c, h.intent, h.source, h.ord
          from app.hint_knob() with ordinality as h(hint, side, knob, direction, "position", mash_c, intent, source, ord)
         where exists (select 1 from jsonb_array_elements_text(coalesce(hint_list, '[]'::jsonb)) x
                        where lower(trim(x)) = h.hint)
    )
    select p.knob, p.direction,
           string_agg(p.hint, ', ' order by p.ord),
           max(p."position"), max(p.mash_c), max(p.intent),
           string_agg(distinct p.source, '; ')
      from present p
     where p.knob not in (select knob from present group by knob having count(distinct direction) > 1)
     group by p.knob, p.direction
     order by min(p.ord)
$$;

-- One range-based target (OG, FG, IBU or SRM) as {value, from, because}: the user's number, else
-- the hinted position of the range, else the midpoint. places null = not rounded.
create or replace function app.step4_pick(code text, label text, rng numrange, stated_value numeric,
                                          pos numeric, hint_names text, places int)
returns jsonb
language plpgsql
immutable
as $$
declare
    p numeric := coalesce(pos, 0.5);
    v numeric;
    range_text text;
begin
    if stated_value is not null then
        return jsonb_build_object('value', stated_value, 'from', 'stated',
                                  'because', 'stated by the user');
    end if;
    if rng is null or isempty(rng) then
        return jsonb_build_object('value', null, 'from', 'none',
                                  'because', format('%s has no %s range', coalesce(code, 'no style'), label));
    end if;
    v := app.range_position(rng, p);
    if places is not null then v := round(v, places); end if;
    range_text := format('%s %s %s–%s', code, label, coalesce(trim_scale(lower(rng))::text, ''),
                         coalesce(trim_scale(upper(rng))::text, ''));
    if pos is not null then
        return jsonb_build_object('value', v, 'from', 'hint',
                   'because', format('%s: %s %% of %s', hint_names, trim_scale(pos * 100), range_text));
    end if;
    return jsonb_build_object('value', v, 'from', 'midpoint', 'because', 'midpoint of ' || range_text);
end;
$$;

-- The targets for a style, the user's stated numbers and the brief's hints, each as
-- {value, from, because}. Order of work:
--   1. IBU and SRM: stated, else the hinted position, else the midpoint.
--   2. OG the same way; FG stated or the midpoint (no hint moves FG).
--   3. ABV: stated ABV and stated OG -> FG solved; stated ABV only -> OG solved at the FG (it
--      replaces an OG hint, and may leave the OG range); else ABV = app.abv(OG, FG), and when
--      that is outside the ABV range and OG is not stated, OG moves just far enough (inside its
--      own range) to reach the nearest range end.
--   4. Rounding: OG and FG 4 decimals, ABV 2, IBU and SRM not rounded. An OG solved for a range
--      end is rounded toward the inside, so the rounded ABV stays in range.
create or replace function app.step4_numbers(style_code text, stated jsonb, hint_list jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
    st record;
    s jsonb := coalesce(stated, '{}'::jsonb);
    m record;
    ibu_j jsonb; srm_j jsonb; og_j jsonb; fg_j jsonb; abv_j jsonb;
    og_v numeric; fg_v numeric; abv_v numeric; abv_stated numeric := (s->>'abv')::numeric;
    og_before numeric; edge numeric; solved numeric;
begin
    select og, fg, abv, ibu, srm into st from ref.beer_style where code = style_code order by id limit 1;

    -- 1. IBU and SRM
    select * into m from app.hint_moves(hint_list) x where x.knob = 'ibu';
    ibu_j := app.step4_pick(style_code, 'IBU', st.ibu, (s->>'ibu')::numeric, m."position", m.hints, null);
    select * into m from app.hint_moves(hint_list) x where x.knob = 'srm';
    srm_j := app.step4_pick(style_code, 'SRM', st.srm, (s->>'srm')::numeric, m."position", m.hints, null);

    -- 2. OG and FG
    select * into m from app.hint_moves(hint_list) x where x.knob = 'og';
    og_j := app.step4_pick(style_code, 'OG', st.og, (s->>'og')::numeric, m."position", m.hints, 4);
    fg_j := app.step4_pick(style_code, 'FG', st.fg, (s->>'fg')::numeric, null, null, 4);
    og_v := (og_j->>'value')::numeric;
    fg_v := (fg_j->>'value')::numeric;

    -- 3. ABV
    if abv_stated is not null then
        abv_j := jsonb_build_object('value', abv_stated, 'from', 'stated', 'because', 'stated by the user');
        if s ? 'og' and not s ? 'fg' then
            fg_v := round(app.fg_for_abv(og_v, abv_stated), 4);
            fg_j := jsonb_build_object('value', fg_v, 'from', 'derived',
                'because', format('solved so app.abv gives the stated ABV %s at OG %s', trim_scale(abv_stated), trim_scale(og_v)));
        elsif not s ? 'og' and fg_v is not null then
            og_v := round(app.og_for_abv(abv_stated, fg_v), 4);
            og_j := jsonb_build_object('value', og_v, 'from', 'derived',
                'because', format('solved so app.abv gives the stated ABV %s at FG %s', trim_scale(abv_stated), trim_scale(fg_v)));
        end if;
    elsif og_v is null or fg_v is null then
        abv_j := jsonb_build_object('value', null, 'from', 'none',
                                    'because', format('%s has no OG and FG range to derive an ABV from', coalesce(style_code, 'no style')));
    else
        abv_v := app.abv(og_v, fg_v);
        if st.abv is not null and not isempty(st.abv) and not (og_j->>'from' = 'stated')
           and not (st.abv @> abv_v) then
            og_before := og_v;
            if lower(st.abv) is not null and abv_v < lower(st.abv) then
                edge := lower(st.abv);
                solved := round(ceil(app.og_for_abv(edge, fg_v) * 10000) / 10000, 4);
                if lower(st.og) is not null then solved := greatest(solved, lower(st.og)); end if;
                if upper(st.og) is not null then solved := least(solved, upper(st.og)); end if;
            else
                edge := upper(st.abv);
                solved := round(floor(app.og_for_abv(edge, fg_v) * 10000) / 10000, 4);
                if lower(st.og) is not null then solved := greatest(solved, lower(st.og)); end if;
                if upper(st.og) is not null then solved := least(solved, upper(st.og)); end if;
            end if;
            og_v := solved;
            og_j := jsonb_build_object('value', og_v, 'from', 'derived',
                'because', format('moved from %s so app.abv falls inside %s ABV %s–%s (nearest end %s) at FG %s',
                    trim_scale(og_before), style_code, trim_scale(lower(st.abv)), trim_scale(upper(st.abv)),
                    trim_scale(edge), trim_scale(fg_v)));
            abv_v := app.abv(og_v, fg_v);
        end if;
        abv_j := jsonb_build_object('value', round(abv_v, 2), 'from', 'derived',
                    'because', format('app.abv of OG %s and FG %s', trim_scale(og_v), trim_scale(fg_v)));
    end if;

    return jsonb_build_object('og', og_j, 'fg', fg_j, 'abv', abv_j, 'ibu', ibu_j, 'srm', srm_j);
end;
$$;
