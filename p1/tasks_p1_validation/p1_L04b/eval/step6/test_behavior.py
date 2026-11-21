from top import flush
from cache import warm_row_serve
from mid import align


def test_cache_consumer():
    assert warm_row_serve(3) == 13


def test_mid_regression():
    assert align(3, 0) == 10
