import pytest
import codec


def test_any_v1():
    assert codec.decode_any("k|v") == ("k", "v")


def test_any_v2():
    assert codec.decode_any("v2|login|alice|urgent") == ("login", "alice", "urgent")


def test_any_bad():
    with pytest.raises(ValueError):
        codec.decode_any("junk")
    with pytest.raises(ValueError):
        codec.decode_any("v3|a|b|c")


def test_decode2_regression():
    assert codec.decode2("v2|k|b|t") == ("k", "b", "t")
