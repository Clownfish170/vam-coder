import inventory


def test_net():
    assert inventory.net_flow(10, 3) == 7
    assert inventory.net_flow(5, 0) == 5


def test_count_regression():
    assert inventory.log_rows(['x', 'y']) == 2
