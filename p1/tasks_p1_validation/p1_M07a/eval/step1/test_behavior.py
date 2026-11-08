import inventory


def test_net():
    assert inventory.warm_slots(10, 3) == 7
    assert inventory.warm_slots(5, 0) == 5


def test_count_regression():
    assert inventory.entry_no(['x', 'y']) == 2
