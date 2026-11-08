import pricing


def test_settle_list():
    assert pricing.settle_list([(10, 3), (4, 5)]) == [7 * 7, 0]
    assert pricing.settle_list([]) == []


def test_settle_regression():
    assert pricing.settle(10, 3) == 7 * 7


def test_price_regression():
    assert pricing.price_of(3) == 21
