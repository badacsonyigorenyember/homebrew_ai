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
FROM ref.fermentables m
WHERE m.potential_ppg IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM brew.ingredients i
                  WHERE i.kind = 'fermentable' AND i.name = m.name
                    AND i.supplier IS NOT DISTINCT FROM m.maltster);

-- Hops -----------------------------------------------------------------------
-- ⛔ REWRITTEN 2026-09-22 FOR THE NEW ref.hops SHAPE. This read h.alpha_min,
-- h.alpha_max, h.origin and h.hop_type, all of which were dropped -- and because
-- db-init runs psql with ON_ERROR_STOP=1 inside `set -e`, the missing column did
-- not degrade this seed, it aborted the whole run at file 6 of 20 and skipped
-- every later one including 50_roles.sql.
--
-- There is no midpoint left to take: brewersfriend publishes one alpha figure per
-- variety, so alpha_acid_pct is carried straight through and no spread goes into
-- attrs. Rows seeded from the handbook keep their old attrs -- the NOT EXISTS
-- guard matches on name, so this never rewrites one.
INSERT INTO brew.ingredients (kind, name, supplier, alpha_acid_pct, attrs)
SELECT 'hop', h.name, NULL,
       h.alpha_acid_pct,
       jsonb_build_object('ref_hop_id', h.id,
                          'substitutes', to_jsonb(h.substitutes),
                          'beer_styles', h.beer_styles,
                          'source_doc', 'brewersfriend.com')
FROM ref.hops h
WHERE NOT EXISTS (SELECT 1 FROM brew.ingredients i
                  WHERE i.kind = 'hop' AND i.name = h.name);
