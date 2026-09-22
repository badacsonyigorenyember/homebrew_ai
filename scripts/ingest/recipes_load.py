#!/usr/bin/env python3
"""
recipes_load.py — load every Brewfather BeerJSON export in recipes/ into corpus.*

    ./scripts/ingest/recipes_load.py              # apply schema, then load
    ./scripts/ingest/recipes_load.py --dry-run    # print the SQL, write nothing

Applies db/init/75_corpus_recipes.sql first (it is idempotent), so one command
is enough on a database that has never seen these tables.

⛔ TO WIPE THE TABLES AND RESET THE ID COUNTERS, uncomment the single line in
RESET_SQL below. It is SQL-commented, not Python-commented, so nothing else
changes. It is OFF by default and this script only ever appends.

⛔ NOTHING IS CONVERTED. Every quantity goes in as value + unit exactly as the
export wrote it, because the units are not uniform: hop durations are min AND
day, culture amounts pkg/unit/ml, misc amounts g/each/ml/unit. Water ions are
the one exception -- the columns are named _ppm, so a water addition in any
other unit ABORTS the load rather than being silently converted.

⚠ There is no natural key. Filenames and raw JSON are deliberately not stored,
and `name` is not unique enough ('Sierra Nevada Pale Ale' vs 'Sierra Nevada pale
ale'). Re-running therefore APPENDS; use the reset block to replace.
"""
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DDL = ROOT / "db" / "init" / "75_corpus_recipes.sql"
PSQL = ["docker", "exec", "-i", "supabase-db", "psql", "-U", "postgres",
        "-d", "postgres", "-v", "ON_ERROR_STOP=1"]

# ---------------------------------------------------------------------------
# RESET — delete every row and set the id counters back to 1.
# Uncomment the TRUNCATE line to arm it. CASCADE empties the seven child
# tables, RESTART IDENTITY sets each table's id sequence back to 1.
# ---------------------------------------------------------------------------
RESET_SQL = """
-- TRUNCATE corpus.recipes RESTART IDENTITY CASCADE;
"""

CHILD_SEQ = "corpus.recipes_id_seq"


def q(v):
    """Render a Python value as a SQL literal."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def qty(d, *path):
    """Pull a {value, unit} pair from a nested path. Returns (value, unit)."""
    for k in path:
        if not isinstance(d, dict):
            return (None, None)
        d = d.get(k)
    if not isinstance(d, dict):
        return (None, None)
    return (d.get("value"), d.get("unit"))


def insert(table, cols, values):
    return (f"INSERT INTO {table} ({', '.join(cols)})\nVALUES\n  "
            + ",\n  ".join("(" + ", ".join(q(v) for v in row) + ")" for row in values)
            + ";\n")


def recipe_sql(r, src):
    """Return the SQL inserting one recipe and all of its child rows."""
    out = []
    style = r.get("style") or {}
    ing = r.get("ingredients") or {}

    cols = ["name", "type", "author", "notes", "carbonation",
            "batch_size_value", "batch_size_unit",
            "efficiency_brewhouse_value", "efficiency_brewhouse_unit",
            "boil_time_value", "boil_time_unit",
            "pre_boil_size_value", "pre_boil_size_unit",
            "original_gravity_value", "original_gravity_unit",
            "final_gravity_value", "final_gravity_unit",
            "alcohol_by_volume_value", "alcohol_by_volume_unit",
            "apparent_attenuation_value", "apparent_attenuation_unit",
            "color_estimate_value", "color_estimate_unit", "ibu_estimate_method",
            "style_name", "style_category", "style_category_number",
            "style_letter", "style_guide", "style_type",
            "mash_name", "mash_grain_temperature_value",
            "mash_grain_temperature_unit", "fermentation_name"]
    vals = [r.get("name"), r.get("type"), r.get("author"), r.get("notes"),
            r.get("carbonation"),
            *qty(r, "batch_size"), *qty(r, "efficiency", "brewhouse"),
            *qty(r, "boil", "boil_time"), *qty(r, "boil", "pre_boil_size"),
            *qty(r, "original_gravity"), *qty(r, "final_gravity"),
            *qty(r, "alcohol_by_volume"), *qty(r, "apparent_attenuation"),
            *qty(r, "color_estimate"),
            (r.get("ibu_estimate") or {}).get("method"),
            style.get("name"), style.get("category"), style.get("category_number"),
            style.get("style_letter"), style.get("style_guide"), style.get("type"),
            (r.get("mash") or {}).get("name"),
            *qty(r, "mash", "grain_temperature"),
            (r.get("fermentation") or {}).get("name")]
    out.append(insert("corpus.recipes", cols, [vals]))

    rid = f"currval('{CHILD_SEQ}')"

    def child(table, cols, rows):
        if rows:
            out.append(insert(table, ["recipe_id"] + cols,
                              [[_Raw(rid)] + row for row in rows]))

    child("corpus.recipe_fermentables",
          ["position", "name", "type", "grain_group", "producer", "origin",
           "amount_value", "amount_unit", "color_value", "color_unit",
           "yield_fine_grind_value", "yield_fine_grind_unit",
           "yield_potential_value", "yield_potential_unit", "timing_use"],
          [[i, f.get("name"), f.get("type"), f.get("grain_group"),
            f.get("producer"), f.get("origin"),
            *qty(f, "amount"), *qty(f, "color"),
            *qty(f, "yield", "fine_grind"), *qty(f, "yield", "potential"),
            (f.get("timing") or {}).get("use")]
           for i, f in enumerate(ing.get("fermentable_additions") or [])])

    child("corpus.recipe_hops",
          ["position", "name", "origin", "form", "year",
           "alpha_acid_value", "alpha_acid_unit", "amount_value", "amount_unit",
           "timing_use", "timing_duration_value", "timing_duration_unit"],
          [[i, h.get("name"), h.get("origin"), h.get("form"), h.get("year"),
            *qty(h, "alpha_acid"), *qty(h, "amount"),
            (h.get("timing") or {}).get("use"), *qty(h, "timing", "duration")]
           for i, h in enumerate(ing.get("hop_additions") or [])])

    child("corpus.recipe_cultures",
          ["position", "name", "type", "form", "producer", "product_id",
           "amount_value", "amount_unit", "attenuation_value",
           "attenuation_unit", "cell_count_billions", "timing_use"],
          [[i, c.get("name"), c.get("type"), c.get("form"), c.get("producer"),
            c.get("product_id"), *qty(c, "amount"), *qty(c, "attenuation"),
            c.get("cell_count_billions"), (c.get("timing") or {}).get("use")]
           for i, c in enumerate(ing.get("culture_additions") or [])])

    child("corpus.recipe_miscs",
          ["position", "name", "type", "amount_value", "amount_unit",
           "timing_use", "timing_duration_value", "timing_duration_unit"],
          [[i, m.get("name"), m.get("type"), *qty(m, "amount"),
            (m.get("timing") or {}).get("use"), *qty(m, "timing", "duration")]
           for i, m in enumerate(ing.get("miscellaneous_additions") or [])])

    waters = []
    for i, w in enumerate(ing.get("water_additions") or []):
        ions = {}
        for ion in ("calcium", "bicarbonate", "sulfate", "chloride",
                    "sodium", "magnesium"):
            value, unit = qty(w, ion)
            if value is not None and unit not in (None, "ppm"):
                sys.exit(f"ABORT: {src}: water '{w.get('name')}' reports "
                         f"{ion} in {unit!r}, not ppm. The column is named "
                         f"{ion}_ppm and this loader does not convert units. "
                         f"Widen the schema before loading this file.")
            ions[ion] = value
        waters.append([i, w.get("name"), *qty(w, "amount"),
                       ions["calcium"], ions["bicarbonate"], ions["sulfate"],
                       ions["chloride"], ions["sodium"], ions["magnesium"]])
    child("corpus.recipe_waters",
          ["position", "name", "amount_value", "amount_unit", "calcium_ppm",
           "bicarbonate_ppm", "sulfate_ppm", "chloride_ppm", "sodium_ppm",
           "magnesium_ppm"], waters)

    child("corpus.recipe_mash_steps",
          ["position", "name", "type", "step_temperature_value",
           "step_temperature_unit", "step_time_value", "step_time_unit",
           "ramp_time_value", "ramp_time_unit"],
          [[i, s.get("name"), s.get("type"), *qty(s, "step_temperature"),
            *qty(s, "step_time"), *qty(s, "ramp_time")]
           for i, s in enumerate((r.get("mash") or {}).get("mash_steps") or [])])

    child("corpus.recipe_fermentation_steps",
          ["position", "name", "description", "start_temperature_value",
           "start_temperature_unit", "step_time_value", "step_time_unit"],
          [[i, s.get("name"), s.get("description"),
            *qty(s, "start_temperature"), *qty(s, "step_time")]
           for i, s in enumerate((r.get("fermentation") or {})
                                 .get("fermentation_steps") or [])])
    return "".join(out)


class _Raw(str):
    """A SQL fragment that must not be quoted."""


_orig_q = q
def q(v):                                      # noqa: F811  (wraps the above)
    return str(v) if isinstance(v, _Raw) else _orig_q(v)


def psql(sql):
    r = subprocess.run(PSQL + ["-tA", "-f", "-"], input=sql,
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"SQL failed:\n{r.stderr}")
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(ROOT / "recipes"))
    ap.add_argument("--dry-run", action="store_true",
                    help="print the SQL instead of running it")
    args = ap.parse_args()

    files = sorted(Path(args.src).glob("*.json"))
    if not files:
        sys.exit(f"no .json files in {args.src}")

    body, n = [], 0
    for fp in files:
        doc = json.load(open(fp, encoding="utf-8"))
        bj = doc.get("beerjson", doc)
        for r in bj.get("recipes") or []:
            body.append(recipe_sql(r, fp.name))
            n += 1

    sql = "BEGIN;\n" + RESET_SQL + "".join(body) + "COMMIT;\n"

    if args.dry_run:
        print(sql)
        print(f"-- {n} recipes from {len(files)} files (nothing written)",
              file=sys.stderr)
        return 0

    psql(DDL.read_text())
    before = psql("SELECT count(*) FROM corpus.recipes;")
    if before != "0" and "\n-- TRUNCATE" in RESET_SQL:
        print(f"note: corpus.recipes already holds {before} rows -- this run "
              f"APPENDS. Uncomment the TRUNCATE in RESET_SQL to replace.")
    psql(sql)

    counts = psql("""
      SELECT 'recipes            '||count(*) FROM corpus.recipes
      UNION ALL SELECT 'fermentables       '||count(*) FROM corpus.recipe_fermentables
      UNION ALL SELECT 'hops               '||count(*) FROM corpus.recipe_hops
      UNION ALL SELECT 'cultures           '||count(*) FROM corpus.recipe_cultures
      UNION ALL SELECT 'miscs              '||count(*) FROM corpus.recipe_miscs
      UNION ALL SELECT 'waters             '||count(*) FROM corpus.recipe_waters
      UNION ALL SELECT 'mash_steps         '||count(*) FROM corpus.recipe_mash_steps
      UNION ALL SELECT 'fermentation_steps '||count(*) FROM corpus.recipe_fermentation_steps;""")
    print(f"loaded {n} recipes from {len(files)} files")
    print(counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
