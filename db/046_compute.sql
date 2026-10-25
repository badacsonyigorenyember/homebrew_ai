-- Step 10 computing (docs/work/m6-compute-validate, Tasks 3-4): the colour solver (rule 7),
-- the boil time and the amounts and numbers of a recipe. Task 3 adds app.solve_colour; Task 4
-- appends the rest to this file. s1's functions do all the maths, no LLM.
-- Needs db/030_maths.sql (grist_mcu, srm, solve_grist), db/032_formulation_check.sql.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/046_compute.sql
-- Idempotent: safe to re-run.

-- Colour adjustment (rule 7). When the SRM of the proposed grist is more than 1 from the target,
-- the darkest fermentable that is not a crystal malt changes its share, and the base malt with
-- the largest share (the absorber) takes up the difference, so every other share stays as
-- proposed. Grist items {ingredient_id, name, role, pct, extract_pct, mashed, ebc, max_pct};
-- a null ebc counts as 0. Returns {grist (pct changed, kg from app.solve_grist), adjusted,
-- reached (SRM within 1 of the target), srm, darkest, absorber, from_pct, to_pct, because}.
--
-- Closed form. With the shares p_i (percent), e_i = extract_i/100 x 384 x eff_i/100 (eff is the
-- efficiency for mashed items, 100 otherwise) and ebc_i, app.solve_grist gives
-- kg_i = p_i x K / sum(p e) with K = (OG - 1) x 1000 x volume, so
-- MCU = c x N / D, c = (OG - 1) x 1000 x 3.785411784 / (1.97 x 0.45359237),
-- N = sum(p ebc), D = sum(p e): the volume cancels, and both N and D are linear in the darkest's
-- share x, because the absorber's share is S - x (S = their shares together) and nothing else
-- moves. Setting c N(x) = m D(x), with m the MCU of the target SRM (app.srm inverted), gives
-- x = x0 + (m D0 - c N0) / (c dN - m dD), dN and dD the change of N and D per point moved from
-- the absorber to the darkest. x is then clamped so that the darkest stays in (0, its max_pct]
-- and the absorber in (0, its max_pct]; if SRM is still more than 1 away, reached is false.
create or replace function app.solve_colour(target_srm numeric, grist jsonb, target_og numeric,
                                            efficiency_pct numeric, volume_l numeric)
returns jsonb
language plpgsql
immutable
as $$
declare
    tolerance constant numeric := 1;  -- SRM, the brief's tolerance (user decision 2026-10-25)
    least constant numeric := 0.01;   -- the smallest share a fermentable may be left with, in percent
    items jsonb;
    solved jsonb;
    srm_before numeric;
    srm_after numeric;
    d jsonb;
    a jsonb;
    d_idx int;
    a_idx int;
    x0 numeric;
    s numeric;
    x numeric;
    lo numeric;
    hi numeric;
    c numeric;
    m numeric;
    n0 numeric := 0;
    d0 numeric := 0;
    dn numeric;
    dd numeric;
    denom numeric;
    e_d numeric;
    e_a numeric;
    why text;
    result jsonb;
begin
    if jsonb_typeof(grist) is distinct from 'array' or jsonb_array_length(grist) = 0 then
        raise exception 'solve_colour: grist must be a non-empty JSON array, got %', grist;
    end if;
    if target_srm is null or target_srm <= 0 then
        raise exception 'solve_colour: target SRM must be above 0, got %', target_srm;
    end if;

    -- null ebc counts as 0
    select jsonb_agg(g || jsonb_build_object('ebc', coalesce((g->>'ebc')::numeric, 0)) order by ord)
      into items from jsonb_array_elements(grist) with ordinality t(g, ord);
    solved := app.solve_grist(target_og, items, efficiency_pct, volume_l);
    srm_before := app.srm(app.grist_mcu(solved, volume_l));

    -- the darkest non-crystal: highest ebc, then larger share, then lower id
    select (ord - 1)::int into d_idx
      from jsonb_array_elements(items) with ordinality t(g, ord)
     where g->>'role' <> 'crystal'
     order by (g->>'ebc')::numeric desc, (g->>'pct')::numeric desc, (g->>'ingredient_id')::bigint
     limit 1;
    if d_idx is not null then
        d := items -> d_idx;
        -- the absorber: the base malt with the largest share other than the darkest
        select (ord - 1)::int into a_idx
          from jsonb_array_elements(items) with ordinality t(g, ord)
         where g->>'role' = 'base' and (ord - 1)::int <> d_idx
         order by (g->>'pct')::numeric desc, (g->>'ingredient_id')::bigint
         limit 1;
        if a_idx is not null then
            a := items -> a_idx;
        end if;
    end if;

    if abs(srm_before - target_srm) <= tolerance then
        why := format('SRM %s is within %s of the target %s, so the shares stay as proposed',
                      round(srm_before, 1), tolerance, target_srm);
    elsif d is null then
        why := 'every fermentable is a crystal malt, so no share can take the colour change';
    elsif a is null then
        why := format('%s is the darkest fermentable and no other base malt can take up the change',
                      d->>'name');
    elsif (d->>'ebc')::numeric <= (a->>'ebc')::numeric then
        why := format('%s is not darker than %s, so moving shares between them cannot change the colour as needed',
                      d->>'name', a->>'name');
    end if;

    if why is not null then
        return jsonb_build_object(
            'grist', solved, 'adjusted', false,
            'reached', abs(srm_before - target_srm) <= tolerance, 'srm', srm_before,
            'darkest', case when d is null then null
                       else jsonb_build_object('ingredient_id', d->'ingredient_id', 'name', d->'name') end,
            'absorber', case when a is null then null
                        else jsonb_build_object('ingredient_id', a->'ingredient_id', 'name', a->'name') end,
            'from_pct', d->'pct', 'to_pct', d->'pct', 'because', why);
    end if;

    x0 := (d->>'pct')::numeric;
    s := x0 + (a->>'pct')::numeric;
    c := (target_og - 1) * 1000 * 3.785411784 / (1.97 * 0.45359237);
    m := power(target_srm / 1.49, 1 / 0.69);
    e_d := (d->>'extract_pct')::numeric / 100 * 384
           * case when (d->>'mashed')::boolean then efficiency_pct else 100 end / 100;
    e_a := (a->>'extract_pct')::numeric / 100 * 384
           * case when (a->>'mashed')::boolean then efficiency_pct else 100 end / 100;
    select sum((g->>'pct')::numeric * (g->>'ebc')::numeric),
           sum((g->>'pct')::numeric * (g->>'extract_pct')::numeric / 100 * 384
               * case when (g->>'mashed')::boolean then efficiency_pct else 100 end / 100)
      into n0, d0 from jsonb_array_elements(items) g;
    dn := (d->>'ebc')::numeric - (a->>'ebc')::numeric;
    dd := e_d - e_a;
    denom := c * dn - m * dd;
    if denom = 0 then
        x := x0;
    else
        x := x0 + (m * d0 - c * n0) / denom;
    end if;

    lo := greatest(least, s - coalesce((a->>'max_pct')::numeric, 100));
    hi := least(s - least, coalesce((d->>'max_pct')::numeric, 100));
    if lo > hi then
        x := x0;  -- no room to move inside both limits
    else
        x := least(greatest(x, lo), hi);
    end if;

    items := jsonb_set(items, array[d_idx::text, 'pct'], to_jsonb(x));
    items := jsonb_set(items, array[a_idx::text, 'pct'], to_jsonb(s - x));
    solved := app.solve_grist(target_og, items, efficiency_pct, volume_l);
    srm_after := app.srm(app.grist_mcu(solved, volume_l));

    return jsonb_build_object(
        'grist', solved, 'adjusted', x <> x0,
        'reached', abs(srm_after - target_srm) <= tolerance, 'srm', srm_after,
        'darkest', jsonb_build_object('ingredient_id', d->'ingredient_id', 'name', d->'name'),
        'absorber', jsonb_build_object('ingredient_id', a->'ingredient_id', 'name', a->'name'),
        'from_pct', x0, 'to_pct', x,
        'because', format('%s %s %% to %s %%, %s %s %% to %s %%: SRM %s to %s (target %s)%s',
            d->>'name', round(x0, 2), round(x, 2), a->>'name',
            round((a->>'pct')::numeric, 2), round(s - x, 2),
            round(srm_before, 1), round(srm_after, 1), target_srm,
            case when abs(srm_after - target_srm) <= tolerance then ''
                 else ', still more than ' || tolerance || ' away because of the share limits' end));
end;
$$;

comment on function app.solve_colour(numeric, jsonb, numeric, numeric, numeric) is
    'Rule 7 colour adjustment: the darkest non-crystal fermentable changes its share and the largest base malt takes up the difference (closed form, see the file header).';
