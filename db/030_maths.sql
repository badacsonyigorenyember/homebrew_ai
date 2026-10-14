-- Brewing maths (docs/work/s1-maths): one function per formula, source in the comment above it.
-- Per-item functions take plain numbers in SI units. Recipe-level functions take a jsonb array of
-- items. Results are unrounded; rounding is left to display. Bad input raises, it never becomes 0.
-- Needs db/015_app.sql (schema app). Built task by task; later tasks append to this file.
-- Apply as postgres (docs/OPERATIONS.md §4):
--   docker exec -i supabase-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < db/030_maths.sql
-- Idempotent: safe to re-run.

-- Version of the formulas and constants below. Bump it in the same commit as any change to one,
-- and add a line to the version log in docs/work/s1-maths/doc-calc.md.
create or replace function app.calc_version()
returns text
language sql
immutable
as $$ select 'maths-1'::text $$;

-- SG to degrees Plato: °P = 259 - 259 / SG (HTB p. 285; doc-calc section 3).
create or replace function app.sg_to_plato(sg numeric)
returns numeric
language sql
immutable
as $$ select 259 - 259 / sg $$;

-- Degrees Plato to SG: SG = 259 / (259 - °P) (HTB p. 285).
create or replace function app.plato_to_sg(plato numeric)
returns numeric
language sql
immutable
as $$ select 259 / (259 - plato) $$;

-- EBC to SRM: EBC = 1.97 x SRM (HTB p. 469).
create or replace function app.srm_from_ebc(ebc numeric)
returns numeric
language sql
immutable
as $$ select ebc / 1.97 $$;

-- SRM to EBC: EBC = 1.97 x SRM (HTB p. 469).
create or replace function app.ebc_from_srm(srm numeric)
returns numeric
language sql
immutable
as $$ select srm * 1.97 $$;

-- Gravity points (SG - 1) x 1000 from one fermentable: kg x extract/100 x 384 PKL x efficiency/100
-- / litres. 384 PKL = 46 PPG, the sucrose reference (HTB p. 52-53, p. 280, p. 290). Palmer applies
-- no moisture correction, so extract_pct is used as stored (doc-calc section 1, R2).
create or replace function app.gravity_points(kg numeric, extract_pct numeric,
                                              efficiency_pct numeric, volume_l numeric)
returns numeric
language plpgsql
immutable
as $$
begin
    if kg is null or extract_pct is null or efficiency_pct is null or volume_l is null then
        raise exception 'gravity_points: every input is required';
    end if;
    if volume_l <= 0 then
        raise exception 'gravity_points: volume must be above 0, got %', volume_l;
    end if;
    return kg * extract_pct / 100 * 384 * efficiency_pct / 100 / volume_l;
end;
$$;

-- Original gravity from a grist: items {kg, extract_pct, mashed}. Efficiency applies only to
-- mashed items; extract and sugar go in at full yield (HTB p. 53, p. 78; OBC p. 2).
create or replace function app.og(grist jsonb, efficiency_pct numeric, volume_l numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    points numeric := 0;
    g jsonb;
begin
    if jsonb_typeof(grist) is distinct from 'array' then
        raise exception 'og: grist must be a JSON array, got %', grist;
    end if;
    if volume_l is null or volume_l <= 0 then
        raise exception 'og: volume must be above 0, got %', volume_l;
    end if;
    for g in select * from jsonb_array_elements(grist) loop
        if g->>'kg' is null or g->>'extract_pct' is null or g->>'mashed' is null then
            raise exception 'og: each item needs kg, extract_pct and mashed, got %', g;
        end if;
        points := points + app.gravity_points(
            (g->>'kg')::numeric,
            (g->>'extract_pct')::numeric,
            case when (g->>'mashed')::boolean then efficiency_pct else 100 end,
            volume_l);
    end loop;
    return 1 + points / 1000;
end;
$$;

-- Pre-boil volume: batch + losses + boil-off rate x boil time (mass balance, no book example;
-- doc-calc section 2).
create or replace function app.preboil_volume(batch_l numeric, boil_min numeric,
                                              boil_off_l_h numeric, losses_l numeric)
returns numeric
language plpgsql
immutable
as $$
begin
    if batch_l is null or batch_l <= 0 then
        raise exception 'preboil_volume: batch volume must be above 0, got %', batch_l;
    end if;
    if boil_min is null or boil_off_l_h is null or losses_l is null
       or boil_min < 0 or boil_off_l_h < 0 or losses_l < 0 then
        raise exception 'preboil_volume: boil time, boil-off and losses must be 0 or more';
    end if;
    return batch_l + losses_l + boil_off_l_h * boil_min / 60;
end;
$$;

-- Boil gravity: OG points x post-boil volume / pre-boil volume (HTB p. 291). The caller passes the
-- volume at the end of the boil (batch + kettle and fermenter losses), not the batch volume.
-- The old signature is dropped because CREATE OR REPLACE cannot rename an argument.
drop function if exists app.boil_gravity(numeric, numeric, numeric);
create function app.boil_gravity(og numeric, postboil_l numeric, preboil_l numeric)
returns numeric
language plpgsql
immutable
as $$
begin
    if postboil_l is null or postboil_l <= 0 or preboil_l is null or preboil_l <= 0 then
        raise exception 'boil_gravity: volumes must be above 0, got % and %', postboil_l, preboil_l;
    end if;
    return 1 + (og - 1) * postboil_l / preboil_l;
end;
$$;

-- Final gravity from a grist: items {kg, extract_pct, mashed, fermentability}. Apparent
-- attenuation = (OG - FG) / (OG - 1) (HTB p. 108), so a normal item leaves (1 - attenuation) of
-- its gravity points in the beer. Sugars ferment 100 %, lactose not at all (HTB table 24.1,
-- p. 436): 'full' leaves 0 points, 'none' keeps all of them, 'normal' follows attenuation_pct.
-- Table 4.3 (p. 55): FG = 1 + 0.25 x (OG - 1) at 75 % (doc-calc section 4).
create or replace function app.fg(grist jsonb, efficiency_pct numeric, volume_l numeric,
                                  attenuation_pct numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    points numeric := 0;
    item_points numeric;
    g jsonb;
begin
    if jsonb_typeof(grist) is distinct from 'array' then
        raise exception 'fg: grist must be a JSON array, got %', grist;
    end if;
    if volume_l is null or volume_l <= 0 then
        raise exception 'fg: volume must be above 0, got %', volume_l;
    end if;
    if attenuation_pct is null or attenuation_pct < 0 or attenuation_pct > 100 then
        raise exception 'fg: attenuation must be between 0 and 100, got %', attenuation_pct;
    end if;
    for g in select * from jsonb_array_elements(grist) loop
        if g->>'kg' is null or g->>'extract_pct' is null or g->>'mashed' is null
           or g->>'fermentability' is null then
            raise exception 'fg: each item needs kg, extract_pct, mashed and fermentability, got %', g;
        end if;
        item_points := app.gravity_points(
            (g->>'kg')::numeric,
            (g->>'extract_pct')::numeric,
            case when (g->>'mashed')::boolean then efficiency_pct else 100 end,
            volume_l);
        points := points + case g->>'fermentability'
            when 'full'   then 0
            when 'none'   then item_points
            when 'normal' then item_points * (1 - attenuation_pct / 100)
            else null
        end;
        if g->>'fermentability' not in ('full', 'none', 'normal') then
            raise exception 'fg: unknown fermentability %, use full, normal or none',
                g->>'fermentability';
        end if;
    end loop;
    return 1 + points / 1000;
end;
$$;

-- Alcohol by volume, % v/v, from OG and FG. HTB table 9.1 (p. 150) is "based on the work of
-- Balling" and prints no formula. This is the Balling form published in BYO (Bill Pierce,
-- "Calculating Alcohol", https://byo.com/articles/calculating-alcohol/), with HTB's own SG to
-- degrees Plato: RE = 0.1886 OE + 0.8114 AE, ABW = (OE - RE) / (2.0665 - 0.010665 OE),
-- ABV = 1.259 ABW. It matches all 140 cells of table 9.1 within 0.1 (doc-calc section 5).
create or replace function app.abv(og numeric, fg numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    oe numeric;
    ae numeric;
    re numeric;
    abw numeric;
begin
    if og is null or fg is null or og <= 0 or fg <= 0 then
        raise exception 'abv: OG and FG must be above 0, got % and %', og, fg;
    end if;
    oe := app.sg_to_plato(og);
    ae := app.sg_to_plato(fg);
    re := 0.1886 * oe + 0.8114 * ae;
    abw := (oe - re) / (2.0665 - 0.010665 * oe);
    return 1.259 * abw;
end;
$$;

-- Tinseth utilisation (HTB p. 80): U = f(G) x f(t), f(G) = 1.65 x 0.000125^(Gb - 1) and
-- f(t) = (1 - e^(-0.04 t)) / 4.15, t in minutes. Gb is the pre-boil gravity (HTB p. 78).
-- Reproduces all 160 cells of table 5.5 (p. 81) within 0.0005 (doc-calc section 6).
create or replace function app.tinseth_utilisation(boil_sg numeric, minutes numeric)
returns numeric
language plpgsql
immutable
as $$
begin
    if boil_sg is null or boil_sg < 1 then
        raise exception 'tinseth_utilisation: boil gravity must be 1 or more, got %', boil_sg;
    end if;
    if minutes is null or minutes < 0 then
        raise exception 'tinseth_utilisation: minutes must be 0 or more, got %', minutes;
    end if;
    return 1.65 * power(0.000125, boil_sg - 1) * (1 - exp(-0.04 * minutes)) / 4.15;
end;
$$;

-- IBU (mg/L) from one hop addition: grams x alpha% / 100 x U x 1000 / final litres (HTB p. 77-78).
-- Only 'boil' additions count (Tinseth).
-- Whirlpool and dry hop count as 0 IBU for now: the book gives no figure for either, and a cited
-- model for them is a late-game follow-up (docs/RECIPE-ROADMAP.md section 8, Later).
-- Any other usage raises.
create or replace function app.ibu_addition(grams numeric, alpha_pct numeric, minutes numeric,
                                            usage text, boil_sg numeric, volume_l numeric)
returns numeric
language plpgsql
immutable
as $$
begin
    if grams is null or alpha_pct is null or minutes is null or usage is null then
        raise exception 'ibu_addition: grams, alpha_pct, minutes and usage are required';
    end if;
    if volume_l is null or volume_l <= 0 then
        raise exception 'ibu_addition: volume must be above 0, got %', volume_l;
    end if;
    if usage in ('whirlpool', 'dry_hop') then
        return 0;
    elsif usage = 'boil' then
        return grams * alpha_pct / 100 * app.tinseth_utilisation(boil_sg, minutes) * 1000 / volume_l;
    end if;
    raise exception 'ibu_addition: unknown hop usage %, use boil, whirlpool or dry_hop', usage;
end;
$$;

-- IBU of a hop schedule: items {g, alpha_pct, minutes, usage}. An empty array gives 0.
create or replace function app.ibu(hops jsonb, boil_sg numeric, volume_l numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    total numeric := 0;
    h jsonb;
begin
    if jsonb_typeof(hops) is distinct from 'array' then
        raise exception 'ibu: hops must be a JSON array, got %', hops;
    end if;
    for h in select * from jsonb_array_elements(hops) loop
        if h->>'g' is null or h->>'alpha_pct' is null or h->>'minutes' is null or h->>'usage' is null then
            raise exception 'ibu: each item needs g, alpha_pct, minutes and usage, got %', h;
        end if;
        total := total + app.ibu_addition(
            (h->>'g')::numeric, (h->>'alpha_pct')::numeric, (h->>'minutes')::numeric,
            h->>'usage', boil_sg, volume_l);
    end loop;
    return total;
end;
$$;

-- Malt colour units of one fermentable: MCU = °L x lb / gal (HTB p. 469, p. 472). Malt °L is used
-- as SRM-equivalent (HTB p. 468), so the input is EBC and °L = EBC / 1.97 (doc-calc section 7).
create or replace function app.mcu(kg numeric, ebc numeric, volume_l numeric)
returns numeric
language plpgsql
immutable
as $$
begin
    if kg is null or ebc is null or volume_l is null then
        raise exception 'mcu: every input is required';
    end if;
    if volume_l <= 0 then
        raise exception 'mcu: volume must be above 0, got %', volume_l;
    end if;
    return (ebc / 1.97) * (kg / 0.45359237) / (volume_l / 3.785411784);
end;
$$;

-- MCU of a grist: items {kg, ebc}. An empty array gives 0.
create or replace function app.grist_mcu(grist jsonb, volume_l numeric)
returns numeric
language plpgsql
immutable
as $$
declare
    total numeric := 0;
    g jsonb;
begin
    if jsonb_typeof(grist) is distinct from 'array' then
        raise exception 'grist_mcu: grist must be a JSON array, got %', grist;
    end if;
    for g in select * from jsonb_array_elements(grist) loop
        if g->>'kg' is null or g->>'ebc' is null then
            raise exception 'grist_mcu: each item needs kg and ebc, got %', g;
        end if;
        total := total + app.mcu((g->>'kg')::numeric, (g->>'ebc')::numeric, volume_l);
    end loop;
    return total;
end;
$$;

-- SRM from MCU, Morey: SRM = 1.49 x MCU^0.69 (HTB table B.3, p. 470; Palmer's printed constants).
-- 0 MCU gives 0 SRM.
create or replace function app.srm(mcu numeric)
returns numeric
language plpgsql
immutable
as $$
begin
    if mcu is null or mcu < 0 then
        raise exception 'srm: MCU must be 0 or more, got %', mcu;
    end if;
    return 1.49 * power(mcu, 0.69);
end;
$$;

-- Grist solver: items {pct, extract_pct, mashed} in, the same items plus kg out. pct is a share of
-- mass and is normalised by its sum. OG is linear in mass, so it is closed form (no iteration):
-- with a_i = pct_i / sum(pct), kg_i = a_i x M, and M = target points x litres
-- / sum(a_i x extract_i/100 x 384 x eff_i/100), where eff_i is the efficiency for mashed items
-- and 100 otherwise. It inverts app.og (doc-calc section 1).
create or replace function app.solve_grist(target_og numeric, grist jsonb,
                                           efficiency_pct numeric, volume_l numeric)
returns jsonb
language plpgsql
immutable
as $$
declare
    total_pct numeric := 0;
    yield_per_kg numeric := 0;
    total_kg numeric;
    g jsonb;
    result jsonb := '[]'::jsonb;
begin
    if jsonb_typeof(grist) is distinct from 'array' then
        raise exception 'solve_grist: grist must be a JSON array, got %', grist;
    end if;
    if volume_l is null or volume_l <= 0 then
        raise exception 'solve_grist: volume must be above 0, got %', volume_l;
    end if;
    if target_og is null or target_og < 1 then
        raise exception 'solve_grist: target OG must be 1 or more, got %', target_og;
    end if;
    if efficiency_pct is null or efficiency_pct <= 0 then
        raise exception 'solve_grist: efficiency must be above 0, got %', efficiency_pct;
    end if;
    for g in select * from jsonb_array_elements(grist) loop
        if g->>'pct' is null or g->>'extract_pct' is null or g->>'mashed' is null then
            raise exception 'solve_grist: each item needs pct, extract_pct and mashed, got %', g;
        end if;
        total_pct := total_pct + (g->>'pct')::numeric;
    end loop;
    if total_pct <= 0 then
        raise exception 'solve_grist: the grist percentages must add up to more than 0';
    end if;
    for g in select * from jsonb_array_elements(grist) loop
        yield_per_kg := yield_per_kg + (g->>'pct')::numeric / total_pct
            * (g->>'extract_pct')::numeric / 100 * 384
            * case when (g->>'mashed')::boolean then efficiency_pct else 100 end / 100;
    end loop;
    if yield_per_kg <= 0 then
        raise exception 'solve_grist: the grist has no extract';
    end if;
    total_kg := (target_og - 1) * 1000 * volume_l / yield_per_kg;
    for g in select * from jsonb_array_elements(grist) loop
        result := result || (g || jsonb_build_object(
            'kg', (g->>'pct')::numeric / total_pct * total_kg));
    end loop;
    return result;
end;
$$;

-- Hop solver: items {share_pct, alpha_pct, minutes, usage} in, the same items plus g out.
-- share_pct is a share of hop mass among the items passed in (whirlpool and dry-hop items get
-- their mass and add 0 IBU), normalised by its sum. IBU is linear in mass, so it is closed form:
-- with a_i = share_i / sum(share), g_i = a_i x M, and M = target x litres
-- / (1000 x sum(a_i x alpha_i/100 x U_i)), using the same terms as app.ibu_addition.
-- A target of 0 gives 0 g everywhere. A positive target with no boil addition raises.
create or replace function app.solve_hops(target_ibu numeric, hops jsonb,
                                          boil_sg numeric, volume_l numeric)
returns jsonb
language plpgsql
immutable
as $$
declare
    total_share numeric := 0;
    ibu_per_g numeric := 0;
    total_g numeric;
    h jsonb;
    result jsonb := '[]'::jsonb;
begin
    if jsonb_typeof(hops) is distinct from 'array' then
        raise exception 'solve_hops: hops must be a JSON array, got %', hops;
    end if;
    if volume_l is null or volume_l <= 0 then
        raise exception 'solve_hops: volume must be above 0, got %', volume_l;
    end if;
    if target_ibu is null or target_ibu < 0 then
        raise exception 'solve_hops: target IBU must be 0 or more, got %', target_ibu;
    end if;
    for h in select * from jsonb_array_elements(hops) loop
        if h->>'share_pct' is null or h->>'alpha_pct' is null or h->>'minutes' is null
           or h->>'usage' is null then
            raise exception 'solve_hops: each item needs share_pct, alpha_pct, minutes and usage, got %', h;
        end if;
        total_share := total_share + (h->>'share_pct')::numeric;
    end loop;
    if total_share <= 0 then
        raise exception 'solve_hops: the hop shares must add up to more than 0';
    end if;
    for h in select * from jsonb_array_elements(hops) loop
        -- one gram of the whole blend: this item's share of it, times its IBU per gram
        ibu_per_g := ibu_per_g + (h->>'share_pct')::numeric / total_share
            * app.ibu_addition(1, (h->>'alpha_pct')::numeric, (h->>'minutes')::numeric,
                               h->>'usage', boil_sg, volume_l);
    end loop;
    if target_ibu = 0 then
        total_g := 0;
    elsif ibu_per_g <= 0 then
        raise exception 'solve_hops: a target of % IBU needs a boil addition with a boil time and alpha acid above 0', target_ibu;
    else
        total_g := target_ibu / ibu_per_g;
    end if;
    for h in select * from jsonb_array_elements(hops) loop
        result := result || (h || jsonb_build_object(
            'g', (h->>'share_pct')::numeric / total_share * total_g));
    end loop;
    return result;
end;
$$;
