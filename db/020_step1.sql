-- app.step1_read_answer: checks a model's step 1 answer (docs/work/m1-read-request).
-- Needs db/015_app.sql (pg_jsonschema in schema extensions).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/020_step1.sql
-- Idempotent: safe to re-run.
--
-- Returns the cleaned brief and a list of errors (empty = the answer is good):
--   1. the text must be JSON;
--   2. exact repeats in the five lists are dropped (the contract's uniqueItems is then met);
--      `wanted` holds {item, role} objects, so a repeat is an identical object;
--   3. the brief must match the contract;
--   4. every number in `stated` must be a number written in the request (R3). Comma decimals
--      read as points. Words for numbers ("twenty") and unit conversions are not recognised,
--      so such a `stated` value fails the check: only numbers the user wrote.

create or replace function app.step1_read_answer(request text, content text, contract json)
returns table (brief jsonb, errors text[])
language plpgsql
as $$
declare
    answer   jsonb;
    list_key text;
    deduped  jsonb;
    written  numeric[];
    stated   record;
    problems text[];
begin
    begin
        answer := content::jsonb;
    exception when others then
        return query select null::jsonb, array['answer is not JSON: ' || sqlerrm];
        return;
    end;

    if jsonb_typeof(answer) = 'object' then
        foreach list_key in array array['hints', 'wanted', 'excluded', 'inventory', 'unknown'] loop
            if jsonb_typeof(answer -> list_key) = 'array' then
                select coalesce(jsonb_agg(item order by first_pos), '[]'::jsonb)
                  into deduped
                  from (select item, min(pos) as first_pos
                          from jsonb_array_elements(answer -> list_key)
                               with ordinality as t(item, pos)
                         group by item) firsts;
                answer := jsonb_set(answer, array[list_key], deduped);
            end if;
        end loop;
    end if;

    problems := coalesce(extensions.jsonschema_validation_errors(contract, answer::json), '{}');

    if jsonb_typeof(answer -> 'stated') = 'object' then
        select coalesce(array_agg(replace(m[1], ',', '.')::numeric), '{}')
          into written
          from regexp_matches(request, '\d+(?:[.,]\d+)?', 'g') as m;
        for stated in
            select key, value from jsonb_each(answer -> 'stated')
             where jsonb_typeof(value) = 'number'
        loop
            if not (stated.value::text::numeric = any (written)) then
                problems := problems || format('stated.%s = %s is not a number in the request',
                                               stated.key, stated.value);
            end if;
        end loop;
    end if;

    return query select answer, problems;
end;
$$;
