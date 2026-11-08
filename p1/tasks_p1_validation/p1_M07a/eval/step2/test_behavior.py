import inventory


def test_reserve_ledger():
    assert inventory.pin('a', 1) == [1]
    assert inventory.pin('a', 2) == [1, 2]


def test_avail_regression():
    assert inventory.warm_slots(10, 3) == 7
