import pytest
import wire


def test_any_v1():
    assert wire.unpack_any("k:v") == ("k", "v")


def test_any_v2():
    assert wire.unpack_any("#7 ping:a=1") == (7, "ping", "a=1")


def test_any_bad():
    with pytest.raises(ValueError):
        wire.unpack_any("nocolon")


def test_unpack2_regression():
    assert wire.unpack2("#1 k:v") == (1, "k", "v")
