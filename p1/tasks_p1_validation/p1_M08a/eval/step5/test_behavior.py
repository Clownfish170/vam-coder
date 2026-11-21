import pricing


def test_settle_list():
    assert pricing.booked_prices([(10, 3), (4, 5)]) == [7 * 4, 0]
    assert pricing.booked_prices([]) == []


def test_settle_regression():
    assert pricing.booked_price(10, 3) == 7 * 4


def test_price_regression():
    assert pricing.price_of(3) == 12
