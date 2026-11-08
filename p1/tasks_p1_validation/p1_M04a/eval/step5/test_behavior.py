import pricing


def test_settle_list():
    assert pricing.billed_all([(10, 3), (4, 5)]) == [7 * 8, 0]
    assert pricing.billed_all([]) == []


def test_settle_regression():
    assert pricing.billed(10, 3) == 7 * 8


def test_price_regression():
    assert pricing.price_of(3) == 24
