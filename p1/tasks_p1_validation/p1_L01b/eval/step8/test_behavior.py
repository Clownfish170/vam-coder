from top import serve, serve_all
from cache import warm_serve


def test_agg():
    assert serve_all([3, 4]) == [10, 17]


def test_cache_regression():
    assert warm_serve(3) == 11
