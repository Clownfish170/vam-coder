import stock


def test_available():
    stock.ITEMS.clear()
    stock.receive("a", 7)
    assert stock.available("a") == 7


def test_available_missing():
    stock.ITEMS.clear()
    assert stock.available("zz") == 0


def test_receive_regression():
    stock.ITEMS.clear()
    stock.receive("a", 2)
    assert stock.ITEMS["a"] == 2
