Overall: ✅ all 7 checks and 52 tests pass (51 pytest + load-twice)

# Verification: water-salts

Diff: main...water-salts at 19822be  ·  Run 2026-10-11

No brief; checked against `plan.md` and its source, the `fill-ref` index item 7 (now at
`docs/FILL-REF-README.md`).

## Part 1: Summary

🎯 **Goal:** put the 8 common brewing salts into `ref`, with the ions each one adds to water.

🛠️ **How:** `loaders/water_salts.py` computes mg/L of each ion from 1 g in 1 L out of IUPAC atomic masses in tested `Decimal` code, and loads the salts into `ref.ingredient` + `ref.water_salt`.

🤔 **Why this way:** brewing maths stays deterministic, tested code (CLAUDE.md), so no ion value is typed in by hand and no source file is needed.

🏁 **Result:** `ref.water_salt` has 8 rows with 8 `ref.ingredient` rows of kind `water_salt` (source `water-chemistry`); all 8 stored ion sets match the code output; re-running the loader keeps 8 rows.

### 🚦 Steps

- ⏭️ 📝 **Brief:** skipped; the plan was split from the `fill-ref` index (item 7), which serves as the source.
- ✅ 🗺️ **Plan:** written in an earlier session (7cdc4a2), approved as written in d288103.
  - ⚠️ The plan's `Source:` link still points to `docs/work/fill-ref/README.md`, which moved to `docs/FILL-REF-README.md` in 941f102.
- ✅ 🔨 **Implement:** 2 tasks, no fix rounds: eeaccd6 (ion maths, tests first, 3 passed) and 0d09ea4 (loader, run twice → 8 rows). Two deviations recorded: no `molar_mass` column (slim-ref), compositions counted in `PARTS`.
- ✅ 🔍 **Review:** ready for testing (19822be); 0 must-fix, 0 should-fix, 3 notes.
- ✅ 🧪 **Verify:** all checks and tests pass; loader re-run twice more, still 8 rows. 🧮 spot checks ✅ 7/7 · 🧪 tests ✅ 52/52

👀 **Start here:** `loaders/water_salts.py`: `SALTS` lists the 8 salts by their parts, and `ion_mg_per_l_per_g` turns a composition into ion mg/L (gypsum → Ca 232.8, SO4 557.9).

📁 **Changed files:**
- `PROJECT.md`
- `docs/work/water-salts/plan.md`
- `docs/work/water-salts/review.md`
- `docs/work/water-salts/verification.md`
- `loaders/water_salts.py`
- `tests/test_water_salts.py`

## Part 2: Spot checks

### ✅ C1 · 8 water salts loaded (Task 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.water_salt"
```

| Expected | Actual | Result |
|---|---|---|
| 8 | 8 | ✅ pass |

### ✅ C2 · Each salt is a `water_salt` ingredient from `water-chemistry` (Task 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient i join ref.source s on s.id = i.source_id where i.kind = 'water_salt' and s.slug = 'water-chemistry'"
```

| Expected | Actual | Result |
|---|---|---|
| 8 | 8 | ✅ pass |

### ✅ C3 · Gypsum's stored ions match the tested values (Task 1 + 2)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select w.ion_mg_per_l_per_g from ref.water_salt w join ref.ingredient i on i.id = w.ingredient_id where i.name = 'gypsum'"
```

| Expected | Actual | Result |
|---|---|---|
| `{"Ca": 232.8, "SO4": 557.9}` | `{"Ca": 232.8, "SO4": 557.9}` | ✅ pass |

### ✅ C4 · All 8 stored ion sets equal the code output

```bash
.venv/bin/python -c "
from decimal import Decimal
from loaders.db import connect
from loaders.water_salts import SALTS, ion_mg_per_l_per_g
with connect() as c:
    db = dict(c.execute(\"select i.name, w.ion_mg_per_l_per_g from ref.water_salt w join ref.ingredient i on i.id = w.ingredient_id\").fetchall())
ok = sum(1 for n, _, comp in SALTS if {k: Decimal(str(v)) for k, v in db.get(n, {}).items()} == ion_mg_per_l_per_g(comp))
print(f'{ok}/{len(SALTS)} match')
"
```

| Expected | Actual | Result |
|---|---|---|
| 8/8 match | 8/8 match | ✅ pass |

Stored values (also equal to the review's hand check): baking soda Na 273.7 / HCO3 726.3,
calcium chloride Ca 272.6 / Cl 482.3, chalk Ca 400.4 / CO3 599.6, epsom salt Mg 98.6 / SO4 389.7,
gypsum Ca 232.8 / SO4 557.9, magnesium chloride Mg 119.6 / Cl 348.8, slaked lime Ca 540.9 /
OH 459.1, table salt Na 393.4 / Cl 606.6.

### ✅ C5 · No `water_salt` ingredient without its `ref.water_salt` row

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.ingredient i left join ref.water_salt w on w.ingredient_id = i.id where i.kind = 'water_salt' and w.ingredient_id is null"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C6 · No `molar_mass` column (Task 2 deviation, slim-ref)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from information_schema.columns where table_schema = 'ref' and table_name = 'water_salt' and column_name = 'molar_mass'"
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

### ✅ C7 · Ion values are computed, not typed into the loader (plan rule)

```bash
grep -cE '\b(232\.8|557\.9|272\.6|482\.3|273\.7|726\.3)\b' loaders/water_salts.py
```

| Expected | Actual | Result |
|---|---|---|
| 0 | 0 | ✅ pass |

## Part 3: Regression tests

All tests named in the plan's *Critical behaviour and its tests* table exist; none added.

Command: `.venv/bin/python -m pytest -q`  ·  Result: ✅ 51 passed

| Test | Protects | Result |
|---|---|---|
| tests/test_water_salts.py::test_gypsum | Ion mg/L from 1 g/L for a sulfate salt with water of hydration (Ca 232.8, SO4 557.9) | ✅ |
| tests/test_water_salts.py::test_calcium_chloride_dihydrate | Chloride salt with water of hydration (Ca 272.6, Cl 482.3) | ✅ |
| tests/test_water_salts.py::test_baking_soda | Bicarbonate salt (Na 273.7, HCO3 726.3) | ✅ |
| rest of the suite (48 tests) | Earlier loaders and helpers unchanged | ✅ |

Command: `.venv/bin/python -m loaders.water_salts` run twice, each followed by
`docker exec supabase-db psql -U postgres -d postgres -tAc "select count(*) from ref.water_salt"`
·  Result: ✅

| Test | Protects | Result |
|---|---|---|
| load-twice count | Re-running doesn't duplicate: `loaded: 8 water salts` → 8, then `loaded: 8 water salts` → 8; `ref.ingredient` kind `water_salt` still 8 | ✅ |

Failures: none.
