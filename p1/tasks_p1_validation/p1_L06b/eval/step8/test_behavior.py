from top import relay, relay_all
from cache import load_cell_serve


def test_agg():
    assert relay_all([3, 4]) == [10, 17]


def test_cache_regression():
    assert load_cell_serve(3) == 11
