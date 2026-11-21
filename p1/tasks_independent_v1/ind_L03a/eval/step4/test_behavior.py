import stock


def test_release():
    stock.ITEMS.clear()
    stock.receive("a", 10)
    stock.reserve("a", 4)
    assert stock.release("a", 4) == 10
    assert stock.available("a") == 10


def test_release_partial():
    stock.ITEMS.clear()
    stock.receive("b", 5)
    stock.reserve("b", 2)
    assert stock.release("b", 1) == 4


def test_reserve_regression():
    stock.ITEMS.clear()
    stock.receive("a", 3)
    assert stock.reserve("a", 5) is False
    assert stock.available("a") == 3
