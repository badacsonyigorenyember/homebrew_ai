Overall: ✅ all 17 checks and 33 tests pass (re-verify 2026-10-10)

# Verification: hop-loader

Branch: hop-loader at 3419696 · Run: 2026-10-10, re-verified the same day after A9 changed · DB checks read-only (no reload in this run)

## Part 1: Summary

🎯 **Goal:** Fill the empty `ref.hop` with the hops hopline.hu sells, with their figures, so the recipe pipeline has hops and alpha acids to work with.

🛠️ **How:** A `--hops` mode for the hopline fetcher saves the 106 product pages raw, an explicit committed SKU map decides which hop each product is, and a tested parser and loader upsert `ref.ingredient` + `ref.hop` with `field_source` and `raw`.

🤔 **Why this way:** The user chose the malt approach (hopline only) so the catalogue matches what can be bought, and the explicit map keeps every merge a written decision rather than a guess.

🏁 **Result:** `ref.hop` holds 90 hops (5 LUPOMAX), purpose aroma 34 / bittering 4 / dual 51 / NULL 1, alpha NULL only for Delta, Lotus and Sterling; `ref.source` has 10 rows with `hopline-hops` and without `hops-json` / `hopslist`.

### 🚦 Steps

- ✅ 📝 **Brief:** Written in the session directly from a read-only fetch of 2026-10-10 (106 products, 85 varieties + 5 LUPOMAX + 16 pack sizes); four user decisions recorded; approved in cbb90a3.
- ✅ 🗺️ **Plan:** Five tasks rewritten for hopline-only input; approved in 5987233.
- ⚠️ 🔨 **Implement:** All 5 tasks done (7a0f5df, 54dba9e, a1d9361, 26c1255, 1f019fd); two loads gave identical counts; one fix round after review.
  - ⚠️ Task 5: the plan's no-LLM grep matched `fullmatch`; changed to whole-word `-w` and recorded in plan Deviations (brief A9 followed on user decision, see Verify).
- ❌ 🔍 **Review:** Ready for testing (62ab1ef) with one should-fix: PROJECT.md showed both 11 and 10 `ref.source` rows. 🔧 fixed in 3419696
  - ⚠️ Note: Lotus purpose `dual` comes from hopline's categories for a page that carries Taurus content (within the R7 decision).
  - ⚠️ Note: a `HOPS` SKU missing from the fetched file stops the load with a bare `KeyError`, not a named message.
  - ⚠️ Note: oil stored as mL/100 g is still the brief's unverified assumption.
- ❌ 🧪 **Verify:** First run: C16 failed, because brief A9's substring grep matched `re.fullmatch`. The user changed A9 to the whole-word grep (brief Deviations). The re-verify passes everything. 🔧 fixed in 6cfe61a 🧮 spot checks ✅ 17/17 · 🧪 tests ✅ 33/33

👀 **Start here:** `docs/work/hop-loader/report.md`: you should see Delta, Lotus and Sterling loaded without figures, the two Nectaron pack sizes whose alpha differs, and Amarillo and Mosaic LUPOMAX repeating the pellet figures.

📁 **Changed files:**
- `PROJECT.md`
- `db/011_ref_sources.sql`
- `docs/work/fill-ref/README.md`
- `docs/work/hop-loader/brief.md`
- `docs/work/hop-loader/plan.md`
- `docs/work/hop-loader/report.md`
- `docs/work/hop-loader/review.md`
- `docs/work/hop-loader/verification.md`
- `loaders/fetch_hopline.py`
- `loaders/hop_products.py`
- `loaders/hops.py`
- `tests/test_fetch_hopline.py`
- `tests/test_hops.py`

## Part 2: Spot checks

### ✅ C1 · Fetched file: 106 products, every name set, categories (A1)

```bash
.venv/bin/python -c "import json; d=json.load(open('shared/rag-files/pending/hopline_hops.json')); p=d['products']; print(len(p), sum(1 for x in p if x['name']), {k:len(v) for k,v in d['categories'].items()})"
```

| Expected | Actual | Result |
|---|---|---|
| 106 106 aroma 101, bittering 60, dual 56 | `106 106 {'aroma': 101, 'bittering': 60, 'dual': 56}` | ✅ pass |

### ✅ C2 · Every fetched SKU is in the map and every hop SKU is in the file (A2)

```bash
.venv/bin/python -c "import json; from loaders.hop_products import HOPS, PACK_SIZES; d=json.load(open('shared/rag-files/pending/hopline_hops.json')); s={x['sku'] for x in d['products']}; print(len(s - set(HOPS) - set(PACK_SIZES)), len(set(HOPS) - s), len(HOPS), len(PACK_SIZES))"
```

| Expected | Actual | Result |
|---|---|---|
| 0 unmapped, 0 missing, 90 HOPS, 16 PACK_SIZES | `0 0 90 16` | ✅ pass |

### ✅ C3 · 90 hops, 5 LUPOMAX (A3)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), count(*) filter (where i.name like '% LUPOMAX') from ref.hop h join ref.ingredient i on i.id = h.ingredient_id"
```

| Expected | Actual | Result |
|---|---|---|
| 90\|5 | 90\|5 | ✅ pass |

### ✅ C4 · No duplicate hop ingredients after two loads (A3, R8)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*), count(distinct name_key) from ref.ingredient where kind='hop'"
```

| Expected | Actual | Result |
|---|---|---|
| 90\|90 | 90\|90 | ✅ pass |

The two loads were run in Task 5 (identical counts); this run did not reload.

### ✅ C5 · Purpose split (R5)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select coalesce(purpose,'NULL'), count(*) from ref.hop group by 1 order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| aroma 34, bittering 4, dual 51, NULL 1 | aroma\|34, bittering\|4, dual\|51, NULL\|1 | ✅ pass |

### ✅ C6 · The unclassified hop is Enigma (R5)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name from ref.hop h join ref.ingredient i on i.id = h.ingredient_id where h.purpose is null"
```

| Expected | Actual | Result |
|---|---|---|
| Enigma | Enigma | ✅ pass |

### ✅ C7 · Hops with NULL alpha (A6)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(i.name, ', ' order by i.name) from ref.hop h join ref.ingredient i on i.id = h.ingredient_id where h.alpha_pct is null"
```

| Expected | Actual | Result |
|---|---|---|
| Delta, Lotus, Sterling (count 3) | Delta, Lotus, Sterling | ✅ pass |

### ✅ C8 · Only Dolcita has no origin (R4)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select i.name from ref.hop h join ref.ingredient i on i.id = h.ingredient_id where h.origins is null"
```

| Expected | Actual | Result |
|---|---|---|
| Dolcita | Dolcita | ✅ pass |

### ✅ C9 · Citra row (A5)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select h.origins, h.purpose, h.alpha_pct, h.beta_pct, h.total_oil_ml_100g, h.field_source from ref.hop h join ref.ingredient i on i.id = h.ingredient_id where i.name = 'Citra'"
```

| Expected | Actual | Result |
|---|---|---|
| {US}\|dual\|[10,15]\|[3,4.5]\|[1.5,3]\|5 fields, all `hopline-hops` | `{US}\|dual\|[10,15]\|[3,4.5]\|[1.5,3]\|{"origins": "hopline-hops", "purpose": "hopline-hops", "beta_pct": "hopline-hops", "alpha_pct": "hopline-hops", "total_oil_ml_100g": "hopline-hops"}` | ✅ pass |

### ✅ C10 · No figure stored as 0; `oils_pct` stays NULL (R3, scope)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) filter (where lower(alpha_pct) = 0 or lower(beta_pct) = 0 or lower(total_oil_ml_100g) = 0), count(*) filter (where oils_pct is not null) from ref.hop"
```

| Expected | Actual | Result |
|---|---|---|
| 0\|0 | 0\|0 | ✅ pass |

### ✅ C11 · Sources: `hopline-hops` present, `hops-json` / `hopslist` gone (A7)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select string_agg(slug, ',' order by id), count(*) from ref.source"
```

| Expected | Actual | Result |
|---|---|---|
| 10 rows, includes `hopline-hops`, no `hops-json` / `hopslist` | `bjcp-2021,ba-2026,brewtarget-default-data,water-chemistry,hopline-malts,weyermann-2026,viking-malt-2023,simpsons-malt-2025,user-supplied,hopline-hops\|10` | ✅ pass |

### ✅ C12 · Every hop ingredient has source `hopline-hops` (R6)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient where kind = 'hop' and source_id <> (select id from ref.source where slug = 'hopline-hops')"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C13 · Delta and Lotus: figures NULL, origin and purpose set (R7)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.hop h join ref.ingredient i on i.id=h.ingredient_id where i.name in ('Delta','Lotus') and h.alpha_pct is null and h.beta_pct is null and h.total_oil_ml_100g is null and h.origins is not null and h.purpose is not null"
```

| Expected | Actual | Result |
|---|---|---|
| 2 | 2 | ✅ pass |

### ✅ C14 · report.md lists Delta, Lotus, Nectaron and the LUPOMAX repeats (A8)

```bash
grep -oE '^- (Delta|Lotus|Sterling|Nectaron|[A-Za-z ]+ LUPOMAX)' docs/work/hop-loader/report.md | sort | uniq -c
```

| Expected | Actual | Result |
|---|---|---|
| Delta, Lotus, Nectaron, Mosaic LUPOMAX listed | Amarillo LUPOMAX 1, Delta 1, Lotus 1, Mosaic LUPOMAX 1, Nectaron 2, Sterling 1 | ✅ pass |

### ✅ C15 · No LLM in the hop modules, whole words (A9, plan Task 5)

```bash
grep -nwiE "ollama|llm" loaders/hops.py loaders/hop_products.py; echo "exit $?"
```

| Expected | Actual | Result |
|---|---|---|
| no match, exit 1 | `exit 1` | ✅ pass |

### ❌ C16 · No LLM in `loaders/hops.py`, brief A9's command as written (A9)

```bash
grep -ri "ollama\|llm" loaders/hops.py; echo "exit $?"
```

| Expected | Actual | Result |
|---|---|---|
| nothing found | `loaders/hops.py:    match = FIGURE.fullmatch(cleaned)` · `exit 0` | ❌ fail |

Cause: decision — the only match is the substring "llm" in `re.fullmatch`, not an LLM call (C15 passes); plan Deviations changed the grep to whole words, but brief A9 still names the substring grep, and changing an acceptance criterion needs the user's answer.

### ✅ C17 · The fetched file is git-ignored and nothing in `pending/` is committed (constraints)

```bash
git check-ignore shared/rag-files/pending/hopline_hops.json; git ls-files shared/rag-files/pending | wc -l
```

| Expected | Actual | Result |
|---|---|---|
| path printed, 0 | `shared/rag-files/pending/hopline_hops.json`, `0` | ✅ pass |

## Part 3: Regression tests

Every test in the plan's *Critical behaviour and its tests* table exists; none added. The last
row (re-running doesn't duplicate) is a load-twice check, not a test: Task 5's two runs and C4.

Command: `.venv/bin/python -m pytest -v`  ·  Result: ✅ 33 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_fetch_hopline.py::test_listing_links_any_sku | Every hop SKU is found on the listing, including `-cs` SKUs | ✅ |
| tests/test_fetch_hopline.py::test_spec_table_and_params | Spec table read by column, `mobile-head` labels dropped; data block pairs | ✅ |
| tests/test_hops.py::test_parse_figure | Figure formats → ranges; `?` stays NULL, never 0; unknown format raises | ✅ |
| tests/test_hops.py::test_origin_codes | Country → ISO code; unknown country raises | ✅ |
| tests/test_hops.py::test_purpose_of | Purpose rule from hopline's categories, across pack sizes | ✅ |
| tests/test_hops.py::test_citra | Table alpha wins; `field_source` and `raw` complete | ✅ |
| tests/test_hops.py::test_alpha_falls_back_to_data_block | Data-block alpha only as fallback; none → NULL, not in `field_source` | ✅ |
| tests/test_hops.py::test_pack_sizes_and_null_figures | Pack sizes become one hop with the main page's figures; Delta figures stay NULL | ✅ |
| tests/test_hops.py::test_hop_map | Every SKU decided once; no two hops share a name key | ✅ |
| tests/test_hops.py::test_unknown_sku_raises | A new hopline product never loads silently | ✅ |
| tests/test_fetch_hopline.py, test_common.py, test_malts.py, test_styles.py (23 others) | Malt, style and shared-helper behaviour unchanged | ✅ |

Failures: none.

## Re-verify 2026-10-10

After the user's decision on C16: brief A9 now reads `grep -nwiE "ollama|llm" loaders/hops.py
loaders/hop_products.py` finds nothing (brief Deviations, 2026-10-10). Every check and the whole
suite were run again; commands as above unless shown.

| Check | Expected | Actual | Result |
|---|---|---|---|
| C1 | 106 106 aroma 101, bittering 60, dual 56 | `106 106 {'aroma': 101, 'bittering': 60, 'dual': 56}` | ✅ pass |
| C2 | 0 0 90 16 | `0 0 90 16` | ✅ pass |
| C3 | 90\|5 | 90\|5 | ✅ pass |
| C4 | 90\|90 | 90\|90 | ✅ pass |
| C5 | aroma 34, bittering 4, dual 51, NULL 1 | aroma\|34, bittering\|4, dual\|51, NULL\|1 | ✅ pass |
| C6 | Enigma | Enigma | ✅ pass |
| C7 | Delta, Lotus, Sterling | Delta, Lotus, Sterling | ✅ pass |
| C8 | Dolcita | Dolcita | ✅ pass |
| C9 | {US}\|dual\|[10,15]\|[3,4.5]\|[1.5,3]\|5 fields, all `hopline-hops` | same, 5 fields all `hopline-hops` | ✅ pass |
| C10 | 0\|0 | 0\|0 | ✅ pass |
| C11 | 10 rows, `hopline-hops`, no `hops-json` / `hopslist` | 10 rows, ends `user-supplied,hopline-hops` | ✅ pass |
| C12 | 0 | 0 | ✅ pass |
| C13 | 2 | 2 | ✅ pass |
| C14 | Delta, Lotus, Nectaron, Mosaic LUPOMAX listed | Amarillo LUPOMAX 1, Delta 1, Lotus 1, Mosaic LUPOMAX 1, Nectaron 2, Sterling 1 | ✅ pass |
| C15 | no match, exit 1 | `exit 1` | ✅ pass |
| C17 | path printed, 0 | `shared/rag-files/pending/hopline_hops.json`, `0` | ✅ pass |

### ✅ C16 · No LLM in the hop modules, brief A9 as now written (A9)

```bash
grep -nwiE "ollama|llm" loaders/hops.py loaders/hop_products.py; echo "exit $?"
```

| Expected | Actual | Result |
|---|---|---|
| nothing found | `exit 1` (no match) | ✅ pass |

Command: `.venv/bin/python -m pytest -q`  ·  Result: ✅ 33 passed

Failures: none.
