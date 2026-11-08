import terms
import stock
import ship


def test_min_revised():
    assert terms.BACKORDER_MIN == 3
    stock.ITEMS.clear()
    stock.receive("a", 4)
    assert stock.backorder_qty("a") == 0
    stock.receive("b", 1)
    assert stock.backorder_qty("b") == 2
    assert stock.low_stock() == ["b"]


def test_full_chain():
    stock.ITEMS.clear()
    stock.receive("a", 10)
    assert stock.available("a") == 10
    assert stock.reserve("a", 4) is True
    assert ship.reservation_line("a", 20) == "short=a"
    assert stock.release("a", 4) == 10
    assert stock.backorder_qty("a") == 0
