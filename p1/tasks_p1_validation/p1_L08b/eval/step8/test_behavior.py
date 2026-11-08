from top import dispatch, dispatch_all
from cache import prime_f_serve


def test_agg():
    assert dispatch_all([3, 4]) == [10, 17]


def test_cache_regression():
    assert prime_f_serve(3) == 11
