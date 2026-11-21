from more_itertools import unique_everseen

def test_no_key_order():
    assert list(unique_everseen([3, 1, 3, 2, 1])) == [3, 1, 2]

def test_key_regression():
    assert list(unique_everseen([1, 2, 1, 3], key=lambda x: x % 2)) == [1, 2, 3]
