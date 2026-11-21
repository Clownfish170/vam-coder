import pricing


def test_settle_list():
    assert pricing.parked_many([(10, 3), (4, 5)]) == [7 * 6, 0]
    assert pricing.parked_many([]) == []


def test_settle_regression():
    assert pricing.parked_price(10, 3) == 7 * 6


def test_price_regression():
    assert pricing.price_of(3) == 18
