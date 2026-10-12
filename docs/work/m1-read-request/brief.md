# M1 · Step 1: read the request (and choose the chat model, D2)

Status: draft
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
- Brief check (WORKFLOW-ROADMAP §3): the naming rule for ingredients and a `named` field in the
  20 briefs (Open questions 1 and 2), reviewed by you.

Out:
- Mapping words to `ref` ids (M5 does that through a resolver). Choosing a style (M2). Asking the
  user follow-up questions (M8). Prompt tricks beyond one clear system prompt and the contract.

## Requirements
R1. Step 1 outputs, for every request: `named` (style words the user used, or null), `stated`
    (only `batch_l`, `abv`, `og`, `ibu`, `srm`, only numbers the user said), `hints` (only words
    from the RECIPE-ROADMAP §7 table), `wanted`, `excluded`, `inventory` (ingredient words),
    `guidance` (true unless the user said to ignore the style), and `unknown` (anything asked for
    that fits no field).
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
    model: briefs with every field right (per run), accuracy per field, median and p90 seconds
    per call, and whether it ran fully on the GPU.
R7. The benchmark result is saved in this work folder (`benchmark.md`) and D2 moves from
    PROJECT.md §7 to §4 with its *why*.
R8. `evals/recipe_briefs.toml` gains the `named` field for all 20 briefs (and any naming rule from
    Open question 1), reviewed and approved by you; `tests/test_recipe_briefs.py` allows the field.

## Constraints
- PROJECT.md §6.2: one narrow LLM call with a checkable contract, not a recipe prompt.
- §6.3: the contract has `unknown` and null slots so the model is never pushed to invent.
- §6.1: the LLM never reads or writes a style range or an ingredient spec here.
- Ollama is local; no cloud model (PROJECT.md §2 non-goals). Speed is second to quality for D2
  (user, 2026-10-11).
- n8n-skills rules for the LLM node (`n8n-agents-official`).

## Assumptions
- `qwen3.8:27b` (17 GB) runs partly on the CPU with 16 GB VRAM *(unverified; measured by R6)*.
- Ollama's structured output (a JSON schema in the request) works with all three candidates
  *(unverified)*.

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
A6. `benchmark.md` holds the R6 table for at least `qwen3.8:27b`, `gemma4:12b-it-q8_0` and
    `gemma4:12b`; PROJECT.md §4 names the chosen model and §7 no longer lists D2 (R6, R7).
A7. `tests/test_recipe_briefs.py` passes with the `named` field in all 20 briefs (R8).

## Open questions
1. How are ingredient words graded against the briefs? The briefs use generic names (`flaked
   rice`), requests sometimes shorter words ("a bit of rice"). — options: a) step 1 keeps the
   user's words; the grader accepts a match by a small synonym list in the harness (`rice` ≈
   `flaked rice`); b) step 1 must output the canonical word from the briefs — recommend a: step 1
   stays a faithful reader, and M5's resolver does the mapping to `ref`.
2. Add `named` to the briefs? — options: a) yes, for all 20 (M2's mismatch check needs it); b) no,
   leave it ungraded — recommend a.
3. Which models besides the three pulled ones? — options: a) only the three; b) add one or two
   that fit 16 GB VRAM, named by you — recommend b if you have a candidate, else a.
4. What if no model reaches 19/20? — options: a) look at the failing fields first (prompt vs
   contract vs a genuinely ambiguous brief), then decide; b) lower the bar — recommend a.

## Deviations
