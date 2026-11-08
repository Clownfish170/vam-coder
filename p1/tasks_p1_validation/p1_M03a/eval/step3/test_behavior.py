import pricing
from inventory import free_qty


def test_settle():
    assert pricing.parked_price(10, 3) == 7 * 6
    assert pricing.parked_price(6, 1) == 5 * 6


def test_avail_visible():
    assert free_qty(10, 3) == 7


def test_price_regression():
    assert pricing.price_of(2) == 12
