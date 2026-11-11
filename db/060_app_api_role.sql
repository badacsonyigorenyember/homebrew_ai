-- The app_api role: the login the .NET API (app/api) uses, through the Supavisor pooler. It can
-- read app.recipe, app.recipe_item, ref.ingredient and ref.beer_style, and nothing else.
-- Needs db/010_ref_schema.sql and db/015_app.sql, which create the tables.
-- Apply as postgres (docs/OPERATIONS.md §4), after `read -rs APP_API_PASSWORD` (the password is
-- never written into this file or the shell history):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 -v app_api_password="$APP_API_PASSWORD" < db/060_app_api_role.sql
-- Idempotent: safe to re-run. Re-running with a new password changes the password.

DO $$
BEGIN
    if not exists (
        select from pg_catalog.pg_roles 
        where rolname = 'app_api') 
       then 
        create role app_api login;
    end if;
END 
$$;

alter role app_api with login password :'app_api_password';
      
grant usage on schema app, ref to app_api;
grant select on app.recipe, app.recipe_item, ref.ingredient, ref.beer_style to app_api;
