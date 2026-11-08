import pytest
import codec


def test_encode2():
    assert codec.encode2("login", "alice", "urgent") == "v2|login|alice|urgent"


def test_decode2():
    assert codec.decode2("v2|login|alice|urgent") == ("login", "alice", "urgent")


def test_decode2_bad():
    with pytest.raises(ValueError):
        codec.decode2("v1|a|b|c")
    with pytest.raises(ValueError):
        codec.decode2("v2|a|b")


def test_decode_regression():
    assert codec.decode("k|v") == ("k", "v")
