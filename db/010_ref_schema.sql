-- ref schema: reference data (styles and ingredients), each row traceable to a source.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/010_ref_schema.sql
-- Idempotent: safe to re-run.
-- Units are SI. Unknown values stay NULL. raw keeps the original record whole.

create schema if not exists ref;

-- Where a row came from. Every source has an edition or version.
create table if not exists ref.source (
    id        bigint generated always as identity primary key,
    slug      text not null unique,
    title     text,
    edition   text,
    publisher text,
    licence   text,
    url       text,
    notes     text
);

-- BJCP and BA styles. Vital statistics are ranges; a missing range is NULL, not zero.
create table if not exists ref.beer_style (
    id                         bigint generated always as identity primary key,
    source_id                  bigint not null references ref.source (id),
    guide                      text not null check (guide in ('BJCP', 'BA')),
    code                       text not null,
    name                       text,
    category                   text,
    category_code              text,
    og                         numrange,
    fg                         numrange,
    ibu                        numrange,
    srm                        numrange,
    abv                        numrange,
    characteristic_ingredients text,
    raw                        jsonb not null,
    unique (source_id, code)
);

-- One row per ingredient; the kind-specific details live in the tables below.
-- name_key and producer_key come from loaders.common.name_key, so re-loading never duplicates.
create table if not exists ref.ingredient (
    id           bigint generated always as identity primary key,
    kind         text not null check (kind in ('fermentable', 'hop', 'yeast', 'misc', 'water_salt')),
    name         text not null,
    name_key     text not null,
    producer     text not null default '',
    producer_key text not null default '',
    source_id    bigint not null references ref.source (id),
    raw          jsonb not null,
    unique (kind, producer_key, name_key)
);

create table if not exists ref.fermentable (
    ingredient_id    bigint primary key references ref.ingredient (id) on delete cascade,
    extract_dbfg_pct numeric(4, 1),
    ebc              numrange,
    max_pct          numeric(4, 1),  -- stated maximum share of the grist, %
    field_source     jsonb not null  -- which source each field was taken from
);

create table if not exists ref.hop (
    ingredient_id     bigint primary key references ref.ingredient (id) on delete cascade,
    origins           text[],
    purpose           text check (purpose in ('aroma', 'bittering', 'dual')),
    alpha_pct         numrange,
    total_oil_ml_100g numrange,
    field_source      jsonb not null  -- which source each field was taken from
);

create table if not exists ref.yeast (
    ingredient_id         bigint primary key references ref.ingredient (id) on delete cascade,
    product_id            text,
    type                  text,
    form                  text,
    attenuation_pct       numrange,
    temp_c                numrange,
    flocculation          text check (flocculation in
                              ('very low', 'low', 'medium low', 'medium',
                               'medium high', 'high', 'very high')),
    alcohol_tolerance_pct numeric(4, 1),
    field_source          jsonb not null  -- which source each field was taken from
);

create table if not exists ref.water_salt (
    ingredient_id      bigint primary key references ref.ingredient (id) on delete cascade,
    formula            text not null,
    ion_mg_per_l_per_g jsonb not null
);

-- Bring tables created by an earlier version of this file up to date
-- (create table if not exists leaves an existing table as it is).
-- Natural-key columns must be NOT NULL: a NULL never matches ON CONFLICT, so it would duplicate.
alter table ref.beer_style alter column guide set not null,
                           alter column code  set not null;
alter table ref.ingredient alter column kind  set not null;

-- Deleting an ingredient removes its detail row, for every kind.
alter table ref.hop
    drop constraint if exists hop_ingredient_id_fkey,
    add  constraint hop_ingredient_id_fkey
         foreign key (ingredient_id) references ref.ingredient (id) on delete cascade;
alter table ref.yeast
    drop constraint if exists yeast_ingredient_id_fkey,
    add  constraint yeast_ingredient_id_fkey
         foreign key (ingredient_id) references ref.ingredient (id) on delete cascade;
alter table ref.water_salt
    drop constraint if exists water_salt_ingredient_id_fkey,
    add  constraint water_salt_ingredient_id_fkey
         foreign key (ingredient_id) references ref.ingredient (id) on delete cascade;

-- Per-field provenance for fermentables (ref.fermentable had 0 rows when this was added,
-- so NOT NULL without a default works).
alter table ref.fermentable add column if not exists field_source jsonb not null;

-- Per-field provenance for yeasts (ref.yeast had 0 rows when this was added).
alter table ref.yeast add column if not exists field_source jsonb not null;

-- Columns removed by the database review (docs/DATABASE-REVIEW.md §5.1, 2026-10-11)

-- beer_style: edition lives in ref.source; co2_vol has no source yet (back in P6)
alter table ref.beer_style drop constraint if exists beer_style_guide_edition_code_key;
alter table ref.beer_style drop constraint if exists beer_style_source_id_code_key;
alter table ref.beer_style add  constraint beer_style_source_id_code_key unique (source_id, code);
alter table ref.beer_style drop column if exists edition,
                           drop column if exists co2_vol;

-- fermentable: potential follows from extract (maths library); role replaces type in P3
alter table ref.fermentable drop column if exists potential_sg,
                            drop column if exists type;

-- hop: nothing reads beta acids or the oil breakdown; both stay in raw
alter table ref.hop drop column if exists beta_pct,
                    drop column if exists oils_pct;

-- water_salt (empty): molar mass is an input to the ion computation, not a result
alter table ref.water_salt drop column if exists molar_mass;

-- How much of a fermentable's extract yeast can ferment (adjunct-fermentables, 2026-10-11):
-- full = all of it (sugars), normal = follows the yeast's attenuation (malts, flakes),
-- none = none of it (lactose). The 74 malts already loaded take the default, normal.
alter table ref.fermentable add column if not exists fermentability text not null default 'normal'
    check (fermentability in ('full', 'normal', 'none'));

-- Formulation data (s2-formulation-rules, 2026-10-15). Loaded by loaders/fermentable_facts.py.
alter table ref.fermentable
    add column if not exists enzyme_activity text
        check (enzyme_activity in ('none', 'low', 'normal', 'high')),
    add column if not exists min_boil_min integer check (min_boil_min between 60 and 120),
    add column if not exists description text,
    add column if not exists description_ref text;  -- page or URL inside field_source.description

-- One row per substitute pair, stored once (smaller id first); counts both ways, never chains.
create table if not exists ref.fermentable_substitute (
    fermentable_id bigint not null references ref.fermentable (ingredient_id) on delete cascade,
    substitute_id  bigint not null references ref.fermentable (ingredient_id) on delete cascade,
    source_id      bigint not null references ref.source (id),
    note           text   not null,  -- chart row ("1C row 9") or "user decision D, 2026-10-14"
    primary key (fermentable_id, substitute_id),
    check (fermentable_id < substitute_id));

create or replace view ref.fermentable_substitutes as  -- both directions
    select fermentable_id, substitute_id, source_id, note from ref.fermentable_substitute
    union all
    select substitute_id, fermentable_id, source_id, note from ref.fermentable_substitute;

-- Typical styles a maltster names for a malt, mapped to our style rows.
create table if not exists ref.fermentable_style (
    ingredient_id bigint not null references ref.fermentable (ingredient_id) on delete cascade,
    style_id      bigint not null references ref.beer_style (id),
    source_id     bigint not null references ref.source (id),
    primary key (ingredient_id, style_id));

-- Words a brewer types for a product, beyond its name (docs/work/s8-ingredient-intake).
-- Written by loaders/extra_ingredients.py, read by app.resolve_ingredient.
create table if not exists ref.ingredient_alias (
    ingredient_id bigint not null references ref.ingredient (id) on delete cascade,
    alias         text   not null,
    primary key (ingredient_id, alias));
