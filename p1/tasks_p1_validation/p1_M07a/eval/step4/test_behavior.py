import inventory
import pricing


def test_clamp_negative():
    assert inventory.warm_slots(4, 5) == 0
    assert inventory.warm_slots(4, 1) == 3


def test_settle_regression():
    assert pricing.pinned_rate(10, 3) == 7 * 5
    assert pricing.pinned_rate(4, 5) == 0


def test_reserve_regression():
    assert inventory.pin('b', 1) == [1]
