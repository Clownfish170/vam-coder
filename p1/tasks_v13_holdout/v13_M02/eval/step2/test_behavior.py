from stream import dedupe
from stream_rules import normalize


def test_normalize_lower():
    assert normalize(["A", "Bc"]) == ["a", "bc"]


def test_normalize_non_string():
    assert normalize([1]) == [1]


def test_dedupe_regression():
    assert dedupe(["b", "a", "b"]) == ["b", "a"]
