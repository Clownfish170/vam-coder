import stock


def test_reserve_success():
    stock.ITEMS.clear()
    stock.receive("a", 10)
    assert stock.reserve("a", 4) is True
    assert stock.available("a") == 6


def test_reserve_short():
    stock.ITEMS.clear()
    stock.receive("a", 3)
    assert stock.reserve("a", 5) is False
    assert stock.available("a") == 3


def test_receive_regression():
    import pytest
    stock.ITEMS.clear()
    with pytest.raises(ValueError):
        stock.receive("a", -1)
