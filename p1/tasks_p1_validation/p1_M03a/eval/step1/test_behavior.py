import inventory


def test_net():
    assert inventory.free_qty(10, 3) == 7
    assert inventory.free_qty(5, 0) == 5


def test_count_regression():
    assert inventory.rows_seen(['x', 'y']) == 2
