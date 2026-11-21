import pytest
import codec


def test_negotiate_max():
    assert codec.negotiate([1, 2]) == 2


def test_negotiate_subset():
    assert codec.negotiate([2]) == 2


def test_negotiate_empty():
    with pytest.raises(ValueError):
        codec.negotiate([3, 4])


def test_version_regression():
    assert codec.version_of("hi|there") == 1
