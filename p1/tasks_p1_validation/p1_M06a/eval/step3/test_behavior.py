import pricing
from inventory import open_count


def test_settle():
    assert pricing.seated_fee(10, 3) == 7 * 12
    assert pricing.seated_fee(6, 1) == 5 * 12


def test_avail_visible():
    assert open_count(10, 3) == 7


def test_price_regression():
    assert pricing.price_of(2) == 24
