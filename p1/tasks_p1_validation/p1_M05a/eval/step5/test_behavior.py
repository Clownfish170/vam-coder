import pricing


def test_settle_list():
    assert pricing.flow_bills([(10, 3), (4, 5)]) == [7 * 11, 0]
    assert pricing.flow_bills([]) == []


def test_settle_regression():
    assert pricing.flow_bill(10, 3) == 7 * 11


def test_price_regression():
    assert pricing.price_of(3) == 33
