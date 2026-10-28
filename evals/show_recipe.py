"""Print a saved recipe as plain text, for a person to judge ("would you brew it?").

    python -m evals.show_recipe <run_id>

Reads only. The recipe comes from the saved rows (evals.run.read_recipe); the style, targets and
each pick's `because` come from the run's step 4 and steps 6-9 outputs. Design:
docs/work/m6-compute-validate/plan.md Task 9 (A11).
"""

import sys

from evals import run
from loaders.db import connect


def _because(steps: dict) -> dict:
    """ingredient id -> the because the pick was given in steps 6-9."""
    found = {}
    for n in run.CHOOSE_STEPS:
        for pick in run.grade._picks(n, steps.get(n) or {}):
            found[pick["ingredient_id"]] = pick.get("because")
    return found


def _number(label, value, target, unit=""):
    got = "-" if value is None else f"{value:g}"
    goal = "" if target is None else f"   (target {target:g})"
    return f"  {label:<4} {got}{unit}{goal}"


def _process_lines(process: dict | None) -> list[str]:
    """Steps 12-15 as saved in app.recipe.process: water, mash and volumes, boil, fermentation, packaging."""
    if not process:
        return []
    water, mash, boil = process["water"], process["mash"], process["boil"]
    ferm, pack = process["fermentation"], process["packaging"]
    target, vol = water["target"], mash["volumes"]
    lines = ["", "Water:",
             f"  row: {target.get('row') or 'none'} ({target.get('basis') or 'no basis'}"
             f"{', fallback' if target.get('fallback') else ''})"]
    for salt in water["salts"]:
        lines.append(f"  {salt['name']}: {salt['total_g']:g} g ({salt['strike_g']:g} strike, "
                     f"{salt['sparge_g']:g} sparge), for {salt['aims_at']}")
    if water["none_needed"]:
        lines.append("  no salts needed")
    ph = water["mash_ph"]
    lines.append(f"  mash pH {ph['ph']:g} (aim {ph['target_low']:g}-{ph['target_high']:g})")
    lines.append(f"  acid: {water['acid']['text']}")
    lines.extend(["", f"Mash: strike {vol['strike_l']:g} l at {mash['strike_c']:g} °C, sparge {vol['sparge_l']:g} l, "
                      f"pre-boil {vol['preboil_l']:g} l"])
    lines.extend(f"  {x['name']}: {x['temp_c']:g} °C, {x['minutes']:g} min" for x in mash["steps"])
    lines.extend(["", f"Boil: {boil['boil_min']:g} min"])
    lines.extend(f"  at {x['at_min']:g} min: {x['g']:g} g {x['name']} ({x['usage']})" for x in boil["additions"])
    lines.extend(f"  whirlpool: {x['g']:g} g {x['name']} ({x['usage']})" for x in boil["whirlpool"])
    lines.extend(["", "Fermentation:"])
    for x in ferm["steps"]:
        lines.append(f"  {x['phase']}: {x['temp_c']:g} °C, {x['days']:g} days"
                     + (f"; {x['move_on']}" if x.get("move_on") else ""))
    for x in ferm["pitch"]:
        lines.append(f"  pitch ({x['role']}): {x['amount']:g} {x['unit']} {x['name']}; {x['because']}")
    co2, prime = pack["co2"], pack["priming"]
    lines.extend(["", f"Packaging: CO2 {co2['volumes']:g} volumes ({co2['from']}, {co2['source']})"])
    lines.append(f"  priming: {prime['g']:g} g {prime['sugar']} for {prime['volume_l']:g} l at {prime['temp_c']:g} °C")
    return lines


def format_recipe(request: str, steps: dict, recipe: dict) -> str:
    step4 = steps.get(4) or {}
    style = step4.get("style") or {}
    targets = {k: (v or {}).get("value") for k, v in (step4.get("targets") or {}).items()}
    why = _because(steps)
    lines = [f"Request: {request}", "",
             f"Style: {style.get('name', '?')} ({style.get('code', '?')})",
             f"Batch: {recipe['batch_l']:g} l"]
    mash = (steps.get(10) or {}).get("mash_c")
    if mash is not None:  # the saved rows have no mash until M7's process, so it comes from the step 10 row
        mash_why = next((v["because"] for v in steps[10].get("values_used", []) if v["what"] == "mash"), "")
        lines.append(f"Mash: {round(mash, 1):g} °C ({mash_why})")
    lines.extend(["", "Numbers against targets:"])
    for key, label in (("og", "OG"), ("fg", "FG"), ("abv", "ABV"), ("ibu", "IBU"), ("srm", "SRM")):
        target = targets.get(key)
        lines.append(_number(label, recipe[key], None if target is None else float(target),
                             " %" if key == "abv" else ""))

    # items are told apart as step 10 saved them: fermentables in kg, hops in g with a share,
    # yeast as `ferment`, extras in g without a share
    def section(title, keep, show):
        rows = [i for i in recipe["items"] if keep(i)]
        if rows:
            lines.extend(["", title])
            for i in rows:
                lines.append(f"  {show(i)}")
                if why.get(i["ingredient_id"]):
                    lines.append(f"      because: {why[i['ingredient_id']]}")

    def minutes(i):
        return "" if i["time_min"] is None else f" {i['time_min']:g} min"

    section("Fermentables:", lambda i: i["unit"] == "kg",
            lambda i: f"{i['amount']:g} kg  {i['pct']:g} %  {i['raw_name']}  ({i['usage']})")
    section("Hops:", lambda i: i["unit"] == "g" and i["pct"] is not None and i["usage"] != "ferment",
            lambda i: f"{i['amount']:g} g  {i['raw_name']}  {i['usage']}{minutes(i)}")
    section("Yeast:", lambda i: i["usage"] == "ferment",
            lambda i: f"{i['amount']:g} {i['unit']}  {i['raw_name']}")
    section("Extras:", lambda i: i["unit"] == "g" and i["pct"] is None and i["usage"] != "ferment",
            lambda i: f"{i['amount']:g} g  {i['raw_name']}  {i['usage']}{minutes(i)}")
    lines.extend(_process_lines(recipe.get("process")))
    lines.extend(["", "Deviations:"])
    lines.extend([f"  {d['subject']}: {d['level']} (asked by {d['requested_by']}) {d['note']}"
                  for d in recipe["deviations"]] or ["  none"])
    return "\n".join(lines)


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or not args[0].isdigit():
        print("usage: python -m evals.show_recipe <run_id>", file=sys.stderr)
        return 2
    conn = connect()
    try:
        recipe = run.read_recipe(conn, int(args[0]))
        if recipe is None:
            print(f"run {args[0]} saved no recipe", file=sys.stderr)
            return 1
        steps = run.read_run(conn, int(args[0]))["steps"]
        request = conn.execute("select b.request_text from app.run r join app.brief b on b.id = r.brief_id "
                               "where r.id = %s", (int(args[0]),)).fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    print(format_recipe(request, steps, recipe))
    return 0


if __name__ == "__main__":
    sys.exit(main())
