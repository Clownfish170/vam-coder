import order


def test_ship():
    assert order.advance("paid", "ship") == "shipped"


def test_pay_regression():
    assert order.advance("new", "pay") == "paid"


def test_unknown_regression():
    assert order.advance("new", "ship") == "new"
