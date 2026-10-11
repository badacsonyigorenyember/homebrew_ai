-- ref spot-check pack: what a person needs to check ref against the source documents.
-- Read-only. Prints row counts for all 15 ref tables, rows without a source, and 10 random
-- rows from each of the 7 tables P1a loads. The 8 style-fit tables stay empty until P3.
-- Run as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres < db/checks/ref_spotcheck.sql
-- Each run picks different random rows.

set default_transaction_read_only = on;

\echo '== Row counts (style-fit tables must be 0) =='
select t.tbl as "table", t.group_name as "group", t.n as rows
from (
              select 'source'            as tbl, 'loaded'    as group_name, count(*) as n from ref.source
    union all select 'beer_style',        'loaded',    count(*) from ref.beer_style
    union all select 'ingredient',        'loaded',    count(*) from ref.ingredient
    union all select 'fermentable',       'loaded',    count(*) from ref.fermentable
    union all select 'hop',               'loaded',    count(*) from ref.hop
    union all select 'yeast',             'loaded',    count(*) from ref.yeast
    union all select 'water_salt',        'loaded',    count(*) from ref.water_salt
    union all select 'misc',              'style-fit', count(*) from ref.misc
    union all select 'tag',               'style-fit', count(*) from ref.tag
    union all select 'tag_synonym',       'style-fit', count(*) from ref.tag_synonym
    union all select 'ingredient_tag',    'style-fit', count(*) from ref.ingredient_tag
    union all select 'sensory_dimension', 'style-fit', count(*) from ref.sensory_dimension
    union all select 'style_sensory',     'style-fit', count(*) from ref.style_sensory
    union all select 'style_character',   'style-fit', count(*) from ref.style_character
    union all select 'style_rule',        'style-fit', count(*) from ref.style_rule
) t;

\echo '== Ingredient rows per kind =='
select kind, count(*) as rows from ref.ingredient group by kind order by kind;

\echo '== Rows without a source (must be 0) =='
select 'beer_style' as "table", count(*) as no_source
from ref.beer_style b left join ref.source s on s.id = b.source_id
where s.id is null
union all
select 'ingredient', count(*)
from ref.ingredient i left join ref.source s on s.id = i.source_id
where s.id is null;

\echo '== source: 10 random rows =='
select slug, title, edition, publisher, url
from ref.source order by random() limit 10;

\echo '== beer_style: 10 random rows =='
select s.slug as source, b.guide, b.code, b.name, b.category,
       b.og, b.fg, b.ibu, b.srm, b.abv
from ref.beer_style b join ref.source s on s.id = b.source_id
order by random() limit 10;

\echo '== ingredient: 10 random rows =='
select s.slug as source, i.kind, i.producer, i.name
from ref.ingredient i join ref.source s on s.id = i.source_id
order by random() limit 10;

\echo '== fermentable: 10 random rows =='
select s.slug as source, i.producer, i.name,
       f.extract_dbfg_pct, f.ebc, f.max_pct, f.field_source
from ref.fermentable f
join ref.ingredient i on i.id = f.ingredient_id
join ref.source s on s.id = i.source_id
order by random() limit 10;

\echo '== hop: 10 random rows =='
select s.slug as source, i.name, h.origins, h.purpose,
       h.alpha_pct, h.total_oil_ml_100g, h.field_source
from ref.hop h
join ref.ingredient i on i.id = h.ingredient_id
join ref.source s on s.id = i.source_id
order by random() limit 10;

\echo '== yeast: 10 random rows =='
select s.slug as source, i.producer, i.name, y.product_id, y.type, y.form,
       y.attenuation_pct, y.temp_c, y.flocculation, y.alcohol_tolerance_pct, y.field_source
from ref.yeast y
join ref.ingredient i on i.id = y.ingredient_id
join ref.source s on s.id = i.source_id
order by random() limit 10;

\echo '== water_salt: 10 random rows =='
select s.slug as source, i.name, w.formula, w.ion_mg_per_l_per_g
from ref.water_salt w
join ref.ingredient i on i.id = w.ingredient_id
join ref.source s on s.id = i.source_id
order by random() limit 10;
