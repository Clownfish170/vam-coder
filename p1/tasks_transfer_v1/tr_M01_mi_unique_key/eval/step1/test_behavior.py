from more_itertools import unique_everseen

def test_key_keeps_distinct_raw_values():
    assert list(unique_everseen([1, 2, 1, 3], key=lambda x: x % 2)) == [1, 2, 3]

def test_key_same_value():
    assert list(unique_everseen([1, 1, 2, 2], key=lambda x: x)) == [1, 2]
