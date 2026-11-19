-- The batch tables of the brewing app (docs/app/SYSTEM.md §8, ticket a1-05): app.batch, its copy of
-- the recipe's items (app.batch_item) and its checklist (app.batch_step), with every column up to
-- M3. The app_api role may read and write all three.
-- Needs db/015_app.sql (app.recipe, app.recipe_item, ref.ingredient) and db/060_app_api_role.sql
-- (the app_api role).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/061_app_batch.sql
-- Idempotent: safe to re-run.

create table if not exists app.batch (
    id             bigint  generated always as identity primary key,
    number         integer not null unique,                -- "Batch 7"; a1-06 gives the highest plus one
    name           text    not null,
    recipe_id      bigint  not null references app.recipe (id),
    brew_date      date    not null,
    status         text    not null default 'plan'
                   check (status in ('plan', 'prep', 'brew_day', 'ferment', 'condition', 'package', 'done')),
    -- copied from the recipe, with app.recipe's types
    batch_l        numeric(5, 1) not null,
    efficiency_pct numeric(4, 1) not null,
    process        jsonb  not null,
    og  numeric(5, 4), fg numeric(5, 4), abv numeric(4, 1),
    ibu numeric(5, 1), srm numeric(5, 1),
    locked_at      timestamptz,                            -- M3: set when the first Brew day step is ticked
    created_at     timestamptz not null default now()
);

create table if not exists app.batch_item (
    id             bigint  generated always as identity primary key,
    batch_id       bigint  not null references app.batch (id) on delete cascade,
    source_item_id bigint  references app.recipe_item (id) on delete set null,   -- the recipe item it was copied from
    -- copied from the recipe item, with app.recipe_item's types
    ingredient_id  bigint  references ref.ingredient (id),  -- null only for unlisted extras
    raw_name       text    not null,
    usage          text    not null,
    time_min       numeric(6, 1),
    pct            numeric(5, 2),
    amount         numeric(10, 3) not null,
    unit           text    not null,
    changed        boolean not null default false           -- M3: edited in Plan or Prep
);
create index if not exists batch_item_batch_id_idx on app.batch_item (batch_id);

create table if not exists app.batch_step (
    id               bigint  generated always as identity primary key,
    batch_id         bigint  not null references app.batch (id) on delete cascade,
    phase            text    not null
                     check (phase in ('plan', 'prep', 'brew_day', 'ferment', 'condition', 'package', 'done')),
    position         integer not null,                      -- order within its phase
    title            text    not null,
    planned          jsonb   not null default '[]',         -- a1-08: a list of { key, label, value, unit }
    actual           jsonb   not null default '{}',         -- a1-10: key -> number; empty means as planned
    step_date        date,
    date_pinned      boolean not null default false,        -- M3: the date was set by hand
    source           text    not null,                      -- mash.steps[0], user or ai
    done_at          timestamptz,                           -- null: not ticked
    note             text,
    timer_started_at timestamptz
);
create index if not exists batch_step_batch_id_idx on app.batch_step (batch_id);

-- Identity columns need no grant on their sequences: the insert privilege is enough.
grant select, insert, update, delete on app.batch, app.batch_item, app.batch_step to app_api;
