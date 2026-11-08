import pytest
from vault import Loan
from accounting import due_view


def test_view_ok():
    a = Loan(120)
    assert due_view(a, 40) == 80


def test_view_propagates():
    a = Loan(120)
    with pytest.raises(ValueError):
        due_view(a, 0)


def test_contract_regression():
    a = Loan(120)
    with pytest.raises(ValueError):
        a.repay(-1)
