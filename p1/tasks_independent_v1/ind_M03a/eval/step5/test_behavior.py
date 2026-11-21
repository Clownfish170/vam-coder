import order


def test_actions_new():
    assert order.available_actions("new") == ["pay", "cancel"]


def test_actions_shipped():
    assert order.available_actions("shipped") == ["refund"]


def test_actions_terminal():
    assert order.available_actions("cancelled") == []
    assert order.available_actions("refunded") == []


def test_refund_regression():
    assert order.advance("shipped", "refund") == "refunded"
