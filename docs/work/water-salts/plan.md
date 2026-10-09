# Water salts (computed from atomic masses) — implementation plan

Stage: draft
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 7; was Task 8)
Branch: water-salts

## Approach

The 8 common brewing salts are defined in code by their chemical composition. Their ion
contributions (mg/L of each brewing ion from 1 g in 1 L) are **computed** from IUPAC standard
atomic masses in tested code, not typed in. They are stored as `ref.ingredient` (kind
`water_salt`, source `water-chemistry`) + `ref.water_salt`. This is brewing maths, so it
stays deterministic code.

Needs `ref-schema` shipped. No source files needed, so this item can run before the loaders
that wait on files.

Rules for this work: `molar_mass` and ion values come from `ATOMIC_MASS` only; the loader is
idempotent.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `loaders/water_salts.py` | new | `ATOMIC_MASS`, `SALTS`, `ion_mg_per_l_per_g`, `load`, CLI |
| `tests/test_water_salts.py` | new | 3 tests |
| `PROJECT.md` | changed | §8 |

## Tasks

### Task 1: Compute ion contributions
Why: water adjustments (P6, step 12) depend on these numbers being exact.
- [ ] In `loaders/water_salts.py`: `ATOMIC_MASS: dict[str, Decimal]` (IUPAC standard values for
  H, C, O, Na, Mg, S, Cl, Ca); `SALTS: list[tuple[name, formula, composition]]` for gypsum
  CaSO₄·2H₂O, calcium chloride CaCl₂·2H₂O, epsom salt MgSO₄·7H₂O, magnesium chloride MgCl₂·6H₂O,
  table salt NaCl, baking soda NaHCO₃, chalk CaCO₃, slaked lime Ca(OH)₂;
  `ion_mg_per_l_per_g(composition) -> dict[str, Decimal]`, the mg/L of each brewing ion (Ca, Mg,
  Na, SO4, Cl, HCO3, CO3, OH) from 1 g in 1 L, rounded to 0.1.
- [ ] Write the tests first and see them fail on import. The values follow from the atomic masses
  (re-checked 2026-10-09). Cross-check against the *Water* book's salt table once it is
  re-added:
  - `test_gypsum`: Ca `232.8`, SO4 `557.9`
  - `test_calcium_chloride_dihydrate`: Ca `272.6`, Cl `482.3`
  - `test_baking_soda`: Na `273.7`, HCO3 `726.3`
- [ ] Implement, then `.venv/bin/python -m pytest tests/test_water_salts.py -v` → 3 passed; whole suite passes.
Done when: 3 passed.
Commit: `Compute water salt ion contributions`

### Task 2: Load water salts into `ref`
Why: the salts step 12 chooses from (Review focus 4).
- [ ] Add `load(conn) -> int` (`upsert_ingredient` kind `water_salt`, source `water-chemistry`;
  upsert `ref.water_salt` with `formula`, `molar_mass`, `ion_mg_per_l_per_g`) and the CLI
  `python -m loaders.water_salts`.
- [ ] Run it twice → `select count(*) from ref.water_salt` → `8` both times.
Done when: 8 rows after each run.
Commit: `Load water salts into ref`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Ion mg/L from 1 g/L, sulfate salt with water of hydration | `tests/test_water_salts.py::test_gypsum` | 1 |
| Chloride salt with water of hydration | `tests/test_water_salts.py::test_calcium_chloride_dihydrate` | 1 |
| Bicarbonate salt | `tests/test_water_salts.py::test_baking_soda` | 1 |
| Re-running doesn't duplicate | load-twice count | 2 |

## Approved exceptions

## Deviations
