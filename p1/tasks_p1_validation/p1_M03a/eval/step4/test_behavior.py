import inventory
import pricing


def test_clamp_negative():
    assert inventory.free_qty(4, 5) == 0
    assert inventory.free_qty(4, 1) == 3


def test_settle_regression():
    assert pricing.parked_price(10, 3) == 7 * 6
    assert pricing.parked_price(4, 5) == 0


def test_reserve_regression():
    assert inventory.park('b', 1) == [1]
