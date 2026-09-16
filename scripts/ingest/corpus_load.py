#!/usr/bin/env python3
"""Load the Brewer's Friend recipe corpus into corpus.* (70_corpus.sql).

One-shot. The DDL runs on every stack start; this does not -- 1.6M rows are not
something db-init should replay. Re-running is safe: it truncates first.

    python3 scripts/ingest/corpus_load.py <recipes_full.txt>

Source: angeredsquid/brewers-friend-beer-recipes (Kaggle, CC0), 179,455 recipes
scraped from brewersfriend.com before July 2020.
"""
import csv, json, os, re, subprocess, sys, tempfile

SRC = "brewersfriend"
TIME_RE = re.compile(r"^\s*([\d.]+)\s*(min|mins|minutes|day|days|hr|hrs|hour|hours)\b", re.I)
TEMP_RE = re.compile(r"\bat\s+([\d.]+)\s*°?\s*([CF])\b", re.I)
UNIT = {"min": "min", "mins": "min", "minutes": "min",
        "day": "days", "days": "days",
        "hr": "hr", "hrs": "hr", "hour": "hr", "hours": "hr"}


def num(v):
    """A number, or None. The source uses '', None and 'N/A' interchangeably."""
    if v is None:
        return None
    s = re.sub(r"[^0-9.\-]", "", str(v))
    if s in ("", "-", ".", "-."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def inum(v):
    """num() for an integer column -- the source writes counts as floats ('16.0')."""
    n = num(v)
    return None if n is None else int(n)


def txt(v):
    if v is None:
        return None
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s or None


def split_use(raw):
    """'Whirlpool at 170 °F' -> ('Whirlpool', 76.7). Temperature to Celsius."""
    s = txt(raw)
    if not s:
        return None, None, None
    temp_c = None
    m = TEMP_RE.search(s)
    if m:
        val = float(m.group(1))
        temp_c = round((val - 32) * 5 / 9, 1) if m.group(2).upper() == "F" else val
    verb = txt(re.split(r"\s+at\s+", s, maxsplit=1, flags=re.I)[0])
    return s, verb, temp_c


def split_time(raw):
    """'60 min' -> (60, 'min'); '7 days' -> (7, 'days'). Units are NOT unified:
    dry-hop days must not sort alongside boil minutes."""
    s = txt(raw)
    if not s:
        return None, None, None
    m = TIME_RE.match(s)
    if not m:
        return None, None, s
    return float(m.group(1)), UNIT[m.group(2).lower()], s


def main(path):
    print(f"reading {path} ...", flush=True)
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    tmp = tempfile.mkdtemp(prefix="corpus_load_")
    files = {k: open(os.path.join(tmp, f"{k}.csv"), "w", newline="", encoding="utf-8")
             for k in ("recipes", "ferm", "hops", "yeast", "misc")}
    w = {k: csv.writer(v) for k, v in files.items()}

    seen, dupes, n = set(), 0, 0
    for key, r in data.items():
        # source_ref is the natural key. A handful of rows carry no url; the
        # source's own dict key stands in so the recipe is not dropped.
        ref = txt(r.get("url")) or f"#{key}"
        if ref in seen:
            dupes += 1
            continue
        seen.add(ref)
        n += 1

        ph = num(r.get("ph mash"))
        w["recipes"].writerow([
            SRC, ref, txt(r.get("name")), txt(r.get("style")), txt(r.get("method")),
            num(r.get("batch")), num(r.get("og")), num(r.get("fg")), num(r.get("abv")),
            num(r.get("ibu")), num(r.get("color")),
            None if ph is None or ph < 0 else ph,   # the source writes -1 for absent
            num(r.get("rating")), inum(r.get("num rating")), inum(r.get("views")),
        ])

        for i, f in enumerate(r.get("fermentables") or []):
            if len(f) < 5 or not txt(f[1]):
                continue
            w["ferm"].writerow([ref, i, txt(f[1]), num(f[0]), num(f[2]), num(f[3]), num(f[4])])

        for i, h in enumerate(r.get("hops") or []):
            if len(h) < 8 or not txt(h[1]):
                continue
            use_raw, use, tc = split_use(h[4])
            tv, tu, traw = split_time(h[5])
            w["hops"].writerow([ref, i, txt(h[1]), num(h[0]), txt(h[2]), num(h[3]),
                                use_raw, use, tc, tv, tu, traw, num(h[6]), num(h[7])])

        y = r.get("yeast")
        if isinstance(y, list) and len(y) >= 6 and txt(y[0]) and txt(y[0]) != "- -":
            st = txt(y[5])
            w["yeast"].writerow([ref, txt(y[0]), num(y[1]), txt(y[2]), num(y[3]), num(y[4]),
                                 None if st not in ("Yes", "No") else (st == "Yes")])

        for i, o in enumerate(r.get("other") or []):
            if len(o) < 5 or not txt(o[1]):
                continue
            w["misc"].writerow([ref, i, txt(o[1]), txt(o[0]), txt(o[2]), txt(o[3]), txt(o[4])])

    for fh in files.values():
        fh.close()
    print(f"staged {n:,} recipes ({dupes:,} duplicate urls skipped) -> {tmp}", flush=True)
    return tmp


# Child staging tables are explicitly typed: Postgres will not assignment-cast
# text into numeric, so an all-text staging table cannot be INSERT..SELECT'd.
SPEC = {
    "ferm": ("recipe_fermentables", [
        ("position", "int"), ("name_raw", "text"), ("amount_kg", "numeric"),
        ("potential_ppg", "numeric"), ("color_lovibond", "numeric"), ("pct_bill", "numeric")]),
    "hops": ("recipe_hops", [
        ("position", "int"), ("name_raw", "text"), ("amount_g", "numeric"),
        ("form", "text"), ("alpha_pct", "numeric"), ("use_raw", "text"),
        ('"use"', "text"), ("use_temp_c", "numeric"), ("time_value", "numeric"),
        ("time_unit", "text"), ("time_raw", "text"), ("ibu_contrib", "numeric"),
        ("pct_amount", "numeric")]),
    "yeast": ("recipe_yeasts", [
        ("name_raw", "text"), ("attenuation_pct", "numeric"), ("flocculation", "text"),
        ("temp_min_f", "numeric"), ("temp_max_f", "numeric"), ("starter", "boolean")]),
    "misc": ("recipe_misc", [
        ("position", "int"), ("name_raw", "text"), ("amount_raw", "text"),
        ("type_raw", "text"), ("use_raw", "text"), ("time_raw", "text")]),
}
RECIPE_COLS = ("source, source_ref, name, style_raw, method, batch_l, og, fg, abv, ibu, "
               "color_srm, mash_ph, rating, num_ratings, views")


def psql(sql, stdin=None):
    """supabase_admin, not postgres -- postgres is not a superuser in this stack."""
    p = subprocess.run(
        ["docker", "exec", "-i", "supabase-db", "psql", "-U", "supabase_admin",
         "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-c", sql],
        stdin=stdin, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"psql failed:\n{p.stderr}")
    return p.stdout.strip()


def load(tmp):
    # corpus.recipes.style_raw references corpus.styles, which is rebuilt from the
    # recipes AFTER they land -- so the constraint cannot be in place during the
    # COPY or any style new to this load fails the FK. f_rebuild_styles re-adds it.
    psql("ALTER TABLE corpus.recipes DROP CONSTRAINT IF EXISTS recipes_style_fk;")
    psql("TRUNCATE corpus.recipes CASCADE;")
    print("copying recipes ...", flush=True)
    with open(os.path.join(tmp, "recipes.csv"), "rb") as fh:
        psql(f"COPY corpus.recipes ({RECIPE_COLS}) FROM STDIN WITH (FORMAT csv)", stdin=fh)

    # Children carry source_ref, not the generated id: they are joined to it
    # rather than relying on COPY preserving insertion order.
    for key, (tbl, cols) in SPEC.items():
        print(f"copying {tbl} ...", flush=True)
        stage = f"stg_{key}"
        ddl = ", ".join(f"{n} {t}" for n, t in cols)
        names = ", ".join(n for n, _ in cols)
        picks = ", ".join(f"s.{n}" for n, _ in cols)
        psql(f"DROP TABLE IF EXISTS {stage}; "
             f"CREATE UNLOGGED TABLE {stage} (source_ref text, {ddl});")
        with open(os.path.join(tmp, f"{key}.csv"), "rb") as fh:
            psql(f"COPY {stage} FROM STDIN WITH (FORMAT csv)", stdin=fh)
        psql(f"CREATE INDEX ON {stage} (source_ref);")
        psql(f"INSERT INTO corpus.{tbl} (recipe_id, {names}) "
             f"SELECT r.id, {picks} FROM {stage} s "
             f"JOIN corpus.recipes r ON r.source_ref = s.source_ref;")
        psql(f"DROP TABLE {stage};")

    # ⛔ ALL THREE REBUILDS, IN THIS ORDER. Everything derived from the facts is
    # rebuilt here because nothing keeps it in sync on its own -- there is no
    # trigger, by design, since a 1.4M-row load would be crippled by one.
    #   dims    derives the ingredient dimensions and owns the fact-table FKs
    #   search  TRUNCATEs and refills corpus.recipe_search -- and note it is
    #           CASCADE-wiped by the TRUNCATE above, so skipping it leaves every
    #           cohort query matching nothing at all
    #   styles  reads recipe_search (so it must follow it) and re-adds the
    #           recipes.style_raw FK dropped at the top
    print("rebuilding dimensions ...", flush=True)
    print(psql("SELECT * FROM corpus.f_rebuild_dims();"))
    print("rebuilding search index ...", flush=True)
    print(psql("SELECT corpus.f_rebuild_search();") + " rows")
    print("rebuilding styles + ref bridge ...", flush=True)
    print(psql("SELECT * FROM corpus.f_rebuild_styles();"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    load(main(sys.argv[1]))
    print("\n" + psql(
        "SELECT 'recipes', count(*) FROM corpus.recipes "
        "UNION ALL SELECT 'fermentables', count(*) FROM corpus.recipe_fermentables "
        "UNION ALL SELECT 'hops', count(*) FROM corpus.recipe_hops "
        "UNION ALL SELECT 'yeasts', count(*) FROM corpus.recipe_yeasts "
        "UNION ALL SELECT 'misc', count(*) FROM corpus.recipe_misc;"))
