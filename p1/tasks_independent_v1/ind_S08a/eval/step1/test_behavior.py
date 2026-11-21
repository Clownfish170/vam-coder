import pytest

import kv


def test_tuple():
    out = kv.parse_pair("a=1")
    assert isinstance(out, tuple)
    assert out == ("a", "1")


def test_missing_eq():
    with pytest.raises(ValueError):
        kv.parse_pair("nope")


def test_format_regression():
    assert kv.format_pair("a", 1) == "a=1"
