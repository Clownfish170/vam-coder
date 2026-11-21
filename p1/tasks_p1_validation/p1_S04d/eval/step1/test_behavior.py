import pytest
from vault import Loan


def test_positive_ok():
    a = Loan(120)
    assert a.repay(40) == 80


def test_zero_raises():
    a = Loan(120)
    with pytest.raises(ValueError):
        a.repay(0)


def test_negative_raises():
    a = Loan(120)
    with pytest.raises(ValueError):
        a.repay(-5)
