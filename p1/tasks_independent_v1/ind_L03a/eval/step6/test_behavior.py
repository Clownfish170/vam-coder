import terms
import stock


def test_min_updated():
    assert terms.BACKORDER_MIN == 10


def test_reserve_regression():
    stock.ITEMS.clear()
    stock.receive("a", 10)
    assert stock.reserve("a", 4) is True
    assert stock.available("a") == 6


def test_release_regression():
    stock.ITEMS.clear()
    stock.receive("a", 5)
    assert stock.release("a", 2) == 7
