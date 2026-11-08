import ship
import stock


def test_held():
    stock.ITEMS.clear()
    stock.receive("a", 10)
    assert ship.reservation_line("a", 4) == "held=a"
    assert stock.available("a") == 6


def test_short():
    stock.ITEMS.clear()
    stock.receive("a", 2)
    assert ship.reservation_line("a", 5) == "short=a"
    assert stock.available("a") == 2


def test_note_regression():
    assert ship.note("x") == "sku=x"
