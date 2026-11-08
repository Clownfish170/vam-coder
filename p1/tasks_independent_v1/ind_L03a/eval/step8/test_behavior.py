import pytest
import stock


def test_reserve_zero():
    stock.ITEMS.clear()
    stock.receive("a", 5)
    with pytest.raises(ValueError):
        stock.reserve("a", 0)


def test_reserve_negative():
    stock.ITEMS.clear()
    stock.receive("a", 5)
    with pytest.raises(ValueError):
        stock.reserve("a", -2)


def test_reserve_ok_regression():
    stock.ITEMS.clear()
    stock.receive("a", 5)
    assert stock.reserve("a", 2) is True
    assert stock.available("a") == 3
