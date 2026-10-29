-- The recipe sheet column and the accept function (docs/work/m8-recipe-sheet-chat, Task 1).
-- app.recipe.sheet holds the Markdown sheet step 16 writes; app.accept_recipe turns a draft with a
-- sheet into a final recipe. No LLM.
-- Needs: db/048_save_recipe.sql (app.recipe).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/054_recipe_sheet.sql
-- Idempotent: safe to re-run.

alter table app.recipe add column if not exists sheet text;

-- Saves (or overwrites, so a re-run of step 16 works) the sheet of a recipe. Returns the recipe id.
create or replace function app.save_sheet(recipe_id bigint, sheet text)
returns bigint
language plpgsql
as $$
begin
    if sheet is null or btrim(sheet) = '' then
        raise exception 'save_sheet: the sheet is empty';
    end if;
    update app.recipe set sheet = save_sheet.sheet where id = recipe_id;
    if not found then
        raise exception 'save_sheet: unknown recipe %', recipe_id;
    end if;
    return recipe_id;
end;
$$;

-- Accepts a recipe: draft becomes final. A final recipe stays final and a brewed one is not changed
-- back. Raises when the recipe has no sheet. Returns the status after the call.
create or replace function app.accept_recipe(recipe_id bigint)
returns text
language plpgsql
as $$
declare
    r record;
begin
    select status, sheet into r from app.recipe where id = recipe_id;
    if not found then
        raise exception 'accept_recipe: unknown recipe %', recipe_id;
    end if;
    if r.sheet is null then
        raise exception 'accept_recipe: recipe % has no sheet', recipe_id;
    end if;
    if r.status = 'draft' then
        update app.recipe set status = 'final' where id = recipe_id;
        return 'final';
    end if;
    return r.status;
end;
$$;
