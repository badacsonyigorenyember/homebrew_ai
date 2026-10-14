-- Drops the adjunct word rule. Step 1 now reports each adjunct's role, so step 2 no longer
-- reads cue and damper words from the request (m2-adjunct-role, Task 8).
-- Apply: docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/023_drop_adjunct_rule.sql
-- Idempotent: safe to run again.

drop function if exists app.adjunct_is_prominent(text, text);
drop function if exists app.adjunct_cue(text, text);
