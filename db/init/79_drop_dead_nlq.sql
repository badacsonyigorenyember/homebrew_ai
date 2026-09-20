-- =============================================================================
-- 79_drop_dead_nlq.sql  ·  Remove the functions trend.* replaces (D12)
--
-- nlq.common_practice, nlq.ingredient_practice and nlq.f_corpus_styles read
-- corpus.recipe_misc and corpus.recipe_yeasts (dropped with the old corpus) and
-- a corpus.recipes since reshaped to BeerJSON. They raise at every call.
--
-- ⚠ THEY ARE REFERENCED BY SEVEN NODES ACROSS THREE WORKFLOWS -- wf-step-practice,
-- cap-formulate-recipe (Step 3 propose and Step 3b re-propose) and chat-agent.
-- D12: the pipeline is being reworked and owes them no compatibility. Those
-- workflows must move to trend.v_* as part of that rework; this file only stops
-- a broken function from looking available.
--
-- Idempotent.
-- =============================================================================

DROP FUNCTION IF EXISTS nlq.common_practice(text, integer);
DROP FUNCTION IF EXISTS nlq.ingredient_practice(text, text, integer);
DROP FUNCTION IF EXISTS nlq.f_corpus_styles(text);
