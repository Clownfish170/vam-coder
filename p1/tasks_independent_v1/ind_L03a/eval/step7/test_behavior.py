import stock
import terms


def test_backorder_low():
    stock.ITEMS.clear()
    stock.receive("a", 4)
    assert stock.backorder_qty("a") == 6


def test_backorder_none():
    stock.ITEMS.clear()
    stock.receive("a", 50)
    assert stock.backorder_qty("a") == 0


def test_min_regression():
    assert terms.BACKORDER_MIN == 10
