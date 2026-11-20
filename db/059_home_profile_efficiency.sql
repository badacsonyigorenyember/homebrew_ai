-- Corrects the `home` brewer profile's efficiency from 75 % to 70 %. No LLM.
-- Needs db/058_home_profile.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/059_home_profile_efficiency.sql
-- Idempotent: safe to re-run.

-- db/058 set 75 % from an estimated 12-13 L into the fermenter. Bottling showed about
-- 10.5-11.5 L (20 x 0.5 L bottled, 0.5-1 L of trub left in the bucket), which gives 65-72 % at
-- OG 1.0426; the user chose 70 % (2026-11-20).
-- Changes the row only while it still holds 058's 75 %, so a number the user set later stays.
update app.brewer_profile
   set efficiency_pct = 70, updated_at = now()
 where name = 'home' and efficiency_pct = 75;
