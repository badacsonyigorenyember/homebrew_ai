"""Step 2 signal functions in db/022_step2.sql, each called on its own with literal inputs.

Requirements R3-R7, acceptance A6 and A7 of docs/work/m2-best-fit-style/brief.md.
"""

import json

import pytest

from loaders.db import connect


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


def one(conn, sql, *params):
    return conn.execute(sql, params).fetchone()[0]


def name_score(conn, named, style_name, aliases=()):
    return float(one(conn, "select app.style_name_score(%s, %s, %s::text[])", named, style_name, list(aliases)))


def number_score(conn, stated, abv=None, og=None, ibu=None, srm=None):
    sql = (
        "select score, outside from app.style_number_score(%s::jsonb, %s::numrange, %s::numrange, "
        "%s::numrange, %s::numrange)"
    )
    score, outside = conn.execute(sql, (json.dumps(stated), abv, og, ibu, srm)).fetchone()
    return float(score), outside


def words(conn, brief):
    return one(conn, "select app.brief_words(%s::jsonb)", json.dumps(brief))


@pytest.mark.stack
def test_exact_name_scores_one(conn):
    assert name_score(conn, "Irish Stout", "Irish Stout") == 1


@pytest.mark.stack
def test_alias_scores_one(conn):
    aliases = one(conn, "select array_agg(alias) from app.style_alias() where guide = 'BJCP' and code = '16A'")
    assert name_score(conn, "milk stout", "Sweet Stout", aliases) == 1


@pytest.mark.stack
def test_partial_name(conn):
    assert name_score(conn, "imperial stout", "Irish Stout") == pytest.approx(0.25)


@pytest.mark.stack
def test_accents_and_case_ignored(conn):
    assert name_score(conn, "MÄRZEN", "Marzen") == 1


@pytest.mark.stack
def test_ipa_spelled_out(conn):
    assert name_score(conn, "hazy IPA", "Juicy or Hazy India Pale Ale") == pytest.approx(0.8)


@pytest.mark.stack
def test_guide_words_not_part_of_the_name(conn):
    assert name_score(conn, "BJCP German pils", "German Pils") == 1


@pytest.mark.stack
def test_no_name_scores_zero(conn):
    assert name_score(conn, None, "German Pils") == 0
    assert name_score(conn, "", "German Pils") == 0


@pytest.mark.stack
def test_number_at_centre_and_edge(conn):
    # 1 (centre) or 0.5 (edge), plus the tightness bonus 1 / (1 + 4 / 1.0) = 0.2 for a 4-point range
    assert number_score(conn, {"abv": 10}, abv="[8,12]")[0] == pytest.approx(1.2)
    assert number_score(conn, {"abv": 8}, abv="[8,12]")[0] == pytest.approx(0.7)


@pytest.mark.stack
def test_tight_range_beats_wide_range(conn):
    """The same formula for every number: the narrower range around the value scores higher."""
    tight = number_score(conn, {"abv": 4}, abv="[3.8,5.0]")[0]
    wide = number_score(conn, {"abv": 4}, abv="[3.2,6.3]")[0]
    assert tight > wide
    assert number_score(conn, {"ibu": 30}, ibu="[25,35]")[0] > number_score(conn, {"ibu": 30}, ibu="[10,50]")[0]


@pytest.mark.stack
def test_number_outside_by_distance(conn):
    score, outside = number_score(conn, {"abv": 4}, abv="[8.0,12.0]")
    assert score == -4
    assert len(outside) == 1 and "ABV" in outside[0] and "8.0–12.0" in outside[0]


@pytest.mark.stack
def test_open_range(conn):
    assert number_score(conn, {"srm": 45}, srm="[40,)")[0] == 0.75


@pytest.mark.stack
def test_no_range_scores_zero(conn):
    assert number_score(conn, {"abv": 5, "ibu": 30}) == (0, [])


@pytest.mark.stack
def test_numbers_add_up(conn):
    score, _ = number_score(conn, {"abv": 10, "ibu": 30}, abv="[8,12]", ibu="[20,40]")
    assert score == pytest.approx(1.2 + 1 + 1 / 3)


@pytest.mark.stack
def test_tag_hit_beats_text_hit(conn):
    tag = one(conn, "select app.style_word_score(array['roasty'], array['roasty'], 'smooth')")
    text = one(conn, "select app.style_word_score(array['roasty'], array[]::text[], 'a roasty finish')")
    assert (float(tag), float(text)) == (1, 0.5)


@pytest.mark.stack
def test_negated_phrase_dropped(conn):
    got = words(conn, {"hints": [], "unknown": ["not too roasty", "fruity esters"]})
    assert "roasty" not in got and "fruity" in got


@pytest.mark.stack
def test_hint_mapped_to_tag(conn):
    assert "dark-color" in words(conn, {"hints": ["darker"], "unknown": []})
    assert "hoppy" in words(conn, {"hints": ["juicy"], "unknown": []})


@pytest.mark.stack
def test_bjcp_and_ba_tags_read(conn):
    assert one(conn, """select app.style_tags('{"tags": "Malty, Roasty ,sweet"}'::jsonb)""") == [
        "malty", "roasty", "sweet",
    ]
    assert one(conn, """select app.style_tags('{"tags": ["Hoppy", "bitter"]}'::jsonb)""") == ["hoppy", "bitter"]


def prominent(conn, request, adjunct="honey"):
    return one(conn, "select app.adjunct_is_prominent(%s, %s)", request, adjunct)


@pytest.mark.stack
def test_forward_adjunct_is_prominent(conn):
    assert prominent(conn, "a honey-forward golden ale") is True


@pytest.mark.stack
def test_touch_of_adjunct_is_not(conn):
    assert prominent(conn, "a porter with a touch of honey") is False


@pytest.mark.stack
def test_adjunct_in_other_sentence_is_not(conn):
    assert prominent(conn, "Honey in it. Make it shine bright.") is False


@pytest.mark.stack
@pytest.mark.parametrize(
    "request_text",
    [
        "A blonde ale where the honey really shines.",
        "a honey ale that showcases the honey",
        "a honey ale that showcased the honey",
        "some hops and plenty of citrus, but honey forward",
        "I want some citrus hops and honey forward",
        "Plenty of honey and some citrus.",
        "Lots of honey and a little lemon zest.",
        "Honey forward and some citrus.",
        "I want some citrus and honey forward.",
    ],
)
def test_cue_word_forms_and_distant_dampers_stay_prominent(conn, request_text):
    assert prominent(conn, request_text) is True


@pytest.mark.stack
def test_nearby_damper_still_cancels(conn):
    assert prominent(conn, "an ale with some honey that shines") is False
    assert prominent(conn, "some very nice honey that shines") is False


@pytest.mark.stack
def test_damper_after_the_adjunct_never_cancels(conn):
    """A damper after the adjunct belongs to the next item."""
    assert prominent(conn, "the honey should shine, a bit of citrus too") is True
    assert prominent(conn, "honey shines and a little spice") is True


@pytest.mark.stack
def test_conjunction_ends_the_damper_reach(conn):
    """'some citrus and honey forward': the 'and' ends the damper, so honey is prominent;
    'some honey and citrus that shine' still damps (honey follows the damper directly)."""
    assert prominent(conn, "some citrus and honey forward") is True
    assert prominent(conn, "some honey and citrus, forward") is False


@pytest.mark.stack
def test_cue_is_quoted_as_written(conn):
    assert one(conn, "select app.adjunct_cue(%s, 'honey')", "the honey really shines") == "shines"
    assert one(conn, "select app.adjunct_cue(%s, 'honey')", "honey you can taste") == "taste"


@pytest.mark.stack
def test_name_covers_needs_every_named_word(conn):
    covers = "select app.style_name_covers(%s, %s, '{}'::text[])"
    assert one(conn, covers, "imperial stout", "Imperial Stout") is True
    assert one(conn, covers, "session IPA", "English IPA") is False


@pytest.mark.stack
@pytest.mark.parametrize(
    "request_text, expected",
    [
        ("a German pils per BJCP", "bjcp"),
        ("a hazy pale ale, BA style", "ba"),
        ("per the Brewers Association", "ba"),
        ("a bass ale with bananas", None),
        ("BJCP or BA, you choose", None),
    ],
)
def test_guide_named_in_request(conn, request_text, expected):
    assert one(conn, "select app.guide_from_request(%s)", request_text) == expected


@pytest.mark.stack
def test_every_alias_has_a_source(conn):
    for fn in ("app.style_alias()", "app.specialty_style()"):
        rows = conn.execute(f"select guide, code, source from {fn}").fetchall()
        assert rows, fn
        for guide, code, source in rows:
            assert source and source.strip(), f"{fn}: {guide} {code} has no source"
            found = one(conn, "select count(*) from ref.beer_style where guide = %s and code = %s", guide, code)
            assert found == 1, f"{fn}: {guide} {code} is not in ref.beer_style"
