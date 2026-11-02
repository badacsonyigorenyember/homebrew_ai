-- Step 16 checks the model's prose (docs/work/m8-recipe-sheet-chat, Task 5). No LLM.
--   app.prose_numbers(t)        the number tokens of a text: digits that touch no letter or digit, and no
--                               "letter-" before them, so 15B, US-05 and S-04 are not tokens
--   app.sheet_read_answer(content, facts, sources, contract)
--                               the answer and its errors (empty = good): JSON, contract, keys, numbers, citations
--   app.sheet_retry_text(errors) the message that lists the failures for the one retry (R7)
-- A number in the prose is good when it equals an allowed number (facts->'allowed_numbers', see
-- app.sheet_allowed_numbers) rounded to the token's decimals: 1.040 for a saved 1.0401, but not 66 for 66.5.
-- Needs: db/055_sheet_facts.sql; pg_jsonschema in schema extensions (db/015_app.sql).
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/056_sheet_check.sql
-- Idempotent: safe to re-run.

create or replace function app.prose_numbers(t text)
returns text[]
language sql
immutable
as $$
    select coalesce(array_agg(m[1] order by ord), '{}'::text[])
    from regexp_matches(coalesce(t, ''), '(?<![[:alnum:]])(?<![A-Za-z]-)([0-9]+(?:\.[0-9]+)?)(?![[:alnum:]])', 'g')
         with ordinality as r(m, ord)
$$;

create or replace function app.sheet_read_answer(content text, facts jsonb, sources jsonb, contract json)
returns table (answer jsonb, errors text[])
language plpgsql
as $$
declare
    ans      jsonb;
    problems text[];
    wanted   text[];
    seen     text[] := '{}';
    allowed  numeric[];
    ids      bigint[];
    cited    boolean := false;
    line     record;
    tok      text;
    cid      bigint;
    decimals integer;
begin
    begin
        ans := content::jsonb;
    exception when others then
        return query select null::jsonb, array['answer is not JSON: ' || sqlerrm];
        return;
    end;

    problems := coalesce(extensions.jsonschema_validation_errors(contract, ans::json), '{}');
    if cardinality(problems) > 0 then
        return query select ans, problems;
        return;
    end if;

    -- keys: exactly one why per listed key
    select array_agg(c->>'key') into wanted from jsonb_array_elements(facts->'choices') c;
    for line in select w->>'key' as key from jsonb_array_elements(ans->'why') w loop
        if line.key = any (seen) then
            problems := array_append(problems, format('why has key %s more than once', line.key));
        elsif not (line.key = any (wanted)) then
            problems := array_append(problems, format('why has key %s, which is not in the list of keys to write', line.key));
        end if;
        seen := seen || line.key;
    end loop;
    select problems || coalesce(array_agg(format('why is missing key %s', k)), '{}')
      into problems from unnest(wanted) k where not (k = any (seen));

    -- numbers and citations, line by line: where = style_description, why[<key>], notes[<n>]
    select coalesce(array_agg(n::numeric), '{}') into allowed from jsonb_array_elements_text(facts->'allowed_numbers') n;
    select coalesce(array_agg((s->>'chunk_id')::bigint), '{}') into ids
      from jsonb_array_elements(coalesce(sources, '[]'::jsonb)) s;
    for line in
        select 'style_description' as place, ans->>'style_description' as text, '[]'::jsonb as cite
        union all
        select format('why[%s]', w->>'key'), w->>'text', w->'cite' from jsonb_array_elements(ans->'why') w
        union all
        select format('notes[%s]', ord - 1), n->>'text', n->'cite'
          from jsonb_array_elements(ans->'notes') with ordinality as t(n, ord)
    loop
        foreach tok in array app.prose_numbers(line.text) loop
            decimals := coalesce(length(split_part(tok, '.', 2)), 0);
            if not exists (select 1 from unnest(allowed) a where round(a, decimals) = tok::numeric) then
                problems := array_append(problems, format('number %s in %s is not a saved value or a style range value', tok, line.place));
            end if;
        end loop;
        for cid in select (x)::bigint from jsonb_array_elements_text(line.cite) x loop
            cited := true;
            if not (cid = any (ids)) then
                problems := array_append(problems, format('chunk %s in %s was not retrieved', cid, line.place));
            end if;
        end loop;
    end loop;
    if not cited then
        problems := array_append(problems, 'the sheet cites no source');
    end if;

    return query select ans, problems;
end;
$$;

create or replace function app.sheet_retry_text(errors text[])
returns text
language sql
immutable
as $$
    select E'Your answer failed these checks:\n'
        || (select string_agg('- ' || e, E'\n') from unnest(errors) e)
        || E'\nAnswer again with the same JSON fields. Fix every point above: use only numbers shown in the user message, cite only listed source ids (at least one in the sheet), and write exactly one "why" for each listed key.'
$$;
