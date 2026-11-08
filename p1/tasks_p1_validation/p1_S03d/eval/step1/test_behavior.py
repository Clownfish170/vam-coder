import pytest
from vault import Deposit


def test_positive_ok():
    a = Deposit(80)
    assert a.takeout(25) == 55


def test_zero_raises():
    a = Deposit(80)
    with pytest.raises(ValueError):
        a.takeout(0)


def test_negative_raises():
    a = Deposit(80)
    with pytest.raises(ValueError):
        a.takeout(-5)
