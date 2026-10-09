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
    guide                      text check (guide in ('BJCP', 'BA')),
    edition                    text not null,
    code                       text,
    name                       text,
    category                   text,
    category_code              text,
    og                         numrange,
    fg                         numrange,
    ibu                        numrange,
    srm                        numrange,
    abv                        numrange,
    co2_vol                    numrange,  -- stays NULL until P2
    characteristic_ingredients text,
    raw                        jsonb not null,
    unique (guide, edition, code)
);

-- One row per ingredient; the kind-specific details live in the tables below.
-- name_key and producer_key come from loaders.common.name_key, so re-loading never duplicates.
create table if not exists ref.ingredient (
    id           bigint generated always as identity primary key,
    kind         text check (kind in ('fermentable', 'hop', 'yeast', 'misc', 'water_salt')),
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
    potential_sg     numeric(5, 4),
    extract_dbfg_pct numeric(4, 1),
    ebc              numrange,
    type             text,           -- stays NULL until P3
    max_pct          numeric(4, 1)   -- stays NULL until P3
);

create table if not exists ref.hop (
    ingredient_id     bigint primary key references ref.ingredient (id),
    origins           text[],
    purpose           text check (purpose in ('aroma', 'bittering', 'dual')),
    alpha_pct         numrange,
    beta_pct          numrange,
    total_oil_ml_100g numrange,
    oils_pct          jsonb,
    field_source      jsonb not null  -- which source each field was taken from
);

create table if not exists ref.yeast (
    ingredient_id         bigint primary key references ref.ingredient (id),
    product_id            text,
    type                  text,
    form                  text,
    attenuation_pct       numrange,
    temp_c                numrange,
    flocculation          text check (flocculation in
                              ('very low', 'low', 'medium low', 'medium',
                               'medium high', 'high', 'very high')),
    alcohol_tolerance_pct numeric(4, 1)
);

create table if not exists ref.water_salt (
    ingredient_id      bigint primary key references ref.ingredient (id),
    formula            text not null,
    molar_mass         numeric(7, 3) not null,
    ion_mg_per_l_per_g jsonb not null
);
