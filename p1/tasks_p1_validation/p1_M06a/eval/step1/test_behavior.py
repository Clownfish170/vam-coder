import inventory


def test_net():
    assert inventory.open_count(10, 3) == 7
    assert inventory.open_count(5, 0) == 5


def test_count_regression():
    assert inventory.queue_len(['x', 'y']) == 2
