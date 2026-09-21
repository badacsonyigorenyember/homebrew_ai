#!/usr/bin/env python3
"""Load the filtered Brewer's Friend corpus into corpus.bf_* (77_bf_corpus.sql).

One-shot. The DDL runs on every stack start; this does not. Re-running is safe:
it truncates first.

    python3 scripts/ingest/bf_load.py <recipes_full.txt>

Filters (TREND-SCHEMA.md D1/D2):
  views > 500          36,271 of 179,455 recipes; 114 styles reach n>=50
  script-block clean   drops CJK/Hangul/Cyrillic/Hebrew/Arabic/Thai names only.
                       NOT an ASCII filter -- that would drop Kolsch and Jalapeno.

Source: angeredsquid/brewers-friend-beer-recipes (Kaggle, CC0).
"""
import csv, difflib, json, re, subprocess, sys, tempfile, unicodedata

MIN_VIEWS = 500

# Script blocks that mean "not readable here". Latin-with-diacritics is KEPT.
_SCRIPTS = ((0x3040, 0x30FF), (0x4E00, 0x9FFF), (0xAC00, 0xD7AF),
            (0x0400, 0x04FF), (0x0590, 0x05FF), (0x0600, 0x06FF), (0x0E00, 0x0E7F))

_PREFIX = re.compile(
    r"^(american|united kingdom|german|belgian|french|canadian|australian|"
    r"new zealand|czech|danish|dutch|finnish|irish|polish|swedish|norwegian|"
    r"austrian|italian|spanish|mexican|japanese|chilean|us|uk)\s+-\s+")


def foreign_script(s):
    return any(lo <= ord(c) <= hi for c in s for lo, hi in _SCRIPTS)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def classify(name, lov):
    """Corpus fermentable string -> corpus.fermentable_types.type_key, or None.

    Reads only values the recipe already carries. `measured` 2026-09-19: 98.7%
    of rows classify. The 1.3% that do not are mostly fruit, which belongs in
    misc rather than the grist.
    """
    n = _PREFIX.sub("", name.lower()).strip()
    L = num(lov)
    h = lambda *w: any(k in n for k in w)

    if h("lactose"):                                            return "sugar_lactose"
    if h("dextrose", "corn sugar", "sucrose", "table sugar", "cane sugar",
          "candi", "molasses", "maple", "treacle", "invert",
          "turbinado", "demerara", "brown sugar", "agave"):      return "sugar"
    if h("honey") and not h("malt"):                             return "sugar"
    if h("extract") and h("dry malt", "dme", "liquid malt", "lme", "malt extract"):
        return "extract"
    if h("acidulated", "acid malt", "sauermalz"):                return "acidulated"
    if h("carapils", "dextrine", "carafoam"):                    return "dextrine"
    if h("smoked", "rauch", "peated", "mesquite"):               return "smoked"
    if h("roasted barley", "roast barley"):                      return "roast_barley"
    if h("de-bittered black", "debittered black"):               return "black"
    if h("black patent", "blackprinz", "black malt", "carafa",
          "midnight wheat", "black barley"):                     return "black"
    if h("chocolate"):                                           return "chocolate"
    if h("special b"):                                           return "crystal_extra_dark"
    if h("crystal", "caramel", "cara"):
        if L is None:                                            return "crystal_medium"
        if L <= 25:                                              return "crystal_light"
        if L <= 70:                                              return "crystal_medium"
        if L <= 120:                                             return "crystal_dark"
        return "crystal_extra_dark"
    if h("coffee malt", "abbey", "red x"):                       return "kilned_specialty"
    if re.fullmatch(r"(brown|amber)", n):                        return "kilned_specialty"
    if h("biscuit", "victory", "amber malt", "brown malt", "melanoidin",
          "aromatic", "special roast", "honey malt"):            return "kilned_specialty"
    if h("munich"):                                              return "munich"
    if h("vienna"):                                              return "vienna"
    if h("oat", "golden naked"):                                 return "oats"
    if h("rye"):                                                 return "rye"
    if h("flaked corn", "maize", "corn", "grits", "polenta", "rice",
          "flaked barley", "torrified", "unmalted", "spelt", "buckwheat",
          "sorghum", "quinoa", "millet"):                        return "adjunct_starch"
    if h("wheat"):                                               return "wheat"
    if h("pilsner", "pilsen", "lager malt") or re.fullmatch(r"lager", n):
        return "base_pilsner"
    if h("maris otter", "golden promise", "pale ale", "2-row", "2 row",
          "six-row", "6-row", "pale malt", "optic", "halcyon", "mild malt"):
        return "base_pale"
    if L is not None and L <= 4 and h("malt", "pale"):            return "base_pale"
    return None


def norm_hop(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


# Spec 1.6's named, evidenced corpus-spelling aliases -- corpus quirks, not
# substitutes, so they do not belong in ref.hops.alternatives.
_ALIASES = {
    norm_hop("Hallertau Hersbrucker"): "Hersbrucker",
    norm_hop("Domestic Hallertau"): "Hallertau (US)",
    norm_hop("Kent Goldings"): "East Kent Golding",
    norm_hop("Ekuanot"): "Equinox",
    norm_hop("Cascade"): "Cascade (US)",
    norm_hop("Amarillo"): "Amarillo VGXP01",
    norm_hop("Cluster"): "Cluster (US)",
    norm_hop("Northern Brewer"): "Northern Brewer (US)",
}

# Bare names with more than one plausible ref.hops target and nothing in the
# data to decide between them -- a refusal, not a coin-flip. `goldings`: East
# Kent Golding (36), Golding (US) (51), Goldings (NZ) (215) are all plausible.
_AMBIGUOUS = frozenset({norm_hop("Goldings")})


# ---------------------------------------------------------------------------
# The corpus was scraped before July 2020 and labels recipes with BJCP 2008/2015
# style NAMES; ref.styles is BJCP 2021. `measured` 2026-09-21: that mismatch, not
# any missing style, is why 10,397 of 35,620 recipes carried no ref_style_id.
# Mapped to CODE rather than name -- a 2021 code is stable, a name is what
# changed. Every entry is a guide-revision rename or an absorbed sub-style.
#
# ⛔ NOT MAPPED, DELIBERATELY: mead, cider, perry and their variants have no
# target at all -- ref.styles is the BJCP BEER guide, 116 styles, no M/C
# categories. Nor are the catch-alls ("--", Specialty Beer, Clone Beer, Belgian
# Specialty Ale), which name no base style to fold to. Those stay NULL: an
# unresolved style is honest, a guessed one corrupts every trend row it reaches.
# ---------------------------------------------------------------------------
_STYLE_ALIASES = {
    # Renamed between guide revisions
    "Imperial IPA": "22A",                   # Double IPA
    "Russian Imperial Stout": "20C",         # Imperial Stout
    "Weizen/Weissbier": "10A",
    "Robust Porter": "20A",                  # American Porter
    "Brown Porter": "13C",                   # English Porter
    "California Common Beer": "19B",
    "American Wheat or Rye Beer": "1D",      # base style is the wheat beer
    "Extra Special/Strong Bitter (ESB)": "11C",
    "Special/Best/Premium Bitter": "11B",
    "Standard/Ordinary Bitter": "11A",
    "German Pilsner (Pils)": "5D",
    "Bohemian Pilsener": "3B",               # Czech Premium Pale Lager
    "Oktoberfest/Märzen": "6A",
    "Dry Stout": "15B",                      # Irish Stout
    "Northern English Brown": "13B",         # British Brown Ale
    "Southern English Brown": "27D",         # Historical: London Brown Ale
    "London Brown Ale": "27D",
    "Mild": "13A",                           # Dark Mild
    "Strong Scotch Ale": "17C",              # Wee Heavy
    "English Barleywine": "17D",
    "Dunkelweizen": "10B",                   # Dunkles Weissbier
    "Maibock/Helles Bock": "4C",
    "Traditional Bock": "6C",                # Dunkles Bock
    "Düsseldorf Altbier": "7B",
    "North German Altbier": "7B",
    "Scottish Export 80/-": "14C",
    "Scottish Heavy 70/-": "14B",
    "Scottish Light 60/-": "14A",
    "Trappist Single": "26A",                # Belgian Single
    "Straight (Unblended) Lambic": "23D",
    "Flanders Brown Ale/Oud Bruin": "23C",
    "Dortmunder Export": "5C",               # German Helles Exportbier
    "Classic Rauchbier": "6B",
    "Other Smoked Beer": "32B",             # Specialty Smoked Beer
    "Premium American Lager": "2A",          # International Pale Lager
    "Light American Lager": "1A",
    "Standard American Lager": "1B",
    "Dark American Lager": "2C",             # International Dark Lager
    "Holiday/Winter Special Spiced Beer": "30C",
    # Absorbed into BJCP 2021 Historical Beer (27)
    "Classic American Pilsner": "27F",       # Pre-Prohibition Lager
    "Pre-Prohibition Lager": "27F",
    "Pre-Prohibition Porter": "27G",
    "Roggenbier (German Rye Beer)": "27H",
    "Roggenbier": "27H",
    "Sahti": "27I",
    "Kentucky Common": "27B",
    "Lichtenhainer": "27C",
    "Piwo Grodziskie": "27E",
    "Kellerbier: Pale Kellerbier": "27A",
    "Kellerbier: Amber Kellerbier": "27A",
    # BJCP 2021 gave New England IPA its own style; the rest stay 21B Specialty IPA
    "Specialty IPA: New England IPA": "21C",  # Hazy IPA
    "Specialty IPA: Black IPA": "21B",
    "Specialty IPA: Red IPA": "21B",
    "Specialty IPA: White IPA": "21B",
    "Specialty IPA: Rye IPA": "21B",
    "Specialty IPA: Belgian IPA": "21B",
    "Specialty IPA: Brown IPA": "21B",
}
_STYLE_ALIASES = {norm_hop(k): v for k, v in _STYLE_ALIASES.items()}


def psql(sql, stdin=None):
    """supabase_admin, not postgres -- postgres is not a superuser in this stack."""
    p = subprocess.run(
        ["docker", "exec", "-i", "supabase-db", "psql", "-U", "supabase_admin",
         "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-c", sql],
        stdin=stdin, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"psql failed:\n{p.stderr}")
    return p.stdout.strip()


def hop_index():
    """name -> ref.hops.id, built from canonical ref.hops.name values only.

    `ref.hops.alternatives` means SUBSTITUTES ("hops you could brew with
    instead"), not alternative spellings, so it must never be indexed by name
    here -- doing so previously answered "give me X" with "something you could
    use instead of X" (`measured` 2026-09-20: 2,803 confidently-wrong rows,
    worst case Hallertau Mittelfruh x1,944 -> Hallertauer Gold, when ref.hops
    has no Mittelfruh row at all).
    """
    idx = {}
    rows = psql("SELECT id, name FROM ref.hops ORDER BY id")
    for line in rows.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or not parts[0].isdigit():
            continue
        hid, name = parts[0], parts[1]
        idx.setdefault(norm_hop(name), hid)
    return idx


def style_index():
    """(normalised BJCP style name -> id, BJCP code -> id), guide='BJCP'.

    The code index exists for _STYLE_ALIASES, which maps the corpus's older
    guide-revision names onto stable 2021 codes.
    """
    by_name, by_code = {}, {}
    for line in psql("SELECT id, code, name FROM ref.styles WHERE guide='BJCP'").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 3 and parts[0].isdigit():
            by_code[parts[1]] = parts[0]
            by_name[norm_hop(parts[2])] = parts[0]
    return by_name, by_code


def resolve_style(style_raw, by_name, by_code):
    """Corpus style string -> ref.styles.id, or None.

    Exact 2021 name first, then the guide-revision alias map. None is a real
    answer: mead, cider and the catch-all labels have no BJCP beer style.
    """
    if not style_raw:
        return None
    sn = norm_hop(style_raw)
    if sn in by_name:
        return by_name[sn]
    code = _STYLE_ALIASES.get(sn)
    return by_code.get(code) if code else None


def main(path):
    hops = hop_index()
    styles, style_codes = style_index()
    alias_ids = {k: hops[norm_hop(v)] for k, v in _ALIASES.items()}
    hop_keys = list(hops)
    fuzzy_cache = {}
    tmp = {k: tempfile.NamedTemporaryFile("w+", newline="", suffix=f".{k}.csv")
           for k in ("r", "f", "h", "m", "y")}
    w = {k: csv.writer(v) for k, v in tmp.items()}
    rid = 0
    kept = skipped_views = skipped_script = 0
    seen, dupes = set(), 0

    for i, line in enumerate(open(path, encoding="utf-8", errors="replace")):
        s = line.strip()
        if i == 0:
            s = s[1:]
        if s.endswith(","):
            s = s[:-1]
        mt = re.match(r'^"\d+":\s*(\{.*)$', s)
        if not mt:
            continue
        body = mt.group(1)
        if body.endswith("}}"):
            body = body[:-1]
        try:
            r = json.loads(body)
        except ValueError:
            continue

        if (r.get("views") or 0) <= MIN_VIEWS:
            skipped_views += 1
            continue
        name = r.get("name") or ""
        if foreign_script(name):
            skipped_script += 1
            continue
        url = r.get("url")
        if not url:
            continue
        if not name:
            continue
        if url in seen:
            dupes += 1
            continue
        seen.add(url)

        rid += 1
        kept += 1
        style_raw = (r.get("style") or "").strip() or None
        w["r"].writerow([
            rid, url, name, style_raw,
            resolve_style(style_raw, styles, style_codes),
            r.get("method"), int(r.get("views") or 0),
            num(r.get("batch")), num(r.get("og")), num(r.get("fg")),
            num(r.get("abv")), num(r.get("ibu")), num(r.get("color"))])

        for pos, x in enumerate(r.get("fermentables") or []):
            if isinstance(x, list) and len(x) >= 5:
                w["f"].writerow([rid, pos, x[1], classify(str(x[1]), x[3]),
                                 num(x[4]), num(x[2]), num(x[3])])
        for pos, x in enumerate(r.get("hops") or []):
            if isinstance(x, list) and len(x) >= 2:
                hn = norm_hop(str(x[1]))
                if hn in _AMBIGUOUS:
                    hop_id = None
                else:
                    hop_id = alias_ids.get(hn)
                    if hop_id is None:
                        hop_id = hops.get(hn)
                    if hop_id is None:
                        if hn not in fuzzy_cache:
                            m = difflib.get_close_matches(hn, hop_keys, n=1, cutoff=0.87)
                            fuzzy_cache[hn] = hops[m[0]] if m else None
                        hop_id = fuzzy_cache[hn]
                t = str(x[5]) if len(x) > 5 else ""
                mm = re.match(r"\s*([\d.]+)", t)
                timing_min = float(mm.group(1)) if mm else None
                if timing_min is not None and abs(timing_min) >= 1_000_000:
                    timing_min = None
                w["h"].writerow([rid, pos, x[1], hop_id,
                                 num(x[0]), (x[4] if len(x) > 4 else None),
                                 timing_min])
        for pos, x in enumerate(r.get("other") or []):
            if isinstance(x, list) and len(x) > 1:
                w["m"].writerow([rid, pos, x[1], x[0],
                                 (x[2] if len(x) > 2 else None),
                                 (x[3] if len(x) > 3 else None)])
        y = r.get("yeast")
        if isinstance(y, list) and y and isinstance(y[0], str):
            w["y"].writerow([rid, 0, y[0]])

    print(f"kept {kept:,}  skipped: views<={MIN_VIEWS} {skipped_views:,}, "
          f"foreign script {skipped_script:,}, duplicate url {dupes:,}", file=sys.stderr)
    for f in tmp.values():
        f.flush()
    return tmp


def load(tmp):
    psql("TRUNCATE corpus.bf_recipes CASCADE")
    psql("ALTER TABLE corpus.bf_recipes ALTER COLUMN id DROP IDENTITY IF EXISTS")
    cols = ("id, source_ref, name, style_raw, ref_style_id, method, views, "
            "batch_l, og, fg, abv, ibu, color_srm")
    order = [("r", f"corpus.bf_recipes ({cols})"),
             ("f", "corpus.bf_fermentables"),
             ("h", "corpus.bf_hops"),
             ("m", "corpus.bf_miscs"),
             ("y", "corpus.bf_yeasts")]
    for key, target in order:
        tmp[key].seek(0)
        with open(tmp[key].name) as fh:
            psql(f"COPY {target} FROM STDIN WITH (FORMAT csv)", stdin=fh)
    psql("ALTER TABLE corpus.bf_recipes ALTER COLUMN id "
         "ADD GENERATED ALWAYS AS IDENTITY")
    psql("SELECT setval(pg_get_serial_sequence('corpus.bf_recipes','id'), "
         "coalesce(max(id),1)) FROM corpus.bf_recipes")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    load(main(sys.argv[1]))
    print("\n" + psql(
        "SELECT 'recipes', count(*) FROM corpus.bf_recipes "
        "UNION ALL SELECT 'fermentables', count(*) FROM corpus.bf_fermentables "
        "UNION ALL SELECT 'hops', count(*) FROM corpus.bf_hops "
        "UNION ALL SELECT 'miscs', count(*) FROM corpus.bf_miscs "
        "UNION ALL SELECT 'yeasts', count(*) FROM corpus.bf_yeasts;"))
