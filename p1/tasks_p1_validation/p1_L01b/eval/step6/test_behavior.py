from top import serve
from cache import warm_serve
from mid import adjust


def test_cache_consumer():
    assert warm_serve(3) == 11


def test_mid_regression():
    assert adjust(3, 0) == 10
