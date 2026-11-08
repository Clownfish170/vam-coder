import inventory
import pricing


def test_clamp_negative():
    assert inventory.available(4, 5) == 0
    assert inventory.available(4, 1) == 3


def test_settle_regression():
    assert pricing.settle(10, 3) == 7 * 7
    assert pricing.settle(4, 5) == 0


def test_reserve_regression():
    assert inventory.reserve('b', 1) == [1]
