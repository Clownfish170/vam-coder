import pytest
from vault import Reserve
from accounting import drain_view


def test_view_ok():
    a = Reserve(100)
    assert drain_view(a, 30) == 70


def test_view_propagates():
    a = Reserve(100)
    with pytest.raises(ValueError):
        drain_view(a, 0)


def test_contract_regression():
    a = Reserve(100)
    with pytest.raises(ValueError):
        a.withdraw(-1)
