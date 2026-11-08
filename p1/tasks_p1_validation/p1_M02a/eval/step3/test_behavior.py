import pricing
from inventory import net_of


def test_settle():
    assert pricing.quote_held(10, 3) == 7 * 9
    assert pricing.quote_held(6, 1) == 5 * 9


def test_avail_visible():
    assert net_of(10, 3) == 7


def test_price_regression():
    assert pricing.price_of(2) == 18
