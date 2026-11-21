from more_itertools import bucket_into

def test_partition_by_predicate():
    m, n = bucket_into([1, 2, 3, 4], lambda x: x % 2 == 0)
    assert m == [2, 4]
    assert n == [1, 3]

def test_empty():
    assert bucket_into([], lambda x: True) == ([], [])
