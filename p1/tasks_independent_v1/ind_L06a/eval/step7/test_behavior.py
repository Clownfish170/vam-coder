import pytest
import codec


def test_version_v2():
    assert codec.version_of("v2|a|b|c") == 2


def test_version_v1():
    assert codec.version_of("hi|there") == 1


def test_version_bad():
    with pytest.raises(ValueError):
        codec.version_of("lonely")


def test_decode_any_regression():
    assert codec.decode_any("v2|k|b|t") == ("k", "b", "t")
