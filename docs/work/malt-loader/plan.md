# Fermentables loader (malts.json) — implementation plan

Stage: draft
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 4; was Task 5)
Branch: malt-loader

## Approach

`loaders/fermentables.py` parses `malts.json` into `Fermentable` records (pure, unit tested),
converting ppg to SG and keeping colour as an EBC range, then writes one `ref.ingredient` row
(kind `fermentable`, via `upsert_ingredient`) plus one `ref.fermentable` row per malt. The
source of each row follows its maltster.

Needs `ref-schema` shipped. **Needs the user:** re-add `malts.json` (the plan uses
`shared/rag-files/pending/`). Without it, Task 2 is `blocked`.

Measured shape (2026-10-08 copy): a list of 77 (Weyermann 44, Viking Malt 33). `category` is
null in all 77, and 4 rows give only a maximum colour (e.g. Carabody, max 8 EBC).

Rules for this work: SI units (SG, EBC; ppg converted on load); unknown stays `NULL`
(`type` and `max_pct` stay NULL until P3); `raw` keeps the whole record; the loader is
idempotent; source files are never committed.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `loaders/fermentables.py` | new | `Fermentable`, `parse_malts`, `load`, CLI |
| `tests/test_fermentables.py` | new | 3 parser tests |
| `PROJECT.md` | changed | §5 malt row, §8 |

## Tasks

### Task 1: Parse malts
Why: potential and colour feed the gravity and colour maths in P2.
- [ ] In `loaders/fermentables.py`:
  `@dataclass Fermentable(name, producer, source_slug, potential_sg, extract_dbfg_pct, ebc, raw)`;
  `parse_malts(rows) -> list[Fermentable]`, where `potential_sg = 1 + potential_ppg/1000`
  rounded to 4 places, `ebc = to_range(colour_ebc_min, colour_ebc_max)`, `producer = maltster`,
  and `source_slug` comes from `maltster` (`Weyermann` → `weyermann-specs`,
  `Viking Malt` → `viking-malt-2020`; anything else raises `ValueError`).
- [ ] Write the tests first and see them fail on import:
  - `test_abbey_malt`: `{maltster:"Weyermann", name:"Abbey Malt®", potential_ppg:34.7, extract_dbfg_pct:75.0, colour_ebc_min:40.0, colour_ebc_max:50.0, color_lovibond:17.4}` → `potential_sg == D("1.0347")`, `ebc == Range(D("40.0"), D("50.0"), "[]")`, `producer == "Weyermann"`
  - `test_colour_max_only`: `Carabody Malt`, `colour_ebc_min: None`, `colour_ebc_max: 8.0` → `ebc == Range(None, D("8.0"), "(]")`
  - `test_unknown_maltster_raises`
- [ ] Implement, then `.venv/bin/python -m pytest tests/test_fermentables.py -v` → 3 passed; whole suite passes.
Done when: 3 passed.
Commit: `Parse Weyermann and Viking malts`

### Task 2: Load malts into `ref`
Why: the fermentable catalogue the recipe steps choose from (Review focus 4).
- [ ] Add `load(conn, items) -> int` (`upsert_ingredient` with kind `fermentable`, then upsert
  `ref.fermentable` on `ingredient_id`) and the CLI `python -m loaders.fermentables PATH`.
- [ ] Run it twice: `.venv/bin/python -m loaders.fermentables shared/rag-files/pending/malts.json`
- [ ] After each run: `select i.producer, count(*), count(f.ebc) from ref.ingredient i join ref.fermentable f on f.ingredient_id=i.id group by 1 order by 1`
  → `Viking Malt|33|33`, `Weyermann|44|44`; and
  `select count(*) from ref.fermentable where lower_inf(ebc)` → `4`.
- [ ] PROJECT.md §5: malt row → loaded, with the measured counts and date.
Done when: both runs give the same counts.
Commit: `Load Weyermann and Viking malts into ref`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| ppg → SG conversion, EBC as a closed range | `tests/test_fermentables.py::test_abbey_malt` | 1 |
| Max-only colour loads as `(,8]` | `tests/test_fermentables.py::test_colour_max_only` | 1 |
| Unknown maltster is never given a guessed source | `tests/test_fermentables.py::test_unknown_maltster_raises` | 1 |
| Re-running doesn't duplicate | load-twice counts | 2 |

## Approved exceptions

## Deviations
