"""Proposal rules of loaders/style_pairs.py (no stack needed).

The test rows are small dicts like the ones the script reads from ref.beer_style:
code, name and abv (text, may be empty).
"""

from loaders.style_pairs import name_words, propose, same_word


def row(code, name):
    return {"code": code, "name": name, "abv": ""}


def proposal_for(ba_row, bjcp_rows):
    return propose([ba_row], bjcp_rows)[0]


def test_koelsch_pairs_with_kolsch():
    p = proposal_for(
        row("german-style-koelsch", "German-Style Koelsch"),
        [row("5B", "Kolsch"), row("5A", "German Leichtbier")],
    )
    assert [m["code"] for m in p["matches"]] == ["5B"]
    assert p["match"] == "BJCP name inside BA name"


def test_dubbel_pairs():
    p = proposal_for(
        row("belgian-style-dubbel", "Belgian-Style Dubbel"),
        [row("26B", "Belgian Dubbel"), row("26C", "Belgian Tripel")],
    )
    assert [m["code"] for m in p["matches"]] == ["26B"]
    assert p["match"] == "same words"


def test_no_pair_for_mexican_amber_lager():
    p = proposal_for(
        row("mexican-style-amber-lager", "Mexican-Style Amber Lager"),
        [row("2A", "International Amber Lager"), row("3B", "Czech Amber Lager")],
    )
    assert p["matches"] == []
    assert p["match"] == ""


def test_ties_are_all_listed():
    p = proposal_for(
        row("ba-x", "Smoked Beer"),
        [row("32A", "Classic Style Smoked Beer"), row("32B", "Smoked Beer")],
    )
    assert sorted(m["code"] for m in p["matches"]) == ["32A", "32B"]


def test_ipa_spelled_out():
    assert name_words("American-Style IPA") == ["american", "india", "pale", "ale"]
    p = proposal_for(
        row("ba-ipa", "American-Style India Pale Ale"),
        [row("21A", "American IPA")],
    )
    assert [m["code"] for m in p["matches"]] == ["21A"]


def test_name_words_drop_accents_and_filler():
    assert name_words("Bière de Garde") == ["biere", "de", "garde"]
    assert name_words("The Beer of the Year Style") == ["year"]


def test_same_word_near_spellings():
    assert same_word("koelsch", "kolsch")
    assert not same_word("stout", "porter")


def test_mexican_is_not_american():
    assert not same_word("mexican", "american")
