# M1 · Step 1: read the request (and choose the chat model, D2)

Status: approved
Slug: m1-read-request · Branch: m1-read-request
Roadmap: [WORKFLOW-ROADMAP.md](../../WORKFLOW-ROADMAP.md) M1, checkpoint **G1** ·
[RECIPE-ROADMAP.md](../../RECIPE-ROADMAP.md) §3 step 1, §7
Needs: `m0-harness` shipped

## Why
Step 1 is one of only two LLM steps in the pipeline. Every later step works from its output, so a
missed number or a wrong hint here shows up as a wrong recipe much later, where it is hard to
trace. The 20 briefs already hold the expected step 1 output for each request (`stated`,
`hints`, `wanted`, `excluded`, `inventory`, `guidance`), which also makes this the right place
to benchmark the chat model (D2, PROJECT.md §7).

## Goal
The pipeline turns each request into a brief JSON that code has checked against the step 1
contract, stored in `app.brief`. On the chosen model, at least 19 of 20 briefs get every graded
field right, three runs in a row. D2 is decided.

## Scope
In:
- Step 1 sub-workflow: request text → LLM → brief JSON → contract check → `app.brief` row and
  `run_step` row.
- Capturing the style the user named, in their own words (e.g. "imperial stout"), for step 2.
- The D2 benchmark on the same 20 briefs, and the decision.
- Brief check (WORKFLOW-ROADMAP §3): the ingredient naming rule (R1, R9) applied to the expected
  words in the 20 briefs, and a `named` field in all 20, reviewed by you.
- Model research for D2: [model-research.md](model-research.md) names the extra candidates.

Out:
- Mapping words to `ref` ids (M5 does that through a resolver). Choosing a style (M2). Asking the
  user follow-up questions (M8). Prompt tricks beyond one clear system prompt and the contract.

## Requirements
R1. Step 1 outputs, for every request: `named` (style words the user used, or null), `stated`
    (only `batch_l`, `abv`, `og`, `ibu`, `srm`, only numbers the user said), `hints` (only words
    from the RECIPE-ROADMAP §7 table), `wanted`, `excluded`, `inventory` (ingredient words),
    `guidance` (true unless the user said to ignore the style), and `unknown` (anything asked for
    that fits no field).
    Ingredient words are the user's own words. Amount words are not part of them ("a bit of
    rice" → `rice`, "a bag of dark candi sugar" → `dark candi sugar`). Form or condition words
    are part of them and stay ("flaked", "ground", "torrified", "malted": `flaked rice` is a
    different ingredient from `rice`). Mapping words to `ref` stays with M5's resolver.
R2. Code checks the LLM output against the step 1 contract: field names and types, hints only from
    the vocabulary, numbers in plausible bounds (e.g. ABV 0–20 %, OG 1.000–1.200, batch 1–1000 L).
    An output that fails is retried once with the error; a second failure ends the run with
    `ok = false`, not with a guessed brief.
R3. No number appears in `stated` that is not in the request text (checked by code).
R4. The step stores the request and the checked brief in `app.brief` (`request_text`, `brief`,
    `guidance_on`) and logs the step with model, time and tokens in `run_step`.
R5. The LLM call is reproducible: fixed temperature 0 (or the model's lowest), fixed seed where
    the runtime supports it, and the model name recorded in `app.run.model`.
R6. The D2 benchmark runs the 20 briefs three times on each candidate model and reports, per
    model (tag and quantisation): briefs with every field right (per run), accuracy per field,
    median and p90 seconds per call, and the CPU/GPU split from `ollama ps` with no other model
    loaded. Candidates: the three pulled models (`qwen3.8:27b`, `gemma4:12b-it-q8_0`,
    `gemma4:12b`) and three more from [model-research.md](model-research.md), pulled as part of
    this work: `gemma4:31b-it-qat`, `gemma4:26b-a4b-it-qat` and
    `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`. Every model runs with thinking off; the best one
    then runs the three passes again with thinking on, and both results are reported. Speed
    only breaks a tie in quality.
R7. The benchmark result is saved in this work folder (`benchmark.md`) and D2 moves from
    PROJECT.md §7 to §4 with its *why*. If no candidate reaches the bar (A1), `benchmark.md`
    sorts every failing field into prompt, contract or an ambiguous brief, and you decide from
    that; the bar is not lowered without you.
R8. `evals/recipe_briefs.toml` gains the `named` field for all 20 briefs, and its expected
    `wanted`, `excluded` and `inventory` words follow R1's naming rule. Today five briefs expect
    a word the user did not write: b02 `flaked oats` (user: "oats"), b06 `flaked rice`
    ("rice"), b07 `flaked corn` ("corn"), b16 `flaked rice` ("a bit of rice"), b10 `candi sugar`
    and `abbey ale yeast` ("a bag of dark candi sugar", "a pack of abbey yeast"). They change
    to the user's words: b02 `oats`, b06 `rice`, b07 `corn`, b16 `rice`, b10 `dark candi sugar`
    and `abbey yeast` ("dark" is a type word and stays). `needs` keeps its generic names (later steps use
    it). `tests/test_recipe_briefs.py` allows the new field.
R9. The grader compares ingredient words ignoring case, spacing and accents, plus a small synonym
    list in the harness for naming variants only. It never counts a word with a form or
    condition word as equal to one without it (`rice` ≠ `flaked rice`), and amount words never
    reach it (R1).

## Constraints
- PROJECT.md §6.2: one narrow LLM call with a checkable contract, not a recipe prompt.
- §6.3: the contract has `unknown` and null slots so the model is never pushed to invent.
- §6.1: the LLM never reads or writes a style range or an ingredient spec here.
- Ollama is local; no cloud model (PROJECT.md §2 non-goals). Speed is second to quality for D2
  (user, 2026-10-11).
- n8n-skills rules for the LLM node (`n8n-agents-official`).
- Hardware: RX 9070 XT (16 GB VRAM, ROCm), 32 GB RAM, about 18 GiB free with the stack up. Do not
  set `HSA_OVERRIDE_GFX_VERSION` (OPERATIONS.md §6). Only the six models in R6 are pulled or run.

## Assumptions
- Measured 2026-10-12 at 8K context: `qwen3.8:27b` (Q4_K_M) runs 15 % CPU / 85 % GPU,
  `gemma4:12b-it-q8_0` 100 % GPU.
- The fit of the three extra candidates (model-research.md) is estimated from file size
  *(unverified; measured by R6)*.
- Ollama's structured output (a JSON schema in `format`) works with every candidate, also with
  thinking on *(unverified; the Ollama docs do not cover `think` with `format`)*.
- Gemma 4 QAT tags lose less quality than a plain Q4_K_M of the same size *(unverified)*.

## Acceptance criteria
A1. On the chosen model, the runner shows ≥ 19/20 briefs with every graded field right, in each
    of 3 runs (R1, R2, G1 bar).
A2. b05 gives `stated.abv = 4` and `named` "imperial stout"; b18 gives `guidance = false`; b08
    gives `excluded` Saaz and `stated` 10 L and 50 IBU (R1).
A3. A request with an unknown hint word ("make it funky") puts the word in `unknown`, not in
    `hints` (R1, R2).
A4. A mocked LLM answer with a made-up number fails R3's check and the run stops with
    `ok = false` (R2, R3).
A5. Each run leaves one `app.brief` row and a `run_step` row with model, ms and tokens (R4, R5).
A6. `benchmark.md` holds the R6 table for `qwen3.8:27b`, `gemma4:12b-it-q8_0`, `gemma4:12b`,
    `gemma4:31b-it-qat`, `gemma4:26b-a4b-it-qat` and `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`
    with thinking off, plus the best of them with thinking on; PROJECT.md §4 names the chosen model and §7 no
    longer lists D2 (R6, R7). If no model reaches A1, every failing field in `benchmark.md` has
    its cause class (R7).
A7. `tests/test_recipe_briefs.py` passes with the `named` field in all 20 briefs, and b02, b06,
    b07, b10 and b16 hold the user's words listed in R8 (R8).
A8. A harness test: `rice` graded against `flaked rice` is wrong, `Flaked Rice` against
    `flaked rice` is right, and a synonym pair from the harness list is right (R9).

## Open questions
None open. Answered 2026-10-12: step 1 keeps the user's words (R1, R9); `named` in all 20
briefs, and five briefs change to the user's ingredient words (R8); the three pulled models plus
all three researched extras, thinking off, then the best with thinking on (R6); below the bar,
inspect failures first (R7).

## Deviations
