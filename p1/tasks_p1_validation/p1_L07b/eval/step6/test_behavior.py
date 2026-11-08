from top import serve_s
from cache import prime_s_serve
from mid import amp


def test_cache_consumer():
    assert prime_s_serve(3) == 12


def test_mid_regression():
    assert amp(3, 0) == 10
