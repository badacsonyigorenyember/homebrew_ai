# Recipe pipeline v2 — design, evidence, and what is actually buildable

Written 2026-09-16, against the stack as it ran that day. Every number below was
measured on this machine, not estimated. The measurements are in §1 so the rest
of the document can be argued with.

Goal, in the user's words: *"a perfectly rounded, all-knowing recipe creator …
able to create recipes in any style, with any ingredients."* §2 says which half
of that is reachable and which half is not, and why. §3 onward is the design.

---

## 0. TL;DR

The pipeline is **not** badly designed. It is a good four-stage pipeline that is
starved of three things: a catalogue that covers more than malt and hops, a way
to ask *how* an ingredient is used rather than *whether* it exists, and a guard
against the model filling a gap it has just declared.

Everything the ambitious version needs is already in the building — 174,455
corpus recipes with per-addition stage and timing, a working web arm with search
→ fetch → docling → embed → rank, a versioned prompt registry, an arithmetic
verifier, a declarative eval harness. Almost none of it is wired into
`cap-formulate-recipe`.

The binding constraint is not the model and not the data. It is that **one LLM
call is being asked to satisfy nine simultaneous constraints**, and this repo has
already learned twice — in writing, in `29_brew_formulate.sql` and
`63_model_switch.sql` — that gemma4:12b drops one constraint per two you add.

The fix is not a bigger prompt. It is more, smaller prompts, each with a
machine-checkable contract.

---

## 1. What I measured

### 1.1 The catalogue is malt and hops and nothing else

```
brew.ingredients — 150 rows
  fermentable   77   (Weyermann 44, Viking Malt 33)
                     base 37 · caramel 24 · roast 16
  hop           72   (all have alpha_acid_pct)
  adjunct        1   (Lactose, and it is a DERIVED figure — 28_brew_derived_sugars.sql)
  yeast          0
  misc           0
  water_agent    0
```

`brew.ingredients.kind` **already permits** `'yeast'`, `'misc'` and
`'water_agent'` (CHECK constraint). `potential_ppg` is nullable.
`brew.f_compute_recipe` only reads `fermentable`, `adjunct` and `hop`, so a
`misc` row is arithmetically inert and cannot corrupt OG/IBU/SRM. **There is no
structural obstacle to the missing rows. They were simply never inserted.**

### 1.2 The data the pipeline does not ask for

`corpus.miscs` holds 16,112 distinct flavouring/spice/water-agent names.
`corpus.recipe_misc` holds 141,857 additions with `use_raw` (the stage) and
`time_raw`. Which means the corpus already answers the exact question that got
this started:

```
vanilla — 2,671 additions across 2,206 recipes
  Secondary 1509 · Boil 422 · Primary 341 · Kegging 161 · Bottling 125
  · Mash 50 · Whirlpool 35
  median 2.00 "each" (beans)

rum — 120 additions
  Secondary 83 · Primary 11 · Kegging 11 · Bottling 9 · Boil 4 · Whirlpool 1

poppy seed — 1 recipe. Below every threshold. This one genuinely needs the web.
```

`nlq.ingredient_usage('vanilla', 6)` already returns per-style quartiles today:
Sweet Stout 133 recipes, p50 = 2 beans, usual range 1–3. **The formulate path
never calls it.** It is exposed to the chat agent as `common_practice`, which
takes a *style* and not an *ingredient*, so even the agent cannot get at it.

`corpus.yeasts` holds 1,745 strains, 1,743 with an attenuation figure, ranked by
real usage (US-05 in 31,577 recipes). Spot-checked against manufacturer
datasheets: US-05 81%, S-04 75%, WLP002 66.5%, W-34/70 83% — all correct.

### 1.3 The web arm works, and its output is thrown away

`services/webarm/webarm.py` on `:5055`: SearXNG → fetch → docling hybrid chunk →
bge-m3 embed → cosine rank → top_k. Probed live, 2026-09-16, it returned in
seconds.

`wf-step-retrieve` fires it whenever `nlq.corpus_vocabulary_gap` reports a term
the library has never seen. On the run that produced recipe #90 it **did fire**:

```
obs.retrievals #373
  query      "stout creamy custard like sweet thick lactose vanilla poppy seeds rum"
  gap_terms  {custard, poppi}
```

`cap-formulate-recipe`'s `Build propose pack` reads
`$('Step 2 · retrieve').first().json.rows` and never touches `.web` or `.gap`.
The web passages were fetched, ranked, returned — and dropped on the floor.

Two further faults in the same call:

- No `web_query` is passed, so the web arm searches the retrieval bag-of-words.
  Probing `"adding poppy seeds and vanilla to stout maceration rum"` by hand
  returned **vanillamart.com — a Christmas cake recipe and a rum toddy**. The
  search is undirected; nothing steers it at brewing.
- The library query is one flat concatenation of style + descriptors +
  must_include. `wf-step-retrieve-multi` (decompose → parallel search → merge)
  exists and is active, and this path does not use it.

### 1.4 The model: what it actually does

Real per-step latency, runs 181–182, not the skewed all-time average:

```
parse    416 tok in →  111 out ·  3.1–5.7 s
propose 8806 tok in →  684 out · 22.1–22.3 s
compose 4535 tok in →   19 out ·  2.8 s
```

So ~30 s of model time per recipe at 8.8k tokens of context. `num_ctx` is 16384.
There is headroom, but not much: ~12k is the practical prompt ceiling before
generation gets squeezed.

**What it gets wrong is instruction count, not knowledge.** Recipe #90's propose
output simultaneously obeyed and broke the same rule:

```json
"not_available": ["vanilla", "poppy seeds", "rum"],
"items": [ …,
  {"ingredient_id": 153, "qty_g": 500, "stage": "fermenter",
   "notes": "Macerated poppy seeds and vanilla in rum"},   ← Weyermann Wheat Malt
  {"ingredient_id": 145, "qty_g": 200, "stage": "fermenter",
   "notes": "Rum for maceration and flavor"}]              ← Weyermann Pale Ale Malt
```

731 g of malt entered the fermenter as "flavourings". `f_compute_recipe` filters
on `kind`, not `stage`, so it counted at full mash efficiency. The sheet said
**ABV 9.0%**; recomputed without the two phantom items it is **7.8%**.

This is the third instance of the same pattern, and the repo has written the
lesson down twice already:

| What was asked of the prompt | What happened | Where it ended up |
|---|---|---|
| Classify malts by colour, not name | Bohemian *Dark* Malt (6.5 °L) used as roast, EBC 44 | `brew.f_catalogue` derives `role` in SQL |
| Keep roast ≤ 15% of grist | Stated in v5 and v6; crossed in 3 of 6 runs (21.8%, 17.6%, 16.0%) | Enforced in `Validate proposal` |
| Never substitute silently | Declared the gap *and* substituted, same call | **Still only in the prompt** |

### 1.5 Loose ends found on the way

- **`num_ctx` is split.** `obs.profiles` says 16384 for all five profiles;
  `chat-agent`'s Ollama node says **12288**. `ollama ps` right now shows the
  resident runner at **12288**. Ollama keys its runner on context size, so every
  agent turn followed by a capability step risks evicting and reloading a 13 GB
  model. `63_model_switch.sql` warns about exactly this in a ⛔ block; the chat
  node is the profile that was left behind. This plausibly explains the
  `max(latency_ms) = 7,130,502` outlier on `propose`.
- **A `critique` profile exists** (temperature 0) and has never been used.
- **`f_save_recipe` hardcodes `unit = 'g'`** even though `brew.recipe_items.unit`
  is free text with no CHECK. "2 vanilla beans" and "200 ml rum" are not
  currently expressible. Every downstream node uses `qty_g` as a field name.
- **The eval set is 6 cases and 5 of them are stouts.** It cannot detect a
  style-generality regression, and it cannot detect the substitution bug at all.
- **The library is 2,678 chunks over 12 documents**, weighted to process and
  stouts. There is no recipe-formulation text — no *Designing Great Beers*, no
  *Brewing Classic Styles*, no *Radical Brewing*. For styles outside
  stout/porter/IPA, retrieval will thin out fast.

---

## 2. The honest answer on "all-knowing"

Two of the three asks are reachable. One is not, and it is worth being exact
about which.

**"Any style" — reachable, with work.** The blockers are concrete and countable:
zero yeast strains (so attenuation is a guess and lagers/Belgians cannot be
specified), one adjunct (so no candi sugar, dextrose, honey, flaked maize), no
water agents (despite a 382-chunk water book sitting ingested and unused). Add
those and the arithmetic already generalises — `f_compute_recipe`,
`f_fit_to_abv`, `f_fit_ibu` and `ref.f_style_bands` are style-agnostic today.
Retrieval depth outside dark ales stays thin until the library grows, and that
is a book-buying problem, not an engineering one.

**"Any ingredient" — reachable in a specific, limited sense.** The system can
learn to place *any* ingredient — stage, amount, method — because the corpus
carries 141,857 real additions and the web arm can fetch the rest. What it
cannot do is *simulate* an arbitrary ingredient: there is no honest
`potential_ppg` for a vanilla bean, and `27_brew_catalogue.sql` forbids
inventing one. So a flavouring will always be a line on the sheet with a stated
method and a citation, never a term in the gravity equation. That is the right
answer, and it is the answer the brewer actually needs.

**"Perfectly rounded, all-knowing" — not reachable, and chasing it makes the
system worse.** Three hard limits:

1. The corpus tells you what is *popular*, never what is *good*. 1,509 brewers
   put vanilla in secondary; that is evidence, not authority. Recipe 280784 —
   a real 9.34% vanilla-lactose stout — records **IBU 0.00** and two 60-minute
   hops at "0 min". Self-reported data is noisy and must be quality-gated before
   a model ever sees it.
2. Gemma4:12b has a measured instruction-budget. Making it "know more" by
   handing it more context is the move that produced the bug in §1.4. Every
   capability added below is added as a *separate small call*, not as another
   block in the big one.
3. Anything with no published figure and no corpus mass — poppy seed, n=1 — is
   answerable only from the open web, which means the answer is as good as
   whatever SearXNG surfaced that day. The system's job there is to cite it as
   `[W..]`, not to launder it into `[S..]`.

The achievable target is: **a recipe creator that never silently invents, always
shows its evidence, and fails loudly and specifically when it is outside its
knowledge.** That is worth more than an oracle, and it is buildable from here.

---

## 3. The proposed pipeline

Eight stages. Five LLM calls, none over ~6k tokens. Everything that can be
arithmetic stays arithmetic.

```
A  brief          LLM extract    ~0.4k    what the brewer asked for
B  resolve        SQL, no LLM      —      route every named ingredient
C  evidence       SQL + HTTP       —      6 parallel gatherers
D  skeleton       LLM formulate  ~5.5k    fermentables + hops
E  additions      LLM formulate  ~2.0k    flavourings, sugars, spirits, yeast
F  gates          code, no LLM     —      arithmetic + the new guards
G  critique       LLM critique   ~2.0k    non-numeric, advisory, cannot rewrite
H  compose        LLM compose    ~4.5k    one paragraph; the sheet is rendered in code
```

Budget: ~14.4k tokens across five calls against today's 13.7k across three.
Estimated wall clock 45–55 s against today's ~30 s. That is the price, and it
buys every capability below.

### Stage A — Brief *(exists, small extension)*

Today's `parse`, plus a `process` field (all-grain / BIAB / extract) and
`equipment` hints when stated. Everything else stays.

### Stage B — Resolve *(new, no LLM)*

New: `brew.f_resolve_request(p_terms text[])`. For each term the brewer named,
return one verdict:

| verdict | meaning | routing |
|---|---|---|
| `catalogued` | matches a `brew.ingredients` row | pass the id to D or E |
| `known_uncatalogued` | absent from the catalogue, ≥ N corpus recipes use it | E, with a corpus practice block |
| `thin` | in the corpus but below threshold (poppy seed, n=1) | E, with a **web** technique block |
| `unknown` | nothing anywhere | tell the brewer, before building |

`nlq.f_resolve_ingredient` already expands a term to its corpus raw-string
variants (`'vanilla'` → 267 variants including "vanilla bean in rum"), so the
matching half exists. What is new is the verdict and the routing.

**This is the single highest-value addition.** It turns "is it in the catalogue"
— a yes/no that produced a wrong answer and a silent substitution — into a
four-way route where every branch has somewhere to go.

### Stage C — Evidence *(mostly exists, wired wrong)*

Six gatherers, all parallel, no LLM:

| # | what | status |
|---|---|---|
| C1 | published style bands — `ref.f_style_bands` | ✅ exists, wired |
| C2 | cohort quartiles — `nlq.cohort_stats`, rung ≤ 2 only | ✅ exists, wired |
| C3 | **2–3 whole exemplar recipes** from the cohort | ⬜ new `nlq.find_exemplars` |
| C4 | **per-ingredient practice** — stage distribution + amount quantiles | ⬜ new `nlq.ingredient_practice` |
| C5 | library passages, **decomposed** into 2–4 targeted queries | 🟡 `wf-step-retrieve-multi` exists, unused here |
| C6 | web technique passages for `thin` / `unknown` terms | 🟡 fires already, output discarded |

**C3 — exemplars.** Rendering one corpus recipe compactly costs ~250 tokens:
grain bill with percentages, hops with times, yeast, misc with stages. Three fit
in 750. This is the user's step 1 and it is a straightforward query over
`corpus.recipe_search` + the four `recipe_*` tables.

⛔ **It needs a plausibility gate.** Recipe 280784 is a genuine match and records
IBU 0.00 with two "0 min" boil hops. Reject exemplars with zero IBU and boil
hops, an OG/FG pair that implies impossible attenuation, or a grain bill that
does not sum. Show the gate's rejection count on the sheet — "3 of 47 matches
were discarded as implausible" is information, not noise.

**C4 — ingredient practice.** One function, one row per (term, stage):

```
vanilla · Secondary   56%  ·  p25 1.0  p50 2.0  p75 3.0  "each"
vanilla · Boil        16%  ·  p25 1.0  p50 2.0  p75 2.0  "each"
rum     · Secondary   69%  ·  p25 2.0  p50 3.0  p75 4.0  "oz"
```

⛔ Units are never converted. `73_corpus_search.sql` already states the rule:
vanilla arrives as `each`, `oz`, `tsp`, `g`, `tbsp`, `ml` and `lb`, and those are
not one substance measured differently. Report per unit, side by side.

**C6 — steering the web arm.** Two fixes. Pass an explicit `web_query` built for
the web rather than for a vector index — `"<term> homebrew beer addition rate
when to add"` rather than the retrieval bag-of-words. And bias SearXNG toward
brewing: a small allow-list of domains (homebrewtalk, brulosophy, byo.com,
milkthefunk, scottjanish) tried first, general web as fallback. The
`vanillamart.com` result in §1.3 is what an unsteered query gets you.

### Stage D — Skeleton *(exists, narrowed)*

Fermentables and hops only. Same prompt lineage as `formulate.recipe/propose` v7,
minus the additions confusion, plus the exemplars block.

**⚠️⚠️ WITHDRAWN 2026-09-16 — see §9.3, which measured this and found it does
not help.** The reasoning below was plausible and is kept for the record; the
measurement overrides it. The catalogue stays flat and complete.

**⚠️ One deliberate deviation from the brief.** The user asked for step 3 to
"gather info about different malts, hops, techniques … just to see what is
possible". I am proposing the opposite, and here is why: the model already sees
all 77 malts and all 72 hops, ~1,275 tokens of flat list. Its failures are not
from missing options — it picked Bohemian Dark Malt *because it was there*.
Widening the choice set makes every measured failure mode more likely.

Counter-proposal: `brew.f_catalogue_for_style(p_style)`. Rank the catalogue by
corpus co-occurrence with the requested style, keep the top ~15 per role, always
include anything the cohort actually uses, and annotate each row with its
evidence:

```
BASE MALTS — id | name | ppg | °L | used in
145 | Weyermann Pale Ale Malt | 36.5 | 2.9 | 34% of stouts
157 | Viking Oat Malt         | 27.7 | 2.5 | 19% of stouts
```

Smaller prompt, and *more* informative about what is possible in this style than
a flat list ever was. The full catalogue stays reachable — if the brewer names
something outside the narrowed set, Stage B resolves it and it is forced in.

### Stage E — Additions *(new)*

A separate call, and it must be separate for four reasons: a different catalogue
subset, different units (`each`, `ml`, `g`), no interaction with the IBU or
colour arithmetic, and — decisively — it keeps D's prompt under 6k.

Input: the resolved ingredients from B, their C4 practice blocks, C5/C6
technique passages. Output per item:

```json
{"ref": "catalogue:109" | "uncatalogued:vanilla bean",
 "qty": 2, "unit": "each", "stage": "fermenter", "timing_days": 14,
 "method": "split and scraped, macerated in 100 ml dark rum for 2 weeks",
 "cites": ["W2", "S4"]}
```

Yeast is chosen here too, from the top-N corpus strains filtered to the style.
That is what finally removes "attenuation 70% · no yeast in the catalogue — pick
your own" from the sheet, and it makes FG a computed number instead of a guess.

### Stage F — Gates *(exists, three additions)*

Existing and keeping: `f_fit_to_abv` bisection, `f_fit_ibu` scaling, the 15%
roast ceiling, the style-band check with one retry.

**F1 — substitution guard.** ⛔ The fix for §1.4, and it belongs in code for the
same reason the roast ceiling does. Rule: if a term appears in `not_available`
or resolves to `thin`/`unknown`, then **no item may carry that term in its
`notes`**. Drop the item, report the drop. Cheap, exact, catches the measured
failure.

**F2 — unit guard.** Whitelist `g` / `ml` / `each`. Non-mass items are excluded
from the gravity fit and the grain-bill denominator. Requires threading a `unit`
through `propose` → `Validate` → `f_save_recipe` → the sheet; `f_save_recipe`
currently hardcodes `'g'` and everything downstream names the field `qty_g`.

**F3 — fermentable-in-fermenter check.** A `fermentable` at stage `fermenter` or
`packaging` is almost always a mislabelled flavouring. Flag it. Had this existed,
it would have caught recipe #90 independently of F1.

### Stage G — Critique *(new, advisory only)*

Uses the unused `critique` profile (temperature 0).

⛔ **Strictly non-numeric.** `29_brew_formulate.sql` is explicit that judgement
about numbers belongs in SQL and that a model marking its own homework hands the
error straight back. That rule is correct and Stage G does not touch it. F owns
every figure.

G answers one question: *does anything here contradict the brief or the cited
passages?* — wrong yeast temperature for the stated ferment, a spice at a stage
the cited passage warns against, a descriptor in the brief that nothing in the
recipe delivers. Output is a list of flags that print on the sheet. **It cannot
rewrite anything.** If it can only flag, a hallucinated flag costs one confusing
line; if it could rewrite, a hallucinated flag costs a wrong recipe.

Ship this last, behind a switch, and measure whether it earns its 8 seconds.

### Stage H — Compose *(exists)*

Unchanged, plus the new blocks: method notes, yeast, G's flags. The sheet is
already rendered in code; the model writes one grounded paragraph. Keep it that
way.

---

## 4. Feasibility ledger

### Buildable now, no new dependencies

| Item | Why it is easy |
|---|---|
| `misc` flavouring rows (vanilla, cacao, coffee, spices, oak, fruit) | `kind='misc'` already allowed; `potential_ppg` nullable; `f_compute_recipe` ignores the kind |
| Sugars and adjuncts (dextrose, candi, honey, maple, flaked grains) | Same shape as lactose; some have published PPG, the rest follow `28_`'s derived-with-provenance pattern |
| Water agents (gypsum, CaCl₂, chalk, epsom) | `kind='water_agent'` already allowed; 382 chunks of water book ingested and unused |
| `nlq.ingredient_practice` | Pure aggregation over `corpus.recipe_misc`; the columns exist and are indexed |
| `nlq.find_exemplars` | `corpus.recipe_search` is GIN-indexed; a live cohort select measured ~200 ms |
| Consuming `.web` and `.gap` in the formulate path | The data is already in the node's input. This is a code edit in `Build propose pack` |
| F1 substitution guard | ~15 lines in `Validate proposal` |
| F3 fermentable-in-fermenter flag | ~5 lines, same node |
| `num_ctx` unification | One value in `chat-agent`'s Ollama node, 12288 → 16384 |

### Buildable, but a real thread to pull

| Item | What it costs |
|---|---|
| Yeast catalogue | Curate top ~120 from `corpus.yeasts`. Attenuation is trustworthy (spot-checked). `attenuation_min/max` is garbage (0.00–127.00) — discard. Temp units are inconsistent (US-05 recorded as "12.0–25.0 F", plainly °C) — repair or drop. ⚠️ Needs a decision, see §7 Q1 |
| Units beyond grams | Threads through 5 nodes and 2 SQL functions. Unavoidable for "2 vanilla beans" |
| `brew.f_catalogue_for_style` | New function plus a corpus↔catalogue name mapping. The mapping does not exist and `70_corpus.sql` explains why it was deferred. Start with trigram matching on the top ~200 corpus strings and accept partial coverage |
| Web-arm steering | Domain allow-list + query templating. Small, but needs iteration against real queries |
| Decomposed retrieval in the formulate path | `wf-step-retrieve-multi` exists and is active; it adds one LLM decompose call (~2 s) |
| Eval set 6 → ~25 cases | The harness is declarative and errors loudly on unknown keys. Mostly authoring work, but it gates everything else |

### Not worth doing, or not now

| Item | Why not |
|---|---|
| Widening the catalogue shown to the model | Measured to be the cause of failures, not the cure. §3 Stage D |
| Letting a model adjust numbers | Explicitly rejected in `29_brew_formulate.sql`, for cause. Stage G is advisory only |
| Resolving all 8,243 corpus fermentable strings to catalogue ids | `70_corpus.sql`: it would mean inventing a `potential_ppg` per row. Map the top ~200 for ranking only, never for substitution |
| A reranker | §4.4 already found it is not free on this stack. Revisit only on a §10.4 signal |
| A bigger model | `nemotron-3.5-lightning:30b` measured 16× slower and *worse* on the job that matters. 16 GB VRAM is the constraint |
| Embedding the corpus into `kb.chunks` | Hard architectural rule; 179k unvetted docs that look like knowledge is the exact failure the design prevents |

### Blocked on something outside the code

- **Library depth outside dark ales.** No formulation text is ingested. Until
  *Designing Great Beers* or similar is in `kb`, "any style" means "any style the
  BJCP/BA guidelines describe plus whatever the corpus shows", with thinner
  citations than a stout gets. Buying and ingesting one book is the highest-value
  non-code action available.

---

## 5. Phasing

Each phase is independently shippable and has a verification that is a command,
not an opinion.

### Phase 0 — Make the work measurable *(half a day)*

Nothing else is trustworthy until this exists.

1. Grow `scripts/stress/recipe_cases.jsonl` from 6 to ~25. Required coverage:
   at least one each of lager, Belgian, saison, hazy IPA, wheat, sour; at least
   four flavouring cases (vanilla, coffee, cacao, fruit); at least two
   thin-ingredient cases (poppy seed, or similar n≤5); keep all six existing.
2. Add scorer keys: `no_substitution` (no item's notes name a term reported
   unavailable), `has_yeast`, `additions_have_method`, `units_valid`.
3. Re-baseline the current pipeline against the new set and commit the numbers.

→ **verify:** `recipe_eval.py` runs green on the harness itself, and R01–R06
score as they did before. The substitution case **must FAIL** — that is the bug
being pinned down.

### Phase 1 — Stop the bleeding *(one evening)*

4. F1 substitution guard + F3 fermentable-in-fermenter flag.
5. Unify `num_ctx` at 16384 in `chat-agent`.
6. Consume `.web` and `.gap` in `Build propose pack`; render web passages as
   `[W..]`, never renumbered as `[S..]` — `brainstorm.pairing/compose` v2 already
   does this correctly, copy it.
7. Pass an explicit `web_query` from the formulate path.

→ **verify:** the substitution case flips to PASS. `ollama ps` shows one runner
at 16384 after an agent turn followed by a recipe. A recipe naming an
uncatalogued ingredient cites at least one `[W..]`.

### Phase 2 — Give it the ingredients *(a weekend)*

8. New `db/init/3x_brew_misc.sql`: flavourings, spices, oak, fruit as
   `kind='misc'`, with `attrs.provenance`. **Add it to `db-init`'s file list.**
9. New `db/init/3x_brew_sugars.sql`: dextrose, sucrose, candi, honey, maple,
   flaked adjuncts. Published PPG where one exists; derived-with-arithmetic
   otherwise, following `28_`.
10. Add `misc` / `water_agent` / `yeast` sections to `Build propose pack`'s
    `SECTIONS` array. ⛔ **Without this a `misc` row is silently filtered out of
    the rendered catalogue** — `f_catalogue` returns `role = kind` for
    non-fermentables and the array only lists five roles.
11. F2 unit support end to end.

→ **verify:** a vanilla-stout case produces `Vanilla bean · 2 each · fermenter`
and the gravity is unchanged by its presence. `brew.f_compute_recipe` output is
byte-identical with and without the misc rows.

### Phase 3 — Give it the evidence *(a weekend)*

12. `nlq.ingredient_practice`. 13. `nlq.find_exemplars` + plausibility gate.
14. `brew.f_resolve_request` (Stage B). 15. Wire C3/C4 into the pack; switch C5
    to `wf-step-retrieve-multi`.

→ **verify:** for a vanilla request, the propose prompt contains the Secondary
56% / 2 beans block and at least two exemplars. Prompt total stays under 12k
tokens (`obs.steps.tokens_in`). An `unknown` term stops the run before Stage D
and asks the brewer.

### Phase 4 — Split the call *(a weekend)*

16. Stage E as its own prompt + node. 17. Narrow D's catalogue via
    `f_catalogue_for_style`. 18. Yeast selection in E; attenuation becomes
    chosen, not guessed.

→ **verify:** D's `tokens_in` drops below 6k; E's stays under 2.5k; total
latency under 60 s. Full eval set no worse than the Phase 0 baseline on every
case, and better on the flavouring cases.

### Phase 5 — Curate *(evidence-driven, may be skipped)*

19. Stage G behind a switch. 20. Run the full set with and without it.

→ **verify:** ship only if it flags ≥ 1 real problem across the set and
hallucinates ≤ 1. Otherwise delete it and write down why.

---

## 6. Risks

| # | Risk | Mitigation |
|---|---|---|
| 1 | **Five calls, five chances to break instruction-following.** More calls is not automatically better | Every call gets a machine-checkable contract. Phase 4 does not ship unless the eval set is flat or better |
| 2 | **Corpus practice presented as authority.** 1,509 brewers is evidence, not a publisher | Already the house rule (`73_corpus_search.sql`, the rung discipline). Practice blocks are labelled and never cited as `[S..]` |
| 3 | **Web passages laundered into library citations** | `[W..]` vs `[S..]` is already enforced in the pairing path. Copy it verbatim; do not re-derive |
| 4 | **Latency creep past the point of usability.** 30 s → 55 s is tolerable; 55 s → 3 min is not | `obs.steps.latency_ms` is already logged per step. Set a budget and fail the phase on it |
| 5 | **Every workflow edit deactivates the workflow and drops the chat webhook** | CLAUDE.md's hazard. Re-publish *and* `docker restart n8n` after every import, and probe the webhook before trusting any eval run |
| 6 | **Catalogue growth inflates the prompt permanently** | `f_catalogue_for_style` caps it structurally. Do Phase 4 step 17 before Phase 2 makes the flat list much larger |
| 7 | **Yeast attenuation from self-reported data** | Spot-checked correct for the top strains; provenance tagged; ⚠️ still needs the §7 Q1 decision |

---

## 7. Decisions I need from you

**Q1 — Yeast provenance.** `27_brew_catalogue.sql` forbids inventing specs, and
every current row traces to a maltster or the Hop Variety Handbook.
`corpus.yeasts` attenuation is self-reported but verified correct for the strains
that matter. Three options: (a) seed from the corpus with
`attrs.provenance = 'corpus_selfreported'`, following `28_`'s honesty pattern;
(b) hand-enter ~40 strains from manufacturer datasheets — slower, unimpeachable;
(c) ingest a yeast datasheet PDF through docling and derive from `ref.*` like
malts. **My recommendation: (a) now, (c) later** — (a) unblocks Phase 4
immediately and the provenance tag makes the upgrade path honest.

**Q2 — Catalogue narrowing. ✅ CLOSED 2026-09-16 — no longer a question.**
Measured in §9.3: narrowing scored 4/6 clean against 5/6 for the full catalogue,
and cutting passages pushed roast % to 16–20%. The proposal is withdrawn. The
catalogue stays flat and complete, and the passages stay in Stage D.

**Q3 — Where the ambition sits.** The plan targets "never silently invents,
always shows evidence, fails loudly and specifically". If you want to trade some
of that for reach — let it propose an ingredient it can only justify from the
open web, for instance — say so, because it changes Stage B's routing and F1's
strictness.

**Q4 — A book.** The single highest-value non-code action is ingesting a
recipe-formulation text. Nothing in the library teaches *how to build a recipe*;
the books teach process, water, yeast, malt and styles. Is buying one on the
table?

---

## 8. What I would do first, if only one thing

Phase 0 and Phase 1 step 4. The eval set is what makes every later claim
checkable, and the substitution guard closes a bug that is currently shipping
wrong ABV figures to the brewer with full confidence.

---

## 9. Multi-round orchestration — measured 2026-09-16

Added after the question *"can we implement an internal thinking-like mechanism,
so the orchestrator goes multiple rounds? I don't care about the time."*

Short answer: **yes, and it is the right move — but not the model's own thinking
mode, which was measured and does not work.** Unlimited time buys a great deal
here, just through a different mechanism than it first appears.

Everything in this section is a measurement taken on this machine against the
real production prompt, not an estimate. Scripts are in the session scratchpad;
the numbers are reproducible with `ollama` and `seed`.

### 9.1 ⛔ Native thinking mode does not terminate

`ollama show gemma4:12b-it-q8_0` reports the capability, so it was tried:

| `num_predict` | wall clock | thinking emitted | JSON emitted |
|---|---|---|---|
| 2,500 | 65 s | 5,827 chars | **none** |
| 10,000 | **262 s** | **23,368 chars** | **none** |

It never finished. The tail of the 23k-character trace is a verbatim loop:

```
*   Wait, I should check the "stage" field.
*   All are strings.
*   Wait, I should check the "not_available" field.
*   All are strings.
...  (the same 12-field cycle, repeating until the token cap)
```

Two distinct failures, and both matter beyond this one probe:

1. **It does not converge.** This is reasoning-degeneration, not slowness. More
   time does not fix it — the second run had 4× the budget and got 4× the loop.
2. **It reasons about the wrong thing.** The trace opens by re-deriving OG and FG
   by hand — `$9.0 = (OG - FG) \times 131.25$` — which the prompt explicitly
   forbids and which `brew.f_fit_to_abv` already solves exactly, by bisection.
   Thinking tokens pulled the model *toward* the arithmetic this pipeline spent
   four SQL functions taking away from it.

**Verdict: do not enable `think: true` on this model for this task.** Not "tune
it" — the failure is not in the settings.

### 9.2 What the prompt size is actually doing

Same task, same rules, same model, two prompt sizes:

| prompt | tokens in | clean runs |
|---|---|---|
| minimal probe (8 catalogue rows, 3 rules) | 430 | **6 / 6** |
| production prompt | 8,691 | **5 / 6** |

And the production prompt divides like this:

```
passages    15,511 chars  ~3,877 tok   57%   ← the biggest block by far
catalogue    5,744 chars  ~1,436 tok   21%
rules+rest   5,810 chars  ~1,452 tok   21%
```

### 9.3 ⚠️ Retraction: narrowing the catalogue is NOT supported

§3 Stage D proposed `brew.f_catalogue_for_style` to cut the catalogue to ~48
rows. It was tested. **It does not help, and it may hurt:**

| condition | tokens in | clean / 6 | roast % spread |
|---|---|---|---|
| A — full catalogue, 8 passages *(production today)* | 8,691 | **5 / 6** | 12.4 – 15.3 |
| B — narrowed catalogue, 8 passages | 6,770 | **4 / 6** | 12.6 – 17.9 |
| C — narrowed catalogue, 3 passages | 4,665 | **5 / 6** | 15.6 – **19.7** |

"Clean" = no fault that code cannot correct: no substitution, no invented id, no
malt routed to the fermenter, no under-reported `not_available`, hops present.
Roast % is listed separately because `Validate proposal` trims it either way.

Two things fall out, and both contradict §3:

- **Cutting the catalogue bought nothing.** The story — fewer options, fewer bad
  picks — was plausible and is wrong. B is worse than A on the same rubric.
- **Cutting passages made proportions worse.** Condition C drifts to 16–20%
  roast on five of six runs, against 12–15% with the full eight. The library
  passages are carrying real signal about grain-bill proportion, not just
  technique. ⛔ **Do not move them out of Stage D.**

§3 Stage D's narrowing proposal is withdrawn, and §7 Q2 with it. The catalogue
stays flat and complete. Where §3 still stands: splitting *additions* into
Stage E, which §9.4 now supports on independent evidence.

### 9.4 ⭐ The model is already trying to do Stage E

Counting, across the 18 production-prompt runs, items where the model emitted a
**non-numeric** `ingredient_id` naming something it had just declared absent:

```
A  full prompt          9 across 6 runs   (1.5 per run)
B  narrowed catalogue   7 across 6 runs
C  narrowed + 3 pass.  15 across 6 runs   (2.5 per run)
```

A representative one, verbatim:

```json
{"ingredient_id": "vanilla",     "qty_g": 0, "stage": "fermenter",
 "notes": "Add vanilla beans soaked in rum to fermenter"}
{"ingredient_id": "poppy_seeds", "qty_g": 0, "stage": "fermenter",
 "notes": "Macerate crushed poppy seeds in rum and add"}
{"ingredient_id": "rum",         "qty_g": 0, "stage": "fermenter",
 "notes": "Use to macerate vanilla and poppy seeds"}
```
— alongside `"not_available": ["vanilla","poppy seeds","rum"]`.

That is **not a hallucination**. It is the model refusing to substitute, naming
the real ingredient, giving the correct method, setting quantity to zero because
it has no basis for one, and reporting the gap — all at once, correctly. Then
`Validate proposal` drops all three as "unknown ingredient_id".

**Stage E is not a new capability to teach. It is a schema slot to open.** The
behaviour is already there on roughly two items per run and is being discarded.

### 9.5 The substitution bug is stochastic, ~1 in 6

Across the six production-prompt runs, exactly one substituted (seed 2: Weyermann
Munich Malt into the fermenter as "Macerated poppy seeds and vanilla"). The other
five handled the same request correctly.

⚠️ **This is worse news than a deterministic bug, not better.** A fault that
appears once in six passes a casual test, passes a demo, and then ships a wrong
ABV to the brewer. It also means the recipe #90 you saw was not the typical
output — it was the unlucky draw. The F1 code guard is not optional.

### 9.6 What multi-round SHOULD mean here

Four mechanisms, ranked by measured or structural support:

**① Best-of-N with a deterministic scorer — do this first.**
Generate N candidates, score every one with `f_compute_recipe` + `f_style_bands`
+ the F1/F2/F3 guards, keep the best. No model self-judgement anywhere, so it
cannot drift.

The measured clean rate is 5/6 ≈ 83%. Independent draws at N = 5 give
1 − (1/6)^5 ≈ **99.99%** chance that at least one candidate is clean. At ~21 s a
draw that is **~105 s for a near-guarantee**, and it also lets the scorer pick
the *best* in-band candidate rather than the first acceptable one.

This is the single highest-value use of "I don't care about time" on this stack,
and it is perfectly aligned with the house rule: the judge is SQL, never a model.

**② Deterministic-critic revision — already built, extend it.**
`Check bands` → `Retry propose?` → `Step 3b · re-propose` with a specific
`{{correction}}` message. It fires on **20 of 132 logged runs (15%)**. Raise the
cap from 1 retry to 3–4, each with the specific miss named.

⚠️ **Its effectiveness is currently not logged.** `obs.steps.verdict` records
only `schema_ok`; nothing records whether the retry resolved the miss. Log that
before raising the cap, or the change is unfalsifiable.

Best combined with ①: N candidates, score, and revise only the best one.

**③ Self-directed retrieval — one bounded round.**
After C gathers evidence, one extra call: *"here is the brief and what was found;
name up to 3 further questions."* Run those through `wf-step-retrieve`, then
continue. This is your step 3/4 done properly, and it is the genuine "thinking"
win — the model steering its own evidence gathering.

⛔ **Bounded to one round, max 3 queries, no free tool loop.** An open agentic
loop is the measured `Max iterations (5) reached` failure already recorded in
CLAUDE.md.

**④ Model-as-critic — last, advisory, non-numeric.**
Stage G, unchanged from §3. Given §9.1, expect little; measure before keeping.

### 9.7 Revised shape

```
A  brief                     LLM  ~0.4k
B  resolve                   SQL
C  evidence (6 gatherers)    SQL + HTTP
C* self-directed retrieval   LLM  ~2k     ③ one round, ≤3 queries
D  skeleton  × N=5           LLM  ~6k each, FULL catalogue, FULL passages
F  score all N               code          ① deterministic pick
D' revise best, ≤3 rounds    LLM  ~6k each ② critic is arithmetic
E  additions                 LLM  ~2k      ④ the slot §9.4 proved is needed
F' gates                     code
G  critique (optional)       LLM  ~2k
H  compose                   LLM  ~4.5k
```

Estimated wall clock **3–5 minutes** per recipe. Explicitly accepted.

⚠️ **One hard ceiling that time cannot buy past.** Every mechanism above is
*selection* and *evidence*, not *reasoning*. They raise the floor by rejecting
bad draws and by putting better facts in front of the model. None of them makes
gemma4:12b reason better than it does in one pass — §9.1 is the evidence that
the direct attempt at that fails outright. Quality gains will come from the
scorer and from Stages B/C/E, and they will plateau. When they do, the next lever
is a better model or a better library, not more rounds.

### 9.8 Revised phasing

Phases 0–3 are unchanged and still come first — ① is worthless without the eval
set, and ② cannot be tuned without the retry logging.

- **Phase 4** — replaces §5's Phase 4. Drop the catalogue narrowing (§9.3).
  Keep Stage E (§9.4). Add best-of-N at N = 5 with the deterministic scorer.
  → *verify:* clean rate over the full eval set ≥ 95%, against the 83% baseline
  measured here. Log N and the winning index in `obs.steps`.
- **Phase 4.5** — retry-outcome logging, then raise the retry cap to 3.
  → *verify:* the log shows what fraction of retries resolve their named miss.
- **Phase 5** — self-directed retrieval (③), one round, ≤ 3 queries.
  → *verify:* prompts stay under 12k tokens; flavouring cases improve.
- **Phase 6** — Stage G (④), behind a switch, kept only on evidence.

---

## 10. ⭐ Constrained decoding + the Stage E slot — measured 2026-09-16

This section supersedes the priority order in §5 and §9.8. It is the largest
quality result found so far, and it needs no loops at all.

### 10.1 Schema-constrained decoding ALONE makes things much worse

Ollama accepts a JSON Schema in `format`, which constrains decoding so an
invalid token cannot be emitted. Applied to today's propose schema — with
`ingredient_id` restricted to an `enum` of the 150 real ids and `qty_g` required
to be ≥ 1:

| condition | substituted | malt in fermenter | clean |
|---|---|---|---|
| production today, unconstrained | 1 / 6 | 1 / 6 | **5 / 6** |
| **+ schema-constrained decoding** | **6 / 6** | 5 / 6 | **0 / 6** |

Every single run substituted a malt for a flavouring — Styrian Kolibri, Rye
Malt, Caramel — against 1 in 6 before.

⛔ **The grammar caused the bug.** §9.4 measured that the model *wants* to emit
`{"ingredient_id": "vanilla", "qty_g": 0}`. The schema makes a non-integer id
and a zero quantity unrepresentable. So the constrained decoder, forbidden from
telling the truth, is forced to choose *some* valid id and *some* positive
quantity — and it picks a malt and labels it vanilla, every time.

**Constraining an output space with no legal way to say "absent" manufactures
the exact fault you are trying to prevent.** This is the same lesson as the rest
of the document, in its purest form: the schema had no slot for the truth, so
the model produced a falsehood.

### 10.2 ⭐ Add the slot, and the entire fault class disappears

Same constrained decoding, plus one array in the schema and one paragraph of
prompt:

```jsonc
"uncatalogued_additions": [{ "name": str, "qty": num, "unit": "g"|"ml"|"each",
                             "stage": enum, "method": str }]
```
```
⛔ AN INGREDIENT THE BREWER ASKED FOR THAT HAS NO CATALOGUE ID GOES IN
"uncatalogued_additions" -- by its real name, with the stage and the method for
using it. NEVER put it in "items" under some other ingredient's id. A malt is
not a substitute for a spice.
```

| condition | substituted | malt in fermenter |
|---|---|---|
| production today | 1 / 6 | 1 / 6 |
| constrained, no slot | 6 / 6 | 5 / 6 |
| **constrained + slot** | **0 / 6** | **0 / 6** |

**Both failure classes went to zero on all six seeds.** Not reduced — eliminated.

And the output is better than anything the pipeline has produced. All six seeds
independently converged on the same answer, which is also the correct one:

```
· Vanilla beans  @ boil       Add one bean to the kettle at the end of the boil.
· Vanilla beans  @ fermenter  Add second bean soaked in rum after 3-7 days.
· Poppy seeds    @ fermenter  Macerate crushed poppy seeds in rum and add.
· Rum            @ fermenter  Use to macerate poppy seeds and vanilla.
```

That is a direct answer to the brewer's actual question — *macerate or boil?* —
and it is the right one: **both**, split across two stages for two different
effects. The pipeline was capable of this the whole time. The schema was in the
way.

⚠️ One flaw: `qty` and `unit` came back `null` on every run, because the schema
did not mark them required. Two fixes, both already planned — make them
required, and feed the C4 practice block (`vanilla · Secondary 56% · p50 2.00
each`) so the number has a basis instead of being invented.

### 10.3 What this changes about the plan

- **Stage E is promoted from Phase 4 to Phase 1.** It is the highest-value change
  in this document and it is roughly a day: one schema, one prompt paragraph, one
  array to render on the sheet. It also makes F1 (the substitution guard) a
  belt-and-braces check rather than the primary defence.
- **Constrained decoding is adopted — but only together with Stage E.** ⛔ Never
  ship `format` without the slot; §10.1 is what that costs.
- **Best-of-N (§9.6 ①) drops in priority.** It raises 83% to ~99.9% *stochastically*.
  §10.2 takes the same fault class to 0/6 *structurally*, for far less compute.
  Keep best-of-N for what remains — proportion quality, band misses — where the
  scorer genuinely has something to choose between. Structure first, sampling
  second.
- **§9.5 stands but matters less.** The 1-in-6 substitution rate is now a
  property of a schema that is being replaced.

### 10.4 Revised order of work

| # | change | effort | expected |
|---|---|---|---|
| 1 | Stage E slot + constrained decoding | ~1 day | substitution and malt-in-fermenter → 0 |
| 2 | Eval set 6 → 25 cases, new scorer keys | ~1 day | makes everything below checkable |
| 3 | F1/F2/F3 code guards | ~2 h | catches what the schema cannot |
| 4 | `num_ctx` unification, consume `.web`/`.gap`, `web_query` | ~2 h | fixes three live defects |
| 5 | `misc` + sugar catalogue rows, unit support | ~2 days | qty/unit stop being null |
| 6 | C4 `ingredient_practice`, C3 exemplars, B resolve | ~3 days | amounts get an evidence basis |
| 7 | Best-of-N = 5 with the deterministic scorer | ~1 day | proportion quality |
| 8 | Yeast catalogue | ~2 days | FG stops being a guess |
| 9 | Self-directed retrieval, one round | ~1 day | the brewer's step 3/4 |

Items 1–4 are two days of work and fix every defect this investigation found.

---

## 11. Implementation ledger — built and measured 2026-09-16

Everything above this line is the plan as written *before* any of it was built.
This section is what actually happened, and it is kept separate so the two can be
compared rather than quietly reconciled. Where a measurement contradicts §1–§10,
the contradiction is recorded here and the original text is left standing.

### 11.1 §10.4 order of work — status

| # | change | status |
|---|---|---|
| 1 | Stage E slot + constrained decoding | ✅ shipped, `propose` v8 |
| 2 | Eval set 6 → 25 cases, new scorer keys | ✅ shipped |
| 3 | F1/F2/F3 code guards | ✅ shipped, **plus F4 and F5 the plan did not foresee** |
| 4 | `num_ctx`, consume `.web`/`.gap`, `web_query` | ✅ shipped |
| 5 | `misc` + sugar catalogue rows, unit support | ✅ shipped, `31_`/`32_` |
| 6 | C4 practice, C3 exemplars, B resolve | ✅ shipped, `35_`; ⚠️ **C5 not done** |
| 7 | Best-of-N = 5 with the deterministic scorer | ⬜ **not built** |
| 8 | Yeast catalogue | ✅ shipped, `33_`, 120 strains |
| 9 | Self-directed retrieval, one round | ⬜ **not built** |

Also not built, and each is a real gap rather than an oversight worth hiding:

- **C5 — decomposed retrieval.** §5 Phase 3 step 15 says switch the formulate
  path to `wf-step-retrieve-multi`. It still uses the single flat query.
- **Stage B's hard stop.** §3 routes `unknown` to *"tell the brewer, before
  building"*, and §5 Phase 3 makes it a verify criterion. Unknown terms are
  reported at the top of the sheet instead and the recipe is still built. That is
  weaker than specified. ⚠️ It may also be *better* — `unknown` in practice means
  a typo or a non-ingredient, and refusing to build a stout because one word did
  not resolve is a worse trade than building it and saying so. Worth deciding on
  purpose rather than by omission.
- **Stage A's `process` field** (all-grain / BIAB / extract).
- **Web-arm domain allow-list** (§3 C6's second half). The `web_query` half
  shipped and is doing the work: `measured` on recipe #92, gap `{poppi}` returned
  homebrewtalk and the UK homebrew forum, against the `vanillamart.com` Christmas
  cake the unsteered query produced.
- **Stage G**, and §9.6 ②'s retry-outcome logging.

### 11.2 ⭐ §10.2 replicated on the live stack

The slot is the largest result in this document and it holds outside the probe.
`measured` on recipe #91, the §1.4 brief end to end:

```
vanilla     2 each · boil        split and scraped
poppy seeds 50 g   · boil        crushed, macerated in rum
rum         200 ml · fermenter   used to macerate the others
```

Each by its real name, each with a method, no malt in the fermenter, ABV 8.07%
against a target of 8%. Eval case R07 scores `no_substitution` PASS.

### 11.3 ⚠️ §1.1 and §1.5 are now stale, and §1.5 was misdiagnosed

`brew.ingredients` is **302 rows**, not 150: fermentable 81, hop 72, adjunct 9,
misc 14, water_agent 6, yeast 120. Any later reading of §1.1 should start here.

⛔ **§1.5's `num_ctx` diagnosis was wrong, and the real cause is worse.** The
split is not "the chat node is the profile that was left behind". It is that
`62_obs_recipe_prompts.sql` SEEDS the `formulate` profile under
`ON CONFLICT (name) DO UPDATE`, and db-init only lands on the unified value
because `63_model_switch.sql` runs afterwards. Apply `62_` on its own — which
loading any new prompt version does — and the row silently reverts.

That is not a quiet failure. `63_` deliberately leaves `num_predict` OFF because
`propose` must emit closed JSON, so `num_ctx` is the *only* bound on generation.
At ~12k of prompt, 12288 left ~1.2k to generate in: run 187 died with *"asked for
JSON and returned prose"* because the JSON simply stopped, and run 186 is the
worse version of the same fault — a grist truncated so badly the fitter scaled it
**40×**. Fixed in `62_`'s seed.

⚠️ **A second, still-open drift sits underneath it.** `formulate` runs
`gemma4:12b` while the other four profiles run `gemma4:12b-it-q8_0` — genuinely
different models, 7.6 GB against 12 GB. `63_` sets all five to Q8 and `62_` seeds
`formulate` back to Q4, so **the two files disagree and whichever ran last wins.**
This reads as someone acting on D40 and is not: D40's own note says a real revert
would have been made in `63_`. Left unresolved on purpose — see §11.6.

### 11.4 ⛔ The prompt budget is breached, and §9.3 removed the planned answer

§5 Phase 3's verify is *"prompt total stays under 12k tokens"*. Live `propose`
`tokens_in` is **12,172–14,335**. Measured breakdown, sweet-stout brief with 8
library passages:

```
passages              3,956 tok   37.4%
catalogue             3,105 tok   29.3%   ← of which YEAST is 1,415 (120 strains)
rules + scaffold      2,344 tok   22.1%
exemplars               530 tok    5.0%
cohort practice         494 tok    4.7%
ingredient practice     107 tok    1.0%
```

§6 Risk 6 predicted this and named `f_catalogue_for_style` as the mitigation —
which §9.3 then withdrew on measurement. So the plan has no remaining answer, and
none has been invented here.

⭐ **The obvious candidate is the yeast list: 1,415 tokens for 120 strains, of
which the model picks exactly one, while `{{practice}}` already names the style's
top strains with their attenuation.** ⚠️ **This is deliberately NOT done.** §9.3
measured catalogue narrowing and found it *worse* — 4/6 clean against 5/6 — and
the story it killed ("fewer options, fewer bad picks") is the same story that
would justify this. §9.3 tested malts and hops, whose *proportions* the model must
reason about, and yeast is a single pick, so its conclusion does not obviously
transfer either way. **That is an argument for measuring it, not for assuming it.**
Anyone taking this on should run the 25-case set with the yeast list full and
style-filtered before changing anything.

### 11.5 Faults the build found that the investigation did not

All four are the same shape: a fact the pipeline could compute, asked of the
model instead — §1.4's table, extended.

| fault | what happened | where it ended up |
|---|---|---|
| **F4** hop in the mash | 100 g and 1,974 g of hops staged `mash` on recipes 93/94/95, and **none before the C3 block existed** — the corpus records first-wort hopping as stage `Mash` and the model imitates its exemplars. Tinseth scores it 0 IBU, so the sheet told the brewer to buy hops that do nothing | dropped and reported in `Validate proposal` |
| **F5** named ingredient simply missing | R07 asked for lactose *"for body"* and shipped none — not in items, not in additions, not in `not_available`. Stage B had resolved it to id 109 before the call | `propose` v11 states the routing; F5 reports any survivor |
| **F1 false positive** | The guard dropped the *genuine* catalogued vanilla because an addition shared its name — it fired the moment the catalogue gained a vanilla row | compares against the item's own catalogue name first |
| **yeast declined** | Helles picked W-34/70; the same prompt on a sweet stout picked nothing, twice, and FG went back to a model-invented number | picked in code from `nlq.cohort_stats` when the model declines |

⚠️ **F4 is the one worth remembering.** It is the first measured case of an
evidence block *causing* a fault: better inputs made the model imitate something
the arithmetic does not model. Adding evidence is not automatically safe, and the
guard had to be written after the block shipped, not before.

### 11.6 Still open, and genuinely needing a decision

- **§7 Q1 — yeast provenance.** Built as option (a), the plan's own
  recommendation: seeded from `corpus.yeasts` with
  `attrs.provenance = 'corpus_selfreported'`. Acted on, **not decided.**
  Spot-checks hold: US-05 81%, S-04 75%, WLP002 66.5%, W-34/70 83%.
- **§7 Q3 and Q4** are untouched. Q4 — a formulation text in `kb` — is still the
  highest-value non-code action, and §1.5's "no *Designing Great Beers*" stands.
- **D40's model split**, §11.3. Resolve it either by adding
  `WHERE name <> 'formulate'` to `63_`'s UPDATE, or by re-running the Q4/Q8
  comparison now that the case file is 25 cases rather than the single case D40
  rests on.
- **The 25-case set has not been run end to end.** Individual cases have. There is
  no committed baseline, so §5 Phase 0 step 3 is not satisfied and every "no
  worse than baseline" gate below it is currently unenforceable.

### 11.7 ⛔ db-init did not survive a fresh database, and now does

Adding two files to `docker-compose.yml`'s hardcoded list is only safe if the
list still runs. It was tested against an empty database rather than assumed,
and the run **failed at `29_brew_formulate.sql`**:

```
ERROR:  function brew.f_catalogue(text) does not exist
```

`29_` granted `brew.f_catalogue` about a hundred lines **above** the function's
own definition. A GRANT naming a function that does not exist is an error, not a
no-op, so under `ON_ERROR_STOP=1` the file aborted and db-init silently skipped
every later file — which on this list now includes `31_`, `32_`, `33_` and `35_`,
i.e. the entire catalogue and the entire evidence layer.

⚠️ **Pre-existing, and invisible for the same reason it survived.** The GRANT is
duplicated correctly beside the definition, and every restart after the first
found the function already there. It is the same trap the file's own header
describes, from the other direction. Fixed, and the full 22-file list now runs
clean end to end on an empty database.

⛔ **A second ordering fault is documented and deliberately NOT fixed.** Roles are
created in `50_roles.sql`, which runs *after* the loop, while 16 grant sites
across `15_`, `29_` and `60_` grant to `mem_writer` with no guard. `measured`: an
unguarded GRANT to a missing role is an `ERROR`, so a brand-new **cluster** dies
at `15_ref.sql` line 237. It has never bitten this machine because the roles
already exist. The fix is to create the roles before the loop — `50_` cannot
simply move, because it also does `GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA nlq`,
which has to follow every file that defines one. That is security-sensitive
role management and belongs in its own commit with its own fresh-cluster test,
not bundled into a feature landing. Noted in `docker-compose.yml` beside the list.

### 11.8 First measured baseline — R01–R09, 2026-09-16

§5 Phase 0 step 3 asks for a committed baseline. This is the first one. It is
**nine of twenty-five cases**, not the full set, and it is labelled as such
because a partial baseline quoted later as a full one is exactly how the six-case
set came to stand behind claims it could not support.

```
R01 floor          PASS   abv 4.23  ibu 38  srm 38.3  roast 15.0   (retried)
R02 control        PASS   abv 5.03  ibu 15  srm  4.9  roast  0.0
R03 two-way        FAIL   abv 5.56  ibu 38  srm 38.7  roast 15.0   roast outside [5,12]
R04 three-way      PASS   abv 8.04  ibu 11  srm 58.8  roast 15.0
R05 exclusion      PASS   abv 11.05 ibu 48  srm 69.1  roast 15.0
R06 contradiction  PASS   flags the conflict          (retried, band miss reported)
R07 substitution   PASS   abv 6.03  ibu 38  srm 46.8  no_substitution ✓  2 additions
R08 flavouring     PASS   abv 5.68  ibu 38  srm 46.2  no_substitution ✓  1 addition
R09 flavouring     FAIL   the capability errored; no recipe

PASS 7  FAIL 2  ERROR 0   suite 838 s   propose retried on 2 of 9
```

⭐ R02 is the load-bearing one: roast 0.0%, SRM 4.9 on a Munich Helles. The stout
cases are not gameable by always reaching for roast malt, and the catalogue
growing by 140 rows did not break style generality.

**⛔ Finding 1 — the roast ceiling is doing all the work, and that makes some
bands unreachable.** Five of the six dark cases land at **exactly 15.0%**. That
is `Validate proposal` clamping, every time, which means the prompt's stated
"8–15%" range is not being followed at all — the model proposes above the ceiling
and code trims it back. It passes wherever the case allows 15 (R01, R04, R05) and
fails where it does not: **R03 wants 5–12% for a "restrained roast" oatmeal
stout, and a ceiling-only clamp can never bring roast DOWN to 12.**

⚠️ Whether this is a regression is **not knowable** — there was no baseline before
this one, which is the whole reason Phase 0 exists. §9.3 measured a 12.4–15.3
spread on the v7 prompt, but on one case and possibly measured pre-clamp, so it
does not settle it. Two honest options, and they are different claims: either
R03's band is wrong for the style, or the pipeline needs a style-aware roast
*target* rather than a bare ceiling. ⛔ Do not "fix" this by lowering the clamp —
that would break R01, R04 and R05, which need 15.

**⛔ Finding 2 — R09 is generation degeneration, not prompt size.** The run took
**248 s** and died on *"Step 'propose' was asked for JSON and returned prose"*
with the JSON stopping mid-object after `"unit": "g",`. The obvious suspect was
the token budget, and it is measured wrong: reconstructing R09's exact prompt
gives **10,144 tokens against a 16,384 context — 6,240 tokens of headroom.** The
model had ample room and looped anyway, emitting `items` until the context ran
out. Successful runs emit 496–612 tokens.

⚠️ **This is §9.1's non-convergence, in the JSON output rather than the thinking
trace**, and it exposes a cost `63_model_switch.sql` did not account for. That
file deliberately removes `num_predict` for `formulate`, reasoning that a cap
guarantees `propose` cannot close its JSON. True, and incomplete: with no cap, a
degenerate run does not recover — it produces the same truncated JSON, four
minutes later, and takes the whole run down with it. A cap does not cause that
failure; it bounds what the failure costs.

⛔ **Not changed on one observation.** Overriding a documented ⛔ decision needs
more than n=1, and the run-64 measurement behind it (`num_predict` 1600 stopping
propose mid-object) was taken on an older prompt and schema that cannot be
compared to today's 496–612 tokens out. The next person should establish the rate
across the full 25 first; if it is not a one-off, `num_predict` at ~3× the
observed maximum is the obvious candidate, and it should be measured, not argued.
