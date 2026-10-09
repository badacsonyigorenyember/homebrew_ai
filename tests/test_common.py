from decimal import Decimal as D
import pytest
from psycopg.types.range import Range
from loaders.common import num, to_range, f_to_c, name_key, read_beerjson

def test_num():
    assert num(None) is None and num("") is None and num("  ") is None
    assert num("25") == D("25") and num(5.0) == D("5.0")

def test_to_range_closed():
    assert to_range("1.056", "1.070") == Range(D("1.056"), D("1.070"), "[]")

def test_to_range_open_ended():          # Review focus 1
    assert to_range(5.0, None) == Range(D("5.0"), None, "[)")
    assert to_range(None, "12") == Range(None, D("12"), "(]")

def test_to_range_missing():             # Review focus 2
    assert to_range(None, "") is None

def test_to_range_inverted_raises():
    with pytest.raises(ValueError, match="10.*5"):
        to_range(10, 5)

def test_f_to_c():
    assert f_to_c(64) == D("17.8") and f_to_c(73) == D("22.8")

def test_name_key():
    assert name_key("Citra®") == "citra"
    assert name_key("Hallertau Mittelfrüh") == "hallertaumittelfruh"
    assert name_key("Saaz (US)") == "saazus"      # Review focus 3

def test_read_beerjson_strips_comment_header(tmp_path):
    path = tmp_path / "sample.json"
    path.write_text('// header line one\n  // header line two\n{"beerjson": {"version": 1}}\n')
    assert read_beerjson(path) == {"version": 1}
