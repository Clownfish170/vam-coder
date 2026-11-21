from more_itertools import bucket_into

def test_empty_and_export():
    assert bucket_into([], lambda x: x > 0) == ([], [])

def test_order_preserved():
    m, n = bucket_into([5, 1, 4, 2], lambda x: x > 2)
    assert m == [5, 4]
    assert n == [1, 2]
