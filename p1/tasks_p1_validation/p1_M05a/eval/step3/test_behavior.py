import pricing
from inventory import net_flow


def test_settle():
    assert pricing.flow_bill(10, 3) == 7 * 11
    assert pricing.flow_bill(6, 1) == 5 * 11


def test_avail_visible():
    assert net_flow(10, 3) == 7


def test_price_regression():
    assert pricing.price_of(2) == 22
