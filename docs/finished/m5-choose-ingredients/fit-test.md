# Fit test: steps 6-9 in one call (Task 5, R13, A14)

Run 2026-10-19 with `python -m evals.fit_test --num-ctx N --save` on all 24 briefs, the stored step 0/1/2/4
outputs of the s9 runs (`evals/results/2026-10-18-s9.json`), step 5 rebuilt with `app.step5_frame`, model
`hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`, think false, temperature 0, seed 42, `num_predict` 4096. The model was unloaded
before every call, so `prompt_eval_count` is the real prompt size. Results: `evals/results/2026-10-19-m5-fit.json`.

## Decision

**One call for steps 6-9, at `num_ctx` 32768.** (Task 7a.) All 24 briefs fit and, after one prompt revision, all 24 pass the check
within two tries. The per-step shape (Task 7b) is not needed.

## Options

| Option | Prompt | Fits | Passes | Processor split | Median llm_ms |
|---|---|---|---|---|---|
| 8192 | 16,631-26,118 tokens | 0 of 24 | 0 | 36%/64% CPU/GPU | none: Ollama refused every call |
| 16384 | 16,631-26,118 tokens | 0 of 24 | 0 | 38%/62% CPU/GPU | none: refused every call |
| 32768, prompt rev 0 | 16,631-26,569 tokens | 24 of 24 | 22 of 24 | 40%/60% CPU/GPU | 118.0 s |
| 32768, prompt rev 1 | 16,682-26,554 tokens | 24 of 24 | **24 of 24** | 40%/60% CPU/GPU | 117.2 s |

- This Ollama does not truncate an over-long prompt: it answers HTTP 400 `exceed_context_size_error` naming the prompt's token
  count (`rejected` in the results). A refusal counts as a try that does not fit. The prompts are 2-3 times larger than the
  Task 3 character counts suggested (49,546-80,896 characters = 16.6k-26.6k tokens), so neither 8192 nor 16384 comes close.
- Worst case is b18: 26,554 prompt tokens + 4096 output budget = 30,650 of 32,768 (2,118 spare). The longest real answer was
  447 tokens, so the 4096 budget is generous; the prompt is what sets the context.
- Load cost at 32768: `load_ms` about 3.9-4.2 s after an unload (13.7 s for the very first cold load). Step 1 runs at 8192, so
  the step 1 to step 6 switch costs one reload of about 4 s. The call itself takes 88-143 s (median 117 s), prompt evaluation
  dominating, with the model 40%/60% CPU/GPU on the 16 GB GPU.
- `anyOf` with null in `format` (`souring`): Ollama accepted the contract on every call (no error, valid JSON back), so the
  open Task 4 question is answered.

## Prompt revision (1 of at most 2 allowed)

Rev 0 failed two briefs after the retry: b20 (`pct`/`share_pct` of 0, which the contract forbids) and b23 (Black Malt and Roasted
Barley above their 2 % maximum). Rev 1 of `shared/prompts/choose.system.md` adds "every `pct` is above 0 (leave a product out
rather than give it 0)", "every `share_pct` is above 0", and "check this for every dark or roasted malt, and put what is left
over into the base malt". Re-run on all 24: 24 pass. Six briefs (b04, b05, b15, b18, b20, b23) needed the retry; none needed a third try. The
rev 0 results are kept in the results file (`32768-rev0`, `8192-rev0`, `16384-rev0`, with the prompt hash per option).

## Rev 1, per brief (32768)

Tokens and context are of the last try; the context used is prompt tokens + the 4096 output budget.

| Brief | Prompt tokens | Output budget | Context used | Tries | Check | Output tokens | llm s |
|---|---|---|---|---|---|---|---|
| b01 | 19149 | 4096 | 23245 | 1 | pass | 439 | 122 |
| b02 | 21631 | 4096 | 25727 | 1 | pass | 387 | 122 |
| b03 | 23187 | 4096 | 27283 | 1 | pass | 378 | 125 |
| b04 | 24055 | 4096 | 28151 | 2 | pass | 372 | 128 |
| b05 | 24010 | 4096 | 28106 | 2 | pass | 312 | 118 |
| b06 | 19441 | 4096 | 23537 | 1 | pass | 262 | 94 |
| b07 | 19347 | 4096 | 23443 | 1 | pass | 259 | 94 |
| b08 | 19165 | 4096 | 23261 | 1 | pass | 272 | 95 |
| b09 | 16682 | 4096 | 20778 | 1 | pass | 282 | 88 |
| b10 | 19146 | 4096 | 23242 | 1 | pass | 393 | 114 |
| b11 | 20646 | 4096 | 24742 | 1 | pass | 379 | 117 |
| b12 | 21760 | 4096 | 25856 | 1 | pass | 327 | 112 |
| b13 | 17040 | 4096 | 21136 | 1 | pass | 277 | 89 |
| b14 | 23354 | 4096 | 27450 | 1 | pass | 304 | 113 |
| b15 | 23265 | 4096 | 27361 | 2 | pass | 322 | 117 |
| b16 | 21593 | 4096 | 25689 | 1 | pass | 383 | 121 |
| b17 | 19133 | 4096 | 23229 | 1 | pass | 318 | 102 |
| b18 | 26554 | 4096 | 30650 | 2 | pass | 329 | 130 |
| b19 | 21403 | 4096 | 25499 | 1 | pass | 327 | 111 |
| b20 | 23998 | 4096 | 28094 | 2 | pass | 375 | 128 |
| b21 | 22959 | 4096 | 27055 | 1 | pass | 447 | 136 |
| b22 | 19097 | 4096 | 23193 | 1 | pass | 324 | 103 |
| b23 | 25055 | 4096 | 29151 | 2 | pass | 438 | 143 |
| b24 | 21808 | 4096 | 25904 | 1 | pass | 361 | 118 |
