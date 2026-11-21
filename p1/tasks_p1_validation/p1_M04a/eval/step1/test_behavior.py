import inventory


def test_net():
    assert inventory.open_slots(10, 3) == 7
    assert inventory.open_slots(5, 0) == 5


def test_count_regression():
    assert inventory.bin_count(['x', 'y']) == 2
