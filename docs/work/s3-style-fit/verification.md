# Verification: s3-style-fit

Overall: ✅ all 12 checks and 535 tests pass

Run 2026-10-15 at 86dd51e, branch `s3-style-fit`, against the running stack. Brief acceptance criteria A1–A10 are checked as amended in the brief's Deviations.

## Part 1: Summary

🎯 **Goal:** `level(style, ingredient, usage, dose)` answers required / typical / allowed / out of style / changes style, with a "because", for 26 styles and no recipe corpus.

🛠️ **How:** Ingredient tags derived by code (`loaders/tags.py`); style envelopes extracted offline by the LLM and reviewed by you (`loaders/style_envelopes.py`); usage effects, cut points and `app.style_level` / `app.style_fit_recipe` in SQL (`db/033`, `db/034`).

🤔 **Why this way:** the corpus was dropped (D7), so cut points come from the books and your answers, envelopes from reviewed guideline text, and the `fermentable_style` lists replace the popularity bump.

🏁 **Result:** 26 reviewed envelopes (24 with sensory rows), 89 of 89 hops tagged, 53 golden cases and the Citra table pass, and 130 ingredient lines of the 22 reference recipes are rated with only the 3 brief deviations and 5 accepted lines flagged.

### 🚦 Steps

- ✅ 📝 **Brief:** drafted with the abandoned s2-corpus dependency removed and 5 user answers folded in; approved (b2b82f7).
- ✅ 🗺️ **Plan:** 10 tasks; the STYLE-FIT §6 fix added; approved (8bd0d9c).
- ⚠️ 🔨 **Implement:** all 10 tasks done, the three user stops answered (26 envelopes; cut points and golden set; 4 reference recipes).
  - ⚠️ `test_db_enzyme_and_boil` was already failing (it read a moved s2 report); fixed in ee54628.
  - ⚠️ A stash/pop slip in Task 2, nothing lost.
  - ⚠️ Prose keyword scans can mislead (Acidulated Malt tagged sour); later fixed by the vocabulary.
  - ⚠️ One API rate-limit failure mid-run in Task 6, resumed.
  - ⚠️ Task 6 drafts were committed before the user's answer (fa8119d), marked unapproved.
  - ⚠️ Sterling hop removed at your request (9908734); b07/b10/b12/b19 reference recipes and b22's roast min adjusted at your decision.
- ❌ 🔍 **Review:** first verdict fixes needed (1 must-fix: the colour check was skipped on 11 of 22 recipes; 4 should-fix) 🔧 fixed in 845e219, 4a7934d, 1abfe1c, fadabd2; re-review "ready for testing" with should-fix #11–#14 🔧 fixed in 86dd51e.
  - ❌ must-fix #1: colour check skipped on 11 of 22 reference recipes (flakes, honey, lactose had no colour) 🔧 fixed in 845e219 and 4a7934d (flake colours sourced, lower-bound rule, b19 refitted in 1abfe1c).
  - ⚠️ Notes #6–#10, #15, #16 left as notes (no fix asked).
- ✅ 🧪 **Verify:** every acceptance criterion A1–A10 has a passing check, and the full suite is green. 🧮 spot checks ✅ 12/12 · 🧪 tests ✅ 535/535

👀 **Start here:** run the Citra table in Part 2 (example 1): the same hop comes out `out_of_style` in an Irish Stout whirlpool and `typical` in an American Stout whirlpool, each with its quote.

📁 **Changed files:**
- `PROJECT.md`
- `db/011_ref_sources.sql`
- `db/012_style_fit.sql`
- `db/033_style_fit_effects.sql`
- `db/034_style_level.sql`
- `db/035_drop_sterling.sql`
- `docs/DATABASE.md`
- `docs/RECIPE-ROADMAP.md`
- `docs/STYLE-FIT.md`
- `docs/WORKFLOW-ROADMAP.md`
- `docs/work/s3-style-fit/brief.md`
- `docs/work/s3-style-fit/cut-points.md`
- `docs/work/s3-style-fit/envelope-review-proposals.toml`
- `docs/work/s3-style-fit/envelope-review.md`
- `docs/work/s3-style-fit/golden-review.md`
- `docs/work/s3-style-fit/plan.md`
- `docs/work/s3-style-fit/report.md`
- `docs/work/s3-style-fit/review.md`
- `docs/work/s3-style-fit/verification.md`
- `loaders/adjunct_products.py`
- `loaders/adjuncts.py`
- `loaders/hop_products.py`
- `loaders/hops.py`
- `loaders/style_envelope.schema.json`
- `loaders/style_envelope_prompt.md`
- `loaders/style_envelopes.py`
- `loaders/style_envelopes.toml`
- `loaders/style_fit_vocab.toml`
- `loaders/tags.py`
- `tests/fixtures/reference_recipes.toml`
- `tests/fixtures/style_fit_golden.toml`
- `tests/test_adjuncts.py`
- `tests/test_fermentable_facts.py`
- `tests/test_formulation_check.py`
- `tests/test_hops.py`
- `tests/test_style_envelopes.py`
- `tests/test_style_fit_effects.py`
- `tests/test_style_fit_golden.py`
- `tests/test_style_fit_recipe.py`
- `tests/test_style_level.py`
- `tests/test_tags.py`

## Part 2: Showcase

| Function / job | What it does |
|---|---|
| `python -m loaders.tags` | Loads the vocabulary and derives `ref.ingredient_tag` for every hop, fermentable and yeast; unknown words go to `ref.ingredient_review`, never guessed |
| `python -m loaders.style_envelopes` | Loads the 26 reviewed style envelopes (`ref.style_sensory`, `style_character`, `style_ingredient`) |
| `app.style_level(style, ingredient_id, usage, dose)` | One ingredient, used one way, in one style: level plus a because |
| `app.style_fit_recipe(recipe)` | Whole recipe: a level per line, the required check, the recipe-total "too little" check |
| `app.style_fit_cut_points()` | Every cut point as JSON with its basis (book and page, or "set by the user") |

**1. The Citra table (15B Irish Stout vs 20B American Stout)**

```bash
.venv/bin/python - <<'E'
import sys; sys.path.insert(0, ".")
from loaders.db import connect
from tests.test_style_fit_golden import CASES, run_case
c = connect()
for case in CASES:
    if case["id"].startswith("c0"):
        r = run_case(c, case)
        print(case["id"], case["style"], case["usage"], case["dose"], "->", r["level"])
E
```

```text
c01 15B boil {'minutes': 60, 'g_per_l': 1.0, 'ibu': 35} -> allowed
c02 15B whirlpool {'g_per_l': 2.0} -> out_of_style
c03 15B dry_hop {'g_per_l': 8.0} -> out_of_style
c04 20B boil {'minutes': 60, 'g_per_l': 1.0, 'ibu': 50} -> allowed
c05 20B whirlpool {'g_per_l': 2.0} -> typical
c06 20B dry_hop {'g_per_l': 8.0} -> out_of_style
```

**2. Citra in a whirlpool of an Irish Stout, with the because**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select app.style_level('15B',(select id from ref.ingredient where kind='hop' and name='Citra'),'whirlpool','{\"g_per_l\":2.0}'::jsonb)"
```

```text
{"level": "out_of_style", "because": "wrong character: citrus, grapefruit, lime, tropical vs earthy: 'Balancing factors may include some creaminess, medium-low fruitiness, or medium earthy hop flavor.'. too much: 0.0450 mL/L oil is medium, Irish Stout (15B) allows up to low: 'Low earthy or floral hop aroma optional.'. wrong character: citrus, grapefruit, lime, tropical vs earthy, floral: 'Low earthy or floral hop aroma optional.'."}
```

**3. Adjuncts: named by the style's characteristic ingredients or not**

```bash
for c in "16A Lactose boil 5" "19C Lactose boil 5" "1C Flaked_Corn mash 15" "18B Flaked_Rice mash 10"; do set -- $c; docker exec supabase-db psql -U postgres -d postgres -tAc "select '$1 $2: ' || (app.style_level('$1',(select id from ref.ingredient where name=replace('$2','_',' ') limit 1),'$3',jsonb_build_object('pct',$4))->>'level')"; done
```

```text
16A Lactose: typical
19C Lactose: out_of_style
1C Flaked_Corn: typical
18B Flaked_Rice: out_of_style
```

**4. A yeast that is too clean for the style (US-05 in a Weissbier)**

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select app.style_level('10A',(select id from ref.ingredient where name='SafAle US-05'),'ferment','{\"ferm_c\":19}'::jsonb)"
```

```text
{"level": "out_of_style", "because": "too little: esters is very low, Weissbier (10A) wants at least medium: 'Moderate to strong esters and phenols, typically banana and clove, often well balanced and typically stronger than the malt.'. too little: phenols is none, Weissbier (10A) wants at least medium: 'Moderate to strong esters and phenols, typically banana and clove, often well balanced and typically stronger than the malt.'."}
```

**5. The required check: 15B needs a roasted fermentable (reference recipe b05, then with the Roasted Barley swapped for pale malt)**

```bash
.venv/bin/python - <<'E'
import sys, json, copy; sys.path.insert(0, ".")
from loaders.db import connect
from tests.test_reference_recipes import RECIPES, build_input
c = connect()
def req(r): return c.execute("select app.style_fit_recipe(%s::jsonb)", (json.dumps(build_input(c, r)),)).fetchone()[0]["required"]
r = next(x for x in RECIPES if x["brief"] == "b05")
print("with roasted barley:", [(x["requirement"], x["met"]) for x in req(r)])
s = copy.deepcopy(r)
for f in s["fermentable"]:
    if f["name"] == "Roasted Barley": f["producer"], f["name"] = "Weyermann", "Pale Ale Malt"
print("without roast:      ", [(x["requirement"], x["met"]) for x in req(s)])
E
```

```text
with roasted barley: [('a roast fermentable', True)]
without roast:       [('a roast fermentable', False)]
```

**6. The 22 reference recipes: only the lines the briefs or you accepted are flagged**

```bash
.venv/bin/python - <<'E'
import sys, json; sys.path.insert(0, ".")
from loaders.db import connect
from tests.test_reference_recipes import RECIPES, build_input
c = connect(); tot = bad = 0
for r in RECIPES:
    out = c.execute("select app.style_fit_recipe(%s::jsonb)", (json.dumps(build_input(c, r)),)).fetchone()[0]
    for l in out["lines"]:
        tot += 1
        if l["level"] in ("out_of_style", "changes_style") or l["level"] is None:
            bad += 1; print(r["brief"], out["style_code"], l["name"], l["level"])
    if out["too_little"]: print(r["brief"], "too_little", out["too_little"])
print("recipes", len(RECIPES), "lines", tot, "flagged/unrated", bad)
E
```

```text
b08 5D Magnum out_of_style
b08 5D Hallertau Mittelfrüh out_of_style
b16 18B Flaked Rice out_of_style
b18 15A Caramel 100 Malt out_of_style
b18 15A Roasted Barley out_of_style
b18 15A Carafa Special Type 1 out_of_style
b19 17C Honey out_of_style
b20 19C Lactose out_of_style
recipes 22 lines 130 flagged/unrated 8
```

The 8: b16 rice, b19 honey and b20 lactose are the briefs' own deviations; b08 (about 50 IBU asked, 5D allows 22–40) and b18 (20 SRM asked, 15A allows 9–14) are the 5 lines you accepted.

## Part 3: Spot checks

### ✅ C1 · Every hop tagged or flagged (A1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.hop h where not exists (select 1 from ref.ingredient_tag t where t.ingredient_id=h.ingredient_id) and not exists (select 1 from ref.ingredient_review r where r.ingredient_id=h.ingredient_id)"
```

| Expected | Actual | Result |
|---|---|---|
| 0 hops with neither a tag nor a review flag | 0 (89 hops, 89 with tags, 0 flagged hops; 38 yeasts flagged) | ✅ pass |

### ✅ C2 · Tagging is repeatable and a new synonym re-tags (A2)

```bash
.venv/bin/python -m pytest -p no:cacheprovider -q tests/test_tags.py -k "retag or synonym"
```

| Expected | Actual | Result |
|---|---|---|
| 2 passed (`test_retag_is_identical`, `test_new_synonym_retags`) | 2 passed, 8 deselected | ✅ pass |

### ✅ C3 · 26 styles with reviewed characteristic ingredients and quotes (A3)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select (select count(distinct style_id) from ref.style_ingredient where reviewed), (select count(*) from ref.style_ingredient where not reviewed or quote is null or quote=''), (select count(distinct style_id) from ref.style_sensory), (select count(*) from ref.style_sensory where not reviewed or quote is null or quote='')"
```

| Expected | Actual | Result |
|---|---|---|
| 26 styles reviewed; 0 unreviewed or quote-less ingredient rows; 24 styles with sensory rows (31B and Specialty Honey Beer have none, brief Deviations); 0 bad sensory rows | 26 / 0 / 24 / 0 | ✅ pass |

### ✅ C4 · Citra table reproduces exactly (A4)

```bash
.venv/bin/python -m pytest -p no:cacheprovider -q tests/test_style_fit_golden.py -k "citra or m3 or c0"
```

| Expected | Actual | Result |
|---|---|---|
| allowed, out_of_style, out_of_style, allowed, typical, out_of_style (see Part 2, example 1) | the six levels match; 8 passed | ✅ pass |

### ✅ C5 · Golden set passes, no `style_rule` row behind it (A5)

```bash
.venv/bin/python -m pytest -p no:cacheprovider -q tests/test_style_fit_golden.py; docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.style_rule"
```

| Expected | Actual | Result |
|---|---|---|
| 53 cases + 2 tests pass; 0 `style_rule` rows | 55 passed; 0 | ✅ pass |

### ✅ C6 · 15B needs a roast malt (A6)

See Part 2, example 5.

| Expected | Actual | Result |
|---|---|---|
| met false without roast, true with roasted barley | `False` without, `True` with | ✅ pass |

### ✅ C7 · Cut points have a basis; no corpus read in style fit (A7)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from (select jsonb_array_elements(v) e from jsonb_each(app.style_fit_cut_points()) t(k,v) where jsonb_typeof(v)='array') x where not (e ? 'basis')"; docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from pg_proc p join pg_namespace n on n.oid=pronamespace where nspname='app' and prosrc ilike '%corpus.%' and proname like any(array['style_%','usage_effects','tag_%'])"; grep -c "corpus\." db/033_style_fit_effects.sql db/034_style_level.sql
```

| Expected | Actual | Result |
|---|---|---|
| 0 array cut points without a basis; 0 style-fit functions mentioning `corpus.`; 0 matches in the two SQL files | 0; 0; 0 and 0 | ✅ pass |

### ✅ C8 · `fermentable_style` bump: malts yes, hops and yeasts no (A8)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select app.style_level('6A',(select id from ref.ingredient where name='Munich Malt Type 2' and producer='Weyermann'),'mash','{\"pct\":50}'::jsonb)"; docker exec supabase-db psql -U postgres -d postgres -tAc "select app.style_level('21A',(select id from ref.ingredient where name='Magnum' limit 1),'boil','{\"minutes\":60,\"ibu\":55}'::jsonb)"
```

| Expected | Actual | Result |
|---|---|---|
| malt listed for Marzen: typical, because naming the list; a 60-min hop in 21A: allowed, not bumped | `typical` ("listed for Marzen (6A) in Weyermann products, brewery (EN)."); `allowed` ("no sensation of American IPA (21A) conflicts with this use.") | ✅ pass |

### ✅ C9 · Reference recipes: only accepted lines flagged (A9)

See Part 2, example 6.

| Expected | Actual | Result |
|---|---|---|
| 0 ⚠️/⛔ outside b16 rice, b19 honey, b20 lactose and the accepted b08/b18 lines; no recipe total "too little" | 8 flagged, exactly those 3 + 5; no `too_little` line printed; 22 recipes, 130 lines | ✅ pass |

### ✅ C10 · Docs describe the design without a corpus (A10)

```bash
awk '/^## 7/{f=1;next} /^## 8/{f=0} f' PROJECT.md | grep -c "D9"; grep -n -i "corpus" docs/STYLE-FIT.md; grep -n -i "revisit in s3\|revisited in s3" docs/*.md PROJECT.md; grep -n -i "vs corpus\|top in the corpus" docs/RECIPE-ROADMAP.md
```

| Expected | Actual | Result |
|---|---|---|
| D9 absent from §7 (0); STYLE-FIT mentions corpus only to say it is not used; no "revisit in s3"; no "dose vs corpus" / "top in the corpus" | 0; one line (STYLE-FIT.md:96, "come from the books, not from a corpus"); no matches; no matches. D9 is in PROJECT.md:172 with its why | ✅ pass |

### ✅ C11 · Everything created is owned by `postgres`

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select (select count(*) from pg_class c join pg_namespace n on n.oid=relnamespace where nspname in ('ref','app','corpus','kb') and relkind='r' and pg_get_userbyid(relowner)<>'postgres'), (select count(*) from pg_proc p join pg_namespace n on n.oid=pronamespace where nspname='app' and pg_get_userbyid(proowner)<>'postgres')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 tables and 0 functions with another owner | 0 / 0 | ✅ pass |

### ✅ C12 · Flake colours loaded and sourced (review fix, brief Deviations)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.fermentable where ebc is not null"; docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.source where slug in ('briess-flakes-web','simpsons-malt-2025')"
```

| Expected | Actual | Result |
|---|---|---|
| 78 fermentables with EBC (docs/DATABASE.md); both source slugs resolve (2) | 78; 2 (Flaked Barley and Oats [0,3.2], Corn 1.576, Rice 1.97) | ✅ pass |

## Part 4: Regression tests

Command: `.venv/bin/python -m pytest -q -p no:cacheprovider`  ·  Result: ✅ 535 passed in 132.78 s

No critical test from the plan's table was missing, so none was added.

| Test | Protects | Result |
|---|---|---|
| tests/test_tags.py::test_every_hop_tagged_or_flagged | no hop is left without a tag or a flag | ✅ |
| tests/test_tags.py::test_retag_is_identical, ::test_new_synonym_retags | tagging is repeatable, a synonym re-tags | ✅ |
| tests/test_tags.py::test_citra_tags, ::test_hop_words_prefers_aroma_line | Citra is citrus/tropical, not floral | ✅ |
| tests/test_style_envelopes.py::test_quote_must_be_in_prose, ::test_reviewed_style_with_unknown_refused | LLM quotes are verbatim, nothing unreviewed loads | ✅ |
| tests/test_style_envelopes.py::test_extraction_not_in_pipeline | the LLM extraction never runs in the recipe pipeline | ✅ |
| tests/test_style_envelopes.py::test_26_styles_reviewed, ::test_characteristic_ingredients, ::test_reload_is_identical | 26 reviewed envelopes with quotes; reload is identical | ✅ |
| tests/test_style_fit_effects.py::test_every_cut_point_has_a_basis, ::test_no_corpus_in_style_fit | every cut point has a basis; no corpus read | ✅ |
| tests/test_style_level.py (15 tests) | step order, missing dose said, override wins, adjunct rule, yeast min, rounded because, colourless fermentable named | ✅ |
| tests/test_style_level.py::test_fermentable_style_bump_only_for_fermentables | the bump touches fermentables only | ✅ |
| tests/test_style_fit_golden.py::test_citra_table, 53 golden cases, ::test_m3_cases_have_no_rule | Citra table and approved golden set, M3 cases without an override | ✅ |
| tests/test_style_fit_recipe.py::test_15b_needs_roast | required check | ✅ |
| tests/test_style_fit_recipe.py::test_reference_recipe_lines, ::test_deviation_lines_are_flagged, ::test_reference_recipe_totals, ::test_recipe_too_little | reference recipes rated, only accepted lines flagged, recipe-total min | ✅ |
| tests/test_style_fit_recipe.py::test_colour_lower_bound | colour check runs on a floor for colourless fermentables | ✅ |
| tests/test_adjuncts.py (6 tests) | flake colour ranges and their `field_source` | ✅ |

Failures: none.
