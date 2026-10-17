-- Step 0 (load settings): the brewer profile (docs/work/m4-targets-blueprint). No LLM.
-- Creates the `default` profile row and app.step0_profile, which returns the step0.output shape.
-- Needs db/015_app.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/038_step0.sql
-- Idempotent: safe to re-run.

-- The default profile. The brewhouse numbers are the reference recipes' fixture numbers (20 L,
-- 72 %, 4 L/h, 2 L, 1.0 L/kg). The ions are distilled water: Bru'n Water *Water Knowledge*
-- §4.2.1, "Distilled water is free of all ions" (source `brunwater-water-knowledge`). This is a
-- placeholder until the user can set their own water (RECIPE-ROADMAP §8 Later).
-- Insert only, never update: a re-run must not overwrite numbers the user changed later.
insert into app.brewer_profile (name, batch_l, efficiency_pct, boil_off_l_h, losses_l, grain_abs_l_kg,
                                ca_mg_l, mg_mg_l, na_mg_l, so4_mg_l, cl_mg_l, hco3_mg_l, units)
select 'default', 20, 72, 4, 2, 1.0, 0, 0, 0, 0, 0, 0, 'metric'
where not exists (select 1 from app.brewer_profile where name = 'default');

-- Step 0: the profile with this id, or (null) the `default` row with the lowest id.
create or replace function app.step0_profile(profile_id bigint)
returns jsonb
language plpgsql
stable
as $$
declare
    p app.brewer_profile;
begin
    if profile_id is null then
        select * into p from app.brewer_profile where name = 'default' order by id limit 1;
        if not found then
            raise exception 'step 0: no default brewer profile; apply db/038_step0.sql';
        end if;
    else
        select * into p from app.brewer_profile where id = profile_id;
        if not found then
            raise exception 'step 0: no brewer profile %', profile_id;
        end if;
    end if;
    return jsonb_build_object(
        'batch_l', p.batch_l,
        'efficiency_pct', p.efficiency_pct,
        'boil_off_l_h', p.boil_off_l_h,
        'losses_l', p.losses_l,
        'grain_abs_l_kg', p.grain_abs_l_kg,
        'water', jsonb_build_object('ca', p.ca_mg_l, 'mg', p.mg_mg_l, 'na', p.na_mg_l,
                                    'so4', p.so4_mg_l, 'cl', p.cl_mg_l, 'hco3', p.hco3_mg_l),
        'units', p.units,
        'inventory', coalesce((
            select jsonb_agg(jsonb_build_object('raw_name', i.raw_name, 'ingredient_id', i.ingredient_id,
                                                'amount', i.amount, 'unit', i.unit) order by i.id)
            from app.inventory i where i.profile_id = p.id), '[]'::jsonb)
    );
end
$$;
