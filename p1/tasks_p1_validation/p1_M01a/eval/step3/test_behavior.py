import pricing
from inventory import available


def test_settle():
    assert pricing.settle(10, 3) == 7 * 7
    assert pricing.settle(6, 1) == 5 * 7


def test_avail_visible():
    assert available(10, 3) == 7


def test_price_regression():
    assert pricing.price_of(2) == 14
