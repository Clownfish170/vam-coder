import inventory


def test_net():
    assert inventory.net_of(10, 3) == 7
    assert inventory.net_of(5, 0) == 5


def test_count_regression():
    assert inventory.tally(['x', 'y']) == 2
