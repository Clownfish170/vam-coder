import pricing


def test_settle_list():
    assert pricing.seated_fees([(10, 3), (4, 5)]) == [7 * 12, 0]
    assert pricing.seated_fees([]) == []


def test_settle_regression():
    assert pricing.seated_fee(10, 3) == 7 * 12


def test_price_regression():
    assert pricing.price_of(3) == 36
