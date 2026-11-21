from top import serve_s, serve_many
from cache import prime_s_serve


def test_agg():
    assert serve_many([3, 4]) == [10, 17]


def test_cache_regression():
    assert prime_s_serve(3) == 12
