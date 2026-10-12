-- app: the brewer's profile, inventory, briefs, recipes and pipeline run logs.
-- From docs/DATABASE-REVIEW.md §5.5. All tables start empty; P4 and P5 fill them.
-- Needs db/010_ref_schema.sql applied first.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/015_app.sql
-- Idempotent: safe to re-run.

create schema if not exists app;

-- step contract checks, docs/work/m0-harness
create extension if not exists pg_jsonschema with schema extensions;

create table if not exists app.brewer_profile (
    id              bigint generated always as identity primary key,
    name            text not null default 'default',
    batch_l         numeric(5, 1) not null,
    efficiency_pct  numeric(4, 1) not null,   -- brewhouse
    boil_off_l_h    numeric(4, 2) not null,
    losses_l        numeric(4, 2) not null,   -- kettle + fermenter
    grain_abs_l_kg  numeric(4, 2) not null default 1.0,
    ca_mg_l numeric(6, 1), mg_mg_l numeric(6, 1), na_mg_l numeric(6, 1),
    so4_mg_l numeric(6, 1), cl_mg_l numeric(6, 1), hco3_mg_l numeric(6, 1),
    units           text not null default 'metric' check (units in ('metric', 'us')),
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

create table if not exists app.inventory (
    id            bigint generated always as identity primary key,
    profile_id    bigint not null references app.brewer_profile (id) on delete cascade,
    ingredient_id bigint references ref.ingredient (id),   -- null = not in the catalogue
    raw_name      text   not null,
    amount        numeric(10, 3) not null check (amount >= 0),
    unit          text   not null check (unit in ('g', 'kg', 'ml', 'l', 'pack')),
    updated_at    timestamptz not null default now()
);
create index if not exists inventory_profile_id_idx on app.inventory (profile_id);

create table if not exists app.brief (
    id           bigint generated always as identity primary key,
    profile_id   bigint not null references app.brewer_profile (id),
    request_text text   not null,
    brief        jsonb  not null,          -- step 1 output, checked against its contract
    guidance_on  boolean not null default true,
    created_at   timestamptz not null default now()
);

create table if not exists app.recipe (
    id             bigint generated always as identity primary key,
    brief_id       bigint not null references app.brief (id),
    parent_id      bigint references app.recipe (id),     -- previous version
    style_id       bigint not null references ref.beer_style (id),
    status         text   not null default 'draft' check (status in ('draft', 'final', 'brewed')),
    batch_l        numeric(5, 1) not null,   -- snapshot of the profile used
    efficiency_pct numeric(4, 1) not null,
    targets        jsonb  not null,          -- step 4 output
    og  numeric(5, 4), fg numeric(5, 4), abv numeric(4, 1),
    ibu numeric(5, 1), srm numeric(5, 1),
    calc_version   text   not null,          -- maths library version that produced the numbers
    process        jsonb,                    -- P6: water, mash, boil, ferment, package
    created_at     timestamptz not null default now()
);
create index if not exists recipe_brief_id_idx on app.recipe (brief_id);

create table if not exists app.recipe_item (
    id            bigint generated always as identity primary key,
    recipe_id     bigint not null references app.recipe (id) on delete cascade,
    ingredient_id bigint references ref.ingredient (id),   -- null only for unlisted extras
    raw_name      text   not null,
    usage         text   not null check (usage in ('mash', 'sparge', 'boil', 'whirlpool',
                                                   'ferment', 'dry_hop', 'secondary', 'package')),
    time_min      numeric(6, 1),
    pct           numeric(5, 2),    -- the design ratio (grist % or hop share)
    amount        numeric(10, 3) not null,
    unit          text   not null check (unit in ('g', 'kg', 'ml', 'l', 'pack'))
);
create index if not exists recipe_item_recipe_id_idx on app.recipe_item (recipe_id);

create table if not exists app.recipe_deviation (
    id           bigint generated always as identity primary key,
    recipe_id    bigint not null references app.recipe (id) on delete cascade,
    subject      text   not null,
    level        text   not null check (level in ('out_of_style', 'changes_style')),
    requested_by text   not null check (requested_by in ('user', 'model')),
    note         text   not null            -- the "because"
);
create index if not exists recipe_deviation_recipe_id_idx on app.recipe_deviation (recipe_id);

create table if not exists app.run (
    id         bigint generated always as identity primary key,
    brief_id    bigint references app.brief (id),   -- null until step 1 writes the brief
    recipe_id   bigint references app.recipe (id),
    model       text   not null,
    eval_id     text,                                -- 'b01' when sent by the eval runner
    started_at  timestamptz not null default now(),
    finished_at timestamptz,                         -- null = still running or crashed
    ok          boolean                              -- null until finished
);

create table if not exists app.run_step (
    run_id bigint   not null references app.run (id) on delete cascade,
    step   smallint not null check (step between 0 and 16),
    try    smallint not null default 1,      -- the validate loop retries (max 3)
    input  jsonb    not null,
    output jsonb,
    ok     boolean  not null,
    ms     integer  not null,
    tokens integer,
    error  text,                             -- why a step failed; null when it passed
    primary key (run_id, step, try),
    constraint run_step_error_check check (ok = (error is null))
);

-- Run-log changes for tables created before m0-harness (no-ops on a fresh install).
alter table app.run alter column brief_id drop not null;
alter table app.run add column if not exists eval_id     text;
alter table app.run add column if not exists finished_at timestamptz;
alter table app.run add column if not exists ok          boolean;
alter table app.run_step add column if not exists error  text;
alter table app.run_step drop constraint if exists run_step_error_check;
alter table app.run_step add  constraint run_step_error_check check (ok = (error is null));
