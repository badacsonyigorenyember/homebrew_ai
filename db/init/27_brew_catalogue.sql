-- =============================================================================
-- 27_brew_catalogue.sql  ·  Seed brew.ingredients from published reference data
--
-- brew.recipe_items references brew.ingredients, so a recipe can only name an
-- ingredient that exists here. This file fills the catalogue from ref.* -- the
-- published side -- so that every computed number in a recipe traces back to a
-- maltster datasheet or the hop handbook rather than to a model's memory.
--
-- It seeds ONLY what ref.* can support. Sugars and adjuncts with no published
-- row (lactose, maltodextrin, vanilla) are deliberately absent: adding them
-- would mean inventing a potential_ppg, which is the exact failure this
-- architecture exists to prevent. They need a source ingested first.
--
-- Runs AFTER 26_ref_malts.sql. Idempotent: re-running inserts nothing new.
-- attrs carries the provenance back to the ref row.
-- =============================================================================

-- Fermentables ---------------------------------------------------------------
INSERT INTO brew.ingredients (kind, name, supplier, potential_ppg, color_lovibond, attrs)
SELECT 'fermentable', m.name, m.maltster, m.potential_ppg, m.color_lovibond,
       jsonb_build_object('ref_malt_id', m.id,
                          'category', m.category,
                          'extract_dbfg_pct', m.extract_dbfg_pct,
                          'colour_ebc_min', m.colour_ebc_min,
                          'colour_ebc_max', m.colour_ebc_max,
                          'source_doc', m.source_doc)
FROM ref.malts m
WHERE m.potential_ppg IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM brew.ingredients i
                  WHERE i.kind = 'fermentable' AND i.name = m.name
                    AND i.supplier IS NOT DISTINCT FROM m.maltster);

-- Hops -----------------------------------------------------------------------
-- alpha_acid_pct is the midpoint of the published range; the range itself stays
-- in attrs, because a bittering calculation done on a midpoint should be able to
-- show the spread it came from.
INSERT INTO brew.ingredients (kind, name, supplier, alpha_acid_pct, attrs)
SELECT 'hop', h.name, NULL,
       round((h.alpha_min + h.alpha_max) / 2.0, 2),
       jsonb_build_object('ref_hop_id', h.id,
                          'alpha_min', h.alpha_min,
                          'alpha_max', h.alpha_max,
                          'origin', h.origin,
                          'hop_type', h.hop_type,
                          'source_doc', 'Hop Variety Handbook')
FROM ref.hops h
WHERE h.alpha_min IS NOT NULL AND h.alpha_max IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM brew.ingredients i
                  WHERE i.kind = 'hop' AND i.name = h.name);
