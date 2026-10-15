"""The 22 reference recipes (tests/fixtures/reference_recipes.toml) against app.check_recipe.

R16 and A12 of docs/work/s2-formulation-rules. Test data only: nothing under shared/prompts/ or
n8n/workflows/ may mention the fixture file.
"""

import json
import tomllib
from pathlib import Path

import pytest

from loaders.db import connect

ROOT = Path(__file__).resolve().parent.parent
RECIPES_FILE = ROOT / "tests" / "fixtures" / "reference_recipes.toml"
BRIEFS_FILE = ROOT / "evals" / "recipe_briefs.toml"
with RECIPES_FILE.open("rb") as f:
    RECIPES = tomllib.load(f)["recipe"]
with BRIEFS_FILE.open("rb") as f:
    BRIEFS = tomllib.load(f)["brief"]

# Rule failures the user has decided to accept: (brief id, rule number) -> (decision, date).
# Empty until the user decides otherwise (plan.md Task 8).
ACCEPTED_FAILURES: dict[tuple[str, int], tuple[str, str]] = {}


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def ingredient_id(conn, kind, producer, name):
    row = conn.execute(
        "select id from ref.ingredient where kind = %s and producer = %s and name = %s",
        (kind, producer, name),
    ).fetchone()
    assert row, f"{kind} {producer!r} {name!r} is not in ref.ingredient"
    return row[0]


def build_input(conn, rec):
    """The app.check_recipe input for one fixture recipe: names become ingredient ids."""
    hops = []
    for h in rec["hop"]:
        hops.append({
            "ingredient_id": ingredient_id(conn, "hop", "", h["name"]),
            "usage": h["usage"], "minutes": h["minutes"], "g": h["g"], "purpose": h["purpose"],
        })
    y = rec["yeast"]
    return {
        "style_code": rec["style_code"],
        "guidance": rec["guidance"],
        "stated": rec["stated"],
        "targets": rec["targets"],
        "batch": rec["batch"],
        "mash_c": rec["mash_c"],
        "boil_min": rec["boil_min"],
        "fermentables": [
            {"ingredient_id": ingredient_id(conn, "fermentable", f["producer"], f["name"]),
             "pct": f["pct"], "purpose": f["purpose"]}
            for f in rec["fermentable"]
        ],
        "hops": hops,
        "yeast": {"ingredient_id": ingredient_id(conn, "yeast", y["producer"], y["name"]),
                  "ferm_c": y["ferm_c"], "purpose": y["purpose"]},
    }


def check(conn, recipe_input):
    return conn.execute(
        "select app.check_recipe(%s::jsonb)", (json.dumps(recipe_input),)).fetchone()[0]


def test_every_brief_has_exactly_one_recipe():
    brief_ids = [b["id"] for b in BRIEFS]
    assert len(brief_ids) == 22
    assert sorted(r["brief"] for r in RECIPES) == sorted(brief_ids)


def test_recipe_follows_its_brief():
    by_id = {b["id"]: b for b in BRIEFS}
    for rec in RECIPES:
        brief = by_id[rec["brief"]]
        assert rec["guidance"] == brief["guidance"], rec["brief"]
        stated = {k: v for k, v in brief["stated"].items() if k != "batch_l"}
        assert rec["stated"] == stated, rec["brief"]
        assert rec["batch"]["volume_l"] == brief["stated"].get("batch_l", 20), rec["brief"]
        for key, value in stated.items():
            assert rec["targets"][key] == value, f"{rec['brief']}: target {key} is not the stated one"
        if rec["style_code"] != brief["style"]:
            assert rec["brief"] == "b12" and rec["style_code"] == "18A"  # 31B has no vitals


def test_no_prompt_or_workflow_mentions_the_fixture():
    for folder in ("shared/prompts", "n8n/workflows"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file():
                assert "reference_recipes" not in path.read_text(encoding="utf-8"), path


@pytest.mark.stack
def test_names_resolve_and_inputs_match_the_contract(conn):
    schema = (ROOT / "shared/contracts/formulation_check.input.schema.json").read_text()
    for rec in RECIPES:
        recipe_input = build_input(conn, rec)
        errors = conn.execute(
            "select coalesce(extensions.jsonschema_validation_errors(%s::json, %s::json), '{}')",
            (schema, json.dumps(recipe_input))).fetchone()[0]
        assert errors == [], rec["brief"]


@pytest.mark.stack
@pytest.mark.parametrize("rec", RECIPES, ids=[r["brief"] for r in RECIPES])
def test_every_rule_passes(conn, rec):
    out = check(conn, build_input(conn, rec))
    problems = []
    for r in out["results"]:
        number = int(r["rule"])
        if r["status"] == "pass" or (rec["brief"], number) in ACCEPTED_FAILURES:
            continue
        problems.append(f"rule {number} {r['status']}: {r['message']}")
    assert not problems, f"{rec['brief']}: " + " | ".join(problems)
