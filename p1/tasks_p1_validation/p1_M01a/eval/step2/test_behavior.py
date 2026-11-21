import inventory


def test_reserve_ledger():
    assert inventory.reserve('a', 1) == [1]
    assert inventory.reserve('a', 2) == [1, 2]


def test_avail_regression():
    assert inventory.available(10, 3) == 7
