import order


def test_cost_fast():
    assert order.cost_fast(2) == 11


def test_cost():
    assert order.cost(2) == 11
