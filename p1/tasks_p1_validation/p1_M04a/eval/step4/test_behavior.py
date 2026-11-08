import inventory
import pricing


def test_clamp_negative():
    assert inventory.open_slots(4, 5) == 0
    assert inventory.open_slots(4, 1) == 3


def test_settle_regression():
    assert pricing.billed(10, 3) == 7 * 8
    assert pricing.billed(4, 5) == 0


def test_reserve_regression():
    assert inventory.block('b', 1) == [1]
