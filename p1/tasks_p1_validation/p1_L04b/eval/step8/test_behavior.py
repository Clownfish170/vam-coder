from top import flush, flush_all
from cache import warm_row_serve


def test_agg():
    assert flush_all([3, 4]) == [10, 17]


def test_cache_regression():
    assert warm_row_serve(3) == 13
