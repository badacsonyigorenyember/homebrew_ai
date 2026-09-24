# Recipe Creation Workflow: Brainstorm

> Status: **idea / brainstorm** (2026-09-23). A clean-slate design that deliberately
> ignores what already exists. Print this and mark it up.
>
> Legend: `LLM` model call · `SQL` database query · `CODE` deterministic script ·
> `SEARCH` library/web retrieval · `GATE` decision point · `EXT` extension slot (later)

---

## 1. The one-sentence architecture

**The LLM decides *what* goes in the beer and *why*; code decides *how much*, and checks
that the result is the beer that was asked for.**

The LLM is used in three places only: understanding the question (S1), choosing
ingredients and proportions (S6), and writing the final recipe (S9). Everything else is
SQL or a script, which keeps the numbers reproducible and testable.

---

## 2. Flow diagram (print view)

```
                     ┌─────────────────────────────────────┐
                     │ S0  USER QUESTION                   │
                     └──────────────────┬──────────────────┘
                                        ▼
                     ┌─────────────────────────────────────┐
                     │ S1  UNDERSTAND -> BRIEF       [LLM] │
                     │     must / avoid / concepts /       │
                     │     sensory / style / targets       │
                     └──────────────────┬──────────────────┘
                                        ▼
                     ┌─────────────────────────────────────┐
                     │ S2  RESOLVE NAMES TO refs [SQL+LLM] │
                     │     "Citra" -> hop id               │
                     │     "American IPA" -> style id      │
                     └──────────────────┬──────────────────┘
                                        ▼
                               ┌─────────────────┐              ╔═════════════════════╗
                               │ G1 style known? ├─────no──────►║ E1 STYLE RESOLUTION ║
                               │          [GATE] │              ║    LOOP     (later) ║
                               └────────┬────────┘              ╚══════════╤══════════╝
                                        │ yes                              │
                                        ├◄─────────────────────────────────┘
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
   ┌─────────────────────────────────┐     ┌─────────────────────────────────┐
   │ S3  KNOWLEDGE         [SEARCH]  │     │ S4  TRENDS / PROFILE      [SQL] │
   │     library first, web for gaps │     │     targets, ingredient priors, │
   │     -> evidence pack + sources  │     │     ratios, process priors      │
   └────────────────┬────────────────┘     └────────────────┬────────────────┘
                    └───────────────────┬───────────────────┘
                                        ▼
                     ┌─────────────────────────────────────┐    ╔═════════════════════╗
                     │ S5  CANDIDATE POOL         [CODE]   │◄───║ E2a INVENTORY       ║
                     │     trend top-N + descriptor hits   │    ║     FILTER   (later) ║
                     │     + must_include - avoid          │    ╚═════════════════════╝
                     └──────────────────┬──────────────────┘
                                        ▼
                     ┌─────────────────────────────────────┐
              ┌─────►│ S6  SELECT & PROPORTION     [LLM]   │
              │      │     ids, roles, %, hop use, mash    │
              │      └──────────────────┬──────────────────┘
              │                         ▼
              │      ┌─────────────────────────────────────┐
              │  ┌──►│ S7  CALCULATE              [CODE]   │
              │  │   │     kg, g, OG, FG, ABV, IBU, SRM    │
              │  │   └──────────────────┬──────────────────┘
              │  │                      ▼
              │  │   ┌─────────────────────────────────────┐    ╔═════════════════════╗
              │  │   │ S8  VALIDATE               [CODE]   │◄───║ E2b SUBSTITUTION    ║
              │  │   │     style ranges, must / avoid,     │    ║     ENGINE   (later) ║
              │  │   │     trend outliers                  │    ╚═════════════════════╝
              │  │   └───┬─────┬────────┬──────────────────┘
              │  │       │     │        │ pass
              │  └───────┘     │        │
              │  fixable:      │        │
              │  auto-adjust   │        │
              └────────────────┘        │
              structural: back to S6    │
              (max 3 rounds)            │
                                        ▼
                     ┌─────────────────────────────────────┐
                     │ S9  WRITE RECIPE             [LLM]  │
                     │     recipe + reasoning + sources    │
                     └──────────────────┬──────────────────┘
                                        ▼
                     ┌─────────────────────────────────────┐    ╔═════════════════════╗
                     │ S10 SAVE + LOG              [SQL]   ├───►║ E3 FEEDBACK ->      ║
                     └─────────────────────────────────────┘    ║    TRENDS   (later) ║
                                                                ╚═════════════════════╝

   Double-line boxes (╔═╗) are extension slots: not built now, but the arrow is reserved.
```

## 3. Flow diagram (rendered view)

Same flow; renders in VS Code / GitHub preview.

```mermaid
flowchart TD
    S0([S0 User question]) --> S1[S1 Understand → Brief<br/>LLM]
    S1 --> S2[S2 Resolve names to refs<br/>SQL + LLM]
    S2 --> G1{G1 Style known?}
    G1 -- no --> E1[[E1 Style resolution loop<br/>later]]
    E1 --> G1
    G1 -- yes --> S3[S3 Knowledge: library → web<br/>SEARCH]
    G1 -- yes --> S4[S4 Trends / style profile<br/>SQL]
    S3 --> S5[S5 Candidate pool<br/>CODE]
    S4 --> S5
    E2a[[E2a Inventory filter<br/>later]] -.-> S5
    S5 --> S6[S6 Select & proportion<br/>LLM]
    S6 --> S7[S7 Calculate amounts & specs<br/>CODE]
    S7 --> S8{S8 Validate<br/>CODE}
    E2b[[E2b Substitution engine<br/>later]] -.-> S8
    S8 -- fixable: auto-adjust --> S7
    S8 -- structural: max 3 --> S6
    S8 -- pass --> S9[S9 Write recipe<br/>LLM]
    S9 --> S10[(S10 Save + log)]
    S10 -.-> E3[[E3 Feedback → trends<br/>later]]

    classDef ext stroke-dasharray: 5 5;
    class E1,E2a,E2b,E3 ext;
```

---

## 4. Step table: what each step needs and produces

Tick the boxes as you go. `MVP` = needed for the first functional version (`lib` = library
search only; web comes later).

| #   | Step                  | Type     | Needs (input)                          | Produces (output)                      | MVP | Designed | Built | Tested |
|-----|-----------------------|----------|----------------------------------------|----------------------------------------|:---:|:--------:|:-----:|:------:|
| S0  | User question         | -        | chat message                           | raw text                               | ✔   | ☐        | ☐     | ☐      |
| S1  | Understand → Brief    | LLM      | S0                                     | **Brief** (typed JSON, see §6)         | ✔   | ☐        | ☐     | ☐      |
| S2  | Resolve names to refs | SQL+LLM  | Brief, `refs.*`                        | Brief with `ref_id`s + unresolved list | ✔   | ☐        | ☐     | ☐      |
| G1  | Style known?          | GATE     | Brief.style                            | continue / ask user (E1 later)         | ✔   | ☐        | ☐     | ☐      |
| S3  | Knowledge             | SEARCH   | Brief concepts, sensory, unresolved    | **Evidence pack** with citations       | lib | ☐        | ☐     | ☐      |
| S4  | Trends / profile      | SQL      | style id, `trends.*` → `refs.*`        | **Style profile** (targets + priors)   | ✔   | ☐        | ☐     | ☐      |
| S5  | Candidate pool        | CODE     | S3, S4, must/avoid                     | **Candidate pool** per category        | ✔   | ☐        | ☐     | ☐      |
| S6  | Select & proportion   | LLM      | Brief, pool, profile, evidence         | **Selection** (ids, roles, %, no grams)| ✔   | ☐        | ☐     | ☐      |
| S7  | Calculate             | CODE     | Selection, profile targets, `refs` specs, batch | **Calc result** (amounts + specs) | ✔ | ☐     | ☐     | ☐      |
| S8  | Validate              | CODE     | Calc result, style ranges, Brief       | pass / fixable / structural + reasons  | ✔   | ☐        | ☐     | ☐      |
| S9  | Write recipe          | LLM      | Calc result, Selection rationale, evidence | final recipe text                  | ✔   | ☐        | ☐     | ☐      |
| S10 | Save + log            | SQL      | everything above                       | stored recipe + run trace              | ✔   | ☐        | ☐     | ☐      |
| E1  | Style resolution loop | LLM+SQL  | Brief without style                    | 1–3 candidate styles → user picks      |     | ☐        | ☐     | ☐      |
| E2a | Inventory filter      | CODE     | user inventory                         | pool restricted to what you own        |     | ☐        | ☐     | ☐      |
| E2b | Substitution engine   | CODE     | missing item, `refs` specs             | closest substitute + spec delta        |     | ☐        | ☐     | ☐      |
| E3  | Feedback → trends     | SQL      | brewed + rated recipes                 | weighted trends                        |     | ☐        | ☐     | ☐      |

Notes:

```
_______________________________________________________________________________________

_______________________________________________________________________________________

_______________________________________________________________________________________
```

---

## 5. Step-by-step notes

### S1 · Understand → Brief

**Is expanding it easy? Yes**, as long as the Brief is a **typed object with every field
optional**, not free text. Adding a field later is additive: old runs still validate.
The real cost of a new field is not parsing it, it is giving it a *consumer*
downstream. A field nobody reads is noise, so add fields when a later step needs them.

Two ideas worth building in from day one:

1. **Every field carries its source**: `user` | `inferred` | `default` | `missing`. This
   is what makes the E1 style loop trivial later ("style.source = missing → ask").
2. **Split hard constraints from soft preferences.** `must_include`, `avoid`, style and
   explicit targets are *hard* (validator enforces them). Concepts and sensory words are
   *soft* (they steer selection, but nothing fails if one is missed).

Fields to consider beyond your list: target ABV / IBU / colour, batch size, efficiency
(from an equipment default), and `open_questions` (things the model could not decide).

- [ ] Brief schema written
- [ ] LLM prompt with structured output
- [ ] Source tag on every field

### S2 · Resolve names to refs *(new step, and the one I'd push for)*

Before anything can be calculated, "Citra", "Maris Otter", "no crystal" and "NEIPA" must
become `refs` rows. Without ids you have no alpha acid, PPG or colour, so the calculator
has nothing to work with. Do it as trigram/alias match first, with LLM
disambiguation only for ties.

⚠️ `avoid` is often a **category**, not an item ("no crystal malts", "no American hops").
So `refs` needs a role/category taxonomy the avoid list can point at.

Unresolved names go to S3 (web) instead of being dropped.

- [ ] Alias / fuzzy match per refs table
- [ ] Category-level avoid supported
- [ ] Unresolved list handed to S3

### S3 · Knowledge (library → web)

Search per concept and sensory descriptor, library first; web only for what the library
cannot answer. The output should be a **structured evidence pack**, where each finding is
`{claim, suggests_ref_id?, source, confidence}`, so it can *add candidates* in S5
instead of only being prompt text.

A cheaper path for sensory words: if `refs` carries descriptor tags (hop aroma tags, malt
flavour tags), "tropical, dank" → hop candidates is a **SQL query**, not a search.
Use search for concepts the tags cannot express ("like a Belgian but crisp").

S3 and S4 are independent given the Brief, so run them **in parallel**.

- [ ] Library search per concept
- [ ] Web fallback for gaps + unresolved
- [ ] Descriptor tags on refs (hops, malts, yeast)

### S4 · Trends / style profile

Returns one **style profile**: target ranges plus ingredient and process priors.
Detailed ideas in §7.

- [ ] Style targets (OG/FG/IBU/SRM/ABV ranges)
- [ ] Hop / fermentable / yeast / misc priors
- [ ] Fallback when sample size is small

### S5 · Candidate pool

Deterministic union: trend top-N per category + descriptor/evidence hits +
`must_include`, minus `avoid`. Each candidate keeps *why* it is there (`trend`, `descriptor`,
`evidence`, `user`) and its trend stats.

This is the step that stops the LLM from inventing ingredients: **S6 may only pick ids
from this pool.**

**▶ E2a slot (inventory):** filter the pool to what the user owns. Two modes worth
planning for: `strict` (only owned) and `prefer` (owned first, others allowed).

- [ ] Pool builder
- [ ] Reason + stats kept per candidate

### S6 · Select & proportion (LLM)

To your question, *"am I right?"*: **yes, with one refinement.** The LLM should output
**choices and proportions, never grams**:

- fermentables: `ref_id`, role (base / specialty / adjunct / sugar), **% of grist**
- hops: `ref_id`, use (bittering / flavour / whirlpool / dry hop), **g/L for late
  additions**; the bittering addition is left for the script to solve
- yeast: `ref_id`
- misc: `ref_id`, use, timing
- mash temperature (a *choice* that drives body and FG, not a calculation)
- chosen targets inside the style range (for example "OG 1.062, IBU 35")
- a short rationale per item, pointing at evidence / trend ids

The prompt gets the Brief, the pool with trend stats, and the style profile, and is told
to stay inside the trend p10–p90 ranges unless the Brief says otherwise.

- [ ] Selection schema
- [ ] Prompt with pool + profile
- [ ] Rejects ids not in pool

### S7 · Calculate (code)

The trick is picking **balancing variables**: most amounts come straight from trend
ratios, and one item per category is solved to hit the target.

| Quantity         | Set by                               | Balancing variable (solved)       |
|------------------|--------------------------------------|-----------------------------------|
| OG               | target from S6                       | **base malt kg**, specialties fixed by % |
| IBU              | target from S6                       | **bittering hop g** (Tinseth), after late hops |
| Late / dry hops  | trend g/L                            | -                                 |
| FG               | yeast attenuation × mash-temp adjustment × fermentability | - (it is an estimate) |
| ABV              | from OG, FG                          | -                                 |
| SRM              | Morey from grist                     | - (checked, not solved)           |

Calculation order matters: **gravity → IBU** (utilisation depends on boil gravity)
**→ FG → ABV → SRM**. Batch size, efficiency, boil-off and losses come from an equipment
default (**▶ E5 slot** later).

⚠️ FG is the weakest number: attenuation adjusted for mash temperature is a heuristic.
Label it as an estimate in the output.

- [ ] Gravity solver (base malt balances)
- [ ] Tinseth IBU solver (bittering balances)
- [ ] FG estimate, ABV, SRM (Morey)
- [ ] Unit tests against a few known recipes

### S8 · Validate (code)

Checks: OG/FG/ABV/IBU/SRM inside style range and user targets · every `must_include`
present · nothing from `avoid` (including category-level) · each % / g/L inside trend
p5–p95 (warning, not failure) · BU:GU sane.

Three outcomes:

- **pass** → S9
- **fixable** (numbers only, for example IBU 4 over) → auto-adjust the balancing variable → S7
- **structural** (for example SRM far out because of the chosen malts) → back to S6 with the
  reasons; **max 3 rounds**, then return the best attempt with warnings

**Conflict policy** when things disagree:
`hard user constraints > style ranges > soft preferences > trend priors`.
If a `must_include` is rare for the style (for example 0% in trends), don't fail. Warn and
say so in the recipe.

**▶ E2b slot (substitution):** when a selected item is unavailable, swap it for the
nearest `refs` item in the same substitution group (fermentable: type + colour + PPG; hop:
alpha + aroma tags; yeast: attenuation + temperature + flavour profile), then re-run S7.

- [ ] Range + constraint checks
- [ ] Auto-adjust loop
- [ ] Structural loop back to S6 with reasons

### S9 · Write recipe (LLM)

Writing only, with no new decisions. It gets the final numbers and the rationale and
produces the recipe, the "why" behind each choice with citations, and the warnings.

- [ ] Output template
- [ ] Citations from evidence pack

### S10 · Save + log

Persist **every intermediate object** (Brief, evidence pack, profile, pool, selection,
calc result, validation). This pays for itself three ways: debugging, evals, and the
**▶ E4 slot (refine)**: "make it more bitter" re-enters at S6/S7 with saved state instead
of starting over.

**▶ E3 slot (feedback):** brewed + rated recipes feed back into trend weighting.

- [ ] Recipe stored
- [ ] Each step output logged per run

---

## 6. Data contract: the `RecipeRun` envelope (sketch)

**One object per run, passed down the whole workflow and nested by step.** Each step owns
exactly one slot and fills it. Dump the object after any step and you see the whole run
so far. S10 saves it by serialising it, and E4 (refine) reloads it, clears everything
from S6 on, and re-runs.

**The envelope is the container, not the interface.** Steps are *called with the slots
they need*, not with the whole object, so the §4 "Needs" column stays true and every step
can be tested in isolation.

### 6.1 Rules

1. **One owner per slot.** A step writes only its own slot (table in §6.3). The single
   exception is S2, which fills the `ref_id`s *inside* `brief`. It resolves the Brief's
   own names, so it doesn't get a slot of its own.
2. **Write-once, except `attempts`.** The S6 → S8 loop *appends* one entry per round, so
   failed rounds are kept for debugging and evals instead of being overwritten.
3. **Steps take arguments, the orchestrator assigns.** A step returns its slot. It never
   receives or mutates `run`.
4. **An LLM step gets a projection and returns only its slot.** It never sees or returns
   the whole object: that costs tokens, lets it second-guess earlier steps (S9 must make
   no new decisions), and a model asked to return the whole object will quietly rewrite
   or drop fields. Its output is schema-validated *before* it is assigned.
5. **Every slot is optional.** `null` means "not reached yet". Adding a field is additive.
   Bump `schema_version` only when a field is renamed or removed.
6. **Parallel steps write disjoint slots.** S3 → `evidence` and S4 → `profile`, so merging
   the two branches is trivial.

### 6.2 Shape

```jsonc
// RecipeRun: the one object that travels S0 → S10
{
  "id": "run_…",
  "schema_version": 1,
  "question":  "…",                           // S0  raw user text
  "brief":     { /* Brief */ },               // S1, ref_ids filled by S2
  "evidence":  { "findings": [ /* … */ ] },   // S3
  "profile":   { /* StyleProfile */ },        // S4
  "pool":      { /* CandidatePool */ },       // S5
  "attempts":  [                              // S6–S8, one entry per round
    {"kind": "initial", "selection": {}, "calc": {}, "validation": {}}
  ],
  "recipe":    { /* Recipe */ },              // S9
  "trace":     [{"step": "S1", "ms": 2140, "model": "…", "tokens": 1830, "error": null}]
}
```

The slots:

```jsonc
// brief (S1 → S2)
{
  "style":        {"value": null, "ref_id": null, "source": "missing"},
  "must_include": [{"text": "Citra", "ref_id": null, "kind": "item"}],
  "avoid":        [{"text": "crystal malt", "ref_id": null, "kind": "category"}],
  "concepts":     ["hazy", "soft bitterness"],
  "sensory":      {"aroma": [], "flavour": [], "appearance": [], "mouthfeel": []},
  "targets":      {"abv": null, "ibu": null, "srm": null},
  "batch":        {"volume_l": 20, "efficiency": 0.72, "source": "default"},
  "unresolved":   [],            // S2: names with no refs match → S3
  "open_questions": []
}

// evidence (S3)
{
  "findings": [
    {"id": "ev3", "claim": "…", "suggests_ref_id": 7, "source": "…", "confidence": 0.8}
  ]
}

// profile (S4): style description, targets, trend priors
{
  "style":   {"ref_id": 21, "name": "American IPA", "description": "…"},
  "targets": {"og": {"min": 1.056, "max": 1.070, "p10": 1.058, "p50": 1.063, "p90": 1.068}, ...},
  "priors":  {"hops": [{"ref_id": 7, "use": "dry_hop", "g_per_l": {"p10": 4, "p50": 7, "p90": 12}, "n": 140}], ...},
  "fallback": null               // e.g. "parent_style" when n is too small
}

// pool (S5): the only ids S6 may pick
{
  "fermentables": [{"ref_id": 12, "reasons": ["trend", "user"], "stats": {"p50": 80, "n": 210}}],
  "hops": [], "yeast": [], "misc": []
}

// attempts[n].selection (S6 → S7): proportions only, no grams
{
  "fermentables": [{"ref_id": 12, "role": "base", "pct": 80}, ...],
  "hops":  [{"ref_id": 7, "use": "dry_hop", "g_per_l": 8}, {"ref_id": 3, "use": "bittering"}],
  "yeast": {"ref_id": 44},
  "misc":  [],
  "mash_temp_c": 67,
  "targets": {"og": 1.062, "ibu": 35},
  "rationale": [{"ref_id": 7, "why": "...", "evidence": ["ev3", "trend:hop:7"]}]
}

// attempts[n].calc (S7)
{
  "amounts": [{"ref_id": 12, "kg": 4.8}, {"ref_id": 3, "g": 22, "time_min": 60}, ...],
  "specs":   {"og": 1.062, "fg": 1.012, "abv": 6.6, "ibu": 35, "srm": 6.1},
  "estimates": ["fg"]            // FG is a heuristic; say so in the recipe
}

// attempts[n].validation (S8)
{
  "outcome": "fixable",          // pass | fixable | structural
  "reasons": [{"check": "ibu_in_style", "value": 74, "range": [40, 70], "severity": "fail"}]
}

// recipe (S9)
{"attempt": 2, "text": "…", "citations": ["ev3"], "warnings": []}
```

`attempts[].kind` is `initial`, `auto_adjust` (S8 fixable → S7, same selection with the
balancing variable moved) or `reselect` (S8 structural → S6). "Max 3 rounds" counts
`reselect` entries. `recipe.attempt` records which attempt was written up: the passing
one, or the best one after the round limit.

### 6.3 Who reads and writes what

This table is the contract. A step that needs a slot not listed here means the table
needs changing, not the step.

| Step | Reads (its projection)                                          | Writes                    |
|------|-----------------------------------------------------------------|---------------------------|
| S1   | `question`                                                      | `brief`                   |
| S2   | `brief`                                                         | `brief.*.ref_id`, `brief.unresolved` |
| G1   | `brief.style`                                                   | -                         |
| S3   | `brief.concepts`, `brief.sensory`, `brief.unresolved`           | `evidence`                |
| S4   | `brief.style.ref_id`                                            | `profile`                 |
| S5   | `evidence`, `profile.priors`, `brief.must_include`, `brief.avoid` | `pool`                  |
| S6   | `brief`, `pool`, `profile`, `evidence`, last `validation.reasons` | new `attempts[n].selection` |
| S7   | `attempts[n].selection`, `profile.targets`, `brief.batch`       | `attempts[n].calc`        |
| S8   | `attempts[n].calc`, `profile.targets`, `brief.must_include`, `brief.avoid` | `attempts[n].validation` |
| S9   | chosen attempt's `calc` + `selection.rationale`, cited `evidence` only | `recipe`           |
| S10  | the whole run                                                   | DB                        |

### 6.4 In Python

The ingest scripts use `dataclasses`. Use **Pydantic** here instead: LLM output has to be
validated, and Pydantic gives the JSON schema for structured output
(`Brief.model_json_schema()`) plus validation (`Brief.model_validate_json(text)`) and S10's
serialisation (`run.model_dump_json()`) for free.

```python
class Attempt(BaseModel):
    kind: Literal["initial", "auto_adjust", "reselect"]
    selection: Selection
    calc: Calc | None = None
    validation: Validation | None = None

class RecipeRun(BaseModel):
    id: str
    schema_version: int = 1
    question: str
    brief: Brief | None = None
    evidence: Evidence | None = None
    profile: StyleProfile | None = None
    pool: CandidatePool | None = None
    attempts: list[Attempt] = []
    recipe: Recipe | None = None
    trace: list[TraceEntry] = []
```

The orchestrator is the only code that touches `run`, and it reads like the flow diagram:

```python
def run_workflow(question: str) -> RecipeRun:
    run = RecipeRun(id=new_run_id(), question=question)
    run.brief = understand(run.question)                             # S1  LLM
    run.brief = resolve_refs(run.brief)                              # S2
    if run.brief.style.ref_id is None:                               # G1
        return ask_for_style(run)
    run.evidence, run.profile = gather(run.brief)                    # S3 ‖ S4
    run.pool = build_pool(run.evidence, run.profile, run.brief)      # S5

    feedback, kind = None, "initial"
    for _ in range(MAX_RESELECT):
        sel = select(run.brief, run.pool, run.profile, run.evidence, feedback)  # S6 LLM
        for _ in range(MAX_ADJUST):
            calc = calculate(sel, run.profile.targets, run.brief.batch)         # S7
            val = validate(calc, run.profile, run.brief)                        # S8
            run.attempts.append(Attempt(kind=kind, selection=sel, calc=calc, validation=val))
            if val.outcome != "fixable":
                break
            sel, kind = auto_adjust(sel, val), "auto_adjust"
        if val.outcome == "pass":
            break
        feedback, kind = val.reasons, "reselect"

    run.recipe = write_recipe(best_attempt(run.attempts), run.evidence)          # S9  LLM
    save(run)                                                                    # S10
    return run
```

An LLM step builds its prompt from its arguments and returns only its slot:

```python
def understand(question: str) -> Brief:
    text = llm(prompt=S1_PROMPT.format(question=question),
               schema=Brief.model_json_schema())
    return Brief.model_validate_json(text)      # fails loudly instead of corrupting run
```

`trace` is filled by a small `@step("S1")` wrapper around each step (timing, model,
tokens, error), so step code stays free of logging.

### 6.5 In n8n (if it is built there)

The envelope goes against n8n's grain: Postgres, HTTP Request and AI Agent nodes replace
`$json` with their own output. The cleanest mapping is **one sub-workflow per step,
envelope in → envelope out**. The step's inner nodes do what they like, and a final Code
node merges the result back into the incoming envelope (`{...envelope, profile: $json}`).
⚠️ Every sub-workflow must be active, and re-activated plus `docker restart n8n` after any
`import:workflow` (see `CLAUDE.md`).

- [ ] `RecipeRun` model + slot models
- [ ] Orchestrator with `attempts` loop
- [ ] `@step` trace wrapper
- [ ] Projection per LLM step (S1, S6, S9)

---

## 7. Trend ideas (S4)

Your list (popularity, ratio, amount, co-occurrence, specs for substitution) is the right
core. Additions, roughly in priority order:

| Trend                         | What it stores (per style)                                  | Why it helps                                   | When  |
|-------------------------------|-------------------------------------------------------------|------------------------------------------------|:-----:|
| **Percentiles, not averages** | p10 / p50 / p90 of every % and g/L                          | gives S6 a range and S8 an outlier test        | now   |
| **Sample size `n`**           | recipe count behind each stat                               | don't trust n < ~10; fall back to parent style | now   |
| **Usage by role**             | hops split by bittering / whirlpool / dry hop; malts by role | same hop, different job, different amounts     | now   |
| **Real vital stats**          | actual OG/FG/IBU/SRM distribution of recipes                | "what brewers do" vs the guideline range       | now   |
| **Co-occurrence with lift**   | pairs that appear together *more than chance*               | "what goes with Citra?" beyond raw popularity  | soon  |
| **Process priors**            | mash temp, boil time, ferment temp, dry-hop day             | S6 picks mash temp from data, not a guess      | soon  |
| **Recipe shape**              | number of hops / malts per recipe, base-malt share           | stops 9-malt kitchen-sink recipes              | soon  |
| **Substitution groups**       | fermentable: type + colour band + PPG; hop: alpha + tags    | powers E2b                                     | E2    |
| **Water profile**             | sulfate:chloride ratio distribution                         | powers a water-chemistry slot                  | later |
| **Time trend**                | popularity per year → rising / falling                      | separates *norm* from *trend*                  | later |
| **Source weighting**          | weight by source quality / medal / rating                   | good recipes count more (links to E3)          | later |

Structural rule: **every trend row references a `refs` id** (style, hop, fermentable,
yeast, misc). Trends are *derived* data (rebuildable from the recipe corpus, for example
materialised views), and `refs` stays the single source of truth for specs.

---

## 8. Extension slots: where they plug in

| Slot | What                              | Plugs in at            | Needs first                                  |
|------|-----------------------------------|------------------------|----------------------------------------------|
| E1   | Style resolution loop             | G1 (after S2)          | `source` tag on Brief.style; style descriptions searchable |
| E2a  | Inventory: "use only what I have" | S5 (pool filter)       | user inventory table keyed to `refs`         |
| E2b  | Substitution engine               | S8 (and S6 re-select)  | substitution groups + spec-distance function |
| E3   | Feedback → trends                 | S10 → S4               | brewed/rated flag on saved recipes           |
| E4   | Conversational refine             | re-enter at S6 / S7    | every step output persisted (S10)            |
| E5   | Equipment profile                 | S7                     | efficiency / losses / boil-off per user      |
| E6   | Water chemistry                   | S7 / S8                | water trends + salt calculator               |

For E1, the style guess can come from two signals: sensory/concept text matched against
style descriptions, and an **ingredient fingerprint** (must_include matched against
trends, so Citra + oats + low IBU → NEIPA). Offer the top 3 and let the user pick, then
resume at G1.

---

## 9. Suggested build order (MVP)

1. Brief schema + S1 prompt (require style for now; G1 just asks)
2. S2 resolve to refs
3. S4 trends: percentiles + `n` + role, for hops / fermentables / yeast
4. S7 calculator + unit tests, **before** any LLM selection (test with hand-written selections)
5. S5 pool + S6 selection
6. S8 validator (auto-adjust only at first; structural loop second)
7. S9 writer + S10 logging
8. S3 library search → web fallback

Notes:

```
_______________________________________________________________________________________

_______________________________________________________________________________________

_______________________________________________________________________________________

_______________________________________________________________________________________
```
