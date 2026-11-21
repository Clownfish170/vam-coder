import pricing
from inventory import open_lanes


def test_settle():
    assert pricing.booked_price(10, 3) == 7 * 4
    assert pricing.booked_price(6, 1) == 5 * 4


def test_avail_visible():
    assert open_lanes(10, 3) == 7


def test_price_regression():
    assert pricing.price_of(2) == 8
