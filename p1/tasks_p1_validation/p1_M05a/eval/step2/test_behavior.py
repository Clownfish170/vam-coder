import inventory


def test_reserve_ledger():
    assert inventory.dial('a', 1) == [1]
    assert inventory.dial('a', 2) == [1, 2]


def test_avail_regression():
    assert inventory.net_flow(10, 3) == 7
