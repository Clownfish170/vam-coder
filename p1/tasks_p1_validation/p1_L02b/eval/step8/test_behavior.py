from top import handle, handle_all
from cache import prime_serve


def test_agg():
    assert handle_all([3, 4]) == [10, 17]


def test_cache_regression():
    assert prime_serve(3) == 12
