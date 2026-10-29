-- Task 11 read-only check (A7, A11): each validated m7 run's saved process against its step 10 row,
-- and its yeast rows against the pitch. Run ids are the validated runs of evals/results/2026-10-28-m7.json.
-- docker exec -i supabase-db psql -U postgres -d postgres -P pager=off < docs/work/m7-process/task11-check.sql
with runs as (
    select r.id as run_id, r.recipe_id, rc.fg, rc.process
    from app.run r join app.recipe rc on rc.id = r.recipe_id
    where r.id in (4957,4958,4959,4960,4961,4962,4963,4964,4965,4966,4967,4969,4970,4972,4973,4976,4977,4978,4980)
), s10 as (
    select distinct on (run_id) run_id, output from app.run_step
    where step = 10 and ok order by run_id, try desc
), yeast as (
    select recipe_id, string_agg(amount::text || ' ' || unit, ', ' order by id) as rows
    from app.recipe_item where usage = 'ferment' and unit = 'pack' group by recipe_id
)
select runs.run_id,
       (runs.process is not null)                                                         as has_process,
       (runs.process->'mash'->>'mash_c')::numeric = (s10.output->>'mash_c')::numeric      as mash_c_eq,
       exists (select 1 from jsonb_array_elements(runs.process->'mash'->'steps') x
               where (x->>'temp_c')::numeric = (s10.output->>'mash_c')::numeric)          as mash_step_eq,
       (runs.process->'boil'->>'boil_min')::numeric = (s10.output->'boil'->>'boil_min')::numeric as boil_eq,
       runs.fg = round((s10.output->'numbers'->>'fg')::numeric, 4)                        as fg_eq,
       runs.fg, y.rows as yeast_packs,
       (select string_agg((p->>'amount') || ' ' || (p->>'unit'), ', ')
        from jsonb_array_elements(runs.process->'fermentation'->'pitch') p)               as pitch
from runs join s10 using (run_id) left join yeast y on y.recipe_id = runs.recipe_id
order by run_id;
