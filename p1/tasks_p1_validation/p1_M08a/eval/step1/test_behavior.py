import inventory


def test_net():
    assert inventory.open_lanes(10, 3) == 7
    assert inventory.open_lanes(5, 0) == 5


def test_count_regression():
    assert inventory.lane_rows(['x', 'y']) == 2
