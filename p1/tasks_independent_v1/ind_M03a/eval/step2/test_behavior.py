import order


def test_cancel_new():
    assert order.advance("new", "cancel") == "cancelled"


def test_cancel_paid():
    assert order.advance("paid", "cancel") == "cancelled"


def test_ship_regression():
    assert order.advance("paid", "ship") == "shipped"
