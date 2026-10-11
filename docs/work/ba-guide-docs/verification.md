Overall: ✅ all 9 checks and 61 tests pass

# Verification: ba-guide-docs

Diff: main...ba-guide-docs at 8521b56 · Run 2026-10-11

## Part 1: Summary

🎯 **Goal:** Make RECIPE-ROADMAP and DATABASE.md agree with D1, so neither describes BA as a future or optional guide.

🛠️ **How:** Moved the BA item out of the RECIPE-ROADMAP §8 Later row into the P4 "Do" cell (step 2 picks BJCP or BA per D1, with the BJCP only / BA only setting), and gave the DATABASE.md §9 BA style-family row the user's new trigger.

🤔 **Why this way:** Two table cells and one row are the only places that contradict D1. The D1 note in RECIPE-ROADMAP §9 was already right, and the BA style family is still unbuilt, so the row stays in "Later" with a trigger that is true under D1.

🏁 **Result:** Both docs now match D1. Outside `docs/finished/` and this work folder, the old wording appears only once, as history in the PROJECT.md §8 log (line 212). The DB facts quoted in the docs still match: 169 BA rows, 0 with `category_code`, 10 categories; 116 BJCP rows, all with `category_code`, 34 categories.

### 🚦 Steps

- ✅ 📝 **Brief:** Written twice (the second run added the user's answers to Q1 and Q2), approved, committed in ce9a308. It measured 169 BA rows with `category_code` NULL.
  - ⚠️ A4 was narrowed after approval (it left out `docs/work/ba-guide-docs/` and allowed one hit in the §8 log), by user decision, recorded in Deviations.
- ⚠️ 🗺️ **Plan:** Written twice and approved, committed in 3583677. It found that A4 as first written could never pass.
  - ⚠️ A4 as first written matched the PROJECT.md §8 entry and this folder's own files; the user chose option a) to narrow it.
- ⚠️ 🔨 **Implement:** Task 1/1 done in 9ca8ca6, with no fix rounds.
  - ⚠️ In this shell, `grep` is a ugrep wrapper that prints paths without `./`, so A4's `^./docs/...` filter did not match. A4 has to run with `command grep`, which is recorded as a plan deviation.
- ✅ 🔍 **Review:** Ready for testing, with 0 must-fix, 0 should-fix and 5 notes, all confirming A1–A6. Committed in 8521b56.
- ✅ 🧪 **Verify:** All acceptance checks were re-run, plus a live DB check of the BA/BJCP counts. 🧮 spot checks ✅ 9/9 · 🧪 tests ✅ 61/61
  - ⚠️ A4's recursive grep reaches `supabase/docker/volumes/db/data` and prints "Permission denied" on stderr, so the command below adds `2>/dev/null`. The result is unchanged.

👀 **Start here:** `docs/RECIPE-ROADMAP.md` line 294 (the P4 row). The "Do" cell now says step 2 picks from BJCP 2021 or BA 2026 per D1, and the Later row (line 299) no longer mentions BA.

📁 **Changed files:**
- `PROJECT.md`
- `docs/DATABASE.md`
- `docs/RECIPE-ROADMAP.md`
- `docs/work/ba-guide-docs/brief.md`
- `docs/work/ba-guide-docs/plan.md`
- `docs/work/ba-guide-docs/review.md`

## Part 2: Spot checks

All commands run from the repo root. `command grep` is used so that GNU grep runs, not the ugrep wrapper (plan Deviations).

### ✅ C1 · RECIPE-ROADMAP no longer says "selectable" (A1)

```bash
command grep -n "selectable" docs/RECIPE-ROADMAP.md; echo "exit $?"
```

| Expected | Actual | Result |
|---|---|---|
| no output, exit 1 | `exit 1` | ✅ pass |

### ✅ C2 · Later row keeps its other three items (A1)

```bash
command grep -n '^| \*\*Later\*\*' docs/RECIPE-ROADMAP.md
```

| Expected | Actual | Result |
|---|---|---|
| one line: inventory-first mode · substitutions · batch log → feedback | `299:\| **Later** \| inventory-first mode · substitutions · batch log → feedback \| \|` | ✅ pass |

### ✅ C3 · P4 "Do" cell states D1 for step 2 (A2)

```bash
command grep -n '^| \*\*P4\*\*' docs/RECIPE-ROADMAP.md
```

| Expected | Actual | Result |
|---|---|---|
| one line containing "D1", "BJCP only", "BA only"; "Done when" unchanged | `294:\| **P4** \| Steps 0–3. Step 2 picks the style from BJCP 2021 or BA 2026 per D1 (§9): BJCP preferred, BA where it describes the beer better or the user is asked, and one guide only when the user sets BJCP only or BA only \| ≥ 18/20 briefs: right style, right deviations \|` | ✅ pass |

### ✅ C4 · DATABASE.md BA style-family row has the new trigger and keeps its facts (A3)

```bash
command grep -n "A style family for BA styles" docs/DATABASE.md
```

| Expected | Actual | Result |
|---|---|---|
| one line with "when a BA style needs a style profile (D1: step 2 can pick a BA style)", "169", "`category_code`", "10 origin families", "STYLE-PROFILES.md" | `451:\| A style family for BA styles \| when a BA style needs a style profile (D1: step 2 can pick a BA style): `category_code` is `NULL` for all 169 BA rows (the source has none), so the thin-style family fallback ([STYLE-PROFILES.md](STYLE-PROFILES.md) §3) would use BA's `category` text (10 origin families, e.g. *British Origin Ale Styles*) \|` | ✅ pass |

### ✅ C5 · Old trigger gone from DATABASE.md (A3)

```bash
command grep -c "if BA becomes a selectable guide" docs/DATABASE.md
```

| Expected | Actual | Result |
|---|---|---|
| `0` | `0` | ✅ pass |

### ✅ C6 · No doc outside docs/finished/ calls BA a future guide (A4)

```bash
command grep -rn -i "selectable guide\|if BA becomes" --include=*.md . 2>/dev/null | command grep -v "^./docs/finished/\|^./docs/work/ba-guide-docs/" | cut -d: -f1,2; command grep -n '^## [89]\.' PROJECT.md | cut -d' ' -f1-3
```

| Expected | Actual | Result |
|---|---|---|
| exactly one hit, `./PROJECT.md:<n>`, with `<n>` inside §8 | `./PROJECT.md:212`; `200:## 8. Progress`, `708:## 9. History` (212 is in §8) | ✅ pass |

### ✅ C7 · PROJECT.md §8 has the entry for this work (A5)

```bash
command grep -n "ba-guide-docs" PROJECT.md | cut -c1-60
```

| Expected | Actual | Result |
|---|---|---|
| a 2026-10-11 entry naming ba-guide-docs with a link to its folder | `205:- Implemented ba-guide-docs ([docs/work/ba-guide-docs/](d…`, `209:- Planned …`, `211:- Wrote brief …`, all under `### 2026-10-11` | ✅ pass |

### ✅ C8 · Branch touches only the planned files (A6)

```bash
git diff main...ba-guide-docs --stat | awk '{print $1}'
```

| Expected | Actual | Result |
|---|---|---|
| only `PROJECT.md`, `docs/DATABASE.md`, `docs/RECIPE-ROADMAP.md`, `docs/work/ba-guide-docs/*` | `PROJECT.md`, `docs/DATABASE.md`, `docs/RECIPE-ROADMAP.md`, `docs/work/ba-guide-docs/brief.md`, `…/plan.md`, `…/review.md`, then `6` (the stat summary line) | ✅ pass |

### ✅ C9 · DB facts quoted in DATABASE.md §9 still hold (brief assumption)

```bash
docker exec supabase-db psql -U postgres -d postgres -tAc "select guide, count(*), count(category_code), count(distinct category) from ref.beer_style group by guide order by guide"
```

| Expected | Actual | Result |
|---|---|---|
| `BA\|169\|0\|10` and `BJCP\|116\|116\|34` | `BA\|169\|0\|10`, `BJCP\|116\|116\|34` | ✅ pass |

## Part 3: Regression tests

The plan's *Critical behaviour and its tests* table lists none, because this is a docs-only change. No tests were missing, so none were added. The whole suite was run to confirm nothing else broke.

Command: `.venv/bin/python -m pytest -q`  ·  Result: ✅ 61 passed

| Test | Protects | Result |
|---|---|---|
| the 61 existing tests | earlier work (loaders, ref data, recipe briefs) | ✅ |
