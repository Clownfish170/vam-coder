import inventory
import pricing


def test_clamp_negative():
    assert inventory.open_count(4, 5) == 0
    assert inventory.open_count(4, 1) == 3


def test_settle_regression():
    assert pricing.seated_fee(10, 3) == 7 * 12
    assert pricing.seated_fee(4, 5) == 0


def test_reserve_regression():
    assert inventory.seat('b', 1) == [1]
