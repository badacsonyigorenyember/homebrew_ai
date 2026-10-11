-- corpus: scraped recipes, their ingredient lines, the raw-name map and computed style profiles.
-- From docs/DATABASE-REVIEW.md §5.3. All tables start empty; P1b and P3 fill them.
-- Needs db/010_ref_schema.sql applied first.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/013_corpus.sql
-- Idempotent: safe to re-run.

create schema if not exists corpus;

create table if not exists corpus.recipe (
    id             bigint generated always as identity primary key,
    source_id      bigint not null references ref.source (id),
    external_id    text   not null,
    name           text,
    style_id       bigint references ref.beer_style (id),   -- null = not mapped
    batch_l        numeric(6, 1),
    efficiency_pct numeric(4, 1),
    boil_min       smallint,
    og             numeric(5, 4),      -- as reported, for gates G3, G4, G6
    fg             numeric(5, 4),
    ibu            numeric(5, 1),
    srm            numeric(5, 1),
    abv            numeric(4, 1),
    views          integer,
    gates          jsonb  not null default '{}',   -- {"G1": 1.0, "G4": 0.0, …}; flags, never deletes
    quality_weight numeric(4, 3) not null default 0,
    raw            jsonb  not null,
    unique (source_id, external_id)
);
create index if not exists recipe_style_id_idx on corpus.recipe (style_id);

create table if not exists corpus.recipe_item (
    id         bigint generated always as identity primary key,
    recipe_id  bigint not null references corpus.recipe (id) on delete cascade,
    kind       text   not null check (kind in ('fermentable', 'hop', 'yeast', 'misc')),
    raw_name   text   not null,        -- kept as written
    raw_key    text   not null,        -- name_key(raw_name), joins name_map
    amount     numeric(10, 3),         -- kg for fermentables, g for hops and misc
    usage      text,                   -- boil · whirlpool · dry_hop · mash · …
    time_min   numeric(6, 1),
    alpha_pct  numeric(4, 1)           -- as reported, for recomputing IBU (G4)
);
create index if not exists recipe_item_recipe_id_idx on corpus.recipe_item (recipe_id);
create index if not exists recipe_item_kind_raw_key_idx on corpus.recipe_item (kind, raw_key);

-- Raw name → catalogue ingredient, or only a role when no ingredient matches. Unmapped = absent.
create table if not exists corpus.name_map (
    kind          text not null,
    raw_key       text not null,
    ingredient_id bigint references ref.ingredient (id),
    role          text,                -- base · crystal · roast · … when no ingredient
    method        text not null check (method in ('exact', 'rule', 'reviewed')),
    primary key (kind, raw_key),
    check (ingredient_id is not null or role is not null)
);

-- Style profiles: computed by a re-runnable job, one table per measure
create table if not exists corpus.style_profile (
    style_id     bigint primary key references ref.beer_style (id) on delete cascade,
    n_recipes    integer not null,     -- own recipes after gates
    family_share numeric(4, 3) not null,  -- 0 = only own data, 1 = only family
    computed_at  timestamptz not null default now()
);

create table if not exists corpus.style_grist (       -- % of grist per role
    style_id bigint not null references corpus.style_profile (style_id) on delete cascade,
    role     text   not null,
    p25 numeric(4, 1), p50 numeric(4, 1), p75 numeric(4, 1),
    used_share numeric(4, 3) not null,                -- share of recipes using the role
    primary key (style_id, role)
);

create table if not exists corpus.style_hop_use (     -- hop mass share and dose per use
    style_id     bigint not null references corpus.style_profile (style_id) on delete cascade,
    usage        text   not null,
    mass_share   numeric(4, 3) not null,
    g_per_l_p10  numeric(5, 2), g_per_l_p50 numeric(5, 2), g_per_l_p90 numeric(5, 2),
    primary key (style_id, usage)
);

create table if not exists corpus.style_ingredient (  -- top yeasts, hops, malts, extras
    style_id      bigint not null references corpus.style_profile (style_id) on delete cascade,
    ingredient_id bigint not null references ref.ingredient (id),
    used_share    numeric(4, 3) not null,             -- weighted share of recipes
    usage         text,                               -- typical use (extras: boil · secondary · …)
    dose_p50      numeric(8, 2),                      -- g/L (hops, misc) or % (fermentables)
    primary key (style_id, ingredient_id)
);
