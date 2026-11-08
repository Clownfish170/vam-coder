import pytest
from vault import Deposit
from accounting import peek_view


def test_view_ok():
    a = Deposit(80)
    assert peek_view(a, 25) == 55


def test_view_propagates():
    a = Deposit(80)
    with pytest.raises(ValueError):
        peek_view(a, 0)


def test_contract_regression():
    a = Deposit(80)
    with pytest.raises(ValueError):
        a.takeout(-1)
