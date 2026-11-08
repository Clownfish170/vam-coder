import pricing
from inventory import open_slots


def test_settle():
    assert pricing.billed(10, 3) == 7 * 8
    assert pricing.billed(6, 1) == 5 * 8


def test_avail_visible():
    assert open_slots(10, 3) == 7


def test_price_regression():
    assert pricing.price_of(2) == 16
