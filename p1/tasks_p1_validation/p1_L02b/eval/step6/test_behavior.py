from top import handle
from cache import prime_serve
from mid import tune


def test_cache_consumer():
    assert prime_serve(3) == 12


def test_mid_regression():
    assert tune(3, 0) == 10
