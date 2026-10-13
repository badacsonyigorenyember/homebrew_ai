# D2 benchmark: step 1 (read request)

Measured 2026-10-12 (first three rows) and 2026-10-13 (the rest) with
`python -m evals.benchmark --model <tag> --runs 3 --save`; results in
[`evals/results/2026-10-13-m1-benchmark.json`](../../../evals/results/2026-10-13-m1-benchmark.json).

- Machine: AMD Ryzen 9 9900X, 32 GB RAM, 16 GB VRAM GPU; Ollama in Docker, `num_ctx` 8192,
  temperature 0, seed 42.
- Prompt `shared/prompts/step1.system.md` sha256 `ba3a9ca320b9fd6ccbe32a51b925560a54af91049ee035282c5bf9994b753ec9`;
  contract `shared/contracts/step1.output.schema.json` sha256
  `e304028c1ca1905d0fa566a736fa5c320b850010644f0f67cb7551b327c9f266`. Every row used these two (checked
  against the repo files before and after).
- Bar: 19 of 20 briefs right in every one of 3 runs. 7 configurations: six models thinking off,
  then the best (`pick_best`: `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K`) with thinking on.
- Split = CPU/GPU share from `ollama ps`. Times are the LLM call only (median / p90 over 60 calls).

## Prompt changes made during the Task 4 smoke pass

Both are general rules that quote no brief (gemma4:12b-it-q8_0 went from 15/20 to 17/20):

1. `hints`: a word is added only if the user wrote it or a direct form of it; no inference from the
   purpose or occasion; other wishes go to `unknown`.
2. `stated`: each number is matched to the unit written next to it (litres, %, IBU, SRM, gravity).

The prompt was not changed during Task 6. No synonyms were added in Task 6.

## Results

| model | quant | think | split | all right per run | named | stated | hints | wanted | excluded | inventory | guidance | median s | p90 s | retries |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3.8:27b | Q4_K_M | off | 15%/85% CPU/GPU | 18/20 / 18/20 / 18/20 | 95% | 100% | 95% | 100% | 100% | 100% | 100% | 5.5 | 7.0 | 0 |
| gemma4:12b-it-q8_0 | Q8_0 | off | 100% GPU | 17/20 / 17/20 / 17/20 | 100% | 95% | 90% | 100% | 100% | 100% | 100% | 1.7 | 2.0 | 0 |
| gemma4:12b | Q4_K_M | off | 100% GPU | 16/20 / 16/20 / 16/20 | 100% | 95% | 85% | 100% | 100% | 100% | 100% | 1.6 | 2.2 | 3 |
| gemma4:31b-it-qat | Q4_0 | off | 28%/72% CPU/GPU | 17/20 / 17/20 / 17/20 | 100% | 95% | 90% | 100% | 100% | 100% | 100% | 9.4 | 11.3 | 0 |
| gemma4:26b-a4b-it-qat | Q4_0 | off | 6%/94% CPU/GPU | 12/20 / 13/20 / 13/20 | 95% | 100% | 73% | 95% | 100% | 95% | 90% | 1.3 | 1.5 | 0 |
| hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K | Q6_K | off | 36%/64% CPU/GPU | 19/20 / 19/20 / 19/20 | 100% | 100% | 95% | 100% | 100% | 100% | 100% | 12.5 | 15.6 | 0 |
| hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K | Q6_K | on | 36%/64% CPU/GPU | 19/20 / 19/20 / 19/20 | 100% | 100% | 100% | 95% | 100% | 100% | 100% | 96.7 | 160.1 | 1 |

Median output tokens per call: 53 (gemma4:12b-it-q8_0), 66 (gemma4:12b), 84 (gemma4:31b), 86
(gemma4:26b-a4b), 89 (both Qwen no-think), 721 (Qwen Q6_K thinking on).

## A2: the named cases, per configuration (right in 3 of 3 runs unless shown)

| Configuration | b05 `abv 4` + `named` | b18 `guidance false` | b08 `excluded Saaz` | b08 `batch_l 10`, `ibu 50` |
|---|---|---|---|---|
| qwen3.8:27b (Q4_K_M) | yes | yes | yes | yes |
| gemma4:12b-it-q8_0 | yes | yes | yes | 0/3 |
| gemma4:12b | yes | yes | yes | 0/3 |
| gemma4:31b-it-qat | yes | yes | yes | 0/3 |
| gemma4:26b-a4b-it-qat | yes | yes | yes | yes |
| Qwen3.8-27B UD-Q6_K, think off | yes | yes | yes | yes |
| Qwen3.8-27B UD-Q6_K, think on | yes | yes | yes | yes |

## Result

Two configurations meet the bar, both with 19/20 in all three runs: Qwen3.8-27B UD-Q6_K with
thinking off (12.5 s median, 15.6 s p90, no retries) and with thinking on (96.7 s median, 160.1 s
p90, 1 retry). Thinking on did not raise the count: it fixed b05 `hints` and broke b08 `wanted`.
`pick_best` (most right, then worst run, then median time) chooses the thinking-off one. All
other models are below the bar (best of them: qwen3.8:27b Q4_K_M 18/20). Run counts were identical
across the 3 runs of every model, except gemma4:26b-a4b (12, 13, 13).

## Failing fields of the two configurations that meet the bar

| Config | Brief | Field | What the model returned | Expected | Cause |
|---|---|---|---|---|---|
| Q6_K think off | b05 "4 % imperial stout, something I can drink a few pints of" | `hints` | `["session"]` (3/3 runs) | `[]` | **prompt**: the rule says no inference from purpose or occasion, and the user never wrote "session"; the model still infers it. One could also argue the brief is **ambiguous** ("a few pints" is a session wish in all but name). Not changed without you (R7). |
| Q6_K think on | b08 "pick another noble-type hop" | `wanted` | `["noble-type hop"]` (3/3 runs) | `[]` | **ambiguous brief**: "pick another noble-type hop" is a request the model can fairly read as a wanted ingredient; the contract has no way to say "a hop of this family, chosen by the pipeline". |

Same b05 `hints` miss for qwen3.8:27b (Q4_K_M), which also fails b19 `named` (returns null and puts
"wee heavy" in `unknown`: cause not inspected, probably **prompt**).

## Notes

- Disk: 472 GB free before the pulls, 419 GB after (three models, about 53 GB).
- Placement on the 16 GB GPU: only gemma4:12b models fit fully (100% GPU). Qwen Q6_K runs
  36%/64% CPU/GPU, gemma4:31b 28%/72%, which is why they are slow.
- gemma4:26b-a4b-it-qat is fast (1.3 s) but the least accurate (12-13/20, hints and several
  other fields): it is out on quality.
- gemma4:31b, gemma4:12b-it-q8_0 and gemma4:12b all miss b08 `stated` in 3/3 runs (cause not inspected), b04/b05 `hints` as in the smoke pass.
