# Hops loader (3 sources merged) — implementation plan

Stage: draft
Source: [`docs/work/fill-ref/README.md`](../fill-ref/README.md) (P1a index, item 5; was Task 6)
Branch: hop-loader

## Approach

Three hop sources are parsed into one `Hop` shape (pure, unit tested), merged on
`name_key(name)` only, then written as `ref.ingredient` (kind `hop`) + `ref.hop`. Each field is
taken from the first source in a fixed precedence that has a value, and `field_source` records
which one. `raw` keeps every source's original record, so P3 tagging sees every `flavour` list
and `notes` text. Similar names are **never** merged automatically. They go to a report the user
reads.

Needs `ref-schema` shipped (`read_beerjson`, `name_key`, `to_range`, `upsert_ingredient`).
**Needs the user:** re-add `hops.json`, `hops.hopslist.json` and
`DefaultContent003-Ingredients-Hops-Yeasts.json` (the plan uses `shared/rag-files/pending/`).
Without them, Task 3 is `blocked`.

Measured shapes (2026-10-08 copies): `hops.json` is a list of 72, with a `flavour` list and
origins like `USA`, `SVN`, `BE/DE`. `hops.hopslist.json` is a list of 268 with the same fields,
22 of them with no origin. Brewtarget `DefaultContent003` is BeerJSON with a `//` comment header,
then `beerjson.hop_varieties` (282).

Rules for this work: unknown stays `NULL`; the loader is idempotent; source files are never
committed; nothing is merged on a guess.

## Question at plan approval

`HOP_SOURCE_PRECEDENCE = ("hops-json", "hopslist", "brewtarget-default-data")` is a guess. It
decides which source wins each field, and so which `source_id` a hop row gets. Options:
a) keep this order; b) put Brewtarget first (GPL-3, known provenance; `hops-json` and
`hopslist` have unverified provenance); c) another order. Recommend b) if provenance matters
more than range data (Brewtarget gives single values, the others give min–max ranges),
otherwise a). The constant is one line and easy to change later.

## Files

| Path | New / changed | Purpose |
|---|---|---|
| `loaders/hops.py` | new | `Hop`, `ORIGIN_CODES`, 3 parsers, `merge_hops`, `near_duplicates`, `load`, CLI |
| `tests/test_hops.py` | new | 6 tests |
| `docs/work/hop-loader/report.md` | new | near-duplicate pairs and unknown origins, for the user |
| `PROJECT.md` | changed | §5 hop row, §8 |

## Tasks

### Task 1: Parse the three hop sources
Why: origins, purpose and acid ranges drive hop choice and IBU (Review focus 3).
- [ ] In `loaders/hops.py`:
  - `@dataclass Hop(name, origins: list[str], purpose: str | None, alpha_pct, beta_pct, total_oil_ml_100g, oils_pct: dict, source_slug: str, field_source: dict[str, str], raw: dict)`.
    `raw` is `{source_slug: original_record}`.
  - `ORIGIN_CODES: dict[str, str]` maps every origin token measured in the sources to ISO 3166
    alpha-2: `USA`→`US`, `UK`→`GB`, `DE`/`GER`→`DE`, `SVN`/`SLO`→`SI`, `CZ`/`CZH`→`CZ`,
    `AU`/`AUS`→`AU`, `NZ`, `BE`, `FR`, `SA`→`ZA`, `POL`→`PL`, `JP`, `CAN`→`CA`, `CN`, `UA`.
    Brewtarget's form `"Name (CODE)"` uses the code in parentheses. `BE/DE` → `["BE","DE"]`.
    An unknown token gets no code and is collected for the report.
  - `parse_hops_json(rows, slug="hops-json")`, `parse_hopslist(rows, slug="hopslist")`,
    `parse_brewtarget_hops(rows, slug="brewtarget-default-data") -> list[Hop]`. Brewtarget
    single values become `[v,v]`. `purpose`: `Aroma`/`aroma` → `aroma`,
    `Bittering`/`bittering` → `bittering`, `Dual purpose`/`aroma/bittering` → `dual`.
- [ ] Write the tests first and see them fail on import:
  - `test_citra_hops_json`: `{name:"Citra", origin:"USA", hop_type:"Dual purpose", alpha_min:10.0, alpha_max:16.0, flavour:["Citrus","Fruity","Stone fruit","Tropical fruit"], …}` → `origins == ["US"]`, `purpose == "dual"`, `alpha_pct == Range(D("10.0"), D("16.0"), "[]")`
  - `test_brewtarget_origin_and_single_values`: `{name:"Adeena", origin:"United States of America (USA)", alpha_acid:{value:4.3}, type:"aroma", …}` → `origins == ["US"]`, `alpha_pct == Range(D("4.3"), D("4.3"), "[]")`
  - `test_multi_origin`: `origin:"CZ/SVN/DE"` → `["CZ","SI","DE"]`
- [ ] Implement, then `.venv/bin/python -m pytest tests/test_hops.py -v` → 3 passed; whole suite passes.
Done when: 3 passed.
Commit: `Parse three hop sources`

### Task 2: Merge hops and report near-duplicates
Why: one row per real hop, with no silent merge of different hops (Review focus 3).
- [ ] `HOP_SOURCE_PRECEDENCE` (order as approved, see the question above): each field comes from
  the first source that has a value, and `field_source[field]` records which one. The merged
  row's `source_slug` is the source of `alpha_pct`.
- [ ] `merge_hops(*lists: list[Hop]) -> list[Hop]` merges on `name_key(name)` only, and unions
  `raw`.
- [ ] `near_duplicates(keys: list[str]) -> list[tuple[str, str]]` returns pairs where one key
  is a prefix of the other, or `difflib.SequenceMatcher` ratio ≥ 0.9. Report only.
- [ ] Tests first, see them fail:
  - `test_merge_precedence`: hops.json Citra (alpha 10–16, no beta) + Brewtarget Citra (alpha 12, beta 3.5) → one hop, `alpha_pct` 10–16, `field_source == {"alpha_pct":"hops-json","beta_pct":"brewtarget-default-data", …}`, `set(raw) == {"hops-json","brewtarget-default-data"}` (adjust the expected sources if the approved precedence differs)
  - `test_saaz_not_merged`: `Saaz` + `Saaz (US)` → 2 hops (Review focus 3)
  - `test_near_duplicates`: `near_duplicates(["citra","citrahbc394","cascade"]) == [("citra","citrahbc394")]`
- [ ] Implement, then run `tests/test_hops.py` → 6 passed; whole suite passes.
Done when: 6 passed.
Commit: `Merge hop sources and flag near-duplicates`

### Task 3: Load hops into `ref` and write the report
Why: the hop catalogue the recipe steps choose from (Review focus 4).
- [ ] Add `load(conn, hops) -> int` (`upsert_ingredient` kind `hop`, no producer, `source_id`
  from the hop's `source_slug`; upsert `ref.hop` on `ingredient_id`) and the CLI
  `python -m loaders.hops --hops-json P --hopslist P --brewtarget P --report PATH`, which writes
  the near-duplicate pairs and unknown origins to `PATH` as Markdown.
- [ ] Run it twice with `--report docs/work/hop-loader/report.md`.
- [ ] `select count(*) from ref.hop` gives the same number on both runs, and it is ≤ 402 (the
  measured distinct-name union before accent folding). Record the actual number in the plan
  and in PROJECT.md.
- [ ] Record `select count(*) from ref.hop where alpha_pct is null`.
- [ ] PROJECT.md §5: hop row → loaded, with the measured counts and date. Point the user at
  `report.md` in the Report summary.
Done when: both runs give the same count and the report exists.
Commit: `Load and merge three hop sources into ref`

## Critical behaviour and its tests

| Behaviour | Test | Task |
|---|---|---|
| Origin tokens map to ISO codes | `tests/test_hops.py::test_citra_hops_json`, `::test_multi_origin` | 1 |
| Brewtarget single values become `[v,v]`, `(CODE)` origin parsed | `tests/test_hops.py::test_brewtarget_origin_and_single_values` | 1 |
| Field precedence and `field_source` | `tests/test_hops.py::test_merge_precedence` | 2 |
| Different hops with similar names stay apart | `tests/test_hops.py::test_saaz_not_merged` | 2 |
| Near-duplicates are reported, not merged | `tests/test_hops.py::test_near_duplicates` | 2 |
| Re-running doesn't duplicate | load-twice count | 3 |

## Approved exceptions

## Deviations
