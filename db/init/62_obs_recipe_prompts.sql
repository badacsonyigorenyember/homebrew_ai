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
-- compose v3 — the Sources HEADING, the "none" sentinel, and one line to cite.
--
-- Three defects measured over 8 runs (gemma4:12b-it-q8_0 vs gemma4:12b), read
-- from obs.steps at step_id 'compose', not from the agent's final message:
--
--   * ⛔ The literal word "Sources" was absent in 3 of 5 Q8 runs (0 of 3 on Q4).
--     The source LINES were emitted with titles and pages -- v2's fix held --
--     but with no heading above them. The chat-agent reformats compose's output
--     and silently discards trailing unheaded lines, so the brewer saw no
--     provenance at all. The heading is the load-bearing part, not the lines.
--   * ⛔ `Build compose vars` passes gaps: 'none' when there are no gaps, and the
--     model printed a bare line reading "none" in the middle of the recipe --
--     5 of 5 Q8 runs, 0 of 3 Q4. `sources` carries the same sentinel and can
--     leak the same way.
--   * The root cause of the first: v2 asked for [S..] labels on technique claims
--     while also closing the body with "Nothing else". A model obeying both
--     writes no technique prose, so it has nothing to attach a label to, so it
--     cites nothing -- and v2 then told it to omit the block entirely. What came
--     out was the list with its heading stripped: the worst of both rules.
--
-- Hence: the block is unconditional on having cited, and the body gains exactly
-- ONE technique line so a label has something to sit on. Bounded at 25 words on
-- purpose -- this is a recipe, not an essay. The "none" suppression is the
-- construction brainstorm.pairing/compose already uses (60_obs.sql), applied to
-- both sentinels. Every other v2 rule is carried over unchanged.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/compose', 3, $body$
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
  additions, then mash temperature.
- Then exactly ONE line, at most 25 words, on the technique that makes this beer
  what the brewer asked for, taken from the passages and carrying its [S..]
  label. One line -- not two, not a paragraph. Nothing else follows it but the
  figures and the Sources block.
- State OG, FG, ABV, IBU and EBC exactly as given above, once, together.
- ⛔ Never state a number that does not appear above. If you find yourself
  calculating anything, stop -- the arithmetic is already done.
- Mark technique claims taken from the passages with their [S..] label. Do not
  cite the ingredient amounts; those are computed, not quoted.
- If "not available" is non-empty, add one short line naming what the library
  and catalogue do not cover. Do not substitute something else for it silently.
- ⛔ If the "not available" list reads "none", that line MUST NOT appear at all.
  "none" is a sentinel meaning there is nothing to report -- never print it, and
  never print the word "none" on a line of its own anywhere in the answer.
- ⛔ End with a Sources block. It is MANDATORY whenever the passage list above
  has lines in it, and it does NOT depend on what you cited. Print the literal
  heading
  Sources:
  on its own line, then the passage lines copied verbatim -- each carries its
  document title and page and both must be printed. Keep the lines whose label
  you cited; if you cited none, print them all. A list with no heading is a
  failure, and so is a bare "[S1]" with no title. Never invent a title and never
  print a placeholder.
- ⛔ If the passage list reads "none", omit the Sources block entirely.
- English. Metric: litres, °C, grams. Gravity to three decimals. IBU whole.
- Direct and technical. This brewer is experienced.
$body$, false, 'v3: Sources heading mandatory; "none" sentinel suppressed; one technique line to carry [S..]')
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
-- propose v4 — a slot for the verifier to answer into.
--
-- The computed figures are now checked against the brief before the recipe is
-- accepted (`Check bands` in cap-formulate-recipe), and a miss re-runs THIS step
-- once with the miss named in numbers. That correction has to reach the model
-- somewhere, and it cannot be smuggled into {{question}} or {{spec}} -- those are
-- what the brewer said, and overwriting them would falsify what obs.steps
-- records as the request.
--
-- So v4 is v3 with one empty placeholder, and nothing else changes: byte for
-- byte the same instructions, the same colour floor, the same binding `avoid`.
-- The first attempt supplies correction: '' and renders exactly v3; only a
-- second attempt fills it, with the sentences `Check bands` built from
-- ref.f_style_bands and brew.f_compute_recipe -- numbers, and the catalogue
-- section to move, never "try again".
--
-- ⛔ The slot is UNCONDITIONAL because wf-step-llm's `Render prompt` throws on a
-- placeholder it was not given. Both callers must pass `correction`; the first
-- one passes nothing.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/propose', 4, $body$
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

{{correction}}

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
$body$, false, 'v4: {{correction}} slot for the verifier gate; v3 otherwise verbatim')
ON CONFLICT (name, version) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Which propose version is live.
--
-- prompts_one_active_idx allows exactly one ACTIVE row per name, so activating
-- version-by-version as versions are added makes this file non-idempotent: on a
-- re-run an earlier block activates v2 while v3 is still active and the insert
-- aborts. Clear them all, then set the one that should be live. Change the
-- version number here to roll forward or back.
-- ---------------------------------------------------------------------------
-- ---------------------------------------------------------------------------
-- propose v5: stop `avoid` eating the hop schedule, take roast FIRST, and make
-- a self-contradicting request say so.
--
-- ⛔ Three failures found by the first full run of scripts/stress/recipe_eval.py
-- (1 PASS / 5 FAIL on gemma4:12b-it-q8_0). All three are prompt defects, not
-- model defects -- the model did what v4 told it to.
--
-- 1. THE HOP COLLAPSE. v4 ended the `avoid` rule with "Honour every other entry
--    in avoid the same way", meaning "respect the other entries too". It reads
--    as "give the other entries the same 10-15 min hop treatment", and that is
--    how it was followed. R03 avoid ["roast character"] -> one hop at 10 min,
--    IBU 6 against a band of 20-40. R05 avoid ["roasted barley", "astringent
--    bite"] -> one hop at 10 min, IBU 16 against 40-80. NEITHER request said a
--    word about hops. The two cases whose `avoid` was empty (R01, R02) both got
--    a 60 min charge and both landed in band. "Always include exactly one hop"
--    then removed any way back: one hop cannot bitter and flavour at once.
--
-- 2. THE ROAST SQUEEZE. v4 asked for base 70-85% AND roast 8-15% AND gave
--    caramel no ceiling. Those do not fit: R04 filled base to 76.5% and caramel
--    to 17.3%, leaving 6.2% for roast against a floor of 8. The model satisfied
--    the constraints in the order they were written. So the order is stated now,
--    and the base figure is advisory where the roast fraction is binding.
--
-- 3. THE DENIED CONTRADICTION. R06 asks for a jet-black stout "using absolutely
--    no roasted or dark malts". v4 had no way to say "that cannot be done", so
--    it put 1104 g of Black Malt -- 22.5% of the grist -- into the beer and
--    wrote "provides the jet-black color and roast without using roasted or
--    dark malts". Committing the contradiction and denying it in the same
--    sentence is worse than either failure alone. `not_available` is the wrong
--    channel: that field is for ingredients the CATALOGUE lacks. New field.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/propose', 5, $body$
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

⛔ BUILD THE GRAIN BILL IN THIS ORDER. Take the ROAST MALTS fraction FIRST, then
caramel, then fill whatever remains with base malt. Doing it the other way round
leaves nothing for the roast malts and produces a pale beer wearing a dark name.
  1. ROAST MALTS -- for a stout or porter, 8-15% of the grain bill. This is
     BINDING. Below 8% it is a brown ale wearing the wrong name; above 15% it
     turns acrid. A pale style takes none.
  2. CARAMEL malts -- sweetness and body, never colour. Keep them under 20%.
  3. BASE malt -- the remainder. Around 70-85% in a pale beer, and lower in a
     dark one. This is the figure that gives way, not the roast fraction.
Colour comes from the ROAST MALTS list and nowhere else. A malt with "dark" or
"brown" in its name is not a roast malt -- the lists already sort that out, so
trust the heading, not the name.

⛔ THE "avoid" LIST IS BINDING, BUT EACH ENTRY CONSTRAINS ONLY WHAT IT NAMES.
An entry about roast, colour or astringency constrains the ROAST MALTS. An entry
naming an ingredient means leave that ingredient out. An entry about malt must
NOT change the hop schedule. Read each entry for what it says and nothing more.

⛔ HOPS. Give the beer a 60 min bittering addition. That is what creates
bitterness -- a 10 or 15 min addition creates almost none, and a stout with no
60 min charge finishes flabby. You may add a SECOND hop late (10-20 min) for
flavour where the style wants it.
  THE ONE EXCEPTION: if "avoid" names HOPS or BITTERNESS specifically -- and only
  then -- there is no 60 min addition at all. Use a single 10-15 min hop, at most
  10 g per 10 L of batch. Nothing else in "avoid" triggers this.

⛔ IF THE REQUEST CONTRADICTS ITSELF, SAY SO IN "conflicts". Some briefs cannot
be satisfied: a beer cannot be jet-black while using no roasted or dark malts,
because colour of that depth comes only from roast malts. Name the conflict in
plain words, then build the closest honest beer you can and let "conflicts"
carry the caveat. ⛔ Never satisfy one half and describe it as satisfying both.
Putting black malt into a beer specified to have none, and calling it "without
roasted or dark malts", is the worst answer available to you.

{{correction}}

Fields:
- items: array of {ingredient_id, stage, qty_g, timing_min, notes}
  - stage: one of "mash", "boil", "whirlpool", "dryhop", "fermenter", "packaging".
  - qty_g: grams. Whole numbers.
  - timing_min: REQUIRED for every hop and every boil addition -- minutes before
    the end of the boil. 60 for the bittering charge; see the hop rule above.
  - notes: at most 12 words saying what that ingredient is doing.
  - Sugars and lactose go in at "boil" late, never in the mash.
  - Always include at least one hop. Even a sweet stout needs a little balance.
- mash_temp_c: a single number. Higher leaves more unfermentable body.
- attenuation: apparent attenuation as a decimal (0.72 = 72%). Lower finishes sweeter.
- not_available: array of things the brewer asked for that are not in the lists.
- conflicts: array of plain sentences, each naming one way the request cannot be
  satisfied as written. Empty array if the request is coherent.
- rationale: one sentence, at most 30 words, on the shape of the grist.
$body$, false, 'v5: avoid scoped to what it names; 60 min bittering default; roast taken first; conflicts field')
ON CONFLICT (name, version) DO NOTHING;


-- ---------------------------------------------------------------------------
-- propose v6: size the bittering charge, and make 15% roast a real ceiling.
--
-- ⛔ v5 fixed the hop collapse and overshot it. Measured on the same six cases:
-- IBU went from 6/16 (too low) to 35/44/126 (too high). v5 said "give the beer
-- a 60 min bittering addition" and never said HOW MUCH, so the model guessed,
-- and it guessed without reference to either batch volume or alpha acid. R05 put
-- 25 g of Magnum at 12.5% alpha into a FIVE litre batch -- 5 g/L of a high-alpha
-- hop, IBU 126 against a band of 40-80. R02, a Helles that had passed under v4,
-- took 35 g of Perle at 7% in 20 L and went to IBU 35 against 12-28.
-- The rule now carries arithmetic: grams per litre, times volume, divided by
-- alpha. A worked example of the exact measured failure is included, because
-- "scale by batch size" on its own did not survive contact with a 5 L recipe.
--
-- ⛔ Also: taking the roast fraction FIRST (v5's fix for R04, which worked --
-- 6.2% -> 13.3% and the case passes) moved the failure to the other end. R01
-- reached 19.2% and R05 20.0%, both past the 15% ceiling, because the gate's
-- correction says "more roast" and v5 gave the ceiling no authority against it.
-- The ceiling now explicitly outranks a correction, and points at the real fix:
-- a darker malt, not more of a paler one.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/propose', 6, $body$
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

⛔ BUILD THE GRAIN BILL IN THIS ORDER. Take the ROAST MALTS fraction FIRST, then
caramel, then fill whatever remains with base malt. Doing it the other way round
leaves nothing for the roast malts and produces a pale beer wearing a dark name.
  1. ROAST MALTS -- for a stout or porter, 8-15% of the grain bill. BOTH ENDS
     ARE BINDING. Below 8% it is a brown ale wearing the wrong name; above 15%
     it turns acrid and thin, and 15% is a ceiling you never cross -- not even
     when a correction below tells you the beer came out too pale. If you are
     already at 15% and still short of colour, move to a DARKER roast malt from
     the list rather than adding more of the one you have. A pale style takes
     none.
  2. CARAMEL malts -- sweetness and body, never colour. Keep them under 20%.
  3. BASE malt -- the remainder. Around 70-85% in a pale beer, and lower in a
     dark one. This is the figure that gives way, not the roast fraction.
Colour comes from the ROAST MALTS list and nowhere else. A malt with "dark" or
"brown" in its name is not a roast malt -- the lists already sort that out, so
trust the heading, not the name.

⛔ THE "avoid" LIST IS BINDING, BUT EACH ENTRY CONSTRAINS ONLY WHAT IT NAMES.
An entry about roast, colour or astringency constrains the ROAST MALTS. An entry
naming an ingredient means leave that ingredient out. An entry about malt must
NOT change the hop schedule. Read each entry for what it says and nothing more.

⛔ HOPS. Give the beer a 60 min bittering addition -- that is what creates
bitterness, a 10 or 15 min addition creates almost none. You may add a SECOND
hop late (10-20 min) for flavour where the style wants it.

⛔ SIZE THE BITTERING CHARGE BY BATCH VOLUME AND BY ALPHA. Both, every time.
  - Start from 0.5 g per LITRE of batch for a hop around 5% alpha.
  - Multiply by batch_size_l. A 5 L batch takes a fifth of what a 25 L batch
    takes. This is the step most often skipped, and it is the expensive one.
  - Then divide by (alpha / 5). A 12.5% alpha hop needs LESS THAN HALF the grams
    of a 5% one for the same bitterness. The catalogue lists each hop's alpha.
  - A gently bittered style takes half of that; an aggressively hoppy one twice.
  ⛔ Worked example of the failure: 25 g of Magnum at 12.5% alpha in a 5 L batch
  is 5 g per litre of a high-alpha hop -- roughly TEN times too much, and it was
  measured. The correct charge there is about 1 g. Late flavour hops are not
  bound by this; they contribute almost no bitterness whatever their weight.

  THE ONE EXCEPTION: if "avoid" names HOPS or BITTERNESS specifically -- and only
  then -- there is no 60 min addition at all. Use a single 10-15 min hop, at most
  10 g per 10 L of batch. Nothing else in "avoid" triggers this.

⛔ IF THE REQUEST CONTRADICTS ITSELF, SAY SO IN "conflicts". Some briefs cannot
be satisfied: a beer cannot be jet-black while using no roasted or dark malts,
because colour of that depth comes only from roast malts. Name the conflict in
plain words, then build the closest honest beer you can and let "conflicts"
carry the caveat. ⛔ Never satisfy one half and describe it as satisfying both.
Putting black malt into a beer specified to have none, and calling it "without
roasted or dark malts", is the worst answer available to you.

{{correction}}

Fields:
- items: array of {ingredient_id, stage, qty_g, timing_min, notes}
  - stage: one of "mash", "boil", "whirlpool", "dryhop", "fermenter", "packaging".
  - qty_g: grams. Whole numbers.
  - timing_min: REQUIRED for every hop and every boil addition -- minutes before
    the end of the boil. 60 for the bittering charge; see the hop rule above.
  - notes: at most 12 words saying what that ingredient is doing.
  - Sugars and lactose go in at "boil" late, never in the mash.
  - Always include at least one hop. Even a sweet stout needs a little balance.
- mash_temp_c: a single number. Higher leaves more unfermentable body.
- attenuation: apparent attenuation as a decimal (0.72 = 72%). Lower finishes sweeter.
- not_available: array of things the brewer asked for that are not in the lists.
- conflicts: array of plain sentences, each naming one way the request cannot be
  satisfied as written. Empty array if the request is coherent.
- rationale: one sentence, at most 30 words, on the shape of the grist.
$body$, false, 'v6: bittering charge sized by volume and alpha; 15% roast ceiling outranks a correction')
ON CONFLICT (name, version) DO NOTHING;


UPDATE obs.prompts SET active = false WHERE name = 'formulate.recipe/propose';
UPDATE obs.prompts SET active = true  WHERE name = 'formulate.recipe/propose' AND version = 6;

-- ---------------------------------------------------------------------------
-- compose v4: carry a contradiction through to the brewer.
--
-- propose v5 gained a "conflicts" field, and `Validate proposal` merges it into
-- the same `gaps` channel that already carried missing ingredients. v3's header
-- called that channel "Asked for but not in the catalogue", which is now only
-- half of what arrives on it, and v3's rule let the line be dropped. R06
-- measured what that costs: the answer described a beer built from 22.5% black
-- malt as using "no roasted or dark malts". The contradiction line is mandatory.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/compose', 4, $body$
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

Problems the brewer must be told about -- anything the catalogue does not
cover, and any way the request contradicts itself:
{{gaps}}

Rules:
- Lead with the recipe. No preamble, no "great choice".
- Give the grain bill as a list with grams, then hops with times, then the
  additions, then mash temperature.
- Then exactly ONE line, at most 25 words, on the technique that makes this beer
  what the brewer asked for, taken from the passages and carrying its [S..]
  label. One line -- not two, not a paragraph. Nothing else follows it but the
  figures and the Sources block.
- State OG, FG, ABV, IBU and EBC exactly as given above, once, together.
- ⛔ Never state a number that does not appear above. If you find yourself
  calculating anything, stop -- the arithmetic is already done.
- Mark technique claims taken from the passages with their [S..] label. Do not
  cite the ingredient amounts; those are computed, not quoted.
- If the problems list is non-empty, add one short line naming each problem.
  Do not substitute something else for a missing ingredient silently.
- ⛔ If a problem says the request CONTRADICTS ITSELF, that line is not optional
  and it is not softened. Say which two things cannot both be true, in the
  brewer's own terms, before the figures. A recipe that quietly does the
  opposite of what was asked and does not say so is the worst answer available.
- ⛔ If the problems list reads "none", that line MUST NOT appear at all.
  "none" is a sentinel meaning there is nothing to report -- never print it, and
  never print the word "none" on a line of its own anywhere in the answer.
- ⛔ End with a Sources block. It is MANDATORY whenever the passage list above
  has lines in it, and it does NOT depend on what you cited. Print the literal
  heading
  Sources:
  on its own line, then the passage lines copied verbatim -- each carries its
  document title and page and both must be printed. Keep the lines whose label
  you cited; if you cited none, print them all. A list with no heading is a
  failure, and so is a bare "[S1]" with no title. Never invent a title and never
  print a placeholder.
- ⛔ If the passage list reads "none", omit the Sources block entirely.
- English. Metric: litres, °C, grams. Gravity to three decimals. IBU whole.
- Direct and technical. This brewer is experienced.
$body$, false, 'v4: gaps channel also carries contradictions, and the contradiction line is mandatory')
ON CONFLICT (name, version) DO NOTHING;


UPDATE obs.prompts SET active = false WHERE name = 'formulate.recipe/compose';
UPDATE obs.prompts SET active = true  WHERE name = 'formulate.recipe/compose' AND version = 4;


-- ---------------------------------------------------------------------------
-- compose v5: the layout stops being the model's job.
--
-- v1-v4 grew from four layout rules to nine, and the measurements in the
-- comments above say what that bought: the mandatory Sources heading went
-- missing in 3 of 5 runs, a bare "[S1]" with no title in two more, and R06's
-- contradiction line dropped entirely. Each miss was answered with a more
-- forceful restatement of the same rule. That is the move `Validate proposal`
-- already abandoned for the 15% roast ceiling -- "restating a numeric
-- proportion more forcefully did not work twice, so it stops being the model's
-- job" -- and it is abandoned here for the same reason.
--
-- Every figure on the sheet comes from brew.f_compute_recipe or fit.items, so
-- the sheet is rendered by the `Return` code node and cannot drift. What is
-- left for a model is the one thing no table holds: a sentence of technique.
-- This prompt asks for that sentence and nothing else.
--
-- ⛔ It is also the first version that can actually support the claim. v1-v4
-- were handed {{sources}} -- "[S1] How to Brew, p.98" reference lines with no
-- passage TEXT -- and asked to "mark technique claims taken from the passages
-- with their [S..] label". There was nothing behind the label to take a claim
-- from. v5 gets {{passages}}, the same passage text `propose` receives.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/compose', 5, $body$
One line. Nothing else.

What the brewer asked for:
{{question}}

The grain bill that was built for them:
{{recipe}}

Passages from the brewer's library:
{{passages}}

Write ONE sentence, at most 25 words, naming the technique that makes this beer
what the brewer asked for, and ending with the [S..] label of the passage that
says it.

⛔ Output that sentence and nothing else. No heading, no preamble, no list, no
second sentence, no sign-off. The grain bill, the hops, the mash, the figures,
the warnings and the Sources block are all printed around your line by the
program that called you. Anything you print from them appears twice.

⛔ The claim must be IN one of the passages above. If no passage supports a
technique claim about this beer, output nothing at all -- an empty answer is
correct and the sheet reads perfectly well without the line. Never invent a
claim, and never put an [S..] label on something its passage does not say.

⛔ Never state a gravity, ABV, IBU, colour, weight or temperature. Every number
this brewer needs is already printed for them, computed rather than recalled.

English. Direct and technical. This brewer is experienced.
$body$, false, 'v5: one technique sentence only; the sheet is rendered in code, not composed. First version given the passage text behind the [S..] labels.')
ON CONFLICT (name, version) DO NOTHING;

UPDATE obs.prompts SET active = false WHERE name = 'formulate.recipe/compose';
UPDATE obs.prompts SET active = true  WHERE name = 'formulate.recipe/compose' AND version = 5;


-- ---------------------------------------------------------------------------
-- propose v7 -- the corpus enters the prompt (2026-09-16)
--
-- v6 told the model to build a grain bill from rules alone: "8-15% roast",
-- "0.5 g per litre for a 5% alpha hop". Those numbers were reasoned from the
-- library, and they are the numbers the model kept missing. v7 also hands it
-- what 174,554 homebrewers actually did for the style it was asked for --
-- nlq.cohort_stats, quartiles, so a wide spread reads as wide.
--
-- ⛔ THE RULES STAY. The practice block is added ABOVE them, not instead of
-- them: the 8-15% roast window and the alpha-scaled bittering charge are
-- reasoned from the brewer's books and the corpus cannot overrule a book. The
-- prompt says so explicitly, and the 15% ceiling is still enforced in code in
-- `Validate proposal` regardless of what either says.
--
-- ⛔ THE BLOCK'S NAMES ARE NOT IDS, and this is the failure mode to watch. The
-- corpus speaks in "American - Pale 2-Row"; brew.ingredients speaks in
-- Weyermann SKUs. A model that reads a name in the practice block and reaches
-- for the nearest-sounding catalogue entry has been handed a way to pick the
-- wrong malt with confidence, so the prompt names that trap twice.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/propose', 7, $body$

You are formulating a grain bill and hop schedule for an experienced homebrewer.

Their request:
{{question}}

The brief:
{{spec}}

Passages from the brewer's library -- use these for TECHNIQUE decisions (mash
temperature, when to add an adjunct, what builds body in this style):
{{passages}}

What brewers ACTUALLY do for this style, from 174,000 self-reported homebrew
recipes -- percentages are share of the grain bill, hop figures are grams per
litre of batch:
{{practice}}

⛔ THE PRACTICE BLOCK IS EVIDENCE, NOT INSTRUCTION, AND ITS NAMES ARE NOT IDS.
Those ingredient names come from a different catalogue than yours -- "American -
Pale 2-Row" is not in your list and has no id. Use the block for PROPORTIONS and
for which KIND of ingredient belongs in this beer; take every id from the
catalogue below and nowhere else. If the block names something you have no
equivalent for, ignore it rather than reaching for the nearest-sounding entry.

⛔ It records what people DID, which is not what is correct. A thing 60% of
brewers do can still be wrong, and the passages above are what say whether it
is. Where the passages and the practice block disagree, follow the passages.
Where the block is absent or says it was widened to a different beer, ignore it
completely and build from the rules below.

The ONLY ingredients you may use, grouped by what they do:
{{catalogue}}

Choose the ingredients and their PROPORTIONS. Output JSON only.

⛔ Every ingredient_id MUST appear in the lists above, copied exactly. Never
invent an id and never use an ingredient that is not listed -- if the brewer
asked for something absent, leave it out and name it in "not_available".

⛔ Do NOT state a gravity, ABV, IBU, colour or efficiency anywhere. Those are
computed from your choices after you answer. Your amounts set PROPORTIONS only;
the mashed grain is scaled afterwards to hit the target strength.

⛔ BUILD THE GRAIN BILL IN THIS ORDER. Take the ROAST MALTS fraction FIRST, then
caramel, then fill whatever remains with base malt. Doing it the other way round
leaves nothing for the roast malts and produces a pale beer wearing a dark name.
  1. ROAST MALTS -- for a stout or porter, 8-15% of the grain bill. BOTH ENDS
     ARE BINDING. Below 8% it is a brown ale wearing the wrong name; above 15%
     it turns acrid and thin, and 15% is a ceiling you never cross -- not even
     when a correction below tells you the beer came out too pale. If you are
     already at 15% and still short of colour, move to a DARKER roast malt from
     the list rather than adding more of the one you have. A pale style takes
     none.
  2. CARAMEL malts -- sweetness and body, never colour. Keep them under 20%.
  3. BASE malt -- the remainder. Around 70-85% in a pale beer, and lower in a
     dark one. This is the figure that gives way, not the roast fraction.
Colour comes from the ROAST MALTS list and nowhere else. A malt with "dark" or
"brown" in its name is not a roast malt -- the lists already sort that out, so
trust the heading, not the name.

⛔ THE "avoid" LIST IS BINDING, BUT EACH ENTRY CONSTRAINS ONLY WHAT IT NAMES.
An entry about roast, colour or astringency constrains the ROAST MALTS. An entry
naming an ingredient means leave that ingredient out. An entry about malt must
NOT change the hop schedule. Read each entry for what it says and nothing more.

⛔ HOPS. Give the beer a 60 min bittering addition -- that is what creates
bitterness, a 10 or 15 min addition creates almost none. You may add a SECOND
hop late (10-20 min) for flavour where the style wants it.

⛔ SIZE THE BITTERING CHARGE BY BATCH VOLUME AND BY ALPHA. Both, every time.
  - Start from 0.5 g per LITRE of batch for a hop around 5% alpha.
  - Multiply by batch_size_l. A 5 L batch takes a fifth of what a 25 L batch
    takes. This is the step most often skipped, and it is the expensive one.
  - Then divide by (alpha / 5). A 12.5% alpha hop needs LESS THAN HALF the grams
    of a 5% one for the same bitterness. The catalogue lists each hop's alpha.
  - A gently bittered style takes half of that; an aggressively hoppy one twice.
  ⛔ Worked example of the failure: 25 g of Magnum at 12.5% alpha in a 5 L batch
  is 5 g per litre of a high-alpha hop -- roughly TEN times too much, and it was
  measured. The correct charge there is about 1 g. Late flavour hops are not
  bound by this; they contribute almost no bitterness whatever their weight.

  THE ONE EXCEPTION: if "avoid" names HOPS or BITTERNESS specifically -- and only
  then -- there is no 60 min addition at all. Use a single 10-15 min hop, at most
  10 g per 10 L of batch. Nothing else in "avoid" triggers this.

⛔ IF THE REQUEST CONTRADICTS ITSELF, SAY SO IN "conflicts". Some briefs cannot
be satisfied: a beer cannot be jet-black while using no roasted or dark malts,
because colour of that depth comes only from roast malts. Name the conflict in
plain words, then build the closest honest beer you can and let "conflicts"
carry the caveat. ⛔ Never satisfy one half and describe it as satisfying both.
Putting black malt into a beer specified to have none, and calling it "without
roasted or dark malts", is the worst answer available to you.

{{correction}}

Fields:
- items: array of {ingredient_id, stage, qty_g, timing_min, notes}
  - stage: one of "mash", "boil", "whirlpool", "dryhop", "fermenter", "packaging".
  - qty_g: grams. Whole numbers.
  - timing_min: REQUIRED for every hop and every boil addition -- minutes before
    the end of the boil. 60 for the bittering charge; see the hop rule above.
  - notes: at most 12 words saying what that ingredient is doing.
  - Sugars and lactose go in at "boil" late, never in the mash.
  - Always include at least one hop. Even a sweet stout needs a little balance.
- mash_temp_c: a single number. Higher leaves more unfermentable body.
- attenuation: apparent attenuation as a decimal (0.72 = 72%). Lower finishes sweeter.
- not_available: array of things the brewer asked for that are not in the lists.
- conflicts: array of plain sentences, each naming one way the request cannot be
  satisfied as written. Empty array if the request is coherent.
- rationale: one sentence, at most 30 words, on the shape of the grist.
$body$, false, 'v7: adds {{practice}} -- observed grain-bill and hop proportions for the style from the 174k-recipe corpus, above the reasoned rules rather than replacing them. Names in the block are explicitly not catalogue ids.')
ON CONFLICT (name, version) DO NOTHING;

UPDATE obs.prompts SET active = false WHERE name = 'formulate.recipe/propose';
UPDATE obs.prompts SET active = true  WHERE name = 'formulate.recipe/propose' AND version = 7;


-- ---------------------------------------------------------------------------
-- ⭐ propose v8: the schema gains a slot for an ingredient that has no id.
--
-- `measured` 2026-09-16 (docs/RECIPE-PIPELINE-V2.md §10), and it is the largest
-- quality result this pipeline has produced. Three conditions, six seeds each,
-- on the pastry-stout request naming vanilla, poppy seeds and rum:
--
--   condition                     substituted   malt in fermenter
--   production today (v7)            1 / 6            1 / 6
--   constrained decoding, no slot    6 / 6            5 / 6
--   constrained decoding + slot      0 / 6            0 / 6
--
-- ⛔ READ THE MIDDLE ROW BEFORE TOUCHING THE SCHEMA. Restricting ingredient_id
-- to an enum of real ids -- with no legal way to say "this one has no id" --
-- did not prevent the substitution, it CAUSED it. Forbidden from telling the
-- truth, the decoder has to emit SOME valid id and SOME positive quantity, so
-- it picked a malt and labelled it vanilla, every seed. Constraining an output
-- space with no slot for the truth manufactures the exact fault it was added to
-- prevent. The schema and this prompt ship together or neither ships.
--
-- ⭐ The behaviour was already there and was being thrown away. Across 18 runs
-- on v7 the model emitted ~1.5 items per run with a NON-NUMERIC ingredient_id
-- naming something it had just declared absent -- {"ingredient_id": "vanilla",
-- "qty_g": 0, "notes": "Add vanilla beans soaked in rum to fermenter"} -- which
-- is the model refusing to substitute, naming the real ingredient, giving the
-- correct method and reporting the gap, all at once and all correctly. Then
-- `Validate proposal` dropped every one as "unknown ingredient_id". Stage E was
-- never a capability to teach; it was a schema slot to open.
--
-- ⚠️ In the measured run qty and unit came back null on every seed because the
-- probe schema did not mark them required. They are required here, in the
-- schema and in the field list. The remaining half of that fix -- feeding the
-- per-ingredient practice block so the number has an evidence basis rather than
-- being invented -- is nlq.ingredient_practice and lands in a later version.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/propose', 8, $body$

You are formulating a grain bill and hop schedule for an experienced homebrewer.

Their request:
{{question}}

The brief:
{{spec}}

Passages from the brewer's library -- use these for TECHNIQUE decisions (mash
temperature, when to add an adjunct, what builds body in this style):
{{passages}}

What brewers ACTUALLY do for this style, from 174,000 self-reported homebrew
recipes -- percentages are share of the grain bill, hop figures are grams per
litre of batch:
{{practice}}

⛔ THE PRACTICE BLOCK IS EVIDENCE, NOT INSTRUCTION, AND ITS NAMES ARE NOT IDS.
Those ingredient names come from a different catalogue than yours -- "American -
Pale 2-Row" is not in your list and has no id. Use the block for PROPORTIONS and
for which KIND of ingredient belongs in this beer; take every id from the
catalogue below and nowhere else. If the block names something you have no
equivalent for, ignore it rather than reaching for the nearest-sounding entry.

⛔ It records what people DID, which is not what is correct. A thing 60% of
brewers do can still be wrong, and the passages above are what say whether it
is. Where the passages and the practice block disagree, follow the passages.
Where the block is absent or says it was widened to a different beer, ignore it
completely and build from the rules below.

The ONLY ingredients you may use, grouped by what they do:
{{catalogue}}

Choose the ingredients and their PROPORTIONS. Output JSON only.

⛔ Every ingredient_id MUST appear in the lists above, copied exactly. Never
invent an id and never use an ingredient that is not listed.

⭐ AN INGREDIENT THE BREWER ASKED FOR THAT HAS NO CATALOGUE ID GOES IN
"uncatalogued_additions" -- by its real name, with the amount, the unit, the
stage and the method for using it. NEVER put it in "items" under some other
ingredient's id. A malt is not a substitute for a spice.

That list is a real part of the recipe and it is printed on the brewer's sheet.
It is where vanilla beans, coffee, spices, oak, fruit and spirits belong when
the catalogue has no row for them. Give the amount a brewer would actually use
-- two vanilla beans, 200 ml of rum -- and say in "method" how it is prepared
and added, because that is the part the brewer cannot look up from a weight.

⛔ Do NOT state a gravity, ABV, IBU, colour or efficiency anywhere. Those are
computed from your choices after you answer. Your amounts set PROPORTIONS only;
the mashed grain is scaled afterwards to hit the target strength.

⛔ BUILD THE GRAIN BILL IN THIS ORDER. Take the ROAST MALTS fraction FIRST, then
caramel, then fill whatever remains with base malt. Doing it the other way round
leaves nothing for the roast malts and produces a pale beer wearing a dark name.
  1. ROAST MALTS -- for a stout or porter, 8-15% of the grain bill. BOTH ENDS
     ARE BINDING. Below 8% it is a brown ale wearing the wrong name; above 15%
     it turns acrid and thin, and 15% is a ceiling you never cross -- not even
     when a correction below tells you the beer came out too pale. If you are
     already at 15% and still short of colour, move to a DARKER roast malt from
     the list rather than adding more of the one you have. A pale style takes
     none.
  2. CARAMEL malts -- sweetness and body, never colour. Keep them under 20%.
  3. BASE malt -- the remainder. Around 70-85% in a pale beer, and lower in a
     dark one. This is the figure that gives way, not the roast fraction.
Colour comes from the ROAST MALTS list and nowhere else. A malt with "dark" or
"brown" in its name is not a roast malt -- the lists already sort that out, so
trust the heading, not the name.

⛔ THE "avoid" LIST IS BINDING, BUT EACH ENTRY CONSTRAINS ONLY WHAT IT NAMES.
An entry about roast, colour or astringency constrains the ROAST MALTS. An entry
naming an ingredient means leave that ingredient out. An entry about malt must
NOT change the hop schedule. Read each entry for what it says and nothing more.

⛔ HOPS. Give the beer a 60 min bittering addition -- that is what creates
bitterness, a 10 or 15 min addition creates almost none. You may add a SECOND
hop late (10-20 min) for flavour where the style wants it.

⛔ SIZE THE BITTERING CHARGE BY BATCH VOLUME AND BY ALPHA. Both, every time.
  - Start from 0.5 g per LITRE of batch for a hop around 5% alpha.
  - Multiply by batch_size_l. A 5 L batch takes a fifth of what a 25 L batch
    takes. This is the step most often skipped, and it is the expensive one.
  - Then divide by (alpha / 5). A 12.5% alpha hop needs LESS THAN HALF the grams
    of a 5% one for the same bitterness. The catalogue lists each hop's alpha.
  - A gently bittered style takes half of that; an aggressively hoppy one twice.
  ⛔ Worked example of the failure: 25 g of Magnum at 12.5% alpha in a 5 L batch
  is 5 g per litre of a high-alpha hop -- roughly TEN times too much, and it was
  measured. The correct charge there is about 1 g. Late flavour hops are not
  bound by this; they contribute almost no bitterness whatever their weight.

  THE ONE EXCEPTION: if "avoid" names HOPS or BITTERNESS specifically -- and only
  then -- there is no 60 min addition at all. Use a single 10-15 min hop, at most
  10 g per 10 L of batch. Nothing else in "avoid" triggers this.

⛔ IF THE REQUEST CONTRADICTS ITSELF, SAY SO IN "conflicts". Some briefs cannot
be satisfied: a beer cannot be jet-black while using no roasted or dark malts,
because colour of that depth comes only from roast malts. Name the conflict in
plain words, then build the closest honest beer you can and let "conflicts"
carry the caveat. ⛔ Never satisfy one half and describe it as satisfying both.
Putting black malt into a beer specified to have none, and calling it "without
roasted or dark malts", is the worst answer available to you.

{{correction}}

Fields:
- items: array of {ingredient_id, stage, qty_g, unit, timing_min, notes}
  - stage: one of "mash", "boil", "whirlpool", "dryhop", "fermenter", "packaging".
  - qty_g: the amount. Whole numbers, and at least 1.
  - unit: "g" for anything weighed, which is nearly everything. "each" only for
    a catalogue item that is genuinely counted rather than weighed.
  - timing_min: REQUIRED for every hop and every boil addition -- minutes before
    the end of the boil. 60 for the bittering charge; see the hop rule above.
  - notes: at most 12 words saying what that ingredient is doing.
  - Sugars and lactose go in at "boil" late, never in the mash.
  - Always include at least one hop. Even a sweet stout needs a little balance.
- mash_temp_c: a single number. Higher leaves more unfermentable body.
- attenuation: apparent attenuation as a decimal (0.72 = 72%). Lower finishes sweeter.
- not_available: array of things the brewer asked for that are in neither the
  catalogue nor "uncatalogued_additions" -- things you could not place at all.
  ⛔ An ingredient you put in "uncatalogued_additions" is NOT unavailable. You
  placed it. Do not name it here as well.
- uncatalogued_additions: array of {name, qty, unit, stage, timing_days, method}
  - name: the real ingredient, as the brewer would write it on a shopping list.
  - qty and unit: BOTH REQUIRED, never null. unit is "g", "ml" or "each".
  - stage: the same six stages as items.
  - timing_days: days at that stage, for a fermenter or packaging addition.
  - method: how it is prepared and added. This is the useful part -- "split and
    scraped, macerated in 100 ml dark rum for two weeks" tells the brewer
    something a weight never can.
  - Empty array if the brewer asked for nothing outside the catalogue.
- conflicts: array of plain sentences, each naming one way the request cannot be
  satisfied as written. Empty array if the request is coherent.
- rationale: one sentence, at most 30 words, on the shape of the grist.
$body$, false, 'v8: opens "uncatalogued_additions" -- the slot for an ingredient the brewer asked for that has no catalogue id. Measured 2026-09-16: substitution and malt-in-fermenter both 1/6 on v7, both 0/6 with this plus the matching schema. qty and unit are required; the practice block that gives them an evidence basis is not wired yet.')
ON CONFLICT (name, version) DO NOTHING;

UPDATE obs.prompts SET active = false WHERE name = 'formulate.recipe/propose';
UPDATE obs.prompts SET active = true  WHERE name = 'formulate.recipe/propose' AND version = 8;


-- ---------------------------------------------------------------------------
-- ⭐ propose v9: the catalogue grew by 140 rows, so the prompt has to say what
-- they are for.
--
-- 31_brew_misc.sql, 32_brew_sugars.sql and 33_brew_yeast.sql added 14 misc,
-- 6 water_agent, 8 adjunct, 4 flaked fermentable and 120 yeast rows. ⛔ Rows
-- alone change nothing: brew.f_catalogue returns role = kind for everything that
-- is not a fermentable, and `Build propose pack`'s SECTIONS array listed five
-- roles, so every one of those rows was rendered into exactly nothing. That node
-- now throws on an unlisted role rather than quietly dropping it.
--
-- ⭐ WHAT THE YEAST ROWS ACTUALLY BUY. Until now `attenuation` was a number the
-- model invented and FG was an estimate resting on it -- the sheet said as much,
-- printing "no yeast in the catalogue -- pick your own". A strain picked from
-- the list carries its own measured attenuation, and `Validate proposal` uses
-- THAT, ignoring whatever the model reported. Same move brew.f_catalogue made
-- deriving malt role from published colour rather than from the malt's name:
-- take the judgement out of the model and read it off the thing itself.
--
-- ⚠️ The attenuation figures are corpus self-reported -- attrs.provenance says
-- so on every row -- spot-checked against manufacturer datasheets for the
-- strains that carry the weight: US-05 81%, S-04 75%, WLP002 66.5%, W-34/70 83%.
-- §7 Q1 is still open and this is option (a), the plan's own recommendation,
-- acted on rather than decided.
--
-- ⚠️ A flavouring with an id belongs in "items", not in "uncatalogued_additions".
-- The slot v8 opened is for what the catalogue genuinely cannot hold, and it
-- gets smaller every time the catalogue grows. Both paths print on the sheet.
-- ---------------------------------------------------------------------------
INSERT INTO obs.prompts (name, version, body, active, notes) VALUES
('formulate.recipe/propose', 9, $body$

You are formulating a grain bill and hop schedule for an experienced homebrewer.

Their request:
{{question}}

The brief:
{{spec}}

Passages from the brewer's library -- use these for TECHNIQUE decisions (mash
temperature, when to add an adjunct, what builds body in this style):
{{passages}}

What brewers ACTUALLY do for this style, from 174,000 self-reported homebrew
recipes -- percentages are share of the grain bill, hop figures are grams per
litre of batch:
{{practice}}

⛔ THE PRACTICE BLOCK IS EVIDENCE, NOT INSTRUCTION, AND ITS NAMES ARE NOT IDS.
Those ingredient names come from a different catalogue than yours -- "American -
Pale 2-Row" is not in your list and has no id. Use the block for PROPORTIONS and
for which KIND of ingredient belongs in this beer; take every id from the
catalogue below and nowhere else. If the block names something you have no
equivalent for, ignore it rather than reaching for the nearest-sounding entry.

⛔ It records what people DID, which is not what is correct. A thing 60% of
brewers do can still be wrong, and the passages above are what say whether it
is. Where the passages and the practice block disagree, follow the passages.
Where the block is absent or says it was widened to a different beer, ignore it
completely and build from the rules below.

The ONLY ingredients you may use, grouped by what they do:
{{catalogue}}

Choose the ingredients and their PROPORTIONS. Output JSON only.

⛔ Every ingredient_id MUST appear in the lists above, copied exactly. Never
invent an id and never use an ingredient that is not listed.

⭐ AN INGREDIENT THE BREWER ASKED FOR THAT HAS NO CATALOGUE ID GOES IN
"uncatalogued_additions" -- by its real name, with the amount, the unit, the
stage and the method for using it. NEVER put it in "items" under some other
ingredient's id. A malt is not a substitute for a spice.

That list is a real part of the recipe and it is printed on the brewer's sheet.
It is where vanilla beans, coffee, spices, oak, fruit and spirits belong when
the catalogue has no row for them. Give the amount a brewer would actually use
-- two vanilla beans, 200 ml of rum -- and say in "method" how it is prepared
and added, because that is the part the brewer cannot look up from a weight.

⛔ Do NOT state a gravity, ABV, IBU, colour or efficiency anywhere. Those are
computed from your choices after you answer. Your amounts set PROPORTIONS only;
the mashed grain is scaled afterwards to hit the target strength.

⛔ BUILD THE GRAIN BILL IN THIS ORDER. Take the ROAST MALTS fraction FIRST, then
caramel, then fill whatever remains with base malt. Doing it the other way round
leaves nothing for the roast malts and produces a pale beer wearing a dark name.
  1. ROAST MALTS -- for a stout or porter, 8-15% of the grain bill. BOTH ENDS
     ARE BINDING. Below 8% it is a brown ale wearing the wrong name; above 15%
     it turns acrid and thin, and 15% is a ceiling you never cross -- not even
     when a correction below tells you the beer came out too pale. If you are
     already at 15% and still short of colour, move to a DARKER roast malt from
     the list rather than adding more of the one you have. A pale style takes
     none.
  2. CARAMEL malts -- sweetness and body, never colour. Keep them under 20%.
  3. BASE malt -- the remainder. Around 70-85% in a pale beer, and lower in a
     dark one. This is the figure that gives way, not the roast fraction.
Colour comes from the ROAST MALTS list and nowhere else. A malt with "dark" or
"brown" in its name is not a roast malt -- the lists already sort that out, so
trust the heading, not the name.

⛔ THE "avoid" LIST IS BINDING, BUT EACH ENTRY CONSTRAINS ONLY WHAT IT NAMES.
An entry about roast, colour or astringency constrains the ROAST MALTS. An entry
naming an ingredient means leave that ingredient out. An entry about malt must
NOT change the hop schedule. Read each entry for what it says and nothing more.

⛔ PICK EXACTLY ONE YEAST, from the YEAST list, and stage it at "fermenter"
with qty_g 1 and unit "each". Choose it for the STYLE: a lager strain for a
lager, a saison or Belgian strain for those, a clean ale strain otherwise. The
attenuation figure beside each strain is what the beer will actually finish at,
so pick a low one for a sweet beer and a high one for a dry one. ⛔ Never two.
⛔ The number you put in "attenuation" is IGNORED once you pick a strain -- the
strain's own figure is used -- so choose the strain that finishes where you want
the beer to finish rather than trying to state the number yourself.

⛔ FLAVOURINGS, SPICES, OAK AND FRUIT HAVE IDS NOW. If one of the lists above
has what the brewer asked for, use its id in "items" with a unit: "each" for
things that are counted, "g" for things that are weighed. Only something in NO
list goes in "uncatalogued_additions".

⛔ WATER SALTS: leave them out entirely unless the brewer asked about water.

⛔ HOPS. Give the beer a 60 min bittering addition -- that is what creates
bitterness, a 10 or 15 min addition creates almost none. You may add a SECOND
hop late (10-20 min) for flavour where the style wants it.

⛔ SIZE THE BITTERING CHARGE BY BATCH VOLUME AND BY ALPHA. Both, every time.
  - Start from 0.5 g per LITRE of batch for a hop around 5% alpha.
  - Multiply by batch_size_l. A 5 L batch takes a fifth of what a 25 L batch
    takes. This is the step most often skipped, and it is the expensive one.
  - Then divide by (alpha / 5). A 12.5% alpha hop needs LESS THAN HALF the grams
    of a 5% one for the same bitterness. The catalogue lists each hop's alpha.
  - A gently bittered style takes half of that; an aggressively hoppy one twice.
  ⛔ Worked example of the failure: 25 g of Magnum at 12.5% alpha in a 5 L batch
  is 5 g per litre of a high-alpha hop -- roughly TEN times too much, and it was
  measured. The correct charge there is about 1 g. Late flavour hops are not
  bound by this; they contribute almost no bitterness whatever their weight.

  THE ONE EXCEPTION: if "avoid" names HOPS or BITTERNESS specifically -- and only
  then -- there is no 60 min addition at all. Use a single 10-15 min hop, at most
  10 g per 10 L of batch. Nothing else in "avoid" triggers this.

⛔ IF THE REQUEST CONTRADICTS ITSELF, SAY SO IN "conflicts". Some briefs cannot
be satisfied: a beer cannot be jet-black while using no roasted or dark malts,
because colour of that depth comes only from roast malts. Name the conflict in
plain words, then build the closest honest beer you can and let "conflicts"
carry the caveat. ⛔ Never satisfy one half and describe it as satisfying both.
Putting black malt into a beer specified to have none, and calling it "without
roasted or dark malts", is the worst answer available to you.

{{correction}}

Fields:
- items: array of {ingredient_id, stage, qty_g, unit, timing_min, notes}
  - stage: one of "mash", "boil", "whirlpool", "dryhop", "fermenter", "packaging".
  - qty_g: the amount. Whole numbers, and at least 1.
  - unit: "g" for anything weighed, which is nearly everything. "each" only for
    a catalogue item that is genuinely counted rather than weighed.
  - timing_min: REQUIRED for every hop and every boil addition -- minutes before
    the end of the boil. 60 for the bittering charge; see the hop rule above.
  - notes: at most 12 words saying what that ingredient is doing.
  - Sugars and lactose go in at "boil" late, never in the mash.
  - Always include at least one hop. Even a sweet stout needs a little balance.
- mash_temp_c: a single number. Higher leaves more unfermentable body.
- attenuation: apparent attenuation as a decimal (0.72 = 72%). A fallback only,
  used if you picked no yeast; the chosen strain's own figure wins.
- not_available: array of things the brewer asked for that are in neither the
  catalogue nor "uncatalogued_additions" -- things you could not place at all.
  ⛔ An ingredient you put in "uncatalogued_additions" is NOT unavailable. You
  placed it. Do not name it here as well.
- uncatalogued_additions: array of {name, qty, unit, stage, timing_days, method}
  - name: the real ingredient, as the brewer would write it on a shopping list.
  - qty and unit: BOTH REQUIRED, never null. unit is "g", "ml" or "each".
  - stage: the same six stages as items.
  - timing_days: days at that stage, for a fermenter or packaging addition.
  - method: how it is prepared and added. This is the useful part -- "split and
    scraped, macerated in 100 ml dark rum for two weeks" tells the brewer
    something a weight never can.
  - Empty array if the brewer asked for nothing outside the catalogue.
- conflicts: array of plain sentences, each naming one way the request cannot be
  satisfied as written. Empty array if the request is coherent.
- rationale: one sentence, at most 30 words, on the shape of the grist.
$body$, false, 'v9: the catalogue gained 120 yeast strains, 14 misc, 6 water salts and 12 sugars/flaked cereals, so the prompt names them. One yeast, staged at fermenter, chosen for the style -- and its catalogued attenuation overrides whatever the model reports, which is what stops FG being a guess. A flavouring WITH an id now belongs in items, not in the v8 slot.')
ON CONFLICT (name, version) DO NOTHING;

UPDATE obs.prompts SET active = false WHERE name = 'formulate.recipe/propose';
UPDATE obs.prompts SET active = true  WHERE name = 'formulate.recipe/propose' AND version = 9;
