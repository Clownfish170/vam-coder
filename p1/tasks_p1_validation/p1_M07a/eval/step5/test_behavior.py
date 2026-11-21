import pricing


def test_settle_list():
    assert pricing.pinned_rates([(10, 3), (4, 5)]) == [7 * 5, 0]
    assert pricing.pinned_rates([]) == []


def test_settle_regression():
    assert pricing.pinned_rate(10, 3) == 7 * 5


def test_price_regression():
    assert pricing.price_of(3) == 15
