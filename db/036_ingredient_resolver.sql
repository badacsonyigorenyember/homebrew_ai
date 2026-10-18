-- Ingredient-word resolver: a word the user typed ("oats", "abbey yeast") to its ref.ingredient
-- products (docs/work/m3-deviations). First version, extended by M5.
-- app.resolve_ingredient first tries the aliases in ref.ingredient_alias (written by
-- loaders/extra_ingredients.py, docs/work/s8-ingredient-intake) and, only when none match, falls
-- back to app.resolve_ingredient_by_name (the name rules, as before aliases existed).
-- It keeps its own synonym list and never reads evals/ or the brief fixtures.
-- Needs db/010_ref_schema.sql (incl. ref.ingredient_alias) and db/015_app.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/036_ingredient_resolver.sql
-- Idempotent: safe to re-run.

-- Spellings and common names of the same product. Add a row only for a spelling or common name of
-- the same product, never to fit a brief.
create or replace function app.ingredient_synonym()
returns table (word text, same_as text, note text)
language sql
immutable
as $$
    values
        ('abbaye', 'abbey',   'French spelling of abbey'),
        ('caramel', 'crystal', 'caramel malt is the common name of crystal malt'),
        ('maize', 'corn',     'British name of corn')
$$;

-- Words that name the kind of ingredient: they restrict the kind of the products found.
create or replace function app.ingredient_kind_word()
returns table (word text, kind text)
language sql
immutable
as $$
    values ('malt', 'fermentable'), ('hop', 'hop'), ('yeast', 'yeast'),
           ('spice', 'misc'), ('herb', 'misc'), ('fruit', 'misc')
$$;

-- Words of an ingredient name: lower case, accents removed, anything not a letter or digit read as
-- a space, a trailing "s" dropped from words longer than 3 letters (not "ss"), then synonyms.
create or replace function app.ingredient_words(t text)
returns text[]
language sql
immutable
as $$
    select coalesce(array_agg(coalesce(s.same_as, w.word) order by w.ord), '{}'::text[])
      from (select case when length(x.word) > 3 and x.word like '%s' and x.word not like '%ss'
                        then left(x.word, -1) else x.word end as word, x.ord
              from regexp_split_to_table(
                       regexp_replace(
                           translate(lower(coalesce(t, '')), 'äöüéèêëàâáíóúçñôîïûù', 'aoueeeeaaaioucnoiiuu'),
                           '[^a-z0-9]+', ' ', 'g'),
                       ' ') with ordinality as x(word, ord)
             where x.word <> '') w
      left join app.ingredient_synonym() s on s.word = w.word;
$$;

-- The products a word names, by name only (aliases are not read).  The kind words malt, hop, yeast, spice, herb and fruit restrict the kind, so "crystal malt"
-- never reaches the Crystal hop. Two rules, the first that finds anything wins:
-- 1. the same words as a product's name; 2. every remaining word (kind word removed, only when
-- another word remains) among the words of the product's name and producer.
create or replace function app.resolve_ingredient_by_name(word text)
returns table (ingredient_id bigint, kind text, name text, rule text)
language sql
stable
as $$
    with q as (
        select app.ingredient_words(word) as w
    ),
    kind_of as (  -- the kind named by a kind word, if any (the first one)
        select k.kind
          from q, unnest(q.w) with ordinality as u(word, ord)
          join app.ingredient_kind_word() k on k.word = u.word
         order by u.ord
         limit 1
    ),
    rest as (  -- the words for rule 2: kind words removed, unless nothing else would remain
        select case when exists (select 1 from unnest(q.w) x where x not in (select word from app.ingredient_kind_word()))
                    then array(select x from unnest(q.w) x where x not in (select word from app.ingredient_kind_word()))
                    else q.w end as w
          from q
    ),
    cand as (
        select i.id, i.kind, i.name,
               app.ingredient_words(i.name) as name_words,
               app.ingredient_words(i.name || ' ' || i.producer) as all_words
          from ref.ingredient i
         where i.kind in ('fermentable', 'hop', 'yeast', 'water_salt', 'misc')
           and (not exists (select 1 from kind_of) or i.kind = (select kind from kind_of))
    ),
    same_name as (  -- rule 1
        select c.id, c.kind, c.name, 'same name'::text as rule
          from cand c, q
         where cardinality(q.w) > 0
           and (select array_agg(x order by x) from unnest(c.name_words) x)
             = (select array_agg(x order by x) from unnest(q.w) x)
    ),
    all_words as (  -- rule 2
        select c.id, c.kind, c.name, 'all words'::text as rule
          from cand c, rest r
         where cardinality(r.w) > 0
           and r.w <@ c.all_words
    )
    select r.id, r.kind, r.name, r.rule
      from (select * from same_name
            union all
            select * from all_words where not exists (select 1 from same_name)) r
     order by r.name, r.id;
$$;

-- Words that name a culture type, never a product: "Lactobacillus" finds every yeast of type lacto
-- (docs/work/m5-choose-ingredients). Used only when aliases and names find nothing.
create or replace function app.yeast_type_word()
returns table (word text, type text)
language sql
immutable
as $$
    values ('lactobacillus', 'lacto'), ('lacto', 'lacto')
$$;

-- The products a word names: aliases first, then the name rules above, then (when both find
-- nothing) the culture type the word names. An alias matches when its
-- words (app.ingredient_words, sorted) equal the query's words, or equal the query's words with
-- the kind words removed when the alias's product is of that kind ("fixture crystal malt" finds
-- the fermentable with alias "fixture crystal"; "fixture crystal yeast" does not).
create or replace function app.resolve_ingredient(word text)
returns table (ingredient_id bigint, kind text, name text, rule text)
language sql
stable
as $$
    with q as (
        select app.ingredient_words(word) as w
    ),
    hit as (
        select distinct i.id, i.kind, i.name, 'alias'::text as rule
          from ref.ingredient_alias a
          join ref.ingredient i on i.id = a.ingredient_id,
               q
         where cardinality(q.w) > 0
           and (select array_agg(x order by x) from unnest(app.ingredient_words(a.alias)) x)
             in ((select array_agg(x order by x) from unnest(q.w) x),
                 (select array_agg(x order by x) from unnest(q.w) x
                   where x not in (select k.word from app.ingredient_kind_word() k where k.kind = i.kind)))
    ),
    by_name as (
        select b.ingredient_id, b.kind, b.name, b.rule
          from app.resolve_ingredient_by_name(word) b
         where not exists (select 1 from hit)
    ),
    type_words as (  -- the query's words, kind word "yeast" removed when another word remains
        select case when exists (select 1 from unnest(q.w) x where x <> 'yeast')
                    then array(select x from unnest(q.w) x where x <> 'yeast')
                    else q.w end as w
          from q
    ),
    by_type as (
        select i.id as ingredient_id, i.kind, i.name, 'yeast type'::text as rule
          from type_words t
          join app.yeast_type_word() tw on app.ingredient_words(tw.word) = t.w
          join ref.yeast y on y.type = tw.type
          join ref.ingredient i on i.id = y.ingredient_id
         where not exists (select 1 from hit) and not exists (select 1 from by_name)
    )
    select h.id, h.kind, h.name, h.rule from hit h
    union all
    select * from by_name
    union all
    select * from by_type
    order by 3, 1;
$$;
