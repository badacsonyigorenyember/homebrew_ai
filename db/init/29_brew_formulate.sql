-- =============================================================================
-- 29_brew_formulate.sql  ·  Recipe arithmetic, and the one write surface for it
--
-- The numbers in a recipe are computed HERE, in SQL, never by the model. A 12B
-- does not do gravity maths reliably, and section 7.4 of the architecture is
-- explicit: any number that must be correct is SQL's job. The model chooses
-- ingredients and quantities; this file turns them into OG/FG/ABV/IBU/SRM.
--
-- Units: metric in, metric out. The published constants (PPG, degrees Lovibond)
-- are imperial by definition, so the conversions are done once, here, and named.
--
-- Runs AFTER 27/28 (needs brew.ingredients populated). Idempotent.
-- =============================================================================

-- Litres -> US gallons, kilograms -> pounds. Named so the formulae below read.
CREATE OR REPLACE FUNCTION brew.f_l_to_gal(l numeric) RETURNS numeric
LANGUAGE sql IMMUTABLE SET search_path = brew, public AS $fn$
  SELECT l * 0.2641720524
$fn$;

CREATE OR REPLACE FUNCTION brew.f_kg_to_lb(kg numeric) RETURNS numeric
LANGUAGE sql IMMUTABLE SET search_path = brew, public AS $fn$
  SELECT kg * 2.2046226218
$fn$;

-- ---------------------------------------------------------------------------
-- brew.f_compute_recipe
--
-- p_items: jsonb array of {ingredient_id, stage, qty_g, timing_min}. qty_g is
-- grams for every ingredient -- one unit, so the caller cannot mix kg and g.
--
-- Returns every figure plus the inputs it used, so a wrong number can always be
-- traced to the row that caused it rather than re-derived by hand.
--
-- SECURITY DEFINER because it JOINs brew.ingredients and the caller holds no
-- SELECT there. It reads the catalogue only -- the same rows f_catalogue already
-- exposes -- never batches, inventory or measurements.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION brew.f_compute_recipe(
  p_batch_size_l   numeric,
  p_items          jsonb,
  p_efficiency     numeric DEFAULT 0.72,   -- brewhouse efficiency, mashed grain only
  p_attenuation    numeric DEFAULT 0.75,   -- apparent attenuation of the chosen yeast
  p_boil_volume_l  numeric DEFAULT NULL    -- defaults to batch size; pre-boil if given
) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = brew, public AS $fn$
DECLARE
  v_gal        numeric := brew.f_l_to_gal(p_batch_size_l);
  v_boil_l     numeric := coalesce(p_boil_volume_l, p_batch_size_l);
  v_ferm_pts   numeric := 0;   -- gravity points that yeast can eat
  v_unferm_pts numeric := 0;   -- gravity points that survive into FG
  v_mcu        numeric := 0;
  v_og         numeric;
  v_fg         numeric;
  v_ibu        numeric := 0;
  v_srm        numeric;
  v_bigness    numeric;
  v_og_boil    numeric;
  r            record;
BEGIN
  IF p_batch_size_l IS NULL OR p_batch_size_l <= 0 THEN
    RAISE EXCEPTION 'batch size must be positive, got %', p_batch_size_l;
  END IF;

  -- Pass 1: gravity and colour from fermentables and sugars -------------------
  FOR r IN
    SELECT i.kind, i.potential_ppg, i.color_lovibond, i.attrs,
           (it->>'qty_g')::numeric AS qty_g
    FROM jsonb_array_elements(p_items) it
    JOIN brew.ingredients i ON i.id = (it->>'ingredient_id')::bigint
    WHERE i.kind IN ('fermentable','adjunct')
  LOOP
    CONTINUE WHEN r.potential_ppg IS NULL OR r.qty_g IS NULL;

    DECLARE
      v_lb    numeric := brew.f_kg_to_lb(r.qty_g / 1000.0);
      -- Sugars dissolve completely; only mashed grain is subject to brewhouse
      -- efficiency. Treating lactose as 72% efficient would understate OG.
      v_eff   numeric := CASE WHEN r.kind = 'adjunct' THEN 1.0 ELSE p_efficiency END;
      v_pts   numeric;
      v_canferm boolean := coalesce((r.attrs->>'fermentable')::boolean, true);
    BEGIN
      v_pts := v_lb * r.potential_ppg * v_eff / v_gal;
      IF v_canferm THEN
        v_ferm_pts := v_ferm_pts + v_pts;
      ELSE
        v_unferm_pts := v_unferm_pts + v_pts;
      END IF;

      IF r.color_lovibond IS NOT NULL THEN
        v_mcu := v_mcu + (v_lb * r.color_lovibond / v_gal);
      END IF;
    END;
  END LOOP;

  v_og := 1 + (v_ferm_pts + v_unferm_pts) / 1000.0;
  -- Attenuation acts only on what the yeast can reach; unfermentable points
  -- carry straight through. This is why a lactose stout finishes high.
  v_fg := 1 + (v_ferm_pts * (1 - p_attenuation) + v_unferm_pts) / 1000.0;

  -- Pass 2: bitterness, Tinseth -----------------------------------------------
  -- Utilisation falls as wort gravity rises, so it is computed against the BOIL
  -- gravity, not the packaged OG.
  v_og_boil := 1 + ((v_og - 1) * p_batch_size_l / v_boil_l);
  v_bigness := 1.65 * power(0.000125, v_og_boil - 1);

  FOR r IN
    SELECT i.alpha_acid_pct,
           (it->>'qty_g')::numeric      AS qty_g,
           (it->>'timing_min')::numeric AS timing_min,
           it->>'stage'                 AS stage
    FROM jsonb_array_elements(p_items) it
    JOIN brew.ingredients i ON i.id = (it->>'ingredient_id')::bigint
    WHERE i.kind = 'hop'
  LOOP
    CONTINUE WHEN r.alpha_acid_pct IS NULL OR r.qty_g IS NULL;
    -- Dry hops and packaging additions contribute no measurable IBU.
    CONTINUE WHEN r.stage IN ('dryhop','fermenter','packaging');

    DECLARE
      v_t   numeric := coalesce(r.timing_min, 0);
      v_btf numeric := (1 - exp(-0.04 * v_t)) / 4.15;
    BEGIN
      v_ibu := v_ibu + (r.qty_g * v_bigness * v_btf * (r.alpha_acid_pct / 100.0) * 1000.0)
                       / p_batch_size_l;
    END;
  END LOOP;

  -- Morey. Beyond roughly SRM 50 every model is extrapolation, not measurement.
  v_srm := CASE WHEN v_mcu > 0 THEN 1.4922 * power(v_mcu, 0.6859) ELSE 0 END;

  RETURN jsonb_build_object(
    'batch_size_l',   p_batch_size_l,
    'og',             round(v_og, 3),
    'fg',             round(v_fg, 3),
    'abv_pct',        round(brew.f_abv(round(v_og,3), round(v_fg,3)), 1),
    'ibu',            round(v_ibu)::int,
    'srm',            round(v_srm, 1),
    'ebc',            round(v_srm * 1.97, 1),
    'inputs', jsonb_build_object(
      'efficiency',            p_efficiency,
      'attenuation',           p_attenuation,
      'boil_volume_l',         v_boil_l,
      'fermentable_points',    round(v_ferm_pts, 2),
      'unfermentable_points',  round(v_unferm_pts, 2),
      'mcu',                   round(v_mcu, 2),
      'tinseth_bigness',       round(v_bigness, 4)));
END;
$fn$;

COMMENT ON FUNCTION brew.f_compute_recipe(numeric, jsonb, numeric, numeric, numeric) IS
  'Deterministic recipe arithmetic: OG/FG/ABV/IBU/SRM from ingredient rows. '
  'Gravity uses potential_ppg, bitterness uses Tinseth against boil gravity, '
  'colour uses Morey. Returns the intermediate inputs alongside the results so '
  'a surprising figure can be traced rather than re-derived.';

-- ---------------------------------------------------------------------------
-- brew.f_save_recipe  ·  the ONLY write surface for recipes
--
-- SECURITY DEFINER so the calling role needs no table grants -- the same
-- contract as mem.f_save_memory (section 8.4). The caller can create a recipe
-- and cannot read this brewer's batches, inventory or measurements, which is
-- the property 50_roles.sql exists to preserve.
--
-- Re-saving a name creates a new VERSION rather than overwriting: recipes are
-- iterated on, and the row a batch was brewed from must not change under it.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION brew.f_save_recipe(
  p_name           text,
  p_batch_size_l   numeric,
  p_items          jsonb,
  p_style_id       bigint  DEFAULT NULL,
  p_efficiency     numeric DEFAULT 0.72,
  p_attenuation    numeric DEFAULT 0.75,
  p_boil_volume_l  numeric DEFAULT NULL,
  p_mash_profile   jsonb   DEFAULT NULL,
  p_notes          text    DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = brew, public AS $fn$
DECLARE
  v_calc    jsonb;
  v_version int;
  v_parent  bigint;
  v_id      bigint;
  v_items   int := 0;
  it        jsonb;
BEGIN
  IF coalesce(trim(p_name), '') = '' THEN
    RAISE EXCEPTION 'recipe name is required';
  END IF;
  IF jsonb_typeof(p_items) <> 'array' OR jsonb_array_length(p_items) = 0 THEN
    RAISE EXCEPTION 'recipe % has no items', p_name;
  END IF;

  -- Fail before inserting anything if an item names an ingredient that is not
  -- in the catalogue: a recipe referencing a malt nobody stocks is not a recipe.
  PERFORM 1 FROM jsonb_array_elements(p_items) x
   WHERE NOT EXISTS (SELECT 1 FROM brew.ingredients i
                     WHERE i.id = (x->>'ingredient_id')::bigint);
  IF FOUND THEN
    RAISE EXCEPTION 'recipe % references an ingredient_id not in brew.ingredients', p_name;
  END IF;

  v_calc := brew.f_compute_recipe(p_batch_size_l, p_items, p_efficiency,
                                  p_attenuation, p_boil_volume_l);

  SELECT max(version), max(id) INTO v_version, v_parent
  FROM brew.recipes WHERE name = p_name;
  v_version := coalesce(v_version, 0) + 1;

  INSERT INTO brew.recipes (name, version, parent_recipe_id, style_id, batch_size_l,
                            target_og, target_fg, target_ibu, target_srm,
                            mash_profile, notes)
  VALUES (p_name, v_version, v_parent, p_style_id, p_batch_size_l,
          (v_calc->>'og')::numeric, (v_calc->>'fg')::numeric,
          (v_calc->>'ibu')::int,    (v_calc->>'srm')::numeric,
          p_mash_profile, p_notes)
  RETURNING id INTO v_id;

  FOR it IN SELECT * FROM jsonb_array_elements(p_items) LOOP
    INSERT INTO brew.recipe_items (recipe_id, ingredient_id, stage, qty, unit,
                                   timing_min, notes)
    VALUES (v_id,
            (it->>'ingredient_id')::bigint,
            coalesce(it->>'stage', 'mash'),
            (it->>'qty_g')::numeric,
            'g',
            (it->>'timing_min')::int,
            it->>'notes');
    v_items := v_items + 1;
  END LOOP;

  RETURN jsonb_build_object('recipe_id', v_id, 'name', p_name, 'version', v_version,
                            'parent_recipe_id', v_parent, 'items', v_items,
                            'computed', v_calc);
END;
$fn$;

COMMENT ON FUNCTION brew.f_save_recipe(text, numeric, jsonb, bigint, numeric, numeric, numeric, jsonb, text) IS
  'The only write surface for brew.recipes / brew.recipe_items. SECURITY DEFINER '
  'so the caller needs no table grants and still cannot read the brewer''s '
  'batches. Targets are computed by brew.f_compute_recipe, never supplied by the '
  'caller. Re-saving a name creates a new version linked to the previous one.';

-- The n8n write credential already exists as mem_writer (obs.* logging uses it).
-- EXECUTE here does NOT widen its read surface: SECURITY DEFINER means it still
-- holds no SELECT on any brew table. A dedicated brew_writer role would be
-- tidier naming, but would need a new password and n8n credential; the security
-- property is identical either way.
GRANT EXECUTE ON FUNCTION brew.f_save_recipe(text, numeric, jsonb, bigint, numeric, numeric, numeric, jsonb, text) TO mem_writer;
GRANT USAGE ON SCHEMA brew TO mem_writer;

-- ---------------------------------------------------------------------------
-- brew.f_catalogue is defined once, further down -- see "v2, now returns a
-- ROLE". A superseded 7-column definition used to sit here, and because it ran
-- BEFORE the 8-column one it made this whole file non-idempotent: on a fresh
-- database it was harmlessly replaced, but on any restart the 8-column function
-- already existed and CREATE OR REPLACE failed with "cannot change return type
-- of existing function". db-init runs with ON_ERROR_STOP=1 and this hardcoded
-- file list, so that error halted the run HERE and silently skipped every
-- later file -- 62_obs_recipe_prompts.sql and 63_model_switch.sql included.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- brew.f_fit_recipe  ·  hit the target gravity without asking the model to
--
-- The model chooses ingredients and their PROPORTIONS; this scales the mashed
-- grain so the batch actually lands on p_target_og. Sugars and adjuncts are NOT
-- scaled -- 400 g of lactose is a flavour decision, and silently doubling it to
-- reach a gravity would change the beer the brewer asked for.
--
-- Returns the scaled items and the recomputed figures together, so the caller
-- persists exactly what was computed.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION brew.f_fit_recipe(
  p_batch_size_l  numeric,
  p_items         jsonb,
  p_target_og     numeric,
  p_efficiency    numeric DEFAULT 0.72,
  p_attenuation   numeric DEFAULT 0.75,
  p_boil_volume_l numeric DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = brew, public AS $fn$
DECLARE
  v_first   jsonb;
  v_ferm    numeric;
  v_unferm  numeric;
  v_needed  numeric;
  v_factor  numeric;
  v_scaled  jsonb;
BEGIN
  v_first  := brew.f_compute_recipe(p_batch_size_l, p_items, p_efficiency,
                                    p_attenuation, p_boil_volume_l);
  IF p_target_og IS NULL THEN
    RETURN jsonb_build_object('items', p_items, 'scale_factor', 1,
                              'computed', v_first);
  END IF;

  v_ferm   := (v_first->'inputs'->>'fermentable_points')::numeric;
  v_unferm := (v_first->'inputs'->>'unfermentable_points')::numeric;
  v_needed := (p_target_og - 1) * 1000 - v_unferm;

  IF v_ferm <= 0 OR v_needed <= 0 THEN
    -- Adjuncts alone already meet or exceed the target: scaling grain cannot
    -- help, so return the honest figures rather than a negative grist.
    RETURN jsonb_build_object('items', p_items, 'scale_factor', 1,
                              'computed', v_first,
                              'warning', 'target unreachable by scaling grain');
  END IF;

  v_factor := round(v_needed / v_ferm, 4);

  SELECT jsonb_agg(
           CASE WHEN i.kind = 'fermentable'
                THEN it || jsonb_build_object('qty_g', round((it->>'qty_g')::numeric * v_factor))
                ELSE it END
           ORDER BY ord)
  INTO v_scaled
  FROM jsonb_array_elements(p_items) WITH ORDINALITY AS t(it, ord)
  JOIN brew.ingredients i ON i.id = (t.it->>'ingredient_id')::bigint;

  RETURN jsonb_build_object(
    'items', v_scaled,
    'scale_factor', v_factor,
    'computed', brew.f_compute_recipe(p_batch_size_l, v_scaled, p_efficiency,
                                      p_attenuation, p_boil_volume_l));
END;
$fn$;

GRANT EXECUTE ON FUNCTION brew.f_catalogue(text) TO mem_writer;
GRANT EXECUTE ON FUNCTION brew.f_fit_recipe(numeric, jsonb, numeric, numeric, numeric, numeric) TO mem_writer;
GRANT EXECUTE ON FUNCTION brew.f_compute_recipe(numeric, jsonb, numeric, numeric, numeric) TO mem_writer;

-- ---------------------------------------------------------------------------
-- brew.f_fit_to_abv  ·  scale the grist to land on a target ABV
--
-- f_fit_recipe targets an OG, but a brewer asks for a strength. brew.f_abv uses
-- the high-gravity formula, which does not inverse cleanly, and the lactose in a
-- pastry stout shifts the OG->ABV relationship further. So solve it numerically:
-- bisect on target OG until the computed ABV converges. Twenty iterations is
-- exact to well under 0.1%, and costs nothing next to one LLM call.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION brew.f_fit_to_abv(
  p_batch_size_l  numeric,
  p_items         jsonb,
  p_target_abv    numeric,
  p_efficiency    numeric DEFAULT 0.72,
  p_attenuation   numeric DEFAULT 0.75,
  p_boil_volume_l numeric DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = brew, public AS $fn$
DECLARE
  v_lo  numeric := 1.020;
  v_hi  numeric := 1.180;
  v_mid numeric;
  v_res jsonb;
  v_abv numeric;
  i     int;
BEGIN
  IF p_target_abv IS NULL OR p_target_abv <= 0 THEN
    RETURN brew.f_fit_recipe(p_batch_size_l, p_items, NULL, p_efficiency,
                             p_attenuation, p_boil_volume_l);
  END IF;

  FOR i IN 1..20 LOOP
    v_mid := (v_lo + v_hi) / 2;
    v_res := brew.f_fit_recipe(p_batch_size_l, p_items, v_mid, p_efficiency,
                               p_attenuation, p_boil_volume_l);
    v_abv := (v_res->'computed'->>'abv_pct')::numeric;
    IF v_abv < p_target_abv THEN v_lo := v_mid; ELSE v_hi := v_mid; END IF;
  END LOOP;

  -- The loop keeps v_lo below the target and v_hi at or above it. abv_pct is
  -- reported to one decimal, so bisecting a rounded value leaves the final v_mid
  -- on either side; answer from v_hi, the bound that is known to satisfy it.
  v_res := brew.f_fit_recipe(p_batch_size_l, p_items, v_hi, p_efficiency,
                             p_attenuation, p_boil_volume_l);

  RETURN v_res || jsonb_build_object('target_abv_pct', p_target_abv,
                                     'solved_target_og', round(v_hi, 3));
END;
$fn$;

GRANT EXECUTE ON FUNCTION brew.f_fit_to_abv(numeric, jsonb, numeric, numeric, numeric, numeric) TO mem_writer;

-- ---------------------------------------------------------------------------
-- brew.f_catalogue, v2 — now returns a ROLE.
--
-- ⛔ Why this exists. The model was asked to pick dark malts by reading the
-- lovibond column and instead read the NAME: it put Weyermann "Floor-Malted
-- Bohemian DARK Malt" -- 6.5 degrees Lovibond, barely darker than pale ale malt
-- -- in the roast slot of a stout, and the beer came out at EBC 44 (measured,
-- run 62). Every number downstream was correct; the classification was not.
--
-- So classification stops being a judgement call. The role is derived here, in
-- SQL, from the published colour, and the prompt selects from named buckets. A
-- malt cannot land in 'roast' because of what it is called.
--
--   base    < 10 L   pale and lightly kilned; Munich and Vienna live here too
--   caramel 10-199   crystal and caramel
--   roast   >= 200   chocolate, black, CARAFA, roasted barley
--               ...  OR named for a roasted family AND at least 100 L
--
-- The 200 boundary is not arbitrary: in this catalogue nothing sits between
-- 151.2 and 207.8, so the gap is where the corpus itself separates them.
--
-- ⛔ But colour alone got one row wrong, and a model found it. Viking "Chocolate
-- Light Malt" is 150.5 L -- 296 EBC -- and colour alone files it under the
-- header "CARAMEL & CRYSTAL MALTS (10-199 degL)", which is simply false: it is
-- a roasted malt. qwen3.5:9b used it as one (measured, recipe 13), correctly,
-- and scored 5.1% roast instead of 12.8% because the bucket lied to it.
--
-- So the name IS consulted now -- but only to PROMOTE into 'roast', only for
-- named roasted families, and only above 100 L. That colour floor is what keeps
-- the original bug fixed: "Floor-Malted Bohemian Dark Malt" at 6.5 L cannot
-- reach it, and "dark" is deliberately absent from the pattern. The name can
-- never pull a malt down out of 'roast', and it can never act on its own.
-- ---------------------------------------------------------------------------
DROP FUNCTION IF EXISTS brew.f_catalogue(text);

CREATE OR REPLACE FUNCTION brew.f_catalogue(p_kind text DEFAULT NULL)
RETURNS TABLE (id bigint, kind text, role text, name text, supplier text,
               potential_ppg numeric, color_lovibond numeric, alpha_acid_pct numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = brew, public AS $fn$
  SELECT i.id, i.kind,
         CASE i.kind
           WHEN 'fermentable' THEN
             CASE
               WHEN i.color_lovibond IS NULL     THEN 'base'
               WHEN i.color_lovibond >= 200      THEN 'roast'
               WHEN i.color_lovibond >= 100
                AND i.name ~* '(chocolate|black|roast|carafa|patent)'
                                                 THEN 'roast'
               WHEN i.color_lovibond >= 10       THEN 'caramel'
               ELSE 'base'
             END
           ELSE i.kind
         END AS role,
         i.name, i.supplier, i.potential_ppg, i.color_lovibond, i.alpha_acid_pct
  FROM brew.ingredients i
  WHERE p_kind IS NULL OR i.kind = p_kind
  ORDER BY 3, coalesce(i.color_lovibond, 0), i.name
$fn$;

GRANT EXECUTE ON FUNCTION brew.f_catalogue(text) TO mem_writer;
