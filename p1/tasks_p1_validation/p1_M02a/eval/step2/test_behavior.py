import inventory


def test_reserve_ledger():
    assert inventory.hold('a', 1) == [1]
    assert inventory.hold('a', 2) == [1, 2]


def test_avail_regression():
    assert inventory.net_of(10, 3) == 7
