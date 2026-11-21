import inventory
import pricing


def test_clamp_negative():
    assert inventory.net_of(4, 5) == 0
    assert inventory.net_of(4, 1) == 3


def test_settle_regression():
    assert pricing.quote_held(10, 3) == 7 * 9
    assert pricing.quote_held(4, 5) == 0


def test_reserve_regression():
    assert inventory.hold('b', 1) == [1]
