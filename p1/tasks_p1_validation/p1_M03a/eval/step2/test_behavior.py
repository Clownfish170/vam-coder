import inventory


def test_reserve_ledger():
    assert inventory.park('a', 1) == [1]
    assert inventory.park('a', 2) == [1, 2]


def test_avail_regression():
    assert inventory.free_qty(10, 3) == 7
