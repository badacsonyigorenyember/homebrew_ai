-- The `home` brewer profile: the user's own brewhouse, next to the `default` fixture row
-- (db/038_step0.sql), which the tests and evals keep using. No LLM.
-- Needs db/038_step0.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/058_home_profile.sql
-- Idempotent: safe to re-run.

-- Numbers from the 10A Weissbier brew of 2026-11-08 (recipe 1489, Brewfather ingredients), all
-- estimated, not measured with a gauge: about 17.5 L pre-boil at 1.033, 12-13 L into the
-- fermenter at OG 1.043 (hydrometer at 20 C).
--   efficiency 75 %: 12 L at 1.043 from 1.10 kg wheat (82 %) + 1.10 kg Pilsner (80 %) is 75.4 %,
--     13 L would be 81.7 %; the cautious end, chosen by the user.
--   boil-off 2.75 L/h: about 17.5 L before the 90 min boil, 13-14 L after (2.5-3 L/h).
--   batch 10 L: the user brews 10 L batches.
-- Losses (2 L), grain absorption (1.0 L/kg) and the water (distilled, all ions 0) were not
-- measured, so they stay at the `default` values.
-- Insert only, never update: a re-run must not overwrite numbers the user changed later.
insert into app.brewer_profile (name, batch_l, efficiency_pct, boil_off_l_h, losses_l, grain_abs_l_kg,
                                ca_mg_l, mg_mg_l, na_mg_l, so4_mg_l, cl_mg_l, hco3_mg_l, units)
select 'home', 10, 75, 2.75, 2, 1.0, 0, 0, 0, 0, 0, 0, 'metric'
where not exists (select 1 from app.brewer_profile where name = 'home');
