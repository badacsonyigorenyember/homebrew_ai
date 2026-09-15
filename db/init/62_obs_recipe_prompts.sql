-- =============================================================================
-- 62_obs_recipe_prompts.sql  ·  Prompts for cap-formulate-recipe
--
-- Same contract as the brainstorm prompts in 60_obs.sql: versioned, one ACTIVE
-- row per name, body hashed by the trigger so a run records exactly what was
-- sent. Runs AFTER 60_obs.sql. Idempotent.
--
-- ⛔ The division of labour these prompts encode: the model picks INGREDIENTS
-- and PROPORTIONS. It never states a gravity, an ABV, an IBU or a colour --
-- brew.f_fit_recipe and brew.f_compute_recipe produce those, and `compose` is
-- given them as facts to repeat. A 12B cannot do this arithmetic reliably and
-- is never asked to.
-- =============================================================================

INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/parse', 1, $body$
Extract the recipe brief from a brewer's request. Output JSON only, no prose.

Request:
{{question}}

Fields:
- style: the beer style asked for, in the brewer's words ("pastry stout",
  "dry irish stout"). If none is named, infer the closest style and use that.
- batch_size_l: batch volume in litres. If the brewer gives gallons, convert.
  If no volume is given at all, use 20.
- target_abv_pct: the ABV asked for, as a number. If a range is given take its
  midpoint. If none is given, use 0 and the caller will pick from the style.
- descriptors: array of the sensory words the brewer used -- "sweet", "thick",
  "custardy", "roasty". Their words, not synonyms. Empty array if none.
- must_include: array of ingredients or additions the brewer explicitly asked
  for -- "vanilla", "lactose", "rum". Empty array if none.
- avoid: array of things they said they did not want, including anything they
  wanted very little of -- "hops" if they asked for very little hop character.
  Empty array if none.
$body$, true, 'v1 initial'),

('formulate.recipe/propose', 1, $body$
You are formulating a grain bill and hop schedule for an experienced homebrewer.

Their request:
{{question}}

The brief:
{{spec}}

Passages from the brewer's library -- use these for TECHNIQUE decisions (mash
temperature, when to add an adjunct, what builds body in this style):
{{passages}}

The ONLY ingredients you may use, as "id | kind | name | ppg | lovibond | alpha":
{{catalogue}}

Choose the ingredients and their PROPORTIONS. Output JSON only.

⛔ Every ingredient_id MUST appear in the catalogue above, copied exactly. Never
invent an id, never invent an ingredient, and never use an ingredient that is
not listed -- if the brewer asked for something that is not there, leave it out
and name it in "not_available".

⛔ Do NOT state a gravity, ABV, IBU, colour or efficiency anywhere. Those are
computed from your choices after you answer. Your amounts set the PROPORTIONS
only; the mashed grain is scaled afterwards to hit the target strength, so pick
a sensible total and let the ratios carry the recipe.

Fields:
- items: array of {ingredient_id, stage, qty_g, timing_min, notes}
  - stage: one of "mash", "boil", "whirlpool", "dryhop", "fermenter", "packaging".
  - qty_g: grams. Whole numbers.
  - timing_min: minutes for hop and boil additions; omit for mash items.
  - notes: at most 12 words saying what that ingredient is doing. Not a sales pitch.
  - Base malt is normally 70-85% of the grain. Roasted malts above about 8% turn
    acrid. A sugar or lactose addition belongs at "boil" late, not in the mash.
  - Include at least one hop with a timing_min, even when the brewer wants very
    little bitterness -- a stout with no bittering addition is cloying.
- mash_temp_c: a single number. Higher leaves more unfermentable body.
- attenuation: apparent attenuation as a decimal (0.72 = 72%). Pick from the
  yeast character the style needs; lower finishes sweeter.
- not_available: array of things the brewer asked for that are not in the
  catalogue. Empty array if none.
- rationale: one sentence, at most 30 words, on the shape of the grist.
$body$, true, 'v1 initial'),

('formulate.recipe/compose', 1, $body$
Write the recipe for the brewer.

What they asked for:
{{question}}

The recipe, already costed -- ingredient, stage, amount:
{{recipe}}

⛔ The computed figures. These are CORRECT and were calculated, not estimated.
Print them exactly as given; never recalculate, round or "correct" them:
{{computed}}

Library passages supporting the technique, cite these by label:
{{sources}}

Asked for but not in the catalogue -- say so plainly, once:
{{gaps}}

Rules:
- Lead with the recipe. No preamble, no "great choice".
- Give the grain bill as a list with grams, then hops with times, then the
  additions, then mash temperature. Nothing else.
- State OG, FG, ABV, IBU and EBC exactly as given above, once, together.
- ⛔ Never state a number that does not appear above. If you find yourself
  calculating anything, stop -- the arithmetic is already done.
- Mark technique claims taken from the passages with their [S..] label. Do not
  cite the ingredient amounts; those are computed, not quoted.
- If "not available" is non-empty, add one short line naming what the library
  and catalogue do not cover. Do not substitute something else for it silently.
- End with a Sources block listing only the labels you actually cited. If you
  cited nothing, omit it entirely.
- English. Metric: litres, °C, grams. Gravity to three decimals. IBU whole.
- Direct and technical. This brewer is experienced.
$body$, true, 'v1 initial')
ON CONFLICT (name, version) DO NOTHING;

-- ---------------------------------------------------------------------------
-- compose v2: print the Sources LINES, not the labels.
--
-- ⛔ v1 ended with "a Sources block listing only the labels you actually cited"
-- and both models did exactly that -- gemma4:12b and qwen3.5:9b-q8 each closed
-- with a bare "[S1] [S2] [S3]" and no titles (measured, runs 71 and 72). Neither
-- was disobeying: `sources` arrives here already formatted as
-- "[S1] <title>, p.<n>" per line, and the rule asked for labels.
--
-- The pairing prompt already had the right wording; this one never got it.
-- Copied across verbatim, including the anti-placeholder clause.
--
-- ⚠️ The defect was invisible for a while because the chat-agent holds the same
-- passages in its own context and sometimes backfills the titles downstream.
-- Whether the brewer sees provenance was therefore luck. Read the compose step
-- output in obs.steps, not the agent's final message, when judging this rule.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/compose', 2, $body$
Write the recipe for the brewer.

What they asked for:
{{question}}

The recipe, already costed -- ingredient, stage, amount:
{{recipe}}

⛔ The computed figures. These are CORRECT and were calculated, not estimated.
Print them exactly as given; never recalculate, round or "correct" them:
{{computed}}

Library passages supporting the technique, cite these by label:
{{sources}}

Asked for but not in the catalogue -- say so plainly, once:
{{gaps}}

Rules:
- Lead with the recipe. No preamble, no "great choice".
- Give the grain bill as a list with grams, then hops with times, then the
  additions, then mash temperature. Nothing else.
- State OG, FG, ABV, IBU and EBC exactly as given above, once, together.
- ⛔ Never state a number that does not appear above. If you find yourself
  calculating anything, stop -- the arithmetic is already done.
- Mark technique claims taken from the passages with their [S..] label. Do not
  cite the ingredient amounts; those are computed, not quoted.
- If "not available" is non-empty, add one short line naming what the library
  and catalogue do not cover. Do not substitute something else for it silently.
- End with a Sources block, copied verbatim from the passage list above, keeping
  only the WHOLE lines whose label you actually cited -- each line carries its
  document title and page and both must be printed. A bare "[S1]" with no title
  is a failure. Never invent a title and never print a placeholder. If you cited
  nothing, omit the block entirely.
- English. Metric: litres, °C, grams. Gravity to three decimals. IBU whole.
- Direct and technical. This brewer is experienced.
$body$, false, 'v2: Sources block prints whole lines with titles, not bare labels')
ON CONFLICT (name, version) DO NOTHING;

-- ---------------------------------------------------------------------------
-- The `formulate` profile.
--
-- `propose` cannot run on the `extract` profile: its prompt carries the whole
-- ingredient catalogue plus the retrieved passages, which measured 7325 tokens
-- against extract's num_ctx of 8192. That left ~800 tokens for the answer, the
-- structured output stopped with done_reason "length", and the truncated JSON
-- failed validation.
--
-- num_ctx matches `creative`/`compose` at 12288 ON PURPOSE: Ollama keys its
-- loaded runner on the context size, so reusing 12288 means no model reload
-- between steps. Temperature stays near zero -- this step emits a schema, not prose.
-- ---------------------------------------------------------------------------
INSERT INTO obs.profiles (name, model, options, notes) VALUES
('formulate', 'gemma4:12b',
 '{"num_ctx": 12288, "keep_alive": "30m", "temperature": 0.1}'::jsonb,
 'recipe grist/hop selection: large prompt, structured output')
ON CONFLICT (name) DO UPDATE
  SET model = EXCLUDED.model, options = EXCLUDED.options, notes = EXCLUDED.notes;

-- ---------------------------------------------------------------------------
-- propose v2 — colour and bitterness floors.
--
-- v1 produced a "pastry stout" at EBC 13.7 (run 61): 179 g of dark malt in a
-- 3.5 kg grist, which is the colour of a pale ale. v1 warned about the CEILING
-- ("roasted malts above 8% turn acrid") and gave no floor, so the model kept
-- trimming. It also omitted the boil time on its only hop, which computes to
-- IBU 0 -- the workflow now assumes 60 min and says so, but the prompt should
-- ask for it plainly.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/propose', 2, $body$
You are formulating a grain bill and hop schedule for an experienced homebrewer.

Their request:
{{question}}

The brief:
{{spec}}

Passages from the brewer's library -- use these for TECHNIQUE decisions (mash
temperature, when to add an adjunct, what builds body in this style):
{{passages}}

The ONLY ingredients you may use, as "id | kind | name | ppg | lovibond | alpha":
{{catalogue}}

Choose the ingredients and their PROPORTIONS. Output JSON only.

⛔ Every ingredient_id MUST appear in the catalogue above, copied exactly. Never
invent an id, never invent an ingredient, and never use an ingredient that is
not listed -- if the brewer asked for something that is not there, leave it out
and name it in "not_available".

⛔ Do NOT state a gravity, ABV, IBU, colour or efficiency anywhere. Those are
computed from your choices after you answer. Your amounts set the PROPORTIONS
only; the mashed grain is scaled afterwards to hit the target strength, so pick
a sensible total and let the ratios carry the recipe.

⛔ The grist must produce the COLOUR the style actually is. A stout or porter is
black: it needs roughly 8-15% of the grain bill in dark and roasted malts
combined -- chocolate, roast barley, black malt, dark caramel. Below that it is
a brown ale wearing the wrong name. Stay under about 15% or it turns acrid. A
pale style needs almost none. Look at the lovibond column and mean it.

Fields:
- items: array of {ingredient_id, stage, qty_g, timing_min, notes}
  - stage: one of "mash", "boil", "whirlpool", "dryhop", "fermenter", "packaging".
  - qty_g: grams. Whole numbers.
  - timing_min: REQUIRED for every hop and every boil addition -- minutes before
    the end of the boil. A bittering hop is normally 60. Omit only for mash items.
  - notes: at most 12 words saying what that ingredient is doing. Not a sales pitch.
  - Base malt is normally 70-85% of the grain. A sugar or lactose addition belongs
    at "boil" late, not in the mash.
  - Include at least one hop with a timing_min, even when the brewer wants very
    little bitterness -- a stout with no bittering addition is cloying.
- mash_temp_c: a single number. Higher leaves more unfermentable body.
- attenuation: apparent attenuation as a decimal (0.72 = 72%). Pick from the
  yeast character the style needs; lower finishes sweeter.
- not_available: array of things the brewer asked for that are not in the
  catalogue. Empty array if none.
- rationale: one sentence, at most 30 words, on the shape of the grist.
$body$, false, 'v2: colour floor for dark styles; boil time required on hops')
ON CONFLICT (name, version) DO NOTHING;


-- ---------------------------------------------------------------------------
-- propose v3 — buckets instead of judgement, and `avoid` made binding.
--
-- Two measured failures in run 62, both with all the information present:
--   * v2 asked the model to pick dark malts by reading the lovibond column. It
--     read the NAME instead and put "Floor-Malted Bohemian Dark Malt" (6.5 degL)
--     in the roast slot -> EBC 44 for a pastry stout. The catalogue is now
--     pre-bucketed by brew.f_catalogue, so that choice is no longer available.
--   * parse extracted avoid:["hop bitterness"] correctly and propose then
--     specified 30 g at 60 min -> 40 IBU. Nothing told it `avoid` was binding.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/propose', 3, $body$
You are formulating a grain bill and hop schedule for an experienced homebrewer.

Their request:
{{question}}

The brief:
{{spec}}

Passages from the brewer's library -- use these for TECHNIQUE decisions (mash
temperature, when to add an adjunct, what builds body in this style):
{{passages}}

The ONLY ingredients you may use, grouped by what they do:
{{catalogue}}

Choose the ingredients and their PROPORTIONS. Output JSON only.

⛔ Every ingredient_id MUST appear in the lists above, copied exactly. Never
invent an id and never use an ingredient that is not listed -- if the brewer
asked for something absent, leave it out and name it in "not_available".

⛔ Do NOT state a gravity, ABV, IBU, colour or efficiency anywhere. Those are
computed from your choices after you answer. Your amounts set PROPORTIONS only;
the mashed grain is scaled afterwards to hit the target strength.

⛔ COLOUR COMES FROM THE "ROAST MALTS" LIST AND NOWHERE ELSE. A malt with "dark"
or "brown" in its name is not a roast malt -- the lists already sort that out,
so trust the heading, not the name. For a stout or porter take 8-15% of the
grain bill from ROAST MALTS specifically; below 8% it is a brown ale wearing the
wrong name, above 15% it turns acrid. Caramel malts add sweetness and body, not
darkness. A pale style takes none.

⛔ THE "avoid" LIST IN THE BRIEF IS BINDING. If it names hops or bitterness, the
bittering addition is 10-15 min and no more than 10 g per 10 L of batch -- NOT
60 min. A late, small addition gives balance without bitterness. Honour every
other entry in "avoid" the same way.

Fields:
- items: array of {ingredient_id, stage, qty_g, timing_min, notes}
  - stage: one of "mash", "boil", "whirlpool", "dryhop", "fermenter", "packaging".
  - qty_g: grams. Whole numbers.
  - timing_min: REQUIRED for every hop and every boil addition -- minutes before
    the end of the boil. Normally 60; see the avoid rule above.
  - notes: at most 12 words saying what that ingredient is doing.
  - Base malt is normally 70-85% of the grain. Sugars and lactose go in at
    "boil" late, never in the mash.
  - Always include exactly one hop. Even a sweet stout needs a little balance.
- mash_temp_c: a single number. Higher leaves more unfermentable body.
- attenuation: apparent attenuation as a decimal (0.72 = 72%). Lower finishes sweeter.
- not_available: array of things the brewer asked for that are not in the lists.
- rationale: one sentence, at most 30 words, on the shape of the grist.
$body$, false, 'v3: role-bucketed catalogue; avoid list binding on hop timing')
ON CONFLICT (name, version) DO NOTHING;


-- ---------------------------------------------------------------------------
-- Generation caps.
--
-- Measured run 63: `compose` was given a 704-token prompt and generated 11,584
-- tokens before hitting num_ctx, returning done_reason "length" and a truncated
-- answer -- for a recipe write-up that needs about 300. Nothing bounded it.
-- num_predict turns a runaway into a clean stop instead of a broken response.
-- ---------------------------------------------------------------------------
UPDATE obs.profiles
   SET options = options || '{"num_predict": 900}'::jsonb
 WHERE name = 'compose';

-- ⛔ NOT on `formulate`. Capping a schema-constrained step is worse than not
-- capping it: `compose` writes prose, so a cap just shortens the answer, but
-- `propose` must emit closed JSON and a cap guarantees it cannot. Measured run
-- 64: num_predict 1600 stopped propose at exactly 1599 tokens mid-object and
-- all three retries failed validation. Let it finish; num_ctx is the real bound.
UPDATE obs.profiles
   SET options = options - 'num_predict'
 WHERE name = 'formulate';

-- ---------------------------------------------------------------------------
-- Which propose version is live.
--
-- prompts_one_active_idx allows exactly one ACTIVE row per name, so activating
-- version-by-version as versions are added makes this file non-idempotent: on a
-- re-run an earlier block activates v2 while v3 is still active and the insert
-- aborts. Clear them all, then set the one that should be live. Change the
-- version number here to roll forward or back.
-- ---------------------------------------------------------------------------
UPDATE obs.prompts SET active = false WHERE name = 'formulate.recipe/propose';
UPDATE obs.prompts SET active = true  WHERE name = 'formulate.recipe/propose' AND version = 3;

UPDATE obs.prompts SET active = false WHERE name = 'formulate.recipe/compose';
UPDATE obs.prompts SET active = true  WHERE name = 'formulate.recipe/compose' AND version = 2;
