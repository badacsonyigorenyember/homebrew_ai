# D2 model research: which local models to benchmark for step 1

Checked 2026-10-12, for [brief.md](brief.md) R6. Nothing was pulled. Step 1 is a short
structured extraction (one request of 1–3 sentences in, a small JSON object out), and the user
puts quality before speed, so models that partly run on the CPU are in.

## This machine (measured)

- GPU: Radeon RX 9070 XT (gfx1201), 15.9 GiB VRAM as Ollama reports it, ROCm 7.2 inside Ollama
  0.34.0. The Raphael iGPU (512 MiB) is dropped on purpose ([OPERATIONS.md](../../OPERATIONS.md) §6).
- RAM: 30 GiB usable, about 11 GiB used with the stack running (`free -h`), so about 18 GiB is
  left for layers that spill out of VRAM. CPU: Ryzen 9 9900X, 12 cores / 24 threads.
- Ollama: `OLLAMA_NUM_PARALLEL=1`, `OLLAMA_KEEP_ALIVE=-1`, `OLLAMA_MAX_LOADED_MODELS=2`.
  394 GB free on the model volume.

Pulled models, each loaded alone at 8K context with `ollama ps` read afterwards, then unloaded:

| Tag | Params | Quant | Size | Fit at 8K context |
|---|---|---|---|---|
| `qwen3.8:27b` (= `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q4_K_M`) | 27.3B dense | Q4_K_M | 17 GB | 15 % CPU / 85 % GPU (measured) |
| `gemma4:12b-it-q8_0` | 11.9B dense | Q8_0 | 12 GB (13 GB loaded) | 100 % GPU (measured) |
| `gemma4:12b` | 11.9B dense | Q4_K_M | 7.6 GB | 100 % GPU *(not loaded; smaller than the q8_0)* |

`KEEP_ALIVE=-1` keeps a model loaded after use and two can be loaded at once, so a second model
gets less VRAM. The "ran fully on the GPU" column in R6 is only true if each candidate is
measured with nothing else loaded.

## What quantisation costs

- On a 27B model, Q4_K_M is within about half a point of Q8_0. Unsloth's MMLU table for Gemma 3
  27B: Q4_K_M 71.2, Q5_K_M 71.8, Q6_K 71.9, Q8_0 71.6, BF16 71.5 (disk 15.4 / 18.0 / 20.6 /
  26.7 GB). KL divergence of their Q4_K_XL against BF16 is 0.024 ([Unsloth][unsloth-dyn]).
  No such table exists for Qwen3.8 or Gemma 4 in text form.
- Smaller models are generally said to lose more per bit *(unverified for Gemma 4 12B)*. The
  pulled `gemma4:12b` / `gemma4:12b-it-q8_0` pair measures exactly that on our 20 briefs.
- QAT tags (`-it-qat`) come from Google's quantisation-aware training, so the 4-bit weights are
  trained for 4 bits instead of rounded afterwards. That should put them closer to BF16 than a
  plain Q4_K_M of the same size *(unverified for Gemma 4)*.
- Offload cost: a dense model runs every token through the CPU layers, so speed falls roughly
  with the share on the CPU. A mixture-of-experts (MoE) model only touches its few active experts
  per token, so spilled experts cost much less. Step 1 writes maybe 100–200 tokens per call, so
  even 5 tokens/s is under a minute per brief *(estimate; R6 measures it)*.

## Public benchmarks

There is no public benchmark of short JSON-schema extraction for models in this class. The
closest are instruction following and tool calling, and the sources disagree in places.

- A 24 GB-card test with all three at Q4_K_M (Aug 2026): instruction following Gemma 4 31B
  44/50, Qwen3.8-27B 43/50; single tool calls 90/90 for both; multi-step tool runs Gemma 30/30,
  Qwen3.8 28/30. The author recommends Gemma for "short, schema-bound contracts" ([kingy.ai][kingy]).
- BenchLM, marked "directional": instruction following Gemma 4 26B-A4B 88.7, Qwen3.8-27B 86.9
  ([BenchLM][benchlm]).
- Gemma 4 model card: 31B 84.3 vs 26B-A4B 82.3 on a line whose benchmark is not named
  ([Google][gemma-card]).
- 16 GB guide (Aug 2026): `gemma4:26b-a4b` QAT is the "daily default" for 16 GB cards, about
  15 GB in VRAM at 8–16K context with a quantised KV cache ([runaihome][runaihome]).
- Ollama structured outputs: pass the JSON schema in `format`, also put the schema in the
  prompt, use temperature 0. The docs do not say how `think` interacts with `format`
  ([Ollama docs][ollama-so]). All candidates below are thinking models.

## Extra candidates (all three chosen by the user, 2026-10-12)

| # | Tag | Params | Quant | Size | Expected fit at 8K | Why |
|---|---|---|---|---|---|---|
| 1 | `gemma4:31b-it-qat` | 31B dense | QAT 4-bit | 19 GB | partial offload, about 20 % CPU *(estimate)* | Strongest Gemma 4; best instruction following and tool calls in the 24 GB test; QAT keeps 4-bit close to full precision. |
| 2 | `gemma4:26b-a4b-it-qat` | 25.2B MoE, 3.8B active | QAT 4-bit | 16 GB | nearly all on GPU, a little offload likely *(estimate)* | Different architecture; MoE spills cheaply; directional instruction-following score above Qwen3.8. |
| 3 | `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q6_K` | 27B dense | Q6_K | 22 GB | partial offload, about 30 % CPU *(estimate)* | Same model as the pulled Q4_K_M, so it answers "does q6 beat q4 here" directly. |

The largest (22 GB) leaves about 7 GB in system RAM, well inside the 18 GiB that is free with the
stack up. Together the three need about 57 GB of disk.

## Considered, not proposed

- `qwen3.8:27b-q8_0` (30 GB): about 14 GB would sit in RAM, close to what is free with the stack
  up, and dense offload that large is slow. The Gemma 3 table shows little gain from Q6 to Q8.
- `gemma4:26b-a4b-it-q8_0` (28 GB): MoE, so the offload is cheaper, but 12 GB or more in RAM.
  Worth a look later only if the QAT build lands just under the bar.
- `gemma4:31b-it-q4_K_M` (20 GB): same size class as the QAT tag, which should be the better 4-bit.
- `gpt-oss:20b` (13 GB, fits fully): a popular 16 GB pick, but a generation older (Aug 2025)
  than Gemma 4 and Qwen3.8, so it is unlikely to beat them.
- Qwen3.6-27B / 35B-A3B: older than Qwen3.8 and behind it on tool calls in the 24 GB test.
- `qwen3.8-flash-next` (125B MoE) and the other large new models on ollama.com: do not fit.

## Sources

- [Ollama library: gemma4 tags](https://ollama.com/library/gemma4/tags),
  [qwen3.8 tags](https://ollama.com/library/qwen3.8/tags)
- [unsloth/Qwen3.8-27B-GGUF](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF),
  [unsloth/gemma-4-26B-A4B-it-GGUF](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF),
  [unsloth/gemma-4-31B-it-GGUF](https://huggingface.co/unsloth/gemma-4-31B-it-GGUF)
- [Unsloth Dynamic GGUFs: quant benchmarks][unsloth-dyn]
- [Qwen3.8 vs Qwen3.6 vs Gemma 4: 24GB GPU test (kingy.ai)][kingy]
- [BenchLM: Gemma 4 26B A4B vs Qwen3.8-27B][benchlm]
- [Gemma 4 model card][gemma-card]
- [Best local LLMs for 16GB VRAM in 2026 (runaihome)][runaihome]
- [Ollama docs: structured outputs][ollama-so]

[unsloth-dyn]: https://unsloth.ai/docs/basics/unsloth-dynamic-2.0-ggufs
[kingy]: https://kingy.ai/blog/qwen3-8-27b-vs-qwen3-6-27b-vs-gemma-4-31b/
[benchlm]: https://benchlm.ai/compare/gemma-4-26b-a4b-vs-qwen3-8-27b
[gemma-card]: https://ai.google.dev/gemma/docs/core/model_card_4
[runaihome]: https://www.runaihome.com/blog/best-local-llm-16gb-vram-2026/
[ollama-so]: https://docs.ollama.com/capabilities/structured-outputs
