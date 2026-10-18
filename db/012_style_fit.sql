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
                                      'vanilla', 'smoke', 'fining', 'other'))
);

-- Lactose is a fermentable now (adjunct-fermentables), so it is no longer a misc category.
-- Brings a table created by an earlier version of this file up to date.
-- s9-misc-extras: a misc has a purpose (flavour or process), usages, a time, a sourced dose in
-- g/L and the source of each figure. The table had 0 rows when these not-null columns were added.
alter table ref.misc
    add column if not exists purpose      text   not null,
    add column if not exists usages       text[] not null,
    add column if not exists time_min     integer,
    add column if not exists dose_g_per_l numrange,
    add column if not exists description  text,
    add column if not exists field_source jsonb;

alter table ref.misc
    drop constraint if exists misc_category_check,
    add  constraint misc_category_check
         check (category in ('spice', 'herb', 'fruit', 'wood', 'coffee', 'cacao', 'vanilla',
                             'smoke', 'other',
                             'fining', 'nutrient', 'enzyme', 'acid', 'other-process')),
    drop constraint if exists misc_purpose_check,
    add  constraint misc_purpose_check
         check (purpose in ('flavour', 'process')),
    drop constraint if exists misc_category_purpose_check,
    add  constraint misc_category_purpose_check
         check ((purpose = 'flavour' and category in ('spice', 'herb', 'fruit', 'wood', 'coffee',
                                                      'cacao', 'vanilla', 'smoke', 'other'))
             or (purpose = 'process' and category in ('fining', 'nutrient', 'enzyme', 'acid',
                                                      'other-process'))),
    drop constraint if exists misc_usages_check,
    add  constraint misc_usages_check
         check (cardinality(usages) > 0
                and usages <@ array['mash', 'boil', 'whirlpool', 'ferment', 'secondary', 'packaging']),
    drop constraint if exists misc_time_min_check,
    add  constraint misc_time_min_check
         check (time_min >= 0),
    drop constraint if exists misc_dose_check,
    add  constraint misc_dose_check
         check (lower(dose_g_per_l) >= 0);

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

-- A style's characteristic ingredients (R3, R6): exactly one of a fermentable role, an
-- ingredient or a tag (yeast family, hop origin). required = the recipe must have it (✅).
create table if not exists ref.style_ingredient (
    id            bigint generated always as identity primary key,
    style_id      bigint not null references ref.beer_style (id) on delete cascade,
    role          text check (role in ('base', 'kilned', 'crystal', 'roast', 'adjunct', 'sugar')),
    ingredient_id bigint references ref.ingredient (id) on delete cascade,
    tag_id        bigint references ref.tag (id) on delete cascade,
    required      boolean not null default false,
    min_pct       numeric(4, 1),     -- with role: at least this % of the grist
    quote         text not null,     -- the guideline text it comes from
    reviewed      boolean not null default false,
    check (num_nonnulls(role, ingredient_id, tag_id) = 1),
    check (min_pct is null or role is not null)
);
create index if not exists style_ingredient_style_id_idx on ref.style_ingredient (style_id);

-- Ingredients whose tags need a person: unknown descriptor words, or no descriptor text.
-- Rewritten by loaders/tags.py on every run.
create table if not exists ref.ingredient_review (
    ingredient_id bigint primary key references ref.ingredient (id) on delete cascade,
    reason        text not null      -- "unknown words: …" or "no descriptor text"
);
