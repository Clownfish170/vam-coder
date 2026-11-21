from converter import convert, bulk
from parserx import normalize


def test_bulk():
    assert bulk(["x y", "z"]) == "X Y|Z"


def test_bulk_empty():
    assert bulk([]) == ""


def test_convert_regression():
    assert convert("  ab ") == "AB"


def test_normalize_regression():
    assert normalize("  Ab ") == "ab"
