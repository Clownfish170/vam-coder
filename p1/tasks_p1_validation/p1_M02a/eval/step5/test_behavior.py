import pricing


def test_settle_list():
    assert pricing.quote_batch([(10, 3), (4, 5)]) == [7 * 9, 0]
    assert pricing.quote_batch([]) == []


def test_settle_regression():
    assert pricing.quote_held(10, 3) == 7 * 9


def test_price_regression():
    assert pricing.price_of(3) == 27
