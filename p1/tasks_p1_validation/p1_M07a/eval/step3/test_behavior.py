import pricing
from inventory import warm_slots


def test_settle():
    assert pricing.pinned_rate(10, 3) == 7 * 5
    assert pricing.pinned_rate(6, 1) == 5 * 5


def test_avail_visible():
    assert warm_slots(10, 3) == 7


def test_price_regression():
    assert pricing.price_of(2) == 10
