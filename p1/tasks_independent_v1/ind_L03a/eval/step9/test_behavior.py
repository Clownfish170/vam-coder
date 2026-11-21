import stock


def test_low_stock():
    stock.ITEMS.clear()
    stock.receive("a", 4)
    stock.receive("b", 50)
    stock.receive("c", 9)
    assert stock.low_stock() == ["a", "c"]


def test_low_stock_empty():
    stock.ITEMS.clear()
    stock.receive("a", 50)
    assert stock.low_stock() == []


def test_backorder_regression():
    stock.ITEMS.clear()
    stock.receive("a", 4)
    assert stock.backorder_qty("a") == 6
