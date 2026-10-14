-- Step 2 (pick the best-fit style): signal functions (docs/work/m2-best-fit-style).
-- Each function reads one signal from the request, the brief or a style row. The picking function
-- that adds them up is the last function in this file.
-- Needs db/010_ref_schema.sql, db/015_app.sql and db/021_style_pairs.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/022_step2.sql
-- Idempotent: safe to re-run.

-- Words of a name: lower case, accents removed, punctuation read as spaces, "ipa" spelled out,
-- filler and guide words dropped.
create or replace function app.style_words(t text)
returns text[]
language sql
immutable
as $$
    select coalesce(array_agg(e.word order by w.ord, e.sub), '{}'::text[])
      from regexp_split_to_table(
               regexp_replace(
                   translate(lower(coalesce(t, '')), 'äöüéèêëàâáíóúçñôîïûù', 'aoueeeeaaaioucnoiiuu'),
                   '[^a-z0-9]+', ' ', 'g'),
               ' ') with ordinality as w(word, ord)
     cross join lateral unnest(case when w.word = 'ipa' then array['india', 'pale', 'ale']
                                    else array[w.word] end) with ordinality as e(word, sub)
     where e.word <> ''
       and e.word <> all (array['and', 'or', 'the', 'of', 'a', 'style', 'beer',
                                'bjcp', 'ba', 'brewers', 'association']);
$$;

-- Common names a guide itself gives for a style. Never add one made up to fit a brief.
create or replace function app.style_alias()
returns table (alias text, guide text, code text, source text)
language sql
immutable
as $$
    values
        ('milk stout',     'BJCP', '16A', 'BJCP 16A history: Historically known as "Milk" or "Cream" stouts'),
        ('cream stout',    'BJCP', '16A', 'BJCP 16A history: Historically known as "Milk" or "Cream" stouts'),
        ('west coast ipa', 'BJCP', '21A', 'BJCP 21A comments: sometimes known as West Coast IPA'),
        ('hefeweizen',     'BJCP', '10A', 'BJCP 10A comments: Also known as hefeweizen or weizenbier'),
        ('weizenbier',     'BJCP', '10A', 'BJCP 10A comments: Also known as hefeweizen or weizenbier')
$$;

-- How well a named style matches a style's name or one of its aliases, 0 to 1:
-- (style words found in the name / style words) x (named words found in the style / named words).
create or replace function app.style_name_score(named text, style_name text, aliases text[])
returns numeric
language sql
immutable
as $$
    with n as (select app.style_words(named) as nw)
    select case when cardinality(n.nw) = 0 then 0::numeric
                else coalesce((
                    select max(
                        (select count(*) from unnest(c.sw) s where s = any (n.nw))::numeric / cardinality(c.sw)
                      * (select count(*) from unnest(n.nw) x where x = any (c.sw))::numeric / cardinality(n.nw))
                      from (select app.style_words(cand) as sw
                              from unnest(array[style_name] || coalesce(aliases, '{}'::text[])) as cand) c
                     where cardinality(c.sw) > 0), 0::numeric)
           end
      from n;
$$;

-- Does the style's name (or an alias) hold every word the user named? "imperial stout" is covered
-- by Imperial Stout, "session IPA" by no BJCP style, since none has the word "session".
create or replace function app.style_name_covers(named text, style_name text, aliases text[])
returns boolean
language sql
immutable
as $$
    select cardinality(app.style_words(named)) > 0 and exists (
        select 1
          from (select app.style_words(cand) as sw
                  from unnest(array[style_name] || coalesce(aliases, '{}'::text[])) as cand) c
         where app.style_words(named) <@ c.sw);
$$;

-- Stated numbers against a style's ranges. Inside a range: 1 at the centre, 0.5 at an edge, plus a
-- tightness bonus TIGHT / (1 + width / scale), so a style whose range fits tightly around the
-- stated value beats a wide range that merely contains it (a 4 % ABV fits Irish Stout 3.8-5.0
-- better than Sweet Stout 3.2-6.3). Width is measured in the number's own scale, so the same
-- formula serves ABV, OG, IBU and SRM in both guides. A range with an open end (BA "[40,)") has
-- no width: it gets 0.75 and no bonus. Outside: minus the distance divided by the scale.
-- No range: 0.
create or replace function app.style_number_score(stated jsonb, abv numrange, og numrange, ibu numrange, srm numrange)
returns table (score numeric, outside text[])
language plpgsql
immutable
as $$
declare
    SCALE_ABV constant numeric := 1.0;    -- one point of ABV outside costs 1
    SCALE_OG  constant numeric := 0.008;  -- 8 gravity points outside cost 1
    SCALE_IBU constant numeric := 10;     -- 10 IBU outside cost 1
    SCALE_SRM constant numeric := 5;      -- 5 SRM outside cost 1
    TIGHT     constant numeric := 1.0;    -- most a very narrow range adds when it contains the number
    item      record;
    x         numeric;
    lo        numeric;
    hi        numeric;
    dist      numeric;
    total     numeric := 0;
    misses    text[] := '{}';
begin
    for item in
        select * from (values ('abv', 'ABV', abv, SCALE_ABV), ('og', 'OG', og, SCALE_OG),
                              ('ibu', 'IBU', ibu, SCALE_IBU), ('srm', 'SRM', srm, SCALE_SRM))
               as t(key, label, r, scale)
    loop
        if stated ? item.key and jsonb_typeof(stated -> item.key) = 'number' and item.r is not null
           and not isempty(item.r) then
            x := (stated ->> item.key)::numeric;
            lo := lower(item.r);
            hi := upper(item.r);
            if item.r @> x then
                if lo is null or hi is null then
                    total := total + 0.75;
                else
                    total := total + 1 - 0.5 * abs(x - (lo + hi) / 2) / ((hi - lo) / 2)
                                   + TIGHT / (1 + (hi - lo) / item.scale);
                end if;
            else
                dist := case when lo is not null and x < lo then lo - x else x - hi end;
                total := total - dist / item.scale;
                misses := misses || (item.label || ' ' || x || ' outside '
                                     || coalesce(lo::text, '') || case when hi is null then '+' else '–' || hi end);
            end if;
        end if;
    end loop;
    return query select total, misses;
end;
$$;

-- The words a brief asks for: hints (some renamed to the guide's tag words) and the words of
-- step 1's "unknown" phrases (4 letters or more; a phrase with not/no/without/less is dropped).
create or replace function app.brief_words(brief jsonb)
returns text[]
language sql
immutable
as $$
    select coalesce(array_agg(distinct w order by w), '{}'::text[])
      from (
          select case lower(trim(h)) when 'juicy' then 'hoppy'
                                     when 'darker' then 'dark-color'
                                     when 'stronger' then 'high-strength'
                                     when 'session' then 'session-strength'
                                     else lower(trim(h)) end as w
            from jsonb_array_elements_text(case when jsonb_typeof(brief -> 'hints') = 'array'
                                                then brief -> 'hints' else '[]'::jsonb end) h
          union all
          select p.w
            from jsonb_array_elements_text(case when jsonb_typeof(brief -> 'unknown') = 'array'
                                                then brief -> 'unknown' else '[]'::jsonb end) u
           cross join lateral regexp_split_to_table(lower(u), '[^a-z]+') as p(w)
           where lower(u) !~ '\m(not|no|without|less)\M'
             and length(p.w) >= 4
      ) all_words
     where w <> '';
$$;

-- A style's tags as lower-case words: BJCP keeps a comma-separated string, BA an array.
create or replace function app.style_tags(raw jsonb)
returns text[]
language sql
immutable
as $$
    select case jsonb_typeof(raw -> 'tags')
        when 'string' then coalesce((select array_agg(lower(trim(t)))
                                       from unnest(string_to_array(raw ->> 'tags', ',')) t
                                      where trim(t) <> ''), '{}'::text[])
        when 'array' then coalesce((select array_agg(lower(t)) from jsonb_array_elements_text(raw -> 'tags') t), '{}'::text[])
        else '{}'::text[]
    end;
$$;

-- Sum over the words: 1 for a hit in the tags, else 0.5 when the word's stem starts a word in the
-- style's text. Not capped here; the picking function caps it.
create or replace function app.style_word_score(words text[], tags text[], style_text text)
returns numeric
language sql
immutable
as $$
    select coalesce(sum(case
        when w = any (coalesce(tags, '{}'::text[])) then 1
        when lower(coalesce(style_text, '')) ~ ('\m' || regexp_replace(
                 case when length(w) > 4 then regexp_replace(w, '[ys]$', '') else w end,
                 '[^a-z0-9-]', '', 'g')) then 0.5
        else 0 end), 0)::numeric
      from unnest(coalesce(words, '{}'::text[])) w
     where w <> '';
$$;

-- A guide named in the request: 'bjcp', 'ba', or null when it names both or neither.
-- "BA" counts only in upper case, so the word "ba" in other text is not read as the guide.
create or replace function app.guide_from_request(request text)
returns text
language sql
immutable
as $$
    select case when b and not a then 'bjcp'
                when a and not b then 'ba'
           end
      from (select coalesce(request, '') ~* '\mBJCP\M' as b,
                   coalesce(request, '') ~ '\mBA\M' or coalesce(request, '') ~* 'brewers\s+association' as a) g;
$$;

-- Adjuncts that have a specialty style of their own, per guide.
create or replace function app.specialty_style()
returns table (adjunct text, guide text, code text, source text)
language sql
immutable
as $$
    values
        ('honey',    'BJCP', '31B', 'BJCP 31B aroma: additional fermentables (e.g., honey, molasses)'),
        ('molasses', 'BJCP', '31B', 'BJCP 31B aroma: additional fermentables (e.g., honey, molasses)'),
        ('honey',    'BA',   'specialty-honey-beer', 'BA style name: Specialty Honey Beer')
$$;

-- BJCP catch-all styles: a BA style paired with one of these keeps the BA style (no swap to
-- BJCP). The specific BA style (e.g. Dessert Stout or Pastry Beer) guides the recipe's resources
-- better than a catch-all (e.g. 30D Specialty Spice Beer). Like-for-like pairs (Koelsch = 5B) swap.
create or replace function app.bjcp_catch_all()
returns table (code text)
language sql
immutable
as $$
    values ('28A'), ('30A'), ('30B'), ('30C'), ('30D'), ('31A'), ('31B'),
           ('32A'), ('32B'), ('33A'), ('33B'), ('34A'), ('34B'), ('34C')
$$;

-- Step 2: pick the best-fit style for a step 1 brief. Every weight is a named constant below; the
-- signals are added in one visible line (the "total" in step 2 of the body).
-- The user's named style is the strongest evidence. The pick, "unknown" and the mismatch use the plain
-- total. Only the choice of alt_styles scales: when the name matches at least one scored style
-- (name score > 0), a style that shares no word with it counts its numbers and words at
-- NO_NAME_FACTOR (alt_total), so numbers and hint words alone cannot make an unrelated style (a pale
-- lager for an imperial stout) an alternative. When the name matches nothing, nothing is scaled.
-- The "named style" for a mismatch must hold every word the user named (app.style_name_covers), so
-- a partial match ("session IPA" against English IPA) is never reported as the style the user named.
-- guide_preference: 'any', 'bjcp', 'ba' from the webhook, or null when it was not sent.
create or replace function app.step2_best_style(brief jsonb, request text, guide_preference text)
returns jsonb
language plpgsql
stable
as $$
declare
    W_NAME     constant numeric := 4;    -- a full name match is worth 4
    WORD_CAP   constant numeric := 2;    -- hint and flavour words together never outweigh a name
    ALT_MARGIN constant numeric := 0.5;  -- a style within 0.5 of the best total is an alternative
    MIN_SCORE  constant numeric := 1.0;  -- below this total nothing fits: unknown
    NO_NAME_FACTOR constant numeric := 0.5;  -- when the name matches some style, a style sharing no
                                         -- word with it keeps only this share of its numbers and words
    named      text    := nullif(trim(coalesce(brief ->> 'named', '')), '');
    stated     jsonb   := case when jsonb_typeof(brief -> 'stated') = 'object' then brief -> 'stated' else '{}'::jsonb end;
    words      text[]  := app.brief_words(brief);
    g          text;                      -- 'any', 'bjcp' or 'ba'
    g_reason   text;
    scored     jsonb;                     -- every scored style, best first
    best       record;
    base       record;                    -- the base pick (a row of scored)
    base_code  text;
    pair_note  text := '';
    catch_note text := '';
    named_row  record;
    mismatch   jsonb := null;
    alts       text[] := '{}';
    cand       text;
    style_out  jsonb;
    spec_code  text;
    spec_item  text;
    strongest  text;
    reason     text;
    unknown_r  text := null;
begin
    -- 1. Guide: the webhook setting wins, then a guide named in the request, else both.
    if guide_preference is not null then
        g := guide_preference;
        g_reason := 'webhook setting: ' || guide_preference;
    elsif app.guide_from_request(request) is not null then
        g := app.guide_from_request(request);
        g_reason := 'the request names ' || upper(g);
    else
        g := 'any';
        g_reason := 'no guide set or named in the request';
    end if;

    -- 2. Score every style of the allowed guides. Equal totals go BJCP first, then by code.
    --    "pair" is the BJCP code of a BA style's decided pair (only under "any").
    select coalesce(jsonb_agg(to_jsonb(r) order by r.ord), '[]'::jsonb)
      into scored
      from (
          select q.*, row_number() over (order by q.total desc, (q.guide = 'BA'), q.code) as ord
            from (
              select s.id, s.guide, s.code, s.name,
                     x.ns as name_score, n.score as number_score, to_jsonb(n.outside) as outside, y.ws as word_score,
                     W_NAME * x.ns + (n.score + least(y.ws, WORD_CAP)) as total,
                     W_NAME * x.ns + (n.score + least(y.ws, WORD_CAP))
                         * case when x.ns = 0 and max(x.ns) over () > 0 then NO_NAME_FACTOR else 1 end as alt_total,
                     x.covers,
                     case when g = 'any' and s.guide = 'BA'
                          then (select p.bjcp_code from app.style_pair() p
                                 where p.ba_code = s.code and p.bjcp_code not in (select code from app.bjcp_catch_all())) end as pair,
                     case when g = 'any' and s.guide = 'BA'
                          then (select p.bjcp_code from app.style_pair() p
                                 where p.ba_code = s.code and p.bjcp_code in (select code from app.bjcp_catch_all())) end as catch_all
                from ref.beer_style s
               cross join lateral app.style_number_score(stated, s.abv, s.og, s.ibu, s.srm) n
               cross join lateral (select app.style_name_score(named, s.name, al.aliases),
                                          app.style_name_covers(named, s.name, al.aliases)
                                     from (select (select array_agg(a.alias) from app.style_alias() a
                                                    where a.guide = s.guide and a.code = s.code)) al(aliases)) x(ns, covers)
               cross join lateral (select app.style_word_score(words, app.style_tags(s.raw),
                                          concat_ws(' ', s.raw ->> 'overallimpression', s.raw ->> 'aroma',
                                                    s.raw ->> 'flavor', s.raw ->> 'mouthfeel'))) y(ws)
               where s.name is not null and (g = 'any' or upper(g) = s.guide)
            ) q
      ) r;

    select * into best from jsonb_to_recordset(scored)
        as t(id bigint, guide text, code text, name text, name_score numeric, number_score numeric,
             outside jsonb, word_score numeric, total numeric, covers boolean, pair text, catch_all text, ord bigint)
     order by ord limit 1;

    -- 3. Unknown: nothing fits well enough.
    if best.code is null or best.total < MIN_SCORE then
        return jsonb_build_object(
            'style', null,
            'unknown_reason', 'no style name, number or flavour word in the request fits a style',
            'alt_styles', '[]'::jsonb,
            'candidates', (select coalesce(jsonb_agg(jsonb_build_object('guide', c.guide, 'code', c.code,
                                  'score', round(c.total, 2)) order by c.ord), '[]'::jsonb)
                             from jsonb_to_recordset(scored) as c(guide text, code text, total numeric, ord bigint)
                            where c.ord <= 5),
            'scores', '{}'::jsonb,
            'mismatch', null,
            'guide_reason', g_reason,
            'reason', 'No style fits the request, so no style is picked.');
    end if;

    -- 4. Base pick. Under "any" a BA winner that has a BJCP pair is replaced by that pair
    --    (the pair's own scores are reported).
    base := best;
    if best.pair is not null then
        select t.* into base
          from jsonb_to_recordset(scored)
               as t(id bigint, guide text, code text, name text, name_score numeric, number_score numeric,
                    outside jsonb, word_score numeric, total numeric, covers boolean, pair text, catch_all text, ord bigint)
         where t.guide = 'BJCP' and t.code = best.pair;
        pair_note := '; ' || best.code || ' is the same style as ' || base.code || ' (style pair), BJCP used';
    elsif best.catch_all is not null then
        catch_note := best.code || ' pairs with the BJCP catch-all ' || best.catch_all;
        pair_note := '; ' || catch_note || ', BA kept';
    end if;
    base_code := base.code;

    -- 5. Alternatives: other styles within ALT_MARGIN of the best total, a paired BA code written
    --    as its BJCP pair, no duplicates, best first, at most 4.
    select coalesce(array_agg(z.alt order by z.ord), '{}') into alts
      from (select alt, ord from (
                select coalesce(t.pair, t.code) as alt, t.ord,
                       row_number() over (partition by coalesce(t.pair, t.code) order by t.ord) as rn
                  from jsonb_to_recordset(scored)
                       as t(code text, alt_total numeric, pair text, ord bigint)
                 where t.alt_total >= (select max(a.alt_total) from jsonb_to_recordset(scored) as a(alt_total numeric)) - ALT_MARGIN) y
             where rn = 1 and alt <> base_code
             order by ord limit 4) z;

    -- 6. Mismatch: the named style (best name score, at least 0.5; a paired BA style counts as its
    --    BJCP pair) differs from the base pick and a stated number lies outside its range.
    select t.* into named_row
      from jsonb_to_recordset(scored)
           as t(id bigint, guide text, code text, name text, name_score numeric, number_score numeric,
                outside jsonb, word_score numeric, total numeric, covers boolean, pair text, catch_all text, ord bigint)
     where t.name_score >= 0.5 and t.covers
     order by t.name_score desc, t.ord
     limit 1;
    if named_row.pair is not null then
        select t.* into named_row
          from jsonb_to_recordset(scored)
               as t(id bigint, guide text, code text, name text, name_score numeric, number_score numeric,
                    outside jsonb, word_score numeric, total numeric, covers boolean, pair text, catch_all text, ord bigint)
         where t.guide = 'BJCP' and t.code = named_row.pair;
    end if;
    if named_row.code is not null and named_row.code <> base_code and jsonb_array_length(named_row.outside) > 0 then
        mismatch := jsonb_build_object(
            'named', named_row.code || ' ' || named_row.name,
            'range', (select string_agg(regexp_replace(o, '^(\S+) \S+ outside ', '\1 '), ', ')
                        from jsonb_array_elements_text(named_row.outside) o),
            'chosen', base.code || ' ' || base.name);
    end if;

    -- 7. Specialty: a wanted item that has a specialty style for this guide and the role "feature"
    --    (step 1 sets the role). The request is not read here.
    style_out := jsonb_build_object('id', base.id, 'guide', base.guide, 'code', base.code, 'name', base.name);
    select sp.adjunct, sp.code
      into spec_item, spec_code
      from jsonb_array_elements(coalesce(brief -> 'wanted', '[]'::jsonb)) w
      join app.specialty_style() sp on sp.guide = base.guide and lower(w ->> 'item') ~ ('\m' || sp.adjunct || '\M')
     where w ->> 'role' = 'feature'
     order by sp.adjunct
     limit 1;
    if spec_code is not null then
        select jsonb_build_object('id', s.id, 'guide', s.guide, 'code', s.code, 'name', s.name)
          into style_out
          from ref.beer_style s where s.guide = base.guide and s.code = spec_code;
        alts := (base_code || array_remove(alts, spec_code))[1:4];
    end if;

    -- 8. Return the pick and why.
    strongest := case when W_NAME * base.name_score >= base.number_score
                           and W_NAME * base.name_score >= least(base.word_score, WORD_CAP)
                           and base.name_score > 0
                      then 'the name matches (' || round(base.name_score, 2) || ')'
                      when base.number_score >= least(base.word_score, WORD_CAP) and base.number_score > 0
                      then 'the stated numbers fit (' || round(base.number_score, 2) || ')'
                      else 'the flavour and hint words fit (' || round(least(base.word_score, WORD_CAP), 2) || ')'
                 end;
    reason := 'Picked ' || base.code || ' ' || base.name || ': ' || strongest || '.'
              || case when catch_note <> '' then ' ' || catch_note || '.' else '' end;
    if spec_code is not null then
        reason := 'Picked ' || (style_out ->> 'code') || ' ' || (style_out ->> 'name') || ': ' || spec_item
                  || ' has the role "feature" in step 1''s brief; base style ' || base.code || '.';
    end if;

    return jsonb_build_object(
        'style', style_out,
        'unknown_reason', unknown_r,
        'alt_styles', to_jsonb(alts),
        'candidates', (select coalesce(jsonb_agg(jsonb_build_object('guide', c.guide, 'code', c.code,
                              'score', round(c.total, 2)) order by c.ord), '[]'::jsonb)
                         from jsonb_to_recordset(scored) as c(guide text, code text, total numeric, ord bigint)
                        where c.ord <= 5),
        'scores', jsonb_build_object(
            'name', round(W_NAME * base.name_score, 2),
            'numbers', round(base.number_score, 2),
            'words', round(least(base.word_score, WORD_CAP), 2),
            'total', round(base.total, 2)),
        'mismatch', mismatch,
        'guide_reason', g_reason || case when g = 'any'
            then '; both guides scored, best fit ' || best.code || pair_note else '' end,
        'reason', reason);
end;
$$;
