"""The role measurement tool: scored role and the gate verdict (no stack)."""

from evals import roles


def brief(*pairs):
    return {"wanted": [{"item": i, "role": r} for i, r in pairs]}


def test_scored_role_finds_adjunct_inside_a_longer_item():
    assert roles.scored_role(brief(("orange blossom honey", "feature")), "honey") == "feature"


def test_scored_role_accepts_plain_plural():
    assert roles.scored_role(brief(("raspberries", "feature")), "raspberry") == "feature"
    assert roles.scored_role(brief(("molasses", "background")), "molasses") == "background"
    assert roles.scored_role(brief(("oranges", "feature")), "orange") == "feature"


def test_scored_role_none_when_adjunct_missing():
    assert roles.scored_role(brief(("oats", "background")), "honey") is None
    assert roles.scored_role({"wanted": []}, "honey") is None
    assert roles.scored_role(None, "honey") is None


def test_scored_role_mixed_on_disagreement():
    b = brief(("honey", "feature"), ("wildflower honey", "background"))
    assert roles.scored_role(b, "honey") == "mixed"


def test_scored_role_ignores_part_of_a_word():
    assert roles.scored_role(brief(("honeydew", "feature")), "honey") is None


def wording(id_, set_, expected, gated_roles):
    return {"id": id_, "set": set_, "expected": expected,
            "settings": {"gated": roles.summarise_runs(gated_roles, expected, [1] * len(gated_roles), [1] * len(gated_roles))}}


def all_right():
    ws = [wording("r01", "clear", "feature", ["feature"] * 3),
          wording("r15", "clear", "background", ["background"] * 3)]
    ws += [wording(f"x{i}", "clear", "feature", ["feature"] * 3) for i in range(19)]
    ws += [wording("r22", "ambiguous", "", ["feature"] * 3)]
    ws += [wording(f"h{i}", "held_out", "background", ["background"] * 3) for i in range(10)]
    return ws


def test_gate_met_on_all_right():
    g = roles.gate(all_right())
    assert g["met"] and g["b12_b19"]["ok"] and g["clear"]["ok"]
    assert g["clear"]["value"] == "21/21" and g["held_out"]["value"] == "10/10"


def fail(ws, id_, runs):
    return [wording(w["id"], w["set"], w["expected"], runs) if w["id"] == id_ else w for w in ws]


def test_gate_fails_when_b19_is_feature_once():
    ws = fail(all_right(), "r15", ["background", "feature", "background"])
    g = roles.gate(ws)
    assert not g["met"] and not g["b12_b19"]["ok"]
    assert g["clear"]["ok"] is False or g["clear"]["value"] == "20/21"


def test_gate_fails_on_two_clear_wrong():
    ws = fail(fail(all_right(), "x0", ["background"] * 3), "x1", ["background"] * 3)
    g = roles.gate(ws)
    assert not g["met"] and not g["clear"]["ok"] and g["b12_b19"]["ok"]


def test_gate_allows_one_clear_wrong():
    ws = fail(all_right(), "x0", ["background"] * 3)
    g = roles.gate(ws)
    assert g["clear"]["ok"] and g["clear"]["value"] == "20/21"


def test_gate_fails_when_an_ambiguous_wording_flips():
    ws = fail(all_right(), "r22", ["feature", "background", "feature"])
    g = roles.gate(ws)
    assert not g["met"] and not g["consistent"]["ok"] and g["clear"]["ok"]


def test_gate_fails_on_two_held_out_wrong():
    ws = fail(fail(all_right(), "h0", ["feature"] * 3), "h1", ["feature"] * 3)
    g = roles.gate(ws)
    assert not g["met"] and not g["held_out"]["ok"] and g["held_out"]["value"] == "8/10"


def test_gate_allows_one_held_out_wrong():
    g = roles.gate(fail(all_right(), "h0", ["feature"] * 3))
    assert g["held_out"]["ok"] and g["met"]


WORDINGS = [{"id": "r01", "set": "clear"}, {"id": "r22", "set": "ambiguous"},
            {"id": "h01", "set": "held_out"}]


def ids(ws):
    return [w["id"] for w in ws]


def test_select_full_run_includes_held_out():
    assert ids(roles.select(WORDINGS, None, None)) == ["r01", "r22", "h01"]


def test_select_sets_never_picks_held_out():
    assert ids(roles.select(WORDINGS, ["clear", "ambiguous"], None)) == ["r01", "r22"]


def test_select_ids_never_picks_held_out():
    assert ids(roles.select(WORDINGS, None, ["r01", "h01"])) == ["r01"]
