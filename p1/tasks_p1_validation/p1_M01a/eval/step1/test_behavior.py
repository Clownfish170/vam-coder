import inventory


def test_net():
    assert inventory.available(10, 3) == 7
    assert inventory.available(5, 0) == 5


def test_count_regression():
    assert inventory.count_rows(['x', 'y']) == 2
