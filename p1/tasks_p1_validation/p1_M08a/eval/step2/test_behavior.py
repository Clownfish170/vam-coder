import inventory


def test_reserve_ledger():
    assert inventory.book('a', 1) == [1]
    assert inventory.book('a', 2) == [1, 2]


def test_avail_regression():
    assert inventory.open_lanes(10, 3) == 7
