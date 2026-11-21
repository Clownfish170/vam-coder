import inventory
import pricing


def test_clamp_negative():
    assert inventory.net_flow(4, 5) == 0
    assert inventory.net_flow(4, 1) == 3


def test_settle_regression():
    assert pricing.flow_bill(10, 3) == 7 * 11
    assert pricing.flow_bill(4, 5) == 0


def test_reserve_regression():
    assert inventory.dial('b', 1) == [1]
