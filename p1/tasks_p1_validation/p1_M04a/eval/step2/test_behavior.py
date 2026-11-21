import inventory


def test_reserve_ledger():
    assert inventory.block('a', 1) == [1]
    assert inventory.block('a', 2) == [1, 2]


def test_avail_regression():
    assert inventory.open_slots(10, 3) == 7
