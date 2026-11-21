import pytest
from vault import Reserve


def test_positive_ok():
    a = Reserve(100)
    assert a.withdraw(30) == 70


def test_zero_raises():
    a = Reserve(100)
    with pytest.raises(ValueError):
        a.withdraw(0)


def test_negative_raises():
    a = Reserve(100)
    with pytest.raises(ValueError):
        a.withdraw(-5)
