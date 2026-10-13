-- Step 2 (pick the best-fit style): signal functions (docs/work/m2-best-fit-style).
-- Each function reads one signal from the request, the brief or a style row. The picking function
-- that adds them up is appended in a later task.
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

-- Stated numbers against a style's ranges. Inside a range: 1 at the centre, 0.5 at an edge, 0.75
-- when a bound is open. Outside: minus the distance divided by a scale per number. No range: 0.
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
                    total := total + 1 - 0.5 * abs(x - (lo + hi) / 2) / ((hi - lo) / 2);
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

-- Does the request make the adjunct prominent? One sentence must name the adjunct, hold a cue
-- word and hold no damper. Hyphens read as spaces ("honey-forward").
create or replace function app.adjunct_is_prominent(request text, adjunct text)
returns boolean
language plpgsql
immutable
as $$
declare
    -- words that make an adjunct prominent
    CUES    constant text[] := array['shine', 'forward', 'prominent', 'showcase', 'stand out',
                                     'taste', 'front', 'dominant', 'lots of', 'plenty of'];
    -- words that make it minor
    DAMPERS constant text[] := array['some', 'a bit', 'a little', 'a touch', 'a hint', 'subtle', 'slight'];
begin
    return exists (
        select 1
          from unnest(regexp_split_to_array(replace(lower(coalesce(request, '')), '-', ' '), '[.!?;]')) s
         where s ~ ('\m' || lower(adjunct) || '\M')
           and s ~ ('\m(' || array_to_string(CUES, '|') || ')\M')
           and s !~ ('\m(' || array_to_string(DAMPERS, '|') || ')\M'));
end;
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
