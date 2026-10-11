-- ref style-fit vocabulary: malt role, misc, flavour tags, sensory envelopes and style rules.
-- From docs/DATABASE-REVIEW.md §5.2. All tables start empty; P3 fills them.
-- Needs db/010_ref_schema.sql applied first.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/012_style_fit.sql
-- Idempotent: safe to re-run.

alter table ref.fermentable add column if not exists role text
    check (role in ('base', 'kilned', 'crystal', 'roast', 'adjunct', 'sugar'));

create table if not exists ref.misc (
    ingredient_id bigint primary key references ref.ingredient (id) on delete cascade,
    category      text not null
                  check (category in ('spice', 'herb', 'fruit', 'wood', 'coffee', 'cacao',
                                      'vanilla', 'lactose', 'smoke', 'fining', 'other'))
);

-- Flavour and origin vocabulary; parent gives partial matches (grapefruit ⊂ citrus ⊂ fruity)
create table if not exists ref.tag (
    id        bigint generated always as identity primary key,
    facet     text not null check (facet in ('origin', 'character', 'family')),
    name      text not null,
    parent_id bigint references ref.tag (id),
    unique (facet, name)
);

-- Source words → tag ("grapefruit", "grépfrút" → citrus). The only hand-made part.
create table if not exists ref.tag_synonym (
    word   text primary key,           -- name_key of the word
    tag_id bigint not null references ref.tag (id) on delete cascade
);

create table if not exists ref.ingredient_tag (
    ingredient_id bigint not null references ref.ingredient (id) on delete cascade,
    tag_id        bigint not null references ref.tag (id) on delete cascade,
    reviewed      boolean not null default false,   -- false = derived by code
    primary key (ingredient_id, tag_id)
);
create index if not exists ingredient_tag_tag_id_idx on ref.ingredient_tag (tag_id);

-- The sensations a style can describe; class decides what a style's silence means
create table if not exists ref.sensory_dimension (
    name  text primary key,            -- hop_aroma, roast, sourness, …
    class text not null check (class in ('core', 'specialty', 'transforming'))
);

-- A style's envelope: per sensation, the allowed intensity (0 none … 7 very high)
create table if not exists ref.style_sensory (
    style_id  bigint not null references ref.beer_style (id) on delete cascade,
    dimension text   not null references ref.sensory_dimension (name),
    min_level smallint not null check (min_level between 0 and 7),
    max_level smallint not null check (max_level between 0 and 7),
    quote     text not null,           -- the guideline sentence it comes from
    reviewed  boolean not null default false,
    primary key (style_id, dimension),
    check (min_level <= max_level)
);

-- Characters a style allows for a sensation (15B hop_aroma: earthy, floral)
create table if not exists ref.style_character (
    style_id  bigint not null,
    dimension text   not null,
    tag_id    bigint not null references ref.tag (id),
    primary key (style_id, dimension, tag_id),
    foreign key (style_id, dimension)
        references ref.style_sensory (style_id, dimension) on delete cascade
);

-- Rare hand-written exceptions: exactly one of ingredient or tag
create table if not exists ref.style_rule (
    id            bigint generated always as identity primary key,
    style_id      bigint not null references ref.beer_style (id) on delete cascade,
    ingredient_id bigint references ref.ingredient (id),
    tag_id        bigint references ref.tag (id),
    usage         text,                -- null = any use
    level         text not null
                  check (level in ('required', 'typical', 'allowed', 'out_of_style', 'changes_style')),
    max_pct       numeric(4, 1),
    quote         text not null,
    check ((ingredient_id is null) <> (tag_id is null))
);
