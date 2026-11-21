import inventory
import pricing


def test_clamp_negative():
    assert inventory.open_lanes(4, 5) == 0
    assert inventory.open_lanes(4, 1) == 3


def test_settle_regression():
    assert pricing.booked_price(10, 3) == 7 * 4
    assert pricing.booked_price(4, 5) == 0


def test_reserve_regression():
    assert inventory.book('b', 1) == [1]
