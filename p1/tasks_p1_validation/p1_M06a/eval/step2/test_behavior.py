import inventory


def test_reserve_ledger():
    assert inventory.seat('a', 1) == [1]
    assert inventory.seat('a', 2) == [1, 2]


def test_avail_regression():
    assert inventory.open_count(10, 3) == 7
