import pytest

import balance


def test_insufficient():
    with pytest.raises(balance.InsufficientFunds):
        balance.withdraw(50, 80)


def test_amount_regression():
    with pytest.raises(ValueError):
        balance.withdraw(100, 0)


def test_ok_regression():
    assert balance.withdraw(100, 30) == 70
