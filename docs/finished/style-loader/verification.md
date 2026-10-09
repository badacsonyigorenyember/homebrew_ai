Overall: ✅ all 10 checks and 12 tests pass

# Verification: style-loader

Branch `style-loader` at 567a6ac, against `main`. Run 2026-10-09. No brief; checked against
`plan.md` and its Source, [`docs/work/fill-ref/README.md`](../../work/fill-ref/README.md) (global
constraints, Review focus 1, 2, 4).

## Part 1: Where to look

- **Goal:** load the BJCP 2021 and BA 2026 style guidelines into `ref.beer_style`, sourced and re-runnable.
- **How:** `loaders/styles.py` parses each JSON file into `Style` records with pure, tested functions, then upserts them on `(guide, edition, code)`.
- **Why this way:** parsing apart from loading keeps the range logic unit-testable without a DB, and the upsert on the table's natural key makes re-runs safe.
- **Result:** 285 styles in `ref.beer_style`: BJCP 116 (96 with vitals, 20 specialty styles with `NULL` ranges), BA 169 (144 with OG, 12 with open-ended SRM); every row has a `source_id` and its whole source record in `raw`.
- **Start here:** `docker exec -it supabase-db psql -U postgres -d postgres`, then
  `select guide, code, name, og, ibu, srm from ref.beer_style where code in ('15B','27A','american-style-black-ale');`.
  You should see 15B with `[1.036,1.044] | [25,45] | [25,40]`, 27A with all ranges empty (`NULL`),
  and the BA black ale with SRM `[35.0,)`.
- **Changed files:**

```
PROJECT.md
docs/work/style-loader/plan.md
docs/work/style-loader/review.md
loaders/styles.py
tests/test_styles.py
```

## Part 2: Spot checks

### ✅ C1 · Row counts per guide, and how many have OG (plan Task 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select guide || '|' || count(*) || '|' || count(og) from ref.beer_style group by guide order by guide"
```

| Expected | Actual | Result |
|---|---|---|
| `BA\|169\|144`, `BJCP\|116\|96` | `BA\|169\|144`, `BJCP\|116\|96` | ✅ pass |

### ✅ C2 · Re-running the loader doesn't duplicate (Review focus 4)

```bash
.venv/bin/python -m loaders.styles --bjcp shared/rag-files/pending/styles.json --ba shared/rag-files/pending/ba_styles.json
```

Run twice, with C1's query after each run (this one writes to the DB; the others are read-only).

| Expected | Actual | Result |
|---|---|---|
| each run prints 116 / 169; C1 unchanged after both | run 1 and run 2: `BJCP 2021: 116 styles`, `BA 2026: 169 styles`; C1 after each: `BA\|169\|144`, `BJCP\|116\|96` | ✅ pass |

### ✅ C3 · 15B vitals match `styles.json` (plan Task 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select og || '|' || ibu || '|' || srm from ref.beer_style where guide='BJCP' and code='15B'"
```

| Expected | Actual | Result |
|---|---|---|
| `[1.036,1.044]\|[25,45]\|[25,40]` | `[1.036,1.044]\|[25,45]\|[25,40]` | ✅ pass |

### ✅ C4 · BA open-ended SRM stays `[x,)` (Review focus 1)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.beer_style where guide='BA' and srm is not null and upper_inf(srm) and not lower_inf(srm); select code || '|' || srm from ref.beer_style where guide='BA' and upper_inf(srm) order by code limit 2"
```

| Expected | Actual | Result |
|---|---|---|
| 12 rows; sample bounds open at the top | `12`; `american-style-black-ale\|[35.0,)`, `american-style-imperial-porter\|[40.0,)` | ✅ pass |

### ✅ C5 · No empty or inverted ranges

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.beer_style where isempty(og) or isempty(fg) or isempty(ibu) or isempty(srm) or isempty(abv) or upper(og) < lower(og)"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C6 · BJCP specialty styles load with `NULL` vitals (Review focus 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.beer_style where guide='BJCP' and og is null and fg is null and ibu is null and srm is null and abv is null; select string_agg(code, ',' order by code) from ref.beer_style where guide='BJCP' and og is null"
```

| Expected | Actual | Result |
|---|---|---|
| 20, codes 27A–34C | `20`; `27A,28A,28B,28C,29A,29B,29C,30A,30B,30C,30D,31A,31B,32A,32B,33A,33B,34A,34B,34C` | ✅ pass |

### ✅ C7 · BA styles without OG still load (Review focus 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.beer_style where guide='BA' and og is null"
```

| Expected | Actual | Result |
|---|---|---|
| 25 | 25 | ✅ pass |

### ✅ C8 · Every row is sourced, with the right edition (global constraint)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.beer_style where source_id is null; select s.slug || '|' || b.guide || '|' || b.edition || '|' || count(*) from ref.beer_style b join ref.source s on s.id = b.source_id group by s.slug, b.guide, b.edition order by 1"
```

| Expected | Actual | Result |
|---|---|---|
| 0 unsourced; `ba-2026\|BA\|2026\|169`, `bjcp-2021\|BJCP\|2021\|116` | `0`; `ba-2026\|BA\|2026\|169`, `bjcp-2021\|BJCP\|2021\|116` | ✅ pass |

### ✅ C9 · Whole source record kept in `raw` (global constraint)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) || '|' || count(*) filter (where raw ? 'aroma' and raw ? 'overallimpression') from ref.beer_style"
```

| Expected | Actual | Result |
|---|---|---|
| `285\|285` | `285\|285` | ✅ pass |

### ✅ C10 · Source files are never committed (global constraint)

```bash
git ls-files shared/rag-files/pending/ | wc -l; git check-ignore shared/rag-files/pending/styles.json shared/rag-files/pending/ba_styles.json; git log main..style-loader --name-only --format= | grep -c 'pending/'
```

| Expected | Actual | Result |
|---|---|---|
| 0 tracked; both files ignored; 0 in branch commits | `0`; both paths printed by `check-ignore`; `0` | ✅ pass |

## Part 3: Regression tests

All critical tests named in the plan exist; none added. The "re-running doesn't duplicate"
behaviour is the load-twice check C2, as planned.

Command: `.venv/bin/python -m pytest -v`  ·  Result: ✅ 12 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_styles.py::test_bjcp_21a | BJCP string vitals become closed ranges; prose kept in `raw` | ✅ |
| tests/test_styles.py::test_bjcp_specialty_no_vitals | Specialty styles load with `NULL` ranges, not zeros | ✅ |
| tests/test_styles.py::test_ba_open_srm | BA `srmmin` without `srmmax` stays `[5,)` | ✅ |
| tests/test_styles.py::test_ba_code_is_slug | BA code is the slug, edition 2026 | ✅ |
| tests/test_common.py::test_num | Source values become `Decimal` | ✅ |
| tests/test_common.py::test_to_range_closed | Both bounds give a closed range | ✅ |
| tests/test_common.py::test_to_range_open_ended | One missing bound gives an open-ended range | ✅ |
| tests/test_common.py::test_to_range_missing | Both missing gives `NULL` | ✅ |
| tests/test_common.py::test_to_range_inverted_raises | Inverted bounds fail loudly | ✅ |
| tests/test_common.py::test_f_to_c | °F converted to °C | ✅ |
| tests/test_common.py::test_name_key | Accent-folded name keys | ✅ |
| tests/test_common.py::test_read_beerjson_strips_comment_header | BeerJSON `//` header is stripped | ✅ |
