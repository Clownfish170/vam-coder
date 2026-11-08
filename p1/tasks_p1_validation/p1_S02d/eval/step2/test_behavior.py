import pytest
from vault import Session
from accounting import burn_view


def test_view_ok():
    a = Session(50)
    assert burn_view(a, 20) == 30


def test_view_propagates():
    a = Session(50)
    with pytest.raises(ValueError):
        burn_view(a, 0)


def test_contract_regression():
    a = Session(50)
    with pytest.raises(ValueError):
        a.consume(-1)
