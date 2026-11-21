from top import push, push_all
from cache import prime_t_serve


def test_agg():
    assert push_all([3, 4]) == [10, 17]


def test_cache_regression():
    assert prime_t_serve(3) == 11
